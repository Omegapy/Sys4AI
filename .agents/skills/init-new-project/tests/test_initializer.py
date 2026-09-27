"""Governance setup boundaries and recovery in disposable depot fixtures."""

from __future__ import annotations

import ast
import fcntl
import importlib.util
import json
import os
import select
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SOURCE_SKILL = Path(__file__).resolve().parents[1]
BASELINE = ("curate", "agent-task", "communication", "init-new-project", "manage-subagent-roles",
            "memory", "ontology", "task", "to-implementation-plan", "to-trd", "what-did-you-learn")


def load_helper(skill: Path):
    spec = importlib.util.spec_from_file_location("fixture_initializer", skill / "scripts/init_new_project.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SOURCE_DEPOT = load_helper(SOURCE_SKILL).installed_locations()[0]


def fixture_depot(base: Path) -> Path:
    """Compose a disposable proposed Template before any live adoption.

    The production helper still reads only this fixture's registered Template.
    Tests must not require publishing a new live Template to validate its pending
    initializer. Mapped source bytes form the fixture; unmanaged historical
    starter files retain the existing Template bytes.
    """
    root = base.resolve() / "Sys4AI"
    root.mkdir(parents=True)
    (root / "depot").mkdir()
    (root / "Projects").mkdir()
    template = root / "Projects/Sys4AI-Template-Project"
    template.mkdir()
    ignore = shutil.ignore_patterns("__pycache__", ".DS_Store", "*.pyc")
    for name in BASELINE:
        source = SOURCE_SKILL if name == "init-new-project" else SOURCE_DEPOT / "SKILLS-depo" / name
        shutil.copytree(source, root / "SKILLS-depo" / name, ignore=ignore)
        shutil.copytree(source, template / ".agents/skills" / name, ignore=ignore)
    (root / "SOULS-depo").mkdir()
    shutil.copyfile(SOURCE_DEPOT / "SOULS-depo/SOUL.md", root / "SOULS-depo/SOUL.md")
    shutil.copyfile(root / "SOULS-depo/SOUL.md", template / "SOUL.md")
    policy = json.loads((SOURCE_SKILL / "assets/baseline-assets.json").read_text())
    mapping = json.loads((SOURCE_DEPOT / "depot/template-update.json").read_text())["overrides"]
    mapped = {destination: source for source, destination in mapping.items()}
    mapped.update({"memory.yaml": "MEMORY-depo/starter/memory.yaml",
                   "MEMORY/README.md": "MEMORY-depo/starter/MEMORY/README.md",
                   "ontology-advanced.yaml": "ONTOLOGY-depo/starter/ontology-advanced.yaml",
                   "tools/template_update.py": "SKILLS-depo/init-new-project/assets/template_update.py"})
    mapped.update({"reference-assets/LEARNING-depo/" + path.relative_to(SOURCE_DEPOT / "LEARNING-depo").as_posix():
                   path.relative_to(SOURCE_DEPOT).as_posix()
                   for path in (SOURCE_DEPOT / "LEARNING-depo").rglob("*") if path.is_file()})
    mapped.update({"reference-assets/ONTOLOGY-depo/" + path.relative_to(SOURCE_DEPOT / "ONTOLOGY-depo").as_posix():
                   path.relative_to(SOURCE_DEPOT).as_posix()
                   for path in (SOURCE_DEPOT / "ONTOLOGY-depo").rglob("*") if path.is_file() and "starter" not in path.relative_to(SOURCE_DEPOT / "ONTOLOGY-depo").parts})
    for relative in policy["starter_files"]:
        target = template / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        source = SOURCE_DEPOT / mapped[relative] if relative in mapped else SOURCE_DEPOT / "Projects/Sys4AI-Template-Project" / relative
        shutil.copyfile(source, target)
    # Starter mappings override their reference destinations; only their active
    # MEMORY/README.md and memory.yaml copies belong to this Template edition.
    shutil.copytree(SOURCE_DEPOT / "MEMORY-depo", template / "reference-assets/MEMORY-depo",
                    ignore=shutil.ignore_patterns("__pycache__", ".DS_Store", "*.pyc", "starter"))
    shutil.copytree(SOURCE_DEPOT / "LEARNING-depo", template / "reference-assets/LEARNING-depo", ignore=ignore, dirs_exist_ok=True)
    shutil.copytree(SOURCE_DEPOT / "CURATION-depo", template / "reference-assets/CURATION-depo", ignore=ignore, dirs_exist_ok=True)
    shutil.copytree(SOURCE_DEPOT / "ONTOLOGY-depo", template / "reference-assets/ONTOLOGY-depo",
                    ignore=shutil.ignore_patterns("__pycache__", ".DS_Store", "*.pyc", "starter"), dirs_exist_ok=True)
    for relative, source in mapped.items():
        if relative.startswith(policy["roles"] + "/"):
            target = template / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(SOURCE_DEPOT / source, target)
    role_script = template / ".agents/skills/manage-subagent-roles/scripts/role_catalog.py"
    role_spec = importlib.util.spec_from_file_location("fixture_role_catalog", role_script)
    role_helper = importlib.util.module_from_spec(role_spec)
    sys.modules[role_spec.name] = role_helper
    role_spec.loader.exec_module(role_helper)
    catalog = role_helper.build_catalog(template.resolve(), inspect_index=False)
    assert not catalog.invalid_roles, catalog.invalid_roles
    (template / policy["roles"] / "INDEX.md").write_text(role_helper.render_index(catalog))
    (template / ".template").mkdir()
    for name in ("baseline-assets.json", "project-readme.md"):
        shutil.copyfile(SOURCE_SKILL / "assets" / name, template / ".template" / name)
    registry = json.loads((SOURCE_DEPOT / "depot/projects.json").read_text())
    registry["projects"] = [entry for entry in registry["projects"]
                            if entry["id"] in {"sys4ai-depot", "sys4ai-template-project"}]
    (root / "depot/projects.json").write_text(json.dumps(registry, indent=2) + "\n")
    return root


def remove_ontology_edition(template: Path) -> None:
    """Reconstruct a pre-ontology Template without upgrading its receipt."""
    for name in (".agents/skills/ontology", "reference-assets/ONTOLOGY-depo", "ONTOLOGY"):
        if (template / name).exists():
            shutil.rmtree(template / name)
    if (template / "ontology.yaml").exists():
        (template / "ontology.yaml").unlink()
    for name in ("ontology-advanced.yaml", "tools/template_update.py"):
        if (template / name).exists():
            (template / name).unlink()
    policy = template / ".template/baseline-assets.json"
    data = json.loads(policy.read_text())
    data["starter_files"] = [name for name in data["starter_files"] if name not in {"ontology.yaml", "ontology-advanced.yaml", "tools/template_update.py"} and not name.startswith(("ONTOLOGY/", "reference-assets/ONTOLOGY-depo/"))]
    policy.write_text(json.dumps(data, indent=2) + "\n")


def remove_learning_edition(template: Path) -> None:
    """Remove learning assets when reconstructing an actual earlier Template."""
    remove_ontology_edition(template)
    for name in (".agents/skills/what-did-you-learn", "reference-assets/LEARNING-depo"):
        if (template / name).exists():
            shutil.rmtree(template / name)
    policy = template / ".template/baseline-assets.json"
    data = json.loads(policy.read_text())
    data["starter_files"] = [name for name in data["starter_files"] if not name.startswith("reference-assets/LEARNING-depo/")]
    policy.write_text(json.dumps(data, indent=2) + "\n")


def remove_memory_edition(template: Path) -> None:
    """Reconstruct a pre-memory Template for a historical receipt fixture."""
    remove_learning_edition(template)
    for name in (".agents/skills/memory", "reference-assets/MEMORY-depo", "MEMORY"):
        shutil.rmtree(template / name)
    (template / "memory.yaml").unlink()


def manifest(root: Path) -> dict[str, str]:
    import hashlib
    result = {}
    if root.exists():
        for path in root.rglob("*"):
            name = path.relative_to(root).as_posix()
            if path.is_symlink():
                result[name] = "symlink:" + os.readlink(path)
            elif path.is_file():
                result[name] = hashlib.sha256(path.read_bytes()).hexdigest()
            elif path.is_dir():
                result[name] = "directory"
    return result


class InitializerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="sys4ai-governance-initializer-", dir=os.environ.get("TMPDIR", "/private/tmp"))
        self.addCleanup(self.temporary.cleanup)
        self.root = fixture_depot(Path(self.temporary.name))
        self.helper = load_helper(self.root / "SKILLS-depo/init-new-project")
        self.target = self.root / "Projects/Orchard"
        self.arguments = {"mode": "create", "destination": self.target, "project_id": "orchard",
                          "project_name": "Orchard", "purpose": "Track orchard observations with ORCHARD_FIXTURE_MARKER."}

    def run_setup(self, **overrides):
        report = self.helper.run_initialization(**{**self.arguments, **overrides})
        self.assertEqual("completed", report["status"])
        return report

    def fail_verification(self, **overrides):
        with (patch.object(self.helper, "verify_project", side_effect=self.helper.InitializationError("injected verification failure")),
              self.assertRaises(self.helper.InitializationError) as caught):
            self.helper.run_initialization(**{**self.arguments, **overrides})
        self.assertEqual("verification", caught.exception.report["recovery"]["stage"])
        return caught.exception.report

    def test_forbidden_destinations_leave_every_byte_unchanged(self):
        outside = Path(self.temporary.name) / "outside"
        outside.mkdir()
        link = self.root / "Projects/linked"
        link.symlink_to(outside, target_is_directory=True)
        occupied = self.root / "Projects/Occupied"
        occupied.mkdir()
        (occupied / "owned.txt").write_text("preserve")
        for target in (
            self.root,
            self.root / "Projects",
            self.root / "Projects/Sys4AI-Template-Project",
            self.root / "Projects/Sys4AI-Template-Project/Nested",
            outside / "New",
            link / "New",
            self.root / "Projects/../New",
            occupied,
            Path("Projects/relative"),
        ):
            with self.subTest(target=target):
                before = manifest(self.root)
                with self.assertRaises(self.helper.InitializationError):
                    self.helper.run_initialization(
                        **{**self.arguments, "destination": target}
                    )
                self.assertEqual(before, manifest(self.root))

    def test_invalid_identity_and_duplicate_registration_precede_writes(self):
        self.run_setup()
        for updates in (
            {"project_id": "sys4ai-depot"},
            {"project_id": "UPPER"},
            {"project_id": "bad_id"},
            {"project_name": "Sys4AI Template Project"},
            {"purpose": "token=must-not-write"},
            {"destination": self.root / "Projects/Another"},
            {"project_id": "another"},
        ):
            before = manifest(self.root)
            with (
                self.subTest(updates=updates),
                self.assertRaises(self.helper.InitializationError),
            ):
                self.helper.run_initialization(**{**self.arguments, **updates})
            self.assertEqual(before, manifest(self.root))

    def test_exact_seed_allowlist_ignores_repository_metadata_and_transients(self):
        template = self.root / "Projects/Sys4AI-Template-Project"
        garbage = (
            ".git/objects/history",
            ".gitmodules",
            ".venv/bin/python",
            ".sys4ai/private-state/log",
            "models/weights",
            "unknown.txt",
            ".DS_Store",
            "Roles/project-sub-agent/__pycache__/compiled.pyc",
            "Roles/.transition.json",
            "Roles/task-manager/.transition.json",
            ".sys4ai/role-catalog.lock",
            "Implementation_Plans/old-plan.md",
            "Tasks/old-task/task.json",
        )
        for relative in garbage:
            target = template / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("must not copy")
        (self.root / "SKILLS-depo/future-opt-in").mkdir()
        report = self.run_setup()
        self.assertEqual(
            list(BASELINE),
            sorted(path.name for path in (self.target / ".agents/skills").iterdir()),
        )
        for relative in garbage:
            self.assertFalse((self.target / relative).exists(), relative)
        self.assertFalse((self.target / ".git").exists())
        self.assertNotIn(
            "Sys4AI Template Project", (self.target / "README.md").read_text()
        )
        self.assertIn("ORCHARD_FIXTURE_MARKER", (self.target / "README.md").read_text())
        self.assertEqual(
            (template / "SPECS.md").read_bytes(),
            (self.target / "SPECS.md").read_bytes(),
        )
        self.assertIn("[SPECS.md](./SPECS.md)", (self.target / "README.md").read_text())
        self.assertIn("[SPECS.md](./SPECS.md)", (self.target / "AGENTS.md").read_text())
        self.assertNotIn("## Python environment", (self.target / "README.md").read_text())
        self.assertEqual(
            "not_initialized", report["registry"]["entry"]["repository"]["status"]
        )
        # A template gitfile is excluded just like a metadata directory.
        shutil.rmtree(template / ".git")
        (template / ".git").write_text("gitdir: /fixture-only/no-repository\n")
        other = self.root / "Projects/Second"
        self.run_setup(
            destination=other, project_id="second", project_name="Second"
        )
        self.assertFalse((other / ".git").exists())

    def test_asset_copies_are_complete_pinned_and_do_not_synchronize(self):
        report = self.run_setup()
        for name in BASELINE:
            self.assertEqual(
                self.helper.package_files(self.root / self.helper.TEMPLATE / ".agents/skills" / name),
                self.helper.package_files(self.target / ".agents/skills" / name),
            )
        before = manifest(self.target)
        source = self.root / self.helper.TEMPLATE / ".agents/skills/communication/SKILL.md"
        source.write_text(source.read_text() + "\nLater source edit.\n")
        self.assertEqual(before, manifest(self.target))
        self.assertTrue(
            all(
                len(item["source_sha256"]) == 64
                and len(item["destination_sha256"]) == 64
                for item in report["sources"]
            )
        )

    def test_legacy_private_provider_directories_are_never_copied(self):
        template = self.root / self.helper.TEMPLATE
        excluded_files = []
        for collection in (".agents/skills/communication", "Roles/project-sub-agent", "reference-assets"):
            for private_directory in (".cognee", ".cognee_system"):
                relative = Path(collection) / private_directory / "db.sqlite"
                target = template / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(b"private legacy state must remain in its original project")
                excluded_files.append(relative)
                self.assertTrue(self.helper.excluded(relative), str(relative))
        self.run_setup()
        for relative in excluded_files:
            self.assertFalse((self.target / relative.parent).exists(), str(relative))

    def test_template_assets_and_renderer_win_over_reusable_depot_editions(self):
        template = self.root / self.helper.TEMPLATE
        (self.root / "SOULS-depo/SOUL.md").write_text("unused reusable soul\n")
        (self.root / "SKILLS-depo/communication/SKILL.md").write_text("unused reusable skill\n")
        (self.root / "SKILLS-depo/init-new-project/assets/project-readme.md").write_text("unused renderer\n")
        (template / "SOUL.md").write_text("Template soul selected.\n")
        renderer = template / ".template/project-readme.md"
        renderer.write_text(renderer.read_text() + "\nTEMPLATE_RENDERER_MARKER\n")
        report = self.run_setup()
        self.assertEqual("Template soul selected.\n", (self.target / "SOUL.md").read_text())
        self.assertIn("TEMPLATE_RENDERER_MARKER", (self.target / "README.md").read_text())
        self.assertEqual(
            (template / ".agents/skills/communication/SKILL.md").read_bytes(),
            (self.target / ".agents/skills/communication/SKILL.md").read_bytes(),
        )
        self.assertTrue(all(item["source"].startswith(self.helper.TEMPLATE + "/") for item in report["sources"]))
        self.assertIn(self.helper.TEMPLATE + "/.template/baseline-assets.json", {item["source"] for item in report["sources"]})
        self.assertFalse((self.target / ".template").exists())

    def test_installed_helper_works_when_all_reusable_collections_are_missing(self):
        active = self.root / ".agents/skills/init-new-project"
        shutil.copytree(self.root / "SKILLS-depo/init-new-project", active)
        self.helper = load_helper(active)
        shutil.rmtree(self.root / "SKILLS-depo")
        shutil.rmtree(self.root / "SOULS-depo")
        self.run_setup()
        manual = self.root / "Projects/Manual"
        shutil.copytree(self.root / self.helper.TEMPLATE, manual)
        (manual / "notes.txt").write_text("keep manual notes")
        self.run_setup(mode="prepare-existing", destination=manual, project_id="manual", project_name="Manual")
        self.assertEqual("keep manual notes", (manual / "notes.txt").read_text())
        self.assertFalse((self.root / "SKILLS-depo").exists())
        self.assertFalse((self.root / "SOULS-depo").exists())

    def test_template_package_additions_deletions_roles_and_reference_assets_are_adopted(self):
        template = self.root / self.helper.TEMPLATE
        package = template / ".agents/skills/new-skill"
        package.mkdir()
        (package / "SKILL.md").write_text("---\nname: new-skill\ndescription: Template addition.\n---\nUse this skill.\n")
        (package / "resource.md").write_text("complete added package")
        role = template / "Roles/new-role"
        shutil.copytree(template / "Roles/project-sub-agent", role)
        (role / "reference.md").write_text("complete role reference")
        role_file = role / "ROLE.md"
        role_file.write_text(role_file.read_text().replace("name: project-sub-agent", "name: new-role"))
        inputs = {"SOUL.md": (template / "SOUL.md").read_bytes(), self.helper.ROLE_HELPER: (template / self.helper.ROLE_HELPER).read_bytes()}
        inputs.update({"Roles/" + name: raw for name, raw in self.helper.tree_files(template / "Roles").items() if name != "INDEX.md"})
        (template / "Roles/INDEX.md").write_bytes(self.helper.role_index_bytes(inputs, required=True))
        reference = template / "reference-assets/SOULS-depo/alternative.md"
        reference.parent.mkdir(parents=True)
        reference.write_text("template reference asset")
        self.run_setup()
        self.assertEqual("complete added package", (self.target / ".agents/skills/new-skill/resource.md").read_text())
        self.assertTrue((self.target / ".agents/skills/init-new-project/SKILL.md").is_file())
        self.assertEqual("complete role reference", (self.target / "Roles/new-role/reference.md").read_text())
        self.assertEqual("template reference asset", (self.target / "reference-assets/SOULS-depo/alternative.md").read_text())

    def test_missing_required_template_dependencies_refuse_without_mutation(self):
        template = self.root / self.helper.TEMPLATE
        for relative in (".agents/skills/task", "Roles/project-sub-agent", "AGENTS.md", self.helper.ROLE_HELPER):
            with self.subTest(relative=relative):
                selected = template / relative
                backup = Path(self.temporary.name) / "required-backup"
                selected.rename(backup)
                before = manifest(self.root)
                with self.assertRaises((self.helper.InitializationError, OSError)):
                    self.helper.run_initialization(**self.arguments)
                self.assertEqual(before, manifest(self.root))
                backup.rename(selected)
        policy = template / ".template/baseline-assets.json"
        current = json.loads(policy.read_text())
        current["starter_files"].remove("AGENTS.md")
        policy.write_text(json.dumps(current))
        before = manifest(self.root)
        with self.assertRaisesRegex(self.helper.InitializationError, "allowlist is invalid"):
            self.helper.run_initialization(**self.arguments)
        self.assertEqual(before, manifest(self.root))

    def test_symlink_and_hardlinked_allowed_sources_are_refused(self):
        soul = self.root / self.helper.TEMPLATE / "SOUL.md"
        backup = self.root / "soul-original"
        soul.rename(backup)
        for symlink in (True, False):
            if symlink:
                soul.symlink_to(backup)
            else:
                os.link(backup, soul)
            with (
                self.subTest(symlink=symlink),
                self.assertRaises(self.helper.InitializationError),
            ):
                self.helper.run_initialization(**self.arguments)
            self.assertFalse(self.target.exists())
            soul.unlink()

    def test_registry_stale_conflict_and_atomic_failure_preserve_inventory(self):
        record = self.run_setup()
        candidate = record["registry"]["entry"]
        registry, raw = self.helper.read_registry(self.root)
        equivalent = self.helper.register_project(self.root, candidate, raw)
        self.assertFalse(equivalent["changed"])
        self.assertEqual(raw, (self.root / "depot/projects.json").read_bytes())
        for changed in (
            {**candidate, "name": "Conflicting"},
            {**candidate, "id": "other"},
        ):
            with self.assertRaises(self.helper.InitializationError):
                self.helper.register_project(self.root, changed, raw)
            self.assertEqual(raw, (self.root / "depot/projects.json").read_bytes())
        registry["projects"].remove(candidate)
        without = self.helper.encoded(registry)
        (self.root / "depot/projects.json").write_bytes(without)
        with self.assertRaisesRegex(self.helper.InitializationError, "changed since"):
            self.helper.register_project(self.root, candidate, raw)
        with (
            patch.object(self.helper.os, "replace", side_effect=OSError("injected")),
            self.assertRaises(OSError),
        ):
            self.helper.register_project(self.root, candidate, without)
        self.assertEqual(without, (self.root / "depot/projects.json").read_bytes())
        locks = list((self.root / "depot").glob(".*initializer*"))
        self.assertEqual([self.root / "depot/.projects-initializer.lock"], locks)
        with self.helper.exclusive(locks[0]):
            self.assertEqual(b"", locks[0].read_bytes())

    def test_registry_rejects_schema_duplicates_and_source_substitution(self):
        _registry, raw = self.helper.read_registry(self.root)
        cases = []
        bad = json.loads(raw)
        bad["schema_version"] = 1
        cases.append(bad)
        bad = json.loads(raw)
        bad["projects"].append(bad["projects"][1])
        cases.append(bad)
        bad = json.loads(raw)
        bad["projects"][1]["path"] = "Projects"
        cases.append(bad)
        bad = json.loads(raw)
        bad["projects"][1]["repository"]["remote"] = "invented"
        cases.append(bad)
        for invalid in cases:
            (self.root / "depot/projects.json").write_text(json.dumps(invalid))
            before = manifest(self.root)
            with (
                self.subTest(invalid=invalid),
                self.assertRaises(self.helper.InitializationError),
            ):
                self.helper.run_initialization(**self.arguments)
            self.assertEqual(before, manifest(self.root))

    def test_manual_preparation_uses_template_and_preserves_extra_files(self):
        shutil.copytree(self.root / "Projects/Sys4AI-Template-Project", self.target)
        (self.target / "notes.txt").write_text("project-owned note")
        (self.target / ".agents/skills/communication/local-reference.md").write_text("project-owned reference")
        source = self.root / "SKILLS-depo/communication/SKILL.md"
        source.write_text(source.read_text() + "\nCurrent depot edition.\n")
        self.run_setup(mode="prepare-existing")
        self.assertEqual("project-owned note", (self.target / "notes.txt").read_text())
        self.assertEqual("project-owned reference", (self.target / ".agents/skills/communication/local-reference.md").read_text())
        self.assertEqual(
            (self.root / self.helper.TEMPLATE / ".agents/skills/communication/SKILL.md").read_bytes(),
            (self.target / ".agents/skills/communication/SKILL.md").read_bytes(),
        )
        self.assertNotEqual(source.read_bytes(), (self.target / ".agents/skills/communication/SKILL.md").read_bytes())
        self.assertIn("Orchard", (self.target / "README.md").read_text())
        self.assertEqual(
            "orchard",
            json.loads((self.target / "project.json").read_text())["project_id"],
        )

    def test_manual_customized_skill_is_preserved_during_setup(self):
        shutil.copytree(self.root / "Projects/Sys4AI-Template-Project", self.target)
        (self.target / ".agents/skills/communication/SKILL.md").write_text(
            "custom project skill"
        )
        self.run_setup(mode="prepare-existing")
        self.assertEqual("custom project skill", (self.target / ".agents/skills/communication/SKILL.md").read_text())

    def test_helper_location_cannot_retarget_the_depot(self):
        with (
            patch.object(
                self.helper,
                "__file__",
                str(self.root / "arbitrary/scripts/init_new_project.py"),
            ),
            self.assertRaises(self.helper.InitializationError),
        ):
            self.helper.installed_locations()
        result = subprocess.run(
            [
                sys.executable,
                str(
                    self.root
                    / "SKILLS-depo/init-new-project/scripts/init_new_project.py"
                ),
                "create",
                "--depot-root",
                str(self.root),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(0, result.returncode)
        active = self.root / ".agents/skills/init-new-project"
        shutil.copytree(self.root / "SKILLS-depo/init-new-project", active)
        installed = load_helper(active)
        self.assertEqual((self.root, active), installed.installed_locations())
        self.assertFalse(active.is_symlink())

    def test_template_and_registered_child_installations_find_only_the_owning_depot(self):
        template_skill = self.root / self.helper.TEMPLATE / ".agents/skills/init-new-project"
        self.helper = load_helper(template_skill)
        self.assertEqual((self.root, template_skill), self.helper.installed_locations())
        self.run_setup()
        child_skill = self.target / ".agents/skills/init-new-project"
        self.helper = load_helper(child_skill)
        self.assertEqual((self.root, child_skill), self.helper.installed_locations())
        self.run_setup(destination=self.root / "Projects/Second", project_id="second", project_name="Second")
        unregistered = self.root / "Projects/Unregistered/.agents/skills/init-new-project"
        shutil.copytree(child_skill, unregistered)
        unregistered_helper = load_helper(unregistered)
        with self.assertRaisesRegex(unregistered_helper.InitializationError, "owner is not a registered project"):
            unregistered_helper.installed_locations()

    def test_git_observation_requires_exact_child_marker_and_never_mutates_git(self):
        self.target.mkdir()
        with patch.object(self.helper.subprocess, "run") as commands:
            self.assertEqual(
                {"status": "not_initialized", "remote": None},
                self.helper.repository_observation(self.target),
            )
            commands.assert_not_called()
        (self.target / ".git").write_text("gitdir: /preconstructed-fixture/metadata\n")
        with (
            patch.object(self.helper, "process", return_value=str(self.root)),
            self.assertRaises(self.helper.InitializationError),
        ):
            self.helper.repository_observation(self.target)
        observation = subprocess.CompletedProcess(["git"], 1, "", "")
        with (
            patch.object(self.helper, "process", return_value=str(self.target)) as top,
            patch.object(
                self.helper.subprocess, "run", return_value=observation
            ) as remote,
        ):
            self.assertEqual(
                {"status": "initialized", "remote": None},
                self.helper.repository_observation(self.target),
            )
            self.assertEqual(
                ["git", "-C", str(self.target), "rev-parse", "--show-toplevel"],
                top.call_args.args[0],
            )
            self.assertEqual(
                ["git", "-C", str(self.target), "config", "--get", "remote.origin.url"],
                remote.call_args.args[0],
            )

    def test_initializer_lock_excludes_live_writer_and_releases_after_abrupt_exit(self):
        lock = self.root / "depot/abrupt-initializer.lock"
        script = """import importlib.util,os,sys
from pathlib import Path
spec=importlib.util.spec_from_file_location('initializer',sys.argv[1])
helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
with helper.exclusive(Path(sys.argv[2])):
 print('locked',flush=True)
 sys.stdin.read(1)
 os._exit(9)
"""
        child = subprocess.Popen([sys.executable, "-c", script, self.helper.__file__, str(lock)],
                                 stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            self.assertTrue(select.select([child.stdout], [], [], 10)[0], "lock child did not become ready")
            self.assertEqual("locked\n", child.stdout.readline())
            inode = lock.stat().st_ino
            with self.assertRaisesRegex(self.helper.InitializationError, "operation is active"):
                with self.helper.exclusive(lock):
                    self.fail("a competing writer entered the locked section")
            child.communicate("x", timeout=10)
            self.assertEqual(9, child.returncode)
            with self.helper.exclusive(lock):
                self.assertEqual(inode, lock.stat().st_ino)
            with self.helper.exclusive(lock):
                self.assertEqual(inode, lock.stat().st_ino)
        finally:
            if child.poll() is None:
                child.kill()
            child.communicate(timeout=10)


if __name__ == "__main__":
    unittest.main()
