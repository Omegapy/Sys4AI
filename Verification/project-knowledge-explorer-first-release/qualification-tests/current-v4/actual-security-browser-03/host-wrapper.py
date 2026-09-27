"""Root-owned execution of one reviewed frozen qualification browser job."""
import ast, hashlib, json, os, pathlib, selectors, signal, stat, subprocess, sys, tempfile, time

ROOT = pathlib.Path('/Volumes/P-SSD/AngryOwl/Sys4AI')
RELEASE = ROOT/'Tasks/Task-implement-project-knowledge-explorer-full-first-release-2026-09-19--1FA1F620/artifacts/orchestration/manager/qualification-current-v4-security-browser03-release.json'
RELEASE_SHA = '0a46b0a4a45c7f058a3f5a42d46118f06efbb54d5fc1bdc28106e67512b20ed1'
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
assert job_path.name.startswith('host-security-browser-')
job_raw = read_exact(job_path); assert digest(job_raw) == expected_job
job = json.loads(job_raw); original = pathlib.Path(job['staging_root'])
assert str(original).startswith('/private/tmp/explorer-qualification-security-browser-')
assert job['command'] == [str(ROOT/'.venv/bin/python'), '-I', '-B', str(original/'host-security-browser.py')]
assert job['source_writes'] is False and job['timeout_seconds'] <= 300
assert pathlib.Path(job['manifest']['path']) == original/'inputs.json'
manifest_raw = read_exact(original/'inputs.json'); assert digest(manifest_raw) == job['manifest']['sha256']
release_raw = read_exact(RELEASE); assert digest(release_raw) == RELEASE_SHA
release = json.loads(release_raw)
assert release['job'] == {'path':str(job_path.relative_to(ROOT)), 'sha256':expected_job}
assert release['manifest']['sha256'] == job['manifest']['sha256']
assert release['command'] == job['command'] and release['timeout_seconds'] == job['timeout_seconds'] == 100
assert release['stage_members'] == job['inputs_count'] == 109
assert release['live_source_mapping'] == job['source_mapping']
assert release['external_tools'] == len(job['external_tools']) == 28
manifest = json.loads(manifest_raw); records = manifest['files']
assert len(records) == job['inputs_count'] and len(records) <= 250
assert len({r['path'] for r in records}) == len(records)
captured = {}; live_paths = {}; total = 0
assert set(job['source_mapping']) == {'host-security-browser.py','security-browser.cjs','test-browser-runtime.json'}
for row in records:
    relative = pathlib.PurePosixPath(row['path'])
    assert not relative.is_absolute() and all(p not in ('', '.', '..') for p in row['path'].split('/'))
    raw = read_exact(original/row['path']); assert len(raw) == row['bytes'] and digest(raw) == row['sha256']
    live_path = pathlib.Path(job['source_mapping'][row['path']]) if row['path'] in job['source_mapping'] else ROOT/row['path']
    assert live_path.is_absolute() and read_exact(live_path) == raw
    live_paths[row['path']] = live_path
    captured[row['path']] = raw; total += len(raw); assert total <= 64*1024*1024
assert 'host-security-browser.py' in captured
expected_checks = {
    'AT-27 malicious label is literal heading text without executable elements',
    'AT-27 hostile source HTML and javascript link are plain text with entry retained',
    'AT-27 malicious search result label remains inert literal text',
    'AT-27 real production CSP has no violations and no script/dialog/external execution',
}
assert set(release['actual_group_names']) == expected_checks and len(release['actual_group_names']) == 4
assert len({r['resolved'] for r in job['external_tools']}) == 28
for tool in job['external_tools']:
    assert str(pathlib.Path(tool['path']).resolve(strict=True)) == tool['resolved']
    assert tool['bytes'] <= 256*1024*1024
    raw = read_exact(tool['resolved'], maximum=max(4*1024*1024, tool['bytes'])); assert digest(raw) == tool['sha256'] and len(raw) == tool['bytes']
    if 'mode' in tool: assert stat.S_IMODE(os.stat(tool['resolved'],follow_symlinks=False).st_mode) == tool['mode']

def verify_runtime():
    spec = job['browser_runtime']; root = pathlib.Path(spec['complete_inventory_root'])
    assert not root.is_symlink() and spec['complete_file_count'] == 20
    runtime = json.loads(read_exact(original/spec['inventory_stage_file']))
    assert runtime['executable'] == spec['executable'] and runtime['supported_registry_entry']['browserVersion'] == spec['expected_version'] == '151.0.7922.34'
    assert runtime['file_count'] == 20 and runtime['symlinks'] == [] and len(runtime['complete_files']) == 20
    found = []
    for base, dirs, files in os.walk(root,followlinks=False):
        assert all(not (pathlib.Path(base)/name).is_symlink() for name in dirs + files)
        found.extend(str((pathlib.Path(base)/name).relative_to(root)) for name in files)
    runtime_pins = [r for r in job['external_tools'] if pathlib.Path(r['resolved']).is_relative_to(root)]
    assert len(runtime_pins) == 20 and set(found) == {str(pathlib.Path(r['resolved']).relative_to(root)) for r in runtime_pins}
    indexed = {r['path']:r for r in runtime['complete_files']}
    assert set(indexed) == set(found)
    for row in runtime_pins:
        relative = str(pathlib.Path(row['resolved']).relative_to(root))
        item = indexed[relative]
        assert item['sha256'] == row['sha256'] and item['bytes'] == row['bytes'] and item['mode'] == row['mode']
        raw = read_exact(row['resolved'], maximum=max(4*1024*1024,row['bytes']))
        assert len(raw) == row['bytes'] and digest(raw) == row['sha256']
        assert stat.S_IMODE(os.stat(row['resolved'],follow_symlinks=False).st_mode) == row['mode']
    return len(found)
assert verify_runtime() == 20
if len(sys.argv) == 4 and sys.argv[3] == '--admit-only':
    print(json.dumps({'status':'admitted','files':len(records),'live':len(live_paths),'tools':len(job['external_tools']),'runtime_files':20,'job_sha256':expected_job,'release_sha256':RELEASE_SHA}))
    raise SystemExit(0)
assert len(sys.argv) == 3

output = pathlib.Path(tempfile.mkdtemp(prefix='explorer-security-browser-host-', dir='/private/tmp'))
execution = output/'captured-stage'; execution.mkdir(mode=0o700)
for name, raw in captured.items(): write_new(execution/name, raw)
write_new(execution/'inputs.json', manifest_raw)
write_new(output/'reviewed-job.json', job_raw)
write_new(output/'reviewed-release.json', release_raw)
write_new(output/'host-wrapper.py', read_exact(pathlib.Path(__file__).absolute()))
command = [*job['command'][:-1], str(execution/'host-security-browser.py')]
receipt = {'schema_version':1, 'actor':'/root', 'job':{'path':str(job_path),'sha256':expected_job},
    'reviewed_command':job['command'], 'actual_command':command, 'original_stage':str(original),
    'execution_stage':str(execution), 'method':'Every stage component was opened without following symlinks. Regular single-link bytes and stable identities were verified, then copied byte-for-byte into an exclusively created root-owned private execution tree. Only the staging directory changes; no test or production bytes are edited.',
    'admitted_files':len(records), 'admitted_live_files':len(live_paths), 'admitted_bytes':total, 'manifest_sha256':digest(manifest_raw), 'release_sha256':RELEASE_SHA, 'runtime_files':20,
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
for row in records:
    try: assert read_exact(live_paths[row['path']]) == captured[row['path']]
    except Exception: post_errors.append({'base':'live','path':row['path']})
for tool in job['external_tools']:
    try:
        raw = read_exact(tool['resolved'], maximum=max(4*1024*1024,tool['bytes']))
        assert len(raw) == tool['bytes'] and digest(raw) == tool['sha256']
        if 'mode' in tool: assert stat.S_IMODE(os.stat(tool['resolved'],follow_symlinks=False).st_mode) == tool['mode']
    except Exception: post_errors.append({'base':'external_tool','path':tool['resolved']})
try: assert verify_runtime() == 20
except Exception: post_errors.append({'base':'runtime_inventory','path':job['browser_runtime']['complete_inventory_root']})
for path, original_raw in ((job_path,job_raw),(RELEASE,release_raw)):
    try: assert read_exact(path) == original_raw
    except Exception: post_errors.append({'path':str(path)})
if captured_out: write_new(output/'stdout.json', bytes(captured_out))
result = None
if not timed_out and not output_limit and not host_error:
    try:
        result = json.loads(captured_out)
        assert isinstance(result,dict) and result.get('status') in ('passed','failed')
        if result['status'] == 'passed':
            assert result['browser_version'] == '151.0.7922.34'
            assert {check['name'] for check in result['checks']} == expected_checks and len(result['checks']) == len(expected_checks)
            assert all(check['status'] == 'passed' for check in result['checks'])
            assert result['node_exit_code'] == result['page_errors'] == result['dialogs'] == result['nonlocal_requests'] == 0
            assert result['csp_violations'] == [] and result['fragment_removed_before_network'] is True
            assert result['observed_browser_descendants_exited'] and result['owned_read_worker_reaped']
            assert result['fixture_regular_files_unchanged'] and result['stage_inputs_unchanged']
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
