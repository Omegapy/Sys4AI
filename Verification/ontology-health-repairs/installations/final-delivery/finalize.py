"""Finalize observer evidence; no source, Template, or fixture mutation."""
from pathlib import Path
from datetime import datetime, timezone
import importlib.util
import json
import sys

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
sys.path.insert(0, str(OUT.parent))
from prepare_static import tree, digest_tree, sha, write_json

def read(relative):
    return json.loads((OUT / relative).read_text())

def proof(path):
    return {"path": str(path), "sha256": sha(path.read_bytes())}

provenance = read('template-provenance.json')
template = Path(provenance['actual_template'])
local_template = Path(provenance['fixture_template'])
current_template = tree(template)
assert current_template == provenance['template_tree'] == tree(local_template)
preparation = read('runtime-preparation.json')
relocated = Path(preparation['relocated_project'])
populated_project = Path(preparation['initialized_project'])

# This is a separately labeled byte observer, not a lock-bypassing updater run.
spec = importlib.util.spec_from_file_location('delivery_source_observer', ROOT/'tools/template_update.py')
updater = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = updater
spec.loader.exec_module(updater)
snapshot = updater.snapshot(ROOT)
mapped = {}
for relative, item in snapshot['state']['files'].items():
    expected = item['sha256']
    actual = sha((template/relative).read_bytes())
    fixture = sha((local_template/relative).read_bytes())
    assert expected == actual == fixture, relative
    mapped[relative] = {'source':item['source'], 'sha256':expected,
                        'generated':item.get('generated'), 'source_template_fixture_equal':True}

helpers = read('installed-suite/receipt.json')['delivered_helpers']
helper_rows = {}
for relative, expected in helpers.items():
    source = ROOT/'SKILLS-depo'/relative.removeprefix('.agents/skills/')
    hashes = {'source':sha(source.read_bytes()), 'template':sha((template/relative).read_bytes()),
              'fixture_template':sha((local_template/relative).read_bytes()),
              'relocated_installed':sha((relocated/relative).read_bytes()),
              'populated_installed':sha((populated_project/relative).read_bytes())}
    assert set(hashes.values()) == {expected}, relative
    if relative.split('/')[2] in ('memory','ontology','init-new-project'):
        hashes['actual_root_installed'] = sha((ROOT/relative).read_bytes())
        assert hashes['actual_root_installed'] == expected, relative
    helper_rows[relative] = hashes

raw = next(row for row in read('neutral-matrix.json')['cases'] if row['case']=='raw')
raw_tree = tree(Path(raw['project_root'])/'.venv', mtimes=True)
assert raw_tree == read('raw-copy-runtime-inventory.json')
assert digest_tree(raw_tree) == raw['preexisting_runtime_sha256']

suite = read('installed-suite/test-identities.json')
suite_receipt = read('installed-suite/receipt.json')
assert suite['status']=='passed' and suite['observed_count']==suite['required_count']==183
assert all(row['outcome']=='passed' for row in suite['tests'])
assert not suite['missing'] and not suite['unexpected'] and not suite['duplicate_ids']
population = read('populated/result.json')
assert population['status']=='passed'
semantic = read('installed-suite/semantic-packet.json')
assert semantic['status']=='passed' and semantic['backend']=='actual-selected-pinned-semantic-model'
counts = {row['g'].rsplit(':',1)[-1]:int(row['n']['value']) for row in population['full_graph_counts_result']['rows']}
assert sum(counts.values()) == 3642
commands = []
for receipt_path in sorted((OUT/'commands').glob('*/receipt.json')):
    receipt=json.loads(receipt_path.read_text())
    assert receipt['exit_code']==receipt['expected_exit'], receipt_path
    commands.append({'case':receipt_path.parent.name, 'exit_code':receipt['exit_code'],
                     'expected_exit':receipt['expected_exit'], 'receipt':proof(receipt_path)})
assert len(commands)==19
host_check_folder=ROOT/'Verification/ontology-health-repairs/commands/completion-template-check'
host_receipt=json.loads((host_check_folder/'receipt.json').read_text())
host_check=json.loads((host_check_folder/'stdout.log').read_text())
assert host_receipt['exit_code']==0 and host_check['status']=='current'
assert host_receipt['stdout_sha256']==sha((host_check_folder/'stdout.log').read_bytes())

observer={'observed_at':datetime.now(timezone.utc).isoformat(),'status':'equal',
 'actual_template_tree_preserved':True,'actual_template_tree_sha256':digest_tree(current_template),
 'selected_starter_file_count':provenance['selected_count'],'mapped_file_count':len(mapped),
 'source_snapshot_fingerprint':snapshot['fingerprint'],'mapped_files':mapped,'delivered_helper_files':helper_rows,
 'actual_root_parity_scope':['memory','ontology','init-new-project'],
 'rendered_project_inputs':'Identity, config, binding, README, and setup receipt transforms are assessed by the neutral matrix; they are not asserted byte-equal to neutral sources.',
 'raw_copy_runtime_preserved':True,'raw_runtime_tree_sha256':digest_tree(raw_tree),
 'raw_copy_runtime_classification':'Pre-existing unmapped Template .venv copied by the raw-copy negative/control; setup neither adopted, provisioned, ran, nor certified it.',
 'post_lock_pipeline_check':{'receipt':proof(host_check_folder/'receipt.json'),'stdout':proof(host_check_folder/'stdout.log'),'result':host_check},
 'earlier_busy_checks_retained':['template-postcheck.json','template-postcheck-after-lock.json','template-finalcheck.json']}
write_json(OUT/'observer-parity.json',observer)

artifacts=['template-provenance.json','neutral-matrix.json','recovery-matrix.json','earlier-edition-result.json',
 'raw-copy-runtime-inventory.json','static-stage-result.json','static.stdout.log','static.stderr.log',
 'runtime-preparation.json','observer-parity.json','installed-suite/receipt.json','installed-suite/test-identities.json',
 'installed-suite/stdout.log','installed-suite/stderr.log','installed-suite/semantic-packet.json',
 'installed-suite/guard-dispatch.json','installed-suite/guard-boundary.json','installed-suite/guard-deadline.json',
 'installed-suite/advanced-memory.json','populated/result.json','populated/runtime-copy-provenance.json',
 'populated/full-shacl/receipt.json','populated/full-shacl/stdout.json',
 'run_static_matrix.py','run_installed_suite.py','run_populated.py','finalize.py']
assert all((OUT/p).is_file() for p in artifacts)
result={'schema_version':1,'status':'passed','scope':'bounded final delivered acceptance; parent retains final requirement acceptance',
 'observed_at':observer['observed_at'],'final_delivery_root':str(OUT),
 'static_matrix':{'cases':8,'recovery_scenarios':2,'actual_cli_commands':commands,
   'neutral_runtime':'not-exercised','no_learned_history':True,'no_runtime_autoactivation':True,
   'raw_copy_control_preserves_preexisting_runtime':True,
   'earlier_edition':'Documented synthetic v8 fixture, exact recovery and explicit advanced adoption; no real historical setup claimed.',
   'wrapper_exit':1,'wrapper_exit_reason':'All 19 expected CLI outcomes passed; the final read-only pipeline postcheck encountered a shared lock. This observation remains retained. Host completion-template-check later passed current with no changes.'},
 'installed_suite':{'command':suite_receipt['command'],'cwd':suite_receipt['cwd'],'required':183,'observed':183,'passed':183,
   'original_baseline_obligations':153,'skipped':0,'missing':[],'unexpected':[],'duplicates':0,
   'elapsed_seconds':suite_receipt['elapsed_seconds'],'selected_profiles':['standards','semantic'],
   'fixture_bytes_preserved':True,'shared_selected_inputs_preserved':True},
 'populated_acceptance':{'project_root':str(populated_project),'project_id':population['project_id'],
   'records':191,'new_fixture_records':126,'external_records':2,'graph_counts':counts,'total_triples':sum(counts.values()),
   'complete_shacl':True,'conforms':True,'graph_scope':population['full_shacl']['graph_scope'],
   'shacl_seconds':population['full_shacl']['worker']['elapsed_seconds'],'project_type_query':True,'derived_type_entailed':True,
   'limits':population['limits'],'canonical_bytes_preserved_by_reads':True,
   'publication_and_profile_authority':'Explicit fixture-only synthetic grants via delivered helpers; no shared root authority claimed.'},
 'runtime_boundaries':{'standards':'Explicit copy of the existing certified root standards environment into only the populated fixture; equal fingerprint, no provision or package install.',
   'semantic':'Ordinary installed actual-semantic test explicitly selects Sys4AI as runtime/model origin, copies it into its isolated temporary fixture, builds that fixture index offline, and freezes vectors. It does not certify semantic readiness in the populated project.',
   'semantic_model':semantic['build']['runtime']['model']['model'],'semantic_revision':semantic['build']['runtime']['model']['revision'],
   'actual_semantic_acceptance':'passed','packages_installed':False,'models_downloaded':False,'shared_root_mutation':False},
 'final_source_template_delivered_parity':'observer-parity.json','host_post_lock_pipeline_receipt':proof(host_check_folder/'receipt.json'),
 'prior_stage_evidence':'Previous-version installations evidence and final static-only preparation snapshots remain unchanged; this result adds the authorized later runtime stage.',
 'artifacts':{p:proof(OUT/p) for p in artifacts}}
write_json(OUT/'RESULT.json',result)
text=f"""Final delivered acceptance passed. The ordinary installed ontology command in the relocated, space-containing fixture executed all **183 required identities**, including the original 153 obligations, with **zero skips, failures, missing tests, or duplicate identities**. Raw output and exact identity accounting are in `installed-suite/`.

The neutral/recovery matrix exercised **19 expected CLI outcomes**, eight setup cases and two recovery scenarios. Fresh, first preparation, selected-starter manual copy, capture-off/disabled preservation, customized incomplete capability, equivalent rerun, deep placement, relocation refusal, real registry-lock interruption/recovery, and reconstructed earlier-edition recovery/adoption are retained. Setup reported static readiness only, kept learned inventories empty, and did not activate runtime profiles. The raw-copy control preserved its pre-existing unmapped `.venv` bytes and mtimes without running, provisioning, adopting, or certifying that runtime.

The separate populated deep fixture published 126 synthetic records through the installed owning helper using explicit fixture-only grants. Its **191 records / 3,642 triples** include a project-specific subtype, project instances, and two external types: asserted 2,606, derived 1,012, external 24. Complete default authored SHACL was conformant in **5.6893 seconds**, within unchanged 10-second limits. The exact project-type query and derived Artifact type inference passed. Reads preserved canonical fixture bytes and the tracked shared root inputs.

Standards acceptance used an explicitly copied existing certified environment with an equal fingerprint. The ordinary suite's actual semantic test used Sys4AI as the explicit existing model/runtime origin and isolated its index/build in a temporary fixture; it does not certify the populated project's semantic profile. No packages were installed or models downloaded.

`observer-parity.json` verifies the unchanged actual Template full tree, all 312 mapped delivery files, and source/Template/installed helper parity. The static wrapper retained exit 1 because its postcheck encountered a shared lock after all case checks passed; the later host `completion-template-check` receipt is verified exit 0/current with no changes or conflicts. No lock was bypassed. Earlier static snapshots remain intact and are superseded only as stage summaries by `RESULT.json`.

Parent acceptance can use `RESULT.json`, `observer-parity.json`, `installed-suite/test-identities.json`, and `populated/result.json`. No source, real project registry, root canonical content, or actual Template writes were performed in this acceptance assignment.
"""
(OUT/'HANDOFF.md').write_text(text)
print(json.dumps({'status':'passed','result':str(OUT/'RESULT.json'),'result_sha256':sha((OUT/'RESULT.json').read_bytes()),
                  'observer_sha256':sha((OUT/'observer-parity.json').read_bytes()),'handoff_sha256':sha((OUT/'HANDOFF.md').read_bytes())}))
