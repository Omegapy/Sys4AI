"""Reproducible pure-client checks; no dependency installation or production build."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[5]
EXPLORER = ROOT / 'SKILLS-depo/ontology/explorer'
EVIDENCE = ROOT / 'Verification/project-knowledge-explorer-first-release/client-foundations-tests'
DEPS = Path('/private/tmp/explorer-contracts-implement-g3/node_modules')
STAGE = Path(tempfile.mkdtemp(prefix='explorer-client-foundations-', dir='/private/tmp'))
EXPECTED = {'typescript': '7.0.2', 'vite': '8.3.0', 'cytoscape': '3.34.3'}
checks = []

def run(label, args, *, expected=0, env=None):
    proc = subprocess.run(args, cwd=STAGE, capture_output=True, text=True, env=env)
    checks.append({'name': label, 'command': args, 'exit_code': proc.returncode,
                   'expected_exit_code': expected, 'stdout': proc.stdout, 'stderr': proc.stderr})
    if proc.returncode != expected:
        raise RuntimeError(label + ' failed')
    return proc.stdout

try:
    assert subprocess.check_output(['node', '--version'], text=True).strip() == 'v25.9.0'
    assert subprocess.check_output(['npm', '--version'], text=True).strip() == '11.12.1'
    for package, version in EXPECTED.items():
        assert json.loads((DEPS/package/'package.json').read_text())['version'] == version
    (STAGE/'src').mkdir()
    for name in ['contracts','state','routes','preferences','model']:
        shutil.copy2(EXPLORER/'src'/f'{name}.ts', STAGE/'src'/f'{name}.ts')
    # The existing verified closure is copied unchanged; no install/hook runs.
    shutil.copytree(DEPS, STAGE/'node_modules', symlinks=False)
    def inventory(folder):
        return [{'path':str(x.relative_to(folder)), 'sha256':hashlib.sha256(x.read_bytes()).hexdigest(), 'bytes':x.stat().st_size} for x in sorted(folder.rglob('*')) if x.is_file()]
    original_deps=inventory(DEPS)
    copied_deps=inventory(STAGE/'node_modules')
    assert original_deps==copied_deps
    checks.append({'name':'unchanged_dependency_copy','regular_files':len(original_deps),'inventory_sha256':hashlib.sha256(json.dumps(original_deps,sort_keys=True).encode()).hexdigest(),'status':'passed'})
    shutil.copy2(EXPLORER/'tsconfig.json', STAGE/'tsconfig.json')
    compiler = str(STAGE/'node_modules/typescript/bin/tsc')
    run('strict_exact_project_config', ['node', compiler, '--project', str(STAGE/'tsconfig.json')])
    (STAGE/'negative.ts').write_text("import type { Direction, SourceRef } from './src/contracts';\nconst invalid: Direction = 'sideways';\nconst source: SourceRef = { owner_id: true };\n")
    run('deliberate_negative_types', ['node',compiler,'--ignoreConfig','--strict','--noUncheckedIndexedAccess','--target','ES2022','--module','Node16','--moduleResolution','node16','--lib','ES2022,DOM','--noEmit',str(STAGE/'negative.ts')], expected=1)
    assert 'TS2322' in checks[-1]['stdout']
    run('isolated_runtime_compile', ['node',compiler,'--ignoreConfig','--strict','--noUncheckedIndexedAccess','--target','ES2022','--module','Node16','--moduleResolution','node16','--lib','ES2022,DOM','--outDir',str(STAGE/'out'),*[str(x) for x in sorted((STAGE/'src').glob('*.ts'))]])
    env = dict(os.environ, EXPLORER_FOUNDATIONS_OUT=str(STAGE/'out'), EXPLORER_FOUNDATIONS_ROOT=str(ROOT), EXPLORER_FOUNDATIONS_EXAMPLES=str(STAGE/'wire-examples.json'))
    stdout=run('pure_runtime_tests', ['node',str(EXPLORER/'tests/client-foundations/client-foundations.test.cjs')],env=env)
    report=json.loads(stdout)
    (EVIDENCE/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    schema_check = """import json,sys
from pathlib import Path
from jsonschema import Draft202012Validator
schema=json.loads(Path(sys.argv[1]).read_text())
Draft202012Validator.check_schema(schema)
v=Draft202012Validator({'$ref':'#/$defs/ReadResponse','$defs':schema['$defs']})
examples=json.loads(Path(sys.argv[2]).read_text())
for x in examples:v.validate(x)
print(json.dumps({'schema':'Draft202012Validator','validated_success_and_fixed_error_examples':len(examples),'status':'passed'}))
"""
    # This installed test interpreter supplies the independent full validator;
    # no memory/backend operations or environment changes occur.
    run('independent_json_schema', [str(ROOT/'.venv-memory-pilot/bin/python'),'-B','-c',schema_check,str(ROOT/'ONTOLOGY-depo/schema/explorer-v1.json'),str(STAGE/'wire-examples.json')])
    run('source_whitespace_check',['git','-C',str(ROOT),'diff','--check','--','SKILLS-depo/ontology/explorer/src','SKILLS-depo/ontology/explorer/tests/client-foundations'])
    checks.append({'name':'compiled_api_manifest','files':[{'path':str(x),'sha256':hashlib.sha256(x.read_bytes()).hexdigest(),'bytes':x.stat().st_size} for x in sorted((STAGE/'out').glob('*.js'))]})
    result='passed'
except Exception as exc:
    result='failed'
    checks.append({'name':'runner_failure','error':str(exc)})
receipt={'schema_version':1,'status':result,'stage':str(STAGE),'toolchain':{'node':'25.9.0','npm':'11.12.1',**EXPECTED},'checks':checks,
         'inputs':[{'path':str(x.relative_to(ROOT)),'sha256':hashlib.sha256(x.read_bytes()).hexdigest(),'bytes':x.stat().st_size} for x in sorted((EXPLORER/'src').glob('*.ts')) if x.stem in ['contracts','state','routes','preferences','model']]}
(EVIDENCE/'checks.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'status':result,'stage':str(STAGE),'checks':[(x['name'],x.get('exit_code')) for x in checks]}))
sys.exit(0 if result=='passed' else 1)
