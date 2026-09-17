"""Completion writes and user opt-out exercise the real on-disk helpers."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from test_core import build_project, make_record, make_payload, make_grant, write, snapshot, SCRIPTS
from memory_core import default_config, validate_config, load_config, json_bytes, sha256, load_records
from memory_capture import capture, capture_status, set_capture
from memory_paths import MemoryError


class AutomaticCaptureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = build_project(Path(self.temp.name))

    def test_default_and_boolean_configuration(self):
        config = default_config("sample", "Sample")
        self.assertTrue(config["integration"]["automatic_capture"])
        for value in (True, False):
            config["integration"]["automatic_capture"] = value
            validate_config(config)
        for value in ("on", "off", 1, 0, None):
            config["integration"]["automatic_capture"] = value
            with self.assertRaises(MemoryError): validate_config(config)

    def test_completion_capture_and_exact_retry(self):
        record = make_record(self.root); payload = make_payload(self.root, record)
        grant = make_grant(self.root, payload)
        first = capture(self.root, payload, grant, "/root", trigger="work-completed")
        self.assertEqual("captured", first["status"])
        self.assertEqual("complete", first["publication"]["state"])
        before = snapshot(self.root)
        self.assertEqual(first, capture(self.root, payload, grant, "/root", trigger="work-completed"))
        self.assertEqual(before, snapshot(self.root)); self.assertEqual(1, len(load_records(self.root)))

    def test_off_skips_without_any_write_and_explicit_publication_still_works(self):
        original = load_config(self.root)
        result = set_capture(self.root, False, capture_status(self.root)["config_sha256"])
        self.assertTrue(result["mutated"])
        current = load_config(self.root); current["integration"]["automatic_capture"] = True
        self.assertEqual(original, current)
        before = snapshot(self.root)
        result = capture(self.root, {}, "absent-grant.json", "/root", trigger="task-completed")
        self.assertEqual("automatic_capture_off", result["reason"])
        self.assertEqual(before, snapshot(self.root))
        self.assertFalse(set_capture(self.root, False, capture_status(self.root)["config_sha256"])["mutated"])
        self.assertEqual(before, snapshot(self.root))
        from memory_publish import publish
        payload = make_payload(self.root, make_record(self.root)); grant = make_grant(self.root, payload)
        self.assertEqual("complete", publish(self.root, payload, grant, "/root")["state"])

    def test_stale_preference_change_and_publication_authority_fail_closed(self):
        old = capture_status(self.root)["config_sha256"]
        set_capture(self.root, False, old); before = snapshot(self.root)
        with self.assertRaises(MemoryError): set_capture(self.root, True, old)
        self.assertEqual(before, snapshot(self.root))
        set_capture(self.root, True, capture_status(self.root)["config_sha256"])
        payload = make_payload(self.root, make_record(self.root)); grant = make_grant(self.root, payload)
        with self.assertRaises(MemoryError): capture(self.root, payload, grant, "/root/child", trigger="work-completed")
        write(self.root, "docs/design.md", "Changed evidence\n")
        with self.assertRaises(MemoryError): capture(self.root, payload, grant, "/root", trigger="decision-recorded")
        self.assertEqual([], load_records(self.root))

    def test_cli_off_on_and_capture_status(self):
        def cli(*args):
            result = subprocess.run([sys.executable, "-B", str(SCRIPTS / "memory.py"),
                "--project-root", str(self.root), *args], capture_output=True, text=True)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            return json.loads(result.stdout)
        before = snapshot(self.root); state = cli("capture-status")
        self.assertEqual(before, snapshot(self.root))
        self.assertFalse(cli("set-capture", "off", "--expected-config-sha256", state["config_sha256"])["automatic_capture"])
        state = cli("capture-status")
        self.assertTrue(cli("set-capture", "on", "--expected-config-sha256", state["config_sha256"])["automatic_capture"])

    def test_native_grant_cannot_override_capture_off_but_explicit_publication_works(self):
        from test_publication import NativeMemoryFixture
        from memory_publish import publish
        fixture=NativeMemoryFixture();self.addCleanup(fixture.close)
        set_capture(fixture.root,False,capture_status(fixture.root)['config_sha256'])
        context=fixture.driver.context('memory.publish');grant,_=fixture.grant(context)
        before=snapshot(fixture.root)
        with fixture.driver.authority.invoke(context):
            result=capture(fixture.root,fixture.payload,grant,fixture.driver.actor,trigger='task-completed')
        self.assertEqual(result['reason'],'automatic_capture_off')
        self.assertEqual(before,snapshot(fixture.root))
        context=fixture.driver.context('memory.publish');grant,_=fixture.grant(context,suffix='explicit-correction')
        with fixture.driver.authority.invoke(context):
            explicit=publish(fixture.root,fixture.payload,grant,fixture.driver.actor)
        self.assertEqual(explicit['state'],'complete')
        self.assertFalse(load_config(fixture.root)['integration']['automatic_capture'])


if __name__ == "__main__": unittest.main()
