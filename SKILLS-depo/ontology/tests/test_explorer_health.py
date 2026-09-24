"""Narrow health and explicit CLI behavior; no optional profile sweep."""
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import unittest
from test_explorer_service import Harness,OBSERVATIONS


class HealthTests(unittest.TestCase):
    def test_static_and_endpoint_facts_preserve_files(self):
        h=Harness().start()
        try:
            health=h.package.modules['ontology_explorer_health'];before=list(h.service.sessions)
            result=health.inspect(h.package,h.assets,h.root,h.service.origin)
            self.assertTrue(result['installed']);self.assertTrue(result['configured']);self.assertTrue(result['running']);self.assertTrue(result['readable'])
            self.assertFalse(result['wrong_project']);self.assertTrue(before==list(h.service.sessions))
            self.assertNotIn('project',json.loads(h.request('/health')[2]))
            for url in ('https://127.0.0.1:123','http://localhost:123','http://127.0.0.1:123/#bootstrap=redacted','http://127.0.0.1:123/?x=y','http://127.0.0.1:65536'):
                with self.assertRaises(Exception):health.inspect(h.package,h.assets,h.root,url)
            OBSERVATIONS.append({'case':'health','facts':result})
        finally:h.close()
    def test_cli_launch_and_no_optional_imports(self):
        h=Harness();process=None
        try:
            command=[sys.executable,'-B',str(h.scripts/'ontology.py'),'--project-root',str(h.root),'explore']
            process=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=h.module.sanitized_environment(),cwd='/',text=True)
            import select
            self.assertTrue(select.select([process.stdout],[],[],8)[0]);line=process.stdout.readline();result=json.loads(line)
            self.assertEqual(result['status'],'running');self.assertNotIn('bootstrap=',line);self.assertNotIn('csrf',line)
            origin=result['origin'];self.assertTrue(origin.startswith('http://127.0.0.1:'))
            health=subprocess.run([sys.executable,'-B',str(h.scripts/'ontology.py'),'--project-root',str(h.root),'explorer-health','--url',origin],capture_output=True,text=True,timeout=10)
            self.assertEqual(health.returncode,0,health.stdout);self.assertTrue(json.loads(health.stdout)['readable'])
            process.terminate();process.wait(8);self.assertEqual(process.returncode,0)
            self.assertFalse(list((h.root/'.sys4ai/ontology/explorer').glob('*.json')))
            forbidden=('ontology_workbench','ontology_advanced_cli','ontology_publication','ontology_memory','ontology_profiles','ontology_backend')
            self.assertTrue(all(n not in h.package.loaded_digests for n in forbidden))
            OBSERVATIONS.append({'case':'cli','explicit_service_launch':True,'health_read_only':True,'child_reaped':True})
        finally:
            if process and process.poll() is None:
                process.terminate()
                try:process.wait(5)
                except subprocess.TimeoutExpired:process.kill();process.wait(3)
            if process:process.stdout.close();process.stderr.close()
            h.close()
    def test_wrong_selected_configuration_and_neutral(self):
        for project_id,expected in ((None,'configuration_needed'),('other-project','identity_mismatch')):
            h=Harness()
            try:
                p=h.root/'ontology-explorer.yaml';d=json.loads(p.read_text());d['project_id']=project_id;p.write_text(json.dumps(d))
                result=h.package.modules['ontology_explorer_health'].inspect(h.package,h.assets,h.root)
                self.assertFalse(result['configured']);self.assertFalse(result['readable']);self.assertEqual(result['local']['error'],expected)
                if project_id:self.assertTrue(result['wrong_project'])
            finally:h.close()
    def test_slow_health_peer_has_absolute_header_body_deadline(self):
        import socket,threading
        h=Harness()
        try:
            health=h.package.modules['ontology_explorer_health']
            for mode in ('trickle','oversized','transfer','redirect'):
                listener=socket.socket();listener.bind(('127.0.0.1',0));listener.listen(1);port=listener.getsockname()[1]
                def peer():
                    conn,_=listener.accept();conn.settimeout(3)
                    try:
                        conn.recv(8192)
                        if mode=='trickle':
                            for _ in range(30):conn.sendall(b'H');time.sleep(.12)
                        elif mode=='oversized':conn.sendall(b'HTTP/1.1 200 OK\r\nX: '+b'x'*9000+b'\r\n\r\n')
                        elif mode=='transfer':conn.sendall(b'HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\nContent-Length: 2\r\n\r\n{}')
                        else:conn.sendall(b'HTTP/1.1 302 Found\r\nLocation: https://outside.invalid\r\nContent-Length: 2\r\n\r\n{}')
                    except OSError:pass
                    finally:conn.close();listener.close()
                thread=threading.Thread(target=peer);thread.start();start=time.monotonic()
                with self.assertRaises(Exception):health.probe(port)
                elapsed=time.monotonic()-start;self.assertLess(elapsed,2.5);thread.join(4)
                OBSERVATIONS.append({'case':'bounded_health_probe','peer_mode':mode,'elapsed_seconds':elapsed,'rejected':True})
        finally:h.close()
    def test_missing_bundle_health_facts_and_legacy_help(self):
        h=Harness()
        try:
            legacy=subprocess.run([sys.executable,'-B',str(h.scripts/'ontology.py'),'--project-root',str(h.root),'workbench','--help'],capture_output=True,text=True,timeout=5)
            self.assertEqual(legacy.returncode,0);self.assertIn('--authority-file',legacy.stdout);self.assertIn('--session-file',legacy.stdout)
            (h.explorer/'assets/manifest.json').unlink()
            probe=subprocess.run([sys.executable,'-B',str(h.scripts/'ontology.py'),'--project-root',str(h.root),'explorer-health'],capture_output=True,text=True,timeout=5)
            self.assertEqual(probe.returncode,1);result=json.loads(probe.stdout)
            self.assertFalse(result['installed']);self.assertFalse(result['readable']);self.assertIsNone(result['running'])
            self.assertTrue(result['unavailable']);self.assertFalse((h.root/'.sys4ai/ontology/explorer').exists())
        finally:h.close()


class InstalledLayoutTests(unittest.TestCase):
    def test_installed_package_serves_and_cli_health_reads_real_root_contracts(self):
        import shutil
        h=Harness()
        try:
            installed=h.root/'.agents/skills/ontology'
            shutil.copytree(h.scripts.parent,installed)
            contract=h.root/'reference-assets/ONTOLOGY-depo/schema/explorer-v1.json';contract.parent.mkdir(parents=True)
            shutil.copyfile(h.schema,contract)
            package,assets=h.launcher.prepare_package(installed/'scripts')
            h.package.close();h.package=package;h.assets=assets;h.module=package.modules['ontology_explorer']
            self.assertEqual(package.package_files['schema'],contract)
            self.assertTrue(Path(h.module.__file__).is_relative_to(installed))
            h.start();session=h.connect();response=h.read(session)
            self.assertEqual(response[0],200);self.assertEqual(json.loads(response[2])['data']['project']['id'],'explorer-fixture')
            health=subprocess.run([sys.executable,'-B',str(installed/'scripts/ontology.py'),'--project-root',str(h.root),'explorer-health','--url',h.service.origin],capture_output=True,text=True,timeout=10)
            self.assertEqual(health.returncode,0,health.stdout);facts=json.loads(health.stdout)
            self.assertTrue(facts['installed'] and facts['configured'] and facts['running'] and facts['readable'])
            self.assertFalse(facts['wrong_project'])
            OBSERVATIONS.append({'case':'installed_layout','actual_service_context':True,'actual_installed_cli_health':True,
                'schema_relative_to_root':'reference-assets/ONTOLOGY-depo/schema/explorer-v1.json'})
        finally:h.close()


class LauncherRaceTests(unittest.TestCase):
    def test_public_cli_captures_before_selected_service_execution(self):
        import ast,shutil,tempfile
        from test_explorer_service import compile_file
        h=Harness();original=subprocess.Popen
        try:
            cli=compile_file('_tested_reader_cli',h.scripts/'ontology.py')
            self.assertEqual(cli._READER_BOOTSTRAP,h.module.BOOTSTRAP)
            marker=h.base/'cli-unverified-execution';source=h.scripts/'ontology_explorer.py'
            with tempfile.TemporaryFile() as output:
                def swapped(*args,**kwargs):
                    command=args[0];self.assertIn('-c',command)
                    raw=source.read_text();at=raw.find('\n',raw.find('from __future__ import annotations'))+1
                    source.write_text(raw[:at]+'\nopen('+repr(str(marker))+',"w").write("executed")\n'+raw[at:])
                    kwargs['stdout']=output;kwargs['stderr']=output
                    return original(*args,**kwargs)
                subprocess.Popen=swapped
                result=cli._reader_launch(['--project-root',str(h.root),'explorer-health'],'explorer-health')
                output.seek(0);response=json.loads(output.read())
            self.assertEqual(result,2);self.assertEqual(response['error'],'package_changed');self.assertFalse(marker.exists())
            OBSERVATIONS.append({'case':'public_cli_verify_load_race','fixed_capture_bootstrap':True,'unverified_service_executed':False})
        finally:subprocess.Popen=original;h.close()
    def test_documented_reader_cli_rejects_ambient_stdlib_shadows(self):
        import shutil,tempfile
        from pathlib import Path
        h=Harness()
        try:
            for name in ('argparse','json','pathlib','hashlib'):
                folder=h.base/('shadow-'+name);folder.mkdir();shutil.copyfile(h.scripts/'ontology.py',folder/'ontology.py')
                marker=folder/'unmanifested-executed'
                (folder/(name+'.py')).write_text('open('+repr(str(marker))+',"w").write("executed")\nraise RuntimeError("shadow probe")\n')
                env={**os.environ,'PYTHONPATH':str(folder)}
                done=subprocess.run([sys.executable,'-B',str(folder/'ontology.py'),'--project-root',str(folder),'explore','--help'],env=env,capture_output=True,text=True,timeout=8)
                self.assertFalse(marker.exists(),name)
                self.assertEqual(done.returncode,2);self.assertEqual(json.loads(done.stdout)['error'],'package_incomplete')
            OBSERVATIONS.append({'case':'ordinary_reader_cli_shadow_isolation','modules':['argparse','json','pathlib','hashlib'],'unmanifested_execution':False})
        finally:h.close()
