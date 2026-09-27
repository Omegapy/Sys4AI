"""Execute one released current TASK021 browser job from a private byte-exact copy."""
import hashlib
import json
import os
import pathlib
import selectors
import signal
import stat
import subprocess
import sys
import tempfile
import time

ROOT = pathlib.Path('/Volumes/P-SSD/AngryOwl/Sys4AI')
RELEASE = ROOT/'Tasks/Task-implement-project-knowledge-explorer-full-first-release-2026-09-19--1FA1F620/artifacts/orchestration/manager/qualification-current-v4-production07-diagnostic-release.json'
RELEASE_SHA = '4192f23a08b9e5f058299c4cef6664b18942f7127f160067938dbec0f0d2924a'
CONFIRM = ROOT/'Tasks/Task-implement-project-knowledge-explorer-full-first-release-2026-09-19--1FA1F620/artifacts/orchestration/manager/qualification-current-v4-production07-confirmation-release.json'
CONFIRM_SHA = 'afca0fb61f4cfdd660ec41bf14a48f6796208eb695057221b86f25641ecdbe82'
Q = ROOT/'Verification/project-knowledge-explorer-first-release/qualification-tests'
sha = lambda raw: hashlib.sha256(raw).hexdigest()

def read_exact(path, limit=256*1024*1024):
    path = pathlib.Path(path)
    assert path.is_absolute() and '..' not in path.parts
    parent = os.open('/', os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in path.parts[1:-1]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
            os.close(parent); parent = child
        fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
        try:
            first = os.fstat(fd)
            assert stat.S_ISREG(first.st_mode) and first.st_nlink == 1 and first.st_size <= limit
            blocks = []; total = 0
            while True:
                block = os.read(fd, min(1048576, limit+1-total))
                if not block: break
                blocks.append(block); total += len(block); assert total <= limit
            last = os.fstat(fd)
            bound = os.stat(path.name, dir_fd=parent, follow_symlinks=False)
            signature = lambda s: (s.st_dev,s.st_ino,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
            assert signature(first) == signature(last) == signature(bound)
            return b''.join(blocks)
        finally: os.close(fd)
    finally: os.close(parent)

def write_new(path, raw):
    path.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd,'wb') as stream:
        stream.write(raw); stream.flush(); os.fsync(stream.fileno())

def packed(value):
    return (json.dumps(value,sort_keys=True,indent=2)+'\n').encode()

def process_rows():
    result = subprocess.run(['/bin/ps','-axo','pid=,ppid=,lstart='],capture_output=True,text=True,timeout=3,check=True)
    rows = {}
    for line in result.stdout.splitlines():
        parts = line.split(None,2)
        if len(parts)==3 and parts[0].isdigit() and parts[1].isdigit(): rows[int(parts[0])] = (int(parts[1]),parts[2])
    return rows

release_raw = read_exact(RELEASE, 1000000); assert sha(release_raw) == RELEASE_SHA
release = json.loads(release_raw)
assert release['status'] == 'released_one_root_diagnostic_run' and 'job' in release
assert len(sys.argv) in (2,3) and sys.argv[1].isdigit()
index = int(sys.argv[1]); assert index == 0
entry = release['job']
confirm_raw = read_exact(CONFIRM,1000000); assert sha(confirm_raw) == CONFIRM_SHA
confirm = json.loads(confirm_raw)
assert confirm['status'] == 'released_one_bounded_diagnostic_confirmation'
assert confirm['prior_release'] == {'path':str(RELEASE.relative_to(ROOT)),'sha256':RELEASE_SHA}
assert confirm['job'] == entry['job']
for evidence in (confirm['passing_run'],confirm['failed_run']):
    for ref in evidence.values():
        raw = read_exact(ROOT/ref['path'],2*1024*1024)
        assert sha(raw) == ref['sha256']
job_path = ROOT/entry['job']['path']; assert job_path.parent == Q
job_raw = read_exact(job_path,1000000); assert sha(job_raw) == entry['job']['sha256']
job = json.loads(job_raw); stage = pathlib.Path(job['staging_root'])
assert stage == pathlib.Path(entry['manifest']['path']).parent and stage == pathlib.Path(job['manifest']['path']).parent
assert job['manifest'] == entry['manifest']
assert job['command'] == entry['command'] and job['timeout_seconds'] == entry['timeout_seconds']
assert job['source_mapping'] == entry['source_mapping']
assert job['browser_runtime'] == entry['runtime']
assert job['source_writes'] is False and job['inputs_count'] == entry['stage_members'] == 108
assert job['external_tools'] == release['external_tools'] and len(job['external_tools']) == 28
assert release['complete_runtime_files'] == 20
manifest_raw = read_exact(stage/'inputs.json',1000000)
assert sha(manifest_raw) == job['manifest']['sha256'] and len(manifest_raw) == entry['manifest']['bytes']
records = json.loads(manifest_raw)['files']
assert len(records) == 108 and len({r['path'] for r in records}) == 108
runner = pathlib.Path(job['command'][3]).name
assert job['command'][:3] == [str(ROOT/'.venv/bin/python'),'-I','-B'] and job['command'][3] == str(stage/runner)
mode = entry['mode']
assert job['command'][4:] == ([mode] if mode is not None else [])
assert (index < 2 and mode is None) or (index >= 2 and mode in ('stop','entry_deadline','expiry'))
assert set(job['source_mapping']) == {runner, 'test-browser-runtime.json', runner.removeprefix('host-').removesuffix('.py')+'.cjs'}
expected = set(entry['actual_group_names']); assert len(expected) == entry['expected_groups'] and len(expected) in (1,4,9)
live_paths = {}; captured = {}; total = 0
for row in records:
    name = row['path']; parts = name.split('/')
    assert not name.startswith('/') and all(part not in ('','.','..') for part in parts)
    raw = read_exact(stage/name,max(4*1024*1024,row['bytes']))
    assert len(raw) == row['bytes'] and sha(raw) == row['sha256']
    live = pathlib.Path(job['source_mapping'][name]) if name in job['source_mapping'] else ROOT/name
    assert live.is_absolute() and read_exact(live,max(4*1024*1024,row['bytes'])) == raw
    live_paths[name] = live; captured[name] = raw; total += len(raw); assert total <= 64*1024*1024

def verify_tools_runtime():
    spec = job['browser_runtime']; root = pathlib.Path(spec['complete_inventory_root'])
    assert not root.is_symlink() and spec['complete_file_count'] == 20 and spec['expected_version'] == '151.0.7922.34'
    assert spec['executable'] == '/Users/alex.omegapy/Library/Caches/ms-playwright/chromium_headless_shell-1234/chrome-headless-shell-mac-arm64/chrome-headless-shell'
    runtime = json.loads(read_exact(stage/spec['inventory_stage_file'],1000000))
    assert runtime['executable'] == spec['executable'] and runtime['supported_registry_entry']['browserVersion'] == spec['expected_version']
    assert runtime['file_count'] == 20 and runtime['symlinks'] == [] and len(runtime['complete_files']) == 20
    listed = {}
    for base, dirs, files in os.walk(root,followlinks=False):
        assert all(not (pathlib.Path(base)/name).is_symlink() for name in dirs + files)
        for name in files: listed[str((pathlib.Path(base)/name).relative_to(root))] = pathlib.Path(base)/name
    pins = job['external_tools']; assert len({r['resolved'] for r in pins}) == 28
    runtime_pins = [r for r in pins if pathlib.Path(r['resolved']).is_relative_to(root)]
    assert len(runtime_pins) == len(listed) == 20
    indexed = {r['path']:r for r in runtime['complete_files']}
    assert set(indexed) == set(listed) == {str(pathlib.Path(r['resolved']).relative_to(root)) for r in runtime_pins}
    for row in pins:
        assert str(pathlib.Path(row['path']).resolve(strict=True)) == row['resolved']
        raw = read_exact(row['resolved'],max(4*1024*1024,row['bytes']))
        assert len(raw) == row['bytes'] and sha(raw) == row['sha256']
        if 'mode' in row: assert stat.S_IMODE(os.stat(row['resolved'],follow_symlinks=False).st_mode) == row['mode']
    for row in runtime_pins:
        item = indexed[str(pathlib.Path(row['resolved']).relative_to(root))]
        assert (item['sha256'],item['bytes'],item['mode']) == (row['sha256'],row['bytes'],row['mode'])
    return len(listed)
assert verify_tools_runtime() == 20
if len(sys.argv)==3 and sys.argv[2]=='--admit-only':
    print(json.dumps({'status':'admitted','index':index,'files':len(records),'live':len(live_paths),'tools':28,'runtime_files':20,'job_sha256':entry['job']['sha256']}))
    raise SystemExit(0)
assert len(sys.argv)==2
out = pathlib.Path(tempfile.mkdtemp(prefix='explorer-task021-host-',dir='/private/tmp'))
execution = out/'captured-stage'; execution.mkdir(mode=0o700)
for name,raw in captured.items(): write_new(execution/name,raw)
write_new(execution/'inputs.json',manifest_raw)
write_new(out/'reviewed-job.json',job_raw)
write_new(out/'reviewed-release.json',release_raw)
write_new(out/'reviewed-confirmation-release.json',confirm_raw)
write_new(out/'host-wrapper.py',read_exact(pathlib.Path(__file__).absolute(),1000000))
command = [*job['command'][:3],str(execution/runner),*job['command'][4:]]
receipt = {'schema_version':1,'actor':'/root','release_sha256':RELEASE_SHA,'index':index,
 'job':entry['job'],'confirmation_release_sha256':CONFIRM_SHA,'reviewed_command':job['command'],'actual_command':command,
 'original_stage':str(stage),'execution_stage':str(execution),'admitted_files':108,'admitted_live_files':108,
 'external_tool_count':28,'runtime_inventory_count':20,'manifest_sha256':sha(manifest_raw),
 'wrapper_sha256':sha((out/'host-wrapper.py').read_bytes()),'started_unix':time.time(),
 'expected_checks':sorted(expected),'mode':mode}
write_new(out/'admission.json',packed(receipt))
print(json.dumps({'status':'running','index':index,'receipt_directory':str(out),'admitted_files':108}),flush=True)
start=time.monotonic(); process=None; known={}; signals=[]; stdout=bytearray(); stderr_hash=hashlib.sha256(); stderr_size=0
error=None; timed_out=False; output_limit=False

def interrupted(signum,frame): raise KeyboardInterrupt()
signal.signal(signal.SIGTERM,interrupted)
def observe():
    rows=process_rows(); front={process.pid}; found=set()
    while front:
        children={pid for pid,(ppid,stamp) in rows.items() if ppid in front and pid not in found}
        for pid in children: known[pid]=rows[pid][1]
        found.update(children);front=children
    return rows
try:
    process=subprocess.Popen(command,cwd=execution,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                             env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},start_new_session=True)
    sel=selectors.DefaultSelector();sel.register(process.stdout,selectors.EVENT_READ,'stdout');sel.register(process.stderr,selectors.EVENT_READ,'stderr')
    next_observation=0
    while sel.get_map():
        now=time.monotonic()
        if now>=next_observation: observe();next_observation=now+0.5
        if now-start>job['timeout_seconds']: timed_out=True;break
        for key,event in sel.select(0.2):
            block=os.read(key.fileobj.fileno(),65536)
            if not block:sel.unregister(key.fileobj);continue
            if key.data=='stdout':
                stdout.extend(block)
                if len(stdout)>2*1024*1024:output_limit=True;break
            else:
                stderr_hash.update(block);stderr_size+=len(block)
                if stderr_size>2*1024*1024:output_limit=True;break
        if output_limit:break
    sel.close()
    if not timed_out and not output_limit:
        try:process.wait(timeout=3)
        except subprocess.TimeoutExpired:error='ProcessDidNotExitAfterOutput'
except BaseException as exc:error=type(exc).__name__
finally:
    signal.signal(signal.SIGTERM,signal.SIG_IGN)
    if process is not None:
        if process.poll() is None:
            try:os.killpg(process.pid,signal.SIGTERM)
            except ProcessLookupError:pass
            try:process.wait(timeout=8)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid,signal.SIGKILL);process.wait(timeout=3)
        for sig in (signal.SIGTERM,signal.SIGKILL):
            rows=process_rows();alive=[pid for pid,stamp in known.items() if pid in rows and rows[pid][1]==stamp]
            for pid in alive:
                try:os.kill(pid,sig);signals.append({'pid':pid,'signal':int(sig)})
                except ProcessLookupError:pass
            if alive:time.sleep(0.3)
        rows=process_rows();alive=[pid for pid,stamp in known.items() if pid in rows and rows[pid][1]==stamp]
    else:alive=[]
post=[]
for base in (stage,execution):
    for row in records:
        try:assert read_exact(base/row['path'],max(4*1024*1024,row['bytes'])) == captured[row['path']]
        except Exception:post.append({'base':str(base),'path':row['path']})
    try:assert read_exact(base/'inputs.json',1000000) == manifest_raw
    except Exception:post.append({'base':str(base),'path':'inputs.json'})
for row in records:
    try:assert read_exact(live_paths[row['path']],max(4*1024*1024,row['bytes'])) == captured[row['path']]
    except Exception:post.append({'base':'live','path':row['path']})
try:assert verify_tools_runtime()==20
except Exception:post.append({'base':'external_tools_or_runtime','path':job['browser_runtime']['complete_inventory_root']})
for path,raw in ((job_path,job_raw),(RELEASE,release_raw),(CONFIRM,confirm_raw)):
    try:assert read_exact(path,1000000)==raw
    except Exception:post.append({'path':str(path)})
if stdout:write_new(out/'stdout.json',bytes(stdout))
result=None;assessment_error=None
if not timed_out and not output_limit and not error:
    try:
        result=json.loads(stdout)
        assert isinstance(result,dict) and result.get('status') in ('passed','failed')
        if result['status']=='passed':
            assert result['browser_version']=='151.0.7922.34'
            assert {c['name'] for c in result['checks']}==expected and len(result['checks'])==len(expected)
            assert all(c['status']=='passed' for c in result['checks'])
            assert result['node_exit_code']==result['page_errors']==result['nonlocal_requests']==0
            assert result['observed_browser_descendants_exited'] and result['owned_read_worker_reaped']
            assert result['fixture_regular_files_unchanged'] and result['stage_inputs_unchanged']
            if index==0:
                assert result['csp_violations']==[] and result['fragment_removed_before_network'] is True
                assert result['optional_paths_absent'] is True and result['publication_enabled'] is False
                assert result['generated_files_unchanged'] and result['generated_absences_preserved']
                g=result['generated_state'];assert g['setup_status']=='complete'
                assert g['actual_stale_index_sha256'] != g['recorded_owned_hashes']['ONTOLOGY/WIKI/INDEX.md']
                assert g['absent']==['ONTOLOGY/WIKI/concepts.md']
            elif index==1:
                assert result['renderer_requests_explicitly_blocked']==1
                targets={'search','first_exact_result','entry_sources','selected_entry_source','returned_source_trigger','open_relationships','request_renderer','equivalent_list','list_select_term','list_more_connections','list_focus_here','processes','ordered_process_by_recorded_label','recorded_step_source'}
                assert len(result['traversals'])==14 and {r['target'] for r in result['traversals']}==targets
                for row in result['traversals']:
                    rect=row['rect'];x=rect['x']+rect['width']/2;y=rect['y']+rect['height']/2
                    assert row['center_in_viewport'] and row['center_visible'] and 0<=x<1280 and 0<=y<900
                assert all('not observed screen-reader speech' in r['qualification'] for r in result['live_regions'])
                catalog=result['process_catalog_observation'];assert catalog['recorded_label_present'] is True
                assert catalog['recorded_label']=='Fixture ordered inspection' and catalog['visible_text'].strip()=='Fixture ordered inspection'
                assert 'entry-00014' in catalog['href']
            else:
                assert result['mode']==mode and result['csp_violations']==[]
                check=result['checks'][0];assert check['session_seconds']==60 and check['clock_unchanged'] is True
                if mode=='expiry':assert check['elapsed_ms']>=59000
                if mode=='entry_deadline':
                    d=check['deadline_evidence'];assert d['http_status']==504 and d['error_code']=='deadline_exceeded'
                    assert d['request_seconds']==5 and d['elapsed_ms']>=5000
                    assert result['suspended_owned_worker_reaped'] is True
                assert result['fixture_protected_before']==result['fixture_protected_after']
                assert result['only_exact_startup_directory_changes'] is True
                assert result['exact_startup_files_removed'] is True
                assert all(x['mode']==384 for x in result['exact_startup_files'])
                assert all(value==448 for key,value in result['fixture_directory_modes_after'].items() if key.startswith('.sys4ai'))
    except Exception as exc:
        assessment_error=type(exc).__name__;result=None
receipt.update(exit_code=process.returncode if process else None,elapsed_seconds=time.monotonic()-start,
               timed_out=timed_out,output_limit=output_limit,host_error=error,assessment_error=assessment_error,
               stdout_bytes=len(stdout),stdout_sha256=sha(stdout),stderr_bytes=stderr_size,stderr_sha256=stderr_hash.hexdigest(),
               raw_stderr_retained=False,known_descendant_count=len(known),observed_descendants_exited=not alive,
               emergency_signals=signals,post_verification_errors=post,result_status=result.get('status') if result else 'unavailable')
receipt['status']='passed' if result and result['status']=='passed' and receipt['exit_code']==0 and not alive and not post and not error and not timed_out and not output_limit else 'failed'
write_new(out/'receipt.json',packed(receipt))
print(json.dumps({'status':receipt['status'],'index':index,'receipt_directory':str(out),'receipt_sha256':sha((out/'receipt.json').read_bytes()),
                  'result_status':receipt['result_status'],'checks':len(result.get('checks',[])) if result else None,
                  'browser_version':result.get('browser_version') if result else None,'elapsed_seconds':receipt['elapsed_seconds'],
                  'owned_descendants_exited':not alive,'post_verification_errors':len(post),'raw_stderr_bytes':stderr_size}),flush=True)
raise SystemExit(0 if receipt['status']=='passed' else 1)
