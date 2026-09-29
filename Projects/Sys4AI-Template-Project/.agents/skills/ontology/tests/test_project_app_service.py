"""Focused novel app transport/lifecycle boundaries using the existing fixture."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import threading
import time
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_explorer_service import Harness, ROOT, SCRIPTS, inventory


def app_fixture(h, *, ontology=False):
    for p in SCRIPTS.glob('project_app*.py'):shutil.copyfile(p,h.scripts/p.name)
    shutil.copytree(SCRIPTS.parent/'assets/project-app',h.scripts.parent/'assets/project-app')
    shutil.copyfile(ROOT/'ONTOLOGY-depo/schema/project-app-v1.json',h.schema.with_name('project-app-v1.json'))
    identity=json.loads((h.root/'ontology.yaml').read_text())['project']
    (h.root/'project.json').write_text(json.dumps({'project_id':identity['id'],'project_name':identity['name'],'purpose':identity['purpose']}))
    shutil.copyfile(SCRIPTS.parent/'assets/project-app/project-app.json',h.root/'project-app.json')
    (h.root/'README.md').write_text('Alternate project overview.\n')
    config=json.loads((h.root/'project-app.json').read_text())
    raw=(h.root/'README.md').read_bytes()
    text='This is the alternate project.'
    config['project_id']='explorer-fixture';config['documents']=[{'title':'Overview','path':'README.md'}]
    config['home']['purpose']={'text':text,'sources':[{'path':'README.md','sha256':hashlib.sha256(raw).hexdigest()}],
        'reviewed_sha256':hashlib.sha256(text.encode()).hexdigest(),'reviewed_at':'2026-09-29'}
    (h.root/'project-app.json').write_text(json.dumps(config))
    if not ontology:(h.root/'ontology.yaml').write_text('{ invalid optional ontology')


class ProjectAppServiceTests(unittest.TestCase):
    def setUp(self):self.h=None
    def tearDown(self):
        if self.h:self.h.close()
    def fixture(self, *, ontology=False, start=True):
        self.h=Harness(mutator=lambda h:app_fixture(h,ontology=ontology))
        h=self.h
        if start:
            h.service=h.module.Service(h.package,h.assets,h.root,mode='app')
            h.thread=threading.Thread(target=h.service.serve);h.thread.start()
        return h
    def read(self,h,session,op,params=None,headers=None):
        auth={'Cookie':session['cookie'],'X-Explorer-CSRF':session['value']['csrf']};auth.update(headers or {})
        return h.request('/api/project/v1/read',{'operation':op,'params':params or {}},headers=auth)
    def test_independent_home_and_new_routes_retain_controls(self):
        h=self.fixture();session=h.connect()
        self.assertIn('Path=/api/',session['headers']['Set-Cookie'])
        self.assertEqual(h.request('/?app=1')[0],200)
        self.assertEqual(h.request('/?root=other')[0],400)
        status,headers,raw=self.read(h,session,'home');body=json.loads(raw)
        self.assertEqual(status,200);self.assertEqual(body['project_id'],'explorer-fixture')
        self.assertEqual(body['content']['purpose']['text'],'This is the alternate project.')
        self.assertEqual(h.request('/api/project/v1/read',{'operation':'home','params':{}})[0],401)
        self.assertEqual(self.read(h,session,'home',headers={'X-Explorer-CSRF':'invalid'})[0],403)
        self.assertEqual(self.read(h,session,'home',headers={'Origin':'https://outside.invalid'})[0],403)
        self.assertEqual(self.read(h,session,'home',headers={'Host':'localhost:'+str(h.service.port)})[0],403)
        self.assertEqual(h.request('/api/project/v1/execute',{},headers={'Cookie':session['cookie'],'X-Explorer-CSRF':session['value']['csrf']})[0],404)
        # Optional knowledge failure stays contained; a fresh Home still works.
        self.assertNotEqual(h.read(session)[0],200)
        self.assertEqual(self.read(h,session,'home')[0],200)
        pending={}
        h.service.worker.process.send_signal(signal.SIGSTOP)
        request_thread=threading.Thread(target=lambda:pending.setdefault('result',self.read(h,session,'home')))
        request_thread.start()
        deadline=time.monotonic()+2
        while h.service.active is None and time.monotonic()<deadline:time.sleep(.01)
        self.assertIsNotNone(h.service.active)
        closed=h.request('/api/explorer/v1/session-close',{'schema_version':1,'code_epoch':h.package.code_epoch},
            headers={'Cookie':session['cookie'],'X-Explorer-CSRF':session['value']['csrf']})
        self.assertEqual(closed[0],200)
        h.service.worker.process.send_signal(signal.SIGCONT);request_thread.join(6)
        self.assertEqual(pending['result'][0],401)
        self.assertEqual(self.read(h,session,'home')[0],401)
        renewed=h.connect()
        self.assertEqual(h.request('/api/project/v1/stop',{},headers={'Cookie':renewed['cookie'],'X-Explorer-CSRF':'bad'})[0],403)
        result=h.request('/api/project/v1/stop',{},headers={'Cookie':renewed['cookie'],'X-Explorer-CSRF':renewed['value']['csrf']})
        self.assertEqual(result[0],200);self.assertEqual(json.loads(result[2])['status'],'stopping')
        h.thread.join(5);self.assertFalse(h.thread.is_alive());self.assertFalse(h.service.sessions)
        h.service.close();self.assertEqual(h.before,inventory(h.root))
    def test_authenticated_reopen_rejects_wrong_identity_and_stops_changed_package(self):
        h=self.fixture();life=h.package.modules['project_app'];receipt=life.read_receipt(h.service.identity_file)
        reopened=life.exchange(receipt,h.package,h.root,'explorer-fixture')
        self.assertTrue(reopened.startswith(h.service.origin+'/?app=1#bootstrap='))
        for replacement in ({'project_id':'other-project'},{'service_instance':'0'*32},{'credential':h.module.token()},{'code_epoch':'0'*64}):
            with self.assertRaises(ValueError):life.exchange({**receipt,**replacement},h.package,h.root,'explorer-fixture')
        h.service.bootstraps.clear()
        # Package drift revokes sessions/reads, but the private owned stop remains
        # available to a freshly verified replacement package; no PID is used.
        old=(h.scripts/'project_app_core.py').read_bytes()
        (h.scripts/'project_app_core.py').write_bytes(old+b'\n# replacement\n')
        h.request('/')
        new_package,new_assets=h.launcher.prepare_package(h.scripts)
        try:
            new_life=new_package.modules['project_app']
            with self.assertRaises(ValueError):new_life.exchange(receipt,new_package,h.root,'explorer-fixture')
            result=new_life.exchange(receipt,new_package,h.root,'explorer-fixture',action='stop')
            self.assertEqual(result['status'],'stopping');h.thread.join(5);self.assertFalse(h.thread.is_alive())
        finally:new_package.close()
    def test_new_package_retains_standalone_and_cli_owned_launch_stop(self):
        h=self.fixture(ontology=True,start=False)
        h.service=h.module.Service(h.package,h.assets,h.root)
        h.thread=threading.Thread(target=h.service.serve);h.thread.start()
        session=h.connect();self.assertEqual(h.read(session)[0],200)
        self.assertEqual(h.request('/api/project/v1/read',{'operation':'home','params':{}})[0],404)
        h.service.stopping=True;h.thread.join(5);h.service.close();h.service=None
        # The same reviewed package also serves embedded Knowledge and unified
        # lexical results through its single lazy reader in app mode.
        h.service=h.module.Service(h.package,h.assets,h.root,mode='app')
        h.thread=threading.Thread(target=h.service.serve);h.thread.start()
        session=h.connect();self.assertEqual(h.read(session)[0],200)
        result=self.read(h,session,'search',{'query':'Fixture'})
        self.assertEqual(result[0],200)
        self.assertTrue(any(row.get('owner')=='knowledge' for row in json.loads(result[2])['items']))
        h.service.stopping=True;h.thread.join(5);h.service.close();h.service=None
        command=[sys.executable,'-I','-S','-B',str(h.scripts/'project_app.py'),'--project-root',str(h.root)]
        env={'PATH':'/usr/bin:/bin','LANG':'en_US.UTF-8'}
        try:
            first=subprocess.run(command,capture_output=True,text=True,timeout=15,env=env)
            self.assertEqual(first.returncode,0,first.stdout+first.stderr)
            value=json.loads(first.stdout);self.assertEqual(value['status'],'ready')
            second=subprocess.run(command,capture_output=True,text=True,timeout=10,env=env)
            self.assertEqual(second.returncode,0,second.stdout+second.stderr);self.assertEqual(json.loads(second.stdout)['status'],'reopened')
            self.assertNotIn('bootstrap',first.stdout+second.stdout)
        finally:
            stopped=subprocess.run(command+['--stop'],capture_output=True,text=True,timeout=10,env=env)
            self.assertEqual(stopped.returncode,0,stopped.stdout+stopped.stderr)
            self.assertEqual(json.loads(stopped.stdout)['status'],'stopping')


if __name__=='__main__':unittest.main()
