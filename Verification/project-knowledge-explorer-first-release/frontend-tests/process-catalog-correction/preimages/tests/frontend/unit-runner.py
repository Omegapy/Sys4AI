from pathlib import Path
import hashlib,json,os,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[5];SOURCE=ROOT/'SKILLS-depo/ontology/explorer';E=ROOT/'Verification/project-knowledge-explorer-first-release/frontend-tests'
stage=Path(tempfile.mkdtemp(prefix='explorer-frontend-unit-',dir='/private/tmp'))
import shutil
shutil.copytree(SOURCE/'src',stage/'src')
(stage/'src/main.ts').unlink()
controller=stage/'src/map/controller.ts'
controller.write_text(controller.read_text().replace("import('./renderer')","import('./renderer.js')"))
(stage/'package.json').write_text('{"type":"commonjs"}')
(stage/'node_modules').symlink_to('/private/tmp/explorer-contracts-implement-g3/node_modules',target_is_directory=True)
command=['node','/private/tmp/explorer-contracts-implement-g3/node_modules/typescript/bin/tsc','--ignoreConfig','--strict','--noUncheckedIndexedAccess','--target','ES2022','--module','Node16','--moduleResolution','node16','--lib','ES2022,DOM,DOM.Iterable','--outDir',str(stage/'out'),*[str(p) for p in sorted((stage/'src').rglob('*.ts'))]]
compiled=subprocess.run(command,capture_output=True,text=True)
if compiled.returncode:
 (E/('unit-compile-'+stage.name+'.json')).write_text(json.dumps({'command':command,'exit_code':compiled.returncode,'stdout':compiled.stdout,'stderr':compiled.stderr},indent=2)+'\n')
 print(compiled.stdout,compiled.stderr);raise SystemExit(compiled.returncode)
run=subprocess.run(['node',str(SOURCE/'tests/frontend/unit.cjs'),str(stage/'out'),str(ROOT)],capture_output=True,text=True,timeout=30)
number=len(list(E.glob('unit-[0-9][0-9].json')))+1
receipt={'stage':str(stage),'command':['node','tests/frontend/unit.cjs'],'exit_code':run.returncode,'stdout':run.stdout,'stderr':run.stderr,'inputs':[{'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted((SOURCE/'src').rglob('*.ts'))]}
receipt['test_inputs']=[{'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in [Path(__file__),SOURCE/'tests/frontend/unit.cjs',SOURCE/'tests/client-foundations/client-foundations.test.cjs']]
(E/f'unit-{number:02}.json').write_text(json.dumps(receipt,indent=2)+'\n');print(run.stdout);print(run.stderr);raise SystemExit(run.returncode)
