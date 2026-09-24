"""Reproduce the initial source-bound coverage map; never record runtime passes."""
from pathlib import Path
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[5]
PLAN = 'Implementation_Plans/Plan_project-knowledge-explorer-full-first-release_2026-09-20_9B9964BA/plan.json'
TRD = 'TRDs/trd_project-knowledge-explorer-full-first-release_2026-09-19.md'
CONTRACT = 'SKILLS-depo/ontology/references/explorer-contract.md'
SCHEMA = 'ONTOLOGY-depo/schema/explorer-v1.json'
DEST = 'Verification/project-knowledge-explorer-first-release/acceptance-matrix.json'

# Each scenario is a reusable substrate or a future integration protocol. The
# evidence fields below deliberately contain no pass claim for an unbuilt reader.
SCENARIOS = [
 ('FX-NEUTRAL','Neutral/import-only reading','make_neutral_project', 'Only locked core vocabulary; specialized empty local corpus and explicitly unspecialized refusal variant.'),
 ('FX-SMALL','Small canonical corpus','make_explorer_project(scale="small")','50 local entries, 100 local relations, separate binding and imported counts; deterministic structured graph.'),
 ('FX-REPRESENTATIVE','Representative target corpus','make_explorer_project(scale="representative")','1000 local entries / 5000 relations; requested workload, with actual canonical load and predicted reader admission reported separately.'),
 ('FX-STRESS','Stress target corpus','make_explorer_project(scale="stress")','5000 local entries / 50000 relations, partitioned under unchanged per-file limits; bounded refusal is an acceptable measured outcome, not rendering everything.'),
 ('FX-BOUNDARY','Near reference-admission boundary','make_explorer_project(path,entries=N,relationships=0,pathological=False)','Generate adjacent corpora at 1024 and 1025 distinct owner/binding/reference tuples after measuring imported support; do not change limits.'),
 ('FX-ISOLATION','Second namespace and same label','make_explorer_project(identity="explorer-beta")','Alignment shares its label across namespaces but retains different definitions, IDs, sources, root identity and future sessions/preferences/routes.'),
 ('FX-DISCOVERY','Exact identity, label, alias and lexical discovery','FX-SMALL','Alignment duplicate labels and Orientation aliases have explicit distinctions. FixtureTaskManager tests CamelCase normalization; core Task retains case-sensitive ID.'),
 ('FX-FILTERS','Lifecycle/category multi-page selection','FX-SMALL','Approved/draft/deprecated and asserted/derived/inferred/external entries, long fields and categories; filters must apply before pagination.'),
 ('FX-LONG','Lossless long data and consuming/deferred markers','FX-SMALL','5000-CJK-character label, Unicode definition, long qualified edge and 130 exact source references; expected service byte/field limits remain future evidence.'),
 ('FX-GRAPH','Directed parallel edges, self-loop, cycle and hub','FX-SMALL','Distinct documents/supports predicates between same endpoints, one self-loop, directed cycle, explicit process edges and a high-degree focus.'),
 ('FX-BROKEN','Rejected broken canonical inputs','mutate_fixture','broken_reference -> dangling_target; duplicate_identity -> duplicate_id; unmodeled_ambiguity -> label_ambiguity; unsupported_property -> unsupported_profile; invalid_qualifier -> invalid_qualifiers.'),
 ('FX-PROCESS','Reviewed ordered and unsupported order','FX-SMALL','Four exact configured process IDs: numbered ordered text, no designation, partial precedence without numbered order, and selected order whose source can become stale/missing. No inferred global sequence.'),
 ('FX-SOURCES','Exact evidence and freshness','FX-SMALL + mutate_fixture','Bounded line/range, unique section, repeated heading excerpt, JSON pointer, full-tuple binding distinction, stale/missing/unchanged-mtime bytes.'),
 ('FX-INERT','Markup and instruction-like data','FX-SMALL','Script/image/javascript-link text is inert source content. No external fetch or instruction execution is authorized.'),
 ('FX-CURSORS','Continuation scope and progression protocol','protocol-cases.json','Generate cursors in ephemeral test memory, bind exact Q separately from normalized Q, filters, limits, IDs, roots, snapshots, service, session and monotonic expiry; tamper/replay errors never represented as observed here.'),
 ('FX-SNAPSHOTS','Coherence and code-epoch protocol','protocol-cases.json','Use deterministic barriers around both actual publication families, absent/present lock races, unresolved/retained/superseded journals, source-only mismatch, same-mtime bytes and loaded-helper/schema/asset drift.'),
 ('FX-SESSIONS','Bootstrap, expiry and local service isolation','protocol-cases.json','Create credentials only at runtime in memory; test one use, removal from history, same-origin session resume, expiry/service stop, cross-service rejection and safe route retention.'),
 ('FX-PATHS','Registered source and manifested asset denial','protocol-cases.json','Encoded traversal, absolute/unselected path and symlink/hardlink replacements; future tests use temporary roots and assert safe denial without disclosure.'),
 ('FX-WRITES','Direct forbidden dispatch and safe errors','protocol-cases.json','Probe exact forbidden operations with protected before/after inventory and fail-on-call hooks; browser omissions alone cannot pass.'),
 ('FX-RESOURCES','Request/cache/worker limits and cancellation','protocol-cases.json','Measure exact byte/item/visit/scan/deadline/socket/queue/RSS/lease limits; distinguish lower bounds, unknown totals and local display limits. No unsafe retry or changed caps.'),
 ('FX-CLIENT','State/routes/history and stale-response protocol','protocol-cases.json','Late A after B, same normalized/different exact query, atomic refresh, root-scoped preference reset, bounded history/source/cache and graph cleanup.'),
 ('FX-LIST','Independent List and renderer failure','protocol-cases.json','Identical normalized relation IDs/direction/qualifiers/scope/warnings; throwing renderer import and layout timeout retain list, evidence and keyboard actions.'),
 ('FX-OFFLINE','Actual production build and CSP','protocol-cases.json','Later installed production assets under denied external network; no dev server or screenshots substitute for real package/HTTP evidence.'),
 ('FX-ACCESSIBILITY','Manual and automated accessibility protocol','protocol-cases.json','Actual VoiceOver/Safari versions and keyboard/focus/320px/zoom/themes/reduced-motion; Windows screen reader/browser when available, otherwise explicit limitation.'),
 ('FX-PRESERVATION','Complete protected-state comparison','protocol-cases.json','Ontology, source/config, memory, generated outputs, proposals and receipts plus exact startup artifact exceptions; no blanket .sys4ai exemption.'),
 ('FX-DISTRIBUTION','Source/Template/root/initializer ownership','protocol-cases.json','Exact manifest, neutral context, independent root adoption, historical editions and no recursive products. Recipes outside HTTP assets; future bundle must be inspected.'),
 ('FX-REGRESSION','Agent and rollback preservation','protocol-cases.json','Independent existing retrieval/publication/recovery/Template checks, separate owner provenance work and code rollback preserving newer knowledge/history.'),
 ('FX-PERFORMANCE','Repeated production measurement protocol','protocol-cases.json','Repeated median/p95, hardware/browser/build, cold/warm/debounce exclusions, limits/memory/first unsupported threshold, source validation separately and compressed bundle baseline.'),
 ('FX-PEOPLE','Knowledge comprehension walkthrough','protocol-cases.json','Unfamiliar participant or explicitly owner-only walkthrough; known term target roughly30s, wrong turns/mistaken relation meanings/help/wording without statistical generalization.'),
 ('FX-HANDOFF','Final production visuals and audit','protocol-cases.json','Nine actual screens, safe local evidence, final source/build/installed versions and preservation after last changes; no credentials or unsupported pass claim.'),
 ('FX-LICENSES','Dependency provenance and independent code','protocol-cases.json','Exact direct/transitive lock/notices, separate build tool/runtime distinction, no copied Logseq implementation or implicit installs.')]

REQ_SCENARIOS = {
1:['OFFLINE','CLIENT','WRITES'],2:['NEUTRAL','SMALL','REGRESSION'],3:['FILTERS','SOURCES'],4:['NEUTRAL','DISCOVERY'],5:['DISCOVERY','OFFLINE'],6:['DISCOVERY','ISOLATION'],7:['FILTERS','CURSORS','LONG'],8:['SMALL','LONG'],9:['GRAPH','LONG','SOURCES'],10:['PROCESS','SOURCES'],11:['SOURCES','PATHS','INERT'],12:['CLIENT','SESSIONS'],13:['CLIENT','ISOLATION'],14:['GRAPH','RESOURCES'],15:['GRAPH','CLIENT','LIST'],16:['GRAPH','BROKEN'],17:['GRAPH','LIST','ACCESSIBILITY'],18:['LONG','RESOURCES','STRESS'],19:['LIST','ACCESSIBILITY'],20:['BROKEN','SESSIONS','LIST'],21:['SNAPSHOTS'],22:['SNAPSHOTS','RESOURCES'],23:['SMALL','CURSORS','RESOURCES'],24:['CURSORS'],25:['CLIENT','LIST','RESOURCES'],26:['PRESERVATION','WRITES'],27:['NEUTRAL','PRESERVATION','OFFLINE'],28:['OFFLINE','LICENSES'],29:['SESSIONS','ISOLATION','PATHS'],30:['SESSIONS','CLIENT'],31:['WRITES','REGRESSION'],32:['PATHS','INERT','OFFLINE'],33:['RESOURCES','LONG'],34:['ACCESSIBILITY','LIST'],35:['ACCESSIBILITY','CLIENT'],36:['ACCESSIBILITY'],37:['DISTRIBUTION','NEUTRAL'],38:['DISTRIBUTION','ISOLATION'],39:['SESSIONS','OFFLINE','REGRESSION'],40:['REGRESSION','DISTRIBUTION'],41:['REGRESSION','PRESERVATION'],42:['SMALL','PROCESS','PRESERVATION'],43:['SMALL','OFFLINE','HANDOFF'],44:['ACCESSIBILITY'],45:['PERFORMANCE','BOUNDARY','REPRESENTATIVE','STRESS'],46:['SMALL','REPRESENTATIVE','STRESS','LONG','GRAPH','BROKEN','BOUNDARY'],47:['PEOPLE','PROCESS','LIST'],48:['HANDOFF','PRESERVATION'],49:['LICENSES','OFFLINE']}


def ref(path):
    return {'path': path, 'sha256': hashlib.sha256((ROOT/path).read_bytes()).hexdigest()}


def build():
    plan = json.loads((ROOT/PLAN).read_text())
    text = (ROOT/TRD).read_text()
    coverage = {r['requirement_id']: r['task_ids'] for r in plan['coverage']['requirement_to_task']}
    tasks = {t['task_id']: t for t in plan['tasks']}
    rows=[]
    for match in re.finditer(r'^### (REQ-\d{3}) - ([^\n]+)\n(.*?)(?=^### REQ-|^## Decisions)', text, re.M|re.S):
        rid,title,body=match.groups()
        criteria=re.findall(r'^- Acceptance: (.+)$',body,re.M)
        rows.append({'requirement_id':rid,'title':title,'requirement_verbatim':re.search(r'^- Requirement: (.+)$',body,re.M).group(1),
                     'acceptance_criteria_verbatim':criteria,'source_verbatim':re.search(r'^- Source: (.+)$',body,re.M).group(1),
                     'depends_on_verbatim':re.search(r'^- Depends on: (.+)$',body,re.M).group(1),
                     'source_locator':f'{TRD}#'+rid,'scenario_ids':['FX-'+x for x in REQ_SCENARIOS[int(rid[-3:])]],
                     'plan_task_ids':coverage[rid],'evidence_owner_task_ids':coverage[rid],
                     'status':'planned_coverage_only','runtime_evidence':[]})
    ats=[]
    for i in range(1,37):
        aid=f'AT-{i:02d}'
        related=[r for r in rows if any(re.search(r'\b'+aid+r':',s) for s in r['acceptance_criteria_verbatim'])]
        assert related,aid
        sentences=[{'requirement_id':r['requirement_id'],'text':s} for r in related for s in r['acceptance_criteria_verbatim'] if re.search(r'\b'+aid+r':',s)]
        linked=sorted({t for r in related for t in r['plan_task_ids']})
        owners=[t['task_id'] for t in tasks.values() if any(aid in s and ('individual observed result' in s or 'Record an individual' in s) for s in t['verification_steps'])]
        ats.append({'acceptance_id':aid,'trd_acceptance_source_verbatim':sentences,'requirement_ids':[r['requirement_id'] for r in related],
                    'scenario_ids':sorted({s for r in related for s in r['scenario_ids']}), 'plan_task_ids':linked,
                    'individual_result_owner_task_ids':owners, 'status':'not_run','evidence':[]})
    owner_rows=[]
    for tid,t in tasks.items():
        owner_rows.append({k:t[k] for k in ['task_id','phase_id','title','requirement_ids','dependencies','target_artifacts','acceptance_criteria','verification_steps','risks']} |
                          {'evidence_owner':'The manager-assigned executor of '+tid,'status':'planned_coverage_only',
                           'scenario_ids':sorted({s for r in rows if tid in r['plan_task_ids'] for s in r['scenario_ids']})})
    value={'schema_version':1,'kind':'frozen_initial_acceptance_coverage','source_plan_id':plan['plan_id'],'source_plan_revision':plan['revision'],
           'source_trd_id':'TRD-20260919-B6D51106','source_trd_revision':2,'sources':[ref(p) for p in (PLAN,TRD,CONTRACT,SCHEMA)],
           'qualification':'Coverage and synthetic fixture validation only. No AT runtime/browser/manual/performance result is established here. Later outcomes belong in separate current release evidence; preserve this initial map.',
           'evidence_owner_definition':'Task IDs identify exact plan execution responsibilities and target evidence artifacts, not people, permissions or completed assignments.',
           'global_qualifications':[
               'All 49 requirement statements and acceptance sentences are copied verbatim from TRD revision2; qualified source budgets, proposed targets and source gaps remain unchanged.',
               'Small/representative/stress are approximate proposed workload targets. Counts distinguish local entries, local relations, bindings, imported and loaded records. Reader admission and canonical loading are separate.',
               'Manual actual macOS VoiceOver/Safari walkthrough and precise versions remain required. Windows screen-reader/browser is added when available; otherwise record untested limitation.',
               'People walkthrough records unfamiliar participants or owner-only availability. Roughly30 seconds is a proposed known-term task target, never a measured/universal guarantee.',
               'Cold readable about2s; warm search p95 <=200ms excluding intentional debounce; warm entry p95 <=250ms; focused25/50 graph about1.5s; selection <=100ms. Actual repeated median/p95 and failures required.',
               'Transaction, source identity/freshness, nonmutation, production bundle/offline/CSP, accessibility, distribution, final cutover and rollback require direct current evidence. Fixture schema passes cannot substitute.',
               'Source mappings distinguish exact observed support, missing designation, partial precedence, stale/unavailable source and unexamined coverage. Do not infer global sequence or absence.',
               'Only exact documented startup/session files and harmless preferences are exempt from final before/after preservation; .sys4ai is not generally exempt.',
               'Fixtures may be installed as test resources by existing source distribution. They must never enter the production asset manifest or HTTP allowlist; that later build does not exist at this fixture checkpoint.'
           ], 'scenario_catalog':[{'scenario_id':i,'title':t,'fixture_or_protocol':b,'description':d,'status':'substrate_or_protocol_only'} for i,t,b,d in SCENARIOS],
           'requirements':rows,'acceptance_scenarios':ats,'plan_tasks':owner_rows,
           'phases':[{k:v for k,v in p.items() if k in ('phase_id','title','task_ids','dependencies')} for p in plan['phases']]}
    assert len(rows)==49 and len(ats)==36 and len(owner_rows)==33 and len(value['phases'])==8
    assert all(a['individual_result_owner_task_ids'] for a in ats)
    output=(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode()
    assert len(output)<=250000,len(output)
    return output

if __name__=='__main__':
    (ROOT/DEST).write_bytes(build())
    print(DEST)
