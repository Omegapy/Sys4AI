"""Advanced frozen input boundaries using the real Task helper and labeled fixture owners."""
import copy
from pathlib import Path
import unittest
from unittest.mock import patch

from support import core_id, write_json
import test_query_packets as packet_fixtures
from ontology_core import OntologyError, read_json
from ontology_packet import assess_change, build_packet, freeze_packet, load_packet, search_packet


class AdvancedPacketTests(unittest.TestCase):
    def setUp(self):
        self.fixture = packet_fixtures.PacketTests("test_wrong_owner_scope_empty_size_and_immutability")
        self.fixture.setUp()
        self.root = self.fixture.root
        write_json(self.root / "ontology-advanced.yaml", {"schema_version": 1, "profiles": {}, "extensions": [], "limits": {}})

    def tearDown(self):
        self.fixture.tearDown()

    def build(self, **kwargs):
        return self.fixture.build(advanced=True, **kwargs)

    def test_explicit_version_preserves_existing_artifact_interface(self):
        packet = self.build()
        self.assertEqual(packet["schema_version"], 2)
        self.assertEqual(packet["advanced"]["graphs"], ["asserted"])
        ref = freeze_packet(self.root, packet, "packets/ontology-v2.json", actor=self.fixture.driver.actor)
        self.assertEqual(packet, load_packet(self.root, ref))
        with patch("ontology_semantic._embed", side_effect=AssertionError("Frozen query attempted a live model")):
            self.assertEqual(search_packet(self.root, ref, "Task")["results"][0]["@id"], core_id("Task"))
        bad = copy.deepcopy(packet); bad["schema_version"] = 3
        with self.assertRaises(OntologyError):
            freeze_packet(self.root, bad, "packets/future.json", actor=self.fixture.driver.actor)
        with self.assertRaises(OntologyError):
            self.build(max_bytes=1024)

    def test_changed_rules_and_profiles_require_manager_reassessment(self):
        packet = self.build()
        ref = freeze_packet(self.root, packet, "packets/ontology-v2.json", actor=self.fixture.driver.actor)
        raw = (self.root / ref["path"]).read_bytes()
        cfg = read_json(self.root / "ontology-advanced.yaml")
        cfg["limits"] = {"query_seconds": 5}
        write_json(self.root / "ontology-advanced.yaml", cfg)
        with self.assertRaises(OntologyError) as stale:
            load_packet(self.root, ref)
        self.assertEqual(stale.exception.code, "stale_packet")
        newer = self.build()
        assessment = assess_change(packet, newer, "The selected execution profile changed.")
        self.assertTrue(assessment["material"])
        self.assertTrue(assessment["advanced_context_changed"])
        self.assertFalse(assessment["task_events_replayed"])
        self.assertEqual(raw, (self.root / ref["path"]).read_bytes())

    def test_proposal_store_and_arbitrary_advanced_sources_are_excluded(self):
        p = "ONTOLOGY/proposals/source.md"
        (self.root / p).parent.mkdir(parents=True)
        (self.root / p).write_text("DRAFT-CONTENT")
        cfg = read_json(self.root / "ontology.yaml")
        cfg["source_allowlist"].append(p)
        write_json(self.root / "ontology.yaml", cfg)
        from ontology_core import sha256
        with self.assertRaises(OntologyError) as excluded:
            self.build(allowed_sources=[{"path": p, "sha256": sha256(self.root / p)}])
        self.assertEqual(excluded.exception.code, "excluded_source")
        packet = self.build()
        packet["advanced"]["references"].append({"path": "outside.txt", "sha256": "0"*64})
        with self.assertRaises(OntologyError):
            freeze_packet(self.root, packet, "packets/forged.json", actor=self.fixture.driver.actor)


if __name__ == "__main__":
    unittest.main()
