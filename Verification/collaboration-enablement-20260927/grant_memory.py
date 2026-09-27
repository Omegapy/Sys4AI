from pathlib import Path
import json,sys
from datetime import datetime,timezone,timedelta
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'.agents/skills/memory/scripts'))
from memory_core import sha256,json_bytes
payload=json.loads((OUT/'memory-payload.json').read_bytes());now=datetime.now(timezone.utc)
grant=dict(schema_version=1,grant_id='MEMGRANT-20260927-collaboration-enable-v2',project_id='sys4ai-depot',actor_id='/root',actor_kind='director',operation=payload['operation'],payload_sha256=sha256(json_bytes(payload)),config_sha256=sha256((ROOT/'memory.yaml').read_bytes()),scope=[c['path'] for c in payload['changes']],native_receipt=json.loads((OUT/'native-observation-memory.json').read_bytes()),observed_at=now.isoformat(),expires_at=(now+timedelta(minutes=4)).isoformat(),task=None,reviewed_records=[dict(path=c['path'],sha256=c['reviewed_record_sha256'],expected_sha256=c['expected_sha256']) for c in payload['changes']],privacy_redaction=False)
(OUT/'memory-grant.json').write_bytes(json_bytes(grant))
