"""Explicit optional setup and read-only readiness; no provisioning on reads."""
from pathlib import Path
import json
import os
import socket
import subprocess
import sys
import tempfile
import threading
from ontology_core import OntologyError, canonical_bytes, decode_json, read_bytes, require, safe_path, sha256
from ontology_advanced import load_advanced
from ontology_limits import limits
from ontology_worker import run_worker

PACKAGE=Path(__file__).resolve().parents[1]
ENV='.venv-ontology-standards'
CERT=ENV+'/certification.json'
WORKER_FILES=('ontology_core.py','ontology_limits.py','ontology_advanced.py','ontology_worker.py',
 'ontology_backend.py','ontology_rdf.py','ontology_provenance.py','ontology_sparql.py',
 'ontology_interchange.py','ontology_reasoning.py','ontology_derivations.py','ontology_shacl.py')
ONTOLOGY_GUARDED_ACTIONS = ['configure_profile']


def fingerprint(root):
    manifest=decode_json(read_bytes(PACKAGE/'profiles/standards-v1.json'))
    env=Path(root)/ENV
    site=env/'lib/python3.12/site-packages'
    require(site.is_dir() and not env.is_symlink() and not site.is_symlink(),'backend_unavailable','The selected standards environment is absent or aliased.')
    files={}
    for item in manifest['packages']:
        name=item['name'].replace('-','_')
        matches=list(site.glob(name+'-'+item['version']+'.dist-info'))
        require(len(matches)==1,'backend_incompatible','Locked package metadata is absent: '+item['name'])
        for folder in [site/name,matches[0]]:
            require(folder.is_dir() and not folder.is_symlink(),'backend_incompatible','Locked package directory is unavailable.')
            for path in sorted(folder.rglob('*')):
                if path.is_file() and '__pycache__' not in path.parts and path.suffix not in {'.pyc','.pyo'}:
                    require(not path.is_symlink(),'backend_incompatible','Package file symlinks are outside the locked profile.')
                    files[str(path.relative_to(site))]=sha256(path.read_bytes())
    return {'schema_version':1,'profile_sha256':sha256(PACKAGE/'profiles/standards-v1.json'),
        'lock_sha256':sha256(PACKAGE/'requirements-standards.txt'),
        'worker_files':{name:sha256(PACKAGE/'scripts'/name) for name in WORKER_FILES},
        'installed_files_sha256':sha256(canonical_bytes(files)),'python_executable_sha256':sha256((env/'bin/python').resolve().read_bytes()),
        'packages':{p['name']:p['version'] for p in manifest['packages']}}


def health(root,profile='standards'):
    try:
        import platform
        cfg=load_advanced(root)
        runtime=Path(root)/('.venv-ontology-semantic' if profile=='semantic' else ENV)
        presence=(runtime/'bin/python').is_file()
        if cfg is None: return {'status':'absent','implemented':True,'installed':'not_assessed' if presence else False,'runtime_present':presence,'enabled':False,'validated':False,'profile':profile}
        selection=cfg['profiles'].get(profile,{})
        if not selection.get('enabled',False): return {'status':'disabled','implemented':True,'installed':'not_assessed' if presence else False,'runtime_present':presence,'enabled':False,'validated':False,'profile':profile}
        if profile=='inference' and not cfg['profiles'].get('standards',{}).get('enabled',False):
            return {'status':'dependency_disabled','enabled':True,'validated':False,'profile':profile}
        if profile=='semantic':
            from ontology_semantic import health as semantic_health
            return semantic_health(root)
        require(profile in {'standards','inference'},'unsupported_profile','Unknown optional backend profile.')
        require(platform.system()=='Darwin' and Path('/usr/bin/sandbox-exec').is_file(),'confinement_unavailable','This standards profile has no verified confinement on the current host.')
        observed=fingerprint(root)
        certificate_path=cfg['profiles'].get('standards',{}).get('certification',CERT)
        path=safe_path(root,certificate_path,must_exist=False)
        if not path.exists(): return {'status':'uncertified','implemented':True,'installed':True,'enabled':True,'validated':False,'profile':profile,'fingerprint':observed}
        cert=decode_json(read_bytes(path))
        valid=(cert.get('fingerprint')==observed and cert.get('status')=='validated' and
               cert.get('platform')=='Darwin' and all(cert.get('checks',{}).get(k) is True for k in ('file_denied','network_denied','parser_file_denied','parser_network_denied','memory_terminated','timeout_terminated','cancelled','malformed_ipc','worker_failure','output_bounded')))
        return {'status':'ready' if valid else 'incompatible_certification','implemented':True,'installed':True,
            'enabled':True,'validated':valid,'profile':profile,'versions':cert.get('versions'),
            'fingerprint':observed,'certification_sha256':sha256(path),'guarded':False}
    except OntologyError as exc:
        return {'status':exc.code,'implemented':True,'enabled':True,'validated':False,'profile':profile,'diagnostics':[exc.as_dict()]}


def certify(root):
    import platform
    python=Path(root)/ENV/'bin/python'; bound=limits()
    for index in range(2):
        slot=Path(root)/ENV/('worker-slot-'+str(index))
        if not slot.exists():
            fd=os.open(slot,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600); os.close(fd)
    actual=run_worker(python,'versions',{},bound)
    require(actual.get('status')=='ok','backend_unavailable','Actual locked backend imports did not complete: '+str(actual.get('diagnostics'))+' '+actual.get('stderr',''))
    expected=fingerprint(root)
    require(actual['versions']['packages']==expected['packages'] and actual['versions']['python'].startswith('3.12.'),'backend_incompatible','Observed backend versions differ from the exact lock.')
    observations={}
    with tempfile.TemporaryDirectory(prefix='ontology-denial-') as temporary:
        sentinel=Path(temporary)/'sentinel.txt'; sentinel.write_text('unselected probe sentinel')
        listener=socket.socket(); listener.bind(('127.0.0.1',0)); listener.listen(); listener.settimeout(.01)
        port=listener.getsockname()[1]
        try:
            observations['file']=run_worker(python,'probe_file',{'path':str(sentinel)},bound)
            observations['network']=run_worker(python,'probe_network',{'port':port},bound)
            for name,url in (('parser_file',sentinel.as_uri()),('parser_network',f'http://127.0.0.1:{port}/context')):
                observations[name]=run_worker(python,'probe_parser',{'format':'json-ld','data':json.dumps({'@context':url,'@id':'urn:example:thing'})},bound)
            try: connection,_=listener.accept(); connection.close(); network_observed=True
            except socket.timeout: network_observed=False
            require(sentinel.read_text()=='unselected probe sentinel','probe_failure','Protected sentinel was modified.')
        finally: listener.close()
    observations['memory']=run_worker(python,'probe_memory',{},limits(overrides={'query_seconds':5}))
    observations['timeout']=run_worker(python,'probe_timeout',{},limits(overrides={'query_seconds':1}))
    cancel=threading.Event(); timer=threading.Timer(.2,cancel.set); timer.start()
    observations['cancel']=run_worker(python,'probe_timeout',{},bound,cancel=cancel); timer.join()
    for key,operation in (('malformed','probe_malformed'),('failure','probe_crash'),('output','probe_output')):
        observations[key]=run_worker(python,operation,{},bound)
    checks={k+'_denied':observations[k].get('denied') is True for k in ('file','network','parser_file','parser_network')}
    checks['network_denied']=checks['network_denied'] and not network_observed
    checks.update(memory_terminated=observations['memory'].get('status')=='memory_limit',timeout_terminated=observations['timeout'].get('status')=='timeout',
        cancelled=observations['cancel'].get('status')=='cancelled',malformed_ipc=observations['malformed'].get('status')=='malformed_ipc',
        worker_failure=observations['failure'].get('status')=='worker_failure',output_bounded=observations['output'].get('status')=='output_limit')
    result={'schema_version':1,'status':'validated' if all(checks.values()) else 'incomplete','platform':platform.system(),
        'versions':actual['versions'],'fingerprint':expected,'checks':checks,'observations':observations,
        'scope':'Darwin local standards worker only; no cross-host claim.'}
    (Path(root)/CERT).write_bytes(canonical_bytes(result))
    return result


def setup_profile(root,profile='standards',*,provision=False,certification=True):
    """Only explicit setup callers may provision; ordinary APIs never call this."""
    require(profile=='standards','unsupported_profile','This setup owns standards only; select semantic setup separately.')
    env=Path(root)/ENV
    require(not env.is_symlink(),'unsafe_symlink','Selected runtime cannot be a symlink.')
    if provision:
        commands=[]
        if not env.exists(): commands.append([sys.executable,'-m','venv',str(env)])
        commands.extend([[str(env/'bin/python'),'-m','pip','install','--only-binary=:all:','--require-hashes','-r',str(PACKAGE/'requirements-standards.txt')],
                         [str(env/'bin/python'),'-m','pip','check']])
        for command in commands:
            completed=subprocess.run(command,capture_output=True,text=True)
            require(completed.returncode==0,'profile_setup_failure','Selected standards setup failed: '+(completed.stderr or completed.stdout)[-800:])
    return certify(root) if certification else {'status':'installed','fingerprint':fingerprint(root),'enabled':False}


def preview_profile(root,profile,enabled,expected_config_sha256):
    import copy
    from ontology_core import exact
    require(profile in {'standards','inference','semantic','workbench'},'unsupported_profile','Configure only a separately selected optional profile; guard changes use guarded setup.')
    require(type(enabled) is bool,'invalid_profile','Profile enabled must be Boolean.')
    path=safe_path(root,'ontology-advanced.yaml')
    require(sha256(path)==expected_config_sha256,'config_changed','Advanced configuration changed after exact selection.')
    cfg=load_advanced(root,required=True); updated=copy.deepcopy(cfg)
    selected=updated['profiles'].setdefault(profile,{'enabled':False}); selected['enabled']=enabled
    content=canonical_bytes(updated)
    load_advanced(root,required=True,_overrides={'ontology-advanced.yaml':content})
    change={'path':'ontology-advanced.yaml','expected_sha256':expected_config_sha256,'content':content.decode(),'sha256':sha256(content)}
    return {'schema_version':1,'operation':'configure-profile','profile':profile,'enabled':enabled,'change':change,
            'guard_repair_required':False,
            'semantic_guard_required':cfg['profiles'].get('guards',{}).get('enabled',False)}


def configure_profile(root,profile,enabled,expected_config_sha256,authority):
    """Explicit local configuration under current Director authority, without setup."""
    from ontology_core import exact,load_project,operation_lock,atomic_write
    from ontology_authority import validate_native_observation,validate_director_binding,active_managers,within
    import re
    exact(authority,('schema_version','operation_id','operation','project_id','profile','enabled','expected_config_sha256',
          'actor_id','actor_kind','native_receipt','observed_at','expires_at'))
    require(authority['schema_version']==1 and authority['operation']=='configure-profile' and
            authority['profile']==profile and authority['enabled'] is enabled and
            authority['expected_config_sha256']==expected_config_sha256,'grant_scope','Setup authority must select these exact profile/configuration bytes.')
    require(isinstance(authority['operation_id'],str) and re.fullmatch(r'ONTPROFILE-[A-Za-z0-9-]{4,100}',authority['operation_id']),'invalid_operation','Use a unique ONTPROFILE operation identity.')
    intent_path='control_records/ontology/profile-setup/'+authority['operation_id']+'-intent.json'
    receipt_path='control_records/ontology/profile-setup/'+authority['operation_id']+'.json'
    intent_file=safe_path(root,intent_path,must_exist=False)
    if intent_file.exists():
        saved=decode_json(read_bytes(intent_file)); preview=saved['preview']
        before=saved.get('before_content','').encode()
        require(sha256(before)==expected_config_sha256,'intent_changed','Profile setup intent lost its exact accepted original configuration.')
        original=decode_json(before)
        original['profiles'].setdefault(profile,{'enabled':False})['enabled']=enabled
        require(canonical_bytes(original).decode()==preview['change']['content'] and sha256(canonical_bytes(original))==preview['change']['sha256'],'intent_changed','Profile intent includes changes beyond the selected enablement.')
        require(preview['profile']==profile and preview['enabled'] is enabled and preview['change']['expected_sha256']==expected_config_sha256,'operation_exists','Profile operation belongs to different reviewed bytes.')
        require(sha256(safe_path(root,'ontology-advanced.yaml')) in {expected_config_sha256,preview['change']['sha256']},'config_changed','Profile setup recovery does not match the accepted pre/post snapshots.')
    else: preview=preview_profile(root,profile,enabled,expected_config_sha256)
    guards_enabled = load_advanced(root,required=True)['profiles'].get('guards',{}).get('enabled',False)
    require(not (guards_enabled and profile == 'standards' and enabled is False),
            'guard_dependency','Enabled guards require the standards validation profile; keep it enabled while configuring other profiles.')
    from ontology_guards import begin_action,require_adapter,GuardError
    try:
        decision = begin_action(root,'setup','configure_profile',
            {'profile':profile,'enabled':enabled,'expected_config_sha256':expected_config_sha256,
             'authority':authority,'preview':preview},['ontology-advanced.yaml'])
        require_adapter(decision,__file__)
    except GuardError as exc:
        raise OntologyError(exc.code,str(exc)) from exc
    def recheck():
        try:
            decision.recheck()
            decision.lock_checked = True
        except GuardError as exc:
            raise OntologyError(exc.code,str(exc)) from exc
    def authorize():
        project=load_project(root,validate=False)
        require(authority['project_id']==project.project_id and authority['actor_kind']=='director','director_required','Profile configuration requires its current destination-local Director.')
        validate_native_observation(authority); validate_director_binding(project,authority['actor_id'])
        for _,_,assignment in active_managers(Path(root).absolute()):
            require(not any(within('ontology-advanced.yaml',scope) or within(scope,'ontology-advanced.yaml') for scope in assignment.get('fit',{}).get('writes',[])),'manager_owns_scope','An unreconciled manager owns the selected configuration.')
    authorize()
    with operation_lock(root,'control_records/ontology/publication.lock'):
        recheck()
        authorize()
        change=preview['change']
        current_sha=sha256(safe_path(root,change['path']))
        require(current_sha in {expected_config_sha256,change['sha256']},'config_changed','Profile changed at the mutation boundary.')
        receipt_file=safe_path(root,receipt_path,must_exist=False)
        if receipt_file.exists():
            existing=decode_json(read_bytes(receipt_file))
            require(current_sha==change['sha256'] and existing.get('change')=={k:change[k] for k in ('path','expected_sha256','sha256')},'config_changed','Completed profile receipt no longer matches the target.')
            return decision.finish({**existing,'receipt_path':receipt_path,'receipt_sha256':sha256(receipt_file),'replayed':True})
        if not intent_file.exists():
            require(preview_profile(root,profile,enabled,expected_config_sha256)==preview,'config_changed','Profile preview changed before setup intent.')
            atomic_write(root,intent_path,canonical_bytes({'schema_version':1,'preview':preview,'authority':authority,'before_content':read_bytes(safe_path(root,'ontology-advanced.yaml')).decode()}),None)
        recheck()
        if current_sha!=change['sha256']: atomic_write(root,change['path'],change['content'].encode(),expected_config_sha256)
        receipt={'schema_version':1,'status':'configured','profile':profile,'enabled':enabled,'provisioned':False,
            'change':{k:change[k] for k in ('path','expected_sha256','sha256')},'authority':authority}
        atomic_write(root,receipt_path,canonical_bytes(receipt),None)
    return decision.finish({**receipt,'receipt_path':receipt_path,'receipt_sha256':sha256(safe_path(root,receipt_path))})
