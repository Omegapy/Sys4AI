import sys,json
from pathlib import Path
from datetime import datetime,timezone,timedelta
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'.agents/skills/memory/scripts'))
from memory_core import json_bytes,sha256
payload=json.loads((OUT/'memory-reindex-payload.json').read_text())['result'];now=datetime.now(timezone.utc)
grant={'schema_version':1,'grant_id':'MEMGRANT-20260927-collaboration-reindex-v1','project_id':'sys4ai-depot','actor_id':'/root','actor_kind':'director','operation':'reindex','payload_sha256':sha256(json_bytes(payload)),'config_sha256':sha256((ROOT/'memory.yaml').read_bytes()),'scope':payload['paths'],'native_receipt':json.loads((OUT/'native-observation-reindex.json').read_text()),'observed_at':now.isoformat(),'expires_at':(now+timedelta(minutes=4)).isoformat(),'task':None,'reviewed_records':[],'privacy_redaction':False}
(OUT/'memory-reindex-grant.json').write_bytes(json_bytes(grant));print(json.dumps({'operation':'reindex','expected_payload_sha256':grant['payload_sha256'],'scope':grant['scope'],'authority':'Explicit current user system update; refresh already selected state only.'}))
