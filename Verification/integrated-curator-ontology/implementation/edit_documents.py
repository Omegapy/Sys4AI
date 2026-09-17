from pathlib import Path
import json
out=Path('Verification/integrated-curator-ontology/implementation/preimages')
def save(name):
 p=Path(name);prior=out/name
 if not prior.exists():prior.parent.mkdir(parents=True,exist_ok=True);prior.write_bytes(p.read_bytes())
 return p
p=save('SKILLS-depo/init-new-project/tests/test_curator_setup.py');p.write_text(p.read_text().replace("record['setup_contract'],'governance-starter-v11'","record['setup_contract'],'governance-starter-v12'"))
p=save('CURATION-depo/contract.json');d=json.loads(p.read_text());d['compatibility']['preserved_setup_editions'].append('governance-starter-v11');d['compatibility']['setup_edition']='governance-starter-v12';d['ontology_integration']={'edition':'curator-ontology-1.0.0','recipe':'reference-assets/ONTOLOGY-depo/integrations/curator/1.0.0','owner':'ontology','setup_generated':True,'authored_publication':'exact integrate-curator owner grant','runtime_authority':False};p.write_text(json.dumps(d,indent=2)+'\n')
for name,text in {
'SKILLS-depo/ontology/references/commands.md':'''\n## Curator semantic integration\n\n`integration-preview SELECTION.json` returns the exact `proposal` and stable\n`preview_sha256`. The selection has schema_version 1, an `ONTOP-` operation_id,\nand a bounded reason. `integration-publish PROPOSAL.json --grant-file GRANT.json\n--expected-preview-sha256 DIGEST` publishes only ontology.yaml additive selections\nand the three reserved Curator files. `integration-recover OPERATION_ID\n--grant-file GRANT.json` continues the original accepted intent. All file arguments\nare confined project-relative paths. The separate `integrate-curator` grant binds\nthe original configuration predecessor, even after a partial config commit.\n\nUse the current Director or confirmed manager; support roles do not own canonical\npublication. A schema-1 integration grant requires orchestration version 1 for a\nmanager. Protected-native version 2 needs a separately supported grant contract\nand remains a diagnostic hold. Guard validation supplies no grant.\n\nThe recipe describes policy inspection, scoped review, update/correction owners,\nexact retry, Task pause/resume, selected dispatch, session catch-up and bounded\nlog access. Queries report declared source freshness and never certify execution.\n''',
'ONTOLOGY-depo/publication-and-recovery.md':'''\n## Curator integration owner operation\n\nThe schema-1 `integrate-curator` operation is separate from ordinary publication.\nIt selects only ontology.yaml and reserved curator.jsonld graph/binding and\ncurator-competency.json files. Config changes append deduplicated recipe-required\nproject, binding, competency and source-allowlist selections; identity, core locks,\nprofiles, retrieval and publication configuration remain unchanged.\n\nImmutable intent records retain all original target bytes before graph, bindings,\ncompetencies and config are replaced in that order. Reads diagnose partial state.\nRecovery requires fresh current authority bound to the original preview and\nconfiguration predecessor, exact pre/post targets and unchanged sources/helpers.\nThird-state edits remain preserved. Publication receipts and completed v12 setup\nreceipts establish exact generated integration ownership for explicit refresh.\nEqual unowned bytes do not establish ownership. No cross-file atomicity is claimed.\n''',
'SKILLS-depo/init-new-project/SKILL.md':'''\n## Integrated Curator edition\n\nNew and first preparation select governance-starter-v12. This edition specializes\nthe Curator process and all function semantics after identity, session choice,\nowner packages and Roles/INDEX.md settle. The Template retains empty active graphs,\nnull project identity, unbound authority and disabled session policy.\n\nFor a previously initialized project, select `prepare-existing --adopt-module\ncurator`. To refresh an earlier Curator installation explicitly add\n`--refresh-module curator`; `project-curator` is the retained alias. An ordinary\nrerun verifies its recorded edition. Original setup receipts and v1-v11 meanings\nremain unchanged. Unchanged completed selections verify without new operations.\n\nCompatible authored ontology uses an exact ontology-owner publication. A missing\ngrant leaves a resumable `curator_integration.preview` in the setup receipt. Supply\n`--integration-grant-file` and optionally `--integration-proposal-file` on the same\nrequest after exact review. API callers may supply a trusted current grant callback.\nThis route adds no installation, background AI, Git or unselected-project authority.\nStatic semantic success is separate from current runtime execution.\n''',
'depot/template-update.md':'''\nCurator integration resources under ONTOLOGY-depo/integrations/curator/1.0.0 are\nneutral source material mapped through the existing reference-assets distribution.\nThe v12 initializer generates project-local semantic records after specialization;\nno populated Curator graph or receipt is distributed as a Template starter.\n''',
'ROLES-depo/project-curator-CURATOR.md':'''\n## Functional ontology integration\n\nThe selected initializer supplies the Curator process and function knowledge from\nthe neutral curator-ontology-1.0.0 recipe. Ontology records describe current source\ncontracts and supporting roles. Canonical operations still require their actual\nDirector or confirmed Task manager and the existing public owner. Source freshness,\ninstalled capability, session configuration and completed execution remain distinct.\n''',
'SKILLS-depo/curate/references/session-maintenance.md':'''\n## Semantic context\n\nThe Curator ontology describes collection, owner evaluation and selected dispatch\nas separate steps. Retained delivery means pending input, and dispatch alone does\nnot prove a completed owner outcome. Current-owner receipts determine consumption.\nSession-off remains an explicit opt-out; no ontology record enables background AI.\n'''
}.items():
 p=save(name);p.write_text(p.read_text()+text)
p=save('SKILLS-depo/init-new-project/assets/initialization-receipt.schema.json');d=json.loads(p.read_text())
def visit(v):
 if isinstance(v,dict):
  if isinstance(v.get('enum'),list) and 'governance-starter-v11' in v['enum']:v['enum'].append('governance-starter-v12')
  for x in v.values():visit(x)
 elif isinstance(v,list):
  for x in v:visit(x)
visit(d)
d['properties']['curator_integration']={'type':'object','description':'Exact v12 generated or current ontology-owner integration disposition and immutable receipt link.'}
d['properties']['generated_files']={'type':'object','description':'Exact generated Curator outputs, separately bound to neutral recipe manifest hashes.'}
# Explicit schema 2 Curator operation has independent frozen edition and selection.
def module(v):
 if isinstance(v,dict):
  props=v.get('properties',{})
  if 'module_id' in props and 'manifest_sha256' in props:
   props['schema_version']={'enum':[1,2]}
   props['integration_edition']={'const':'curator-ontology-1.0.0'}
   props['curator_integration']={'type':'object'}
   if 'refresh_modules' in props:props['refresh_modules']['items']={'enum':['ontology','project-curator']}
  for x in v.values():module(x)
 elif isinstance(v,list):
  for x in v:module(x)
module(d);p.write_text(json.dumps(d,indent=2)+'\n')
