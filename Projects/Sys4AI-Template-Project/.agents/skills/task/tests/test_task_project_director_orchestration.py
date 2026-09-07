"""Contract and scenario tests for Task-triggered orchestration.

These tests inspect the reusable sources and the active root adoption. They do
not spawn native children or claim end-to-end multi-agent behavior. Separate
cross-project tests verify the Template and Electronics Project adoptions.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
import re
import shutil
import tempfile
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[3]
TASK_SKILL = PROJECT_ROOT / "SKILLS-depo" / "task" / "SKILL.md"
TASK_METADATA = PROJECT_ROOT / "SKILLS-depo" / "task" / "agents" / "openai.yaml"
DIRECTOR_ROLE = PROJECT_ROOT / "ROLES-depo" / "project-director-ROLE.md"
IMPACT_MATRIX = (
    PROJECT_ROOT
    / "Verification"
    / "task_triggered_project_director_orchestration_impact_matrix_2026-09-02.md"
)
ACTIVE_TASK_SKILL = PROJECT_ROOT / ".agents" / "skills" / "task" / "SKILL.md"

LIMITATIONS = {
    "native_child_execution": "not_exercised",
}


def normalized(text: str) -> str:
    return " ".join(text.casefold().split())


def file_digest(target: Path) -> str:
    return hashlib.sha256(target.read_bytes()).hexdigest()


def source_files(package: Path) -> dict[Path, bytes]:
    return {
        item.relative_to(package): item.read_bytes()
        for item in sorted(package.rglob("*"))
        if item.is_file() and "__pycache__" not in item.parts
    }


@dataclass(frozen=True)
class Scenario:
    name: str
    clauses: tuple[tuple[str, ...], ...]


SCENARIOS = (
    Scenario(
        "simple-direct",
        (
            ("direct path",),
            ("simple, low-risk task",),
            ("would not add material value",),
        ),
    ),
    Scenario(
        "decomposed-complex",
        (
            ("decomposed path",),
            ("dependencies", "ownership", "deliverables"),
            ("allowed scope", "protected state", "required checks"),
            ("stopping condition", "non-overlapping write ownership"),
        ),
    ),
    Scenario(
        "uncertain-adversarial",
        (
            ("adversarial path",),
            ("substantial uncertainty", "decomposition"),
            ("at least two solvers", "task-appropriate count"),
            ("same packet", "identical packet"),
            ("different suitable role or perspective",),
        ),
    ),
    Scenario(
        "user-defined-orchestration",
        (
            ("follow feasible explicit user instructions",),
            ("counts", "roles", "perspectives", "reviewers"),
            ("do not silently substitute another pattern",),
        ),
    ),
    Scenario(
        "one-to-one-review",
        (
            ("formal review is conditional",),
            ("one-to-one", "every candidate"),
            ("reviewer child", "reviewer role"),
            ("unreviewed or rejected candidate", "synthesis"),
        ),
    ),
    Scenario(
        "failed-review-revision",
        (
            ("clear failure explanation", "actionable revision requests"),
            ("originating solver child",),
            ("materially revised candidate",),
            ("review again", "repeat review"),
        ),
    ),
    Scenario(
        "all-pass-synthesis",
        (
            ("every candidate required to receive formal review", "recorded pass"),
            ("distinct senior synthesis agent",),
            ("every accepted candidate", "every material review finding"),
            ("preserves compatible contributions",),
        ),
    ),
    Scenario(
        "irreconcilable-conflict-recycle",
        (
            ("one exact shared conflict record",),
            ("same conflict explanation",),
            ("every affected originating solver",),
            ("every required review repeats",),
            ("another synthesis attempt",),
        ),
    ),
    Scenario(
        "implementation-owner",
        (
            ("case by case based on the task",),
            ("exactly one accountable implementation owner",),
            ("reject a missing or multiple-owner state",),
            ("not performed implementation",),
        ),
    ),
    Scenario(
        "evidence-gated-completion",
        (
            ("reopen the live artifacts",),
            ("every definition-of-done criterion with current direct evidence",),
            ("child report as sole proof",),
            ("exactly one truthful final task response",),
        ),
    ),
    Scenario(
        "no-progress-blocker",
        (
            ("material hypothesis", "evidence item", "targeted revision"),
            ("repeated unchanged failure",),
            ("exact blocker", "bounded user decision"),
            ("truthful stopping path", "stopping contract"),
        ),
    ),
)


REQUIREMENT_COVERAGE = {
    "REQ-001": "test_root_director_activation",
    "REQ-002": "test_task_identity_and_state_distinctions",
    "REQ-003": "test_project_director_ownership",
    "REQ-004": "test_classification_dimensions",
    "REQ-005": "test_scenario_matrix",
    "REQ-006": "test_scenario_matrix",
    "REQ-007": "test_role_selection_and_creation_boundaries",
    "REQ-008": "test_role_selection_and_creation_boundaries",
    "REQ-009": "test_scenario_matrix",
    "REQ-010": "test_scenario_matrix",
    "REQ-011": "test_scenario_matrix",
    "REQ-012": "test_scenario_matrix",
    "REQ-013": "test_scenario_matrix",
    "REQ-014": "test_scenario_matrix",
    "REQ-015": "test_scenario_matrix",
    "REQ-016": "test_scenario_matrix",
    "REQ-017": "test_durable_audit_record",
    "REQ-018": "test_state_and_authority_boundaries",
    "REQ-019": "test_scenario_matrix",
    "REQ-020": "test_required_sources_are_adopted_by_the_active_root",
    "REQ-021": "test_conditional_packages_match_impact_matrix",
    "REQ-022": "test_isolated_fixture_does_not_touch_protected_files",
    "REQ-023": "test_requirement_and_scenario_coverage_is_complete",
}


class TaskProjectDirectorOrchestrationTests(unittest.TestCase):
    maxDiff = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.task = TASK_SKILL.read_text(encoding="utf-8")
        cls.role = DIRECTOR_ROLE.read_text(encoding="utf-8")
        cls.task_normalized = normalized(cls.task)
        cls.role_normalized = normalized(cls.role)
        cls.contract = cls.task_normalized + " " + cls.role_normalized
        cls.matrix = IMPACT_MATRIX.read_text(encoding="utf-8")

    def assert_clauses(
        self,
        text: str,
        clause_groups: tuple[tuple[str, ...], ...],
    ) -> None:
        for group in clause_groups:
            with self.subTest(group=group):
                self.assertTrue(
                    all(normalized(clause) in text for clause in group),
                    f"missing contract group: {group}",
                )

    def test_root_director_activation(self) -> None:
        self.assert_clauses(
            self.task_normalized,
            (
                ("one exact project root", "agents.md", "soul.md", "role.md"),
                ("read the complete root `role.md`",),
                ("before any task mutation, classification", "role selection", "delegation"),
                ("existing root agent", "entire task workflow"),
                ("never spawns, substitutes, or delegates to a replacement director",),
            ),
        )

    def test_task_identity_and_state_distinctions(self) -> None:
        for text in (self.task_normalized, self.role_normalized):
            self.assert_clauses(
                text,
                (
                    ("user-given job or problem", "existing root project director"),
                    ("simple or complex",),
                    ("delegated subtask", "codex conversation", "native goal"),
                    ("managed trd", "implementation plan", "git state"),
                ),
            )

    def test_project_director_ownership(self) -> None:
        self.assert_clauses(
            self.role_normalized,
            (
                ("project director owns task framing", "decomposition", "role selection"),
                ("integration decisions", "final verification", "final reporting"),
                ("only the project director", "agent task completion"),
                ("child agents return evidence", "final task responses"),
            ),
        )

    def test_classification_dimensions(self) -> None:
        self.assert_clauses(
            self.role_normalized,
            (
                ("complexity", "uncertainty", "material unknowns"),
                ("decomposability", "dependency structure", "risk"),
                ("review need", "completion-evidence needs"),
                ("one proportional execution path", "evidence-based rationale"),
                ("fixed numeric threshold or fixed agent count",),
            ),
        )

    def test_scenario_matrix(self) -> None:
        for scenario in SCENARIOS:
            with self.subTest(scenario=scenario.name):
                self.assert_clauses(self.contract, scenario.clauses)

    def test_role_selection_and_creation_boundaries(self) -> None:
        self.assert_clauses(
            self.task_normalized,
            (
                ("solver", "reviewer", "senior synthesizer", "implementer"),
                ("fresh valid filesystem-backed role catalog",),
                ("objective", "capabilities", "read and write needs", "expected output"),
                ("required codex skills", "required tools", "risk", "stopping condition"),
                ("narrowest valid existing role",),
                ("reusable role-definition gap", "no valid existing role fits"),
                ("missing codex skill", "tool", "permission", "dependency"),
                ("native runtime capability", "exact diagnostic"),
            ),
        )

    def test_durable_audit_record(self) -> None:
        self.assert_clauses(
            self.task_normalized,
            (
                ("governed project task record", "append-only task responses"),
                ("do not create a second orchestration ledger",),
                ("selected workflow", "subtask contracts", "native child identifiers"),
                ("candidate-to-reviewer mappings", "revision cycles"),
                ("synthesis", "single implementation owner", "completion evidence"),
                ("work_completed", "verification_evidence", "current_summary"),
                ("next_step", "blockers", "open_questions", "relevant_files"),
            ),
        )

    def test_state_and_authority_boundaries(self) -> None:
        self.assert_clauses(
            self.task_normalized,
            (
                ("project task", "delegated subtasks", "child-agent state"),
                ("managed trds", "implementation plans", "codex conversations"),
                ("native goals", "git", "deployment", "release state"),
                ("hidden reasoning", "full transcript", "stale memory"),
                ("does not authorize destructive actions", "dependency installs"),
                ("external messages", "commits", "pushes", "publication", "deployment"),
            ),
        )

    def test_exact_inheritance_and_delegation_contract(self) -> None:
        self.assert_clauses(
            self.contract,
            (
                ("both role-file paths", "root `soul.md`"),
                ("selected `agents.md` and `role.md`",),
                ("bounded scope", "protected state", "checks", "evidence to return"),
                ("authority limits", "stopping condition"),
                ("exact project director model and reasoning-effort inheritance",),
            ),
        )

    def test_cross_package_references_resolve(self) -> None:
        destinations = re.findall(r"\[[^]]+\]\(([^)]+)\)", self.task)
        local_destinations = [item for item in destinations if "://" not in item]
        self.assertIn("../agent-task/SKILL.md", local_destinations)
        self.assertIn("../manage-subagent-roles/SKILL.md", local_destinations)
        for relative in local_destinations:
            with self.subTest(relative=relative):
                self.assertTrue((TASK_SKILL.parent / relative).resolve().is_file())

    def test_conditional_packages_match_impact_matrix(self) -> None:
        for package_name in ("agent-task", "manage-subagent-roles"):
            with self.subTest(package=package_name):
                source = PROJECT_ROOT / "SKILLS-depo" / package_name
                active = PROJECT_ROOT / ".agents" / "skills" / package_name
                self.assertEqual(source_files(source), source_files(active))
                self.assertIn(f"`SKILLS-depo/{package_name}/", self.matrix)
                dispositions = re.findall(
                    rf"^\| `SKILLS-depo/{re.escape(package_name)}/[^`]+` \| Unchanged \|",
                    self.matrix,
                    re.MULTILINE,
                )
                self.assertEqual(8, len(dispositions))

    def test_required_sources_are_adopted_by_the_active_root(self) -> None:
        self.assertIn("## Generate independent adversarial candidates", self.task)
        self.assertIn("## Senior synthesis and conflict recycling", self.role)
        self.assertEqual(TASK_SKILL.read_bytes(), ACTIVE_TASK_SKILL.read_bytes())
        self.assertEqual(
            file_digest(TASK_METADATA),
            "3882fc74a4c4cfadc6256e2d79b912d706cc4435f64625fb74fc86e772f47ba3",
        )

    def test_isolated_fixture_does_not_touch_protected_files(self) -> None:
        protected = {
            item: file_digest(item)
            for item in (
                PROJECT_ROOT / "AGENTS.md",
                PROJECT_ROOT / "SOUL.md",
                PROJECT_ROOT / "ROLE.md",
                ACTIVE_TASK_SKILL,
            )
        }
        with tempfile.TemporaryDirectory(prefix="task-orchestration-fixture-") as name:
            fixture = Path(name)
            self.assertFalse(fixture.resolve().is_relative_to(PROJECT_ROOT.resolve()))
            for filename in ("AGENTS.md", "SOUL.md", "ROLE.md"):
                (fixture / filename).write_text(f"# Fixture {filename}\n", encoding="utf-8")
            target = fixture / ".agents" / "skills" / "task"
            target.mkdir(parents=True)
            shutil.copy2(TASK_SKILL, target / "SKILL.md")
            copied = (target / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn("one exact project root", copied)
        self.assertEqual(protected, {item: file_digest(item) for item in protected})

    def test_negative_controls_detect_missing_policy_clauses(self) -> None:
        scenario = next(item for item in SCENARIOS if item.name == "implementation-owner")
        damaged = self.contract.replace("reject a missing or multiple-owner state", "")
        missing = [
            group
            for group in scenario.clauses
            if not all(normalized(clause) in damaged for clause in group)
        ]
        self.assertEqual(("reject a missing or multiple-owner state",), missing[0])

    def test_requirement_and_scenario_coverage_is_complete(self) -> None:
        self.assertEqual(
            {f"REQ-{number:03d}" for number in range(1, 24)},
            set(REQUIREMENT_COVERAGE),
        )
        for method_name in REQUIREMENT_COVERAGE.values():
            self.assertTrue(callable(getattr(self, method_name)))
        matrix_ids = re.findall(r"^\| `(REQ-\d{3})` \|", self.matrix, re.MULTILINE)
        self.assertEqual(list(REQUIREMENT_COVERAGE), matrix_ids)
        self.assertEqual(11, len(SCENARIOS))

    def test_remaining_runtime_limitations_are_explicit(self) -> None:
        self.assertEqual(
            {
                "native_child_execution": "not_exercised",
            },
            LIMITATIONS,
        )


if __name__ == "__main__":
    unittest.main()
