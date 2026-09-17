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
    "memory",
    "what-did-you-learn",
    "ontology",
    "curate",
}
STARTERS = {
    "AGENTS.md",
    "ROLE.md",
    ".gitignore",
    "README.md",
    "SPECS.md",
    "LICENSE",
    "LICENSE-CODE",
    "LICENSE-DOCS",
    "Implementation_Plans/subagent_role_system_implementation_plan.md",
    "Implementation_Plans/task_system_implementation_plan.md",
    "Tasks/INDEX.md",
    "memory.yaml",
    "MEMORY/README.md",
    "reference-assets/LEARNING-depo/contract.json",
    "reference-assets/LEARNING-depo/README.md",
    "reference-assets/LEARNING-depo/policy.md",
    "reference-assets/LEARNING-depo/review-contract.md",
    "reference-assets/LEARNING-depo/assets/lesson-body-template.md",
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
        # APFS may resolve the retired spelling to the new ONTOLOGY folder.
        self.assertNotIn("Ontology", {p.name for p in TEMPLATE.iterdir()})
        self.assertIn("ONTOLOGY", {p.name for p in TEMPLATE.iterdir()})
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

    def test_memory_starter_is_empty_and_complete(self):
        config = json.loads((TEMPLATE / "memory.yaml").read_text())
        self.assertEqual({"id": None, "name": None, "root": "."}, config["project"])
        self.assertEqual("MEMORY", config["canonical_root"])
        self.assertEqual("reference-assets/MEMORY-depo", config["contract_root"])
        self.assertFalse(config["backend"]["enabled"])
        self.assertFalse(config["backend"]["semantic_enabled"])
        self.assertEqual(["README.md"], sorted(p.relative_to(TEMPLATE / "MEMORY").as_posix()
                         for p in (TEMPLATE / "MEMORY").rglob("*") if p.is_file()))
        for rel in ("README.md", "policy.md", "publication-and-recovery.md",
                    "schema/record-v1.json", "schema/config-v1.json", "schema/normalization-v1.json",
                    "schema/backend-projection-v1.json", "profiles/basic-memory-v0.23.0.json"):
            self.assertTrue((TEMPLATE / "reference-assets/MEMORY-depo" / rel).is_file(), rel)
        self.assertIsNone(config["publication"]["director"])

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

    def test_learning_module_is_complete_local_and_neutral(self):
        module = TEMPLATE / "reference-assets/LEARNING-depo"
        manifest = json.loads((module / "contract.json").read_text())
        self.assertEqual("what-did-you-learn", manifest["module_id"])
        self.assertEqual("1.0.0", manifest["module_version"])
        self.assertEqual(set(manifest["required_resources"]),
                         {p.relative_to(module).as_posix() for p in module.rglob("*") if p.is_file()})
        self.assertEqual({"schema_version", "module_id", "module_version", "required_resources", "skill", "memory"},
                         set(manifest))
        for relative in manifest["skill"]["required_resources"]:
            self.assertTrue((TEMPLATE / ".agents/skills/what-did-you-learn" / relative).is_file(), relative)
        with self.helper.learning_resolver((TEMPLATE / self.helper.LEARNING_RESOLVER).read_bytes()) as resolver:
            result = resolver.resolve(TEMPLATE)
        self.assertEqual([], result["errors"])
        self.assertTrue(result["capabilities"]["manual_review"])
        self.assertTrue(result["capabilities"]["shared_automatic_checkpoint"])
        self.assertEqual("not_assessed", result["capabilities"]["authorized_publication"])
        self.assertEqual("not_assessed", result["capabilities"]["optional_backend"])
        config = json.loads((TEMPLATE / "memory.yaml").read_text())
        self.assertIsNone(config["publication"]["director"])
        self.assertIsNone(config["project"]["id"])
        self.assertFalse((TEMPLATE / "control_records/project-setup.json").exists())

    def test_ontology_starter_is_neutral_locked_and_service_independent(self):
        files = {name: (TEMPLATE / name).read_bytes() for name, value in self.helper.ontology_inventory(TEMPLATE).items() if value != "directory"}
        config = self.helper.validate_ontology_static(TEMPLATE, files, neutral=True)
        self.assertEqual({"id": None, "name": None, "purpose": None, "namespace": None, "root": "."}, config["project"])
        self.assertEqual({"enabled": False, "binding": None}, config["publication"])
        for relative in ("ONTOLOGY/WIKI", "control_records/ontology", ".sys4ai/ontology"):
            self.assertFalse((TEMPLATE / relative).exists(), relative)
        for name in ("ONTOLOGY/modules/project/project.jsonld", "ONTOLOGY/bindings/bindings.jsonld"):
            self.assertEqual([], json.loads((TEMPLATE / name).read_text())["@graph"])

    def test_complete_static_capability_inventory_includes_health_and_test_delivery(self):
        inventory = self.helper._static("inventory")
        required = {name for names in inventory["packages"].values() for name in names}
        for relative in (".agents/skills/ontology/scripts/ontology_health.py",
                         ".agents/skills/ontology/tests/acceptance_runner.py",
                         ".agents/skills/init-new-project/scripts/init_static_health.py"):
            self.assertIn(relative, required)
        files = {name: (TEMPLATE / name).read_bytes() for name in required}
        self.helper._static("validate_source", files, contract=self.helper.SETUP_CONTRACT)
        self.assertFalse(any(part.startswith((".venv", ".sys4ai")) or part == "control_records"
                             for name in required for part in Path(name).parts))

    def test_starter_policy_uses_template_relative_sources(self):
        self.assertEqual("Projects/Sys4AI-Template-Project", self.allowlist["template"])
        self.assertEqual(STARTERS | self.helper.ONTOLOGY_FILES | self.helper.ADVANCED.STARTERS | self.helper.CURATOR.STARTERS,
                         set(self.allowlist["starter_files"]))
        self.assertEqual([], self.allowlist["optional_starter_files"])
        self.assertEqual(2, self.allowlist["schema_version"])
        self.assertEqual(".agents/skills", self.allowlist["skills"])
        self.assertEqual("Roles", self.allowlist["roles"])
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
            if retired == "Ontology":
                self.assertNotIn(retired, {p.name for p in TEMPLATE.iterdir()})
            else:
                self.assertFalse((TEMPLATE / retired).exists(), retired)
        roles = {p.name for p in (TEMPLATE / "Roles").iterdir() if p.is_dir()}
        self.assertEqual({"project-sub-agent", "task-manager", *self.helper.CURATOR.ROLES}, roles)
        self.assertEqual((TEMPLATE / "Roles/INDEX.md").read_bytes(), self.helper.planned_role_index(TEMPLATE, {}, {}))
        self.assertFalse((TEMPLATE / "Roles/.transition.json").exists())


    def test_curator_contract_is_complete_neutral_and_owner_bound(self):
        files = self.helper.template_sources(DEPOT)[0]
        cfg = self.helper._curator("validate_static", files, neutral=True)
        self.assertTrue(all(value is None for value in cfg["project"].values()))
        self.assertFalse(cfg["schedule"]["enabled"]); self.assertEqual(cfg["entitlements"], [])
        session = json.loads((TEMPLATE / "curator-session.yaml").read_text())
        self.assertFalse(session["enabled"]); self.assertIsNone(session["project_id"])
        self.assertFalse(session["unattended_background_ai"])
        self.assertFalse(cfg["notifications"]["enabled"]); self.assertFalse(cfg["service_installed"]); self.assertFalse(cfg["hook_installed"])
        self.assertIsNone(cfg["runtime"]); self.assertFalse(cfg["autonomous_write"])
        for relative in ("control_records/curator", ".sys4ai/curator", "MEMORY/Records", "CURATION/records"):
            self.assertFalse((TEMPLATE / relative).exists())
        contract = json.loads((TEMPLATE / "reference-assets/CURATION-depo/contract.json").read_text())
        self.assertEqual("project-curator", contract["module_id"])
        self.assertEqual(2, contract["schema_version"])
        self.assertEqual("governance-starter-v11", contract["compatibility"]["setup_edition"])
        self.assertFalse(contract["connected_application"]["runtime_observed"])
        self.assertEqual("agent-task", contract["existing_owners"]["task"].split("owned by ")[-1].rstrip("."))
        for role in self.helper.CURATOR.ROLES:
            self.assertTrue((TEMPLATE / "Roles" / role / "AGENTS.md").is_file())
            self.assertTrue((TEMPLATE / "Roles" / role / "ROLE.md").is_file())


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
