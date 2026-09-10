"""Prepare reviewable historical-proof and lifecycle candidates; no live writes."""
import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT/'SKILLS-depo/memory/scripts'))
from memory_core import json_bytes, sha256, parse_record, render_record, reject_sensitive
from memory_publish import transaction_payload

old_path = 'MEMORY/MEM-20260909-89C402A6.md'
old_raw = (ROOT/old_path).read_bytes()
old = parse_record(old_raw)
receipt_path = old['metadata']['sources'][0]['path']
receipt_raw = (ROOT/receipt_path).read_bytes()
assert sha256(receipt_raw) == old['metadata']['sources'][0]['sha256']
receipt = json.loads(receipt_raw)
retained_names = ['historical-memory.yaml', 'historical-memory_capture.py', 'historical-memory_core.py',
                  'historical-init_new_project.py', 'historical-config-v1.json']
companion = {'schema_version': 1, 'receipt': {'path': receipt_path, 'sha256': sha256(receipt_raw)},
             'applicability': 'historical', 'artifacts': []}
for ref, name in zip(receipt['artifacts'], retained_names):
    retained = OUT/name
    if not retained.exists():
        raw = (ROOT/ref['path']).read_bytes()
        assert sha256(raw) == ref['sha256'], 'Current artifact no longer matches original: '+ref['path']
        retained.write_bytes(raw)
    raw = retained.read_bytes()
    assert sha256(raw) == ref['sha256']
    reject_sensitive(raw.decode('utf-8'))
    companion['artifacts'].append(dict(ref, retained_path=retained.relative_to(ROOT).as_posix()))
companion_path = 'Verification/project-memory/evidence/verification-'+sha256(receipt_raw)+'.json'
(OUT/'historical-proof-companion.json').write_bytes(json_bytes(companion))
manifest = {'status': 'prepared_for_host_review_not_published', 'destination': companion_path,
            'expected_sha256': None, 'source': 'Verification/ontology-health-repairs/memory/historical-proof-companion.json',
            'sha256': sha256(json_bytes(companion)), 'original_record': {'path': old_path, 'sha256': sha256(old_raw)},
            'original_receipt': companion['receipt'], 'artifacts': companion['artifacts'],
            'scope': 'exact historical evidence retention; no new execution, current verification, or canonical publication'}
(OUT/'retained-artifact-manifest.json').write_bytes(json_bytes(manifest))
now = datetime.now(timezone.utc).isoformat()
new_id = 'MEM-20260910-'+sha256('historical-only:'+old['metadata']['id'])[:8].upper()
operation = 'MEMOP-ontology-health-historical-20260910'
reason = 'The original verified observation is retained with exact historical artifact bytes; its capture and initializer versions differ from the current implementation. The successor records historical context and makes no renewed current verification claim.'
new = copy.deepcopy(old)
m = new['metadata']
m.update(id=new_id, state='active', created=now, modified=now,
         title='Historical automatic-capture v6 verification and current applicability boundary',
         claim={'level':'historical_context', 'summary':'The intact 2026-09-09 receipt and retained exact artifacts support the earlier automatic-capture and initializer-v6 observation; this note does not verify the current implementation.'},
         applicability=['The observation at 2026-09-09T02:31:12.103208+00:00 and its exact retained artifact versions.'],
         limitations=['Current capture and initializer code differ from the original observed versions; current verification requires its own observed result.',
                      'The original check used disposable fixtures and documented skips. This disposition did not rerun or broaden that historical test result.',
                      'Historical memory does not grant current execution, publication, installation or maintenance authority.'],
         lifecycle={'supersedes':[old['metadata']['id']], 'superseded_by':None, 'reason':reason},
         publication={'actor_id':'/root','actor_kind':'director','operation_id':operation,'approved_at':now})
m['sources'] = [copy.deepcopy(old['metadata']['sources'][0]),
                {'path': companion_path,'sha256':sha256(json_bytes(companion)),'locator':'document','kind':'source'},
                {'path':'Verification/ontology-health-repairs/memory/retained-artifact-manifest.json',
                 'sha256':sha256(json_bytes(manifest)),'locator':'json:/artifacts','kind':'source'}]
new['body'] = '# Historical verification and applicability\nThe original receipt reports the earlier automatic-capture default and initializer-v6 checks. Its receipt bytes and six referenced test logs retain their original digests. Both changed implementation artifacts were recovered as exact bytes from local Git history; the other observed artifacts were retained from exact matching project bytes.\n\nThe predecessor remains readable with its original claim, sources, body and publication history. Current capture and initializer implementations differ from that observation. This successor provides historical context only; current operational readiness and current verification require their own final-version checks.\n'
prior = copy.deepcopy(old)
prior['metadata'].update(state='superseded',modified=now,publication=copy.deepcopy(m['publication']))
prior['metadata']['lifecycle'].update(superseded_by=new_id,reason=reason)
changes=[]
for record, expected in ((prior,sha256(old_raw)),(new,None)):
    content=render_record(record)
    changes.append({'path':'MEMORY/'+record['metadata']['id']+'.md','expected_sha256':expected,
                    'content':content,'reviewed_record_sha256':sha256(content)})
payload = transaction_payload(operation,'supersede',changes,reason)
(OUT/'historical-supersession-payload.json').write_bytes(json_bytes(payload))
(OUT/'historical-successor-review.md').write_text(render_record(new))
print(json.dumps({'candidate_only':True,'companion_destination':companion_path,'companion_sha256':sha256(json_bytes(companion)),
                  'successor_id':new_id,'payload_sha256':sha256(json_bytes(payload))},indent=2))
