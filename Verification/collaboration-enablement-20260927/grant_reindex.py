from pathlib import Path
import sys,json
from datetime import datetime,timezone,timedelta
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'.agents/skills/memory/scripts'))
from basic_memory_projection import digest,canonical_json
from memory_core import sha256,json_bytes
p=json.loads((OUT/'memory-reindex-payload.json').read_bytes())['result'];now=datetime.now(timezone.utc)
grant=dict(schema_version=1,grant_id='MEMGRANT-20260927-collaboration-enable-index-v3',project_id='sys4ai-depot',actor_id='/root',actor_kind='director',operation='reindex',payload_sha256=digest(canonical_json(p)),config_sha256=sha256((ROOT/'memory.yaml').read_bytes()),scope=p['paths'],native_receipt=json.loads((OUT/'native-observation-reindex.json').read_bytes()),observed_at=now.isoformat(),expires_at=(now+timedelta(minutes=4)).isoformat(),task=None,reviewed_records=[],privacy_redaction=False)
(OUT/'memory-reindex-grant.json').write_bytes(json_bytes(grant));print(grant['payload_sha256'])
