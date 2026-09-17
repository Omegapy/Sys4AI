"""Exercise the installed pure plan functions without managed-plan writes."""
from pathlib import Path
import hashlib
import importlib.util
import json
import re
import sys

ROOT=Path('/Volumes/P-SSD/AngryOwl/Sys4AI')
OUT=Path(__file__).parent
helper=ROOT/'.agents/skills/to-implementation-plan/scripts/plan_state.py'
sys.path.insert(0,str(helper.parent))
spec=importlib.util.spec_from_file_location('planning_candidate_validation',helper)
p=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=p
spec.loader.exec_module(p)
payload=json.loads((OUT/'create-input.json').read_text())
context=p.resolve_context(str(ROOT),'Implementation_Plans')
try:
    source_checks=[]
    for source in payload['sources']:
        path=ROOT/source['locator']
        assert not any(part.is_symlink() for part in [path,*path.parents]), source['locator']
        current=hashlib.sha256(path.read_bytes()).hexdigest()
        assert source['digest']=='sha256:'+current, source['locator']
        source_checks.append(dict(source_id=source['source_id'],sha256=current,current=True))
    trd=(ROOT/payload['sources'][0]['locator']).read_text()
    parsed=[]
    for m in re.finditer(r'^### (REQ-\d+) — ([^\n]+)\n(.*?)(?=\n### |\n## Decisions)',trd,re.M|re.S):
        body=m[3]
        parsed.append(dict(requirement_id=m[1],outcome=re.findall(r'^- Requirement: (.+)$',body,re.M)[0],acceptance_criteria=re.findall(r'^- Acceptance: (.+)$',body,re.M),dependencies=re.findall(r'REQ-\d+',re.findall(r'^- Depends on: (.+)$',body,re.M)[0])))
    for expected,actual in zip(parsed,payload['requirements'],strict=True):
        assert all(actual[key]==value for key,value in expected.items()), expected['requirement_id']
    plan=p.normalize_plan_input(payload,context)
    p.ensure_initial_lifecycle_state(plan)
    directory=p._assign_new_identity(plan,set())
    plan['history']=[p.history_entry(plan,revision=1,event_time=plan['updated_at'],action_id='TO-IP-001',
        affected_ids=plan['initial_record_ids'],status_before=None,status_after='draft',
        summary='Pure in-memory candidate validation; no managed plan created.',
        authority_basis='Bounded solver candidate assignment for planning only.')]
    p.recompute_phase_statuses(plan)
    p.refresh_validation(plan)
    p.ensure_structurally_valid(plan,context,directory_name=directory,input_context=True)
    result=dict(status='passed',highest_verification='static_checks_passed',
        managed_plan_written=False,canonical_task_written=False,implementation_performed=False,
        helper_sha256=hashlib.sha256(helper.read_bytes()).hexdigest(),
        candidate_sha256=hashlib.sha256((OUT/'create-input.json').read_bytes()).hexdigest(),
        validation=plan['validation'],readiness_findings=p.readiness_findings(plan),
        source_checks=source_checks,verbatim_source_coverage=True,
        counts=dict(requirements=len(plan['requirements']),acceptance_clauses=sum(len(r['acceptance_criteria']) for r in plan['requirements']),phases=len(plan['phases']),tasks=len(plan['tasks'])),
        lifecycle='draft',approval='Exact managed plan revision has not been approved.',
        checks=['normalize_plan_input','ensure_initial_lifecycle_state','_assign_new_identity in memory','history_entry in memory','recompute_phase_statuses','refresh_validation','ensure_structurally_valid'],
        temporary_identity='Pure validation identity discarded; not a managed plan ID.')
except Exception as exc:
    result=dict(status='failed',error=str(exc),details=getattr(exc,'details',None))
(OUT/'validation.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
if result['status']!='passed': raise SystemExit(1)
