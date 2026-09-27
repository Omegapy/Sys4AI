"""Freeze one reviewed current security job in a fresh owned disposable root."""
from pathlib import Path
import hashlib,json,stat,sys
root=Path(__file__).resolve().parents[3];out=Path(__file__).resolve().parent
number=sys.argv[1];assert len(number)==2 and number.isdigit()
stage=Path('/private/tmp/explorer-qualification-security-'+number);stage.mkdir()
paths=list((root/'SKILLS-depo/ontology/scripts').glob('ontology*.py'))
paths.extend(root/'SKILLS-depo/ontology/tests'/n for n in ['test_explorer_service.py','test_explorer_security.py','support.py','explorer_support.py'])
paths.extend(p for p in (root/'ONTOLOGY-depo').rglob('*') if p.is_file() and '__pycache__' not in p.parts)
paths.extend(root/'SKILLS-depo/ontology/explorer'/n for n in ['package.json','package-lock.json','THIRD_PARTY_NOTICES.md','BUILD.md'])
paths.extend(p for p in (root/'SKILLS-depo/ontology/explorer/assets').rglob('*') if p.is_file())
rows=[]
for p in sorted(set(paths)):
    st=p.lstat();assert stat.S_ISREG(st.st_mode) and st.st_nlink==1 and not any(x.is_symlink() for x in [p,*p.parents])
    raw=p.read_bytes();relative=p.relative_to(root);dest=stage/relative;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    rows.append({'path':str(relative),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)})
raw=(out/'host-security-runner.py').read_bytes();(stage/'host-security-runner.py').write_bytes(raw)
rows.append({'path':'host-security-runner.py','sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)})
manifest=(json.dumps({'files':rows},indent=2)+'\n').encode();(stage/'inputs.json').write_bytes(manifest);(out/('stage-security-'+number+'.json')).write_bytes(manifest)
tools=[]
for p in [root/'.venv/bin/python',Path('/bin/ps')]:
    actual=p.resolve();raw=actual.read_bytes();tools.append({'path':str(p),'resolved':str(actual),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)})
job={'command':[str(root/'.venv/bin/python'),'-I','-B',str(stage/'host-security-runner.py')],
 'staging_root':str(stage),'manifest':{'path':str(stage/'inputs.json'),'sha256':hashlib.sha256(manifest).hexdigest()},'external_tools':tools,
 'timeout_seconds':300,'inputs_count':len(rows),'source_writes':False,'intended_writes':['Owned /private/tmp/explorer-http-* fixtures and services only; test mutations target only those synthetic roots. Every service/child is reaped.'],
 'credentials':'Private files and process memory only; no raw URL, headers, responses or exception values in evidence.',
 'scenarios':['AT-24 closed write families','AT-25 hostile credentials and two namespaces','AT-26 source/path authority','AT-27 inert wire and strict CSP','actual in-process Reader forbidden-call audit; browser malicious-text behavior follows separately']}
p=out/('host-security-'+number+'.json');p.write_text(json.dumps(job,indent=2)+'\n');print(json.dumps({'job':str(p.relative_to(root)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'manifest':job['manifest'],'inputs_count':len(rows)}))
