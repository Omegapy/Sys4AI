"""Run only after Main's explicit settled-evidence comparison clearance."""
from manager_driver import *
from datetime import datetime,timezone
import os,stat

def snapshot(path,excluded):
 p=Path(path)
 for q in [p,*p.parents]:
  if q.exists() and q.is_symlink():raise RuntimeError('symlink in protected ancestor')
 if not p.exists():return {'state':'absent','sha256':None,'file_count':0}
 info=p.lstat()
 if stat.S_ISREG(info.st_mode):return {'state':'regular-file','sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'file_count':1}
 if not stat.S_ISDIR(info.st_mode):raise RuntimeError('special protected target')
 rows=[]
 for cur,dirs,files in os.walk(p,followlinks=False):
  dirs[:]=sorted(q for q in dirs if q not in excluded)
  for name in dirs:
   q=Path(cur)/name;s=q.lstat()
   if not stat.S_ISDIR(s.st_mode) or stat.S_ISLNK(s.st_mode):raise RuntimeError('unsafe protected directory')
  for name in sorted(files):
   if name in excluded:continue
   q=Path(cur)/name;s=q.lstat()
   if not stat.S_ISREG(s.st_mode):raise RuntimeError('unsafe protected file')
   rows.append([str(q.relative_to(p)),hashlib.sha256(q.read_bytes()).hexdigest(),s.st_size])
 raw=json.dumps(rows,ensure_ascii=False,separators=(',',':')).encode()
 return {'state':'directory','sha256':hashlib.sha256(raw).hexdigest(),'file_count':len(rows)}

def compare(name,clearance_refs):
 baseline=AREA/'bounded-protected-baseline.json';b=json.loads(baseline.read_text());rows=[]
 # Aggregate recipe is identified from frozen original worker metadata, not a rebaseline.
 frozen=json.loads((CHILD/'Verification/mathematics-initialization/foundation-work/protected-file-inventories.json').read_text());role_entries=[[x['path'],x['sha256'],x['size']] for x in frozen['ROLES-depo']['entries'] if x['type']=='file'];role_entries.sort(key=lambda x:x[0]);role_hash=hashlib.sha256(json.dumps(role_entries,ensure_ascii=False,separators=(',',':')).encode()).hexdigest();assert role_hash==next(x['sha256'] for x in b['protected_paths'] if x['path']==str(ROOT/'ROLES-depo'))
 for v in b['protected_paths']:
  p=Path(v['path']);p=p if p.is_absolute() else CHILD/p;s=snapshot(p,set(b['excluded_names']));same=all(s[k]==v[k] for k in ['state','sha256','file_count']);rows.append({'path':v['path'],'resolved_path':str(p),'baseline_state':v['state'],'baseline_sha256':v['sha256'],'baseline_file_count':v['file_count'],'current':s,'preserved':same,'observation_source':'Root manager actual no-follow comparison to original frozen baseline','evidence':'Current exact state, aggregate/file SHA256 and regular-file count equal original baseline.' if same else 'Current protected bytes differ; no automatic rollback or preservation claim.'})
 reg=json.loads((ROOT/'depot/projects.json').read_text());old=b['registry_existing_entries'];existing=all(x in reg['projects'] for x in old['projects']);sameheader=all(reg.get(k)==v for k,v in old.items() if k!='projects');added=[x for x in reg['projects'] if x not in old['projects']];math=[x for x in added if x.get('id')=='sys4ai-mathematics'];registry={'old_entries_preserved_exactly':existing,'old_nonproject_fields_preserved':sameheader,'additional_entries':added,'only_one_math_entry_added':len(added)==1 and len(math)==1,'math_real_identity':json.loads((CHILD/'project.json').read_text()),'current_registry':ref(ROOT/'depot/projects.json')};assert len(math)==1;registry['math_path_matches_real_project']=math[0]['path']=='Projects/Sys4AI-Mathematics'
 exceptions=[]
 for n in ['sequential-reservation-withdrawal-applied-20260928.json','sequential-subtask-retirement-applied-20260928.json']:
  p=CHILD/'control_records/mathematics/foundation-owner-grants'/n;j=json.loads(p.read_text());exceptions.append({'kind':'Authorized child-local exact owner correction; no reusable propagation','evidence':ref(p),'operation':j.get('operation'),'file_chain':[{'path':q['path'],'before_sha256':q['before_sha256'],'after_sha256':q['after_sha256']} for q in j.get('files',[])]})
 latest=json.loads((CHILD/'control_records/mathematics/foundation-owner-grants/sequential-subtask-retirement-applied-20260928.json').read_text());current_child_repairs=[{'path':str((CHILD/q['path']).relative_to(ROOT)),'expected':q['after_sha256'],'actual':ref(CHILD/q['path'])['sha256'],'matches':ref(CHILD/q['path'])['sha256']==q['after_sha256']} for q in latest['files']]
 context=json.loads((AREA/'setup-guard-repair-context.json').read_text());guard=ROOT/'.agents/skills/ontology/scripts/ontology_guards.py';root_guard={'kind':'Host-owned installed root ontology guard/module compatibility repair via reviewed public preview/apply; source/Template c2f632… unchanged','evidence':ref(AREA/'setup-guard-repair-context.json'),'installed_guard':ref(guard),'expected_guard_sha256':context['active_installed_owner_guard_sha256'],'current_matches_exact_authorized_postimage':ref(guard)['sha256']==context['active_installed_owner_guard_sha256'],'immutable_receipt':ref(ROOT/'control_records/ontology/guard-bootstrap/ONTGUARD-math-init-modules-20260928-receipt.json'),'advanced_config':ref(ROOT/'ontology-advanced.yaml')}
 observed=datetime.now(timezone.utc).isoformat();ok=all(x['preserved'] for x in rows) and existing and sameheader and registry['only_one_math_entry_added'] and registry['math_path_matches_real_project'] and all(x['matches'] for x in current_child_repairs) and root_guard['current_matches_exact_authorized_postimage'];out={'observed_at':observed,'status':'preserved_with_explicit_authorized_project_local_owner_changes' if ok else 'comparison_failed_requires_exact_disposition','original_baseline':ref(baseline),'clearance_and_settled_inputs':clearance_refs,'procedure':b['procedure'],'exclusions_exactly_reused':b['excluded_names'],'aggregate_recipe':'Original os.walk traversal with sorted directory names and per-directory sorted file names; regular-file [relative_path,sha256,size] triples in traversal order; UTF-8 compact JSON without trailing newline. Reproduces every original12 directory aggregate; flat ROLES-depo alone did not distinguish traversal from global sorting. Initial global-sort diagnostic retained separately; no new baseline. No symlink/special targets followed.','protected_paths':rows,'registry':registry,'root_owner_correction':root_guard,'child_owner_correction_chain':exceptions,'current_child_repair_postimages':current_child_repairs,'scope':'Only actual protected-path/registry/current authorized-owner postimage verification. Root/child Task and plan are read-only; no product, Git, installation, global or child memory write.','other_work':'Known unrelated root work and memory remain preserved; whole repository is not declared clean.','all_required_protected_paths_preserved':ok};p=save(name,out);print(json.dumps({'evidence':p,'observed_at':observed,'status':out['status'],'protected_paths':len(rows),'mismatches':[x['path'] for x in rows if not x['preserved']],'registry_ok':registry['only_one_math_entry_added'] and existing and sameheader,'root_guard_ok':root_guard['current_matches_exact_authorized_postimage'],'child_repairs_ok':all(x['matches'] for x in current_child_repairs)},indent=2),flush=True);return out,p
