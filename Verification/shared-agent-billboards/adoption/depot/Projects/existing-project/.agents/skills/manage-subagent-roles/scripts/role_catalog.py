#!/usr/bin/env python3
"""Discover, validate, show, and safely create project sub-agent roles."""

from __future__ import annotations

import argparse
import ast
import contextlib
import hashlib
import json
import os
import re
import shutil
import stat
import sys
import tempfile
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path

SCHEMA_VERSION = 1
ROLE_ROOT_NAME = "Roles"
PREVIOUS_ROLE_ROOT_NAME = "roles"
CASE_RENAME_RECEIPT = ".sys4ai/roles-case-rename.json"
LEGACY_ROLE_ROOT_NAME = "sub-agent-roles"
MAX_MANIFEST_BYTES = 1_000_000
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


class PublicationPending(CatalogError):
    """A valid bundle/transition committed; only the named recovery remains."""

    def __init__(self, result: dict[str, object]):
        self.result = result
        super().__init__(str(result.get("error", "role publication remains pending")))


@dataclass
class RoleEntry:
    """One discovered role directory and its validation state."""

    name: str
    description: str
    folder: str
    agents_file: str
    role_file: str
    diagnostics: list[str] = field(default_factory=list)
    agents_sha256: str | None = None
    role_sha256: str | None = None

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
            "agents_sha256": self.agents_sha256,
            "role_sha256": self.role_sha256,
        }


@dataclass
class RoleCatalog:
    """Live role-catalog result."""

    role_root: str
    valid_roles: list[RoleEntry]
    invalid_roles: list[RoleEntry]
    index_status: str = "missing"
    fingerprint: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": SCHEMA_VERSION,
            "role_root": self.role_root,
            "valid_roles": [entry.to_dict() for entry in self.valid_roles],
            "invalid_roles": [entry.to_dict() for entry in self.invalid_roles],
            "index_status": self.index_status,
            "fingerprint": self.fingerprint,
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

    candidate = Path(raw_root).expanduser()
    if candidate.is_symlink():
        raise CatalogError("project root must not be a symbolic link")
    # Normalize host aliases such as macOS /var before confining project paths.
    root = checked_path(candidate.resolve())
    if not root.is_dir():
        raise CatalogError(f"project root is not a directory: {root}")
    return root


def role_root_for(root: Path, role_root_name: str = ROLE_ROOT_NAME) -> Path:
    """Return a safe, existing role root below the project root."""

    root = root.resolve()
    if role_root_name not in {ROLE_ROOT_NAME, LEGACY_ROLE_ROOT_NAME}:
        raise CatalogError("unsupported role root")
    role_root = root / role_root_name
    if role_root.is_symlink() and not is_within(role_root.resolve(), root):
        raise CatalogError(f"role root escapes the project root: {role_root}")
    exact_directory_entry(root, role_root_name)
    role_root = checked_path(role_root)
    if not role_root.exists():
        legacy = " Use transition-preview for the legacy layout." if (root / LEGACY_ROLE_ROOT_NAME).exists() else ""
        raise CatalogError(f"role root does not exist: {role_root}.{legacy}")
    if not role_root.is_dir():
        raise CatalogError(f"role root is not a directory: {role_root}")

    resolved = role_root.resolve()
    if not is_within(resolved, root):
        raise CatalogError(f"role root escapes the project root: {role_root}")
    if role_root.is_symlink():
        raise CatalogError(f"role root must not be a symbolic link: {role_root}")
    return role_root


def exact_directory_entry(parent: Path, name: str, *, allow_missing: bool = False) -> Path:
    """Inspect spelling, including aliases hidden by case-insensitive lookup."""
    matches = sorted(item.name for item in parent.iterdir() if item.name.casefold() == name.casefold())
    if matches and matches != [name]:
        raise CatalogError(f"role directory must have exact spelling {name}; found {matches}. "
                           "Use case-rename-preview for the previous lowercase layout.")
    target = checked_path(parent / name)
    if not matches and not allow_missing:
        legacy = " Use transition-preview for the legacy layout." if (parent / LEGACY_ROLE_ROOT_NAME).exists() else ""
        raise CatalogError(f"role root does not exist: {target}.{legacy}")
    if matches and not target.is_dir():
        raise CatalogError(f"role root is not a directory: {target}")
    return target


def checked_path(path: Path) -> Path:
    """Reject aliases before resolving; never follow a role or control symlink."""
    absolute = Path(os.path.abspath(path))
    for component in reversed((absolute, *absolute.parents)):
        if component.is_symlink():
            raise CatalogError(f"path must not be a symbolic link: {component}")
    if absolute.exists() and absolute.is_file() and absolute.stat().st_nlink != 1:
        raise CatalogError(f"file must not be hard-linked: {absolute}")
    return absolute


def digest_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def file_digest(path: Path) -> str | None:
    checked_path(path)
    if not path.exists():
        return None
    if not path.is_file():
        raise CatalogError(f"expected a regular file: {path}")
    return digest_bytes(path.read_bytes())


def object_digest(value: object) -> str:
    return digest_bytes(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode())


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
        "../../SOUL.md": root / "SOUL.md",
        "./ROLE.md": role_file,
    }
    for target, expected in expected_links.items():
        if target not in targets:
            diagnostics.append(f"AGENTS.md is missing required link: {target}")
            continue
        try:
            checked_path(expected)
            if not is_within(expected.resolve(), root.resolve()):
                raise CatalogError("required instruction source escapes the project")
        except CatalogError as exc:
            diagnostics.append(str(exc))
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
        return entry

    if agents_file.is_symlink():
        entry.add_diagnostic("role bundle requires one regular AGENTS.md")
    if role_file.is_symlink():
        entry.add_diagnostic("role bundle requires one regular ROLE.md")
    if entry.diagnostics and (agents_file.is_symlink() or role_file.is_symlink()):
        return entry

    try:
        checked_path(role_dir)
        checked_path(agents_file)
        checked_path(role_file)
    except CatalogError as exc:
        entry.add_diagnostic(str(exc))
        return entry

    if not agents_file.is_file() or agents_file.is_symlink():
        entry.add_diagnostic("role bundle requires one regular AGENTS.md")
    if not role_file.is_file() or role_file.is_symlink():
        entry.add_diagnostic("role bundle requires one regular ROLE.md")

    if role_file.is_file() and not role_file.is_symlink():
        try:
            role_bytes = role_file.read_bytes()
            role_text = role_bytes.decode("utf-8")
            entry.role_sha256 = digest_bytes(role_bytes)
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
            agents_bytes = agents_file.read_bytes()
            agents_text = agents_bytes.decode("utf-8")
            entry.agents_sha256 = digest_bytes(agents_bytes)
            for diagnostic in validate_agents_file(
                agents_text, role_dir, role_file, root
            ):
                entry.add_diagnostic(diagnostic)
        except (OSError, UnicodeError) as exc:
            entry.add_diagnostic(str(exc))

    return entry


def build_catalog(root: Path, *, role_root_name: str = ROLE_ROOT_NAME, inspect_index: bool = True) -> RoleCatalog:
    """Scan the live filesystem and return valid and invalid roles."""

    root = root.resolve()
    role_root = role_root_for(root, role_root_name)
    candidates = sorted(
        (item for item in role_root.iterdir() if item.name not in {"INDEX.md", ".transition.json"} and (item.is_dir() or item.is_symlink())),
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
    catalog = RoleCatalog(
        role_root=relative_path(role_root, root),
        valid_roles=valid_roles,
        invalid_roles=invalid_roles,
    )
    catalog.fingerprint = object_digest({"valid": [e.to_dict() for e in valid_roles], "invalid": [e.to_dict() for e in invalid_roles]})
    if role_root_name == ROLE_ROOT_NAME and inspect_index:
        index = checked_path(role_root / "INDEX.md")
        if index.exists():
            if not index.is_file():
                raise CatalogError("role index must be a regular file")
            catalog.index_status = "current" if index.read_bytes() == render_index(catalog).encode() else "stale"
    elif role_root_name != ROLE_ROOT_NAME:
        catalog.index_status = "legacy"
    return catalog


def render_index(catalog: RoleCatalog) -> str:
    """Render context-relative navigation without a clock or absolute root."""
    lines = ["<!-- Generated by role_catalog.py. Paired role files are authoritative. -->", "", "# Roles", "",
             f"Catalog SHA-256: `{catalog.fingerprint}`", "",
             "| Role | Selection | AGENTS.md | ROLE.md | AGENTS SHA-256 | ROLE SHA-256 |",
             "| --- | --- | --- | --- | --- | --- |"]
    for entry in catalog.valid_roles:
        name = Path(entry.folder).name
        lines.append(f"| {entry.name} | {markdown_escape(entry.description)} | [AGENTS.md](./{name}/AGENTS.md) | [ROLE.md](./{name}/ROLE.md) | `{entry.agents_sha256}` | `{entry.role_sha256}` |")
    lines.extend(["", "## Invalid bundles", ""])
    if not catalog.invalid_roles:
        lines.append("None.")
    for entry in catalog.invalid_roles:
        lines.append(f"- `{markdown_escape(entry.folder)}`: {markdown_escape('; '.join(entry.diagnostics))}")
    return "\n".join(lines) + "\n"


@contextlib.contextmanager
def mutation_lock(root: Path):
    """A retained advisory-lock file avoids unlink/reacquire races."""
    root = repository_root(root)
    try:
        import fcntl
    except ImportError as exc:
        raise CatalogError("role mutations require POSIX advisory locking on this host") from exc
    control = checked_path(root / ".sys4ai")
    control.mkdir(exist_ok=True)
    lock = checked_path(control / "role-catalog.lock")
    descriptor = os.open(lock, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise CatalogError("unsafe role-catalog lock")
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise CatalogError("role catalog is busy; preserve the active writer") from exc
        _ontology_checkpoint()
        yield
    finally:
        os.close(descriptor)


def atomic_publish(path: Path, content: bytes, *, replace: bool = True) -> None:
    checked_path(path)
    if path.exists() and not path.is_file():
        raise CatalogError(f"publication target is not a regular file: {path}")
    descriptor, temporary = tempfile.mkstemp(prefix=".role-publish-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        checked_path(path)
        if replace:
            _ontology_checkpoint(targets=False)
            os.replace(temporary, path)
        else:
            # A preview of an absent role file never authorizes replacing a
            # concurrently appearing file, even if another editor ignores locks.
            _ontology_checkpoint(targets=False)
            os.link(temporary, path, follow_symlinks=False)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def publish_index(root: Path, *, expected_fingerprint: str | None = None) -> dict[str, object]:
    """Publish while the caller holds the catalog mutation lock."""
    catalog = build_catalog(root)
    if expected_fingerprint is not None and catalog.fingerprint != expected_fingerprint:
        raise CatalogError("role bundles changed since the reviewed catalog")
    content = render_index(catalog).encode()
    target = checked_path(root / ROLE_ROOT_NAME / "INDEX.md")
    if target.exists() and target.read_bytes() == content:
        return {"status": "current", "mutated": False, "index_sha256": digest_bytes(content), **catalog.to_dict()}
    if build_catalog(root).fingerprint != catalog.fingerprint:
        raise CatalogError("role bundles changed during index generation")
    atomic_publish(target, content)
    current = build_catalog(root)
    if current.index_status != "current":
        raise CatalogError("role bundles changed during index publication; reindex after the writer stops")
    return {"status": "updated", "mutated": True, "index_sha256": digest_bytes(content), **current.to_dict()}


def reindex(root: Path) -> dict[str, object]:
    root = repository_root(root)
    build_catalog(root)
    with mutation_lock(root):
        return publish_index(root)


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


def remove_created_target(target: Path, expected_contents: dict[str, str], expected_identity: tuple[int, int] | None = None, file_identities: dict[str, tuple[int, int]] | None = None) -> None:
    """Rollback only files created by this operation, preserving surprises."""

    try:
        checked_path(target)
        info = target.stat()
        if expected_identity is not None and (info.st_dev, info.st_ino) != expected_identity:
            return
    except (CatalogError, OSError):
        return
    for filename, expected_text in expected_contents.items():
        candidate = target / filename
        if candidate.is_file() and not candidate.is_symlink():
            try:
                info = candidate.stat()
                if file_identities is not None and (info.st_dev, info.st_ino) != file_identities.get(filename):
                    continue
                if candidate.read_text(encoding="utf-8") == expected_text:
                    candidate.unlink()
            except (OSError, UnicodeError):
                pass
    try:
        target.rmdir()
    except OSError:
        pass


def _create_role(root: Path, args: argparse.Namespace) -> tuple[RoleEntry, RoleCatalog]:
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
    target_identity = None
    published_contents = {}
    published_identities = {}
    try:
        for filename, content in expected_contents.items():
            (temporary / filename).write_text(content, encoding="utf-8")

        try:
            target.mkdir()
        except FileExistsError as exc:
            raise CatalogError(f"role target already exists: {target}") from exc
        target_created = True
        info = target.stat()
        target_identity = (info.st_dev, info.st_ino)

        for filename in expected_contents:
            checked_path(target)
            info = (temporary / filename).stat()
            _ontology_checkpoint(targets=False)
            os.link(temporary / filename, target / filename, follow_symlinks=False)
            published_contents[filename] = expected_contents[filename]
            published_identities[filename] = (info.st_dev, info.st_ino)
            (temporary / filename).unlink()

        temporary.rmdir()
        catalog = build_catalog(root, inspect_index=False)
        entry = find_valid_role(catalog, args.name)
        return entry, catalog
    except Exception:
        if target_created:
            remove_created_target(target, published_contents, target_identity, published_identities)
        raise
    finally:
        shutil.rmtree(temporary, ignore_errors=True)


def create_role(root: Path, args: argparse.Namespace) -> tuple[RoleEntry, RoleCatalog]:
    root = repository_root(root)
    role_root_for(root)
    render_role_bundle(args)
    with mutation_lock(root):
        # Reject an already unsafe index before publishing any new pair. Later
        # navigation failures belong to the post-commit recovery boundary below.
        build_catalog(root)
        entry, catalog = _create_role(root, args)
        try:
            publish_index(root, expected_fingerprint=catalog.fingerprint)
        except (CatalogError, OSError, UnicodeError) as exc:
            raise PublicationPending({"status": "partial", "bundle_committed": True,
                "created_role": entry.to_dict(), "index_status": "pending",
                "recovery": "reindex", "error": str(exc)}) from exc
        return entry, build_catalog(root)


def transition_preview(root: Path) -> dict[str, object]:
    """Inspect exact legacy pairs; no role-root creation or index repair."""
    root = repository_root(root)
    legacy = build_catalog(root, role_root_name=LEGACY_ROLE_ROOT_NAME)
    target_root = exact_directory_entry(root, ROLE_ROOT_NAME, allow_missing=True)
    if target_root.exists() and not target_root.is_dir():
        raise CatalogError("active role root is not a directory")
    pairs = []
    conflicts = [f"invalid legacy bundle {e.folder}: {'; '.join(e.diagnostics)}" for e in legacy.invalid_roles]
    for entry in legacy.valid_roles:
        destination = checked_path(target_root / entry.name)
        if destination.exists() and not destination.is_dir():
            conflicts.append(f"role destination is not a directory: {entry.name}")
        files = []
        for name, expected in (("AGENTS.md", entry.agents_sha256), ("ROLE.md", entry.role_sha256)):
            target = checked_path(destination / name)
            actual = file_digest(target)
            if actual is not None and actual != expected:
                conflicts.append(f"customized destination: {entry.name}/{name}")
            files.append({"source": f"{LEGACY_ROLE_ROOT_NAME}/{entry.name}/{name}",
                          "destination": f"{ROLE_ROOT_NAME}/{entry.name}/{name}",
                          "source_sha256": expected, "destination_sha256": actual})
        pairs.append({"name": entry.name, "files": files})
    preview = {"schema_version": 1, "project_root": str(root),
               "legacy_fingerprint": legacy.fingerprint, "pairs": pairs,
               "conflicts": conflicts, "receipt": f"{ROLE_ROOT_NAME}/.transition.json"}
    preview["preview_sha256"] = object_digest(preview)
    return preview


def load_manifest(path: Path) -> dict[str, object]:
    checked_path(path)
    if not path.is_file() or path.stat().st_size > MAX_MANIFEST_BYTES:
        raise CatalogError("manifest must be a bounded regular file")
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise CatalogError("duplicate JSON key in role manifest")
            result[key] = value
        return result
    try:
        value = json.loads(path.read_text(), object_pairs_hook=unique)
    except (ValueError, RecursionError) as exc:
        raise CatalogError("invalid role manifest JSON") from exc
    if not isinstance(value, dict):
        raise CatalogError("role manifest must be an object")
    return value


def directory_identity(path: Path) -> dict[str, int]:
    checked_path(path)
    info = path.stat()
    if not stat.S_ISDIR(info.st_mode):
        raise CatalogError(f"expected a directory: {path}")
    return {"device": info.st_dev, "inode": info.st_ino}


def role_tree_inventory(path: Path) -> dict[str, dict[str, str]]:
    """Bind every retained file, including custom content and old receipts."""
    directory_identity(path)
    inventory = {}
    for item in sorted(path.rglob("*")):
        checked_path(item)
        relative = item.relative_to(path).as_posix()
        if item.is_dir():
            inventory[relative] = {"kind": "directory"}
        elif item.is_file():
            inventory[relative] = {"kind": "file", "sha256": file_digest(item)}
        else:
            raise CatalogError(f"unsupported entry in role tree: {relative}")
    return inventory


def validate_case_rename_preview(preview: object, root: Path) -> None:
    fields = {"schema_version", "project_root", "source", "destination", "temporary",
              "source_identity", "inventory", "preview_sha256"}
    if not isinstance(preview, dict) or set(preview) != fields or type(preview["schema_version"]) is not int or preview["schema_version"] != 1:
        raise CatalogError("unsupported role case-rename preview")
    unsigned = {k: v for k, v in preview.items() if k != "preview_sha256"}
    if preview["preview_sha256"] != object_digest(unsigned) or preview["project_root"] != str(root):
        raise CatalogError("role case-rename preview digest or project mismatch")
    if preview["source"] != PREVIOUS_ROLE_ROOT_NAME or preview["destination"] != ROLE_ROOT_NAME:
        raise CatalogError("case rename must be exactly roles to Roles")
    base = {k: v for k, v in unsigned.items() if k != "temporary"}
    if preview["temporary"] != ".roles-case-rename-" + object_digest(base)[:24]:
        raise CatalogError("unsafe role case-rename temporary path")
    identity = preview["source_identity"]
    if not isinstance(identity, dict) or set(identity) != {"device", "inode"} or any(type(v) is not int or v < 0 for v in identity.values()):
        raise CatalogError("invalid role directory identity")
    inventory = preview["inventory"]
    if not isinstance(inventory, dict):
        raise CatalogError("invalid role case-rename inventory")
    for name, item in inventory.items():
        if not isinstance(name, str) or not name or "\\" in name or "\x00" in name or Path(name).is_absolute() or any(part in {"", ".", ".."} for part in name.split("/")):
            raise CatalogError("unconfined role case-rename inventory path")
        if not isinstance(item, dict) or not isinstance(item.get("kind"), str) or item["kind"] not in {"directory", "file"}:
            raise CatalogError("invalid role case-rename inventory entry")
        if item["kind"] == "directory":
            if set(item) != {"kind"}:
                raise CatalogError("invalid role case-rename directory entry")
        elif set(item) != {"kind", "sha256"} or not isinstance(item["sha256"], str) or not re.fullmatch(r"[0-9a-f]{64}", item["sha256"]):
            raise CatalogError("invalid role case-rename file digest")
        for parent in Path(name).parents:
            if parent != Path(".") and inventory.get(parent.as_posix()) != {"kind": "directory"}:
                raise CatalogError("incomplete role case-rename directory coverage")
    receipt_bytes = (json.dumps({"schema_version": 1, "preview": preview, "status": "completed"}, indent=2) + "\n").encode()
    if len(receipt_bytes) > MAX_MANIFEST_BYTES:
        raise CatalogError("role case-rename inventory exceeds the bounded receipt size")


def _validate_case_receipt(value: object, root: Path) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != {"schema_version", "preview", "status"} or type(value["schema_version"]) is not int or value["schema_version"] != 1 or not isinstance(value["status"], str) or value["status"] not in {"pending", "completed"}:
        raise CatalogError("unsupported role case-rename receipt")
    validate_case_rename_preview(value["preview"], root)
    return value


def _case_rename_location(root: Path, preview: dict[str, object]) -> Path:
    """A recoverable rename owns one exact directory, never two aliases."""
    names = {preview["source"], preview["destination"], preview["temporary"]}
    candidates = sorted((item for item in root.iterdir()
                         if item.name.casefold() in {name.casefold() for name in names}), key=lambda item: item.name)
    if len(candidates) != 1 or candidates[0].name not in names:
        raise CatalogError("role case-rename has missing, ambiguous or conflicting directories")
    current = candidates[0]
    if directory_identity(current) != preview["source_identity"]:
        raise CatalogError("role case-rename directory identity changed")
    return current


def validate_case_rename_receipt(value: object, root: Path) -> dict[str, object]:
    """Return historical path proof, without claiming old file hashes are current."""
    root = repository_root(root)
    receipt = _validate_case_receipt(value, root)
    preview = receipt["preview"]
    if receipt["status"] != "completed" or _case_rename_location(root, preview).name != ROLE_ROOT_NAME:
        raise CatalogError("role case-rename is not completed at the exact active Roles directory")
    source_files = {f"{PREVIOUS_ROLE_ROOT_NAME}/{name}": item["sha256"]
                    for name, item in preview["inventory"].items() if item["kind"] == "file"}
    return {"status": "completed", "source_files": source_files,
            "destination_paths": {name: f"{ROLE_ROOT_NAME}/{name.split('/', 1)[1]}" for name in source_files},
            "directory_identity": dict(preview["source_identity"])}


def case_rename_preview(root: Path) -> dict[str, object]:
    """Read-only exact lowercase-to-uppercase tree inspection or recovery view."""
    root = repository_root(root)
    receipt_path = checked_path(root / CASE_RENAME_RECEIPT)
    if receipt_path.exists():
        receipt = _validate_case_receipt(load_manifest(receipt_path), root)
        preview = receipt["preview"]
        if receipt["status"] == "completed":
            validate_case_rename_receipt(receipt, root)
        elif role_tree_inventory(_case_rename_location(root, preview)) != preview["inventory"]:
            raise CatalogError("pending role case-rename tree changed; preserve it for review")
        return preview
    source = exact_directory_entry(root, PREVIOUS_ROLE_ROOT_NAME)
    identity = directory_identity(source)
    inventory = role_tree_inventory(source)
    old_transition = source / ".transition.json"
    if old_transition.exists():
        receipt = load_manifest(old_transition)
        validate_transition_receipt(receipt, root)
        if receipt["status"] != "completed":
            raise CatalogError("finish the pending legacy transition with its original helper before renaming roles")
    if directory_identity(source) != identity:
        raise CatalogError("role directory changed during case-rename inspection")
    preview = {"schema_version": 1, "project_root": str(root), "source": PREVIOUS_ROLE_ROOT_NAME,
               "destination": ROLE_ROOT_NAME, "source_identity": identity, "inventory": inventory}
    preview["temporary"] = ".roles-case-rename-" + object_digest(preview)[:24]
    preview["preview_sha256"] = object_digest(preview)
    validate_case_rename_preview(preview, root)
    if any(item.name.casefold() == preview["temporary"].casefold() for item in root.iterdir()):
        raise CatalogError("role case-rename temporary path already exists")
    return preview


def rename_directory_no_replace(source: Path, destination: Path) -> None:
    """Use the host's exclusive rename, refusing an appearing empty directory."""
    import ctypes
    library = ctypes.CDLL(None, use_errno=True)
    if sys.platform == "darwin" and hasattr(library, "renamex_np"):
        rename = library.renamex_np
        rename.argtypes = (ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint)
        args = (os.fsencode(source), os.fsencode(destination), 0x00000004)  # RENAME_EXCL
    elif sys.platform.startswith("linux") and hasattr(library, "renameat2"):
        rename = library.renameat2
        rename.argtypes = (ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint)
        args = (-100, os.fsencode(source), -100, os.fsencode(destination), 1)  # AT_FDCWD, RENAME_NOREPLACE
    else:
        raise CatalogError("this host has no supported exclusive directory rename")
    rename.restype = ctypes.c_int
    _ontology_checkpoint(targets=False)
    if rename(*args) != 0:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error), str(destination))
    descriptor = os.open(source.parent, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def case_rename_apply(root: Path, preview: dict[str, object], *, confirmed: bool) -> dict[str, object]:
    """Rename the bound tree in two no-overwrite hops, retaining exact recovery."""
    root = repository_root(root)
    if not confirmed:
        raise CatalogError("role case rename requires explicit confirmation of the reviewed preview")
    validate_case_rename_preview(preview, root)
    with mutation_lock(root):
        receipt_path = checked_path(root / CASE_RENAME_RECEIPT)
        new_receipt = not receipt_path.exists()
        if not new_receipt:
            receipt = _validate_case_receipt(load_manifest(receipt_path), root)
            if receipt["preview"] != preview:
                raise CatalogError("another role case-rename preview owns recovery")
            if receipt["status"] == "completed":
                proof = validate_case_rename_receipt(receipt, root)
                return {**proof, "status": "current", "mutated": False, "receipt": CASE_RENAME_RECEIPT}
        else:
            if case_rename_preview(root) != preview:
                raise CatalogError("stale role case-rename preview")
            receipt = {"schema_version": 1, "preview": preview, "status": "pending"}
        try:
            if new_receipt:
                atomic_publish(receipt_path, (json.dumps(receipt, indent=2) + "\n").encode(), replace=False)
            for expected, destination in ((PREVIOUS_ROLE_ROOT_NAME, preview["temporary"]),
                                          (preview["temporary"], ROLE_ROOT_NAME)):
                current = _case_rename_location(root, preview)
                if role_tree_inventory(current) != preview["inventory"]:
                    raise CatalogError("pending role case-rename tree changed; preserve it for review")
                if current.name == expected:
                    rename_directory_no_replace(current, root / destination)
            current = _case_rename_location(root, preview)
            if current.name != ROLE_ROOT_NAME or role_tree_inventory(current) != preview["inventory"]:
                raise CatalogError("role case-rename postcondition changed")
            receipt["status"] = "completed"
            atomic_publish(receipt_path, (json.dumps(receipt, indent=2) + "\n").encode())
            proof = validate_case_rename_receipt(receipt, root)
            return {**proof, "status": "updated", "mutated": True, "receipt": CASE_RENAME_RECEIPT}
        except (CatalogError, OSError, UnicodeError) as exc:
            raise PublicationPending({"status": "partial", "receipt": CASE_RENAME_RECEIPT,
                "recovery": "case-rename-apply with the same reviewed preview and --confirmed",
                "error": str(exc)}) from exc


def validate_preview(preview: dict[str, object], root: Path, *, destination_root: str = ROLE_ROOT_NAME) -> None:
    fields = {"schema_version", "project_root", "legacy_fingerprint", "pairs", "conflicts", "receipt", "preview_sha256"}
    if not isinstance(preview, dict) or set(preview) != fields or type(preview["schema_version"]) is not int or preview["schema_version"] != 1:
        raise CatalogError("unsupported role transition preview")
    unsigned = {k: v for k, v in preview.items() if k != "preview_sha256"}
    if preview["preview_sha256"] != object_digest(unsigned) or preview["project_root"] != str(root):
        raise CatalogError("role transition preview digest or project mismatch")
    if destination_root not in {ROLE_ROOT_NAME, PREVIOUS_ROLE_ROOT_NAME}:
        raise CatalogError("unsupported transition destination root")
    if preview["receipt"] != f"{destination_root}/.transition.json" or preview["conflicts"] != []:
        raise CatalogError("role transition preview contains conflicts or an unsafe receipt")
    if not isinstance(preview["pairs"], list) or not preview["pairs"]:
        raise CatalogError("role transition needs at least one valid legacy pair")
    names = set()
    for pair in preview["pairs"]:
        if not isinstance(pair, dict) or set(pair) != {"name", "files"} or not isinstance(pair["name"], str):
            raise CatalogError("invalid transition pair")
        validate_role_name(pair["name"])
        if pair["name"] in names:
            raise CatalogError("duplicate transition pair")
        names.add(pair["name"])
        if not isinstance(pair["files"], list) or len(pair["files"]) != 2:
            raise CatalogError("transition must retain both role files")
        for filename, item in zip(("AGENTS.md", "ROLE.md"), pair["files"]):
            if not isinstance(item, dict) or set(item) != {"source", "destination", "source_sha256", "destination_sha256"}:
                raise CatalogError("invalid transition file fields")
            if item["source"] != f"{LEGACY_ROLE_ROOT_NAME}/{pair['name']}/{filename}" or item["destination"] != f"{destination_root}/{pair['name']}/{filename}":
                raise CatalogError("unconfined transition path")
            for key in ("source_sha256", "destination_sha256"):
                value = item[key]
                if key == "destination_sha256" and value is None:
                    continue
                if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
                    raise CatalogError("invalid transition digest")


def validate_transition_receipt(value: object, root: Path, *, historical: bool = False) -> dict[str, str]:
    fields = {"schema_version", "preview", "completed", "status"}
    if not historical:
        fields.add("history")
    if not isinstance(value, dict) or set(value) != fields or type(value["schema_version"]) is not int or value["schema_version"] != 1:
        raise CatalogError("unsupported transition receipt; preserve it for reviewed recovery")
    # Lowercase previews remain attributable historical provenance. Only the
    # separate case-rename proof can resolve them to current active paths.
    preview = value["preview"]
    destination_root = PREVIOUS_ROLE_ROOT_NAME if isinstance(preview, dict) and preview.get("receipt") == f"{PREVIOUS_ROLE_ROOT_NAME}/.transition.json" else ROLE_ROOT_NAME
    validate_preview(preview, root, destination_root=destination_root)
    if not isinstance(value["status"], str) or value["status"] not in {"pending", "completed"} or (historical and value["status"] != "completed"):
        raise CatalogError("invalid transition receipt status")
    destinations = {item["destination"]: item["source_sha256"] for pair in value["preview"]["pairs"] for item in pair["files"]}
    completed = value["completed"]
    if not isinstance(completed, list) or any(not isinstance(item, str) or item not in destinations for item in completed) or len(set(completed)) != len(completed):
        raise CatalogError("invalid completed transition references")
    if value["status"] == "completed" and set(completed) != set(destinations):
        raise CatalogError("completed transition receipt has incomplete destination coverage")
    if not historical:
        if not isinstance(value["history"], list):
            raise CatalogError("invalid retained transition history")
        for previous in value["history"]:
            # Historical provenance is checked internally; its old destinations
            # need not retain those bytes after a later authorized adoption.
            validate_transition_receipt(previous, root, historical=True)
    return destinations


def transition_destination_paths(value: object, root: Path) -> dict[str, str]:
    """Resolve historical paths only with the explicit completed rename proof."""
    root = repository_root(root)
    destinations = validate_transition_receipt(value, root)
    if all(item.startswith(f"{ROLE_ROOT_NAME}/") for item in destinations):
        exact_directory_entry(root, ROLE_ROOT_NAME)
        return {item: item for item in destinations}
    proof = validate_case_rename_receipt(load_manifest(root / CASE_RENAME_RECEIPT), root)
    if not set(destinations).issubset(proof["destination_paths"]):
        raise CatalogError("historical transition destinations were not in the renamed tree")
    return {item: proof["destination_paths"][item] for item in destinations}


def transition_apply(root: Path, preview: dict[str, object], *, confirmed: bool) -> dict[str, object]:
    root = repository_root(root)
    if not confirmed:
        raise CatalogError("role transition requires explicit confirmation of the reviewed preview")
    validate_preview(preview, root)
    with mutation_lock(root):
        fresh = transition_preview(root)
        receipt_path = checked_path(root / ROLE_ROOT_NAME / ".transition.json")
        prior = load_manifest(receipt_path) if receipt_path.exists() else None
        if prior is not None:
            destinations = validate_transition_receipt(prior, root)
            # Active previews never use lowercase paths. A prior completed
            # receipt may retain them after an explicit case-only rename.
            paths = transition_destination_paths(prior, root)
            if any(file_digest(root / paths[item]) != destinations[item] for item in prior["completed"]):
                raise CatalogError("a committed transition destination changed; preserve it for review")
        resuming = prior is not None and prior["preview"] == preview
        if prior is not None and prior["status"] == "pending" and not resuming:
            raise CatalogError("another reviewed role transition needs recovery first")
        if fresh["legacy_fingerprint"] != preview["legacy_fingerprint"] or fresh["conflicts"]:
            raise CatalogError("legacy roles changed or a destination is customized")
        if not resuming and fresh != preview:
            raise CatalogError("stale role transition preview")
        for pair in preview["pairs"]:
            for item in pair["files"]:
                actual = file_digest(root / item["destination"])
                allowed = {item["destination_sha256"]}
                if resuming:
                    allowed.add(item["source_sha256"])
                if actual not in allowed:
                    raise CatalogError("transition destination changed outside the reviewed publication")
        if resuming and prior["status"] == "completed":
            for pair in preview["pairs"]:
                for item in pair["files"]:
                    if file_digest(root / item["destination"]) != item["source_sha256"]:
                        raise CatalogError("completed transition bytes changed; do not replay it")
            catalog = build_catalog(root)
            if catalog.index_status != "current":
                raise PublicationPending({"status": "partial", "transition_committed": True,
                    "index_status": catalog.index_status, "recovery": "reindex",
                    "error": "completed transition has index drift; regenerate navigation explicitly"})
            return {"status": "current", "mutated": False, "receipt": str(receipt_path.relative_to(root)), **catalog.to_dict()}
        role_root = checked_path(root / ROLE_ROOT_NAME)
        role_root.mkdir(exist_ok=True)
        history = [] if prior is None else prior["history"] + ([{k: v for k, v in prior.items() if k != "history"}] if not resuming else [])
        receipt = prior if resuming else {"schema_version": 1, "preview": preview, "completed": [], "status": "pending", "history": history}
        atomic_publish(receipt_path, (json.dumps(receipt, indent=2) + "\n").encode())
        try:
            for pair in preview["pairs"]:
                target_dir = checked_path(role_root / pair["name"])
                target_dir.mkdir(exist_ok=True)
                for item in pair["files"]:
                    source = checked_path(root / item["source"])
                    content = source.read_bytes()
                    if digest_bytes(content) != item["source_sha256"]:
                        raise CatalogError("legacy role changed during publication")
                    target = checked_path(root / item["destination"])
                    current = file_digest(target)
                    if current != item["source_sha256"]:
                        if current != item["destination_sha256"]:
                            raise CatalogError("role destination changed during publication")
                        atomic_publish(target, content, replace=False)
                    if item["destination"] not in receipt["completed"]:
                        receipt["completed"].append(item["destination"])
                        atomic_publish(receipt_path, (json.dumps(receipt, indent=2) + "\n").encode())
                entry = validate_role_directory(target_dir, root)
                if not entry.valid:
                    raise CatalogError(f"published role is invalid: {entry.diagnostics}")
            publish_index(root)
            receipt["status"] = "completed"
            atomic_publish(receipt_path, (json.dumps(receipt, indent=2) + "\n").encode())
            return {"status": "updated", "mutated": True, "receipt": str(receipt_path.relative_to(root)), **build_catalog(root).to_dict()}
        except (CatalogError, OSError, UnicodeError) as exc:
            raise PublicationPending({"status": "partial", "transition_committed": True,
                "receipt": str(receipt_path.relative_to(root)), "completed_files": receipt["completed"],
                "recovery": "transition-apply with the same reviewed preview and --confirmed", "error": str(exc)}) from exc


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
        help="project root containing roles (default: current directory)",
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

    for command, help_text in (("reindex", "regenerate role navigation from current pairs"),
                               ("transition-preview", "inspect a preserved legacy-role transition"),
                               ("case-rename-preview", "inspect the exact roles to Roles rename")):
        add_format_argument(subparsers.add_parser(command, help=help_text))
    for command in ("transition-apply", "case-rename-apply"):
        transition_parser = subparsers.add_parser(command, help="apply or recover an exact reviewed preview")
        transition_parser.add_argument("--preview-file", type=Path, required=True)
        transition_parser.add_argument("--confirmed", action="store_true")
        add_format_argument(transition_parser)

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

    if args.command in {"reindex", "transition-preview", "transition-apply", "case-rename-preview", "case-rename-apply"}:
        if args.command == "reindex":
            result = reindex(root)
        elif args.command == "transition-preview":
            result = transition_preview(root)
        elif args.command == "case-rename-preview":
            result = case_rename_preview(root)
        elif args.command == "case-rename-apply":
            result = case_rename_apply(root, load_manifest(args.preview_file), confirmed=args.confirmed)
        else:
            result = transition_apply(root, load_manifest(args.preview_file), confirmed=args.confirmed)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 1 if result.get("conflicts") or result.get("invalid_roles") else 0

    if args.command == "create":
        entry, catalog = create_role(root, args)
        if args.format == "json":
            payload = catalog.to_dict()
            payload["created_role"] = entry.to_dict()
            payload["bundle_committed"] = True
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
        return 1 if catalog.invalid_roles or catalog.index_status != "current" else 0

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
    except PublicationPending as exc:
        print(json.dumps(exc.result, indent=2, sort_keys=True))
        return 3
    except (CatalogError, OSError, UnicodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2



# Optional action guard adapter.  Standalone/core use imports no ontology runtime.
def _ontology_checkpoint(*, targets=True):
    import sys as _sys
    _module = _sys.modules.get("ontology_guards")
    if _module is not None:
        _module.checkpoint(targets=targets)


def _ontology_guard_adapter(function, family, root_argument, target_paths):
    import functools as _functools
    import inspect as _inspect
    @_functools.wraps(function)
    def guarded(*args, **kwargs):
        import importlib.util as _util
        import sys as _sys
        from pathlib import Path as _Path
        arguments = dict(_inspect.signature(function).bind(*args, **kwargs).arguments)
        if root_argument == "@depot":
            selected_root = installed_locations()[0]
        else:
            selected_root = arguments[root_argument]
            if not isinstance(selected_root, (_Path, str)):
                selected_root = getattr(selected_root, "project_root", getattr(selected_root, "root", selected_root))
        selected_root = _Path(selected_root).absolute()
        config_path = selected_root / "ontology-advanced.yaml"
        if not config_path.exists() and not config_path.is_symlink():
            return function(*args, **kwargs)
        if family == "template" and arguments.get("command") == "check":
            return function(*args, **kwargs)
        import json as _json
        import hashlib as _hashlib
        def unique_pairs(pairs):
            value = {}
            for key, item in pairs:
                if key in value:
                    raise ValueError("duplicate guard configuration key")
                value[key] = item
            return value
        try:
            if config_path.is_symlink():
                raise ValueError("symbolic guard configuration")
            config = _json.loads(config_path.read_text(), object_pairs_hook=unique_pairs)
            selected = config.get("profiles", {}).get("guards", {"enabled": False})
            if config.get("schema_version") != 1 or not isinstance(selected, dict) or type(selected.get("enabled")) is not bool:
                raise ValueError("unsupported guard configuration")
        except (OSError, ValueError, AttributeError) as exc:
            raise _ontology_adapter_error("guard_schema", "Guard configuration is unreadable or unsupported.", {}) from exc
        if not selected["enabled"]:
            if set(selected) != {"enabled"}:
                raise _ontology_adapter_error("guard_schema", "Disabled guard configuration has unsupported fields.", {})
            return function(*args, **kwargs)
        script = selected_root / ".agents/skills/ontology/scripts/ontology_guards.py"
        if not script.is_file() or any(parent.is_symlink() for parent in (script, *script.parents)):
            raise _ontology_adapter_error("guard_unavailable", "Enabled guards require their current project-local installed adapter.", {})
        current_sha256 = _hashlib.sha256(script.read_bytes()).hexdigest()
        module = _sys.modules.get("ontology_guards")
        if module is not None and (_Path(module.__file__).resolve() != script.resolve()
                or getattr(module, "ENGINE_SOURCE_SHA256", None) != current_sha256):
            raise _ontology_adapter_error("guard_stale", "Loaded guard code differs from this selected project's current installed bytes; use a fresh owning-helper process after reviewed repair.", {})
        if module is None:
            spec = _util.spec_from_file_location("ontology_guards", script)
            module = _util.module_from_spec(spec)
            _sys.modules["ontology_guards"] = module
            _sys.path.insert(0, str(script.parent))
            spec.loader.exec_module(module)
        targets = list(target_paths)
        if family == "setup":
            destination = _Path(arguments["destination"]).absolute()
            try:
                relative = destination.relative_to(selected_root).as_posix()
            except ValueError:
                raise _ontology_adapter_error("guard_scope", "Setup target escapes the selected depot.", {})
            targets.extend([relative + "/control_records/project-setup.json", relative + "/AGENTS.md", relative + "/ROLE.md"])
        try:
            return module.dispatch(lambda: function(*args, **kwargs), family, function.__name__, selected_root, arguments, targets)
        except module.GuardError as exc:
            raise _ontology_adapter_error(exc.code, str(exc), exc.details) from exc
    return guarded


def _ontology_adapter_error(code, message, details):
    return CatalogError(code + ": " + message)

ONTOLOGY_GUARDED_ACTIONS = ['create_role', 'transition_apply', 'case_rename_apply', 'reindex', 'publish_index']
create_role = _ontology_guard_adapter(create_role, 'role', 'root', ['Roles', 'roles', 'control_records/roles'])
transition_apply = _ontology_guard_adapter(transition_apply, 'role', 'root', ['Roles', 'roles', 'control_records/roles'])
case_rename_apply = _ontology_guard_adapter(case_rename_apply, 'role', 'root', ['Roles', 'roles', 'control_records/roles'])
reindex = _ontology_guard_adapter(reindex, 'role', 'root', ['Roles', 'roles', 'control_records/roles'])
publish_index = _ontology_guard_adapter(publish_index, 'role', 'root', ['Roles', 'roles', 'control_records/roles'])

if __name__ == "__main__":
    raise SystemExit(main())
