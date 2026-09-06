"""Project-bound depot memory configuration and canonical source contracts."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

try:
    from sys4ai_memory.configuration import ConfigurationError, load_configuration
    from sys4ai_memory.sources import SourceDiscovery, load_registry_bundle
except ModuleNotFoundError:
    RUNTIME_AVAILABLE = False
else:
    RUNTIME_AVAILABLE = True

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(RUNTIME_AVAILABLE, "Run with the installed Memory Service consumer runtime")
class DepotMemoryConfigurationTests(unittest.TestCase):
    def test_configuration_is_independent_and_loading_is_noninitializing(self) -> None:
        derived = ROOT / ".sys4ai/memory"
        before = derived.exists()
        native_before = "cognee" in sys.modules
        loaded = load_configuration(ROOT / "config/memory.toml", trusted_project_root=ROOT)
        self.assertEqual("sys4ai-depot", loaded.configuration.memory.project_id)
        self.assertEqual("sys4ai-depot-memory", loaded.configuration.memory.provider.cognee.dataset)
        self.assertEqual("base@1", loaded.configuration.memory.default_memory_profile)
        self.assertFalse(loaded.configuration.memory.models.semantic_enabled)
        for name in ("exact_index", "model_cache", "audit_log"):
            self.assertTrue(loaded.resolved_paths[name].is_relative_to(derived))
        self.assertEqual(before, derived.exists())
        self.assertEqual(native_before, "cognee" in sys.modules)

    def test_permissions_bind_only_the_depot_owner(self) -> None:
        permissions = json.loads((ROOT / "control_records/memory/permissions.json").read_text())
        self.assertEqual("sys4ai-depot", permissions["project_id"])
        self.assertEqual("sys4ai-depot-memory", permissions["dataset_id"])
        for grant in permissions["grants"]:
            self.assertEqual("sys4ai-depot-director", grant["principal_id"])
            self.assertEqual([], grant["shared_project_ids"])
            self.assertEqual(["sys4ai-depot"], [scope["scope_id"] for scope in grant["scopes"]])

    def test_unsafe_storage_candidates_refuse_without_derived_state(self) -> None:
        with tempfile.TemporaryDirectory(prefix="sys4ai-depot-config-") as temporary:
            fixture = Path(temporary).resolve()
            for name in ("config", "registries", "profiles", "schemas", "control_records"):
                shutil.copytree(ROOT / name, fixture / name)
            config = fixture / "config/memory.toml"
            original = config.read_text()
            for path in ("Projects/foreign/models", "../outside", str(Path.home() / "models")):
                with self.subTest(path=path):
                    config.write_text(original.replace(
                        'model_cache_dir = ".sys4ai/memory/models"',
                        f'model_cache_dir = {json.dumps(path)}',
                    ))
                    with self.assertRaises(ConfigurationError):
                        load_configuration(config, trusted_project_root=fixture)
                    self.assertFalse((fixture / ".sys4ai").exists())
            config.write_text(original)
            (fixture / ".sys4ai").symlink_to(fixture / "elsewhere", target_is_directory=True)
            with self.assertRaises(ConfigurationError):
                load_configuration(config, trusted_project_root=fixture)
            self.assertFalse((fixture / "elsewhere").exists())


@unittest.skipUnless(RUNTIME_AVAILABLE, "Run with the installed Memory Service consumer runtime")
class DepotSourceRegistryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="sys4ai-root-sources-")
        self.addCleanup(self.temporary.cleanup)
        self.fixture = Path(self.temporary.name).resolve()
        for name in ("config", "registries", "profiles", "schemas", "control_records"):
            shutil.copytree(ROOT / name, self.fixture / name)
        loaded = load_configuration(self.fixture / "config/memory.toml", trusted_project_root=self.fixture)
        self.registry = load_registry_bundle(
            source_registry=loaded.resolved_paths["source_registry"],
            profile_registry=loaded.resolved_paths["profile_registry"],
            relation_registry=loaded.resolved_paths["relation_registry"],
            project_root=self.fixture,
        )
        self.discovery = SourceDiscovery(
            project_root=self.fixture, project_id="sys4ai-depot", entries=self.registry.sources
        )

    def write(self, path: str, text: str = "# Root-owned fixture\n") -> None:
        target = self.fixture / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)

    def test_every_approved_source_category_has_one_appropriate_rule(self) -> None:
        examples = {
            "AGENTS.md": ("active-governance", "A1"),
            "SOUL.md": ("active-governance", "A1"),
            "ROLE.md": ("active-governance", "A1"),
            "README.md": ("project-knowledge", "A3"),
            "depot/projects.json": ("inventory", "A2"),
            "Requirements/requirements.md": ("requirements", "A2"),
            "TRDs/trd.md": ("requirements-trd", "A2"),
            "Implementation_Plans/example/plan.json": ("plan-state", "A2"),
            "Verification/result.md": ("verification", "A5"),
            "Tasks/example/task.json": ("task-state", "A2"),
            ".agents/skills/fixture/SKILL.md": ("active-skills", "A2"),
            "SKILLS-depo/fixture/SKILL.md": ("reusable-skills", "A5"),
            "SOULS-depo/SOUL.md": ("reusable-souls", "A5"),
            "AGENTS-depo/AGENTS.md": ("reusable-agent-guidance", "A5"),
            "ROLES-depo/ROLE.md": ("reusable-roles", "A5"),
            "tests/test_example.py": ("tests", "A5"),
        }
        by_id = {item.source_id: item for item in self.registry.sources}
        for path, (namespace, tier) in examples.items():
            self.write(path, "{}\n" if path.endswith(".json") else "# fixture\n")
            with self.subTest(path=path):
                decision = self.discovery.explain_path(path)
                self.assertEqual("included", decision.disposition.value)
                self.assertEqual(1, len(decision.rule_ids))
                rule = by_id[decision.rule_ids[0]]
                self.assertEqual("sys4ai-depot:" + namespace, rule.namespace)
                self.assertEqual(tier, rule.authority_tier.value)
                self.assertEqual("deny", rule.write_policy)
        self.assertFalse((self.fixture / ".sys4ai").exists())

    def test_child_and_prohibited_paths_are_excluded_without_reading_them(self) -> None:
        paths = [
            "Projects/Sys4AI-Electronics-Projects/README.md",
            "Projects/unregistered-no-git/README.md",
            "Projects/registered-with-git/.git/HEAD",
            ".sys4ai/memory/receipts/initialization.json",
            ".venv/site-packages/module.py", "other/.cache/state.json",
            "models/model.json", "Verification/logs/raw.md",
            "SKILLS-depo/fixture/.env.example", "tests/credentials.json",
            "Tasks/.locks/ledger.json", "Verification/result.log",
            "Requirements/tmp/source.md", "depot/staging/data.json",
        ]
        for path in paths:
            with self.subTest(path=path):
                decision = self.discovery.explain_path(path)
                self.assertEqual("excluded", decision.disposition.value)
        self.assertFalse((self.fixture / ".sys4ai").exists())

    def test_new_folder_and_nested_tests_do_not_inherit_root_admission(self) -> None:
        self.write("Future/README.md")
        self.write("Future/tests/test_new.py", "# not registered\n")
        for path in ("Future/README.md", "Future/tests/test_new.py"):
            self.assertEqual("unmatched", self.discovery.explain_path(path).disposition.value)
        self.write("SKILLS-depo/fixture/tests/test_tool.py", "# reusable test\n")
        decision = self.discovery.explain_path("SKILLS-depo/fixture/tests/test_tool.py")
        self.assertEqual("included", decision.disposition.value)
        self.assertEqual(("src_depot_SKILLS-depo_py",), decision.rule_ids)


if __name__ == "__main__":
    unittest.main()
