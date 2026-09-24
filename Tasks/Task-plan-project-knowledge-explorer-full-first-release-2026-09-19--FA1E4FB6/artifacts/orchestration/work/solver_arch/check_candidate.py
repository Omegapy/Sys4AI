from pathlib import Path
import hashlib
import importlib.util
import json
import re
import sys

root = Path('/Volumes/P-SSD/AngryOwl/Sys4AI')
base = Path(__file__).parent
spec = importlib.util.spec_from_file_location('plan_state', root / '.agents/skills/to-implementation-plan/scripts/plan_state.py')
m = importlib.util.module_from_spec(spec)
sys.modules['plan_state'] = m
spec.loader.exec_module(m)
ctx = m.resolve_context(str(root), 'Implementation_Plans')
payload = json.loads((base / 'candidate.json').read_text())
normalized = m.normalize_plan_input(payload, ctx)
m.ensure_initial_lifecycle_state(normalized)
directory = m._assign_new_identity(normalized, set())
normalized['history'] = [m.history_entry(normalized, revision=1,
    event_time=normalized['created_at'], action_id='TO-IP-001',
    affected_ids=m.stable_record_ids(normalized), status_before=None, status_after='draft',
    summary='In-memory creation-input validation only.',
    authority_basis='Delegated candidate preparation; this ephemeral object is never published.')]
m.recompute_phase_statuses(normalized)
m.refresh_validation(normalized, normalized['updated_at'])
errors = m.validate_plan_structure(normalized, ctx, directory_name=directory)
m.ensure_structurally_valid(normalized, ctx, directory_name=directory, input_context=True, check_snapshot=True)
source = root / 'TRDs/trd_project-knowledge-explorer-full-first-release_2026-09-19.md'
blocks = re.findall(r'^### (REQ-\d{3}) - ([^\n]+)\n(.*?)(?=^### REQ-|^## Decisions)', source.read_text(), re.M | re.S)
for rid, title, body in blocks:
    r = next(r for r in payload['requirements'] if r['requirement_id'] == rid)
    assert r['title'] == title
    assert r['outcome'] == re.search(r'^- Requirement: (.+)$', body, re.M).group(1)
    assert r['acceptance_criteria'] == re.findall(r'^- Acceptance: (.+)$', body, re.M)
    assert r['dependencies'] == re.findall(r'REQ-\d{3}', re.search(r'^- Depends on: (.+)$', body, re.M).group(1))
ats = set(re.findall(r'AT-\d{2}', json.dumps(payload['requirements'])))
assert ats == {f'AT-{i:02}' for i in range(1, 37)}
task_ats = set(re.findall(r'AT-\d{2}', json.dumps(payload['tasks'])))
assert task_ats == ats
assert all(t['status'] == 'planned' and t['evidence'] == [] for t in payload['tasks'])
assert all(r['status'] == 'active' and r['evidence'] == [] for r in payload['requirements'])
assert not errors
result = dict(method='In-memory application of the helper create normalization, generated-field preparation and structure/source snapshot checks; no handle_create, managed write, product implementation or publication was invoked.',
    structural_errors=errors, quality_findings=m.quality_findings(normalized),
    counts=dict(requirements=len(payload['requirements']), phases=len(payload['phases']), tasks=len(payload['tasks'])),
    fidelity=dict(exact_requirement_title_outcome_acceptance_dependencies=len(blocks), AT_references=sorted(ats), explicit_task_AT_references=sorted(task_ats), source_sha256=hashlib.sha256(source.read_bytes()).hexdigest()),
    candidate_sha256=hashlib.sha256((base/'candidate.json').read_bytes()).hexdigest(),
    bytes=(base/'candidate.json').stat().st_size,
    lifecycle='Draft creation input only; generated canonical identity is ephemeral and not retained.')
(base/'static-check.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'structural_errors': errors, 'quality_findings':len(result['quality_findings']), 'counts':result['counts'], 'fidelity':49, 'candidate_sha256':result['candidate_sha256']}))
