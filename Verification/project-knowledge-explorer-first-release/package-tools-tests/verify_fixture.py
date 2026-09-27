"""Run current tooling checks against an explicitly prepared disposable fixture."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys

parser=argparse.ArgumentParser()
parser.add_argument('--fixture',type=Path,required=True)
args=parser.parse_args()
root=args.fixture.resolve(strict=True)
repo=Path(__file__).resolve().parents[3]
out=Path(__file__).resolve().parent
if not root.is_relative_to(Path('/private/tmp')):
    parser.error('fixture must be under real /private/tmp')
env={**os.environ,'EXPLORER_SCHEMA':str(root.parent/'schema.json'),'EXPLORER_PYTHON':sys.executable,'EXPLORER_BUILD_FIXTURE':str(root),'PYTHONDONTWRITEBYTECODE':'1'}
def sha(b):return hashlib.sha256(b).hexdigest()
def ref(p):
    b=p.read_bytes();return {'path':str(p.relative_to(repo)),'bytes':len(b),'sha256':sha(b)}
def run(command,name,cwd=root,expected=0):
    result=subprocess.run(command,cwd=cwd,env=env,capture_output=True,text=True,timeout=120)
    log=out/name;log.write_text(result.stdout+result.stderr)
    if result.returncode!=expected:raise RuntimeError(f'{name}: exit {result.returncode}')
    return {'command':command,'exit_code':result.returncode,'log':ref(log)}
source_names=['vite.config.ts','tsconfig.json','BUILD.md','scripts/package-runtime.mjs','package.json','package-lock.json','THIRD_PARTY_NOTICES.md']
for name in source_names:assert (repo/'SKILLS-depo/ontology/explorer'/name).read_bytes()==(root/name).read_bytes(),name
assert (repo/'SKILLS-depo/ontology/scripts/ontology_explorer_assets.py').read_bytes()==(root.parent/'scripts/ontology_explorer_assets.py').read_bytes()
checks=[]
checks.append(run(['npm','run','build'],'build-delivery-v1.log'))
checks.append(run(['npm','run','package:runtime'],'publish-delivery-v1.log'))
first_manifest=(root/'assets/manifest.json').read_bytes();first_record=(root/'dist/.explorer-build.json').read_bytes()
checks.append(run([sys.executable,'-B','-m','unittest','discover','-s','SKILLS-depo/ontology/tests','-p','test_explorer_assets.py','-v'],'suite-delivery-v1.log',repo))
count=int(re.search(r'Ran (\d+) tests',(out/'suite-delivery-v1.log').read_text()).group(1))
source=root/'src/main.ts';original=source.read_bytes();source.write_bytes(original+b'\nconst deliberateTypeFailure: number = "wrong";\n')
try:
    failed=run(['npm','run','typecheck'],'typecheck-negative-delivery-v1.log',expected=1)
    assert 'TS2322' in (out/'typecheck-negative-delivery-v1.log').read_text()
    checks.append(failed)
finally:source.write_bytes(original)
checks.append(run(['npm','run','build'],'repeat-build-delivery-v1.log'))
checks.append(run(['npm','run','package:runtime'],'repeat-publish-delivery-v1.log'))
assert first_manifest==(root/'assets/manifest.json').read_bytes()
assert first_record==(root/'dist/.explorer-build.json').read_bytes()
sys.path.insert(0,str(repo/'SKILLS-depo/ontology/scripts'))
import ontology_explorer_assets as a
from ontology_core import canonical_bytes
record=json.loads(first_record);manifest=json.loads(first_manifest)
assert a.canonical_bytes(record['inputs']['record'])==canonical_bytes(record['inputs']['record'])
assert sha(canonical_bytes(record['inputs']['record']))==manifest['source_digest']
assert a.build_id(manifest,record['inputs']['schema_sha256'])==manifest['build_id']
package=a.load_assets(root/'assets',schema_sha256=record['inputs']['schema_sha256'],lock_path=root/'package-lock.json',notices_path=root/'THIRD_PARTY_NOTICES.md')
js=''.join((root/'assets'/v['path']).read_text() for v in manifest['assets'] if v['mime']=='text/javascript')
assert manifest['build_id'] in js and record['inputs']['schema_sha256'] in js
node_compare=run(['node','--input-type=module','-e',"import{canonicalBytes}from './scripts/package-runtime.mjs';process.stdout.write(canonicalBytes({z:'日本語 😀',a:[1,null,false]}));"],'javascript-canonical-delivery-v1.log')
assert (out/'javascript-canonical-delivery-v1.log').read_bytes()==canonical_bytes({'z':'日本語 😀','a':[1,None,False]})
checks.append(node_compare)
for name,data in [('minimal-runtime-manifest.json',first_manifest),('minimal-build-receipt.json',first_record),('minimal-index.html',(root/'index.html').read_bytes()),('minimal-main.ts',(root/'src/main.ts').read_bytes()),('minimal-styles.css',(root/'src/styles.css').read_bytes())]:
    (out/name).write_bytes(data)
result={'schema_version':1,'scope':'PACKAGE_TOOLS only; disposable minimal production build and publisher, no application/HTTP/browser acceptance','fixture':str(root),'tests':count,'skipped':0,'checks':checks,'same_host_repeat':'byte-identical runtime manifest and complete input/output build receipt','build_id':manifest['build_id'],'source_digest':manifest['source_digest'],'manifest_sha256':sha(first_manifest),'receipt_sha256':sha(first_record),'schema_sha256':record['inputs']['schema_sha256'],'toolchain':manifest['toolchain'],'lazy_cytoscape_chunk':[v for v in manifest['assets'] if 'cytoscape' in v['path']],'production_literals_verified':True,'python_js_core_canonical_bytes_verified':True,'all_real_metadata_bindings_verified':True,'runtime_members':manifest['assets'],'source_files':[ref(repo/'SKILLS-depo/ontology/explorer'/n) for n in source_names]+[ref(repo/'SKILLS-depo/ontology/scripts/ontology_explorer_assets.py'),ref(repo/'SKILLS-depo/ontology/tests/test_explorer_assets.py'),ref(repo/'ONTOLOGY-depo/starter/ontology-explorer.yaml')],'qualification':['No network provisioning or npm hooks were executed. This does not claim a browser ran with its network disabled.','Compiler targets are configuration; actual browser/CSP/HTTP/whole-service epoch checks remain later gates.','No application src/index/assets, root adoption, Template, canonical knowledge, memory, Task or Git publication was written by this worker.','Existing all-helper closure may change concurrently; these tests bind their own exact selected helper and production-tooling inputs.','Publication is a single-writer operation; interruption can leave a fail-closed incomplete package rather than automatic rollback.']}
(out/'verification-result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'tests':count,'build_id':result['build_id'],'manifest_sha256':result['manifest_sha256'],'result':str(out/'verification-result.json')}))
