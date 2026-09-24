"""Optional test-only Draft 2020-12 checks; no reader runtime dependency."""
from pathlib import Path
import importlib.metadata
import json
import sys
import tempfile
from jsonschema import Draft202012Validator, ValidationError, validators

sys.dont_write_bytecode = True
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
sys.path.insert(0,str(HERE.parents[1]))
from explorer_support import *

schema_path=ROOT/'ONTOLOGY-depo/schema/explorer-v1.json'
schema=read_json(schema_path)
Draft202012Validator.check_schema(schema)
def byte_limit(validator,bound,instance,selected):
    if isinstance(instance,str) and len(instance.encode('utf-8'))>bound:
        yield ValidationError('UTF-8 byte limit exceeded')
Strict=validators.extend(Draft202012Validator,{'x-max-utf8-bytes':byte_limit},
    type_checker=Draft202012Validator.TYPE_CHECKER.redefine('integer',lambda checker,value:type(value) is int))
checks=[]
with tempfile.TemporaryDirectory(prefix='explorer-fixture-schema-') as tmp:
    base=Path(tmp).resolve()
    for identity in ('explorer-alpha','explorer-beta'):
        sample=make_explorer_project(base/identity,identity=identity)
        cfg=read_json(sample['root']/'ontology-explorer.yaml')
        Strict(schema).validate(cfg)
        project=load_project(sample['root'],validate=True)
        for process in cfg['process_views']:
            for mapped in process['field_sources']['applicability']:
                owner=project.by_id[mapped['owner_id']]
                source=next(s for s in owner['sources'] if reference_id(owner['@id'],s)==mapped['reference_id'])
                value={'owner_id':owner['@id'],'binding_id':None,'path':source['path'],'locator':source['locator'],'recorded_sha256':source['sha256']}
                Strict({'$defs':schema['$defs'],**schema['$defs']['SourceReferenceIdentity']}).validate(value)
        checks.append({'id':identity,'configuration':'passed','canonical_selected_mapping_reference_tuples':'passed','process_mappings':len(cfg['process_views'])})
    for unspecialized in (False,True):
        root=make_neutral_project(base/str(unspecialized),unspecialized=unspecialized)
        Strict(schema).validate(read_json(root/'ontology-explorer.yaml'))
        checks.append({'id':'neutral-'+str(unspecialized),'configuration':'passed','runtime':'not_exercised'})
    for value in (True,1.0,0,101):
        assert not Strict(schema).is_valid({'schema_version':1,'project_id':'explorer-alpha','limits':{'page_items':value}})
        checks.append({'id':'invalid-page-limit-'+repr(value),'rejected':True})
result={'schema_version':1,'kind':'fixture_schema_validation','schema_sha256':sha256(schema_path),
        'validator':'jsonschema '+importlib.metadata.version('jsonschema')+' Draft202012Validator with strict integer-token and UTF-8 extensions',
        'interpreter':sys.executable,'purpose':'test-only; no memory operation or production dependency',
        'checks':checks,'passed':True,
        'qualification':'Structural schema and exact selected-reference identity checks only. Process ordering/extraction, runtime semantic config validation and all service/browser behaviors remain untested.'}
(HERE/'validation/schema-result.json').write_bytes(canonical_bytes(result))
print(json.dumps({'passed':True,'checks':len(checks)}))
