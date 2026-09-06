from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.util
import io
import json
import os
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "role_catalog.py"
PROJECT_ROOT = Path(__file__).resolve().parents[4]
SPEC = importlib.util.spec_from_file_location("role_catalog_under_test", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"could not load role catalog helper: {SCRIPT_PATH}")
role_catalog = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = role_catalog
SPEC.loader.exec_module(role_catalog)


VALID_AGENT_TEXT = """# Sub-Agent Instructions

## Required first reads

Before performing delegated work:

1. Read the [project soul](../../SOUL.md).
2. Read this sub-agent's [role definition](./ROLE.md).
3. Read the complete delegation contract supplied by the Project Director.

## Delegated-work rules

- Work only on the delegated objective and scope.
- Preserve authority limits and the stopping condition.
- Return evidence and checks to the Project Director.
- Keep the exact model and reasoning effort inherited from the Project Director.
- Do not create nested sub-agents unless the Project Director authorizes it.
"""

ROLE_HEADINGS = (
    "Purpose",
    "Suitable tasks",
    "Capabilities",
    "Tasks outside the role",
    "Required Codex skills",
    "Expected inputs",
    "Expected outputs",
    "Working method",
    "Validation responsibilities",
    "Authority limits",
    "Escalation and stopping conditions",
    "Result-reporting contract",
)


def valid_role_text(
    name: str,
    description: str | None = None,
    title: str = "Fixture Role",
) -> str:
    selection = description or (
        "Use for bounded fixture work when no narrower test role is required."
    )
    sections = "\n\n".join(
        f"## {heading}\n\nSubstantive fixture content for {heading.lower()}."
        for heading in ROLE_HEADINGS
    )
    return (
        f"---\nname: {name}\ndescription: {selection}\n---\n\n# {title}\n\n{sections}\n"
    )


class RoleCatalogTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        (self.root / "SOUL.md").write_text("# Fixture soul\n", encoding="utf-8")
        self.role_root = self.root / "sub-agent-roles"
        self.role_root.mkdir()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def make_bundle(
        self,
        folder_name: str,
        *,
        metadata_name: str | None = None,
        description: str | None = None,
        agents_text: str | None = VALID_AGENT_TEXT,
        role_text: str | None = None,
    ) -> Path:
        role_dir = self.role_root / folder_name
        role_dir.mkdir()
        if agents_text is not None:
            (role_dir / "AGENTS.md").write_text(agents_text, encoding="utf-8")
        if role_text is not None:
            (role_dir / "ROLE.md").write_text(role_text, encoding="utf-8")
        elif metadata_name is not None or folder_name:
            (role_dir / "ROLE.md").write_text(
                valid_role_text(
                    metadata_name or folder_name,
                    description=description,
                ),
                encoding="utf-8",
            )
        return role_dir

    def creation_args(
        self,
        name: str = "documentation-reviewer",
        required_skills: list[str] | None = None,
    ) -> argparse.Namespace:
        return argparse.Namespace(
            name=name,
            title="Documentation Reviewer Role",
            description=(
                "Use for source-grounded documentation review, not for "
                "application implementation."
            ),
            purpose="Review documentation against authoritative project sources.",
            suitable_task=["Review documentation against supplied sources."],
            capability=["Source-grounded documentation review."],
            outside_task=["Application-code implementation."],
            required_skill=required_skills,
            expected_input=["The document and its authoritative sources."],
            expected_output=["Findings with exact file references."],
            working_method=["Compare each material claim with its source."],
            validation_duty=["Verify every finding against the current file."],
            authority_limit=["Do not edit files unless explicitly authorized."],
            escalation_condition=["Stop when an authoritative source is missing."],
            format="json",
        )

    def snapshot(self) -> dict[str, str]:
        result: dict[str, str] = {}
        for item in sorted(self.root.rglob("*")):
            relative = item.relative_to(self.root).as_posix()
            if item.is_file() and not item.is_symlink():
                digest = hashlib.sha256(item.read_bytes()).hexdigest()
                result[relative] = f"file:{digest}"
            elif item.is_symlink():
                result[relative] = f"symlink:{os.readlink(item)}"
            elif item.is_dir():
                result[relative] = "directory"
        return result

    def test_t001_empty_role_root_is_a_valid_empty_catalog(self) -> None:
        catalog = role_catalog.build_catalog(self.root)
        self.assertEqual([], catalog.valid_roles)
        self.assertEqual([], catalog.invalid_roles)

    def test_t002_complete_bundle_returns_both_paths(self) -> None:
        self.make_bundle("project-sub-agent")
        catalog = role_catalog.build_catalog(self.root)
        self.assertEqual(1, len(catalog.valid_roles))
        entry = catalog.valid_roles[0]
        self.assertEqual(
            "sub-agent-roles/project-sub-agent/AGENTS.md", entry.agents_file
        )
        self.assertEqual("sub-agent-roles/project-sub-agent/ROLE.md", entry.role_file)

    def test_t003_missing_agents_file_is_invalid(self) -> None:
        self.make_bundle("missing-agents", agents_text=None)
        catalog = role_catalog.build_catalog(self.root)
        self.assertFalse(catalog.valid_roles)
        self.assertIn(
            "regular AGENTS.md", " ".join(catalog.invalid_roles[0].diagnostics)
        )

    def test_t004_missing_role_file_is_invalid(self) -> None:
        role_dir = self.role_root / "missing-role"
        role_dir.mkdir()
        (role_dir / "AGENTS.md").write_text(VALID_AGENT_TEXT, encoding="utf-8")
        catalog = role_catalog.build_catalog(self.root)
        self.assertFalse(catalog.valid_roles)
        self.assertIn("regular ROLE.md", " ".join(catalog.invalid_roles[0].diagnostics))

    def test_t005_missing_frontmatter_is_invalid(self) -> None:
        self.make_bundle(
            "no-frontmatter",
            role_text="# Fixture Role\n\nNo frontmatter.\n",
        )
        diagnostics = role_catalog.build_catalog(self.root).invalid_roles[0].diagnostics
        self.assertIn("must start with YAML frontmatter", " ".join(diagnostics))

    def test_t006_empty_metadata_name_is_invalid(self) -> None:
        text = valid_role_text("empty-name").replace("name: empty-name", "name:")
        self.make_bundle("empty-name", role_text=text)
        diagnostics = role_catalog.build_catalog(self.root).invalid_roles[0].diagnostics
        self.assertIn("metadata field is empty: name", diagnostics)

    def test_t007_empty_description_is_invalid(self) -> None:
        text = valid_role_text("empty-description").replace(
            "description: Use for bounded fixture work when no narrower test role is required.",
            "description:",
        )
        self.make_bundle("empty-description", role_text=text)
        diagnostics = role_catalog.build_catalog(self.root).invalid_roles[0].diagnostics
        self.assertIn("metadata field is empty: description", diagnostics)

    def test_t008_metadata_name_must_match_folder(self) -> None:
        self.make_bundle("folder-name", metadata_name="different-name")
        diagnostics = role_catalog.build_catalog(self.root).invalid_roles[0].diagnostics
        self.assertIn(
            "metadata name does not match the role directory", " ".join(diagnostics)
        )

    def test_t009_duplicate_metadata_names_report_all_locations(self) -> None:
        self.make_bundle("first-folder", metadata_name="shared-role")
        self.make_bundle("second-folder", metadata_name="shared-role")
        catalog = role_catalog.build_catalog(self.root)
        self.assertFalse(catalog.valid_roles)
        self.assertEqual(2, len(catalog.invalid_roles))
        for entry in catalog.invalid_roles:
            diagnostic_text = " ".join(entry.diagnostics)
            self.assertIn("duplicate role name", diagnostic_text)
            self.assertIn("first-folder", diagnostic_text)
            self.assertIn("second-folder", diagnostic_text)

    def test_t010_broken_root_soul_link_is_invalid(self) -> None:
        agents_text = VALID_AGENT_TEXT.replace("../../SOUL.md", "../../MISSING.md")
        self.make_bundle("broken-soul", agents_text=agents_text)
        diagnostics = role_catalog.build_catalog(self.root).invalid_roles[0].diagnostics
        self.assertIn("missing required link: ../../SOUL.md", " ".join(diagnostics))

    def test_t011_broken_local_role_link_is_invalid(self) -> None:
        agents_text = VALID_AGENT_TEXT.replace("./ROLE.md", "./OTHER.md")
        self.make_bundle("broken-role-link", agents_text=agents_text)
        diagnostics = role_catalog.build_catalog(self.root).invalid_roles[0].diagnostics
        self.assertIn("missing required link: ./ROLE.md", " ".join(diagnostics))

    def test_t012_multiple_roles_are_sorted_by_name_then_folder(self) -> None:
        self.make_bundle("zeta-role")
        self.make_bundle("alpha-role")
        catalog = role_catalog.build_catalog(self.root)
        self.assertEqual(
            ["alpha-role", "zeta-role"],
            [entry.name for entry in catalog.valid_roles],
        )

    def test_t013_markdown_output_has_required_columns_and_paths(self) -> None:
        self.make_bundle("project-sub-agent")
        rendered = role_catalog.catalog_markdown(role_catalog.build_catalog(self.root))
        self.assertIn(
            "| Role | Description | Folder | AGENTS.md | ROLE.md | State |", rendered
        )
        self.assertIn("sub-agent-roles/project-sub-agent/AGENTS.md", rendered)
        self.assertIn("sub-agent-roles/project-sub-agent/ROLE.md", rendered)

    def test_t014_json_output_has_versioned_contract(self) -> None:
        self.make_bundle("project-sub-agent")
        payload = role_catalog.build_catalog(self.root).to_dict()
        serialized = json.loads(json.dumps(payload))
        self.assertEqual(1, serialized["schema_version"])
        self.assertEqual("sub-agent-roles", serialized["role_root"])
        self.assertTrue(serialized["valid_roles"][0]["valid"])
        self.assertEqual([], serialized["invalid_roles"])

    def test_t015_inventory_does_not_write(self) -> None:
        self.make_bundle("project-sub-agent")
        before = self.snapshot()
        role_catalog.build_catalog(self.root)
        after = self.snapshot()
        self.assertEqual(before, after)

    def test_t016_create_builds_and_validates_both_files(self) -> None:
        entry, catalog = role_catalog.create_role(self.root, self.creation_args())
        target = self.role_root / "documentation-reviewer"
        self.assertTrue((target / "AGENTS.md").is_file())
        self.assertTrue((target / "ROLE.md").is_file())
        self.assertTrue(entry.valid)
        self.assertEqual(1, len(catalog.valid_roles))
        self.assertNotIn("{{", (target / "ROLE.md").read_text(encoding="utf-8"))

    def test_t017_create_existing_target_fails_without_changes(self) -> None:
        role_catalog.create_role(self.root, self.creation_args())
        before = self.snapshot()
        with self.assertRaisesRegex(role_catalog.CatalogError, "already exists"):
            role_catalog.create_role(self.root, self.creation_args())
        self.assertEqual(before, self.snapshot())

    def test_t018_traversal_hidden_and_opaque_names_are_rejected(self) -> None:
        for name in ("../escape", ".hidden-role", "Agent-Role", "agent-1"):
            with self.subTest(name=name):
                args = self.creation_args(name=name)
                with self.assertRaises(role_catalog.CatalogError):
                    role_catalog.create_role(self.root, args)
        self.assertEqual([], list(self.role_root.iterdir()))

    def test_t019_show_existing_role_does_not_create_a_role(self) -> None:
        self.make_bundle("project-sub-agent")
        before = self.snapshot()
        catalog = role_catalog.build_catalog(self.root)
        entry = role_catalog.find_valid_role(catalog, "project-sub-agent")
        self.assertEqual("project-sub-agent", entry.name)
        self.assertEqual(before, self.snapshot())

    def test_t020_reusable_gap_can_create_a_second_valid_role(self) -> None:
        self.make_bundle("project-sub-agent")
        role_catalog.create_role(self.root, self.creation_args())
        catalog = role_catalog.build_catalog(self.root)
        self.assertEqual(
            ["documentation-reviewer", "project-sub-agent"],
            [entry.name for entry in catalog.valid_roles],
        )

    def test_t021_declared_missing_skill_is_not_installed(self) -> None:
        role_catalog.create_role(
            self.root,
            self.creation_args(required_skills=["not-installed-fixture-skill"]),
        )
        role_text = (self.role_root / "documentation-reviewer" / "ROLE.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("- not-installed-fixture-skill", role_text)
        self.assertFalse((self.root / ".agents" / "skills").exists())

    def test_t022_list_command_is_read_only(self) -> None:
        self.make_bundle("project-sub-agent")
        before = self.snapshot()
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            result = role_catalog.main(
                ["--repo-root", str(self.root), "list", "--format", "json"]
            )
        self.assertEqual(0, result)
        self.assertEqual(before, self.snapshot())
        self.assertIn('"valid_roles"', stdout.getvalue())

    def test_t023_create_command_creates_only_the_role_bundle(self) -> None:
        args = self.creation_args()
        role_catalog.create_role(self.root, args)
        created = sorted(
            item.relative_to(self.root).as_posix()
            for item in self.root.rglob("*")
            if item.is_file()
        )
        self.assertEqual(
            [
                "SOUL.md",
                "sub-agent-roles/documentation-reviewer/AGENTS.md",
                "sub-agent-roles/documentation-reviewer/ROLE.md",
            ],
            created,
        )

    def test_missing_role_root_fails_closed(self) -> None:
        self.role_root.rmdir()
        with self.assertRaisesRegex(role_catalog.CatalogError, "does not exist"):
            role_catalog.build_catalog(self.root)

    def test_unknown_frontmatter_field_is_invalid(self) -> None:
        text = valid_role_text("unknown-field").replace(
            "description:", "version: 1\ndescription:"
        )
        self.make_bundle("unknown-field", role_text=text)
        diagnostics = role_catalog.build_catalog(self.root).invalid_roles[0].diagnostics
        self.assertIn("unsupported ROLE.md metadata field: version", diagnostics)

    def test_duplicate_frontmatter_field_is_invalid(self) -> None:
        text = valid_role_text("duplicate-field").replace(
            "description:", "name: duplicate-field\ndescription:"
        )
        self.make_bundle("duplicate-field", role_text=text)
        diagnostics = role_catalog.build_catalog(self.root).invalid_roles[0].diagnostics
        self.assertIn("duplicate ROLE.md metadata field: name", diagnostics)

    def test_missing_required_role_section_is_invalid(self) -> None:
        text = valid_role_text("missing-section").replace(
            "## Authority limits", "## Different limits"
        )
        self.make_bundle("missing-section", role_text=text)
        diagnostics = role_catalog.build_catalog(self.root).invalid_roles[0].diagnostics
        self.assertIn(
            "ROLE.md is missing required section: Authority limits", diagnostics
        )

    def test_empty_required_role_section_is_invalid(self) -> None:
        text = valid_role_text("empty-section").replace(
            "## Capabilities\n\nSubstantive fixture content for capabilities.",
            "## Capabilities\n",
        )
        self.make_bundle("empty-section", role_text=text)
        diagnostics = role_catalog.build_catalog(self.root).invalid_roles[0].diagnostics
        self.assertIn("ROLE.md section is empty: Capabilities", diagnostics)

    def test_role_directory_symlink_is_invalid(self) -> None:
        source = self.root / "source-role"
        source.mkdir()
        (source / "AGENTS.md").write_text(VALID_AGENT_TEXT, encoding="utf-8")
        (source / "ROLE.md").write_text(
            valid_role_text("linked-role"), encoding="utf-8"
        )
        link = self.role_root / "linked-role"
        try:
            link.symlink_to(source, target_is_directory=True)
        except (NotImplementedError, OSError) as exc:
            self.skipTest(f"symlinks unavailable: {exc}")
        diagnostics = role_catalog.build_catalog(self.root).invalid_roles[0].diagnostics
        self.assertIn("role directory must not be a symbolic link", diagnostics)

    def test_role_file_symlink_is_invalid(self) -> None:
        role_dir = self.role_root / "linked-file"
        role_dir.mkdir()
        (role_dir / "AGENTS.md").write_text(VALID_AGENT_TEXT, encoding="utf-8")
        source = self.root / "role-source.md"
        source.write_text(valid_role_text("linked-file"), encoding="utf-8")
        try:
            (role_dir / "ROLE.md").symlink_to(source)
        except (NotImplementedError, OSError) as exc:
            self.skipTest(f"symlinks unavailable: {exc}")
        diagnostics = role_catalog.build_catalog(self.root).invalid_roles[0].diagnostics
        self.assertIn("role bundle requires one regular ROLE.md", diagnostics)

    def test_validate_command_is_nonzero_for_invalid_roles(self) -> None:
        self.make_bundle("missing-agents", agents_text=None)
        with contextlib.redirect_stdout(io.StringIO()):
            result = role_catalog.main(
                ["--repo-root", str(self.root), "validate", "--format", "json"]
            )
        self.assertEqual(1, result)

    def test_list_command_reports_invalid_roles_but_returns_zero(self) -> None:
        self.make_bundle("missing-agents", agents_text=None)
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            result = role_catalog.main(
                ["--repo-root", str(self.root), "list", "--format", "json"]
            )
        self.assertEqual(0, result)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(1, len(payload["invalid_roles"]))

    def test_show_invalid_role_fails_closed(self) -> None:
        self.make_bundle("missing-agents", agents_text=None)
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            result = role_catalog.main(
                ["--repo-root", str(self.root), "show", "missing-agents"]
            )
        self.assertEqual(2, result)
        self.assertIn("role is invalid", stderr.getvalue())

    def test_create_rolls_back_when_template_has_placeholder(self) -> None:
        original_reader = role_catalog.read_template

        def broken_reader(skill_root: Path, filename: str) -> str:
            value = original_reader(skill_root, filename)
            if filename == "ROLE.md.template":
                return value + "\n{{UNRESOLVED}}\n"
            return value

        with (
            mock.patch.object(role_catalog, "read_template", broken_reader),
            self.assertRaisesRegex(role_catalog.CatalogError, "unresolved placeholder"),
        ):
            role_catalog.create_role(self.root, self.creation_args())
        self.assertFalse((self.role_root / "documentation-reviewer").exists())
        self.assertFalse(
            any(item.name.startswith(".creating-") for item in self.role_root.iterdir())
        )

    def test_description_requires_a_selection_boundary(self) -> None:
        args = self.creation_args()
        args.description = "Performs documentation review across project materials."
        with self.assertRaisesRegex(role_catalog.CatalogError, "selection boundary"):
            role_catalog.create_role(self.root, args)

    def test_role_root_symlink_escape_is_rejected(self) -> None:
        self.role_root.rmdir()
        outside = Path(tempfile.mkdtemp())
        try:
            try:
                self.role_root.symlink_to(outside, target_is_directory=True)
            except (NotImplementedError, OSError) as exc:
                self.skipTest(f"symlinks unavailable: {exc}")
            with self.assertRaisesRegex(role_catalog.CatalogError, "escapes"):
                role_catalog.build_catalog(self.root)
        finally:
            if self.role_root.is_symlink():
                self.role_root.unlink()
            Path(outside).rmdir()

    def test_helper_uses_only_standard_library_imports(self) -> None:
        source = SCRIPT_PATH.read_text(encoding="utf-8")
        self.assertNotIn("import yaml", source)
        self.assertNotIn("from yaml", source)
        self.assertNotIn("subprocess", source)

    def test_repeated_required_role_section_is_invalid(self) -> None:
        text = valid_role_text("repeated-section") + (
            "\n## Capabilities\n\nA repeated capabilities section.\n"
        )
        self.make_bundle("repeated-section", role_text=text)
        diagnostics = role_catalog.build_catalog(self.root).invalid_roles[0].diagnostics
        self.assertIn("ROLE.md repeats required section: Capabilities", diagnostics)

    def test_create_quotes_yaml_description_with_colon(self) -> None:
        args = self.creation_args()
        args.description = (
            "Use for documentation review when the boundary is: do not edit code."
        )
        entry, _ = role_catalog.create_role(self.root, args)
        self.assertTrue(entry.valid)
        role_text = (self.role_root / "documentation-reviewer" / "ROLE.md").read_text(
            encoding="utf-8"
        )
        self.assertIn('description: "Use for documentation review', role_text)

    def test_create_command_line_parses_creates_validates_and_relists(self) -> None:
        stdout = io.StringIO()
        argv = [
            "--repo-root",
            str(self.root),
            "create",
            "documentation-reviewer",
            "--title",
            "Documentation Reviewer Role",
            "--description",
            "Use for documentation review, not for code implementation.",
            "--purpose",
            "Review documentation against authoritative sources.",
            "--suitable-task",
            "Review documentation.",
            "--capability",
            "Source-grounded review.",
            "--outside-task",
            "Code implementation.",
            "--expected-input",
            "Documentation and sources.",
            "--expected-output",
            "Evidence-backed findings.",
            "--working-method",
            "Compare claims with sources.",
            "--validation-duty",
            "Verify each finding.",
            "--authority-limit",
            "Do not edit without authority.",
            "--escalation-condition",
            "Stop when a source is missing.",
            "--format",
            "json",
        ]
        with contextlib.redirect_stdout(stdout):
            result = role_catalog.main(argv)
        self.assertEqual(0, result)
        payload = json.loads(stdout.getvalue())
        self.assertEqual("documentation-reviewer", payload["created_role"]["name"])
        self.assertEqual(1, len(payload["valid_roles"]))
        self.assertEqual([], payload["invalid_roles"])


class ImplementationContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.plan = (
            PROJECT_ROOT
            / "Implementation_Plans"
            / "subagent_role_system_implementation_plan.md"
        ).read_text(encoding="utf-8")
        cls.root_agents = (PROJECT_ROOT / "AGENTS.md").read_text(encoding="utf-8")
        cls.director = (PROJECT_ROOT / "ROLE.md").read_text(encoding="utf-8")
        cls.role_agents = (
            PROJECT_ROOT / "sub-agent-roles" / "project-sub-agent" / "AGENTS.md"
        ).read_text(encoding="utf-8")
        cls.role = (
            PROJECT_ROOT / "sub-agent-roles" / "project-sub-agent" / "ROLE.md"
        ).read_text(encoding="utf-8")
        cls.skill = (
            PROJECT_ROOT / ".agents" / "skills" / "manage-subagent-roles" / "SKILL.md"
        ).read_text(encoding="utf-8")
        cls.schema = (
            PROJECT_ROOT
            / ".agents"
            / "skills"
            / "manage-subagent-roles"
            / "references"
            / "role-schema.md"
        ).read_text(encoding="utf-8")

    def test_plan_contains_all_unique_contiguous_formal_requirements(self) -> None:
        identifiers = re.findall(
            r"^- \*\*([A-Z]{3}-\d{3}):\*\*",
            self.plan,
            flags=re.MULTILINE,
        )
        expected_counts = {
            "DIR": 18,
            "ROL": 15,
            "GEN": 10,
            "MET": 15,
            "FIT": 11,
            "SKL": 20,
            "CRT": 14,
            "SPN": 16,
            "VER": 16,
        }
        self.assertEqual(135, len(identifiers))
        self.assertEqual(len(identifiers), len(set(identifiers)))
        for prefix, count in expected_counts.items():
            expected = {f"{prefix}-{number:03d}" for number in range(1, count + 1)}
            self.assertEqual(
                expected,
                {
                    identifier
                    for identifier in identifiers
                    if identifier.startswith(prefix)
                },
            )

    def test_director_role_contains_every_required_operating_section(self) -> None:
        required_sections = (
            "# Project Director Role",
            "## Purpose",
            "## Primary responsibilities",
            "## Authority and non-authority",
            "## Task assessment and decomposition",
            "## Mandatory role-management skill workflow",
            "## Role selection and role creation",
            "## Delegation contract",
            "## Model and reasoning identity",
            "## Parallel-work ownership",
            "## Supervision and steering",
            "## Review and integration",
            "## Verification and validation",
            "## Escalation and stopping conditions",
            "## Completion report",
        )
        for section in required_sections:
            self.assertIn(section, self.director)
        normalized_director = " ".join(self.director.split())
        for fragment in (
            "$manage-subagent-roles",
            "fresh filesystem-backed role catalog",
            "one bounded objective",
            "one stopping condition",
            "non-overlapping write ownership",
            "sub-agent completion message is not proof",
            "required Codex skill, tool, permission",
            "exact model and reasoning effort",
            "fork_turns",
            "runtime limit",
        ):
            self.assertIn(fragment, normalized_director)

    def test_root_role_does_not_repeat_automatic_instruction_loading(self) -> None:
        self.assertNotIn("## Required first reads", self.director)
        self.assertNotIn("Read the root `AGENTS.md`", self.director)
        self.assertNotIn("Read this root `ROLE.md`", self.director)
        self.assertIn("Read `./SOUL.md`", self.root_agents)
        self.assertIn("Read `./ROLE.md`", self.root_agents)

        normalized_skill = " ".join(self.skill.split())
        normalized_schema = " ".join(self.schema.split())
        self.assertIn(
            "Do not assume that Codex automatically loaded the role-specific nested",
            normalized_skill,
        )
        self.assertIn(
            "Codex does not recursively load every descendant `AGENTS.md`",
            normalized_schema,
        )
        self.assertIn(
            "explicitly require reading the selected role's `AGENTS.md` and `ROLE.md`",
            " ".join(self.plan.split()),
        )

    def test_root_agents_connects_director_to_local_skill(self) -> None:
        self.assertIn("Read `./SOUL.md`", self.root_agents)
        self.assertIn("Read `./ROLE.md`", self.root_agents)
        self.assertIn(
            "./.agents/skills/manage-subagent-roles/SKILL.md",
            self.root_agents,
        )
        self.assertIn("Before selecting", self.root_agents)

    def test_generic_role_has_exact_metadata_title_links_and_contract(self) -> None:
        metadata, body = role_catalog.parse_frontmatter(self.role)
        self.assertEqual("project-sub-agent", metadata["name"])
        self.assertIn("when no narrower specialized role", metadata["description"])
        h1_titles, heading_names, sections = role_catalog.role_sections(body)
        self.assertEqual(["Sub-Agent Project Role"], h1_titles)
        self.assertEqual(list(role_catalog.REQUIRED_ROLE_HEADINGS), heading_names)
        self.assertTrue(all(sections.values()))
        self.assertIn("](../../SOUL.md)", self.role_agents)
        self.assertIn("](./ROLE.md)", self.role_agents)
        self.assertIn("Do not create nested sub-agents", self.role_agents)
        self.assertIn("exact model and reasoning effort inherited", self.role_agents)
        self.assertIn("Project Director decisions", self.role)
        self.assertIn("None by default", self.role)

    def test_skill_contract_covers_all_modes_fit_and_native_orchestration(self) -> None:
        self.assertTrue(self.skill.startswith("---\nname: manage-subagent-roles\n"))
        frontmatter_end = self.skill.index("\n---", 4)
        description_line = next(
            line
            for line in self.skill[4:frontmatter_end].splitlines()
            if line.startswith("description:")
        )
        self.assertTrue(
            description_line.startswith(
                "description: Discover and return project sub-agent roles"
            )
        )
        for heading in (
            "## Inventory before other modes",
            "## Select by task fit",
            "## Create a reusable role",
            "## Validate a catalog or role",
            "## Build the delegation contract",
            "## Spawn through native Codex orchestration",
            "## Supervise and collect",
            "## Failure behavior",
        ):
            self.assertIn(heading, self.skill)
        for fragment in (
            "AGENTS.md",
            "ROLE.md",
            "Invalid roles are never eligible",
            "A role capability is not the same as a Codex skill dependency",
            "Only the first case enters role creation",
            "If the request is inventory only",
            "If it is creation only",
            "spawn_agent",
            "followup_task",
            "wait_agent",
            "interrupt_agent",
            "fork_turns",
            "Omit the `model` and `reasoning_effort` spawn arguments",
            "agents.default_subagent_model",
            "agents.default_subagent_reasoning_effort",
            "Do not shell out to another Codex process",
            "Do not create a user-visible task or thread",
        ):
            self.assertIn(fragment, " ".join(self.skill.split()))

    def test_schema_templates_and_helper_form_one_role_creation_system(self) -> None:
        skill_root = SCRIPT_PATH.parents[1]
        agents_template = skill_root / "assets" / "role-bundle" / "AGENTS.md.template"
        role_template = skill_root / "assets" / "role-bundle" / "ROLE.md.template"
        self.assertTrue(agents_template.is_file())
        self.assertTrue(role_template.is_file())
        source = SCRIPT_PATH.read_text(encoding="utf-8")
        self.assertIn('read_template(skill_root, "AGENTS.md.template")', source)
        self.assertIn('read_template(skill_root, "ROLE.md.template")', source)
        self.assertIn("target.mkdir()", source)
        self.assertIn("build_catalog(root)", source)
        self.assertIn("find_valid_role(catalog, args.name)", source)
        self.assertIn("role target already exists", source)
        for fragment in (
            "Do not add a registry",
            "Create a role only for a reusable role-definition gap",
            "missing skill, tool, dependency, permission",
            "Both links must resolve",
        ):
            self.assertIn(fragment, " ".join(self.schema.split()))

    def test_skill_ui_metadata_keeps_implicit_invocation_enabled(self) -> None:
        openai_yaml = (
            PROJECT_ROOT
            / ".agents"
            / "skills"
            / "manage-subagent-roles"
            / "agents"
            / "openai.yaml"
        ).read_text(encoding="utf-8")
        self.assertIn('display_name: "Manage Sub-Agent Roles"', openai_yaml)
        self.assertIn(
            'short_description: "Find, create, and assign sub-agent roles"', openai_yaml
        )
        self.assertIn("$manage-subagent-roles", openai_yaml)
        self.assertNotIn("allow_implicit_invocation: false", openai_yaml)

    def test_readme_exposes_the_generic_role_system_without_a_registry(self) -> None:
        readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
        specs_path = PROJECT_ROOT / "SPECS.md"
        if specs_path.is_file():
            self.assertIn("[SPECS.md](./SPECS.md)", readme)
            self.assertIn("## Python environment", specs_path.read_text(encoding="utf-8"))
            self.assertNotIn("## Python environment", readme)
        else:
            self.assertIn("## Python environment", readme)
        self.assertRegex(readme, r"\]\((?:\./)?ROLE\.md\)")
        self.assertRegex(readme, r"\]\((?:\./)?sub-agent-roles\)")
        self.assertRegex(
            readme, r"\]\((?:\./)?\.agents/skills/manage-subagent-roles/SKILL\.md\)"
        )
        self.assertFalse((PROJECT_ROOT / ".codex" / "agents").exists())
        forbidden_registry_names = {
            "AGENT_ROLE_REGISTRY.csv",
            "role-registry.json",
            "role_registry.json",
            "roles.csv",
        }
        discovered = {item.name for item in PROJECT_ROOT.rglob("*") if item.is_file()}
        self.assertTrue(forbidden_registry_names.isdisjoint(discovered))

    def test_children_must_inherit_exact_director_model_and_reasoning(self) -> None:
        normalized_director = " ".join(self.director.split())
        normalized_skill = " ".join(self.skill.split())
        normalized_schema = " ".join(self.schema.split())

        for text in (normalized_director, normalized_skill, normalized_schema):
            self.assertIn("exact model and reasoning effort", text)
            self.assertIn("fork_turns", text)
            self.assertIn("model", text)
            self.assertIn("reasoning_effort", text)

        self.assertIn("Set `fork_turns` to `all`", self.director)
        self.assertIn("Do not pass `model`", self.director)
        self.assertIn("Do not pass `reasoning_effort`", self.director)
        self.assertIn("Omit the `model` and `reasoning_effort`", self.skill)
        self.assertIn("agents.default_subagent_model", self.skill)
        self.assertIn("agents.default_subagent_reasoning_effort", self.skill)
        self.assertIn("not spawnable", normalized_schema)

        obsolete_exception = (
            "unless the user, project policy, or task explicitly requires an override"
        )
        self.assertNotIn(obsolete_exception, normalized_skill.lower())
        self.assertNotIn(
            "unless the user, applicable project policy, or task explicitly requires an override",
            normalized_director.lower(),
        )


if __name__ == "__main__":
    unittest.main()
