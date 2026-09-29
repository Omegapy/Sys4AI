from pathlib import Path
import json,hashlib
from datetime import datetime,timezone
root=Path(__file__).resolve().parents[2]
config=json.loads((root/'SKILLS-depo/ontology/assets/project-app/project-app.json').read_text())
config['project_id']='sys4ai-depot'
reviewed=datetime.now(timezone.utc).isoformat()
texts={
 'purpose':'Sys4AI is a local workspace for building agentic AI systems. It keeps reusable skills, guidance and roles alongside the project tools that use them.',
 'scope':'Maintain reusable source collections, prepare projects from the shared Template, and read project planning and verification records. Each product project keeps its own files and receives updates through a selected adoption.',
 'audience':'For people and agents maintaining this depot, preparing Sys4AI projects, or reading how the workspace is organized.'}
for key,text in texts.items():
 config['home'][key]={'text':text,'sources':[{'path':'README.md','sha256':hashlib.sha256((root/'README.md').read_bytes()).hexdigest()}],'reviewed_sha256':hashlib.sha256(text.encode()).hexdigest(),'reviewed_at':reviewed}
config['documents']=[{'title':'Workspace overview and ownership','path':'README.md'},{'title':'Project specifications and supported capabilities','path':'SPECS.md'}]
config['start_here']={'label':'Read the workspace overview','path':'README.md'}
(root/'Verification/shared-project-app/root-project-app.json').write_text(json.dumps(config,indent=2)+'\n')
