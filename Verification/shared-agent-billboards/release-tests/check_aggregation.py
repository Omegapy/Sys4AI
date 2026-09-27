from pathlib import Path
import json,hashlib,sys
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'SKILLS-depo/collaborate/scripts'))
from collaboration_task import Context
from collaboration_read import Board
from collaboration_overview import overview,rebuild_overview
from collaboration_store import CollaborationError
P=ROOT/'Verification/shared-agent-billboards/pilots/project'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def protected():return {str(p.relative_to(P)):sha(p) for area in ['Tasks','Evidence'] for p in (P/area).rglob('*') if p.is_file() and '__pycache__' not in p.parts}
def refused(fn,expected):
 try:fn()
 except CollaborationError as e:assert e.code==expected;return expected
 raise AssertionError('expected refusal')
before=protected();boards=[];views=[]
for f in P.glob('Tasks/*/task.json'):
 t=json.loads(f.read_text());o=t['orchestration']
 if t['task_id'] not in ['TASK-20260926-B9F05B47','TASK-20260926-7014404F']:continue
 a=o['assignments'][o['manager_id']]
 art=next(v for k,v in o['artifacts'].items() if 'policy' in k.lower())
 policy={'path':str(f.parent.relative_to(P)/art['path']),'sha256':art['sha256']}
 c=Context(P,str(f.relative_to(P)),a['assignment_id'],a['native_id'],o['execution_id'],o['generation'],policy)
 b=Board(c);boards.append(b);v=overview([b],items=2);assert v['selected_tasks'][0]['status']=='completed'
 for e in v['entries']:
  assert sha(P/e['source']['path'])==e['source']['sha256'];assert e['task_source']['sha256']==sha(f)
 views.append({'view':v,'next_page':overview([b],offset=v['returned'],items=2),'completed_rebuild_refusal':refused(lambda:rebuild_overview([b]),'COLLAB_LEASE'),
               'unassigned_curator_refusal':refused(lambda:Context(P,str(f.relative_to(P)),'curator','/unassigned/curator',o['execution_id'],o['generation'],policy),'COLLAB_GATE')})
assert len(boards)==2
cross=refused(lambda:overview(boards),'COLLAB_IDENTITY')
# Actual one-worker sub-agent view: exact scope is enforced before Task metadata exposure.
b=next(b for b in boards if b.c.task['task_id']=='TASK-20260926-B9F05B47');c=b.c
worker=next(a for a in c.o['assignments'].values() if a['function']=='worker' and a['state']!='revoked')
w=Board(Context(P,c.task_path,worker['assignment_id'],worker['native_id'],c.o['execution_id'],c.o['generation'],c.policy_ref))
try:sub={'view':overview([w],items=2)}
except CollaborationError as e:assert e.code=='COLLAB_SCOPE';sub={'refused':'COLLAB_SCOPE','reason':'Actual worker grant omits canonical Task metadata path; role creates no access.'}
after=protected();assert before==after
result={'status':'passed','source_root':str(P),'checks':{'separate_actual_manager_views':views,'cross_actor_union_refused':cross,'actual_subagent_scope':sub,'source_receipt_task_hashes_unchanged':True,'protected_files':len(before)},'limits':['Two distinct native managers are separate views, not one universally authorized viewer.','Unassigned Director/Curator has no Task binding.','Completed boards remain read-only; active disposable adoption fixture exercises derived rebuild.','No repeated native run or unchanged helper suite.']}
(ROOT/'Verification/shared-agent-billboards/aggregation-evidence.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'status':'passed','files_unchanged':len(before),'views':len(views),'entries':[v['view']['total'] for v in views],'cross_actor':cross,'subagent':list(sub)}))
