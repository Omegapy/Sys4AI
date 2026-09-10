"""Read selected historical evidence and retain an audit copy; never edit live memory."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sha = lambda raw: hashlib.sha256(raw).hexdigest()
record_path = 'MEMORY/MEM-20260909-89C402A6.md'
receipt_path = 'Verification/automatic-memory-capture/verification.json'
record_raw = (ROOT / record_path).read_bytes()
receipt_raw = (ROOT / receipt_path).read_bytes()
metadata = json.loads(record_raw.decode().split('---\n', 2)[1])
receipt = json.loads(receipt_raw)
assert sha(receipt_raw) == metadata['sources'][0]['sha256']
(OUT / 'original-record.md').write_bytes(record_raw)
(OUT / 'original-verification.json').write_bytes(receipt_raw)
paths = [record_path, receipt_path, 'Verification/automatic-memory-capture/root-adoption.json',
         '.sys4ai/memory/maintenance/transactions/MEMOP-auto-capture-default-on-001.json',
         'TRDs/trd_ontology-and-health-reliability-repairs-and-initialization-p_2026-09-10.md',
         'Implementation_Plans/Plan_ontology-health-reliability-and-initialization-prevention_2026-09-10_2C3A0863/plan.json',
         'Verification/ontology-health-repairs/health-contract.md', 'SOUL.md',
         'Roles/project-sub-agent/AGENTS.md', 'Roles/project-sub-agent/ROLE.md']
source_inventory = [{'path': path, 'sha256': sha((ROOT/path).read_bytes())} for path in paths]
artifacts = []
for ref in receipt['artifacts']:
    current = (ROOT/ref['path']).read_bytes()
    item = dict(ref, current_sha256=sha(current), current_matches=sha(current)==ref['sha256'])
    if not item['current_matches']:
        candidates = [ref['path'].replace('.agents/skills/', 'SKILLS-depo/'),
                      'Projects/Sys4AI-Template-Project/'+ref['path']]
        proofs = []
        for candidate in candidates:
            path = ROOT/candidate
            proofs.append({'path': candidate, 'exists': path.is_file(),
                           'sha256': sha(path.read_bytes()) if path.is_file() else None})
        tracked = subprocess.run(['git', 'show', 'HEAD:'+ref['path']], cwd=ROOT, capture_output=True)
        proofs.append({'path': 'git:HEAD:'+ref['path'], 'exists': tracked.returncode==0,
                       'sha256': sha(tracked.stdout) if tracked.returncode==0 else None})
        item['inspected_alternative_versions'] = proofs
        item['exact_old_bytes_accessible'] = any(p['sha256'] == ref['sha256'] for p in proofs)
    else:
        item['exact_old_bytes_accessible'] = True
    artifacts.append(item)
logs = []
for ref in receipt['details']['tests']:
    path = ROOT/ref['log']
    logs.append(dict(ref, accessible=path.is_file(), current_sha256=sha(path.read_bytes()) if path.is_file() else None,
                     retained_log_matches=path.is_file() and sha(path.read_bytes())==ref['sha256']))
value = {'record_id': metadata['id'], 'record_sha256': sha(record_raw), 'receipt_sha256': sha(receipt_raw),
         'receipt_integrity': 'intact', 'observed_at': receipt['observed_at'],
         'source_inventory': source_inventory, 'artifacts': artifacts, 'logs': logs,
         'limitations': ['This review did not execute the old check or reconstruct unavailable source versions.',
                        'An intact historical receipt and logs corroborate the report, but do not replace missing exact source proof.',
                        'Alternative-version checks were bounded to source, registered Template copy and Git HEAD; no claim of exhaustive external backup search.']}
(OUT/'evidence-inventory.json').write_text(json.dumps(value, indent=2, sort_keys=True)+'\n')
print(json.dumps({'changed_artifacts': [x for x in artifacts if not x['current_matches']],
                  'all_test_logs_match': all(x['retained_log_matches'] for x in logs)}, indent=2))
