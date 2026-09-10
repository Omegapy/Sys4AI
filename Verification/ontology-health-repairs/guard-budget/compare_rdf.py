"""Compare original and repaired confined workers on exact RDF fixture inputs."""
from pathlib import Path
import copy,importlib.util,json,sys
out=Path(__file__).resolve().parent;root=out.parents[2]
sys.dont_write_bytecode=True;sys.path.insert(0,str(root/'SKILLS-depo/ontology/tests'))
from test_rdf_canonicalization import ground_document,blank_document
from ontology_core import canonical_bytes,sha256
from ontology_limits import limits
from ontology_worker import run_worker
spec=importlib.util.spec_from_file_location('original_worker',out/'original-scripts/ontology_worker.py');original=importlib.util.module_from_spec(spec);spec.loader.exec_module(original)
cases={'ground':ground_document(),'blank':blank_document(),'empty':[]}
cases['ground_reordered']=list(reversed(ground_document()))
cases['blank_reordered']=json.loads(json.dumps(blank_document()).replace('_:a','_:another-a').replace('_:b','_:another-b').replace('_:c','_:another-c'));cases['blank_reordered'].reverse()
for graph in cases['blank_reordered']:graph['@graph'].reverse()
cases['different_graph']=copy.deepcopy(cases['ground']);cases['different_graph'][0]['@id']='urn:another:graph'
results={}
python=root/'Verification/ontology-health-repairs/shacl/source-runtime/.venv-ontology-standards/bin/python'
for label,document in cases.items():
 payload={'data':json.dumps(document),'format':'json-ld','records':[],'extensions':[],'sources':[],'context':{'project_id':'example','snapshot_sha256':'a'*64}}
 before=original.run_worker(python,'parse',payload,limits());after=run_worker(python,'parse',payload,limits())
 assert before['status']==after['status']=='staged' and before['complete'] and after['complete']
 assert before['quads']==after['quads'] and before['semantic_sha256']==after['semantic_sha256'],label
 results[label]={'payload_sha256':sha256(canonical_bytes(payload)),'semantic_sha256':after['semantic_sha256'],'quad_count':len(after['quads']),'before':before,'after':after}
(out/'rdf-equivalence.json').write_text(json.dumps({'status':'pass','cases':results},indent=2)+'\n')
print('PASS:',len(results),'exact original/repaired RDF cases, all quads and semantic hashes equal')
