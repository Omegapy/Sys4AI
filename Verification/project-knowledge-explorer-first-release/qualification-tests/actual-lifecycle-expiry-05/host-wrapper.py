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

job_path = pathlib.Path(sys.argv[1]); expected_job = sys.argv[2]
assert job_path.parent == ROOT/'Verification/project-knowledge-explorer-first-release/qualification-tests'
assert job_path.name.startswith('host-lifecycle-browser-')
job_raw = read_exact(job_path); assert digest(job_raw) == expected_job
job = json.loads(job_raw); original = pathlib.Path(job['staging_root'])
assert str(original).startswith('/private/tmp/explorer-qualification-lifecycle-browser-')
mode = job['command'][-1]; assert mode in ('expiry','stop','entry_deadline')
assert job['command'] == [str(ROOT/'.venv/bin/python'), '-I', '-B', str(original/'host-lifecycle-browser.py'), mode]
assert job['source_writes'] is False and job['timeout_seconds'] <= 300
assert pathlib.Path(job['manifest']['path']) == original/'inputs.json'
manifest_raw = read_exact(original/'inputs.json'); assert digest(manifest_raw) == job['manifest']['sha256']
manifest = json.loads(manifest_raw); records = manifest['files']
assert len(records) == job['inputs_count'] and len(records) <= 250
assert len({r['path'] for r in records}) == len(records)
captured = {}; total = 0
for row in records:
    relative = pathlib.PurePosixPath(row['path'])
    assert not relative.is_absolute() and all(p not in ('', '.', '..') for p in row['path'].split('/'))
    raw = read_exact(original/row['path']); assert len(raw) == row['bytes'] and digest(raw) == row['sha256']
    captured[row['path']] = raw; total += len(raw); assert total <= 64*1024*1024
assert 'host-lifecycle-browser.py' in captured
expected_checks = {('AT-06 ' if mode == 'entry_deadline' else 'AT-23 ')+mode+' retains exact recorded entry and desired route with explicit reopening guidance'}
for tool in job['external_tools']:
    assert str(pathlib.Path(tool['path']).resolve(strict=True)) == tool['resolved']
    assert tool['bytes'] <= 256*1024*1024
    raw = read_exact(tool['resolved'], maximum=max(4*1024*1024, tool['bytes'])); assert digest(raw) == tool['sha256'] and len(raw) == tool['bytes']

output = pathlib.Path(tempfile.mkdtemp(prefix='explorer-lifecycle-browser-host-', dir='/private/tmp'))
execution = output/'captured-stage'; execution.mkdir(mode=0o700)
for name, raw in captured.items(): write_new(execution/name, raw)
write_new(execution/'inputs.json', manifest_raw)
write_new(output/'reviewed-job.json', job_raw)
write_new(output/'host-wrapper.py', read_exact(pathlib.Path(__file__).absolute()))
command = [*job['command'][:3], str(execution/'host-lifecycle-browser.py'), mode]
receipt = {'schema_version':1, 'actor':'/root', 'job':{'path':str(job_path),'sha256':expected_job},
    'reviewed_command':job['command'], 'actual_command':command, 'original_stage':str(original),
    'execution_stage':str(execution), 'method':'Every stage component was opened without following symlinks. Regular single-link bytes and stable identities were verified, then copied byte-for-byte into an exclusively created root-owned private execution tree. Only the staging directory changes; no test or production bytes are edited.',
    'admitted_files':len(records), 'admitted_bytes':total, 'manifest_sha256':digest(manifest_raw),
    'external_tools':job['external_tools'], 'started_unix':time.time(), 'root_wrapper_pid':os.getpid(),
    'host_wrapper_sha256':digest((output/'host-wrapper.py').read_bytes()), 'expected_checks':sorted(expected_checks)}
write_new(output/'admission.json', json_bytes(receipt))
print(json.dumps({'status':'running','receipt_directory':str(output),'admitted_files':len(records)}), flush=True)
started = time.monotonic(); process = None; known = {}; signals = []; captured_out = bytearray(); stderr_hash = hashlib.sha256(); stderr_size = 0
timed_out = False; output_limit = False; host_error = None
def interrupted(signum, frame): raise KeyboardInterrupt()
signal.signal(signal.SIGTERM, interrupted)

def observe():
    rows = processes(); front = {process.pid}; found = set()
    while front:
        children = {pid for pid, (ppid, stamp) in rows.items() if ppid in front and pid not in found}
        for pid in children: known[pid] = rows[pid][1]
        found.update(children); front = children
    return rows

try:
    process = subprocess.Popen(command, cwd=execution, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        env={**os.environ, 'PYTHONDONTWRITEBYTECODE':'1'}, start_new_session=True)
    selector = selectors.DefaultSelector()
    selector.register(process.stdout, selectors.EVENT_READ, 'stdout'); selector.register(process.stderr, selectors.EVENT_READ, 'stderr')
    next_observation = 0
    while selector.get_map():
        now = time.monotonic()
        if now >= next_observation: observe(); next_observation = now + 0.5
        if now - started > job['timeout_seconds']: timed_out = True; break
        for key, event in selector.select(0.2):
            block = os.read(key.fileobj.fileno(), 65536)
            if not block: selector.unregister(key.fileobj); continue
            if key.data == 'stdout':
                captured_out.extend(block)
                if len(captured_out) > 2*1024*1024: output_limit = True; break
            else:
                stderr_hash.update(block); stderr_size += len(block)
                if stderr_size > 2*1024*1024: output_limit = True; break
        if output_limit: break
    selector.close()
    if not timed_out and not output_limit:
        try: process.wait(timeout=3)
        except subprocess.TimeoutExpired: host_error = 'ProcessDidNotExitAfterOutput'
except BaseException as error:
    host_error = type(error).__name__
finally:
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    if process is not None:
        if process.poll() is None:
            try: os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError: pass
            try: process.wait(timeout=8)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL); process.wait(timeout=3)
        for sig in (signal.SIGTERM, signal.SIGKILL):
            rows = processes(); alive = [pid for pid, stamp in known.items() if pid in rows and rows[pid][1] == stamp]
            for pid in alive:
                try: os.kill(pid, sig); signals.append({'pid':pid,'signal':int(sig)})
                except ProcessLookupError: pass
            if alive: time.sleep(0.3)
        rows = processes(); alive = [pid for pid, stamp in known.items() if pid in rows and rows[pid][1] == stamp]
    else: alive = []

post_errors = []
for base in (original, execution):
    for row in records:
        try:
            raw = read_exact(base/row['path']); assert len(raw) == row['bytes'] and digest(raw) == row['sha256']
        except Exception: post_errors.append({'base':str(base),'path':row['path']})
    try: assert read_exact(base/'inputs.json') == manifest_raw
    except Exception: post_errors.append({'base':str(base),'path':'inputs.json'})
try: assert read_exact(job_path) == job_raw
except Exception: post_errors.append({'path':str(job_path)})
result = None
if not timed_out and not output_limit and not host_error:
    try:
        result = json.loads(captured_out)
        assert isinstance(result,dict) and result.get('status') in ('passed','failed')
        if result['status'] == 'passed':
            assert {check['name'] for check in result['checks']} == expected_checks and len(result['checks']) == len(expected_checks)
            assert all(check['status'] == 'passed' for check in result['checks'])
            assert result['node_exit_code'] == result['page_errors'] == result['nonlocal_requests'] == 0
            assert result['csp_violations'] == [] and result['mode'] == mode
            assert result['checks'][0]['session_seconds'] == 60 and result['checks'][0]['clock_unchanged'] is True
            if mode == 'expiry': assert result['checks'][0]['elapsed_ms'] >= 59000
            if mode == 'entry_deadline':
                deadline = result['checks'][0]['deadline_evidence']
                assert deadline['http_status'] == 504 and deadline['error_code'] == 'deadline_exceeded'
                assert deadline['request_seconds'] == 5 and deadline['elapsed_ms'] >= 5000
                assert result['suspended_owned_worker_reaped'] is True
            assert result['observed_browser_descendants_exited'] and result['owned_read_worker_reaped']
            assert result['fixture_regular_files_unchanged'] and result['stage_inputs_unchanged']
        write_new(output/'stdout.json', bytes(captured_out))
    except Exception: result = None
receipt.update(exit_code=process.returncode if process else None, elapsed_seconds=time.monotonic()-started,
    timed_out=timed_out, output_limit=output_limit, host_error=host_error,
    stdout_bytes=len(captured_out), stdout_sha256=digest(captured_out), stderr_bytes=stderr_size,
    stderr_sha256=stderr_hash.hexdigest(), raw_stderr_retained=False, known_descendant_count=len(known),
    observed_descendants_exited=not alive, emergency_signals=signals, post_verification_errors=post_errors,
    result_status=result.get('status') if result else 'unavailable')
receipt['status'] = 'passed' if result and result['status']=='passed' and receipt['exit_code']==0 and not alive and not post_errors and not host_error and not timed_out and not output_limit else 'failed'
write_new(output/'receipt.json', json_bytes(receipt))
print(json.dumps({'status':receipt['status'],'receipt_directory':str(output),'receipt_sha256':digest((output/'receipt.json').read_bytes()),
    'result_status':receipt['result_status'],'browser_checks':len(result.get('checks',[])) if result else None,'browser_version':result.get('browser_version') if result else None,
    'failures':result.get('failures') if result else None,'errors':result.get('errors') if result else None,
    'elapsed_seconds':receipt['elapsed_seconds'],'owned_descendants_exited':not alive,
    'post_verification_errors':len(post_errors),'raw_stderr_bytes':stderr_size}),flush=True)
raise SystemExit(0 if receipt['status']=='passed' else 1)
