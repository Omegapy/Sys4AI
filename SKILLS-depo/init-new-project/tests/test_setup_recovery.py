"""Generic setup recovery and preservation; no installed service is involved."""

from copy import deepcopy
import fcntl
import json
from pathlib import Path
import shutil
import unittest
from unittest.mock import patch

import test_initializer as fixture


class RecoveryCases(unittest.TestCase):
    setUp = fixture.InitializerTests.setUp
    run_setup = fixture.InitializerTests.run_setup
    fail_verification = fixture.InitializerTests.fail_verification

    def test_source_drift_rejected_before_destination_publication(self):
        template = self.root / self.helper.TEMPLATE
        changes = {
            "changed-file": lambda: (template / "SOUL.md").write_text("changed source"),
            "new-resource": lambda: (template / ".agents/skills/communication/new.md").write_text("added source"),
            "deleted-file": lambda: (template / ".agents/skills/communication/SKILL.md").unlink(),
        }
        original_snapshot = self.helper.source_snapshot
        registry_before = (self.root / "depot/projects.json").read_bytes()
        for name, change in changes.items():
            backup = Path(self.temporary.name) / "template-backup"
            shutil.copytree(template, backup)
            def changed_snapshot(*args):
                snapshot = original_snapshot(*args)
                change()
                return snapshot
            with (self.subTest(change=name), patch.object(self.helper, "source_snapshot", side_effect=changed_snapshot),
                  self.assertRaisesRegex(self.helper.InitializationError, "source .*changed")):
                self.helper.run_initialization(**self.arguments)
            self.assertFalse(self.target.exists())
            self.assertEqual(registry_before, (self.root / "depot/projects.json").read_bytes())
            shutil.rmtree(template)
            backup.rename(template)

    def test_role_reference_and_package_file_sets_are_bound(self):
        template = self.root / self.helper.TEMPLATE
        identity = {"schema_version": 1, "project_id": "orchard", "project_name": "Orchard",
                    "purpose": "Orchard observations.", "relative_path": "Projects/Orchard"}
        _, records, _ = self.helper.source_snapshot(self.root, fixture.SOURCE_SKILL, identity)
        for relative in ("sub-agent-roles/project-sub-agent/new.md", "reference-assets/new.md",
                         ".agents/skills/communication/new.md"):
            changed = template / relative
            changed.parent.mkdir(parents=True, exist_ok=True)
            changed.write_text("added during adoption")
            with (self.subTest(relative=relative), self.assertRaisesRegex(self.helper.InitializationError, "file set changed")):
                self.helper.check_sources(self.root, records)
            changed.unlink()

    def test_template_lock_blocks_adoption_and_releases_before_registration(self):
        lock = self.root / ".sys4ai/template-update/lock"
        lock.parent.mkdir(parents=True)
        with lock.open("w") as stream:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
            with self.assertRaisesRegex(self.helper.InitializationError, "template update is active"):
                self.helper.run_initialization(**self.arguments)
            self.assertFalse(self.target.exists())
        original = self.helper.register_project
        def register(*args, **kwargs):
            with lock.open("r") as stream:
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return original(*args, **kwargs)
        with patch.object(self.helper, "register_project", side_effect=register):
            self.run_setup()

    def test_interrupted_asset_adoption_resumes_and_rejects_conflicting_bytes(self):
        original = self.helper.atomic_write
        interrupted = False
        def write(target, raw, expected, **kwargs):
            nonlocal interrupted
            if not interrupted and target == self.target / "ROLE.md":
                interrupted = True
                raise OSError("injected interruption")
            return original(target, raw, expected, **kwargs)
        with (patch.object(self.helper, "atomic_write", side_effect=write),
              self.assertRaises(self.helper.InitializationError) as caught):
            self.helper.run_initialization(**self.arguments)
        self.assertEqual("assets", caught.exception.report["active_stage"])
        self.assertEqual([], caught.exception.report["completed_stages"])
        agents = self.target / "AGENTS.md"
        adopted = agents.read_bytes()
        agents.write_text("concurrent project edit")
        with self.assertRaises(self.helper.InitializationError) as conflict:
            self.helper.run_initialization(**self.arguments)
        self.assertIn("owned asset changed", conflict.exception.report["recovery"]["reason"])
        self.assertEqual("concurrent project edit", agents.read_text())
        agents.write_bytes(adopted)
        report = self.run_setup()
        self.assertEqual(["assets", "registration", "verification"], report["completed_stages"])

    def test_partial_source_change_cannot_silently_adopt_new_edition(self):
        original = self.helper.atomic_write
        def interrupted(target, raw, expected, **kwargs):
            if target == self.target / "ROLE.md":
                raise OSError("injected interruption")
            return original(target, raw, expected, **kwargs)
        with (patch.object(self.helper, "atomic_write", side_effect=interrupted),
              self.assertRaises(self.helper.InitializationError)):
            self.helper.run_initialization(**self.arguments)
        (self.root / self.helper.TEMPLATE / "SOUL.md").write_text("next edition")
        before = fixture.manifest(self.target)
        with self.assertRaisesRegex(self.helper.InitializationError, "partial asset adoption source changed"):
            self.helper.run_initialization(**self.arguments)
        self.assertEqual(before, fixture.manifest(self.target))

    def test_registration_interruption_is_idempotent_and_saved_assets_can_resume(self):
        original = self.helper.register_project
        def interrupted(*args, **kwargs):
            original(*args, **kwargs)
            raise OSError("interrupted after registration")
        with (patch.object(self.helper, "register_project", side_effect=interrupted),
              self.assertRaises(self.helper.InitializationError) as caught):
            self.helper.run_initialization(**self.arguments)
        self.assertEqual(["assets"], caught.exception.report["completed_stages"])
        soul = (self.target / "SOUL.md").read_bytes()
        shutil.rmtree(self.root / self.helper.TEMPLATE / ".template")
        self.run_setup()
        registry, _ = self.helper.read_registry(self.root)
        self.assertEqual(1, sum(entry["id"] == "orchard" for entry in registry["projects"]))
        self.assertEqual(soul, (self.target / "SOUL.md").read_bytes())

    def test_completed_rerun_preserves_edits_and_registry_metadata(self):
        first = self.run_setup()
        custom = b"Project-owned README after setup.\n"
        (self.target / "README.md").write_bytes(custom)
        registry_path = self.root / "depot/projects.json"
        registry = json.loads(registry_path.read_text())
        selected = next(entry for entry in registry["projects"] if entry["id"] == "orchard")
        selected.update(name="Registered display name", notes="Project-owned registry notes")
        selected["github_pages"] = {"status": "configured", "url": "https://example.com/orchard/"}
        registry_path.write_bytes(self.helper.encoded(registry))
        before = registry_path.read_bytes()
        repeated = self.run_setup(project_name="New input is not a rename", purpose="New input is not a rewrite")
        self.assertEqual("verified-current-files-and-registration", repeated["rerun"])
        self.assertEqual(first["identity"], repeated["identity"])
        self.assertEqual(custom, (self.target / "README.md").read_bytes())
        self.assertEqual(before, registry_path.read_bytes())
        self.assertNotEqual(repeated["owned_files"]["README.md"], repeated["current_files"]["README.md"])
        self.assertTrue(repeated["history"])
        (self.target / "ROLE.md").unlink()
        with self.assertRaises(self.helper.InitializationError) as caught:
            self.helper.run_initialization(**self.arguments)
        self.assertEqual("partial", caught.exception.report["status"])
        saved = json.loads((self.target / self.helper.RECORD).read_text())
        self.assertEqual("partial", saved["status"])
        self.assertNotIn("verified_at", saved)

    def test_existing_identity_packages_tasks_and_legacy_state_are_preserved(self):
        self.target.mkdir()
        identity = {"schema_version": 1, "project_id": "orchard", "project_name": "Saved name",
                    "purpose": "Saved purpose.", "relative_path": "Projects/Orchard",
                    "dataset_id": "project-owned-dataset", "custom": "keep"}
        (self.target / "project.json").write_text(json.dumps(identity))
        files = {
            "README.md": b"Custom README",
            "SPECS.md": b"Custom specs",
            ".agents/skills/communication/SKILL.md": b"Custom skill",
            "sub-agent-roles/project-sub-agent/ROLE.md": b"Custom role",
            "Tasks/task-owned/task.json": b'{"preserve":true}',
            "config/memory.toml": b"preserve original configuration bytes",
            "control_records/project-initialization.json": b"legacy receipt remains untouched",
            ".sys4ai/memory/private-data": b"project-owned data",
        }
        for name, raw in files.items():
            target = self.target / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
        before = fixture.manifest(self.target)
        report = self.run_setup(mode="prepare-existing")
        after = fixture.manifest(self.target)
        for name, checksum in before.items():
            self.assertEqual(checksum, after[name], name)
        self.assertFalse((self.target / ".agents/skills/communication/README.md").exists())
        self.assertFalse((self.target / "sub-agent-roles/project-sub-agent/AGENTS.md").exists())
        self.assertFalse((self.target / "Tasks/INDEX.md").exists())
        self.assertEqual("Saved name", report["identity"]["project_name"])
        self.assertNotIn("dataset_id", report["identity"])
        skipped = [entry for entry in report["sources"] if entry["adoption"] == "skipped-existing-package"]
        self.assertTrue(skipped)
        self.assertTrue(all(entry["destination_sha256"] is None for entry in skipped))

    def test_policy_and_receipt_reject_unsupported_contracts(self):
        policy = self.root / self.helper.TEMPLATE / ".template/baseline-assets.json"
        original = json.loads(policy.read_text())
        for change in ({"schema_version": 3}, {"optional_starter_files": ["obsolete.md"]}, {"extra": {}}):
            policy.write_text(json.dumps({**original, **change}))
            with (self.subTest(change=change), self.assertRaises(self.helper.InitializationError)):
                self.helper.run_initialization(**self.arguments)
            self.assertFalse(self.target.exists())
        policy.write_text(json.dumps(original))
        report = self.run_setup()
        schema = json.loads((fixture.SOURCE_SKILL / "assets/initialization-receipt.schema.json").read_text())
        self.assertTrue(set(schema["required"]) <= report.keys())
        self.assertEqual(schema["properties"]["setup_contract"]["const"], report["setup_contract"])
        self.helper.validate_record(report, self.target, report["identity"])
        for change in ({"schema_version": 2}, {"completed_stages": ["assets"]},
                       {"active_stage": "assets"}, {"owned_files": {"../outside": "0" * 64}},
                       {"sources": [{}]}, {"owned_files": {}, "preserved_files": {}}):
            with (self.subTest(change=change), self.assertRaises(self.helper.InitializationError)):
                self.helper.validate_record({**deepcopy(report), **change}, self.target, report["identity"])

    def test_missing_owned_file_cannot_be_hidden_by_reducing_receipt_inventory(self):
        original = self.run_setup()
        receipt_path = self.target / self.helper.RECORD
        soul = self.target / "SOUL.md"
        soul_bytes = soul.read_bytes()
        for remove_source, pretend_skipped in ((False, False), (True, False), (False, True)):
            altered = deepcopy(original)
            altered["owned_files"].pop("SOUL.md")
            if remove_source:
                altered["sources"] = [entry for entry in altered["sources"] if entry["destination"] != "SOUL.md"]
            if pretend_skipped:
                for entry in altered["sources"]:
                    if entry["destination"] == "SOUL.md":
                        entry.update(adoption="skipped-existing-package", destination_sha256=None)
            receipt_path.write_bytes(self.helper.encoded(altered))
            soul.unlink()
            before = fixture.manifest(self.target)
            with (self.subTest(remove_source=remove_source, pretend_skipped=pretend_skipped),
                  self.assertRaises(self.helper.InitializationError)):
                self.helper.run_initialization(**self.arguments)
            self.assertEqual(before, fixture.manifest(self.target))
            with self.assertRaises(self.helper.InitializationError):
                self.helper.verify_project(self.target, altered)
            soul.write_bytes(soul_bytes)
        receipt_path.write_bytes(self.helper.encoded(original))
        self.run_setup()

    def test_preserved_inventory_source_ownership_and_hashes_must_match_both_ways(self):
        self.target.mkdir()
        (self.target / "SOUL.md").write_bytes(b"Project-owned soul.\n")
        (self.target / "README.md").write_bytes(b"Project-owned README.\n")
        original = self.run_setup(mode="prepare-existing")
        receipt_path = self.target / self.helper.RECORD
        soul = self.target / "SOUL.md"
        soul_bytes = soul.read_bytes()
        cases = []
        altered = deepcopy(original)
        altered["preserved_files"].pop("SOUL.md")
        cases.append(("omitted-preserved", altered, True))
        altered = deepcopy(original)
        altered["sources"] = [entry for entry in altered["sources"] if entry["destination"] != "SOUL.md"]
        cases.append(("unreviewed-preserved", altered, False))
        altered = deepcopy(original)
        altered["owned_files"]["SOUL.md"] = altered["preserved_files"].pop("SOUL.md")
        cases.append(("preserved-moved-to-owned", altered, False))
        altered = deepcopy(original)
        altered["preserved_files"]["ROLE.md"] = altered["owned_files"].pop("ROLE.md")
        cases.append(("owned-moved-to-preserved", altered, False))
        altered = deepcopy(original)
        altered["preserved_files"]["SOUL.md"] = "0" * 64
        cases.append(("preserved-hash-mismatch", altered, False))
        altered = deepcopy(original)
        next(entry for entry in altered["sources"] if entry["destination"] == "README.md")["adoption"] = "adopted"
        cases.append(("contradictory-readme-sources", altered, False))
        for name, altered, delete_soul in cases:
            receipt_path.write_bytes(self.helper.encoded(altered))
            if delete_soul:
                soul.unlink()
            before = fixture.manifest(self.target)
            with (self.subTest(case=name), self.assertRaises(self.helper.InitializationError)):
                self.helper.run_initialization(**{**self.arguments, "mode": "prepare-existing"})
            self.assertEqual(before, fixture.manifest(self.target))
            if delete_soul:
                soul.write_bytes(soul_bytes)
        receipt_path.write_bytes(self.helper.encoded(original))
        self.run_setup(mode="prepare-existing")

    def test_minimum_saved_inventory_keeps_governance_and_renderer_sources(self):
        original = self.run_setup()
        for name in (".agents/skills/task/SKILL.md", "sub-agent-roles/project-sub-agent/ROLE.md",
                     self.helper.README_RENDERER, self.helper.TEMPLATE_POLICY):
            altered = deepcopy(original)
            source = self.helper.TEMPLATE + "/" + name
            removed = next(entry for entry in altered["sources"] if entry["source"] == source)
            altered["sources"] = [entry for entry in altered["sources"] if entry["source"] != source]
            destination = removed["destination"]
            if not any(entry["destination"] == destination for entry in altered["sources"]):
                altered["owned_files"].pop(destination)
            with (self.subTest(source=name), self.assertRaisesRegex(self.helper.InitializationError, "required starter source")):
                self.helper.validate_record(altered, self.target, original["identity"])


if __name__ == "__main__":
    unittest.main()
