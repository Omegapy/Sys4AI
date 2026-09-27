import sys,json,hashlib
from pathlib import Path
from datetime import datetime,timezone,timedelta
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'.agents/skills/memory/scripts'))
from memory_core import json_bytes,sha256
payload=json.loads((OUT/'memory-payload.json').read_text());now=datetime.now(timezone.utc)
grant={'schema_version':1,'grant_id':'MEMGRANT-20260927-collaboration-release-v1','project_id':'sys4ai-depot','actor_id':'/root','actor_kind':'director','operation':'publish','payload_sha256':sha256(json_bytes(payload)),'config_sha256':sha256((ROOT/'memory.yaml').read_bytes()),'scope':[c['path'] for c in payload['changes']],'native_receipt':json.loads((OUT/'native-observation-memory.json').read_text()),'observed_at':now.isoformat(),'expires_at':(now+timedelta(minutes=4)).isoformat(),'task':None,'reviewed_records':[{'path':c['path'],'sha256':c['reviewed_record_sha256'],'expected_sha256':c['expected_sha256']} for c in payload['changes']],'privacy_redaction':False}
(OUT/'memory-grant.json').write_bytes(json_bytes(grant));print(json.dumps({'actor':grant['actor_id'],'scope':grant['scope'],'reviewed_records':grant['reviewed_records'],'payload_sha256':grant['payload_sha256']}))
