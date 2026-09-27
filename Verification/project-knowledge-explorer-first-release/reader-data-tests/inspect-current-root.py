"""Bounded selected live-root read; no startup, full preservation or latency claim."""
from pathlib import Path
import hashlib,json,sys,time
ROOT=Path(__file__).resolve().parents[3]
scripts=ROOT/'SKILLS-depo/ontology/scripts'
sys.path.insert(0,str(scripts))
from ontology_explorer_snapshot import VerifiedPackage
import ontology_explorer_read as bootstrap
p=VerifiedPackage(scripts,{'schema':ROOT/'ONTOLOGY-depo/schema/explorer-v1.json'},allowed_modules=bootstrap.READ_CLOSURE)
s=p.load('ontology_explorer_snapshot');m=p.load('ontology_explorer_read');store=s.SnapshotStore(ROOT,p)
r=m.Reader(store,service_instance='1'*32,build_id='2'*64,schema_sha256=hashlib.sha256(p.member_bytes['schema']).hexdigest(),service_secret=b'x'*32)
req=dict(schema_version=1,request_id='root-read-check',code_epoch=p.code_epoch,snapshot=None,params={'refresh':False})
start=time.monotonic();context=r.read('context',req,session_scope='3'*32,session_expires_ms=900000);elapsed=time.monotonic()-start
selected={path:(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),(ROOT/path).stat().st_mtime_ns) for path,marker in store.current.manifest['files'].items() if marker['state']=='present'}
req.update(snapshot=context['snapshot'],params=dict(query='Task',category=None,lifecycles=['approved'],fact_kinds=['asserted'],sort='relevance',limit=5,cursor=None))
search=r.read('search',req,session_scope='3'*32,session_expires_ms=900000)
req['params']=dict(id='urn:sys4ai:ontology:core:Task',section='header',cursor=None)
entry=r.read('entry',req,session_scope='3'*32,session_expires_ms=900000)
after={path:(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),(ROOT/path).stat().st_mtime_ns) for path in selected}
result={'context_status':context['status'],'context_bytes':len(m.compact(context)),'initial_context_seconds':elapsed,'records':len(store.current.project.records),'relations':len(store.current.project.relations),'categories':len(context['data']['categories']),'process_ids':context['data']['process_ids'],'search_status':search['status'],'search_returned':search['page']['returned'],'entry_status':entry['status'],'selected_bytes_mtimes_unchanged_after_context':selected==after,'loaded_modules':p.loaded_digests,'qualification':'One read-only live-root observation. Timing includes startup materialization, not repeated cold/warm service performance. Selected comparison begins after context; not complete protected-state, production bootstrap, HTTP or release proof.'}
store.close();(Path(__file__).parent/'current-root-result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ('loaded_modules',)}))
