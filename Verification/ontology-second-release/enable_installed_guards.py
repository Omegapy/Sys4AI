"""Explicit guard activation after installed dispatch evidence and real native observation."""
import sys,json,shutil
from datetime import datetime,timezone,timedelta
from pathlib import Path
base=Path(__file__).resolve().parents[2];root=Path(sys.argv[1]).resolve();sys.path.insert(0,str(root/'.agents/skills/ontology/scripts'))
from ontology_core import canonical_bytes,sha256
from ontology_guard_setup import preview_enablement,apply
name='root' if root==base else 'combined'
out=base/'Verification/ontology-second-release';relative='Verification/ontology-second-release/root-guarded-dispatch.json' if root==base else 'Verification/guarded-dispatch.json'
if root!=base:shutil.copyfile(out/'root-guarded-dispatch.json',root/relative)
def bound(p):return {'path':p,'sha256':sha256(root/p)}
pre=preview_enablement(root,operation_id='ONTGUARD-'+name+'-second-release-20260909',contract=bound('reference-assets/ONTOLOGY-depo/actions/contracts-v1.json'),repair=bound('reference-assets/ONTOLOGY-depo/actions/repair-v1.json'),verification=bound(relative))
(out/(name+'-guard-preview.json')).write_bytes(canonical_bytes(pre))
now=datetime.now(timezone.utc);config=json.loads((root/'ontology.yaml').read_text())
grant={'schema_version':1,'operation':pre['payload']['operation'],'preview_sha256':pre['preview_sha256'],'actor_id':'/root','actor_kind':'director','observed_at':now.isoformat(),'expires_at':(now+timedelta(seconds=300)).isoformat(),'native_receipt':{'tool':'collaboration.list_agents','result':{'agents':[{'agent_name':'/root','agent_status':'running'}]}},'scope':[c['path'] for c in pre['payload']['changes']],'reviewed_records':[{k:c[k] for k in ('path','expected_sha256','sha256')} for c in pre['payload']['changes']],'task':None,'project_id':config['project']['id'],'config_sha256':sha256(root/'ontology.yaml')}
(out/(name+'-guard-grant.json')).write_bytes(canonical_bytes(grant))
result=apply(root,pre,grant);(out/(name+'-guard-receipt.json')).write_bytes(canonical_bytes(result))
assert json.loads((root/'ontology-advanced.yaml').read_text())['profiles']['guards']['enabled'] is True
print(json.dumps({'root':name,'status':result['status'],'reopened_enabled':True}))
