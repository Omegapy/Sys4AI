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
assert job_path.parent == ROOT/'Verification/project-knowledge-explorer-first-release/frontend-tests/process-catalog-correction'
assert job_path.name.startswith('host-browser-job-')
job_raw = read_exact(job_path); assert digest(job_raw) == expected_job
job = json.loads(job_raw); assert job['kind'] == 'catalog'; original = pathlib.Path(job['stage'])
assert str(original).startswith('/private/tmp/explorer-process-catalog-browser-')
assert job['command'] == [str(ROOT/'.venv/bin/python'), '-I', '-B', str(original/'host-playwright-driver.py')]
assert job['timeout_seconds'] == 180
assert pathlib.Path(job['manifest']['path']) == original/'inputs.json'
manifest_raw = read_exact(original/'inputs.json'); assert digest(manifest_raw) == job['manifest']['sha256']
manifest = json.loads(manifest_raw); records = manifest['files']
assert len(records) == job['inputs_count'] == 111
assert len({r['path'] for r in records}) == len(records)
captured = {}; total = 0
for row in records:
    relative = pathlib.PurePosixPath(row['path'])
    assert not relative.is_absolute() and all(p not in ('', '.', '..') for p in row['path'].split('/'))
    raw = read_exact(original/row['path']); assert len(raw) == row['bytes'] and digest(raw) == row['sha256']
    captured[row['path']] = raw; total += len(raw); assert total <= 64*1024*1024
assert 'host-playwright-driver.py' in captured and all(name in captured for name in ('browser-catalog.cjs','catalog-fixture.py','mutate-catalog.py'))
assert captured['browser-catalog.cjs'] == read_exact(job_path.parent/'browser-catalog.cjs')
assert captured['host-playwright-driver.py'] == read_exact(job_path.parent/'host-catalog.py')
assert captured['catalog-fixture.py'] == read_exact(job_path.parent/'catalog-fixture.py')
assert captured['mutate-catalog.py'] == read_exact(job_path.parent/'mutate-catalog.py')
expected_checks = {
 'non_starting_recorded_labels_duplicate_identities_and_sequential_catalog',
 'truncated_catalog_name_disclosed_and_full_recorded_name_read',
 'late_header_updates_same_focused_link_and_presentation_does_not_restart',
 'actual_production_10s_deadline_late_rejection_and_keyboard_retry_focus',
 'abort_insensitive_catalog_reply_cannot_restore_obsolete_route',
 'atomic_snapshot_refresh_uses_new_catalog_and_rejects_held_old_name',
 'closed_session_rejects_held_catalog_reply_and_keeps_exact_process_link',
}
external_tools = []
for selected in [ROOT/'.venv/bin/python', pathlib.Path('/bin/ps'), pathlib.Path('/Users/alex.omegapy/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'), pathlib.Path('/Users/alex.omegapy/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/package.json'), pathlib.Path('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')]:
    resolved = selected.resolve(strict=True); raw = read_exact(resolved, maximum=256*1024*1024)
    external_tools.append({'path':str(selected),'resolved':str(resolved),'bytes':len(raw),'sha256':digest(raw)})

output = pathlib.Path(tempfile.mkdtemp(prefix='explorer-keyboard-browser-host-', dir='/private/tmp'))
execution = output/'captured-stage'; execution.mkdir(mode=0o700)
for name, raw in captured.items(): write_new(execution/name, raw)
write_new(execution/'inputs.json', manifest_raw)
write_new(output/'reviewed-job.json', job_raw)
write_new(output/'host-wrapper.py', read_exact(pathlib.Path(__file__).absolute()))
command = [*job['command'][:-1], str(execution/'host-playwright-driver.py')]
receipt = {'schema_version':1, 'actor':'/root', 'job':{'path':str(job_path),'sha256':expected_job},
    'reviewed_command':job['command'], 'actual_command':command, 'original_stage':str(original),
    'execution_stage':str(execution), 'method':'Every stage component was opened without following symlinks. Regular single-link bytes and stable identities were verified, then copied byte-for-byte into an exclusively created root-owned private execution tree. Only the staging directory changes; no test or production bytes are edited.',
    'admitted_files':len(records), 'admitted_bytes':total, 'manifest_sha256':digest(manifest_raw),
    'external_tools':external_tools, 'started_unix':time.time(), 'root_wrapper_pid':os.getpid(),
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
for tool in external_tools:
    try:
        assert str(pathlib.Path(tool['path']).resolve(strict=True)) == tool['resolved']
        raw = read_exact(tool['resolved'], maximum=256*1024*1024)
        assert len(raw) == tool['bytes'] and digest(raw) == tool['sha256']
    except Exception: post_errors.append({'path':tool['path'],'kind':'external_tool'})
try: assert read_exact(job_path) == job_raw
except Exception: post_errors.append({'path':str(job_path)})
result = None
if not timed_out and not output_limit and not host_error:
    try:
        result = json.loads(captured_out)
        assert isinstance(result,dict) and result.get('status') in ('passed','failed')
        assert b'bootstrap=' not in captured_out and b'sys4ai_explorer_' not in captured_out
        write_new(output/'stdout.json', bytes(captured_out))
        if result['status'] == 'passed':
            assert {check['name'] for check in result['checks']} == expected_checks and len(result['checks']) == len(expected_checks)
            assert all(check['status'] == 'passed' for check in result['checks'])
            assert result['node_exit_code'] == result['page_errors'] == result['nonlocal_requests'] == 0
            assert result['csp_violations'] == []
            assert result['observed_browser_descendants_exited'] and result['owned_read_worker_reaped']
            assert result['stage_inputs_unchanged'] and result['fixture_changes_within_declared_test_paths']
            assert len(result['fixture_changes']) == 1 and result['fixture_changes'][0].startswith('ONTOLOGY/modules/project/')
            assert result['fixture_regular_files_unchanged'] is False
            assert result['fixture_partition_exact_expected'] is True
            assert result['fixture_partition_unchanged'] is False
            assert result['all_other_partition_values_unchanged'] is True
            deadline = next(row for row in result['checks'] if row['name'] == 'actual_production_10s_deadline_late_rejection_and_keyboard_retry_focus')
            assert 9900 <= deadline['elapsed_ms'] < 14500
            assert deadline['abort_ignored_intentionally'] is deadline['real_http_response_held'] is deadline['production_timer_unmodified'] is True
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
    'result_status':receipt['result_status'],'browser_checks':len(result.get('checks',[])) if result else None,'browser_version':result.get('browser') if result else None,
    'failures':result.get('failures') if result else None,'errors':result.get('errors') if result else None,
    'elapsed_seconds':receipt['elapsed_seconds'],'owned_descendants_exited':not alive,
    'post_verification_errors':len(post_errors),'raw_stderr_bytes':stderr_size}),flush=True)
raise SystemExit(0 if receipt['status']=='passed' else 1)
