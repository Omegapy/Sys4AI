"""Explicit fixture-only publication/profile activation and full authored SHACL."""
from pathlib import Path
from datetime import datetime,timedelta,timezone
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[3]
project=Path(json.loads((OUT/'runtime-preparation.json').read_text())['initialized_project'])
folder=OUT/'populated';folder.mkdir(exist_ok=False)
script=project/'.agents/skills/ontology/scripts/ontology.py'
sys.path.insert(0,str(script.parent))
from ontology_core import canonical_bytes,sha256,load_project
from ontology_profiles import fingerprint


def save(path,value):
 path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(canonical_bytes(value))

def invoke(name,arguments):
 case=folder/name;case.mkdir()
 command=[str(ROOT/'.venv/bin/python'),'-B',str(script),'--project-root',str(project),*arguments]
 begin=time.monotonic();started=datetime.now(timezone.utc).isoformat()
 env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','PYTHONNOUSERSITE':'1','TMPDIR':str(folder/'tmp')}
 cp=subprocess.run(command,cwd=project,env=env,capture_output=True,timeout=90)
 (case/'stdout.json').write_bytes(cp.stdout);(case/'stderr.log').write_bytes(cp.stderr)
 value=json.loads(cp.stdout)
 save(case/'receipt.json',{'command':command,'cwd':str(project),'started_at':started,'elapsed_seconds':round(time.monotonic()-begin,4),
 'exit_code':cp.returncode,'stdout_sha256':sha256(cp.stdout),'stderr_sha256':sha256(cp.stderr),'helper_sha256':sha256(script)})
 print(json.dumps({'case':name,'exit':cp.returncode,'status':value.get('status'),'complete':value.get('complete'),'conforms':value.get('conforms')}),flush=True)
 assert cp.returncode==0,(name,value)
 return value

(folder/'tmp').mkdir()
shared_paths=['depot/projects.json','ontology.yaml','ontology-advanced.yaml','memory.yaml','.venv-ontology-standards/certification.json','.sys4ai/ontology/semantic/model.json','.sys4ai/ontology/semantic/index-v1.json']
shared_before={p:sha256(ROOT/p) for p in shared_paths}
assert not (project/'.venv-ontology-standards').exists()
shared_fingerprint=fingerprint(ROOT)
shutil.copytree(ROOT/'.venv-ontology-standards',project/'.venv-ontology-standards',symlinks=True,
                ignore=shutil.ignore_patterns('wheels','__pycache__','*.pyc'))
assert fingerprint(project)==shared_fingerprint
save(folder/'runtime-copy-provenance.json',{'source':str(ROOT/'.venv-ontology-standards'),'destination':str(project/'.venv-ontology-standards'),
 'source_and_copy_fingerprints_equal':True,'fingerprint':shared_fingerprint,'provisioned':False,'packages_installed':False,'models_downloaded':False,
 'classification':'Explicit isolated copy of the existing certified standards runtime, after neutral setup; no automatic activation.',
 'semantic_runtime':'No semantic environment activated in this populated project. Actual semantic-model test has its own separate retained acceptance evidence.'})
config=json.loads((project/'ontology.yaml').read_text());identity=config['project']['id'];ns=config['project']['namespace'];core='urn:sys4ai:ontology:core:'
source={'path':'SPECS.md','sha256':sha256(project/'SPECS.md'),'locator':'line:1'}
record_path=config['project_files'][0]
original=json.loads((project/record_path).read_text())
assert not original['@graph']
def rec(local,kind='instance',types=None,fact='asserted',**extra):
 return {'@id':ns+local,'@type':types or [core+'Artifact'],'kind':kind,'label':'Delivery '+local,
  'definition':'Synthetic full-scale acceptance meaning for '+local+'.','lifecycle':'approved','module':'project','fact_kind':fact,
  'sources':[source],'aliases':[local+' acceptance alias',local+' fixture alias'],
  'scope_note':'Applies only to this isolated delivered acceptance fixture; no real product authority.',
  'examples':['Local acceptance example for '+local],'non_examples':['Unrelated real project for '+local],**extra}
records=[rec('DeliveryArtifact',kind='concept',types=[core+'OntologyConcept']),
 rec('delivery-subtype',kind='relation',types=[core+'Relationship'],subject=ns+'DeliveryArtifact',predicate=core+'subtypeOf',object=core+'Artifact')]
records.extend(rec('artifact-'+str(i),types=[ns+'DeliveryArtifact']) for i in range(122))
records.extend([rec('external-project',types=[core+'Project'],fact='external'),rec('external-template',types=[core+'ProjectTemplate'],fact='external')])
assert len(records)==126
content=canonical_bytes({'@context':original['@context'],'@graph':records})
assert len(content)<=250000
request={'schema_version':1,'operation_id':'ONTOP-delivered-populated-acceptance','operation':'publish',
 'reason':'Publish explicitly authorized synthetic full-scale fixture records, including project-specific and external types, through the delivered owning helper.',
 'changes':[{'path':record_path,'expected_sha256':sha256(project/record_path),'content':content.decode(),'sha256':sha256(content)}]}
# Grants are explicit isolated test fixtures, as in the shipped guard/publication
# tests. They confer no authority in the shared root or another real project.
evidence_root=project/'Verification/delivery-acceptance';evidence_root.mkdir(parents=True)
save(evidence_root/'proposal.json',request)
preview=invoke('publication-preview',['preview','Verification/delivery-acceptance/proposal.json'])
now=datetime.now(timezone.utc)
native={'tool':'collaboration.list_agents','result':{'agents':[{'agent_name':'/root','agent_status':'running'}]}}
grant={'schema_version':1,'grant_id':'ONTGRANT-delivered-populated-fixture','project_id':identity,'actor_id':'/root','actor_kind':'director','operation':'publish',
 'payload_sha256':sha256(canonical_bytes(request)),'preview_sha256':preview['preview_sha256'],'config_sha256':sha256(project/'ontology.yaml'),
 'scope':[record_path],'native_receipt':native,'observed_at':now.isoformat(),'expires_at':(now+timedelta(minutes=4)).isoformat(),'task':None,
 'reviewed_records':[{k:r[k] for k in ('path','expected_sha256','sha256')} for r in request['changes']]}
save(evidence_root/'publication-grant.json',grant)
published=invoke('publication',['publish','Verification/delivery-acceptance/proposal.json','--grant-file','Verification/delivery-acceptance/publication-grant.json','--expected-preview-sha256',preview['preview_sha256']])
assert (project/record_path).read_bytes()==content
for profile in ('standards','inference'):
 now=datetime.now(timezone.utc);expected=sha256(project/'ontology-advanced.yaml')
 authority={'schema_version':1,'operation_id':'ONTPROFILE-delivered-'+profile,'operation':'configure-profile','project_id':identity,
 'profile':profile,'enabled':True,'expected_config_sha256':expected,'actor_id':'/root','actor_kind':'director','native_receipt':native,
 'observed_at':now.isoformat(),'expires_at':(now+timedelta(minutes=4)).isoformat()}
 save(evidence_root/(profile+'-grant.json'),{'profile':profile,'enabled':True,'expected_config_sha256':expected,'authority':authority})
 activated=invoke('activate-'+profile,['profile-configure','Verification/delivery-acceptance/'+profile+'-grant.json'])
 assert activated['status']=='configured' and activated['provisioned'] is False
p=load_project(project);assert len(p.records)==191
tracked={str(f.relative_to(project)):sha256(f) for f in project.rglob('*') if f.is_file() and '.venv-ontology-standards' not in f.parts}
query='SELECT ?g (COUNT(*) AS ?n) WHERE { GRAPH ?g { ?s ?p ?o } } GROUP BY ?g'
counts=invoke('graph-counts',['sparql','--query',query,'--graph','asserted','--graph','derived','--graph','external'])
validated=invoke('full-shacl',['shacl'])
assert validated['complete'] is True and validated['conforms'] is True and validated['status']=='conformant'
assert validated['graph_scope']==['asserted','derived','external']
assert validated['worker']['elapsed_seconds']<=10
expected_type=ns+'DeliveryArtifact'
answer=invoke('project-type-query',['sparql','--query','ASK { <'+ns+'artifact-0> a <'+expected_type+'> }'])
assert answer['complete'] and answer['answer'] is True
inference=invoke('derived-type',['infer','--goal',ns+'artifact-0','http://www.w3.org/1999/02/22-rdf-syntax-ns#type',core+'Artifact'])
assert inference['complete'] and inference['status']=='ok' and inference['trusted'] is True
assert inference['conclusions'][0]['classification']=='entailed'
assert tracked=={str(f.relative_to(project)):sha256(f) for f in project.rglob('*') if f.is_file() and '.venv-ontology-standards' not in f.parts}
assert shared_before=={p:sha256(ROOT/p) for p in shared_paths}
result={'status':'passed','project_root':str(project),'project_id':identity,'record_count':len(p.records),'new_project_records':126,'external_records':2,
 'full_graph_counts_result':counts,'full_shacl':validated,'project_type_query':answer,'inference':inference,
 'fixture_publication':{'operation_id':request['operation_id'],'receipt':published,'native_authority':'Synthetic isolated fixture grant under explicit acceptance scope; no real root authority claim.'},
 'runtime_copy':'runtime-copy-provenance.json','shared_selected_inputs_preserved':shared_before,'canonical_fixture_bytes_preserved_by_reads':True,
 'limits':'Unchanged delivered defaults: SHACL/query10 seconds, reasoning30 seconds, RSS512MiB, workers2.',
 'no_packages_installed':True,'no_model_download':True,'no_shared_root_mutation':True}
save(folder/'result.json',result)
print(json.dumps({'status':'populated_acceptance_passed','records':len(p.records),'shacl_seconds':validated['worker']['elapsed_seconds']}),flush=True)
