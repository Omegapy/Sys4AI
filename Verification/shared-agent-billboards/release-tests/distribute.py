from pathlib import Path
import importlib.util,hashlib,json,subprocess,sys
R=Path(__file__).resolve().parents[3];V=R/'Verification/shared-agent-billboards';T=R/'Projects/Sys4AI-Template-Project'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,obj):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,indent=2)+'\n')
spec=importlib.util.spec_from_file_location('exact_release_updater',R/'tools/template_update.py');u=importlib.util.module_from_spec(spec);spec.loader.exec_module(u)
snapshot=u.snapshot(R);preview=u.plan(R,u.load_state(R),snapshot['state'])
allowed={'.agents/skills/agent-task/references/orchestration-contract.md','.agents/skills/task/SKILL.md','AGENTS.md','ROLE.md','Roles/INDEX.md','Roles/project-sub-agent/AGENTS.md','Roles/project-sub-agent/ROLE.md','Roles/task-manager/AGENTS.md','Roles/task-manager/ROLE.md'}
assert not preview['conflicts'] and not preview['deletions'] and not preview['adoptions']
assert all(p.startswith('.agents/skills/collaborate/') or p in allowed for p in preview['additions']+preview['updates'])
skills=('collaborate','agent-task','task','manage-subagent-roles','communication')
selected={p:e for p,e in snapshot['state']['files'].items() if p in allowed or any(p.startswith('.agents/skills/'+s+'/') for s in skills)}
manifest=[]
for dest,e in selected.items():
 source=e['source']; manifest.append({'source':source,'destination':'Projects/Sys4AI-Template-Project/'+dest,'sha256':e['sha256'],'generated':dest=='Roles/INDEX.md','before_sha256':sha(T/dest) if (T/dest).exists() else None})
assert not any('/messages/' in x['destination'] or '/receipts/' in x['destination'] or '/Tasks/' in x['destination'] or '.sys4ai' in x['destination'] for x in manifest)
review={'reviewed':True,'preview':preview,'manifest':manifest,'mapping_sha256':sha(R/'depot/template-update.json'),'starter_policy_sha256':sha(R/'SKILLS-depo/init-new-project/assets/baseline-assets.json'),'boundary':'Exact selected current source/guidance/dependency bytes; only established updater owns mapped Template writes. Dynamic discovery reused; no mapping/edition changes.'}
write(V/'release-tests/distribution-preview-v2.json',review)
proc=subprocess.run([sys.executable,str(R/'tools/template_update.py'),'apply'],cwd=R,capture_output=True,text=True)
assert proc.returncode==0,proc.stdout+proc.stderr
applied=json.loads(proc.stdout)
assert applied['status'] in ('applied','current') and not applied['conflicts']
proc2=subprocess.run([sys.executable,str(R/'tools/template_update.py'),'check'],cwd=R,capture_output=True,text=True)
assert proc2.returncode==0,proc2.stdout+proc2.stderr
checked=json.loads(proc2.stdout);assert checked['status']=='current'
for x in manifest:assert sha(R/x['destination'])==x['sha256']
assert sha(R/'depot/template-update.json')==review['mapping_sha256'];assert sha(R/'SKILLS-depo/init-new-project/assets/baseline-assets.json')==review['starter_policy_sha256']
write(V/'distribution-manifest.json',{'status':'passed','review':{'path':str((V/'release-tests/distribution-preview-v2.json').relative_to(R)),'sha256':sha(V/'release-tests/distribution-preview-v2.json')},'apply':{'command':'.venv/bin/python tools/template_update.py apply','exit_code':proc.returncode,'result':applied},'final_check':{'command':'.venv/bin/python tools/template_update.py check','exit_code':proc2.returncode,'result':checked},'files':manifest,'all_exact':True,'neutral_starter':'Static package/guidance/tests only; no populated Task/post/receipt/native bindings, grants or runtime copied. Source tests contain explicitly synthetic examples.','initializer':'Existing schema2 dynamic skill inventory; current edition retained without modification.','scope':'Template only; active depot root, live registry/products and Aether-Flow not adopted.'})
print(json.dumps({'status':'passed','files':len(manifest),'apply':applied['status'],'final':checked['status']}))
