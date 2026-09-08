from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import plistlib
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('template_watch', Path(__file__).resolve().parents[1] / 'tools/template_watch.py')
watcher = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(watcher)


class WatcherTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        for directory in ('depot', 'tools', 'SKILLS-depo/demo/references', 'Projects/Sys4AI-Template-Project'):
            (self.root / directory).mkdir(parents=True, exist_ok=True)
        (self.root / 'depot/template-update.json').write_text('{}')
        (self.root / 'tools/template_update.py').write_text('')

    def test_nested_file_add_change_delete_changes_fingerprint(self):
        original = watcher.fingerprint(self.root)
        target = self.root / 'SKILLS-depo/demo/references/a.md'
        target.write_text('first')
        added = watcher.fingerprint(self.root)
        self.assertNotEqual(original, added)
        target.write_text('second content')
        self.assertNotEqual(added, watcher.fingerprint(self.root))
        before = watcher.fingerprint(self.root)
        target.unlink()
        self.assertNotEqual(before, watcher.fingerprint(self.root))

    def test_role_source_and_generated_template_index_changes_are_observed(self):
        source = self.root / "ROLES-depo/task-manager-ROLE.md"
        source.parent.mkdir()
        source.write_bytes((Path(__file__).resolve().parents[1] / "ROLES-depo/task-manager-ROLE.md").read_bytes())
        before = watcher.fingerprint(self.root)
        source.write_bytes(source.read_bytes() + b"\nBounded fixture edit.\n")
        self.assertNotEqual(before, watcher.fingerprint(self.root))
        index = self.root / "Projects/Sys4AI-Template-Project/roles/INDEX.md"
        index.parent.mkdir()
        index.write_text("Generated fixture navigation\n")
        before = watcher.fingerprint(self.root)
        index.write_text("Changed generated fixture navigation\n")
        self.assertNotEqual(before, watcher.fingerprint(self.root))
        # Another product remains outside the watcher's designated boundary.
        other = self.root / "Projects/Other/roles"
        other.mkdir(parents=True)
        before = watcher.fingerprint(self.root)
        (other / "INDEX.md").write_text("Unselected project\n")
        self.assertEqual(before, watcher.fingerprint(self.root))

    def test_transients_ignored_and_symlinks_not_followed(self):
        folder = self.root / 'SKILLS-depo/demo'
        (folder / '__pycache__').mkdir()
        before = watcher.fingerprint(self.root)
        (folder / '__pycache__/a.pyc').write_bytes(b'cache')
        self.assertEqual(before, watcher.fingerprint(self.root))
        (folder / 'cycle').symlink_to(folder, target_is_directory=True)
        self.assertIsInstance(watcher.fingerprint(self.root), str)

    def test_quiet_period_debounces_and_retries_unchanged_failures(self):
        quiet = watcher.QuietPeriod(2, retry=30)
        self.assertFalse(quiet.ready('a', 0))
        self.assertFalse(quiet.ready('a', 1))
        self.assertFalse(quiet.ready('b', 1.5))
        self.assertFalse(quiet.ready('b', 3))
        self.assertTrue(quiet.ready('b', 3.5))
        quiet.attempted_now('b', 3.5)
        self.assertFalse(quiet.ready('b', 20))
        self.assertTrue(quiet.ready('b', 34))

    def test_missing_depot_and_state_symlink_rejected(self):
        (self.root / 'depot/template-update.json').unlink()
        with self.assertRaises(FileNotFoundError):
            watcher.fingerprint(self.root)
        (self.root / 'depot/template-update.json').write_text('{}')
        (self.root / '.sys4ai').symlink_to(self.root / 'tools', target_is_directory=True)
        with self.assertRaises(ValueError):
            watcher.write_status(self.root, {'status': 'current'})

    def test_launch_agent_uses_exact_argv_and_host_logs(self):
        config = plistlib.loads(plistlib.dumps(watcher.configuration(self.root, 1, 2)))
        self.assertIn(str(self.root / 'tools/template_watch.py'), config['ProgramArguments'])
        self.assertIn(str(self.root), config['ProgramArguments'])
        self.assertTrue(config['KeepAlive'])
        self.assertTrue(config['RunAtLoad'])
        self.assertTrue(config['StandardErrorPath'].startswith(str(Path.home() / 'Library/Logs/Sys4AI')))
        self.assertNotEqual(watcher.label_for(self.root), watcher.label_for(self.root / 'other'))

    def test_engine_output_is_structured_and_never_saves_raw_failure(self):
        response = type('Response', (), {'stdout': 'sensitive raw output', 'returncode': 1})()
        with patch.object(watcher.subprocess, 'run', return_value=response):
            result = watcher.engine_apply(self.root)
        self.assertEqual('error', result['status'])
        self.assertNotIn('sensitive', json.dumps(result))

    def test_scan_failure_replaces_prior_success_status(self):
        watcher.write_status(self.root, {'result': {'status': 'current'}})
        handlers = {}
        def register(number, callback):
            handlers[number] = callback
        def stop(_delay):
            handlers[watcher.signal.SIGTERM](None, None)
        with patch.object(watcher.signal, 'signal', side_effect=register), patch.object(watcher, 'fingerprint', side_effect=OSError('scan failed')), patch.object(watcher.time, 'sleep', side_effect=stop):
            self.assertEqual(0, watcher.watch(self.root, 1, 2))
        status = json.loads((self.root / '.sys4ai/template-update/watcher.json').read_text())
        self.assertEqual('waiting', status['result']['status'])

    def test_log_symlink_rejected_before_launchctl(self):
        state = watcher.local_state(self.root)
        (state / 'watcher.log').symlink_to(self.root / 'tools/template_update.py')
        with patch.object(watcher, 'agent_path', return_value=self.root / 'agent.plist'), patch.object(watcher, 'log_directory', return_value=state), patch.object(watcher, 'launchctl') as launch:
            with self.assertRaisesRegex(ValueError, 'Watcher logs'):
                watcher.install(self.root, 1, 2)
            launch.assert_not_called()

    def test_loaded_service_needs_a_fresh_successful_check_to_be_ready(self):
        output = type('Response', (), {'stdout': 'state = running\npid = 1234\n', 'returncode': 0})()
        with patch.object(watcher, 'launchctl', return_value=output), patch.object(watcher.time, 'time', return_value=200):
            self.assertFalse(watcher.service_status(self.root)['ready'])
            watcher.write_status(self.root, {'pid': 1234, 'checked_at': 100, 'result': {'exit_code': 0}})
            self.assertFalse(watcher.service_status(self.root)['ready'])
            watcher.write_status(self.root, {'pid': 1234, 'checked_at': 199, 'result': {'exit_code': 2}})
            self.assertFalse(watcher.service_status(self.root)['ready'])
            watcher.write_status(self.root, {'pid': 9999, 'checked_at': 199, 'result': {'exit_code': 0}})
            self.assertFalse(watcher.service_status(self.root)['ready'])
            watcher.write_status(self.root, {'pid': 1234, 'checked_at': 199, 'result': {'exit_code': 0}})
            self.assertTrue(watcher.service_status(self.root)['ready'])

    def test_stop_waits_for_launchd_to_finish_unloading(self):
        response = lambda code: type('Response', (), {'returncode': code})()
        with patch.object(watcher, 'launchctl', side_effect=[response(0), response(0), response(0), response(113)]) as command, patch.object(watcher.time, 'sleep') as sleep:
            watcher.stop_service('gui/501/example')
        self.assertEqual(['print', 'bootout', 'print', 'print'], [call.args[0] for call in command.call_args_list])
        sleep.assert_called_once_with(0.1)


if __name__ == '__main__':
    unittest.main()
