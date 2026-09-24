"""Disposable production-service HTTP and supervision regression checks."""
from __future__ import annotations
import base64
import gc
import hashlib
import http.client
import json
import os
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
import types
import unittest

SCRIPTS=Path(__file__).resolve().parents[1]/'scripts'
ROOT=SCRIPTS.parents[2]
OBSERVATIONS=[]
LIVE_HARNESSES=[]


def compile_file(name,path):
    raw=Path(path).read_bytes();module=types.ModuleType(name);module.__file__=str(path)
    sys.modules[name]=module;exec(compile(raw,str(path),'exec',dont_inherit=True),module.__dict__)
    return module


def inventory(root):
    return {str(p.relative_to(root)):(hashlib.sha256(p.read_bytes()).hexdigest(),p.stat().st_mtime_ns)
            for p in sorted(root.rglob('*')) if p.is_file()}


class Harness:
    def __init__(self, *, identity='explorer-fixture',limits=None,mutator=None):
        self.temp=tempfile.TemporaryDirectory(prefix='explorer-http-',dir='/private/tmp');self.base=Path(self.temp.name)
        self.scripts=self.base/'SKILLS-depo/ontology/scripts';self.scripts.mkdir(parents=True)
        for p in SCRIPTS.glob('ontology*.py'):shutil.copyfile(p,self.scripts/p.name)
        self.explorer=self.scripts.parent/'explorer';self.explorer.mkdir()
        for name in ('package.json','package-lock.json','THIRD_PARTY_NOTICES.md','BUILD.md'):
            shutil.copyfile(SCRIPTS.parent/'explorer'/name,self.explorer/name)
        shutil.copytree(SCRIPTS.parent/'explorer/assets',self.explorer/'assets')
        self.schema=self.base/'ONTOLOGY-depo/schema/explorer-v1.json';self.schema.parent.mkdir(parents=True)
        shutil.copyfile(ROOT/'ONTOLOGY-depo/schema/explorer-v1.json',self.schema)
        support=compile_file('_service_fixture_support',Path(__file__).parent/'explorer_support.py')
        self.fixture=support.make_explorer_project(self.base/'project',identity=identity)
        self.root=self.fixture['root'];self.ids=self.fixture['ids']
        if limits:
            cfg=self.root/'ontology-explorer.yaml';d=json.loads(cfg.read_text());d['limits'].update(limits);cfg.write_text(json.dumps(d))
        if mutator:mutator(self)
        self.before=inventory(self.root)
        self.launcher=compile_file('_service_test_launcher',self.scripts/'ontology_explorer.py')
        self.package,self.assets=self.launcher.prepare_package(self.scripts)
        LIVE_HARNESSES.append(self)
        self.module=self.package.modules['ontology_explorer'];self.service=None;self.thread=None
    def start(self):
        self.service=self.module.Service(self.package,self.assets,self.root)
        self.thread=threading.Thread(target=self.service.serve);self.thread.start();return self
    def request(self,path,body=None,*,method=None,headers=None,raw=None):
        method=method or ('POST' if body is not None or raw is not None else 'GET')
        h={'Host':f'127.0.0.1:{self.service.port}','Connection':'close'}
        if method=='POST':h.update({'Origin':self.service.origin,'Content-Type':'application/json'})
        h.update(headers or {})
        data=raw if raw is not None else json.dumps(body,separators=(',',':')).encode() if body is not None else None
        c=http.client.HTTPConnection('127.0.0.1',self.service.port,timeout=8)
        try:
            c.request(method,path,body=data,headers=h);r=c.getresponse();payload=r.read(8*1024**2+1)
            return r.status,dict(r.getheaders()),payload
        finally:c.close()
    def bootstrap(self):
        # Generated private runtime credential is used only in memory.
        return self.service.new_bootstrap()
    def connect(self,previous=None,bootstrap=None):
        value=bootstrap or self.bootstrap()
        body={'schema_version':1,'bootstrap':value,'client_build_id':self.assets.manifest['build_id'],
              'schema_sha256':hashlib.sha256(self.package.member_bytes['schema']).hexdigest()}
        status,headers,raw=self.request('/api/explorer/v1/session',body,headers={'Cookie':previous['cookie']} if previous else None)
        assert status==200,('session exchange',status,json.loads(raw)['error']['code'])
        admitted=json.loads(raw);return {'cookie':headers['Set-Cookie'].split(';',1)[0],'value':admitted,'headers':headers}
    def read(self,session,operation='context',params=None,snapshot=None,**kw):
        body={'schema_version':1,'request_id':'request','code_epoch':self.package.code_epoch,'snapshot':snapshot,
              'params':{'refresh':False} if params is None else params}
        body.update(kw.pop('body',{}));headers={'Cookie':session['cookie'],'X-Explorer-CSRF':session['value']['csrf']};headers.update(kw.pop('headers',{}))
        return self.request('/api/explorer/v1/'+operation,body,headers=headers,**kw)
    def close(self):
        if self.service:
            self.service.stopping=True
            if self.thread:self.thread.join(8)
            self.service.close()
        self.package.close();self.temp.cleanup()
        if self in LIVE_HARNESSES:LIVE_HARNESSES.remove(self)
        gc.collect()


class ServiceTests(unittest.TestCase):
    def setUp(self):self.h=Harness().start()
    def tearDown(self):self.h.close()
    def error(self,result,code):
        status,headers,raw=result;value=json.loads(raw)
        self.assertEqual(value['error']['code'],code)
        self.assertLessEqual(len(raw),1024);self.assertIsNone(value['project']);self.assertIsNone(value['snapshot'])
        self.assertEqual(headers['Cache-Control'],'no-store');return value
    def test_success_all_operations_and_safe_assets(self):
        h=self.h;s=h.connect();status,headers,raw=h.read(s);self.assertEqual(status,200)
        context=json.loads(raw);snap=context['snapshot'];self.assertEqual(context['data']['service']['identity'],h.module.IDENTITY)
        self.assertEqual(context['code_epoch'],h.package.code_epoch);self.assertEqual(context['session_scope'],s['value']['session_scope'])
        self.assertEqual(context['project']['root_scope_id'],context['data']['root_scope_id'])
        search=dict(query='',category=None,lifecycles=['draft','approved','deprecated'],fact_kinds=['asserted','derived','inferred','external'],sort='label',limit=3,cursor=None)
        graph=dict(id=h.ids['focus'],direction='both',predicate_ids=[],lifecycles=search['lifecycles'],fact_kinds=search['fact_kinds'],limit=3,cursor=None)
        cases=[('search',search),('entry',dict(id=h.ids['focus'],section='header',cursor=None)),('relationships',graph),('neighborhood',{**graph,'node_limit':3})]
        for op,params in cases:
            result=h.read(s,op,params,snap);self.assertEqual(result[0],200,(op,result[0]));value=json.loads(result[2])
            self.assertTrue(h.package.modules['ontology_explorer_read'].validate(value,op.title()+'Response',json.loads(h.package.member_bytes['schema'])))
            self.assertIn('coverage',value);self.assertIn('has_more',value['page'])
        refs=json.loads(h.read(s,'entry',dict(id=h.ids['focus'],section='sources',cursor=None),snap)[2])['data']['references']
        self.assertTrue(refs)
        source=h.read(s,'source',dict(owner_id=h.ids['focus'],reference_id=refs[0]['reference_id'],cursor=None),snap)
        self.assertEqual(source[0],200);self.assertEqual(json.loads(source[2])['data']['extraction']['content_type'],'text/plain')
        for path in ['/',*('/'+p for p in h.assets.members)]:
            status,headers,raw=h.request(path);self.assertEqual(status,200)
            self.assertEqual(headers['X-Content-Type-Options'],'nosniff');self.assertEqual(headers['Referrer-Policy'],'no-referrer')
            self.assertEqual(headers['Content-Security-Policy'],h.module.CSP);self.assertNotIn('unsafe-eval',headers['Content-Security-Policy'])
            head=h.request(path,method='HEAD');self.assertEqual(head[0],200);self.assertEqual(head[2],b'');self.assertEqual(head[1]['Content-Length'],str(len(raw)))
        for path in ('/manifest.json','/package-lock.json','/THIRD_PARTY_NOTICES.md','/src/main.ts','/node_modules/a.js','/ontology.yaml'):
            self.error(h.request(path),'resource_forbidden')
        OBSERVATIONS.append({'case':'all_operations_assets','loaded':h.service.worker.handshake,'worker_peak':h.service.worker.peak,'parent_peak':h.service.worker.parent_peak,'observations':h.service.worker.observations,'max_observation_gap_seconds':h.service.worker.max_observation_gap})
    def test_closed_transport_and_error_bounds(self):
        h=self.h
        self.error(h.request('/health',headers={'Host':'localhost:'+str(h.service.port)}),'host_forbidden')
        self.error(h.request('/',headers={'Origin':'https://outside.invalid'}),'origin_forbidden')
        self.error(h.request('/api/explorer/v1/context',{},headers={'Origin':'null'}),'origin_forbidden')
        self.error(h.request('/api/explorer/v1/context',{},headers={'Content-Type':'text/plain'}),'content_type_invalid')
        self.error(h.request('/api/explorer/v1/execute',{}),'endpoint_unavailable')
        self.error(h.request('/api/explorer/v1/context'),'method_forbidden')
        head=h.request('/health',method='HEAD');self.assertEqual(head[0],405);self.assertEqual(head[2],b'');self.assertEqual(head[1]['Cache-Control'],'no-store')
        self.error(h.request('/api/explorer/v1/context',{},raw=b'{}'*9000),'request_too_large')
        s=h.connect()
        self.error(h.read(s,body={'root':'/etc'}),'invalid_request')
        self.error(h.read(s,headers={'X-Explorer-CSRF':'wrong'}),'csrf_forbidden')
        for raw in (b'{"x":1,"x":2}',b'{"x":NaN}',b'\xff',b'{"a":'+b'['*18+b'0'+b']'*18+b'}'):
            self.error(h.request('/api/explorer/v1/context',raw=raw,headers={'Cookie':s['cookie'],'X-Explorer-CSRF':s['value']['csrf']}),'invalid_request')
        for code in h.service.errors:
            status,raw=h.service.error(code);self.assertLessEqual(len(raw),1024)
        self.assertTrue(h.request('/',headers={'Sec-Fetch-Site':'cross-site','Sec-Fetch-Mode':'navigate','Sec-Fetch-Dest':'document'})[0]==200)
        self.error(h.request('/health',headers={'Sec-Fetch-Site':'cross-site'}),'origin_forbidden')
    def test_raw_header_limits_duplicates_and_paths(self):
        h=self.h
        cases=[b'Host: duplicate\r\n', b'Transfer-Encoding: chunked\r\n',b'Origin: '+h.service.origin.encode()+b'\r\nOrigin: '+h.service.origin.encode()+b'\r\n']
        for extra in cases:
            sock=socket.create_connection(('127.0.0.1',h.service.port));sock.settimeout(3)
            sock.sendall(b'GET /health HTTP/1.1\r\nHost: 127.0.0.1:'+str(h.service.port).encode()+b'\r\n'+extra+b'\r\n')
            raw=sock.recv(8192);sock.close();self.assertIn(b' 400 ',raw)
        for target in ('/%2e%2e/ontology.yaml','/health?root=x','//health','/../ontology.yaml'):
            result=h.request(target);self.assertIn(result[0],(400,403))
    def test_sticky_helper_schema_asset_drift(self):
        h=self.h;s=h.connect()
        p=h.scripts/'ontology_explorer_read.py';old=p.read_bytes();st=p.stat();p.write_bytes(old+b'\n# changed\n');os.utime(p,ns=(st.st_atime_ns,st.st_mtime_ns))
        self.error(h.read(s),'package_changed');self.assertIsNone(h.service.worker.process)
        p.write_bytes(old);os.utime(p,ns=(st.st_atime_ns,st.st_mtime_ns))
        self.error(h.request('/'),'package_changed');self.assertEqual(json.loads(h.request('/health')[2])['status'],'package_changed')
        self.assertFalse(h.service.sessions)
    def test_nonmutation_private_modes_and_cleanup(self):
        h=self.h;s=h.connect();self.assertEqual(h.read(s)[0],200)
        for p in (h.service.bootstrap_file,h.service.identity_file):self.assertEqual(p.stat().st_mode&0o777,0o600)
        self.assertEqual(h.service.bootstrap_file.parent.stat().st_mode&0o777,0o700)
        h.service.stopping=True;h.thread.join(8);h.service.close()
        self.assertEqual(h.before,inventory(h.root))
    def test_worker_timeout_discards_preexisting_queue(self):
        h=self.h;a=h.connect();b=h.connect();pid=h.service.worker.process.pid
        os.kill(pid,signal.SIGSTOP)
        h.service.worker.last_start-=31
        results={}
        thread=threading.Thread(target=lambda:results.setdefault('a',h.read(a)));thread.start()
        deadline=time.monotonic()+2
        while h.service.active is None and time.monotonic()<deadline:time.sleep(.01)
        second=threading.Thread(target=lambda:results.setdefault('b',h.read(b)));second.start()
        deadline=time.monotonic()+1
        while h.service.waiting is None and time.monotonic()<deadline:time.sleep(.01)
        self.assertIsNotNone(h.service.waiting)
        self.assertEqual(h.read(b)[0],429)
        thread.join(8);second.join(8)
        self.error(results['a'],'deadline_exceeded');self.error(results['b'],'deadline_exceeded')
        self.assertIsNone(h.service.worker.process);self.assertIsNone(h.service.waiting)
        self.assertEqual(h.read(b)[0],200)
        self.assertNotEqual(pid,h.service.worker.process.pid)
        self.assertEqual(h.service.worker.handshake['loaded'],h.package.loaded_digests)
        OBSERVATIONS.append({'case':'deadline_replacement','old_pid_reaped':True,'loaded_reverified':True})
    def test_actual_parent_rss_refuses_new_work(self):
        h=self.h;s=h.connect();large=bytearray(72*1024**2)
        try:
            for i in range(0,len(large),4096):large[i]=1
            self.error(h.read(s),'resource_limit')
            self.assertTrue(h.service.parent_exhausted)
            self.assertIsNone(h.service.worker.process)
        finally:del large;gc.collect()
        self.error(h.read(s),'resource_limit')
        self.error(h.request('/'),'resource_limit')
        self.assertEqual(h.request('/health')[0],200)
        OBSERVATIONS.append({'case':'parent_rss','observed_peak_bytes':h.service.worker.parent_peak,'limit':67108864,'sticky_refusal':True})


class PackageRaceTests(unittest.TestCase):
    def test_mutated_snapshot_never_executes_before_child_admission(self):
        for filename in ('ontology_explorer.py','ontology_explorer_snapshot.py','ontology_explorer_read.py'):
            h=Harness();worker=h.module.PipeWorker(h.package,h.root,'1'*32,time.monotonic(),os.urandom(32));marker=h.base/'forbidden-execution'
            original=h.module.subprocess.Popen
            def swapped(*args,**kwargs):
                path=h.scripts/filename;raw=path.read_text();payload='\nopen('+repr(str(marker))+',"w").write("executed")\n'
                # A valid future-import prefix keeps the candidate executable.
                at=raw.find('\n',raw.find('from __future__ import annotations'))+1
                path.write_text(raw[:at]+payload+raw[at:]);return original(*args,**kwargs)
            h.module.subprocess.Popen=swapped
            try:
                with self.assertRaises(Exception) as caught:worker.start(time.monotonic()+5,initial=True);worker.wait_ready(time.monotonic()+5)
                self.assertEqual(getattr(caught.exception,'code',None),'package_changed',filename)
                self.assertFalse(marker.exists(),filename)
                OBSERVATIONS.append({'case':'verify_load_race','member':filename,'unverified_candidate_executed':False})
            finally:h.module.subprocess.Popen=original;worker.stop();h.close()
    def test_missing_assets_and_invalid_configuration(self):
        h=Harness()
        try:
            (h.explorer/'assets/manifest.json').unlink()
            with self.assertRaises(Exception):h.launcher.prepare_package(h.scripts)
        finally:h.close()
    def test_nested_manifest_entry_redirect(self):
        def nested(h):
            root=h.explorer/'assets';m=json.loads((root/'manifest.json').read_text());html=root/m['entry'];raw=html.read_bytes()
            # Keep relative imports valid when the document moves down one level.
            raw=raw.replace(b'./chunks/',b'../chunks/');(root/'nested').mkdir();(root/'nested/page.html').write_bytes(raw);html.unlink()
            for a in m['assets']:
                if a['path']==m['entry']:a.update(path='nested/page.html',bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
            m['entry']='nested/page.html';(root/'manifest.json').write_text(json.dumps(m))
        h=Harness(mutator=nested).start()
        try:
            for path in ('/','/index.html'):
                response=h.request(path);self.assertEqual(response[0],307);self.assertEqual(response[1]['Location'],'/nested/page.html')
            self.assertEqual(h.request('/nested/page.html')[0],200)
        finally:h.close()


class ResourceTests(unittest.TestCase):
    def test_actual_worker_rss_overshoot_killed_and_reaped(self):
        def allocation(h):
            p=h.scripts/'ontology_explorer_worker.py';s=p.read_text()
            s=s.replace("            job=receive()", "            job=receive()\n            if job.get('operation')=='search':\n                block=bytearray(280*1024**2)\n                for i in range(0,len(block),4096):block[i]=1\n                time.sleep(2)")
            p.write_text(s)
        h=Harness(mutator=allocation).start()
        try:
            session=h.connect();context=json.loads(h.read(session)[2]);pid=h.service.worker.process.pid
            params=dict(query='',category=None,lifecycles=['approved'],fact_kinds=['asserted'],sort='label',limit=2,cursor=None)
            start=time.monotonic();response=h.read(session,'search',params,context['snapshot']);elapsed=time.monotonic()-start
            self.assertEqual(json.loads(response[2])['error']['code'],'resource_limit');self.assertIsNone(h.service.worker.process)
            self.assertGreater(h.service.worker.peak,268435456);self.assertLess(elapsed,2)
            OBSERVATIONS.append({'case':'worker_rss','peak_bytes':h.service.worker.peak,'limit_bytes':268435456,
                'overshoot_bytes':h.service.worker.peak-268435456,'elapsed_seconds':elapsed,'max_observation_gap_seconds':h.service.worker.max_observation_gap,'owned_pid_reaped':True,
                'qualification':'Trusted disposable fault fixture allocates resident pages; operational sampling, not prevention of transient overshoot.'})
        finally:h.close()
    def test_header_body_absolute_timeout_and_eight_socket_cap(self):
        h=Harness().start();sockets=[]
        try:
            start=time.monotonic()
            for _ in range(9):
                sock=socket.create_connection(('127.0.0.1',h.service.port));sock.settimeout(3);sockets.append(sock)
            time.sleep(.05);self.assertLessEqual(len(h.service.connections),8)
            for sock in sockets:
                try:sock.sendall(b'G')
                except OSError:pass
            time.sleep(2.05)
            self.assertLessEqual(time.monotonic()-start,3)
            self.assertTrue(all(c.stage=='write' or c.closed for c in h.service.connections.values()))
        finally:
            for sock in sockets:sock.close()
            h.close()


class QualifierTests(unittest.TestCase):
    def test_1025_scalar_qualifiers_survive_reader_ipc_http(self):
        def qualifiers(h):
            cfg=json.loads((h.root/'ontology.yaml').read_text());documents=[];relation=None;predicate=None
            for relative in cfg['project_files']:
                path=h.root/relative;doc=json.loads(path.read_text());documents.append((path,doc))
                for row in doc['@graph']:
                    if row['@id'].endswith(':relation-000000'):relation=row
            assert relation is not None
            for _,doc in documents:
                for row in doc['@graph']:
                    if row['@id']==relation['predicate']:predicate=row
            assert predicate is not None
            predicate.setdefault('qualifiers',{}).update({f'q{i}':{'type':'integer','required':False} for i in range(1025)})
            relation['qualifiers']={f'q{i}':i for i in range(1025)}
            for path,doc in documents:path.write_text(json.dumps(doc))
        h=Harness(mutator=qualifiers).start()
        try:
            s=h.connect();context=json.loads(h.read(s)[2]);params=dict(id=h.ids['focus'],direction='both',predicate_ids=[],
                lifecycles=['draft','approved','deprecated'],fact_kinds=['asserted','derived','inferred','external'],limit=1,cursor=None)
            result=h.read(s,'relationships',params,context['snapshot']);self.assertEqual(result[0],200)
            edge=json.loads(result[2])['data']['items'][0];self.assertEqual(edge['kind'],'edge');self.assertEqual(len(edge['edge']['qualifiers']),1025)
            self.assertEqual(edge['edge']['qualifiers']['q1024'],1024)
            OBSERVATIONS.append({'case':'canonical_1025_qualifiers_http','response_bytes':len(result[2]),'qualifiers':1025,'full_edge':True})
        finally:h.close()


class AdditionalPackageTests(unittest.TestCase):
    def test_schema_or_asset_or_helper_addition_is_sticky(self):
        for kind in ('schema','asset','helper_addition'):
            h=Harness().start()
            try:
                s=h.connect()
                if kind=='schema':p=h.schema
                elif kind=='asset':p=h.explorer/'assets'/next(x for x in h.assets.members if x.endswith('.js'))
                else:p=h.scripts/'ontology_unexpected.py'
                old=p.read_bytes() if p.exists() else None;st=p.stat() if p.exists() else None
                p.write_bytes((old or b'')+b'\n ')
                if st:os.utime(p,ns=(st.st_atime_ns,st.st_mtime_ns))
                self.assertEqual(json.loads(h.read(s)[2])['error']['code'],'package_changed')
                if old is None:p.unlink()
                else:p.write_bytes(old)
                self.assertEqual(json.loads(h.request('/')[2])['error']['code'],'package_changed')
            finally:h.close()
    def test_optional_config_defaults_and_explicit_private_path_confinement(self):
        h=Harness()
        try:
            (h.root/'ontology-explorer.yaml').unlink();h.start();s=h.connect();context=json.loads(h.read(s)[2])
            self.assertEqual(context['data']['process_ids'],[]);self.assertEqual(context['data']['project']['id'],'explorer-fixture')
        finally:h.close()
        h=Harness()
        try:
            with self.assertRaises(Exception):h.module.Service(h.package,h.assets,h.root,session_file=h.base/'outside.json')
            self.assertFalse((h.base/'outside.json').exists())
        finally:h.close()
