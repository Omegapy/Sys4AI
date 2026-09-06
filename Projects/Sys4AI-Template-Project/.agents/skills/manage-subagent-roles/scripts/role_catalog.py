#!/usr/bin/env python3
"""Discover, validate, show, and safely create project sub-agent roles."""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import shutil
import sys
import tempfile
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path

SCHEMA_VERSION = 1
ROLE_ROOT_NAME = "sub-agent-roles"
ROLE_NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MAX_ROLE_NAME_LENGTH = 63
MAX_FRONTMATTER_LINES = 64
MAX_FRONTMATTER_BYTES = 8192
ALLOWED_METADATA_FIELDS = {"name", "description"}
BOUNDARY_PATTERN = re.compile(
    r"\b(when|not|only|unless|outside|avoid|except|rather than)\b",
    flags=re.IGNORECASE,
)
PLACEHOLDER_PATTERN = re.compile(r"\{\{[A-Z0-9_]+\}\}")

REQUIRED_ROLE_HEADINGS = (
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

REQUIRED_AGENT_HEADINGS = (
    "# Sub-Agent Instructions",
    "## Required first reads",
    "## Delegated-work rules",
)

REQUIRED_AGENT_FRAGMENTS = (
    "delegation contract",
    "stopping condition",
    "evidence",
    "authority",
    "exact model and reasoning effort inherited",
    "do not create nested sub-agents",
    "project director",
)


class CatalogError(RuntimeError):
    """Raised when the role catalog cannot be used safely."""


@dataclass
class RoleEntry:
    """One discovered role directory and its validation state."""

    name: str
    description: str
    folder: str
    agents_file: str
    role_file: str
    diagnostics: list[str] = field(default_factory=list)

    @property
    def valid(self) -> bool:
        return not self.diagnostics

    def add_diagnostic(self, message: str) -> None:
        if message not in self.diagnostics:
            self.diagnostics.append(message)

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "description": self.description,
            "folder": self.folder,
            "agents_file": self.agents_file,
            "role_file": self.role_file,
            "valid": self.valid,
            "diagnostics": list(self.diagnostics),
        }


@dataclass
class RoleCatalog:
    """Live role-catalog result."""

    role_root: str
    valid_roles: list[RoleEntry]
    invalid_roles: list[RoleEntry]

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": SCHEMA_VERSION,
            "role_root": self.role_root,
            "valid_roles": [entry.to_dict() for entry in self.valid_roles],
            "invalid_roles": [entry.to_dict() for entry in self.invalid_roles],
        }


def is_within(candidate: Path, parent: Path) -> bool:
    """Return whether candidate resolves within parent."""

    try:
        candidate.relative_to(parent)
    except ValueError:
        return False
    return True


def repository_root(raw_root: str | os.PathLike[str]) -> Path:
    """Resolve and validate the supplied project root."""

    root = Path(raw_root).expanduser().resolve()
    if not root.is_dir():
        raise CatalogError(f"project root is not a directory: {root}")
    return root


def role_root_for(root: Path) -> Path:
    """Return a safe, existing role root below the project root."""

    root = root.resolve()
    role_root = root / ROLE_ROOT_NAME
    if not role_root.exists():
        raise CatalogError(f"role root does not exist: {role_root}")
    if not role_root.is_dir():
        raise CatalogError(f"role root is not a directory: {role_root}")

    resolved = role_root.resolve()
    if not is_within(resolved, root):
        raise CatalogError(f"role root escapes the project root: {role_root}")
    if role_root.is_symlink():
        raise CatalogError(f"role root must not be a symbolic link: {role_root}")
    return role_root


def relative_path(path: Path, root: Path) -> str:
    """Return a repository-relative POSIX path."""

    return path.relative_to(root).as_posix()


def validate_role_name(name: str) -> None:
    """Reject unsafe, hidden, opaque, or noncanonical role names."""

    if not name:
        raise CatalogError("role name must not be empty")
    if len(name) > MAX_ROLE_NAME_LENGTH:
        raise CatalogError(
            f"role name exceeds {MAX_ROLE_NAME_LENGTH} characters: {name}"
        )
    if not ROLE_NAME_PATTERN.fullmatch(name):
        raise CatalogError(
            f"role name must use lowercase letters, digits, and single hyphens: {name}"
        )
    if re.fullmatch(r"(?:agent|role)-\d+", name):
        raise CatalogError(f"role name is opaque rather than descriptive: {name}")


def decode_yaml_scalar(raw_value: str, field_name: str) -> str:
    """Decode the small string-only YAML subset used by role metadata."""

    value = raw_value.strip()
    if not value:
        raise CatalogError(f"metadata field is empty: {field_name}")

    if value[0] in {'"', "'"}:
        try:
            decoded = ast.literal_eval(value)
        except (SyntaxError, ValueError) as exc:
            raise CatalogError(
                f"metadata field has invalid quoted text: {field_name}"
            ) from exc
        if not isinstance(decoded, str):
            raise CatalogError(f"metadata field must be a string: {field_name}")
        value = decoded.strip()

    if not value or "\n" in value or "\r" in value:
        raise CatalogError(f"metadata field must be one non-empty line: {field_name}")
    return value


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Parse bounded flat frontmatter and return metadata plus body."""

    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        raise CatalogError("ROLE.md must start with YAML frontmatter")

    frontmatter_bytes = len(lines[0].encode("utf-8"))
    closing_index: int | None = None
    for index, line in enumerate(lines[1:MAX_FRONTMATTER_LINES], start=1):
        frontmatter_bytes += len(line.encode("utf-8"))
        if frontmatter_bytes > MAX_FRONTMATTER_BYTES:
            raise CatalogError("ROLE.md frontmatter exceeds the bounded size")
        if line.strip() == "---":
            closing_index = index
            break

    if closing_index is None:
        raise CatalogError("ROLE.md frontmatter has no closing delimiter")

    metadata: dict[str, str] = {}
    for raw_line in lines[1:closing_index]:
        line = raw_line.rstrip("\r\n")
        if not line.strip():
            continue
        if line[:1].isspace() or ":" not in line:
            raise CatalogError("ROLE.md frontmatter must use flat key-value fields")
        key, raw_value = line.split(":", 1)
        key = key.strip()
        if key not in ALLOWED_METADATA_FIELDS:
            raise CatalogError(f"unsupported ROLE.md metadata field: {key}")
        if key in metadata:
            raise CatalogError(f"duplicate ROLE.md metadata field: {key}")
        metadata[key] = decode_yaml_scalar(raw_value, key)

    missing = sorted(ALLOWED_METADATA_FIELDS - metadata.keys())
    if missing:
        raise CatalogError("missing ROLE.md metadata field(s): " + ", ".join(missing))

    return metadata, "".join(lines[closing_index + 1 :])


def validate_description(description: str) -> None:
    """Require a useful selection description with a routing boundary."""

    if len(description) < 24:
        raise CatalogError("role description is too short for reliable selection")
    if len(description) > 500:
        raise CatalogError("role description exceeds 500 characters")
    if not BOUNDARY_PATTERN.search(description):
        raise CatalogError(
            "role description must state a selection boundary using wording "
            "such as when, not, only, unless, outside, or avoid"
        )


def role_sections(body: str) -> tuple[list[str], list[str], dict[str, str]]:
    """Return H1 titles, ordered H2 names, and exact H2 section bodies."""

    h1_titles = re.findall(r"^# (?!#)(.+?)\s*$", body, flags=re.MULTILINE)
    heading_names: list[str] = []
    sections: dict[str, str] = {}
    heading_matches = list(re.finditer(r"^## (.+?)\s*$", body, flags=re.MULTILINE))
    for index, match in enumerate(heading_matches):
        heading = match.group(1).strip()
        heading_names.append(heading)
        start = match.end()
        end = (
            heading_matches[index + 1].start()
            if index + 1 < len(heading_matches)
            else len(body)
        )
        sections[heading] = body[start:end].strip()
    return h1_titles, heading_names, sections


def validate_role_body(body: str) -> list[str]:
    """Validate the human-readable role contract."""

    diagnostics: list[str] = []
    h1_titles, heading_names, sections = role_sections(body)
    if len(h1_titles) != 1 or not h1_titles[0].strip():
        diagnostics.append("ROLE.md must contain exactly one non-empty H1 title")

    for heading in REQUIRED_ROLE_HEADINGS:
        if heading not in sections:
            diagnostics.append(f"ROLE.md is missing required section: {heading}")
        elif heading_names.count(heading) != 1:
            diagnostics.append(f"ROLE.md repeats required section: {heading}")
        elif not sections[heading]:
            diagnostics.append(f"ROLE.md section is empty: {heading}")

    lowered = body.lower()
    if "{{" in body or "}}" in body or "todo" in lowered:
        diagnostics.append("ROLE.md contains an unfinished placeholder")
    return diagnostics


def markdown_link_targets(text: str) -> list[str]:
    """Extract ordinary Markdown link targets."""

    return [target.strip() for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text)]


def validate_agents_file(
    agents_text: str,
    role_dir: Path,
    role_file: Path,
    root: Path,
) -> list[str]:
    """Validate the role-specific AGENTS.md contract and links."""

    diagnostics: list[str] = []
    for heading in REQUIRED_AGENT_HEADINGS:
        if heading not in agents_text:
            diagnostics.append(f"AGENTS.md is missing required heading: {heading}")

    lowered = agents_text.lower()
    for fragment in REQUIRED_AGENT_FRAGMENTS:
        if fragment not in lowered:
            diagnostics.append(
                f"AGENTS.md is missing delegated-work requirement: {fragment}"
            )

    targets = markdown_link_targets(agents_text)
    expected_links = {
        "../../SOUL.md": (root / "SOUL.md").resolve(),
        "./ROLE.md": role_file.resolve(),
    }
    for target, expected in expected_links.items():
        if target not in targets:
            diagnostics.append(f"AGENTS.md is missing required link: {target}")
            continue
        resolved_target = (role_dir / target).resolve()
        if resolved_target != expected:
            diagnostics.append(f"AGENTS.md link resolves to the wrong path: {target}")
        elif not resolved_target.is_file():
            diagnostics.append(f"AGENTS.md link target is not a file: {target}")

    return diagnostics


def validate_role_directory(role_dir: Path, root: Path) -> RoleEntry:
    """Validate one immediate role directory."""

    folder = relative_path(role_dir, root)
    agents_file = role_dir / "AGENTS.md"
    role_file = role_dir / "ROLE.md"
    entry = RoleEntry(
        name=role_dir.name,
        description="",
        folder=folder,
        agents_file=relative_path(agents_file, root),
        role_file=relative_path(role_file, root),
    )

    try:
        validate_role_name(role_dir.name)
    except CatalogError as exc:
        entry.add_diagnostic(str(exc))

    if role_dir.is_symlink():
        entry.add_diagnostic("role directory must not be a symbolic link")

    if not agents_file.is_file() or agents_file.is_symlink():
        entry.add_diagnostic("role bundle requires one regular AGENTS.md")
    if not role_file.is_file() or role_file.is_symlink():
        entry.add_diagnostic("role bundle requires one regular ROLE.md")

    if role_file.is_file() and not role_file.is_symlink():
        try:
            role_text = role_file.read_text(encoding="utf-8")
            metadata, body = parse_frontmatter(role_text)
            entry.name = metadata["name"]
            entry.description = metadata["description"]
            validate_role_name(entry.name)
            validate_description(entry.description)
            if entry.name != role_dir.name:
                entry.add_diagnostic(
                    "ROLE.md metadata name does not match the role directory"
                )
            for diagnostic in validate_role_body(body):
                entry.add_diagnostic(diagnostic)
        except (CatalogError, OSError, UnicodeError) as exc:
            entry.add_diagnostic(str(exc))

    if agents_file.is_file() and not agents_file.is_symlink():
        try:
            agents_text = agents_file.read_text(encoding="utf-8")
            for diagnostic in validate_agents_file(
                agents_text, role_dir, role_file, root
            ):
                entry.add_diagnostic(diagnostic)
        except (OSError, UnicodeError) as exc:
            entry.add_diagnostic(str(exc))

    return entry


def build_catalog(root: Path) -> RoleCatalog:
    """Scan the live filesystem and return valid and invalid roles."""

    root = root.resolve()
    role_root = role_root_for(root)
    candidates = sorted(
        (item for item in role_root.iterdir() if item.is_dir() or item.is_symlink()),
        key=lambda item: item.name,
    )
    entries = [validate_role_directory(item, root) for item in candidates]

    names: dict[str, list[RoleEntry]] = {}
    for entry in entries:
        if entry.name:
            names.setdefault(entry.name, []).append(entry)
    for name, matching_entries in names.items():
        if len(matching_entries) > 1:
            locations = ", ".join(sorted(entry.folder for entry in matching_entries))
            for entry in matching_entries:
                entry.add_diagnostic(
                    f"duplicate role name {name!r} appears in: {locations}"
                )

    valid_roles = sorted(
        (entry for entry in entries if entry.valid),
        key=lambda entry: (entry.name, entry.folder),
    )
    invalid_roles = sorted(
        (entry for entry in entries if not entry.valid),
        key=lambda entry: (entry.name or entry.folder, entry.folder),
    )
    return RoleCatalog(
        role_root=relative_path(role_root, root),
        valid_roles=valid_roles,
        invalid_roles=invalid_roles,
    )


def markdown_escape(value: object) -> str:
    """Escape a value for a compact Markdown table cell."""

    return str(value).replace("|", r"\|").replace("\n", "<br>")


def catalog_markdown(catalog: RoleCatalog) -> str:
    """Render the role catalog as human-facing Markdown."""

    lines = [
        "## Valid roles",
        "",
    ]
    if catalog.valid_roles:
        lines.extend(
            [
                "| Role | Description | Folder | AGENTS.md | ROLE.md | State |",
                "| --- | --- | --- | --- | --- | --- |",
            ]
        )
        for entry in catalog.valid_roles:
            lines.append(
                "| "
                + " | ".join(
                    markdown_escape(value)
                    for value in (
                        entry.name,
                        entry.description,
                        entry.folder,
                        entry.agents_file,
                        entry.role_file,
                        "valid",
                    )
                )
                + " |"
            )
    else:
        lines.append("No valid roles found.")

    lines.extend(["", "## Invalid roles", ""])
    if catalog.invalid_roles:
        lines.extend(
            [
                "| Folder | AGENTS.md | ROLE.md | Diagnostics | State |",
                "| --- | --- | --- | --- | --- |",
            ]
        )
        for entry in catalog.invalid_roles:
            lines.append(
                "| "
                + " | ".join(
                    markdown_escape(value)
                    for value in (
                        entry.folder,
                        entry.agents_file,
                        entry.role_file,
                        "; ".join(entry.diagnostics),
                        "invalid",
                    )
                )
                + " |"
            )
    else:
        lines.append("No invalid roles found.")
    return "\n".join(lines)


def entry_markdown(entry: RoleEntry) -> str:
    """Render one valid role as a Markdown table."""

    catalog = RoleCatalog(
        role_root=ROLE_ROOT_NAME,
        valid_roles=[entry] if entry.valid else [],
        invalid_roles=[] if entry.valid else [entry],
    )
    return catalog_markdown(catalog)


def print_catalog(catalog: RoleCatalog, output_format: str) -> None:
    """Print a catalog using the requested output format."""

    if output_format == "json":
        print(json.dumps(catalog.to_dict(), indent=2, sort_keys=True))
    else:
        print(catalog_markdown(catalog))


def find_valid_role(catalog: RoleCatalog, role_name: str) -> RoleEntry:
    """Return one valid role or raise an exact catalog error."""

    for entry in catalog.valid_roles:
        if entry.name == role_name:
            return entry

    invalid_matches = [
        entry
        for entry in catalog.invalid_roles
        if entry.name == role_name or Path(entry.folder).name == role_name
    ]
    if invalid_matches:
        diagnostics = "; ".join(
            diagnostic for entry in invalid_matches for diagnostic in entry.diagnostics
        )
        raise CatalogError(f"role is invalid: {role_name}: {diagnostics}")
    raise CatalogError(f"role not found: {role_name}")


def clean_single_line(value: str, field_name: str, maximum: int = 500) -> str:
    """Validate a user-supplied one-line role-creation value."""

    cleaned = value.strip()
    if not cleaned:
        raise CatalogError(f"creation field must not be empty: {field_name}")
    if "\n" in cleaned or "\r" in cleaned:
        raise CatalogError(f"creation field must be one line: {field_name}")
    if len(cleaned) > maximum:
        raise CatalogError(f"creation field exceeds {maximum} characters: {field_name}")
    if "{{" in cleaned or "}}" in cleaned or "todo" in cleaned.lower():
        raise CatalogError(f"creation field contains a placeholder: {field_name}")
    return cleaned


def clean_values(values: Sequence[str], field_name: str) -> list[str]:
    """Validate one required repeated creation field."""

    if not values:
        raise CatalogError(f"at least one value is required: {field_name}")
    return [clean_single_line(value, field_name) for value in values]


def markdown_list(values: Iterable[str]) -> str:
    """Render values as a Markdown bullet list."""

    return "\n".join(f"- {value}" for value in values)


def numbered_markdown_list(values: Iterable[str]) -> str:
    """Render values as a Markdown numbered list."""

    return "\n".join(f"{index}. {value}" for index, value in enumerate(values, 1))


def read_template(skill_root: Path, filename: str) -> str:
    """Read one required role-bundle template."""

    template = skill_root / "assets" / "role-bundle" / filename
    if not template.is_file():
        raise CatalogError(f"required role template is missing: {template}")
    return template.read_text(encoding="utf-8")


def render_role_bundle(args: argparse.Namespace) -> tuple[str, str]:
    """Render complete AGENTS.md and ROLE.md contents from creation inputs."""

    name = args.name
    validate_role_name(name)
    title = clean_single_line(args.title, "title", maximum=120)
    description = clean_single_line(args.description, "description")
    validate_description(description)
    purpose = clean_single_line(args.purpose, "purpose", maximum=1000)

    suitable_tasks = clean_values(args.suitable_task, "suitable-task")
    capabilities = clean_values(args.capability, "capability")
    outside_tasks = clean_values(args.outside_task, "outside-task")
    expected_inputs = clean_values(args.expected_input, "expected-input")
    expected_outputs = clean_values(args.expected_output, "expected-output")
    working_method = clean_values(args.working_method, "working-method")
    validation_duties = clean_values(args.validation_duty, "validation-duty")
    authority_limits = clean_values(args.authority_limit, "authority-limit")
    escalation_conditions = clean_values(
        args.escalation_condition, "escalation-condition"
    )
    required_skills = [
        clean_single_line(value, "required-skill")
        for value in (args.required_skill or [])
    ]
    if not required_skills:
        required_skills = ["None by default."]

    skill_root = Path(__file__).resolve().parents[1]
    agents_text = read_template(skill_root, "AGENTS.md.template")
    role_template = read_template(skill_root, "ROLE.md.template")
    replacements = {
        "{{ROLE_NAME}}": name,
        "{{ROLE_DESCRIPTION}}": json.dumps(description, ensure_ascii=False),
        "{{ROLE_TITLE}}": title,
        "{{ROLE_PURPOSE}}": purpose,
        "{{SUITABLE_TASKS}}": markdown_list(suitable_tasks),
        "{{CAPABILITIES}}": markdown_list(capabilities),
        "{{OUTSIDE_TASKS}}": markdown_list(outside_tasks),
        "{{REQUIRED_SKILLS}}": markdown_list(required_skills),
        "{{EXPECTED_INPUTS}}": markdown_list(expected_inputs),
        "{{EXPECTED_OUTPUTS}}": markdown_list(expected_outputs),
        "{{WORKING_METHOD}}": numbered_markdown_list(working_method),
        "{{VALIDATION_DUTIES}}": markdown_list(validation_duties),
        "{{AUTHORITY_LIMITS}}": markdown_list(authority_limits),
        "{{ESCALATION_CONDITIONS}}": markdown_list(escalation_conditions),
    }
    role_text = role_template
    for placeholder, replacement in replacements.items():
        role_text = role_text.replace(placeholder, replacement)

    unresolved = PLACEHOLDER_PATTERN.findall(role_text)
    if unresolved:
        raise CatalogError(
            "role template has unresolved placeholder(s): "
            + ", ".join(sorted(set(unresolved)))
        )
    return agents_text, role_text


def remove_created_target(target: Path, expected_contents: dict[str, str]) -> None:
    """Rollback only files created by this operation, preserving surprises."""

    for filename, expected_text in expected_contents.items():
        candidate = target / filename
        if candidate.is_file() and not candidate.is_symlink():
            try:
                if candidate.read_text(encoding="utf-8") == expected_text:
                    candidate.unlink()
            except (OSError, UnicodeError):
                pass
    try:
        target.rmdir()
    except OSError:
        pass


def create_role(root: Path, args: argparse.Namespace) -> tuple[RoleEntry, RoleCatalog]:
    """Create both canonical files safely, validate, and relist."""

    root = root.resolve()
    role_root = role_root_for(root)
    validate_role_name(args.name)
    target = role_root / args.name
    if os.path.lexists(target):
        raise CatalogError(f"role target already exists: {target}")
    if target.resolve(strict=False).parent != role_root.resolve():
        raise CatalogError(f"role target escapes the role root: {target}")

    agents_text, role_text = render_role_bundle(args)
    expected_contents = {
        "AGENTS.md": agents_text,
        "ROLE.md": role_text,
    }
    temporary = Path(tempfile.mkdtemp(prefix=".creating-", dir=role_root))
    target_created = False
    try:
        for filename, content in expected_contents.items():
            (temporary / filename).write_text(content, encoding="utf-8")

        try:
            target.mkdir()
        except FileExistsError as exc:
            raise CatalogError(f"role target already exists: {target}") from exc
        target_created = True

        for filename in expected_contents:
            os.replace(temporary / filename, target / filename)

        temporary.rmdir()
        catalog = build_catalog(root)
        entry = find_valid_role(catalog, args.name)
        return entry, catalog
    except Exception:
        if target_created:
            remove_created_target(target, expected_contents)
        raise
    finally:
        shutil.rmtree(temporary, ignore_errors=True)


def add_format_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="output format (default: markdown)",
    )


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line interface."""

    parser = argparse.ArgumentParser(
        description="Discover, validate, show, and safely create sub-agent roles."
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="project root containing sub-agent-roles (default: current directory)",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser(
        "list", help="list live valid and invalid roles"
    )
    add_format_argument(list_parser)

    validate_parser = subparsers.add_parser(
        "validate", help="validate every intended role bundle"
    )
    add_format_argument(validate_parser)

    show_parser = subparsers.add_parser("show", help="show one valid role")
    show_parser.add_argument("name", help="role metadata name")
    add_format_argument(show_parser)

    create_parser = subparsers.add_parser(
        "create", help="create, validate, and relist one reusable role"
    )
    create_parser.add_argument("name", help="descriptive lowercase-hyphenated name")
    create_parser.add_argument("--title", required=True)
    create_parser.add_argument("--description", required=True)
    create_parser.add_argument("--purpose", required=True)
    create_parser.add_argument("--suitable-task", action="append", required=True)
    create_parser.add_argument("--capability", action="append", required=True)
    create_parser.add_argument("--outside-task", action="append", required=True)
    create_parser.add_argument("--required-skill", action="append")
    create_parser.add_argument("--expected-input", action="append", required=True)
    create_parser.add_argument("--expected-output", action="append", required=True)
    create_parser.add_argument("--working-method", action="append", required=True)
    create_parser.add_argument("--validation-duty", action="append", required=True)
    create_parser.add_argument("--authority-limit", action="append", required=True)
    create_parser.add_argument("--escalation-condition", action="append", required=True)
    add_format_argument(create_parser)
    return parser


def run(args: argparse.Namespace) -> int:
    """Execute one parsed command."""

    root = repository_root(args.repo_root)

    if args.command == "create":
        entry, catalog = create_role(root, args)
        if args.format == "json":
            payload = catalog.to_dict()
            payload["created_role"] = entry.to_dict()
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(f"Created and validated role: {entry.name}\n")
            print(entry_markdown(entry))
        return 0

    catalog = build_catalog(root)
    if args.command == "list":
        print_catalog(catalog, args.format)
        return 0

    if args.command == "validate":
        print_catalog(catalog, args.format)
        return 1 if catalog.invalid_roles else 0

    if args.command == "show":
        entry = find_valid_role(catalog, args.name)
        if args.format == "json":
            print(json.dumps(entry.to_dict(), indent=2, sort_keys=True))
        else:
            print(entry_markdown(entry))
        return 0

    raise CatalogError(f"unsupported command: {args.command}")


def main(argv: Sequence[str] | None = None) -> int:
    """Program entry point."""

    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return run(args)
    except (CatalogError, OSError, UnicodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
