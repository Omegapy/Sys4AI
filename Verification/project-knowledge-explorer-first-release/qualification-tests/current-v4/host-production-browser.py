"""Frozen disposable test executor: outputs evidence, edits no project files."""
import hashlib,importlib.abc,importlib.util,io,json,os,signal,stat,subprocess,sys,time,types,unittest
from pathlib import Path
stage=Path(__file__).resolve().parent
manifest=json.loads((stage/'inputs.json').read_text())
def verify():
    for item in manifest['files']:
        p=stage/item['path'];s=p.lstat()
        assert stat.S_ISREG(s.st_mode) and s.st_nlink==1
        assert hashlib.sha256(p.read_bytes()).hexdigest()==item['sha256'],item['path']
verify();sys.dont_write_bytecode=True
scripts=stage/'SKILLS-depo/ontology/scripts';tests=stage/'SKILLS-depo/ontology/tests'
known={row['path']:row['sha256'] for row in manifest['files']}
class Source(importlib.abc.MetaPathFinder,importlib.abc.Loader):
    def find_spec(self,name,path=None,target=None):
        p=(scripts/name).with_suffix('.py') if name.startswith('ontology') else (tests/name).with_suffix('.py')
        if p.is_file() and str(p.relative_to(stage)) in known:return importlib.util.spec_from_file_location(name,p,loader=self)
        return None
    def create_module(self,spec):return None
    def exec_module(self,module):
        p=Path(module.__spec__.origin);raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()==known[str(p.relative_to(stage))]
        module.__file__=str(p);exec(compile(raw,str(p),'exec',dont_inherit=True),module.__dict__)
sys.meta_path.insert(0,Source())
import test_explorer_service

def process_snapshot():
    observed=subprocess.run(['/bin/ps','-axo','pid=,ppid=,lstart='],capture_output=True,text=True,timeout=2)
    rows={}
    for line in observed.stdout.splitlines():
        parts=line.split(None,2)
        if len(parts)==3 and parts[0].isdigit() and parts[1].isdigit():rows[int(parts[0])]=(int(parts[1]),parts[2])
    return rows

def remember_descendants(pid,known):
    rows=process_snapshot();front={pid};seen=set()
    while front:
        found={child for child,(parent,stamp) in rows.items() if parent in front and child not in seen}
        seen.update(found)
        for child in found:known[child]=rows[child][1]
        front=found

def cleanup_descendants(known):
    count=0
    for sig,wait in ((signal.SIGTERM,2),(signal.SIGKILL,2)):
        rows=process_snapshot()
        alive=[pid for pid,stamp in known.items() if pid in rows and rows[pid][1]==stamp]
        if not alive:return count,True
        for pid in alive:
            try:os.kill(pid,sig);count+=1
            except ProcessLookupError:pass
        end=time.monotonic()+wait
        while time.monotonic()<end:
            rows=process_snapshot()
            if not any(pid in rows and rows[pid][1]==known[pid] for pid in alive):return count,True
            time.sleep(.05)
    rows=process_snapshot()
    return count,not any(pid in rows and rows[pid][1]==stamp for pid,stamp in known.items())


assert len(sys.argv)==1 or sys.argv[1:]==['--fixture-check']
def specialize(h):
    # Explicit setup writes only this fresh synthetic fixture before inventory.
    (h.root/'ontology-advanced.yaml').unlink()
    (h.root/'MEMORY').mkdir();(h.root/'MEMORY/fixture.md').write_text('Synthetic retained memory. No browser authority.\n')
    (h.root/'memory.yaml').write_text('schema_version: 1\nfixture_marker: preserved\n')
    from ontology_wiki import build_wiki
    generated=build_wiki(h.root)
    assert generated['status']=='complete'
    manifest_path=h.root/generated['manifest']['path'];manifest_bytes=manifest_path.read_bytes()
    owned=json.loads(manifest_bytes);assert owned['operation']=='build-wiki'
    changed='ONTOLOGY/WIKI/INDEX.md';missing='ONTOLOGY/WIKI/concepts.md'
    assert changed in owned['outputs'] and missing in owned['outputs']
    assert hashlib.sha256((h.root/changed).read_bytes()).hexdigest()==owned['outputs'][changed]
    assert hashlib.sha256((h.root/missing).read_bytes()).hexdigest()==owned['outputs'][missing]
    with (h.root/changed).open('a') as f:f.write('\nExplicit test setup made this generated index stale.\n')
    (h.root/missing).unlink()
    assert manifest_path.read_bytes()==manifest_bytes
    h.generated_state={'setup_owner':'ontology_wiki.build_wiki -> ontology_build.write_generated','setup_status':generated['status'],
      'ownership_manifest':generated['manifest'],'generated_output_count':len(owned['outputs']),
      'recorded_owned_hashes':{changed:owned['outputs'][changed],missing:owned['outputs'][missing]},
      'present_stale':[changed,generated['manifest']['path']],'absent':[missing],
      'actual_stale_index_sha256':hashlib.sha256((h.root/changed).read_bytes()).hexdigest(),
      'qualification':'Actual generator ran only in explicit disposable fixture setup. Original ownership manifest retained; listed index then altered and listed concepts.md removed before the read baseline.'}
    h.optional_absent=['ontology-advanced.yaml','ontology-semantic.yaml','ontology-standards.yaml','.venv-ontology-standards']
def query_expectations(h):
    from ontology_core import load_project
    from ontology_retrieval import ranked,tokens,normalize
    selected=load_project(h.root,validate=False);result={}
    for query in ('FixtureTaskManager','Orientation',h.ids['camelcase'],'coordinates'):
        rows=[]
        for rank,record in ranked(selected,query):
            if record['kind']=='binding' or record['lifecycle']!='approved' or record['fact_kind']!='asserted':continue
            fields={name:tokens(value) for name,value in {'label':record['label'],'aliases':' '.join(record.get('aliases',[])),'definition':record['definition'],'scope_note':record.get('scope_note','')}.items()}
            overlaps={name:sorted(tokens(query)&words) for name,words in fields.items() if tokens(query)&words}
            assert rank[2]!='lexical' or overlaps
            aliases=[a for a in record.get('aliases',[]) if normalize(a)==normalize(query)]
            rows.append({'id':record['@id'],'label':record['label'],'reason':rank[2],'canonical_rank':[rank[0],-rank[1],record['@id']],
              'matched_alias':aliases[0] if rank[2]=='alias' else None,'field_overlap_proof':overlaps,
              'label_requires_detail':len(record['label'])>4096 or len(record['label'].encode())>16384})
        result[query]=rows
    return result
h=test_explorer_service.Harness(identity='explorer-alpha',limits={'page_items':7},mutator=specialize)
if sys.argv[1:]==['--fixture-check']:
    print(json.dumps({'status':'passed','generated_state':h.generated_state,'fixture_files':len(h.before),'no_listener_started':True,'expected_query_summary':{query:{'count':len(rows),'leading':[{k:r[k] for k in ('id','reason','canonical_rank','field_overlap_proof')} for r in rows[:8]]} for query,rows in query_expectations(h).items()}}));h.close();raise SystemExit(0)
h.start()
before=h.before
process=None;report={'status':'failed','reason':'browser_not_run'};known={}
try:
    selected=h.package.modules['ontology_core'].load_project(h.root,validate=False)
    artifact='urn:sys4ai:ontology:core:Artifact'
    expected=sorted(r['@id'] for r in selected.records if r['kind']!='binding' and artifact in r['@type'] and r['lifecycle']=='approved' and r['fact_kind']=='asserted')
    assert expected and len(expected)>7
    metadata={'private_file':str(h.service.bootstrap_file),'origin':h.service.origin,
      'desired_route':'#/p/explorer-alpha/overview','expected_artifact_ids':expected,'expected_queries':query_expectations(h)}
    job=h.base/'browser-job.json';job.write_text(json.dumps(metadata))
    node='/Users/alex.omegapy/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'
    process=subprocess.Popen([node,str(stage/'production-browser.cjs'),str(job)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,
        env={'PATH':'/usr/bin:/bin','LANG':'en_US.UTF-8','TMPDIR':'/private/tmp'})
    deadline=time.monotonic()+150
    while True:
        remember_descendants(process.pid,known)
        try:stdout,stderr=process.communicate(timeout=.25);break
        except subprocess.TimeoutExpired:
            if time.monotonic()<deadline:continue
            process.terminate()
            try:stdout,stderr=process.communicate(timeout=10)
            except subprocess.TimeoutExpired:process.kill();stdout,stderr=process.communicate(timeout=3)
            break
    try:report=json.loads(stdout)
    except ValueError:report={'status':'failed','reason':'no_safe_browser_report'}
    report['node_exit_code']=process.returncode
    report['raw_stderr_suppressed']=bool(stderr)
    signals,exited=cleanup_descendants(known)
    report['observed_browser_descendants_exited']=exited;report['emergency_descendant_signals']=signals
    if not exited or process.returncode!=0:report['status']='failed'
finally:
    if process and process.poll() is None:process.terminate();process.wait(10)
    h.service.stopping=True;h.thread.join(8);h.service.close()
    report['owned_read_worker_reaped']=h.service.worker.process is None
    report['fixture_regular_files_unchanged']=before==test_explorer_service.inventory(h.root)
    verify();report['stage_inputs_unchanged']=True;report['optional_paths_absent']=all(not (h.root/p).exists() for p in h.optional_absent);report['publication_enabled']=json.loads((h.root/'ontology.yaml').read_text())['publication']['enabled'];report['fixture_identity']=h.fixture['counts'];report['search_expectations']={'oracle':'Existing canonical ontology_retrieval.ranked after exact default status/nonbinding filter; every lexical extra has canonical-field token overlap proof','queries':metadata['expected_queries']};report['generated_state']=h.generated_state;report['generated_files_unchanged']=all(before.get(p)==test_explorer_service.inventory(h.root).get(p) for p in h.generated_state['present_stale']);report['generated_absences_preserved']=all(not (h.root/p).exists() for p in h.generated_state['absent'])
    print(json.dumps(report,sort_keys=True));h.close()
raise SystemExit(0 if report['status']=='passed' and report['fixture_regular_files_unchanged'] else 1)
