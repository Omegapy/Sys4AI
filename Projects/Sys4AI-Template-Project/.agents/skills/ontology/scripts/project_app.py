"""Project app entry and authenticated local-instance lifecycle. No installation."""
from __future__ import annotations
import sys
if __name__ == '__main__' and not (sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode):
    import posix
    posix.execve(sys.executable, [sys.executable, '-I', '-S', '-B', __file__, *sys.argv[1:]],
                 {'PATH':'/usr/bin:/bin', 'LANG':'en_US.UTF-8', 'PYTHONDONTWRITEBYTECODE':'1'})
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import signal
import socket
import stat
import subprocess
import time


def proof(secret, value):
    return hmac.new(secret.encode('ascii'), json.dumps(value, sort_keys=True, separators=(',', ':')).encode(), hashlib.sha256).hexdigest()


def root_scope(root, project):
    import ontology_explorer as t
    fd = t.directory(root)
    try: st = os.fstat(fd)
    finally: os.close(fd)
    return hashlib.sha256(t.compact({'domain':'sys4ai-project-app-root-v1', 'root':str(root),
        'device':st.st_dev, 'inode':st.st_ino, 'project_id':project})).hexdigest()


def instance_request(service, body):
    """Only a private receipt holder can request a fresh one-use browser entry."""
    import ontology_explorer as t
    t.need(type(body) is dict and set(body) == {'service_instance','project_id','root_scope_id','code_epoch','nonce','proof','action','issued_at'})
    t.need(body['service_instance'] == service.instance and body['project_id'] == service.project and
        body['root_scope_id'] == service.root_scope and body['code_epoch'] == service.package.code_epoch, 'identity_mismatch')
    t.need(body['action'] in ('ready','stop'))
    t.need(t.is_token(body['nonce']) and isinstance(body['proof'], str), 'session_invalid')
    signed = {k:v for k,v in body.items() if k != 'proof'}
    t.need(hmac.compare_digest(body['proof'], proof(service.control_secret, signed)), 'session_invalid')
    now = service.now()
    t.need(type(body['issued_at']) is int and 0 <= int(now*1000)-body['issued_at'] < 30000, 'session_invalid')
    service.control_nonces = {k:v for k,v in service.control_nonces.items() if v > now}
    t.need(body['nonce'] not in service.control_nonces and len(service.control_nonces) < 16, 'service_busy')
    service.control_nonces[body['nonce']] = now + 60
    result = {**signed, 'schema_version':1, 'status':'stopping' if body['action']=='stop' else 'ready'}
    if body['action']=='ready':
        service.prune()
        if len(service.bootstraps) >= 4:
            del service.bootstraps[min(service.bootstraps, key=service.bootstraps.get)]
        result['url']=service.bootstrap_url(service.new_bootstrap())
    return {**result, 'proof':proof(service.control_secret, result)}


def exchange(receipt, package, root, project, *, action='ready'):
    """Authenticate both request and response; a listening port proves nothing."""
    import ontology_explorer as t
    t.need(type(receipt) is dict and receipt.get('service') == t.APP_IDENTITY and
           receipt.get('schema_version') == 1 and receipt.get('project_id') == project and
           (receipt.get('code_epoch') == package.code_epoch or (action == 'stop' and isinstance(receipt.get('code_epoch'),str) and t.DIGEST.fullmatch(receipt['code_epoch']))) and receipt.get('root_scope_id') == root_scope(root, project), 'identity_mismatch')
    t.need(isinstance(receipt.get('service_instance'), str) and re.fullmatch(r'[a-f0-9]{32}',receipt['service_instance']) and
           t.is_token(receipt.get('credential')), 'identity_mismatch')
    origin = receipt.get('origin')
    t.need(isinstance(origin, str) and re.fullmatch(r'http://127\.0\.0\.1:[1-9][0-9]{0,4}',origin), 'identity_mismatch')
    port = int(origin.rsplit(':',1)[1]); t.need(port <= 65535)
    signed = {k:receipt[k] for k in ('service_instance','project_id','root_scope_id','code_epoch')}
    signed['nonce'] = t.token(); signed['action'] = action; signed['issued_at'] = int(time.monotonic()*1000)
    raw = t.compact({**signed,'proof':proof(receipt['credential'],signed)})
    deadline = time.monotonic() + 2
    connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    def remaining():
        left = deadline - time.monotonic(); t.need(left > 0, 'deadline_exceeded'); connection.settimeout(left)
    try:
        remaining(); connection.connect(('127.0.0.1',port))
        head = (f'POST {t.APP_API}instance HTTP/1.1\r\nHost: 127.0.0.1:{port}\r\nOrigin: {origin}\r\n'
                f'Content-Type: application/json\r\nContent-Length: {len(raw)}\r\nConnection: close\r\n\r\n').encode()
        remaining(); connection.sendall(head + raw)
        response = bytearray()
        while b'\r\n\r\n' not in response:
            remaining(); part = connection.recv(1024); t.need(part and len(response)+len(part) <= 8192); response.extend(part)
        headers, body = bytes(response).split(b'\r\n\r\n',1)
        lines = headers.split(b'\r\n'); t.need(lines[0].startswith(b'HTTP/1.1 200 '),'session_invalid')
        fields = {}
        for line in lines[1:]:
            key, value = line.decode('ascii').split(':',1); key=key.lower(); t.need(key not in fields); fields[key]=value.strip()
        t.need('transfer-encoding' not in fields and re.fullmatch(r'[1-9][0-9]{0,3}',fields.get('content-length','')))
        length = int(fields['content-length']); t.need(length <= 4096)
        while len(body) < length:
            remaining(); part=connection.recv(length-len(body)+1); t.need(part); body += part
        t.need(len(body)==length)
        result=t.strict(body); signature=result.pop('proof',None)
        t.need(isinstance(signature,str) and hmac.compare_digest(signature,proof(receipt['credential'],result)), 'identity_mismatch')
        t.need(all(result.get(k)==v for k,v in signed.items()) and result.get('status')==('stopping' if action=='stop' else 'ready') and result.get('schema_version')==1, 'identity_mismatch')
        if action=='stop':
            package.verify()
            return {'status':'stopping','service_instance':receipt['service_instance']}
        url=result.get('url'); prefix=origin+'/?app=1#bootstrap='
        t.need(isinstance(url,str) and url.startswith(prefix) and t.is_token(url[len(prefix):]), 'identity_mismatch')
        package.verify(); return url
    finally: connection.close()


def read_receipt(path):
    import ontology_explorer as t
    fd=t.directory(Path(path).parent)
    try:
        directory_info=os.fstat(fd)
        st=os.stat(Path(path).name,dir_fd=fd,follow_symlinks=False)
        t.need(directory_info.st_uid==os.getuid() and stat.S_IMODE(directory_info.st_mode)==0o700 and
               st.st_uid==os.getuid() and stat.S_IMODE(st.st_mode)==0o600, 'identity_mismatch')
        return t.strict(t.read_file(path,8192))
    finally: os.close(fd)


def reopen(package, root, project, *, action='ready'):
    import ontology_explorer as t
    directory=Path(root)/'.sys4ai/project-app'
    try: fd=t.directory(directory)
    except FileNotFoundError:return None
    try:
        # Refuse an unbounded or unsafe catalog instead of probing arbitrary files.
        names=[]
        with os.scandir(fd) as entries:
            for entry in entries:
                if re.fullmatch(r'service-[a-f0-9]{32}\.json',entry.name):
                    t.need(len(names)<16,'resource_limit');names.append(entry.name)
        deadline=time.monotonic()+3
        for name in sorted(names):
            if time.monotonic()>=deadline:break
            try:return exchange(read_receipt(directory/name),package,root,project,action=action)
            except (OSError,ValueError,KeyError,TypeError):continue
    finally:os.close(fd)
    return None


def open_browser(url):
    # The initial supported host is macOS; never run project-discovered code.
    if sys.platform == 'darwin':
        result=subprocess.run(['/usr/bin/open',url],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL,timeout=5,env={'PATH':'/usr/bin:/bin'})
        if result.returncode:raise ValueError('browser_unavailable')
    else:
        raise ValueError('browser_unavailable')


def command(args, package, assets):
    import ontology_explorer as t
    root=Path(args.project_root).absolute()
    reader=package.modules['project_app_core'].ProjectReader(root,package=package)
    project=reader.read('context',{}).get('project_id');t.need(project,'configuration_needed')
    if args.stop:
        result=reopen(package,root,project,action='stop')
        print(json.dumps(result or {'status':'not_running','project_id':project}),flush=True)
        return 0
    if args.serve:
        service=t.Service(package,assets,root,args.port,mode='app')
        def stop(signum,frame):service.stopping=True
        signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
        try:
            print(json.dumps({'service':t.APP_IDENTITY,'status':'running','origin':service.origin,
                'service_instance':service.instance,'identity_file':str(service.identity_file)}),flush=True)
            service.serve()
        finally:service.close();package.close()
        return 0
    url=reopen(package,root,project)
    if url is not None:
        if args.open:open_browser(url)
        print(json.dumps({'service':t.APP_IDENTITY,'status':'reopened','project_id':project}),flush=True)
        return 0
    process=subprocess.Popen([sys.executable,'-I','-S','-B','-c',t.BOOTSTRAP,
        str(package.scripts/'ontology_explorer.py'),package.helpers['ontology_explorer.py'],
        package.helpers['ontology_explorer_snapshot.py'],'--project-root',str(root),'app','--serve','--port',str(args.port)],
        stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,cwd='/',
        env=t.sanitized_environment(),start_new_session=True,bufsize=0)
    try:
        import select
        deadline=time.monotonic()+8; output=bytearray()
        while b'\n' not in output:
            left=deadline-time.monotonic();t.need(left>0,'deadline_exceeded')
            ready,_,_=select.select([process.stdout],[],[],min(left,.2))
            if ready:
                part=os.read(process.stdout.fileno(),4097-len(output));t.need(part,'package_incomplete');output.extend(part)
                t.need(len(output)<=4096,'resource_limit')
            t.need(process.poll() is None or b'\n' in output,'package_incomplete')
        result=t.strict(bytes(output).split(b'\n',1)[0]);t.need(result.get('status')=='running','package_incomplete')
        instance=result.get('service_instance');t.need(isinstance(instance,str) and re.fullmatch(r'[a-f0-9]{32}',instance))
        # Derive receipt path locally, never trust a returned filesystem path.
        receipt=read_receipt(root/'.sys4ai/project-app'/f'service-{instance}.json')
        url=exchange(receipt,package,root,project)
        if args.open:open_browser(url)
        print(json.dumps({'service':t.APP_IDENTITY,'status':'opened' if args.open else 'ready',
            'project_id':project,'origin':receipt['origin'],'service_instance':instance}),flush=True)
    except BaseException:
        # Only our still-owned child handle is eligible for termination.
        if process.poll() is None:process.terminate()
        try:process.wait(timeout=3)
        except subprocess.TimeoutExpired:process.kill();process.wait(timeout=2)
        raise
    finally:process.stdout.close()
    return 0


if __name__ == '__main__':
    # The transport performs the same captured-byte bootstrap and package checks
    # used by the standalone Explorer before it starts any service or worker.
    path=Path(__file__).absolute().with_name('ontology_explorer.py')
    arguments=sys.argv[1:]
    if '--project-root' not in arguments:
        print('{"status":"unavailable","error":"configuration_needed"}')
        raise SystemExit(2)
    index=arguments.index('--project-root')
    if index+1>=len(arguments):raise SystemExit(2)
    root=arguments[index+1]; remaining=arguments[:index]+arguments[index+2:]
    os.execve(sys.executable,[sys.executable,'-I','-S','-B',str(path),'--project-root',root,'app',*remaining],
              {'PATH':'/usr/bin:/bin','LANG':'en_US.UTF-8','PYTHONDONTWRITEBYTECODE':'1'})
