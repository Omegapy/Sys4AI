"""Boundary and recovery contracts, exercised only in test-owned depot copies."""

from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SOURCE_SKILL = Path(__file__).resolve().parents[1]
if SOURCE_SKILL.parent.name == "SKILLS-depo":
    SOURCE_DEPOT = SOURCE_SKILL.parents[1]
elif SOURCE_SKILL.parent.name == "skills" and SOURCE_SKILL.parents[1].name == ".agents":
    SOURCE_DEPOT = SOURCE_SKILL.parents[2]
else:
    raise RuntimeError("Initializer tests must run from a source or active depot package")
BASELINE = (
    "agent-task",
    "communication",
    "manage-subagent-roles",
    "task",
    "to-implementation-plan",
    "to-trd",
)


def load_helper(skill: Path):
    spec = importlib.util.spec_from_file_location(
        "fixture_initializer", skill / "scripts/init_new_project.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fixture_depot(base: Path) -> Path:
    root = base / "Sys4AI"
    root.mkdir()
    (root / "depot").mkdir()
    (root / "Projects").mkdir()
    shutil.copytree(
        SOURCE_SKILL,
        root / "SKILLS-depo/init-new-project",
        ignore=shutil.ignore_patterns("__pycache__", ".DS_Store"),
    )
    for name in BASELINE:
        shutil.copytree(
            SOURCE_DEPOT / "SKILLS-depo" / name,
            root / "SKILLS-depo" / name,
            ignore=shutil.ignore_patterns("__pycache__", ".DS_Store", "*.pyc"),
        )
    (root / "SOULS-depo").mkdir()
    shutil.copyfile(SOURCE_DEPOT / "SOULS-depo/SOUL.md", root / "SOULS-depo/SOUL.md")
    template = root / "Projects/Sys4AI-Template-Project"
    template.mkdir()
    specification = json.loads(
        (SOURCE_SKILL / "assets/baseline-assets.json").read_text()
    )
    for relative in specification["starter_files"]:
        target = template / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(
            SOURCE_DEPOT / "Projects/Sys4AI-Template-Project" / relative, target
        )
    guide = SOURCE_DEPOT / "Projects/Sys4AI-Template-Project/INIT_MEMORY.md"
    if guide.is_file():
        shutil.copyfile(guide, template / "INIT_MEMORY.md")
    else:
        (template / "INIT_MEMORY.md").write_text(
            "# Manual project memory\n\nThis starter is not initialized. Use shared preparation on a real copy.\n"
        )
    shutil.copyfile(root / "SOULS-depo/SOUL.md", template / "SOUL.md")
    for name in BASELINE:
        shutil.copytree(root / "SKILLS-depo" / name, template / ".agents/skills" / name)
    (root / "Projects/Sys4AI-Memory-Service").mkdir()
    registry = json.loads((SOURCE_DEPOT / "depot/projects.json").read_text())
    registry["projects"] = [
        entry
        for entry in registry["projects"]
        if entry["id"]
        in {"sys4ai-depot", "sys4ai-template-project", "sys4ai-memory-service"}
    ]
    (root / "depot/projects.json").write_text(json.dumps(registry, indent=2) + "\n")
    return root


def manifest(root: Path) -> dict[str, str]:
    result = {}
    if not root.exists():
        return result
    for path in root.rglob("*"):
        if path.is_symlink():
            result[path.relative_to(root).as_posix()] = "symlink:" + os.readlink(path)
        elif path.is_file():
            import hashlib

            result[path.relative_to(root).as_posix()] = hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
        elif path.is_dir():
            result[path.relative_to(root).as_posix()] = "directory"
    return result


class InitializerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(
            prefix="sys4ai-initializer-unit-", dir="/private/tmp"
        )
        self.addCleanup(self.temporary.cleanup)
        self.root = fixture_depot(Path(self.temporary.name))
        self.helper = load_helper(self.root / "SKILLS-depo/init-new-project")
        self.target = self.root / "Projects/Orchard"
        self.arguments = {
            "mode": "create",
            "destination": self.target,
            "project_id": "orchard",
            "project_name": "Orchard",
            "purpose": "Track orchard observations with ORCHARD_FIXTURE_MARKER.",
            "principal_id": "fixture-owner",
        }
        self.artifact = (
            self.root / "Projects/Sys4AI-Memory-Service/dist/consumer/1/artifact.json"
        )
        self.artifact.parent.mkdir(parents=True)
        self.artifact.write_text("{}\n")

    def stop_at_install(self, **overrides):
        arguments = {**self.arguments, **overrides}
        with (
            patch.object(
                self.helper, "artifact_selection", return_value=(self.artifact, {})
            ),
            patch.object(
                self.helper,
                "process",
                side_effect=self.helper.InitializationError(
                    "injected installation failure"
                ),
            ),
            self.assertRaises(self.helper.InitializationError) as caught,
        ):
            self.helper.run_initialization(**arguments)
        self.assertEqual(
            "runtime-installation", caught.exception.report["recovery"]["stage"]
        )
        return caught.exception.report

    def test_nested_guide_links_keep_reviewed_targets_and_source_digest(self):
        guide = self.root / "Projects/Sys4AI-Template-Project/INIT_MEMORY.md"
        original = (
            "[Skill](../../.agents/skills/init-new-project/SKILL.md)\n"
            "[Builder](../Sys4AI-Memory-Service/tools/build_consumer_artifact.py#usage)\n"
            "[Anchor](#manual) [Website](https://example.com/guide)\n"
        )
        guide.write_text(original)
        identity = {
            "project_id": "orchard", "project_name": "Orchard",
            "purpose": "Track orchard observations.",
            "relative_path": "Projects/Archive/Orchard",
        }
        proposed, records, originals = self.helper.source_snapshot(
            self.root, self.root / "SKILLS-depo/init-new-project", identity
        )
        self.assertEqual(original.encode(), guide.read_bytes())
        self.assertEqual(original.encode(), originals["INIT_MEMORY.md"])
        copied = proposed["INIT_MEMORY.md"].decode()
        self.assertIn("[Anchor](#manual) [Website](https://example.com/guide)", copied)
        before = re.findall(r"\]\(([^)]+)\)", original)[:2]
        after = re.findall(r"\]\(([^)]+)\)", copied)[:2]
        for source_link, copied_link in zip(before, after):
            self.assertEqual(
                (guide.parent / source_link.split("#")[0]).resolve(),
                (self.root / identity["relative_path"] / copied_link.split("#")[0]).resolve(),
            )
            self.assertEqual(source_link.partition("#")[2], copied_link.partition("#")[2])
        evidence = next(x for x in records if x["destination"] == "INIT_MEMORY.md")
        self.assertEqual(self.helper.sha(original.encode()), evidence["source_sha256"])
        self.assertEqual(self.helper.sha(proposed["INIT_MEMORY.md"]), evidence["destination_sha256"])
        self.assertNotEqual(evidence["source_sha256"], evidence["destination_sha256"])
        identity["relative_path"] = "Projects/Orchard"
        direct, _, _ = self.helper.source_snapshot(
            self.root, self.root / "SKILLS-depo/init-new-project", identity
        )
        self.assertEqual(original.encode(), direct["INIT_MEMORY.md"])

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
            self.root / "Projects/Sys4AI-Memory-Service",
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
        self.stop_at_install()
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
            ".sys4ai/memory/log",
            "models/weights",
            "unknown.txt",
            ".DS_Store",
            "sub-agent-roles/project-sub-agent/__pycache__/compiled.pyc",
            "Implementation_Plans/old-plan.md",
            "Tasks/old-task/task.json",
        )
        for relative in garbage:
            target = template / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("must not copy")
        (self.root / "SKILLS-depo/future-opt-in").mkdir()
        report = self.stop_at_install()
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
        self.stop_at_install(
            destination=other, project_id="second", project_name="Second"
        )
        self.assertFalse((other / ".git").exists())

    def test_asset_copies_are_complete_pinned_and_do_not_synchronize(self):
        report = self.stop_at_install()
        for name in BASELINE:
            self.assertEqual(
                self.helper.package_files(self.root / "SKILLS-depo" / name),
                self.helper.package_files(self.target / ".agents/skills" / name),
            )
        before = manifest(self.target)
        source = self.root / "SKILLS-depo/communication/SKILL.md"
        source.write_text(source.read_text() + "\nLater source edit.\n")
        self.assertEqual(before, manifest(self.target))
        self.assertTrue(
            all(
                len(item["source_sha256"]) == 64
                and len(item["destination_sha256"]) == 64
                for item in report["sources"]
            )
        )

    def test_source_drift_rejected_before_project_publication(self):
        def changed_artifact(*arguments):
            (self.root / "SOULS-depo/SOUL.md").write_text("changed during preflight")
            return self.artifact, {}

        before = (self.root / "depot/projects.json").read_bytes()
        with (
            patch.object(
                self.helper, "artifact_selection", side_effect=changed_artifact
            ),
            self.assertRaisesRegex(self.helper.InitializationError, "source changed"),
        ):
            self.helper.run_initialization(**self.arguments)
        self.assertFalse(self.target.exists())
        self.assertEqual(before, (self.root / "depot/projects.json").read_bytes())

    def test_package_file_addition_during_adoption_is_source_drift(self):
        def changed_artifact(*arguments):
            (self.root / "SKILLS-depo/communication/new-resource.md").write_text(
                "added after snapshot"
            )
            return self.artifact, {}

        with (
            patch.object(
                self.helper, "artifact_selection", side_effect=changed_artifact
            ),
            self.assertRaisesRegex(self.helper.InitializationError, "file set changed"),
        ):
            self.helper.run_initialization(**self.arguments)
        self.assertFalse(self.target.exists())

    def test_symlink_and_hardlinked_allowed_sources_are_refused(self):
        soul = self.root / "SOULS-depo/SOUL.md"
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
        record = self.stop_at_install()
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
        self.assertFalse(list((self.root / "depot").glob(".*initializer*")))

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
        bad["projects"][1]["path"] = "Projects/Sys4AI-Memory-Service"
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

    def test_manual_preparation_adopts_current_sources_and_preserves_extra_files(self):
        shutil.copytree(self.root / "Projects/Sys4AI-Template-Project", self.target)
        (self.target / "notes.txt").write_text("project-owned note")
        source = self.root / "SKILLS-depo/communication/SKILL.md"
        source.write_text(source.read_text() + "\nCurrent depot edition.\n")
        self.stop_at_install(mode="prepare-existing")
        self.assertEqual("project-owned note", (self.target / "notes.txt").read_text())
        self.assertEqual(
            source.read_bytes(),
            (self.target / ".agents/skills/communication/SKILL.md").read_bytes(),
        )
        self.assertIn("Orchard", (self.target / "README.md").read_text())
        self.assertEqual(
            "orchard",
            json.loads((self.target / "project.json").read_text())["project_id"],
        )

    def test_manual_customized_content_refuses_before_any_mutation(self):
        shutil.copytree(self.root / "Projects/Sys4AI-Template-Project", self.target)
        (self.target / ".agents/skills/communication/SKILL.md").write_text(
            "custom project skill"
        )
        before = manifest(self.root)
        with self.assertRaises(self.helper.InitializationError):
            self.helper.run_initialization(
                **{**self.arguments, "mode": "prepare-existing"}
            )
        self.assertEqual(before, manifest(self.root))

    def test_install_failure_recovery_records_exact_owned_state(self):
        record = self.stop_at_install()
        self.assertEqual("partial", record["status"])
        self.assertEqual(["assets", "registration"], record["completed_stages"])
        self.assertTrue(record["recovery"]["observed_owned_files"])
        (self.target / "unrelated.txt").write_text("preserve on retry")
        self.stop_at_install()
        self.assertEqual(
            "preserve on retry", (self.target / "unrelated.txt").read_text()
        )
        registry, _ = self.helper.read_registry(self.root)
        self.assertEqual(
            1, sum(entry["id"] == "orchard" for entry in registry["projects"])
        )

    def test_completed_rerun_refuses_changed_receipt_context_without_mutation(self):
        record = self.stop_at_install()
        receipt = {
            "project_id": "orchard",
            "dataset_id": "orchard-memory",
            "configuration_fingerprint": "1" * 64,
            "exact_index_initialized": True,
        }
        observed = {
            "version": "0.1.0",
            "origin": str(self.target / ".venv/fixture/sys4ai_memory/__init__.py"),
            "direct_url": {"url": "file:///fixture/immutable.whl"},
            "dependencies": {"sys4ai-memory-service": "0.1.0"},
        }
        record.update(
            status="completed",
            initialization=receipt,
            runtime={"version": "0.1.0", "observed": observed},
            installed_package_files={},
        )
        configuration = self.target / "config/memory.toml"
        configuration.parent.mkdir()
        configuration.write_text(
            '[memory.exact_index]\npath = ".sys4ai/memory/exact_index/index.sqlite3"\n'
        )
        record["owned_files"]["config/memory.toml"] = self.helper.sha(
            configuration.read_bytes()
        )
        index = self.target / ".sys4ai/memory/exact_index/index.sqlite3"
        index.parent.mkdir(parents=True)
        with sqlite3.connect(index) as connection:
            connection.execute("CREATE TABLE records(project_id TEXT)")
            connection.execute("INSERT INTO records VALUES ('orchard')")
        receipt_path = self.target / ".sys4ai/memory/receipts/initialization.json"
        receipt_path.parent.mkdir()
        receipt_path.write_bytes(self.helper.encoded(receipt))
        (self.target / self.helper.RECORD).write_bytes(self.helper.encoded(record))
        with patch.object(self.helper, "process", return_value=observed) as processes:
            before = manifest(self.root)
            completed = self.helper.run_initialization(**self.arguments)
            self.assertEqual("verified-existing", completed["rerun"])
            self.assertEqual(before, manifest(self.root))
            for field, value in (
                ("dataset_id", "another-project-memory"),
                ("configuration_fingerprint", "2" * 64),
            ):
                with self.subTest(field=field):
                    receipt_path.write_bytes(
                        self.helper.encoded({**receipt, field: value})
                    )
                    before = manifest(self.root)
                    with self.assertRaisesRegex(
                        self.helper.InitializationError, "differs from recorded context"
                    ):
                        self.helper.run_initialization(**self.arguments)
                    self.assertEqual(before, manifest(self.root))
            for call in processes.call_args_list:
                argv = call.args[0]
                self.assertEqual(str(self.target / ".venv/bin/python"), argv[0])
                self.assertEqual(["-I", "-c"], argv[1:3])
                self.assertIn("importlib.metadata", argv[3])
                self.assertNotIn("sys4ai_memory.cli", argv[3])

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


if __name__ == "__main__":
    unittest.main()
