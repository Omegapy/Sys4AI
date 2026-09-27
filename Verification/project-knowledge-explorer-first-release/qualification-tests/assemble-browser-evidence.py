"""Bind each TASK021 scenario to exact observed current production evidence."""
from pathlib import Path
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[3];Q=Path(__file__).resolve().parent;OUT=Q.parent
M=ROOT/'Tasks/Task-implement-project-knowledge-explorer-full-first-release-2026-09-19--1FA1F620/artifacts/orchestration/manager'
F=OUT/'frontend-tests'
def ref(p):
    b=p.read_bytes();return {'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
sources={}
current=json.loads((F/'process-catalog-correction/final-v3/current-checks.json').read_text())
for key,ident in [('F19','neutral05'),('F20','advanced03'),('F21','bounds04')]:
    check=next(c for c in current['checks'] if c['id']==ident)
    sources[key]={name:ROOT/check[field]['path'] for name,field in [('raw','report'),('receipt','receipt'),('inputs','inputs'),('job','job')]}
for key,stem in [('P','production-05'),('EXP','lifecycle-expiry-05'),('STOP','lifecycle-stop-03'),('TIME','lifecycle-deadline-04'),('KEY','keyboard-03')]:
    folder=Q/('actual-'+stem);sources[key]={'raw':folder/'stdout.json','receipt':folder/'receipt.json','job':folder/'reviewed-job.json','attribution':folder/'attribution.json'}
missing=[str(p.relative_to(ROOT)) for value in sources.values() for p in value.values() if not p.exists()]
if missing:print(json.dumps({'status':'pending_required_observations','missing':missing}));raise SystemExit(2)
reports={}
for key,value in sources.items():
    report=json.loads(value['raw'].read_text());assert report['status']=='passed',key
    assert all(c['status']=='passed' for c in report['checks']),key
    reports[key]=report
def checks(key,indexes):
    return [{'source':key,'locator':f'checks[{i}]','name':reports[key]['checks'][i]['name'],'status':'passed'} for i in indexes]
mapping={
 'AT-01':checks('P',[0])+checks('F20',[0]),
 'AT-02':checks('P',[1,2,3,4]),
 'AT-03':checks('F20',[1])+checks('P',[2]),
 'AT-04':checks('P',[5]),'AT-05':checks('P',[5]),
 'AT-06':checks('P',[5])+checks('F20',[12,13])+checks('F21',[1])+checks('TIME',[0]),
 'AT-07':checks('F20',[2,3,12,13]),
 'AT-08':checks('F20',[11]),'AT-09':checks('P',[6]),
 'AT-10':checks('F20',[7,19]),
 'AT-11':checks('F20',[8,18,20,22])+checks('KEY',[2]),
 'AT-12':checks('F21',[1]),
 'AT-13':checks('F20',[5,6,13,17]),
 'AT-14':checks('P',[7])+checks('F20',[6]),
 'AT-15':checks('F20',[5,6,13,17,18])+checks('F21',[1]),
 'AT-16':checks('F20',[5,6,20,22])+checks('KEY',[2]),
 'AT-17':checks('F20',[14,15])+checks('KEY',[3]),
 'AT-18':checks('F20',[16])+checks('F19',[3]),
 'AT-19':checks('F20',[4,14,15])+checks('KEY',[1,3]),
 'AT-20':checks('F20',[26]),
 'AT-21':checks('F20',[24,25]),
 'AT-22':checks('P',[8])+checks('F20',[21]),
 'AT-23':checks('EXP',[0])+checks('STOP',[0]),
 'AT-28':checks('P',[7])+checks('F20',[5,6]),
 'AT-29':checks('KEY',[0,1,2,3])+checks('F20',[19,22]),
 'AT-32':checks('P',[0]),
 'AT-34':checks('F20',[22])+checks('F21',[2,3])+checks('KEY',[2]),
}
assert set(mapping)=={f'AT-{n:02}' for n in [*range(1,24),28,29,32,34]}
command=[str(ROOT/'.venv/bin/python'),'-I','-B',str(M/'audit-live-runtime.py'),'--expected-manifest','c59422dc85017405ff9c92e335a459f770e649a2a59507d7dc7b7f449d04ae4a']
p=subprocess.run(command,capture_output=True,text=True,timeout=30);assert p.returncode==0 and not p.stderr
(Q/'browser-live-runtime-audit.json').write_text(p.stdout)
source_refs={key:{name:ref(path) for name,path in value.items()} for key,value in sources.items()}
result={'status':'passed','plan_task':'TASK-021','build_id':'09b4571b34594b39e9d19be3320f334bf7d608a333e0d06902dfda0a361259b8','runtime_manifest_sha256':'c59422dc85017405ff9c92e335a459f770e649a2a59507d7dc7b7f449d04ae4a',
 'scenarios':{key:{'status':'passed','observations':value} for key,value in mapping.items()},'sources':source_refs,
 'production_build':ref(OUT/'production-build.json'),'current_runtime_audit':ref(Q/'browser-live-runtime-audit.json'),'reused_current_input_closure':ref(Q/'current-evidence-closure-v3.json'),
 'proof_boundaries':['Every source is an actual production bundle HTTP/browser receipt for its named fixture and executed browser version. F19/F20/F21 are accepted current process-catalog-correction neutral05/advanced03/bounds04 actual Chrome154 results, with complete input closure freshly rechecked; P/EXP/STOP/TIME/KEY are current independent qualification host runs. No build19 evidence is relabeled current.','The exact immutable frozen stage manifests bind fixture semantics, explicit fault injection and producer identity. Root-owned captured execution stages are byte-identical copies; root receipts retain actual and logical paths.','TIME suspends only its retained owned read-worker Popen, then observes unchanged bounded deadline handling and reaping. KEY uses actual keyboard reachability; prior mixed pointer/keyboard checks retain their narrower scope.','DOM live-region text is not observed VoiceOver speech. Native AT, full accessibility review and user comprehension remain TASK022/TASK025.','Current source-layout disposable package and installed-layout Service V3 discovery are distinguished from later root/Template adoption. No Node dev server or production package installation occurs during reads.','Dense graph captions retain the accepted qualification: current UI/list/zoom are available, but universal association readability or human comprehension is not inferred.'],
 'complete_scenario_count':len(mapping),'highest_verification':'Actual production HTTP/browser behavior for named scenarios and fixtures; separate root/Template adoption, assistive-technology and participant gates remain.'}
(OUT/'browser-results.json').write_text(json.dumps(result,indent=2)+'\n')
production=reports['P'];assert production['optional_paths_absent'] and production['publication_enabled'] is False
assert production['fixture_regular_files_unchanged'] and production['generated_files_unchanged'] and production['generated_absences_preserved']
offline={'status':'passed','plan_task':'TASK-021','production_build':ref(OUT/'production-build.json'),'source':source_refs['P'],
 'network':{'external_requests':production['nonlocal_requests'],'csp_violations':production['csp_violations'],'page_errors':production['page_errors'],'server':'Actual dedicated Python Service; Node was browser-test tooling only, not a serving/dev process.'},
 'optional_services_absent':production['optional_paths_absent'],'publication_enabled':False,'generated_products':production['generated_state'],
 'generated_files_unchanged':True,'generated_absences_preserved':True,'fixture_regular_files_unchanged':True,
 'missing_assets_evidence':{'raw':ref(OUT/'service-tests/service-v3/service-host-output.json'),'case':'test_explorer_service.PackageRaceTests.test_missing_assets_and_invalid_configuration','scope':'Actual accepted current Service V3 missing manifest/invalid configuration fail package preparation before a browser UI is served. Complete stage input closure rechecked in current-evidence-closure-v3.json.'},
 'qualification':'Explicit fixture setup ran the actual wiki generator before measurement, retained its real manifest, changed its listed index and removed its listed concepts.md. Browsing neither rebuilt nor depended on those products. Full selected live-depot nonmutation is TASK023.'}
assert offline['network']['external_requests']==0 and not offline['network']['csp_violations'] and not offline['network']['page_errors']
(OUT/'offline-csp-results.json').write_text(json.dumps(offline,indent=2)+'\n')
print(json.dumps({'status':'passed','browser':ref(OUT/'browser-results.json'),'offline':ref(OUT/'offline-csp-results.json'),'scenarios':len(mapping)}))
