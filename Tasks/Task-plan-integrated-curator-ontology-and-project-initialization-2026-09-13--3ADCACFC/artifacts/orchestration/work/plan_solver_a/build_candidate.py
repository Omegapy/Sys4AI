"""Build a planning-only candidate; never invokes managed-plan mutation routes."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import re
import sys

ROOT = Path('/Volumes/P-SSD/AngryOwl/Sys4AI')
OUT = Path(__file__).parent
NOW = datetime.now(timezone.utc).isoformat()
TRD = 'TRDs/trd_integrated-project-curator-ontology-and-project-initializati_2026-09-13.md'
def read(path):
    p = ROOT / path
    for part in [p, *p.parents]:
        assert not part.is_symlink(), str(part)
    return p.read_bytes()
def digest(path): return hashlib.sha256(read(path)).hexdigest()
def dump(path, value): path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')

sources = []
source_requirements = {}
def source(path, title, facts, reqs, kind='file', external_id=None):
    sid = f'SRC-{len(sources)+1:03}'
    sources.append(dict(source_id=sid, kind=kind, locator=path, title=title,
        accessed_at=NOW, digest='sha256:'+digest(path), facts_used=facts,
        access_limitations=[], provenance_mode='agent_inspected',
        inspection_method='direct_text', external_id=external_id))
    source_requirements[sid] = reqs
    return sid

ALL = [f'REQ-{n:03}' for n in range(1,15)]
source(TRD, 'Approved integrated Curator TRD revision 2', [
    'TRD-20260913-C85981B3 revision 2 is trd_done and contains 14 requirements, 34 acceptance clauses and no open questions or assumptions.',
    'Functional Curator integration covers root, reusable neutral Template, new creation, first preparation and selected prior-project adoption; approval establishes requirements only.',
    'Term identifiers, resource packaging, specialization and the next setup edition are planning choices, not missing user requirements.'
], ALL, 'trd', 'TRD-20260913-C85981B3 revision 2')
source('AGENTS.md', 'Depot instructions', ['Source collections own reusable changes; checked Template distribution, selected adoption, current canonical owners and independent state systems remain required.'], ALL)
source('SOUL.md', 'Engineering and preservation rules', ['Inspect current sources, choose the smallest complete design and distinguish static, runtime and end-to-end evidence.'], ALL)
source('ROLE.md', 'Depot Director and Task authority', ['The current confirmed manager owns its Task; the host owns registration and reusable adoption; roles and ontology do not grant action authority.'], ALL)
source('SPECS.md', 'Root technical specifications', ['Root helpers use .venv Python 3.12, standard-library transactions and exact source hashes; project ontology and memory remain separate. Some edition prose is historical and executing helper bytes govern the actual selected edition.'], ALL)
source('.agents/skills/curate/ACTIONS.md', 'Installed Curator action inventory', ['Status/validate, review, update, correct, retry, pause/resume, tick and bounded log routes use fixed existing owners. Session collection creates no Task or activation.'], ['REQ-001','REQ-002','REQ-003','REQ-009','REQ-010'])
source('.agents/skills/curate/references/session-maintenance.md', 'Installed session contract', ['Enabled session-start/return collection queues changed inputs. Current owners dispatch at most one operation with two model calls, 30 seconds, 1,000,000 candidate bytes and at most three agent slots per checkpoint; actual capacity can be lower. Outcomes alone consume deliveries.'], ['REQ-001','REQ-002','REQ-003','REQ-005','REQ-006','REQ-007','REQ-009','REQ-010'])
source('.agents/skills/ontology/SKILL.md', 'Installed ontology boundaries', ['Read queries preserve current source context and do not repair, run a discovered action, publish or provision. Canonical ontology writes require an exact proposal and current ontology grant.'], ['REQ-001','REQ-002','REQ-003','REQ-004','REQ-008','REQ-009','REQ-012','REQ-013'])
source('.agents/skills/ontology/references/commands.md', 'Ontology query, health and workbench interfaces', ['capability and knowledge --intent current are bounded reads; compile, build-wiki and link-memory are separate writes. Operational health differs from browser navigation and guarded dispatch. Private on-demand workbench browsing requires selected service startup.'], ['REQ-002','REQ-003','REQ-009','REQ-012','REQ-013','REQ-014'])
source('SKILLS-depo/ontology/scripts/ontology_modules.py', 'Locked import implementation', ['The loader accepts only sys4ai-core, verifies complete manifest and file hashes, and excludes imported project instances and bindings. A new imported Curator module is not supported today.'], ['REQ-002','REQ-003','REQ-004','REQ-008'])
source('SKILLS-depo/ontology/scripts/ontology_core.py', 'Compact ontology configuration and local record loader', ['Existing project_files and binding_files allow multiple explicitly selected project-local files; records must use the destination namespace and module project. Canonical configuration admits exact allowlisted source paths and competency files.'], ['REQ-002','REQ-003','REQ-004','REQ-005','REQ-006','REQ-007','REQ-008'])
source('SKILLS-depo/ontology/scripts/ontology_validate.py', 'Typed record and binding validator', ['Concepts, instances, predicates, relations and bindings have exact constraints; role bindings require both AGENTS.md and ROLE.md and labels require explicit ambiguity handling.'], ['REQ-002','REQ-003','REQ-004','REQ-008'])
source('SKILLS-depo/ontology/scripts/ontology_knowledge.py', 'Capability and current-source query behavior', ['capability selects Skill/Capability types and providesCapability edges; current_sources reads selected source bytes with recorded and actual hashes. Current capability availability follows source freshness and must not be mistaken for runtime or authorization.'], ['REQ-002','REQ-003','REQ-009','REQ-014'])
source('ONTOLOGY-depo/publication-and-recovery.md', 'Ontology owner publication and recovery', ['Canonical publish permits configured project, binding and competency files. Configuration and imported modules belong to separately authorized initializer/adoption work. Exact previews, current grants, lock-time checks, durable partial intent and unchanged replay are mandatory.'], ['REQ-001','REQ-003','REQ-004','REQ-007','REQ-008','REQ-009','REQ-013'])
source('ONTOLOGY-depo/starter/ontology.yaml', 'Neutral ontology configuration', ['Template identity and publication binding are null, publication is disabled, core 1.0.0 is locked and only neutral empty project/binding starter files are selected.'], ['REQ-004','REQ-005','REQ-006','REQ-007','REQ-008'])
source('ONTOLOGY-depo/starter/ONTOLOGY/modules/project/project.jsonld', 'Neutral project graph', ['The complete project graph is empty. Neutral definition recipes must not be mistaken for active project-instance records.'], ['REQ-004','REQ-005','REQ-006'])
source('ONTOLOGY-depo/starter/ONTOLOGY/bindings/bindings.jsonld', 'Neutral source binding graph', ['The complete binding graph is empty; installed-source hashes require destination specialization.'], ['REQ-003','REQ-004','REQ-005','REQ-006'])
source('SKILLS-depo/init-new-project/SKILL.md', 'Reusable initializer contract', ['Current reusable setup is governance-starter-v11. create and prepare-existing use only the registered Template. Selected --adopt-module curator covers earlier completed setups, with ordinary reruns preserving recorded editions and opt-outs.'], ['REQ-004','REQ-005','REQ-006','REQ-007','REQ-008','REQ-009','REQ-014'])
source('SKILLS-depo/init-new-project/scripts/init_curator.py', 'Curator adoption and assessment implementation', ['source_files selects Curator resources and complete owner packages. protected_inventory protects ONTOLOGY and ontology.yaml; existing starters are preserved. Current assessment checks installation/configuration/interfaces but does not materialize functional ontology records.'], ['REQ-004','REQ-005','REQ-006','REQ-007','REQ-008'])
source('SKILLS-depo/init-new-project/scripts/init_new_project.py', 'Initializer source and current edition', ['New setup specializes identity and Curator/session settings. Existing ontology packages are preserved as a whole unless pristine. The current source has edition-specific neutral validation and exact receipt stages; integration requires a coordinated new setup edition and selected module operation.'], ['REQ-004','REQ-005','REQ-006','REQ-007','REQ-008','REQ-014'])
source('CURATION-depo/contract.json', 'Reusable Curator resource and owner contract', ['The complete resource inventory and owner entry points cover Task, memory, ontology, learning, roles, setup and distribution. Current contract states retained support and separately unexercised native dispatch.'], ['REQ-002','REQ-003','REQ-004','REQ-009','REQ-014'])
source('depot/template-update.md', 'Template update and recovery guide', ['Reusable sources reach only the registered Template via check/apply. Configuration overrides and reference collection discovery have distinct destinations. Unknown targets, drift, symlinks and exact pending recovery remain fail-closed.'], ['REQ-004','REQ-005','REQ-006','REQ-007','REQ-008','REQ-014'])
source('depot/template-update.json', 'Current Template mappings', ['The selected Template path is Projects/Sys4AI-Template-Project. Exact overrides select current empty ontology starter graphs; Curator source contracts follow reference collection discovery.'], ['REQ-004','REQ-008','REQ-014'])
source('depot/projects.json', 'Factual project registry', ['The current registry contains the sys4ai-depot manager and neutral sys4ai-template-project; registration supplies no bulk adoption or publication authority.'], ['REQ-001','REQ-004','REQ-007','REQ-008','REQ-014'])
source('curator.yaml', 'Root Curator identity and inactive background configuration', ['The root identifies sys4ai-depot and its exact absolute coordination root; unattended schedule, autonomous writes, service and hook installation remain disabled.'], ['REQ-001','REQ-009','REQ-013'])
source('curator-session.yaml', 'Root enabled session configuration', ['Root project-session maintenance is enabled with stated bounded catch-up; unattended_background_ai is false.'], ['REQ-001','REQ-009','REQ-010'])
source('ontology.yaml', 'Root ontology selection', ['The root selects its existing authored project graph and four binding files, core 1.0.0 and sys4ai-depot namespace. Its source allowlist lacks the Curator skill/action/session sources; exact configuration adoption is needed before their canonical bindings.'], ['REQ-001','REQ-002','REQ-003','REQ-008','REQ-013'])
source('Verification/root-health-followup-trd-20260912-v1/REPORT.md', 'Dated supplied root health report', ['September 12 observations reported no Curator ontology match, two pending catch-up signals, 42,406 changed-path metadata rows and a staged 1,425-byte response under cancelled TASK-20260910-7F1A11AE revision 238. These are dated observations.', 'At that observation memory retrieval and ontology backends passed; workbench had no selected endpoint and was not_assessed, not proved failed.'], ['REQ-001','REQ-010','REQ-011','REQ-012','REQ-013','REQ-014'])
source('Verification/curator-ontology-integration-trd-20260913-v1/integration-observation.json', 'TRD integration source observation', ['The retained observation binds empty source/Template graphs and the original preserved ontology adoption behavior; later inspected source bytes are separately recorded in this plan.'], ['REQ-003','REQ-004','REQ-005','REQ-006','REQ-007','REQ-008'])
source('Verification/guard-capacity-20260913/REPORT.md', 'Separately authorized guard prerequisite repair', ['A separate 64-to-128 MiB inventory capacity repair retained file-count, source, owner, freshness and deadline guards. Its root actual-backend dispatch and selected recovery checks are prerequisite evidence, not Curator integration completion.', 'The installed initializer remains v9 while reusable and Template are v11; the installed compatibility fixture must match the installed helper edition.'], ['REQ-004','REQ-007','REQ-008','REQ-013','REQ-014'])

raw_trd = read(TRD).decode()
requirements=[]
for match in re.finditer(r'^### (REQ-\d+) — ([^\n]+)\n(.*?)(?=\n### |\n## Decisions)', raw_trd, re.M|re.S):
    rid,title,body=match.groups()
    value=lambda field: re.findall(r'^- '+re.escape(field)+r': (.+)$', body, re.M)
    deps = re.findall(r'REQ-\d+',value('Depends on')[0])
    negative = {
    'REQ-001':['File presence, policy validity or name-only discovery is insufficient.'],
    'REQ-002':['Do not present unsupported operations as available or confuse coordination with owner execution.'],
    'REQ-003':['Retrieval performs no repair or canonical write; historical ontology and memory never replace a current owner check.'],
    'REQ-004':['Do not distribute root identity, live actors, backlog, learned records, project-instance claims or runtime evidence into the Template.'],
    'REQ-005':['No manual ontology follow-up may be omitted from successful new setup; installation is not live session evidence.'],
    'REQ-006':['Preserve authored content, established identity and explicit choices; incompatible preservation cannot be reported healthy.'],
    'REQ-007':['No implicit new edition on ordinary reruns; no bulk propagation or change to existing disabled settings.'],
    'REQ-008':['No wholesale graph replacement, duplicate IDs, receipt relabeling, stale replay or inferred overwrite authority.'],
    'REQ-009':['No unattended AI, scheduler, invented actor, second canonical writer, implicit publication or mutation from discovery.'],
    'REQ-010':['Do not consume a delivery before completed owner outcome or treat metadata rows as failure counts.'],
    'REQ-011':['Do not infer safe cleanup from age, cancellation or roster absence; no silent reopen or false Task completion.'],
    'REQ-012':['Do not expose private session token, require always-on service, classify absent endpoint as failure or infer write verification from browsing.'],
    'REQ-013':['Do not alter independent authored facts, memory records, capture settings, locked imports, runtimes or grants to produce healthy status.'],
    'REQ-014':['No file-only success, stale counts, fixtures as live evidence or unexercised requirement marked satisfied.']
    }[rid]
    source_ids=[s['source_id'] for s in sources if rid in source_requirements[s['source_id']]]
    requirements.append(dict(requirement_id=rid,title=title,outcome=value('Requirement')[0],
       intent='Preserve the approved integrated outcome and source meaning in TRD-20260913-C85981B3 revision 2, '+rid+'.',
       source_ids=source_ids,acceptance_criteria=value('Acceptance'),dependencies=deps,
       negative_requirements=negative,status='active',disposition=None,evidence=[]))
assert len(requirements)==14 and sum(len(r['acceptance_criteria']) for r in requirements)==34

tasks=[]
def task(n,phase,title,reqs,action,artifacts,deps,criteria,checks,risks):
    tasks.append(dict(task_id=f'TASK-{n:03}',phase_id=f'PHASE-{phase:03}',title=title,action=action,
       requirement_ids=[f'REQ-{r:03}' for r in reqs],design_basis=[],target_artifacts=artifacts,
       dependencies=[f'TASK-{i:03}' for i in deps],parallel_group=None,risks=risks,
       acceptance_criteria=criteria,verification_steps=checks,status='planned',
       blocker_reason=None,pause_reason=None,skip_reason=None,skip_authority=None,evidence=[],completed_at=None))

task(1,1,'Bind the implementation scope to fresh owner and source evidence',list(range(1,15)),
 'Before authorized execution, freeze the exact plan revision, approved TRD, root/source/Template hashes, current helper editions, guard bindings, factual registry and mixed-worktree preservation manifest. Use read-only current-owner inspection for overlapping assignments and name each later action grant separately. Preserve the completed 128 MiB guard repair as a prerequisite and reject incompatible old initializer fixtures.',
 ['Verification/integrated-curator/baseline.json','Verification/integrated-curator/authority-scope.json'],[],
 ['The manifest identifies every intended source, Template and root adoption target, protected file and selected fixture destination before any integration edit.',
  'Current manager, guards and root v9 versus source/Template v11 divergence are observed; implementation, configuration adoption, canonical publication, cleanup and service-start grants are individually recorded or their work is blocked.'],
 ['Inspect current canonical Task assignment and actual native owners through their read-only helpers; do not infer actors from saved ontology or role names.',
  'Hash intended targets and protected identities, licensing, authored ontology/memory, old receipts and unselected project inventories; retain current Git diff only as a preservation baseline.'],
 ['Concurrent unrelated edits invalidate only overlapping planned inputs and require rebinding before writes. No existing dirty work is overwritten.'])
task(2,1,'Specify the full functional ontology contract',[1,2,3,4,9],
 'Define a versioned declarative Curator integration recipe with stable local suffixes, full function descriptions, inputs, outputs, prerequisites, effects and canonical owners. Represent policy inspection, scoped review, owner update/correct, original retry/recovery, Task pause/resume, selected dispatch, session catch-up and bounded log access. Use existing Capability/Skill typing and providesCapability relations; add typed local predicates only where existing vocabulary lacks a precise relation. Bind governing role pairs and skill/action/session sources by exact installed path, locator and digest. Model current-owner resolution as a required owner read, never a persistent assertion of a live actor or Task status.',
 ['ONTOLOGY-depo/curator-integration/v1/contract.json','ONTOLOGY-depo/curator-integration/v1/README.md','ONTOLOGY-depo/curator-integration/v1/competency.json'],[1],
 ['Every supported action has a queryable meaning, exact source, input/output, effect, owner, scope and prerequisite; aliases and domain/range/cardinality rules are explicit.',
  'Declaration, installation, configuration, authorization, compatibility, runtime observation, pending delivery and completed outcome are separate concepts; no runtime or native authority is inferred from ontology availability.',
  'The proposed representation uses project-local records generated from a neutral recipe and preserves the locked sys4ai-core module unchanged.'],
 ['Review the function matrix against installed Curator ACTIONS.md, commands and session contract and each fixed canonical owner route.',
  'Map competency questions to bounded capability, read, neighbors/path and knowledge --intent current queries; include missing/ambiguous/stale-source and unsupported-operation negative cases.'],
 ['A list of names cannot pass the functional contract. Data from source files cannot grant execution authority.'])
task(3,1,'Specify exact integration specialization and adoption transactions',[4,5,6,7,8,9],
 'Define integration edition curator-ontology-v1 and propose governance-starter-v12 for new/first preparation while preserving all v1-v11 bases. Extend the existing selected curator adoption with a hash-bound integrated edition/refresh, never an ordinary-rerun upgrade. Materialize new project-local curator.jsonld, binding and competency files plus exact ontology.yaml file-list and allowlist additions; retain the old graphs and core lock byte-for-byte. Use complete source/target inventory, missing prerequisites, duplicate/collision rules, package ownership checks and original operation recovery. The root uses an explicitly reviewed project-local configuration adoption manifest without generic project.json creation; child routes continue using existing setup receipts/module_adoptions.',
 ['SKILLS-depo/init-new-project/references/curator-integration.md','SKILLS-depo/init-new-project/assets/initialization-receipt.schema.json','ONTOLOGY-depo/curator-integration/v1/contract.json'],[1,2],
 ['The contract distinguishes new creation, first preparation, pristine manual copy, earlier setup without Curator and earlier setup with Curator but missing ontology.',
  'Compatible existing ontology is extended through new configured files and exact config deltas; conflicts preserve whole project-owned data and return a specific blocked capability.',
  'Recovery uses existing setup/module history and exact source/pre/post states; there is no second adoption ledger, relabeled historical edition or implicit publication grant.'],
 ['Review state transitions for preflight, staged configuration/record additions, registration, verification, partial replay and subsequent selected refresh.',
  'Review preserved session-disabled, capture-off, publication-disabled, custom packages, legacy role-layout and independent core-import cases before implementing.'],
 ['Current init_curator.protected_inventory deliberately protects ontology; only exact selected integration targets may become writable. Existing-file equality never grants replacement.'])

task(4,2,'Implement the neutral recipe and deterministic destination materializer',[2,3,4,8],
 'Author complete neutral recipe/competency assets in ONTOLOGY-depo/curator-integration/v1 and a pure bounded materializer owned by the reusable initializer. Instantiate only module project records under the actual destination namespace into ONTOLOGY/modules/project/curator.jsonld, ONTOLOGY/bindings/curator.jsonld and ONTOLOGY/modules/project/curator-competency.json. Source hashes are derived from installed destination governing bytes after specialization. Reject unresolved required sources, duplicate local suffixes, graph collisions, mismatched namespace, invalid role pairs and malformed recipes before any write. Preserve the existing module loader and shared core IDs.',
 ['ONTOLOGY-depo/curator-integration/v1','SKILLS-depo/init-new-project/scripts/init_curator.py','SKILLS-depo/init-new-project/tests/test_curator_integration.py'],[2,3],
 ['The complete neutral recipe contains no actual project-instance fact, owner identity, task snapshot, grants, backlog, learned record or runtime evidence.',
  'Repeated materialization from identical identity/source bytes is deterministic and produces all required typed function/relationship records and exact bindings without changing existing graphs or imports.'],
 ['Run new focused pure materializer tests using a non-root destination namespace and changed source hashes; validate generated records with the existing compact profile in a disposable configured destination.',
  'Exercise missing sources, wrong role pairs, duplicate identifiers, unsafe paths, source drift and incomplete recipe failures with zero target writes.'],
 ['A recipe is a specialization input, not a new supported imported module. Source text is data; materialization must not execute target project Python.'])
task(5,2,'Make static assessment require functional integration',[2,3,4,5,6,7,14],
 'Extend the current initializer static inventory and assess-curator output to require the recipe edition, installed owner interfaces, configured file selections, destination identity, exact source bindings and every functional competency. Report installed, configured, compatible, authorized and runtime_observed separately. Add a bounded read-only clarification to ontology capability output/documentation if needed so source-current declaration does not imply authorization, runtime or completed maintenance; preserve existing query identities and no-write behavior.',
 ['SKILLS-depo/init-new-project/scripts/init_static_health.py','SKILLS-depo/init-new-project/scripts/init_curator.py','SKILLS-depo/init-new-project/assets/static-capability-v1.json','SKILLS-depo/ontology/scripts/ontology_knowledge.py','SKILLS-depo/ontology/references/commands.md','SKILLS-depo/init-new-project/tests/test_static_readiness.py'],[4],
 ['An installed Curator package or name-only capability with missing function, binding, source or owner prerequisite is non-ready with the exact capability diagnostic.',
  'A neutral Template is assessed as reusable completeness with unbound/disabled operational state; an enabled flag or source-current result never reports runtime execution.'],
 ['Run targeted static-readiness tests for complete integration, omitted function, omitted binding, stale source, missing owner interface and preserved incompatible package.',
  'Snapshot files and timestamps around bounded capability and current-source queries; verify no repairs, state writes, target Python execution or service startup.'],
 ['The assessment must not run unknown customized helpers or create runtime authority to satisfy its own check.'])
task(6,2,'Integrate new and first-preparation setup in one operation',[4,5,6,8,9],
 'Wire proposed governance-starter-v12 through template_sources, source_snapshot, asset planning, specialization and verification. After destination governance and identity are final, materialize exact local ontology additions and config selections inside the existing setup transaction before successful verification. Pristine Template copies specialize once; compatible authored ontology keeps its files and import locks while selected integration files are added. Existing opt-outs win. A preserved incompatible package yields exact degraded/non-ready evidence instead of integrated success.',
 ['SKILLS-depo/init-new-project/scripts/init_new_project.py','SKILLS-depo/init-new-project/scripts/init_curator.py','SKILLS-depo/init-new-project/assets/baseline-assets.json','SKILLS-depo/init-new-project/assets/initialization-receipt.schema.json','SKILLS-depo/init-new-project/SKILL.md'],[3,4,5],
 ['Both create and first prepare-existing deliver project wiring and all ontology functionality without a manual ontology step.',
  'Session policy is enabled only by the selected install policy; explicit session-off, capture-off and publication-disabled choices remain unchanged. Static setup records runtime not-exercised.',
  'Every copied, specialized, added, retained and blocked resource has exact receipt provenance and existing historical editions remain accepted.'],
 ['Run focused new/first-preparation tests including empty destination, authored existing project and pristine manual Template copy.',
  'Verify changed destination identity/name/purpose, hash bindings after governance specialization, opt-outs, configured file lists and CLI nonzero behavior for missing functional integration.'],
 ['Whole-package preservation cannot silently omit required integration; customized or unsafe inputs remain preserved and diagnosed.'])
task(7,2,'Add selected integrated adoption and refresh for earlier setups',[4,7,8,9],
 'Extend prepare-existing --adopt-module curator to select the integrated edition and add an explicit refresh selector for a later integration edition without implicit acquisition on ordinary rerun. Include earlier projects with no ontology as a recorded prerequisite and existing Curator without semantic integration. Reuse module_adoptions and archived original receipt hashes. Extend only recognized receipt-owned complete packages and exact selected config/file additions; preserve existing ontology graphs, authority settings and core locks. Reject legacy role layouts pending their existing separately selected transition.',
 ['SKILLS-depo/init-new-project/scripts/init_curator.py','SKILLS-depo/init-new-project/scripts/init_new_project.py','SKILLS-depo/init-new-project/assets/initialization-receipt.schema.json','SKILLS-depo/init-new-project/tests/test_curator_adoption.py','SKILLS-depo/init-new-project/README.md'],[3,4,5,6],
 ['One selected workflow installs both integrations or returns a specific prerequisite/conflict blocker; it cannot silently leave ontology for manual completion.',
  'Original base edition, source/adoption inventories and historical receipt bytes are preserved; the new integration edition, selected targets and current observed state are separate.',
  'Ordinary reruns verify their recorded edition and do not refresh newly available integration; same selected inputs add no duplicate IDs, bindings or registrations.'],
 ['Run targeted adoption cases for supported historical editions, earlier Curator installations, missing ontology, compatible authored ontology and already integrated destinations.',
  'Verify historical receipt content hashes, disabled preferences, unselected registry entries and root-specific customized Task helper preservation.'],
 ['Missing, extra, customized or unowned package files cannot be overwritten as a dependency upgrade. Existing source-equal files are retained without inferring ownership.'])
task(8,2,'Prove exact failure and recovery behavior',[5,6,7,8,9,14],
 'Extend current initializer recovery fixtures for interruption before/after config and ontology publication, registration and verification. Bind recipe version, installed helper/source inventory, identity, protected inventory and exact pre/post file states to the existing pending operation. Recheck protected content at every replay gate and preserve pending evidence on conflicting human edits, changed sources or competing writers.',
 ['SKILLS-depo/init-new-project/tests/test_curator_recovery.py','SKILLS-depo/init-new-project/tests/test_ontology_recovery.py','SKILLS-depo/init-new-project/tests/test_setup_recovery.py','SKILLS-depo/init-new-project/scripts/init_curator.py'],[6,7],
 ['Exact unchanged replay completes or verifies once, including partially published records, and never duplicates capabilities or registration.',
  'Source/recipe/identity changes, concurrent target edits, unknown files and mismatched operation IDs block replay with explicit committed/pending state and preserve all project content.',
  'Session/capture/publication opt-outs, custom ontology/memory and historical Task/receipt/role/license state survive preparation, adoption and reruns.'],
 ['Run the relevant Curator, ontology and setup recovery tests with explicit SYS4AI_CURATOR_TEST_SOURCE and separate disposable SYS4AI_CURATOR_TEST_WORK paths; do not invoke current v11 fixtures through installed v9.',
  'Compare complete before/after file inventories and semantic records across failure injection points, including lock contention and replay after changed configured sources.'],
 ['Do not delete pending receipts or weaken hash, lock, symlink or owner checks to unblock a fixture. Synthetic identities remain fixture evidence.'])

task(9,3,'Distribute the complete reusable edition through the checked Template pipeline',[4,8,14],
 'Update only owning reusable collections, initializer resource pins/contracts, source Template tests and the exact mapping needed for recipe resources. The ordinary ONTOLOGY-depo reference collection distributes the neutral recipe; active project/binding starter graphs remain empty and destination specialization is explicit. Run tools/template_update.py check, review the entire current mapping and source inventory, then apply the authorized exact update to the registered Template only. Retain normal conflict and pending-operation recovery.',
 ['ONTOLOGY-depo/curator-integration/v1','CURATION-depo/contract.json','SKILLS-depo/init-new-project/assets/static-capability-v1.json','AGENTS-depo/project-template-AGENTS.md','SPECS-depo/project-template-SPECS.md','SPECS-depo/template-tests/test_template_contract.py','depot/template-update.json','depot/template-update.md'],[4,5,6,7,8],
 ['The source-to-Template manifest accounts for every semantic recipe, competency, source binding input, owner interface and session asset; no incompatible resource is omitted.',
  'The Template has null identity/unbound publication and disabled session mode with no root facts or runtime state; only the registered Template receives distribution.',
  'Checked source pins and generated role/index assets match their intended complete current packages; no direct edits to generated Template copies occur.'],
 ['Run .venv/bin/python tools/template_update.py check before apply and again afterward; inspect structured receipts and exact final source/destination hashes.',
  'Run the focused source/template contract and mapping tests; check empty graphs, null bindings, false session flag and absent learned/runtime/control history.'],
 ['The watcher may observe intermediate sources; stage a coherent selected edition and honor existing lock/recovery behavior without installing or reconfiguring the watcher.'])
task(10,3,'Verify neutral completeness and destination specialization controls',[2,3,4,8,14],
 'Use the reviewed Template as read-only source for an isolated neutral assessment and deterministic specialization rehearsal. Validate every recipe function and its source/owner prerequisites without claiming an unbound Template is a running project. Exercise missing recipe resources, incompatible helper pins, polluted instance facts, enabled session state and altered locked core imports.',
 ['SPECS-depo/template-tests/test_template_contract.py','SKILLS-depo/init-new-project/tests/test_curator_integration.py','Verification/integrated-curator/template-contract.json'],[9],
 ['Neutral completeness passes with empty active graphs because complete validated specialization inputs are present; omitted semantic resources fail.',
  'The exact source/Template inventory contains no active root actor, source digest bound to a root-only file, maintenance delivery, Task status, learned record or runtime claim.',
  'Materialization into a non-root identity demonstrates all functional and current-source competencies while retaining core 1.0.0.'],
 ['Run the Template contract using its documented interpreter and source tests against the exact mapped revision.',
  'Inspect generated fixture records and source bindings, query all function competencies and compare the original Template and unrelated registry hashes afterward.'],
 ['A polluted Template cannot be made neutral merely by disabling one flag. Fixtures establish static/functional behavior only.'])

task(11,4,'Apply the exact active-root adoption and configuration selection',[1,2,3,8,9,13],
 'Prepare and review a root-specific adoption manifest for only required new helper/contract resources and ontology.yaml source/file-list additions. Preserve root custom Task intake, identity, publication settings, original core lock, authored graphs and active guard choices. Apply through the explicitly selected existing adoption/configuration boundary with current Director authority; this is not generic project initialization and must not create project.json or replace the installed v9 initializer merely to match the Template. If affected guarded helper or governing hashes change, execute only the separately selected exact guard binding repair/recertification with actual native evidence, retaining its existing verification gates.',
 ['ontology.yaml','.agents/skills/ontology','reference-assets/ONTOLOGY-depo/curator-integration/v1','Verification/integrated-curator/root-adoption-manifest.json','Verification/integrated-curator/root-adoption-receipt.json'],[1,9,10],
 ['Exact adopted files and config additions are reviewable and verified; root-specific governance, custom Task behavior, identity, publication state and core import lock remain intact.',
  'Curator governing sources and the dedicated future canonical file paths are selected before publication. Enabled guard bindings are current for changed dispatch code, or work remains blocked.',
  'The root adoption does not imply product-project adoption, generic initializer conversion or provisioning authority.'],
 ['Compare every manifested pre/post byte and every protected root target; use installed read-only configuration and owner/guard checks after adoption.',
  'If repair is required, rerun the exact installed-edition dispatch/recovery checks and inspect actual receipt/bindings; preserve existing 128 MiB capacity and all other guard limits.'],
 ['No existing helper may be replaced wholesale if it contains root-specific changes. Missing action authority blocks the exact adoption or repair, not plan creation.'])
task(12,4,'Publish the root functional ontology through its current owner',[1,2,3,8,9],
 'Materialize the root-specific Curator records and exact installed source/paired-role bindings from the accepted recipe. Prepare an ontology proposal selecting only the new configured curator graph, binding and competency files with expected hashes. Obtain current ontology-specific Director or confirmed-manager authority, run read-only preview, publish through the existing guarded owner and recover only the original operation if partial. Do not persist live native identities, current Task status or maintenance outcomes as reusable capability declarations.',
 ['ONTOLOGY/modules/project/curator.jsonld','ONTOLOGY/bindings/curator.jsonld','ONTOLOGY/modules/project/curator-competency.json','control_records/ontology','Verification/integrated-curator/root-query-evidence.json'],[11],
 ['Bounded root capability/read/relationship/current-source queries answer every function competency with actual sys4ai-depot identity, installed governing sources and current-versus-recorded digest context.',
  'Owner routes are discoverable yet every actual action still requires its current canonical owner/authority check; publication has an attributable exact owner receipt.',
  'Existing project records and locked core imports retain their bytes and meanings; missing, ambiguous and stale sources retain their diagnostics.'],
 ['Run exact preview and inspect the complete proposed graph before publication; reread final canonical files and immutable receipt after the current owner returns.',
  'Run capability curator, per-function capability/read queries, typed neighbors/path and knowledge --intent current using bounded limits; prove unsupported actions and stale-source negative cases in fixtures.'],
 ['Configuration selection belongs to prior adoption; publish may not expand allowlists, imports or authority. A valid graph or Task title supplies no grant.'])
task(13,4,'Refresh selected ontology products without changing memory meaning',[3,8,13],
 'After root sources settle, assess current source freshness, compiled/wiki/link products and enabled backend certification. Use the existing explicit owners to rebuild only products made stale by the integration, in dependency order: current canonical sources and approved memory disposition, required backend recertification, existing memory projection/index maintenance when actually stale, then ontology compile/wiki/semantic/link products. Retain precise pending reasons for any unavailable authority or dependency.',
 ['ONTOLOGY/WIKI','.sys4ai/ontology/compiled','.sys4ai/ontology/links','.sys4ai/ontology/manifests','Verification/integrated-curator/product-health.json'],[12],
 ['Required generated indexes/wiki and relevant memory links match the selected current canonical Curator records and current source contexts.',
  'Healthy memory records/settings and independent backend choices retain meaning and provenance; retrieval performs no repair.',
  'Any recertification or selected build has its own observed result and unperformed work remains pending.'],
 ['Run explicit compile, build-wiki and only necessary link-memory/semantic builds with current authority; validate wiki links and relevant generated manifests.',
  'Run fresh ontology health --scope selected --level static and applicable operational advanced-health; compare selected inputs before and after and label guarded dispatch separately.'],
 ['Changing later documentation invalidates source-linked products. Do not alter unrelated profiles or memory facts just to remove health warnings.'])

task(14,5,'Obtain current-owner disposition of root session obligations',[1,9,10,14],
 'Reopen bounded current delivery and ownership evidence for every still-relevant obligation cited by the September 12 report. On an enabled representative start/return, collect changed-input catch-up and inspect actual usage and capacity. Admit at most the configured operation budget, route eligible work to its current existing owner and retain exact observation, admission, dispatch and completed outcome separately. Reuse actual owning Tasks where required; do not instantiate a fake Task or manager. Consume a delivery only after its canonical owner completes and supplies an attributable receipt. Retain supersession/completion history or exact blocker, owner and next eligible action for each item.',
 ['control_records/curator','.sys4ai/curator','Verification/integrated-curator/owner-dispositions.json','Verification/integrated-curator/live-session.json'],[12,13],
 ['At least one representative bounded eligible maintenance operation reaches the applicable current owner with actual native attribution and an observed result; no static flag is substituted for root integration.',
  'Each still-relevant reported obligation is completed with receipt or retained with explicit blocker/owner/next action; completed and superseded history remain attributable.',
  'Disabled-session control performs no maintenance; unavailable owner or exhausted budget retains pending work without consumption, scheduler, second writer or invented authority.'],
 ['Use current read-only policy/delivery inspection and session-start collection; inspect exact observation snapshot and page bounds rather than interpreting metadata totals as failure counts.',
  'Perform the selected actual-owner operation with current authority and source checks; reread canonical outcome/receipt and delivery state, then run focused session retention/consumption tests.'],
 ['Reported counts and cancelled historical actors are not current ownership evidence. Work exceeding session bounds is retained for explicitly selected execution.'])
task(15,5,'Reconcile the historical staged Task response through the Task owner',[8,11,14],
 'Use read-only Task and native ownership inspection to locate the exact current staged response originally reported under TASK-20260910-7F1A11AE, its transaction evidence, current canonical revision/status and known write-owning assignments. Reconcile actual owners before deciding recoverable, already represented or blocked. Perform only a supported exact recovery/disposition when its action-specific authority is present; otherwise preserve the artifact and state the smallest required owner action. Never delete based on age/cancellation or silently reopen the Task.',
 ['Verification/integrated-curator/staged-task-disposition.json','Task owner output for exact TASK-20260910-7F1A11AE'],[1],
 ['Evidence identifies the actual current artifact path/hash and transaction state or proves the dated artifact is already represented, with current owner evidence.',
  'Any authorized change uses the Task helper, preserves response history and unrelated work, and is followed by canonical reread and validation; insufficient evidence leaves a precise blocker.'],
 ['Resolve the historical Task by exact ID through read-only show/validate and inspect only returned staged/transaction paths; the listed folder is a planning locator until the helper verifies its actual name.',
  'After a supported disposition, reread canonical Task and response inventories and run validate; record unchanged preservation if no disposition is authorized.'],
 ['Cancellation, age and roster absence alone cannot prove the writer is stopped or the staged response safely removable.'])
task(16,5,'Observe the selected on-demand workbench read flow',[8,12,13,14],
 'After separate service-start authorization and current selected-profile checks, start or select the root loopback ontology workbench in browsing-only mode using a new private one-use session file. Open its actual local browser UI, confirm intended root identity and exercise search/navigation from Curator capability to a representative function and current source. Record redacted observations without URLs containing secrets, then leave the service only in its authorized lifecycle state and verify private file cleanup when stopping.',
 ['Verification/integrated-curator/workbench-observation.json','.sys4ai/ontology/workbench'],[12,13],
 ['Actual local browser navigation against the intended root is observed and attributed; endpoint-only probing is insufficient.',
  'The report distinguishes not running, not assessed, observed operational and failed behavior; no always-on service or guarded-write success is inferred.',
  'Private tokens stay out of screenshots, logs, reports, fixtures and Git, and final service/session-file disposition is verified.'],
 ['Run advanced-health with the selected token-free loopback endpoint and compare project/source/helper identity before using the private browsing session.',
  'Use actual browser UI to inspect the representative Curator function and source, then stop the foreground service if selected and verify only its unchanged exclusively created private session file is cleaned.'],
 ['Absent endpoint is not proof of failure. Missing service authority or browser capability is an explicit unexercised requirement, not a simulated pass.'])

task(17,6,'Exercise complete new-project initialization from the reviewed Template',[2,3,4,5,8,9,14],
 'Select an isolated disposable depot copy and a new child identity; invoke the complete supported create CLI from its reviewed current reusable initializer and Template. Reopen setup receipt, identity, Curator/session configuration and ontology files, then run every functional/current-source competency. Observe static setup success independently of an actual new-project session. Recheck original source, registry and unselected project hashes after the disposable exercise.',
 ['Verification/integrated-curator/new-project-route.json','SKILLS-depo/init-new-project/tests/test_end_to_end.py'],[9,10,8],
 ['The full CLI workflow supplies Curator wiring, exact local source bindings, all function relationships and selected session policy without manual ontology work.',
  'No root identifiers/actors, live memory, backlog or runtime data are copied; neutral backend/service and explicit opt-out choices are preserved.',
  'Receipt evidence reports installed/configured/compatible/static success and separately not-exercised or actually observed runtime state.'],
 ['Run the complete create CLI in the selected disposable source/work layout; reopen receipt and query the destination using the copied helper with its exact project root.',
  'Inspect all required files/functions and perform file-install-only/missing-ontology rejection control through the same static assessment.'],
 ['Disposable full CLI evidence is end-to-end setup evidence for that fixture, not adoption of a real user product or proof of native session execution.'])
task(18,6,'Exercise existing-project and manual-copy preparation',[2,3,4,6,8,9,14],
 'Run full prepare-existing workflows for a representative authored project and a pristine unspecialized Template copy in isolated destinations. Seed authored ontology/memory, Task history, custom roles/licensing and explicit disabled preferences where applicable; record exact before inventories. Confirm compatible project knowledge stays usable and incompatible preserved content yields precise capability diagnostics without false integrated completion.',
 ['Verification/integrated-curator/first-preparation-routes.json','SKILLS-depo/init-new-project/tests/test_curator_setup.py','SKILLS-depo/init-new-project/tests/test_ontology_setup.py'],[9,10,8],
 ['Both representative first preparations yield destination-specific full functionality without a later manual integration step.',
  'Compatible authored data and custom identity/README/roles/licensing survive; session-disabled, capture-off and publication-disabled values remain effective.',
  'Incompatible custom packages/graphs are preserved and the exact blocked capability is reported as non-ready.'],
 ['Run prepare-existing with supplied destination identity, then compare complete before/after manifests and query both destinations for every approved function and typed relationship.',
  'Run a preserved incompatible control and a same-request rerun; verify no hidden overwrite, duplicate binding or registration and no unknown project Python execution.'],
 ['A completed base receipt with degraded capability is not integrated success. Pristine equality permits only the specifically contracted specialization.'])
task(19,6,'Exercise selected prior-project adoption and historical reruns',[2,3,4,7,8,9,14],
 'Run the selected integrated curator adoption/refresh workflow on representative prior initialized destinations with and without Curator semantic integration, using retained edition fixtures. Include supported old base editions, absent ontology prerequisite, compatible authored data, existing disabled settings and legacy layout refusal. Compare original receipt bytes and history, then perform ordinary and selected reruns, a changed-source operation and interrupted exact replay controls.',
 ['Verification/integrated-curator/prior-adoption-routes.json','SKILLS-depo/init-new-project/tests/test_curator_adoption.py','SKILLS-depo/init-new-project/tests/test_curator_recovery.py'],[9,10,8],
 ['Every supported selected adoption delivers both integrations in one workflow; missing prerequisites or conflicts fail explicitly without manual omissions.',
  'Original editions, source inventories and receipt history remain unchanged and current integration edition/state are recorded separately.',
  'Ordinary reruns do not acquire a new edition; selected unchanged reruns verify idempotently; explicit off settings and unselected projects remain untouched.'],
 ['Run full CLI operations and all function/relationship/current-source queries for representative completed prior setups; distinguish reconstructed historical fixtures from original historical binaries.',
  'Compare receipt/history/config/core/authored-file hashes across ordinary rerun, explicit refresh and recovery; verify duplicate-free graph IDs and registry membership.'],
 ['Legacy layouts require the existing selected transition and cannot be silently migrated or relabeled by a fixture.'])

task(20,7,'Verify final root health and independent memory preservation',[1,3,8,9,10,11,12,13,14],
 'After all selected source/configuration changes settle, rerun bounded actual memory retrieval and applicable fresh memory/ontology canonical, source, projection/link and selected backend health. Recheck root process queries, real owner receipts, staged Task disposition and token-free workbench state. Compare final exact inventories against the initial preservation manifest; recertify or rebuild only an authorized stale dependency and repeat affected checks when source drift occurs.',
 ['Verification/integrated-curator/final-health.json','Verification/integrated-curator/preservation.json','Verification/integrated-curator/final-source-manifest.json'],[13,14,15,16,17,18,19],
 ['Actual bounded memory retrieval and fresh selected ontology checks demonstrate no regression while authored facts/records, capture settings, core locks and independent backend/grant choices retain meaning and provenance.',
  'All final claims bind current root/source/Template/destination hashes; no last-minute guidance edit leaves source freshness or generated products silently stale.',
  'Every protected path has an affirmative before/after preservation finding or an exact authorized change; unselected projects and dated health report remain preserved.'],
 ['Use the installed memory health and bounded search interfaces and ontology health/advanced-health; retain exact current exit/result state and probe scope.',
  'Reopen canonical artifacts and actual owner receipts and compare the final source/destination inventory against TASK-001; inspect all residual diagnostics rather than a top-level ready flag.'],
 ['The active planning Task and new work legitimately alter runtime inventory; classify authorized changes instead of demanding stale global byte equality.'])
task(21,7,'Publish the requirement-by-requirement integration evidence report',list(range(1,15)),
 'Produce one final evidence report that maps all 14 requirement outcomes and 34 acceptance clauses to exact current source/destination artifacts, owner/setup/publication receipts and checks. Cover root, reusable sources, neutral Template and each new/first/manual/prior route. Explicitly label contract/static checks, deterministic fixtures, actual owner execution, browser navigation and complete setup workflows. Preserve blockers and unexercised behavior and record final project inspection after evidence through the plan helper before any completion transition.',
 ['Verification/integrated-curator/REPORT.md','Verification/integrated-curator/coverage.json','Implementation_Plans'],[20],
 ['Every requirement and clause has current evidence or an explicit unsatisfied/blocker disposition; reverse coverage accounts for every changed artifact and implemented task.',
  'No fixture, configured flag, file installation, declared capability or dated observation is represented as live behavior or associated requirement completion.',
  'The report identifies the highest verification level for each route and the exact remaining authority/capability limits; final canonical plan/Task completion requires their respective truthful evidence gates.'],
 ['Compare the report and bidirectional coverage directly with the unchanged approved TRD; reopen every material referenced receipt and final canonical artifact.',
  'While the exact implementation plan is in_progress, append criterion/verification-step evidence and a final later project inspection through plan_state.py, then show/validate and inspect deterministic projections/index before the separate completion gate.'],
 ['A legitimate blocker for health maintenance or browser authority remains incomplete for the affected acceptance clause; it cannot be hidden by aggregate setup success.'])

phases=[]
phase_defs=[
 (1,'Bind scope and integration design','Establish exact evidence, owners and a complete semantic/setup contract.',[],['Implementation of this exact plan is separately authorized; current action scopes are observed.']),
 (2,'Implement reusable semantics and exact setup behavior','Deliver neutral recipe, specialization, functional assessment and historical-safe transactions.',[1],['The exact semantic and transaction contracts from phase 1 are accepted for implementation.']),
 (3,'Distribute and verify neutral Template capability','Publish complete reusable assets into only the registered Template and prove neutral completeness.',[2],['Focused source, specialization and recovery checks passed for the selected source edition.']),
 (4,'Adopt and publish integrated root functionality','Bind the active root and publish functional ontology through its current owners.',[3],['Root-specific adoption and ontology publication authority are current; protected root customization manifest is reviewed.']),
 (5,'Resolve root owner and browser evidence gaps','Obtain actual bounded owner outcomes and selected browser observations with honest blockers.',[4],['The root ontology/current-source integration is verified; cleanup and workbench startup actions have their separate selected scopes.']),
 (6,'Validate complete supported setup routes','Exercise new, first-prepared, manual-copy and prior initialized routes with preserved histories.',[3],['An isolated disposable depot/work area and exact reviewed Template edition are selected; no real product adoption is inferred.']),
 (7,'Verify final health, preservation and coverage','Prove current integrated outcomes and report every evidence limit.',[5,6],['Root owner/browser results and representative setup routes have reviewable current evidence or explicit blockers.'])
]
for n,title,obj,deps,entry in phase_defs:
    members=[t for t in tasks if t['phase_id']==f'PHASE-{n:03}']
    phases.append(dict(phase_id=f'PHASE-{n:03}',title=title,objective=obj,scope=[t['title'] for t in members],
        depends_on_phase_ids=[f'PHASE-{d:03}' for d in deps],entry_conditions=entry,
        exit_criteria=['Every owned task meets its current criteria with exact evidence, or the phase remains incomplete with its precise blocker.'],
        task_ids=[t['task_id'] for t in members],risks=['Source or owner changes invalidate affected gates; preserve original work and rebind before proceeding.']))

decisions=[]
def decision(text,reqsources=['SRC-001'],status='proposed',basis='Solver proposal constrained by the approved TRD and inspected existing interfaces; requires approval of the exact plan revision before readiness.'):
    decisions.append(dict(decision_id=f'DEC-{len(decisions)+1:03}',statement=text,status=status,source_ids=reqsources,authority_basis=basis,decided_at='2026-09-13T09:02:47-06:00' if status=='approved' else None))
decision('Preserve the approved 14-requirement functional scope across the depot root, neutral Template and all selected setup routes. TRD approval authorizes requirements only.',['SRC-001'],'approved','Approved TRD-20260913-C85981B3 revision 2 records the current user approval and its action boundary.')
decision('Use a versioned neutral declarative recipe, proposed ONTOLOGY-depo/curator-integration/v1, distributed as reference-assets/ONTOLOGY-depo/curator-integration/v1. Materialize destination-local module project records and bindings in separate curator files using existing project_files/binding_files/competency_files support. Keep active neutral starter graphs empty. Do not add a new imported module or redefine sys4ai-core.',['SRC-001','SRC-010','SRC-011','SRC-014','SRC-015','SRC-016','SRC-017'])
decision('Propose integration edition curator-ontology-v1 and governance-starter-v12 for new and first-prepared setups. Extend selected curator adoption with an explicit integrated refresh selection; preserve v1-v11 original editions and ordinary rerun semantics. The actual next version must be confirmed against live source before implementation.',['SRC-001','SRC-018','SRC-019','SRC-020'])
decision('Use existing setup/module_adoptions history for child integration and existing ontology proposal/publish/recover for root canonical content. Root configuration/resource adoption is a separately reviewed project-local manifest and cannot be routed through generic child initialization or create a project.json. If a supported exact adoption route cannot honor root preservation, stop that action with an explicit blocker rather than invent a writer or ledger.',['SRC-002','SRC-004','SRC-014','SRC-018','SRC-027'])
decision('Treat the selected function owner as a current invocation-time resolution through the existing owner API. Ontology stores governing role/skill bindings and prerequisites, not current native actors, authority grants, dynamic Task statuses or completed delivery claims.',['SRC-006','SRC-007','SRC-009','SRC-013','SRC-021'])
decision('Retain existing capability query fields for compatibility while making declaration/source freshness distinct from installation, authorization and runtime in bounded explanatory metadata and assessment. No query executes an owner or repairs stale sources.',['SRC-008','SRC-009','SRC-013'])
decision('Run native owner and browser validation only under their actual selected action scopes. Disposable setup fixtures are sufficient to exercise implementation routes but must remain labeled fixtures; real product adoption, new runtime installation, service provisioning and Git publication remain separate requests.',['SRC-001','SRC-007','SRC-009','SRC-018'])

guidance=[]
for path,summary in [
 ('AGENTS.md','Root depot governance, sole canonical owners, source-to-Template ownership and selected adoption boundaries.'),
 ('SOUL.md','Source-first engineering, exact scope and evidence discipline.'),
 ('ROLE.md','Project Director ownership and separate Task/native/state authority.'),
 ('SPECS.md','Root interpreter, setup/ontology/memory architecture and source-specific editions.'),
 ('.agents/skills/to-implementation-plan/SKILL.md','Explicit planning-only operation; exact-revision approval is required before ready; helper owns canonical records.')]:
    guidance.append(dict(path=path,observed_at=NOW,digest='sha256:'+digest(path),summary=summary))

plan=dict(title='Integrated Project Curator, ontology and project initialization',
    slug='integrated-project-curator-ontology-and-project-initialization',
    status_reason='Draft derived from approved TRD revision 2; engineering decisions are proposed and exact plan approval is pending. No planned implementation has been performed.',
    project=dict(root_hint=str(ROOT),inspected_at=NOW,guidance=guidance,
        baseline_facts=[
          dict(fact='The current root is sys4ai-depot, not a generic product; registry lists the depot and its neutral Template only.',evidence_locator='depot/projects.json',observed_at=NOW),
          dict(fact='Current ontology imports only locked sys4ai-core 1.0.0. Existing configuration supports multiple project-local and binding files without adding a module loader.',evidence_locator='SKILLS-depo/ontology/scripts/ontology_modules.py and ontology_core.py',observed_at=NOW),
          dict(fact='Neutral starter project and binding graphs are empty; current Curator adoption preserves ontology.yaml and ONTOLOGY rather than creating Curator semantics.',evidence_locator='ONTOLOGY-depo/starter/ONTOLOGY and SKILLS-depo/init-new-project/scripts/init_curator.py',observed_at=NOW),
          dict(fact='Root session maintenance is enabled, but unattended scheduler/services/autonomous writes remain disabled.',evidence_locator='curator-session.yaml and curator.yaml',observed_at=NOW),
          dict(fact='The separately authorized guard capacity repair is recorded as complete; installed initializer remains v9 and reusable/Template setup is v11.',evidence_locator='Verification/guard-capacity-20260913/REPORT.md',observed_at=NOW),
          dict(fact='The repository has existing tracked changes across governance, source, Template and ontology; they are pre-existing work to preserve rather than a clean baseline.',evidence_locator='Read-only git status --short --untracked-files=no during this planning inspection',observed_at=NOW)
        ],constraints=[
          'Use the selected root .venv Python 3.12; plan helpers need no new dependencies.',
          'Author reusable changes only in their owning source collections; use checked Template distribution and separate exact root/destination adoption.',
          'Preserve core schema/context/import locks, exact source/owner checks, current Task writer and all action-specific authority gates.',
          'The active root initializer v9 is not automatically upgraded to source/Template v11; use the executing helper own current compatible fixture.',
          'Source-current ontology declaration, installation, configuration, compatibility, authorization and runtime are distinct evidence states.',
          'No current integration execution authority is conferred by this planning task or the approved TRD.'
        ],preserved_paths=[
          TRD,'Verification/root-health-followup-trd-20260912-v1/REPORT.md','MEMORY','memory.yaml','ONTOLOGY/modules/sys4ai-core/1.0.0',
          'ONTOLOGY/modules/project/project.jsonld','ONTOLOGY/bindings/artifacts.json','ONTOLOGY/bindings/roles.json','ONTOLOGY/bindings/skills.json','ONTOLOGY/bindings/projects.json',
          'LICENSE','LICENSE-CODE','LICENSE-DOCS','.agents/skills/agent-task/scripts/task_state.py','Projects outside explicitly selected disposable fixtures','Historical control_records/project-setup-history receipts'
        ],evidence_gaps=[]),
    objective=dict(summary='Deliver one complete functional Curator process integrated with project ontology and every supported selected initialization route, then resolve the root health follow-up with current owner evidence.',
        user_value='The user can discover what Curator does and which current owner governs it, and obtain the same usable integration from setup without hidden manual ontology work.',
        success_outcomes=[r['outcome'] for r in requirements]),
    scope=dict(in_scope=[
        'Functional process/owner/trigger/source semantics and current-root project integration.',
        'Neutral reusable recipe, checked Template completeness and exact destination specialization.',
        'New creation, first existing preparation, pristine Template-copy specialization and explicit integrated adoption/refresh of earlier initialized projects.',
        'Preservation, historical editions, exact partial recovery and current receipt/static assessment.',
        'Current-owner disposition of dated pending deliveries and historical staged Task evidence; separately selected on-demand browser observation; fresh memory/ontology health.',
        'Requirement-level current evidence and explicit non-complete limits.'
    ],out_of_scope=[
        'Performing any planned implementation, source/Template update, root/destination adoption, canonical ontology publication, staged Task cleanup or service startup during creation of this draft.',
        'Bulk registered-project propagation, root generic project initialization, restoration of the rejected TRD, replacement of historical setup editions or receipts.',
        'New background AI, unattended scheduling, service or hook installation, dependency/model/runtime provisioning, external communications, Git actions, publication or deployment.',
        'Changing healthy unrelated backends, locked core imports, project memory schemas/data or publication grants to produce a healthy aggregate.'
    ],execution_authority='Creating, approving or tracking this plan does not authorize implementation, installation, deletion, configuration adoption, ontology publication, Task recovery, service startup, real product adoption, Git publication or any other separately governed action. A later exact implementation request and current action-specific scopes control each planned task.'),
    sources=sources,requirements=requirements,decisions=decisions,open_questions=[],assumptions=[],phases=phases,tasks=tasks,
    coverage=dict(source_to_requirement=[dict(source_id=s['source_id'],requirement_ids=source_requirements[s['source_id']],disposition=None) for s in sources],
        requirement_to_task=[dict(requirement_id=r['requirement_id'],task_ids=[t['task_id'] for t in tasks if r['requirement_id'] in t['requirement_ids']],disposition=None) for r in requirements]))

dump(OUT/'create-input.json',plan)
dump(OUT/'source-manifest.json',dict(observed_at=NOW,method='Direct UTF-8 source inspection and SHA256 with no symlink in source path components',
    sources=[dict(path=s['locator'],sha256=s['digest'].removeprefix('sha256:')) for s in sources],
    frozen_baseline='8a21cbed242a225b48a72457b6159e48aca8153798d6d48e3bb2123b32d9887e',
    memory='Only supplied empty planning_memory_v1.json; no live memory retrieval or sibling candidate reads.'))
dump(OUT/'coverage.json',dict(trd=TRD,trd_sha256=digest(TRD),requirement_count=len(requirements),acceptance_count=34,
    requirements=[dict(requirement_id=r['requirement_id'],outcome_preserved_verbatim=True,acceptance_criteria_preserved_verbatim=True,
        dependencies=r['dependencies'],clauses=[dict(clause=f"{r['requirement_id']}-AC-{i+1:02}",text=a,task_ids=[t['task_id'] for t in tasks if r['requirement_id'] in t['requirement_ids']]) for i,a in enumerate(r['acceptance_criteria'])]) for r in requirements]))
print(json.dumps(dict(candidate=str(OUT/'create-input.json'),requirements=len(requirements),acceptance_clauses=34,phases=len(phases),tasks=len(tasks))))
