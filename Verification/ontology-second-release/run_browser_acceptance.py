"""Trusted local launcher for observed browser acceptance; exposes no extra HTTP endpoint."""
import json,sys,os,signal,threading
from datetime import datetime,timezone
from pathlib import Path
base=Path(__file__).resolve().parents[2];root=base/'Verification/ontology-second-release/fixtures/generation-native';sys.path.insert(0,str(root/'.agents/skills/ontology/scripts'))
from ontology_workbench import Workbench,trusted_authority
cfg=json.loads((root/'ontology.yaml').read_text());now=datetime.now(timezone.utc).isoformat()
native={'tool':'collaboration.list_agents','result':{'agents':[{'agent_name':'/root','agent_status':'running'}]}}
# Exact root-running observation was obtained immediately before the trusted launch.
authority=trusted_authority(root,actor_id='/root',actor_kind='director',native_receipt=native,observed_at=now,scope=cfg['project_files']+cfg['binding_files'])
author=Workbench(root,authority,port=0).start();reader=Workbench(root,None,port=0).start()
runtime=root/'.sys4ai/ontology/workbench';runtime.mkdir(parents=True,exist_ok=True)
file=runtime/('browser-acceptance-'+sys.argv[1]+'.json')
with os.fdopen(os.open(file,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'w') as stream:json.dump({'author':author.bootstrap_url(),'second':author.bootstrap_url(),'reader':reader.bootstrap_url(),'author_origin':author.origin,'reader_origin':reader.origin,'pid':os.getpid()},stream)
(base/'Verification/ontology-second-release'/('browser-native-authority-'+sys.argv[1]+'.json')).write_text(json.dumps({'actor':'/root','observed_at':now,'native_receipt':native,'scope':authority.scope,'origins':[author.origin,reader.origin],'pid':os.getpid()},indent=2)+'\n')
print(json.dumps({'author_origin':author.origin,'reader_origin':reader.origin,'session_file':str(file),'pid':os.getpid()}),flush=True)
stop=threading.Event();signal.signal(signal.SIGTERM,lambda *_:stop.set());signal.signal(signal.SIGINT,lambda *_:stop.set())
try:stop.wait()
finally:author.close();reader.close()
