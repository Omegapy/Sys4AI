"""Generate real closed reader responses for the client precision integration."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'SKILLS-depo/ontology/tests'))
from test_explorer_read import ReaderCase
case=ReaderCase();case.setUp()
try:
 predicate='urn:sys4ai:ontology:project:explorer-alpha:documents'
 case.edit_record(predicate,lambda r:r['qualifiers'].update(count={'type':'integer','required':False},ratio={'type':'number','required':False}))
 ids=['urn:sys4ai:ontology:project:explorer-alpha:relation-'+f'{i:06d}' for i in (0,2,4,12)]
 for ident,qualifiers in zip(ids,({'count':9007199254740993},{'count':9007199254740991,'ratio':0.1},{'count':10**350},{'ratio':-0.0})):
  case.edit_record(ident,lambda r,q=qualifiers:r.update(qualifiers=q))
 case.snapshot=case.call('context',{'refresh':True})['snapshot']
 graph=case.call('relationships',case.graph_params(limit=20))
 details=[case.entry(ident,'qualifiers') for ident in ids]
 report={'schema_version':1,'qualification':'Real adapter responses on disposable synthetic canonical data. Public scope IDs/cursors are non-authorizing synthetic values; no live credentials or knowledge are included. HTTP/browser transport not exercised.',
  'reader_sha256':hashlib.sha256((ROOT/'SKILLS-depo/ontology/scripts/ontology_explorer_read.py').read_bytes()).hexdigest(),
  'source_sha256':hashlib.sha256((ROOT/'SKILLS-depo/ontology/scripts/ontology_explorer_source.py').read_bytes()).hexdigest(),
  'relationships_response':graph,'qualifier_responses':details,'expected_marker_ids':[ids[0],ids[2],ids[3]],'expected_full_edge_id':ids[1]}
 target=Path(__file__).parent/'precision-wire-fixture.json';target.write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
 print(json.dumps({'path':str(target.relative_to(ROOT)),'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'bytes':target.stat().st_size}))
finally:case.tearDown()
