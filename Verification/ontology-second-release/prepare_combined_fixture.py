"""Select existing local runtime copies and explicit profiles for integrated browser acceptance."""
import json,sys,shutil
from datetime import datetime,timezone,timedelta
from pathlib import Path
base=Path(__file__).resolve().parents[2];root=base/'Verification/ontology-second-release/fixtures/generation-native'
sys.path.insert(0,str(root/'.agents/skills/ontology/scripts'))
from ontology_profiles import configure_profile
from ontology_core import canonical_bytes,sha256
# This exact fixture setup is authorized by the release goal. No package/model fetch occurs here.
for relative in ['.venv-ontology-semantic','.sys4ai/ontology/semantic']:
 shutil.copytree(base/relative,root/relative,dirs_exist_ok=True,symlinks=True,ignore=shutil.ignore_patterns('__pycache__','*.pyc','index.json'))
observed=json.loads((base/'Verification/ontology-second-release/root-semantic-grant.json').read_text())
for name in ['semantic','workbench']:
 now=datetime.now(timezone.utc)
 authority={'schema_version':1,'operation_id':'ONTPROFILE-native-combined-'+name,'operation':'configure-profile','project_id':'example','profile':name,'enabled':True,'expected_config_sha256':sha256(root/'ontology-advanced.yaml'),'actor_id':'/root','actor_kind':'director','native_receipt':observed['native_receipt'],'observed_at':observed['observed_at'],'expires_at':observed['expires_at']}
 result=configure_profile(root,name,True,authority['expected_config_sha256'],authority)
 (root/'Verification'/('configure-'+name+'.json')).write_bytes(canonical_bytes(result))
 print(name,result['status'])
