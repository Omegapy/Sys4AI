"""Editioned setup integration using trusted pure ontology code and exact owners."""
from contextlib import contextmanager
from pathlib import Path
import importlib
import sys

EDITION='curator-ontology-1.0.0'
CONTRACT='governance-starter-v12'
RECIPE='reference-assets/ONTOLOGY-depo/integrations/curator/1.0.0'
GENERATED=('ONTOLOGY/modules/project/curator.jsonld','ONTOLOGY/bindings/curator.jsonld','ONTOLOGY/modules/project/curator-competency.json')


@contextmanager
def owner(h):
    """Execute this reviewed delivery's helper; destination Python stays data."""
    scripts=Path(__file__).resolve().parents[2]/'ontology/scripts'
    saved={name:value for name,value in sys.modules.items() if name.startswith('ontology') or name=='check_ontology'}
    for name in saved:del sys.modules[name]
    sys.path.insert(0,str(scripts))
    try:
        yield importlib.import_module('ontology_integration')
    finally:
        for name in list(sys.modules):
            if name.startswith('ontology') or name=='check_ontology':del sys.modules[name]
        sys.modules.update(saved);sys.path.remove(str(scripts))


def recipe_files(original):
    return {name:original[RECIPE+'/'+name] for name in ('manifest.json','recipe.json','locators.json','competency.json','contract.md')}


def render(h,identity,files,original):
    with owner(h) as api:
        config=h.unique_json(files['ontology.yaml'])
        if config['project']['id']!=identity['project_id']:raise h.InitializationError('Curator ontology identity mismatch')
        selected=recipe_files(original)
        rendered=api.render(selected,config['project'],files)
        return {**rendered['files'],'ontology.yaml':api.canonical_bytes(api.selection_config(config,rendered['additions']))}


def prepare(h,destination,identity,selected,original,preserved,before):
    """Render after all governing bytes and the final role index settle."""
    if 'ontology.yaml' not in selected:
        return {'edition':EDITION,'mode':'owner-publication','status':'pending','operation_id':None},{}
    effective=dict(original)
    for name in effective:
        path=h.destination_file(destination,name)
        if name not in selected and path.is_file():effective[name]=h.file_bytes(path)
    effective.update(selected)
    rendered=render(h,identity,effective,original)
    for name,raw in rendered.items():
        path=h.destination_file(destination,name)
        if name in GENERATED and path.exists():raise h.InitializationError('Unowned reserved Curator integration file preserved: '+name)
        selected[name]=raw
        if name not in before:before[name]=h.sha(h.file_bytes(path)) if path.exists() else None
    generated={name:{'sha256':h.sha(rendered[name]),'recipe_manifest_sha256':h.sha(original[RECIPE+'/manifest.json'])} for name in GENERATED}
    return {'edition':EDITION,'mode':'setup-generated','status':'pending','files':{name:h.sha(raw) for name,raw in rendered.items()}},generated


def validate_generated(h,record,source_adoptions):
    generated=record.get('generated_files',{})
    if record['setup_contract']!=CONTRACT:
        if generated:raise h.InitializationError('Historical setup cannot acquire generated integration provenance')
        return
    integration=record.get('curator_integration')
    if not isinstance(integration,dict) or integration.get('edition')!=EDITION or integration.get('mode') not in ('setup-generated','owner-publication'):
        raise h.InitializationError('Integrated setup lacks its exact integration disposition')
    if integration['mode']=='setup-generated':
        if set(generated)!=set(GENERATED):raise h.InitializationError('Integrated setup lacks complete generated output provenance')
        for name,value in generated.items():
            if set(value)!={'sha256','recipe_manifest_sha256'} or any(not h.SHA256.fullmatch(d) for d in value.values()) or record['owned_files'].get(name)!=value['sha256']:
                raise h.InitializationError('Invalid generated integration ownership')
            source_adoptions[name]=('specialized',value['sha256'])
        refs=[r['source_sha256'] for r in record['sources'] if r['destination']==RECIPE+'/manifest.json']
        if len(refs)!=1 or any(v['recipe_manifest_sha256']!=refs[0] for v in generated.values()):raise h.InitializationError('Generated outputs differ from selected neutral recipe')
    elif generated:raise h.InitializationError('Authored integration must use its owner receipt')


def assess(h,destination,*,required=True):
    result={'edition':EDITION,'required':required,'compatible':False,'declared':False,'runtime_observed':False,'executed':False,'mutated':False,'diagnostics':[]}
    try:
        with owner(h) as api:
            p=api.load_project(destination)
            resources=api.resources(destination)
            sources={name:h.file_bytes(h.destination_file(destination,name)) for name in api.source_paths(resources)}
            cfg=h.unique_json(sources['curator.yaml'])
            if cfg['project']['coordination_root']!=str(destination):raise h.InitializationError('Curator coordination root differs')
            expected=api.render(resources,p.config['project'],sources)
            for key,items in expected['additions'].items():
                if not set(items)<=set(p.config.get(key,[])):raise h.InitializationError('Curator integration selection is incomplete: '+key)
            for name,raw in expected['files'].items():
                if h.file_bytes(h.destination_file(destination,name))!=raw:raise h.InitializationError('Curator semantic graph, function, binding or source freshness differs: '+name)
            result.update(compatible=True,declared=True,source_freshness='current',function_count=len(api.decode_json(resources['recipe.json'])['functions']),project_id=p.project_id)
    except (h.InitializationError,OSError,ValueError,KeyError,TypeError) as exc:
        result['diagnostics'].append({'code':'curator_semantic_integration_unavailable','message':str(exc)[:1200]})
    return result


def _complete(h,destination,record,checkpoint,grant_input=None,proposal_input=None):
    """Continue the same selected setup using exact current owner authority."""
    integration=record['curator_integration']
    if integration['mode']=='setup-generated' and integration.get('status')=='completed':
        current=assess(h,destination)
        if not current['compatible']:
            refresh=integration.setdefault('refresh',{'edition':EDITION,'mode':'owner-publication','status':'pending','operation_id':None})
            complete(h,destination,{'operation_id':record['operation_id']+'-source-refresh','curator_integration':refresh},checkpoint,grant_input,proposal_input)
    if integration['mode']=='owner-publication':
        with owner(h) as api:
            from ontology_publication import integration_preview,integration_publish,integration_recover
            op=integration.get('operation_id') or 'ONTOP-'+record['operation_id']
            integration['operation_id']=op
            intent=h.destination_file(destination,api._paths(op)[0])
            if intent.exists():
                accepted=api._intent(destination,op);pre=accepted['preview']
            else:
                pre=integration_preview(destination,{'schema_version':1,'operation_id':op,'reason':'Complete selected '+record['operation_id']+' Curator ontology integration.'})
            integration['preview']=pre
            checkpoint()
            grant=grant_input(pre) if callable(grant_input) else h.unique_json(h.file_bytes(h.destination_file(destination,str(grant_input)))) if grant_input else None
            if grant is None:raise h.InitializationError('curator-integration-owner-grant-required: review saved curator_integration.preview and repeat the same setup with exact current --integration-grant-file')
            if proposal_input:
                proposed=h.unique_json(h.file_bytes(h.destination_file(destination,str(proposal_input))))
                if proposed!=pre['proposal']:raise h.InitializationError('Supplied integration proposal differs from exact saved/current preview')
            receipt=integration_recover(destination,op,grant) if intent.exists() else integration_publish(destination,pre['proposal'],grant,expected_preview_sha256=pre['preview_sha256'])
            if receipt.get('status')!='complete':raise h.InitializationError('curator-integration-owner-partial: renew original preview grant and repeat exact setup')
            receipt_path=api._paths(op)[1];raw=h.file_bytes(h.destination_file(destination,receipt_path))
            if api.decode_json(raw).get('intent_sha256')!=receipt['intent_sha256']:raise h.InitializationError('Owner completion receipt link differs')
            integration['owner_receipt']={'path':receipt_path,'sha256':h.sha(raw)}
    checked=assess(h,destination)
    if not checked['compatible']:raise h.InitializationError(checked['diagnostics'][0]['message'])
    integration.update(status='completed',assessment=checked)
    checkpoint()


def owner_changes(h,destination,operation):
    integration=operation.get('curator_integration',{})
    op=integration.get('operation_id')
    if integration.get('edition')!=EDITION or not op:return {}
    with owner(h) as api:
        path=h.destination_file(destination,api._paths(op)[0])
        if not path.exists():return {}
        intent=api._intent(destination,op)
        if integration.get('preview')!=intent['preview']:raise h.InitializationError('Saved setup link differs from immutable owner intent')
        changes={c['path']:c for c in intent['proposal']['changes']}
        for name,c in changes.items():
            target=h.destination_file(destination,name);actual=h.sha(h.file_bytes(target)) if target.exists() else None
            if actual not in (c['expected_sha256'],c['sha256']):raise h.InitializationError('Owner target has third-state edits: '+name)
        return changes


def complete(h,destination,record,checkpoint,grant_input=None,proposal_input=None):
    try:
        return _complete(h,destination,record,checkpoint,grant_input,proposal_input)
    except h.InitializationError:
        raise
    except (ValueError,KeyError,TypeError) as exc:
        raise h.InitializationError('curator-integration-owner-hold: '+getattr(exc,'code',type(exc).__name__)+': '+str(exc)[:1000]) from exc
