import hashlib,json,shutil,subprocess,sys,tempfile
from pathlib import Path
sys.path.insert(0,'/tmp')
from explorer_g3 import M,ref
root=Path.cwd();scripts=root/'SKILLS-depo/ontology/scripts';tests=root/'SKILLS-depo/ontology/tests'
sys.path[:0]=[str(scripts),str(tests)]
from explorer_support import make_explorer_project
from ontology_explorer_snapshot import VerifiedPackage
from ontology_explorer_read import READ_CLOSURE
inputs=[ref(scripts/(n+'.py')) for n in READ_CLOSURE]+[ref(tests/'explorer_support.py'),ref(root/'ONTOLOGY-depo/schema/explorer-v1.json'),ref(root/'SKILLS-depo/ontology/explorer/src/contracts.ts')]
checks=json.loads((root/'Verification/project-knowledge-explorer-first-release/client-foundations-tests/checks.json').read_text())
with tempfile.TemporaryDirectory(prefix='explorer-all-operations-',dir='/private/tmp') as tmp:
    base=Path(tmp);helper=base/'helpers';helper.mkdir()
    for name in READ_CLOSURE:shutil.copyfile(scripts/(name+'.py'),helper/(name+'.py'))
    fixture=make_explorer_project(base/'fixture')
    package=VerifiedPackage(helper,{'schema':root/'ONTOLOGY-depo/schema/explorer-v1.json'},allowed_modules=READ_CLOSURE)
    module=package.load('ontology_explorer_read');snapshot_module=package.load('ontology_explorer_snapshot')
    store=snapshot_module.SnapshotStore(fixture['root'],package)
    reader=module.Reader(store,service_instance='1'*32,build_id='2'*64,schema_sha256=hashlib.sha256(package.member_bytes['schema']).hexdigest(),service_secret=b'x'*32)
    wires=[];snapshot=None
    def call(name,op,params):
        value=reader.read(op,dict(schema_version=1,request_id=name,code_epoch=package.code_epoch,snapshot=snapshot,params=params),session_scope='3'*32,session_expires_ms=900000)
        wires.append({'name':name,'raw':module.compact(value).decode()});return value
    try:
        context=call('context','context',{'refresh':False});snapshot=context['snapshot']
        focus=fixture['ids']['focus'];policy=context['data']['resource_policy']
        params=dict(query='',category=None,lifecycles=['draft','approved','deprecated'],fact_kinds=['asserted','derived','inferred','external'],sort='label',limit=2,cursor=None)
        for i in range(3):
            value=call('search-page-'+str(i),'search',params);params={**params,'cursor':value['page']['next_cursor']}
        call('search-ambiguous','search',{**params,'query':'Alignment','sort':'relevance','cursor':None})
        empty=call('search-empty','search',{**params,'query':'zzqxvplmknz','sort':'relevance','cursor':None})
        assert empty['status']=='empty' and empty['page']['returned']==0
        for section in ['header','definition','details','sources']:
            value=call('entry-'+section,'entry',dict(id=focus,section=section,cursor=None))
            if section=='sources':source=value['data']['references'][0]
        for i,p in enumerate(store.current.presentation['process_views']):call('process-'+str(i),'entry',dict(id=p['id'],section='process',cursor=None))
        graph=dict(id=focus,predicate_ids=[],lifecycles=params['lifecycles'],fact_kinds=params['fact_kinds'],limit=20,cursor=None)
        for direction in ['both','incoming','outgoing']:call('relations-'+direction,'relationships',{**graph,'direction':direction})
        call('neighborhood','neighborhood',{**graph,'direction':'both','node_limit':25})
        source_params=dict(owner_id=source['owner_id'],reference_id=source['reference_id'],cursor=None)
        call('source-current','source',source_params)
        source_path=fixture['root']/source['path'];source_path.write_bytes(source_path.read_bytes()+b'\nSynthetic changed evidence.\n')
        call('source-changed','source',source_params)
        (base/'packet.json').write_text(json.dumps({'policy':policy,'wires':wires},ensure_ascii=False))
        shutil.copyfile(root/'SKILLS-depo/ontology/explorer/src/contracts.ts',base/'contracts.ts')
        command=['node',str(Path(checks['stage'])/'node_modules/typescript/bin/tsc'),'--ignoreConfig','--strict','--noUncheckedIndexedAccess','--target','ES2022','--module','Node16','--moduleResolution','node16','--lib','ES2022,DOM','--outDir',str(base/'out'),str(base/'contracts.ts')]
        c=subprocess.run(command,capture_output=True,text=True);assert c.returncode==0,c.stderr+c.stdout
        r=subprocess.run(['node','/tmp/explorer-all-operation-bridge.cjs',str(base/'out/contracts.js'),str(base/'packet.json')],capture_output=True,text=True)
        for f in inputs:assert ref(f['path'])['sha256']==f['sha256'],f['path']
        report={'inputs':inputs,'status':'passed' if r.returncode==0 else 'failed','command':command,'compiler_exit':c.returncode,'client_exit':r.returncode,'client_output':r.stdout,'client_error':r.stderr,'responses':[{'name':x['name'],'bytes':len(x['raw'].encode()),'sha256':hashlib.sha256(x['raw'].encode()).hexdigest()} for x in wires],'qualification':'Fresh disposable canonical fixture, exact seven-module read closure, actual Reader compact responses and independently compiled current client; full current resource-policy digest and identities checked. No HTTP, service/bootstrap, browser, production or live-root preservation claim.'}
        report['historical_probe_correction']='Initial attempted empty-query spelling contained ordinary token example and returned one legitimate lexical match; changed only test query to a nonmatching token and added explicit empty-status/count assertion.'
        for filename in ['explorer-all-operation-bridge.py','explorer-all-operation-bridge.cjs']:shutil.copyfile(Path('/tmp')/filename,M/filename)
        report['verification_code']=[ref(M/name) for name in ['explorer-all-operation-bridge.py','explorer-all-operation-bridge.cjs']]
        (M/'all-operation-bridge.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps({k:report[k] for k in ['status','client_exit','client_output','client_error']},indent=2))
        if r.returncode:raise SystemExit(r.returncode)
    finally:store.close()
