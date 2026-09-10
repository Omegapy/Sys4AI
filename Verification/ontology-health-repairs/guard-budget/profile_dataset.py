"""Isolate dataset construction and exact quad normalization in a confined worker."""
from pathlib import Path
import hashlib, importlib, importlib.util, json, shutil, sys, tempfile
out=Path(__file__).resolve().parent;root=out.parents[2]
sys.dont_write_bytecode=True;tempfile.tempdir=str(out)
sys.path.insert(0,str(root/'SKILLS-depo/ontology/tests'))
import test_action_semantics as tests
factory=tests.ActionSemanticsTests();project,owner,proposal=factory.extension_candidate()
from ontology_standards import _prepare
from ontology_limits import limits
from ontology_core import canonical_bytes
cfg,payload,_=_prepare(project,{c['path']:c['content'].encode() for c in proposal['changes']});payload['graphs']=['asserted','derived']
(out/'dataset-payload.json').write_bytes(canonical_bytes(payload))
results={}
try:
 for variant in ('original','ground-fast-path'):
  target=out/(variant+'-scripts');shutil.copytree(project/'.agents/skills/ontology/scripts',target,dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
  worker=target/'ontology_worker.py';worker.write_text(worker.read_text().replace("'project_files_readable': False}","'project_files_readable': False, 'phase_trace':err.decode(errors='replace')}"))
  backend=target/'ontology_backend.py';t=backend.read_text().replace('        ds,names,premises=project_dataset(payload)',"        import time\n        started=time.monotonic()\n        ds,names,premises=project_dataset(payload)\n        print(json.dumps({'phase':'project_dataset','seconds':time.monotonic()-started}),file=sys.stderr,flush=True)");backend.write_text(t)
  rdf=target/'ontology_rdf.py';t=(out/'original-ontology_rdf.py').read_text()
  if variant=='ground-fast-path':
   t=t.replace('    q = Graph()',"    if not any(isinstance(value,BNode) for quad in dataset.quads((None,None,None,None)) for value in quad):\n        return sorted([[encode(value) for value in quad] for quad in dataset.quads((None,None,None,None))],key=canonical_bytes)\n    q = Graph()",1)
  t+='''\n_original_quad_rows=quad_rows
def quad_rows(dataset):
    import json,sys,time
    from rdflib import BNode
    count=sum(1 for _ in dataset.quads((None,None,None,None)))
    blank_nodes=sum(isinstance(v,BNode) for row in dataset.quads((None,None,None,None)) for v in row)
    start=time.monotonic();result=_original_quad_rows(dataset)
    print(json.dumps({'phase':'quad_rows','seconds':time.monotonic()-start,'quads':count,'blank_node_terms':blank_nodes}),file=sys.stderr,flush=True)
    return result
''';rdf.write_text(t)
  spec=importlib.util.spec_from_file_location('worker_'+variant.replace('-','_'),worker);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
  result=module.run_worker(project/'.venv-ontology-standards/bin/python','dataset',payload,limits(overrides={'query_seconds':5}))
  results[variant]=result
finally:factory.doCleanups()
assert results['original']['complete'] and results['ground-fast-path']['complete']
assert results['original']['quads']==results['ground-fast-path']['quads']
assert results['original']['semantic_sha256']==results['ground-fast-path']['semantic_sha256']
(out/'dataset-comparison.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps({k:{'status':v['status'],'worker':v['worker'],'semantic_sha256':v['semantic_sha256']} for k,v in results.items()},indent=2))
