"""Read-only exact V4 input, authored/build/runtime and V1/V2 history recheck."""
from pathlib import Path
import ast,hashlib,json,os,stat,types
ROOT=Path(__file__).resolve().parents[4]
B=ROOT/'Verification/project-knowledge-explorer-first-release/service-tests'
P=ROOT/'Tasks/Task-implement-project-knowledge-explorer-full-first-release-2026-09-19--1FA1F620/artifacts/orchestration/manager/service-v4-input-packet.json'
def raw(p):
    p=Path(p);fd=os.open('/',os.O_RDONLY|os.O_DIRECTORY)
    try:
        for part in p.absolute().parts[1:-1]:
            nxt=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=fd);os.close(fd);fd=nxt
        member=os.open(p.name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=fd)
        try:
            first=os.fstat(member);assert stat.S_ISREG(first.st_mode) and first.st_nlink==1
            assert first.st_size<=8388608
            chunks=[]
            while block:=os.read(member,65536):chunks.append(block)
            after=os.fstat(member);fields=lambda s:(s.st_dev,s.st_ino,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
            value=b''.join(chunks);assert fields(first)==fields(after) and len(value)==first.st_size;return value
        finally:os.close(member)
    finally:os.close(fd)
def digest(value):return hashlib.sha256(value).hexdigest()
def canonical(v):return (json.dumps(v,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
def check(row):
    value=raw(ROOT/row['path']);assert digest(value)==row['sha256'],row['path'];assert len(value)==row.get('bytes',len(value));return value
def ref(p):
    value=raw(p);return {'path':str(p.relative_to(ROOT)),'sha256':digest(value),'bytes':len(value)}
packet=raw(P);assert digest(packet)=='09496d697ce6ee3853ecce3adbfa7297a1f3962dc9144b43df09028db9a2e6dd'
d=json.loads(packet)
for row in d['references']:check(row)
owned=[ref(ROOT/row['path']) for row in d['owned_test_sources_now_readonly']]
# Original test sources are read-only for V3.
unchanged=sum(a['sha256']==b['sha256'] for a,b in zip(owned,d['owned_test_sources_now_readonly']))
assert unchanged==3
explorer=ROOT/'SKILLS-depo/ontology/explorer';manifest=json.loads(raw(explorer/'assets/manifest.json'))
for row in manifest['assets']:check({**row,'path':str((explorer/'assets'/row['path']).relative_to(ROOT))})
front=ROOT/'Verification/project-knowledge-explorer-first-release/frontend-tests/narrow-layout-correction';build=json.loads(raw(front/'build-inputs-03.json'))['inputs'];record=build['record']
for row in record['files']:
    name=row['path'];p=ROOT/'ONTOLOGY-depo/schema/explorer-v1.json' if name=='$schema/explorer-v1.json' else ROOT/'SKILLS-depo/ontology/scripts'/name[len('$tooling/'):] if name.startswith('$tooling/') else explorer/name
    value=raw(p);assert len(value)==row['bytes'] and digest(value)==row['sha256'],str(p)
fixed=['index.html','package.json','package-lock.json','THIRD_PARTY_NOTICES.md','vite.config.ts','tsconfig.json','BUILD.md','scripts/package-runtime.mjs']
authored=[str(p.relative_to(explorer)) for p in (explorer/'src').rglob('*') if p.is_file()]
assert set(fixed+authored+['$schema/explorer-v1.json','$tooling/ontology_explorer_assets.py'])=={x['path'] for x in record['files']}
assert digest(canonical(record))==build['source_digest']==manifest['source_digest']
assert build['build_id']==manifest['build_id']
assert json.loads(raw(front/'build-03.json'))['manifest']==manifest
# V1 evidence bytes are historical and immutable; do not compare obsolete shared
# output hashes to the new frontend. Its own bounded inventory remains exact.
v1=json.loads(raw(B/'delivery.json'));inv=v1['evidence_inventory'];old=json.loads(check(inv))
for row in old['files']:check(row)
v2=json.loads(raw(B/'delivery-v2.json'));prior=json.loads(check(v2['evidence_inventory']))
for row in prior['files']:check(row)
v3=json.loads(raw(B/'service-v3/delivery.json'));third=json.loads(check(v3['evidence_inventory']))
for row in third['files']:check(row)
# Execute only the unchanged Template predicate/constants, never update/adopt.
p=ROOT/'tools/template_update.py';tree=ast.parse(raw(p));nodes=[]
for node in tree.body:
    if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id in ['EXCLUDED','EXCLUDED_SUFFIXES'] for t in node.targets):nodes.append(node)
    if isinstance(node,ast.FunctionDef) and node.name=='excluded':nodes.append(node)
from pathlib import PurePosixPath
env={'PurePosixPath':PurePosixPath};exec(compile(ast.Module(body=nodes,type_ignores=[]),str(p),'exec'),env)
paths=['assets/manifest.json','THIRD_PARTY_NOTICES.md','package-lock.json','BUILD.md']+['assets/'+x['path'] for x in manifest['assets']]
inclusions=[{'path':str((explorer/n).relative_to(ROOT)),'excluded':env['excluded'](n)} for n in paths]
exclusions=[{'path':n,'excluded':env['excluded'](n)} for n in ['dist/index.html','build/a.js','node_modules/a.js']]
assert all(not x['excluded'] for x in inclusions) and all(x['excluded'] for x in exclusions)
# Evaluate all fixed error cases with actual formatter and maximum policy widths.
service=ROOT/'SKILLS-depo/ontology/scripts/ontology_explorer.py';env={'__name__':'service_v4_error_check','__file__':str(service)};exec(compile(raw(service),str(service),'exec',dont_inherit=True),env)
schema=json.loads(raw(ROOT/'ONTOLOGY-depo/schema/explorer-v1.json'));obj=env['Service'].__new__(env['Service'])
obj.errors={r['properties']['code']['const']:({k:v['const'] for k,v in r['properties'].items()},r['x-http-status']) for r in schema['$defs']['Error']['oneOf']}
obj.policy={k:schema['$defs']['EffectivePolicy']['properties'][k]['maximum'] for k in ['page_items','response_bytes','visited_nodes','request_seconds']}
lengths=[len(obj.error(code,types.SimpleNamespace(operation=op,request_id='x'*32,authenticated=True))[1]) for code in obj.errors for op in env['OPERATIONS']];assert max(lengths)<=1024
print(json.dumps({'status':'passed','packet':ref(P),'readonly_refs_verified':len(d['references']),'original_readonly_tests':owned,'original_tests_unchanged':unchanged,'runtime_members':manifest['assets'],'manifest':ref(explorer/'assets/manifest.json'),'build_id':manifest['build_id'],'authored_source_record_members':len(record['files']),'authored_source_digest':build['source_digest'],'build_receipt':ref(front/'build-03.json'),'build_inputs_receipt':ref(front/'build-inputs-03.json'),'v1_evidence_files_unchanged':len(old['files']),'v2_evidence_files_unchanged':len(prior['files']),'v3_evidence_files_unchanged':len(third['files']),'discovery':{'source':ref(p),'included':inclusions,'excluded':exclusions},'fixed_errors':{'cases':len(lengths),'maximum_utf8_bytes':max(lengths),'tested_policy_maxima':obj.policy,'source':ref(service)},'qualification':'Current authored/build/runtime and readonly/history audit, not new build execution or UI/native-zoom proof. No production writes, Template adoption or limit change.'},sort_keys=True))
