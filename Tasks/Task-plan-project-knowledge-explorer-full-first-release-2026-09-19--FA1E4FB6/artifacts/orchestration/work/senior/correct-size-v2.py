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
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
v1_files = ['proposal.json', 'dispositions.json', 'static-validation.json', 'README.md', 'synthesize.py']
v1_hashes = {name: sha(OUT/name) for name in v1_files}
assert v1_hashes['proposal.json'] == '68a98087547e42a964ab95f9fb05b101c7e141dd381e536856d51f52aadfb103'
task = json.loads((ORCH.parent.parent/'task.json').read_text())
assignment = task['orchestration']['assignments']['senior']
assert assignment['state'] == 'active'
assert len(assignment['context']) == 11
assert assignment['input_receipt']['tool'] == 'collaboration.send_message'
for c in assignment['context']:
    assert sha(ROOT/c['path']) == c['sha256']
assert assignment['context'][-1]['sha256'] == 'fcaa0e787c8723e7ac2df33419ac3970e746a61f098dbccc741003a7afa0a7c4'
original = json.loads((OUT/'proposal.json').read_text())
plan = deepcopy(original)

# These concise obligations replace duplicated acceptance prose only.
# Exact outcomes, acceptance sentences, dependency lists and full scope remain verbatim.
negative = [
    'No browser authoring, administration, execution or hidden Advanced mode.',
    'No second authority, invented content, publication or wiki-derived truth.',
    'Do not conflate lifecycle, fact kind, freshness, truth or action authority.',
    'Do not invent starting identities or derive hierarchy from node degree.',
    'No AI fallback or generated meaning; preserve agent search defaults.',
    'No guessed categories, merged identities or silent ambiguity resolution.',
    'No filtering after paging, lost matches or false absence/completeness.',
    'No paraphrase, invented missing fields, edit or run actions.',
    'Do not merge relations, reverse meaning or hide conditional qualifiers.',
    'No invented process facts/order, execution or automatic flow generation.',
    'No false exact-excerpt claim, source execution, fetch or hash repair.',
    'No credential-bearing links or camera-generated history spam.',
    'No knowledge/source-body persistence or administration via preferences.',
    'No whole-project fetch or change to existing agent traversal/byte limits.',
    'Selection must not refocus; no unbounded or gesture-only essential action.',
    'No merged IDs, inferred assertions or invented labels for broken references.',
    'No semantic layout claims, continuous motion or full relayout on selection.',
    'No invented totals, hidden omissions or unbounded browser accumulation.',
    'No substantive Map-only information or canvas-only essential action.',
    'No false global absence or loss of unrelated context after failure.',
    'No mixed snapshots or silent substitution of new input versions.',
    'No stale-as-current cache authority or unbounded cache lifetime.',
    'No generic execution, oversized output or unsupported completeness claims.',
    'No client-trusted or wrong-scope continuation; preserve stable identity order.',
    'No obsolete response application, renderer reads or hidden graph resources.',
    'No browsing mutations, implicit builds/repairs or broad runtime exemptions.',
    'No memory browsing/mutation, implicit wiki rebuild or wiki prerequisite.',
    'No implicit installs/builds, remote assets or optional-runtime prerequisite.',
    'No non-loopback exposure, browser-selected root or cross-project authority.',
    'No bootstrap/session secrets in routes, copies, logs or retained evidence.',
    'No browser route to any write, execute, function or authoring dispatcher.',
    'No arbitrary paths, unsafe source rendering or broad CSP workaround.',
    'No unbounded service work or sensitive/raw exception diagnostics.',
    'No inaccessible essential actions or semantics conveyed by color alone.',
    'No focus traps, context loss or layout-frame announcement noise.',
    'No narrow/zoom/theme/motion exception for surrounding reading and controls.',
    'No direct Template source edits, private runtime shipping or bulk propagation.',
    'No inferred root adoption, recursive product update or project leakage.',
    'No false health readiness, implicit startup or accepted legacy grant arguments.',
    'No premature cutover, weakened agent operations or erased historical records.',
    'No browsing provenance repair or rollback of newer valid knowledge/history.',
    'No invented baseline/content absence or overwrite of unrelated edits.',
    'No acceptance claim from plans, screenshots or unit evidence alone.',
    'No unqualified accessibility claim from scanners or untested environments.',
    'No measured-guarantee claim or weakened integrity to meet timing targets.',
    'No assumed loader capacity or uniform-random-only workload coverage.',
    'No statistical usability claim or unresolved high-impact misunderstanding.',
    'No mockup-only proof, credentials or unsupported delivery claims.',
    'No Logseq code copying, implicit dependency or second production authority.',
]
assert len(negative) == len(plan['requirements']) == 49
for req, text in zip(plan['requirements'], negative):
    req['negative_requirements'] = [text]

# Only the negative summary field may differ; complete requirements remain protected.
for before, after in zip(original['requirements'], plan['requirements']):
    for key in before:
        if key != 'negative_requirements':
            assert before[key] == after[key], (before['requirement_id'], key)
for key in original:
    if key != 'requirements':
        assert original[key] == plan[key], key

spec = importlib.util.spec_from_file_location('plan_state', ROOT/'.agents/skills/to-implementation-plan/scripts/plan_state.py')
m = importlib.util.module_from_spec(spec)
sys.modules['plan_state'] = m
spec.loader.exec_module(m)
ctx = m.resolve_context(str(ROOT), 'Implementation_Plans')
n = m.normalize_plan_input(plan, ctx)
m.ensure_initial_lifecycle_state(n)
directory = m._assign_new_identity(n, set())
n['history'] = [m.history_entry(n, revision=1, event_time=n['created_at'], action_id='TO-IP-001', affected_ids=m.stable_record_ids(n), status_before=None, status_after='draft', summary='In-memory validation of complete senior synthesis with bounded canonical evidence size.', authority_basis='The manager reactivated senior through assignment.inputs PKE_INPUTS_SENIOR_V2 and followup_task for exact size correction only; no managed creation is invoked.')]
m.recompute_phase_statuses(n)
m.refresh_validation(n, n['updated_at'])
errors = m.validate_plan_structure(n, ctx, directory_name=directory)
m.ensure_structurally_valid(n, ctx, directory_name=directory, input_context=True, check_snapshot=True)
canonical_size = len(m.canonical_bytes(n))
assert canonical_size < 235000, canonical_size
source = ROOT/'TRDs/trd_project-knowledge-explorer-full-first-release_2026-09-19.md'
blocks = re.findall(r'^### (REQ-\d{3}) - ([^\n]+)\n(.*?)(?=^### REQ-|^## Decisions)', source.read_text(), re.M|re.S)
count = 0
for rid,title,body in blocks:
    req = next(r for r in plan['requirements'] if r['requirement_id']==rid)
    criteria = re.findall(r'^- Acceptance: (.+)$', body, re.M)
    assert req['title']==title
    assert req['outcome']==re.search(r'^- Requirement: (.+)$', body, re.M).group(1)
    assert req['acceptance_criteria']==criteria
    assert req['dependencies']==re.findall(r'REQ-\d{3}', re.search(r'^- Depends on: (.+)$', body, re.M).group(1))
    count += len(criteria)
ats = {f'AT-{i:02}' for i in range(1,37)}
assert len(blocks)==49 and count==119
assert set(re.findall(r'AT-\d{2}',json.dumps([t['verification_steps'] for t in plan['tasks']])))==ats
positions = {t['task_id']:i for i,t in enumerate(plan['tasks'])}
assert all(positions[dep]<positions[t['task_id']] for t in plan['tasks'] for dep in t['dependencies'])
assert all(t['status']=='planned' and t['evidence']==[] for t in plan['tasks'])
assert all(r['status']=='active' and r['evidence']==[] for r in plan['requirements'])
assert all(d['status']=='proposed' and d['decided_at'] is None for d in plan['decisions'])
assert not errors

dispositions = json.loads((OUT/'dispositions.json').read_text())
dispositions['omitted'].append('V2 replaces repeated full acceptance prose in negative_requirements with concise negative obligations. The 49 requirement titles/outcomes, 119 exact acceptance sentences, dependencies, full scope, all tasks/coverage and chosen design remain byte-for-byte equal as parsed fields to V1; normalized canonical size now includes generated identity/history/validation in the bound check.')
assert set(dispositions)=={'retained','omitted','differences','assumptions','interfaces','requirements','risks','verification','unresolved'}
assert set(dispositions['differences'])=={'complementary','terminology','scope','evidence','exclusive'}
assert all(isinstance(v,str) and v for v in dispositions['differences'].values())
assert dispositions['unresolved']==[]

proposal = OUT/'proposal-v2.json'
proposal.write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n')
(OUT/'dispositions-v2.json').write_text(json.dumps(dispositions,indent=2)+'\n')
receipt = {
    'method':'Installed helper normalization and full ephemeral canonical identity/history/validation serialization, structure/source-snapshot/fidelity/AT/order checks; no managed write.',
    'highest_verification_level':'static_checks_passed',
    'structural_errors':errors,
    'quality_findings':m.quality_findings(n),
    'counts':{'requirements':49,'exact_acceptance_sentences':119,'phases':8,'tasks':33,'sources':22,'proposed_decisions':13},
    'proposal_bytes':proposal.stat().st_size,
    'fully_normalized_canonical_bytes':canonical_size,
    'canonical_target_bytes':235000,
    'task_evidence_max_bytes':250000,
    'canonical_headroom_bytes':250000-canonical_size,
    'proposal_sha256':sha(proposal),
    'dispositions_sha256':sha(OUT/'dispositions-v2.json'),
    'source_sha256':sha(source),
    'all_36_explicit_AT_verification_references':sorted(ats),
    'unchanged_v1_fields':'Every top-level field except requirements is exactly equal; every requirement field except negative_requirements is exactly equal. No task, source, decision, coverage, scope, phase, acceptance or dependency changed.',
    'v1_artifact_sha256s':v1_hashes,
    'input_context_digests_match':len(assignment['context']),
    'input_rebind_receipt':assignment['input_receipt'],
    'ordering':'All task dependencies precede consumers; shared state before screens, independent List before renderer, final audit after handoff.',
    'unresolved_synthesis_conflicts':[],
    'canonical_mutation':False,
    'product_behavior_verified':False,
}
for name,digest in v1_hashes.items():
    assert sha(OUT/name)==digest
(OUT/'static-validation-v2.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({k:receipt[k] for k in ['structural_errors','counts','proposal_bytes','fully_normalized_canonical_bytes','canonical_headroom_bytes','proposal_sha256','dispositions_sha256','input_context_digests_match']}))
