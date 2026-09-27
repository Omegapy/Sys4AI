"""Bounded native-pilot calls; canonical state is owned by the installed helper."""
import sys,json,pathlib,hashlib,subprocess,datetime
sys.path.insert(0,'/Volumes/P-SSD/AngryOwl/Sys4AI/Tasks/Task-implement-shared-agent-billboards-revision-1-2026-09-26--7F3F57E1/artifacts/orchestration/manager')
import fixture_driver as f
ROOT=pathlib.Path('/Volumes/P-SSD/AngryOwl/Sys4AI/Verification/shared-agent-billboards/pilots/project')
TASK='TASK-20260926-7014404F'; ACTOR='/root/billboards_manager/enabled_manager'; EXEC='EXEC_CLOCK_ENABLED'
FOLDER='Tasks/Task-clock-rule-billboard-enabled-native-pilot-2026-09-26--7014404F'; MAN=FOLDER+'/artifacts/orchestration/manager'; WORK=FOLDER+'/artifacts/orchestration/work'
def state():return f.state(ROOT,TASK)[1]
def ref(path):return f.ref(ROOT,path)
def write(name,obj):
 p=ROOT/MAN/name;p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():raise ValueError('Evidence exists')
 p.write_text(json.dumps(obj,indent=2)+'\n');return ref(p)
def event(kind,data,summary):return f.event(ROOT,TASK,ACTOR,EXEC,1,kind,data,summary)
def artifact(aid,owner,path):
 event('artifact.register',dict(artifact_id=aid,assignment_id=owner,source_path=path),'Preserve exact '+aid+' evidence.')
 a=state()['orchestration']['artifacts'][aid];return {'path':FOLDER+'/'+a['path'],'sha256':a['sha256']}
def role(aid):
 aid=aid+'-'+str(state()['revision'])
 p=subprocess.run(['/Volumes/P-SSD/AngryOwl/Sys4AI/.venv/bin/python',str(ROOT/'.agents/skills/manage-subagent-roles/scripts/role_catalog.py'),'--repo-root',str(ROOT),'list','--format','json'],capture_output=True,text=True,check=True)
 cat=write('catalog-'+aid+'.json',json.loads(p.stdout))
 return dict(name='project-sub-agent',agents_path='Roles/project-sub-agent/AGENTS.md',role_path='Roles/project-sub-agent/ROLE.md',agents_sha256=ref('Roles/project-sub-agent/AGENTS.md')['sha256'],role_sha256=ref('Roles/project-sub-agent/ROLE.md')['sha256'],catalog=cat)
def runtime(name,roster):
 name=name+'-'+str(state()['revision'])
 r=write('runtime-'+name+'.json',{'native_receipt':{'tool':'collaboration.list_agents','result':roster},'settings':'Verified full-history exact model/effort inheritance with no defaults/custom overrides; omit overrides. Context excludes sibling drafts/verdicts until dispatch barriers.','available_slots':1,'depth':4})
 return dict(tools=['spawn_agent','list_agents','send_message','followup_task','interrupt_agent'],depth=4,available_slots=1,evidence=[r])
def reserve(aid,slot,perspective,roster,extra=[]):
 s=state()['orchestration']['subtasks']['CLOCK']; baseline=ref(FOLDER+'/artifacts/orchestration/baseline_'+s['digest']+'.json')
 r=role(aid);run=runtime(aid,roster)
 pol=state()['orchestration']['artifacts']['POLICY_V1'];polref={'path':FOLDER+'/'+pol['path'],'sha256':pol['sha256']}
 context=[baseline,*s['baseline']['inputs'],*extra]
 fit=dict(objective='One complete bounded '+slot+' clock-rule function under frozen criteria.',capabilities=['algebra and dimensional reasoning','bounded evidence reporting'],reads=['SOUL.md','AGENTS.md','ROLE.md','SPECS.md','Roles/project-sub-agent','.agents/skills/collaborate',FOLDER+'/task.json',FOLDER+'/artifacts/orchestration', 'clock-rule-packet.json','comparison-protocol.json'],writes=[WORK+'/'+aid],deliverable='Own exact candidate/review/coherent synthesis and checkpoint evidence; path/hash/status only until dispatch barrier.',tools=['exec_command'],skills=['collaborate'],authority='Analysis and own immutable evidence/board only; no ledger, role index, source/publication/external/nested authority.',risk='Preserve initial independence and exact current target versions.',stop='One required output under all frozen criteria; mandatory targeted correction only.',rationale='Fresh project-sub-agent pair expressly supports distinct '+slot+' function; only elementary algebra required.')
 event('assignment.reserve',dict(assignment_id=aid,subtask_id='CLOCK',slot=slot,role=r,fit=fit,runtime=run,settings=state()['orchestration']['settings'],context=context),'Reserve distinct '+aid+' with fresh role/current input evidence.')
 return dict(assignment=aid,role=r,context=context,policy=polref,baseline=s['digest'],round=s['round'],perspective=perspective)
def receipt(aid,native):event('assignment.receipt',dict(assignment_id=aid,receipt={'tool':'collaboration.spawn_agent','result':{'task_name':native}}),'Record actual native '+aid+' receipt.')
def reads(aid):
 a=state()['orchestration']['assignments'][aid]
 event('assignment.reads',dict(assignment_id=aid,role_reads=dict(agents_sha256=a['role']['agents_sha256'],role_sha256=a['role']['role_sha256'],evidence='Actual native child explicitly acknowledged both complete role files, SOUL and exact registered policy/frozen packet.')),'Bind actual '+aid+' role-read acknowledgment.')
def observe(aid,roster,changes=[]):event('assignment.observe',dict(assignment_id=aid,receipt={'tool':'collaboration.list_agents','result':roster},changes=changes),'Observe actual '+aid+' native state and exact outputs.')
def board(aid='enabled_manager'):
 sys.path.insert(0,str(ROOT/'.agents/skills/collaborate/scripts'))
 from collaboration_task import Context
 from collaboration_read import Board
 a=state()['orchestration']['assignments'][aid];pol=state()['orchestration']['artifacts']['POLICY_V1']
 return Board(Context(str(ROOT),FOLDER+'/task.json',aid,a['native_id'],EXEC,1,{'path':FOLDER+'/'+pol['path'],'sha256':pol['sha256']}))
