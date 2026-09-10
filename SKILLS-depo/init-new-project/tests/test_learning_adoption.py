"""Selected module adoption extends the original receipt in disposable projects."""
from copy import deepcopy
import fcntl
import json
from pathlib import Path
import shutil
import unittest
from unittest.mock import patch

import test_initializer as fixture


class LearningAdoptionTests(unittest.TestCase):
    setUp = fixture.InitializerTests.setUp
    run_setup = fixture.InitializerTests.run_setup

    def historical(self, contract="governance-starter-v6"):
        h = self.helper
        template = self.root / h.TEMPLATE
        backup = Path(self.temporary.name) / "current-template"
        shutil.copytree(template, backup)
        if contract == h.CAPTURE_CONTRACT:
            fixture.remove_learning_edition(template)
            checkpoint = template / ".agents/skills/memory/references/automatic-capture.md"
            checkpoint.write_text("# Earlier memory-only completion checkpoint\n")
            extra = template / ".agents/skills/memory/legacy/retired-guide.md"
            extra.parent.mkdir()
            extra.write_text("An owned resource retired by the later complete package.\n")
        else:
            fixture.remove_memory_edition(template)
        policy = json.loads((template / h.TEMPLATE_POLICY).read_text())
        policy["starter_files"] = sorted(h.required_starters(contract))
        (template / h.TEMPLATE_POLICY).write_bytes(h.encoded(policy))
        identity = {"schema_version": 1, "project_id": "orchard", "project_name": "Orchard", "purpose": self.arguments["purpose"], "relative_path": "Projects/Orchard"}
        proposed, sources, original = h.source_snapshot(self.root, fixture.SOURCE_SKILL, identity, contract=contract)
        for source in sources:
            name = source["destination"]
            source["adoption"] = "specialized" if contract in h.MEMORY_CONTRACTS and name in h.SPECIALIZED_FILES and proposed[name] != original.get(name) else "adopted"
        record = {"schema_version": 1, "setup_contract": contract, "status": "partial", "mode": "create",
                  "operation_id": "project-setup-" + "6" * 32, "identity": identity, "project_root": str(self.target),
                  "sources": sources, "owned_files": {name: h.sha(raw) for name, raw in proposed.items()}, "preserved_files": {},
                  "preserved_licenses": {}, "recovery_before": {name: None for name in proposed},
                  "completed_stages": [], "active_stage": "assets", "checks": [], "created_at": "2026-09-09T00:00:00+00:00", "git_setup": "separate"}
        if contract in h.MEMORY_CONTRACTS:
            record["preserved_memory"] = {}
        receipt = self.target / h.RECORD
        receipt.parent.mkdir(parents=True)
        receipt.write_bytes(h.encoded(record))
        result = self.run_setup()
        shutil.rmtree(template)
        backup.rename(template)
        return result

    def adopt(self, refresh=False):
        return self.run_setup(mode="prepare-existing", adopt_module="what-did-you-learn", refresh_dependency=["memory"] if refresh else [])

    def assert_base(self, first, after):
        for key in self.helper.BASE_IMMUTABLE:
            self.assertEqual(first.get(key), after.get(key), key)

    def test_v6_requires_selected_adoption_and_explicit_whole_dependency_refresh(self):
        first = self.historical()
        config = (self.target / "memory.yaml").read_bytes()
        ordinary = self.run_setup()
        self.assert_base(first, ordinary)
        self.assertFalse((self.target / self.helper.LEARNING_ROOT).exists())
        preserved = self.adopt()
        operation = preserved["module_adoptions"][-1]
        self.assertEqual("available", operation["capabilities"]["manual_review"])
        self.assertEqual("unavailable", operation["capabilities"]["shared_automatic_checkpoint"])
        self.assertEqual("preserved-package", operation["packages"][".agents/skills/memory"]["decision"])
        self.assertTrue((self.target / ".agents/skills/memory/legacy/retired-guide.md").exists())
        refreshed = self.adopt(refresh=True)
        self.assert_base(first, refreshed)
        operation = refreshed["module_adoptions"][-1]
        self.assertEqual("refreshed-owned-package", operation["packages"][".agents/skills/memory"]["decision"])
        self.assertEqual("available", operation["capabilities"]["shared_automatic_checkpoint"])
        self.assertFalse((self.target / ".agents/skills/memory/legacy").exists())
        self.assertEqual(config, (self.target / "memory.yaml").read_bytes())
        bare_repeat = self.adopt()
        self.assertEqual(2, len(bare_repeat["module_adoptions"]))
        self.helper.validate_record(bare_repeat, self.target, first["identity"])
        self.assertEqual(operation["manifest_sha256"], bare_repeat["module_adoptions"][-1]["manifest_sha256"])
        ordinary_after = self.run_setup()
        self.assert_base(first, ordinary_after)
        self.assertEqual(2, len(ordinary_after["module_adoptions"]))
        self.assertEqual(1, sum(entry["id"] == "orchard" for entry in json.loads((self.root / "depot/projects.json").read_text())["projects"]))

    def test_prememory_adoption_gets_empty_local_binding_and_preserves_base(self):
        first = self.historical(self.helper.LICENSE_CONTRACT)
        # The original v4 governing files may contain no memory completion route.
        (self.target / "AGENTS.md").write_text("# Original project-specific rules\n")
        original_rules = (self.target / "AGENTS.md").read_bytes()
        after = self.adopt()
        self.assert_base(first, after)
        self.assertNotIn("preserved_memory", after)
        config = json.loads((self.target / "memory.yaml").read_text())
        self.assertEqual("orchard", config["project"]["id"])
        self.assertEqual(original_rules + self.helper.completion_link(), (self.target / "AGENTS.md").read_bytes())
        for ref in config["publication"]["director"]["authority"]:
            self.assertEqual(self.helper.sha((self.target / ref["path"]).read_bytes()), ref["sha256"])
        self.assertEqual({"README.md"}, set(self.helper.tree_files(self.target / "MEMORY")))
        self.assertFalse((self.target / ".sys4ai").exists())
        self.assertEqual("available", after["module_adoptions"][-1]["capabilities"]["shared_automatic_checkpoint"])

    def test_custom_incomplete_dependency_capture_off_notes_and_runtime_stay_whole(self):
        self.historical()
        config_path = self.target / "memory.yaml"
        config = json.loads(config_path.read_text()); config["integration"]["automatic_capture"] = False
        config_path.write_bytes(self.helper.encoded(config))
        (self.target / ".agents/skills/memory/scripts/memory_recovery.py").unlink()
        (self.target / ".agents/skills/memory/custom.txt").write_text("Retain custom package content.\n")
        for name in ("MEMORY/owned-note.md", "control_records/memory/owned-history.json", ".sys4ai/memory/backend-config/owned.json"):
            path = self.target / name; path.parent.mkdir(parents=True, exist_ok=True); path.write_text("Preserve project-owned content.\n")
        memory_before = self.helper.memory_inventory(self.target)
        runtime = fixture.manifest(self.target / ".sys4ai")
        history = fixture.manifest(self.target / "control_records/memory")
        with self.assertRaisesRegex(self.helper.InitializationError, "incomplete") as caught:
            self.adopt(refresh=True)
        after = caught.exception.report
        operation = after["module_adoptions"][-1]
        self.assertEqual("preserved-incompatible-refresh", operation["packages"][".agents/skills/memory"]["decision"])
        self.assertEqual("partial", operation["status"])
        self.assertFalse(operation["static_health"]["static_ready"])
        self.assertIn(".agents/skills/memory/scripts/memory_recovery.py", operation["packages"][".agents/skills/memory"]["diagnostic"]["different_resources"])
        self.assertEqual("off", operation["capabilities"]["shared_automatic_checkpoint"])
        self.assertEqual(memory_before, self.helper.memory_inventory(self.target))
        self.assertEqual(runtime, fixture.manifest(self.target / ".sys4ai"))
        self.assertEqual(history, fixture.manifest(self.target / "control_records/memory"))

    def test_completed_module_rerun_preserves_edits_and_does_not_read_new_template(self):
        first = self.historical()
        after = self.adopt(refresh=True)
        operation_id = after["module_adoptions"][-1]["operation_id"]
        module_readme = self.target / self.helper.LEARNING_ROOT / "README.md"
        module_readme.write_bytes(module_readme.read_bytes() + b"\nProject-local addition.\n")
        before = module_readme.read_bytes()
        (self.root / self.helper.TEMPLATE / self.helper.TEMPLATE_POLICY).write_text("Changed, incompatible current Template policy.\n")
        repeated = self.adopt(refresh=True)
        self.assertEqual(operation_id, repeated["module_adoptions"][-1]["operation_id"])
        self.assertEqual(1, len(repeated["module_adoptions"]))
        self.assertEqual(before, module_readme.read_bytes())
        self.assert_base(first, repeated)

    def test_interrupted_adoption_rejects_source_target_drift_and_recovers_exact_operation(self):
        first = self.historical()
        write = self.helper.atomic_write
        count = 0
        def interrupt(target, data, expected, **kwargs):
            nonlocal count
            if str(target).startswith(str(self.target / self.helper.LEARNING_ROOT)):
                count += 1
                if count == 2:
                    raise self.helper.InitializationError("injected module publication interruption")
            return write(target, data, expected, **kwargs)
        with patch.object(self.helper, "atomic_write", side_effect=interrupt), self.assertRaises(self.helper.InitializationError) as caught:
            self.adopt(refresh=True)
        pending = caught.exception.report["module_adoptions"][-1]
        with self.assertRaisesRegex(self.helper.InitializationError, "pending selected module"):
            self.helper.run_initialization(**self.arguments)
        target = self.target / next(name for name in pending["files"] if (self.target / name).is_file() and name.startswith(self.helper.LEARNING_ROOT))
        original = target.read_bytes(); target.write_bytes(original + b"Changed during recovery.\n")
        before = fixture.manifest(self.target)
        with self.assertRaisesRegex(self.helper.InitializationError, "target changed|conflicting content"):
            self.adopt(refresh=True)
        self.assertEqual(before, fixture.manifest(self.target))
        target.write_bytes(original)
        source = self.root / self.helper.TEMPLATE / self.helper.LEARNING_ROOT / "README.md"
        original_source = source.read_bytes(); source.write_bytes(original_source + b"Source drift.\n")
        before = fixture.manifest(self.target)
        with self.assertRaisesRegex(self.helper.InitializationError, "sources changed"):
            self.adopt(refresh=True)
        self.assertEqual(before, fixture.manifest(self.target))
        source.write_bytes(original_source)
        complete = self.adopt(refresh=True)
        self.assert_base(first, complete)
        self.assertEqual(pending["operation_id"], complete["module_adoptions"][-1]["operation_id"])
        self.assertEqual("available", complete["module_adoptions"][-1]["capabilities"]["shared_automatic_checkpoint"])

    def test_incomplete_base_bad_nested_scope_and_active_locks_refuse_writes(self):
        first = self.historical()
        receipt = self.target / self.helper.RECORD
        original = receipt.read_bytes()
        altered = json.loads(original); altered["status"] = "partial"; altered["active_stage"] = "verification"
        receipt.write_bytes(self.helper.encoded(altered))
        before = fixture.manifest(self.target)
        with self.assertRaisesRegex(self.helper.InitializationError, "incomplete base"):
            self.adopt()
        self.assertEqual(before, fixture.manifest(self.target))
        receipt.write_bytes(original)
        lock = self.root / "depot" / (".initialize-" + self.helper.sha(b"Projects/Orchard")[:16] + ".lock")
        for selected_lock in (lock, self.root / ".sys4ai/template-update/lock"):
            with selected_lock.open("r+") as stream:
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
                before = fixture.manifest(self.target)
                with self.assertRaisesRegex(self.helper.InitializationError, "active"):
                    self.adopt()
                self.assertEqual(before, fixture.manifest(self.target))
        after = self.adopt()
        valid = deepcopy(after)
        operation = after["module_adoptions"][-1]
        operation["files"]["docs/unauthorized.txt"] = {"before": None, "after": "0" * 64}
        operation["manifest_sha256"] = self.helper.sha(self.helper.encoded({key: operation[key] for key in self.helper.MODULE_FROZEN}))
        with self.assertRaisesRegex(self.helper.InitializationError, "outside its selected scope"):
            self.helper.validate_record(after, self.target, first["identity"])
        for field, value in (("schema_version", True), ("status", []), ("status", {}), ("active_stage", []), ("unsupported_field", True)):
            with self.subTest(field=field, value=value):
                malformed = deepcopy(valid)
                malformed["module_adoptions"][-1][field] = value
                receipt.write_bytes(self.helper.encoded(malformed))
                before = fixture.manifest(self.target)
                with self.assertRaises(self.helper.InitializationError):
                    self.helper.run_initialization(**{**self.arguments, "mode": "prepare-existing", "adopt_module": "what-did-you-learn"})
                self.assertEqual(before, fixture.manifest(self.target))
        receipt.write_bytes(self.helper.encoded(valid))

    def test_receipt_stage_interruptions_resume_and_preserve_exact_operation(self):
        self.historical()
        backup = Path(self.temporary.name) / "base-project"
        shutil.copytree(self.target, backup)
        write = self.helper.atomic_write
        for stage in ("first-file", "verification", "verified-receipt", "completed-receipt"):
            with self.subTest(stage=stage):
                if stage != "first-file":
                    shutil.rmtree(self.target); shutil.copytree(backup, self.target)
                injected = False
                def interrupt(target, data, expected, **kwargs):
                    nonlocal injected
                    selected = stage == "first-file" and str(target).startswith(str(self.target / self.helper.LEARNING_ROOT))
                    if target == self.target / self.helper.RECORD and stage in {"verified-receipt", "completed-receipt"}:
                        operation = json.loads(data).get("module_adoptions", [{}])[-1]
                        selected = (operation.get("completed_stages") == ["assets", "verification"]
                                    and operation.get("status") == ("completed" if stage == "completed-receipt" else "partial"))
                    if selected and not injected:
                        injected = True
                        raise self.helper.InitializationError("injected stage boundary")
                    return write(target, data, expected, **kwargs)
                with patch.object(self.helper, "atomic_write", side_effect=interrupt):
                    if stage == "verification":
                        with patch.object(self.helper, "verify_module_current", side_effect=self.helper.InitializationError("injected verification boundary")), self.assertRaises(self.helper.InitializationError) as caught:
                            self.adopt(refresh=True)
                    else:
                        with self.assertRaises(self.helper.InitializationError) as caught:
                            self.adopt(refresh=True)
                pending = caught.exception.report["module_adoptions"][-1]
                self.assertEqual("completed", json.loads((self.target / self.helper.RECORD).read_text())["status"])
                completed = self.adopt(refresh=True)["module_adoptions"][-1]
                self.assertEqual(pending["operation_id"], completed["operation_id"])
                self.assertEqual(pending["manifest_sha256"], completed["manifest_sha256"])
                self.assertEqual("completed", completed["status"])

    def test_interrupted_first_binding_reuses_final_governance_without_rebinding_old_state(self):
        first = self.historical(self.helper.LICENSE_CONTRACT)
        (self.target / "AGENTS.md").write_text("# Custom original rules\n")
        write = self.helper.atomic_write
        def interrupt(target, data, expected, **kwargs):
            if target == self.target / "memory.yaml":
                raise self.helper.InitializationError("injected first binding interruption")
            return write(target, data, expected, **kwargs)
        with patch.object(self.helper, "atomic_write", side_effect=interrupt), self.assertRaises(self.helper.InitializationError):
            self.adopt()
        governing = (self.target / "AGENTS.md").read_bytes()
        completed = self.adopt()
        self.assertEqual(governing, (self.target / "AGENTS.md").read_bytes())
        self.assert_base(first, completed)
        self.assertEqual("current", completed["module_adoptions"][-1]["capabilities"]["director_binding"])

    def test_owned_package_file_directory_transition_refuses_before_receipt_or_asset_writes(self):
        self.historical()
        collision = self.root / self.helper.TEMPLATE / ".agents/skills/memory/legacy"
        collision.write_text("Current edition replaces the old directory with a file.\n")
        before = fixture.manifest(self.root)
        with self.assertRaisesRegex(self.helper.InitializationError, "file/directory transition"):
            self.adopt(refresh=True)
        self.assertEqual(before, fixture.manifest(self.root))
        self.assertTrue((self.target / ".agents/skills/memory/legacy/retired-guide.md").is_file())

    def test_empty_unowned_dependency_directory_never_becomes_refresh_authority(self):
        self.historical(self.helper.LICENSE_CONTRACT)
        package = self.target / ".agents/skills/memory"
        package.mkdir()
        with self.assertRaisesRegex(self.helper.InitializationError, "incomplete") as caught:
            self.adopt(refresh=True)
        result = caught.exception.report
        decision = result["module_adoptions"][-1]["packages"][".agents/skills/memory"]
        self.assertEqual("preserved-incompatible-refresh", decision["decision"])
        self.assertEqual({".agents/skills/memory": "directory"}, decision["after"])
        self.assertEqual([], list(package.iterdir()))
        self.assertEqual("unavailable", result["module_adoptions"][-1]["capabilities"]["manual_review"])
        self.assertEqual("partial", result["module_adoptions"][-1]["status"])
        self.assertFalse(result["static_ready"])


if __name__ == "__main__":
    unittest.main()
