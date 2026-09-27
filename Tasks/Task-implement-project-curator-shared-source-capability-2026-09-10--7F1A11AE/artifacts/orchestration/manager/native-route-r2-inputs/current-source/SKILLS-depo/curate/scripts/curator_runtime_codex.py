"""Pinned Codex App Server stdio adapter; raw transport is never a model tool."""
from collections import deque
import ctypes
import hashlib
import json
import os
from pathlib import Path
import selectors
import select
import signal
import subprocess
import sys
import time

from curator_policy import PolicyError, canonical, digest, exact, require
from curator_confinement import verify_manifest

METHOD_SCHEMAS = {
    'initialize': ('InitializeParams', 'InitializeResponse'),
    'config/read': ('ConfigReadParams', 'ConfigReadResponse'),
    'model/list': ('ModelListParams', 'ModelListResponse'),
    'thread/start': ('ThreadStartParams', 'ThreadStartResponse'),
    'thread/read': ('ThreadReadParams', 'ThreadReadResponse'),
    'thread/list': ('ThreadListParams', 'ThreadListResponse'),
    'thread/resume': ('ThreadResumeParams', 'ThreadResumeResponse'),
    'turn/start': ('TurnStartParams', 'TurnStartResponse'),
    'turn/steer': ('TurnSteerParams', 'TurnSteerResponse'),
    'turn/interrupt': ('TurnInterruptParams', 'TurnInterruptResponse'),
}

DISABLED_FEATURES = ('apps','plugins','hooks','memories','chronicle','image_generation',
    'browser_use','browser_use_external','computer_use','in_app_browser','remote_plugin','goals',
    'browser_use_full_cdp_access','enable_mcp_apps','realtime_conversation','code_mode',
    'code_mode_host','code_mode_only','code_mode_prewarm','code_mode_interrupt','plugin_sharing',
    'recommended_plugins','skill_mcp_dependency_install','in_app_local_automation','in_app_chat',
    'tool_suggest','auth_elicitation','shell_snapshot','view_image')
DESKTOP_UI_KEYS = frozenset(('conversationDetailMode','show-context-window-usage','toys-confetti-enabled',
    'appearanceLightChromeTheme','appearanceDarkChromeTheme','toys-audio-visualizer-enabled',
    'microphoneInputDeviceId','enabled-reasoning-efforts','followUpQueueMode','avatar-overlay-mascot-width-px',
    'selected-avatar-id','keepRemoteControlAwakeWhilePluggedIn','preventSleepWhileRunning',
    'open-in-target-preferences','appearanceLightCodeThemeId','appearanceDarkCodeThemeId',
    'realtimeVoiceScreenContextEnabled','dock-icon-preference'))


def shape(value, schema, definitions, depth=0):
    """Validate only generated schema constructs used by the pinned wire protocol."""
    require(depth <= 64, 'wire_depth', 'Native value is too deeply nested.')
    if schema is True: return
    require(schema is not False and type(schema) is dict, 'wire_schema', 'Unsupported schema.')
    if '$ref' in schema:
        parts = schema['$ref'].split('/')[2:]; selected = definitions
        for part in parts: selected = selected[part]
        return shape(value, selected, definitions, depth + 1)
    for union in ('oneOf', 'anyOf'):
        if union in schema:
            accepted = 0
            for branch in schema[union]:
                try: shape(value, branch, definitions, depth + 1); accepted += 1
                except PolicyError: pass
            require(accepted == 1 if union == 'oneOf' else accepted > 0, 'wire_union', 'Native value does not match schema union.')
    for branch in schema.get('allOf', []): shape(value, branch, definitions, depth + 1)
    if 'enum' in schema: require(value in schema['enum'], 'wire_enum', 'Unsupported native enum.')
    kind = schema.get('type')
    if kind is not None:
        kinds = kind if isinstance(kind, list) else [kind]
        valid = any((k == 'null' and value is None) or (k == 'string' and type(value) is str)
                    or (k == 'object' and type(value) is dict) or (k == 'array' and type(value) is list)
                    or (k == 'integer' and type(value) is int) or (k == 'number' and type(value) in (int, float))
                    or (k == 'boolean' and type(value) is bool) for k in kinds)
        require(valid, 'wire_type', 'Native field type differs.')
    if type(value) is dict and any(k in schema for k in ('properties', 'required', 'additionalProperties', 'type')):
        properties = schema.get('properties', {})
        require(set(schema.get('required', [])) <= set(value), 'wire_fields', 'Required native field missing.')
        if schema.get('additionalProperties', False) is False:
            require(set(value) <= set(properties), 'wire_fields', 'Unknown native field.')
        for key, item in value.items():
            if key in properties: shape(item, properties[key], definitions, depth + 1)
            elif isinstance(schema.get('additionalProperties'), dict):
                shape(item, schema['additionalProperties'], definitions, depth + 1)
    if type(value) is list:
        require(len(value) <= 10000, 'wire_size', 'Native array exceeds bound.')
        for item in value: shape(item, schema.get('items', True), definitions, depth + 1)


class CodexAdapter:
    def __init__(self, executable, schema_root, trusted_manifest, native_helper, *, cwd, environment,
                 config_overrides=(), deadline_seconds=60, max_frame_bytes=2000000, absolute_deadline=None,
                 companion=None):
        self.executable = str(Path(executable).resolve(strict=True))
        self.schema_root = Path(schema_root).resolve(strict=True)
        self.manifest = trusted_manifest; self.native = native_helper
        self.cwd = str(Path(cwd).resolve(strict=True)); self.environment = dict(environment)
        require(not set(environment) & {'PYTHONPATH','PYTHONSTARTUP','BASH_ENV','ENV','DYLD_INSERT_LIBRARIES','LD_PRELOAD'},
                'environment', 'Unsafe broker/runtime environment override.')
        self.config_overrides = tuple(config_overrides)
        require(all(type(x) is str and '\x00' not in x for x in self.config_overrides), 'config', 'Invalid trusted startup configuration.')
        require(type(deadline_seconds) is int and 0 < deadline_seconds <= 60, 'deadline', 'Use bounded I/O waits.')
        self.deadline_seconds = deadline_seconds; self.max_frame_bytes = max_frame_bytes
        self.absolute_deadline = absolute_deadline; self.stopping = False
        self.received_bytes = 0; self.max_transport_bytes = 64000000; self.pending_methods = {}
        self.process = None; self.sequence = 0; self.request_id = 0; self.buffer = b''
        self.events = []; self.pending_calls = deque(); self.responses = {}; self.threads = {}; self.turns = {}
        self.authority = None; self.dispatch = None; self.raw_frames = {}
        self.launch_settings = {}; self.effective = {}; self.bootstrap_profile = None
        self.method_counts = {}; self.request_counts = {}
        self.companion = dict(companion) if companion and companion.get('enabled') is True else None
        self.companion_observations = {}; self._owned_processes = {}; self._last_process_poll = 0
        self.companion_verified = False; self.companion_identity_uncertain = False; self._server_identity = None
        if self.companion:
            require(self.companion.get('disable_in_process_fallback') is True and self.companion.get('remote_url') is None,
                    'companion_binding','Only the selected local standalone companion with fallback disabled is admitted.')
            self.companion['path']=str(Path(self.companion['path']).resolve(strict=True))
            self._verify_companion_file()
            own=self._kernel_identity(os.getpid())
            require(own is not None and own['parent']==os.getppid() and own['group']==os.getpgrp() and own['uid']==os.getuid(),
                    'kernel_identity_unavailable','Kernel process identity self-check failed.')
        aggregate = self.schema_root / 'codex_app_server_protocol.v2.schemas.json'
        self.definitions = json.loads(aggregate.read_text())['definitions']
        self.schemas = {}
        for name in {x for pair in METHOD_SCHEMAS.values() for x in pair}:
            files = list(self.schema_root.rglob(name + '.json'))
            require(len(files) == 1, 'schema_unavailable', 'Pinned method schema is missing or ambiguous: ' + name)
            self.schemas[name] = json.loads(files[0].read_text())

    def _validate(self, name, value):
        schema = self.schemas[name]
        shape(value, schema, schema.get('definitions', self.definitions))

    def _verify_companion_file(self):
        from curator_confinement import file_snapshot
        expected=self.companion
        require(file_snapshot('/',expected['path'].lstrip('/'),250000000)['sha256']==expected['sha256'],
                'companion_changed','Pinned standalone companion executable changed.')

    def _process_snapshot(self):
        # Only process metadata is read. Arguments/environment are never requested.
        result=subprocess.run(['/bin/ps','-ax','-o','pid=,ppid='],
            capture_output=True,text=True,timeout=min(2,self._remaining()))
        require(result.returncode==0 and len(result.stdout)<=2000000,'process_observation_unavailable','Bounded kernel process observation is unavailable.')
        rows={}
        for line in result.stdout.splitlines():
            fields=line.split()
            if len(fields)!=2:continue
            try:pid,parent=map(int,fields)
            except ValueError:continue
            rows[pid]={'pid':pid,'parent':parent}
        return rows

    def _kernel_identity(self, pid):
        require(sys.platform=='darwin','kernel_identity_unavailable','This companion tracker requires the verified Darwin kernel interface.')
        class BSDInfo(ctypes.Structure):
            _fields_=[(name,ctypes.c_uint32) for name in ('flags','status','xstatus','pid','ppid','uid','gid','ruid','rgid','svuid','svgid','reserved')]+[
                ('comm',ctypes.c_char*16),('name',ctypes.c_char*32)]+[(name,ctypes.c_uint32) for name in ('nfiles','pgid','pjobc','tdev','tpgid')]+[
                ('nice',ctypes.c_int32),('start_seconds',ctypes.c_uint64),('start_microseconds',ctypes.c_uint64)]
        require(ctypes.sizeof(BSDInfo)==136,'kernel_identity_unavailable','Kernel ABI differs from the inspected SDK declaration.')
        library=ctypes.CDLL('/usr/lib/libproc.dylib')
        library.proc_pidinfo.argtypes=[ctypes.c_int,ctypes.c_int,ctypes.c_uint64,ctypes.c_void_p,ctypes.c_int]
        library.proc_pidinfo.restype=ctypes.c_int
        library.proc_pidpath.argtypes=[ctypes.c_int,ctypes.c_void_p,ctypes.c_uint32]
        library.proc_pidpath.restype=ctypes.c_int
        info=BSDInfo();path=ctypes.create_string_buffer(4096)
        if library.proc_pidinfo(pid,3,0,ctypes.byref(info),ctypes.sizeof(info))!=ctypes.sizeof(info):return None
        if library.proc_pidpath(pid,path,len(path))<=0:return None
        require(info.pid==pid,'kernel_identity_unavailable','Kernel returned a different process identity.')
        return {'pid':pid,'parent':info.ppid,'group':info.pgid,'uid':info.uid,
            'started':[info.start_seconds,info.start_microseconds],'executable':os.fsdecode(path.value)}

    def _owned_kernel_identity(self, pid):
        initial=self._kernel_identity(pid)
        if initial is None:return None
        chain={};current=initial
        for _ in range(16):
            if current['pid'] in chain:break
            chain[current['pid']]=current
            if current['pid']==self.process.pid:
                if current!=self._server_identity:break
                # Recheck every microsecond start/parent/image binding before
                # recording ownership; a ps candidate is never authority.
                if all(self._kernel_identity(key)==value for key,value in chain.items()):return initial
                break
            current=self._kernel_identity(current['parent'])
            if current is None:break
        self.companion_identity_uncertain=True
        return None

    def _observe_companion(self, force=False):
        if not self.companion or not self.process or self.process.poll() is not None:return
        now=time.monotonic()
        if not force and now-self._last_process_poll<0.2:return
        self._last_process_poll=now
        rows=self._process_snapshot();owned={self.process.pid}
        for _ in range(16):
            found={pid for pid,row in rows.items() if row['parent'] in owned}
            if found<=owned:break
            owned.update(found)
            require(len(owned)<=128,'process_bound','Owned process observation bound reached.')
        for pid in owned-{self.process.pid}:
            row=self._owned_kernel_identity(pid)
            if row is None:continue
            if row['parent']!=rows[pid]['parent']:
                self.companion_identity_uncertain=True
                continue
            require(row['uid']==os.getuid(),'process_identity_unavailable','Owned process has an unexpected user identity.')
            self._owned_processes[pid]=row
            if Path(row['executable']).name=='codex-code-mode-host':
                require(str(Path(row['executable']).resolve(strict=True))==self.companion['path'],
                        'companion_mismatch','A test-owned code-mode host resolved to an unselected executable.')
                self._verify_companion_file()
                self.companion_observations[pid]={**row,'sha256':self.companion['sha256']}
                self.companion_verified=True

    def _close_companion(self, deadline):
        if not self.companion:return None
        result={'observed':self.companion_verified,'processes':list(self.companion_observations.values()),'groups':[],'state':'uncertain'}
        groups={row['group'] for row in self._owned_processes.values()}-{self.process.pid}
        for group in sorted(groups):
            record={'group':group,'state':'uncertain'}
            while time.monotonic()<deadline:
                try:os.killpg(group,0)
                except ProcessLookupError:record['state']='stopped';break
                except PermissionError:record['code']='status_unavailable';break
                current={pid:self._kernel_identity(pid) for pid,old in self._owned_processes.items() if old['group']==group}
                # Never signal a reused or unbound group: at least one original
                # test-owned member must retain its start/executable identity.
                bound=any(current.get(pid) is not None and all(current[pid][key]==old[key] for key in ('group','uid','started','executable'))
                          for pid,old in self._owned_processes.items() if old['group']==group)
                if not bound:record['code']='identity_unconfirmed';break
                try:os.killpg(group,signal.SIGKILL)
                except ProcessLookupError:record['state']='stopped';break
                except PermissionError:record['code']='signal_denied';break
                time.sleep(min(0.05,max(0,deadline-time.monotonic())))
            result['groups'].append(record)
        result['identity_checks']=[]
        for pid,old in self.companion_observations.items():
            record={'pid':pid,'started':old['started'],'state':'uncertain'}
            try:os.kill(pid,0)
            except ProcessLookupError:record['state']='original_identity_absent'
            except PermissionError:record['code']='identity_status_unavailable'
            else:
                current=self._kernel_identity(pid)
                if current is not None and current['started']!=old['started']:
                    record['state']='original_identity_absent'
                else:
                    record['code']='original_helper_still_present' if current is not None else 'identity_unconfirmed'
                    # A surviving helper may have changed group or image.
                    # Do not authorize any newly observed group at cleanup.
            result['identity_checks'].append(record)
        result['identity_uncertain']=self.companion_identity_uncertain
        if self.companion_verified and not self.companion_identity_uncertain and all(row['state']=='stopped' for row in result['groups']) and all(row['state']=='original_identity_absent' for row in result['identity_checks']):
            result['state']='owned_companion_stopped'
        return result

    def start(self):
        require(self.process is None, 'transport_started', 'Transport already exists.')
        verify_manifest(self.manifest)
        argv = [self.executable, 'app-server']
        for override in self.config_overrides: argv.extend(['-c', override])
        self.process = subprocess.Popen(argv, cwd=self.cwd, env=self.environment,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            shell=False, close_fds=True, start_new_session=True, bufsize=0)
        os.set_blocking(self.process.stdin.fileno(), False)
        os.set_blocking(self.process.stdout.fileno(), False)
        os.set_blocking(self.process.stderr.fileno(), False)
        self.selector = selectors.DefaultSelector()
        self.selector.register(self.process.stdout, selectors.EVENT_READ, 'stdout')
        self.selector.register(self.process.stderr, selectors.EVENT_READ, 'stderr')
        if self.companion:
            self._server_identity=self._kernel_identity(self.process.pid)
            require(self._server_identity is not None and self._server_identity['parent']==os.getpid()
                    and self._server_identity['uid']==os.getuid() and self._server_identity['group']==self.process.pid
                    and self._server_identity['executable']==self.executable,
                    'server_identity_unavailable','New App Server kernel identity does not match this owned launch.')
        result = self._request('initialize', {'clientInfo': {'name':'sys4ai-curator','version':'1.0.0'},
            'capabilities': {'experimentalApi':True}})
        self._send({'method':'initialized'})
        return result

    def _remaining(self, deadline=None):
        ends = [time.monotonic() + self.deadline_seconds]
        if self.absolute_deadline is not None: ends.append(self.absolute_deadline)
        if deadline is not None: ends.append(deadline)
        remaining = min(ends) - time.monotonic()
        require(remaining > 0, 'native_deadline', 'Overall runtime deadline reached.')
        return remaining

    def begin_stop(self, deadline):
        self.stopping = True; self.absolute_deadline = deadline

    def _send(self, frame):
        require(self.process is not None and self.process.poll() is None, 'runtime_unavailable', 'App Server is not running.')
        raw = canonical(frame) + b'\n'
        require(len(raw) <= self.max_frame_bytes, 'wire_size', 'Request exceeds frame bound.')
        deadline = time.monotonic() + self._remaining()
        offset = 0
        while offset < len(raw):
            ready = select.select([], [self.process.stdin], [], min(1, self._remaining(deadline)))[1]
            if ready:
                try: offset += os.write(self.process.stdin.fileno(), raw[offset:])
                except BlockingIOError: continue

    def _receive(self, timeout):
        self._observe_companion()
        timeout = min(timeout, self._remaining())
        ready = self.selector.select(timeout)
        for key, _ in ready:
            raw = os.read(key.fileobj.fileno(), 65536)
            if not raw:
                self.selector.unregister(key.fileobj)
                continue
            if key.data == 'stderr':
                # Do not copy runtime diagnostics that could include account/config values.
                continue
            self.received_bytes += len(raw)
            require(self.received_bytes <= self.max_transport_bytes, 'transport_bound', 'Native transport byte bound reached.')
            self.buffer += raw
            require(len(self.buffer) <= self.max_frame_bytes, 'wire_size', 'Native frame exceeds selected limit.')
            while b'\n' in self.buffer:
                line, self.buffer = self.buffer.split(b'\n', 1)
                if not line: continue
                try: frame = json.loads(line)
                except (ValueError, RecursionError) as exc: raise PolicyError('wire_json', 'Malformed server frame.') from exc
                self.sequence += 1
                method = frame.get('method', 'response')
                if not isinstance(method, str) or len(method) > 100: method = 'unknown'
                self.method_counts[method] = self.method_counts.get(method, 0) + 1
                if self.pending_methods.get(frame.get('id')) != 'config/read':
                    self.raw_frames[self.sequence] = {'sha256':hashlib.sha256(line).hexdigest(), 'frame':frame}
                if 'method' not in frame and 'id' in frame:
                    self.responses[frame['id']] = frame
                elif frame.get('method') == 'item/tool/call' and 'id' in frame:
                    require(self.authority is not None, 'session_unbound', 'No selected native session.')
                    context = self.authority.capture(frame, self.sequence)
                    self.pending_calls.append((context, frame['params']['arguments']))
                elif 'id' in frame:
                    self._send({'id':frame['id'], 'error':{'code':-32601, 'message':'Unselected server request denied by Curator broker.'}})
                else:
                    self.events.append((self.sequence, frame))
                    params = frame.get('params', {})
                    if frame.get('method') == 'thread/started' and 'thread' in params:
                        self.threads[params['thread']['id']] = params['thread']
                    if frame.get('method') in ('turn/started','turn/completed'):
                        self.turns[params['threadId']] = params['turn']
        if self.process.poll() is not None:
            raise PolicyError('runtime_unavailable', 'App Server exited; reservations require reconciliation.')

    def pump(self, timeout=0):
        self._receive(min(timeout, self.deadline_seconds))
        while self.pending_calls:
            context, arguments = self.pending_calls.popleft()
            try:
                require(self.dispatch is not None, 'broker_unavailable', 'No selected dynamic owner dispatcher.')
                if self.companion:
                    self._observe_companion(force=True)
                    require(self.companion_verified,'companion_unproven','Actual test-owned standalone companion identity is unproven.')
                with self.authority.invoke(context):
                    result = self.dispatch(context, arguments)
                response = {'success':True,'contentItems':[{'type':'inputText','text':json.dumps(result, sort_keys=True)}]}
            except (PolicyError, self.native.NativeError) as exc:
                response = {'success':False,'contentItems':[{'type':'inputText','text':getattr(exc,'code','native_denied')}]}
            self._send({'id':context.request_id, 'result':response})
        return len(self.events)

    def _request(self, method, params):
        require(method in METHOD_SCHEMAS, 'method_denied', 'No raw protocol forwarding.')
        require(not self.stopping or method in ('turn/interrupt','thread/read'), 'stopped_admission', 'Only stop reconciliation is admitted.')
        self._remaining()
        self._validate(METHOD_SCHEMAS[method][0], params)
        verify_manifest(self.manifest)
        self.request_id += 1; identifier = self.request_id
        self.request_counts[method] = self.request_counts.get(method, 0) + 1
        self.pending_methods[identifier] = method
        self._send({'id':identifier, 'method':method, 'params':params})
        deadline = time.monotonic() + self._remaining()
        while identifier not in self.responses:
            require(time.monotonic() < deadline, 'native_uncertain', 'No correlated reply; retain the original operation.')
            self._receive(min(1, max(0, deadline - time.monotonic())))
        frame = self.responses.pop(identifier)
        self.pending_methods.pop(identifier, None)
        require('error' not in frame, 'native_error', 'Native request returned an error.')
        result = frame['result']; self._validate(METHOD_SCHEMAS[method][1], result)
        return result

    def inspect_tool_configuration(self, *, code_mode_host=False):
        require(type(code_mode_host) is bool,'tool_config','Trusted code-mode selection must be a boolean.')
        result = self._request('config/read', {'includeLayers':False, 'cwd':self.cwd})
        config = result['config']
        features = config.get('features', {})
        disabled = DISABLED_FEATURES
        require(isinstance(features, dict), 'tool_config_unavailable', 'Effective feature configuration is unavailable.')
        servers = config.get('mcp_servers', {})
        require(isinstance(servers, dict), 'tool_config_unavailable', 'Effective MCP configuration is unavailable.')
        safe = {'features':{name:features.get(name) for name in disabled},
                'delegation':{**{name:features.get(name) for name in ('multi_agent','multi_agent_v2')},
                    'agents_enabled':config.get('agents',{}).get('enabled') if isinstance(config.get('agents'),dict) else None},
                'mcp_servers':{name:value.get('enabled', True) if isinstance(value, dict) else None for name,value in servers.items()},
                'web_search':config.get('web_search')}
        host=features.get('code_mode_host')
        if isinstance(host,dict):safe['features']['code_mode_host']=host.get('enabled')
        self.tool_configuration = safe
        require(all(value is (code_mode_host if name=='code_mode_host' else False) for name,value in safe['features'].items()) and safe['web_search'] == 'disabled',
                'external_tools_unproven', 'An external tool feature is enabled or its effective state is unavailable.')
        safe['code_mode_host']={'enabled':host.get('enabled') if isinstance(host,dict) else None,
            'disable_in_process_fallback':host.get('disable_in_process_fallback') if isinstance(host,dict) else None}
        if code_mode_host:
            require(isinstance(host,dict) and set(host)<= {'enabled','disable_in_process_fallback'}
                    and safe['code_mode_host']=={'enabled':True,'disable_in_process_fallback':True},
                    'code_mode_host_unproven','Selected standalone code-mode host must fail closed without in-process fallback.')
        require(all(value is False for value in safe['mcp_servers'].values()), 'mcp_tools_enabled', 'Unselected MCP servers remain enabled.')
        browser = config.get('browser_use') or {}; computer = config.get('computer_use') or {}
        apps = config.get('apps') or {}; desktop = config.get('desktop') or {}; configured_tools = config.get('tools') or {}
        require(all(isinstance(value,dict) for value in (browser,computer,apps,desktop,configured_tools)),
                'tool_config_unavailable','Effective tool surface configuration is malformed.')
        default = browser.get('default_origin_policy') or {}
        deny = ('access','downloads','uploads','full_cdp_access')
        origins = browser.get('origins') or {}
        require(browser.get('allow_history_access') is False and isinstance(default,dict)
                and all(default.get(key)=='deny' for key in deny) and isinstance(origins,dict)
                and all(isinstance(rule,dict) and all(rule.get(key)=='deny' for key in deny) for rule in origins.values()),
                'browser_surface_unproven','Browser history and origin routes must be explicitly denied.')
        require(computer.get('default_app_access')=='deny','computer_surface_unproven','Computer app access must default to deny.')
        for platform,keys in (('macos',('bundle_ids',)),('windows',('aumids',))):
            selected=computer.get(platform) or {}
            require(isinstance(selected,dict),'computer_surface_unproven','Unexpected platform configuration.')
            for key in keys:
                values=selected.get(key) or {}
                require(isinstance(values,dict) and all(value=='deny' for value in values.values()),
                        'computer_surface_unproven','An application override permits computer access.')
            require(not selected.get('exes'),'computer_surface_unproven','Executable computer-access overrides are not selected.')
        app_default=apps.get('_default') or {}
        require(set(apps)<= {'_default'} and isinstance(app_default,dict)
                and all(app_default.get(key) is False for key in ('enabled','destructive_enabled','open_world_enabled')),
                'apps_surface_unproven','App tools must be explicitly disabled without per-app overrides.')
        require(set(desktop)<=DESKTOP_UI_KEYS and desktop.get('realtimeVoiceScreenContextEnabled') is False
                and desktop.get('keepRemoteControlAwakeWhilePluggedIn') is False,
                'desktop_surface_unproven','Unselected desktop routes or unknown desktop settings remain.')
        require(set(configured_tools)<= {'web_search'},'tools_surface_unproven','Unknown effective tool configuration.')
        safe['surfaces']={'browser_default':'deny','browser_history':False,'browser_origin_overrides':len(origins),
            'computer_default':'deny','apps_enabled':False,'desktop_voice_screen_context':False,
            'desktop_remote_awake':False,'desktop_ui_keys':sorted(desktop),'configured_tool_keys':sorted(configured_tools)}
        return safe

    def inspect_model(self, model, effort):
        result=self._request('model/list',{'includeHidden':True,'limit':100})
        require(result.get('nextCursor') is None,'model_catalog_unavailable','Selected bounded catalog is incomplete.')
        selected=[entry for entry in result['data'] if entry['model']==model]
        require(len(selected)==1 and any(value['reasoningEffort']==effort for value in selected[0]['supportedReasoningEfforts']),
                'model_unavailable','Exact selected model and effort are not advertised by this runtime.')
        return {'model':model,'effort':effort,'advertised':True,
                'multi_agent_version':selected[0].get('multiAgentVersion'),'provider_execution':'not_yet_observed'}

    def start_controller(self, *, model, effort, profile, dynamic_tools, instructions):
        require('allowProviderModelFallback' in self.schemas['ThreadStartParams']['properties'],
                'model_fallback_unavailable','Runtime cannot explicitly prohibit provider model substitution.')
        result = self._request('thread/start', {'model':model, 'permissions':profile, 'approvalPolicy':'never',
            'cwd':self.cwd, 'dynamicTools':dynamic_tools, 'baseInstructions':instructions,
            'config':{'model_reasoning_effort':effort}, 'ephemeral':True,'allowProviderModelFallback':False})
        thread = result['thread']; self.threads[thread['id']] = thread
        require(result['model'] == model and result['reasoningEffort'] == effort
                and isinstance(result.get('activePermissionProfile'), dict)
                and result['activePermissionProfile'].get('id') == profile,
                'settings_unproven', 'Controller effective settings/profile differ from exact selection.')
        self.bootstrap_profile = profile; self.effective[thread['id']] = result
        self.authority = self.native.TransportAuthority(thread['sessionId'])
        return result

    def observe(self, thread_id):
        require(thread_id in self.threads, 'native_unknown', 'Control is limited to bound native actors.')
        result = self._request('thread/read', {'threadId':thread_id,'includeTurns':False})
        self.threads[thread_id] = result['thread']; return result

    def list_bound(self):
        return {key:self.observe(key)['thread']['status'] for key in tuple(self.threads)}

    def select_child_profile(self, thread_id, profile, model, effort):
        require(thread_id in self.threads, 'native_unknown', 'Only an observed child may receive a profile.')
        observed=self.observe(thread_id)['thread']
        if 'model' in observed or 'reasoningEffort' in observed:
            require(observed.get('model')==model and observed.get('reasoningEffort')==effort,
                    'inheritance_mismatch','Read-only child settings differ before any resume or profile mutation.')
            require(observed.get('canAcceptDirectInput') is True,'direct_input_unavailable','Child does not expose the required direct-input route.')
        inherited = self._request('thread/resume', {'threadId':thread_id, 'excludeTurns':True})
        require(inherited['model'] == model and inherited['reasoningEffort'] == effort
                and isinstance(inherited.get('activePermissionProfile'), dict)
                and inherited['activePermissionProfile'].get('id') == self.bootstrap_profile,
                'inheritance_mismatch', 'Child launch settings or bootstrap profile differ; do not repair them in place.')
        self.launch_settings[thread_id] = inherited
        result = self._request('thread/resume', {'threadId':thread_id, 'permissions':profile,
            'excludeTurns':True})
        require(result['model'] == model and result['reasoningEffort'] == effort
                and isinstance(result.get('activePermissionProfile'), dict)
                and result['activePermissionProfile'].get('id') == profile,
                'settings_unproven', 'Effective settings/profile are unavailable or differ.')
        self.effective[thread_id] = result
        return result

    def followup(self, thread_id, text):
        require(thread_id in self.threads and type(text) is str, 'native_unknown', 'Only bound actors accept work.')
        result = self._request('turn/start', {'threadId':thread_id, 'input':[{'type':'text','text':text,'text_elements':[]}]})
        # A correlated start response is also an actual turn observation. Do not
        # overwrite a newer terminal notification received before that response.
        current = self.turns.get(thread_id)
        if current is None or current['id'] != result['turn']['id'] or current['status'] == 'inProgress':
            self.turns[thread_id] = result['turn']
        return result

    def message(self, thread_id, text):
        turn = self.turns.get(thread_id)
        require(turn and turn['status'] == 'inProgress', 'turn_unavailable', 'No observed active turn.')
        return self._request('turn/steer', {'threadId':thread_id, 'expectedTurnId':turn['id'],
            'input':[{'type':'text','text':text,'text_elements':[]}]})

    def interrupt(self, thread_id):
        turn = self.turns.get(thread_id)
        require(turn and turn['status'] == 'inProgress',
                'turn_unavailable', 'No observed active turn to interrupt.')
        return self._request('turn/interrupt', {'threadId':thread_id,'turnId':turn['id']})

    def receipt(self, sequence, *, child=None):
        frame = self.raw_frames[sequence]['frame']
        event = {k:frame[k] for k in ('method','params')}
        result = {'schema_version':1,'backend':'codex-app-server-v2','session_id':self.authority.session_id,
            'sequence':sequence,'raw_sha256':hashlib.sha256(canonical(event)).hexdigest(),'event':event}
        if child is not None:
            thread = self.threads[child]
            result['child'] = {k:thread[k] for k in ('id','parentThreadId','source')}
        return result

    def discover_child(self, sequence, parent):
        frame = self.raw_frames[sequence]['frame']; item = frame.get('params', {}).get('item', {})
        require(frame.get('method') == 'item/completed' and item.get('type') == 'collabAgentToolCall'
                and item.get('tool') == 'spawnAgent' and item.get('status') == 'completed'
                and item.get('senderThreadId') == parent and len(item.get('receiverThreadIds', [])) == 1,
                'native_lineage', 'Child discovery requires an actual completed parent spawn.')
        child = item['receiverThreadIds'][0]
        result = self._request('thread/read', {'threadId':child, 'includeTurns':False})
        require(result['thread']['id'] == child, 'native_lineage', 'Discovered child identity differs.')
        self.threads[child] = result['thread']
        observation = self.receipt(sequence, child=child)
        self.validate_launch(observation, parent)
        return observation

    def validate_launch(self, observation, parent):
        child = self.native.observation(observation, launch=True, parent=parent, session=self.authority.session_id)
        require(self.raw_frames.get(observation['sequence'], {}).get('frame') == observation['event'],
                'observation_forged', 'Launch evidence was not received on the protected connection.')
        require(child in self.threads, 'lineage_unavailable', 'Child discovery is incomplete.')
        return child

    def validate_status(self, observation, subject):
        require(self.raw_frames.get(observation['sequence'], {}).get('frame') == observation['event'],
                'observation_forged', 'Status was not received on this connection.')
        return self.native.observation(observation, subject=subject, session=self.authority.session_id)

    def close(self, deadline=None):
        if self.process is None: return {'state':'not_started'}
        deadline = deadline or (time.monotonic() + 10)
        pid = self.process.pid; result = {'pid':pid,'process_group':pid,'state':'uncertain'}
        try:
            try:self._observe_companion(force=True)
            except (PolicyError,OSError,subprocess.TimeoutExpired) as exc:
                self.companion_identity_uncertain = True
                result['companion_observation_error']=getattr(exc,'code',type(exc).__name__)
            if self.process.stdin and not self.process.stdin.closed: self.process.stdin.close()
            if self.process.poll() is None:
                try: self.process.wait(timeout=max(0.01,min(2,deadline-time.monotonic())))
                except subprocess.TimeoutExpired: pass
            # start_new_session made this exact owned PID its process-group leader.
            for sig in (signal.SIGTERM,signal.SIGKILL):
                try: os.killpg(pid,sig)
                except ProcessLookupError: break
                except PermissionError: result['code']='group_signal_denied'; break
                try: self.process.wait(timeout=max(0.01,min(2,deadline-time.monotonic())))
                except subprocess.TimeoutExpired: pass
                if time.monotonic() >= deadline: break
            # Signalling is asynchronous even after the parent has exited.
            # Observe the exact owned group until the separate cleanup deadline.
            while True:
                try:os.killpg(pid,0)
                except ProcessLookupError:
                    result['state']='owned_process_group_stopped';break
                except PermissionError:
                    result['code']='group_status_unavailable';break
                remaining=deadline-time.monotonic()
                if remaining<=0:break
                time.sleep(min(0.05,remaining))
            result['parent_returncode']=self.process.poll()
            try:result['companion']=self._close_companion(deadline)
            except (PolicyError,OSError,subprocess.TimeoutExpired) as exc:
                result['companion']={'state':'uncertain','code':getattr(exc,'code',type(exc).__name__)}
        finally:
            self.selector.close()
            for stream in (self.process.stdout,self.process.stderr):
                if stream and not stream.closed:stream.close()
        return result
