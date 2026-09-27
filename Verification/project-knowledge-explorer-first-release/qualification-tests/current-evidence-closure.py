"""Recheck named accepted current-build receipts and their complete frozen inputs."""
from pathlib import Path
import importlib.util,json,hashlib,time
Q=Path(__file__).resolve().parent;ROOT=Q.parents[2]
spec=importlib.util.spec_from_file_location('admission',Q/'current-admission.py');a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
F=Q.parent/'frontend-tests/process-catalog-correction/final-v3/current-checks.json';S=Q.parent/'service-tests/service-v3/current-checks.json'
admitted=json.loads((Q/'input-admission-current-v3.json').read_text());expected={r['path']:r for r in admitted['references']}
records=[]
for catalog,ids in [(F,{'keyboard01','catalog07','advanced03','bounds04','neutral05'}),(S,{'service_http','browser_basic','browser_late_session','browser_late_context'})]:
    a.check(expected[str(catalog.relative_to(ROOT))]);d=json.loads(a.read(catalog))
    for c in d['checks']:
        if c['id'] not in ids:continue
        assert c['status']=='passed';refs={k:a.check(c[k]) for k in ('report','receipt','inputs','job')}
        if 'attribution' in c:refs['attribution']=a.check(c['attribution'])
        report=json.loads(a.read(ROOT/c['report']['path']));assert report['status']=='passed',c['id']
        groups=report.get('checks',report.get('cases',[]));assert groups and all(x['status']=='passed' for x in groups)
        job=json.loads(a.read(ROOT/c['job']['path']));stage=Path(job.get('stage',job.get('staging_root','')));assert stage.is_absolute() and str(stage).startswith('/private/tmp/explorer-')
        manifest=json.loads(a.read(ROOT/c['inputs']['path']));raw=a.read(Path(job['manifest']['path']));assert hashlib.sha256(raw).hexdigest()==c['inputs']['sha256']==job['manifest']['sha256']
        live=[];frozen=[]
        for r in manifest['files']:
            b=a.read(stage/r['path']);assert hashlib.sha256(b).hexdigest()==r['sha256'] and len(b)==r['bytes'],r['path'];frozen.append(r['path'])
            if r['path'].startswith(('ONTOLOGY-depo/','SKILLS-depo/')):a.check(r);live.append(r['path'])
        observed={str(p.relative_to(stage)) for p in stage.rglob('*') if p.is_file()};assert observed==set(frozen)|{'inputs.json'},c['id']
        assert not any(p.is_symlink() for p in stage.rglob('*'))
        records.append({'catalog':a.ref(catalog),'id':c['id'],'references':refs,'actual_executor':'Primary host /root; reuse of exact recorded current-build execution, no worker replay.','groups':len(groups),'frozen_stage':str(stage),'frozen_member_count':len(frozen),'live_source_member_count':len(live),'complete_frozen_inventory_equal':True,'current_source_runtime_schema_fixture_inputs_equal':True,'browser_version':report.get('browser_version'),'qualification':c.get('qualification','Exact accepted current service receipt; operational resource supervision, not release benchmark.')})
result={'status':'passed','observed_unix':time.time(),'build_id':admitted['current_build_id'],'runtime_members':a.admit()['runtime_members'],'evidence':records,'reuse_basis':'Every named raw result is passing; exact receipt/job/manifests reopened, every frozen file matches, every repository source/schema/fixture/runtime member matches live, complete stage inventory has no extras or symlinks. Only declared stage-local drivers are stage-relative. Historical build19 checks are not reused.','limitations':'Actual browser/tool versions are those recorded in each run. Speech, human comprehension, full protected live-state comparison and benchmark measurements remain separate.'}
p=Q/'current-evidence-closure-v3.json'
with p.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(a.ref(p)))
