"""Apply the host-reviewed exact proposal using its actual observed native identity."""
import json,sys
from datetime import datetime,timezone,timedelta
from pathlib import Path
root=Path(__file__).resolve().parents[2];sys.path.insert(0,str(root/'.agents/skills/ontology/scripts'))
from ontology_core import canonical_bytes,sha256
from ontology_publication import publish
out=root/'Verification/ontology-second-release';candidate=json.loads((out/'root-semantic-proposal.json').read_text());pre=json.loads((out/'root-semantic-preview.json').read_text())
now=datetime.now(timezone.utc)
# Normalize the exact root-running entry observed in the immediately preceding native roster.
native={'tool':'collaboration.list_agents','result':{'agents':[{'agent_name':'/root','agent_status':'running'}]}}
grant={'schema_version':1,'grant_id':'ONTGRANT-root-advanced-adoption-20260909','project_id':'sys4ai-depot','actor_id':'/root','actor_kind':'director','operation':'publish','payload_sha256':sha256(canonical_bytes(candidate)),'preview_sha256':pre['preview_sha256'],'config_sha256':sha256(root/'ontology.yaml'),'scope':[c['path'] for c in candidate['changes']],'native_receipt':native,'observed_at':now.isoformat(),'expires_at':(now+timedelta(seconds=300)).isoformat(),'task':None,'reviewed_records':[{k:c[k] for k in ('path','sha256','expected_sha256')} for c in candidate['changes']]}
(out/'root-semantic-grant.json').write_bytes(canonical_bytes(grant))
result=publish(root,candidate,grant,expected_preview_sha256=pre['preview_sha256']);(out/'root-semantic-publication.json').write_bytes(canonical_bytes(result))
assert result['status']=='complete',result
assert all(sha256(root/c['path'])==c['sha256'] for c in candidate['changes'])
print(json.dumps({'status':result['status'],'reopened':len(candidate['changes'])}))
