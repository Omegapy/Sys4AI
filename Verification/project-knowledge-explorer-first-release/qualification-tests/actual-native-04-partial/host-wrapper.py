"""Root-owned execution of one reviewed frozen qualification browser job."""
import ast, hashlib, json, os, pathlib, selectors, signal, stat, subprocess, sys, tempfile, time

ROOT = pathlib.Path('/Volumes/P-SSD/AngryOwl/Sys4AI')
digest = lambda b: hashlib.sha256(b).hexdigest()

def read_exact(path, maximum=4*1024*1024):
    path = pathlib.Path(path)
    assert path.is_absolute() and '..' not in path.parts
    parent = os.open('/', os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in path.parts[1:-1]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
            os.close(parent); parent = child
        fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
        try:
            before = os.fstat(fd)
            assert stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and before.st_size <= maximum
            chunks = []
            while True:
                chunk = os.read(fd, min(65536, maximum + 1 - sum(map(len, chunks))))
                if not chunk: break
                chunks.append(chunk)
                assert sum(map(len, chunks)) <= maximum
            after = os.fstat(fd); bound = os.stat(path.name, dir_fd=parent, follow_symlinks=False)
            signature = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns, s.st_nlink)
            assert signature(before) == signature(after) == signature(bound)
            return b''.join(chunks)
        finally: os.close(fd)
    finally: os.close(parent)

def write_new(path, data):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(data); stream.flush(); os.fsync(stream.fileno())

def json_bytes(value):
    return (json.dumps(value, sort_keys=True, indent=2) + '\n').encode()

def processes():
    result = subprocess.run(['/bin/ps', '-axo', 'pid=,ppid=,lstart='], capture_output=True, text=True, timeout=3)
    assert result.returncode == 0
    rows = {}
    for line in result.stdout.splitlines():
        parts = line.split(None, 2)
        if len(parts) == 3 and parts[0].isdigit() and parts[1].isdigit():
            rows[int(parts[0])] = (int(parts[1]), parts[2])
    return rows

job_path=pathlib.Path(sys.argv[1]);expected_job=sys.argv[2]
assert job_path.parent==ROOT/'Verification/project-knowledge-explorer-first-release/qualification-tests'
assert job_path.name.startswith('host-native-at-')
job_raw=read_exact(job_path);assert digest(job_raw)==expected_job
job=json.loads(job_raw);original=pathlib.Path(job['staging_root'])
assert str(original).startswith('/private/tmp/explorer-qualification-native-at-')
assert job['command']==[str(ROOT/'.venv/bin/python'),'-I','-B',str(original/'host-native-at-driver.py')]
assert job['source_writes'] is False and job['timeout_seconds']==900
assert pathlib.Path(job['manifest']['path'])==original/'inputs.json'
manifest_raw=read_exact(original/'inputs.json');assert digest(manifest_raw)==job['manifest']['sha256']
records=json.loads(manifest_raw)['files'];assert len(records)==job['inputs_count']==107
assert len({r['path'] for r in records})==len(records)
captured={};total=0
for row in records:
    relative=pathlib.PurePosixPath(row['path'])
    assert not relative.is_absolute() and all(p not in ('','.','..') for p in row['path'].split('/'))
    raw=read_exact(original/row['path']);assert len(raw)==row['bytes'] and digest(raw)==row['sha256']
    captured[row['path']]=raw;total+=len(raw);assert total<=64*1024*1024
assert 'host-native-at-driver.py' in captured
expected_build=json.loads(captured['SKILLS-depo/ontology/explorer/assets/manifest.json'])['build_id']
assert isinstance(expected_build,str) and len(expected_build)==64 and all(c in '0123456789abcdef' for c in expected_build)
for tool in job['external_tools']:
    assert str(pathlib.Path(tool['path']).resolve(strict=True))==tool['resolved']
    raw=read_exact(tool['resolved'],maximum=max(4*1024*1024,tool['bytes']))
    assert digest(raw)==tool['sha256'] and len(raw)==tool['bytes']
output=pathlib.Path(tempfile.mkdtemp(prefix='explorer-native-at-host-',dir='/private/tmp'))
execution=output/'captured-stage';execution.mkdir(mode=0o700)
for name,raw in captured.items():write_new(execution/name,raw)
write_new(execution/'inputs.json',manifest_raw);write_new(output/'reviewed-job.json',job_raw)
write_new(output/'host-wrapper.py',read_exact(pathlib.Path(__file__).absolute()))
command=[*job['command'][:3],str(execution/'host-native-at-driver.py')]
receipt={'schema_version':1,'actor':'/root','job':{'path':str(job_path),'sha256':expected_job},
'reviewed_command':job['command'],'actual_command':command,'original_stage':str(original),'execution_stage':str(execution),
'method':'No-follow, stable-identity, size/hash verified inputs copied unchanged into an exclusively created root-private stage. Safe readiness is streamed; manual UI evidence is separate. A fixed stop control signals only the retained driver Popen. No Safari process or unrelated window is terminated.',
'admitted_files':len(records),'admitted_bytes':total,'manifest_sha256':digest(manifest_raw),'external_tools':job['external_tools'],
'started_unix':time.time(),'root_wrapper_pid':os.getpid(),'host_wrapper_sha256':digest(read_exact(output/'host-wrapper.py'))}
write_new(output/'admission.json',json_bytes(receipt))
print(json.dumps({'status':'running','receipt_directory':str(output),'admitted_files':len(records)}),flush=True)
started=time.monotonic();process=None;known={};stderr_hash=hashlib.sha256();stderr_size=0;stdout_size=0
pending=bytearray();events=[];host_error=None;timed_out=False;output_limit=False;stop_requested=False;stop_sent=None;ready=None;final=None;emergency=[]
def stop_wrapper(signum,frame):
    global stop_requested
    stop_requested=True
signal.signal(signal.SIGTERM,stop_wrapper);signal.signal(signal.SIGINT,stop_wrapper)
def observe():
    rows=processes();front={process.pid};found=set()
    while front:
        children={pid for pid,(ppid,stamp) in rows.items() if ppid in front and pid not in found}
        for pid in children:known[pid]=rows[pid][1]
        found.update(children);front=children
    return rows

def consume(line):
    global ready,final
    value=json.loads(line);assert isinstance(value,dict)
    if value.get('status')=='native_ready':
        from urllib.parse import urlsplit
        assert ready is None and final is None
        assert set(value)=={'status','browser','owned_window_id','clean_url','origin','bootstrap_removed','context_response_processed','fixture_identity','build_id','service_instance'}
        u=urlsplit(value['clean_url']);o=urlsplit(value['origin'])
        assert u.scheme==o.scheme=='http' and u.hostname==o.hostname=='127.0.0.1' and u.port==o.port
        assert u.path=='/' and u.query=='' and u.username is None and u.password is None
        assert u.fragment.startswith('/p/explorer-native-at/')
        assert value['browser']=='Safari' and isinstance(value['owned_window_id'],int)
        assert value['bootstrap_removed'] is value['context_response_processed'] is True
        assert value['fixture_identity']=='explorer-native-at'
        assert value['build_id']==expected_build
        assert isinstance(value['service_instance'],str) and len(value['service_instance'])<150
        ready=value;write_new(output/'native-ready.json',json_bytes(value));print(json.dumps(value),flush=True)
    else:
        assert final is None
        assert value.get('status') in ('completed','timeout','failed')
        assert set(value)<= {'status','reason','exception_type','native_ready','owned_window_id','observed_read_operations','qualification','owned_read_worker_reaped','fixture_regular_files_unchanged','owned_safari_window_closed','owned_document_origin_absent','stage_inputs_unchanged'}
        assert all(set(r)=={'operation','status'} and r['operation'] in ('context','search','entry','relationships','neighborhood','source') and r['status'] in ('ok','error','incomplete','empty','ambiguous','source_changed') for r in value.get('observed_read_operations',[]))
        final=value
    events.append(value)
try:
    process=subprocess.Popen(command,cwd=execution,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},start_new_session=True)
    driver_stamp=processes().get(process.pid,(None,None))[1];assert driver_stamp
    write_new(output/'driver-identity.json',json_bytes({'pid':process.pid,'start_identity':driver_stamp,'command':command}))
    selector=selectors.DefaultSelector();selector.register(process.stdout,selectors.EVENT_READ,'stdout');selector.register(process.stderr,selectors.EVENT_READ,'stderr');next_observation=0
    while selector.get_map():
        now=time.monotonic()
        if now>=next_observation:observe();next_observation=now+.5
        control=output/'request-stop.json'
        if not stop_requested and control.exists():
            assert json.loads(read_exact(control,4096))=={'operation':'stop'};stop_requested=True
        if now-started>job['timeout_seconds']:timed_out=True;stop_requested=True
        if stop_requested and stop_sent is None and process.poll() is None:
            assert processes().get(process.pid,(None,None))[1]==driver_stamp
            process.send_signal(signal.SIGTERM);stop_sent=now
        if stop_sent is not None and now-stop_sent>20 and process.poll() is None:
            host_error='DriverDidNotExitAfterStop';break
        for key,event in selector.select(.2):
            block=os.read(key.fileobj.fileno(),65536)
            if not block:selector.unregister(key.fileobj);continue
            if key.data=='stdout':
                stdout_size+=len(block);pending.extend(block)
                if stdout_size>2*1024*1024:output_limit=True;break
                while b'\n' in pending:
                    line,_,rest=pending.partition(b'\n');pending=bytearray(rest)
                    if line:consume(line)
            else:
                stderr_hash.update(block);stderr_size+=len(block)
                if stderr_size>2*1024*1024:output_limit=True;break
        if output_limit:break
    selector.close()
    if pending:consume(bytes(pending))
    if not host_error and not output_limit:process.wait(timeout=5)
except BaseException as error:host_error=type(error).__name__
finally:
    signal.signal(signal.SIGTERM,signal.SIG_IGN)
    if process is not None and process.poll() is None:
        # Do not signal the process group: Safari is a shared native application.
        process.terminate()
        try:process.wait(timeout=10)
        except subprocess.TimeoutExpired:process.kill();process.wait(timeout=3);emergency.append({'pid':process.pid,'signal':9})
    rows=processes();alive=[pid for pid,stamp in known.items() if pid in rows and rows[pid][1]==stamp]
    # Only explicitly recognized executor descendants may be cleaned; Safari is never included.
    for pid in list(alive):
        r=subprocess.run(['/bin/ps','-p',str(pid),'-o','comm='],capture_output=True,text=True,timeout=3)
        name=pathlib.Path(r.stdout.strip()).name
        if name not in ('Python','python3.12','osascript'):continue
        if processes().get(pid,(None,None))[1]!=known[pid]:continue
        try:os.kill(pid,signal.SIGTERM);emergency.append({'pid':pid,'signal':15})
        except ProcessLookupError:pass
    if alive:time.sleep(.3)
    rows=processes();alive=[pid for pid,stamp in known.items() if pid in rows and rows[pid][1]==stamp]
post_errors=[]
for base in (original,execution):
    for row in records:
        try:
            raw=read_exact(base/row['path']);assert len(raw)==row['bytes'] and digest(raw)==row['sha256']
        except Exception:post_errors.append({'base':str(base),'path':row['path']})
    try:assert read_exact(base/'inputs.json')==manifest_raw
    except Exception:post_errors.append({'base':str(base),'path':'inputs.json'})
try:assert read_exact(job_path)==job_raw
except Exception:post_errors.append({'path':str(job_path)})
write_new(output/'stdout-events.json',json_bytes(events))
if final:write_new(output/'stdout.json',json_bytes(final))
receipt.update(exit_code=process.returncode if process else None,elapsed_seconds=time.monotonic()-started,timed_out=timed_out,output_limit=output_limit,host_error=host_error,stderr_bytes=stderr_size,stderr_sha256=stderr_hash.hexdigest(),raw_stderr_retained=False,stdout_bytes=stdout_size,known_descendant_count=len(known),observed_descendants_exited=not alive,remaining_owned_descendants=alive,emergency_signals=emergency,post_verification_errors=post_errors,native_ready=ready is not None,result_status=final.get('status') if final else 'unavailable',stop_requested=stop_requested)
receipt['status']='passed' if final and final['status']=='completed' and final.get('owned_read_worker_reaped') and final.get('fixture_regular_files_unchanged') and final.get('owned_document_origin_absent') and final.get('stage_inputs_unchanged') and receipt['exit_code']==0 and not alive and not post_errors and not host_error and not timed_out and not output_limit else 'failed'
receipt['qualification']='This receipt verifies driver execution and cleanup only. Actual keyboard/VoiceOver/zoom/reflow/restoration findings must be recorded separately; no accessibility pass is inferred here.'
write_new(output/'receipt.json',json_bytes(receipt))
print(json.dumps({'status':receipt['status'],'receipt_directory':str(output),'receipt_sha256':digest(read_exact(output/'receipt.json')),'result_status':receipt['result_status'],'host_error':host_error,'owned_descendants_exited':not alive,'post_verification_errors':len(post_errors),'raw_stderr_bytes':stderr_size}),flush=True)
raise SystemExit(0 if receipt['status']=='passed' else 1)
