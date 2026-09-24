from pathlib import Path
from copy import deepcopy
import hashlib
import importlib.util
import json
import re
import sys

ROOT = Path('/Volumes/P-SSD/AngryOwl/Sys4AI')
OUT = Path(__file__).parent
ORCH = OUT.parent.parent
ARCH = json.loads((ORCH / 'CAND_ARCH_V1.json').read_text())
EVID = json.loads((ORCH / 'CAND_EVIDENCE_V1.json').read_text())
plan = deepcopy(EVID)
plan['slug'] = 'project-knowledge-explorer-full-first-release'
plan['status_reason'] = 'Complete source-grounded draft for exact canonical revision review; proposed implementation choices are not yet approved and no product work has been performed.'

def unique(values):
    return list(dict.fromkeys(values))

tasks = {t['task_id']: t for t in plan['tasks']}
atasks = {t['task_id']: t for t in ARCH['tasks']}

# Integrate source observations without changing their observed times or claiming new runs.
source_by_path = {s['locator']: s for s in plan['sources']}
source_edges = {e['source_id']: e for e in plan['coverage']['source_to_requirement']}
arch_edges = {e['source_id']: e for e in ARCH['coverage']['source_to_requirement']}
for s in ARCH['sources']:
    if s['kind'] == 'prompt':
        continue
    existing = source_by_path.get(s['locator'])
    if existing:
        assert existing['digest'] == s['digest']
        # Equivalent observations share a source record; retain its original observation metadata.
        edge = source_edges[existing['source_id']]
        edge['requirement_ids'] = sorted(set(edge['requirement_ids'] + arch_edges[s['source_id']]['requirement_ids']))
    else:
        new = deepcopy(s)
        new['source_id'] = f"SRC-{len(plan['sources']) + 1:03}"
        plan['sources'].append(new)
        source_by_path[new['locator']] = new
        edge = deepcopy(arch_edges[s['source_id']])
        edge['source_id'] = new['source_id']
        plan['coverage']['source_to_requirement'].append(edge)
        source_edges[new['source_id']] = edge
for r in plan['requirements']:
    r['source_ids'] = sorted(e['source_id'] for e in plan['coverage']['source_to_requirement'] if r['requirement_id'] in e['requirement_ids'])

plan['project']['inspected_at'] = ARCH['project']['inspected_at']
for fact in ARCH['project']['baseline_facts']:
    if any(x in fact['fact'] for x in ['412 records', 'Curator process', 'separate.', 'excludes directories']):
        plan['project']['baseline_facts'].append(deepcopy(fact))
plan['project']['baseline_facts'].append({
    'fact': 'Planning evidence is source/code/test-definition inspection plus the scoped architecture-candidate canonical load. No product launch, regression suite, dependency provisioning, production browser, assistive-technology, performance or participant result is established. Process linked-source coverage is not fully classified. These are scheduled implementation gates with defined supported/absent/unexamined outcomes under TRD D06/D08; no missing scope is inferred.',
    'evidence_locator': 'TRDs/trd_project-knowledge-explorer-full-first-release_2026-09-19.md D06/D08; frozen CAND_ARCH_V1 and CAND_EVIDENCE_V1',
    'observed_at': ARCH['project']['inspected_at'],
})
# Future evidence is explicitly planned; treating it as prerequisite planning evidence would deadlock ready -> implementation.
plan['project']['evidence_gaps'] = []
plan['project']['preserved_paths'] = unique(plan['project']['preserved_paths'] + ['ontology-advanced.yaml'])
plan['project']['constraints'] += [
    'Current helper/source observations establish a planning baseline, not product acceptance. TASK-001 refreshes the baseline before product edits; linked-source content classification, dependency selection and all runtime evidence remain explicit future gates. A material new fact returns the affected design to review.',
    'Ship manifest-owned production files under explorer/assets; current Template exclusions for dist, build, node_modules and caches remain effective. Stage build output privately before publishing the complete source-owned asset manifest.',
    'Prior initializer edition receipts/resources retain their historical meaning. Current explorer capability inventory must explicitly replace the current dependency on old workbench assets before active retirement.',
    'Protected-path preservation includes knowledge/history and unrelated tracker state. Only the exact implementing Task and selected plan may receive their owner-governed tracking updates; this does not grant changes to other Tasks or plans. New release evidence belongs only to the named Verification release directory.',
]
plan['scope']['in_scope'] = [s.replace('during TRD capture', 'during plan creation') for s in plan['scope']['in_scope']]

decisions = {d['decision_id']: d for d in plan['decisions']}
decisions['DEC-003']['statement'] = 'Use authenticated same-origin JSON POST reads at /api/explorer/v1/context, /api/explorer/v1/search, /api/explorer/v1/entry, /api/explorer/v1/relationships, /api/explorer/v1/neighborhood and /api/explorer/v1/source; bootstrap/session exchange is separate. GET serves only explicit runtime bundle assets and a minimal non-sensitive service health identity. Validate exact versioned request/response envelopes; expose no generic execution, caller root or authority dispatch.'
decisions['DEC-005']['statement'] = 'Materialize immutable canonical views with complete selected-input/module/source/helper/configuration/presentation digests and read-only observation of existing publication coordination. Before and after materialization, require stable version inputs and no active or unresolved selected-input publication transaction, including stable partial commits and lock missing-to-present races. Retry at most twice within the request deadline, then return knowledge_updating; do not create/acquire write-creating locks or invoke publication/recovery. An old coherent view may remain visible only with its original snapshot and clear update warning. Missing coordination proof fails closed, while stale source evidence alone does not erase safe recorded definitions. Cache a bounded current/retiring set and release retired views when readers finish.'
decisions['DEC-006']['statement'] = 'Preserve canonical normalize/match/ranked semantics with semantic=False only for ordinary explorer search. Filter visibility/category/lifecycle before keyset pagination and project compact summaries. Use size-bounded, expiring HMAC cursors authenticated by a per-service-start secret and bound to service instance, reading session, resolved root/project, snapshot, normalized query/filter/direction/sort and last stable key. Validate scope against the active session on every page; cursors are not authentication or source/write authority and become invalid after service restart or a fresh reading session.'
decisions['DEC-007']['statement'] += ' The normalized data and List own no renderer dependency; renderer code consumes the same model and emits intentions through the shared read/state layer. A renderer import/layout failure leaves List, entry and source actions usable.'
decisions['DEC-008']['statement'] += ' Implement the common API client, state transitions, snapshot conflict handling and encoded stable-ID hash routes before consumer screens. Prove pure transitions early; actual Back/Forward, focus and browser response-race integration is tested after all consumers exist.'
decisions['DEC-010']['statement'] = 'Keep frontend source/build declarations in SKILLS-depo/ontology/explorer. Stage builds privately and publish a reviewed manifest and hashed runtime assets under explorer/assets, which the existing Template updater can ship without relaxing dist/build exclusions. Keep lock, BUILD.md, build identity and notices in the package; only manifest runtime members are HTTP-addressable. Source opens require selected record/reference identities and revalidated no-follow bounded bytes, never browser paths. Exact supported locator content or a clearly labeled bounded excerpt remains escaped and transient.'
decisions['DEC-011']['statement'] += ' The current initializer explicitly depends on legacy workbench assets; add an explicit current explorer capability/compatibility path and its completeness tests while preserving historical v9 receipt semantics. Neutral Template startup reports missing specialization honestly or is exercised through a documented disposable specialization, never a fabricated depot identity.'
plan['decisions'].append({
    'decision_id': 'DEC-013',
    'statement': 'Evaluate TRD D04 starting values: 224-260 CSS-pixel collapsible rail, 65-75-character reading line, roughly 320-400-pixel map details panel, around 16 CSS-pixel body size, and approximately 44-pixel primary controls as comfort targets. The applicable AA target criterion remains 24 by 24 CSS pixels with exceptions. Tune search debounce near 150-200 ms initially, excluded from warm-search timing. These are subordinate to readability, accessibility and reflow and are not measured or approved layouts.',
    'status': 'proposed', 'source_ids': ['SRC-001'],
    'authority_basis': 'Qualified implementation-plan proposal preserving TRD D04; exact canonical plan review remains required.',
    'decided_at': None,
})
for d in plan['decisions']:
    assert d['status'] == 'proposed' and d['decided_at'] is None

# Earlier boundary contracts incorporate the architecture contribution, without importing a second plan.
t = tasks['TASK-001']
t['action'] += ' Inspect current initializer edition/resource callers and updater shipping exclusions, including publication intents/recovery state relevant to selected canonical inputs.'
t['acceptance_criteria'].append('The local-file 347-record inventory and complete 412-record loaded inventory retain their different scopes; a canonical process identity is a lead, not evidence of ordered process steps.')
t = tasks['TASK-002']
t['action'] += ' Freeze compact response/source/session/cursor, common state/route and transaction-coordination contracts plus exact source/Template/root/initializer ownership maps before consumer implementation.'
t['requirement_ids'] = sorted(set(t['requirement_ids'] + atasks['TASK-002']['requirement_ids']))
t['target_artifacts'] += ['Verification/project-knowledge-explorer-first-release/change-map.json', 'Verification/project-knowledge-explorer-first-release/implementation-decisions.md']
t['risks'] += ['Stable pre/post file digests cannot establish a complete transaction when publication stopped after only some canonical replacements.', 'Existing dist/build exclusions and initializer v9 resource requirements constrain shipping; do not silently weaken either contract.']
t['acceptance_criteria'] += [
    'The contract includes selected-input unresolved-transaction detection, bounded coherent snapshot reads, precise source-reference identity, per-service and per-session cursor scope, independent List normalization and shared state/route ownership.',
    'The change map names source files, generated Template destinations, prospective exact root adoption and current initializer capability compatibility; each preserves its independent authority boundary.',
]
t['verification_steps'].append('Review existing publication intent/receipt/recovery and lock creation semantics, updater exclusions, strict configuration and current initializer resource inventories before approving the proposed contracts.')
t = tasks['TASK-004']
t['action'] = 'Implement a thin immutable snapshot adapter over load_project, complete pre/post selected-input digests and non-creating read-only observation of existing publication coordination; reject active or unresolved selected-input transactions, bound retries/cache lifetime and retire views after active readers finish.'
t['risks'] = ['Stable partial canonical commits are not current coherent snapshots; digest equality alone is insufficient.', 'Never introduce another coordination store or change writer/publication behavior to make reading convenient.']
t['acceptance_criteria'] += [
    'Interrupted multi-file publication with stable bytes is rejected until existing owner state establishes completion or recovery; malformed or unreadable relevant coordination returns a safe bounded diagnostic.',
    'Read-only coordination brackets materialization and covers missing-to-present lock races; ordinary browsing creates no lock, intent, receipt, repaired source hash or generated output.',
]
t['verification_steps'].append('Use deterministic barriers with actual publication/recovery helpers on disposable fixtures for active writes, interrupted partial commits with stable digests, missing-lock creation races, relevant versus unrelated transactions and continuous churn. Assert a complete version or specific bounded refusal, never a mixed version.')
t = tasks['TASK-005']
t['acceptance_criteria'][2] = 'Changing query, filters, direction, sort, project/root, snapshot, service instance or reading session invalidates a cursor; endpoint bounds never widen agent contracts.'
t['verification_steps'].append('Replay a valid cursor across two concurrent sessions, service restart, expired session and second selected project; only the exact live cursor scope may continue.')
t = tasks['TASK-010']
t['target_artifacts'] = [p.replace('explorer/dist/', 'explorer/assets/').replace('explorer/asset-manifest.json', 'explorer/assets/manifest.json') for p in t['target_artifacts']]
t['target_artifacts'] += ['SKILLS-depo/ontology/explorer/BUILD.md', 'SKILLS-depo/ontology/explorer/vite.config.ts']
t['action'] += ' Stage builds privately and publish complete manifest-owned explorer/assets output; this task establishes a minimal build/service fixture, and TASK-020 rebuilds and qualifies the complete later UI.'
t['acceptance_criteria'].append('Manifest, hashed runtime files and notices are included by the unchanged Template discovery rules; dist/build exclusions stay effective. The manifest names runtime assets only, while the lock and build instructions remain package metadata outside HTTP access.')
t['verification_steps'].append('Inspect the exact updater-discovered package list and manifest hashes; no requirement depends on excluded dist/build output or a live Node dev server.')

# Explicit launch is a separate bounded implementation task, required before browser consumers.
launch = deepcopy(atasks['TASK-012'])
launch['task_id'] = 'LAUNCH'
launch['phase_id'] = 'PHASE-002'
launch['dependencies'] = ['TASK-008', 'TASK-009', 'TASK-010']
tasks['LAUNCH'] = launch

# Shared foundations precede their screens. Later integration owns browser-level acceptance.
old_state = deepcopy(tasks['TASK-014'])
t = tasks['TASK-014']
t['title'] = 'Implement shared read client, state and safe route foundations'
t['action'] = 'Implement one versioned API client and explicit state transitions for identity, focus, search/filter, snapshot, expansion, source selection and preferences; encode stable-ID hash routes and transient session handling before screen consumers are connected.'
t['target_artifacts'] = ['SKILLS-depo/ontology/explorer/src/api.ts', 'SKILLS-depo/ontology/explorer/src/state.ts', 'SKILLS-depo/ontology/explorer/src/routes.ts', 'SKILLS-depo/ontology/explorer/src/preferences.ts', 'SKILLS-depo/ontology/explorer/tests/state.test.ts']
t['dependencies'] = ['TASK-002', 'TASK-005', 'TASK-006', 'TASK-007', 'TASK-009', 'TASK-010', 'LAUNCH']
t['acceptance_criteria'] = [
    'Pure state transitions preserve distinct identity/focus/query/filter/snapshot/expansion/source/preference fields and reject obsolete response sequences even when cancellation loses a race.',
    'Route codecs encode exact IDs and safe view state; bootstrap/session values and source bodies cannot enter copied links, history state or durable preference storage.',
    'Selection emits one navigation event, camera changes emit none, snapshot conflict retains old coherent context, and explicit refresh discards incompatible cursor/expansion state atomically.',
    'Only the shared read client initiates allowed reads; later screens and renderer consume state and emit intentions. Browser-level Back/Forward and focus integration are assigned to TASK-018.',
]
t['verification_steps'] = [
    'Run pure route/state tests for IDs, query/filter round trips, late entry-A-after-B responses, cancelled requests, snapshot conflict/refresh and preference reset.',
    'Test bootstrap consumption and safe desired-route restoration with a stubbed session exchange; inspect serialized route/preferences for forbidden secrets or source content.',
]
tasks['TASK-011']['dependencies'] = ['LAUNCH', 'TASK-014']
tasks['TASK-012']['dependencies'] = ['TASK-011', 'TASK-005', 'TASK-014']
tasks['TASK-013']['dependencies'] = ['TASK-011', 'TASK-006', 'TASK-007', 'TASK-014']

# The normalized model and List exist before the renderer; actual parity is verified after both are integrated.
t = tasks['TASK-017']
t['title'] = 'Implement normalized relationship data and independent List'
t['action'] = 'Build one normalized relationship model and semantic List over bounded reader data, preserving exact selection, filters, returned scope, identity/direction/qualifier/evidence and focus/more-connection intentions independently of the graph library.'
t['target_artifacts'] += ['SKILLS-depo/ontology/explorer/src/map/data.ts']
t['dependencies'] = ['TASK-006', 'TASK-013', 'TASK-014']
t['acceptance_criteria'] = [
    'The normalized model retains all returned node/relation IDs, canonical endpoints/predicates/direction, qualifiers, sources, warnings, filters and limits without inferring completeness.',
    'List entry/evidence/focus/expand actions work using keyboard and the shared read/state layer with the renderer module absent; no canvas/drag/hover/double-click is required.',
    'Selection and returned scope survive switching intentions; actual Map/List parity is a required integration gate in TASK-018 after the renderer is connected.',
]
t['verification_steps'] = [
    'Compare List and normalized API records against exact fixture identities, direction, qualifiers, sources and coverage; complete neighbor/source/focus/more/return using keyboard with the renderer unavailable.',
    'Verify List has no renderer import dependency and exposes meaningful result/selection announcements without hundreds of hidden controls. AT-16 and AT-29 actual Map/List switching is verified by TASK-018.',
]
tasks['TASK-016']['dependencies'] = ['TASK-006', 'TASK-014', 'TASK-017']
tasks['TASK-016']['acceptance_criteria'].append('Renderer reads the normalized model and emits intentions; it never initiates source/ontology reads. Legend and guidance retain: Select a term to read it. Use Focus here to explore its connections.')
t = tasks['TASK-018']
t['target_artifacts'] += ['SKILLS-depo/ontology/explorer/tests/navigation.spec.ts', 'SKILLS-depo/ontology/explorer/tests/map-list.spec.ts']
t['acceptance_criteria'] += old_state['acceptance_criteria']
t['acceptance_criteria'][1] = 'When no relationships are recorded in the returned view, say No relationships are recorded in this view; byte/time/traversal limits and incomplete data are distinguished from absence.'
t['acceptance_criteria'].append('AT-16 and AT-29 compare exact Map/List relation IDs, direction, qualifiers, sources, warnings, filters, selection and returned scope. Every substantive map action remains usable through List when graph import or rendering fails.')
t['verification_steps'] += old_state['verification_steps']
t['verification_steps'].append('Run real Map/List switching and keyboard-only neighbor/source/focus/more/return flows, including absent renderer module, layout timeout and truncated data; compare both views against the same normalized response.')

# Keep the evidence candidate's separate security/manual/nonmutation/performance/usability gates.
for task_id, ats in {
    'TASK-019': [24,25,26,27],
    'TASK-020': list(range(1,24)) + [28,29,32,34],
    'TASK-021': [29,30],
    'TASK-022': [33],
    'TASK-023': [36],
    'TASK-027': [31],
    'TASK-029': [35],
}.items():
    tasks[task_id]['verification_steps'].append('Record an individual observed result and exact evidence locator for each scenario: ' + ', '.join(f'AT-{i:02}' for i in ats) + '. Aggregate suite success does not replace per-scenario evidence.')
tasks['TASK-023']['verification_steps'].append('Record the first unsupported loader-capacity threshold with safe bounded failure; do not silently increase shared agent caps to force the stress fixture to load.')

t = tasks['TASK-025']
t['title'] = 'Update current delivery inventories and distribute neutral Template assets'
t['action'] += ' Add the current explorer capability/compatibility inventory without rewriting historical initializer editions, and finish shipping operational documentation before final cutover and provenance analysis.'
t['requirement_ids'] = sorted(set(t['requirement_ids'] + ['REQ-038', 'REQ-041', 'REQ-048']))
t['target_artifacts'] += [
    'SKILLS-depo/ontology/SKILL.md',
    'SKILLS-depo/ontology/references/explorer-operations.md',
    'SKILLS-depo/init-new-project/scripts/init_ontology_advanced.py',
    'SKILLS-depo/init-new-project/assets/static-capability-v1.json',
    'SPECS-depo/template-tests/test_template_contract.py',
]
t['acceptance_criteria'][0] = 'Source collection owns every reusable addition/removal; neutral Template contains runtime assets, lock/build identity/notices and neutral identity/purpose/category configuration without claiming it is a specialized running project.'
t['acceptance_criteria'] += [
    'Current explorer inventory handles legacy workbench asset coupling explicitly. Historical v9 receipt/resource meaning and earlier-edition snapshots remain intact; old assets are not deleted merely to satisfy new setup tests.',
    'All shipping assets survive existing dist/build exclusions, and missing/corrupt manifests fail package validation. Operational docs name actual build/launch/config/compatibility/error/rollback routes before cutover.',
]
t['verification_steps'] += [
    'Run affected current initializer and Template contract tests for current explorer completeness, historical receipt preservation, missing assets/notices and neutral optional-profile state.',
    'Reopen Template output and compare exact manifest digests; if watcher readiness is relied on, inspect a fresh successful check from its current PID.',
]
t = tasks['TASK-027']
t['acceptance_criteria'].append('Neutral Template has no invented depot identity: unspecialized startup reports configuration need, or a documented disposable specialization demonstrates reading. Record which behavior was observed; keep a different-namespace fixture with a shared label/different meaning for isolation.')
t['verification_steps'][0] = 'Run actual production launch/read/search/process/map/List/source checks in the root and documented neutral-Template context (explicit configuration-needed behavior or disposable specialization), plus the second namespace fixture.'
t = tasks['TASK-028']
t['risks'] += ['Legacy initializer resource requirements and trusted-authority callers must have verified current compatibility before active asset retirement.', 'Final cutover bytes require another exact owner-mediated Template update and separately authorized root adoption; a prior manifest does not authorize an expanded write set.']
t['verification_steps'].append('Verify the final current initializer package excludes active old authoring destinations while all historical receipt/edition compatibility tests and preserved trusted-helper callers remain valid.')
t = tasks['TASK-029']
t['acceptance_criteria'].append('Re-exercise final normal-launch read/process/Map/List/source/isolation and direct forbidden-write probes against the final installed build; any changed code/asset invalidates affected prior browser/manual/performance evidence and those cases are rerun.')
t['verification_steps'].append('Reopen final build/service/source/Template/root identity and re-run affected integrated production checks; compare preservation hashes after any last separately authorized provenance maintenance.')

# Source docs settle before provenance. Handoff evidence precedes the final audit/preservation observation.
t = tasks['TASK-032']
t['action'] = 'Assemble local release evidence and safe final-production visuals, linking the already-settled operational build/launch/config/compatibility/maintenance/rollback documentation and recording all actual tested limits.'
t['target_artifacts'] = [p for p in t['target_artifacts'] if p != 'SKILLS-depo/ontology/references/explorer-operations.md']
t['dependencies'] = ['TASK-024', 'TASK-027', 'TASK-028', 'TASK-029', 'TASK-030']
t['acceptance_criteria'].append('This task creates only local release evidence. If a shipping source/document correction is needed, return it to its owner and refresh affected distribution/provenance/regression evidence before final audit.')
tasks['TASK-031']['dependencies'] = unique(tasks['TASK-031']['dependencies'] + ['TASK-032'])
tasks['TASK-031']['acceptance_criteria'].append('Final affirmative preservation observations occur strictly after the current implementation and handoff evidence; each protected path and authorized exception is explicit. No source/document modification is hidden after this closing audit.')

# Assign deterministic final IDs in executable order before any managed plan has been created.
order = [f'TASK-{i:03}' for i in range(1,11)] + ['LAUNCH','TASK-014','TASK-011','TASK-012','TASK-013','TASK-015','TASK-017','TASK-016'] + [f'TASK-{i:03}' for i in range(18,31)] + ['TASK-032','TASK-031']
assert len(order) == len(tasks) == 33
mapping = {old: f'TASK-{i:03}' for i,old in enumerate(order,1)}
plan['tasks'] = [tasks[old] for old in order]
for phase in plan['phases']:
    phase['task_ids'] = [t['task_id'] for t in plan['tasks'] if t['phase_id'] == phase['phase_id']]
    phase['scope'] = [t['title'] for t in plan['tasks'] if t['phase_id'] == phase['phase_id']]
plan['phases'][1]['exit_criteria'] = ['Snapshot/data/service/session/assets and explicit launch/health contracts pass focused tests; minimal production build can support later UI consumers without authoring or optional backend prerequisites.']
plan['phases'][2]['entry_conditions'] = ['Phase 2 read/service/launch contracts pass; implement the shared API/state/route foundation before attaching screen consumers.']
plan['phases'][3]['entry_conditions'] = ['Phase 3 reader and route state are available; implement normalized List before renderer and test actual Map/List parity after integration.']
plan['phases'][7]['exit_criteria'] = ['Local handoff evidence and final production visuals are assembled before the closing 49-REQ/36-AT audit and final preservation observations; missing mandatory evidence prevents completion.']

def remap(value):
    if isinstance(value,str):
        return re.sub(r'TASK-\d{3}|\bLAUNCH\b', lambda m:mapping.get(m.group(),m.group()), value)
    if isinstance(value,list): return [remap(x) for x in value]
    if isinstance(value,dict): return {k:remap(v) for k,v in value.items()}
    return value
plan = remap(plan)
plan['coverage']['requirement_to_task'] = [
    {'requirement_id': r['requirement_id'], 'task_ids': [t['task_id'] for t in plan['tasks'] if r['requirement_id'] in t['requirement_ids']], 'disposition': None}
    for r in plan['requirements']
]
for t in plan['tasks']:
    for field in ['dependencies','target_artifacts','requirement_ids','verification_steps']:
        t[field] = unique(t[field])

proposal = OUT / 'proposal.json'
proposal.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + '\n')
assert proposal.stat().st_size < 250000, proposal.stat().st_size

dispositions = {
    'retained': [
        'CAND_EVIDENCE_V1 supplies the complete 49-requirement/119-acceptance inventory, eight-phase release flow, granular security/offline/manual/nonmutation/performance/usability gates, separate Template/adoption/cutover/provenance work and honest delivery criteria.',
        'CAND_ARCH_V1 supplies explicit shipping inventories and explorer/assets placement, updater dist/build exclusions, current initializer legacy-asset compatibility, partial-transaction snapshot refusal, precise source references, separate launch/health work, independent normalized List and final evidence-before-audit ordering.',
        'Both candidates retain canonical semantics, semantic=False only for ordinary reader search, compact bounded projections, exact graph/source identity, thin Python read service, proposed TypeScript/Vite/Cytoscape choice, explicit action authority and all first-release exclusions.',
    ],
    'omitted': [
        'CAND_EVIDENCE_V1 explorer/dist shipping target is replaced with explorer/assets/manifest.json and hashed runtime members because current Template discovery excludes dist/build. Build scratch remains private; exclusions are not loosened.',
        'CAND_EVIDENCE_V1 late shared-state implementation and renderer-before-List dependency are replaced with foundation-first sequencing and renderer-independent List. Actual browser history and Map/List parity are retained in later integration gates.',
        'CAND_ARCH_V1 combines accessibility/usability and security/nonmutation tasks; the proposal instead retains the evidence candidate separate bounded tasks so each required evidence gate has a clear owner. No required check is omitted.',
        'CAND_ARCH_V1 observation-time decided_at for source approval is not adopted. All synthesized implementation decisions remain proposed with null decision timestamps; approved TRD revision/lifecycle/digest is retained as source provenance.',
        'Future production/manual/performance/dependency/content observations are not represented as missing planning scope. Their unperformed status remains explicit in baseline limitations, proposed selection protocols and scheduled tasks under TRD D06/D08. No result or absent-source claim is invented.',
    ],
    'differences': {
        'complementary': 'Architecture shipping/transaction/initializer findings are incorporated into the evidence candidate complete acceptance flow; the result is one 33-task draft with a dedicated launcher and common foundations before consumers.',
        'terminology': 'Service instance means one Python launch; reading session means one authenticated bootstrap exchange. Cursors bind to both, plus selected root/project/snapshot/query scope. The normalized relationship model drives both Map and List; List is independent of renderer availability. Module and endpoint names remain proposed.',
        'scope': 'Both cover the same full release. Eight evidence-oriented phases are retained, with granular manual/security/performance gates and explicit current initializer compatibility from architecture. Root adoption, retirement/deletion, installations, provenance maintenance and external actions remain separate exact authority gates.',
        'evidence': '347 records describes seven selected project/binding files; 412 describes the fully loaded canonical project including imports. Both are retained with their own locators/times. The process Capability is a source-inventory lead, not proof of sequence. Direct load is the only observed runtime-like planning result; future product verification remains unperformed.',
        'exclusive': 'No unresolved mutually exclusive core commitment remains. The unshippable dist target, digest-only partial-transaction acceptance, renderer-dependent List order and invented approval time are explicitly rejected in favor of the current updater, transaction and source-fidelity constraints. The candidate shared goals coexist under one bounded design.',
    },
    'assumptions': [
        'No unconfirmed product fact is adopted as an assumption. Exact dependency versions, package provisioning, source-content classification and target-environment observations remain future constrained work; a material incompatibility returns the affected proposed design to review.',
        'Qualified timing, graph size, fixture scales and D04 layout/debounce values remain evaluation targets rather than guaranteed or measured behavior.',
    ],
    'interfaces': [
        'Dedicated Python read/session dispatcher with exact authenticated context/search/entry/relationships/neighborhood/source operations, narrow health and server-selected root; no generic execution or browser authority fields.',
        'Non-creating observation of existing publication lock/intent/receipt/recovery state brackets immutable snapshot materialization and refuses active/unresolved selected-input transactions; stable pre/post digests alone cannot prove coherence.',
        'HMAC cursors bind service instance, reading session, root/project, snapshot, normalized filters/query/direction/sort and key; stale context or restart invalidates continuation.',
        'Selected identity plus registered snapshot reference governs source opens; fresh bounded no-follow bytes, exact verified locator or labeled excerpt, and recorded/current version distinction preserve evidence.',
        'One shared API/state/route layer initiates reads; independent normalized relationship model/List precede renderer adapter. Shipping assets use explorer/assets; current initializer capability compatibility precedes legacy active-asset retirement.',
    ],
    'requirements': [
        'All 49 source requirement titles/outcomes, 119 exact acceptance sentences and requirement dependency lists remain unchanged; all AT-01 through AT-36 have explicit task verification mappings and no requirement is dispositioned away.',
        'Forward/reverse source, requirement and task coverage is regenerated for the final task IDs; D01-D08 boundaries and all negative requirements remain represented.',
    ],
    'risks': [
        'Publication interruption/lock races, oversized projections and cross-session/cross-project cursor replay have explicit adversarial fixture gates.',
        'Updater exclusions, historical initializer compatibility, watcher coordination and mixed installed/source root copies constrain distribution and retirement; exact manifests and preservation checks remain mandatory.',
        'Graph meaning, List accessibility, source freshness, manual environment availability and measured capacity remain explicit production acceptance risks; no synthetic/static evidence is promoted to live acceptance.',
    ],
    'verification': [
        'Validate with the installed plan helper normalization, ephemeral identity/history preparation, structure and local source snapshot checks entirely in memory; no create or managed write is called.',
        'Compare final title/outcome/acceptance/dependency arrays to exact TRD bytes, assert all36 explicit task AT references, planned-only tasks and empty evidence, verify executable ordering and common foundation dependencies, validate dispositions shape and current input digests.',
    ],
    'unresolved': [],
}
(OUT/'dispositions.json').write_text(json.dumps(dispositions, indent=2) + '\n')

spec = importlib.util.spec_from_file_location('plan_state', ROOT/'.agents/skills/to-implementation-plan/scripts/plan_state.py')
module = importlib.util.module_from_spec(spec)
sys.modules['plan_state'] = module
spec.loader.exec_module(module)
ctx = module.resolve_context(str(ROOT), 'Implementation_Plans')
normalized = module.normalize_plan_input(plan, ctx)
module.ensure_initial_lifecycle_state(normalized)
directory = module._assign_new_identity(normalized, set())
normalized['history'] = [module.history_entry(normalized, revision=1, event_time=normalized['created_at'], action_id='TO-IP-001', affected_ids=module.stable_record_ids(normalized), status_before=None, status_after='draft', summary='In-memory synthesis proposal validation only.', authority_basis='Bounded senior proposal; no canonical creation is invoked.')]
module.recompute_phase_statuses(normalized)
module.refresh_validation(normalized, normalized['updated_at'])
errors = module.validate_plan_structure(normalized, ctx, directory_name=directory)
module.ensure_structurally_valid(normalized, ctx, directory_name=directory, input_context=True, check_snapshot=True)
source = ROOT/'TRDs/trd_project-knowledge-explorer-full-first-release_2026-09-19.md'
blocks = re.findall(r'^### (REQ-\d{3}) - ([^\n]+)\n(.*?)(?=^### REQ-|^## Decisions)', source.read_text(), re.M|re.S)
acceptance_count = 0
for rid,title,body in blocks:
    r = next(x for x in plan['requirements'] if x['requirement_id']==rid)
    criteria = re.findall(r'^- Acceptance: (.+)$',body,re.M)
    assert r['title']==title and r['outcome']==re.search(r'^- Requirement: (.+)$',body,re.M).group(1)
    assert r['acceptance_criteria']==criteria
    assert r['dependencies']==re.findall(r'REQ-\d{3}',re.search(r'^- Depends on: (.+)$',body,re.M).group(1))
    acceptance_count += len(criteria)
ats = {f'AT-{i:02}' for i in range(1,37)}
task_ats = set(re.findall(r'AT-\d{2}',json.dumps(plan['tasks'])))
verification_ats = set(re.findall(r'AT-\d{2}',json.dumps([t['verification_steps'] for t in plan['tasks']])))
assert len(blocks)==49 and acceptance_count==119 and task_ats==verification_ats==ats
assert all(t['status']=='planned' and t['evidence']==[] for t in plan['tasks'])
assert all(r['status']=='active' and r['evidence']==[] for r in plan['requirements'])
assert all(d['decided_at'] is None and d['status']=='proposed' for d in plan['decisions'])
assert not errors
by_id = {t['task_id']:t for t in plan['tasks']}
positions = {t['task_id']:i for i,t in enumerate(plan['tasks'])}
assert all(positions[dep]<positions[t['task_id']] for t in plan['tasks'] for dep in t['dependencies'])
assert mapping['TASK-014'] in by_id[mapping['TASK-011']]['dependencies']
assert mapping['TASK-017'] in by_id[mapping['TASK-016']]['dependencies']
assert mapping['TASK-016'] not in by_id[mapping['TASK-017']]['dependencies']
assert plan['tasks'][-1]['task_id']==mapping['TASK-031']
assert set(dispositions)=={'retained','omitted','differences','assumptions','interfaces','requirements','risks','verification','unresolved'}
assert set(dispositions['differences'])=={'complementary','terminology','scope','evidence','exclusive'}
assert all(isinstance(v,str) and v for v in dispositions['differences'].values())
assert all(isinstance(v,list) and all(isinstance(x,str) for x in v) for k,v in dispositions.items() if k!='differences')

hash_file = lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
task_json = json.loads((ORCH.parent.parent/'task.json').read_text())
assignment = task_json['orchestration']['assignments']['senior']
context_matches = []
for c in assignment['context']:
    assert hash_file(ROOT/c['path'])==c['sha256']
    context_matches.append(c['path'])
receipt = {
    'method': 'Installed helper normalization, ephemeral in-memory identity/history/phase/structure/source-snapshot checks. No canonical create/write, product tests, service or browser invocation.',
    'highest_verification_level':'static_checks_passed',
    'structural_errors': errors,
    'quality_findings': module.quality_findings(normalized),
    'counts': {'requirements':49,'exact_acceptance_sentences':119,'phases':len(plan['phases']),'tasks':len(plan['tasks']),'sources':len(plan['sources']),'proposed_decisions':len(plan['decisions'])},
    'all_36_ATs_in_explicit_verification':sorted(verification_ats),
    'source_sha256':hash_file(source),
    'proposal_sha256':hash_file(proposal),
    'proposal_bytes':proposal.stat().st_size,
    'dispositions_sha256':hash_file(OUT/'dispositions.json'),
    'input_context_digest_matches':context_matches,
    'canonical_mutation':False,
    'product_behavior_verified':False,
    'ordering':'All task dependencies precede consumers; shared state before screens; independent List before renderer; final audit after handoff evidence.',
    'unresolved_synthesis_conflicts':[],
    'old_evidence_to_final_task_ids':mapping,
}
(OUT/'static-validation.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({k:receipt[k] for k in ['highest_verification_level','structural_errors','counts','proposal_sha256','proposal_bytes','dispositions_sha256','ordering']}))
