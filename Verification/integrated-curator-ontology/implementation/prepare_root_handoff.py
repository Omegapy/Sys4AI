"""Prepare exact root source adoption and guard-repair review; never apply them.

Run on the final source bytes after the implementation writer has stopped.
"""
from pathlib import Path
import ast,copy,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent/'root-handoff'
OUT.mkdir(exist_ok=True)
def encoded(x):return (json.dumps(x,indent=2,sort_keys=True,ensure_ascii=False)+'\n').encode()
def sha(raw):return hashlib.sha256(raw).hexdigest()
files={'.agents/skills/ontology/scripts/'+name:'SKILLS-depo/ontology/scripts/'+name for name in ('ontology.py','ontology_core.py','ontology_integration.py','ontology_publication.py','ontology_guards.py','ontology_knowledge.py')}
files['.agents/skills/ontology/references/commands.md']='SKILLS-depo/ontology/references/commands.md'
publication=(ROOT/'reference-assets/ONTOLOGY-depo/publication-and-recovery.md').read_bytes()
new_section=(ROOT/'ONTOLOGY-depo/publication-and-recovery.md').read_text().split('\n## Curator integration owner operation\n',1)[1]
publication_proposal=publication+b'\n## Curator integration owner operation\n'+new_section.encode()
(OUT/'publication-and-recovery.proposed.md').write_bytes(publication_proposal)
files['reference-assets/ONTOLOGY-depo/publication-and-recovery.md']=(OUT/'publication-and-recovery.proposed.md').relative_to(ROOT).as_posix()
files['reference-assets/ONTOLOGY-depo/actions/contracts-v1.json']='ONTOLOGY-depo/actions/contracts-v1.json'
for name in ('recipe.json','locators.json','competency.json','manifest.json','contract.md'):
 files['reference-assets/ONTOLOGY-depo/integrations/curator/1.0.0/'+name]='ONTOLOGY-depo/integrations/curator/1.0.0/'+name
charter=(ROOT/'CURATOR.md').read_text()
old='''This reusable charter describes an optional controller for bounded project
maintenance. Installation and reading this file are inactive. The ordinary
Project Director remains the default controller. Select one controller and one
exact charter for a new execution through protected project policy.

Bind each selection to the adopting project's `project.json`, README, SPECS.md
and the identity in `curator.yaml`. Those local sources supply its name, purpose,
domain and maintenance priorities. This shared charter supplies the common
responsibilities; it does not import another project's records or expertise.'''
new='''This charter describes bounded maintenance for the Sys4AI depot. Enabled
`curator-session.yaml` collects changed-input observations at session start and
return. The current owner separately evaluates and dispatches eligible work
within its configured session budget. The Project Director remains the default
controller; a new Task execution still needs its exact protected selection.

Bind each selection to the actual Sys4AI depot identity in `depot/projects.json`,
`curator.yaml` and `ontology.yaml`, with README and SPECS.md supplying local
purpose and scope. The depot has no project.json. This charter supplies common
responsibilities without importing another project's records or expertise.'''
if old not in charter:raise SystemExit('Root CURATOR.md differs from the reviewed correction predecessor; inspect before regenerating.')
charter=charter.replace(old,new)
prior_route='''For a new ordinary execution, validate the schema-version-1 selection artifact
through `validate_controller_selection`. It binds the prepared project, this
charter, current policy and current role pair. Freeze its exact bytes and returned
source references in the normal manager reservation's `source_refs` and context.
Use Task schema 2 with orchestration version 1, then record the actual native
manager receipt, required charter/policy/role reads and confirmed activation.
The selection itself enables no standing entitlement or schedule. Existing
orchestration version 2 records keep their original requirements and history.'''
root_route='''This depot's session maintenance uses its existing root Task and current-owner
routes. The prepared-project `validate_controller_selection` artifact applies
only where its required project.json exists; it is not a supported depot-root
selection route. Do not manufacture project.json to use it. Explicit root Task
execution retains its current intake, reservation, actual native receipt,
required role reads and confirmed manager activation. Existing orchestration
versions retain their original requirements and history. Collection or semantic
context alone enables no execution, standing entitlement or schedule.'''
if prior_route not in charter:raise SystemExit('Root controller paragraph changed; inspect its exact predecessor.')
proposed_charter=charter.replace(prior_route,root_route).encode();(OUT/'CURATOR.proposed.md').write_bytes(proposed_charter)
files['reference-assets/CURATION-depo/contract.json']='CURATION-depo/contract.json'
files['tools/template_update.py']='SKILLS-depo/init-new-project/assets/template_update.py'
files['CURATOR.md']=(OUT/'CURATOR.proposed.md').relative_to(ROOT).as_posix()
rows=[]
for destination,source in files.items():
 raw=(ROOT/source).read_bytes();target=ROOT/destination
 rows.append({'source':source,'destination':destination,'source_sha256':sha(raw),'before_sha256':sha(target.read_bytes()) if target.exists() else None,'after_sha256':sha(raw),
              'route':'ontology-guard-repair' if '/scripts/' in destination or destination in ('reference-assets/ONTOLOGY-depo/actions/contracts-v1.json','tools/template_update.py') else 'exact-local-source-adoption'})
(OUT/'source-adoption-manifest.json').write_bytes(encoded({'schema_version':1,'root':str(ROOT),'authority':'Host /root after current overlap/owner reconciliation','preserve':['.agents/skills/init-new-project','.agents/skills/agent-task','AGENTS.md','ROLE.md','SOUL.md','memory.yaml','MEMORY','Tasks','ontology.yaml','ONTOLOGY/modules/sys4ai-core'], 'files':rows}))
# Prepare the candidate adapter inventory from actual selected old or proposed
# bytes. The existing guard owner validates this bundle without executing it.
contract=json.loads((ROOT/files['reference-assets/ONTOLOGY-depo/actions/contracts-v1.json']).read_text())
family={key:{} for key in ('ontology','memory','task','trd','plan','role','template','setup')}
for action in contract['actions']+contract.get('optional_actions',[]):
 path=action['dispatch']['path'];raw=(ROOT/files.get(path,path)).read_bytes();tree=ast.parse(raw)
 symbol=action['dispatch']['symbol'];operation=action['operation']
 if action in contract.get('optional_actions',[]) and not any(isinstance(n,ast.FunctionDef) and n.name==symbol for n in tree.body):continue
 declarations=[]
 for node in tree.body:
  if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='ONTOLOGY_GUARDED_ACTIONS' for t in node.targets):declarations=ast.literal_eval(node.value)
 if symbol not in declarations and operation not in declarations:raise SystemExit('Candidate adapter declaration is incomplete: '+path+' '+operation)
 family[action['family']].setdefault(path,{'path':path,'sha256':sha(raw),'operations':[]})['operations'].append(operation)
adapters={'schema_version':1,'families':{key:[dict(row,operations=sorted(row['operations'])) for _,row in sorted(value.items())] for key,value in sorted(family.items())}}
op='ONTGUARD-curator-integration-20260913'
base='control_records/ontology/guard-bootstrap/'+op
config=json.loads((ROOT/'ontology-advanced.yaml').read_text());old_selected=config['profiles']['guards']
old_bootstrap=json.loads((ROOT/old_selected['bootstrap']['path']).read_text())
contract_ref={'path':'reference-assets/ONTOLOGY-depo/actions/contracts-v1.json','sha256':sha(encoded(contract))}
# Preserve exact file bytes, including source ordering, instead of re-encoding.
contract_ref['sha256']=sha((ROOT/files[contract_ref['path']]).read_bytes())
adapter_ref={'path':base+'-adapters.json','sha256':sha(encoded(adapters))}
def bound(path):return {'path':path,'sha256':sha((ROOT/files.get(path,path)).read_bytes())}
bootstrap={'schema_version':1,'status':'verified','operation_id':op,'contract':contract_ref,'repair':old_bootstrap['repair'],'adapters':adapter_ref,
           'engine':bound('.agents/skills/ontology/scripts/ontology_guards.py'),'setup':bound('.agents/skills/ontology/scripts/ontology_guard_setup.py'),
           'verification':old_bootstrap.get('verification'),'repair_basis':'Exact enabled guard repair; current actual-backend regressions in Verification/integrated-curator-ontology/implementation.'}
bootstrap_ref={'path':base+'-bootstrap.json','sha256':sha(encoded(bootstrap))}
config['profiles']['guards']={'enabled':True,'contract':contract_ref,'adapters':adapter_ref,'bootstrap':bootstrap_ref}
changes=[]
for row in rows:
 if row['route']=='ontology-guard-repair':changes.append({'path':row['destination'],'expected_sha256':row['before_sha256'],'sha256':row['after_sha256'],'content':(ROOT/row['source']).read_text()})
for path,raw in ((adapter_ref['path'],encoded(adapters)),(bootstrap_ref['path'],encoded(bootstrap)),('ontology-advanced.yaml',encoded(config))):
 target=ROOT/path;changes.append({'path':path,'expected_sha256':sha(target.read_bytes()) if target.exists() else None,'sha256':sha(raw),'content':raw.decode()})
(OUT/'guard-repair-selection.json').write_bytes(encoded({'operation_id':op,'changes':changes}))
(OUT/'integration-selection.json').write_bytes(encoded({'schema_version':1,'edition':'curator-ontology-1.0.0','operation_id':'ONTOP-curator-integration-root-20260913','reason':'Implement PLAN-20260913-64A6385B revision 1 root Curator integration.'}))
print(json.dumps({'status':'prepared-not-applied','files':len(rows),'guard_changes':len(changes),'output':str(OUT)},indent=2))
