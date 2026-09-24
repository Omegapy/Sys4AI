import ast,hashlib,json,math,shutil,subprocess,sys,tempfile
from pathlib import Path
sys.path.insert(0,'/tmp')
from explorer_g3 import M,ref
root=Path.cwd();scripts=root/'SKILLS-depo/ontology/scripts';tests=root/'SKILLS-depo/ontology/tests'
sys.path[:0]=[str(scripts),str(tests)]
from explorer_support import make_explorer_project
from ontology_explorer_snapshot import VerifiedPackage
from ontology_explorer_read import READ_CLOSURE
with tempfile.TemporaryDirectory(prefix='explorer-scalar-qualifiers-',dir='/private/tmp') as temp:
    base=Path(temp);fixture=make_explorer_project(base/'fixture');cfg=json.loads((fixture['root']/'ontology.yaml').read_text())
    docs=[(fixture['root']/p,json.loads((fixture['root']/p).read_text())) for p in cfg['project_files']]
    records=[r for _,doc in docs for r in doc['@graph']]
    edge=next(r for r in records if r['kind']=='relation' and r['@id'].endswith('relation-000000'))
    predicate=next(r for r in records if r['@id']==edge['predicate'])
    predicate['qualifiers'].update({f'q{i}':{'type':'integer','required':False} for i in range(1025)})
    edge['qualifiers']={f'q{i}':i for i in range(1025)}
    for path,doc in docs:path.write_text(json.dumps(doc,ensure_ascii=False))
    helper=base/'helpers';helper.mkdir()
    inputs=[ref(scripts/(n+'.py')) for n in READ_CLOSURE]
    for name in READ_CLOSURE:shutil.copyfile(scripts/(name+'.py'),helper/(name+'.py'))
    package=VerifiedPackage(helper,{'schema':root/'ONTOLOGY-depo/schema/explorer-v1.json'},allowed_modules=READ_CLOSURE)
    module=package.load('ontology_explorer_read');store=package.load('ontology_explorer_snapshot').SnapshotStore(fixture['root'],package)
    reader=module.Reader(store,service_instance='1'*32,build_id='2'*64,schema_sha256=hashlib.sha256(package.member_bytes['schema']).hexdigest(),service_secret=b'x'*32)
    try:
        request=dict(schema_version=1,request_id='scalar-qualifiers',code_epoch=package.code_epoch,snapshot=None,params={'refresh':False})
        context=reader.read('context',request,session_scope='3'*32,session_expires_ms=900000)
        request.update(snapshot=context['snapshot'],params=dict(id=edge['subject'],direction='both',predicate_ids=[],lifecycles=['draft','approved','deprecated'],fact_kinds=['asserted','derived','inferred','external'],limit=1,cursor=None))
        response=reader.read('relationships',request,session_scope='3'*32,session_expires_ms=900000)
        item=response['data']['items'][0];assert item['kind']=='edge' and item['edge']['id']==edge['@id']
        assert item['edge']['qualifiers']==edge['qualifiers']
        raw=module.compact(response);Path('/private/tmp/explorer-scalar-qualifier-response.json').write_bytes(raw)
        service=scripts/'ontology_explorer.py';service_raw=service.read_bytes();tree=ast.parse(service_raw)
        nodes=[n for n in tree.body if isinstance(n,(ast.ClassDef,ast.FunctionDef)) and n.name in ['ServiceError','need','strict']]
        ns={'json':json,'math':math};exec(compile(ast.Module(body=nodes,type_ignores=[]),str(service),'exec'),ns)
        kwargs={'members':131072,'arrays':131072}
        if 'maximum_depth' in ns['strict'].__code__.co_varnames:kwargs['maximum_depth']=17
        transport_result='passed'
        try:ns['strict'](module.compact({'kind':'result','body':response}),**kwargs)
        except ns['ServiceError'] as exc:transport_result=exc.code
        assert service.read_bytes()==service_raw
        report={'scope':'Actual canonical disposable fixture with1025 declared optional integer qualifiers on existing project predicate and one incident relation; no new canonical types or wire formats. Actual current Reader output; isolated current transport strict parser only, no HTTP.','reader_inputs':inputs,'transport_sha256':hashlib.sha256(service_raw).hexdigest(),'record_id':edge['@id'],'qualifier_count':len(item['edge']['qualifiers']),'response_bytes':len(raw),'response_sha256':hashlib.sha256(raw).hexdigest(),'all_qualifiers_preserved':True,'current_transport_result':transport_result,'canonical_loaded_records':len(store.current.project.records),'recipe':'Merge q0 through q1024 into the existing relation-000000 predicate qualifiers as type integer/required false; set that relation qualifiers to exactly qN:N; retain all preexisting optional predicate definitions; query its subject relationships both with limit1.'}
        shutil.copyfile('/tmp/explorer-scalar-qualifier-probe.py',M/'scalar-qualifier-probe.py');report['verification_code']=ref(M/'scalar-qualifier-probe.py')
        (M/'scalar-qualifier-probe.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report,indent=2))
    finally:store.close()
