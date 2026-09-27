from pathlib import Path
import json,hashlib
from datetime import datetime,timezone,timedelta
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
preview=json.loads((OUT/'ontology-preview.json').read_text())['result'];proposal=json.loads((OUT/'ontology-proposal.json').read_text());assert preview['valid'];now=datetime.now(timezone.utc)
grant=dict(schema_version=1,grant_id='ONTGRANT-20260927-collaboration-enabled-v4',project_id='sys4ai-depot',actor_id='/root',actor_kind='director',operation='publish',payload_sha256=preview['payload_sha256'],preview_sha256=preview['preview_sha256'],config_sha256=hashlib.sha256((ROOT/'ontology.yaml').read_bytes()).hexdigest(),scope=[c['path'] for c in proposal['changes']],native_receipt=json.loads((OUT/'native-observation-ontology.json').read_bytes()),observed_at=now.isoformat(),expires_at=(now+timedelta(minutes=4)).isoformat(),task=None,reviewed_records=[{k:c[k] for k in ('path','sha256','expected_sha256')} for c in proposal['changes']])
(OUT/'ontology-grant.json').write_text(json.dumps(grant,indent=2,sort_keys=True)+'\n')
print(preview['preview_sha256'])
