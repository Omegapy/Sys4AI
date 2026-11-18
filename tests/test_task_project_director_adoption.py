"""Cross-project checks for Task-triggered Project Director adoption."""

from __future__ import annotations

import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
SOURCE_SKILL = ROOT / "SKILLS-depo" / "task" / "SKILL.md"
SOURCE_METADATA = ROOT / "SKILLS-depo" / "task" / "agents" / "openai.yaml"
SOURCE_ROLE = ROOT / "ROLES-depo" / "project-director-ROLE.md"
PLAN = (
    ROOT
    / "Implementation_Plans"
    / "Plan_task-triggered-project-director-orchestration_2026-09-02_2C15FED4"
    / "plan.json"
)

DESTINATIONS = {
    "sys4ai-root": ROOT,
    "template-project": ROOT / "Projects" / "Sys4AI-Template-Project",
}
ELECTRONICS_PATH = Path("Projects") / "Sys4AI-Electronics-Projects"
ADOPTION_REPORT = (
    ROOT
    / "Verification"
    / "task_triggered_project_director_orchestration_adoption_verification_2026-09-02.md"
)
ORCHESTRATION_EVIDENCE = ROOT / "Verification" / "task-manager-orchestration"

ROLE_HEADINGS = (
    "## Authority and non-authority", "## Task activation and ownership",
    "## Task decomposition and categories", "## Candidate review and senior synthesis",
    "## Implementation and completion", "## Mandatory role-management skill workflow",
    "## Delegation contract and settings", "## Supervision, stopping and recovery",
    "## Evidence and final report",
)
ROLE_CLAUSE_GROUPS = (
    ("confirmed manager", "canonical writer", "bootstrap"),
    ("generic", "one worker", "complex", "extra-complex"),
    ("at least two", "one distinct", "one-to-one"),
    ("sibling drafts", "queued", "paths, hashes and status"),
    ("same", "conflict", "all originating solvers", "review"),
    ("exactly one dedicated implementation child", "analysis-only"),
    ("candidate-byte edits", "dependency changes", "invalidate"),
    ("mixed-category integration", "directly", "final task response"),
    ("actual native", "reconcile", "unconfirmed", "non-overlapping"),
)


def normalized(text: str) -> str:
    return " ".join(text.casefold().split())


class TaskProjectDirectorAdoptionTests(unittest.TestCase):
    maxDiff = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.source_skill = SOURCE_SKILL.read_bytes()
        cls.source_metadata = SOURCE_METADATA.read_bytes()
        cls.source_role = SOURCE_ROLE.read_bytes()
        cls.plan = json.loads(PLAN.read_text(encoding="utf-8"))

    def test_completed_plan_is_the_adoption_source(self) -> None:
        self.assertEqual("PLAN-20260902-2C15FED4", self.plan["plan_id"])
        self.assertEqual("completed", self.plan["status"])
        self.assertEqual(84, self.plan["revision"])
        self.assertEqual(5, len(self.plan["phases"]))
        self.assertTrue(all(item["status"] == "completed" for item in self.plan["phases"]))
        self.assertEqual(16, len(self.plan["tasks"]))
        self.assertTrue(all(item["status"] == "completed" for item in self.plan["tasks"]))
        self.assertEqual(23, len(self.plan["requirements"]))
        self.assertTrue(
            all(item["status"] == "satisfied" for item in self.plan["requirements"])
        )

    def test_unchanged_child_task_skills_match_their_adopted_source(self) -> None:
        for name, project in DESTINATIONS.items():
            if name != "template-project":
                continue  # Only the Template adopts common sources automatically.
            with self.subTest(project=name):
                skill_root = project / ".agents" / "skills" / "task"
                self.assertEqual(self.source_skill, (skill_root / "SKILL.md").read_bytes())
                self.assertEqual(
                    self.source_metadata,
                    (skill_root / "agents" / "openai.yaml").read_bytes(),
                )

    def test_root_task_revision_preserves_the_adopted_orchestration_contract(self) -> None:
        active = ROOT / ".agents" / "skills" / "task"
        root_text = (active / "SKILL.md").read_text(encoding="utf-8")
        source_text = self.source_skill.decode("utf-8")
        # The Template has its own Curator selection and handoff guidance.
        # Compare the entire shared manager and collaboration sections.
        bootstrap = "\n## Bootstrap and the real manager\n"
        template_curator_headings = {
            "## Explicit Curator Task provenance",
            "## Existing Curator awareness and conversational handoff",
        }
        source_sections = re.split(
            r"(?=^## )", source_text.split(bootstrap, 1)[1], flags=re.MULTILINE
        )
        shared_contract = "".join(
            section for section in source_sections
            if section.partition("\n")[0] not in template_curator_headings
        )
        self.assertEqual(shared_contract, root_text.split(bootstrap, 1)[1])
        self.assertIn("intake --match-task SELECTOR", root_text)
        self.assertIn("close-old-task", root_text)
        self.assertNotIn("Ask whether to reopen the same", root_text)
        metadata = (active / "agents" / "openai.yaml").read_text(encoding="utf-8")
        self.assertIn("allow_implicit_invocation: false", metadata)
        self.assertIn("$task", metadata)

    def test_active_task_skill_references_resolve_in_every_project(self) -> None:
        required_links = {
            "../agent-task/SKILL.md",
            "../manage-subagent-roles/SKILL.md",
            "../agent-task/references/orchestration-contract.md",
            "references/memory-context.md",
            "../collaborate/SKILL.md",
        }
        for name, project in DESTINATIONS.items():
            skill_file = project / ".agents" / "skills" / "task" / "SKILL.md"
            target_links = re.findall(
                r"\[[^]]+\]\(([^)]+)\)", skill_file.read_text(encoding="utf-8")
            )
            relative_links = {item for item in target_links if "://" not in item}
            with self.subTest(project=name):
                self.assertLessEqual(required_links, relative_links)
            for relative in sorted(relative_links):
                with self.subTest(project=name, relative=relative):
                    self.assertTrue((skill_file.parent / relative).resolve().is_file())

    def test_every_project_role_contains_the_orchestration_contract(self) -> None:
        for name, project in DESTINATIONS.items():
            role = (project / "ROLE.md").read_text(encoding="utf-8")
            contract = normalized(
                (project / ".agents" / "skills" / "task" / "SKILL.md").read_text(
                    encoding="utf-8"
                )
                + "\n"
                + role
            )
            for heading in ROLE_HEADINGS:
                with self.subTest(project=name, heading=heading):
                    self.assertEqual(1, role.count(heading))
            for clauses in ROLE_CLAUSE_GROUPS:
                with self.subTest(project=name, clauses=clauses):
                    self.assertTrue(
                        all(normalized(clause) in contract for clause in clauses),
                        f"{name} missing clause group {clauses}",
                    )

    def test_template_uses_the_generic_reusable_role_exactly(self) -> None:
        template = DESTINATIONS["template-project"]
        self.assertEqual(self.source_role, (template / "ROLE.md").read_bytes())
        role = (template / "ROLE.md").read_text(encoding="utf-8")
        self.assertIn("Project Director", role)
        self.assertIn("project-neutral", role)

    def test_root_preserves_workspace_and_depot_governance(self) -> None:
        role = (ROOT / "ROLE.md").read_text(encoding="utf-8")
        for text in (
            "Sys4AI depot and multi-project workspace",
            "## Workspace and depot governance",
            "depot/projects.json",
            "## Requirements-to-verification workflow",
            "reusable source collections",
        ):
            self.assertIn(text, role)

    def test_electronics_adoption_records_domain_and_safety_preservation(self) -> None:
        # The independent Electronics project was a historical adoption target.
        # The root repository retains its adoption and preservation evidence.
        report = ADOPTION_REPORT.read_text(encoding="utf-8")
        role_path = (ELECTRONICS_PATH / "ROLE.md").as_posix()
        rows = [
            row for row in report.splitlines() if row.startswith(f"| `{role_path}` |")
        ]
        self.assertEqual(1, len(rows))
        self.assertIn("Reusable orchestration sections merged", rows[0])
        self.assertIn(
            "engineering, energized-work, and physical-safety rules preserved", rows[0]
        )
        preservation = normalized(
            report.split("## Preservation audit\n", 1)[1].split("\n## ", 1)[0]
        )
        self.assertIn("electronics role retains its professional perspectives", preservation)
        self.assertRegex(preservation, r"\bno-unobserved-physical-\s*test rule\b")
        self.assertIn("energized-work authority limits", preservation)

    def test_unselected_electronics_adoption_is_recorded_in_release_evidence(self) -> None:
        # The reviewed publication used these bytes as protected inputs and
        # published only the selected implementation scope.
        expected = {
            "ROLE.md": "ab5b659b8e4427abfd5e7484ce803aad6675be8771e72ba25f8e4ceeb2847055",
            ".agents/skills/task/SKILL.md": "836b025334143f912975ed076027fd22d4cbaf5c96e26104fa45f3f7d4fed023",
            ".agents/skills/task/agents/openai.yaml": "3882fc74a4c4cfadc6256e2d79b912d706cc4435f64625fb74fc86e772f47ba3",
        }
        baseline = json.loads(
            (ORCHESTRATION_EVIDENCE / "baseline-and-adoption-manifest.json").read_text(
                encoding="utf-8"
            )
        )
        protected = baseline["preserved"][f"{ELECTRONICS_PATH.as_posix()}/"]["files"]
        self.assertEqual(expected, {path: protected[path] for path in expected})
        publication = json.loads(
            (ORCHESTRATION_EVIDENCE / "git-publication-scope.json").read_text(encoding="utf-8")
        )
        staged = publication["staged_snapshot_validation"]
        supplied_inputs = {
            Path(item["path"]).relative_to(ELECTRONICS_PATH).as_posix(): item["sha256"]
            for item in staged["supplied_workspace_inputs"]
            if Path(item["path"]).is_relative_to(ELECTRONICS_PATH)
        }
        self.assertEqual(expected, supplied_inputs)
        self.assertEqual(0, staged["retry_exit_code"])
        self.assertFalse(
            any(
                Path(item["path"]).is_relative_to(ELECTRONICS_PATH)
                for item in publication["files"]
            )
        )

    def test_all_twenty_three_requirement_ids_remain_contiguous(self) -> None:
        self.assertEqual(
            [f"REQ-{number:03d}" for number in range(1, 24)],
            [item["requirement_id"] for item in self.plan["requirements"]],
        )


if __name__ == "__main__":
    unittest.main()
