"""Template ownership and failure boundaries, using temporary depots only."""

from __future__ import annotations

import importlib.util
import base64
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

HELPER = Path(__file__).resolve().parents[1] / "tools/template_update.py"
spec = importlib.util.spec_from_file_location("template_update", HELPER)
engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)


def put(root: Path, relative: str, text: str) -> Path:
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    return target


def add_skill(root: Path, name: str) -> None:
    put(root, f"SKILLS-depo/{name}/SKILL.md", f"---\nname: {name}\ndescription: Test {name}.\n---\n\n# Skill\n")
    put(root, f"SKILLS-depo/{name}/scripts/example.py", "def answer():\n    return 42\n")


def fixture(root: Path) -> Path:
    template = root / engine.TEMPLATE
    template.mkdir(parents=True)
    for name in (*engine.BASELINE_SKILLS, "init-new-project"):
        add_skill(root, name)
    overrides = {
        "SOULS-depo/SOUL.md": "SOUL.md",
        "AGENTS-depo/project-template-AGENTS.md": "AGENTS.md",
        "ROLES-depo/project-director-ROLE.md": "ROLE.md",
        "ROLES-depo/project-sub-agent-AGENTS.md": "Roles/project-sub-agent/AGENTS.md",
        "ROLES-depo/project-sub-agent-ROLE.md": "Roles/project-sub-agent/ROLE.md",
        "SPECS-depo/project-template-SPECS.md": "SPECS.md",
        "SPECS-depo/project-template.gitignore": ".gitignore",
    }
    for role in ("project-sub-agent", "task-manager"):
        for name in ("AGENTS", "ROLE"):
            overrides[f"ROLES-depo/{role}-{name}.md"] = f"Roles/{role}/{name}.md"
    for origin, target in overrides.items():
        actual = HELPER.parents[1] / origin
        text = actual.read_text() if target.startswith("Roles/") else "# Starter " + target + "\n"
        put(root, origin, text)
    put(root, "SKILLS-depo/manage-subagent-roles/scripts/role_catalog.py",
        (HELPER.parents[1] / "SKILLS-depo/manage-subagent-roles/scripts/role_catalog.py").read_text())
    mirrors = {
        "SKILLS-depo/init-new-project/assets/baseline-assets.json": ".template/baseline-assets.json",
        "SKILLS-depo/init-new-project/assets/project-readme.md": ".template/project-readme.md",
    }
    put(root, next(iter(mirrors)), '{"schema_version": 2, "roles": "Roles"}\n')
    put(root, "SKILLS-depo/init-new-project/assets/project-readme.md", "# __PROJECT_NAME__\n")
    put(root, engine.MANIFEST, json.dumps({
        "schema_version": 1, "template": engine.TEMPLATE,
        "overrides": overrides, "mirrors": mirrors,
    }))
    return template


def file_inventory(folder: Path) -> dict[str, bytes]:
    return {
        item.relative_to(folder).as_posix(): item.read_bytes()
        for item in folder.rglob("*") if item.is_file()
    }


def lowercase_owned_template(root: Path, template: Path) -> bytes:
    """Recreate the prior ownership edition without altering its source bindings."""
    engine.update(root, "apply")
    state = engine.load_state(root)
    state["files"] = {name.replace("Roles/", "roles/", 1): entry for name, entry in state["files"].items()}
    index = state["files"][engine.PREVIOUS_ROLE_INDEX]
    index["generated"]["inputs"] = engine.role_index_inputs(state["files"], "roles")
    folder = template / "Roles"
    folder.rename(template / "fixture-case-hop")
    (template / "fixture-case-hop").rename(template / "roles")
    # Preserve a raw-state representation distinct from the writer's encoding.
    raw = json.dumps(state, indent=4).encode() + b"\n"
    (root / engine.STATE).write_bytes(raw)
    engine.validate_state(state)
    return raw


class TemplateUpdateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.template = fixture(self.root)

    def apply(self) -> dict:
        return engine.update(self.root, "apply")

    def memory_fixture(self):
        add_skill(self.root, "memory")
        put(self.root, "MEMORY-depo/starter/MEMORY/README.md", "# Empty memory\n")
        put(self.root, "MEMORY-depo/starter/memory.yaml", '{"project": null, "enabled": false}\n')
        put(self.root, "MEMORY-depo/policy.md", "# Memory policy\n")
        mapping = json.loads((self.root / engine.MANIFEST).read_text())
        mapping["overrides"].update({"MEMORY-depo/starter/MEMORY/README.md": "MEMORY/README.md",
                                     "MEMORY-depo/starter/memory.yaml": "memory.yaml"})
        (self.root / engine.MANIFEST).write_text(json.dumps(mapping))

    def test_memory_starters_complete_skill_and_contract_ownership(self):
        self.memory_fixture()
        self.assertEqual(self.apply()["status"], "applied")
        self.assertEqual((self.template / "MEMORY/README.md").read_text(), "# Empty memory\n")
        self.assertTrue((self.template / ".agents/skills/memory/scripts/example.py").is_file())
        self.assertTrue((self.template / "reference-assets/MEMORY-depo/policy.md").is_file())
        self.assertFalse((self.template / "reference-assets/MEMORY-depo/starter").exists())
        put(self.root, "MEMORY-depo/example.md", "Inactive example\n")
        self.apply()
        self.assertTrue((self.template / "reference-assets/MEMORY-depo/example.md").exists())
        (self.root / "MEMORY-depo/example.md").unlink()
        self.apply()
        self.assertFalse((self.template / "reference-assets/MEMORY-depo/example.md").exists())
        put(self.template, "MEMORY/README.md", "Customized memory ownership\n")
        put(self.root, "MEMORY-depo/starter/MEMORY/README.md", "Revised empty starter\n")
        before = file_inventory(self.template)
        with self.assertRaisesRegex(engine.UpdateError, "conflicts"):
            self.apply()
        self.assertEqual(before, file_inventory(self.template))

    def test_interrupted_memory_publication_resumes_exact_pending_inputs(self):
        self.memory_fixture()
        self.apply()
        put(self.root, "MEMORY-depo/policy.md", "# Revised memory policy\n")
        put(self.root, "MEMORY-depo/starter/MEMORY/README.md", "# Revised empty memory\n")
        original = engine.atomic_write
        interrupted_once = []
        def interrupted(path, data, mode=0o644):
            original(path, data, mode)
            if path == self.template / "MEMORY/README.md" and not interrupted_once:
                interrupted_once.append(True)
                raise OSError("memory fixture interruption")
        with patch.object(engine, "atomic_write", side_effect=interrupted):
            with self.assertRaisesRegex(OSError, "memory fixture interruption"):
                self.apply()
        self.assertTrue((self.root / engine.PENDING).is_file())
        result = self.apply()
        self.assertTrue(result["recovered"])
        self.assertEqual(engine.update(self.root, "check")["status"], "current")
        self.assertEqual((self.template / "reference-assets/MEMORY-depo/policy.md").read_text(), "# Revised memory policy\n")

    def learning_fixture(self):
        source = HELPER.parents[1]
        for relative in ("LEARNING-depo", "SKILLS-depo/what-did-you-learn"):
            shutil.copytree(source / relative, self.root / relative)

    def test_learning_default_mapping_tracks_declared_add_modify_remove(self):
        self.learning_fixture()
        self.apply()
        for origin, target in (("LEARNING-depo", "reference-assets/LEARNING-depo"),
                               ("SKILLS-depo/what-did-you-learn", ".agents/skills/what-did-you-learn")):
            self.assertEqual(file_inventory(self.root / origin), file_inventory(self.template / target))
        manifest_path = self.root / "LEARNING-depo/contract.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["required_resources"].append("usage.md")
        manifest_path.write_text(json.dumps(manifest))
        put(self.root, "LEARNING-depo/usage.md", "# Reusable usage\n")
        self.apply()
        self.assertEqual("# Reusable usage\n", (self.template / "reference-assets/LEARNING-depo/usage.md").read_text())
        put(self.root, "LEARNING-depo/usage.md", "# Revised reusable usage\n")
        self.apply()
        self.assertEqual("# Revised reusable usage\n", (self.template / "reference-assets/LEARNING-depo/usage.md").read_text())
        manifest["required_resources"].remove("usage.md")
        manifest_path.write_text(json.dumps(manifest))
        (self.root / "LEARNING-depo/usage.md").unlink()
        self.apply()
        self.assertFalse((self.template / "reference-assets/LEARNING-depo/usage.md").exists())
        self.assertEqual("current", engine.update(self.root, "check")["status"])

    def test_learning_conflict_and_broken_package_preserve_the_template(self):
        self.learning_fixture()
        self.apply()
        resolver = self.root / "SKILLS-depo/what-did-you-learn/scripts/learning_contract.py"
        original = resolver.read_bytes()
        resolver.write_text("def incomplete(\n")
        before = file_inventory(self.template)
        with self.assertRaises(engine.UpdateError):
            self.apply()
        self.assertEqual(before, file_inventory(self.template))
        resolver.write_bytes(original)
        put(self.template, "reference-assets/LEARNING-depo/policy.md", "# Project customization\n")
        put(self.root, "LEARNING-depo/policy.md", "# Updated reusable policy\n")
        before = file_inventory(self.template)
        with self.assertRaisesRegex(engine.UpdateError, "conflicts"):
            self.apply()
        self.assertEqual(before, file_inventory(self.template))

    def test_case_transition_renames_exact_directory_and_archives_original_state(self):
        raw_state = lowercase_owned_template(self.root, self.template)
        put(self.template, "roles/project-sub-agent/local-notes.txt", "Preserve project notes\n")
        (self.template / "roles/project-sub-agent/empty").mkdir()
        inode = (self.template / "roles").stat().st_ino
        old_tree = file_inventory(self.template / "roles")
        before = file_inventory(self.root)
        preview = engine.update(self.root, "check")
        self.assertEqual(before, file_inventory(self.root))
        self.assertEqual(["roles"], engine.role_case_entries(self.template))
        self.assertEqual("Roles", preview["role_case_transition"]["to"])
        self.assertFalse(any(name.startswith(("Roles/", "roles/")) for name in preview["deletions"] + preview["additions"]))
        self.assertEqual("applied", self.apply()["status"])
        self.assertEqual(["Roles"], engine.role_case_entries(self.template))
        self.assertEqual(inode, (self.template / "Roles").stat().st_ino)
        self.assertEqual(old_tree, file_inventory(self.template / "Roles"))
        self.assertTrue((self.template / "Roles/project-sub-agent/empty").is_dir())
        self.assertEqual("Preserve project notes\n", (self.template / "Roles/project-sub-agent/local-notes.txt").read_text())
        archives = list((self.root / engine.CONTROL / "role-layout-history").glob("*.json"))
        self.assertEqual(1, len(archives))
        retained = json.loads(archives[0].read_bytes())
        self.assertEqual(raw_state, base64.b64decode(retained["before_state"]))
        self.assertEqual(old_tree, {name: base64.b64decode(raw) for name, raw in retained["payloads"].items()})
        self.assertFalse(any(name.startswith("roles/") for name in engine.load_state(self.root)["files"]))
        self.assertFalse((self.template / ".sys4ai").exists())
        mtimes = {item: item.stat().st_mtime_ns for item in [self.root / engine.STATE, *self.template.rglob("*")]}
        self.assertEqual("current", engine.update(self.root, "check")["status"])
        self.assertEqual("current", self.apply()["status"])
        self.assertEqual(mtimes, {item: item.stat().st_mtime_ns for item in mtimes})

    def test_case_transition_rejects_distinct_dual_trees_even_when_identical(self):
        lowercase_owned_template(self.root, self.template)
        try:
            (self.template / "Roles").mkdir()
        except FileExistsError:
            self.skipTest("distinct case-equivalent directories require a case-sensitive filesystem")
        shutil.copytree(self.template / "roles", self.template / "Roles", dirs_exist_ok=True)
        for changed in (False, True):
            if changed:
                (self.template / "Roles/task-manager/ROLE.md").write_text("Distinct customized tree\n")
            original = file_inventory(self.root)
            with self.assertRaisesRegex(engine.UpdateError, "exactly.*lowercase"):
                self.apply()
            self.assertEqual(original, file_inventory(self.root))
            self.assertFalse((self.root / engine.PENDING).exists())

    def test_case_transition_rejects_wrong_case_aliases_and_missing_ownership(self):
        lowercase_owned_template(self.root, self.template)
        (self.template / "roles").rename(self.template / "fixture-case-hop")
        (self.template / "fixture-case-hop").rename(self.template / "ROLES")
        original = file_inventory(self.root)
        with self.assertRaisesRegex(engine.UpdateError, "exactly.*lowercase"):
            self.apply()
        self.assertEqual(original, file_inventory(self.root))
        (self.template / "ROLES").rename(self.template / "fixture-case-hop")
        (self.template / "fixture-case-hop").rename(self.template / "roles")
        (self.root / engine.STATE).unlink()
        original = file_inventory(self.template)
        with self.assertRaises(engine.UpdateError):
            self.apply()
        self.assertEqual(original, file_inventory(self.template))

    def test_case_transition_requires_complete_mapping_and_fresh_reviewed_tree(self):
        lowercase_owned_template(self.root, self.template)
        before = engine.load_state(self.root)
        snap = engine.snapshot(self.root)
        missing = json.loads(json.dumps(snap["state"]))
        missing["files"].pop("Roles/task-manager/ROLE.md")
        with self.assertRaisesRegex(engine.UpdateError, "every old role destination"):
            engine.role_case_mapping(before, missing)
        preview = engine.case_preview(self.root, before, snap["state"])
        put(self.template, "roles/project-sub-agent/new-notes.txt", "Changed after review\n")
        original = file_inventory(self.root)
        with self.assertRaisesRegex(engine.UpdateError, "changed after preflight"):
            engine.make_pending(before, snap, root=self.root, reviewed_case=preview)
        self.assertEqual(original, file_inventory(self.root))

    def test_case_transition_rejects_linked_managed_bytes_before_publication(self):
        lowercase_owned_template(self.root, self.template)
        source = self.template / "roles/task-manager/ROLE.md"
        os.link(source, self.root / "aliased-role.md")
        original = file_inventory(self.root)
        with self.assertRaisesRegex(engine.UpdateError, "non-aliased"):
            self.apply()
        self.assertEqual(original, file_inventory(self.root))

    def test_case_transition_never_replaces_an_appearing_empty_destination(self):
        lowercase_owned_template(self.root, self.template)
        original = file_inventory(self.template)
        rename = engine.rename_role_directory
        appeared = {}
        def competing_directory(source, destination):
            if source.name == "roles":
                destination.mkdir()
                appeared["path"] = destination
                appeared["inode"] = destination.stat().st_ino
            return rename(source, destination)
        with patch.object(engine, "rename_role_directory", side_effect=competing_directory):
            with self.assertRaises(OSError):
                self.apply()
        self.assertEqual(original, file_inventory(self.template))
        self.assertEqual(appeared["inode"], appeared["path"].stat().st_ino)
        self.assertEqual([], list(appeared["path"].iterdir()))
        self.assertEqual(["roles"], engine.role_case_entries(self.template))
        # Removing only the empty directory created by this fixture allows recovery.
        appeared["path"].rmdir()
        self.assertTrue(self.apply()["recovered"])

    def interrupt_case_transition(self, boundary):
        rename, write, unlink = engine.rename_role_directory, engine.atomic_write, Path.unlink
        hops = 0
        def interrupted_rename(source, destination):
            nonlocal hops
            if Path(source).parent == self.template and Path(source).name in {"roles", *[p.name for p in self.template.glob(".template-roles-case-*")]}:
                hops += 1
                if boundary == "before-rename" and hops == 1:
                    raise OSError("injected case transition interruption")
                result = rename(source, destination)
                if boundary == f"after-hop-{hops}":
                    raise OSError("injected case transition interruption")
                return result
            return rename(source, destination)
        def interrupted_write(path, data, mode=0o644):
            if boundary == "content" and path == self.template / "Roles/task-manager/ROLE.md":
                raise OSError("injected case transition interruption")
            result = write(path, data, mode)
            if boundary == "state" and path == self.root / engine.STATE:
                raise OSError("injected case transition interruption")
            return result
        def interrupted_unlink(path, *args, **kwargs):
            if boundary == "cleanup" and path == self.root / engine.PENDING:
                raise OSError("injected case transition interruption")
            return unlink(path, *args, **kwargs)
        with patch.object(engine, "rename_role_directory", side_effect=interrupted_rename), patch.object(engine, "atomic_write", side_effect=interrupted_write), patch.object(Path, "unlink", interrupted_unlink):
            with self.assertRaisesRegex(OSError, "injected case transition"):
                self.apply()
        self.assertTrue((self.root / engine.PENDING).exists())

    def test_case_transition_recovers_each_rename_and_publication_boundary(self):
        for boundary in ("before-rename", "after-hop-1", "after-hop-2", "content", "state", "cleanup"):
            with self.subTest(boundary=boundary), tempfile.TemporaryDirectory() as temporary:
                saved_root, saved_template = self.root, self.template
                self.root = Path(temporary).resolve()
                self.template = fixture(self.root)
                try:
                    raw_state = lowercase_owned_template(self.root, self.template)
                    role = self.root / "ROLES-depo/task-manager-ROLE.md"
                    role.write_bytes(role.read_bytes() + b"\nA reviewed source update accompanies the rename.\n")
                    self.interrupt_case_transition(boundary)
                    original = file_inventory(self.root)
                    with self.assertRaisesRegex(engine.UpdateError, "interrupted"):
                        engine.update(self.root, "check")
                    self.assertEqual(original, file_inventory(self.root))
                    archives = list((self.root / engine.CONTROL / "role-layout-history").glob("*.json"))
                    self.assertEqual(raw_state, base64.b64decode(json.loads(archives[0].read_bytes())["before_state"]))
                    self.assertTrue(self.apply()["recovered"])
                    self.assertEqual(["Roles"], engine.role_case_entries(self.template))
                    self.assertFalse(list(self.template.glob(".template-roles-case-*")))
                    self.assertEqual(role.read_bytes(), (self.template / "Roles/task-manager/ROLE.md").read_bytes())
                    self.assertFalse((self.root / engine.PENDING).exists())
                    self.assertEqual("current", self.apply()["status"])
                finally:
                    self.root, self.template = saved_root, saved_template

    def test_case_recovery_refuses_new_destination_changed_bytes_and_forged_receipt(self):
        lowercase_owned_template(self.root, self.template)
        self.interrupt_case_transition("after-hop-1")
        pending_path = self.root / engine.PENDING
        pending_raw = pending_path.read_bytes()
        pending = json.loads(pending_raw)
        temporary = self.template / pending["role_case_transition"]["preview"]["temporary"]
        (self.template / "Roles").mkdir()
        original = file_inventory(self.root)
        with self.assertRaisesRegex(engine.UpdateError, "ambiguous directories"):
            self.apply()
        self.assertEqual(original, file_inventory(self.root))
        (self.template / "Roles").rmdir()
        role = temporary / "task-manager/ROLE.md"
        saved = role.read_bytes()
        role.write_bytes(saved + b"\nUnreviewed concurrent change.\n")
        original = file_inventory(self.root)
        with self.assertRaisesRegex(engine.UpdateError, "tree changed before rename"):
            self.apply()
        self.assertEqual(original, file_inventory(self.root))
        role.write_bytes(saved)
        for mutation in ("missing", "payload", "identity"):
            corrupt = json.loads(pending_raw)
            if mutation == "missing":
                corrupt.pop("role_case_transition")
            elif mutation == "payload":
                corrupt["role_case_transition"]["payloads"]["task-manager/ROLE.md"] = base64.b64encode(b"Wrong archive").decode()
            else:
                corrupt["role_case_transition"]["preview"]["directory_identity"]["inode"] += 1
            pending_path.write_bytes(engine.encoded(corrupt))
            original = file_inventory(self.template)
            with self.assertRaises(engine.UpdateError):
                self.apply()
            self.assertEqual(original, file_inventory(self.template))
        pending_path.write_bytes(pending_raw)
        self.assertTrue(self.apply()["recovered"])

    def test_case_recovery_rejects_replaced_directory_even_with_identical_bytes(self):
        lowercase_owned_template(self.root, self.template)
        self.interrupt_case_transition("after-hop-1")
        pending = json.loads((self.root / engine.PENDING).read_bytes())
        temporary = self.template / pending["role_case_transition"]["preview"]["temporary"]
        saved = self.root / "retained-original-role-tree"
        temporary.rename(saved)
        shutil.copytree(saved, temporary)
        original = file_inventory(self.root)
        with self.assertRaisesRegex(engine.UpdateError, "directory identity changed"):
            self.apply()
        self.assertEqual(original, file_inventory(self.root))

    def test_role_index_is_generated_bound_and_customization_protected(self):
        self.apply()
        state = engine.load_state(self.root)
        entry = state["files"][engine.ROLE_INDEX]
        self.assertEqual("role-index-v1", entry["generated"]["kind"])
        self.assertEqual(engine.role_index_inputs(state["files"]), entry["generated"]["inputs"])
        original = (self.template / engine.ROLE_INDEX).read_bytes()
        self.assertEqual(original, engine.snapshot(self.root)["generated"][engine.ROLE_INDEX])
        role = self.root / "ROLES-depo/task-manager-ROLE.md"
        role.write_bytes(role.read_bytes() + b"\nAdditional bounded fixture duty.\n")
        self.assertIn(engine.ROLE_INDEX, engine.update(self.root, "check")["updates"])
        self.apply()
        self.assertNotEqual(original, (self.template / engine.ROLE_INDEX).read_bytes())
        (self.template / engine.ROLE_INDEX).write_text("Project-owned navigation\n")
        with self.assertRaises(engine.UpdateError):
            self.apply()
        self.assertEqual("Project-owned navigation\n", (self.template / engine.ROLE_INDEX).read_text())

    def test_invalid_role_and_static_index_mapping_fail_without_template_writes(self):
        role = self.root / "ROLES-depo/task-manager-ROLE.md"
        good = role.read_bytes()
        role.write_text("invalid role")
        with self.assertRaisesRegex(engine.UpdateError, "role pairs"):
            self.apply()
        self.assertEqual({}, file_inventory(self.template))
        role.write_bytes(good)
        manifest = json.loads((self.root / engine.MANIFEST).read_bytes())
        for destination in ("Roles/INDEX.md", "Roles/index.md", "Roles/INDEX.md/child.md"):
            manifest["mirrors"]["ROLES-depo/task-manager-ROLE.md"] = destination
            put(self.root, engine.MANIFEST, json.dumps(manifest))
            with self.assertRaisesRegex(engine.UpdateError, "generated|collision"):
                self.apply()
            self.assertEqual({}, file_inventory(self.template))

    def test_generated_index_cannot_omit_an_unmanaged_destination_role(self):
        self.apply()
        owned = self.template / "Roles/local-worker"
        shutil.copytree(self.template / "Roles/project-sub-agent", owned)
        role = owned / "ROLE.md"
        role.write_text(role.read_text().replace("name: project-sub-agent", "name: local-worker"))
        before = file_inventory(self.template)
        with self.assertRaises(engine.UpdateError) as caught:
            self.apply()
        self.assertTrue(any("unmanaged role directory" in error for error in caught.exception.report["conflicts"]))
        self.assertEqual(before, file_inventory(self.template))

    def test_pending_generated_bytes_are_validated_against_frozen_inputs(self):
        import base64
        self.apply()
        before = engine.load_state(self.root)
        role = self.root / "ROLES-depo/task-manager-ROLE.md"
        role.write_bytes(role.read_bytes() + b"\nChanged bounded fixture duty.\n")
        snap = engine.snapshot(self.root)
        pending = engine.make_pending(before, snap)
        corrupted = json.loads(json.dumps(pending))
        fake = b"Forged index\n"
        corrupted["payloads"][engine.ROLE_INDEX] = base64.b64encode(fake).decode()
        corrupted["after"]["files"][engine.ROLE_INDEX]["sha256"] = engine.digest(fake)
        original = file_inventory(self.template)
        with self.assertRaisesRegex(engine.UpdateError, "frozen role pairs"):
            engine.recover(self.root, corrupted)
        self.assertEqual(original, file_inventory(self.template))
        engine.atomic_write(self.root / engine.PENDING, engine.encoded(pending))
        # Saved payloads, not a later depot edition, govern recovery.
        role.write_bytes(role.read_bytes() + b"\nA later unrelated source edit.\n")
        engine.recover(self.root, pending)
        self.assertEqual(snap["generated"][engine.ROLE_INDEX], (self.template / engine.ROLE_INDEX).read_bytes())
        self.assertFalse((self.root / engine.PENDING).exists())

    def test_legacy_state_transition_retains_exact_pairs_before_interruption(self):
        import base64
        self.apply()
        before = engine.load_state(self.root)
        for name in list(before["files"]):
            if name.startswith("Roles/task-manager/") or name == engine.ROLE_INDEX:
                before["files"].pop(name)
                (self.template / name).unlink()
            elif name.startswith("Roles/project-sub-agent/"):
                legacy = name.replace("Roles/", "sub-agent-roles/", 1)
                before["files"][legacy] = before["files"].pop(name)
                (self.template / legacy).parent.mkdir(parents=True, exist_ok=True)
                (self.template / name).rename(self.template / legacy)
        (self.template / "Roles/project-sub-agent").rmdir()
        (self.template / "Roles/task-manager").rmdir()
        (self.template / "Roles").rmdir()
        engine.atomic_write(self.root / engine.STATE, engine.encoded(before))
        old = {name: (self.template / name).read_bytes() for name in before["files"] if name.startswith("sub-agent-roles/")}
        preview = engine.update(self.root, "check")
        self.assertEqual(set(old), {entry["legacy"] for entry in preview["role_retirements"]})
        write = engine.atomic_write
        def interrupted(path, raw, mode=0o644):
            if path == self.template / "Roles/project-sub-agent/ROLE.md":
                raise OSError("injected role transition interruption")
            return write(path, raw, mode)
        with patch.object(engine, "atomic_write", side_effect=interrupted), self.assertRaises(OSError):
            self.apply()
        archives = list((self.root / engine.CONTROL / "role-layout-history").glob("*.json"))
        self.assertEqual(1, len(archives))
        retained = json.loads(archives[0].read_bytes())
        self.assertEqual(old, {name: base64.b64decode(raw) for name, raw in retained["payloads"].items()})
        result = self.apply()
        self.assertTrue(result["recovered"])
        self.assertFalse((self.template / "sub-agent-roles").exists())
        self.assertEqual("current", engine.update(self.root, "check")["status"])

    def test_check_is_read_only_and_noop_apply_preserves_mtimes(self) -> None:
        before = file_inventory(self.root)
        self.assertEqual("outdated", engine.update(self.root, "check")["status"])
        self.assertEqual(before, file_inventory(self.root))
        self.assertFalse((self.root / ".sys4ai").exists())
        self.assertEqual("applied", self.apply()["status"])
        tracked = [self.root / engine.STATE, *self.template.rglob("*")]
        mtimes = {item: item.stat().st_mtime_ns for item in tracked}
        self.assertEqual("current", engine.update(self.root, "check")["status"])
        self.assertEqual("current", self.apply()["status"])
        self.assertEqual(mtimes, {item: item.stat().st_mtime_ns for item in tracked})

    def test_add_edit_and_delete_skill_packages(self) -> None:
        self.apply()
        add_skill(self.root, "new-skill")
        report = self.apply()
        target = ".agents/skills/new-skill/scripts/example.py"
        self.assertIn(target, report["additions"])
        put(self.root, "SKILLS-depo/new-skill/scripts/example.py", "answer = 43\n")
        self.assertIn(target, self.apply()["updates"])
        self.assertEqual("answer = 43\n", (self.template / target).read_text())
        shutil.rmtree(self.root / "SKILLS-depo/new-skill")
        self.assertIn(target, self.apply()["deletions"])
        self.assertFalse((self.template / ".agents/skills/new-skill").exists())
        self.assertEqual("current", engine.update(self.root, "check")["status"])

    def test_other_collections_keep_active_and_reference_destinations(self) -> None:
        for collection in ("SKILLS-depo", "SOULS-depo", "ROLES-depo", "AGENTS-depo", "SPECS-depo", "EXAMPLES-depo"):
            put(self.root, collection + "/notes.md", collection + " notes\n")
        self.apply()
        state = engine.load_state(self.root)
        for collection in state["collections"]:
            target = self.template / "reference-assets" / collection / "notes.md"
            self.assertEqual(collection + " notes\n", target.read_text())
        self.assertFalse((self.template / "reference-assets/SOULS-depo/SOUL.md").exists())
        self.assertEqual((self.root / "SOULS-depo/SOUL.md").read_bytes(), (self.template / "SOUL.md").read_bytes())
        self.assertEqual(
            (self.template / ".template/baseline-assets.json").read_bytes(),
            (self.template / ".agents/skills/init-new-project/assets/baseline-assets.json").read_bytes(),
        )
        (self.root / "EXAMPLES-depo/notes.md").unlink()
        self.assertIn("reference-assets/EXAMPLES-depo/notes.md", self.apply()["deletions"])

    def test_license_collection_maps_to_template_root_and_preserves_projects(self) -> None:
        policy = json.loads((self.root / engine.MANIFEST).read_text())
        names = ("LICENSE", "LICENSE-CODE", "LICENSE-DOCS")
        for name in names:
            put(self.root, "LICENSES-depo/" + name, "License fixture " + name + "\n")
            policy["overrides"]["LICENSES-depo/" + name] = name
        put(self.root, engine.MANIFEST, json.dumps(policy))
        product = put(self.root, "Projects/Existing/LICENSE", "Existing project terms\n")
        root_license = put(self.root, "LICENSE", "Active root terms\n")
        self.apply()
        state = engine.load_state(self.root)
        self.assertIn("LICENSES-depo", state["collections"])
        for name in names:
            self.assertEqual((self.root / "LICENSES-depo" / name).read_bytes(),
                             (self.template / name).read_bytes())
            self.assertEqual("LICENSES-depo/" + name, state["files"][name]["source"])
            self.assertFalse((self.template / "reference-assets/LICENSES-depo" / name).exists())
        put(self.root, "LICENSES-depo/LICENSE-CODE", "Revised code fixture\n")
        self.assertIn("LICENSE-CODE", self.apply()["updates"])
        self.assertEqual("Existing project terms\n", product.read_text())
        self.assertEqual("Active root terms\n", root_license.read_text())
        (self.root / "LICENSES-depo/LICENSE-DOCS").unlink()
        before = file_inventory(self.template)
        with self.assertRaises(engine.UpdateError):
            engine.update(self.root, "apply")
        self.assertEqual(before, file_inventory(self.template))

    def test_explicit_mappings_require_valid_safe_sources(self) -> None:
        manifest = json.loads((self.root / engine.MANIFEST).read_bytes())
        origin = "EXAMPLES-depo/example.py"
        manifest["overrides"][origin] = "examples/example.py"
        put(self.root, engine.MANIFEST, json.dumps(manifest))
        with self.assertRaisesRegex(engine.UpdateError, "mapped source is missing"):
            self.apply()
        candidate = put(self.root, origin, "def unfinished(\n")
        with self.assertRaisesRegex(engine.UpdateError, "invalid Python"):
            self.apply()
        candidate.unlink()
        candidate.symlink_to(self.root / "SKILLS-depo/task/scripts/example.py")
        with self.assertRaisesRegex(engine.UpdateError, "symbolic link"):
            self.apply()
        self.assertEqual({}, file_inventory(self.template))

    def test_policy_requires_schema2(self) -> None:
        for version in (1, 3, 2.0, True):
            with self.subTest(version=version):
                put(self.root, "SKILLS-depo/init-new-project/assets/baseline-assets.json",
                    json.dumps({"schema_version": version}))
                with self.assertRaisesRegex(engine.UpdateError, "schema 2"):
                    self.apply()
                self.assertEqual({}, file_inventory(self.template))

    def retired_collection(self) -> dict[str, str]:
        put(self.root, "EXAMPLES-depo/a.md", "First example\n")
        put(self.root, "EXAMPLES-depo/b.md", "Second example\n")
        self.apply()
        options = {
            "retire_collection": "EXAMPLES-depo",
            "expected_state_sha256": engine.file_hash(self.root / engine.STATE),
        }
        shutil.rmtree(self.root / "EXAMPLES-depo")
        return options

    def test_retirement_preview_apply_and_normal_rerun(self) -> None:
        options = self.retired_collection()
        personal = put(self.template, "reference-assets/EXAMPLES-depo/personal.md", "Keep me\n")
        before = file_inventory(self.root)
        preview = engine.update(self.root, "check", **options)
        expected = ["reference-assets/EXAMPLES-depo/a.md", "reference-assets/EXAMPLES-depo/b.md"]
        self.assertEqual("outdated", preview["status"])
        self.assertEqual(expected, preview["deletions"])
        self.assertEqual(expected, preview["retired_destinations"])
        self.assertEqual(before, file_inventory(self.root))
        result = engine.update(self.root, "apply", **options)
        self.assertEqual("applied", result["status"])
        self.assertEqual("EXAMPLES-depo", result["retired_collection"])
        self.assertNotIn("EXAMPLES-depo", engine.load_state(self.root)["collections"])
        for target in expected:
            self.assertFalse((self.template / target).exists())
        self.assertEqual("Keep me\n", personal.read_text())
        self.assertFalse((self.root / engine.PENDING).exists())
        self.assertEqual("current", self.apply()["status"])
        self.assertEqual("current", engine.update(self.root, "check")["status"])

    def test_retirement_requires_paired_flags_and_raw_current_digest(self) -> None:
        options = self.retired_collection()
        before = file_inventory(self.root)
        for arguments in (
            {"retire_collection": "EXAMPLES-depo"},
            {"expected_state_sha256": options["expected_state_sha256"]},
            {**options, "expected_state_sha256": "0" * 64},
            {**options, "expected_state_sha256": "invalid"},
            {**options, "retire_collection": "../EXAMPLES-depo"},
            {**options, "retire_collection": "UNKNOWN-depo"},
        ):
            with self.subTest(arguments=arguments):
                with self.assertRaises(engine.UpdateError):
                    engine.update(self.root, "apply", **arguments)
                self.assertEqual(before, file_inventory(self.root))
        state = self.root / engine.STATE
        state.write_text(json.dumps(json.loads(state.read_bytes())))
        with self.assertRaisesRegex(engine.UpdateError, "state digest is stale"):
            engine.update(self.root, "apply", **options)
        options["expected_state_sha256"] = engine.file_hash(state)
        self.assertEqual("applied", engine.update(self.root, "apply", **options)["status"])

    def test_retirement_rejects_present_collection_and_remaining_mapping(self) -> None:
        options = self.retired_collection()
        (self.root / "EXAMPLES-depo").mkdir()
        with self.assertRaisesRegex(engine.UpdateError, "must be absent"):
            engine.update(self.root, "apply", **options)
        (self.root / "EXAMPLES-depo").rmdir()
        manifest = json.loads((self.root / engine.MANIFEST).read_bytes())
        manifest["mirrors"]["EXAMPLES-depo/a.md"] = "example.md"
        put(self.root, engine.MANIFEST, json.dumps(manifest))
        with self.assertRaisesRegex(engine.UpdateError, "mapped source is missing"):
            engine.update(self.root, "apply", **options)
        self.assertTrue((self.template / "reference-assets/EXAMPLES-depo/a.md").is_file())
        self.assertFalse((self.root / engine.PENDING).exists())

    def test_retirement_rechecks_raw_digest_before_publishing(self) -> None:
        options = self.retired_collection()
        before = file_inventory(self.template)
        original = engine.snapshot
        calls = 0

        def changing(root):
            nonlocal calls
            result = original(root)
            calls += 1
            if calls == 2:
                state = root / engine.STATE
                state.write_text(json.dumps(json.loads(state.read_bytes())))
            return result

        with patch.object(engine, "snapshot", side_effect=changing):
            with self.assertRaisesRegex(engine.UpdateError, "digest changed during preflight"):
                engine.update(self.root, "apply", **options)
        self.assertEqual(before, file_inventory(self.template))
        self.assertFalse((self.root / engine.PENDING).exists())

    def test_retirement_rejects_another_missing_collection_or_disconnected_roots(self) -> None:
        put(self.root, "EXTRAS-depo/notes.md", "Other collection\n")
        options = self.retired_collection()
        shutil.rmtree(self.root / "EXTRAS-depo")
        before = file_inventory(self.template)
        with self.assertRaisesRegex(engine.UpdateError, "unexpected missing source collection"):
            engine.update(self.root, "apply", **options)
        self.assertEqual(before, file_inventory(self.template))
        missing = self.root / "disconnected-volume"
        with self.assertRaisesRegex(engine.UpdateError, "root is missing"):
            engine.update(missing, "apply", **options)
        self.assertFalse(missing.exists())
        moved = self.template.with_name("moved-template")
        self.template.rename(moved)
        with self.assertRaisesRegex(engine.UpdateError, "template directory is missing"):
            engine.update(self.root, "apply", **options)
        self.assertFalse(self.template.exists())
        self.assertEqual(before, file_inventory(moved))

    def test_retirement_rejects_customized_or_already_missing_destinations(self) -> None:
        options = self.retired_collection()
        target = self.template / "reference-assets/EXAMPLES-depo/a.md"
        target.write_text("Customized\n")
        for remove in (False, True):
            if remove:
                target.unlink()
            before = file_inventory(self.template)
            with self.assertRaisesRegex(engine.UpdateError, "conflicts"):
                engine.update(self.root, "apply", **options)
            self.assertEqual(before, file_inventory(self.template))
            self.assertFalse((self.root / engine.PENDING).exists())

    def test_retirement_rejects_remapped_targets_and_unsafe_destination_parents(self) -> None:
        options = self.retired_collection()
        manifest = json.loads((self.root / engine.MANIFEST).read_bytes())
        original = json.dumps(manifest)
        manifest["mirrors"]["SOULS-depo/SOUL.md"] = "reference-assets/EXAMPLES-depo/a.md"
        put(self.root, engine.MANIFEST, json.dumps(manifest))
        with self.assertRaisesRegex(engine.UpdateError, "must not be remapped"):
            engine.update(self.root, "apply", **options)
        put(self.root, engine.MANIFEST, original)
        folder = self.template / "reference-assets/EXAMPLES-depo"
        outside = self.root / "outside"
        folder.rename(outside)
        folder.symlink_to(outside, target_is_directory=True)
        before = file_inventory(outside)
        with self.assertRaises(engine.UpdateError):
            engine.update(self.root, "apply", **options)
        self.assertEqual(before, file_inventory(outside))

    def interrupt_retirement(self, *, after_state: bool = False) -> dict[str, str]:
        options = self.retired_collection()
        original = Path.unlink
        interrupt = self.root / engine.PENDING if after_state else self.template / "reference-assets/EXAMPLES-depo/b.md"

        def interrupted(path, *args, **kwargs):
            if path == interrupt:
                raise OSError("simulated retirement interruption")
            return original(path, *args, **kwargs)

        with patch.object(Path, "unlink", interrupted):
            with self.assertRaisesRegex(OSError, "simulated retirement interruption"):
                engine.update(self.root, "apply", **options)
        self.assertFalse((self.template / "reference-assets/EXAMPLES-depo/a.md").exists())
        self.assertTrue((self.root / engine.PENDING).exists())
        return options

    def test_interrupted_retirement_requires_ordinary_apply_and_recovers(self) -> None:
        options = self.interrupt_retirement()
        pending = json.loads((self.root / engine.PENDING).read_bytes())
        self.assertEqual(options["expected_state_sha256"], pending["retirement"]["state_sha256"])
        before = file_inventory(self.root)
        with self.assertRaisesRegex(engine.UpdateError, "ordinary apply"):
            engine.update(self.root, "apply", **options)
        with self.assertRaisesRegex(engine.UpdateError, "interrupted"):
            engine.update(self.root, "check")
        self.assertEqual(before, file_inventory(self.root))
        result = self.apply()
        self.assertTrue(result["recovered"])
        self.assertFalse((self.root / engine.PENDING).exists())
        self.assertFalse((self.template / "reference-assets/EXAMPLES-depo").exists())
        self.assertEqual("current", self.apply()["status"])

    def test_retirement_recovers_after_state_publication_with_original_digest(self) -> None:
        options = self.interrupt_retirement(after_state=True)
        self.assertNotEqual(options["expected_state_sha256"], engine.file_hash(self.root / engine.STATE))
        self.assertTrue(self.apply()["recovered"])
        self.assertFalse((self.root / engine.PENDING).exists())
        self.assertEqual("current", engine.update(self.root, "check")["status"])

    def test_retirement_recovery_requires_intact_retirement_record(self) -> None:
        self.interrupt_retirement()
        pending_path = self.root / engine.PENDING
        original = json.loads(pending_path.read_bytes())
        before = file_inventory(self.template)
        for retirement in (None, {"collection": "EXAMPLES-depo"},
                           {"collection": "EXAMPLES-depo", "state_sha256": "0" * 64}):
            document = dict(original)
            if retirement is None:
                del document["retirement"]
            else:
                document["retirement"] = retirement
            pending_path.write_text(json.dumps(document))
            with self.assertRaises(engine.UpdateError):
                self.apply()
            self.assertEqual(before, file_inventory(self.template))
            self.assertTrue(pending_path.exists())
        pending_path.write_text(json.dumps(original))
        self.assertTrue(self.apply()["recovered"])

    def test_retirement_recovery_rechecks_surviving_sources_and_destination_bytes(self) -> None:
        put(self.root, "EXTRAS-depo/notes.md", "Other collection\n")
        self.interrupt_retirement()
        extras = self.root / "EXTRAS-depo"
        extras.rename(self.root / "saved-extras")
        with self.assertRaisesRegex(engine.UpdateError, "unexpected missing source collection"):
            self.apply()
        (self.root / "saved-extras").rename(extras)
        target = self.template / "reference-assets/EXAMPLES-depo/b.md"
        target.write_text("Changed after interruption\n")
        before = file_inventory(self.root)
        with self.assertRaisesRegex(engine.UpdateError, "recovery conflict"):
            self.apply()
        self.assertEqual(before, file_inventory(self.root))

    def test_retirement_cli_previews_exact_deletions(self) -> None:
        options = self.retired_collection()
        result = subprocess.run([
            sys.executable, str(HELPER), "--project-root", str(self.root), "check",
            "--retire-collection", options["retire_collection"],
            "--expected-state-sha256", options["expected_state_sha256"],
        ], capture_output=True, text=True)
        self.assertEqual(1, result.returncode, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual("EXAMPLES-depo", report["retired_collection"])
        self.assertEqual(report["deletions"], report["retired_destinations"])
        self.assertFalse((self.root / engine.PENDING).exists())

    def test_adopts_identical_files_and_preserves_unmanaged_files(self) -> None:
        shutil.copyfile(self.root / "SOULS-depo/SOUL.md", self.template / "SOUL.md")
        put(self.template, "README.md", "Template's own README\n")
        put(self.template, "work/personal.txt", "Keep this\n")
        report = self.apply()
        self.assertIn("SOUL.md", report["adoptions"])
        put(self.root, "SOULS-depo/SOUL.md", "# Updated soul\n")
        self.apply()
        self.assertEqual("Template's own README\n", (self.template / "README.md").read_text())
        self.assertEqual("Keep this\n", (self.template / "work/personal.txt").read_text())

    def test_unmanaged_difference_blocks_all_writes(self) -> None:
        put(self.template, "SOUL.md", "Custom\n")
        before = file_inventory(self.template)
        with self.assertRaisesRegex(engine.UpdateError, "conflicts"):
            self.apply()
        self.assertEqual(before, file_inventory(self.template))
        self.assertFalse((self.root / engine.STATE).exists())
        self.assertFalse((self.root / engine.PENDING).exists())

    def test_managed_customization_blocks_updates_and_deletions(self) -> None:
        add_skill(self.root, "optional")
        self.apply()
        put(self.template, ".agents/skills/optional/scripts/example.py", "custom = True\n")
        shutil.rmtree(self.root / "SKILLS-depo/optional")
        put(self.root, "SOULS-depo/SOUL.md", "# New soul\n")
        before = file_inventory(self.template)
        with self.assertRaisesRegex(engine.UpdateError, "conflicts"):
            self.apply()
        self.assertEqual(before, file_inventory(self.template))

    def test_invalid_partial_skill_and_python_edits_do_not_publish(self) -> None:
        self.apply()
        before = file_inventory(self.template)
        header = self.root / "SKILLS-depo/task/SKILL.md"
        saved = header.read_text()
        for invalid in ("---\nname: task\n", "---\nname: other\ndescription: Test\n---\n", "---\nname: task\ndescription: \n---\n"):
            header.write_text(invalid)
            with self.assertRaises(engine.UpdateError):
                self.apply()
            self.assertEqual(before, file_inventory(self.template))
        header.write_text(saved)
        put(self.root, "SKILLS-depo/task/scripts/example.py", "def broken(\n")
        with self.assertRaisesRegex(engine.UpdateError, "invalid Python"):
            self.apply()
        self.assertEqual(before, file_inventory(self.template))

    def test_partial_new_package_and_removed_baseline_are_rejected(self) -> None:
        self.apply()
        put(self.root, "SKILLS-depo/unfinished/README.md", "Working\n")
        with self.assertRaisesRegex(engine.UpdateError, "incomplete skill"):
            self.apply()
        shutil.rmtree(self.root / "SKILLS-depo/unfinished")
        shutil.rmtree(self.root / "SKILLS-depo/task")
        with self.assertRaisesRegex(engine.UpdateError, "governance source is missing"):
            self.apply()
        self.assertTrue((self.template / ".agents/skills/task/SKILL.md").exists())

    def test_partial_json_policy_and_unterminated_skill_metadata_are_rejected(self) -> None:
        self.apply()
        before = file_inventory(self.template)
        policy = self.root / "SKILLS-depo/init-new-project/assets/baseline-assets.json"
        saved = policy.read_bytes()
        policy.write_text('{"schema_version":')
        with self.assertRaisesRegex(engine.UpdateError, "invalid JSON source"):
            self.apply()
        self.assertEqual(before, file_inventory(self.template))
        policy.write_text('{"schema_version": 1}')
        with self.assertRaisesRegex(engine.UpdateError, "schema 2"):
            self.apply()
        policy.write_bytes(saved)
        put(self.root, "SKILLS-depo/task/SKILL.md", '---\nname: "task\ndescription: Test\n---\n')
        with self.assertRaisesRegex(engine.UpdateError, "unterminated"):
            self.apply()
        self.assertEqual(before, file_inventory(self.template))

    def test_missing_collection_or_template_is_not_treated_as_deletion(self) -> None:
        put(self.root, "EXAMPLES-depo/notes.md", "Example\n")
        self.apply()
        shutil.rmtree(self.root / "EXAMPLES-depo")
        with self.assertRaisesRegex(engine.UpdateError, "conflicts"):
            self.apply()
        self.assertTrue((self.template / "reference-assets/EXAMPLES-depo/notes.md").exists())
        missing = self.root / "absent-volume"
        with self.assertRaisesRegex(engine.UpdateError, "root is missing"):
            engine.update(missing, "apply")
        self.assertFalse(missing.exists())
        self.template.rename(self.template.with_name("moved-template"))
        with self.assertRaisesRegex(engine.UpdateError, "template directory is missing"):
            self.apply()
        self.assertFalse(self.template.exists())

    def test_transients_and_credential_files_are_excluded(self) -> None:
        for name in (".env", ".env.local", "credentials.json", "client.key", "debug.log", ".DS_Store", "bundle.zip", "__pycache__/x.pyc", ".venv/bin/python", "models/weights.bin"):
            put(self.root, "SKILLS-depo/task/" + name, "Excluded\n")
        self.apply()
        self.assertEqual({"SKILL.md", "scripts/example.py"}, set(file_inventory(self.template / ".agents/skills/task")))

    def test_symlinks_and_special_files_are_rejected(self) -> None:
        link = self.root / "SOULS-depo/link.md"
        link.symlink_to(self.root / "SOULS-depo/SOUL.md")
        with self.assertRaisesRegex(engine.UpdateError, "symbolic link"):
            self.apply()
        link.unlink()
        os.mkfifo(link)
        with self.assertRaisesRegex(engine.UpdateError, "non-regular"):
            self.apply()
        link.unlink()
        outside = self.root / "outside"
        outside.mkdir()
        (self.template / "reference-assets").symlink_to(outside, target_is_directory=True)
        put(self.root, "SPECS-depo/notes.md", "Note\n")
        with self.assertRaises(engine.UpdateError):
            self.apply()
        self.assertEqual({}, file_inventory(outside))

    def test_deleted_source_cannot_escape_via_changed_destination_parent(self) -> None:
        put(self.root, "EXAMPLES-depo/notes.md", "Example\n")
        self.apply()
        (self.root / "EXAMPLES-depo/notes.md").unlink()
        folder = self.template / "reference-assets/EXAMPLES-depo"
        outside = self.root / "outside"
        folder.rename(outside)
        folder.symlink_to(outside, target_is_directory=True)
        with self.assertRaises(engine.UpdateError):
            self.apply()
        self.assertEqual("Example\n", (outside / "notes.md").read_text())

    def test_traversal_and_destination_collisions_are_rejected(self) -> None:
        original = (self.root / engine.MANIFEST).read_bytes()
        for target in ("../../escape", "/absolute", ".git/config", "SOUL.md"):
            manifest = json.loads(original)
            manifest["mirrors"]["SOULS-depo/SOUL.md"] = target
            put(self.root, engine.MANIFEST, json.dumps(manifest))
            with self.assertRaises(engine.UpdateError):
                self.apply()
            self.assertEqual({}, file_inventory(self.template))

    def test_shared_initializer_lock_blocks_apply(self) -> None:
        # The updater's readonly path acquires the same shared flock as the initializer.
        with engine.locked(self.root):
            with self.assertRaisesRegex(engine.UpdateError, "busy"):
                self.apply()
        with engine.locked(self.root, readonly=True):
            with self.assertRaisesRegex(engine.UpdateError, "busy"):
                self.apply()
            self.assertEqual("outdated", engine.update(self.root, "check")["status"])
        self.assertFalse((self.root / engine.STATE).exists())

    def test_source_changing_between_snapshots_blocks_all_template_writes(self) -> None:
        original = engine.snapshot
        calls = 0

        def changing(root):
            nonlocal calls
            result = original(root)
            calls += 1
            if calls == 1:
                put(root, "SOULS-depo/SOUL.md", "# Changed during read\n")
            return result

        with patch.object(engine, "snapshot", side_effect=changing):
            with self.assertRaisesRegex(engine.UpdateError, "source changed"):
                self.apply()
        self.assertEqual({}, file_inventory(self.template))
        self.assertFalse((self.root / engine.PENDING).exists())

    def interrupt_update(self) -> None:
        self.apply()
        put(self.root, "SOULS-depo/SOUL.md", "# Updated soul\n")
        put(self.root, "SPECS-depo/project-template-SPECS.md", "# Updated specs\n")
        original = engine.atomic_write
        writes = 0

        def interrupted(path, data, mode=0o644):
            nonlocal writes
            if self.template in path.parents:
                writes += 1
                if writes == 2:
                    raise OSError("simulated interruption")
            return original(path, data, mode)

        with patch.object(engine, "atomic_write", side_effect=interrupted):
            with self.assertRaisesRegex(OSError, "simulated interruption"):
                self.apply()
        self.assertTrue((self.root / engine.PENDING).is_file())
        self.assertFalse(engine.load_state(self.root)["files"]["SOUL.md"]["sha256"] == engine.file_hash(self.template / "SOUL.md"))

    def test_interrupted_update_recovers_then_processes_new_sources(self) -> None:
        self.interrupt_update()
        before = file_inventory(self.root)
        with self.assertRaisesRegex(engine.UpdateError, "interrupted"):
            engine.update(self.root, "check")
        self.assertEqual(before, file_inventory(self.root))
        put(self.root, "SOULS-depo/SOUL.md", "# A newer source edit\n")
        report = self.apply()
        self.assertTrue(report["recovered"])
        self.assertEqual("# A newer source edit\n", (self.template / "SOUL.md").read_text())
        self.assertEqual("# Updated specs\n", (self.template / "SPECS.md").read_text())
        self.assertFalse((self.root / engine.PENDING).exists())
        self.assertEqual("current", self.apply()["status"])

    def test_recovery_refuses_customized_files_before_resuming(self) -> None:
        self.interrupt_update()
        put(self.template, "SPECS.md", "Custom after interruption\n")
        before = file_inventory(self.template)
        with self.assertRaisesRegex(engine.UpdateError, "recovery conflict"):
            self.apply()
        self.assertEqual(before, file_inventory(self.template))
        self.assertTrue((self.root / engine.PENDING).exists())

    def test_cli_reports_outdated_and_errors_as_json(self) -> None:
        result = subprocess.run([sys.executable, str(HELPER), "--project-root", str(self.root), "check"], capture_output=True, text=True)
        self.assertEqual(1, result.returncode, result.stderr)
        self.assertEqual("outdated", json.loads(result.stdout)["status"])
        put(self.template, "SOUL.md", "Custom\n")
        result = subprocess.run([sys.executable, str(HELPER), "--project-root", str(self.root), "apply"], capture_output=True, text=True)
        self.assertEqual(2, result.returncode, result.stderr)
        self.assertEqual("conflict", json.loads(result.stdout)["status"])


if __name__ == "__main__":
    unittest.main()
