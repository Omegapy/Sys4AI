"""Exact role casing and proof-bound setup editions in real depot fixtures."""

from copy import deepcopy
import json
from pathlib import Path
import shutil
import unittest
from unittest.mock import patch

import test_initializer as fixture


def rename_spelling(root: Path, source: str, destination: str) -> None:
    """Make the test arrangement explicit on both filesystem case modes."""
    temporary = root / ".test-role-spelling"
    (root / source).rename(temporary)
    temporary.rename(root / destination)


class RoleCaseEditionTests(unittest.TestCase):
    setUp = fixture.InitializerTests.setUp
    run_setup = fixture.InitializerTests.run_setup

    def lowercase_template(self):
        """Model the v2 policy/path contract, without relabeling a v3 receipt."""
        template = self.root / self.helper.TEMPLATE
        self.template_backup = Path(self.temporary.name) / "capitalized-template"
        shutil.copytree(template, self.template_backup)
        fixture.remove_memory_edition(template)
        rename_spelling(template, "Roles", "roles")
        policy_path = template / self.helper.TEMPLATE_POLICY
        policy = json.loads(policy_path.read_text())
        policy["roles"] = "roles"
        policy["starter_files"] = sorted(self.helper.required_starters(self.helper.LOWERCASE_CONTRACT))
        policy_path.write_bytes(self.helper.encoded(policy))
        script = template / self.helper.ROLE_HELPER
        script.write_text(script.read_text().replace('ROLE_ROOT_NAME = "Roles"', 'ROLE_ROOT_NAME = "roles"'))
        inputs = {"SOUL.md": (template / "SOUL.md").read_bytes(), self.helper.ROLE_HELPER: script.read_bytes()}
        inputs.update({"roles/" + name: raw for name, raw in self.helper.tree_files(template / "roles").items() if name != "INDEX.md"})
        (template / "roles/INDEX.md").write_bytes(self.helper.role_index_bytes(inputs, required=True, contract=self.helper.LOWERCASE_CONTRACT))

    def restore_template(self):
        template = self.root / self.helper.TEMPLATE
        shutil.rmtree(template)
        self.template_backup.rename(template)

    def seed_v2(self):
        self.lowercase_template()
        identity = {"schema_version": 1, "project_id": "orchard", "project_name": "Orchard",
                    "purpose": self.arguments["purpose"], "relative_path": "Projects/Orchard"}
        proposed, sources, _ = self.helper.source_snapshot(self.root, fixture.SOURCE_SKILL, identity,
                                                         contract=self.helper.LOWERCASE_CONTRACT)
        for source in sources:
            source["adoption"] = "adopted"
        record = {"schema_version": 1, "setup_contract": self.helper.LOWERCASE_CONTRACT,
                  "status": "partial", "mode": "create", "operation_id": "project-setup-" + "2" * 32,
                  "identity": identity, "project_root": str(self.target), "sources": sources,
                  "owned_files": {name: self.helper.sha(raw) for name, raw in proposed.items()},
                  "preserved_files": {}, "recovery_before": {name: None for name in proposed},
                  "completed_stages": [], "active_stage": "assets", "checks": [],
                  "created_at": "2026-09-08T00:00:00+00:00", "git_setup": "separate"}
        receipt = self.target / self.helper.RECORD
        receipt.parent.mkdir(parents=True)
        receipt.write_bytes(self.helper.encoded(record))
        return record

    def migrate_v2(self):
        current = (self.root / self.helper.TEMPLATE / self.helper.ROLE_HELPER).read_bytes()
        with self.helper.role_validator(current) as validator:
            preview = validator.case_rename_preview(self.target)
            validator.case_rename_apply(self.target, preview, confirmed=True)
            # Explicit fixture adoption and reindex, not initializer behavior.
            (self.target / self.helper.ROLE_HELPER).write_bytes(current)
            validator.reindex(self.target)
        return current

    def assert_rejected_unchanged(self, **overrides):
        before = fixture.manifest(self.root)
        with self.assertRaises(self.helper.InitializationError):
            self.helper.run_initialization(**{**self.arguments, **overrides})
        self.assertEqual(before, fixture.manifest(self.root))

    def test_lowercase_or_wrong_case_existing_collection_is_never_split(self):
        template = self.root / self.helper.TEMPLATE
        for spelling in ("roles", "ROLES"):
            with self.subTest(spelling=spelling):
                self.target.mkdir()
                shutil.copytree(template / "Roles/project-sub-agent", self.target / spelling / "project-sub-agent")
                self.assert_rejected_unchanged(mode="prepare-existing")
                self.assertEqual([spelling], [p.name for p in self.target.iterdir()])
                shutil.rmtree(self.target)

    def test_distinct_dual_collections_are_rejected_when_filesystem_supports_them(self):
        self.target.mkdir()
        (self.target / "Roles").mkdir()
        try:
            (self.target / "roles").mkdir()
        except FileExistsError:
            self.skipTest("real filesystem uses case-insensitive directory lookup")
        self.assert_rejected_unchanged(mode="prepare-existing")
        self.assertEqual(["Roles", "roles"], sorted(p.name for p in self.target.iterdir()))

    def test_current_policy_rejects_lowercase_template_directory(self):
        template = self.root / self.helper.TEMPLATE
        rename_spelling(template, "Roles", "roles")
        self.assert_rejected_unchanged()

    def test_interrupted_v3_assets_refuse_wrong_case_retry(self):
        original = self.helper.atomic_write
        def interrupted(target, raw, expected, **kwargs):
            if target == self.target / "Roles/INDEX.md":
                raise OSError("injected role index interruption")
            return original(target, raw, expected, **kwargs)
        with patch.object(self.helper, "atomic_write", side_effect=interrupted), self.assertRaises(self.helper.InitializationError):
            self.helper.run_initialization(**self.arguments)
        rename_spelling(self.target, "Roles", "roles")
        self.assert_rejected_unchanged()
        rename_spelling(self.target, "roles", "Roles")
        completed = self.run_setup()
        self.assertEqual(self.helper.SETUP_CONTRACT, completed["setup_contract"])

    def test_v2_partial_and_completed_reruns_keep_original_edition(self):
        original = self.seed_v2()
        first = self.run_setup()
        self.assertEqual(original["sources"], first["sources"])
        before = fixture.manifest(self.target / "roles")
        self.restore_template()
        repeated = self.run_setup()
        self.assertEqual(self.helper.LOWERCASE_CONTRACT, repeated["setup_contract"])
        for key in ("sources", "owned_files", "preserved_files"):
            self.assertEqual(original[key], repeated[key])
        self.assertEqual(before, fixture.manifest(self.target / "roles"))
        self.assertEqual(["roles"], [p.name for p in self.target.iterdir() if p.name.casefold() == "roles"])
        self.assertFalse(any((self.target / name).exists() for name in self.helper.MEMORY_FILES))
        self.assertFalse((self.target / ".agents/skills/memory").exists())

    def test_v2_partial_assets_cannot_switch_template_edition(self):
        self.seed_v2()
        self.restore_template()
        self.assert_rejected_unchanged()

    def test_v2_case_rename_requires_proof_and_records_actual_current_paths(self):
        self.seed_v2()
        first = self.run_setup()
        self.restore_template()
        current = self.migrate_v2()
        proof = self.target / self.helper.CASE_RECEIPT
        proof_raw = proof.read_bytes()
        proof.unlink()
        self.assert_rejected_unchanged()
        proof.write_bytes(proof_raw)
        repeated = self.run_setup()
        for key in ("setup_contract", "sources", "owned_files", "preserved_files"):
            self.assertEqual(first[key], repeated[key])
        self.assertEqual(self.helper.sha(proof_raw), repeated["role_case_transition"]["sha256"])
        self.assertTrue(any(name.startswith("Roles/") for name in repeated["current_files"]))
        self.assertFalse(any(name.startswith("roles/") for name in repeated["current_files"]))
        role = self.target / "Roles/project-sub-agent/ROLE.md"
        role.write_bytes(role.read_bytes() + b"\nA later authorized project role customization.\n")
        with self.helper.role_validator(current) as validator:
            validator.reindex(self.target)
        latest = self.run_setup()
        self.assertEqual(first["sources"], latest["sources"])
        self.assertEqual(self.helper.sha(role.read_bytes()), latest["current_files"]["Roles/project-sub-agent/ROLE.md"])
        self.assertEqual(proof_raw, proof.read_bytes())

    def test_v2_case_proof_pending_wrong_root_or_changed_reference_refuses_rerun(self):
        self.seed_v2()
        self.run_setup()
        self.restore_template()
        self.migrate_v2()
        proof = self.target / self.helper.CASE_RECEIPT
        original = proof.read_bytes()
        for change in ("pending", "wrong-root"):
            altered = json.loads(original)
            if change == "pending":
                altered["status"] = "pending"
            else:
                altered["preview"]["project_root"] = str(self.target.parent / "Other")
            proof.write_bytes(self.helper.encoded(altered))
            with self.subTest(change=change):
                self.assert_rejected_unchanged()
            proof.write_bytes(original)
        complete = self.run_setup()
        altered = deepcopy(complete)
        altered["role_case_transition"]["sha256"] = "0" * 64
        (self.target / self.helper.RECORD).write_bytes(self.helper.encoded(altered))
        self.assert_rejected_unchanged()

    def test_v2_completed_assets_resume_after_explicit_rename(self):
        self.seed_v2()
        original = self.helper.register_project
        def interrupted(*args, **kwargs):
            original(*args, **kwargs)
            raise OSError("injected post-registration interruption")
        with patch.object(self.helper, "register_project", side_effect=interrupted), self.assertRaises(self.helper.InitializationError) as caught:
            self.helper.run_initialization(**self.arguments)
        prior = caught.exception.report
        self.assertEqual(["assets"], prior["completed_stages"])
        self.restore_template()
        self.migrate_v2()
        completed = self.run_setup()
        self.assertEqual(self.helper.LOWERCASE_CONTRACT, completed["setup_contract"])
        self.assertEqual(prior["sources"], completed["sources"])
        self.assertEqual(["assets", "registration", "verification"], completed["completed_stages"])

    def test_prior_copy_first_receipt_survives_case_rename_and_new_preparation(self):
        self.lowercase_template()
        template = self.root / self.helper.TEMPLATE
        self.target.mkdir()
        shutil.copyfile(template / "SOUL.md", self.target / "SOUL.md")
        shutil.copytree(template / ".agents/skills/manage-subagent-roles",
                        self.target / ".agents/skills/manage-subagent-roles")
        shutil.copytree(template / "roles/project-sub-agent",
                        self.target / "sub-agent-roles/project-sub-agent")
        old = (template / self.helper.ROLE_HELPER).read_bytes()
        with self.helper.role_validator(old, role_root="roles") as validator:
            preview = validator.transition_preview(self.target)
            validator.transition_apply(self.target, preview, confirmed=True)
        receipt_bytes = (self.target / "roles/.transition.json").read_bytes()
        legacy = fixture.manifest(self.target / "sub-agent-roles")
        self.restore_template()
        self.migrate_v2()
        first = self.run_setup(mode="prepare-existing")
        self.assertEqual(self.helper.SETUP_CONTRACT, first["setup_contract"])
        self.assertEqual(receipt_bytes, (self.target / "Roles/.transition.json").read_bytes())
        self.assertEqual(legacy, fixture.manifest(self.target / "sub-agent-roles"))
        self.assertFalse((self.target / "Roles/task-manager").exists())
        repeated = self.run_setup(mode="prepare-existing")
        self.assertEqual(first["sources"], repeated["sources"])
        self.assertEqual(receipt_bytes, (self.target / "Roles/.transition.json").read_bytes())


if __name__ == "__main__":
    unittest.main()
