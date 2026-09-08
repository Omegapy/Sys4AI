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
PACKAGE_ROOT = SCRIPT_PATH.parents[1]
SOURCE_LAYOUT = PACKAGE_ROOT.parent.name == "SKILLS-depo"
PROJECT_ROOT = PACKAGE_ROOT.parents[1] if SOURCE_LAYOUT else PACKAGE_ROOT.parents[2]
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
        self.role_root = self.root / "roles"
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
            "roles/project-sub-agent/AGENTS.md", entry.agents_file
        )
        self.assertEqual("roles/project-sub-agent/ROLE.md", entry.role_file)

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
        self.assertIn("roles/project-sub-agent/AGENTS.md", rendered)
        self.assertIn("roles/project-sub-agent/ROLE.md", rendered)

    def test_t014_json_output_has_versioned_contract(self) -> None:
        self.make_bundle("project-sub-agent")
        payload = role_catalog.build_catalog(self.root).to_dict()
        serialized = json.loads(json.dumps(payload))
        self.assertEqual(1, serialized["schema_version"])
        self.assertEqual("roles", serialized["role_root"])
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

    def test_t023_create_publishes_pair_index_and_only_its_lock(self) -> None:
        args = self.creation_args()
        role_catalog.create_role(self.root, args)
        created = sorted(
            item.relative_to(self.root).as_posix()
            for item in self.root.rglob("*")
            if item.is_file()
        )
        self.assertEqual(
            [
                ".sys4ai/role-catalog.lock",
                "SOUL.md",
                "roles/INDEX.md",
                "roles/documentation-reviewer/AGENTS.md",
                "roles/documentation-reviewer/ROLE.md",
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


    def test_index_is_navigation_and_never_grants_role_eligibility(self):
        self.make_bundle("valid-worker")
        self.make_bundle("invalid-worker", agents_text=None)
        (self.role_root / "INDEX.md").write_text("# Roles\nvalid-worker invalid-worker nonexistent-manager\n")
        before = self.snapshot()
        catalog = role_catalog.build_catalog(self.root)
        self.assertEqual(["valid-worker"], [x.name for x in catalog.valid_roles])
        self.assertEqual("stale", catalog.index_status)
        self.assertEqual(64, len(catalog.valid_roles[0].agents_sha256))
        for name in ("invalid-worker", "nonexistent-manager"):
            with self.assertRaises(role_catalog.CatalogError):
                role_catalog.find_valid_role(catalog, name)
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(1, role_catalog.main(["--repo-root", str(self.root), "validate"]))
        self.assertEqual(before, self.snapshot())

    def test_reindex_is_deterministic_and_reports_content_drift(self):
        bundle = self.make_bundle("valid-worker")
        first = role_catalog.reindex(self.root)
        self.assertEqual("current", first["index_status"])
        index = (self.role_root / "INDEX.md").read_bytes()
        self.assertIn(b"[AGENTS.md](./valid-worker/AGENTS.md)", index)
        self.assertNotIn(str(self.root).encode(), index)
        before = self.snapshot()
        self.assertFalse(role_catalog.reindex(self.root)["mutated"])
        self.assertEqual(before, self.snapshot())
        with (bundle / "ROLE.md").open("a") as stream:
            stream.write("\nAdditional bounded capability.\n")
        self.assertEqual("stale", role_catalog.build_catalog(self.root).index_status)
        self.assertEqual(index, (self.role_root / "INDEX.md").read_bytes())
        self.assertTrue(role_catalog.reindex(self.root)["mutated"])
        self.assertNotEqual(index, (self.role_root / "INDEX.md").read_bytes())

    def test_index_failure_preserves_created_bundle_and_reindex_recovers(self):
        with mock.patch.object(role_catalog, "publish_index", side_effect=OSError("interrupted index publication")):
            with self.assertRaises(role_catalog.PublicationPending) as caught:
                role_catalog.create_role(self.root, self.creation_args())
        self.assertTrue(caught.exception.result["bundle_committed"])
        self.assertEqual("reindex", caught.exception.result["recovery"])
        pair = self.role_root / "documentation-reviewer"
        original = {f.name: f.read_bytes() for f in pair.iterdir()}
        self.assertTrue(role_catalog.build_catalog(self.root).valid_roles[0].valid)
        self.assertEqual("current", role_catalog.reindex(self.root)["index_status"])
        self.assertEqual(original, {f.name: f.read_bytes() for f in pair.iterdir()})

    def test_symlink_index_and_control_directory_are_rejected(self):
        self.make_bundle("valid-worker")
        outside = self.root / "outside.txt"
        outside.write_text("preserve")
        (self.role_root / "INDEX.md").symlink_to(outside)
        with self.assertRaises(role_catalog.CatalogError):
            role_catalog.reindex(self.root)
        self.assertEqual("preserve", outside.read_text())
        (self.role_root / "INDEX.md").unlink()
        (self.root / ".sys4ai").symlink_to(self.role_root, target_is_directory=True)
        with self.assertRaises(role_catalog.CatalogError):
            role_catalog.reindex(self.root)
        self.assertFalse((self.role_root / "role-catalog.lock").exists())

    def test_busy_lock_blocks_a_second_writer(self):
        import subprocess
        self.make_bundle("valid-worker")
        with role_catalog.mutation_lock(self.root):
            before = self.snapshot()
            result = subprocess.run([sys.executable, str(SCRIPT_PATH), "--repo-root", str(self.root), "reindex"], capture_output=True, text=True)
            self.assertEqual(2, result.returncode)
            self.assertIn("busy", result.stderr)
            self.assertEqual(before, self.snapshot())

    def make_legacy(self):
        self.make_bundle("legacy-worker")
        legacy = self.root / "sub-agent-roles"
        self.role_root.rename(legacy)
        history = self.root / "historical-response.md"
        history.write_text("Original role: sub-agent-roles/legacy-worker/ROLE.md\n")
        return legacy, history

    def test_legacy_preview_is_read_only_and_active_discovery_has_no_fallback(self):
        self.make_legacy()
        before = self.snapshot()
        preview = role_catalog.transition_preview(self.root)
        self.assertEqual([], preview["conflicts"])
        self.assertEqual(before, self.snapshot())
        with self.assertRaisesRegex(role_catalog.CatalogError, "transition-preview"):
            role_catalog.build_catalog(self.root)
        with self.assertRaisesRegex(role_catalog.CatalogError, "confirmation"):
            role_catalog.transition_apply(self.root, preview, confirmed=False)
        self.assertEqual(before, self.snapshot())

    def test_copy_first_transition_preserves_legacy_and_history_and_is_idempotent(self):
        legacy, history = self.make_legacy()
        originals = {f.name: f.read_bytes() for f in (legacy / "legacy-worker").iterdir()}
        old_history = history.read_bytes()
        preview = role_catalog.transition_preview(self.root)
        result = role_catalog.transition_apply(self.root, preview, confirmed=True)
        self.assertEqual("current", result["index_status"])
        self.assertEqual(originals, {f.name: f.read_bytes() for f in (self.role_root / "legacy-worker").iterdir()})
        self.assertEqual(originals, {f.name: f.read_bytes() for f in (legacy / "legacy-worker").iterdir()})
        self.assertEqual(old_history, history.read_bytes())
        before = self.snapshot()
        self.assertFalse(role_catalog.transition_apply(self.root, preview, confirmed=True)["mutated"])
        self.assertEqual(before, self.snapshot())

    def test_identical_destination_is_retained_and_customization_blocks_transition(self):
        import shutil
        legacy, _ = self.make_legacy()
        shutil.copytree(legacy / "legacy-worker", self.role_root / "legacy-worker")
        extra = self.role_root / "legacy-worker" / "project-notes.md"
        extra.write_text("project-owned")
        preview = role_catalog.transition_preview(self.root)
        role_catalog.transition_apply(self.root, preview, confirmed=True)
        self.assertEqual("project-owned", extra.read_text())
        target = self.role_root / "legacy-worker" / "ROLE.md"
        target.write_text(target.read_text() + "\nCustom project responsibility.\n")
        before = self.snapshot()
        conflicting = role_catalog.transition_preview(self.root)
        self.assertTrue(conflicting["conflicts"])
        with self.assertRaises(role_catalog.CatalogError):
            role_catalog.transition_apply(self.root, conflicting, confirmed=True)
        self.assertEqual(before, self.snapshot())

    def test_stale_or_unconfined_transition_preview_is_rejected(self):
        legacy, _ = self.make_legacy()
        preview = role_catalog.transition_preview(self.root)
        source = legacy / "legacy-worker" / "ROLE.md"
        source.write_text(source.read_text() + "\nChanged role definition.\n")
        with self.assertRaisesRegex(role_catalog.CatalogError, "changed"):
            role_catalog.transition_apply(self.root, preview, confirmed=True)
        self.assertFalse(self.role_root.exists())
        preview = role_catalog.transition_preview(self.root)
        preview["pairs"][0]["files"][0]["destination"] = "../outside"
        preview["preview_sha256"] = role_catalog.object_digest({k: v for k, v in preview.items() if k != "preview_sha256"})
        with self.assertRaisesRegex(role_catalog.CatalogError, "unconfined"):
            role_catalog.transition_apply(self.root, preview, confirmed=True)
        self.assertFalse(self.role_root.exists())

    def test_interrupted_pair_and_index_publication_resume_exact_transition(self):
        self.make_legacy()
        preview = role_catalog.transition_preview(self.root)
        publish = role_catalog.atomic_publish
        def interrupted(path, content, **options):
            if path.name == "ROLE.md":
                raise OSError("interrupted paired-file publication")
            return publish(path, content, **options)
        with mock.patch.object(role_catalog, "atomic_publish", side_effect=interrupted):
            with self.assertRaises(role_catalog.PublicationPending):
                role_catalog.transition_apply(self.root, preview, confirmed=True)
        self.assertTrue((self.role_root / "legacy-worker/AGENTS.md").is_file())
        with mock.patch.object(role_catalog, "publish_index", side_effect=OSError("interrupted index")):
            with self.assertRaises(role_catalog.PublicationPending):
                role_catalog.transition_apply(self.root, preview, confirmed=True)
        self.assertTrue((self.role_root / "legacy-worker/ROLE.md").is_file())
        result = role_catalog.transition_apply(self.root, preview, confirmed=True)
        self.assertEqual("current", result["index_status"])
        receipt = json.loads((self.role_root / ".transition.json").read_text())
        self.assertEqual("completed", receipt["status"])
        self.assertEqual(2, len(receipt["completed"]))

    def test_concurrent_bundle_change_rejects_stale_index_publication(self):
        self.make_bundle("valid-worker")
        expected = role_catalog.build_catalog(self.root).fingerprint
        self.make_bundle("another-worker")
        with role_catalog.mutation_lock(self.root):
            with self.assertRaisesRegex(role_catalog.CatalogError, "changed"):
                role_catalog.publish_index(self.root, expected_fingerprint=expected)
        self.assertFalse((self.role_root / "INDEX.md").exists())

    def test_corrupt_transition_receipt_cannot_authorize_recovery(self):
        self.make_legacy()
        preview = role_catalog.transition_preview(self.root)
        self.role_root.mkdir()
        receipt = self.role_root / ".transition.json"
        for malformed in ({"schema_version": 999}, {"schema_version": 1, "preview": None, "completed": [], "status": "pending", "history": []}):
            receipt.write_text(json.dumps(malformed))
            before = receipt.read_bytes()
            with self.assertRaises(role_catalog.CatalogError):
                role_catalog.transition_apply(self.root, preview, confirmed=True)
            self.assertEqual(before, receipt.read_bytes())
            self.assertFalse((self.role_root / "legacy-worker").exists())

    def test_external_soul_symlink_prevents_role_eligibility(self):
        self.make_bundle("valid-worker")
        with tempfile.TemporaryDirectory() as other:
            external = Path(other) / "SOUL.md"
            external.write_text("External instructions")
            (self.root / "SOUL.md").unlink()
            (self.root / "SOUL.md").symlink_to(external)
            catalog = role_catalog.build_catalog(self.root)
            self.assertEqual([], catalog.valid_roles)
            self.assertTrue(catalog.invalid_roles)

    def test_concurrent_transition_target_is_preserved_at_publication_boundary(self):
        self.make_legacy()
        preview = role_catalog.transition_preview(self.root)
        publish = role_catalog.atomic_publish
        target = self.role_root / "legacy-worker/AGENTS.md"
        def concurrent(path, content, **options):
            if path == target.resolve() and not path.exists():
                path.write_text("Concurrent project-owned content\n")
            return publish(path, content, **options)
        with mock.patch.object(role_catalog, "atomic_publish", side_effect=concurrent):
            with self.assertRaises(role_catalog.PublicationPending):
                role_catalog.transition_apply(self.root, preview, confirmed=True)
        self.assertEqual("Concurrent project-owned content\n", target.read_text())
        self.assertEqual("pending", json.loads((self.role_root / ".transition.json").read_text())["status"])

    def test_index_becoming_unsafe_after_pair_publication_retains_valid_pair(self):
        target = self.role_root / "documentation-reviewer"
        outside = self.root / "keep.txt"
        outside.write_text("Preserve this file")
        catalog = role_catalog.build_catalog
        def index_changed(root, **options):
            index = self.role_root / "INDEX.md"
            if (target / "ROLE.md").exists() and not index.is_symlink():
                index.symlink_to(outside)
            return catalog(root, **options)
        with mock.patch.object(role_catalog, "build_catalog", side_effect=index_changed):
            with self.assertRaises(role_catalog.PublicationPending):
                role_catalog.create_role(self.root, self.creation_args())
        self.assertTrue(role_catalog.validate_role_directory(target.resolve(), self.root.resolve()).valid)
        self.assertEqual("Preserve this file", outside.read_text())

    def test_completed_receipt_and_history_require_exact_internal_coverage(self):
        self.make_legacy()
        preview = role_catalog.transition_preview(self.root)
        role_catalog.transition_apply(self.root, preview, confirmed=True)
        target = self.role_root / ".transition.json"
        original = json.loads(target.read_text())
        for history_case in (False, True):
            receipt = json.loads(json.dumps(original))
            if history_case:
                previous = {k: v for k, v in receipt.items() if k != "history"}
                previous["completed"] = {"../not-a-file": "unreviewed"}
                receipt["history"].append(previous)
            else:
                receipt["completed"] = []
            target.write_text(json.dumps(receipt))
            before = target.read_bytes()
            with self.assertRaises(role_catalog.CatalogError):
                role_catalog.transition_apply(self.root, preview, confirmed=True)
            self.assertEqual(before, target.read_bytes())

    def test_create_rollback_preserves_identical_replacement_file_identity(self):
        target = self.role_root / "documentation-reviewer"
        link = role_catalog.os.link
        observed = []
        def concurrent(source, destination, **options):
            destination = Path(destination)
            if destination.name == "ROLE.md":
                agents = target / "AGENTS.md"
                old_inode = agents.stat().st_ino
                replacement = self.root / "replacement.md"
                replacement.write_bytes(agents.read_bytes())
                os.replace(replacement, agents)
                destination.write_bytes(Path(source).read_bytes())
                observed.append(old_inode != agents.stat().st_ino)
            return link(source, destination, **options)
        with mock.patch.object(role_catalog.os, "link", side_effect=concurrent):
            with self.assertRaises(FileExistsError):
                role_catalog.create_role(self.root, self.creation_args())
        self.assertEqual([True], observed)
        self.assertTrue((target / "AGENTS.md").is_file())
        self.assertTrue((target / "ROLE.md").is_file())
        self.assertTrue(role_catalog.validate_role_directory(target.resolve(), self.root.resolve()).valid)


class ImplementationContractTests(unittest.TestCase):
    """Portable source/installed contracts; native execution is tested separately."""
    @classmethod
    def setUpClass(cls):
        if SOURCE_LAYOUT:
            cls.director = (PROJECT_ROOT / "ROLES-depo/project-director-ROLE.md").read_text()
            cls.root_agents = (PROJECT_ROOT / "AGENTS-depo/project-template-AGENTS.md").read_text()
            cls.readme = (PROJECT_ROOT / "SPECS-depo/project-template-README.md").read_text()
            cls.pairs = {name: (
                (PROJECT_ROOT / f"ROLES-depo/{name}-AGENTS.md").read_text(),
                (PROJECT_ROOT / f"ROLES-depo/{name}-ROLE.md").read_text())
                for name in ("project-sub-agent", "task-manager")}
        else:
            cls.director = (PROJECT_ROOT / "ROLE.md").read_text()
            cls.root_agents = (PROJECT_ROOT / "AGENTS.md").read_text()
            cls.readme = (PROJECT_ROOT / "README.md").read_text()
            cls.pairs = {name: ((PROJECT_ROOT / "roles" / name / "AGENTS.md").read_text(),
                                (PROJECT_ROOT / "roles" / name / "ROLE.md").read_text())
                         for name in ("project-sub-agent", "task-manager")}
        cls.skill = (PACKAGE_ROOT / "SKILL.md").read_text()
        cls.schema = (PACKAGE_ROOT / "references/role-schema.md").read_text()

    def test_director_requires_fresh_roles_and_bounded_delegation(self):
        text = " ".join(self.director.split()).casefold()
        for clause in ("fresh", "catalog", "one bounded objective", "stopping condition",
                       "protected state", "non-overlapping", "directly", "native",
                       "manager", "canonical", "capability", "authority"):
            self.assertIn(clause, text)
        self.assertIn(".agents/skills/manage-subagent-roles/SKILL.md", self.director)

    def test_explicit_instruction_loading_and_no_ordinary_child_promotion(self):
        for name, (agents, role) in self.pairs.items():
            with self.subTest(name=name):
                self.assertIn("](../../SOUL.md)", agents)
                self.assertIn("](./ROLE.md)", agents)
                self.assertIn("delegation", agents)
        self.assertIn("Codex does not recursively load", self.schema)
        self.assertIn("Do not assume that Codex automatically loaded", self.skill)
        self.assertIn("Ordinary children", self.skill)
        self.assertIn("confirmed", self.pairs["task-manager"][1])
        self.assertIn("does not supply task-manager authority", self.pairs["project-sub-agent"][1])

    def test_pair_contracts_validate_in_a_clean_project(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve()
            (root / "SOUL.md").write_text("# Project soul\n")
            for name, (agents, role) in self.pairs.items():
                target = root / "roles" / name
                target.mkdir(parents=True)
                (target / "AGENTS.md").write_text(agents)
                (target / "ROLE.md").write_text(role)
            catalog = role_catalog.reindex(root)
            fresh = role_catalog.build_catalog(root)
            self.assertFalse(fresh.invalid_roles)
            self.assertEqual({"project-sub-agent", "task-manager"}, {r.name for r in fresh.valid_roles})
            self.assertEqual("current", fresh.index_status)

    def test_manager_and_worker_authority_are_distinct(self):
        manager = " ".join(self.pairs["task-manager"][1].split())
        worker = " ".join(self.pairs["project-sub-agent"][1].split())
        for clause in ("confirmed Task execution", "bootstrap handoff", "canonical state",
                       "one distinct dedicated implementer", "one-to-one reviews"):
            self.assertIn(clause, manager)
        self.assertIn("not a substitute for a specialized role", worker)
        self.assertIn("None by default", worker)
        self.assertIn("Do not accept your own work", worker)

    def test_skills_tools_and_roles_do_not_grant_authority(self):
        text = " ".join(self.skill.split())
        for clause in ("narrowest suitable valid role", "required Codex skills",
                       "Only the first case enters role creation",
                       "A role capability is not the same as a Codex skill dependency",
                       "Creation-only requests stop", "Inventory alone creates no role"):
            self.assertIn(clause, text)

    def test_native_operations_and_context_are_separate_from_identity(self):
        text = " ".join(self.skill.split())
        for operation in ("spawn_agent", "send_message", "followup_task", "list_agents",
                          "wait_agent", "interrupt_agent"):
            self.assertIn(operation, text)
        for clause in ("exact effective model and reasoning effort", "inheritance guarantee",
                       "Omit the `model` and `reasoning_effort`", "sibling drafts",
                       "queued", "paths, hashes and status", "before launch",
                       "original reservation", "No shell-launched Codex process"):
            self.assertIn(clause, text)
        for config in ("agents.default_subagent_model", "agents.default_subagent_reasoning_effort"):
            self.assertIn(config, text)

    def test_source_navigation_is_not_role_authority(self):
        text = " ".join((self.skill + " " + self.schema).split())
        for clause in ("roles/INDEX.md", "navigation", "never independent role authority",
                       "transition-preview", "transition-apply", "preview_sha256",
                       "reindex", "read-only", "committed valid bundle"):
            self.assertIn(clause, text)
        self.assertIn("roles/", self.readme)
        self.assertIn(".agents/skills/manage-subagent-roles/SKILL.md", self.readme)

    def test_template_helpers_and_ui_metadata_are_available(self):
        for filename in ("AGENTS.md.template", "ROLE.md.template"):
            self.assertTrue((PACKAGE_ROOT / "assets/role-bundle" / filename).is_file())
        metadata = (PACKAGE_ROOT / "agents/openai.yaml").read_text()
        self.assertIn('display_name: "Manage Sub-Agent Roles"', metadata)
        self.assertIn("$manage-subagent-roles", metadata)
        self.assertNotIn("allow_implicit_invocation: false", metadata)
        self.assertTrue(self.skill.startswith("---\nname: manage-subagent-roles\n"))

    def test_read_only_and_recovery_boundary_is_explicit(self):
        text = " ".join((self.skill + " " + self.schema).split())
        for clause in ("Read-only routes never migrate", "An uncertain outcome",
                       "only its own invalid incomplete pair", "exit 3",
                       "do not create the role again", "age or roster absence alone"):
            # The helper README also documents partial-commit recovery.
            all_text = text + " " + " ".join((PACKAGE_ROOT / "README.md").read_text().split())
            self.assertIn(clause.casefold(), all_text.casefold())


if __name__ == "__main__":
    unittest.main()
