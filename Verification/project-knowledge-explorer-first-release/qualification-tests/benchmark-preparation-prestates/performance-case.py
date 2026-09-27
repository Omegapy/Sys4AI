"""Frozen disposable test executor: outputs evidence, edits no project files."""
import traceback
import hashlib,importlib.abc,importlib.util,io,json,os,signal,stat,subprocess,sys,time,types,unittest
from pathlib import Path
stage=Path(__file__).resolve().parent
manifest=json.loads((stage/'inputs.json').read_text())
def verify():
    for item in manifest['files']:
        p=stage/item['path'];s=p.lstat()
        assert stat.S_ISREG(s.st_mode) and s.st_nlink==1
        assert hashlib.sha256(p.read_bytes()).hexdigest()==item['sha256'],item['path']
verify();sys.dont_write_bytecode=True
scripts=stage/'SKILLS-depo/ontology/scripts';tests=stage/'SKILLS-depo/ontology/tests'
known={row['path']:row['sha256'] for row in manifest['files']}
class Source(importlib.abc.MetaPathFinder,importlib.abc.Loader):
    def find_spec(self,name,path=None,target=None):
        p=(scripts/name).with_suffix('.py') if name.startswith('ontology') else (tests/name).with_suffix('.py')
        if p.is_file() and str(p.relative_to(stage)) in known:return importlib.util.spec_from_file_location(name,p,loader=self)
        return None
    def create_module(self,spec):return None
    def exec_module(self,module):
        p=Path(module.__spec__.origin);raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()==known[str(p.relative_to(stage))]
        module.__file__=str(p);exec(compile(raw,str(p),'exec',dont_inherit=True),module.__dict__)
sys.meta_path.insert(0,Source())
import test_explorer_service


# Only a root-created owned performance job can select this fixed recipe/mode.
import gc,resource,tempfile,threading
assert len(sys.argv)==2
job_path=Path(sys.argv[1]);assert str(job_path).startswith('/private/tmp/explorer-perfdata-') and job_path.name.endswith('.json')
job=json.loads(job_path.read_text());base=Path(job['base']);root=Path(job['root']);assert str(base).startswith('/private/tmp/explorer-perfdata-') and root.parent==base and base==base.resolve() and not root.is_symlink()
assert job['mode'] in ('generate','canonical','service','probe','profile') and job['scale'] in ('small','representative','stress')
report={'mode':job['mode'],'scale':job['scale'],'status':'failed'};service=None;package=None;store=None;thread=None
try:
    if job['mode']=='generate':
        support=test_explorer_service.compile_file('_performance_fixture_support',tests/'explorer_support.py')
        kwargs={'scale':job['scale'],'identity':'explorer-perf-'+root.name}
        if job.get('relationships') is not None:assert job['scale']=='small' and 12<=job['relationships']<=5000;kwargs['relationships']=job['relationships']
        started=time.monotonic();fixture=support.make_explorer_project(root,**kwargs)
        report.update(status='generated',generation_ms=(time.monotonic()-started)*1000,counts=fixture['counts'],ids=fixture['ids'],identity=fixture['identity'],recipe='Complete existing pathological make_explorer_project recipe, unchanged imported core and source tuples.',input_inventory=test_explorer_service.inventory(root))
    elif job['mode']=='canonical':
        before=test_explorer_service.inventory(root)
        import ontology_core
        started=time.monotonic();project=ontology_core.load_project(root,validate=True)
        report.update(status='passed',elapsed_ms=(time.monotonic()-started)*1000,loaded_records=len(project.records),loaded_relations=len(project.relations),source_observations=len(project.sources),peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        report['protected_files_unchanged']=before==test_explorer_service.inventory(root)
        assert report['protected_files_unchanged'],'Canonical fixture preservation required'
    else:
        before=test_explorer_service.inventory(root);started=time.monotonic();launcher=test_explorer_service.compile_file('_performance_launcher',scripts/'ontology_explorer.py');package,assets=launcher.prepare_package(scripts)
        if job['mode']=='profile':
            snap=package.modules['ontology_explorer_snapshot'];mod=package.modules['ontology_explorer_read'];store=snap.SnapshotStore(root,package);reader=mod.Reader(store,service_instance='1'*32,build_id=assets.manifest['build_id'],schema_sha256=hashlib.sha256(package.member_bytes['schema']).hexdigest(),service_secret=b'p'*32)
            timings={};stack={};before_profile=sys.getprofile()
            def profile(frame,event,arg):
                name=frame.f_code.co_name
                if frame.f_code.co_filename!=str(scripts/'ontology_explorer_snapshot.py') or name not in ('_capture','_file','_materialize'):return
                if event=='call':stack[id(frame)]=(name,time.perf_counter())
                elif event=='return' and id(frame) in stack:
                    n,t=stack.pop(id(frame));timings.setdefault(n,[]).append((time.perf_counter()-t)*1000)
            snapshots=[];reads=[];sys.setprofile(profile)
            try:
                for i in range(6):
                    request=dict(schema_version=1,request_id='profile-'+str(i),code_epoch=package.code_epoch,snapshot=None,params={'refresh':False})
                    t=time.perf_counter();value=reader.read('context',request,session_scope='2'*32,session_expires_ms=900000);reads.append({'elapsed_ms':(time.perf_counter()-t)*1000,'status':value['status']});assert value['status']!='error'
                    snapshots.append(store.current)
            finally:sys.setprofile(before_profile)
            report.update(status='passed',profiled_read_samples=reads,profiled_calls=timings,immutable_snapshot_reused=all(x is snapshots[0] for x in snapshots),qualification='In-process exact captured production Reader profiling only. Instrumentation overhead and nested durations are not HTTP/browser latency; _file is included within capture and must not be summed as disjoint cost.')
        else:
            module=package.modules['ontology_explorer'];service=module.Service.__new__(module.Service)
            try:module.Service.__init__(service,package,assets,root)
            except module.ServiceError as exc:
                if exc.code not in ('resource_limit','deadline_exceeded'):raise
                report.update(status='bounded_refusal',safe_code=exc.code,startup_ms=(time.monotonic()-started)*1000,listener_created=service.listener is not None)
            else:
                ready_ms=(time.monotonic()-started)*1000;thread=threading.Thread(target=service.serve);thread.start()
                proxy=types.SimpleNamespace(service=service,package=package,assets=assets)
                for method in ('request','connect','bootstrap','read'):setattr(proxy,method,types.MethodType(getattr(test_explorer_service.Harness,method),proxy))
                session=proxy.connect();t=time.perf_counter();response=proxy.read(session);cold_context_ms=(time.perf_counter()-t)*1000;assert response[0]==200;ctx=json.loads(response[2]);snapshot=ctx['snapshot'];focus=job['ids']['focus'];series={};pages=[]
                operations=[('search',{'query':'Alignment','category':None,'lifecycles':['approved'],'fact_kinds':['asserted'],'sort':'relevance','limit':20,'cursor':None}),('entry_header',{'id':focus,'section':'header','cursor':None}),('entry_definition',{'id':focus,'section':'definition','cursor':None}),('neighborhood',{'id':focus,'direction':'both','predicate_ids':[],'lifecycles':['approved'],'fact_kinds':['asserted'],'limit':50,'node_limit':25,'cursor':None})]
                for label,params in ([] if job['mode']=='probe' else operations):
                    values=[]
                    for i in range(20):
                        t=time.perf_counter();response=proxy.read(session,'entry' if label.startswith('entry_') else label,params,snapshot);elapsed=(time.perf_counter()-t)*1000;value=json.loads(response[2]);assert response[0]==200 and value['status']!='error'
                        values.append({'elapsed_ms':elapsed,'response_bytes':len(response[2]),'status':value['status'],'returned':value['page']['returned'],'coverage':value['coverage']})
                    series[label]=values
                for ident,section in ([] if job['mode']=='probe' else [(focus.rsplit('-',1)[0]+'-00004','definition'),(focus.rsplit('-',1)[0]+'-00011','sources')]):
                    cursor=None;count=0;digest=hashlib.sha256();parts=0;times=[]
                    while True:
                        t=time.perf_counter();response=proxy.read(session,'entry',{'id':ident,'section':section,'cursor':cursor},snapshot);value=json.loads(response[2]);assert response[0]==200 and value['status']!='error';times.append((time.perf_counter()-t)*1000);parts+=1;assert parts<=100
                        if section=='definition':
                            for c in value['data']['chunks']:raw=c['text'].encode();digest.update(raw);count+=len(raw)
                        else:count+=len(value['data']['references'])
                        cursor=value['page']['next_cursor']
                        if cursor is None:break
                    if section=='definition':assert count>60000
                    else:assert count==130
                    pages.append({'section':section,'pages':parts,'utf8_bytes_or_source_count':count,'text_sha256':digest.hexdigest() if section=='definition' else None,'page_elapsed_ms':times})
                report.update(status='passed',startup_ms=ready_ms,cold_context_ms=cold_context_ms,warm_samples=series,pathological_paging=pages,policy=service.policy,worker_peak_rss_bytes=service.worker.peak,parent_peak_rss_bytes=service.worker.parent_peak,rss_samples=service.worker.observations,max_rss_observation_gap_seconds=service.worker.max_observation_gap)
        if store:store.close();store=None
        if service:
            service.stopping=True
            if thread:thread.join(8)
            service.close();report['owned_worker_reaped']=service.worker.process is None
            assert report['owned_worker_reaped'],'Owned read worker must be reaped'
            report.setdefault('worker_peak_rss_bytes',service.worker.peak);report.setdefault('parent_peak_rss_bytes',service.worker.parent_peak)
        report['protected_files_unchanged']=before==test_explorer_service.inventory(root)
        assert report['protected_files_unchanged'],'Fixture preservation required'
except BaseException as exc:
    report.update(status='failed',exception_type=type(exc).__name__,safe_code=getattr(exc,'code',None))
finally:
    if store:store.close()
    if service:
        service.stopping=True
        if thread:thread.join(8)
        service.close()
    if package:package.close()
    verify();report['stage_inputs_unchanged']=True
print(json.dumps(report,sort_keys=True))
raise SystemExit(0 if report['status'] in ('generated','passed','bounded_refusal') else 1)
