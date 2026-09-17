"""Standard-library public API; optional packages only run inside the worker."""
from pathlib import Path
from ontology_core import (OntologyError, canonical_bytes, decode_json, load_project,
    read_bytes, require, safe_path, sha256)
from ontology_advanced import CONFIG, VERSION, load_advanced, load_extensions
from ontology_limits import limits as resolve_limits


def contract_asset(relative):
    package=Path(__file__).resolve().parents[1]
    candidates=[package.parents[1]/'ONTOLOGY-depo',package.parents[2]/'reference-assets/ONTOLOGY-depo']
    for directory in candidates:
        path=directory/relative
        if path.is_file(): return path
    raise OntologyError('missing_contract','The selected installed standards contract is absent: '+relative)


def _prepare(root,overrides=None):
    overrides=overrides or {}
    for path,data in overrides.items():
        safe_path(root,path,must_exist=False)
        require(isinstance(data,bytes),'invalid_override','Preview overrides must contain exact bytes.')
    cfg=load_advanced(root,required=True,_overrides=overrides)
    require(cfg['profiles'].get('standards',{}).get('enabled',False),'profile_disabled','Standards profile is disabled.')
    project=load_project(root,validate=False,_overrides={k:v for k,v in overrides.items() if k!=CONFIG and not k.startswith('ONTOLOGY/extensions/')})
    extensions,extra,sources=load_extensions(project,cfg,_overrides=overrides)
    allowed=set(project.config['project_files']+project.config['binding_files']+project.config.get('competency_files',[]))|{CONFIG}|set(extra)
    require(set(overrides)<=allowed,'canonical_scope','Preview includes unselected advanced files.')
    context=project.context(); context.pop('snapshot_sha256',None)
    context['advanced_version']=VERSION
    context['advanced_inputs']={CONFIG:sha256(overrides[CONFIG] if CONFIG in overrides else read_bytes(safe_path(root,CONFIG))),**extra}
    context['advanced_sources']=sources
    package=Path(__file__).resolve().parents[1]
    context['standards_profile_sha256']=sha256(package/'profiles/standards-v1.json')
    context['contracts']={relative:sha256(contract_asset(relative)) for relative in ('rules/finite-profile-v1.json','shapes/ontology-v1.ttl')}
    from ontology_reasoning import RULES
    rule_manifest=decode_json(read_bytes(contract_asset('rules/finite-profile-v1.json')))
    require(rule_manifest.get('schema_version')==1 and rule_manifest.get('version')=='1.0.0' and set(rule_manifest.get('rules',{}))==set(RULES),'unsupported_rule_profile','Selected finite rule manifest differs from the supported engine.')
    context['preview']=bool(overrides)
    context['snapshot_sha256']=sha256(canonical_bytes(context))
    shapes=[read_bytes(contract_asset('shapes/ontology-v1.ttl')).decode()]
    for ext in extensions:
        for ref in ext.get('shapes',[]): shapes.append((overrides[ref['path']] if ref['path'] in overrides else read_bytes(safe_path(root,ref['path']))).decode())
    payload={'records':project.records,'sources':project.sources+sources,'extensions':extensions,
             'context':context,'shapes':shapes,'inference_enabled':cfg['profiles'].get('inference',{}).get('enabled',False)}
    return cfg,payload,project


def health(root):
    from ontology_profiles import health as profile_health
    return profile_health(root,'standards')


def call(root,operation,*,overrides=None,limits=None,cancel=None,expected_snapshot=None,**options):
    from ontology_worker import run_worker
    from ontology_profiles import health as profile_health
    try:
        cfg,payload,project=_prepare(root,overrides)
        readiness=profile_health(root,'standards')
        require(readiness['status']=='ready','backend_unavailable','Standards profile is not ready: '+readiness['status'])
        if expected_snapshot is not None:
            require(payload['context']['snapshot_sha256']==expected_snapshot,'stale_input','Approved input snapshot changed; the old result cannot be reused.')
        if operation=='infer': require(cfg['profiles'].get('inference',{}).get('enabled',False),'profile_disabled','Inference profile is disabled.')
        bound=resolve_limits(cfg['limits'],limits)
        supplied_shapes=options.pop('shapes',None)
        payload.update(options)
        if supplied_shapes is not None:
            require(isinstance(supplied_shapes,(str,list)),'invalid_shapes','Shapes must be selected Turtle text or a list of texts.')
            payload['shapes'] += [supplied_shapes] if isinstance(supplied_shapes,str) else supplied_shapes
        if operation=='validate' and any(d['severity']=='error' for d in project.diagnostics) and payload.get('triples') is None:
            core_errors=[d for d in project.diagnostics if d['severity']=='error']
        else: core_errors=[]
        result=run_worker(Path(root)/'.venv-ontology-standards/bin/python',operation,payload,bound,cancel=cancel)
        result['context']=payload['context']
        if core_errors and result.get('complete'):
            result.update(status='violation',conforms=False); result.setdefault('diagnostics',[]).extend(core_errors)
        # Reopen exact inputs after execution; preview bytes remain frozen and are
        # never mistaken for canonical state. Queries do not refresh any store.
        now=_prepare(root,overrides)[1]['context']['snapshot_sha256']
        if now!=payload['context']['snapshot_sha256']:
            return {'status':'stale_input','complete':False,'trusted':False,'context':payload['context'],
                'diagnostics':[{'code':'stale_input','message':'Selected inputs changed during the worker operation.'}]}
        if len(canonical_bytes(result))>bound['output_bytes']:
            return {'status':'output_limit','complete':False,'context':payload['context'],
                'diagnostics':[{'code':'output_limit','message':'Complete result with provenance exceeds output_bytes.'}]}
        return result
    except OntologyError as exc:
        return {'status':exc.code,'complete':False,'diagnostics':[exc.as_dict()]}


def dataset(root,graphs=None,**kwargs): return call(root,'dataset',graphs=graphs or ['asserted','derived','inferred','external'],**kwargs)
def query(root,text,graphs=None,**kwargs): return call(root,'query',query=text,graphs=graphs or ['asserted'],**kwargs)
def validate(root,graphs=None,shapes=None,triples=None,**kwargs): return call(root,'validate',graphs=graphs or ['asserted','derived','external'],shapes=shapes,triples=triples,**kwargs)
def infer(root,goals=None,premise_ids=None,**kwargs): return call(root,'infer',goals=goals or [],premise_ids=premise_ids,**kwargs)
def export(root,format,selected_graph=None,**kwargs): return call(root,'export',format=format,selected_graph=selected_graph,**kwargs)
def stage_import(root,data,format,manifest=None,**kwargs): return call(root,'parse',data=data,format=format,manifest=manifest,**kwargs)


def freshness(root,result):
    try:
        context=_prepare(root)[1]['context']
        current=context['snapshot_sha256']==result.get('context',{}).get('snapshot_sha256')
        return {'status':'current' if current else 'stale_input','complete':current,'context':context}
    except OntologyError as exc: return {'status':exc.code,'complete':False,'diagnostics':[exc.as_dict()]}
