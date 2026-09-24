"""Bounded selected-reader inspection, separate from optional profile readiness."""
from __future__ import annotations
import hashlib
import socket
import os
from pathlib import Path
import re
import time
import ontology_explorer as transport


def inspect(package,assets,root,url=None):
    result={'operation':'explorer-health','service':transport.IDENTITY,'installed':True,'configured':None,
        'running':None,'readable':False,'stale':None,'wrong_project':None,'unavailable':False,
        'endpoint':{'status':'not_requested'},'local':{},'mutated':False}
    if url is not None:
        transport.need(isinstance(url,str) and re.fullmatch(r'http://127\.0\.0\.1:([1-9][0-9]{0,4})/?',url),'invalid_request')
        port=int(url.rstrip('/').rsplit(':',1)[1]);transport.need(port<=65535)
        origin=f'http://127.0.0.1:{port}'
        try:
            value=probe(port)
            module=package.modules['ontology_explorer_read']
            transport.need(module.validate(value,'HealthResponse',__import__('json').loads(package.member_bytes['schema'])))
            result['running']=True;result['endpoint']={'status':value['status'],'service_instance':value['service_instance'],'build_id':value['build_id']}
            # Public health cannot establish root identity; only the selected
            # root's matching private instance receipt adds that observation.
            receipt=Path(root)/'.sys4ai/ontology/explorer'/('service-'+value['service_instance']+'.json')
            try:
                local=transport.strict(transport.read_file(receipt,8192))
                if local.get('origin')==origin and local.get('service_instance')==value['service_instance']:
                    result['_receipt']=local
            except (OSError,transport.ServiceError):pass
            if value['status']=='package_changed':result['unavailable']=True
        except ConnectionRefusedError:
            result['running']=False;result['unavailable']=True;result['endpoint']={'status':'connection_refused'}
        except (OSError,ValueError):
            result['unavailable']=True;result['endpoint']={'status':'unavailable'}
    worker=transport.PipeWorker(package,root,os.urandom(16).hex(),time.monotonic(),os.urandom(32))
    try:
        deadline=time.monotonic()+5;worker.start(deadline,initial=True);ready=worker.wait_ready(deadline)
        result.update(configured=True,readable=True,stale=ready['stale'])
        result['local']={'status':'readable','project_id':ready['project'],'root_scope_id':ready['root_scope_id']}
        receipt=result.pop('_receipt',None)
        if receipt is not None:
            result['wrong_project']=receipt.get('project_id')!=ready['project'] or receipt.get('root_scope_id')!=ready['root_scope_id']
    except Exception as exc:
        code=getattr(exc,'code','internal_error')
        result['configured']=False if code in ('configuration_needed','identity_mismatch','presentation_invalid') else None
        result['wrong_project']=True if code=='identity_mismatch' else result['wrong_project']
        result['unavailable']=True;result['local']={'status':'unavailable','error':code}
        result.pop('_receipt',None)
    finally:worker.stop()
    return result


def probe(port):
    """Two-second absolute budget includes connect, all headers and the body."""
    deadline=time.monotonic()+2
    connection=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    def remaining():
        value=deadline-time.monotonic()
        if value<=0:raise TimeoutError()
        connection.settimeout(value)
    try:
        remaining();connection.connect(('127.0.0.1',port))
        remaining();connection.sendall(('GET /health HTTP/1.1\r\nHost: 127.0.0.1:'+str(port)+'\r\nConnection: close\r\n\r\n').encode())
        raw=bytearray()
        while b'\r\n\r\n' not in raw:
            transport.need(len(raw)<=8192)
            remaining();part=connection.recv(min(1024,8193-len(raw)))
            transport.need(part);raw.extend(part)
        head,body=bytes(raw).split(b'\r\n\r\n',1)
        transport.need(len(head)+4<=8192)
        lines=head.split(b'\r\n');transport.need(len(lines)<=33 and len(lines[0])<=2048)
        status=lines[0].decode('ascii').split(' ')
        transport.need(len(status)>=2 and status[0]=='HTTP/1.1' and status[1]=='200')
        headers={}
        for line in lines[1:]:
            transport.need(b':' in line and not line.startswith((b' ',b'\t')))
            key,value=line.decode('ascii').split(':',1);key=key.lower();value=value.strip(' ')
            transport.need(re.fullmatch(r"[!#$&'*+.^_`|~0-9A-Za-z-]+",key) and key not in headers and all(32<=ord(c)<127 for c in value))
            headers[key]=value
        transport.need('transfer-encoding' not in headers and re.fullmatch(r'[1-9][0-9]{0,3}',headers.get('content-length','')))
        length=int(headers['content-length']);transport.need(length<=1024 and len(body)<=length)
        while len(body)<length:
            remaining();part=connection.recv(length-len(body)+1);transport.need(part);body+=part
            transport.need(len(body)<=length)
        transport.need(time.monotonic()<deadline)
        return transport.strict(body)
    finally:connection.close()
