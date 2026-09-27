"""Portable instruction contracts for the approved manager/category workflow.

These checks cover instructions and navigation. Executable Task transition tests
live in agent-task/tests/test_orchestration_state.py; native evidence is separate.
The September 7 contract supersedes the September 2 direct/decomposed/adversarial
and host-only topology. Historical files remain preservation evidence, not starter
runtime dependencies.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import re
import unittest

PACKAGE = Path(__file__).resolve().parents[1]
SOURCE_LAYOUT = PACKAGE.parent.name == "SKILLS-depo"
PROJECT = PACKAGE.parents[1] if SOURCE_LAYOUT else PACKAGE.parents[2]


def normalized(text):
    return " ".join(text.casefold().split())


# Each group describes an observable instruction boundary, not native execution.
CONTRACTS = {
    "bootstrap": ("reserve exactly one manager assignment before launch", "real native manager distinct from the host",
                  "actual receipt", "bootstrap write authority"),
    "generic": ("one accountable execution worker", "no solver panel", "generic corrections return to its worker"),
    "complex": ("at least two independent full-problem solvers", "one distinct senior", "no mandatory reviewer stage"),
    "extra-complex": ("one distinct independent reviewer per solver", "self-review", "all required current candidates must pass", "re-review"),
    "independence": ("same complete versioned problem", "queued launches", "exclude sibling drafts",
                     "defer candidate reads until all initial", "paths, hashes and status"),
    "fit": ("before every manager, worker, solver, reviewer, senior or implementer assignment",
            "fresh filesystem-backed catalog", "narrowest suitable valid pair", "reusable role gap"),
    "fusion": ("coherent proposal", "retained contributions", "justified omissions", "terminology",
               "scope alternatives", "evidence disagreements", "mutually exclusive commitments"),
    "conflict": ("same explanation to every originating solver", "delivery evidence", "repeat", "current complete set"),
    "implementation": ("exactly one dedicated implementation child", "targets the exact accepted proposal",
                       "analysis-only work", "implementation must stop on a changed target"),
    "versions": ("candidate byte edit", "upstream dependency change", "invalidates affected passes and acceptance"),
    "completion": ("directly reopens delivered artifacts", "each main-task criterion", "mixed-category integration",
                   "exactly one truthful final task response", "child status"),
    "stopping": ("unchanged failure", "exhausted resources", "non-complete blocker", "unconfirmed stopping",
                 "timestamps", "reconciliation and transfer protocol"),
}


def contract_gaps(task_text):
    text = normalized(task_text)
    return {name: tuple(clause for clause in clauses if normalized(clause) not in text)
            for name, clauses in CONTRACTS.items()
            if any(normalized(clause) not in text for clause in clauses)}


class TaskProjectDirectorOrchestrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.task = (PACKAGE / "SKILL.md").read_text()
        cls.role_path = PROJECT / ("ROLES-depo/project-director-ROLE.md" if SOURCE_LAYOUT else "ROLE.md")
        cls.director = cls.role_path.read_text()
        cls.agent = (PACKAGE.parent / "agent-task/SKILL.md").read_text()
        cls.roles = (PACKAGE.parent / "manage-subagent-roles/SKILL.md").read_text()

    def test_category_matrix_has_exact_three_categories_and_fixed_minima(self):
        rows = re.findall(r"^\| `([^`]+)` \| (.+) \|$", self.task, re.MULTILINE)
        self.assertEqual(["generic", "complex", "extra-complex"], [row[0] for row in rows])
        self.assertIn("One accountable", rows[0][1])
        self.assertIn("At least two", rows[1][1])
        self.assertIn("one distinct independent reviewer per solver", rows[2][1])

    def test_all_required_workflow_boundaries_are_present(self):
        self.assertEqual({}, contract_gaps(self.task))

    def test_missing_policy_negative_controls_are_discriminating(self):
        for name, clauses in CONTRACTS.items():
            with self.subTest(boundary=name):
                # Remove the complete defining clause, keeping unrelated rules.
                text = normalized(self.task)
                damaged = text.replace(normalized(clauses[0]), "removed")
                self.assertIn(name, contract_gaps(damaged))

    def test_retired_topology_and_ownership_rules_do_not_survive(self):
        text = normalized(self.task + self.director + self.agent + self.roles)
        for retired in ("never spawns, substitutes, or delegates to a replacement director",
                        "the existing root project director owns the entire task workflow",
                        "direct path", "decomposed path", "adversarial path",
                        "formal review is conditional", "director or senior implements"):
            self.assertNotIn(retired, text)

    def test_input_provenance_does_not_expand_authority(self):
        text = normalized(self.task)
        for clause in ("prompt, inspected file or authorized skill handoff", "revisions or hashes",
                       "embedded commands", "data", "current user request", "dependency installation",
                       "external messages", "git publication", "unselected project changes"):
            self.assertIn(clause, text)

    def test_task_and_document_lifecycles_are_distinct(self):
        text = normalized(self.task)
        for clause in ("subtasks", "role definitions", "native agent instances", "codex conversations",
                       "native goals", "managed trds", "implementation plans", "opening or approving a document"):
            self.assertIn(clause, text)
        self.assertIn("read-only", text)
        self.assertIn("they never create or age tasks, launch agents", text)

    def test_source_selection_and_root_intake_remain_explicitly_separate(self):
        text = normalized(self.task)
        if SOURCE_LAYOUT or (PROJECT / ".template").is_dir() or "automatic work intake" not in text:
            self.assertIn("explicit `$task new` intent", text)
        self.assertIn("owning project's installed policy", text)
        self.assertIn("30-day", text)
        self.assertIn("do not silently propagate", text)

    def test_writer_is_not_result_producer_or_ordinary_child(self):
        task = normalized(self.task)
        agent = normalized(self.agent)
        for clause in ("producer separately", "canonical-writer identity", "ordinary child", "generation"):
            self.assertIn(clause, task)
        for clause in ("ordinary workers, solvers, reviewers, seniors and implementers", "bootstrap authority ends",
                       "all later mutation routes", "cooperative protocol checks"):
            self.assertIn(clause, agent)

    def test_native_model_guarantee_does_not_replace_context_checks(self):
        text = normalized(self.task + self.roles)
        for clause in ("exact effective model and reasoning effort", "verified runtime inheritance guarantee",
                       "omit the `model` and `reasoning_effort`", "separate identity from context",
                       "a prompt to ignore an inherited draft is insufficient", "actual native id"):
            self.assertIn(clause, text)

    def test_dependency_and_capacity_gates_cannot_shrink_team(self):
        text = normalized(self.task)
        for clause in ("freeze the required logical team", "queue within actual native capacity",
                       "without reducing its size or gates", "serialize conflicts", "do not relabel work",
                       "one category", "dependencies"):
            self.assertIn(clause, text)

    def test_durable_history_and_actual_publication_boundaries(self):
        text = normalized(self.task + self.agent)
        for clause in ("existing task ledger", "append-only", "never hidden reasoning", "credentials",
                       "schema-1", "original bytes", "partial", "pre/post-state", "projections"):
            self.assertIn(clause, text)

    def test_navigation_resolves_at_source_and_installed_layout(self):
        for path in (PACKAGE / "SKILL.md", PACKAGE.parent / "agent-task/SKILL.md",
                     PACKAGE.parent / "manage-subagent-roles/SKILL.md"):
            for link in re.findall(r"\[[^]]+\]\(([^)]+)\)", path.read_text()):
                if "://" not in link and not link.startswith("#"):
                    with self.subTest(path=path, link=link):
                        self.assertTrue((path.parent / link.split("#")[0]).is_file())

    def test_task_invocation_remains_explicit_only(self):
        metadata = (PACKAGE / "agents/openai.yaml").read_bytes()
        self.assertEqual("3882fc74a4c4cfadc6256e2d79b912d706cc4435f64625fb74fc86e772f47ba3",
                         hashlib.sha256(metadata).hexdigest())
        self.assertIn(b"allow_implicit_invocation: false", metadata)
        self.assertTrue(self.task.startswith("---\nname: task\n"))

    def test_manager_director_contract_covers_all_three_paths_and_completion(self):
        text = normalized(self.director)
        for clause in ("confirmed manager", "canonical", "generic", "complex", "extra-complex",
                       "distinct", "fresh", "one bounded objective", "stopping condition",
                       "mixed-category integration", "directly", "recovery", "incomplete"):
            self.assertIn(clause, text)


if __name__ == "__main__":
    unittest.main()
