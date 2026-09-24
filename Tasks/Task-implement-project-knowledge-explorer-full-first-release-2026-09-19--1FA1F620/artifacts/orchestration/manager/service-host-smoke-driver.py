import hashlib,json,os,stat,sys,time,types
from pathlib import Path
ROOT=Path('/Volumes/P-SSD/AngryOwl/Sys4AI')
M=ROOT/'Tasks/Task-implement-project-knowledge-explorer-full-first-release-2026-09-19--1FA1F620/artifacts/orchestration/manager'
job=json.loads((M/'service-host-smoke-job.json').read_text())
def check_inputs():
    for item in job['inputs']:
        p=ROOT/item['path'];st=p.lstat();assert stat.S_ISREG(st.st_mode) and st.st_nlink==1
        assert hashlib.sha256(p.read_bytes()).hexdigest()==item['sha256'],item['path']
def inventory(root):
    found={};total=0
    for p in sorted(root.rglob('*')):
        if p.is_dir():continue
        st=p.lstat();assert stat.S_ISREG(st.st_mode) and st.st_nlink==1
        assert st.st_size<=2000000 and len(found)<512
        total+=st.st_size;assert total<=32*1024**2
        found[str(p.relative_to(root))]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':st.st_size,'mtime_ns':st.st_mtime_ns}
    return found
fixture=Path(job['fixture']);assert fixture==fixture.resolve(strict=True)
check_inputs();before=inventory(fixture);start=time.monotonic();service=None;package=None;report={}
try:
    scripts=ROOT/'SKILLS-depo/ontology/scripts'
    service_source=scripts/'ontology_explorer.py'
    fd=os.open(service_source,os.O_RDONLY|os.O_NOFOLLOW)
    try:
        st=os.fstat(fd);assert stat.S_ISREG(st.st_mode) and st.st_nlink==1 and st.st_size<=2000000
        raw=os.read(fd,2000001);assert len(raw)<=2000000
    finally:os.close(fd)
    pinned=next(x['sha256'] for x in job['inputs'] if x['path']=='SKILLS-depo/ontology/scripts/ontology_explorer.py')
    assert hashlib.sha256(raw).hexdigest()==pinned
    module=types.ModuleType('manager_scoped_service_smoke');module.__file__=str(service_source)
    sys.modules[module.__name__]=module
    exec(compile(raw,str(service_source),'exec',dont_inherit=True),module.__dict__)
    package,assets=module.prepare_package(scripts)
    service=package.modules['ontology_explorer'].Service(package,assets,fixture)
    report={'status':'passed','origin':service.origin,'code_epoch':package.code_epoch,'build_id':assets.manifest['build_id'],'worker_handshake':service.worker.handshake,'worker_peak_bytes':service.worker.peak,'parent_peak_bytes':service.worker.parent_peak,'public_health':service.health()}
except BaseException as e:
    report={'status':'failed','error_type':type(e).__name__,'error_code':getattr(e,'code',None)}
finally:
    if service is not None:service.close()
    if package is not None:package.close()
report['elapsed_seconds']=time.monotonic()-start
check_inputs();after=inventory(fixture);report['fixture_regular_files_unchanged']=before==after;report['fixture_files']=len(before)
report['scope']='Host-executed constructor/listener/verified-worker startup and cleanup smoke on worker-owned disposable fixture only; no HTTP requests, browser or complete service acceptance.'
print(json.dumps(report,sort_keys=True))
raise SystemExit(0 if report['status']=='passed' and before==after else 1)
