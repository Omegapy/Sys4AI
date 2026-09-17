"""Exact selected local integration with durable original-operation recovery.

A trusted deployment constructs this owner. Model requests carry one opaque
candidate identity; they cannot select paths, validators, Git actions or bytes.
"""
import base64
import copy
import hashlib
import json
import os
from pathlib import Path
import secrets
import stat

from curator_classification import relative
from curator_confinement import file_snapshot, parent_descriptor
from curator_policy import canonical, digest, exact, require, sha


def read_exact(root, path, *, missing=False):
    relative(path)
    with parent_descriptor(root, path) as (parent, name):
        try: fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
        except FileNotFoundError:
            if missing: return None
            raise
        with os.fdopen(fd, 'rb') as source:
            before = os.fstat(source.fileno())
            require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and before.st_size <= 2000000,
                    'integration_file', 'Integration requires bounded regular unlinked files.')
            raw = source.read(2000001); after = os.fstat(source.fileno())
            current = os.stat(name, dir_fd=parent, follow_symlinks=False)
            identity = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
            require(identity(before) == identity(after) == identity(current) and len(raw) <= 2000000,
                    'integration_changed', 'A source changed during read.')
            return raw


def content_hash(raw):
    return None if raw is None else hashlib.sha256(raw).hexdigest()


def replace_exact(root, path, raw, expected):
    """No cleanup or rollback. Other writers must honor project serialization."""
    with parent_descriptor(root, path) as (parent, name):
        before = read_exact(root, path, missing=True)
        require(content_hash(before) == expected, 'target_changed', 'Current target differs from its selected predecessor.')
        require(type(raw) is bytes and len(raw) <= 2000000, 'integration_bytes', 'Expected bounded exact candidate bytes.')
        mode = 0o644 if before is None else stat.S_IMODE(os.stat(name, dir_fd=parent, follow_symlinks=False).st_mode)
        temporary = '.' + name + '-curator-' + secrets.token_hex(12)
        fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, mode, dir_fd=parent)
        try:
            with os.fdopen(fd, 'wb') as out: out.write(raw); out.flush(); os.fsync(out.fileno())
            require(content_hash(read_exact(root, path, missing=True)) == expected, 'target_changed', 'Target changed while candidate was staged.')
            if before is None:
                os.link(temporary, name, src_dir_fd=parent, dst_dir_fd=parent, follow_symlinks=False)
                os.unlink(temporary, dir_fd=parent)
            else: os.replace(temporary, name, src_dir_fd=parent, dst_dir_fd=parent)
            os.fsync(parent)
        finally:
            try: os.unlink(temporary, dir_fd=parent)
            except FileNotFoundError: pass


def changed_ranges(before, after, declared):
    """Derive actual byte changes; a declaration cannot hide another edit.

    Match bounded lines, then trim equal bytes inside each changed hunk. Inserts
    include both adjacent predecessor bytes so a section edge cannot borrow the
    less protected neighbor's authority. No unchanged whole-file classification.
    """
    import difflib
    require(type(before) is bytes and type(after) is bytes and max(len(before), len(after)) <= 2000000,
            'diff_bound', 'Expected bounded exact predecessor and candidate bytes.')
    old_lines = before.splitlines(keepends=True); new_lines = after.splitlines(keepends=True)
    require(max(len(old_lines), len(new_lines)) <= 20000, 'diff_bound', 'Selected byte-diff line bound exceeded.')
    old_offsets = [0]; new_offsets = [0]
    for line in old_lines: old_offsets.append(old_offsets[-1] + len(line))
    for line in new_lines: new_offsets.append(new_offsets[-1] + len(line))
    ranges = []
    for tag, a, b, c, d in difflib.SequenceMatcher(None, old_lines, new_lines, autojunk=True).get_opcodes():
        if tag == 'equal': continue
        low, high = old_offsets[a], old_offsets[b]; new_low, new_high = new_offsets[c], new_offsets[d]
        while low < high and new_low < new_high and before[low] == after[new_low]: low += 1; new_low += 1
        while low < high and new_low < new_high and before[high-1] == after[new_high-1]: high -= 1; new_high -= 1
        if low == high:
            low, high = max(0, low-1), min(len(before), high+1)
        ranges.append([low, high])
    require(ranges and len(ranges) <= 500, 'candidate_unchanged', 'Expected bounded actual changed-byte coverage.')
    allowed = []
    for value in declared:
        require(type(value) is list and len(value)==2 and all(type(n) is int for n in value)
                and 0 <= value[0] <= value[1] <= len(before), 'ranges', 'Invalid declared byte range.')
        allowed.append(value)
    for low, high in ranges:
        cursor = low
        for left, right in sorted(allowed):
            if left <= cursor <= right: cursor = max(cursor, right)
        require(cursor >= high and (low != high or any(a <= low <= b for a,b in allowed)),
                'undeclared_change', 'Actual candidate bytes escape the independently reviewed ranges.')
    return ranges


class IntegrationOwner:
    """Selected source, target and owner checks are protected constructor inputs."""
    def __init__(self, coordination, candidates, *, memory_core=None, ontology_core=None, ontology_validate=None):
        self.coordination = coordination; self.candidates = copy.deepcopy(candidates)
        self.memory_core = memory_core; self.ontology_core = ontology_core; self.ontology_validate = ontology_validate
        self.root = coordination.checkout.root
        require(self.root == coordination.canonical.root, 'integration_root',
                'This selected local integration owner requires the target checkout to own its canonical ledger.')

    def _selected(self, payload):
        exact(payload, ('candidate_id',)); key = payload['candidate_id']
        require(type(key) is str and key in self.candidates, 'candidate_unselected', 'Candidate was not accepted by trusted deployment.')
        selected = self.candidates[key]
        exact(selected, ('operation_id', 'candidate_root', 'source_refs', 'files', 'snapshot', 'checks', 'permissions', 'review_sha256'))
        require(key == selected['operation_id'] and key and len(key) <= 96 and all(c.isascii() and (c.isalnum() or c in '-_') for c in key),
                'operation_id', 'Candidate must bind one original operation identity.')
        sha(selected['review_sha256']); exact(selected['permissions'], ('local_integration', 'commit', 'push', 'merge'))
        require(all(type(v) is bool for v in selected['permissions'].values()) and selected['permissions']['local_integration'],
                'integration_permission', 'Local integration needs its separate selected permission.')
        require(not any(selected['permissions'][k] for k in ('commit', 'push', 'merge')), 'publication_owner',
                'This local owner performs no Git publication; select the existing publication owner separately.')
        require(type(selected['files']) is list and 0 < len(selected['files']) <= 100, 'integration_files', 'Select bounded candidate files.')
        seen = set(); total = 0
        for item in selected['files']:
            exact(item, ('path', 'before_sha256', 'after_sha256')); key = relative(item['path'])
            require(key not in seen, 'integration_alias', 'Candidate paths collide.'); seen.add(key)
            require(not key.startswith(('tasks/', 'memory/', 'ontology/', 'control_records/', '.sys4ai/', '.git/')),
                    'integration_owner', 'Canonical Task/knowledge/runtime writes retain their existing owner.')
            if item['before_sha256'] is not None: sha(item['before_sha256'])
            sha(item['after_sha256'])
            raw = read_exact(selected['candidate_root'], item['path']); total += len(raw)
            require(content_hash(raw) == item['after_sha256'] and total <= 8000000, 'candidate_changed', 'Candidate bytes changed or exceed the selected bound.')
        require(type(selected['checks']) is list and len(selected['checks']) <= 100, 'integration_checks', 'Select at most 100 fixed owner checks.')
        for check in selected['checks']:
            exact(check, ('owner', 'path')); relative(check['path'])
            require(check['owner'] in ('task', 'memory', 'ontology', 'python-syntax'), 'validator_unselected', 'Only fixed owner validation routes are supported.')
        return selected

    def _head(self, selected):
        current = self.coordination.checkout.head()
        require(all(current[k] == selected['snapshot'][k] for k in ('branch', 'commit', 'tree')),
                'head_changed', 'Selected branch, commit or tree changed; preserve the current Git history.')
        return current

    def predecessor(self, selected, path, *, recovering=False):
        item = next(x for x in selected['files'] if x['path'] == path)
        actual = read_exact(self.root, path, missing=True)
        if not recovering:
            require(content_hash(actual) == item['before_sha256'], 'target_changed', 'Original target changed after review.')
            return actual
        journal_path = 'control_records/curator/integration/' + selected['operation_id'] + '.json'
        journal = json.loads(read_exact(self.root, journal_path))
        require(journal['selection_sha256'] == digest(selected), 'recovery_changed', 'Original integration selection changed.')
        original = next(x for x in journal['files'] if x['path'] == path)
        try: raw = None if original['before_base64'] is None else base64.b64decode(original['before_base64'], validate=True)
        except (ValueError, KeyError) as exc: raise ValueError('Original integration predecessor is unavailable.') from exc
        require(content_hash(raw) == item['before_sha256'] and content_hash(actual) in (item['before_sha256'], item['after_sha256']),
                'recovery_changed', 'Original predecessor or current target differs from the accepted operation.')
        return raw

    def _inputs(self, selected):
        for ref in selected['source_refs']:
            exact(ref, ('path', 'sha256'))
            require(content_hash(read_exact(self.root, ref['path'])) == ref['sha256'], 'source_changed', 'Review source changed.')

    def _checks(self, selected):
        results = []
        for check in selected['checks']:
            owner, path = check['owner'], check['path']
            if owner == 'task':
                _, errors, _ = self.coordination.task.validate_task_folder(self.root / path)
                require(not errors, 'integrated_invalid', 'Integrated Task owner check failed.')
            elif owner == 'python-syntax': compile(read_exact(self.root, path), path, 'exec', dont_inherit=True)
            elif owner == 'memory':
                require(self.memory_core is not None, 'owner_unavailable', 'Memory owner is not selected.')
                config = self.memory_core.load_config(self.root)
                self.memory_core.load_records(self.root, config)
            else:
                require(self.ontology_core is not None and self.ontology_validate is not None, 'owner_unavailable', 'Ontology owner is not selected.')
                result = self.ontology_validate.validate_project(self.ontology_core.load_project(self.root), require_current=True)
                require(result['valid'] is True, 'integrated_invalid', 'Integrated ontology owner check failed.')
            results.append({'owner': owner, 'path': path, 'state': 'passed'})
        return results

    def _initial_journal(self, selected, actor, task_binding):
        return {'schema_version': 1, 'operation_id': selected['operation_id'], 'selection_sha256': digest(selected), 'actor': actor,
                           'task': {k: task_binding[k] for k in ('task_id', 'execution_id', 'generation')},
                           'head': {k:selected['snapshot'][k] for k in ('branch','commit','tree')},
                           'index_sha256': selected['snapshot']['index_sha256'], 'index_identity_sha256': selected['snapshot']['index_identity_sha256'],
                           'state': 'pending', 'files': [dict(x, state='pending', before_base64=None if x['before_sha256'] is None else
                               base64.b64encode(self.predecessor(selected, x['path'])).decode()) for x in selected['files']], 'checks': []}

    def preflight_journal(self, selected, *, actor, task_binding, recovering=False):
        if recovering:
            raw = read_exact(self.root, 'control_records/curator/integration/' + selected['operation_id'] + '.json')
            journal = json.loads(raw)
            require(journal['selection_sha256'] == digest(selected), 'recovery_changed', 'Original journal selection differs.')
        else:
            journal = self._initial_journal(selected, actor, task_binding)
        self._journal_budget(selected, journal)

    def _journal_budget(self, selected, journal):
        # The complete success edition is the largest fixed record shape. SHA
        # fields keep their width; False is the longer possible dirty boolean.
        planned = copy.deepcopy(journal)
        planned['state'] = 'complete'
        for item in planned['files']: item['state'] = 'committed'
        planned['checks'] = [dict(check, state='passed') for check in selected['checks']]
        planned['final_snapshot'] = copy.deepcopy(selected['snapshot'])
        planned['final_snapshot']['dirty'] = False
        owner_result = {**planned, 'journal_path': 'control_records/curator/integration/' + selected['operation_id'] + '.json',
                        'journal_sha256': '0'*64, 'git_actions': []}
        require(max(len(canonical(planned)), len(canonical(owner_result))) <= 2000000, 'integration_journal_budget',
                'The complete journal, checks and final snapshot exceed the existing owner byte bound.')

    def execute(self, payload, *, actor, task_binding, recovering=False, fault=None):
        if recovering:
            exact(payload, ('candidate_id', 'original_operation_id'))
            require(payload['original_operation_id'] == payload['candidate_id'], 'recovery_changed', 'Select the exact original integration operation.')
        selected = self._selected({'candidate_id': payload['candidate_id']}) if recovering else self._selected(payload)
        op = selected['operation_id']; path = 'control_records/curator/integration/' + op + '.json'
        with self.coordination.serialized():
            require(self.coordination.owners([x['path'] for x in selected['files']], actor=actor, task_binding=task_binding)['state'] == 'clear',
                    'owner_conflict', 'Current overlapping or uncertain owners must reconcile first.')
            self._head(selected); self._inputs(selected)
            raw_journal = read_exact(self.root, path, missing=True)
            journal = None if raw_journal is None else json.loads(raw_journal)
            if journal is None:
                require(not recovering, 'original_missing', 'Recovery requires the original durable operation.')
                current = self.coordination.checkout.snapshot()
                require(current == selected['snapshot'], 'snapshot_changed', 'Checkout, branch or index changed after review.')
                for item in selected['files']:
                    require(content_hash(read_exact(self.root, item['path'], missing=True)) == item['before_sha256'], 'target_changed', 'Target changed after review.')
                journal = self._initial_journal(selected, actor, task_binding)
                self._journal_budget(selected, journal)
                replace_exact(self.root, path, canonical(journal), None)
            else:
                require(journal['head'] == {k:selected['snapshot'][k] for k in ('branch','commit','tree')},
                        'head_changed', 'Original integration journal binds a different Git version.')
                require(journal['selection_sha256'] == digest(selected) and journal['actor'] == actor
                        and journal['task'] == {k: task_binding[k] for k in ('task_id', 'execution_id', 'generation')},
                        'recovery_changed', 'Retry must retain exact original source, selection and current execution owner.')
                require(recovering or journal['state'] == 'complete', 'recovery_required', 'Pending integration needs the explicit recovery route.')
            self._journal_budget(selected, journal)
            snapshot = self.coordination.checkout.snapshot()
            require(snapshot['index_sha256'] == journal['index_sha256'] and snapshot['index_identity_sha256'] == journal['index_identity_sha256'],
                    'index_changed', 'Index edits invalidate integration or recovery.')
            for index, item in enumerate(journal['files']):
                current = content_hash(read_exact(self.root, item['path'], missing=True))
                require(current in (item['before_sha256'], item['after_sha256']), 'later_edit', 'Unexpected later edits are preserved.')
                require(item['state'] != 'committed' or current == item['after_sha256'], 'later_edit', 'Previously integrated content was changed.')
                if current != item['after_sha256']:
                    if fault: fault('before_replace_' + str(index))
                    self._inputs(selected)
                    self._head(selected)
                    candidate_bytes = read_exact(selected['candidate_root'], item['path'])
                    require(content_hash(candidate_bytes) == item['after_sha256'], 'candidate_changed', 'Candidate changed at the publication boundary.')
                    replace_exact(self.root, item['path'], candidate_bytes, item['before_sha256'])
                    if fault: fault('after_replace_' + str(index))
                self._head(selected)
                item['state'] = 'committed'
                old = read_exact(self.root, path); replace_exact(self.root, path, canonical(journal), content_hash(old))
            self._head(selected)
            journal['checks'] = self._checks(selected)
            self._inputs(selected)
            for item in journal['files']:
                require(content_hash(read_exact(self.root, item['path'])) == item['after_sha256'], 'integrated_changed', 'Integrated bytes changed during validation.')
            final = self.coordination.checkout.snapshot()
            require(final['index_sha256'] == journal['index_sha256'] and final['index_identity_sha256'] == journal['index_identity_sha256'], 'index_changed', 'Index changed during integration.')
            self._head(selected)
            journal['state'] = 'complete'; journal['final_snapshot'] = final
            old = read_exact(self.root, path); replace_exact(self.root, path, canonical(journal), content_hash(old))
            return {**journal, 'journal_path': path, 'journal_sha256': content_hash(canonical(journal)), 'git_actions': []}
