"""Read-only adapter to the actual installed Task owner, without schema extension."""
from __future__ import annotations
import importlib.util
import builtins
import types
import json
from pathlib import Path
from threading import Lock
from collaboration_store import CollaborationError, digest, exact, identifier, parts, read_bytes, reference, require

_TASK_MODULES = {}
_TASK_LOCK = Lock()
# Exact reviewed read-owner profile. Unknown/custom editions are never imported.
OWNER_PROFILES = {'current': {'files': {'.agents/skills/agent-task/scripts/task_state.py': '90c077df7c725b9ed260aaddfcbdf7e5b65e36a7d8d2ba8fb2f02ad8a3f25556', '.agents/skills/agent-task/scripts/orchestration_state.py': 'd4901e205c1ed23f9f11a7da5043883dd2df6c8f4e168830ab46913dbc2965f8', '.agents/skills/agent-task/scripts/native_observations.py': 'cc3bf1eaad4ac248c44c84da356d35a9a8186a181d214ff3fb15ed0ca0436e31', '.agents/skills/manage-subagent-roles/scripts/role_catalog.py': 'b649dc368d9b4f2d8eec032aaf2ae28e08ff493bbaf07d20ef21a55a52fd0cb2'}, 'versions': [1, 2]}, 'depot-v1': {'files': {'.agents/skills/agent-task/scripts/task_state.py': 'b53bca05601b742b28bd9d8f87c4dcee0bb22500f210b21666a508e45440d604', '.agents/skills/agent-task/scripts/orchestration_state.py': '9e2ad68ec90980c736ec5fc6bb1396aff0ea98e90918a20f3adc75b685546368', '.agents/skills/manage-subagent-roles/scripts/role_catalog.py': 'b649dc368d9b4f2d8eec032aaf2ae28e08ff493bbaf07d20ef21a55a52fd0cb2'}, 'versions': [1]}}
OWNER_PROFILE = OWNER_PROFILES['current']['files']


def provider_profile(root):
    """Exact whole reviewed provider edition; never compose pins across profiles."""
    for name, profile in OWNER_PROFILES.items():
        try:
            buffers = {str(Path(root) / raw): read_bytes(root, raw) for raw in profile['files']}
            if all(digest(buffers[str(Path(root) / raw)]) == expected for raw, expected in profile['files'].items()):
                return name, buffers
        except (CollaborationError, OSError):
            continue
    raise CollaborationError('COLLAB_OWNER_UNSUPPORTED')


def provider_buffers(root):
    return provider_profile(root)[1]


def task_module(root):
    """Load only frozen, reviewed bytes from the selected project's actual owner."""
    profile_name, buffers = provider_profile(root)  # Recheck actual bytes before using cached code.
    key = str(Path(root).absolute()) + '|' + profile_name
    with _TASK_LOCK:
        if key not in _TASK_MODULES:
            def controlled_import(name, globals=None, locals=None, fromlist=(), level=0):
                if name == 'importlib.util':
                    return util if fromlist else types.SimpleNamespace(util=util)
                return builtins.__import__(name, globals, locals, fromlist, level)

            class FrozenLoader:
                def __init__(self, path): self.path = path
                def create_module(self, spec): return None
                def exec_module(self, module):
                    module.__file__ = self.path
                    module.__dict__['__builtins__'] = {**vars(builtins), '__import__': controlled_import}
                    exec(compile(buffers[self.path], self.path, 'exec'), module.__dict__)

            def frozen_spec(name, location):
                path = str(Path(location).absolute())
                require(path in buffers, 'COLLAB_OWNER_UNSUPPORTED')
                return importlib.util.spec_from_loader(name, FrozenLoader(path), origin=path)

            util = types.SimpleNamespace(spec_from_file_location=frozen_spec, module_from_spec=importlib.util.module_from_spec)
            source = str(Path(root) / '.agents/skills/agent-task/scripts/task_state.py')
            spec = frozen_spec('collaboration_task_owner_' + digest(key.encode()), source)
            loaded = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(loaded)
            loaded._collaboration_profile = profile_name
            owner_interface(loaded)
            _TASK_MODULES[key] = loaded
        return _TASK_MODULES[key]


def owner_interface(owner):
    """Reject unsupported owner editions before any Task/actor gate is invoked."""
    require(callable(getattr(owner, 'validate_state_shape', None)), 'COLLAB_OWNER_UNSUPPORTED')
    orch = getattr(owner, 'orch', None)
    names = ('producer', 'current_subtask', 'require_input_packet',
             'role', 'role_reads', 'candidate_set', 'candidate_current',
             'evidence_current', 'review_set', 'synthesis_current',
             'acceptance_current', 'verified_current')
    require(orch is not None and all(callable(getattr(orch, name, None)) for name in names), 'COLLAB_OWNER_UNSUPPORTED')
    profile = getattr(owner, '_collaboration_profile', 'current')
    require(profile in OWNER_PROFILES, 'COLLAB_OWNER_UNSUPPORTED')
    if profile == 'current':
        require(callable(getattr(orch, 'versioned', None)), 'COLLAB_OWNER_UNSUPPORTED')
    error_type = getattr(orch, 'OrchestrationError', None)
    require(isinstance(error_type, type) and issubclass(error_type, Exception), 'COLLAB_OWNER_UNSUPPORTED')
    return orch


class Context:
    def __init__(self, root, task_path, assignment, actor, execution, generation, policy):
        self.root = Path(root).absolute(); parts(task_path)
        require(task_path.endswith('/task.json') and task_path.startswith('Tasks/'), 'COLLAB_TASK')
        self.task_path = task_path; self.folder = self.root / Path(task_path).parent
        raw = read_bytes(self.root, task_path, 2000000)
        self.task_sha256 = digest(raw)
        try:
            self.task = json.loads(raw)
            self.owner = task_module(self.root); self.orch = owner_interface(self.owner)
            require(not self.owner.validate_state_shape(self.task, self.folder, raw.decode('utf-8')), 'COLLAB_TASK')
            require(self.task['schema_version'] == 2, 'COLLAB_LEGACY')
            self.o = self.task['orchestration']
            self.profile = self.owner._collaboration_profile
            require(self.o.get('version', 1) in OWNER_PROFILES[self.profile]['versions'], 'COLLAB_OWNER_UNSUPPORTED')
            require(self.o['execution_id'] == execution and type(generation) is int and self.o['generation'] == generation, 'COLLAB_STALE')
            self.a = self.call('producer', assignment)
            require(self.a['native_id'] == actor, 'COLLAB_IDENTITY')
            self.validate_actor()
            self.manager = assignment == self.o['manager_id'] and actor == self.o['writer']
            if self.a['subtask_id'] is not None:
                self.call('current_subtask', self.a['subtask_id'], self.task, self.root, self.folder)
                self.call('require_input_packet', self.a, self.task, self.root, self.folder)
            self.assignment = assignment; self.actor = actor
            self.policy_ref = policy
            data = reference(self.root, policy)
            self.policy = json.loads(data)
            self._policy()
        except (KeyError, TypeError, ValueError, OSError) as exc:
            if isinstance(exc, CollaborationError):
                raise
            raise CollaborationError('COLLAB_BINDING') from exc

    def validate_actor(self):
        def check(task):
            self.orch.role(self.a['role'], self.root)
            if self.profile == 'depot-v1':
                # The pinned v1 owner acknowledges its role pair; it does not
                # expose the v2 current-input acknowledgement API. Preserve
                # that distinction and recheck actual bound input bytes.
                self.orch.role_reads(self.a, self.a['role_reads'])
                for ref in self.a['context']:
                    reference(self.root, ref)
            else:
                self.orch.role_reads(self.a, self.a['role_reads'], current_input=True)
        try:
            (self.orch.versioned(check) if self.profile == 'current' else check)(self.task)
        except (self.orch.OrchestrationError, ValueError, KeyError, OSError) as exc:
            raise CollaborationError('COLLAB_IDENTITY') from exc

    def current(self):
        require(task_module(self.root) is self.owner, 'COLLAB_OWNER_UNSUPPORTED')
        require(digest(read_bytes(self.root, self.task_path, 2000000)) == self.task_sha256, 'COLLAB_STALE')
        reference(self.root, self.policy_ref)
        self.validate_actor()

    def call(self, name, *args):
        # Preserve the selected protected version 2 live-context requirements.
        def invoke(task):
            return getattr(self.orch, name)(task['orchestration'], *args)
        try:
            return (self.orch.versioned(invoke) if self.profile == 'current' else invoke)(self.task)
        except (self.orch.OrchestrationError, ValueError, KeyError, OSError) as exc:
            raise CollaborationError('COLLAB_GATE') from exc

    def scope(self, raw, mode='reads'):
        parts(raw)
        return any(raw == p or raw.startswith(p.rstrip('/') + '/') for p in self.a['fit'][mode])

    def writable(self, raw):
        self.current()
        require(self.a['state'] == 'active' and self.o['stage'] == 'active', 'COLLAB_LEASE')
        require(self.scope(raw, 'writes'), 'COLLAB_SCOPE')
        require(not any(raw == p or raw.startswith(p.rstrip('/') + '/') for p in ['AGENTS.md','ROLE.md','SOUL.md','SPECS.md','Roles','Tasks/INDEX.md',self.task_path]), 'COLLAB_SCOPE')
        if self.a['subtask_id']:
            for p in self.o['subtasks'][self.a['subtask_id']]['baseline']['protected']:
                require(raw != p and not raw.startswith(p.rstrip('/') + '/'), 'COLLAB_SCOPE')

    def _policy(self):
        p = self.policy
        exact(p, ('version','project','task','execution','generation','manager','participants','subtasks','bounds','topology'))
        require(p['version'] == 1 and type(p['version']) is int, 'COLLAB_VERSION')
        require((p['project'],p['task'],p['execution'],p['generation'],p['manager']) == (str(self.root),self.task['task_id'],self.o['execution_id'],self.o['generation'],self.o['manager_id']), 'COLLAB_BINDING')
        require(p['topology'] == 'common-store-cooperative', 'COLLAB_TOPOLOGY')
        matching = [art for art in self.o['artifacts'].values() if str(Path(self.task_path).parent / art['path']) == self.policy_ref['path'] and art['sha256'] == self.policy_ref['sha256']]
        require(len(matching) == 1 and matching[0]['assignment_id'] == self.o['manager_id'] and matching[0]['generation'] == self.o['generation'], 'COLLAB_POLICY')
        if self.manager:
            require(self.a['state'] in ('active','completed'),'COLLAB_OWNER')
        if not self.manager:
            st = self.o['subtasks'][self.a['subtask_id']]
            require(self.policy_ref in self.a['context'] and self.policy_ref in st['baseline']['inputs'], 'COLLAB_INPUT')
        require(type(p['participants']) is dict and self.assignment in p['participants'] and len(p['participants']) <= 200, 'COLLAB_POLICY')
        for aid, entry in p['participants'].items():
            identifier(aid); exact(entry, ('namespace','subtask_id')); parts(entry['namespace'])
            require(entry['namespace'].endswith('/collaboration'), 'COLLAB_NAMESPACE')
            if aid in self.o['assignments']:
                a = self.o['assignments'][aid]
                require(a['subtask_id'] == entry['subtask_id'] and a['generation'] == self.o['generation'], 'COLLAB_STALE')
                require(any(entry['namespace'] == w or entry['namespace'].startswith(w.rstrip('/')+'/') for w in a['fit']['writes']), 'COLLAB_SCOPE')
                if a['function'] in ('solver','reviewer','senior'):
                    expected = str(Path(self.task_path).parent / 'artifacts/orchestration/work' / aid / 'collaboration')
                    require(entry['namespace'] == expected, 'COLLAB_NAMESPACE')
        self.namespace = p['participants'][self.assignment]['namespace']
        require(type(p['subtasks']) is dict, 'COLLAB_POLICY')
        for sid, rule in p['subtasks'].items():
            identifier(sid); exact(rule, ('phase','audience','independent_first_pass','reviewer_first_pass','exchange_stop'))
            require(rule['phase'] in ('independent','peer-exchange','review','component','integration'), 'COLLAB_PHASE')
            require(type(rule['independent_first_pass']) is bool and type(rule['reviewer_first_pass']) is bool, 'COLLAB_POLICY')
            require(type(rule['audience']) is list and set(rule['audience']) <= set(p['participants']) and len(rule['audience']) <= 200, 'COLLAB_AUDIENCE')
            require(isinstance(rule['exchange_stop'], str) and 0 < len(rule['exchange_stop']) <= 2000, 'COLLAB_POLICY')
        exact(p['bounds'], ('record_bytes','output_bytes','page_items'))
        for key, cap, minimum in [('record_bytes',250000,1024),('output_bytes',32768,512),('page_items',200,1)]:
            require(type(p['bounds'][key]) is int and minimum <= p['bounds'][key] <= cap, 'COLLAB_BOUND')

    def binding(self):
        return dict(version=1, project=str(self.root), task=self.task['task_id'], execution=self.o['execution_id'], generation=self.o['generation'], assignment=self.assignment, native_id=self.actor, policy_sha256=self.policy_ref['sha256'])

    def candidates(self, sid):
        return self.call('candidate_set', sid, self.task, self.root, self.folder)

    def first_review(self, aid):
        a = self.call('producer', aid, 'reviewer')
        st = self.o['subtasks'][a['subtask_id']]
        slot = next(x for x in st['baseline']['slots'] if x['slot'] == a['slot'])
        # Superseded reviews are preserved history, not the recipient's current
        # first assessment. Select the exact current assigned candidate first.
        candidates = [c for c in self.o['candidates'].values()
                      if self.o['assignments'][c['assignment_id']]['subtask_id'] == a['subtask_id']
                      and self.o['assignments'][c['assignment_id']]['slot'] == slot['solver_slot']
                      and c['baseline'] == st['digest'] and c['round'] == st['round']
                      and not any(n['supersedes'] == c['candidate_id'] for n in self.o['candidates'].values())]
        require(len(candidates) == 1, 'COLLAB_GATE')
        candidate = candidates[0]
        self.call('candidate_current', candidate['candidate_id'], self.task, self.root, self.folder)
        reviews = [r for r in self.o['reviews'].values()
                   if r['assignment_id'] == aid and r['candidate_id'] == candidate['candidate_id']
                   and r['baseline'] == st['digest'] and r['round'] == st['round']]
        if not reviews:
            return False
        self.call('evidence_current', reviews[-1]['findings'], self.folder)
        return True

    def eligibility(self, sid):
        """Current canonical gates; no communication field manufactures a pass."""
        self.call('current_subtask', sid, self.task, self.root, self.folder)
        category = self.o['subtasks'][sid]['baseline']['category']
        if category == 'generic':
            return {'category':category,'candidates':[],'reviews':[]}
        cids = self.candidates(sid)
        rids = self.call('review_set',sid,cids,self.root,self.folder)
        current = [syn for syn in self.o['syntheses'].values() if self.o['assignments'][syn['assignment_id']]['subtask_id'] == sid and syn['baseline'] == self.o['subtasks'][sid]['digest'] and syn['round'] == self.o['subtasks'][sid]['round'] and set(syn['candidate_ids']) == set(cids) and set(syn['review_ids']) == set(rids)]
        if current:
            selected = current[-1]
            self.call('synthesis_current', selected['synthesis_id'], self.task,self.root,self.folder)
            accepted = [x for x in self.o['acceptances'].values() if x['synthesis_id'] == selected['synthesis_id']]
            if accepted: self.call('acceptance_current', accepted[-1]['acceptance_id'],self.task,self.root,self.folder)
        return {'category':category,'candidates':cids,'reviews':rids}
