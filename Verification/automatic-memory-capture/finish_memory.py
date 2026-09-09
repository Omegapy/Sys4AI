"""Publish the reviewed completion finding and refresh the existing local index.

Requires a freshly observed native receipt file supplied by the host; does not
launch agents, install dependencies, change configuration, or create Tasks.
"""
from datetime import datetime,timedelta,timezone
from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[2]; HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'.agents/skills/memory/scripts'))
from memory_core import load_config,json_bytes,sha256,load_record
from memory_capture import capture
from memory_maintenance import reindex_payload,reindex
from memory_search import search
from basic_memory_adapter import health
from basic_memory_projection import canonical_json

observation=json.loads((HERE/'native-observation.json').read_text())
observed=datetime.fromisoformat(observation['observed_at'])
assert datetime.now(timezone.utc)-observed < timedelta(minutes=4)
def grant(payload,scope,records,label):
    config=load_config(ROOT)
    value={'schema_version':1,'grant_id':'auto-capture-'+label,'project_id':config['project']['id'],
           'actor_id':'/root','actor_kind':'director','operation':payload['operation'],
           'payload_sha256':sha256(canonical_json(payload) if payload['operation']=='reindex' else json_bytes(payload)),'config_sha256':sha256((ROOT/'memory.yaml').read_bytes()),
           'scope':scope,'native_receipt':observation['native_receipt'],
           'observed_at':observed.isoformat(),'expires_at':(observed+timedelta(minutes=4)).isoformat(),
           'task':None,'reviewed_records':records,'privacy_redaction':False}
    rel='Verification/automatic-memory-capture/'+label+'-grant.json'
    (ROOT/rel).write_bytes(json_bytes(value));return rel
payload=json.loads((HERE/'capture-payload.json').read_text())
g=grant(payload,['MEMORY'],[{'path':c['path'],'sha256':c['reviewed_record_sha256'],'expected_sha256':c['expected_sha256']} for c in payload['changes']],'capture')
result=capture(ROOT,payload,g,'/root',trigger='work-completed')
(HERE/'capture-result.json').write_bytes(json_bytes(result))
assert result['status']=='captured'
note=payload['changes'][0]['path'];assert not load_record(ROOT,note)['diagnostics']
print('Captured and validated '+note,flush=True)
payload=reindex_payload(ROOT)
(HERE/'reindex-payload.json').write_bytes(json_bytes(payload))
g=grant(payload,payload['paths'],[],'reindex')
result=reindex(ROOT,grant_file=g,actor='/root',expected_payload_sha256=sha256(canonical_json(payload)))
(HERE/'reindex-result.json').write_bytes(json_bytes(result))
print('Reindex '+result['status'],flush=True)
result=search(ROOT,'Automatic capture defaults on')
(HERE/'search-result.json').write_bytes(json_bytes(result))
assert result['mode']=='hybrid' and any(r['path']==note for r in result['results'])
(HERE/'backend-health.json').write_bytes(json_bytes(health(ROOT)))
print('Hybrid search retrieved the captured note.',flush=True)
