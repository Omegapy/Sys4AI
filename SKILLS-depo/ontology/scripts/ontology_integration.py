"""Curator semantics and a separately scoped, exact four-file owner transaction.

Rendering is pure. Only publish/recover write, under current owner authority.
"""
from pathlib import Path
import copy
import re
from ontology_core import (CORE, PROJECT, CONTEXT_PATH, OntologyError, require, exact,
    canonical_bytes, sha256, decode_json, read_json, read_bytes, safe_path, check_locator,
    allowed_source_path, _load_project, load_project, atomic_write, operation_lock)

EDITION = 'curator-ontology-1.0.0'
RECIPE_ROOT = 'reference-assets/ONTOLOGY-depo/integrations/curator/1.0.0'
GRAPH = 'ONTOLOGY/modules/project/curator.jsonld'
BINDINGS = 'ONTOLOGY/bindings/curator.jsonld'
COMPETENCY = 'ONTOLOGY/modules/project/curator-competency.json'
TARGETS = (GRAPH, BINDINGS, COMPETENCY, 'ontology.yaml')
CONTROL = 'control_records/ontology/integrations/'


def resources(root):
    manifest = read_json(safe_path(root, RECIPE_ROOT + '/manifest.json'))
    require(manifest.get('schema_version') == 1 and manifest.get('edition') == EDITION
            and set(manifest.get('files', {})) == {'recipe.json','locators.json','competency.json','contract.md'},
            'integration_recipe', 'Select the complete reviewed Curator recipe edition.')
    result = {'manifest.json': read_bytes(safe_path(root, RECIPE_ROOT + '/manifest.json'))}
    for name, digest in manifest['files'].items():
        raw = read_bytes(safe_path(root, RECIPE_ROOT + '/' + name))
        require(sha256(raw) == digest, 'integration_recipe_changed', 'Recipe resource differs from its manifest.', path=name)
        result[name] = raw
    return result


def source_paths(recipe_bytes):
    recipe, locators = [decode_json(recipe_bytes[name]) for name in ('recipe.json','locators.json')]
    selected = {ref['path'] for ref in locators['sources'].values()}
    for owner in recipe['owners'].values():
        selected.add('.agents/skills/' + owner['skill'] + '/SKILL.md')
        selected.update('Roles/' + owner['role'] + '/' + leaf for leaf in ('AGENTS.md','ROLE.md'))
    selected.update(('SOUL.md','AGENTS.md','ROLE.md','.agents/skills/curate/SKILL.md'))
    return sorted(selected)


def render(recipe_bytes, identity, sources, canonical_inventory=()):
    """Return exact graph/binding/competency bytes and additive config selection."""
    manifest = decode_json(recipe_bytes['manifest.json'])
    require(manifest.get('edition') == EDITION and manifest.get('schema_version') == 1
            and set(manifest.get('files',{})) == {'recipe.json','locators.json','competency.json','contract.md'}, 'integration_recipe', 'Unsupported recipe.')
    require(all(sha256(recipe_bytes[name]) == digest for name,digest in manifest['files'].items()), 'integration_recipe_changed', 'Reviewed recipe bytes changed.')
    recipe, locators, matrix = [decode_json(recipe_bytes[name]) for name in ('recipe.json','locators.json','competency.json')]
    require(recipe.get('edition') == EDITION and recipe.get('namespace_suffix') == 'curator-', 'integration_recipe', 'Unsupported semantic recipe edition.')
    pid=identity['id']; ns=PROJECT+pid+':'
    require(identity['namespace'] == ns and re.fullmatch('[a-z0-9][a-z0-9-]{0,79}',pid), 'identity_mismatch','Selected integration identity is unresolved.')
    require(set(source_paths(recipe_bytes)) <= sources.keys(),'integration_source_missing','Complete finalized source bytes are required.')
    def ref(path, locator='line:1'):
        allowed_source_path(path);check_locator(sources[path],locator)
        return {'path':path,'locator':locator,'sha256':sha256(sources[path])}
    policy=decode_json(sources['curator.yaml']);session=decode_json(sources['curator-session.yaml'])
    require(policy.get('project',{}).get('id')==pid and session.get('project_id')==pid,
            'identity_mismatch','Curator policy/session identity differs from selected ontology identity.')
    require(isinstance(policy['project'].get('coordination_root'),str) and Path(policy['project']['coordination_root']).is_absolute(),
            'identity_mismatch','Curator policy requires its actual selected root.')
    named={key:ref(**value) for key,value in locators['sources'].items()}
    def rid(key):return ns+'curator-'+key
    records=[];bindings=[]
    def record(key,kind,typ,label,definition,refs,**extra):
        value={'@id':rid(key),'@type':[CORE+typ],'kind':kind,'label':label,'definition':definition,
               'lifecycle':'approved','module':'project','fact_kind':'asserted','sources':refs,**extra}
        records.append(value);return value['@id']
    def binding(key,entity,refs,kind='artifact'):
        bindings.append({'@id':rid('binding-'+key),'@type':[CORE+'SourceBinding'],'kind':'binding','label':'Curator source binding '+key,
            'definition':'Exact current source evidence for '+key+'.','lifecycle':'approved','module':'project','fact_kind':'asserted',
            'sources':refs,'entity':entity,'binding_type':kind})
    def edge(key,subject,predicate,obj,refs):
        record('edge-'+key,'relation','Relationship','Curator '+key,'Declared relationship; current owner evidence is required before execution.',refs,
               subject=subject,predicate=predicate,object=obj)
    general=[named[k] for k in ('charter','policy','session','actions')]
    project_entity=record('project','instance','Project','Curator project '+identity['name'],identity['purpose'],[named['policy']])
    process=record('process','instance','Capability','Curator process','Bounded project-local coordination of maintenance observations, current-owner evaluation and separately authorized execution.',general,
        scope_note='Ontology is declared knowledge. It does not create a Task, native actor, permission, service or completed outcome.')
    skill=record('skill','instance','Skill','Installed curate skill','Project-local public Curator entry point.',[ref('.agents/skills/curate/SKILL.md')])
    binding('skill',skill,[ref('.agents/skills/curate/SKILL.md')],'skill')
    edge('process',skill,CORE+'providesCapability',process,general)
    predicates={'consumes':(['Capability'],['Artifact']),'produces':(['Capability'],['Artifact']),
        'maintains':(['Capability'],['Artifact','Scope']),'coordinatesOwner':(['Capability'],['Skill','Role']),
        'forProject':(['Capability'],['Project']),'triggeredBy':(['Capability'],['Artifact']),'requiresPrerequisite':(['Capability'],['Artifact','Scope','Authority'])}
    for name,(domain,ran) in predicates.items():
        record('predicate-'+name,'predicate','RelationshipType','Curator '+name,'Curator function '+name+' relationship.',[named['actions']],
            domain=[CORE+x for x in domain],range=[CORE+x for x in ran],acyclic=False,cardinality={'min':0,'max':None},qualifiers={})
    edge('project-identity',process,rid('predicate-forProject'),project_entity,general)
    for key,owner in recipe['owners'].items():
        role_text=sources['Roles/'+owner['role']+'/ROLE.md'].decode()
        agents_text=sources['Roles/'+owner['role']+'/AGENTS.md'].decode()
        require(re.search(r'^name:\s*'+re.escape(owner['role'])+r'\s*$',role_text,re.M) is not None
                and all(section in role_text for section in ('## Purpose','## Authority','## Expected'))
                and 'ROLE.md' in agents_text and 'SOUL.md' in agents_text and '# ' in agents_text,
                'role_pair','Curator owner requires a valid matching role definition and instruction pair.')
        pair=[ref('Roles/'+owner['role']+'/'+leaf) for leaf in ('AGENTS.md','ROLE.md')]
        ent=record('owner-'+key,'instance','Role','Curator owner route '+key,'Persisted '+owner['role']+' supporting role proposes work for the '+key+' route; canonical publication remains with the current Director or confirmed Task manager.',pair)
        binding('owner-'+key,ent,pair,'role')
        owner_skill=record('owner-skill-'+key,'instance','Skill','Curator '+key+' owner skill','Installed '+owner['skill']+' public owner contract.',[ref('.agents/skills/'+owner['skill']+'/SKILL.md')])
        binding('owner-skill-'+key,owner_skill,[ref('.agents/skills/'+owner['skill']+'/SKILL.md')],'skill')
    categories={}
    for f in recipe['functions']:
        for field,typ in [('input','Artifact'),('output','Artifact'),('scope','Scope'),('prerequisite','Authority')]:
            key=('scope-' if typ=='Scope' else 'source-')+f[field]
            if key not in categories:
                categories[key]=record(key,'instance',typ,'Curator category '+f[field], (('Current bound Director or confirmed Task manager, exact current grant and applicable native owner checks are required.' if f[field] in ('current-grant','current-owner','live-actor-budget') else 'Selected read scope or configured session budget is required; inspection alone grants no execution authority.') if typ=='Authority' else 'Category of '+field+' used by Curator; no actual receipt or runtime state is asserted.'),[named[f['source']]])
    questions=[];ids=[f['id'] for f in recipe['functions']]
    require(len(ids)==len(set(ids)) and ids==matrix['functions'],'integration_recipe','Function inventory differs from reviewed competencies.')
    for f in recipe['functions']:
        refs=[named['actions'],named[f['source']]]
        if f['source']=='actions':refs=refs[:1]
        fn=record('function-'+f['id'],'instance','Capability','Curator '+f['id'],f['definition'],refs,
            scope_note='Declared function only; current source freshness is not authorization or observed execution.', aliases=['curator function '+f['id']])
        binding(f['id'],fn,refs)
        edge(f['id']+'-provided',skill,CORE+'providesCapability',fn,refs)
        expected=[]
        for pred,obj in [('consumes',rid('source-'+f['input'])),('produces',rid('source-'+f['output'])),
             ('maintains',rid('scope-'+f['scope'])),('coordinatesOwner',rid('owner-'+f['owner'])),
             ('triggeredBy',rid('source-'+f['input'])),('requiresPrerequisite',rid('source-'+f['prerequisite']))]:
            edge(f['id']+'-'+pred,fn,rid('predicate-'+pred),obj,refs)
            expected.append({'subject':fn,'predicate':rid('predicate-'+pred),'object':obj})
        edge(f['id']+'-public-owner',fn,rid('predicate-coordinatesOwner'),rid('owner-skill-'+f['owner']),refs)
        if f['id'] in ('update','correct','retry'):
            for owner in ('memory','ontology','products'):
                edge(f['id']+'-owner-'+owner,fn,rid('predicate-coordinatesOwner'),rid('owner-skill-'+owner),[named['commands']])
        questions.append({'id':'curator-'+f['id'],'intent':'definition','query':fn,'expected_ids':[fn],
                          'expected_relations':expected,'expected_sources':[r['path'] for r in refs]})
    all_ids=[r['@id'] for r in records+bindings]
    require(len(all_ids)==len(set(all_ids)) and not set(all_ids).intersection(canonical_inventory),'integration_collision','Reserved Curator identity collides with existing authored records.')
    graph=lambda items:canonical_bytes({'@context':CONTEXT_PATH,'@graph':items})
    return {'files':{GRAPH:graph(records),BINDINGS:graph(bindings),COMPETENCY:canonical_bytes({'schema_version':1,'questions':questions})},
            'additions':{'project_files':[GRAPH],'binding_files':[BINDINGS],'competency_files':[COMPETENCY],
                         'source_allowlist':source_paths(recipe_bytes)}, 'edition':EDITION}


def selection_config(config, additions):
    result=copy.deepcopy(config)
    for key,paths in additions.items():
        for path in paths:
            if path not in result.setdefault(key,[]):result[key].append(path)
    return result


def _inputs(root):
    recipe=resources(root)
    return recipe,{path:read_bytes(safe_path(root,path)) for path in source_paths(recipe)}


def _owned(root, path, digest):
    folder=safe_path(root,CONTROL+'receipts',must_exist=False)
    for file in sorted(folder.glob('*.json')) if folder.exists() else ():
        receipt=read_json(safe_path(root,file.relative_to(root).as_posix()))
        if receipt.get('status')=='complete' and receipt.get('edition')==EDITION and any(c['path']==path and c['sha256']==digest for c in receipt.get('files',[])):
            intent=_intent(root,receipt.get('operation_id'))
            require(receipt.get('intent_sha256')==intent['intent_sha256'] and receipt.get('preview_sha256')==intent['preview']['preview_sha256'],
                    'receipt_conflict','Integration ownership receipt differs from its immutable accepted intent.')
            return True
    setup=safe_path(root,'control_records/project-setup.json',must_exist=False)
    setup_records=[]
    if setup.exists():
        current_setup=read_json(setup);setup_records.append(current_setup)
        for historical in current_setup.get('history',[]):
            file=safe_path(root,historical['path'])
            require(sha256(file)==historical['sha256'],'receipt_conflict','Historical setup receipt changed.')
            setup_records.append(read_json(file))
    for value in setup_records:
        integration=value.get('curator_integration',{})
        generated=value.get('generated_files',{})
        source_rows=value.get('sources',[])
        recipe_hashes=[row.get('source_sha256') for row in source_rows if isinstance(row,dict) and row.get('destination')==RECIPE_ROOT+'/manifest.json'] if isinstance(source_rows,list) else []
        valid_provenance=(isinstance(value.get('operation_id'),str) and re.fullmatch(r'project-setup-[0-9a-f]{32}',value['operation_id'])
            and value.get('identity',{}).get('project_id')==read_json(safe_path(root,'ontology.yaml'))['project']['id']
            and set(generated)=={GRAPH,BINDINGS,COMPETENCY} and len(recipe_hashes)==1
            and all(isinstance(row,dict) and set(row)=={'sha256','recipe_manifest_sha256'} and row['recipe_manifest_sha256']==recipe_hashes[0] for row in generated.values())
            and all(value.get('owned_files',{}).get(p)==d for p,d in integration.get('files',{}).items()))
        if (valid_provenance and value.get('schema_version')==1 and value.get('setup_contract')=='governance-starter-v12'
            and value.get('status')=='completed' and value.get('completed_stages')==['assets','registration','verification']
            and value.get('project_root')==str(root) and integration.get('edition')==EDITION
            and integration.get('mode')=='setup-generated' and integration.get('status')=='completed'
            and set(integration.get('files',{}))==set(TARGETS)
            and integration['files'].get(path)==digest and value.get('owned_files',{}).get(path)==digest
            and (path=='ontology.yaml' or value.get('generated_files',{}).get(path,{}).get('sha256')==digest)
            and all(sha256(safe_path(root,p))==d for p,d in integration['files'].items())):
            return True
    if setup.exists():
        value=read_json(setup)
        if value.get('schema_version')==1 and value.get('status')=='completed' and value.get('completed_stages')==['assets','registration','verification'] and value.get('project_root')==str(root):
            for operation in value.get('module_adoptions',[]):
                generated=operation.get('generated_contents',{});integration=operation.get('curator_integration',{})
                if not (operation.get('schema_version')==2 and operation.get('module_id')=='project-curator' and operation.get('integration_edition')==EDITION
                    and operation.get('status')=='completed' and operation.get('completed_stages')==['assets','verification']
                    and integration.get('mode')=='setup-generated' and integration.get('status')=='completed' and set(generated)==set(TARGETS)):
                    continue
                frozen=('module_id','module_version','project_root','identity','base_receipt','refresh_dependencies','new_memory','sources','packages','files','preserved_files',
                        'new_curator_files','protected_inventory','prerequisites','integration_edition','refresh_modules','generated_contents')
                require(operation.get('manifest_sha256')==sha256(canonical_bytes({key:operation[key] for key in frozen})), 'receipt_conflict','Generated module ownership manifest changed.')
                require(sha256(safe_path(root,operation['base_receipt']['path']))==operation['base_receipt']['sha256'],'receipt_conflict','Original module setup receipt changed.')
                if path in generated and sha256(generated[path].encode())==digest and all(sha256(safe_path(root,p))==sha256(raw.encode()) for p,raw in generated.items()):return True
    return False


def preview(root, selection):
    from ontology_publication import _root
    root=_root(root)
    exact(selection,('schema_version','operation_id','reason'),('edition',))
    require(selection['schema_version']==1 and selection.get('edition',EDITION)==EDITION and re.fullmatch(r'ONTOP-[A-Za-z0-9-]{4,100}',selection['operation_id'] or ''),'integration_selection','Expected exact Curator integration selection.')
    require(isinstance(selection['reason'],str) and 0<len(selection['reason'].strip())<=2000,'integration_selection','A bounded reason is required.')
    old=load_project(root);recipe,sources=_inputs(root)
    require(decode_json(sources['curator.yaml'])['project']['coordination_root']==str(root),'identity_mismatch','Curator policy names another coordination root.')
    inventory={r['@id'] for r in old.records if not any(old.locations[r['@id']].startswith(path+'#') for path in (GRAPH,BINDINGS))}
    rendered=render(recipe,old.config['project'],sources,inventory)
    newcfg=selection_config(old.config,rendered['additions'])
    files={**rendered['files'],'ontology.yaml':canonical_bytes(newcfg)}
    changes=[]
    for path in TARGETS:
        target=safe_path(root,path,must_exist=False);before=sha256(target) if target.exists() else None
        require(path=='ontology.yaml' or before is None or _owned(root,path,before),'integration_unowned','Existing reserved integration files require an exact completed owner receipt.',path=path)
        changes.append({'path':path,'expected_sha256':before,'sha256':sha256(files[path]),'content':files[path].decode()})
    proposal={'schema_version':1,'operation':'integrate-curator','operation_id':selection['operation_id'],'reason':selection['reason'],'edition':EDITION,'changes':changes,
        'resources':{RECIPE_ROOT+'/'+name:sha256(raw) for name,raw in sorted(recipe.items())},'sources':{name:sha256(raw) for name,raw in sources.items()}}
    return _preview(root,proposal,old=old)


def check_proposal(root, proposal, prior=None):
    exact(proposal,('schema_version','operation','operation_id','reason','edition','changes','resources','sources'))
    require(proposal['schema_version']==1 and proposal['operation']=='integrate-curator' and proposal['edition']==EDITION,'integration_proposal','Unsupported integration proposal.')
    require(re.fullmatch(r'ONTOP-[A-Za-z0-9-]{4,100}',proposal['operation_id'] or ''),'integration_proposal','Invalid operation identity.')
    require([c['path'] for c in proposal['changes']]==list(TARGETS),'integration_scope','Only the four reserved integration targets in commit order are permitted.')
    for c in proposal['changes']:
        exact(c,('path','expected_sha256','sha256','content'))
        require(isinstance(c['content'],str) and len(c['content'].encode())<=250000 and sha256(c['content'].encode())==c['sha256'],'integration_content','Exact reviewed candidate bytes differ.')
        safe_path(root,c['path'],must_exist=False)
    oldcfg=decode_json(prior['ontology.yaml'].encode()) if prior else read_json(safe_path(root,'ontology.yaml'))
    recipe,sources=_inputs(root)
    require(decode_json(sources['curator.yaml'])['project']['coordination_root']==str(root),'identity_mismatch','Curator source root differs from selected publication root.')
    require(proposal['resources']=={RECIPE_ROOT+'/'+name:sha256(raw) for name,raw in sorted(recipe.items())} and proposal['sources']=={name:sha256(raw) for name,raw in sources.items()},'integration_input_changed','Selected recipe or finalized sources changed.')
    overrides={p:raw.encode() for p,raw in (prior or {}).items() if raw is not None and p!='ontology.yaml'}
    old=_load_project(root,config=oldcfg,overrides={p:b for p,b in overrides.items() if p in oldcfg['project_files']+oldcfg['binding_files']+oldcfg.get('competency_files',[])})
    inventory={r['@id'] for r in old.records if not any(old.locations[r['@id']].startswith(path+'#') for path in (GRAPH,BINDINGS))}
    generated=render(recipe,oldcfg['project'],sources,inventory)
    expected={**generated['files'],'ontology.yaml':canonical_bytes(selection_config(oldcfg,generated['additions']))}
    require(all(c['content'].encode()==expected[c['path']] for c in proposal['changes']),'integration_config_scope','Candidate must contain only deterministic recipe output and additive config selections.')
    newcfg=decode_json(expected['ontology.yaml'])
    new=_load_project(root,config=newcfg,overrides=generated['files'])
    for source in new.sources:
        if source['path'] in expected:
            require(source['sha256']==sha256(expected[source['path']]),'integration_protected_binding',
                    'An existing authored source binding would become stale after integration; review its separate owner change before publication.',path=source['path'])
            check_locator(expected[source['path']],source['locator'])
    require(all(s['status']=='current' for s in new.sources),'source_not_current','Complete candidate graph must use current sources.')
    return old,new


def _preview(root, proposal, old=None):
    old,new=check_proposal(root,proposal)
    for c in proposal['changes']:
        target=safe_path(root,c['path'],must_exist=False)
        require((sha256(target) if target.exists() else None)==c['expected_sha256'],'expected_changed','Integration target changed.')
    value={'schema_version':1,'operation':'integrate-curator','proposal':proposal,'payload_sha256':sha256(canonical_bytes(proposal)),
        'before':old.context(),'after':new.context(),'valid':True,'mutated':False}
    value['preview_sha256']=sha256(canonical_bytes(value));return value


def authorize(old,grant,proposal,pre):
    from ontology_authority import validate_native_observation,validate_director_binding,validate_manager_binding,active_managers,within
    exact(grant,('schema_version','grant_id','operation','project_id','actor_id','actor_kind','native_receipt','observed_at','expires_at','task','payload_sha256','preview_sha256','config_sha256','scope','reviewed_records','resources','sources','helpers'))
    require(grant['schema_version']==1 and grant['operation']=='integrate-curator' and str(grant['grant_id']).startswith('ONTIGRANT-'),'integration_grant','Use a distinct integration grant; legacy grants are not accepted.')
    require(old.config['publication']['enabled'],'publication_disabled','Authored integration publication is disabled.')
    require(grant['project_id']==old.project_id and grant['payload_sha256']==pre['payload_sha256'] and grant['preview_sha256']==pre['preview_sha256'],'grant_payload','Integration grant differs from exact preview.')
    require(grant['config_sha256']==next(c['expected_sha256'] for c in proposal['changes'] if c['path']=='ontology.yaml'),'config_changed','Grant must bind the original approved config predecessor, including recovery.')
    require(grant['scope']==list(TARGETS) and grant['reviewed_records']==[{k:c[k] for k in ('path','expected_sha256','sha256')} for c in proposal['changes']],'grant_scope','Integration grant differs from exact four pre/post targets.')
    require(grant['resources']==proposal['resources'] and grant['sources']==proposal['sources'] and grant['helpers']==pre['before']['helpers'],'grant_inputs','Integration grant must bind recipe, helpers and finalized sources.')
    validate_native_observation(grant)
    if grant['actor_kind']=='director':
        binding=validate_director_binding(old,grant['actor_id'])
        require(all(any(within(path,scope) for scope in binding['scope']) for path in TARGETS if path!='ontology.yaml'),'director_scope','Integration canonical targets exceed the existing Director binding scope.')
        require(grant['task'] is None,'director_unbound','Director grant must not impersonate a Task manager.')
        for _,_,assignment in active_managers(old.root):
            require(not any(within(path,scope) or within(scope,path) for path in TARGETS for scope in assignment.get('fit',{}).get('writes',[])),'manager_owns_scope','An unreconciled manager owns overlapping writes.')
    else:
        validate_manager_binding(old,grant['actor_id'],grant['task'],set(TARGETS))
        from ontology_authority import read_task
        state,_=read_task(old.root,grant['task']['path'])
        require(state['orchestration']['version']==1,'grant_version','Integration schema-1 grant requires orchestration version 1; protected-native v2 remains unsupported.')


def _paths(op):
    require(isinstance(op,str) and re.fullmatch(r'ONTOP-[A-Za-z0-9-]{4,100}',op),'integration_operation','Invalid exact operation identity.')
    return [CONTROL+kind+'/'+op+'.json' for kind in ('intents','receipts','recovery')]


def _intent(root,op):
    value=read_json(safe_path(root,_paths(op)[0]));body={k:v for k,v in value.items() if k!='intent_sha256'}
    require(value.get('intent_sha256')==sha256(canonical_bytes(body)) and value['proposal']['operation_id']==op,'intent_changed','Immutable integration intent changed.')
    pre=value['preview'];require(pre['preview_sha256']==sha256(canonical_bytes({k:v for k,v in pre.items() if k!='preview_sha256'})) and pre['proposal']==value['proposal'],'intent_changed','Immutable integration preview changed.')
    for c in value['proposal']['changes']:
        raw=value['prior_contents'][c['path']]
        require((sha256(raw.encode()) if raw is not None else None)==c['expected_sha256'],'intent_changed','Original integration predecessor changed.')
    return value


def _advance(root,intent,grant,fail_at=None,decision=None):
    proposal,pre=intent['proposal'],intent['preview'];_,receipt_path,recovery_path=_paths(proposal['operation_id'])
    old,new=check_proposal(root,proposal,intent['prior_contents'])
    require(old.context()['helpers']==pre['before']['helpers'],'helper_changed','Recovery helpers changed after accepted review.')
    for path,digest in pre['before']['inputs'].items():
        if path in TARGETS:continue
        target=safe_path(root,path,must_exist=False)
        require((sha256(target) if target.exists() else None)==digest,'recovery_input_changed','Protected integration input changed.',path=path)
    authorize(old,grant,proposal,pre)
    states=[]
    for c in proposal['changes']:
        target=safe_path(root,c['path'],must_exist=False);actual=sha256(target) if target.exists() else None
        require(actual in (c['expected_sha256'],c['sha256']),'recovery_conflict','Third-state edits are preserved; exact replay refused.',path=c['path'])
        states.append({k:c[k] for k in ('path','expected_sha256','sha256')})
    existing=safe_path(root,receipt_path,must_exist=False)
    if existing.exists():
        receipt=read_json(existing)
        require(receipt.get('intent_sha256')==intent['intent_sha256'] and all(sha256(safe_path(root,c['path']))==c['sha256'] for c in states),'receipt_conflict','Completed integration receipt differs from current targets.')
        return receipt
    try:
        if fail_at=='before_commit':raise OSError('Injected before commit')
        for index,c in enumerate(proposal['changes'],1):
            if decision is not None:decision.recheck(targets=False)
            target=safe_path(root,c['path'],must_exist=False);actual=sha256(target) if target.exists() else None
            if actual!=c['sha256']:atomic_write(root,c['path'],c['content'].encode(),c['expected_sha256'])
            if fail_at==f'after_commit:{index}':raise OSError('Injected target boundary')
        if fail_at=='projection':raise OSError('Injected projection boundary')
        from ontology_build import compile_project
        projection=compile_project(root)
        receipt={'schema_version':1,'edition':EDITION,'operation':'integrate-curator','operation_id':proposal['operation_id'],'status':'complete',
            'intent_sha256':intent['intent_sha256'],'preview_sha256':pre['preview_sha256'],'payload_sha256':pre['payload_sha256'],'files':states,
            'publisher':intent['publisher'],'context':load_project(root).context(),'projection':projection}
        if fail_at=='receipt':raise OSError('Injected owner receipt boundary')
        atomic_write(root,receipt_path,canonical_bytes(receipt),None);return receipt
    except (OntologyError,OSError) as exc:
        state={'schema_version':1,'status':'partial','operation_id':proposal['operation_id'],'intent_sha256':intent['intent_sha256'],
            'error':{'code':getattr(exc,'code','write_failure'),'message':str(exc)[:1000]},'recovery':'Renew exact original-preview grant and integration-recover this operation.'}
        path=safe_path(root,recovery_path,must_exist=False);atomic_write(root,recovery_path,canonical_bytes(state),sha256(path) if path.exists() else None)
        return state


def publish(root,proposal,grant,*,expected_preview_sha256,fail_at=None):
    from ontology_publication import _root,_integration_guard
    root=_root(root);decision=_integration_guard(root,'integration_publish',{'proposal':proposal,'grant':grant,'expected_preview_sha256':expected_preview_sha256})
    intent_path,_,_=_paths(proposal['operation_id'])
    with operation_lock(root,'control_records/ontology/publication.lock'):
        if safe_path(root,intent_path,must_exist=False).exists():
            intent=_intent(root,proposal['operation_id'])
            require(intent['proposal']==proposal and intent['preview']['preview_sha256']==expected_preview_sha256,'operation_reused','An operation cannot accept another payload.')
        else:
            pre=_preview(root,proposal);require(pre['preview_sha256']==expected_preview_sha256,'preview_changed','Reviewed integration preview changed.')
            old,_=check_proposal(root,proposal);authorize(old,grant,proposal,pre)
            for c in proposal['changes']:
                require(c['path']=='ontology.yaml' or c['expected_sha256'] is None or _owned(root,c['path'],c['expected_sha256']),'integration_unowned','Reserved integration bytes lack receipt ownership.')
            decision.recheck()
            intent={'schema_version':1,'proposal':copy.deepcopy(proposal),'preview':pre,'prior_contents':{c['path']:read_bytes(safe_path(root,c['path'])).decode() if c['expected_sha256'] is not None else None for c in proposal['changes']},'publisher':{'actor_id':grant['actor_id'],'actor_kind':grant['actor_kind'],'grant_id':grant['grant_id'],'grant_sha256':sha256(canonical_bytes(grant))}}
            intent['intent_sha256']=sha256(canonical_bytes(intent))
            if fail_at=='before_intent':raise OntologyError('injected_failure','Injected before intent')
            atomic_write(root,intent_path,canonical_bytes(intent),None)
        decision.lock_checked=True
        return decision.finish(_advance(root,intent,grant,fail_at,decision))


def recover(root,operation_id,grant,*,fail_at=None):
    from ontology_publication import _root,_integration_guard
    root=_root(root);intent=_intent(root,operation_id)
    decision=_integration_guard(root,'integration_recover',{'intent':intent,'proposal':intent['proposal'],'grant':grant,'operation_id':operation_id})
    with operation_lock(root,'control_records/ontology/publication.lock'):
        require(_intent(root,operation_id)==intent,'intent_changed','Accepted integration intent changed.')
        decision.lock_checked=True
        return decision.finish(_advance(root,intent,grant,fail_at,decision))
