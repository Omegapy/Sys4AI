"""Offline behavioral evidence using disposable roots and local Git histories."""
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from curator_events import make_event, commit_signal, catch_up_signal, validate_event
from curator_queue import DeliveryQueue
from curator_git import LocalGit
from curator_snapshots import empty_checkpoint, advance_checkpoint, recompute_obligations, current_stages
from curator_preflight import preflight, coalesce
from curator_causality import obligation_key, obligations_for, reduce_outcomes, stopping_decision
from curator_metrics import metrics
from curator_policy import PolicyError, canonical, digest

NOW = '2026-09-11T20:00:00Z'
REF = {'owner': 'task', 'path': 'Tasks/example/response.json', 'sha256': 'a' * 64}


def context(root):
    return {'project_id': 'project-a', 'repository_id': 'repository-a', 'coordination_root': str(root),
            'branch': 'refs/heads/main', 'snapshot': 'b' * 64, 'policy_sha256': 'c' * 64, 'source_sha256': 'd' * 64}


def event(ctx, operation='operation-1', kind='manual_correction', payload=None):
    return make_event(ctx, kind, operation, payload or {'request': REF}, created_at=NOW)


class DeliveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='curator-delivery-')
        self.root = Path(self.tmp.name).resolve(); self.ctx = context(self.root)
        self.queue = DeliveryQueue(self.root, 'project-a', 'repository-a')
    def tearDown(self): self.tmp.cleanup()

    def test_read_only_status_does_not_create_state(self):
        self.assertEqual(self.queue.status(), []); self.assertIsNone(self.queue.cursor('reader', self.ctx['branch'])['record'])
        self.assertEqual(list(self.root.iterdir()), [])

    def test_restart_cache_cleanup_and_cursor_cannot_hide_correction(self):
        e = event(self.ctx); self.queue.enqueue(e)
        cache = self.root / '.sys4ai/curator'; cache.mkdir(parents=True); (cache / 'cache').write_text('disposable')
        shutil.rmtree(cache)
        restarted = DeliveryQueue(self.root, 'project-a', 'repository-a')
        restarted.advance_cursor('reader', self.ctx['branch'], None, e['event_id'])
        rows = restarted.status(); self.assertEqual(rows[0]['event'], e); self.assertEqual(rows[0]['status'], 'pending')

    def test_event_exact_replay_conflict_and_strict_types(self):
        e = event(self.ctx); self.assertTrue(self.queue.enqueue(e)['created']); self.assertFalse(self.queue.enqueue(e)['created'])
        changed = copy.deepcopy(e); changed['source_sha256'] = 'e' * 64
        with self.assertRaisesRegex(PolicyError, 'different bytes'): self.queue.enqueue(changed)
        for key, value in [('schema_version', 2), ('task_status', 'complete'), ('command', 'touch forbidden')]:
            bad = copy.deepcopy(e); bad[key] = value
            with self.assertRaises(PolicyError): validate_event(bad)
        self.assertEqual(self.queue.status()[0]['event'], e)

    def test_receipt_cas_retry_owner_reference_and_terminal_boundary(self):
        e = event(self.ctx); self.queue.enqueue(e)
        args = dict(receipt_id='receipt-1', status='delivered', reason='delivered to selected reader', created_at=NOW)
        receipt = self.queue.record_delivery(e['event_id'], None, **args)
        self.assertEqual(receipt, self.queue.record_delivery(e['event_id'], None, **args))
        with self.assertRaises(PolicyError): self.queue.record_delivery(e['event_id'], None, **{**args, 'receipt_id': 'receipt-2'})
        with self.assertRaises(PolicyError): self.queue.record_delivery(e['event_id'], digest(receipt), **{**args, 'receipt_id': 'receipt-2', 'status': 'task_complete'})
        with self.assertRaises(PolicyError): self.queue.record_delivery(e['event_id'], digest(receipt), **{**args, 'receipt_id': 'receipt-2', 'status': 'consumed'})
        consumed = self.queue.record_delivery(e['event_id'], digest(receipt), **{**args, 'receipt_id': 'receipt-2', 'status': 'consumed', 'reference': REF})
        with self.assertRaises(PolicyError): self.queue.record_delivery(e['event_id'], digest(consumed), **{**args, 'receipt_id': 'receipt-3'})
        self.assertEqual(self.queue.status()[0]['status'], 'consumed')

    def test_cursor_interrupted_pointer_recovers_same_request(self):
        e = event(self.ctx); self.queue.enqueue(e); original = os.replace
        def fail_pointer(src, dst, **kwargs):
            if dst == 'current.json': raise OSError('synthetic power loss before pointer replacement')
            return original(src, dst, **kwargs)
        with patch('curator_queue.os.replace', side_effect=fail_pointer):
            with self.assertRaises(OSError): self.queue.advance_cursor('reader', self.ctx['branch'], None, e['event_id'])
        restarted = DeliveryQueue(self.root, 'project-a', 'repository-a')
        self.assertTrue(restarted.cursor('reader', self.ctx['branch'])['recovery_pending'])
        record = restarted.advance_cursor('reader', self.ctx['branch'], None, e['event_id'])
        self.assertEqual(record['revision'], 1); self.assertFalse(restarted.cursor('reader', self.ctx['branch'])['recovery_pending'])
        e2 = event(self.ctx, 'operation-2'); restarted.enqueue(e2)
        with self.assertRaises(PolicyError): restarted.advance_cursor('reader', self.ctx['branch'], None, e2['event_id'])
        with self.assertRaises(PolicyError): restarted.advance_cursor('reader', 'refs/heads/feature', None, e2['event_id'])
        self.assertEqual(len(restarted.status()), 2)

    def test_interrupted_event_atomic_publish_and_corrupt_or_unknown_record_hold(self):
        e = event(self.ctx)
        with patch('curator_queue.os.replace', side_effect=OSError('synthetic interruption')):
            with self.assertRaises(OSError): self.queue.enqueue(e)
        self.assertEqual(self.queue.status(), [])
        self.queue.enqueue(e)
        directory = self.root / 'control_records/curator/events'
        (directory / '.pending-orphan').write_text('incomplete unpublished bytes')
        self.assertEqual(len(self.queue.status()), 1)
        record = directory / (e['event_id'] + '.json'); record.write_bytes(b'{"partial":')
        with self.assertRaises(PolicyError): self.queue.status()

    def test_symlink_transport_path_and_hardlinked_record_rejected(self):
        foreign = self.root / 'foreign'; foreign.mkdir()
        (self.root / 'control_records').symlink_to(foreign, target_is_directory=True)
        with self.assertRaises(OSError): self.queue.enqueue(event(self.ctx))
        self.assertEqual(list(foreign.iterdir()), [])
        (self.root / 'control_records').unlink(); e = event(self.ctx); self.queue.enqueue(e)
        record = self.root / 'control_records/curator/events' / (e['event_id'] + '.json')
        os.link(record, self.root / 'alias')
        with self.assertRaises(PolicyError): self.queue.status()

    def test_capacity_rejects_before_append_but_exact_recovery_survives(self):
        first = event(self.ctx); second = event(self.ctx, 'operation-2')
        self.queue.enqueue(first); self.queue.enqueue(second)
        args = {'status': 'held', 'reason': 'waiting for owner', 'created_at': NOW}
        with patch('curator_queue.MAX_RECORDS', 2):
            one = self.queue.record_delivery(first['event_id'], None, receipt_id='receipt-1', **args)
            two = self.queue.record_delivery(first['event_id'], digest(one), receipt_id='receipt-2', **args)
            with self.assertRaises(PolicyError): self.queue.record_delivery(first['event_id'], digest(two), receipt_id='receipt-3', **args)
            self.assertEqual(two, self.queue.record_delivery(first['event_id'], digest(one), receipt_id='receipt-2', **args))
            self.assertEqual(len(self.queue.status()), 2)
            cursor = self.queue.advance_cursor('reader', self.ctx['branch'], None, first['event_id'])
            original = os.replace
            def fail_pointer(src, dst, **kwargs):
                if dst == 'current.json': raise OSError('interrupted pointer at capacity')
                return original(src, dst, **kwargs)
            with patch('curator_queue.os.replace', side_effect=fail_pointer):
                with self.assertRaises(OSError): self.queue.advance_cursor('reader', self.ctx['branch'], digest(cursor), second['event_id'])
            two_cursor = self.queue.advance_cursor('reader', self.ctx['branch'], digest(cursor), second['event_id'])
            with self.assertRaises(PolicyError): self.queue.advance_cursor('reader', self.ctx['branch'], digest(two_cursor), first['event_id'])
            self.assertEqual(self.queue.cursor('reader', self.ctx['branch'])['record']['revision'], 2)
            self.assertFalse(self.queue.cursor('reader', self.ctx['branch'])['recovery_pending'])

    def test_replaced_root_holds_reads_writes_and_preserves_pending_facts(self):
        e = event(self.ctx); self.queue.enqueue(e)
        original_record = self.root / 'control_records/curator/events' / (e['event_id'] + '.json')
        raw = original_record.read_bytes(); moved = self.root.with_name(self.root.name + '-original')
        self.root.rename(moved); self.root.mkdir()
        try:
            with self.assertRaises(PolicyError): self.queue.status()
            with self.assertRaises(PolicyError): self.queue.enqueue(event(self.ctx, 'operation-2'))
            self.assertEqual(list(self.root.iterdir()), [])
            self.assertEqual((moved / 'control_records/curator/events' / (e['event_id'] + '.json')).read_bytes(), raw)
        finally:
            self.root.rmdir(); moved.rename(self.root)
        self.assertEqual(self.queue.status()[0]['event'], e)

    def test_all_local_signal_types_and_human_agent_equivalence(self):
        commit = 'f' * 40
        human = commit_signal(self.ctx, commit, created_at=NOW)
        agent = commit_signal(self.ctx, commit, created_at=NOW)
        self.assertEqual(human, agent)
        signals = [event(self.ctx), human,
            event(self.ctx, 'work-1', 'accepted_work', {'completion': REF, 'effect': 'repair'}),
            catch_up_signal(self.ctx, None, commit, created_at=NOW),
            event(self.ctx, 'due-1', 'dependency_due', {'check_id': 'dependencies', 'due_at': NOW}),
            event(self.ctx, 'stale-1', 'stale_product', {'product_id': 'wiki', 'owner': 'ontology', 'input_sha256': 'e' * 64})]
        for e in signals: self.queue.enqueue(e)
        self.assertEqual(len(self.queue.status()), 6)
        self.assertIsNone(catch_up_signal(self.ctx, commit, commit, created_at=NOW))


class DecisionTests(unittest.TestCase):
    def setUp(self):
        self.ctx = context(Path('/selected/project'))
        self.raw = b'Current usage.'
        self.identity = {'id': 'usage', 'path': 'README.md', 'sha256': hashlib.sha256(self.raw).hexdigest()}
        self.entry = {**self.identity, 'pattern': False, 'class': 'documentation', 'owner': 'project', 'generator': None,
                      'sources': [], 'sections': [], 'interfaces': []}
        self.map = {'schema_version': 1, 'entries': [self.entry]}
    def screen(self, **kw):
        return preflight(self.ctx, ownership=self.map, snapshot={'README.md': self.raw}, relevant_paths=['README.md', 'docs/*'], now=NOW, **kw)

    def test_noop_cannot_call_process_or_mutation_routes(self):
        with patch('subprocess.Popen', side_effect=AssertionError('process invocation')), patch('builtins.open', side_effect=AssertionError('file access')), patch('os.open', side_effect=AssertionError('file access')):
            self.assertEqual(self.screen()['state'], 'idle')
            self.assertEqual(self.screen(pending=True)['state'], 'ready')

    def test_noop_irrelevant_and_cache_churn_have_no_side_effects(self):
        for path in (None, 'unrelated.py', '.sys4ai/curator/cache', 'control_records/curator/cursors/current.json'):
            delta = [] if path is None else [{'identity': {**self.identity, 'path': path}, 'ranges': [[0, 1]]}]
            result = self.screen(deltas=delta)
            self.assertEqual(result['state'], 'idle'); self.assertEqual(sum(result['counters'].values()), 0)
        future = self.screen(due_checks=[{'id': 'due', 'due_at': '2027-01-01T00:00:00Z', 'enabled': True}])
        self.assertEqual(future['state'], 'idle')
        commit = commit_signal(self.ctx, 'f' * 40, created_at=NOW)
        self.assertEqual(self.screen(events=[commit])['state'], 'idle')

    def test_relevant_unknown_due_generated_and_unavailable_routes(self):
        delta = {'identity': self.identity, 'ranges': [[0, len(self.raw)]]}
        relevant = self.screen(deltas=[delta]); self.assertEqual(relevant['routes'], ['project.documentation']); self.assertEqual(relevant['state'], 'ready')
        unknown = self.screen(deltas=[{'identity': {**self.identity, 'id': 'unknown'}, 'ranges': [[0, 1]]}]); self.assertEqual(unknown['state'], 'held')
        self.assertEqual(self.screen(due_checks=[{'id': 'due', 'due_at': NOW, 'enabled': True}])['state'], 'ready')
        self.assertEqual(self.screen(pending=True, runtime_available=False)['state'], 'unavailable')
        self.assertEqual(self.screen(pending=True, root_available=False)['state'], 'unavailable')
        self.assertEqual(self.screen(pending=True, owner_available=False)['state'], 'held')
        self.assertEqual(self.screen(pending=True, recovery_pending=True)['state'], 'held')
        self.entry.update({'class': 'generated', 'owner': 'ontology', 'generator': 'ontology.wiki', 'sources': ['ONTOLOGY/modules/a.jsonld']})
        self.assertEqual(self.screen(deltas=[delta])['routes'], ['ontology.wiki'])
        for result in (relevant, unknown): self.assertEqual(sum(result['counters'].values()), 0)

    def test_stale_branch_and_policy_events_hold_and_reordering_coalesces(self):
        a = event(self.ctx); b = copy.deepcopy(a); b['created_at'] = '2026-09-11T20:01:00Z'; b['event_id'] = 'retry'
        self.assertEqual(coalesce([a, b, a]), coalesce([b, a]))
        self.assertEqual(len(coalesce([a, b, a])), 1)
        for field in ('branch', 'snapshot', 'policy_sha256'):
            other = copy.deepcopy(a); other[field] = 'refs/heads/other' if field == 'branch' else 'f' * 64
            self.assertEqual(self.screen(events=[other])['state'], 'held')

    def test_branch_checkpoints_assessment_cannot_reconcile_or_promote_other_branch(self):
        cp = empty_checkpoint(self.ctx); cp = advance_checkpoint(cp, 'observed', self.ctx)
        cp = advance_checkpoint(cp, 'assessed', self.ctx, evidence=[REF])
        self.assertIsNone(cp['integrated']); self.assertIsNone(cp['reconciled'])
        with self.assertRaises(PolicyError): advance_checkpoint(cp, 'reconciled', self.ctx, evidence=[REF])
        with self.assertRaises(PolicyError): advance_checkpoint(cp, 'integrated', {**self.ctx, 'branch': 'refs/heads/feature'}, evidence=[REF])
        obligation = 'e' * 64
        cp = advance_checkpoint(cp, 'integrated', self.ctx, evidence=[REF], obligations=[obligation])
        with self.assertRaises(PolicyError): advance_checkpoint(cp, 'reconciled', self.ctx, evidence=[REF], obligations=[obligation])
        reconciled = advance_checkpoint(cp, 'reconciled', self.ctx, evidence=[REF], obligations=[obligation], satisfied=[obligation])
        self.assertEqual(metrics([], [], [reconciled])['reconciled_current'], 1)
        changed = {**self.ctx, 'snapshot': 'e' * 64}
        observed = advance_checkpoint(reconciled, 'observed', changed)
        self.assertEqual(metrics([], [], [observed])['reconciled_current'], 0)
        with self.assertRaises(PolicyError): advance_checkpoint(observed, 'integrated', self.ctx, evidence=[REF])

    def test_same_context_changed_predecessor_retains_history_but_invalidates_current(self):
        checkpoint = empty_checkpoint(self.ctx)
        checkpoint = advance_checkpoint(checkpoint, 'observed', self.ctx)
        for stage in ('assessed', 'integrated', 'reconciled'):
            checkpoint = advance_checkpoint(checkpoint, stage, self.ctx, evidence=[REF])
        self.assertEqual(metrics([], [], [checkpoint])['reconciled_current'], 1)
        for stage in ('observed', 'assessed', 'integrated', 'reconciled'):
            self.assertEqual(advance_checkpoint(checkpoint, stage, self.ctx, evidence=[] if stage == 'observed' else [REF]), checkpoint)
        obligation = 'e' * 64
        changed = advance_checkpoint(checkpoint, 'observed', self.ctx, obligations=[obligation])
        self.assertEqual(current_stages(changed), {'observed': True, 'assessed': False, 'integrated': False, 'reconciled': False})
        for stage in ('assessed', 'integrated', 'reconciled'): self.assertEqual(changed[stage], checkpoint[stage])
        self.assertEqual(metrics([], [], [changed])['reconciled_current'], 0)
        with self.assertRaises(PolicyError): advance_checkpoint(changed, 'integrated', self.ctx, evidence=[REF], obligations=[obligation])
        with self.assertRaises(PolicyError): advance_checkpoint(changed, 'reconciled', self.ctx, evidence=[REF])
        for stage in ('assessed', 'integrated', 'reconciled'):
            changed = advance_checkpoint(changed, stage, self.ctx, evidence=[REF], obligations=[obligation],
                                         satisfied=[obligation] if stage == 'reconciled' else [])
        self.assertEqual(metrics([], [], [changed])['reconciled_current'], 1)
        revised_evidence = {**REF, 'sha256': 'f' * 64}
        revised_assessment = advance_checkpoint(checkpoint, 'assessed', self.ctx, evidence=[revised_evidence])
        counts = metrics([], [], [revised_assessment])
        self.assertEqual((counts['assessed_current'], counts['integrated_current'], counts['reconciled_current']), (1, 0, 0))
        self.assertEqual(revised_assessment['integrated'], checkpoint['integrated'])
        self.assertEqual(revised_assessment['reconciled'], checkpoint['reconciled'])

    def test_unavailable_root_never_becomes_deletion(self):
        previous = {'context': self.ctx, 'commit': 'a' * 40}
        result = recompute_obligations(previous, previous, root_available=False)
        self.assertEqual(result['state'], 'unavailable'); self.assertEqual(result['obligations'], []); self.assertTrue(result['retain_previous'])

    def outcome(self, key, attempt=1, status='failed', **kw):
        return {'key': key, 'attempt': attempt, 'status': status, 'input_sha256': 'a' * 64,
                'output_sha256': None, 'finding_sha256': 'b' * 64, 'reference': None, 'elapsed_ms': 10, 'bytes': 20, **kw}

    def test_causal_retry_reorder_conflict_and_repair_followthrough(self):
        e = event(self.ctx, kind='accepted_work', payload={'completion': REF, 'effect': 'repair'})
        obligations = obligations_for(e)
        self.assertEqual([x['obligation'] for x in obligations], ['documentation', 'knowledge'])
        derivative = event(self.ctx, kind='accepted_work', payload={'completion': REF, 'effect': 'derivative'})
        self.assertEqual(obligations_for(derivative), [])
        key = obligations[0]['key']; success = self.outcome(key, status='satisfied', reference=REF, output_sha256='c' * 64, finding_sha256=None)
        self.assertEqual(len(reduce_outcomes([success, success])), 1)
        conflict = {**success, 'output_sha256': 'd' * 64}
        self.assertEqual(reduce_outcomes([success, conflict]), reduce_outcomes([conflict, success]))
        self.assertEqual(reduce_outcomes([success, conflict])[key]['state'], 'held')
        self.assertNotEqual(key, obligation_key({**e, 'branch': 'refs/heads/feature'}, 'documentation'))

    def test_mixed_input_outcomes_hold_and_preserve_ordered_reordered_findings(self):
        key = obligation_key(event(self.ctx), 'assessment')
        satisfied = self.outcome(key, status='satisfied', reference=REF, output_sha256='c' * 64, finding_sha256=None)
        held = self.outcome(key, attempt=2, status='held', input_sha256='d' * 64, finding_sha256='e' * 64)
        limits = {'attempts': 9, 'elapsed_ms': 1000, 'bytes': 1000}
        forward = reduce_outcomes([satisfied, held]); reverse = reduce_outcomes([held, satisfied, satisfied])
        self.assertEqual(forward, reverse); self.assertEqual(forward[key]['state'], 'held')
        self.assertIsNone(forward[key]['output_sha256']); self.assertTrue(forward[key]['input_conflict'])
        self.assertEqual(len(forward[key]['attempts']), 2)
        decision = stopping_decision(key, [held, satisfied], limits)
        self.assertEqual(decision, stopping_decision(key, [satisfied, held], limits))
        self.assertTrue(decision['stop']); self.assertEqual(decision['unresolved_findings'], ['e' * 64])
        self.assertIn('mixed_input_versions', decision['reasons']); self.assertNotIn('satisfied', decision['reasons'])
        self.assertEqual(metrics([], [held, satisfied])['satisfied_effects'], 0)
        self.assertEqual(metrics([], [held, satisfied])['held_effects'], 1)
        exact_retry = reduce_outcomes([satisfied, copy.deepcopy(satisfied)])
        self.assertEqual(exact_retry[key]['state'], 'satisfied'); self.assertEqual(len(exact_retry[key]['attempts']), 1)

    def test_same_attempt_changed_input_retains_both_observations(self):
        key = obligation_key(event(self.ctx), 'assessment')
        satisfied = self.outcome(key, status='satisfied', reference=REF, output_sha256='c' * 64, finding_sha256=None)
        held = self.outcome(key, status='held', input_sha256='d' * 64, finding_sha256='e' * 64)
        first = reduce_outcomes([satisfied, held]); second = reduce_outcomes([held, satisfied])
        self.assertEqual(first, second); self.assertEqual(len(first[key]['attempts']), 2)
        decision = stopping_decision(key, [satisfied, held], {'attempts': 9, 'elapsed_ms': 1000, 'bytes': 1000})
        self.assertEqual(decision['state'], 'held'); self.assertEqual(decision['unresolved_findings'], ['e' * 64])

    def test_selected_limits_and_repeated_unchanged_failures_retain_finding(self):
        key = obligation_key(event(self.ctx), 'assessment'); rows = [self.outcome(key), self.outcome(key, 2)]
        limits = {'attempts': 9, 'elapsed_ms': 1000, 'bytes': 1000}
        result = stopping_decision(key, list(reversed(rows)), limits)
        self.assertTrue(result['stop']); self.assertIn('unchanged_failure', result['reasons']); self.assertEqual(result['unresolved_findings'], ['b' * 64])
        for bound, value in (('attempts', 1), ('elapsed_ms', 10), ('bytes', 20)):
            self.assertTrue(stopping_decision(key, rows[:1], {**limits, bound: value})['stop'])
        with self.assertRaises(PolicyError): stopping_decision(key, [], {**limits, 'attempts': None})

    def test_metrics_are_repeatable_read_only_derivations(self):
        e = event(self.ctx); key = obligation_key(e, 'assessment'); source = [self.outcome(key)]
        before = copy.deepcopy(source); result = metrics([e, e], source)
        self.assertEqual(result['logical_events'], 1); self.assertEqual(result['pending_effects'], 1)
        self.assertEqual(source, before); self.assertEqual(result, metrics([e], source))


class GitTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='curator-git-fixture-'); self.root = Path(self.tmp.name).resolve()
        self.git = shutil.which('git'); self.sha = hashlib.sha256(Path(self.git).read_bytes()).hexdigest()
        self.env = {'PATH': '/usr/bin:/bin:/usr/sbin:/sbin', 'LC_ALL': 'C', 'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': os.devnull,
                    'GIT_CONFIG_SYSTEM': os.devnull, 'GIT_AUTHOR_NAME': 'Fixture', 'GIT_AUTHOR_EMAIL': 'fixture@example.invalid',
                    'GIT_COMMITTER_NAME': 'Fixture', 'GIT_COMMITTER_EMAIL': 'fixture@example.invalid',
                    'GIT_AUTHOR_DATE': NOW, 'GIT_COMMITTER_DATE': NOW, 'GIT_TERMINAL_PROMPT': '0'}
        self.run_git('init', '-b', 'main'); (self.root / 'a.txt').write_text('first source\n'); self.commit('initial')
    def tearDown(self): self.tmp.cleanup()
    def run_git(self, *args):
        return subprocess.run([self.git, '-c', 'core.hooksPath=' + os.devnull, '-c', 'commit.gpgSign=false', '-C', str(self.root), *args],
                              env=self.env, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout
    def commit(self, message):
        self.run_git('add', '--all'); self.run_git('commit', '-m', message)
        return self.run_git('rev-parse', 'HEAD').strip().decode()
    def reader(self, **kw): return LocalGit(self.root, self.git, self.sha, **kw)
    def state(self, reader):
        snap = reader.snapshot(); return {'context': {**context(self.root), 'repository_id': reader.repository_id,
                          'branch': snap['branch'], 'snapshot': snap['snapshot'], 'source_sha256': snap['worktree_sha256']}, 'commit': snap['commit']}

    def test_git_configured_execution_canaries_and_index_are_preserved(self):
        marker = self.root / 'EXECUTED'; script = self.root / 'malicious-helper'
        script.write_text('#!/bin/sh\nprintf executed >> "' + str(marker) + '"\ncat\n'); script.chmod(0o700)
        attrs = self.root / '.gitattributes'; attrs.write_text('*.txt diff=malicious filter=malicious\n')
        self.commit('fixture attributes')
        for key in ('diff.external', 'diff.malicious.command', 'diff.malicious.textconv', 'core.fsmonitor', 'filter.malicious.clean', 'filter.malicious.smudge', 'filter.malicious.process'):
            self.run_git('config', key, str(script))
        self.run_git('config', 'filter.malicious.required', 'true')
        hooks = self.root / '.git/hooks'; (hooks / 'post-index-change').write_text(script.read_text()); (hooks / 'post-index-change').chmod(0o700)
        (self.root / 'a.txt').write_text('changed source\n')
        index = self.root / '.git/index'; before = (index.read_bytes(), index.stat().st_mtime_ns)
        config = (self.root / '.git/config').read_bytes(); hook = (hooks / 'post-index-change').read_bytes()
        with patch.dict(os.environ, {'GIT_EXTERNAL_DIFF': str(script), 'GIT_CONFIG_COUNT': '1', 'GIT_CONFIG_KEY_0': 'core.fsmonitor', 'GIT_CONFIG_VALUE_0': str(script)}):
            reader = self.reader(); snapshot = reader.snapshot(); reader.changes(None, snapshot['commit'])
        self.assertTrue(snapshot['dirty']); self.assertFalse(marker.exists())
        self.assertEqual((index.read_bytes(), index.stat().st_mtime_ns), before)
        self.assertEqual((self.root / '.git/config').read_bytes(), config); self.assertEqual((hooks / 'post-index-change').read_bytes(), hook)

    def test_index_only_change_invalidates_snapshot_with_same_head_and_worktree(self):
        target = self.root / 'a.txt'; target.write_text('unchanged working copy\n')
        reader = self.reader(); before = reader.snapshot()
        target.write_text('different staged copy\n'); self.run_git('add', '--', 'a.txt')
        target.write_text('unchanged working copy\n'); after = reader.snapshot()
        self.assertEqual(before['commit'], after['commit']); self.assertEqual(before['tree'], after['tree'])
        self.assertEqual(before['worktree_sha256'], after['worktree_sha256'])
        self.assertTrue(before['dirty']); self.assertTrue(after['dirty'])
        self.assertNotEqual(before['index_sha256'], after['index_sha256'])
        self.assertNotEqual(before['snapshot'], after['snapshot']); self.assertNotEqual(before['source_sha256'], after['source_sha256'])
        old_context = {**context(self.root), 'snapshot': before['snapshot'], 'source_sha256': before['source_sha256']}
        new_context = {**old_context, 'snapshot': after['snapshot'], 'source_sha256': after['source_sha256']}
        result = recompute_obligations({'context': old_context, 'commit': before['commit']}, {'context': new_context, 'commit': after['commit']})
        self.assertIn('source_changed', [o['kind'] for o in result['obligations']])

    def test_index_intent_flags_identity_and_split_index_hold(self):
        target = self.root / 'new.txt'; target.write_bytes(b'')
        self.run_git('add', '--intent-to-add', '--', 'new.txt')
        listing_before = self.run_git('ls-files', '--stage', '-z')
        reader = self.reader(); before = reader.snapshot()
        self.assertEqual(before, reader.snapshot())
        self.run_git('add', '--', 'new.txt')
        listing_after = self.run_git('ls-files', '--stage', '-z'); after = reader.snapshot()
        self.assertEqual(listing_before, listing_after)
        self.assertEqual(before['commit'], after['commit']); self.assertEqual(before['worktree_sha256'], after['worktree_sha256'])
        self.assertNotEqual(before['index_sha256'], after['index_sha256']); self.assertNotEqual(before['snapshot'], after['snapshot'])
        self.assertNotEqual(before['source_sha256'], after['source_sha256'])
        index = self.root / '.git/index'; replacement = self.root / '.git/index-replacement'
        replacement.write_bytes(index.read_bytes()); os.replace(replacement, index)
        replaced = reader.snapshot()
        self.assertEqual(after['index_sha256'], replaced['index_sha256'])
        self.assertNotEqual(after['index_identity_sha256'], replaced['index_identity_sha256'])
        self.assertNotEqual(after['snapshot'], replaced['snapshot'])
        self.run_git('update-index', '--split-index')
        with self.assertRaises(PolicyError) as held: reader.snapshot()
        self.assertEqual(held.exception.code, 'split_index_unsupported')

    def test_late_filter_config_cannot_execute_and_raw_hash_detects_change(self):
        reader = self.reader(); first = reader.snapshot()
        marker = self.root / 'EXECUTED'; script = self.root / '.git/malicious-late'
        script.write_text('#!/bin/sh\nprintf executed >> "' + str(marker) + '"\ncat\n'); script.chmod(0o700)
        self.run_git('config', 'filter.late.clean', str(script))
        self.run_git('config', 'filter.late.process', str(script))
        (self.root / '.git/info/attributes').write_text('*.txt filter=late diff=late\n')
        self.run_git('config', 'diff.late.textconv', str(script))
        (self.root / 'a.txt').write_text('late change\n')
        current = reader.snapshot()
        self.assertFalse(marker.exists()); self.assertNotEqual(first['snapshot'], current['snapshot']); self.assertTrue(current['dirty'])

    def test_replacement_at_content_close_and_intermediate_symlink_hold(self):
        target = self.root / 'untracked'; target.write_text('original')
        identity = target.stat().st_dev, target.stat().st_ino; reader = self.reader()
        original_close = os.close; injected = []
        def replace_at_close(fd):
            try: info = os.fstat(fd)
            except OSError: return original_close(fd)
            if not injected and (info.st_dev, info.st_ino) == identity:
                replacement = self.root / 'replacement'; replacement.write_text('replaced')
                os.replace(replacement, target); injected.append(True)
            return original_close(fd)
        with patch('curator_git.os.close', side_effect=replace_at_close):
            with self.assertRaises(PolicyError): reader.snapshot()
        self.assertTrue(injected)
        nested = self.root / 'nested'; nested.mkdir(); (nested / 'source').write_text('inside')
        outside = self.root / 'outside'; outside.mkdir(); (outside / 'source').write_text('outside must not be read')
        original_open = os.open; escaped = []
        def replace_parent(name, flags, *args, **kwargs):
            if name == b'nested' and not escaped:
                nested.rename(self.root / 'old-nested'); nested.symlink_to(outside, target_is_directory=True); escaped.append(True)
            return original_open(name, flags, *args, **kwargs)
        with patch('curator_git.os.open', side_effect=replace_parent):
            with self.assertRaises(PolicyError): reader.snapshot()
        self.assertTrue(escaped)

    def test_nul_paths_rename_deletion_and_dirty_snapshot_identity(self):
        reader = self.reader(); before = self.state(reader)
        source = self.root / 'a.txt'; renamed = self.root / 'renamed\nwith tab\t.txt'; source.rename(renamed); commit = self.commit('rename')
        changes = reader.changes(before['commit'], commit)
        self.assertEqual(changes[0]['status'][0], 'R')
        after = self.state(reader); obligations = recompute_obligations(before, after, ancestor=reader.is_ancestor(before['commit'], commit), changes=changes)
        self.assertIn('rename', [o['kind'] for o in obligations['obligations']])
        renamed.unlink(); deleted = self.commit('delete')
        self.assertEqual(reader.changes(commit, deleted)[0]['status'], 'D')
        untracked = self.root / 'new\nfile'; untracked.write_text('one'); first = reader.snapshot(); untracked.write_text('two')
        self.assertNotEqual(first['snapshot'], reader.snapshot()['snapshot'])

    def test_rebase_squash_force_update_and_branch_switch_recompute(self):
        reader = self.reader(); base = self.state(reader)
        self.run_git('checkout', '-b', 'feature'); (self.root / 'feature.txt').write_text('feature'); self.commit('feature'); feature = self.state(reader)
        self.run_git('checkout', 'main'); (self.root / 'main.txt').write_text('main'); self.commit('main')
        self.run_git('checkout', 'feature'); self.run_git('rebase', 'main'); rebased = self.state(reader)
        self.assertFalse(reader.is_ancestor(feature['commit'], rebased['commit']))
        kinds = recompute_obligations(feature, rebased, ancestor=False, changes=reader.changes(feature['commit'], rebased['commit']))
        self.assertIn('rewritten_history', [o['kind'] for o in kinds['obligations']])
        self.run_git('checkout', 'main'); self.run_git('merge', '--squash', 'feature'); self.commit('squash'); squashed = self.state(reader)
        self.assertFalse(reader.is_ancestor(rebased['commit'], squashed['commit']))
        switch = recompute_obligations(rebased, squashed, ancestor=False)
        self.assertIn('branch_switch', [o['kind'] for o in switch['obligations']])
        self.run_git('reset', '--hard', base['commit']); forced = self.state(reader)
        self.assertIn('rewritten_history', [o['kind'] for o in recompute_obligations(squashed, forced, ancestor=reader.is_ancestor(squashed['commit'], forced['commit']))['obligations']])

    def test_missing_root_detached_head_and_finite_output_hold(self):
        reader = self.reader()
        self.run_git('checkout', '--detach')
        with self.assertRaises(PolicyError): reader.head()
        self.run_git('checkout', 'main')
        (self.root / 'large').write_text('x' * 3000)
        with self.assertRaises(PolicyError): self.reader(max_bytes=1024).snapshot()
        moved = self.root.with_name(self.root.name + '-moved'); self.root.rename(moved)
        try:
            with self.assertRaises(PolicyError): reader.head()
        finally: moved.rename(self.root)

if __name__ == '__main__': unittest.main()
