from pathlib import Path
import json,hashlib
from datetime import datetime,timezone,timedelta
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
preview=json.loads((OUT/'guard-repair-preview.json').read_text());now=datetime.now(timezone.utc)
changes=preview['payload']['changes']
grant=dict(schema_version=1,project_id='sys4ai-depot',actor_id='/root',actor_kind='director',operation='guard-repair',preview_sha256=preview['preview_sha256'],config_sha256=hashlib.sha256((ROOT/'ontology.yaml').read_bytes()).hexdigest(),scope=[r['path'] for r in changes],reviewed_records=[{k:r[k] for k in ('path','sha256','expected_sha256')} for r in changes],native_receipt=json.loads((OUT/'native-observation-guard.json').read_bytes()),observed_at=now.isoformat(),expires_at=(now+timedelta(minutes=4)).isoformat(),task=None)
(OUT/'guard-repair-grant.json').write_text(json.dumps(grant,indent=2,sort_keys=True)+'\n')
