from pathlib import Path
import ast,json
r=Path.cwd();p=r/'SKILLS-depo/collaborate/scripts/collaboration_task.py';s=p.read_text();start=s.index('OWNER_PROFILE = {');end=s.index('\n\n\ndef provider_buffers',start);old=ast.literal_eval(s[s.index('{',start):end])
profiles={'current':{'files':old,'versions':[1,2]},'depot-v1':{'files':{'.agents/skills/agent-task/scripts/task_state.py':'b53bca05601b742b28bd9d8f87c4dcee0bb22500f210b21666a508e45440d604','.agents/skills/agent-task/scripts/orchestration_state.py':'9e2ad68ec90980c736ec5fc6bb1396aff0ea98e90918a20f3adc75b685546368','.agents/skills/manage-subagent-roles/scripts/role_catalog.py':'b649dc368d9b4f2d8eec032aaf2ae28e08ff493bbaf07d20ef21a55a52fd0cb2'},'versions':[1]}}
s=s[:start]+'OWNER_PROFILES = '+repr(profiles)+'\nOWNER_PROFILE = OWNER_PROFILES[\'current\'][\'files\']'+s[end:]
a=s.index('def provider_buffers(');b=s.index('\n\ndef task_module',a)
s=s[:a]+'''def provider_profile(root):
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
'''+s[b:]
s=s.replace('buffers = provider_buffers(root)  # Recheck actual bytes before using cached code.\n    key = str(Path(root).absolute())',"profile_name, buffers = provider_profile(root)  # Recheck actual bytes before using cached code.\n    key = str(Path(root).absolute()) + '|' + profile_name")
s=s.replace('owner_interface(loaded)\n            _TASK_MODULES[key]',"loaded._collaboration_profile = profile_name\n            owner_interface(loaded)\n            _TASK_MODULES[key]")
s=s.replace("names = ('versioned', 'producer'", "names = ('producer'")
s=s.replace("require(orch is not None and all(callable(getattr(orch, name, None)) for name in names), 'COLLAB_OWNER_UNSUPPORTED')", "require(orch is not None and all(callable(getattr(orch, name, None)) for name in names), 'COLLAB_OWNER_UNSUPPORTED')\n    profile = getattr(owner, '_collaboration_profile', 'current')\n    require(profile in OWNER_PROFILES, 'COLLAB_OWNER_UNSUPPORTED')\n    if profile == 'current':\n        require(callable(getattr(orch, 'versioned', None)), 'COLLAB_OWNER_UNSUPPORTED')")
s=s.replace("self.o = self.task['orchestration']", "self.o = self.task['orchestration']\n            self.profile = self.owner._collaboration_profile\n            require(self.o.get('version', 1) in OWNER_PROFILES[self.profile]['versions'], 'COLLAB_OWNER_UNSUPPORTED')")
a=s.index('    def validate_actor(self):');b=s.index('\n    def current(self):',a)
s=s[:a]+'''    def validate_actor(self):
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
'''+s[b:]
s=s.replace('        @self.orch.versioned\n        def invoke(task):', '        def invoke(task):')
s=s.replace('            return invoke(self.task)', "            return (self.orch.versioned(invoke) if self.profile == 'current' else invoke)(self.task)")
p.write_text(s)
print('Added exact depot-v1 provider adapter; current/version2 owner dispatch remains versioned.')
