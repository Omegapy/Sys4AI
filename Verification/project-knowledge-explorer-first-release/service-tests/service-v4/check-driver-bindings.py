"""Exercise exact driver hash bindings without importing service or launching processes."""
import ast,hashlib,importlib.abc,importlib.util,json,tempfile,types
from pathlib import Path
out=Path(__file__).resolve().parent
raw=(out/'host-playwright-driver-v2.py').read_bytes();tree=ast.parse(raw)
assignments=[n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='manifest_digests' for t in n.targets)]
assert len(assignments)==1
assert not any(isinstance(n,ast.Name) and n.id=='known' for n in ast.walk(tree))
selected=assignments+[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in ('Source','verify_tools')]
assert len(selected)==3
calls=[]
with tempfile.TemporaryDirectory(prefix='explorer-v4-driver-bindings-') as tmp:
 stage=Path(tmp);scripts=stage/'scripts';scripts.mkdir();tests=stage/'tests';tests.mkdir()
 source=b'captured_value=17\n';(scripts/'ontology_probe.py').write_bytes(source)
 pinned='f'*64
 manifest={'files':[{'path':'scripts/ontology_probe.py','sha256':hashlib.sha256(source).hexdigest()},{'path':'tool-pins.json','sha256':pinned}]}
 def tool_verify(path,digest):calls.append((path.name,digest));assert digest==pinned;return {'status':'passed'}
 scope={'stage':stage,'scripts':scripts,'tests':tests,'manifest':manifest,'importlib':importlib,'Path':Path,'hashlib':hashlib,'tool_scope':{'verify':tool_verify}}
 exec(compile(ast.Module(body=selected,type_ignores=[]),str(out/'host-playwright-driver-v2.py'),'exec'),scope)
 loader=scope['Source']()
 def exercise():
  assert scope['verify_tools']()=={'status':'passed'}
  spec=loader.find_spec('ontology_probe');assert spec is not None
  module=types.ModuleType('ontology_probe');module.__spec__=spec;loader.exec_module(module);assert module.captured_value==17
 exercise();scope['owned_descendants']={123:'bounded fixture process identity'};exercise();scope['owned_descendants'].clear();exercise()
 assert scope['manifest_digests']=={r['path']:r['sha256'] for r in manifest['files']}
 report={'status':'passed','driver_sha256':hashlib.sha256(raw).hexdigest(),'checks':['one immutable manifest binding','separate owned-descendant binding','exact Source loader before/during/after descendant updates','exact verify_tools digest before/during/after descendant updates'],'exact_tool_calls':len(calls),'service_imported':False,'process_or_listener_launched':False,'qualification':'AST extracts and executes the unchanged production-test loader and verify_tools definitions with a private harmless module and mocked tool verifier; actual host end-to-end browser recheck remains pending.'}
print(json.dumps(report,indent=2))
