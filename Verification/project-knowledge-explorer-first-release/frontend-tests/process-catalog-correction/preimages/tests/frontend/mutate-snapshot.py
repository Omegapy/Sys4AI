"""Lossless numeric fixture mutation limited to two named canonical fields."""
import copy,hashlib,json,os,stat,sys
from pathlib import Path
root=Path(sys.argv[1]).resolve(strict=True)
assert root.name=='project' and root.parent.parent==Path('/private/tmp') and root.parent.name.startswith('explorer-http-')
def read(relative):
 path=root/relative;assert path.is_relative_to(root)
 fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
 try:
  st=os.fstat(fd);assert stat.S_ISREG(st.st_mode) and st.st_nlink==1 and st.st_size<=2000000
  raw=os.read(fd,2000001);assert len(raw)==st.st_size
 finally:os.close(fd)
 return path,raw,json.loads(raw)
if len(sys.argv)>2:
 assert sys.argv[2]=='policy'
 path,raw,value=read('ontology-explorer.yaml');before=copy.deepcopy(value)
 value['categories']=[];value['limits'].update(page_items=3,display_nodes=10,display_edges=10,response_bytes=16000)
 expected=copy.deepcopy(before);expected['categories']=[];expected['limits'].update(page_items=3,display_nodes=10,display_edges=10,response_bytes=16000);assert value==expected
 fd=os.open(path,os.O_WRONLY|os.O_TRUNC|os.O_NOFOLLOW)
 try:
  assert os.fstat(fd).st_nlink==1
  with os.fdopen(os.dup(fd),'w') as stream:json.dump(value,stream)
 finally:os.close(fd)
 print(json.dumps({'status':'passed','only_presentation_category_and_lowered_policy_changed':True}));raise SystemExit(0)
_,_,cfg=read('ontology.yaml');ns=cfg['project']['namespace'];selected={ns+'entry-00000':['label'],ns+'relation-000000':['qualifiers','object']};changed=[];target_count=0
for relative in cfg['project_files']:
 path,raw,value=read(relative);before=copy.deepcopy(value);touched=[]
 for record in value['@graph']:
  fields=selected.get(record['@id'])
  if fields:
   for field in fields:record[field]='Refreshed Alignment' if field=='label' else ns+'entry-00037' if field=='object' else {'condition':'Refreshed condition remains attached to this relationship.'}
   touched.append((record['@id'],fields));target_count+=1
 if not touched:continue
 for old,new in zip(before['@graph'],value['@graph']):
  fields=selected.get(old['@id']);expected=copy.deepcopy(old)
  if fields:
   for field in fields:expected[field]=new[field]
  assert expected==new
  if old['@id']==ns+'relation-000005':assert old['qualifiers']['count']==new['qualifiers']['count']==9007199254740993
 assert {k:v for k,v in before.items() if k!='@graph'}=={k:v for k,v in value.items() if k!='@graph'}
 after=json.dumps(value,ensure_ascii=False).encode();assert len(after)<=2000000
 fd=os.open(path,os.O_WRONLY|os.O_TRUNC|os.O_NOFOLLOW)
 try:
  assert os.fstat(fd).st_nlink==1
  with os.fdopen(os.dup(fd),'wb') as stream:stream.write(after)
 finally:os.close(fd)
 changed.append({'path':relative,'fields':touched,'before_sha256':hashlib.sha256(raw).hexdigest(),'after_sha256':hashlib.sha256(after).hexdigest()})
assert target_count==2
print(json.dumps({'status':'passed','only_selected_fields_changed':True,'unsafe_integer_preserved':True,'files':changed}))
