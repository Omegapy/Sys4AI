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
    store=None
    try:
        transport.need(isinstance(initial,dict) and set(initial)=={'kind','root','manifest','epoch','instance','started','secret','deadline'} and initial['kind']=='start')
        transport.need(initial['manifest']==package.manifest and initial['epoch']==package.code_epoch,'package_changed')
        reader_module=package.modules['ontology_explorer_read']
        snapshot_module=package.modules['ontology_explorer_snapshot']
        store=snapshot_module.SnapshotStore(initial['root'],package)
        reader=reader_module.Reader(store,service_instance=initial['instance'],build_id=assets.manifest['build_id'],
            schema_sha256=hashlib.sha256(package.member_bytes['schema']).hexdigest(),
            service_secret=base64.b64decode(initial['secret'],validate=True),started_monotonic=initial['started'])
        # Install Reader's semantic validator before this first materialization.
        with store.lease(deadline=initial['deadline']) as view:
            policy=reader.policy(view)
            ready={'kind':'ready','epoch':package.code_epoch,'loaded':dict(package.loaded_digests),
                'policy':policy,'project':view.project.project_id,'root_scope_id':view.root_scope_id,
                'stale':any(s.get('status')!='current' for s in view.project.sources)}
        package.verify();send(ready)
        while True:
            job=receive()
            transport.need(isinstance(job,dict) and set(job)=={'kind','operation','request','scope','expires','deadline'} and job['kind']=='read')
            transport.need(job['operation'] in transport.OPERATIONS)
            try:
                package.verify()
                body=reader.read(job['operation'],job['request'],session_scope=job['scope'],
                    session_expires_ms=job['expires'],deadline=job['deadline'])
                package.verify()
            except (reader.error_type,store.error_type,package.error_type) as exc:
                _,body=reader.error_response(exc.code,operation=job['operation'],request_id=job['request'].get('request_id'),
                    limits=dict(items=policy['page_items'],bytes=policy['response_bytes'],visited_nodes=policy['visited_nodes'],seconds=policy['request_seconds']))
            except Exception:
                _,body=reader.error_response('internal_error',operation=job['operation'],request_id=job['request'].get('request_id'))
            if store.current:policy=reader.policy(store.current)
            send({'kind':'result','epoch':package.code_epoch,'loaded':dict(package.loaded_digests),'body':body,'policy':policy})
    except EOFError:return 0
    except Exception as exc:
        try:send({'kind':'failed','code':getattr(exc,'code','internal_error')})
        except (OSError,transport.ServiceError):pass
        return 2
    finally:
        if store:store.close()
