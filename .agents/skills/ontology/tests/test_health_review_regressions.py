"""Independent review regressions using authored fixtures and real observations."""
import hashlib
import json
import os
from pathlib import Path
import socketserver
import subprocess
import sys
import tempfile
import threading
import time
import unittest

from support import PACKAGE, make_project, standards_available
from ontology import health
from ontology_build import compile_project
from ontology_core import OntologyError
from ontology_health import advanced_health
from ontology_workbench import assess_service


def snapshot(root):
    return {str(p.relative_to(root)): (hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_mtime_ns)
            for p in root.rglob('*') if p.is_file()}


class HealthReviewRegressions(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='ontology-health-review-')
        self.addCleanup(self.temporary.cleanup)
        self.root = make_project(Path(self.temporary.name) / 'project')

    def cli(self, *arguments):
        return subprocess.run([sys.executable, str(PACKAGE / 'scripts/ontology.py'),
                               '--project-root', str(self.root), *arguments],
                              capture_output=True, text=True, timeout=30,
                              env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})

    def test_manifest_cannot_hide_missing_required_compile_outputs(self):
        for omitted in ('all', 'index'):
            with self.subTest(omitted=omitted):
                self.root = make_project(Path(self.temporary.name) / omitted)
                compile_project(self.root)
                self.assertTrue(health(self.root)['ready'])
                path = self.root / '.sys4ai/ontology/manifests/compile.json'
                manifest = json.loads(path.read_text())
                names = list(manifest['outputs']) if omitted == 'all' else ['.sys4ai/ontology/compiled/index.json']
                for name in names:
                    manifest['outputs'].pop(name)
                    (self.root / name).unlink()
                path.write_text(json.dumps(manifest))
                before = snapshot(self.root)
                result = health(self.root)
                self.assertFalse(result['ready'])
                self.assertEqual(result['generated']['compile']['status'], 'invalid')
                self.assertEqual(self.cli('health').returncode, 1)
                self.assertEqual(before, snapshot(self.root))

    @unittest.skipUnless(standards_available(), 'Selected real backend is unavailable')
    def test_required_inference_rejects_complete_inconsistent_result(self):
        from advanced_support import make_advanced, extension, statement, project_id
        from ontology_advanced import RDF, OWL
        self.root = make_advanced(Path(self.temporary.name) / 'advanced')
        selection = {'scope': 'canonical', 'level': 'operational', 'required': ['inference']}
        self.assertTrue(advanced_health(self.root, **selection)['ready'])
        a, A, B = map(project_id, ('a', 'A', 'B'))
        extension(self.root, axioms=[statement(self.root, 'a1', a, RDF + 'type', A),
            statement(self.root, 'a2', a, RDF + 'type', B),
            statement(self.root, 'd1', A, OWL + 'disjointWith', B)])
        before = snapshot(self.root)
        result = advanced_health(self.root, **selection)
        component = result['assessment']['components']['inference']
        observed = component['observed_operation']
        self.assertTrue(observed['complete'])
        self.assertEqual(observed['status'], 'inconsistent')
        self.assertFalse(observed['trusted'])
        self.assertFalse(component['ready'])
        self.assertFalse(result['ready'])
        self.assertEqual(result['aggregate'], 'degraded')
        self.assertEqual(self.cli('advanced-health', '--scope', 'canonical', '--level', 'operational',
                                  '--require', 'inference').returncode, 1)
        self.assertEqual(before, snapshot(self.root))

    def test_service_deadline_covers_trickled_headers_and_body(self):
        for slow_part in ('headers', 'body'):
            with self.subTest(slow_part=slow_part):
                finished = threading.Event()
                class Handler(socketserver.BaseRequestHandler):
                    def handle(self):
                        try:
                            self.request.recv(4096)
                            headers = b'HTTP/1.1 200 OK\r\nContent-Length: 52\r\nConnection: close\r\n\r\n'
                            body = b'{' + b' ' * 50 + b'}'
                            if slow_part == 'body':
                                self.request.sendall(headers)
                            for value in headers if slow_part == 'headers' else body:
                                self.request.sendall(bytes([value]))
                                time.sleep(.04)
                        except (BrokenPipeError, ConnectionResetError):
                            pass
                        finally:
                            finished.set()
                server = socketserver.ThreadingTCPServer(('127.0.0.1', 0), Handler)
                thread = threading.Thread(target=server.serve_forever)
                thread.start()
                before = snapshot(self.root)
                try:
                    started = time.monotonic()
                    result = assess_service(self.root, f'http://127.0.0.1:{server.server_address[1]}', timeout=.15)
                    self.assertLess(time.monotonic() - started, .8)
                    self.assertEqual(result['service_state'], 'timeout')
                    self.assertEqual(result['diagnostics'][0]['code'], 'service_timeout')
                    self.assertFalse(result['running'])
                    self.assertFalse(result['mutated'])
                    self.assertTrue(finished.wait(1))
                    self.assertEqual(before, snapshot(self.root))
                finally:
                    server.shutdown(); thread.join(); server.server_close()

    def test_malformed_endpoint_has_structured_invalid_request(self):
        before = snapshot(self.root)
        with self.assertRaises(OntologyError) as error:
            assess_service(self.root, 'http://[')
        self.assertEqual(error.exception.code, 'invalid_service')
        result = self.cli('advanced-health', '--workbench-url', 'http://[')
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)['status'], 'invalid')
        self.assertEqual(result.stderr, '')
        self.assertEqual(before, snapshot(self.root))


if __name__ == '__main__':
    unittest.main()
