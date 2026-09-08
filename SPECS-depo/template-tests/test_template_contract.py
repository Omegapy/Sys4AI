"""Read-only contracts for the generic, uninitialized Sys4AI starter."""

from __future__ import annotations

import importlib.util
import json
import os
import re
import subprocess
import sys
import unittest
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parents[1]
DEPOT = TEMPLATE.parents[1]
BASELINE = {
    "init-new-project",
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
    "Implementation_Plans/subagent_role_system_implementation_plan.md",
    "Implementation_Plans/task_system_implementation_plan.md",
    "Tasks/INDEX.md",
}
EXCLUDED_CHECKOUT_PATHS = {".venv", ".ruff_cache", ".DS_Store"}



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
        source = TEMPLATE / ".agents/skills/init-new-project/scripts/init_new_project.py"
        spec = importlib.util.spec_from_file_location("template_initializer", source)
        cls.helper = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.helper)
        cls.allowlist = json.loads(
            (
                TEMPLATE / ".template/baseline-assets.json"
            ).read_text()
        )

    def test_template_is_neutral_and_has_no_product_runtime_or_git_state(self):
        self.assertEqual(
            "# Sys4AI Template Project",
            (TEMPLATE / "README.md").read_text().splitlines()[0],
        )
        forbidden_roots = {
            "Ontology",
            "INIT_MEMORY.md",
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

    def test_all_embedded_packages_are_complete_and_parseable(self):
        skills = TEMPLATE / ".agents/skills"
        names = {path.name for path in skills.iterdir() if path.is_dir()}
        self.assertTrue(BASELINE.issubset(names))
        for name in names:
            package = self.helper.package_files(skills / name)
            self.assertIn("SKILL.md", package)
            self.assertTrue(package)
        self.assertTrue((TEMPLATE / "SOUL.md").is_file())
        # Creation reads this complete template package set, including additions.

    def test_starter_policy_uses_template_relative_sources(self):
        self.assertEqual("Projects/Sys4AI-Template-Project", self.allowlist["template"])
        self.assertEqual(STARTERS, set(self.allowlist["starter_files"]))
        self.assertEqual([], self.allowlist["optional_starter_files"])
        self.assertEqual(2, self.allowlist["schema_version"])
        self.assertEqual(".agents/skills", self.allowlist["skills"])
        self.assertEqual("roles", self.allowlist["roles"])
        self.assertEqual("SOUL.md", self.allowlist["soul"])
        for relative in self.allowlist["starter_files"]:
            target = TEMPLATE / relative
            self.assertTrue(target.is_file(), relative)
            self.assertFalse(target.is_symlink(), relative)
        index = (TEMPLATE / "Tasks/INDEX.md").read_text()
        self.assertIn("| None |", index)
        self.assertNotIn("TASK-", index)
        self.assertFalse(list((TEMPLATE / "Tasks").rglob("task.json")))
        self.assertTrue((TEMPLATE / self.allowlist["soul"]).is_file())
        for name in BASELINE:
            self.assertTrue((TEMPLATE / ".agents/skills" / name / "SKILL.md").is_file())

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

    def test_starter_policy_has_no_product_runtime_bundle(self):
        self.assertEqual(2, self.allowlist["schema_version"])
        self.assertNotIn("ontology", self.allowlist)
        self.assertEqual([], self.allowlist["optional_starter_files"])
        for retired in ("Ontology", "INIT_MEMORY.md"):
            self.assertFalse((TEMPLATE / retired).exists(), retired)
        roles = {p.name for p in (TEMPLATE / "roles").iterdir() if p.is_dir()}
        self.assertEqual({"project-sub-agent", "task-manager"}, roles)
        self.assertEqual((TEMPLATE / "roles/INDEX.md").read_bytes(), self.helper.planned_role_index(TEMPLATE, {}, {}))
        self.assertFalse((TEMPLATE / "roles/.transition.json").exists())


    def test_ignore_rules_protect_local_artifacts_and_secrets(self):
        rules = {
            line.strip() for line in (TEMPLATE / ".gitignore").read_text().splitlines()
            if line.strip() and not line.startswith("#")
        }
        self.assertTrue({"/models/", "/logs/", ".venv/", ".ruff_cache/",
                         "__pycache__/", ".DS_Store", ".env", ".env.*",
                         "*.sqlite", "*.sqlite3", "*.db"}.issubset(rules))
        self.assertFalse({"!/models/", "!*.sqlite3", "!.env"} & rules)


    def test_project_guidance_links_resolve(self):
        for name in ("README.md", "SPECS.md", "AGENTS.md"):
            for link in re.findall(r"\]\(([^)]+)\)", (TEMPLATE / name).read_text()):
                if link.startswith(("https:", "http:", "#")):
                    continue
                relative = link.split("#")[0]
                self.assertTrue((TEMPLATE / relative).resolve().exists(), f"{name}: {link}")
        readme = (TEMPLATE / "README.md").read_text()
        self.assertIn("prepare-existing", readme)
        self.assertIn("control_records/project-setup.json", readme)


    def test_setup_cli_matches_the_documented_governance_inputs(self):
        helper = TEMPLATE / ".agents/skills/init-new-project/scripts/init_new_project.py"
        for command in ("create", "prepare-existing"):
            help_text = cli_help([sys.executable, str(helper), command, "--help"], TEMPLATE)
            for argument in ("--destination", "--project-id", "--project-name", "--purpose"):
                self.assertIn(argument, help_text)
            for argument in ("--principal-id", "--dataset-id", "--artifact-receipt"):
                self.assertNotIn(argument, help_text)




if __name__ == "__main__":
    unittest.main()
