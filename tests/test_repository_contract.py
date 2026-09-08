from __future__ import annotations

import json
import hashlib
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS = ROOT / "Requirements/sys4ai_synchronization_removal_requirements.md"
PLAN = ROOT / "Implementation_Plans/sys4ai_synchronization_removal_implementation_plan.md"
VERIFICATION = ROOT / "Verification/sys4ai_synchronization_removal_verification.md"
TEMPLATE = ROOT / "Projects/Sys4AI-Template-Project"


class RepositoryContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.requirements_text = REQUIREMENTS.read_text(encoding="utf-8")
        cls.plan_text = PLAN.read_text(encoding="utf-8")
        cls.verification_text = VERIFICATION.read_text(encoding="utf-8")
        cls.projects = json.loads(
            (ROOT / "depot/projects.json").read_text(encoding="utf-8")
        )

    def test_required_project_artifacts_exist(self) -> None:
        required_files = (
            "README.md",
            "SPECS.md",
            "AGENTS.md",
            "SOUL.md",
            "ROLE.md",
            "Requirements/sys4ai_synchronization_removal_requirements.md",
            "Implementation_Plans/sys4ai_synchronization_removal_implementation_plan.md",
            "Implementation_Plans/subagent_role_system_implementation_plan.md",
            "Implementation_Plans/task_system_implementation_plan.md",
            "Verification/sys4ai_synchronization_removal_verification.md",
            "Tasks/INDEX.md",
            "sub-agent-roles/project-sub-agent/AGENTS.md",
            "sub-agent-roles/project-sub-agent/ROLE.md",
            "Roles/project-sub-agent/AGENTS.md",
            "Roles/project-sub-agent/ROLE.md",
            "Roles/task-manager/AGENTS.md",
            "Roles/task-manager/ROLE.md",
            "Roles/INDEX.md",
            "depot/README.md",
            "depot/projects.json",
            "tests/test_repository_contract.py",
        )
        for relative in required_files:
            self.assertTrue((ROOT / relative).is_file(), relative)

    def test_retired_control_plane_is_absent(self) -> None:
        retired_paths = (
            ".agents/skills/sys4ai-project-sync",
            "tools/depot_sync.py",
            "tools/__pycache__/depot_sync.cpython-312.pyc",
            "tests/test_depot_sync.py",
            "tests/__pycache__/test_depot_sync.cpython-312.pyc",
            "depot/manifest.json",
            "Requirements/sys4ai_skills_soul_sync_requirements.md",
            "Implementation_Plans/sys4ai_skills_soul_sync_implementation_plan.md",
            "Requirements/sys4ai_depot_requirements.md",
            "Implementation_Plans/sys4ai_depot_implementation_plan.md",
            "Verification/sys4ai_depot_verification.md",
            "depot/contracts/subagent_role_system_implementation_plan.md",
            "depot/contracts/task_system_implementation_plan.md",
            "AGENTS-depo/sys4ai-depot-AGENTS.md",
            "ROLES-depo/sys4ai-depot-ROLE.md",
        )
        for relative in retired_paths:
            self.assertFalse((ROOT / relative).exists(), relative)

    def test_requirements_are_unique_and_fully_mapped_in_plan(self) -> None:
        identifiers = re.findall(
            r"^#### ([A-Z]{3}-\d{3}) - ",
            self.requirements_text,
            re.MULTILINE,
        )
        self.assertEqual(14, len(identifiers))
        self.assertEqual(len(identifiers), len(set(identifiers)))

        traceability = self.plan_text.split(
            "## Requirement-to-work traceability", 1
        )[1].split("## Implementation status", 1)[0]
        mapped = re.findall(
            r"^\| ([A-Z]{3}-\d{3}) \|",
            traceability,
            re.MULTILINE,
        )
        self.assertEqual(set(identifiers), set(mapped))
        self.assertEqual(len(mapped), len(set(mapped)))

        acceptance = self.verification_text.split(
            "## Requirement acceptance matrix", 1
        )[1].split("## Reverse artifact-to-requirement audit", 1)[0]
        verified = re.findall(
            r"^\| ([A-Z]{3}-\d{3}) \| Passed \|",
            acceptance,
            re.MULTILINE,
        )
        self.assertEqual(set(identifiers), set(verified))
        self.assertEqual(len(verified), len(set(verified)))

    def test_registry_is_inventory_only_and_paths_exist(self) -> None:
        self.assertEqual(2, self.projects["schema_version"])
        self.assertEqual("Sys4AI", self.projects["workspace_name"])
        entries = self.projects["projects"]
        self.assertGreaterEqual(len(entries), 2)
        self.assertTrue(
            {
                "sys4ai-depot",
                "sys4ai-template-project",
            }.issubset({entry["id"] for entry in entries}),
        )
        self.assertEqual(len(entries), len({entry["id"] for entry in entries}))
        self.assertEqual(len(entries), len({entry["path"] for entry in entries}))
        for entry in entries:
            self.assertTrue(entry["registered"])
            self.assertNotIn("managed", entry)
            self.assertTrue((ROOT / entry["path"]).is_dir(), entry["path"])
        template = next(
            entry for entry in entries if entry["id"] == "sys4ai-template-project"
        )
        self.assertEqual("Projects/Sys4AI-Template-Project", template["path"])

    def test_registered_external_state_is_truthful_and_bounded(self) -> None:
        entries = {entry["id"]: entry for entry in self.projects["projects"]}
        root_repository = entries["sys4ai-depot"]["repository"]
        self.assertEqual("initialized", root_repository["status"])
        self.assertEqual(
            "git@github-omegapy:Omegapy/Sys4AI.git",
            root_repository["remote"],
        )
        template_repository = entries["sys4ai-template-project"]["repository"]
        self.assertEqual("not_initialized", template_repository["status"])
        self.assertIsNone(template_repository["remote"])
        self.assertTrue((ROOT / ".git").exists())
        self.assertFalse((TEMPLATE / ".git").exists())
        for entry in entries.values():
            self.assertEqual("not_configured", entry["github_pages"]["status"])
            self.assertIsNone(entry["github_pages"]["url"])

    def test_reusable_assets_and_active_installations_are_preserved(self) -> None:
        expected_skills = {
            "agent-task",
            "communication",
            "manage-subagent-roles",
            "task",
            "to-implementation-plan",
            "to-trd",
        }
        source_skills = {
            path.parent.name for path in (ROOT / "SKILLS-depo").glob("*/SKILL.md")
        }
        root_skills = {
            path.parent.name for path in (ROOT / ".agents/skills").glob("*/SKILL.md")
        }
        template_skills = {
            path.parent.name for path in (TEMPLATE / ".agents/skills").glob("*/SKILL.md")
        }
        self.assertTrue(expected_skills.issubset(source_skills))
        self.assertTrue(expected_skills.issubset(root_skills))
        self.assertTrue(expected_skills.issubset(template_skills))
        self.assertEqual(source_skills, template_skills)
        self.assertIn("init-new-project", source_skills)
        self.assertIn("init-new-project", root_skills)
        self.assertIn("init-new-project", template_skills)

        for required in (
            "SOUL.md",
            "SOULS-depo/SOUL.md",
            "Tasks/INDEX.md",
            "sub-agent-roles/project-sub-agent/AGENTS.md",
            "sub-agent-roles/project-sub-agent/ROLE.md",
            "Roles/project-sub-agent/AGENTS.md",
            "Roles/project-sub-agent/ROLE.md",
            "Roles/task-manager/AGENTS.md",
            "Roles/task-manager/ROLE.md",
            "Roles/INDEX.md",
            "Projects/Sys4AI-Template-Project/SOUL.md",
            "Projects/Sys4AI-Template-Project/ROLE.md",
            "Projects/Sys4AI-Template-Project/Tasks/INDEX.md",
        ):
            self.assertTrue((ROOT / required).is_file(), required)

    def test_root_governance_is_project_local_and_preserves_core_contracts(self) -> None:
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        role = (ROOT / "ROLE.md").read_text(encoding="utf-8")
        normalized_agents = " ".join(agents.split())
        normalized_role = " ".join(role.split())

        for forbidden in (
            "depot/manifest.json",
            "depot_sync.py",
            "sys4ai-project-sync",
            "managed-source",
            "synchronized target",
        ):
            self.assertNotIn(forbidden, agents)
            self.assertNotIn(forbidden, role)

        for phrase in (
            "Sys4AI depot and multi-project",
            "depot/projects.json",
            "project-local",
            "Ordinary children return evidence without ledger or role-index writes",
            "native goal state",
        ):
            self.assertIn(phrase, normalized_agents)
        for heading in (
            "# Project Director Role",
            "## Purpose",
            "## Primary responsibilities",
            "## Workspace and depot governance",
            "## Requirements-to-verification workflow",
            "## Depot Task intake policy",
            "## Mandatory role-management skill workflow",
            "## Delegation contract and settings",
            "## Implementation and completion",
            "## Evidence and final report",
        ):
            self.assertIn(heading, role)
        self.assertIn("fresh filesystem-backed role catalog", normalized_role)
        self.assertIn("exact effective model and reasoning effort", normalized_role)
        self.assertIn("final Task Responses", normalized_role)

    def test_template_is_project_local_and_product_neutral(self) -> None:
        readme = (TEMPLATE / "README.md").read_text(encoding="utf-8")
        agents = (TEMPLATE / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("governed starter", readme)
        self.assertIn("does not define the future product", readme)
        self.assertIn("project-local", readme)
        self.assertIn("project-local", agents)
        self.assertIn("This template supplies", agents)
        self.assertIn("project-neutral", (TEMPLATE / "ROLE.md").read_text())
        for forbidden in ("depot/manifest.json", "depot_sync.py", "sys4ai-project-sync"):
            self.assertNotIn(forbidden, readme)
            self.assertNotIn(forbidden, agents)

    def test_active_guidance_has_no_stale_control_plane_reference(self) -> None:
        active_guidance = (
            ROOT / "AGENTS.md",
            ROOT / "ROLE.md",
            ROOT / "depot/README.md",
            ROOT / "Projects/README.md",
            ROOT / "AGENTS-depo/project-template-AGENTS.md",
            TEMPLATE / "AGENTS.md",
            TEMPLATE / "README.md",
        )
        forbidden = re.compile(
            r"depot_sync\.py|depot/manifest\.json|sys4ai-project-sync",
            re.IGNORECASE,
        )
        for document in active_guidance:
            text = document.read_text(encoding="utf-8")
            self.assertIsNone(forbidden.search(text), str(document))

    def test_core_markdown_links_resolve_locally(self) -> None:
        for document in (
            ROOT / "README.md",
            ROOT / "depot/README.md",
            ROOT / "depot/template-update.md",
            ROOT / "Projects/README.md",
            TEMPLATE / "README.md",
            ROOT / "SKILLS-depo/init-new-project/SKILL.md",
            ROOT / ".agents/skills/init-new-project/SKILL.md",
        ):
            text = document.read_text(encoding="utf-8")
            targets = re.findall(r"\[[^\]]+\]\(([^)]+)\)", text)
            for raw in targets:
                if raw.startswith(("http://", "https://", "#")):
                    continue
                path_text = raw.split("#", 1)[0]
                resolved = (document.parent / path_text).resolve()
                self.assertTrue(resolved.exists(), f"{document}: {raw}")

    def test_initializer_adoption_is_exact_and_preserves_existing_packages(self) -> None:
        source = ROOT / "SKILLS-depo/init-new-project"
        active = ROOT / ".agents/skills/init-new-project"
        record = json.loads((ROOT / "Verification/init-new-project-active-adoption.json").read_text())
        def manifest(folder: Path) -> dict[str, str]:
            return {
                item.relative_to(folder).as_posix(): hashlib.sha256(item.read_bytes()).hexdigest()
                for item in folder.rglob("*")
                if item.is_file() and "__pycache__" not in item.parts and item.name != ".DS_Store"
            }
        self.assertEqual(manifest(source), manifest(active))
        previous = json.loads((ROOT / "Verification/task-manager-orchestration/root-adoption-manifest.json").read_text())
        current = json.loads((ROOT / "Verification/roles-capitalization/root-adoption.json").read_text())
        licensing = json.loads((ROOT / "Verification/licenses-depot/root-adoption.json").read_text())
        self.assertEqual(licensing["initializer_files_sha256"], manifest(source))
        self.assertEqual("applied", licensing["status"])
        self.assertEqual(current["initializer_files_sha256"], licensing["previous_initializer_files_sha256"])
        self.assertNotEqual(current["initializer_files_sha256"], licensing["initializer_files_sha256"])
        self.assertEqual("applied", current["status"])
        self.assertNotEqual(previous["initializer_files_sha256"], current["initializer_files_sha256"])
        self.assertEqual("PLAN-20260908-6E6F545E", previous["plan_id"])
        # The original adoption receipt is retained with its original meaning;
        # it is not rewritten to claim the later package bytes.
        self.assertNotEqual(record["files_sha256"], current["initializer_files_sha256"])
        self.assertEqual("adopted", record["status"])
        self.assertIn("no other active skills or projects", record["overwrite_boundary"])

    def test_license_sources_root_and_template_have_complete_matching_terms(self) -> None:
        bodies = {
            "LICENSE-CODE": (11358, "cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30"),
            "LICENSE-DOCS": (18657, "9ba9550ad48438d0836ddab3da480b3b69ffa0aac7b7878b5a0039e7ab429411"),
        }
        for name in ("LICENSE", "LICENSE-CODE", "LICENSE-DOCS"):
            source = (ROOT / "LICENSES-depo" / name).read_bytes()
            self.assertEqual(source, (ROOT / name).read_bytes())
            self.assertEqual(source, (TEMPLATE / name).read_bytes())
            self.assertIn(b"Alexander Samuel Ricciardi", source)
            if name in bodies:
                size, checksum = bodies[name]
                self.assertEqual(checksum, hashlib.sha256(source[-size:]).hexdigest())

    def test_template_seed_and_setup_routes_preserve_project_boundaries(self) -> None:
        spec = json.loads((ROOT / "SKILLS-depo/init-new-project/assets/baseline-assets.json").read_text())
        expected = {"agent-task", "communication", "manage-subagent-roles", "task", "to-implementation-plan", "to-trd"}
        self.assertEqual(".agents/skills", spec["skills"])
        self.assertTrue(expected.issubset({p.name for p in (TEMPLATE / spec["skills"]).iterdir() if p.is_dir()}))
        self.assertEqual("SOUL.md", spec["soul"])
        self.assertEqual(spec, json.loads((TEMPLATE / ".template/baseline-assets.json").read_text()))
        for relative in (*spec["starter_files"], *spec["optional_starter_files"]):
            self.assertTrue((TEMPLATE / relative).is_file(), relative)
            self.assertFalse({".git", ".gitmodules", ".venv", ".sys4ai", "__pycache__", ".ruff_cache"}.intersection(Path(relative).parts))
        for relative in (".sys4ai", "config/memory.toml", "registries/memory_source_registry.csv", "control_records/project-initialization.json", "project.json", "models"):
            self.assertFalse((TEMPLATE / relative).exists(), relative)
        self.assertEqual(2, spec["schema_version"])
        self.assertNotIn("ontology", spec)
        for relative in ("Ontology", "INIT_MEMORY.md"):
            self.assertFalse((TEMPLATE / relative).exists(), relative)
        self.assertIn("[SPECS.md](./SPECS.md)", (ROOT / "README.md").read_text())
        self.assertIn("control_records/project-setup.json", (ROOT / "SPECS.md").read_text())

    def test_retired_service_files_and_entry_points_are_absent(self) -> None:
        for relative in ("ONTOLOGY-depo", "Projects/Sys4AI-Memory-Service",
                         "config/memory.toml", "config/context.toml", "control_records/memory",
                         "schemas/memory", ".sys4ai/memory", ".sys4ai/ontology-artifacts",
                         ".sys4ai/operational-verification"):
            self.assertFalse((ROOT / relative).exists(), relative)
        for command in ("sys4ai-memory", "sys4ai-ontology", "sys4ai-context"):
            self.assertFalse((ROOT / ".venv/bin" / command).exists(), command)
        self.assertNotIn("sys4ai-memory-service", {x["id"] for x in self.projects["projects"]})

    def test_state_systems_remain_separate(self) -> None:
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        role = (ROOT / "ROLE.md").read_text(encoding="utf-8")
        self.assertIn("Keep Task state separate", agents)
        self.assertIn("explicitly invokes `$to-trd`", agents)
        self.assertIn("native Codex goal", role)
        self.assertTrue((ROOT / "Tasks/INDEX.md").is_file())


if __name__ == "__main__":
    unittest.main()
