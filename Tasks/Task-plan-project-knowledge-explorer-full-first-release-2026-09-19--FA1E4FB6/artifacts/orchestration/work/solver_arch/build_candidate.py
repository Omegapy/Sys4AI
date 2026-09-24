from pathlib import Path
import datetime as dt
import hashlib
import json
import re

ROOT = Path('/Volumes/P-SSD/AngryOwl/Sys4AI')
OUT = Path(__file__).parent
NOW = dt.datetime.now().astimezone().isoformat()
TRD = 'TRDs/trd_project-knowledge-explorer-full-first-release_2026-09-19.md'
raw = (ROOT / TRD).read_text()
assert hashlib.sha256((ROOT / TRD).read_bytes()).hexdigest() == 'bc074393b6eb7210154d93ef904b0959db86e0d845f449be56e071b8548c8d4d'

requirements = []
for rid, title, body in re.findall(r'^### (REQ-\d{3}) - ([^\n]+)\n(.*?)(?=^### REQ-|^## Decisions)', raw, re.M | re.S):
    outcome = re.search(r'^- Requirement: (.+)$', body, re.M).group(1)
    source = re.search(r'^- Source: (.+)$', body, re.M).group(1)
    acceptance = re.findall(r'^- Acceptance: (.+)$', body, re.M)
    dependencies = re.findall(r'REQ-\d{3}', re.search(r'^- Depends on: (.+)$', body, re.M).group(1))
    negative = [a for a in acceptance if re.search(r'\b(no |never |not |without |does not|neither |cannot |remain[s]? |preserv)', a, re.I)]
    requirements.append(dict(requirement_id=rid, title=title, outcome=outcome,
        intent='Preserve the full first-release outcome approved in TRD-20260919-B6D51106 revision 2. Original source linkage: ' + source,
        source_ids=['SRC-001'], acceptance_criteria=acceptance, dependencies=dependencies,
        negative_requirements=negative, status='active', disposition=None, evidence=[]))
assert len(requirements) == 49

sources = [dict(source_id='SRC-001', kind='trd', locator=TRD,
    title='Project Knowledge Explorer - full first release, approved TRD revision 2',
    accessed_at=NOW, digest='sha256:' + hashlib.sha256((ROOT / TRD).read_bytes()).hexdigest(),
    facts_used=['TRD-20260919-B6D51106 revision 2 has lifecycle trd_done; all 49 requirements and their acceptance statements and dependencies are retained verbatim.',
                'AT-01 through AT-36, full first release, out-of-scope boundaries, D01 through D08, qualified display/performance targets and separate execution/adoption authority govern this draft.',
                'D02 and D03 permit bounded proposed library, module, service, cursor, coordination, configuration and compatibility choices in the implementation plan.'],
    access_limitations=[], provenance_mode='agent_inspected', inspection_method='direct_text', external_id='TRD-20260919-B6D51106'),
    dict(source_id='SRC-002', kind='prompt', locator='Current explicit /goal, $task new, $to-implementation-plan request',
    title='Create the managed full-release implementation plan', accessed_at=NOW, digest=None,
    facts_used=['The user requests a new Task and a managed implementation plan from the named approved TRD.',
                'The current operation is planning. Product implementation, package installation, adoption, publication and deployment require their own authority.'],
    access_limitations=[], provenance_mode='user_supplied', inspection_method=None, external_id=None)]
source_links = {'SRC-001':[r['requirement_id'] for r in requirements], 'SRC-002':['REQ-042','REQ-048']}

def source(path, title, facts, reqs):
    p = ROOT / path
    for parent in [p, *p.parents]:
        assert not parent.is_symlink(), str(parent)
    sid = f'SRC-{len(sources)+1:03d}'
    sources.append(dict(source_id=sid, kind='file', locator=path, title=title, accessed_at=NOW,
        digest='sha256:' + hashlib.sha256(p.read_bytes()).hexdigest(), facts_used=facts, access_limitations=[],
        provenance_mode='agent_inspected', inspection_method='direct_text', external_id=None))
    source_links[sid] = [f'REQ-{n:03d}' for n in reqs]
    return sid

source('SKILLS-depo/ontology/scripts/ontology_core.py','Canonical loader, identity, snapshot and source confinement',[
    'Project carries records, by_id, relations, canonical locations, selected sources and a snapshot including input/helper digests. load_project validates locked local imports and selected canonical files.',
    'The compact profile has no generic process step/order field. Source locators support section:, line:/lines: and json:. source_status reports current/stale/unavailable; assert_current requires all evidence current and is intended for builds/publication.',
    'load_project is read-only but does not itself establish atomic multi-file publication materialization.'],[2,10,11,21,22,26,32,42])
source('SKILLS-depo/ontology/scripts/ontology_retrieval.py','Existing deterministic ranking and payload limits',[
    'match/ranked order exact stable ID, preferred label, alias and lexical matches deterministically; stable IDs break ties.',
    'search defaults semantic=True; explain expands sources, bindings and all related relations before envelope truncation, so compact reader summaries require a thin adapter before pagination, not slicing existing rich results.',
    'limits preserves maximum 100 results, 8 hops and 32000 bytes under stricter project limits.'],[5,6,7,18,23,24,33])
source('SKILLS-depo/ontology/scripts/ontology_graph.py','Existing relation identity, direction and traversal bounds',[
    'neighbors preserves relation IDs, direction and a visited-node ceiling of min(100, configured max_limit). Its available_results reports discovered results and is not a whole-graph total.',
    'Canonical subject/predicate/object are distinct from traversal direction. A one-hop paged reader projection must preserve that distinction and the existing CLI contract.'],[9,14,16,18,19,23,24,33])
source('SKILLS-depo/ontology/scripts/ontology_workbench.py','Existing human service security and authoring coupling',[
    'Workbench includes trusted authority, source selection, proposal/authoring imports, a workbench-profile prerequisite, session/bootstrap protections and explicit static asset routes.',
    'It binds 127.0.0.1; checks exact Host, same Origin, JSON and CSRF; consumes bootstrap once; creates HttpOnly SameSite=Strict port-specific cookies; suppresses access logs.',
    'dispatch exposes draft, validate, decide, publish, recover, advanced, generate and import routes, while state performs readiness/proposal inventory. A dedicated reader must not inherit it.',
    'Source reads require current evidence and return a whole bounded text body; the reader needs registered exact-reference selection plus honest changed-source viewing.',
    'Fallback exception handling returns str(exc); the reader requires fixed safe diagnostic mappings.'],[11,20,28,29,30,31,32,33,39,40])
source('SKILLS-depo/ontology/scripts/ontology_publication.py','Existing publication and recovery coordination',[
    'publish/recover use control_records/ontology/publication.lock, immutable intents, receipts and recovery records. A transaction may leave partial canonical files after an injected or actual failure.',
    'The reader must coordinate with these existing states without creating another writer lock protocol or invoking compile/publication/recovery.'],[21,22,26,40,41])
source('SKILLS-depo/ontology/scripts/ontology_advanced_cli.py','Current old launch and agent commands',[
    'The workbench command accepts --authority-file, --port and required --session-file, launches Workbench and writes one private bootstrap session file.',
    'Agent proposal save/validate/decide/publish, generation, guard, standards and semantic commands are independent dispatch operations and must survive cutover.'],[28,30,31,39,40])
source('SKILLS-depo/init-new-project/scripts/init_ontology_advanced.py','Initializer resource and historical edition coupling',[
    'governance-starter-v9 advanced resource validation lists Workbench helpers and all old workbench asset filenames. It also requires five explicit advanced profile states.',
    'New explorer delivery therefore needs an explicit current capability inventory/compatibility path; indiscriminate asset deletion or historical edition rewriting would break setup.'],[37,38,39,40,41])
source('tools/template_update.py','Template package discovery and exclusions',[
    'Template discovery excludes dist, build, node_modules, runtime and cache directories. Production artifacts cannot be assumed to ship from a normal Vite dist directory.',
    'Update/recovery uses the existing ownership/conflict and optional ontology guard integration; output is confined to the registered Template.'],[28,37,38,40])
source('depot/template-update.json','Registered Template mappings',[
    'The registered Template is Projects/Sys4AI-Template-Project. ONTOLOGY-depo neutral starter configuration uses explicit source-to-destination overrides.',
    'Reusable skill source trees and neutral starter files are distinct from the installed active root and product project copies.'],[37,38,40])
source('ONTOLOGY-depo/schema/record-v1.json','Canonical ontology shape inventory',[
    'Kinds are concept, instance, predicate, relation and binding; lifecycle is draft, approved or deprecated; fact kinds are asserted, derived, inferred and external.',
    'No process sequence property exists in the compact record inventory; source-backed process reading must not extend ontology meaning from layout.'],[2,3,9,10,16,42])
source('ontology.yaml','Selected depot ontology configuration',[
    'Root identity is sys4ai-depot with project-relative canonical files, locked sys4ai-core import, explicit source allowlist and project purpose.',
    'Retrieval defaults are 2 hops/20 results and maximums 8 hops/100 results/32000 bytes; these are preserved.'],[2,4,14,18,21,29,38,42])
source('ontology-advanced.yaml','Existing optional profile configuration',[
    'Selected root enables standards, inference, semantic, guards and workbench. Reader operation must not rely on those enabled states or change them through browsing.'],[27,28,29,31,39,40])
source('SKILLS-depo/ontology/references/verification.md','Existing verification routes and evidence distinctions',[
    'check_ontology.py provides core structural and competency checks; unittest suites separate retrieval, graph, publication/recovery, guard, workbench service and advanced backend behavior.',
    'Advanced runtime provisioning and real browser/native observations are separate from standard-library checks. The planning run has not executed the production replacement tests.'],[26,40,42,43,44,48])

guidance = []
for name, summary in [('SOUL.md','Evidence-first, scoped implementation and verification; no invented behavior.'),('ROLE.md','Source/Template/root adoption ownership and Task manager authority.'),('AGENTS.md','Explicit Task orchestration, source-first reusable edits, preservation and exact adoption.'),('SPECS.md','Root Python 3.12, existing ontology read/guard profiles and initializer distinctions.'),('.agents/skills/to-implementation-plan/SKILL.md','Draft creation does not execute work; exact revision approval is required for readiness.')]:
    guidance.append(dict(path=name, observed_at=NOW, digest='sha256:' + hashlib.sha256((ROOT/name).read_bytes()).hexdigest(), summary=summary))

plan = dict(title='Project Knowledge Explorer - full first-release implementation', slug='project-knowledge-explorer-full-first-release',
    status_reason='Draft for exact canonical revision review; all work is planned and no product implementation evidence is claimed.',
    project=dict(root_hint=str(ROOT), inspected_at=NOW, guidance=guidance,
        baseline_facts=[
            dict(fact='git rev-parse HEAD returned 744c8b06d5fda905201145ed313a2da8de2e601f, equal to the recommendations snapshot. git status --short showed pre-existing tracked index edits and untracked Curator/Task/verification work. This is a mixed worktree.',evidence_locator='git status --short; git rev-parse HEAD',observed_at=NOW),
            dict(fact='Direct standard-library load_project of the current root succeeded: 412 records (40 concepts, 24 predicates, 181 relations, 102 instances, 65 bindings), 79 selected references all current at observation, snapshot 92f101afa25aebd7908344cee561a9ba9984c3921b801b1169ccf7b00023a555.',evidence_locator='SKILLS-depo/ontology/scripts/ontology_core.py::load_project; ontology.yaml',observed_at=NOW),
            dict(fact='The root contains a canonical Curator process Capability identity with registered source references. This is an inventory lead, not proof of ordered process content; no Process class or sequence field is inferred from its label.',evidence_locator='ONTOLOGY/modules/project/curator.jsonld',observed_at=NOW),
            dict(fact='Source and installed ontology packages are separate. The reusable source has additional Curator and later regression tests; a whole-package blind root overwrite cannot be justified by assumed equality.',evidence_locator='rg --files SKILLS-depo/ontology .agents/skills/ontology',observed_at=NOW),
            dict(fact='No explorer frontend, explorer read service, or production bundle appears in the inspected ontology package file inventory. Current human modules are workbench/app.js, editor.js, review.js and advanced.js.',evidence_locator='SKILLS-depo/ontology/workbench; SKILLS-depo/ontology/scripts/ontology_workbench.py',observed_at=NOW),
            dict(fact='tools/template_update.py excludes directories named dist and build, and current initializer v9 explicitly lists the old workbench package files. Both affect future release packaging.',evidence_locator='tools/template_update.py::EXCLUDED; SKILLS-depo/init-new-project/scripts/init_ontology_advanced.py::RESOURCES',observed_at=NOW)
        ],
        constraints=[
            'Use the owning root Python 3.12 .venv for standard-library helpers. Python and a browser are the normal production runtime; Node is build-only when explicitly provisioned.',
            'The new reader is a dedicated read-only dispatcher over canonical semantics; it does not inherit Workbench, parse wiki as authority or create a graph/RDF/browser database.',
            'All 49 TRD requirements, AT-01 through AT-36 and D01 through D08 remain in scope. Qualified map, timing, scale and visual targets retain their stated conditions.',
            'Author reusable assets under SKILLS-depo/ontology and necessary ONTOLOGY-depo/SPECS-depo/initializer sources. Template output follows its owner helper; active-root adoption needs its own exact reviewed source/destination manifest.',
            'Product implementation, dependencies, maintenance and adoption are future separately authorized operations. This planning Task writes only its evidence and one new managed draft plan.',
            'Current source/Template/root copies, historical initializer editions, private runtime, knowledge records and unrelated work retain their existing ownership. A path mentioned as a future target is not an authorization to write it now.',
            'Browser endpoints accept no root, grant, actor, arbitrary path, command or function dispatch. Semantic=False applies only to ordinary explorer search; agent retrieval defaults and hard bounds remain unchanged.'
        ],
        preserved_paths=['TRDs', 'MEMORY', 'memory.yaml', 'ONTOLOGY/modules', 'ONTOLOGY/bindings', 'ONTOLOGY/extensions', 'ONTOLOGY/WIKI', 'ontology.yaml', 'ontology-advanced.yaml', 'control_records/ontology', '.sys4ai/ontology', 'depot/projects.json', 'Verification/ontology-first-release', 'Verification/ontology-second-release', '.git'],
        evidence_gaps=[
            'This planning session performed source/code inspection and one read-only canonical load, not a browser launch, baseline regression run, dependency/license selection or product acceptance run. TASK-001, TASK-003 and qualification tasks collect those future observations.',
            'The complete linked-source inventory for process purpose/roles/order is not yet classified. TASK-001 must distinguish recorded order, explicit linked source order, absence and unexamined content without authoring missing knowledge.',
            'Exact current frontend dependency versions and licenses are deliberately unselected; TASK-003 checks primary upstream sources and records a reviewed lock before any separately authorized installation.'
        ]),
    objective=dict(summary='Deliver the full first release of the local Project Knowledge Explorer as a faithful reader and relationship explorer, then retire the active human authoring frontend after evidence gates pass.',
        user_value='People can find definitions, understand typed relationships and source-supported processes, and inspect evidence through accessible text and a bounded map without learning ontology management.',
        success_outcomes=['Overview, Terms, Processes and Map work from canonical data with equivalent keyboard/list navigation and safe source inspection.',
                          'Snapshot, bounds, sessions, sources, assets and diagnostics preserve meaning, privacy and observable non-mutation.',
                          'The production source package, neutral Template and separately adopted root have direct acceptance evidence; agent/CLI authoring, recovery and historical data remain intact.',
                          'All 49 requirements and all 36 acceptance scenarios have inspectable implementation and evidence links, with limitations honestly classified.']),
    scope=dict(in_scope=['Canonical read adapter, immutable snapshot/cache, deterministic filtered cursor search, exact entries/relationships and bounded sources.',
                        'Dedicated loopback reader service, one-use session bootstrap, explicit launch/health/configuration, production asset packaging and safe dispatcher.',
                        'Four reading destinations, faithful status and relationship details, source-supported processes, state/history/copy/preferences, map and full list equivalence.',
                        'Accessibility, responsive design, offline production CSP, failure recovery, measured limits/performance, representative/pathological workloads and human comprehension validation.',
                        'Current source ownership, neutral Template distribution, separately authorized root adoption, gated workbench retirement, compatibility, regression, provenance-impact inventory and reversible migration.',
                        'Exact changed-file map, requirement/AT evidence matrix, production visuals and final operational handoff.'],
               out_of_scope=['Ontology authoring, draft/review/publish/recovery UI, inference/query consoles, raw SPARQL, AI generation/chat, skill/agent/Task execution, memory browser, federation and hidden Advanced modes.',
                             'Automatic process ordering, graph-path semantics, extra process diagram library, optional relationship-path search, second graph database/RDF store, GraphQL, production Node server, browser database synchronization.',
                             'Logseq fork or copied graph implementation, remote runtime assets, CDN/font/image downloads, analytics/cloud logging, broad settings workbench and implicit provisioning.',
                             'Canonical content additions or source-hash/certification repair inside browsing; bulk product updates; alteration of historical evidence or prior initializer editions.',
                             'Implementation, installation, deployment, Git mutation/publication and external messages during this plan-creation Task.'],
               execution_authority='Plan creation, review, readiness and tracking do not themselves authorize implementation or another separately governed action. Execute only after the user authorizes the exact ready revision through the project Task workflow; dependency installation, root adoption, provenance maintenance and external actions keep their own exact authority gates.'),
    sources=sources, requirements=requirements, decisions=[], open_questions=[], assumptions=[], phases=[], tasks=[], coverage={})

def decision(statement, approved=False, basis=None):
    plan['decisions'].append(dict(decision_id=f'DEC-{len(plan["decisions"])+1:03d}',statement=statement,
        status='approved' if approved else 'proposed',source_ids=['SRC-001'],
        authority_basis=basis or 'Bounded implementation-plan proposal under TRD D02/D03; subject to exact plan review and any separate operation authority.', decided_at=NOW if approved else None))

decision('The complete first release includes all 49 requirements and AT-01 through AT-36; no reduced reader-only slice substitutes for it.',True,'The user selected the full proposed first release and approved TRD-20260919-B6D51106 revision 2. This approves requirements, not unseen implementation choices.')
decision('Use semantic HTML/CSS and TypeScript without a general UI framework, Vite only for explicit builds, and Cytoscape.js behind one renderer adapter. Pin supported versions only after current primary-source compatibility/license/CSP review in TASK-003. Use its built-in finite layout initially; add no worker/extension/second renderer unless measured need and exact review justify it.')
decision('Keep frontend source/build declarations in SKILLS-depo/ontology/explorer/; stage builds privately and publish a reviewed manifest-addressed bundle under explorer/assets/ with lock, build identity and third-party notices. Do not rely on dist/ or build/ because the Template updater excludes them; no broad exclusion relaxation is proposed.')
decision('Introduce strict optional ontology-explorer.yaml configuration with service/session/resource budgets, reviewed starting IDs, categories by exact type/ID, and source/predicate presentation mappings. Keep ontology.yaml and ontology-advanced.yaml schemas unchanged and retain a validated default reader configuration when the optional companion is absent. Neutral starter values contain no depot identities.')
decision('Use a dedicated Python reader service and six authenticated JSON POST reads at /api/explorer/v1/context, search, entry, relationships, neighborhood and source; use separate session bootstrap and narrow health endpoints. These spellings are proposed. The server selects one root at launch and imports no browser authoring dispatcher.')
decision('Use existing match/ranked/limits semantics with semantic=False and compact reader projections. Apply visibility/category/lifecycle and stable sort before page slicing; use server-authenticated stateless cursors scoped to service session, root/project, snapshot, normalized query/filters/direction/sort and last stable key. Never send arbitrary traversal state from the client.')
decision('Materialize immutable canonical views with selected input/helper/configuration/presentation digests, bounded before/after verification, observation of the existing publication lock and unresolved selected-input transaction state. Reuse the existing publication coordination read-only; do not create a lock during browsing or accept a stable partially committed transaction. A bounded retry then knowledge_updating response is preferable to mixed input. Cache at most a bounded current/retiring view set and release retired views after readers finish.')
decision('Use exact record source reference identities registered in the chosen snapshot; the browser submits an entry/relation ID and opaque reference ID, never a path. On source open, re-read with no-follow confinement and report recorded/current hash difference while retaining the old entry snapshot. Show exact line/JSON/uniquely delimited section content when proven; otherwise label bounded text as an excerpt.')
decision('Processes use the entry/relationship APIs plus reviewed references to exact linked source sections. Render original supported ordered text before any diagram; do not extract execution order from dependencies, relatedTo or layout. No structured sequence schema extension or authored missing process content is part of frontend delivery.')
decision('Keep application state in one small explicit read/state layer: route, selection, focus, query/filters, snapshot, expansions, source selection and view preferences are distinct. Hash routes carry encoded stable IDs and safe view state; immediately consume/remove bootstrap fragment before retaining intended navigation. Knowledge/source bodies remain memory-only.')
decision('Start each map at one hop with evaluated defaults near 25 nodes/50 edges, reduced by stricter project/request/byte caps. Proposed cumulative 100-node/200-edge browser limits are independent. Preserve relation IDs/self-loops/parallel edges/qualifiers; one normalized returned set drives both graph and list. Selection does not refocus or relayout; focus/expansion are explicit.')
decision('Propose ontology.py explore --open for the explicit reader launch and explore-health for a narrow scoped probe. Deprecate workbench with an explicit error pointing to explore; reject former authoring/grant arguments rather than silently alias them. Preserve agent command contracts and historical compatibility definitions; final names are frozen by TASK-002 before implementation.')
decision('Gate current shipping inventories and legacy frontend retirement on direct reader security/offline/list/source/isolation evidence. Keep shared trusted authority helpers callable for existing verified non-browser clients; preserve historical v9 receipts/resources semantics with an explicit current explorer capability path rather than rewriting old editions.')
decision('Qualify the product with the actual built asset manifest and a separate namespace fixture sharing a label with a different meaning. Record unperformed assistive-technology/user environments; use the owner walkthrough when no unfamiliar participant is available, without a broad usability claim. Proposed latency, graph size and fixture scales remain evaluated targets, not guarantees.')

def phase(n,title,objective,scope,deps,entry,exit,risks):
    plan['phases'].append(dict(phase_id=f'PHASE-{n:03d}',title=title,objective=objective,scope=scope,
        depends_on_phase_ids=[f'PHASE-{d:03d}' for d in deps],entry_conditions=entry,exit_criteria=exit,task_ids=[],risks=risks))

def task(n,p,title,action,reqs,artifacts,deps,criteria,checks,risks=()):
    tid=f'TASK-{n:03d}'
    plan['tasks'].append(dict(task_id=tid,phase_id=f'PHASE-{p:03d}',title=title,action=action,
        requirement_ids=[f'REQ-{i:03d}' for i in reqs],design_basis=[],target_artifacts=artifacts,
        dependencies=[f'TASK-{i:03d}' for i in deps],parallel_group=None,risks=list(risks),
        acceptance_criteria=criteria,verification_steps=checks,status='planned',blocker_reason=None,pause_reason=None,
        skip_reason=None,skip_authority=None,evidence=[],completed_at=None))
    plan['phases'][p-1]['task_ids'].append(tid)

P='SKILLS-depo/ontology/'
V='Verification/project-knowledge-explorer-first-release/'

phase(1,'Establish implementation baseline and contracts','Freeze the current product/caller/content baseline and proposed implementation contracts before product edits.',
      ['Scope, preservation, process sources, API/configuration, dependencies, acceptance fixtures'],[],
      ['The exact canonical implementation plan is reviewed, ready and separately authorized for implementation.', 'Current project instructions and mixed working tree are reinspected.'],
      ['All source-derived requirements and AT scenarios map to bounded implementation and verification work.', 'Baseline, interface and source/asset ownership decisions have reviewable current evidence.'],
      ['A stale source recommendation or silent overwrite could damage unrelated state; re-baseline and retain exact protected hashes.', 'Library/configuration choices remain proposals until reviewed; installation is a separate operation.'])
task(1,1,'Record current callers, content and protected baseline',
     'Inspect the exact implementation checkout, package copies, launchers, shared imports, schemas, tests and canonical/source inventory. Record current baseline command results and classify process content as canonical, linked-source-supported, absent or unexamined; preserve a protected-file manifest before edits.',
     [2,10,37,38,40,41,42], [V+'baseline.json',V+'caller-inventory.md',V+'process-source-inventory.json',V+'preservation-baseline.json'],[],
     ['Baseline identifies commit and diff relative to 744c8b06d5fda905201145ed313a2da8de2e601f; all unrelated edits are accounted for.',
      'Runtime callers, shared imports, active tests/docs/launchers, initializer inventories and historical references are separated before retirement.',
      'Every discovered process candidate is selected by canonical type or reviewed ID and its supporting sections are inspected; missing order is not inferred from a name or dependency.',
      'Existing retrieval/publication/recovery/Template checks have actual baseline results or a precise pre-existing failure/environment classification.'],
     ['Record git status --short, git rev-parse HEAD and relevant source/installed hashes without staging or publication.',
      'Run the existing core check_ontology.py route and selected unittest retrieval/publication/recovery/health tests on isolated fixtures; record optional-runtime skips distinctly.',
      'Use tools/template_update.py check and current Template test entry with read-only status interpretation; do not repair drift as an inspection side effect.',
      'Inspect canonical sources and exact linked sections, including the current Curator process lead, against the profile field inventory.'],
     ['A baseline test may require absent optional runtime; record the limitation without provisioning.', 'Process-source inspection does not authorize canonical content changes.'])
task(2,1,'Freeze reader contracts and change/adoption boundaries',
     'Specify compact read schemas, errors, snapshot/transaction behavior, source-reference selection, signed cursor scope, state/history semantics, configuration and launch/health compatibility. Record exact reusable source, Template output and prospective root adoption file maps.',
     [1,2,3,5,9,10,14,18,21,22,23,24,25,28,29,30,31,32,33,37,38,39,40,41,49],
     [P+'references/explorer-contract.md','ONTOLOGY-depo/schema/explorer-v1.json',V+'implementation-decisions.md',V+'change-map.json',V+'adoption-boundary-preview.json'],[1],
     ['All response operations have project/snapshot/version/scope/data/page/limits/coverage/diagnostics contracts; totals declare scope/exactness and unknown hasMore is null.',
      'Continuation and snapshot update rules include partial publication/recovery and retained old read context.',
      'The browser dispatcher has a finite session/read allowlist, no actor/root/grant/execute paths, and safe per-code diagnostics.',
      'Reader configuration is separate from strict ontology/advanced schemas; old-command deprecation and distinct service identity are explicit.',
      'Source/Template/root/initializer changes and code-only rollback are bounded; current plan authority is not reused as installation or adoption authority.'],
     ['Review each schema field against TRD REQ-002/021/023/024/029/032 and inspect the existing helper APIs and transaction protocol.',
      'Trace each route to an allowed read owner and each proposed artifact to its source collection.',
      'Review compatibility with strict advanced-profile and initializer v9 resource validation; record the current capability path without changing prior receipt meaning.'],
     ['Stable pre/post digests alone can accept a paused partial publication; include transaction coordination and tests.', 'An oversized full explain() response must not be reused as compact search.'])
task(3,1,'Review and pin explicit frontend build dependencies',
     'Evaluate the proposed TypeScript/Vite/Cytoscape build-only toolchain against current primary upstream version, license, browser and CSP documentation, then record exact lock and notices plus reproducible offline runtime packaging. Obtain any required explicit installation authority for the exact reviewed manifest before provisioning.',
     [28,32,34,36,49],[P+'explorer/package.json',P+'explorer/package-lock.json',P+'explorer/THIRD_PARTY_NOTICES.md',P+'explorer/BUILD.md',V+'dependency-review.md'],[2],
     ['Dependencies have exact provenance and compatible licenses; no Logseq graph code or embedded application is copied.',
      'Normal launch requires only installed assets, selected Python and a browser; Node is build-only.',
      'Renderer choice fits production CSP, finite layout, lifecycle cleanup, parallel edges and list equivalence without a second library.',
      'Dependency review distinguishes selected declarations, installation authority, actual install and actual build.'],
     ['Verify selected package versions and license text against current official upstream sources; retain dates/URLs and notices.',
      'Review lock resolution and asset output against distribution exclusions; confirm no implicit install/build path in launch design.'],
     ['No package version is asserted current by this draft; if a choice fails the stated contract, revise the exact decision before implementation.'])
task(4,1,'Create canonical fixtures and full acceptance mapping',
     'Create isolated neutral/core-only, second-namespace, small, representative and stress fixtures plus one requirement/AT-to-test matrix. Include semantic and malformed boundary cases without modifying live canonical knowledge.',
     [3,6,7,9,10,16,18,20,21,26,38,43,45,46],
     [P+'tests/explorer_fixtures.py',P+'tests/fixtures/explorer/',V+'acceptance-matrix.json',V+'fixture-manifest.json'],[1,2],
     ['The matrix names all REQ-001 through REQ-049 and AT-01 through AT-36 with future implementing files and evidence owners.',
      'Fixtures include duplicate/shared labels with different namespace meaning, aliases, long fields, sources, parallel predicates, qualified/self/cyclic edges, high-degree hubs, stale/missing references, ordered and unordered processes.',
      'Approximate 50/100, 1000/5000 and 5000/50000 entry/relation targets are labeled synthetic; loader byte/record ceilings are measured and distributed fixture files obey supported per-file bounds.',
      'Fixtures and private session material are excluded from served production assets.'],
     ['Run fixture loading/validation and document deliberately invalid cases as rejected cases, not valid canonical graphs.',
      'Check every AT and requirement has a test/evidence route and that fixtures never appear in the production manifest.'],
     ['The core parser limits one @graph to 10000 records and reads bounded files; stress data must be partitioned within supported configured inputs rather than increasing loader contracts.'])

phase(2,'Build the canonical read adapter','Provide bounded, snapshot-consistent presentation data without changing agent semantics.',
      ['Snapshot coordination/cache, compact search/cursors, identity/relations, source registry/excerpts'],[1],
      ['Phase 1 decisions, fixtures and preservation baseline are complete; no product data changes are needed.'],
      ['Adapter unit/service-independent tests establish faithful meaning, bounds and source/version semantics.', 'No adapter path invokes an authoring, generation, build, memory or optional AI operation.'],
      ['Read cache must not become authority; source byte integrity and transaction freshness remain checked.'])
task(5,2,'Implement immutable snapshot acquisition and bounded cache',
     'Build ontology_explorer_read snapshot acquisition over load_project with verified before/after selected inputs/helper/config digests and existing publication coordination. Create immutable record/source/adjacency indexes keyed by resolved root, project, snapshot, adapter and presentation versions; bound memory/concurrency and retire inactive views.',
     [2,21,22,26,27,33],[P+'scripts/ontology_explorer_read.py',P+'tests/test_explorer_snapshot.py'],[2,4],
     ['A newly served current view is validated and internally coherent; concurrent/partial publication yields bounded retry or knowledge_updating, never a mixed graph.',
      'Existing publication.lock may be observed/acquired read-only when present; browsing creates no lock file, receipt, projection or coordination store. Missing-to-present lock races and unresolved selected-input intents are covered.',
      'Retained old views are explicitly snapshot-bound and released when active readers finish; limits stop unbounded cache growth.',
      'Source-change warnings do not invoke assert_current as a blanket reading refusal or repair evidence.'],
     ['Use barriers/fault injection with actual publication/recovery helpers on disposable fixtures, including interrupted multi-file commits, missing lock creation race, source change and continuous churn.',
      'Assert selected inputs and helper/config versions differ coherently; bound retries and measure immutable-view memory.',
      'Instrument disallowed build/memory/optional-profile calls and verify none occur.'],
     ['A new lock protocol would conflict with existing publication; reuse the owner contract.', 'Stable partial writes require explicit refusal even when files no longer change.'])
task(6,2,'Implement deterministic compact search and validated pagination',
     'Reuse canonical ranking and limits while creating compact summaries, exact type/ID category mapping, lifecycle visibility and stable signed cursors. Filter before pagination and serialize within the whole envelope budget; retain explicit incomplete coverage.',
     [3,5,6,7,18,23,24],[P+'scripts/ontology_explorer_read.py',P+'tests/test_explorer_search.py'],[5],
     ['Exact ID/preferred label/alias/definition search preserves canonical deterministic ranking with semantic=False and unchanged agent default.',
      'Ambiguous labels return all matching identities with module/project distinctions; aliases keep one preferred identity.',
      'Category/lifecycle filtering occurs before page slicing; stable continuation has no duplicate/skipped identity within a snapshot.',
      'Signed cursors reject altered service/project/snapshot/query/filter/direction/sort scope and oversized tokens; no recursive browser state bypass exists.',
      'Byte/time/item exclusions, unknown total and byte-limited empty results are represented honestly.'],
     ['Compare exact/label/alias/lexical ordering with existing ranked() outputs and existing search(..., semantic=False) semantics.',
      'Run multi-page filter, signature tamper, changed query/snapshot, duplicate labels, minimal byte budget and metadata-only limit fixtures.',
      'Check serialized response bytes include metadata; instrument semantic/profile imports to prove ordinary explorer search does not invoke them.'],
     ['Calling existing search then filtering its already truncated result would lose valid later matches.', 'Cursor last key must advance only over actually returned stable identities.'])
task(7,2,'Project exact entries, relationships and bounded neighborhoods',
     'Implement exact entry and relation projections plus incoming/outgoing adjacency paging and one-hop neighborhoods. Resolve nodes/predicate labels from the same view and register compact source references without copying source bodies into search/graph responses.',
     [2,3,8,9,14,16,18,19,23,24],[P+'scripts/ontology_explorer_read.py',P+'tests/test_explorer_projection.py'],[5,6],
     ['Definitions/aliases/scope/examples/non-examples/status/module/location retain recorded wording; absent fields remain absent.',
      'Every edge retains exact relation ID, subject/predicate/object, direction, qualifiers, classification and evidence refs, including parallel relations and self-loops.',
      'Layer selection distinguishes semantic relations, inferred/derived/external facts, type/source associations and navigation categories.',
      'Per-request traversal/items/bytes and max visited nodes respect existing contracts; total coverage applies only to the requested scope.',
      'Dangling references rejected by canonical validation remain a specific read error with safe underlying ID details; valid fixture projections never fabricate endpoint labels.'],
     ['Compare normalized fields directly with canonical fixture bytes and check source/reference identity deterministically.',
      'Exercise incoming traversal, two predicates/same endpoints, cycles/self-loops, qualifiers, missing references, exact deprecated entries and one-hop bounds.',
      'Check the graph/list normalized data can enumerate exactly the same edge identities, endpoints, warnings and scope.'],
     ['Do not interpret retrieval available_results as totalRelationships.', 'Raw graph positions or relation groups cannot create semantic assertions.'])
task(8,2,'Implement confined registered source excerpts and freshness',
     'Resolve source opens from selected entry/relation plus registered snapshot reference ID, revalidate bytes and confinement, and return an exact verified locator excerpt or explicitly labeled bounded text with recorded/current evidence versions.',
     [11,20,26,27,32,33],[P+'scripts/ontology_explorer_sources.py',P+'tests/test_explorer_sources.py'],[5,7],
     ['Sources open only when registered to the selected identity/reference in the selected snapshot and allowed by canonical/module source selection.',
      'Changed bytes remain visibly different from recorded evidence; the previous entry remains available and no hash/configuration is rewritten.',
      'Exact line/JSON/unique section extraction is distinguished from fallback bounded excerpts; unsupported/ambiguous locators never claim an exact cited passage.',
      'Traversal/absolute path/symlink/unselected references and oversized or unsafe bodies fail safely; no external fetch, embedded instruction or executable HTML occurs.'],
     ['Exercise encoded traversal, symlink components, absolute paths, reference reassignment/cross-snapshot spoofing and paths beyond the allowlist.',
      'Change sources between entry/open and during open; verify current versus recorded hashes and immutable entry context.',
      'Test section ambiguity, long content, line/JSON bounds and safe error redaction. Compare all protected bytes/timestamps before and after.'],
     ['An allowlisted file alone is insufficient: the reference must also belong to the selected identity.', 'A stale locator may no longer identify the original passage and must be labeled accordingly.'])

phase(3,'Build the local reading service and asset contract','Expose only session and bounded reads through the normal Python production launch path.',
      ['Service dispatcher, session isolation, resource controls, production assets, CLI/health'],[2],
      ['Read adapter and source confinement tests are complete; reviewed dependency/build declarations exist.'],
      ['Real HTTP negative and positive tests prove local read isolation and unavailable writes.', 'Explicit installed-assets and launch/health contracts work without optional advanced profiles.'],
      ['Read-only UI does not secure a write-capable service; restrict the dispatcher itself.', 'Session credentials may escape through URLs, cookies or evidence unless captured carefully.'])
task(9,3,'Implement dedicated read-only dispatcher and resource limits',
     'Create ontology_explorer.py as an independent bounded loopback HTTP service with exact read endpoint dispatch, strict envelopes, JSON/request-size/deadline/concurrency/memory controls and short fixed diagnostic mappings. Do not subclass Workbench or import its authoring dispatcher.',
     [20,23,26,28,29,31,33],[P+'scripts/ontology_explorer.py',P+'tests/test_explorer_service.py'],[5,6,7,8],
     ['Only six reader operations and session/health functionality are dispatchable; every old write/query/generate/profile/Task endpoint fails without mutation.',
      'Project root is chosen by the server at launch; request schemas reject actor/grant/root/scope/function/command fields.',
      'Request bytes, elapsed work, concurrent materializations and response/cache memory have independent finite limits and truthful resource-limit results.',
      'Unexpected failures reveal no Python exception text, credential, source body or out-of-project path; diagnostics retain safe codes.'],
     ['Exercise actual HTTP requests for every allowed read and every forbidden old/generic endpoint, including malformed/oversized JSON and concurrent exhaustion.',
      'Inspect imports/call graph for forbidden authoring and optional runtime dependencies.',
      'Assert error envelopes are bounded and safe while source/entry regions remain distinguishable to the client.'],
     ['ThreadingHTTPServer defaults are not sufficient concurrency/deadline protection; enforce worker/admission and read/write timeouts.'])
task(10,3,'Implement isolated one-use reading sessions',
     'Reuse the established Host/Origin/CSRF/bootstrap protections in a reader-owned session component, bound to one service/root. Consume bootstrap once and establish fresh reader-only cookies/session memory; preserve no old authoring credential.',
     [12,20,29,30,31],[P+'scripts/ontology_explorer.py',P+'tests/test_explorer_sessions.py'],[9],
     ['Loopback binding is exact; hostile Host/Origin/cross-site/CSRF/session credentials return no project data.',
      'Cookies and CSRF state are isolated across concurrent local services and project roots, including port reuse/restart; expiry is enforced.',
      'Bootstrap URL is one-use/short-lived and access logs contain no credentials; startup runtime files are exclusively created and narrowly owned if used.',
      'Browser state will remove bootstrap from history/copy routes; safe new-tab entry links authenticate without leaking or reusing authoring authority.'],
     ['Run concurrent actual local services with cross-cookie/CSRF/bootstrap replay probes and wrong-project credentials.',
      'Exercise expiry, existing-cookie reconnect, restart/port reuse, no-CORS OPTIONS and service stop; inspect only redacted results.',
      'Capture before/after exact runtime file manifest and confirm no undocumented session artifacts or logs are created.'],
     ['Cookies are host-scoped, not port-scoped; service-instance isolation must prevent collisions.', 'Loopback HTTP cookie protections must be assessed honestly rather than claiming TLS Secure on HTTP.'])
task(11,3,'Serve manifest-owned production assets with narrow CSP',
     'Implement an explicit build/publication script that writes reviewed hashed JS/CSS/assets plus a complete manifest under explorer/assets/, and serve only that manifest with safe MIME/no-store/security headers. Keep the actual production CSP compatible with local renderer use and deny unknown assets.',
     [26,28,32,37,49],[P+'explorer/build-assets.mjs',P+'explorer/assets/manifest.json',P+'scripts/ontology_explorer.py',P+'tests/test_explorer_assets.py'],[3,9,10],
     ['Normal launch serves installed manifest-listed resources only and performs no build/install/CDN/remote fetch.',
      'Missing/mismatched assets produce incomplete_package with a maintenance route; source maps/package-manager caches/source tree are not served.',
      'Unknown/traversing/symlinked asset requests fail and correct MIME/CSP/nosniff/referrer/frame policies apply.',
      'The manifest binds package lock, source/build identity and notices; output avoids the excluded dist/build directory names.'],
     ['Build a minimal actual application entry through the chosen reviewed toolchain after explicit installation authority; validate every served asset digest.',
      'Run asset traversal, query/path encoding, source-map, directory and symlink negative tests.',
      'Use the production CSP from the actual service in later browser tests; reject unsafe-eval or broad inline/remote exceptions.'],
     ['A frontend build may inject inline style attributes for canvas sizing; document any narrowly scoped style mechanism required and prove it without broad script exceptions.'])
task(12,3,'Add explicit reader launch and bounded health inspection',
     'Add the reviewed core reader launch and narrow health commands without requiring workbench-profile enablement or publication authority. Document missing-assets/configuration/session handling and the exact runtime lifecycle; leave old command cutover to its gated retirement task.',
     [20,28,29,30,39,40],[P+'scripts/ontology.py',P+'scripts/ontology_explorer.py',P+'references/commands.md',P+'tests/test_explorer_health.py'],[9,10,11],
     ['The proposed explore --open command starts only the selected reader service and optionally opens a fresh safe bootstrap entry under explicit launch authority.',
      'Health distinguishes installed/configured/running/readable/stale/wrong-project/unavailable without unrelated optional readiness sweeps or startup side effects.',
      'Service identity differs from sys4ai-ontology-workbench; health uses a bounded explicit loopback origin and never accepts a bootstrap URL.',
      'Old authoring CLI behavior is classified and preserved until qualified cutover; no documentation claims the reader can restart a stopped process from a web page.'],
     ['Run launch/stop/health with optional advanced configuration and runtimes absent, invalid assets/configuration and wrong project origin.',
      'Assert health is bounded and does not provision, read proposal inventory or expose root/source/session details to unauthenticated requests.',
      'Compare help/schema/docs spelling with the exact implemented commands.'],
     ['Existing advanced-health reports workbench identity and may require a separate legacy assessment path during transition.'])

phase(4,'Build the reader and navigation','Deliver the four-destination reader shell and faithful text/source/process workflows.',
      ['Overview, search, entry/relationship/process text, history/preferences, async/failure states'],[3],
      ['Production service, sessions, read contracts and actual asset build path are available.'],
      ['Core reading workflows run through the actual service/bundle with exact source meaning and browser history.', 'No authoring, optional AI, memory or broad administrative modules load.'],
      ['Convenience presentation can erase status/evidence distinctions; review canonical comparisons and source-backed content.'])
task(13,4,'Implement accessible shell, Overview and view preferences',
     'Create semantic navigation for Overview, Terms, Processes and Map with visible project/search identity, reviewed starting points, help/theme controls and responsive navigation. Persist only namespaced harmless preferences with reset.',
     [1,4,13,28,34,36],[P+'explorer/src/app.ts',P+'explorer/src/views/overview.ts',P+'explorer/src/styles.css'],[2,11,12],
     ['Only four reading destinations appear; no management metrics, raw storage kinds, hidden Advanced controls or whole-graph initial fetch is used.',
      'Overview uses explicit configured starting IDs/project purpose; missing starting points and empty local extensions expose honest core/category/search browsing.',
      'Light/dark/system themes and preferences reset affect presentation only, scoped by project identity/root discriminator.',
      'Semantic headings/navigation, visible search, reflow, focus and primary controls support the WCAG target.'],
     ['Inspect network/module loads for absent authoring assets and whole-project graph requests.',
      'Run neutral/core-only and differently named project fixtures, preference isolation/reset, initial theme and narrow navigation checks.'])
task(14,4,'Implement deterministic search and discovery UI',
     'Connect visible labeled search/submit, optional combobox suggestions, alphabetical/category browsing, result cards, removable filter chips and bounded continuation to the reader search API.',
     [5,6,7,18,20,34],[P+'explorer/src/views/terms.ts',P+'explorer/src/components/search.ts'],[6,13],
     ['Search result labels/definitions/disambiguation/match reasons match canonical data without formula or generated text.',
      'The query remains visible through no-match, filter and byte/time-limited states; clear filters and continuation remain meaningful.',
      'Autocomplete supports Arrow Up/Down, Enter and Escape dismissal without erasing the query, while ordinary submit remains available.',
      'Filtered later pages remain reachable and response scope/unknown counts are labeled honestly.'],
     ['Run AT-02 through AT-06 against actual service fixture responses, including duplicate alias/label and later-page category matches.',
      'Review combobox semantics against current WAI-ARIA primary guidance during implementation and test keyboard/screen-reader announcements.'])
task(15,4,'Implement faithful entry, relationship and source reading',
     'Render recorded definitions first, optional source-backed detail sections, incoming/outgoing relation sentences and precise relationship details. Add a bounded source drawer retaining entry context and independent lifecycle/fact/freshness warnings.',
     [2,3,8,9,11,20,32,34,35],[P+'explorer/src/views/entry.ts',P+'explorer/src/components/relationship.ts',P+'explorer/src/components/source-drawer.ts'],[7,8,13],
     ['Recorded fields remain faithful, aliases resolve to preferred identity, technical details remain inspectable and absent sections are omitted.',
      'Deprecated/draft/inferred statuses and source mismatch are distinct; no verified badge equates approval/freshness/truth/authority.',
      'Each relationship preserves canonical direction, qualifiers and exact relation ID; parallel predicates remain separate inspectable records.',
      'Source drawer opens the exact registered reference, safely escapes content and reports extraction/freshness limitations; focus moves and restores predictably.'],
     ['Run AT-07/08/09/13/14/19/20/26/27 with canonical byte comparison, long qualifiers and changed sources.',
      'Test drawer open/close/Escape focus restoration and verify malicious labels, links and source markup remain inert.'])
task(16,4,'Implement source-supported process reading',
     'Build Processes as a reviewed selection of canonical identities using entry/relationship/source reads. Present only supported purpose/applicability/roles/inputs/outputs/documents and source-quoted ordering, with numbered text before any optional map link.',
     [4,10,11,34,36],[P+'explorer/src/views/processes.ts',P+'references/explorer-content.md'],[1,7,8,13,15],
     ['Supported process fields and ordering cite exact canonical/source support; unsupported fields are absent.',
      'When order is absent the exact sentence appears: An ordered description has not been recorded. These are the documented relationships.',
      'No dependencies, relatedTo path, diagram branch or left-to-right placement become an execution sequence; pages expose no Run action.',
      'Source/long process text remains vertically readable on narrow screens.'],
     ['Run AT-17/18 with canonical ordered-source and unordered fixtures and compare rendered sequence to exact cited source sections.',
      'Inspect the live inventory disposition: unexamined content is not reported as absence, and missing content remains a separate existing review-process item.'])
task(17,4,'Implement identity history and race-safe read state',
     'Centralize read requests and state transitions with project/snapshot/query/selection request keys, sequence checks and abort support. Preserve route/query/filters/selection/focus/source intent through Back/Forward and coherent knowledge refresh; implement safe copy actions and regional failure states.',
     [12,13,20,21,24,25,30,35],[P+'explorer/src/state.ts',P+'explorer/src/api.ts',P+'explorer/src/routes.ts'],[13,14,15,16],
     ['Entry A responses arriving after B never replace B even when cancellation fails; renderers/components emit intentions through the read layer.',
      'Back/Forward and Terms/Map navigation use exact stable IDs and restore useful state; deliberate selection adds one history event, camera motion does not.',
      'Bootstrap is consumed and removed before safe intended route/history/copy state is retained; local links exclude credentials and explain live local service dependence.',
      'Snapshot conflict preserves the screen and offers Refresh knowledge; refresh atomically replaces incompatible entries/relations/expansions/cursors.',
      'Expiry/service stop preserve readable context and safe desired route, while regional failures do not blank unrelated content.'],
     ['Run AT-21/22/23 with delayed out-of-order responses, failed abort, concurrent canonical update, expiry and service stop.',
      'Inspect browser history, copied local links/stable IDs and storage for session/source bodies; test authenticated new-tab links.',
      'Exercise focus after route changes and accessible status announcements without layout-frame noise.'],
     ['Source freshness can change independently of retained ontology snapshot; the UI must distinguish current source observation from a snapshot replacement.'])

phase(5,'Build bounded Map and equivalent List','Make interactive exploration faithful, stable and fully available through text.',
      ['Normalized relationship list, renderer adapter, selection/focus/expansion, lifecycle/fallback'],[4],
      ['Canonical projection and reader state contracts are implemented; graph dependency is reviewed and locally built.'],
      ['Map and List carry identical substantive information/scope/warnings and complete keyboard exploration.', 'Renderer failure and leaving the view retain text reading and release graph resources.'],
      ['Graph layout can imply causality or hierarchy; explicit semantics and user comprehension tests control that risk.'])
task(18,5,'Implement normalized graph/List data and text actions',
     'Build one browser normalization/projection of returned neighborhood data and a first-class semantic relationship List. Provide open entry/precise relationship/source, focus and bounded more-connections actions from that shared normalized set.',
     [9,14,16,18,19,20,25,34],[P+'explorer/src/map/data.ts',P+'explorer/src/map/list.ts'],[7,15,17],
     ['List and graph preserve the exact same relation IDs/endpoints/direction/qualifiers/warnings/filters/returned scope.',
      'List users can complete every substantive map reading/exploration action without canvas, drag, hover or double-click.',
      'Browser cumulative bounds and server/request exclusions are distinct; no global completeness claim is fabricated.',
      'Broken/absent relationships produce specific truthful states with safe IDs inspectable.'],
     ['Run AT-13/14/15/16/29 parity and keyboard workflows using the actual normalized graph response.',
      'Compare semantic content sets and focus/source/more actions across both modes, including truncation and stale-source warnings.'])
task(19,5,'Implement restrained renderer and explicit map interactions',
     'Implement the small Cytoscape renderer adapter using canonical node/edge IDs, finite built-in layout and stable incremental position reuse. Add visible pan/zoom/Fit/Reset/Focus here/Show more/List controls while keeping selection, focus and camera distinct.',
     [9,14,15,16,17,18,19,36,49],[P+'explorer/src/map/renderer.ts',P+'explorer/src/map/controller.ts',P+'explorer/src/map/map.css'],[18],
     ['Default map requests one hop near evaluated 25-node/50-edge targets only within stricter project/request/byte budgets; no unfiltered graph fetch occurs.',
      'Selection highlights and updates readable details without moving camera or graph focus; Focus here and Show more are explicit bounded operations.',
      'Parallel relations/self-loops/cycles/qualifiers remain meaningful; selected/adjacent edge labels and canonical direction stay inspectable.',
      'Expansion preserves prior positions where practical, performs bounded adjustment and stops; no continuous motion/physics UI/importance sizing/3D appears.',
      'Legend and exact guidance read: Select a term to read it. Use Focus here to explore its connections.'],
     ['Run AT-10/11/12/13/14/15 in the production renderer; inspect selected/focus identity and camera before/after.',
      'Stress high-degree expansion to evaluated cumulative 100-node/200-edge ceiling and verify alternative focus/filter/list guidance.',
      'Check reduced motion, labels at crowded zoom and layout timeout fallback without interpreting position as semantics.'],
     ['A layout algorithm must not become a process engine or unbounded worker.', 'An oversized qualifier must remain complete in accessible details even when edge label space is short.'])
task(20,5,'Verify map cleanup, responsive controls and renderer failure',
     'Implement lazy graph import/instance lifecycle, listener/timer/observer cleanup and bounded layout timeout recovery. Complete narrow-screen selected details, List visibility, keyboard controls, focus restoration and stable text fallback.',
     [15,17,19,20,25,34,35,36],[P+'explorer/src/map/controller.ts',P+'explorer/src/styles.css',P+'explorer/tests/map-lifecycle.spec.ts'],[17,18,19],
     ['Leaving Map disposes its instance, listeners, timers and resize observers; no hidden simulation continues and selection does not rebuild the graph.',
      'AT-34 renderer failure leaves definitions, relationship List and source inspection usable; retry creates no remote service or hidden computation.',
      'At 320 CSS pixels, substantial zoom, both themes and reduced motion, controls/status/text remain operable; mobile Map has dismissible details and visible List.',
      'Focus and announcements reflect meaningful user state rather than layout frames, with no hundreds of invisible graph tab stops.'],
     ['Run instrumented repeated Map enter/leave and selection tests for instance counts, observer/listener/timer disposal and memory growth.',
      'Force module/layout/canvas failure under actual production CSP; complete the same knowledge tasks through List.',
      'Run AT-29/30/34 and inspect keyboard focus and narrow layout in production browser renders.'])

phase(6,'Qualify the actual production candidate','Establish security, non-mutation, offline behavior, accessibility and measured performance before rollout.',
      ['Production build/service/browser integration, fault/security checks, accessibility, scale and human comprehension'],[5],
      ['All reader/map/list source changes are integrated in a real manifest-bound production candidate.', 'Any dependency provisioning and test-runtime use have explicit current authority.'],
      ['Acceptance evidence covers all browser/data/security behavior needed to permit cutover; high-impact defects are corrected and affected tests rerun.', 'Measurements and manual limitations are recorded without unqualified conformance claims.'],
      ['Tests against a dev server or screenshots alone do not establish production behavior.', 'Performance pressure cannot weaken snapshot/source integrity.'])
task(21,6,'Build and exercise the complete production read workflow',
     'Create a reproducible production build and run the actual Python reader with offline networking under its deployed CSP. Exercise Overview/search/entry/process/map/List/source/history/expiry and fault workflows against canonical fixtures; attach evidence to every applicable AT.',
     [1,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,28,32,39,43,48],
     [P+'explorer/assets/manifest.json',P+'explorer/tests/reader.spec.ts',V+'browser-acceptance.json',V+'build-manifest.json'],[12,14,15,16,17,18,19,20],
     ['The actual manifest-bound production reader and renderer work with network egress unavailable, no remote assets and optional AI/RDF/standards/inference services absent.',
      'AT-01 through AT-23 and AT-27/28/32/34 have actual expected behavior or an explicit failing result; implementation gaps are corrected before cutover.',
      'Source HTML/scripts/links remain inert under real CSP; build/runtime identity and service command are recorded.',
      'Loading, empty, limit, invalid canonical, stale source, mixed snapshot, late response, expired session and renderer failure states retain useful context.'],
     ['Run the production build command from the reviewed package lock and verify installed asset hashes and offline network observations.',
      'Run the browser suite against the real Python production service, not the Vite dev server.',
      'Reopen exact evidence outputs and compare each recorded result with its AT/requirement criteria; retain failures and content gaps separately.'])
task(22,6,'Prove read isolation, unavailable writes and non-mutation',
     'Run hostile HTTP/browser probes and a protected hash/timestamp audit across the complete production read workflow. Exercise two live isolated services and source/asset attacks; verify that no browser read can reach authoring or install/build/repair anything.',
     [20,26,27,28,29,30,31,32,33,38,43],[P+'tests/test_explorer_security.py',V+'security-acceptance.json',V+'read-nonmutation.json'],[21],
     ['AT-24/25/26/27 pass against actual service requests, with old endpoint attempts causing no protected change or disclosure.',
      'AT-33 compares ontology, configuration, sources, memory data/configuration, proposals, receipts and generated products before/after; only individually documented startup session artifacts and harmless preferences are exempt.',
      'No broad .sys4ai exemption hides implicit compile/wiki/semantic/memory changes; browsing works while wiki is missing/stale.',
      'Cross-root namespace/cookie/cache/reference/cursor attacks fail and no bootstrap material appears in logs/evidence/history/copies.'],
     ['Run actual session/Host/Origin/CSRF/CORS/port-reuse/cross-service probes and every forbidden dispatcher route.',
      'Compare exact protected file hashes and relevant timestamps around startup separately from browsing, then stop and inspect owned runtime cleanup.',
      'Test arbitrary/encoded/traversing/symlink/unknown manifest paths and source refs, and assert safe bounded error response content.'],
     ['Non-mutation must include generated products and control records, not only canonical ontology files.'])
task(23,6,'Evaluate production accessibility and comprehension',
     'Run automated accessibility checks plus manual keyboard and actual screen-reader knowledge-task walkthroughs on the production bundle. Evaluate relationship/process understanding with an unfamiliar participant when available, otherwise record the owner walkthrough and the unperformed broader validation.',
     [10,19,34,35,36,43,44,47],[V+'accessibility.md',V+'usability.md',P+'explorer/tests/accessibility.spec.ts'],[21,22],
     ['Major tasks complete by keyboard and List, with semantic navigation, accessible search, predictable source/route focus, unobscured focus and useful announcements.',
      'Contrast, 24-by-24 target criterion/exceptions, 320 CSS-pixel reflow, substantial zoom, both themes and reduced motion are assessed on the actual interface.',
      'Evidence names actual macOS VoiceOver/Safari and other tested versions; unavailable Windows combination is explicitly unperformed.',
      'Knowledge tasks include term finding, distinctions, directed relation meaning, neighbor-and-return, process/missing order and evidence freshness; roughly 30-second discovery is a proposed target, not a claim.',
      'Wrong turns/help/misinterpretations/participant wording are recorded without statistical generalization; reversed-edge or layout-as-causality misunderstandings are resolved before polish.'],
     ['Run current automated browser accessibility checks and compare results with manual keyboard and VoiceOver/Safari walkthrough records.',
      'Inspect contrast/focus/reflow states in real theme and zoom conditions; document any assistive-technology limits.',
      'Record small exploratory comprehension rounds with privacy-minimized observations and retest high-impact fixes.'],
     ['A scan pass or component choice does not establish WCAG compliance.', 'If only the owner participates, do not claim novice usability validation.'])
task(24,6,'Measure bounded production performance and stress behavior',
     'Benchmark the real production candidate repeatedly on the actual target host across labeled small/representative/stress fixtures. Report cold/warm timing, memory, payloads, loader capacity and degradation while preserving all integrity checks; optimize only measured bottlenecks within approved contracts.',
     [18,22,25,33,43,45,46],[V+'performance.json',V+'performance.md',P+'explorer/tests/performance.spec.ts'],[4,21,22],
     ['AT-36 records actual median/p95, hardware/browser/build/dataset size and cold/warm conditions; representative and stress behavior remains bounded and honest.',
      'Targets retain conditions: about 2s cold readable screen, warm search p95 200ms excluding debounce, warm entry p95 250ms, focused roughly 25/50 graph usable about 1.5s, selection feedback 100ms without full recreation.',
      'Small roughly 50/100, representative 1000/5000 and stress 5000/50000 fixture scales are measured against actual loader capacity; stress success means bounded degradation, not whole-graph rendering.',
      'Source-validation latency is measured separately when dominant; immutable input reuse precedes contract changes, with no stale-as-current shortcut.',
      'Bundle compressed size and memory become inspectable regression baselines; expansion preserves current view/progress/cancellation.'],
     ['Run repeated measured workflows with fixed corpus/build and instrument applied-result timestamps, renderer usable/selection feedback and server resource counters.',
      'Check enforced traversal/items/bytes/cumulative browser limits and memory across high-degree and repeated navigation workloads.',
      'Record first failing capacity threshold and safe rejection when stress exceeds a supported loader file/record bound; never silently increase shared agent caps.'],
     ['Qualified proposed budgets may not be reached on the actual host; report measurements and disposition material misses before an unqualified performance claim.'])

phase(7,'Distribute, adopt and retire the old entry point','Deliver source-owned assets to the Template and separately selected root, then cut over with preservation and rollback evidence.',
      ['Current package/initializer inventory, Template distribution, root adoption, old-command retirement, provenance impact'],[6],
      ['Production candidate passes reader/map/source/security/isolation gates; material accessibility or comprehension errors are resolved.', 'Exact Template scope is configured and a separate root adoption manifest/authority is available before root writes.'],
      ['Template and root serve the intended version with isolated identity and assets; other projects and history remain unchanged.', 'Active old frontend and write service entry points are retired without loss of agent CLI operations or newer knowledge.'],
      ['The current initializer explicitly requires old assets; retirement must preserve historical editions and current capability completeness.', 'Provenance/helper changes can stale certifications; report and route separate maintenance without browser repair.'])
task(25,7,'Update current delivery contracts and neutral Template assets',
     'Update reusable ontology docs, explorer neutral schema/starter, explicit configuration mappings and current initializer/static capability inventories for the reader package. Run Template check, inspect its exact change set, then apply through the existing owner and validate the generated neutral package.',
     [28,37,38,39,40,49],[P+'README.md',P+'SKILL.md',P+'references/explorer-contract.md','ONTOLOGY-depo/starter/ontology-explorer.yaml','depot/template-update.json','SKILLS-depo/init-new-project/scripts/init_ontology_advanced.py','SKILLS-depo/init-new-project/assets/static-capability-v1.json','SPECS-depo/template-tests/test_template_contract.py',V+'template-distribution.json'],[21,22,23,24],
     ['Production assets, manifest, dependency lock/build instructions and notices ship through the source collection/Template pipeline; dist/build exclusions stay effective.',
      'Neutral Template retains empty canonical local graphs, disabled optional runtimes, no depot IDs/labels or private records; categories/purpose derive from the selected project after specialization.',
      'Current explorer capability inventory handles old workbench resource dependencies explicitly without relabeling prior initializer receipts or changing historical verification snapshots.',
      'Only the registered Template is updated; all unknown/customized conflict rules and existing watcher evidence are honored.'],
     ['Run tools/template_update.py check before apply; inspect exact source/destination manifest and current owner conflicts.',
      'Run the existing Template contract and affected initializer tests, including older receipt preservation, missing assets, notices and installed reader inventory.',
      'Reopen Template output, compare manifest asset digests and run read-only current Template check; if relying on watcher readiness inspect its fresh successful current-PID observation.'],
     ['Do not manually edit mapped Template files or remove historic v9 files merely to make new tests pass.'])
task(26,7,'Apply separately authorized root adoption and isolation checks',
     'Reinspect source and installed root copies/local guidance and finalize the exact adoption preview with overwrite/customization preservation. After specific authority, adopt only those files and test root, neutral Template through its documented identity handling, and an explicitly selected second-namespace fixture.',
     [28,29,30,37,38,39,40],[V+'root-adoption-preview.json',V+'root-adoption-receipt.json',V+'project-isolation.json'],[25],
     ['The adoption receipt records exact source/destination files, before/after hashes, preserved customizations, checks and final diff; equal bytes or registry membership supply no authority.',
      'AT-31 covers root, neutral Template behavior and second fixture with different namespace/shared label/different meaning: routes, caches, preferences, sources and sessions remain isolated.',
      'Neutral Template has no fabricated identity; direct unconfigured startup reports configuration need or a properly specialized disposable Template fixture demonstrates reading, with that distinction documented.',
      'Ordinary product projects, registry, unrelated edits and current ontology/memory/history remain intact.'],
     ['Review exact adoption manifest and current root instructions before mutation; obtain the separately required exact operation authority.',
      'Run actual production read/service/browser isolation across the three selected contexts and compare asset/build identity.',
      'Inspect protected hashes and final diff; verify no recursive product update or registry edit occurred.'],
     ['Root has intentional local differences from reusable sources; blind package replacement is prohibited.', 'Neutral unresolved identity is not a failed requirement to invent a depot identity.'])
task(27,7,'Cut over normal launch and retire active authoring frontend',
     'After adoption qualification, change the normal human entry point to the reader and implement the reviewed workbench deprecation behavior. Remove old authoring imports/routes/assets from active shipping destinations; relocate/preserve verified shared trusted authority helpers and non-browser callers as required by the baseline classification.',
     [1,28,31,37,38,39,40,41],[P+'scripts/ontology_advanced_cli.py',P+'scripts/ontology_health.py',P+'scripts/ontology_workbench.py',P+'workbench/',P+'references/commands.md',V+'cutover.json',V+'rollback.md'],[21,22,25,26],
     ['Normal launch opens only the reader; old workbench command returns a documented deprecation error and explicitly rejects incompatible authoring/grant arguments.',
      'No active frontend destination loads editor/review/advanced assets or reaches write dispatchers; a disabled widget or authoring=false flag is not the control.',
      'Existing permitted agent/CLI retrieval/proposal/review/publication/authority/recovery operations and shared helpers retain behavior.',
      'Historical ontology, memory, proposals, receipts and verification records are preserved; rollback changes only reviewed code/assets/configuration and preserves newer valid knowledge.'],
     ['Re-run active caller inventory and scan production manifests/import graphs/launchers/docs for old frontend exposure.',
      'Run old-command compatibility negatives and agent command regressions against isolated fixtures, independent of browser read-only tests.',
      'Rehearse exact code/asset/config rollback on an isolated copy with newer knowledge and confirm newer records/history survive.'],
     ['Retirement may require a shared helper extraction before deletion; do not delete authority code just because it lived in the old service.', 'Reapply final source changes to Template and exact adopted root through their existing owner boundaries if cutover changes their bytes.'])
task(28,7,'Record provenance effects and separately governed maintenance',
     'After final helper/docs/assets settle, inventory every affected source reference, lock, certification and generated product. Record exact maintenance needs and route only authorized operations through their existing owners, keeping any browser frontend completion separate from ontology/documentation maintenance.',
     [2,26,27,40,41,48],[V+'provenance-impact.json',V+'maintenance-disposition.md',V+'rollback-verification.json'],[27],
     ['Affected hashes/locked inputs/helper certifications/generated products are identified with current warnings; no mechanical hash repair silences a mismatch.',
      'No reader path repairs, compiles or republishes; any maintenance operation has its separate current authority and direct receipt.',
      'Release evidence distinguishes frontend delivery, optional/required maintenance effects and any remaining unperformed operation.',
      'Rollback evidence preserves newer valid knowledge and publication/memory history.'],
     ['Reinspect recorded source/helper/configuration provenance and relevant explicit owner health outputs after final bytes settle.',
      'Compare required maintenance scope with current authority; retain a named pending operation when unavailable rather than broadening the Task.',
      'Verify the final browser non-mutation boundary still holds after any separately authorized maintenance.'],
     ['Task execution and a plan cannot grant missing provenance publication authority; do not fabricate current certifications.'])

phase(8,'Verify final integration and deliver evidence','Close the full release only on current requirement evidence and a truthful operational handoff.',
      ['Final regressions, production visuals, bidirectional audit and limitation report'],[7],
      ['Final source/Template/root asset and command revisions are known; any required maintenance blockers are visible.', 'Current candidate fixes have been integrated and affected qualification evidence refreshed.'],
      ['Every requirement and AT scenario is accounted for with current performed evidence or an explicit incomplete gate.', 'Operational docs, production visuals, preservation/rollback and current exact revision/build identity support the final handoff.'],
      ['Historical evidence and draft plan structure are not proof of final product completion.'])
task(29,8,'Run final agent, Template and integrated production regressions',
     'Reopen final source/installed/Template artifacts and run the relevant existing agent retrieval, publication/recovery and Template/initializer suites independently of browser checks. Refresh only tests invalidated by cutover or other final changes and confirm integrated operation from the normal production launch.',
     [26,27,28,31,37,38,39,40,41,42,43],[V+'final-regressions.json',V+'final-integration.json',V+'final-preservation.json'],[21,22,23,24,25,26,27,28],
     ['AT-35 shows no unintended agent retrieval/publication/recovery/Template behavior regression; pre-existing failures are separated from introduced failures.',
      'Final actual production launch, core reads, process access, interactive map/List, source inspection, isolation and docs agree on the same build/command/schema.',
      'Protected records/configuration/generated state are preserved across browser reads; exact authorized maintenance/adoption changes have distinct evidence.',
      'Any code/bundle change after manual/performance qualification invalidates only affected results and is explicitly retested.'],
     ['Run current core check and selected existing query/publication/advanced-publication/guard/health suites using installed fixture capabilities without provisioning.',
      'Run Template check and affected initializer contract suites and verify final manifests/source/root parity within the exact adoption boundary.',
      'Re-exercise the final production workflow and negative write probe; compare protected before/after evidence and current asset digest.'])
task(30,8,'Capture production visuals and operational handoff',
     'Capture actual production views and finish launch/build/configuration/compatibility/help documentation with exact evidence links and private-data-safe images. Summarize measured performance/accessibility/usability limits and reversible migration.',
     [1,10,18,28,38,39,41,43,44,45,46,47,48,49],[V+'screenshots/',V+'RELEASE.md',P+'explorer/BUILD.md',P+'references/explorer-contract.md',P+'references/commands.md'],[23,24,28,29],
     ['Actual production images include Overview, search results, populated entry, process, focused map, parallel-edge example, source drawer, incomplete-result and narrow-screen views.',
      'The handoff records commit/build identity, changed-file map, exact commands/test summaries, browser/assistive-tech versions, measured limits, non-mutation, root/Template behavior, rollback, content gaps, pre-existing failures/skips and untested environments.',
      'Evidence contains no bootstrap links, credentials or unsupported claims; external sharing is not implied and private source bodies are sanitized before any separately authorized sharing.',
      'Normal use, missing-asset maintenance, expired/stopped service, stable ID/local link distinction and old-command deprecation are documented plainly.'],
     ['Reopen every listed screenshot and verify it came from the final production build and required state.',
      'Resolve all local evidence/doc links and compare each command/claim with current actual outputs.',
      'Inspect images and reports for credentials/private source content; retain only the minimum useful evidence.'])
task(31,8,'Audit every requirement and final preservation criterion',
     'Perform a bidirectional final audit of all 49 requirements, 36 AT scenarios, implementation artifacts and current evidence. Reinspect protected artifacts after evidence collection, record truthful highest verification levels and stop at complete only when every required outcome is supported.',
     list(range(1,50)),[V+'acceptance-matrix.json',V+'requirement-audit.json',V+'final-status.json'],[29,30],
     ['Every requirement maps to performed implementation and every acceptance criterion has current evidence; every changed artifact maps back to a requirement or justified bounded design choice.',
      'AT-01 through AT-36 have exact test/manual evidence or a clearly non-passing classification; no unperformed mandatory behavior is silently deferred.',
      'Protected paths have a final affirmative preservation observation strictly after current implementation evidence; scope exceptions are exact and authorized.',
      'Final report distinguishes static checks, fixture tests, real service/browser behavior and end-to-end delivery; remaining adoption/runtime/environment/maintenance limitations are explicit.'],
     ['Reopen canonical plan, final requirements/AT matrix and changed-file manifest and check forward/reverse coverage, dependencies and stale evidence.',
      'Read final actual outputs and compare to the exact TRD acceptance wording; do not infer pass from task labels.',
      'Inspect final Git status/diff and protected hashes after the latest evidence and classify all outstanding failures or unavailable authority before any completion transition.'])

acceptance_tasks = {21: [*range(1, 24), 27, 28, 32, 34], 22: [24, 25, 26, 27, 33], 23: [29, 30], 24: [36], 26: [31], 29: [35]}
for task_number, at_numbers in acceptance_tasks.items():
    selected_task = next(t for t in plan['tasks'] if t['task_id'] == f'TASK-{task_number:03d}')
    selected_task['verification_steps'].append('Record individual observed result and exact evidence locator for each scenario: ' + ', '.join(f'AT-{number:02d}' for number in at_numbers) + '. A range or aggregate suite result does not replace the per-scenario record.')

for r in requirements:
    r['source_ids'].extend(sid for sid, reqs in source_links.items() if sid!='SRC-001' and r['requirement_id'] in reqs)
plan['coverage'] = dict(source_to_requirement=[dict(source_id=s['source_id'],requirement_ids=source_links[s['source_id']],disposition=None) for s in sources],
    requirement_to_task=[dict(requirement_id=r['requirement_id'],task_ids=[t['task_id'] for t in plan['tasks'] if r['requirement_id'] in t['requirement_ids']],disposition=None) for r in requirements])

candidate = OUT/'candidate.json'
candidate.write_text(json.dumps(plan,indent=2,ensure_ascii=False)+'\n')
assert candidate.stat().st_size < 250000
print(json.dumps({'path':str(candidate),'sha256':hashlib.sha256(candidate.read_bytes()).hexdigest(),'bytes':candidate.stat().st_size,'requirements':len(requirements),'phases':len(plan['phases']),'tasks':len(plan['tasks'])}))
