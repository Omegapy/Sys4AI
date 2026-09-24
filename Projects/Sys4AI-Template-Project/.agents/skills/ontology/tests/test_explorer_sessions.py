"""Real HTTP session isolation with credentials confined to test process memory."""
import json
import os
import signal
import socket
import threading
import time
import unittest
from test_explorer_service import Harness,OBSERVATIONS


class SessionTests(unittest.TestCase):
    def setUp(self):self.h=Harness().start()
    def tearDown(self):self.h.close()
    def code(self,result):return json.loads(result[2])['error']['code']
    def test_replay_replacement_and_resume_without_expiry(self):
        h=self.h;bootstrap=h.bootstrap();a=h.connect(bootstrap=bootstrap);b=h.connect()
        data={'schema_version':1,'bootstrap':bootstrap,'client_build_id':h.assets.manifest['build_id'],
              'schema_sha256':a['value']['schema_sha256']}
        self.assertEqual(self.code(h.request('/api/explorer/v1/session',data)),'session_invalid')
        resumed=h.request('/api/explorer/v1/session-resume',{k:v for k,v in data.items() if k!='bootstrap'},headers={'Cookie':a['cookie']})
        self.assertEqual(resumed[0],200);self.assertEqual(json.loads(resumed[2])['session_scope'],a['value']['session_scope'])
        a2=h.connect(previous=a)
        self.assertNotEqual(a2['value']['session_scope'],a['value']['session_scope'])
        self.assertEqual(self.code(h.read(a)),'session_invalid');self.assertEqual(h.read(b)[0],200)
        old_build={**data,'bootstrap':h.bootstrap(),'client_build_id':'0'*64}
        self.assertEqual(self.code(h.request('/api/explorer/v1/session',old_build)),'package_changed')
        self.assertFalse(h.service.changed);self.assertEqual(h.read(b)[0],200)
        key=a2['cookie'].split('=',1)[1];self.assertNotIn('expires',h.service.sessions[key])
        self.assertEqual(h.read(a2)[0],200)
        self.assertEqual(h.read(b)[0],200)
        attrs=a['headers']['Set-Cookie'];self.assertTrue('HttpOnly' in attrs and 'SameSite=Strict' in attrs and 'Path=/api/explorer/v1/' in attrs)
        self.assertFalse('Domain=' in attrs or 'Secure' in attrs or 'Max-Age=' in attrs or 'Expires=' in attrs)
    def test_capacity_does_not_evict_and_close_is_isolated(self):
        h=self.h;sessions=[h.connect() for _ in range(8)]
        body={'schema_version':1,'bootstrap':h.bootstrap(),'client_build_id':h.assets.manifest['build_id'],
              'schema_sha256':sessions[0]['value']['schema_sha256']}
        self.assertEqual(self.code(h.request('/api/explorer/v1/session',body)),'service_busy')
        for s in sessions:self.assertEqual(h.read(s)[0],200)
        replacement=h.connect(previous=sessions[0]);self.assertEqual(len(h.service.sessions),8)
        result=h.request('/api/explorer/v1/session-close',{'schema_version':1,'code_epoch':h.package.code_epoch},
            headers={'Cookie':replacement['cookie'],'X-Explorer-CSRF':replacement['value']['csrf']})
        self.assertEqual(result[0],200);self.assertTrue('Max-Age=0' in result[1]['Set-Cookie'])
        self.assertEqual(h.read(sessions[1])[0],200);self.assertEqual(self.code(h.read(replacement)),'session_invalid')
    def test_cancel_or_close_a_preserves_healthy_worker_for_b(self):
        h=self.h;a=h.connect();b=h.connect();pid=h.service.worker.process.pid
        os.kill(pid,signal.SIGSTOP)
        sock=socket.create_connection(('127.0.0.1',h.service.port));body=json.dumps({'schema_version':1,'request_id':'cancel',
            'code_epoch':h.package.code_epoch,'snapshot':None,'params':{'refresh':False}}).encode()
        head=f'POST /api/explorer/v1/context HTTP/1.1\r\nHost: 127.0.0.1:{h.service.port}\r\nOrigin: {h.service.origin}\r\nContent-Type: application/json\r\nCookie: {a["cookie"]}\r\nX-Explorer-CSRF: {a["value"]["csrf"]}\r\nContent-Length: {len(body)}\r\n\r\n'
        sock.sendall(head.encode()+body)
        deadline=time.monotonic()+1
        while h.service.active is None and time.monotonic()<deadline:time.sleep(.01)
        self.assertIsNotNone(h.service.active);sock.close();time.sleep(.05);os.kill(pid,signal.SIGCONT)
        self.assertEqual(h.read(b)[0],200);self.assertEqual(h.service.worker.process.pid,pid)
        os.kill(pid,signal.SIGSTOP);result={}
        thread=threading.Thread(target=lambda:result.setdefault('a',h.read(a)));thread.start()
        deadline=time.monotonic()+1
        while h.service.active is None and time.monotonic()<deadline:time.sleep(.01)
        closed=h.request('/api/explorer/v1/session-close',{'schema_version':1,'code_epoch':h.package.code_epoch},
            headers={'Cookie':a['cookie'],'X-Explorer-CSRF':a['value']['csrf']})
        self.assertEqual(closed[0],200);os.kill(pid,signal.SIGCONT);thread.join(5)
        self.assertEqual(self.code(result['a']),'session_invalid');self.assertEqual(h.read(b)[0],200)
        self.assertEqual(h.service.worker.process.pid,pid)
        OBSERVATIONS.append({'case':'two_session_cancellation_close','same_worker_retained':True})
    def test_two_root_cookie_csrf_bootstrap_cursor_isolation(self):
        h=self.h
        def different_meaning(other):
            cfg=json.loads((other.root/'ontology.yaml').read_text())
            for relative in cfg['project_files']:
                p=other.root/relative;doc=json.loads(p.read_text())
                for row in doc['@graph']:
                    if row['@id']==other.ids['focus']:row['definition']='Second root has distinct recorded meaning under the same identity and label.'
                p.write_text(json.dumps(doc))
        other=Harness(identity='explorer-fixture',mutator=different_meaning).start()
        try:
            a=h.connect();b=other.connect()
            self.assertEqual(self.code(other.read(a)),'session_invalid')
            self.assertEqual(self.code(other.read(b,headers={'X-Explorer-CSRF':a['value']['csrf']})),'csrf_forbidden')
            foreign={'schema_version':1,'bootstrap':h.bootstrap(),'client_build_id':other.assets.manifest['build_id'],
                     'schema_sha256':b['value']['schema_sha256']}
            self.assertEqual(self.code(other.request('/api/explorer/v1/session',foreign)),'session_invalid')
            context=json.loads(h.read(a)[2]);second=json.loads(other.read(b)[2]);self.assertNotEqual(context['project']['root_scope_id'],second['project']['root_scope_id'])
            self.assertEqual(context['project']['id'],second['project']['id'])
            first_definition=json.loads(h.read(a,'entry',dict(id=h.ids['focus'],section='definition',cursor=None),context['snapshot'])[2])['data']['chunks']
            second_definition=json.loads(other.read(b,'entry',dict(id=other.ids['focus'],section='definition',cursor=None),second['snapshot'])[2])['data']['chunks']
            self.assertNotEqual(first_definition,second_definition)
            params=dict(query='',category=None,lifecycles=['draft','approved','deprecated'],fact_kinds=['asserted'],sort='label',limit=1,cursor=None)
            page=json.loads(h.read(a,'search',params,context['snapshot'])[2]);self.assertIsNotNone(page['page']['next_cursor'])
            self.assertEqual(self.code(other.read(b,'search',{**params,'cursor':page['page']['next_cursor']},second['snapshot'])),'cursor_invalid')
        finally:other.close()
    def test_worker_drift_survives_discarded_client(self):
        h=self.h;s=h.connect();service=h.service
        # The response is a real exact Reader error shape. This isolates the
        # discard ordering without requiring a nondeterministic restore race.
        c=h.module.Connection(socket.socket());c.closed=True;c.authenticated=True;c.operation='context';c.request_id='discard'
        c.job={'scope':s['value']['session_scope'],'deadline':time.monotonic()+2};c.stage='running'
        _,raw=service.error('package_changed',c)
        service.active=c
        service.finish_job({'kind':'result','epoch':h.package.code_epoch,'loaded':dict(h.package.loaded_digests),
                            'body':json.loads(raw),'policy':service.policy})
        c.sock.close();self.assertTrue(service.changed);self.assertFalse(service.sessions);self.assertIsNone(service.worker.process)
