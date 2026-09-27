"""Two confined package-adoption checks. Every actor/receipt/Task here is synthetic."""
from pathlib import Path
import hashlib,json,shutil,sys,subprocess
R=Path(__file__).resolve().parents[3];V=R/'Verification/shared-agent-billboards';D=V/'adoption';T=R/'Projects/Sys4AI-Template-Project'
sys.path.insert(0,str(R/'SKILLS-depo/agent-task/tests'));import test_orchestration_state as harness
sys.path.insert(0,str(R/'SKILLS-depo/collaborate/scripts'))
from collaboration_task import Context
from collaboration_read import Board
from collaboration_store import encoded
from collaboration_overview import overview,rebuild_overview

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(root,p):return {'path':str(p.relative_to(root)),'sha256':sha(p)}
def write(p,obj):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,indent=2)+'\n')
def tree(root):return {str(p.relative_to(root)):sha(p) for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
def cli(root,command,*args,payload=None):
 p=subprocess.run([sys.executable,str(root/'.agents/skills/agent-task/scripts/task_state.py'),'--project-root',str(root),'--format','json',command,*args],input=json.dumps(payload) if payload is not None else None,capture_output=True,text=True)
 return p,json.loads(p.stdout)

skills=('collaborate','agent-task','task','manage-subagent-roles','communication')
selected=[p for s in skills for p in (T/'.agents/skills'/s).rglob('*') if p.is_file() and '__pycache__' not in p.parts]
selected += [T/p for p in ('SOUL.md','SPECS.md','Roles/project-sub-agent/AGENTS.md','Roles/project-sub-agent/ROLE.md','Roles/task-manager/AGENTS.md','Roles/task-manager/ROLE.md','Roles/INDEX.md')]
new=D/'depot/Projects/new-project';old=D/'depot/Projects/existing-project'
if not (D/'previews.json').exists():
 # Resume only the known first preflight failure before any Task/installation existed.
 assert not list(old.glob('Tasks/Task-*')) and not (old/'.agents').exists()
 new.mkdir(parents=True,exist_ok=True);old.mkdir(parents=True,exist_ok=True)
 (old/'AGENTS.md').write_text('# Existing customized instructions\nKeep product-specific guidance and contents.\n');(old/'ROLE.md').write_text('# Existing customized role\nRetain local ownership choices.\n')
 (old/'README.md').write_text('Existing product content, unrelated to selected package adoption.\n')
 write(old/'control_records/project-setup.json',{'synthetic':True,'contract':'governance-starter-v3','source':'historical setup fixture','meaning':'Earlier edition preserved; selected package adoption does not relabel it.'})
 # Existing owner preflight requires SOUL; retain exact Template bytes before creating history.
 shutil.copyfile(T/'SOUL.md',old/'SOUL.md')
 # Produce preserved historical canonical Task with the actual Template owner, not hand editing state.
 (old/'Tasks').mkdir(exist_ok=True);(old/'Tasks/INDEX.md').write_text(harness.task_state.render_index_markdown([], '2026-09-08T00:00:00+00:00'))
 p=subprocess.run([sys.executable,str(T/'.agents/skills/agent-task/scripts/task_state.py'),'--project-root',str(old),'--format','json','new'],input=json.dumps({'name':'Preserved historical synthetic Task','description':'Historical fixture state before package adoption.','definition_of_done':['Preserve historical semantics.']}),capture_output=True,text=True);assert p.returncode==0,p.stdout+p.stderr
 historical=tree(old)
 # A conflicting selected target is refused before any file is changed. It remains customized.
 collision=old/'.agents/skills/collaborate/references/commands.md';collision.parent.mkdir(parents=True);collision.write_text('Customized selected target must not be overwritten.\n')
 
 def preview(root,files):
  changes=[];conflicts=[]
  for source in files:
   relative=str(source.relative_to(T));target=root/relative; h=sha(source)
   if target.exists() and sha(target)!=h:conflicts.append({'source':str(source.relative_to(R)),'destination':str(target.relative_to(R)),'existing_sha256':sha(target),'source_sha256':h})
   changes.append({'source':str(source.relative_to(R)),'destination':str(target.relative_to(R)),'sha256':h,'action':'identical' if target.exists() and sha(target)==h else 'absent' if not target.exists() else 'conflict'})
  return {'source':str(T),'destination':str(root),'files':changes,'conflicts':conflicts,'overwrite':'Only absent or byte-identical selected targets; customized selected targets refuse atomically.','preservation':'Unrelated guidance/content, existing setup edition and canonical historical Task bytes.','synthetic':True}
 rejected=preview(old,selected); before_refusal=tree(old);assert rejected['conflicts'] and tree(old)==before_refusal
 # Keep the conflicting file intact in the same fixture; select no package installation until authorized resolution.
 # Fixture owner resolves this *synthetic* collision by explicitly preserving it outside the selected package.
 preserved_collision=old/'preserved-selected-customization/commands.md';preserved_collision.parent.mkdir();shutil.move(collision,preserved_collision)
 assert sha(preserved_collision)==before_refusal[str(collision.relative_to(old))]
 new_files=selected+[T/'AGENTS.md',T/'ROLE.md'];new_preview=preview(new,new_files);old_preview=preview(old,selected)
 assert not new_preview['conflicts'] and not old_preview['conflicts']
 write(D/'previews.json',{'new':new_preview,'existing_conflict_refusal':rejected,'existing_after_explicit_synthetic_collision_preservation':old_preview,'collision_disposition':'Original customized bytes preserved verbatim outside the selected helper package, then absent target adopted. No real project file moved.'})
 for root,files in [(new,new_files),(old,selected)]:
  for source in files:
   target=root/source.relative_to(T);target.parent.mkdir(parents=True,exist_ok=True)
   if not target.exists():shutil.copyfile(source,target)
   assert sha(target)==sha(source)
 for p,h in historical.items():assert sha(old/p)==h
 write(D/'depot/depot/projects.json',{'schema_version':1,'synthetic':True,'projects':[{'id':'new-project','path':str(new),'name':'New disposable collaboration package fixture'},{'id':'existing-project','path':str(old),'name':'Existing disposable collaboration package fixture'}]})
else:
 new_files=selected+[T/'AGENTS.md',T/'ROLE.md'];preserved_collision=old/'preserved-selected-customization/commands.md'
 historical={str(p.relative_to(old)):sha(p) for p in old.rglob('*') if p.is_file() and (p.relative_to(old).parts[0] in ('Tasks','control_records') or str(p.relative_to(old)) in ('AGENTS.md','ROLE.md','README.md','SOUL.md')) and '__pycache__' not in p.parts}

if (D/'historical-preservation-before.json').exists():historical=json.loads((D/'historical-preservation-before.json').read_text())
else:write(D/'historical-preservation-before.json',historical)

class Fixture(harness.OrchestrationTests):
 def setup_installed(self,root):
  self.root=root
  (root/'Tasks').mkdir(exist_ok=True)
  if not (root/'Tasks/INDEX.md').exists():(root/'Tasks/INDEX.md').write_text(harness.task_state.render_index_markdown([], '2026-09-08T00:00:00+00:00'))
  cp=subprocess.run([sys.executable,str(root/'.agents/skills/manage-subagent-roles/scripts/role_catalog.py'),'--repo-root',str(root),'reindex'],capture_output=True,text=True);assert cp.returncode==0,cp.stdout+cp.stderr
  cp=subprocess.run([sys.executable,str(root/'.agents/skills/manage-subagent-roles/scripts/role_catalog.py'),'--repo-root',str(root),'list','--format','json'],capture_output=True,text=True);assert cp.returncode==0,cp.stdout+cp.stderr
  (root/'catalog.json').write_text(cp.stdout);(root/'evidence.txt').write_text('Synthetic disposable adoption evidence; no actual native execution, isolation or comprehension claimed.\n')
  self.ev=self.ref('evidence.txt');self.context=[self.ev]
  self.role={'name':'task-manager','agents_path':'Roles/task-manager/AGENTS.md','role_path':'Roles/task-manager/ROLE.md','agents_sha256':self.ref('Roles/task-manager/AGENTS.md')['sha256'],'role_sha256':self.ref('Roles/task-manager/ROLE.md')['sha256'],'catalog':self.ref('catalog.json')}
  self.settings={'mode':'verified_inheritance','model':None,'effort':None,'evidence':self.context};self.runtime={'tools':['spawn_agent','list_agents','send_message','followup_task','interrupt_agent'],'depth':2,'available_slots':2,'evidence':self.context}
  prior=[p for p in root.glob('Tasks/*/task.json') if json.loads(p.read_text())['name']=='Synthetic installed adoption read and rebuild']
  if prior: cp=type('Result',(),{'returncode':0})();res={'task_folder':str(prior[0].parent)}
  else: cp,res=self.run_cli('new',payload={'name':'Synthetic installed adoption read and rebuild','description':'Active deterministic lease for bounded package check only.','definition_of_done':['Inspect derived-only rebuild.'],'orchestration_enabled':True});assert cp.returncode==0,res
  self.folder=Path(res['task_folder']);self.state=self.read_state(self.folder);self.seq=0;self.actor='/root';self.exec_id='execution1';self.generation=1
  self.seq=len(self.state['orchestration']['events'])
  if 'manager1' not in self.state['orchestration']['assignments']:
   self.event('manager.reserve',self.manager_data('manager1'));self.event('manager.receipt',{'assignment_id':'manager1','receipt':self.launch('/root/manager1')});self.event('manager.activate',{'assignment_id':'manager1','role_reads':self.reads()})
  else: assert self.state['orchestration']['assignments']['manager1']['state']=='active'
  self.actor='/root/manager1'
 def run_cli(self,command,*args,payload=None,**kwargs):return cli(self.root,command,*args,payload=payload)
 def fit(self,writes):
  f=super().fit(writes);f['reads']=['evidence.txt',str(self.folder.relative_to(self.root))];return f
 def manager_data(self,aid):
  d=super().manager_data(aid);d['fit']=self.fit([str(self.folder.relative_to(self.root)/'artifacts/orchestration/manager')]);return d

checks=[]
for root,files in [(new,new_files),(old,selected)]:
 installed={str(p.relative_to(T)):sha(root/p.relative_to(T)) for p in files}
 f=Fixture('runTest');f.setup_installed(root)
 ns=str(f.folder.relative_to(root)/'artifacts/orchestration/manager/collaboration')
 policy={'version':1,'project':str(root),'task':f.state['task_id'],'execution':f.exec_id,'generation':1,'manager':'manager1','participants':{'manager1':{'namespace':ns,'subtask_id':None}},'subtasks':{'subtask1':{'phase':'integration','audience':['manager1'],'independent_first_pass':False,'reviewer_first_pass':False,'exchange_stop':'Stop after one synthetic adoption read and rebuild.'}},'bounds':{'record_bytes':65536,'output_bytes':32768,'page_items':20},'topology':'common-store-cooperative'}
 raw=str(f.folder.relative_to(root)/'artifacts/orchestration/manager/policy.json');(root/raw).parent.mkdir(parents=True,exist_ok=True);(root/raw).write_bytes(encoded(policy));f.event('artifact.register',{'artifact_id':'policy1','assignment_id':'manager1','source_path':raw});art=f.state['orchestration']['artifacts']['policy1'];pr={'path':str(f.folder.relative_to(root)/art['path']),'sha256':art['sha256']};f.context.append(pr);f.define()
 board=Board(Context(root,str(f.folder.relative_to(root)/'task.json'),'manager1',f.actor,f.exec_id,1,pr))
 post={'operation_id':'adoption1','thread_id':'adoption','reply_to':None,'supersedes':None,'subtask':'subtask1','type':'question','title':'Synthetic adoption check','body':'Confirm installed read and explicitly derived rebuild.','phase':'integration','visibility':'findings','recipients':['manager1'],'requested_response':'Inspect then stop.','urgency':'routine','targets':[f.ev],'evidence':[],'limitations':['Synthetic, no native proof.'],'material':False}
 board.post(post);before=tree(root);view=overview([board],items=1);assert view['returned']==1 and view['remaining']==0;assert tree(root)==before
 rebuilt=rebuild_overview([board],items=1);after=tree(root);changed=[p for p,h in after.items() if before.get(p)!=h];assert changed==[rebuilt['path']]
 for p,h in installed.items():
  if p!='Roles/INDEX.md':assert sha(root/p)==h
 checks.append({'project':str(root.relative_to(R)),'synthetic':True,'installed_files':len(installed),'installed_hashes_preserved':True,'local_role_index':'Installed exact role helper regenerated navigation for selected two unchanged pairs; Template index describes six roles and cannot be reused unchanged in this minimal installation.','canonical_source':ref(root,f.folder/'task.json'),'view':view,'rebuild':rebuilt,'only_changed':changed,'read_pure':True})
 # Final read-only installed owner validation supports only the deterministic fixture state.
 cp,res=f.run_cli('validate');assert cp.returncode==0,res
for p,h in historical.items():
 if p!='Tasks/INDEX.md':assert sha(old/p)==h
# Task index includes the new synthetic Task; preserved historical canonical records/setup remain exact.
write(D/'preservation-manifest.json',{'status':'passed','checks':checks,'historical_before':historical,'historical_after':{p:sha(old/p) for p in historical if p!='Tasks/INDEX.md'},'historical_task_bytes_preserved':True,'historical_index':'Owner helper updated index to include separately generated synthetic current test Task; previous historical Task record unchanged.','customized_collision_sha256':sha(preserved_collision),'collision_refusal_changed_files':0,'role_index_disposition':'Local generated navigation reindexed with installed owner for selected role set; pair/helper/guidance bytes preserved.','registry':ref(D/'depot',D/'depot/depot/projects.json'),'live_registry_untouched':True,'limits':['Exact separately authorized package adoption manifest, not a new initializer module/edition.','No service/dependency/Git/native actor creation.','Synthetic active Task and receipts are deterministic input data only.','Current final source V4 plus overview installed; historical actual native generic V1/enabled V2 runs are separate evidence.','Exactly two disposable projects; no future-project runtime or live root/product adoption claim.']})
print(json.dumps({'status':'passed','projects':2,'checks':len(checks),'collision_refused':True,'derived_only':True}))
