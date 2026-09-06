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
    "electronics-project": ROOT / "Projects" / "Sys4AI-Electronics-Projects",
}

ROLE_HEADINGS = (
    "## Task intake and execution-path selection",
    "## Durable orchestration record and progress gate",
    "## Task-system ownership",
    "## Mandatory role-management skill workflow",
    "## Independent adversarial candidate generation",
    "## One-to-one review and revision cycle",
    "## Senior synthesis and conflict recycling",
    "## Implementation ownership and evidence-gated completion",
    "## Role selection and role creation",
    "## Delegation contract",
    "## Model and reasoning identity",
    "## Verification and validation",
    "## Escalation and stopping conditions",
    "## Completion report",
)

ROLE_CLAUSE_GROUPS = (
    ("user-given job or problem", "existing root project director"),
    ("complexity", "uncertainty", "material unknowns", "decomposability"),
    ("direct path", "decomposed path", "adversarial path"),
    ("follow feasible explicit user instructions", "do not silently substitute"),
    ("append-only task responses", "do not introduce a second orchestration ledger"),
    ("fresh filesystem-backed role catalog", "every delegated solver"),
    ("at least two solvers", "identical packet", "different suitable role or perspective"),
    ("one-to-one mapping", "originating solver", "reviewer child"),
    ("materially revised candidate", "repeat review"),
    ("distinct senior synthesis agent", "every material review finding"),
    ("exact shared conflict record", "every affected originating solver"),
    ("case by case based on the task", "exactly one accountable implementation owner"),
    ("reopen the live artifacts", "every definition-of-done criterion"),
    ("only the project director", "agent task completion"),
    ("material hypothesis", "repeated unchanged failure", "bounded user decision"),
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
            if name == "sys4ai-root":
                continue  # Root intake was separately revised in TASK-20260904-5D29651E.
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
        # The authorized local intake change leaves the adopted execution,
        # delegation, verification and final-response contract intact.
        boundary = "## Record orchestration durably"
        self.assertEqual(source_text.split(boundary, 1)[1], root_text.split(boundary, 1)[1])
        self.assertIn("intake --match-task SELECTOR", root_text)
        self.assertIn("close-old-task", root_text)
        self.assertNotIn("Ask whether to reopen the same", root_text)
        metadata = (active / "agents" / "openai.yaml").read_text(encoding="utf-8")
        self.assertIn("allow_implicit_invocation: false", metadata)
        self.assertIn("$task", metadata)

    def test_active_task_skill_references_resolve_in_every_project(self) -> None:
        source_text = SOURCE_SKILL.read_text(encoding="utf-8")
        relative_links = [
            item
            for item in re.findall(r"\[[^]]+\]\(([^)]+)\)", source_text)
            if "://" not in item
        ]
        self.assertEqual(
            {"../agent-task/SKILL.md", "../manage-subagent-roles/SKILL.md"},
            set(relative_links),
        )
        for name, project in DESTINATIONS.items():
            skill_file = project / ".agents" / "skills" / "task" / "SKILL.md"
            for relative in relative_links:
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
        self.assertIn("generic Project Director", role)
        self.assertIn("intentionally project-neutral", role)

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

    def test_electronics_role_preserves_domain_and_safety_specialization(self) -> None:
        role = (DESTINATIONS["electronics-project"] / "ROLE.md").read_text(
            encoding="utf-8"
        )
        for text in (
            "# Electronics Project Director role",
            "## Integrated professional perspectives",
            "## Engineering and repair workflow",
            "## Safety and stop conditions",
            "energized work",
            "physical testing",
            "Never claim that a physical device",
        ):
            self.assertIn(text, role)

    def test_all_twenty_three_requirement_ids_remain_contiguous(self) -> None:
        self.assertEqual(
            [f"REQ-{number:03d}" for number in range(1, 24)],
            [item["requirement_id"] for item in self.plan["requirements"]],
        )


if __name__ == "__main__":
    unittest.main()
