"""Compact baseline evidence and supplement explicitly named generated paths."""
import json
import os
from pathlib import Path
import re
import subprocess

from collect_baseline import ROOT,OUT,LOGS,now,metadata,inventory,write,run,digest
from collect_inventories import parts,ref,source_lines

baseline=json.loads((OUT/'baseline.json').read_text())
if 'protected_before' not in baseline:
    raise SystemExit('Baseline already compacted; refusing a second finalization.')

supplement_trees=['.sys4ai/ontology/compiled','.sys4ai/ontology/links','.sys4ai/ontology/manifests',
    '.sys4ai/ontology/root-adoption','.sys4ai/memory/index','.sys4ai/memory/maintenance',
    '.sys4ai/memory/normalized','.sys4ai/memory/projection','.sys4ai/template-update/role-layout-history']
supplement_files=['.sys4ai/ontology/semantic/index-v1.json','.sys4ai/ontology/semantic/model.json',
    '.sys4ai/ontology/build.lock','.sys4ai/ontology/semantic/index.lock','.sys4ai/ontology/semantic/setup.lock',
    '.sys4ai/memory/backend-config/config.json','.sys4ai/memory/backend-config/certification.json',
    '.sys4ai/template-update/state.json','.sys4ai/template-update/lock','.sys4ai/template-update/watcher.json']

def generated_inventory():
    selected={ROOT/f for f in supplement_files if (ROOT/f).is_file()}
    for name in supplement_trees:
        for parent,dirs,files in os.walk(ROOT/name,followlinks=False):
            dirs[:]=[d for d in dirs if d not in {'.git','__pycache__','node_modules'}]
            for name in files:
                p=Path(parent)/name
                if not p.is_symlink():selected.add(p)
    return {str(p.relative_to(ROOT)):metadata(p) for p in sorted(selected)}

supplement={'captured_at':now(),'timing':'Collected after initial named checks, before the existing endpoint identity probe. This is a future implementation preservation baseline; it does not retroactively prove initial checks preserved generated products.',
    'trees':supplement_trees,'single_files':supplement_files,
    'excluded':{'credential_runtime':'.sys4ai/ontology/workbench/* (session URL and private logs never copied)',
                'model_weight_caches':['.sys4ai/ontology/semantic/models','.sys4ai/memory/model-cache'],
                'other_runtime':'All .sys4ai paths outside the exact selections are unexamined.'},
    'before':generated_inventory()}

# Read only the public loopback origin from the already-existing private record.
# The bootstrap URL is never returned, copied, logged or used.
runtime=ROOT/'.sys4ai/ontology/workbench/root-verification.json'
origin=None
if runtime.is_file() and not runtime.is_symlink():
    candidate=json.loads(runtime.read_text()).get('origin')
    if isinstance(candidate,str) and re.fullmatch(r'http://127\.0\.0\.1:[1-9][0-9]{0,4}',candidate):origin=candidate
if origin:
    baseline['checks'].append(run('workbench-existing-identity',[
        '.venv/bin/python','.agents/skills/ontology/scripts/ontology.py','--project-root',str(ROOT),
        'advanced-health','--workbench-url',origin],timeout=60))
else:
    baseline['launch_probe_limitation']='No safe origin in the selected existing private session record; no endpoint guessed and no service started.'

supplement['after']=generated_inventory()
supplement['comparison']={'added':sorted(set(supplement['after'])-set(supplement['before'])),
    'removed':sorted(set(supplement['before'])-set(supplement['after'])),
    'changed':[p for p in supplement['before'] if p in supplement['after'] and supplement['before'][p]!=supplement['after'][p]]}
for phase in ['before','after']:
    supplement[phase+'_chunks']=parts('generated-'+phase,[{'path':p,**m} for p,m in supplement.pop(phase).items()])
write(LOGS/'generated-preservation.json',supplement)

publication=[]
for p in sorted((ROOT/'control_records/ontology').rglob('*.json')):
    if 'intent' not in p.name and '/intents/' not in str(p):continue
    if '/intents/' in str(p):paired=Path(str(p).replace('/intents/','/receipts/'))
    elif p.name=='root-adoption-intent.json':paired=p.with_name('root-adoption.json')
    else:paired=p.with_name(p.name.replace('-intent.json','-receipt.json'))
    d=json.loads(p.read_text())
    item={'intent':ref(str(p.relative_to(ROOT))), 'record_status':d.get('status'),
          'paired_receipt_exists':paired.is_file()}
    if paired.is_file():
        receipt=json.loads(paired.read_text())
        item.update({'receipt':ref(str(paired.relative_to(ROOT))), 'receipt_status':receipt.get('status'),
                     'recovery':receipt.get('recovery')})
    publication.append(item)
write(LOGS/'publication-recovery-inventory.json',{'captured_at':now(),'scope':'All retained intent files under control_records/ontology, paired with their owning receipt naming scheme; payload/prior contents are not copied.',
    'intents':publication, 'unpaired_intents':[r['intent']['path'] for r in publication if not r['paired_receipt_exists']],
    'qualification':'Paired complete/applied receipts are recorded historical outcomes. This baseline does not grant publication/recovery or claim current runtime owner availability.'})

baseline['protected_inventory_count']=len(baseline['protected_before'])
for phase in ['before','after']:
    baseline['protected_'+phase+'_chunks']=parts('protected-'+phase,[{'path':p,**m} for p,m in baseline.pop('protected_'+phase).items()])
baseline['generated_preservation']=ref(str((LOGS/'generated-preservation.json').relative_to(ROOT)))
baseline['publication_recovery_inventory']=ref(str((LOGS/'publication-recovery-inventory.json').relative_to(ROOT)))
head=(LOGS/'git-head.stdout.log').read_text().strip()
baseline['checkout']={'head':head,'recommendation_source_head':'744c8b06d5fda905201145ed313a2da8de2e601f',
    'matches_recommendation_snapshot':head=='744c8b06d5fda905201145ed313a2da8de2e601f',
    'dirty_state_log':str((LOGS/'git-status.stdout.log').relative_to(ROOT)),
    'tracked_dirty_paths':[l[3:] for l in (LOGS/'git-status.stdout.log').read_text().splitlines() if not l.startswith('??')],
    'dirty_classification':'The three tracked indexes were modified before this worker. Untracked prior plan/TRD/Task artifacts are prior work; paths under this evidence directory are worker outputs. Never erase existing edits.'}
baseline['behavior_baseline']={'cli_launcher':'.agents/skills/ontology/scripts/ontology.py --project-root ROOT workbench --session-file PRIVATE_PATH',
    'service_started_by_this_worker':False,'old_frontend_destinations':['Explore','Draft editor','Review','Advanced'],
    'source':ref('SKILLS-depo/ontology/workbench/index.html'),
    'reader_behavior':'Core term/read queries succeeded with selected current sources. Browser authoring remains present in current assets; production Explorer is not implemented by this baseline.',
    'retrieval_defaults':json.loads((ROOT/'ontology.yaml').read_text())['retrieval'],
    'semantic_default_source':source_lines('SKILLS-depo/ontology/scripts/ontology_retrieval.py','semantic=True'),
    'advanced_assessment':'Static readiness passed for selected existing profiles. No provisioning, model execution, standards query, browser session, or broad advanced suite was performed.'}
baseline['named_check_results']={'query_retrieval':'7 tests passed','publication':'8 tests passed',
    'template_check':'current','installed_core_check':'valid; competency results in raw log',
    'core_health':'ready true; selected static','advanced_health':'ready true; selected static; operations not exercised'}
baseline['limitations']=['No browser interaction or frontend usability baseline was exercised.',
    'Read-only scope does not start, repair, build or stop the existing service.',
    'Full ontology/advanced suites were not needed for this baseline; existing advanced configuration/certification was assessed statically only.',
    'Independent non-Template product projects and model weight cache bytes were excluded from this bounded baseline.',
    'Protected Task files may later change through authorized manager bookkeeping; classify those separately from product mutations.']
baseline['finalized_at']=now()
write(OUT/'baseline.json',baseline)

caller=json.loads((OUT/'caller-inventory.json').read_text())
caller['entries_chunks']=parts('caller-entries',caller.pop('entries'))
write(OUT/'caller-inventory.json',caller)

result={'schema_version':1,'worker':'/root/explorer_manager_g3/baseline_worker','status':'stopped_with_completed_baseline',
    'task_id':'TASK-20260919-1FA1F620','plan_task':'TASK-001','captured_at':now(),
    'checks':baseline['checks'],'checkout':baseline['checkout'],
    'criteria':[{'criterion':1,'evidence':['baseline.json','caller-inventory.json'],'result':'Current checkout, pre-existing edits, named checks, launch/source behavior and active/historical caller classification captured.'},
                {'criterion':2,'evidence':['process-content-inventory.json'],'result':'Each selected process/function field is source-backed, absent in the selected canonical representation, or explicitly unexamined; partial source ordering is distinguished from complete sequence.'},
                {'criterion':3,'evidence':['process-content-inventory.json'],'result':'Seven local files contain 347 records INCLUDING 65 bindings (90 project + 192 curator + 65 bindings); full load 412 adds 65 imported-core records. Full loaded non-binding 347 is a different coincidental count. Curator process is typed Capability and its identity does not prove ordered steps.'}],
    'outputs':[ref(str(p.relative_to(ROOT))) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='result.json'],
    'allowed_write_boundary':['Verification/project-knowledge-explorer-first-release/baseline.json','Verification/project-knowledge-explorer-first-release/caller-inventory.json','Verification/project-knowledge-explorer-first-release/process-content-inventory.json','Verification/project-knowledge-explorer-first-release/baseline-tests/'],
    'protected_comparison':baseline['protected_comparison'],'generated_comparison':supplement['comparison'],
    'limitations':baseline['limitations'],'verification_level':'Targeted tests passed and actual core query behavior observed; frontend runtime not exercised.',
    'no_product_or_canonical_writes':True}
write(LOGS/'result.json',result)
print(json.dumps({'baseline_size':(OUT/'baseline.json').stat().st_size,'caller_size':(OUT/'caller-inventory.json').stat().st_size,
    'result_size':(LOGS/'result.json').stat().st_size,'publication_intents':len(publication),'generated_comparison':supplement['comparison']},indent=2))
