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

assert len(sys.argv) in (4,5) and sys.argv[3]=='0'
RELEASE = pathlib.Path(sys.argv[1]); RELEASE_SHA = sys.argv[2]
assert RELEASE.parent == ROOT/'Tasks/Task-implement-project-knowledge-explorer-full-first-release-2026-09-19--1FA1F620/artifacts/orchestration/manager'
assert RELEASE.name == 'qualification-current-v4-TASK022-visual04-release.json'
release_raw = read_exact(RELEASE,1000000); assert sha(release_raw)==RELEASE_SHA
release=json.loads(release_raw);assert release['status']=='released_one_root_targeted_visual_observation'
index=0;kind='visual';entry={'job':release['job'],'manifest':release['manifest'],'source_mapping':release['source_mapping'],'command':release['command'],'timeout_seconds':release['timeout_seconds']}
job_path=ROOT/entry['job']['path'];assert job_path.parent==Q and job_path.name=='host-visual-browser-04.json'
job_raw=read_exact(job_path,1000000);assert sha(job_raw)==entry['job']['sha256']
job=json.loads(job_raw);stage=pathlib.Path(job['staging_root'])
assert job['manifest']==entry['manifest'] and stage/'inputs.json'==pathlib.Path(job['manifest']['path'])
assert job['command']==entry['command'] and job['timeout_seconds']==entry['timeout_seconds']==300
assert job['source_mapping']==entry['source_mapping'] and job['source_writes'] is False
assert job['inputs_count']==108 and job['external_tools']==release['external_tools'] and len(job['external_tools'])==31
assert release['full_runtime_files']==20
expected={(x['name'],x['theme']) for x in release['expected_state_pairs']}
assert len(expected)==8 and {x[0] for x in expected}=={'list_first_sentence','map_320_summary','map_320_first_sentence','source_320_parent_dismissed'}
manifest_raw=read_exact(stage/'inputs.json',1000000)
assert sha(manifest_raw)==job['manifest']['sha256'] and len(manifest_raw)==job['manifest']['bytes']
records=json.loads(manifest_raw)['files']
assert len(records)==108 and len({r['path'] for r in records})==108
runner=pathlib.Path(job['command'][3]).name
assert job['command']==[str(ROOT/'.venv/bin/python'),'-I','-B',str(stage/runner)]
assert set(job['source_mapping'])=={runner,'visual-browser.cjs','test-browser-runtime.json'}
assert job['browser_runtime']['expected_version']=='151.0.7922.34'
live_paths={};captured={};total=0
for row in records:
    name=row['path'];parts=name.split('/')
    assert not name.startswith('/') and all(part not in ('','.','..') for part in parts)
    raw=read_exact(stage/name,max(4*1024*1024,row['bytes']))
    assert len(raw)==row['bytes'] and sha(raw)==row['sha256']
    live=pathlib.Path(job['source_mapping'][name]) if name in job['source_mapping'] else ROOT/name
    assert live.is_absolute() and read_exact(live,max(4*1024*1024,row['bytes']))==raw
    live_paths[name]=live;captured[name]=raw;total+=len(raw);assert total<=64*1024*1024
def verify_tools_runtime():
    spec=job['browser_runtime'];root=pathlib.Path(spec['complete_inventory_root'])
    assert not root.is_symlink() and spec['complete_file_count']==20 and spec['expected_version']=='151.0.7922.34'
    runtime=json.loads(read_exact(stage/spec['inventory_stage_file'],1000000))
    assert runtime['executable']==spec['executable'] and runtime['supported_registry_entry']['browserVersion']==spec['expected_version']
    assert runtime['file_count']==20 and runtime['symlinks']==[] and len(runtime['complete_files'])==20
    listed={}
    for base,dirs,files in os.walk(root,followlinks=False):
        assert all(not (pathlib.Path(base)/name).is_symlink() for name in dirs+files)
        for name in files:listed[str((pathlib.Path(base)/name).relative_to(root))]=pathlib.Path(base)/name
    pins=job['external_tools'];assert len({r['resolved'] for r in pins})==31
    runtime_pins=[r for r in pins if pathlib.Path(r['resolved']).is_relative_to(root)]
    assert len(runtime_pins)==len(listed)==20
    indexed={r['path']:r for r in runtime['complete_files']}
    assert set(indexed)==set(listed)=={str(pathlib.Path(r['resolved']).relative_to(root)) for r in runtime_pins}
    for row in pins:
        assert str(pathlib.Path(row['path']).resolve(strict=True))==row['resolved']
        raw=read_exact(row['resolved'],max(4*1024*1024,row['bytes']))
        assert len(raw)==row['bytes'] and sha(raw)==row['sha256']
        if 'mode' in row:assert stat.S_IMODE(os.stat(row['resolved'],follow_symlinks=False).st_mode)==row['mode']
    for row in runtime_pins:
        item=indexed[str(pathlib.Path(row['resolved']).relative_to(root))]
        assert (item['sha256'],item['bytes'],item['mode'])==(row['sha256'],row['bytes'],row['mode'])
    return len(listed)
assert verify_tools_runtime()==20
if len(sys.argv)==5 and sys.argv[4]=='--admit-only':
    print(json.dumps({'status':'admitted','kind':kind,'files':108,'live':108,'tools':31,'runtime_files':20,'expected_pairs':len(expected),'job_sha256':entry['job']['sha256']}))
    raise SystemExit(0)
assert len(sys.argv)==4
out = pathlib.Path(tempfile.mkdtemp(prefix='explorer-task022-visual-host-',dir='/private/tmp'))
execution = out/'captured-stage'; execution.mkdir(mode=0o700)
for name,raw in captured.items(): write_new(execution/name,raw)
write_new(execution/'inputs.json',manifest_raw)
write_new(out/'reviewed-job.json',job_raw)
write_new(out/'reviewed-release.json',release_raw)
write_new(out/'host-wrapper.py',read_exact(pathlib.Path(__file__).absolute(),1000000))
command = [*job['command'][:3],str(execution/runner),*job['command'][4:]]
receipt = {'schema_version':1,'actor':'/root','release_sha256':RELEASE_SHA,'index':index,
 'job':entry['job'],'reviewed_command':job['command'],'actual_command':command,
 'original_stage':str(stage),'execution_stage':str(execution),'admitted_files':108,'admitted_live_files':108,
 'external_tool_count':31,'runtime_inventory_count':20,'manifest_sha256':sha(manifest_raw),
 'wrapper_sha256':sha((out/'host-wrapper.py').read_bytes()),'started_unix':time.time(),
 'expected_pairs':sorted(expected),'kind':kind}
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
for path,raw in ((job_path,job_raw),(RELEASE,release_raw)):
    try:assert read_exact(path,1000000)==raw
    except Exception:post.append({'path':str(path)})
if stdout:write_new(out/'stdout.json',bytes(stdout))
result=None;assessment_error=None;raw_rows=[];raw_errors=[];raw_dir=None;scan_findings_complete=False
if not timed_out and not output_limit and not error:
    try:
        result=json.loads(stdout)
        assert isinstance(result,dict) and result.get('status') in ('passed','failed')
        scans=result.get('scans',[]);assert isinstance(scans,list)
        if result.get('scan_execution_complete') or result.get('observation_execution_complete'):
            assert len(scans)==len(expected) and {(x['name'],x['theme']) for x in scans}==expected
        for row in scans:
            info=row['raw_report'];path=pathlib.Path(info['path'])
            assert path.parent.parent==pathlib.Path('/private/tmp') and path.parent.name.startswith('explorer-a11y-evidence-')
            assert stat.S_ISDIR(path.parent.lstat().st_mode) and stat.S_IMODE(path.parent.lstat().st_mode)==0o700
            if raw_dir is None:raw_dir=path.parent
            assert raw_dir==path.parent and stat.S_IMODE(path.lstat().st_mode)==0o600
            raw=read_exact(path,max(32*1024*1024,info['bytes']))
            assert len(raw)==info['bytes'] and sha(raw)==info['sha256']
            if kind in ('geometry','visual'):
                observed=json.loads(raw)
                assert (observed['name'],observed['theme'])==(row['name'],row['theme'])
                assert observed['document_theme']==row['theme']
                assert len(observed['elements'])==(1 if 'source' in row['name'] else 2)
                assert all(x['entire_rect_in_viewport'] and x['center_hit'] for x in observed['elements'])
                if 'sentence' in row['name']:assert all(x['codepoints']==[8594] for x in observed['elements'])
                if 'source' in row['name']:
                    parent=observed['source_parent_state']
                    assert parent['details_hidden'] and parent['drawer_visible'] and parent['path']=='SPECS.md' and parent['locator']=='Recorded locator: section:Specification'
                if row['name'].startswith('map_320') or row['name'].startswith('source_320'):assert observed['viewport']['width']==320
                picture=row['screenshot'];shot=pathlib.Path(picture['path'])
                assert shot.parent==raw_dir and stat.S_IMODE(shot.lstat().st_mode)==0o600
                png=read_exact(shot,max(32*1024*1024,picture['bytes']))
                assert len(png)==picture['bytes'] and sha(png)==picture['sha256'] and png.startswith(b'\x89PNG\r\n\x1a\n')
            raw_rows.append({'name':row['name'],'theme':row['theme'],'raw_report':info,**({'screenshot':row['screenshot']} if kind in ('geometry','visual') else {})})
        if result['status']=='passed':
            assert result['browser_version']=='151.0.7922.34'
            assert result['node_exit_code']==result['page_errors']==result['nonlocal_requests']==0
            assert result['observed_browser_descendants_exited'] and result['owned_read_worker_reaped']
            assert result['fixture_regular_files_unchanged'] and result['stage_inputs_unchanged']
            assert result['complete_headless_runtime_inventory_unchanged'] is True and result['headless_runtime_files']==20
            if kind=='scanner':
                assert result['scan_execution_complete'] and result['axe_version']=='4.13.0'
                assert result['violation_nodes']==0 and all(x['violations']==[] for x in scans)
                assert result['actual_configured_session_seconds']==60 and 58000<=result['real_wait_ms']<=75000
                assert result['clock_modified'] is False
            else:
                assert result['observation_execution_complete'] and result['manual_acceptance']=='pending review'
                assert len(scans)==8 and {(x['name'],x['theme']) for x in scans}==expected
        if result['status']=='failed' and kind=='scanner' and result.get('scan_execution_complete') is True:
            assert len(scans)==len(expected) and {(x['name'],x['theme']) for x in scans}==expected
            assert result.get('reason') is None and result.get('async_failures')==[]
            assert result['axe_version']=='4.13.0' and result['browser_version']=='151.0.7922.34'
            assert result['page_errors']==result['nonlocal_requests']==0
            assert result['complete_headless_runtime_inventory_unchanged'] is True and result['headless_runtime_files']==20
            assert result['observed_browser_descendants_exited'] and result['owned_read_worker_reaped']
            assert result['fixture_regular_files_unchanged'] and result['stage_inputs_unchanged']
            assert result['violation_nodes']>0 and any(row['violations'] for row in scans)
            assert all(row['actual_theme']['document']==row['actual_theme']['color_scheme']==row['theme'] for row in scans)
            scan_findings_complete=True
    except Exception as exc:
        assessment_error=type(exc).__name__;result=None
if raw_rows:
    write_new(out/'raw-index.json',packed({'kind':kind,'rows':raw_rows,'raw_directory':str(raw_dir) if raw_dir else None}))
receipt.update(exit_code=process.returncode if process else None,elapsed_seconds=time.monotonic()-start,
               timed_out=timed_out,output_limit=output_limit,host_error=error,assessment_error=assessment_error,
               stdout_bytes=len(stdout),stdout_sha256=sha(stdout),stderr_bytes=stderr_size,stderr_sha256=stderr_hash.hexdigest(),
               raw_stderr_retained=False,known_descendant_count=len(known),observed_descendants_exited=not alive,
               emergency_signals=signals,post_verification_errors=post,result_status=result.get('status') if result else 'unavailable',scan_findings_complete=scan_findings_complete,raw_verified_count=len(raw_rows))
receipt['status']='passed' if result and result['status']=='passed' and receipt['exit_code']==0 and not alive and not post and not error and not timed_out and not output_limit and stderr_size==0 and not signals else ('completed_with_findings' if scan_findings_complete and result and result['status']=='failed' and receipt['exit_code']==1 and not alive and not post and not error and not timed_out and not output_limit and stderr_size==0 and not signals else 'failed')
write_new(out/'receipt.json',packed(receipt))
print(json.dumps({'status':receipt['status'],'index':index,'receipt_directory':str(out),'receipt_sha256':sha((out/'receipt.json').read_bytes()),
                  'result_status':receipt['result_status'],'scans':len(result.get('scans',[])) if result else None,
                  'browser_version':result.get('browser_version') if result else None,'elapsed_seconds':receipt['elapsed_seconds'],
                  'owned_descendants_exited':not alive,'post_verification_errors':len(post),'raw_stderr_bytes':stderr_size}),flush=True)
raise SystemExit(0 if receipt['status'] in ('passed','completed_with_findings') else 1)
