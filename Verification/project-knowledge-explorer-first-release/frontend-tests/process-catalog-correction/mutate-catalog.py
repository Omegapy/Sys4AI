"""One exact disposable canonical label mutation, preserving every other value."""
import json,sys,copy
from pathlib import Path
root=Path(sys.argv[1]);relative=sys.argv[2];ident=sys.argv[3]
assert root.is_absolute() and str(root).startswith('/private/tmp/explorer-http-')
cfg=json.loads((root/'ontology.yaml').read_text());assert relative in cfg['project_files'] and ident==cfg['project']['namespace']+'entry-00014'
p=root/relative;assert p.is_file() and not p.is_symlink();doc=json.loads(p.read_text());before=copy.deepcopy(doc)
changed=[r for r in doc['@graph'] if r['@id']==ident];assert len(changed)==1 and changed[0]['label']=='Fixture ordered inspection';changed[0]['label']='Refreshed ordered inspection'
expected=copy.deepcopy(before)
for row in expected['@graph']:
 if row['@id']==ident:row['label']='Refreshed ordered inspection'
assert expected==doc
p.write_text(json.dumps(doc,ensure_ascii=False));assert json.loads(p.read_text())==expected
print(json.dumps({'status':'passed','only_selected_label_changed':True,'changed_file':relative}))
