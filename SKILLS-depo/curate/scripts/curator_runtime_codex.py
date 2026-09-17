"""Pinned Codex App Server stdio adapter; raw transport is never a model tool."""
from collections import deque
import ctypes
import hashlib
import json
import os
import re
from pathlib import Path
import selectors
import select
import signal
import stat
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
    'tool_suggest','auth_elicitation','shell_snapshot','view_image',
    'background_paginated_rollout_migration','local_thread_store_compression','local_thread_store_shared_compression')
DESKTOP_UI_KEYS = frozenset(('conversationDetailMode','show-context-window-usage','toys-confetti-enabled',
    'appearanceLightChromeTheme','appearanceDarkChromeTheme','toys-audio-visualizer-enabled',
    'microphoneInputDeviceId','enabled-reasoning-efforts','followUpQueueMode','avatar-overlay-mascot-width-px',
    'selected-avatar-id','keepRemoteControlAwakeWhilePluggedIn','preventSleepWhileRunning',
    'open-in-target-preferences','appearanceLightCodeThemeId','appearanceDarkCodeThemeId',
    'realtimeVoiceScreenContextEnabled','dock-icon-preference'))


def safe_rpc_error(method, request_id, frame, locator):
    """Keep recognized error wording and wire identity, never arbitrary server data."""
    error=frame.get('error');error=error if type(error) is dict else {}
    message=error.get('message');message=message if type(message) is str else ''
    recognized=re.fullmatch(r'thread [A-Za-z0-9_-]{1,128} is not materialized yet; (includeTurns|thread/turns/list) is unavailable before first user message',message)
    safe_text=('thread <selected-native-id> is not materialized yet; '+recognized[1]+' is unavailable before first user message'
               if recognized else 'list_turns is not supported yet' if message=='list_turns is not supported yet'
               else '[unrecognized RPC error text omitted]')
    return {'method':method,'request_id':request_id,'locator':locator,
        'rpc_code':error.get('code') if type(error.get('code')) is int else None,
        'category':'pre_user_history_unavailable' if recognized else 'list_turns_unsupported' if message=='list_turns is not supported yet' else 'unclassified_native_error',
        'text':safe_text,'message_sha256':hashlib.sha256(message.encode()).hexdigest(),
        'message_bytes':len(message.encode()),'data_present':'data' in error,
        'unselected_error_values_retained':False}


class NativeRPCError(PolicyError):
    def __init__(self, method, params, request_id, frame, locator):
        super().__init__('native_error','Native request returned an error.')
        self.preuser_actor=None;self.requires_absent_row=False;self.request_id=request_id;self.locator=locator
        actor=params.get('threadId');error=frame.get('error')
        if (method=='thread/read' and type(actor) is str and params=={'threadId':actor,'includeTurns':True}
            and frame.get('id')==request_id and set(frame)=={'id','error'} and type(error) is dict
            and set(error)<= {'code','message','data'} and error.get('data') is None
            and type(error.get('code')) is int
            and locator.get('direction')=='received' and all(type(locator.get(k)) is str and len(locator[k])==64 for k in ('raw_sha256','canonical_sha256'))
            and ((error['code']==-32600 and error.get('message') in
                (f'thread {actor} is not materialized yet; includeTurns is unavailable before first user message',
                 f'thread {actor} is not materialized yet; thread/turns/list is unavailable before first user message'))
                 or (error['code']==-32601 and error.get('message')=='list_turns is not supported yet'))):
            self.preuser_actor=actor
            self.requires_absent_row=error['code']==-32601


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
    if 'const' in schema:require(canonical(value)==canonical(schema['const']),'wire_const','Native constant differs.')
    kind = schema.get('type')
    if kind is not None:
        kinds = kind if isinstance(kind, list) else [kind]
        valid = any((k == 'null' and value is None) or (k == 'string' and type(value) is str)
                    or (k == 'object' and type(value) is dict) or (k == 'array' and type(value) is list)
                    or (k == 'integer' and type(value) is int) or (k == 'number' and type(value) in (int, float))
                    or (k == 'boolean' and type(value) is bool) for k in kinds)
        require(valid, 'wire_type', 'Native field type differs.')
    if type(value) in (int,float):
        if 'minimum' in schema:require(value>=schema['minimum'],'wire_minimum','Native numeric value is below its bound.')
        if 'maximum' in schema:require(value<=schema['maximum'],'wire_maximum','Native numeric value exceeds its bound.')
    if type(value) is str:
        require(len(value)>=schema.get('minLength',0) and len(value)<=schema.get('maxLength',2000000),'wire_length','Native string exceeds its bounds.')
        if 'pattern' in schema:require(re.search(schema['pattern'],value) is not None,'wire_pattern','Native string differs from its pattern.')
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
        require(len(value)>=schema.get('minItems',0) and len(value)<=schema.get('maxItems',10000),'wire_items','Native array differs from its size bounds.')
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
        self.events = []; self.pending_calls = deque(); self.responses = {}; self.response_locators = {}; self.threads = {}; self.turns = {}
        self.authority = None; self.dispatch = None; self.after_response = None; self.raw_frames = {}
        self.launch_settings = {}; self.effective = {}; self.bootstrap_profile = None
        self.method_counts = {}; self.request_counts = {}
        self.rpc_errors = []
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
        self.method_schemas = getattr(type(self),'METHOD_SCHEMAS',METHOD_SCHEMAS)
        for name in {x for pair in self.method_schemas.values() for x in pair}:
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
                observed=self._observe_group(group,deadline)
                if observed['permission_errors']:record['observation_permission_errors']=record.get('observation_permission_errors',0)+observed['permission_errors']
                if observed['state']=='absent':record['state']='stopped';break
                if observed['state']=='unavailable':record['code']='status_unavailable';break
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
        if hasattr(self,'record_wire'):self.record_wire('sent',raw,frame)

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
                require(type(frame) is dict and ('id' not in frame or type(frame['id']) in (int,str)),
                        'wire_envelope','Malformed native JSON-RPC frame identity.')
                if hasattr(self,'record_wire'):self.record_wire('received',line+b'\n',frame)
                self.sequence += 1
                method = frame.get('method', 'response')
                if not isinstance(method, str) or len(method) > 100: method = 'unknown'
                self.method_counts[method] = self.method_counts.get(method, 0) + 1
                if self.pending_methods.get(frame.get('id')) not in ('config/read','account/read'):
                    self.raw_frames[self.sequence] = {'sha256':hashlib.sha256(line).hexdigest(), 'frame':frame}
                if 'method' not in frame and 'id' in frame:
                    self.responses[frame['id']] = frame
                    self.response_locators[frame['id']] = {'direction':'received',
                        'sequence':getattr(self,'wire_sequence',self.sequence),
                        'raw_sha256':hashlib.sha256(line+b'\n').hexdigest(),'canonical_sha256':digest(frame)}
                elif frame.get('method') == 'item/tool/call' and 'id' in frame:
                    require(self.authority is not None, 'session_unbound', 'No selected native session.')
                    context = (self.authority.capture(frame,self.wire_sequence,line+b'\n')
                               if isinstance(self.authority,self.native.TransportAuthorityV2)
                               else self.authority.capture(frame,self.sequence))
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
            if getattr(self,'after_response',None) is not None:self.after_response(context)
        return len(self.events)

    def _request(self, method, params):
        methods=getattr(self,'method_schemas',METHOD_SCHEMAS)
        require(method in methods, 'method_denied', 'No raw protocol forwarding.')
        require(not self.stopping or method in ('turn/interrupt','thread/read'), 'stopped_admission', 'Only stop reconciliation is admitted.')
        self._remaining()
        self._validate(methods[method][0], params)
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
        response_locator=getattr(self,'response_locators',{}).pop(identifier,None)
        self.pending_methods.pop(identifier, None)
        if 'error' in frame:
            records=[row for row in getattr(self,'wire_records',[]) if row['direction']=='received'
                     and row['frame']==frame and 'method' not in row['frame']]
            locator=response_locator or ({key:records[-1][key] for key in ('direction','sequence','raw_sha256','canonical_sha256')}
                     if records else {'state':'wire_locator_unavailable'})
            self.rpc_errors.append(safe_rpc_error(method,identifier,frame,locator))
            self.rpc_errors=self.rpc_errors[-32:]
            raise NativeRPCError(method,params,identifier,frame,locator)
        result = frame['result']; self._validate(methods[method][1], result)
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
                'storage_features':{name:features.get(name) for name in ('transcript_v2','sqlite')},
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

    @staticmethod
    def _observe_group(group,deadline):
        errors=0
        while time.monotonic()<deadline:
            try:os.killpg(group,0)
            except ProcessLookupError:return {'state':'absent','permission_errors':errors}
            except PermissionError:
                errors+=1
                time.sleep(min(.05,max(0,deadline-time.monotonic())))
            else:return {'state':'present','permission_errors':errors}
        return {'state':'unavailable','permission_errors':errors}

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
                observed=self._observe_group(pid,deadline)
                if observed['permission_errors']:result['observation_permission_errors']=result.get('observation_permission_errors',0)+observed['permission_errors']
                if observed['state']=='absent':break
                if observed['state']=='unavailable':result['code']='group_status_unavailable';break
                if self.companion:
                    known=[self._server_identity,*self._owned_processes.values()]
                    bound=False
                    for original in known:
                        if original is None or original['group']!=pid:continue
                        current=self._kernel_identity(original['pid'])
                        if current is not None and all(current[key]==original[key] for key in ('group','uid','started','executable')):
                            bound=True;break
                    if not bound:result['code']='runtime_group_identity_unconfirmed';break
                try: os.killpg(pid,sig)
                except ProcessLookupError: break
                except PermissionError: result['code']='group_signal_denied'; break
                try: self.process.wait(timeout=max(0.01,min(2,deadline-time.monotonic())))
                except subprocess.TimeoutExpired: pass
                if time.monotonic() >= deadline: break
            # Signalling is asynchronous even after the parent has exited.
            # Observe the exact owned group until the separate cleanup deadline.
            while True:
                observed=self._observe_group(pid,deadline)
                if observed['permission_errors']:result['observation_permission_errors']=result.get('observation_permission_errors',0)+observed['permission_errors']
                if observed['state']=='absent':result['state']='owned_process_group_stopped';break
                if observed['state']=='unavailable':result['code']='group_status_unavailable';break
                remaining=deadline-time.monotonic()
                if remaining<=0:break
                time.sleep(min(0.05,remaining))
            result['parent_returncode']=self.process.poll()
            if result['parent_returncode'] is None:
                result['state']='uncertain';result['code']='original_runtime_still_present'
            try:result['companion']=self._close_companion(deadline)
            except (PolicyError,OSError,subprocess.TimeoutExpired) as exc:
                result['companion']={'state':'uncertain','code':getattr(exc,'code',type(exc).__name__)}
        finally:
            self.selector.close()
            for stream in (self.process.stdout,self.process.stderr):
                if stream and not stream.closed:stream.close()
        return result


class ForkCodexAdapter(CodexAdapter):
    """One admitted native actor and one owned runtime per load incarnation."""
    METHOD_SCHEMAS={**METHOD_SCHEMAS,
        'thread/fork':('ThreadForkParams','ThreadForkResponse'),
        'thread/turns/list':('ThreadTurnsListParams','ThreadTurnsListResponse'),
        'environment/status':('EnvironmentStatusParams','EnvironmentStatusResponse'),
        'environment/info':('EnvironmentInfoParams','EnvironmentInfoResponse'),
        'account/read':('GetAccountParams','GetAccountResponse')}

    def __init__(self,*args,selected_protocol,registry,connection_id,load_epoch,storage_admission,instruction_sources=(),local_environment=None,**kwargs):
        super().__init__(*args,**kwargs)
        self.native.protocol(selected_protocol)
        require(selected_protocol['schema_version']==2 and self.companion is not None,
                'fork_protocol','Fork actors require explicit protocol2 and a pinned standalone companion.')
        self.native.identity(connection_id)
        require(type(load_epoch) is int and load_epoch>0,'load_epoch','Select a positive incarnation.')
        self.selected_protocol=selected_protocol;self.registry=registry;self.connection_id=connection_id
        self.load_epoch=load_epoch;self.storage_admission=storage_admission
        self.actor_binding=None;self.expected_creation=False;self.provisional=set();self.quarantine=[]
        self.wire_sequence=0;self.wire_records=[];self.last_rpc=None;self.closed_admission=False
        self.observation_handles={};self._closure_verified=False
        self.history_reads=[];self.cleanup_observation=None;self.creation_responses=[]
        self.instruction_sources=[dict(item) for item in instruction_sources]
        self.local_environment=dict(local_environment) if local_environment is not None else None;self._local_verified=False

    def verify_local_configuration(self):
        selected=self.local_environment
        exact(selected,('id','cwd','runtime_workspace_roots','shell','configuration_path','configuration_state'))
        require(selected['id']=='local' and selected['cwd']==self.cwd and selected['runtime_workspace_roots']==[]
                and selected['shell']=={'name':'zsh','path':'/bin/zsh'} and selected['configuration_state']=='absent',
                'environment_selection','Only the exactly selected reserved local environment is admitted.')
        require(set(self.environment)=={'HOME','PATH','LANG','TMPDIR','PYTHONDONTWRITEBYTECODE'}
                and self.environment['PATH']=='/usr/bin:/bin:/usr/sbin:/sbin' and self.environment['PYTHONDONTWRITEBYTECODE']=='1'
                and str(Path(self.environment['HOME'])/'.codex/environments.toml')==selected['configuration_path'],
                'environment_routing','Only the pinned minimal process environment without remote routing variables is admitted.')
        try:os.lstat(selected['configuration_path'])
        except FileNotFoundError:pass
        else:raise PolicyError('environment_configuration_present','Unreviewed environment configuration exists; do not start or allocate.')
        return {'path':selected['configuration_path'],'state':'absent','contents_read':False}

    def start(self):
        self.verify_local_configuration()
        return super().start()

    def local_selections(self):
        require(self.local_environment is not None and self.local_environment['id']=='local','environment_selection','No selected local execution route.')
        return [{'environmentId':'local','cwd':self.cwd,'runtimeWorkspaceRoots':[]}]

    def inspect_local_environment(self):
        self._local_verified=False
        absent=self.verify_local_configuration()
        status=self._request('environment/status',{'environmentId':'local'});status_frames=list(self.last_rpc['records'])
        require(status.get('status')=='ready' and status.get('error') is None,'local_environment_unready','The reserved local environment is not observed ready.')
        info=self._request('environment/info',{'environmentId':'local'});info_frames=list(self.last_rpc['records'])
        require(info.get('shell')==self.local_environment['shell'] and info.get('cwd')==Path(self.cwd).as_uri(),
                'local_environment_metadata','Actual local shell or default cwd differs from the selected fixture.')
        self._local_verified=True
        return {'id':'local','status':status,'info':info,'configuration':absent,'frames':status_frames+info_frames}

    def verify_instruction_sources(self,result):
        from curator_confinement import file_snapshot
        expected=[item['path'] for item in self.instruction_sources]
        require(type(result.get('instructionSources')) is list and result['instructionSources']==expected,
                'instruction_sources_unproven','Effective native instruction sources differ from the exact protected input selection.')
        for item in self.instruction_sources:
            current=file_snapshot('/',item['path'].lstrip('/'),2000000)
            require(all(current[key]==item[key] for key in ('sha256','device','inode','size','mode')),
                    'instruction_source_changed','Selected instruction input changed; no content is copied.')
        return {'state':'observed_exact','sources':expected,'contents_copied':False}

    def record_wire(self,direction,raw,frame):
        self.wire_sequence+=1
        private_response=(direction=='received' and 'method' not in frame and
            self.pending_methods.get(frame.get('id')) in ('config/read','account/read'))
        if not private_response:
            self.wire_records.append(self.native.wire_record(direction,self.wire_sequence,raw))
        require(len(self.wire_records)<=10000,'wire_bound','Native evidence record bound reached.')
        if direction!='received':return
        params=frame.get('params',{});actor=params.get('threadId') if isinstance(params,dict) else None
        if frame.get('method')=='thread/started':actor=params.get('thread',{}).get('id')
        if actor is None:return
        if self.actor_binding is not None and actor==self.actor_binding['thread_id']:return
        if self.expected_creation:
            self.provisional.add(actor)
            if len(self.provisional)==1:return
        self.quarantine.append({'thread_id':actor,'sequence':self.wire_sequence,'method':frame.get('method')})
        self.closed_admission=True
        raise PolicyError('unadmitted_native_actor','Unexpected actor on this owned runtime; admission closed.')

    def _request(self,method,params):
        actor=getattr(self,'actor_binding',None)
        stop_read=(method=='thread/read' and actor is not None and params=={'threadId':actor['thread_id'],'includeTurns':False})
        stop_interrupt=(method=='turn/interrupt' and actor is not None and params.get('threadId')==actor['thread_id'])
        require(not self.closed_admission or stop_read or stop_interrupt,
                'actor_admission_closed','Only exact stop observations remain admitted.')
        before=self.wire_sequence
        result=super()._request(method,params)
        if method not in ('config/read','account/read'):
            records=[row for row in self.wire_records if row['sequence']>before
                and row['frame'].get('id')==self.request_id and
                ((row['direction']=='sent' and row['frame'].get('method')==method)
                 or (row['direction']=='received' and 'method' not in row['frame']))]
            require(len(records)==2,'native_correlation','Expected one sent request and its received response.')
            self.native.correlated_pair(records,method)
            self.last_rpc={'method':method,'records':records}
        return result

    def verify_prelaunch(self,model,effort,provider):
        self._closure_verified=False
        config=self.inspect_tool_configuration(code_mode_host=True)
        require(config.get('delegation')=={'multi_agent':False,'multi_agent_v2':False,'agents_enabled':False},
                'native_delegation_unproven','Every intrinsic collaboration control must be disabled before creation.')
        require(config.get('storage_features')=={'transcript_v2':False,'sqlite':True},
                'native_storage_mode_unproven','Preserve the observed transcript and SQLite selection before creation.')
        advertised=self.inspect_model(model,effort)
        account=self._request('account/read',{'refreshToken':False})
        require(provider=='openai' and isinstance(account.get('account'),dict),
                'native_auth_reuse_unavailable','Established runtime account readiness is unavailable.')
        local=self.inspect_local_environment()
        self._closure_verified=True
        self.prelaunch_observation={'configuration':config,'catalog':advertised,'account_ready':True,
                'account_contents_retained':False,'provider':provider,'local_environment':local}
        return self.prelaunch_observation

    def _begin_creation(self,kind,operation_id,reservation_id,source_thread_id=None):
        require(self._closure_verified and not self.closed_admission and self.actor_binding is None,
                'creation_held','One new actor requires verified prelaunch closure and an empty owned runtime.')
        require(self.storage_admission is not None,'native_storage_unproven','Explicit native allocation scope is required.')
        self.storage_admission.begin_operation(kind,operation_id,reservation_id,source_thread_id)
        self.expected_creation=True

    def _bind_response(self,result,settings,operation_id,reservation_id,expected_id=None,source_id=None):
        rpc=self.last_rpc
        require(type(rpc) is dict and rpc.get('method') in ('thread/start','thread/fork','thread/resume'),
                'creation_response_unproven','No correlated creation or resume response is available.')
        _,actual=self.native.correlated_pair(rpc['records'],rpc['method'])
        require(actual==result,'creation_response_unproven','Returned actor metadata differs from the authenticated response.')
        thread=result['thread']
        allocation={'operation_id':operation_id,'reservation_id':reservation_id,'connection_id':self.connection_id,
            'load_epoch':self.load_epoch,'method':rpc['method'],'native_id':thread.get('id'),'returned_path':thread.get('path'),
            'admitted':False,'persistence':'not_observed','frames':[{
                key:row[key] for key in ('direction','sequence','raw_sha256','canonical_sha256')} for row in rpc['records']]}
        self.creation_responses.append(allocation)
        thread=result['thread'];actor=thread['id'];self.native.identity(actor)
        require(expected_id is None or actor==expected_id,'native_resume_mismatch','Resume returned a replacement identity.')
        require(not self.provisional or self.provisional=={actor},'native_creation_uncertain','Observed identity differs from the correlated response.')
        require(source_id is None or actor!=source_id,'native_fork_mismatch','Fork returned its source identity.')
        require(thread.get('forkedFromId')==source_id,'native_lineage','Actual fork source differs.')
        self.verify_instruction_sources(result)
        require(result.get('model')==thread.get('model')==settings['model']
                and result.get('reasoningEffort')==thread.get('reasoningEffort')==settings['reasoning_effort']
                and result.get('modelProvider')==thread.get('modelProvider')==settings['provider']
                and result.get('cwd')==settings['cwd'] and (result.get('activePermissionProfile') or {}).get('id')==settings['profile_id'],
                'inheritance_mismatch','Preselected and configured actor settings/profile differ; no repair is admitted.')
        self.storage_admission.register_native(operation_id,reservation_id,thread)
        self.actor_binding={'thread_id':actor,'session_id':thread['sessionId'],'connection_id':self.connection_id,
            'load_epoch':self.load_epoch,'runtime_instance':dict(self._server_identity)}
        self.registry.bind(self.actor_binding)
        self.authority=self.native.TransportAuthorityV2(self.selected_protocol,self.actor_binding,self.registry)
        self.threads={actor:thread};self.effective={actor:result};self.expected_creation=False
        allocation['admitted']=True
        return actor

    def start_seed(self,*,settings,profile,dynamic_tools,instructions,operation_id,reservation_id):
        self._begin_creation('seed',operation_id,reservation_id)
        result=self._request('thread/start',{'model':settings['model'],'modelProvider':settings['provider'],
            'config':{'model_reasoning_effort':settings['reasoning_effort']},'permissions':profile,'approvalPolicy':'never',
            'cwd':self.cwd,'runtimeWorkspaceRoots':[],'dynamicTools':dynamic_tools,'baseInstructions':instructions,
            'ephemeral':False,'historyMode':'paginated','allowProviderModelFallback':False,'environments':self.local_selections()})
        actor=self._bind_response(result,{**settings,'profile_id':profile,'cwd':self.cwd},operation_id,reservation_id)
        return {'thread_id':actor,'response':result,'frames':list(self.last_rpc['records'])}

    def followup(self,thread_id,text):
        require(self._local_verified and thread_id in self.threads and type(text) is str,
                'local_turn_held','Only the observed local route and bound native actor may receive a model-bearing turn.')
        self.verify_local_configuration()
        result=self._request('turn/start',{'threadId':thread_id,'input':[{'type':'text','text':text,'text_elements':[]}],
            'cwd':self.cwd,'runtimeWorkspaceRoots':[],'environments':self.local_selections()})
        current=self.turns.get(thread_id)
        if current is None or current['id']!=result['turn']['id'] or current['status']=='inProgress':self.turns[thread_id]=result['turn']
        return result

    def observe_preuser_storage(self):
        """Bind the actual allocation before reading optional persisted turn history."""
        require(self.actor_binding is not None,'native_unknown','No allocated actor is bound.')
        actor=self.actor_binding['thread_id'];created=self.threads[actor]
        ownership=self.storage_admission.bind_storage(actor,created)
        observed=self.observe(actor)['thread']
        for key in ('id','sessionId','parentThreadId','forkedFromId','source','path','model','reasoningEffort','modelProvider'):
            require(key in observed and observed[key]==created.get(key),'native_metadata_mismatch','Independent pre-user metadata differs: '+key)
        self.storage_admission.require_owned(actor)
        return {'ownership':ownership,'metadata':{key:observed[key] for key in
            ('id','sessionId','parentThreadId','forkedFromId','source','path','model','reasoningEffort','modelProvider')},
            'include_turns':False,'model_turns':0,'frames':list(self.last_rpc['records'])}

    def materialize_preuser_storage(self,operation_id,reservation_id):
        require(self.actor_binding is not None,'native_unknown','No allocated actor is bound.')
        actor=self.actor_binding['thread_id'];hydration='available';requires_absent_row=False
        require(actor not in self.turns,'preuser_only','The partial-persistence exception is unavailable after an observed user turn.')
        try:
            self.persist_history(operation_id,reservation_id)
            materialization={'state':'response_received','frames':list(self.last_rpc['records'])}
        except NativeRPCError as exc:
            require(exc.preuser_actor==actor and exc.request_id==self.request_id,
                    'preuser_materialization_unproven','The pre-user history error is not the exact admitted actor/request/response.')
            hydration='unavailable_before_first_user_message'
            requires_absent_row=exc.requires_absent_row
            materialization={'state':'recognized_empty_history_error','request_id':exc.request_id,
                'response_locator':dict(exc.locator),'diagnostic':dict(self.rpc_errors[-1])}
        observed=self.observe_preuser_storage()
        index=self.storage_admission.observe_index_metadata(actor)
        if requires_absent_row:
            require(index['state']=='absent' and index['actor']==actor and index['metadata'] is None,
                    'preuser_index_not_absent','Unsupported listing is permitted only for the independently absent exact pre-user row.')
        return {**observed,'materialization':materialization,'persistence':'owned_header_observed','hydration':hydration,
                'partial_persistence':hydration!='available','operation_id':operation_id,'index_metadata':index}

    def require_paginated_metadata(self):
        require(self.actor_binding is not None,'native_unknown','No bound actor metadata.')
        actor=self.actor_binding['thread_id'];observed=self.storage_admission.observe_index_metadata(actor)
        thread=self.threads[actor]
        expected={'id':actor,'rollout_path':self.storage_admission.paths[actor],'model_provider':thread['modelProvider'],
            'model':thread['model'],'reasoning_effort':thread['reasoningEffort'],'history_mode':'paginated','cwd':self.cwd}
        require(observed['state']=='present' and observed['actor']==actor and observed['metadata']==expected,
                'native_paginated_metadata_unproven','Actual selected paginated row/path/settings must be present; no post-user exception is admitted.')
        return observed

    def persist_history(self,operation_id,reservation_id):
        require(self.actor_binding is not None,'native_unknown','No actor is bound.')
        actor=self.actor_binding['thread_id']
        # Loaded paginated includeTurns is an allocation, not a read-only view.
        self.storage_admission.begin_operation('persist_history',operation_id,reservation_id,actor)
        result=self._request('thread/read',{'threadId':actor,'includeTurns':True})
        self.storage_admission.bind_storage(actor,result['thread'])
        return result

    def configured_settings(self):
        require(self.actor_binding is not None,'native_unknown','No actor is bound.')
        result=self.observe(self.actor_binding['thread_id']);thread=result['thread']
        configured={'model':thread.get('model'),'reasoning_effort':thread.get('reasoningEffort'),'provider':thread.get('modelProvider')}
        require(all(type(value) is str and value for value in configured.values()),'settings_unproven','Configured parent settings are unavailable.')
        return configured

    def fork_reserved(self,*,parent_settings,source_thread_id,history_cut,profile,logical_parent_id,operation_id,reservation_id):
        self.native.fields(history_cut,('mode','turn_id','history_sha256','input_sha256'))
        require(history_cut['mode'] in ('lastTurnId','beforeTurnId'),'history_cut','Select one proved source-history cut.')
        self._begin_creation('fork',operation_id,reservation_id,source_thread_id)
        params={'threadId':source_thread_id,history_cut['mode']:history_cut['turn_id'],
            'model':parent_settings['model'],'modelProvider':parent_settings['provider'],
            'config':{'model_reasoning_effort':parent_settings['reasoning_effort']},'permissions':profile,
            'approvalPolicy':'never','cwd':self.cwd,'runtimeWorkspaceRoots':[],'ephemeral':False,
            'excludeTurns':True,'deferGoalContinuation':True}
        result=self._request('thread/fork',params);creation_frames=list(self.last_rpc['records'])
        settings={**parent_settings,'profile_id':profile,'cwd':self.cwd}
        actor=self._bind_response(result,settings,operation_id,reservation_id,source_id=source_thread_id)
        observed=self.observe(actor);frames=creation_frames+list(self.last_rpc['records'])
        self.storage_admission.bind_storage(actor,observed['thread'])
        metadata={k:observed['thread'].get(k) for k in ('id','sessionId','parentThreadId','forkedFromId','source','path','model','reasoningEffort','modelProvider')}
        receipt=self.typed_receipt('creation',operation_id,reservation_id,frames,{'source_thread_id':source_thread_id,
            'logical_parent_id':logical_parent_id,'metadata':metadata,'settings':settings,'history_cut':history_cut})
        return {'thread_id':actor,'response':result,'observation':receipt}

    def resume_owned(self,*,stored_actor,settings,profile,operation_id,reservation_id):
        self._begin_creation('resume',operation_id,reservation_id,stored_actor['thread_id'])
        result=self._request('thread/resume',{'threadId':stored_actor['thread_id'],'model':settings['model'],
            'modelProvider':settings['provider'],'config':{'model_reasoning_effort':settings['reasoning_effort']},
            'permissions':profile,'approvalPolicy':'never','cwd':self.cwd,'runtimeWorkspaceRoots':[],'excludeTurns':True})
        resume_frames=list(self.last_rpc['records']);expected={**settings,'profile_id':profile,'cwd':self.cwd}
        actor=self._bind_response(result,expected,operation_id,reservation_id,expected_id=stored_actor['thread_id'],source_id=stored_actor['source_thread_id'])
        observed=self.observe(actor);self.storage_admission.bind_storage(actor,observed['thread'])
        metadata={k:observed['thread'].get(k) for k in ('id','sessionId','parentThreadId','forkedFromId','source','path','model','reasoningEffort','modelProvider')}
        receipt=self.typed_receipt('resume',operation_id,reservation_id,resume_frames+list(self.last_rpc['records']),
            {'source_thread_id':stored_actor['source_thread_id'],'logical_parent_id':stored_actor['logical_parent_id'],
             'metadata':metadata,'settings':expected,'history_cut':stored_actor['history_cut']})
        return {'thread_id':actor,'response':result,'observation':receipt}

    def full_history(self,*,max_turns=100,max_bytes=2000000,max_pages=100):
        require(self.actor_binding is not None,'native_unknown','No bound actor history.')
        require(type(max_pages) is int and 0<max_pages<=100,'history_bound','Select a finite native page bound.')
        actor=self.actor_binding['thread_id'];self.storage_admission.require_owned(actor)
        result=[];cursor=None;seen=set();pages=[]
        while True:
            require(len(pages)<max_pages,'history_bound','Complete history paging exceeded its selected bound.')
            params={'threadId':actor,'itemsView':'full','limit':min(max_turns,100),'sortDirection':'asc'}
            if cursor is not None:params['cursor']=cursor
            page=self._request('thread/turns/list',params)
            pages.append({'request':dict(params),'frames':[{k:r[k] for k in ('direction','sequence','raw_sha256','canonical_sha256')} for r in self.last_rpc['records']]})
            require(type(page.get('data')) is list,'history_unproven','Missing native turn page.')
            result.extend(page['data'])
            require(len(result)<=max_turns and len(canonical(result))<=max_bytes,'history_bound','Native history exceeds its exact selected bound.')
            cursor=page.get('nextCursor')
            if cursor is None:break
            require(type(cursor) is str and cursor not in seen,'history_cursor','Repeated or invalid history cursor.');seen.add(cursor)
        require(len({turn['id'] for turn in result})==len(result),'history_duplicate','Duplicate native turn in complete history.')
        history={'thread_id':actor,'pages':pages,'sha256':digest(result),'turns':len(result),'complete':True}
        self.history_reads.append(history)
        return {'turns':result,'sha256':history['sha256'],'complete':True,'mode':'paginated-full-items'}

    def status_receipt(self,operation_id,reservation_id):
        require(self.actor_binding is not None,'native_unknown','No loaded actor.')
        result=self.observe(self.actor_binding['thread_id'])
        return self.typed_receipt('status',operation_id,reservation_id,list(self.last_rpc['records']),
            {'native_state':result['thread']['status']['type']})

    def delivery_receipt(self,text,operation_id,reservation_id,artifact_sha256s,*,conflict=None,steer=False):
        actor=self.actor_binding['thread_id']
        result=self.message(actor,text) if steer else self.followup(actor,text)
        frames=list(self.last_rpc['records']);params,_=self.native.correlated_pair(frames,'turn/steer' if steer else 'turn/start')
        facts={'recipient':actor,'turn_id':result['turnId'] if steer else result['turn']['id'],
            'input_sha256':digest(params['input']),'artifact_sha256s':list(artifact_sha256s)}
        if conflict is not None:
            exact(conflict,('origin_assignment_id','explanation_sha256'));facts.update(conflict)
        return self.typed_receipt('conflict_delivery' if conflict is not None else 'input_delivery',operation_id,reservation_id,frames,facts)

    def role_receipt(self,context,operation_id,reservation_id,reads):
        self.native.require_current(self.selected_protocol,context.thread_id,context.binding())
        require(context.actor==self.actor_binding and context.tool=='role_acknowledge',
                'role_actor','Role acknowledgement requires the selected wire tool and loaded actor.')
        frames=[r for r in self.wire_records if r['direction']=='received' and r['sequence']==context.sequence]
        require(len(frames)==1 and frames[0]['frame'].get('params',{}).get('namespace') is None,
                'role_namespace','The selected acknowledgement tool is unnamespaced.')
        return self.typed_receipt('role_acknowledgement',operation_id,reservation_id,frames,{'reads':reads,'call_id':context.call_id})

    def interrupt_receipt(self,operation_id,reservation_id):
        actor=self.actor_binding['thread_id'];turn=self.turns.get(actor)
        require(turn is not None and turn['status']=='inProgress','turn_unavailable','Only an observed active turn can be interrupted.')
        self.interrupt(actor);frames=list(self.last_rpc['records'])
        terminal=[r for r in self.wire_records if r['direction']=='received' and r['frame'].get('method')=='turn/completed'
            and r['frame'].get('params',{}).get('threadId')==actor and r['frame']['params']['turn'].get('id')==turn['id']]
        state=terminal[-1]['frame']['params']['turn']['status'] if terminal else 'unknown'
        return self.typed_receipt('interrupt',operation_id,reservation_id,frames+terminal[-1:],
            {'turn_id':turn['id'],'acknowledged':True,'observed_state':state})

    def archive_evidence(self,directory,*,max_bytes,shard_bytes=16384,deadline=None):
        """Protected reconstruction archive; no raw body is returned to model tools."""
        from curator_confinement import canonical_root,parent_descriptor
        root=canonical_root(directory)
        require(type(max_bytes) is int and 0<max_bytes<=128000000 and type(shard_bytes) is int and 1024<=shard_bytes<=20000,
                'evidence_bound','Select finite protected archive and shard limits.')
        total=0;count=0;buffer=b'';whole=hashlib.sha256();shards=[]
        def remaining():
            if deadline is None:self._remaining()
            else:require(time.monotonic()<deadline,'native_deadline','Protected evidence archive exceeded its selected host deadline.')
        def write(raw):
            remaining()
            name='wire-'+str(len(shards)).zfill(6)+'.part'
            with parent_descriptor(root,name) as (parent,leaf):
                fd=os.open(leaf,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=parent)
                with os.fdopen(fd,'wb') as out:out.write(raw);out.flush();os.fsync(out.fileno())
            shards.append({'path':name,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
        for row in self.wire_records:
            remaining()
            self.native.validate_wire_record(row)
            frame=row['frame'];method=frame.get('method','')
            if method.startswith(('account/','config/')):continue
            raw=canonical(row)+b'\n';total+=len(raw);count+=1
            require(total<=max_bytes,'evidence_bound','Complete wire evidence exceeds its assessed archive bound; retain existing shards and hold.')
            whole.update(raw);buffer+=raw
            while len(buffer)>=shard_bytes:write(buffer[:shard_bytes]);buffer=buffer[shard_bytes:]
        if buffer:write(buffer)
        index={'schema_version':1,'kind':'protected_native_wire_v2','actor':self.actor_binding,'records':count,'bytes':total,
            'sha256':whole.hexdigest(),'shards':shards,'history_reads':self.history_reads,
            'private_config_account_responses_excluded':True,'user_facing_body_publication':False}
        with parent_descriptor(root,'index.json') as (parent,name):
            fd=os.open(name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=parent)
            with os.fdopen(fd,'wb') as out:out.write(canonical(index));out.flush();os.fsync(out.fileno())
        return {'path':str(root/'index.json'),'sha256':digest(index),'bytes':total,'records':count,'history_reads':len(self.history_reads)}

    def verify_evidence_archive(self,selection,*,max_bytes,deadline=None):
        """Reconstruct protected raw records/pages without returning their bodies."""
        from curator_confinement import canonical_root,file_snapshot,parent_descriptor
        root=canonical_root(Path(selection['path']).parent)
        def remaining():
            if deadline is None:self._remaining()
            else:require(time.monotonic()<deadline,'native_deadline','Protected evidence reconstruction exceeded its selected host deadline.')
        def read(name,maximum,expected):
            remaining()
            info=file_snapshot(root,name,maximum)
            require(info['sha256']==expected,'evidence_digest','Protected evidence file digest differs.')
            with parent_descriptor(root,name) as (parent,leaf):
                fd=os.open(leaf,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=parent)
                with os.fdopen(fd,'rb') as stream:
                    st=os.fstat(stream.fileno())
                    require(stat.S_ISREG(st.st_mode) and st.st_nlink==1,'evidence_type','Evidence became a special or linked file.')
                    raw=stream.read(maximum+1)
            require(len(raw)<=maximum and hashlib.sha256(raw).hexdigest()==expected,'evidence_digest','Evidence changed during reconstruction.')
            return raw
        index=json.loads(read('index.json',2000000,selection['sha256']))
        exact(index,('schema_version','kind','actor','records','bytes','sha256','shards','history_reads',
                     'private_config_account_responses_excluded','user_facing_body_publication'))
        require(index['schema_version']==1 and index['kind']=='protected_native_wire_v2' and index['actor']==self.actor_binding
                and 0<=index['bytes']<=max_bytes and 0<=index['records']<=10000,
                'evidence_bound','Unexpected archive identity or reconstruction bound.')
        require(type(index['shards']) is list and len(index['shards'])<=125000,'evidence_bound','Unbounded archive shards.')
        buffer=b'';whole=hashlib.sha256();total=0;records={}
        for ordinal,shard in enumerate(index['shards']):
            exact(shard,('path','bytes','sha256'))
            require(shard['path']=='wire-'+str(ordinal).zfill(6)+'.part' and type(shard['bytes']) is int and 0<shard['bytes']<=20000,
                    'evidence_shards','Missing, reordered or oversized evidence shard.')
            raw=read(shard['path'],shard['bytes'],shard['sha256']);whole.update(raw);total+=len(raw)
            require(total<=max_bytes,'evidence_bound','Archive exceeds the exact reconstruction byte bound.')
            buffer+=raw
            while b'\n' in buffer:
                raw,buffer=buffer.split(b'\n',1);row=json.loads(raw);self.native.validate_wire_record(row)
                key=(row['direction'],row['sequence']);require(key not in records,'evidence_duplicate','Duplicate native wire locator.')
                records[key]=row;require(len(records)<=10000,'evidence_bound','Archive record count exceeds its bound.')
        require(not buffer and total==index['bytes'] and len(records)==index['records'] and whole.hexdigest()==index['sha256'],
                'evidence_incomplete','Native wire archive is truncated or differs from its selected count/hash.')
        for history in index['history_reads']:
            remaining();turns=[];cursor=None
            require(history['thread_id']==self.actor_binding['thread_id'] and history['complete'] is True and history['pages'],
                    'history_unproven','Complete owned history page provenance is missing.')
            for ordinal,page in enumerate(history['pages']):
                rows=[]
                for locator in page['frames']:
                    row=records.get((locator['direction'],locator['sequence']))
                    require(row is not None and all(row[key]==value for key,value in locator.items()),
                            'history_locator','A retained native history page frame is missing or changed.')
                    rows.append(row)
                params,result=self.native.correlated_pair(rows,'thread/turns/list')
                require(params==page['request'] and params.get('threadId')==history['thread_id'] and params.get('itemsView')=='full'
                        and params.get('sortDirection')=='asc' and params.get('cursor')==cursor,
                        'history_cursor','History pages are not the exact complete native cursor chain.')
                require(type(result.get('data')) is list,'history_page','Missing complete native items.')
                turns.extend(result['data']);cursor=result.get('nextCursor')
                require((cursor is None)==(ordinal==len(history['pages'])-1),'history_incomplete','Missing or extra native history page.')
            require(len(turns)==history['turns'] and digest(turns)==history['sha256'] and len({t['id'] for t in turns})==len(turns),
                    'history_digest','Reconstructed complete native history differs.')
        return {'state':'verified','index_sha256':selection['sha256'],'records':len(records),'bytes':total,
                'complete_history_reads':len(index['history_reads']),'raw_bodies_returned':False}

    def typed_receipt(self,kind,operation_id,reservation_id,frames,facts):
        value={'schema_version':2,'backend':'codex-app-server-v2','broker_run_id':self.selected_protocol['broker_run_id'],
            'kind':kind,'actor':dict(self.actor_binding),'operation_id':operation_id,'reservation_id':reservation_id,
            'frames':frames,'facts':facts}
        self.native.validate_observation_v2(value)
        for row in frames:require(row in self.wire_records,'native_receipt_forged','Receipt did not originate on this connection.')
        handle='observation-'+digest(value);self.observation_handles[handle]=value
        return {'handle':handle,'value':value}

    def load_observation(self,handle,kind,*,actor=None):
        require(type(handle) is str and handle in self.observation_handles,'observation_unavailable','Unknown protected observation handle.')
        value=self.observation_handles[handle]
        self.native.validate_observation_v2(value,expected_kind=kind,subject=actor,broker_run_id=self.selected_protocol['broker_run_id'])
        if kind=='runtime_release':
            require(self.closed_admission and value['actor']==self.actor_binding and self.cleanup_observation is not None
                    and value['facts']['cleanup_sha256']==digest(self.cleanup_observation),
                    'release_unproven','Release observation does not bind this exact stopped incarnation.')
        else:self.registry.require_current(value['actor'])
        return value

    def close_actor_admission(self):
        self.closed_admission=True
        if self.actor_binding and self.registry.current.get(self.actor_binding['thread_id'])==self.actor_binding:
            self.registry.close_admission(self.actor_binding)

    def close(self,deadline=None):
        self.close_actor_admission()
        self.cleanup_observation=super().close(deadline)
        return self.cleanup_observation
