from pathlib import Path
import importlib.util,sys,json
root=Path('/Volumes/P-SSD/AngryOwl/Sys4AI')
sp=importlib.util.spec_from_file_location('pke_plan_owner',root/'.agents/skills/to-implementation-plan/scripts/plan_state.py');m=importlib.util.module_from_spec(sp);sys.modules[sp.name]=m;sp.loader.exec_module(m)
c=m.resolve_context(str(root),'Implementation_Plans')
v=json.loads(Path(sys.argv[1]).read_text());p=m.normalize_plan_input(v,c)
d=m.parse_timestamp(p['created_at'],'created_at');p['plan_id']=f'PLAN-{d.strftime("%Y%m%d")}-A1B2C3D4'
p['history']=[{'revision':1,'timestamp':p['created_at'],'action_id':'TO-IP-001','affected_ids':[p['plan_id'],*m.stable_record_ids(p)],'status_before':None,'status_after':'draft','summary':'Read-only preflight normalized candidate.','authority_basis':'Explicit user planning operation; in-memory validation only.'}]
m.refresh_validation(p,p['updated_at']);err=m.validate_plan_structure(p,c)
print(json.dumps({'canonical_write':False,'structure_errors':err,'validation':p['validation']},indent=2))
