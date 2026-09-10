"""Memory starter identity, whole-package preservation and edition recovery."""

from copy import deepcopy
import json
from pathlib import Path
import shutil
import unittest
from unittest.mock import patch

import test_initializer as fixture


class MemoryEditionTests(unittest.TestCase):
    setUp = fixture.InitializerTests.setUp
    run_setup = fixture.InitializerTests.run_setup

    def test_new_projects_have_distinct_empty_memory_and_capture_on(self):
        root_note = self.root / "MEMORY/root-only.md"
        root_note.parent.mkdir()
        root_note.write_text("ROOT_LEARNED_MEMORY_MUST_NOT_BE_ADOPTED")
        template = self.root / self.helper.TEMPLATE
        source_config = json.loads((template / "memory.yaml").read_text())
        for name in ("orchard", "meadow", "a"):
            target = self.root / "Projects" / name.title()
            report = self.run_setup(destination=target, project_id=name, project_name=name.title())
            self.assertEqual("governance-starter-v9", report["setup_contract"])
            config = json.loads((target / "memory.yaml").read_text())
            self.assertEqual({"id": name, "name": name.title(), "root": "."}, config["project"])
            self.assertEqual("reference-assets/MEMORY-depo", config["contract_root"])
            self.assertEqual("MEMORY", config["canonical_root"])
            self.assertEqual({"name": "basic-memory", "enabled": False, "semantic_enabled": False}, config["backend"])
            self.assertEqual("/root", config["publication"]["director"]["actor_id"])
            self.assertTrue(config["integration"]["automatic_capture"])
            self.assertEqual("on", report["memory_capture"]["status"])
            self.assertIn("turn it off", report["memory_capture"]["opt_out_question"])
            for ref in config["publication"]["director"]["authority"]:
                self.assertEqual(ref["sha256"], self.helper.sha((target / ref["path"]).read_bytes()))
            self.assertEqual({**source_config, "project": config["project"], "publication": config["publication"]}, config)
            self.assertEqual({"README.md"}, set(self.helper.tree_files(target / "MEMORY")))
            self.assertFalse((target / ".sys4ai").exists())
            self.assertFalse((target / ".venv").exists())
            self.assertEqual({}, report["preserved_memory"])
            for entry in report["sources"]:
                if entry["destination"] in ("memory.yaml", "project.json", "README.md"):
                    self.assertEqual("specialized", entry["adoption"])
                elif entry["destination"] == "MEMORY/README.md":
                    self.assertEqual("adopted", entry["adoption"])
            self.assertEqual(self.helper.memory_inventory(target), report["current_memory"])
            self.assertEqual(self.helper.tree_files(template / "reference-assets/MEMORY-depo"),
                             self.helper.tree_files(target / "reference-assets/MEMORY-depo"))

    def test_existing_notes_config_and_partial_packages_remain_owned(self):
        files = {
            "memory.yaml": b"legacy_config: retain exact bytes and comments\n",
            "MEMORY/decisions/custom.md": b"Project-owned note and evidence.\n",
            "MEMORY/.private-note.md": b"Preserve hidden note too.\n",
            "reference-assets/MEMORY-depo/custom-contract.md": b"An earlier contract collection.\n",
            ".agents/skills/memory/SKILL.md": b"An existing memory skill edition.\n",
            ".agents/skills/memory/custom.txt": b"Custom skill resource.\n",
        }
        for name, raw in files.items():
            target = self.target / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
        original = self.helper.memory_inventory(self.target)
        first = self.run_setup(mode="prepare-existing")
        self.assertEqual(original, first["preserved_memory"])
        self.assertEqual(original, first["current_memory"])
        self.assertFalse((self.target / "MEMORY/README.md").exists())
        self.assertFalse((self.target / "reference-assets/MEMORY-depo/schema").exists())
        self.assertFalse((self.target / ".agents/skills/memory/scripts").exists())
        for name, raw in files.items():
            self.assertEqual(raw, (self.target / name).read_bytes())
        sources = {entry["destination"]: entry for entry in first["sources"]}
        self.assertEqual("preserved-project-owned", sources["memory.yaml"]["adoption"])
        self.assertEqual("skipped-existing-package", sources["MEMORY/README.md"]["adoption"])
        forged = deepcopy(first)
        forged["preserved_memory"] = {}
        with self.assertRaisesRegex(self.helper.InitializationError, "memory source"):
            self.helper.validate_record(forged, self.target, first["identity"])
        (self.target / "MEMORY/decisions/custom.md").write_text("A later project-owned revision.\n")
        (self.target / "memory.yaml").write_text("legacy_config: revised by the project\n")
        repeated = self.run_setup(mode="prepare-existing")
        for key in ("sources", "owned_files", "preserved_files", "preserved_memory"):
            self.assertEqual(first[key], repeated[key])
        self.assertNotEqual(first["current_memory"], repeated["current_memory"])
        self.assertEqual(self.helper.memory_inventory(self.target), repeated["current_memory"])

    def test_existing_empty_memory_collection_is_not_filled(self):
        (self.target / "MEMORY").mkdir(parents=True)
        report = self.run_setup(mode="prepare-existing")
        self.assertEqual([], list((self.target / "MEMORY").iterdir()))
        self.assertEqual("orchard", json.loads((self.target / "memory.yaml").read_text())["project"]["id"])
        self.assertEqual({"MEMORY": "directory"}, report["preserved_memory"])
        self.run_setup(mode="prepare-existing")

    def test_missing_selection_assets_or_unsafe_template_refuse_before_writes(self):
        template = self.root / self.helper.TEMPLATE
        changes = ["policy", "populated", "runtime-path", "enabled", "publisher",
                   "memory.yaml", "MEMORY/README.md", ".agents/skills/memory/SKILL.md",
                   *sorted(self.helper.MEMORY_CONTRACT_FILES), *sorted(self.helper.MEMORY_HELPER_FILES), *sorted(self.helper.CAPTURE_HELPER_FILES)]
        for change in changes:
            with self.subTest(change=change):
                backup = Path(self.temporary.name) / "memory-template-backup"
                shutil.copytree(template, backup)
                try:
                    if change == "policy":
                        policy = json.loads((template / self.helper.TEMPLATE_POLICY).read_text())
                        policy["starter_files"].remove("memory.yaml")
                        (template / self.helper.TEMPLATE_POLICY).write_bytes(self.helper.encoded(policy))
                    elif change == "populated":
                        (template / "MEMORY/learned.md").write_text("Must not seed learned state")
                    elif change in {"runtime-path", "enabled", "publisher"}:
                        config = json.loads((template / "memory.yaml").read_text())
                        if change == "runtime-path":
                            config["state"]["index"] = "/outside/a-prior-project/index"
                        elif change == "enabled":
                            config["backend"]["enabled"] = True
                        else:
                            config["publication"]["director"] = {"actor_id": "prior-project-director"}
                        (template / "memory.yaml").write_bytes(self.helper.encoded(config))
                    else:
                        (template / change).unlink()
                    before = fixture.manifest(self.root)
                    with self.assertRaises((self.helper.InitializationError, OSError)):
                        self.helper.run_initialization(**self.arguments)
                    self.assertEqual(before, fixture.manifest(self.root))
                    self.assertFalse(self.target.exists())
                finally:
                    shutil.rmtree(template)
                    backup.rename(template)

    def test_receipt_cannot_omit_memory_or_forge_specialization(self):
        original = self.run_setup()
        for name in ("memory.yaml", "MEMORY/README.md", ".agents/skills/memory/SKILL.md",
                     *sorted(self.helper.MEMORY_CONTRACT_FILES), *sorted(self.helper.MEMORY_HELPER_FILES)):
            altered = deepcopy(original)
            altered["sources"] = [entry for entry in altered["sources"] if entry["destination"] != name]
            altered["owned_files"].pop(name)
            with self.subTest(name=name), self.assertRaisesRegex(self.helper.InitializationError, "required starter source"):
                self.helper.validate_record(altered, self.target, original["identity"])
        altered = deepcopy(original)
        next(entry for entry in altered["sources"] if entry["destination"] == "memory.yaml")["adoption"] = "adopted"
        with self.assertRaisesRegex(self.helper.InitializationError, "specialization"):
            self.helper.validate_record(altered, self.target, original["identity"])
        altered = deepcopy(original)
        altered.pop("preserved_memory")
        with self.assertRaisesRegex(self.helper.InitializationError, "memory preservation"):
            self.helper.validate_record(altered, self.target, original["identity"])

    def test_interrupted_memory_adoption_resumes_exact_identity_and_sources(self):
        atomic = self.helper.atomic_write
        def interrupt(target, *args, **kwargs):
            if target == self.target / "MEMORY/README.md":
                raise self.helper.InitializationError("injected memory starter interruption")
            return atomic(target, *args, **kwargs)
        with patch.object(self.helper, "atomic_write", side_effect=interrupt), self.assertRaises(self.helper.InitializationError) as caught:
            self.helper.run_initialization(**self.arguments)
        partial = caught.exception.report
        self.assertEqual([], partial["completed_stages"])
        config = self.target / "memory.yaml"
        original_config = config.read_bytes()
        self.assertEqual("orchard", json.loads(original_config)["project"]["id"])
        config.write_text("Concurrent config change must survive a refused recovery.\n")
        before = fixture.manifest(self.root)
        with self.assertRaisesRegex(self.helper.InitializationError, "memory changed"):
            self.helper.run_initialization(**self.arguments)
        self.assertEqual(before, fixture.manifest(self.root))
        config.write_bytes(original_config)
        completed = self.run_setup()
        self.assertEqual(partial["sources"], completed["sources"])
        self.assertEqual(partial["owned_files"], completed["owned_files"])
        self.assertEqual(original_config, config.read_bytes())

    def test_interrupted_setup_binds_all_existing_memory_bytes(self):
        note = self.target / "MEMORY/project-note.md"
        note.parent.mkdir(parents=True)
        note.write_bytes(b"Reviewed original note.\n")
        atomic = self.helper.atomic_write
        def interrupt(target, *args, **kwargs):
            if target == self.target / "AGENTS.md":
                raise self.helper.InitializationError("injected early asset interruption")
            return atomic(target, *args, **kwargs)
        with patch.object(self.helper, "atomic_write", side_effect=interrupt), self.assertRaises(self.helper.InitializationError):
            self.helper.run_initialization(**{**self.arguments, "mode": "prepare-existing"})
        note.write_bytes(b"Concurrent note revision.\n")
        before = fixture.manifest(self.root)
        with self.assertRaisesRegex(self.helper.InitializationError, "memory changed"):
            self.helper.run_initialization(**{**self.arguments, "mode": "prepare-existing"})
        self.assertEqual(before, fixture.manifest(self.root))
        note.write_bytes(b"Reviewed original note.\n")
        self.run_setup(mode="prepare-existing")
        self.assertFalse((self.target / "MEMORY/README.md").exists())

    def test_v4_license_receipt_recovers_then_reruns_without_memory_adoption(self):
        template = self.root / self.helper.TEMPLATE
        backup = Path(self.temporary.name) / "v5-template"
        shutil.copytree(template, backup)
        fixture.remove_memory_edition(template)
        policy = json.loads((template / self.helper.TEMPLATE_POLICY).read_text())
        policy["starter_files"] = sorted(self.helper.required_starters(self.helper.LICENSE_CONTRACT))
        (template / self.helper.TEMPLATE_POLICY).write_bytes(self.helper.encoded(policy))
        identity = {"schema_version": 1, "project_id": "orchard", "project_name": "Orchard",
                    "purpose": self.arguments["purpose"], "relative_path": "Projects/Orchard"}
        proposed, sources, _ = self.helper.source_snapshot(self.root, fixture.SOURCE_SKILL, identity,
                                                         contract=self.helper.LICENSE_CONTRACT)
        for entry in sources:
            entry["adoption"] = "adopted"
        record = {"schema_version": 1, "setup_contract": self.helper.LICENSE_CONTRACT,
                  "status": "partial", "mode": "create", "operation_id": "project-setup-" + "4" * 32,
                  "identity": identity, "project_root": str(self.target), "sources": sources,
                  "owned_files": {name: self.helper.sha(raw) for name, raw in proposed.items()},
                  "preserved_files": {}, "preserved_licenses": {},
                  "recovery_before": {name: None for name in proposed},
                  "completed_stages": [], "active_stage": "assets", "checks": [],
                  "created_at": "2026-09-08T00:00:00+00:00", "git_setup": "separate"}
        receipt = self.target / self.helper.RECORD
        receipt.parent.mkdir(parents=True)
        receipt.write_bytes(self.helper.encoded(record))
        first = self.run_setup()
        self.assertEqual(self.helper.LICENSE_FILES, set(first["current_licenses"]))
        self.assertNotIn("preserved_memory", first)
        shutil.rmtree(template)
        backup.rename(template)
        repeated = self.run_setup()
        self.assertEqual(self.helper.LICENSE_CONTRACT, repeated["setup_contract"])
        for key in ("sources", "owned_files", "preserved_files", "preserved_licenses"):
            self.assertEqual(first[key], repeated[key])
        for name in ("memory.yaml", "MEMORY", "reference-assets/MEMORY-depo", ".agents/skills/memory"):
            self.assertFalse((self.target / name).exists(), name)


if __name__ == "__main__":
    unittest.main()
