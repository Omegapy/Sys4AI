"""Private fixed reader loop; stdin/stdout pipes are its only request interface."""
from __future__ import annotations
import base64
import hashlib
import os
import sys
import time
import ontology_explorer as transport


def receive():
    def take(size):
        result=bytearray()
        while len(result)<size:
            chunk=os.read(0,size-len(result))
            if not chunk:raise EOFError()
            result.extend(chunk)
        return bytes(result)
    size=int.from_bytes(take(4),'big')
    transport.need(0<size<=131072,'resource_limit')
    return transport.strict(take(size),members=1024,arrays=512)


def send(value):
    raw=transport.compact(value)
    transport.need(len(raw)<=131072,'resource_limit')
    value=memoryview(len(raw).to_bytes(4,'big')+raw)
    while value:value=value[os.write(1,value):]


def run(package,assets,initial):
    store=None; reader=None
    try:
        transport.need(isinstance(initial,dict) and set(initial)=={'kind','root','manifest','epoch','instance','started','secret','deadline','mode'} and initial['kind']=='start')
        transport.need(initial['manifest']==package.manifest and initial['epoch']==package.code_epoch,'package_changed')
        transport.need(initial['mode'] in ('app', 'explorer'))
        reader_module=package.modules['ontology_explorer_read']
        snapshot_module=package.modules['ontology_explorer_snapshot']
        app=None; current_job=None
        def knowledge_reader():
            nonlocal store, reader
            if reader is None:
                store=snapshot_module.SnapshotStore(initial['root'],package,expected_project_id=app.project_id if app else None)
                reader=reader_module.Reader(store,service_instance=initial['instance'],build_id=assets.manifest['build_id'],
                    schema_sha256=hashlib.sha256(package.member_bytes['schema']).hexdigest(),
                    service_secret=base64.b64decode(initial['secret'],validate=True),started_monotonic=initial['started'])
            return reader
        def knowledge_search(query):
            selected=knowledge_reader()
            request={'schema_version':1,'request_id':'app-search','code_epoch':package.code_epoch,'snapshot':None,'params':{'refresh':False}}
            context=selected.read('context',request,session_scope=current_job['scope'],deadline=current_job['deadline'])
            if context['status']=='error':return context
            request.update(snapshot=context['snapshot'],params={'query':query,'category':None,'lifecycles':['draft','approved','deprecated'],
                'fact_kinds':['asserted','derived','inferred','external'],'sort':'relevance','limit':min(10,selected.policy(store.current)['page_items']),'cursor':None})
            return selected.read('search',request,session_scope=current_job['scope'],deadline=current_job['deadline'])
        if initial['mode'] == 'app':
            app = package.modules['project_app_core'].ProjectReader(initial['root'], package=package)
            app.knowledge_search=knowledge_search
            context = app.read('context', {})
            transport.need(context.get('project_id'), 'configuration_needed')
            schema = transport.strict(package.member_bytes['schema'], arrays=1024, members=1024)
            policy = {k:v['default'] for k,v in schema['$defs']['ConfiguredLimits']['properties'].items()}
            policy.update({k:v['const'] for k,v in schema['$defs']['EffectivePolicy']['properties'].items() if 'const' in v})
            policy.update(visited_nodes=100, default_page_items=min(20,policy['page_items']))
            root_scope = package.modules['project_app'].root_scope(initial['root'],context['project_id'])
            ready = {'kind':'ready','epoch':package.code_epoch,'loaded':dict(package.loaded_digests),
                'policy':policy,'project':context['project_id'],'root_scope_id':root_scope,'stale':False}
        else:
            selected=knowledge_reader()
            # Standalone Explorer still requires a valid selected ontology.
            with store.lease(deadline=initial['deadline']) as view:
                policy=selected.policy(view)
                ready={'kind':'ready','epoch':package.code_epoch,'loaded':dict(package.loaded_digests),
                    'policy':policy,'project':view.project.project_id,'root_scope_id':view.root_scope_id,
                    'stale':any(s.get('status')!='current' for s in view.project.sources)}
        package.verify();send(ready)
        while True:
            job=receive();current_job=job
            transport.need(isinstance(job,dict) and set(job)=={'kind','operation','request','scope','deadline'} and job['kind'] in ('read','app-read'))
            transport.need(job['operation'] in (transport.APP_OPERATIONS if job['kind']=='app-read' else transport.OPERATIONS))
            try:
                package.verify()
                if job['kind']=='app-read':
                    transport.need(app is not None)
                    body=app.read(job['operation'],job['request']['params'])
                else:
                    if app is not None:
                        context=app.read('context', {})
                        transport.need(context.get('status')=='ready' and context.get('identity')==app.identity, 'identity_mismatch')
                    selected=knowledge_reader()
                    body=selected.read(job['operation'],job['request'],session_scope=job['scope'],deadline=job['deadline'])
                package.verify()
            except Exception as exc:
                code=getattr(exc,'code','internal_error')
                if job['kind']=='app-read' and code != 'package_changed':
                    from datetime import datetime, timezone
                    body={'schema_version':1,'operation':job['operation'],'status':'unavailable','project_id':app.project_id,
                        'observed_at':datetime.now(timezone.utc).isoformat(),'issues':['reader_unavailable']}
                elif job['kind']=='app-read':raise
                else:
                    selected=knowledge_reader()
                    _,body=selected.error_response(code,operation=job['operation'],request_id=job['request'].get('request_id'))
            if store and store.current and initial['mode']=='explorer':policy=reader.policy(store.current)
            send({'kind':'result','epoch':package.code_epoch,'loaded':dict(package.loaded_digests),'body':body,'policy':policy})
    except EOFError:return 0
    except Exception as exc:
        try:send({'kind':'failed','code':getattr(exc,'code','internal_error')})
        except (OSError,transport.ServiceError):pass
        return 2
    finally:
        if store:store.close()
