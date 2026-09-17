"""Execute exact old/new generators against a standard-library RDF recorder.
No optional backend is loaded. Actual pySHACL is tested separately in its worker.
"""
from pathlib import Path
import sys,types,ast,json,itertools
OUT=Path(__file__).parent;ROOT=OUT/'root-copy';sys.path.insert(0,str(ROOT/'.agents/skills/ontology/scripts'))
from ontology_core import canonical_bytes,sha256
collections={};ids=itertools.count()
class URIRef(str):pass
class BNode(str):
 def __new__(cls):return super().__new__(cls,'_:node'+str(next(ids)))
class Literal:
 def __init__(self,value):self.value=value
 def __hash__(self):return hash((type(self.value),self.value))
 def __eq__(self,other):return type(other) is Literal and type(self.value) is type(other.value) and self.value==other.value
class Graph:
 def __init__(self):self.triples=set()
 def add(self,triple):self.triples.add(triple)
def Collection(graph,head,values):collections[head]=list(values)
module=types.ModuleType('rdflib');module.Graph=Graph;module.URIRef=URIRef;module.BNode=BNode;module.Literal=Literal
sys.modules['rdflib']=module;collection=types.ModuleType('rdflib.collection');collection.Collection=Collection;sys.modules['rdflib.collection']=collection
from ontology_shacl import shapes_for_records,record_constraints,SH
from ontology_advanced import RDF
before=OUT/'preimages/SKILLS-depo/ontology/scripts/ontology_shacl.py'
tree=ast.parse(before.read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='shapes_for_records')
namespace={'SH':SH};exec(compile(ast.Module(body=[fn],type_ignores=[]),str(before),'exec'),namespace)
records=json.loads((OUT/'root-copy-payload.json').read_text())['records']
def normalize(graph):
 rows=graph.triples;out={};shapes={s for s,p,o in rows if p==RDF+'type' and o==SH+'NodeShape'}
 for shape in shapes:
  constraints=[]
  for _,_,prop in (t for t in rows if t[:2]==(shape,SH+'property')):
   values={};path=None
   for _,pred,value in (t for t in rows if t[0]==prop):
    if pred==SH+'path':path=str(value)
    else:values[str(pred)[len(SH):]]=[str(v) for v in collections[value]] if type(value) is BNode else value.value if type(value) is Literal else str(value)
   constraints.append([path,values])
  constraints=sorted(constraints,key=canonical_bytes)
  for _,_,target in (t for t in rows if t[:2]==(shape,SH+'targetNode')):out[str(target)]=constraints
 return out,len(shapes)
old,oldcount=normalize(namespace['shapes_for_records'](records));new,newcount=normalize(shapes_for_records(records))
assert old==new==record_constraints(records)
assert set(old)=={r['@id'] for r in records}
result={'scope':'Exact predecessor and proposed generator executed with standard-library RDF recording only; actual worker validates separately','predecessor_sha256':sha256(before),'proposed_sha256':sha256(ROOT/'.agents/skills/ontology/scripts/ontology_shacl.py'),'targets':len(new),'old_node_shapes':oldcount,'new_node_shapes':newcount,'every_target_and_complete_constraint_equal':True,'target_constraints_sha256':sha256(canonical_bytes(new)),'target_digests':{k:sha256(canonical_bytes(v)) for k,v in new.items()}}
(OUT/'constraint-equivalence.json').write_bytes(canonical_bytes(result));print(json.dumps({k:v for k,v in result.items() if k!='target_digests'},indent=2))
