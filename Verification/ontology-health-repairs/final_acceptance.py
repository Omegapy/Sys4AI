"""Record the Director's acceptance after reopening the final evidence set."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    mapping_path = OUT / 'final-traceability.json'
    mapping = json.loads(mapping_path.read_text())
    assert not mapping['confirmed_unmet_acceptance_criteria']
    assert not mapping['pending_execution_and_verification']
    assert all(mapping['validation'].values())
    assert mapping['counts']['requirements'] == 30
    assert mapping['counts']['review_supported_criteria'] == 60
    assert mapping['counts']['planned_tasks'] == 36
    inspected = {}
    for row in mapping['evidence_artifact_reverse_map']:
        path = ROOT / row['path']
        assert path.is_file() and digest(path) == row['sha256'], row['path']
        inspected[row['path']] = row['sha256']
    for row in mapping['root_adoption_reverse_map'] + mapping['template_only_source_reverse_map']:
        for key, hash_key in [('source', 'current_source_sha256'), ('path', 'current_destination_sha256'),
                              ('template_destination', 'template_sha256')]:
            if key in row and hash_key in row:
                assert digest(ROOT / row[key]) == row[hash_key], row[key]
    for label in ('completion-core-health', 'completion-advanced-health', 'completion-memory-health'):
        result = json.loads((OUT / 'commands' / label / 'stdout.log').read_text())
        assert result['ready'] and result['aggregate'] == 'ready'
    for path in ('commands/root-ontology-suite-final/test-identities.json',
                 'installations/final-delivery/installed-suite/test-identities.json'):
        result = json.loads((OUT / path).read_text())
        assert result['status'] == 'passed' and result['required_count'] == result['observed_count'] == 183
        assert not result['missing']
    delivery = json.loads((OUT / 'installations/final-delivery/RESULT.json').read_text())
    preservation = json.loads((OUT / 'final-preservation.json').read_text())
    assert delivery['status'] == preservation['status'] == 'passed'
    assert not preservation['unclassified_changes']
    plan_path = ROOT / 'Implementation_Plans/Plan_ontology-health-reliability-and-initialization-prevention_2026-09-10_2C3A0863/plan.json'
    trd_path = ROOT / 'TRDs/trd_ontology-and-health-reliability-repairs-and-initialization-p_2026-09-10.md'
    assert digest(plan_path) == '1569553faaebb27904e6b5282fd8bff39948cfce79079ecde0807a9290439705'
    assert digest(trd_path) == 'cfb3ef5cebdec871e2c44118f6f7888d93c156a6ce1463b6ba3511625a9c5fa0'
    criteria = []
    for requirement in mapping['requirements']:
        for criterion in requirement['criteria']:
            assert criterion['evidence_state'] == 'SUPPORTED_BY_OBSERVED_EVIDENCE'
            criteria.append({'criterion_id': criterion['criterion_id'], 'status': 'accepted',
                             'evidence_refs': criterion['evidence_refs']})
    assert len(criteria) == len({c['criterion_id'] for c in criteria}) == 60
    report = OUT / 'REPORT.md'
    for target in re.findall(r'\]\(([^)]+)\)', report.read_text()):
        if target == 'final-inspection.json':
            continue
        assert (report.parent / target).is_file(), target
    result = {'schema_version': 1, 'status': 'complete', 'actor': '/root',
              'observed_at': datetime.now(timezone.utc).isoformat(),
              'objective': 'Implement PLAN-20260910-2C3A0863',
              'accepted_requirements': [r['requirement_id'] for r in mapping['requirements']],
              'accepted_criteria': criteria,
              'accepted_planned_tasks': [t['task_id'] for t in mapping['planned_tasks']],
              'highest_verification': 'Final source, installed root and delivered regression, real selected local operations, exact preservation, and independent requirement reconciliation.',
              'review_sha256': digest(mapping_path), 'report_sha256': digest(report),
              'preservation_sha256': digest(OUT / 'final-preservation.json'),
              'delivery_sha256': digest(OUT / 'installations/final-delivery/RESULT.json'),
              'reopened_evidence_count': len(inspected), 'reopened_evidence': inspected,
              'limitations': mapping['limitations'][1:],
              'canonical_plan_unchanged': True, 'canonical_trd_unchanged': True,
              'task_state_changed': False, 'git_committed_or_published': False,
              'remaining_required_work': []}
    (OUT / 'final-inspection.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'status': 'complete', 'accepted_requirements': 30, 'accepted_criteria': 60,
                      'accepted_planned_tasks': 36, 'reopened_evidence': len(inspected)}))


if __name__ == '__main__':
    main()
