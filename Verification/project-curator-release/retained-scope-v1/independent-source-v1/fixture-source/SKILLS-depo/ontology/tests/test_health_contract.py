"""Observable health/exit and no-write regressions for the repair release."""
from pathlib import Path
import json
import os
import subprocess
import sys
import tempfile
import unittest

from support import make_project, write_json, read_json, PACKAGE, record, add_records
from ontology import health
from ontology_build import compile_project
from ontology_health import advanced_health
from ontology_workbench import Workbench, assess_service
from workbench_fixture import make_workbench_project


def snapshot(root):
    return {str(p.relative_to(root)): (p.read_bytes(), p.stat().st_mtime_ns)
            for p in root.rglob("*") if p.is_file()}


class HealthContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = make_project(Path(self.temp.name) / "deep fixture" / "project")

    def cli(self, *args, text=False):
        return subprocess.run([sys.executable, str(PACKAGE / "scripts/ontology.py"),
                               "--project-root", str(self.root), "--format", "text" if text else "json", *args],
                              capture_output=True, text=True, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}, timeout=30)

    def test_neutral_and_explicit_required_missing_cli_preserve_bytes_and_times(self):
        before = snapshot(self.root)
        result = health(self.root)
        self.assertTrue(result["ready"])
        self.assertEqual(result["health_schema_version"], 2)
        self.assertEqual(result["assessment"]["level"], "static")
        required = self.cli("health", "--require", "compile")
        self.assertEqual(required.returncode, 1, required.stderr)
        data = json.loads(required.stdout)
        self.assertEqual(data["aggregate"], "degraded")
        self.assertEqual(data["generated"]["compile"]["status"], "missing")
        rendered = self.cli("health", "--require", "compile", text=True)
        self.assertEqual(rendered.returncode, 1)
        self.assertIn("compile: not ready", rendered.stdout)
        self.assertEqual(before, snapshot(self.root))

    def test_selected_projection_failures_and_canonical_scope(self):
        compiled = compile_project(self.root)
        self.assertTrue(health(self.root)["ready"])
        output = self.root / next(iter(compiled["outputs"]))
        output.unlink()
        self.assertFalse(health(self.root)["ready"])
        self.assertTrue(health(self.root, scope="canonical")["ready"])
        self.assertEqual(self.cli("health").returncode, 1)
        manifest = self.root / ".sys4ai/ontology/manifests/compile.json"
        manifest.write_text("{}")
        before = snapshot(self.root)
        observed = health(self.root)
        self.assertEqual(observed["generated"]["compile"]["status"], "invalid")
        self.assertFalse(observed["ready"])
        self.assertEqual(before, snapshot(self.root))

    def test_stale_authored_source_and_absent_invalid_configuration(self):
        add_records(self.root, [record("health-artifact")])
        (self.root / "SPECS.md").write_text("Changed source")
        self.assertFalse(health(self.root, scope="canonical")["canonical_ready"])
        self.assertEqual(self.cli("health", "--scope", "canonical").returncode, 1)
        (self.root / "ontology.yaml").write_text("{}")
        self.assertEqual(self.cli("health").returncode, 2)
        (self.root / "ontology.yaml").unlink()
        self.assertEqual(json.loads(self.cli("health").stdout)["status"], "absent")

    def test_selected_backend_and_guard_failure_are_not_masked(self):
        cfg = read_json(self.root / "ontology-advanced.yaml")
        cfg["profiles"]["standards"]["enabled"] = True
        write_json(self.root / "ontology-advanced.yaml", cfg)
        before = snapshot(self.root)
        result = advanced_health(self.root)
        self.assertFalse(result["ready"])
        self.assertEqual(result["profiles"]["standards"]["status"], "backend_unavailable")
        self.assertEqual(self.cli("advanced-health").returncode, 1)
        self.assertTrue(advanced_health(self.root, scope="canonical")["ready"])
        cfg["profiles"]["guards"] = {"enabled": True, **{key: {"path": "control_records/missing-" + key + ".json", "sha256": "0"*64}
                                                               for key in ("contract", "adapters", "bootstrap")}}
        write_json(self.root / "ontology-advanced.yaml", cfg)
        guarded = advanced_health(self.root)
        self.assertFalse(guarded["ready"])
        self.assertEqual(guarded["profiles"]["guards"]["status"], "unavailable")
        self.assertEqual(guarded["profiles"]["guards"]["diagnostics"][0]["code"], "guard_unavailable")
        self.assertEqual(set(before), set(snapshot(self.root)))

    def test_workbench_is_on_demand_and_probe_matches_exact_project(self):
        service_root = make_workbench_project(Path(self.temp.name) / "service project")
        self.assertTrue(advanced_health(service_root)["ready"])
        self.assertIsNone(advanced_health(service_root)["profiles"]["workbench"]["running"])
        before = snapshot(service_root)
        service = Workbench(service_root).start()
        try:
            matched = assess_service(service_root, service.origin)
            self.assertTrue(matched["running"])
            other_root = make_workbench_project(Path(self.temp.name) / "other project")
            wrong = assess_service(other_root, service.origin)
            self.assertFalse(wrong["running"])
            self.assertEqual(wrong["service_state"], "wrong_project")
            self.assertEqual(snapshot(service_root), before)
        finally:
            service.close()
        stopped = assess_service(service_root, service.origin)
        self.assertFalse(stopped["running"])
        self.assertEqual(stopped["service_state"], "stopped")

    def test_probe_rejects_external_credentials_and_redirect_surfaces(self):
        from ontology_core import OntologyError
        for origin in ("https://example.com", "http://localhost:80", "http://127.0.0.1:80/#secret",
                       "http://user:secret@127.0.0.1:80", "http://127.0.0.1:80/private", "http://127.0.0.1:80?url=x"):
            with self.subTest(origin=origin), self.assertRaises(OntologyError):
                assess_service(self.root, origin)


if __name__ == "__main__":
    unittest.main()
