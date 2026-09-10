"""Actual guarded configuration through its existing separately scoped owner."""
from datetime import datetime, timedelta, timezone
import importlib
import json
from pathlib import Path
import tempfile
import unittest

from guard_support import standards_available, DEPOT, project, preserve_imports


@unittest.skipUnless(standards_available(), "Actual selected standards backend is unavailable")
class GuardedProfileConfiguration(unittest.TestCase):
    def setUp(self):
        preserve_imports(self)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = project(Path(self.temp.name))
        self.owner = importlib.import_module("ontology_profiles")
        self.core = importlib.import_module("ontology_core")

    def authority(self, profile, enabled, expected):
        now = datetime.now(timezone.utc)
        return {"schema_version": 1, "operation_id": "ONTPROFILE-guard-fixture", "operation": "configure-profile",
                "project_id": "example", "profile": profile, "enabled": enabled, "expected_config_sha256": expected,
                "actor_id": "/root", "actor_kind": "director", "observed_at": now.isoformat(),
                "expires_at": (now + timedelta(minutes=4)).isoformat(),
                "native_receipt": {"tool": "collaboration.list_agents", "result": {"agents": [{"agent_name": "/root", "agent_status": "running"}]}}}

    def test_actual_guarded_profile_enable_replay_and_separate_scope(self):
        path = self.root / "ontology-advanced.yaml"
        before = json.loads(path.read_text())
        checksum = self.core.sha256(path)
        authority = self.authority("semantic", True, checksum)
        denied = dict(authority, actor_id="/root/child")
        with self.assertRaises(self.core.OntologyError):
            self.owner.configure_profile(self.root, "semantic", True, checksum, denied)
        self.assertEqual(self.core.sha256(path), checksum)
        result = self.owner.configure_profile(self.root, "semantic", True, checksum, authority)
        self.assertEqual(result["ontology_guard"]["semantic_status"], "conformant")
        self.assertEqual(result["status"], "configured")
        self.assertFalse(result["provisioned"])
        self.assertFalse(result["current_readiness"]["static_ready"])
        self.assertIn("semantic", {row["component"] for row in result["current_readiness"]["maintenance_pending"]})
        after = json.loads(path.read_text())
        self.assertTrue(after["profiles"]["semantic"]["enabled"])
        self.assertEqual(before["profiles"]["guards"], after["profiles"]["guards"])
        self.assertEqual(before.get("publication"), after.get("publication"))
        self.assertTrue(self.owner.configure_profile(self.root, "semantic", True, checksum, authority)["replayed"])
        self.assertFalse((self.root / ".venv-ontology-semantic").exists())

    def test_guard_dependency_and_missing_backend_block_without_disabling_guards(self):
        path = self.root / "ontology-advanced.yaml"
        checksum = self.core.sha256(path)
        with self.assertRaises(self.core.OntologyError) as rejected:
            self.owner.configure_profile(self.root, "standards", False, checksum, self.authority("standards", False, checksum))
        self.assertEqual(rejected.exception.code, "guard_dependency")
        env = self.root / ".venv-ontology-standards"
        env.rename(self.root / ".backend-unavailable")
        with self.assertRaises(self.core.OntologyError):
            self.owner.configure_profile(self.root, "workbench", True, checksum, self.authority("workbench", True, checksum))
        self.assertEqual(self.core.sha256(path), checksum)
        self.assertTrue(json.loads(path.read_text())["profiles"]["guards"]["enabled"])


if __name__ == "__main__":
    unittest.main()
