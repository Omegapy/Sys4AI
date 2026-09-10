"""Actual delivered CLI acceptance in isolated depots; no runtime acceptance."""
from __future__ import annotations
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone

REAL = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
ACTUAL_TEMPLATE = REAL / 'Projects/Sys4AI-Template-Project'
PYTHON = REAL / '.venv/bin/python'
FIXTURES = OUT / 'fixtures'
TEMPLATE_REL = 'Projects/Sys4AI-Template-Project'
SKILL_REL = '.agents/skills/init-new-project'
sha = lambda raw: hashlib.sha256(raw).hexdigest()

def write_json(p, value):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')

def tree(p, *, mtimes=False):
    result = {}
    for f in sorted(p.rglob('*')) if p.exists() else []:
        rel = f.relative_to(p).as_posix()
        if f.is_symlink():
            result[rel] = {'kind': 'symlink', 'target': os.readlink(f)}
        elif f.is_file():
            result[rel] = {'kind': 'file', 'sha256': sha(f.read_bytes()), 'bytes': f.stat().st_size}
            if mtimes: result[rel]['mtime_ns'] = f.stat().st_mtime_ns
        elif f.is_dir(): result[rel] = {'kind': 'directory'}
    return result

def digest_tree(value): return sha((json.dumps(value, sort_keys=True, separators=(',', ':'))+'\n').encode())

def load_helper(skill):
    spec=importlib.util.spec_from_file_location('delivered_initializer_'+sha(str(skill).encode())[:8], skill/'scripts/init_new_project.py')
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
    return module

def run_cli(name, script, args, cwd, *, expected=0):
    case=OUT/'commands'/name;case.mkdir(parents=True,exist_ok=True)
    command=[str(PYTHON),'-B',str(script),*map(str,args)]
    env={k:os.environ[k] for k in ('PATH','LANG','LC_ALL','HOME') if k in os.environ}
    env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1',TMPDIR=str(OUT/'tmp'))
    started=datetime.now(timezone.utc).isoformat();begin=time.monotonic()
    cp=subprocess.run(command,cwd=cwd,env=env,capture_output=True,timeout=60)
    (case/'stdout.json').write_bytes(cp.stdout);(case/'stderr.log').write_bytes(cp.stderr)
    parsed=None
    try: parsed=json.loads(cp.stdout)
    except (ValueError,UnicodeError): pass
    receipt={'command':command,'cwd':str(cwd),'started_at':started,'elapsed_seconds':round(time.monotonic()-begin,4),
             'exit_code':cp.returncode,'expected_exit':expected,'stdout_sha256':sha(cp.stdout),'stderr_sha256':sha(cp.stderr),
             'helper_sha256':sha(script.read_bytes()),'runtime_selection':'root standard-library Python; no optional runtime/model selected'}
    write_json(case/'receipt.json',receipt)
    if cp.returncode!=expected:
        raise AssertionError(f'{name}: expected {expected}, observed {cp.returncode}; see {case}')
    if parsed is None: raise AssertionError(f'{name}: no JSON result')
    print(json.dumps({'case':name,'exit':cp.returncode,'status':parsed.get('status'),'static_ready':parsed.get('static_ready'),'aggregate':parsed.get('aggregate')}),flush=True)
    return parsed,receipt

def args(mode, target, identity, name):
    return [mode,'--destination',target,'--project-id',identity,'--project-name',name,'--purpose','Verify delivered governance capability in an isolated acceptance fixture.']

def current_summary(target, report, *, runtime_preexisting=False):
    identity=json.loads((target/'project.json').read_text())
    memory=json.loads((target/'memory.yaml').read_text())
    onto=json.loads((target/'ontology.yaml').read_text())
    advanced=json.loads((target/'ontology-advanced.yaml').read_text())
    runtime=[f.name for f in target.iterdir() if f.name.startswith('.venv') or f.name in {'models','runtime'}]
    records=[f.relative_to(target).as_posix() for f in (target/'MEMORY').rglob('*') if f.is_file() and f.name!='README.md']
    assert memory['project']['id']==identity['project_id']==onto['project']['id']==advanced['project_id']
    assert not any(v['enabled'] for v in advanced['profiles'].values())
    assert not memory['backend']['enabled'] and not memory['backend']['semantic_enabled']
    assert not records
    assert runtime==(['.venv'] if runtime_preexisting else [])
    assert report['static_health']['runtime']=='not-exercised'
    assert report['static_health']['provisioned'] is False
    assert report['static_health']['unknown_target_code_executed'] is False
    assert report['static_ready'] is True
    canonical=json.loads((target/'control_records/project-setup.json').read_text())
    assert canonical['operation_id']==report['operation_id'] and canonical['status']=='completed'
    assert not any(x.startswith(('.venv/', 'models/', '.sys4ai/')) for x in report['owned_files'])
    return {'project_root':str(target),'project_id':identity['project_id'],'identity':identity,'operation_id':report['operation_id'],
            'setup_contract':report['setup_contract'],'static_ready':report['static_ready'],'aggregate':report['aggregate'],
            'runtime':'not-exercised','provisioned':False,'unknown_target_code_executed':False,
            'capture_enabled':memory['integration']['automatic_capture'],'backend_enabled':False,
            'advanced_profiles':{k:v['enabled'] for k,v in advanced['profiles'].items()},'learned_record_paths':records,
            'preexisting_runtime_entries':runtime,'owned_files_count':len(report['owned_files']),
            'receipt_sha256':sha((target/'control_records/project-setup.json').read_bytes()),'tree_sha256':digest_tree(tree(target))}

def prepare():
    (OUT/'tmp').mkdir(exist_ok=True);FIXTURES.mkdir(exist_ok=True)
    actual_before=tree(ACTUAL_TEMPLATE)
    real_registry_before=(REAL/'depot/projects.json').read_bytes()
    spec=importlib.util.spec_from_file_location('delivered_factory',REAL/'SKILLS-depo/init-new-project/tests/test_initializer.py')
    factory=importlib.util.module_from_spec(spec);sys.modules[spec.name]=factory;spec.loader.exec_module(factory)
    depot=factory.fixture_depot(FIXTURES/'current delivery')
    local_template=depot/TEMPLATE_REL
    shutil.rmtree(local_template)
    shutil.copytree(ACTUAL_TEMPLATE,local_template,symlinks=True)
    assert tree(local_template)==actual_before
    # Factory support is explicit; all copied source helpers used later match delivery.
    for package in (local_template/'.agents/skills').iterdir():
        if package.is_dir():
            target=depot/'SKILLS-depo'/package.name
            if target.exists(): shutil.rmtree(target)
            shutil.copytree(package,target,symlinks=True)
    helper=load_helper(local_template/SKILL_REL)
    assert helper.installed_locations()==(depot,local_template/SKILL_REL)
    selected,origins,_,renderer,policy=helper.template_sources(depot)
    selected_inventory={p:{'sha256':sha(raw),'origin':str(origins[p].relative_to(local_template))} for p,raw in selected.items()}
    source_evidence={'actual_template':str(ACTUAL_TEMPLATE),'template_tree':actual_before,'template_tree_sha256':digest_tree(actual_before),
                     'selected_starter_inventory':selected_inventory,'selected_count':len(selected),'excluded_source_local_runtime':'.venv',
                     'fixture_template':str(local_template),'fixture_template_exact_full_tree_match':True,
                     'factory_source':str(REAL/'SKILLS-depo/init-new-project/tests/test_initializer.py'),
                     'factory_sha256':sha((REAL/'SKILLS-depo/init-new-project/tests/test_initializer.py').read_bytes()),
                     'delivered_helper_sha256':sha((local_template/SKILL_REL/'scripts/init_new_project.py').read_bytes())}
    write_json(OUT/'template-provenance.json',source_evidence)
    write_json(OUT/'fixture-location.json',{'depot':str(depot),'template':str(local_template),'actual_template_sha256':digest_tree(actual_before)})
    script=local_template/SKILL_REL/'scripts/init_new_project.py';rows=[]
    for slug,name,mode,prep in [('fresh','Fresh Project','create','absent'),('first','First Preparation','prepare-existing','owned'),('manual','Manual Starter Copy','prepare-existing','starter'),('raw','Raw Directory Copy','prepare-existing','raw')]:
        target=depot/'Projects'/name
        preserved={};runtime_before=None
        if prep=='owned':
            target.mkdir();(target/'README.md').write_text('# Existing project\nPreserve this project narrative.\n');(target/'LICENSE').write_text('Fixture-owned license; preserve exact bytes.\n');(target/'notes.txt').write_text('Existing fixture content.\n')
            preserved={n:(target/n).read_bytes() for n in ('README.md','LICENSE','notes.txt')}
        elif prep=='starter':
            target.mkdir()
            for rel,raw in selected.items():
                p=target/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
            # The neutral original README is part of actual manual starter selection.
            shutil.copyfile(local_template/'README.md',target/'README.md')
        elif prep=='raw':
            shutil.copytree(local_template,target,symlinks=True)
            runtime_before=tree(target/'.venv',mtimes=True)
        report,receipt=run_cli(slug,script,args(mode,target,'delivery-'+slug,name),depot)
        summary=current_summary(target,report,runtime_preexisting=prep=='raw')
        summary['case']=slug;summary['command_receipt']='commands/'+slug+'/receipt.json'
        summary['preserved_files']={n:sha(raw) for n,raw in preserved.items()}
        for n,raw in preserved.items():assert (target/n).read_bytes()==raw
        if runtime_before is not None:
            assert tree(target/'.venv',mtimes=True)==runtime_before
            summary.update(preexisting_runtime_bytes_and_mtimes_preserved=True,preexisting_runtime_sha256=digest_tree(runtime_before),
                           runtime_origin='Raw copy of source-local unmapped Template environment; never adopted/provisioned/used/certified by setup.')
            write_json(OUT/'raw-copy-runtime-inventory.json',runtime_before)
        rows.append(summary)
    fresh=depot/'Projects/Fresh Project';first=json.loads((fresh/'control_records/project-setup.json').read_text())
    reg_before=(depot/'depot/projects.json').read_bytes();owned_before={n:(fresh/n).read_bytes() for n in first['owned_files']}
    rerun,_=run_cli('equivalent-rerun',script,args('create',fresh,'delivery-fresh','Fresh Project'),depot)
    assert rerun['operation_id']==first['operation_id'] and rerun['sources']==first['sources'] and rerun['owned_files']==first['owned_files']
    assert (depot/'depot/projects.json').read_bytes()==reg_before
    assert all((fresh/n).read_bytes()==raw for n,raw in owned_before.items())
    rows.append({**current_summary(fresh,rerun),'case':'equivalent-rerun','same_operation':True,'same_sources':True,'no_duplicate_registration':True,'owned_bytes_preserved':True})
    # Current explicit preference helper changes only an isolated fixture setting.
    memory_script=fresh/'.agents/skills/memory/scripts/memory.py'
    run_cli('capture-off',memory_script,['--project-root',fresh,'set-capture','off','--expected-config-sha256',sha((fresh/'memory.yaml').read_bytes())],fresh)
    for name in ('ontology.yaml','ontology-advanced.yaml'):
        p=fresh/name;cfg=json.loads(p.read_text());cfg['publication']={'enabled':False,'binding':None};write_json(p,cfg)
    protected={name:(fresh/name).read_bytes() for name in ('memory.yaml','ontology.yaml','ontology-advanced.yaml','LICENSE','LICENSE-CODE','LICENSE-DOCS','SOUL.md','AGENTS.md','ROLE.md')}
    preference,_=run_cli('preserved-off-disabled',script,args('create',fresh,'delivery-fresh','Fresh Project'),depot)
    assert all((fresh/n).read_bytes()==raw for n,raw in protected.items())
    assert preference['memory_capture']['status']=='off'
    rows.append({**current_summary(fresh,preference),'case':'preserved-off-disabled','protected_bytes_preserved':True})
    # A preserved customized incomplete capability remains usable as owned content,
    # but its static aggregate cannot claim complete healthy installation.
    custom=depot/'Projects/Custom Capability';custom.mkdir();(custom/'ONTOLOGY').mkdir();(custom/'ONTOLOGY/owned-format.txt').write_text('Project-owned unsupported ontology format.\n')
    custom_before=(custom/'ONTOLOGY/owned-format.txt').read_bytes()
    report,_=run_cli('custom-gap',script,args('prepare-existing',custom,'delivery-custom','Custom Capability'),depot,expected=1)
    assert report['status']=='completed' and report['static_ready'] is False and report['aggregate']=='degraded'
    assert (custom/'ONTOLOGY/owned-format.txt').read_bytes()==custom_before
    rows.append({'case':'custom-gap','project_root':str(custom),'status':'completed','aggregate':'degraded','static_ready':False,'project_owned_bytes_preserved':True,'runtime':'not-exercised','command_receipt':'commands/custom-gap/receipt.json'})
    # Force a real delivered CLI interruption at the registry lock boundary.
    recovering=depot/'Projects/Interrupted Setup';lock=depot/'depot/.projects-initializer.lock'
    registry_before=(depot/'depot/projects.json').read_bytes()
    with lock.open('a+b') as stream:
        fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
        partial,_=run_cli('registration-interrupted',script,args('create',recovering,'delivery-recovery','Interrupted Setup'),depot,expected=2)
    assert partial['status']=='partial' and partial['active_stage']=='registration' and partial['completed_stages']==['assets']
    assert (depot/'depot/projects.json').read_bytes()==registry_before
    partial_receipt=(recovering/'control_records/project-setup.json').read_bytes()
    protected_before={n:(recovering/n).read_bytes() for n in partial['owned_files']}
    recovered,_=run_cli('registration-recovered',script,args('create',recovering,'delivery-recovery','Interrupted Setup'),depot)
    assert recovered['operation_id']==partial['operation_id'] and recovered['sources']==partial['sources']
    assert all((recovering/n).read_bytes()==raw for n,raw in protected_before.items())
    recovery={'scenario':'actual-cli-registry-lock-interruption','partial_receipt_sha256':sha(partial_receipt),'partial_stage':'registration','completed_before_failure':['assets'],
              'same_operation':True,'same_sources':True,'asset_bytes_preserved':True,'recovered':current_summary(recovering,recovered),
              'command_receipts':['commands/registration-interrupted/receipt.json','commands/registration-recovered/receipt.json']}
    # Deep initialized layout is ready for the ordinary installed test route later.
    deep=depot/'Projects/Deep Space/one/two/Relocated Runtime Project';deep.parent.mkdir(parents=True)
    report,_=run_cli('deep-prepared',script,args('create',deep,'delivery-deep','Relocated Runtime Project'),depot)
    rows.append({**current_summary(deep,report),'case':'deep-prepared'})
    relocated=depot/'Projects/Deep Space/Relocated Copy';shutil.copytree(deep,relocated,symlinks=True)
    before=tree(relocated,mtimes=True)
    assessment,_=run_cli('relocated-static',script,['assess-ontology','--destination',relocated],depot)
    assert assessment['structural_readiness']=='available' and assessment['director_binding']=='current'
    failed,_=run_cli('relocated-rerun-refused',script,args('prepare-existing',relocated,'delivery-deep','Relocated Runtime Project'),depot,expected=2)
    assert tree(relocated,mtimes=True)==before
    pending={'status':'prepared_static_only_awaiting_host_runtime_signal','initialized_project':str(deep),'relocated_project':str(relocated),
             'installed_test_directory':str(relocated/'.agents/skills/ontology/tests'),'installed_acceptance_runner':str(relocated/'.agents/skills/ontology/tests/acceptance_runner.py'),
             'explicit_test_depot_root':str(REAL),'standards_runtime':'Await host final certified existing runtime path after root restoration.',
             'semantic_acceptance_root':'Await host final restored semantic root; SYS4AI_SEMANTIC_ACCEPTANCE_ROOT required.',
             'population':'not_started','runtime_tests':'not_started','relocated_static_assessment':assessment,'relocated_setup_replay_refused':True,
             'original_runtime_fixture_tree_sha256':digest_tree(tree(deep)),'relocated_fixture_tree_sha256':digest_tree(tree(relocated))}
    write_json(OUT/'neutral-matrix.json',{'status':'static_matrix_complete_runtime_unexercised','cases':rows,'template_provenance':'template-provenance.json'})
    write_json(OUT/'recovery-matrix.json',{'status':'partial_matrix_actual_cli_registration_recovery_observed','cases':[recovery],'earlier_edition_and_asset_conflicts':'separate prepared checks pending'})
    write_json(OUT/'runtime-preparation.json',pending)
    assert tree(ACTUAL_TEMPLATE)==actual_before,'Actual Template changed during matrix; source evidence is stale.'
    assert (REAL/'depot/projects.json').read_bytes()==real_registry_before,'Real registry changed during fixture work.'
    write_json(OUT/'static-stage-result.json',{'status':'passed_static_matrix','case_count':len(rows),'actual_template_unchanged':True,'real_registry_unchanged':True,
        'optional_runtime':'not-exercised','runtime_signal':'awaiting_host','fixture_depot':str(depot),
        'neutral_matrix_sha256':sha((OUT/'neutral-matrix.json').read_bytes()),'recovery_matrix_sha256':sha((OUT/'recovery-matrix.json').read_bytes())})

if __name__=='__main__':prepare()
