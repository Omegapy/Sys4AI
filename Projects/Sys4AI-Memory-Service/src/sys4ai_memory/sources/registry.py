"""Strict readers for the canonical memory registries.

The CSV files are declarations, not executable configuration.  This module
therefore validates every row before discovery can inspect source content.
"""

from __future__ import annotations

import csv
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, replace
from enum import StrEnum
from pathlib import Path, PurePosixPath
from typing import Final
from urllib.parse import urlparse

from sys4ai_memory.contracts import AuthorityTier, Sensitivity, SourceRole, TrustClass

SOURCE_HEADER: Final = (
    "source_id",
    "project_id",
    "path_or_uri",
    "path_pattern",
    "source_kind",
    "format",
    "canonicality",
    "content_role",
    "authority_tier",
    "trust_class",
    "sensitivity",
    "namespace",
    "profile_id",
    "ingestion_adapter",
    "chunking_profile",
    "schema_ref",
    "refresh_mode",
    "retention_policy",
    "owner",
    "write_policy",
    "include_flag",
    "notes",
)

# Release fixtures intentionally use the compact pre-bootstrap declaration.
# It is a separate exact schema, not a permissive subset of the canonical one.
FIXTURE_SOURCE_HEADER: Final = (
    "source_id",
    "project_id",
    "path",
    "format",
    "canonicality",
    "authority_tier",
    "trust_class",
    "sensitivity",
    "namespace",
    "adapter",
    "include_flag",
)

PROFILE_HEADER: Final = (
    "profile_id",
    "profile_name",
    "profile_version",
    "lifecycle_status",
    "implementation_status",
    "extends_profile_id",
    "schema_ref",
    "config_ref",
    "record_types",
    "relation_types",
    "source_adapters",
    "write_policy_ref",
    "migration_ref",
    "api_compatibility",
    "owner",
    "authority_basis",
    "notes",
)

RELATION_HEADER: Final = (
    "relation_id",
    "relation_name",
    "relation_version",
    "lifecycle_status",
    "implementation_status",
    "profile_id",
    "source_types",
    "target_types",
    "directionality",
    "symmetric",
    "transitive",
    "inverse_relation",
    "authority_effect",
    "validation_rule",
    "schema_ref",
    "owner",
    "authority_basis",
    "description",
    "notes",
)

_STABLE_ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.:@/-]*$")
_SOURCE_ID_RE = re.compile(r"^src_[A-Za-z0-9][A-Za-z0-9_.:@-]*$")
_SEMVER_RE = re.compile(
    r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
    r"(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$"
)

_SOURCE_KINDS: Final = frozenset({"file", "external", "path_rule", "exclusion_rule", "generated"})
_FORMATS: Final = frozenset(
    {
        "markdown",
        "yaml",
        "csv",
        "toml",
        "json",
        "jsonl",
        "json_schema",
        "text",
        "python",
        "source_code",
        "javascript",
        "typescript",
        "rust",
        "go",
        "java",
        "c",
        "cpp",
        "shell",
        "pdf",
        "html",
        "docx",
        "xlsx",
        "pptx",
        "image",
        "audio",
        "domain",
        "any",
    }
)
_CANONICALITIES: Final = frozenset(
    {"canonical", "evidential", "generated", "episodic", "scratch", "excluded"}
)
_PROFILE_LIFECYCLES: Final = frozenset(
    {"approved-contract", "active", "deprecated", "retired", "proposed"}
)
_IMPLEMENTATION_STATUSES: Final = frozenset(
    {"not-implemented", "partial", "implemented", "verified", "deprecated", "retired"}
)


class RegistryValidationError(ValueError):
    """A registry failed closed before any source content was inspected."""

    def __init__(
        self,
        message: str,
        *,
        path: Path | None = None,
        row_number: int | None = None,
        field: str | None = None,
    ) -> None:
        location = str(path) if path is not None else "registry"
        if row_number is not None:
            location += f":{row_number}"
        if field is not None:
            location += f" [{field}]"
        super().__init__(f"{location}: {message}")
        self.path = path
        self.row_number = row_number
        self.field = field


@dataclass(frozen=True, slots=True)
class SourceRegistryEntry:
    """Validated source rule, including compact-fixture defaults."""

    source_id: str
    project_id: str
    path_or_uri: str | None
    path_pattern: str | None
    source_kind: str
    format: str
    canonicality: str
    content_role: str
    authority_tier: AuthorityTier
    trust_class: TrustClass
    sensitivity: Sensitivity
    namespace: str
    profile_id: str
    ingestion_adapter: str
    chunking_profile: str
    schema_ref: str | None
    refresh_mode: str
    retention_policy: str
    owner: str
    write_policy: str
    include_flag: bool
    notes: str | None
    registry_path: Path | None = None
    row_number: int | None = None
    one_time: bool = False
    generated_from: tuple[str, ...] = ()

    @property
    def source_role(self) -> SourceRole:
        """Map registry canonicality to the stable public source-role enum."""

        return {
            "canonical": SourceRole.AUTHORITATIVE,
            "evidential": SourceRole.EVIDENTIAL,
            "generated": SourceRole.GENERATED,
            "episodic": SourceRole.EPISODIC,
            "scratch": SourceRole.SCRATCH,
            "excluded": SourceRole.SCRATCH,
        }[self.canonicality]

    @property
    def is_external(self) -> bool:
        return self.source_kind == "external"

    @property
    def is_exclusion(self) -> bool:
        return (
            self.source_kind == "exclusion_rule"
            or not self.include_flag
            or self.canonicality == "excluded"
        )

    def as_one_time(self) -> SourceRegistryEntry:
        return replace(self, one_time=True)


@dataclass(frozen=True, slots=True)
class ProfileRegistryEntry:
    profile_id: str
    profile_name: str
    profile_version: str
    lifecycle_status: str
    implementation_status: str
    extends_profile_id: str | None
    schema_ref: str
    config_ref: str
    record_types: tuple[str, ...]
    relation_types: tuple[str, ...]
    source_adapters: tuple[str, ...]
    write_policy_ref: str
    migration_ref: str | None
    api_compatibility: str
    owner: str
    authority_basis: tuple[str, ...]
    notes: str | None


@dataclass(frozen=True, slots=True)
class RelationRegistryEntry:
    relation_id: str
    relation_name: str
    relation_version: str
    lifecycle_status: str
    implementation_status: str
    profile_id: str
    source_types: tuple[str, ...]
    target_types: tuple[str, ...]
    directionality: str
    symmetric: bool
    transitive: bool
    inverse_relation: str | None
    authority_effect: str
    validation_rule: tuple[str, ...]
    schema_ref: str
    owner: str
    authority_basis: str
    description: str
    notes: str | None


@dataclass(frozen=True, slots=True)
class RegistryBundle:
    sources: tuple[SourceRegistryEntry, ...]
    profiles: tuple[ProfileRegistryEntry, ...]
    relations: tuple[RelationRegistryEntry, ...]

    def with_one_time_sources(self, entries: Iterable[SourceRegistryEntry]) -> RegistryBundle:
        additions = tuple(entry.as_one_time() for entry in entries)
        combined = (*self.sources, *additions)
        _require_unique(
            combined,
            key=lambda item: item.source_id,
            label="source_id",
        )
        known_profiles = {profile.profile_id for profile in self.profiles}
        for entry in additions:
            _validate_source_entry(entry, known_profiles=known_profiles)
        by_id = {entry.source_id: entry for entry in combined}
        for entry in combined:
            if entry.source_role is not SourceRole.GENERATED:
                continue
            for source_id in entry.generated_from:
                parent = by_id.get(source_id)
                if parent is None:
                    raise RegistryValidationError(
                        f"unresolved generated_from source ID {source_id!r}",
                        field="generated_from",
                    )
                if parent.canonicality != "canonical":
                    raise RegistryValidationError(
                        f"generated_from source {source_id!r} is not canonical",
                        field="generated_from",
                    )
                if int(entry.authority_tier.value[1:]) < int(parent.authority_tier.value[1:]):
                    raise RegistryValidationError(
                        "generated source authority cannot outrank its canonical input",
                        field="authority_tier",
                    )
        return RegistryBundle(combined, self.profiles, self.relations)


def _read_csv(
    path: Path, accepted_headers: tuple[tuple[str, ...], ...]
) -> tuple[tuple[str, ...], list[tuple[int, tuple[str, ...]]]]:
    try:
        with path.open("r", encoding="utf-8", newline="") as stream:
            reader = csv.reader(stream, strict=True)
            try:
                header = tuple(next(reader))
            except StopIteration as error:
                raise RegistryValidationError("registry is empty", path=path) from error
            if header not in accepted_headers:
                expected = " or ".join(",".join(item) for item in accepted_headers)
                raise RegistryValidationError(
                    f"header must exactly equal: {expected}", path=path, row_number=1
                )
            rows: list[tuple[int, tuple[str, ...]]] = []
            for row in reader:
                row_number = reader.line_num
                values = tuple(row)
                if not values or all(not value for value in values):
                    raise RegistryValidationError(
                        "blank rows are not allowed", path=path, row_number=row_number
                    )
                if len(values) != len(header):
                    raise RegistryValidationError(
                        f"expected {len(header)} columns, found {len(values)}",
                        path=path,
                        row_number=row_number,
                    )
                for field_name, value in zip(header, values, strict=True):
                    if "\x00" in value:
                        raise RegistryValidationError(
                            "NUL is not allowed",
                            path=path,
                            row_number=row_number,
                            field=field_name,
                        )
                    if value != value.strip():
                        raise RegistryValidationError(
                            "leading or trailing whitespace is invalid",
                            path=path,
                            row_number=row_number,
                            field=field_name,
                        )
                rows.append((row_number, values))
    except UnicodeDecodeError as error:
        raise RegistryValidationError("registry must be UTF-8", path=path) from error
    except csv.Error as error:
        raise RegistryValidationError(f"invalid CSV: {error}", path=path) from error
    return header, rows


def _require(value: str, field: str, *, path: Path, row: int) -> str:
    if not value:
        raise RegistryValidationError("value is required", path=path, row_number=row, field=field)
    return value


def _optional(value: str) -> str | None:
    return value or None


def _parse_bool(value: str, field: str, *, path: Path, row: int) -> bool:
    if value == "true":
        return True
    if value == "false":
        return False
    raise RegistryValidationError(
        "expected lowercase true or false", path=path, row_number=row, field=field
    )


def _parse_set(
    value: str,
    field: str,
    *,
    path: Path,
    row: int,
    required: bool = True,
) -> tuple[str, ...]:
    if not value:
        if required:
            raise RegistryValidationError(
                "value is required", path=path, row_number=row, field=field
            )
        return ()
    members = tuple(value.split("|"))
    if any(not member or member != member.strip() for member in members):
        raise RegistryValidationError(
            "set members must be nonblank and have no outer whitespace",
            path=path,
            row_number=row,
            field=field,
        )
    if len(members) != len(set(members)):
        raise RegistryValidationError(
            "set members must be unique", path=path, row_number=row, field=field
        )
    return members


def _validate_identifier(value: str, field: str, *, path: Path, row: int) -> None:
    if not _STABLE_ID_RE.fullmatch(value):
        raise RegistryValidationError(
            "invalid stable identifier", path=path, row_number=row, field=field
        )


def _validate_relative(
    value: str,
    field: str,
    *,
    path: Path,
    row: int,
    pattern: bool = False,
) -> None:
    if "\\" in value:
        raise RegistryValidationError(
            "repository paths must use forward slashes",
            path=path,
            row_number=row,
            field=field,
        )
    candidate = PurePosixPath(value)
    if candidate.is_absolute() or any(part in {"", ".", ".."} for part in candidate.parts):
        raise RegistryValidationError(
            "path must be project-relative without dot or traversal segments",
            path=path,
            row_number=row,
            field=field,
        )
    if pattern and not any(character in value for character in "*?["):
        # A literal path rule is valid, but calling it out catches accidental
        # empty-pattern substitutions while preserving the documented format.
        return


def _validate_uri(value: str, field: str, *, path: Path, row: int) -> None:
    parsed = urlparse(value)
    if not parsed.scheme or parsed.scheme == "file":
        raise RegistryValidationError(
            "external origin must be a non-file absolute URI",
            path=path,
            row_number=row,
            field=field,
        )


def _enum_value[EnumT: StrEnum](
    enum_type: type[EnumT],
    value: str,
    field: str,
    *,
    path: Path,
    row: int,
) -> EnumT:
    try:
        return enum_type(value)
    except ValueError as error:
        raise RegistryValidationError(
            f"unsupported enum value {value!r}",
            path=path,
            row_number=row,
            field=field,
        ) from error


def _chunking_for_format(format_name: str) -> str:
    return {
        "markdown": "heading-blocks@1",
        "yaml": "structured-fields@1",
        "csv": "row@1",
        "toml": "structured-fields@1",
        "json": "structured-fields@1",
        "jsonl": "row@1",
        "json_schema": "schema-definitions@1",
        "text": "paragraph@1",
    }.get(format_name, "code-symbols@1")


def _source_from_full(path: Path, row_number: int, values: tuple[str, ...]) -> SourceRegistryEntry:
    row = dict(zip(SOURCE_HEADER, values, strict=True))
    path_or_uri = _optional(row["path_or_uri"])
    path_pattern = _optional(row["path_pattern"])
    return SourceRegistryEntry(
        source_id=row["source_id"],
        project_id=row["project_id"],
        path_or_uri=path_or_uri,
        path_pattern=path_pattern,
        source_kind=row["source_kind"],
        format=row["format"],
        canonicality=row["canonicality"],
        content_role=row["content_role"],
        authority_tier=_enum_value(
            AuthorityTier, row["authority_tier"], "authority_tier", path=path, row=row_number
        ),
        trust_class=_enum_value(
            TrustClass, row["trust_class"], "trust_class", path=path, row=row_number
        ),
        sensitivity=_enum_value(
            Sensitivity, row["sensitivity"], "sensitivity", path=path, row=row_number
        ),
        namespace=row["namespace"],
        profile_id=row["profile_id"],
        ingestion_adapter=row["ingestion_adapter"],
        chunking_profile=row["chunking_profile"],
        schema_ref=_optional(row["schema_ref"]),
        refresh_mode=row["refresh_mode"],
        retention_policy=row["retention_policy"],
        owner=row["owner"],
        write_policy=row["write_policy"],
        include_flag=_parse_bool(row["include_flag"], "include_flag", path=path, row=row_number),
        notes=_optional(row["notes"]),
        registry_path=path,
        row_number=row_number,
    )


def _source_from_fixture(
    path: Path, row_number: int, values: tuple[str, ...]
) -> SourceRegistryEntry:
    row = dict(zip(FIXTURE_SOURCE_HEADER, values, strict=True))
    canonicality = row["canonicality"]
    return SourceRegistryEntry(
        source_id=row["source_id"],
        project_id=row["project_id"],
        path_or_uri=row["path"],
        path_pattern=None,
        source_kind="file",
        format=row["format"],
        canonicality=canonicality,
        content_role="fixture-source",
        authority_tier=_enum_value(
            AuthorityTier, row["authority_tier"], "authority_tier", path=path, row=row_number
        ),
        trust_class=_enum_value(
            TrustClass, row["trust_class"], "trust_class", path=path, row=row_number
        ),
        sensitivity=_enum_value(
            Sensitivity, row["sensitivity"], "sensitivity", path=path, row=row_number
        ),
        namespace=row["namespace"],
        profile_id="base@1",
        ingestion_adapter=row["adapter"],
        chunking_profile=_chunking_for_format(row["format"]),
        schema_ref=None,
        refresh_mode="git-revision",
        retention_policy="canonical" if canonicality == "canonical" else "fixture-evidence",
        owner=row["project_id"],
        write_policy="deny",
        include_flag=_parse_bool(row["include_flag"], "include_flag", path=path, row=row_number),
        notes="Release verification fixture declaration",
        registry_path=path,
        row_number=row_number,
    )


def _validate_source_entry(
    entry: SourceRegistryEntry, *, known_profiles: set[str] | None = None
) -> None:
    path = entry.registry_path or Path("<one-time-registration>")
    row = entry.row_number or 1
    if not _SOURCE_ID_RE.fullmatch(entry.source_id):
        raise RegistryValidationError(
            "source_id must use the public src_ prefix",
            path=path,
            row_number=row,
            field="source_id",
        )
    _validate_identifier(entry.project_id, "project_id", path=path, row=row)
    if (entry.path_or_uri is None) == (entry.path_pattern is None):
        raise RegistryValidationError(
            "exactly one of path_or_uri and path_pattern is required",
            path=path,
            row_number=row,
        )
    if entry.source_kind not in _SOURCE_KINDS:
        raise RegistryValidationError(
            f"unsupported source_kind {entry.source_kind!r}",
            path=path,
            row_number=row,
            field="source_kind",
        )
    if entry.format not in _FORMATS:
        raise RegistryValidationError(
            f"unsupported format {entry.format!r}",
            path=path,
            row_number=row,
            field="format",
        )
    if entry.canonicality not in _CANONICALITIES:
        raise RegistryValidationError(
            f"unsupported canonicality {entry.canonicality!r}",
            path=path,
            row_number=row,
            field="canonicality",
        )
    for field_name, value in (
        ("content_role", entry.content_role),
        ("namespace", entry.namespace),
        ("profile_id", entry.profile_id),
        ("ingestion_adapter", entry.ingestion_adapter),
        ("chunking_profile", entry.chunking_profile),
        ("refresh_mode", entry.refresh_mode),
        ("retention_policy", entry.retention_policy),
        ("owner", entry.owner),
        ("write_policy", entry.write_policy),
    ):
        _require(value, field_name, path=path, row=row)
    if entry.path_pattern is not None:
        _validate_relative(entry.path_pattern, "path_pattern", path=path, row=row, pattern=True)
        if entry.source_kind not in {"path_rule", "exclusion_rule"}:
            raise RegistryValidationError(
                "path_pattern requires path_rule or exclusion_rule",
                path=path,
                row_number=row,
                field="source_kind",
            )
    if entry.path_or_uri is not None:
        if entry.source_kind == "external":
            _validate_uri(entry.path_or_uri, "path_or_uri", path=path, row=row)
        else:
            _validate_relative(entry.path_or_uri, "path_or_uri", path=path, row=row)
    if entry.is_exclusion:
        if entry.include_flag:
            raise RegistryValidationError(
                "exclusion rules cannot set include_flag=true",
                path=path,
                row_number=row,
                field="include_flag",
            )
        if entry.format != "any" and entry.source_kind == "exclusion_rule":
            raise RegistryValidationError(
                "exclusion rules must use format=any",
                path=path,
                row_number=row,
                field="format",
            )
    elif entry.format == "any":
        raise RegistryValidationError(
            "format=any is valid only for exclusions",
            path=path,
            row_number=row,
            field="format",
        )
    if entry.source_role is SourceRole.GENERATED and not entry.generated_from:
        raise RegistryValidationError(
            "generated registrations require generated_from source IDs",
            path=path,
            row_number=row,
            field="generated_from",
        )
    if len(entry.generated_from) != len(set(entry.generated_from)):
        raise RegistryValidationError(
            "generated_from source IDs must be unique",
            path=path,
            row_number=row,
            field="generated_from",
        )
    if entry.source_id in entry.generated_from:
        raise RegistryValidationError(
            "a generated source cannot cite itself as an input",
            path=path,
            row_number=row,
            field="generated_from",
        )
    for source_id in entry.generated_from:
        if not _SOURCE_ID_RE.fullmatch(source_id):
            raise RegistryValidationError(
                "generated_from values must use the public src_ prefix",
                path=path,
                row_number=row,
                field="generated_from",
            )
    if known_profiles is not None and entry.profile_id not in known_profiles:
        raise RegistryValidationError(
            f"unresolved profile_id {entry.profile_id!r}",
            path=path,
            row_number=row,
            field="profile_id",
        )
    if entry.schema_ref is not None:
        _validate_relative(entry.schema_ref, "schema_ref", path=path, row=row)


def _require_unique(values: Iterable[object], *, key: object, label: str) -> None:
    # Callable is intentionally kept local to avoid exposing a generic registry
    # abstraction for three small versioned formats.
    getter = key
    if not callable(getter):
        raise TypeError("key must be callable")
    seen: set[object] = set()
    for value in values:
        identity = getter(value)
        if identity in seen:
            raise RegistryValidationError(f"duplicate {label}: {identity!r}")
        seen.add(identity)


def load_source_registry(
    path: Path,
    *,
    known_profiles: Iterable[str] | None = None,
) -> tuple[SourceRegistryEntry, ...]:
    """Load the canonical or exact compact-fixture source registry."""

    header, rows = _read_csv(path, (SOURCE_HEADER, FIXTURE_SOURCE_HEADER))
    entries = tuple(
        _source_from_full(path, row_number, values)
        if header == SOURCE_HEADER
        else _source_from_fixture(path, row_number, values)
        for row_number, values in rows
    )
    profiles = set(known_profiles) if known_profiles is not None else None
    for entry in entries:
        _validate_source_entry(entry, known_profiles=profiles)
    _require_unique(entries, key=lambda item: item.source_id, label="source_id")
    return entries


def load_profile_registry(path: Path) -> tuple[ProfileRegistryEntry, ...]:
    header, rows = _read_csv(path, (PROFILE_HEADER,))
    del header
    entries: list[ProfileRegistryEntry] = []
    for row_number, values in rows:
        row = dict(zip(PROFILE_HEADER, values, strict=True))
        for field in (
            "profile_id",
            "profile_name",
            "profile_version",
            "lifecycle_status",
            "implementation_status",
            "schema_ref",
            "config_ref",
            "write_policy_ref",
            "api_compatibility",
            "owner",
            "authority_basis",
        ):
            _require(row[field], field, path=path, row=row_number)
        _validate_identifier(row["profile_id"], "profile_id", path=path, row=row_number)
        if not _SEMVER_RE.fullmatch(row["profile_version"]):
            raise RegistryValidationError(
                "profile_version must be semantic version",
                path=path,
                row_number=row_number,
                field="profile_version",
            )
        if row["lifecycle_status"] not in _PROFILE_LIFECYCLES:
            raise RegistryValidationError(
                "unsupported lifecycle_status",
                path=path,
                row_number=row_number,
                field="lifecycle_status",
            )
        if row["implementation_status"] not in _IMPLEMENTATION_STATUSES:
            raise RegistryValidationError(
                "unsupported implementation_status",
                path=path,
                row_number=row_number,
                field="implementation_status",
            )
        _validate_relative(row["schema_ref"], "schema_ref", path=path, row=row_number)
        _validate_relative(row["config_ref"], "config_ref", path=path, row=row_number)
        migration = _optional(row["migration_ref"])
        if migration is not None:
            _validate_relative(migration, "migration_ref", path=path, row=row_number)
        entries.append(
            ProfileRegistryEntry(
                profile_id=row["profile_id"],
                profile_name=row["profile_name"],
                profile_version=row["profile_version"],
                lifecycle_status=row["lifecycle_status"],
                implementation_status=row["implementation_status"],
                extends_profile_id=_optional(row["extends_profile_id"]),
                schema_ref=row["schema_ref"],
                config_ref=row["config_ref"],
                record_types=_parse_set(
                    row["record_types"], "record_types", path=path, row=row_number
                ),
                relation_types=_parse_set(
                    row["relation_types"], "relation_types", path=path, row=row_number
                ),
                source_adapters=_parse_set(
                    row["source_adapters"], "source_adapters", path=path, row=row_number
                ),
                write_policy_ref=row["write_policy_ref"],
                migration_ref=migration,
                api_compatibility=row["api_compatibility"],
                owner=row["owner"],
                authority_basis=_parse_set(
                    row["authority_basis"], "authority_basis", path=path, row=row_number
                )
                if "|" in row["authority_basis"]
                else (row["authority_basis"],),
                notes=_optional(row["notes"]),
            )
        )
    result = tuple(entries)
    _require_unique(result, key=lambda item: item.profile_id, label="profile_id")
    _validate_profile_graph(result, path)
    return result


def _validate_profile_graph(entries: tuple[ProfileRegistryEntry, ...], path: Path) -> None:
    by_id = {entry.profile_id: entry for entry in entries}
    for entry in entries:
        parent = entry.extends_profile_id
        if parent is not None and parent not in by_id:
            raise RegistryValidationError(
                f"unresolved extends_profile_id {parent!r}", path=path, field="extends_profile_id"
            )
        visited: set[str] = set()
        cursor: ProfileRegistryEntry | None = entry
        while cursor is not None and cursor.extends_profile_id is not None:
            if cursor.profile_id in visited:
                raise RegistryValidationError(
                    f"profile inheritance cycle includes {cursor.profile_id!r}", path=path
                )
            visited.add(cursor.profile_id)
            cursor = by_id.get(cursor.extends_profile_id)


def load_relation_registry(path: Path) -> tuple[RelationRegistryEntry, ...]:
    header, rows = _read_csv(path, (RELATION_HEADER,))
    del header
    entries: list[RelationRegistryEntry] = []
    for row_number, values in rows:
        row = dict(zip(RELATION_HEADER, values, strict=True))
        for field in (
            "relation_id",
            "relation_name",
            "relation_version",
            "lifecycle_status",
            "implementation_status",
            "profile_id",
            "directionality",
            "symmetric",
            "transitive",
            "authority_effect",
            "schema_ref",
            "owner",
            "authority_basis",
            "description",
        ):
            _require(row[field], field, path=path, row=row_number)
        _validate_identifier(row["relation_id"], "relation_id", path=path, row=row_number)
        if not re.fullmatch(r"[A-Z][A-Z0-9_]*", row["relation_name"]):
            raise RegistryValidationError(
                "relation_name must be uppercase underscore form",
                path=path,
                row_number=row_number,
                field="relation_name",
            )
        if not _SEMVER_RE.fullmatch(row["relation_version"]):
            raise RegistryValidationError(
                "relation_version must be semantic version",
                path=path,
                row_number=row_number,
                field="relation_version",
            )
        if row["lifecycle_status"] not in _PROFILE_LIFECYCLES:
            raise RegistryValidationError(
                "unsupported lifecycle_status",
                path=path,
                row_number=row_number,
                field="lifecycle_status",
            )
        if row["implementation_status"] not in _IMPLEMENTATION_STATUSES:
            raise RegistryValidationError(
                "unsupported implementation_status",
                path=path,
                row_number=row_number,
                field="implementation_status",
            )
        if row["directionality"] not in {"directed", "bidirectional"}:
            raise RegistryValidationError(
                "directionality must be directed or bidirectional",
                path=path,
                row_number=row_number,
                field="directionality",
            )
        if row["authority_effect"] != "none":
            raise RegistryValidationError(
                "base relations cannot raise authority",
                path=path,
                row_number=row_number,
                field="authority_effect",
            )
        _validate_relative(row["schema_ref"], "schema_ref", path=path, row=row_number)
        entries.append(
            RelationRegistryEntry(
                relation_id=row["relation_id"],
                relation_name=row["relation_name"],
                relation_version=row["relation_version"],
                lifecycle_status=row["lifecycle_status"],
                implementation_status=row["implementation_status"],
                profile_id=row["profile_id"],
                source_types=_parse_set(
                    row["source_types"], "source_types", path=path, row=row_number
                ),
                target_types=_parse_set(
                    row["target_types"], "target_types", path=path, row=row_number
                ),
                directionality=row["directionality"],
                symmetric=_parse_bool(row["symmetric"], "symmetric", path=path, row=row_number),
                transitive=_parse_bool(row["transitive"], "transitive", path=path, row=row_number),
                inverse_relation=_optional(row["inverse_relation"]),
                authority_effect=row["authority_effect"],
                validation_rule=_parse_set(
                    row["validation_rule"], "validation_rule", path=path, row=row_number
                ),
                schema_ref=row["schema_ref"],
                owner=row["owner"],
                authority_basis=row["authority_basis"],
                description=row["description"],
                notes=_optional(row["notes"]),
            )
        )
    result = tuple(entries)
    _require_unique(result, key=lambda item: item.relation_id, label="relation_id")
    _require_unique(result, key=lambda item: item.relation_name, label="relation_name")
    names = {entry.relation_name for entry in result}
    for entry in result:
        if entry.inverse_relation is not None and entry.inverse_relation not in names:
            raise RegistryValidationError(
                f"unresolved inverse_relation {entry.inverse_relation!r}",
                path=path,
                field="inverse_relation",
            )
        if entry.symmetric and entry.directionality != "bidirectional":
            raise RegistryValidationError(
                "symmetric relations must be bidirectional", path=path, field="symmetric"
            )
    return result


def _check_project_reference(project_root: Path, reference: str, label: str) -> None:
    candidate = project_root.joinpath(*PurePosixPath(reference).parts)
    if candidate.is_symlink() or not candidate.is_file():
        raise RegistryValidationError(f"unresolved {label} reference {reference!r}")
    try:
        candidate.resolve(strict=True).relative_to(project_root.resolve(strict=True))
    except ValueError as error:
        raise RegistryValidationError(f"{label} reference escapes project root") from error


def load_registry_bundle(
    *,
    source_registry: Path,
    profile_registry: Path,
    relation_registry: Path,
    project_root: Path,
    one_time_sources: Iterable[SourceRegistryEntry] = (),
) -> RegistryBundle:
    """Load all registries and resolve every cross-registry reference."""

    profiles = load_profile_registry(profile_registry)
    profile_ids = {profile.profile_id for profile in profiles}
    sources = load_source_registry(source_registry, known_profiles=profile_ids)
    relations = load_relation_registry(relation_registry)
    for relation in relations:
        if relation.profile_id not in profile_ids:
            raise RegistryValidationError(
                f"unresolved relation profile_id {relation.profile_id!r}",
                path=relation_registry,
                field="profile_id",
            )
    relation_names = {relation.relation_name for relation in relations}
    for profile in profiles:
        unresolved = set(profile.relation_types) - relation_names
        if unresolved:
            raise RegistryValidationError(
                f"unresolved relation types: {sorted(unresolved)!r}",
                path=profile_registry,
                field="relation_types",
            )
        _check_project_reference(project_root, profile.schema_ref, "profile schema")
        _check_project_reference(project_root, profile.config_ref, "profile config")
        if "/" in profile.write_policy_ref or profile.write_policy_ref.endswith(".md"):
            _check_project_reference(project_root, profile.write_policy_ref, "write policy")
        if profile.migration_ref is not None:
            _check_project_reference(project_root, profile.migration_ref, "migration")
    for relation in relations:
        _check_project_reference(project_root, relation.schema_ref, "relation schema")
    for source in sources:
        if source.schema_ref is not None:
            _check_project_reference(project_root, source.schema_ref, "source schema")
    bundle = RegistryBundle(sources=sources, profiles=profiles, relations=relations)
    return bundle.with_one_time_sources(one_time_sources)


def source_entries_by_project(
    entries: Iterable[SourceRegistryEntry],
) -> Mapping[str, tuple[SourceRegistryEntry, ...]]:
    grouped: dict[str, list[SourceRegistryEntry]] = {}
    for entry in entries:
        grouped.setdefault(entry.project_id, []).append(entry)
    return {key: tuple(value) for key, value in grouped.items()}
