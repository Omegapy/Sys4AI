"""Read-only contracts for the generic, uninitialized Sys4AI starter."""

from __future__ import annotations

import importlib.util
import json
import os
import re
import shlex
import subprocess
import sys
import unittest
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parents[1]
DEPOT = TEMPLATE.parents[1]
BASELINE = {
    "agent-task",
    "communication",
    "manage-subagent-roles",
    "task",
    "to-implementation-plan",
    "to-trd",
}
STARTERS = {
    "AGENTS.md",
    "ROLE.md",
    ".gitignore",
    "README.md",
    "SPECS.md",
    "sub-agent-roles/project-sub-agent/AGENTS.md",
    "sub-agent-roles/project-sub-agent/ROLE.md",
    "Implementation_Plans/subagent_role_system_implementation_plan.md",
    "Implementation_Plans/task_system_implementation_plan.md",
    "Tasks/INDEX.md",
}
EXCLUDED_CHECKOUT_PATHS = {".venv", ".ruff_cache", ".DS_Store"}


def guide_commands() -> list[str]:
    return re.findall(
        r"```bash\n(.*?)\n```", (TEMPLATE / "INIT_MEMORY.md").read_text(), re.DOTALL
    )


def cli_help(arguments: list[str], cwd: Path) -> str:
    environment = {
        **os.environ,
        "PYTHONDONTWRITEBYTECODE": "1",
        "GIT_OPTIONAL_LOCKS": "0",
        "TMPDIR": "/private/tmp",
    }
    environment.pop("PYTHONPATH", None)
    completed = subprocess.run(
        arguments,
        cwd=cwd,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    if completed.returncode:
        raise AssertionError(
            f"Read-only help failed for {Path(arguments[0]).name}: "
            f"exit {completed.returncode}"
        )
    return completed.stdout


class TemplateContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = DEPOT / "SKILLS-depo/init-new-project/scripts/init_new_project.py"
        spec = importlib.util.spec_from_file_location("template_initializer", source)
        cls.helper = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.helper)
        cls.allowlist = json.loads(
            (
                DEPOT / "SKILLS-depo/init-new-project/assets/baseline-assets.json"
            ).read_text()
        )

    def test_template_is_neutral_and_has_no_memory_or_git_state(self):
        self.assertEqual(
            "# Sys4AI Template Project",
            (TEMPLATE / "README.md").read_text().splitlines()[0],
        )
        forbidden_roots = {
            ".git",
            ".gitmodules",
            ".sys4ai",
            ".cognee",
            ".cognee_system",
            ".data_storage",
            "project.json",
            "config/memory.toml",
            "registries/memory_source_registry.csv",
            "control_records/memory",
            "control_records/project-initialization.json",
            "models",
            "logs",
            "staging",
            "exports",
        }
        for relative in forbidden_roots:
            target = TEMPLATE / relative
            self.assertFalse(target.exists() or target.is_symlink(), relative)
        for current, directories, files in os.walk(TEMPLATE, followlinks=False):
            if Path(current) == TEMPLATE:
                directories[:] = [
                    name for name in directories if name not in EXCLUDED_CHECKOUT_PATHS
                ]
            for name in directories:
                self.assertNotIn(
                    name,
                    {
                        ".git",
                        ".sys4ai",
                        ".cognee",
                        ".cognee_system",
                        ".data_storage",
                        "models",
                        "logs",
                    },
                )
            for name in files:
                if name in EXCLUDED_CHECKOUT_PATHS:
                    continue
                self.assertFalse(
                    name.endswith((".sqlite", ".sqlite3", ".db", ".cogx", ".log")),
                    str(Path(current) / name),
                )
                self.assertNotIn(name, {".git", "memory.toml", "initialization.json"})

    def test_exact_six_embedded_packages_are_complete_and_parseable(self):
        skills = TEMPLATE / ".agents/skills"
        self.assertEqual(
            BASELINE, {path.name for path in skills.iterdir() if path.is_dir()}
        )
        for name in BASELINE:
            package = self.helper.package_files(skills / name)
            self.assertIn("SKILL.md", package)
            self.assertTrue(package)
        self.assertTrue((TEMPLATE / "SOUL.md").is_file())
        # Embedded copies remain project-owned. The manual helper, not this
        # static seed check, reviews and adopts newer source package versions.

    def test_starter_allowlist_includes_required_files_and_only_fixed_baselines(self):
        self.assertEqual("Projects/Sys4AI-Template-Project", self.allowlist["template"])
        self.assertEqual(STARTERS, set(self.allowlist["starter_files"]))
        self.assertEqual(["INIT_MEMORY.md"], self.allowlist["optional_starter_files"])
        self.assertEqual(BASELINE, set(self.allowlist["skills"]))
        self.assertEqual("SOULS-depo/SOUL.md", self.allowlist["soul"])
        for relative in (*self.allowlist["starter_files"], "INIT_MEMORY.md"):
            target = TEMPLATE / relative
            self.assertTrue(target.is_file(), relative)
            self.assertFalse(target.is_symlink(), relative)
        index = (TEMPLATE / "Tasks/INDEX.md").read_text()
        self.assertIn("| None |", index)
        self.assertNotIn("TASK-", index)
        self.assertFalse(list((TEMPLATE / "Tasks").rglob("task.json")))
        self.assertTrue((DEPOT / self.allowlist["soul"]).is_file())
        for name in BASELINE:
            self.assertTrue((DEPOT / "SKILLS-depo" / name / "SKILL.md").is_file())

    def test_transient_and_repository_metadata_categories_are_excluded(self):
        candidates = (
            ".git",
            ".git/objects/history",
            ".gitmodules",
            ".venv/bin/python",
            ".ruff_cache/entry",
            ".DS_Store",
            "__pycache__/module.pyc",
            ".sys4ai/memory/exact_index/index.sqlite3",
            "models/model.bin",
            ".cognee_system/db.sqlite",
            ".data_storage/graph",
            "logs/provider.log",
            ".env",
            ".secrets/key",
            "dist/package.whl",
        )
        for relative in candidates:
            self.assertTrue(self.helper.excluded(Path(relative)), relative)
            self.assertNotIn(relative, self.allowlist["starter_files"])
        self.assertTrue(
            EXCLUDED_CHECKOUT_PATHS.isdisjoint(self.allowlist["starter_files"])
        )
        self.assertNotIn(
            "tests/test_template_contract.py", self.allowlist["starter_files"]
        )

    def test_ignore_rules_protect_future_local_memory_state(self):
        rules = {
            line.strip()
            for line in (TEMPLATE / ".gitignore").read_text().splitlines()
            if line.strip() and not line.startswith("#")
        }
        self.assertTrue(
            {
                "/.sys4ai/memory/",
                "/.cognee_system/",
                "/.data_storage/",
                "/models/",
                "/logs/",
                ".venv/",
                ".ruff_cache/",
                "__pycache__/",
                ".DS_Store",
                ".env",
                ".env.*",
                "*.sqlite",
                "*.sqlite3",
                "*.db",
                "*.cogx",
            }.issubset(rules)
        )
        self.assertFalse({"!/.sys4ai/memory/", "!/models/", "!*.sqlite3"} & rules)

    def test_guide_links_resolve_and_remain_portable_from_a_direct_project_copy(self):
        for name in ("README.md", "INIT_MEMORY.md"):
            text = (TEMPLATE / name).read_text()
            for link in re.findall(r"\]\(([^)]+)\)", text):
                if link.startswith(("https:", "http:", "#")):
                    continue
                relative = link.split("#")[0]
                target = (TEMPLATE / relative).resolve()
                self.assertTrue(target.exists(), f"{name}: {link}")
                if name == "INIT_MEMORY.md":
                    copied_base = DEPOT / "Projects/ExampleManualCopy"
                    self.assertEqual(target, (copied_base / relative).resolve())
        guide = (TEMPLATE / "INIT_MEMORY.md").read_text()
        self.assertIn("This template is not initialized", guide)
        self.assertIn(
            "[Initialize memory in a copied project](./INIT_MEMORY.md)",
            (TEMPLATE / "README.md").read_text(),
        )

    def test_manual_commands_match_read_only_installed_help(self):
        blocks = guide_commands()
        preparation = shlex.split(blocks[0].replace("\\\n", " "))
        self.assertEqual("prepare-existing", preparation[2])
        active_helper = DEPOT / preparation[1]
        self.assertTrue(active_helper.is_file())
        help_text = cli_help(
            [sys.executable, str(active_helper), "prepare-existing", "--help"], DEPOT
        )
        for argument in preparation[3:]:
            if argument.startswith("--"):
                self.assertIn(argument, help_text)
        prefix_text = re.search(
            r"memory_command=\((.*?)\)", blocks[1], re.DOTALL
        ).group(1)
        prefix = shlex.split(prefix_text)
        executable = DEPOT / "Projects/Sys4AI-Memory-Service/.venv/bin/sys4ai-memory"
        for command in ("init-memory", "sync", "recall"):
            help_text = cli_help(
                [str(executable), *prefix[1:], command, "--help"], TEMPLATE
            )
            self.assertIn(
                "--mode" if command == "recall" else "--idempotency-key", help_text
            )
        for block in blocks:
            self.assertNotIn("Sys4AI-Template-Project", block)
            self.assertNotRegex(block, r"\b(?:preview|apply)\b")
        self.assertIn("next_command", (TEMPLATE / "INIT_MEMORY.md").read_text())


if __name__ == "__main__":
    unittest.main()
