"""Default-deny, registry-driven discovery inside one project root."""

from __future__ import annotations

import fnmatch
import hashlib
import os
import re
import shutil
import stat
import subprocess
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from pathlib import Path, PurePosixPath

from sys4ai_memory.contracts import API_VERSION, SCHEMA_VERSION, MemoryScope
from sys4ai_memory.contracts.models import ScopeReference, SourceRecord
from sys4ai_memory.util.ids import stable_id
from sys4ai_memory.util.paths import PathBoundaryError, resolve_within
from sys4ai_memory.util.time import ensure_utc, utc_now

from .registry import SourceRegistryEntry

_SOURCE_CODE_SUFFIXES = frozenset(
    {
        ".py",
        ".pyi",
        ".js",
        ".jsx",
        ".mjs",
        ".cjs",
        ".ts",
        ".tsx",
        ".rs",
        ".go",
        ".java",
        ".c",
        ".h",
        ".cc",
        ".cpp",
        ".cxx",
        ".hpp",
        ".sh",
        ".bash",
        ".zsh",
    }
)

_FORMAT_SUFFIXES: Mapping[str, frozenset[str]] = {
    "markdown": frozenset({".md", ".markdown"}),
    "yaml": frozenset({".yaml", ".yml"}),
    "csv": frozenset({".csv"}),
    "toml": frozenset({".toml"}),
    "json": frozenset({".json"}),
    "jsonl": frozenset({".jsonl", ".ndjson"}),
    "json_schema": frozenset({".json"}),
    "text": frozenset({".txt", ".text"}),
    "python": frozenset({".py", ".pyi"}),
    "source_code": _SOURCE_CODE_SUFFIXES,
    "javascript": frozenset({".js", ".jsx", ".mjs", ".cjs"}),
    "typescript": frozenset({".ts", ".tsx"}),
    "rust": frozenset({".rs"}),
    "go": frozenset({".go"}),
    "java": frozenset({".java"}),
    "c": frozenset({".c", ".h"}),
    "cpp": frozenset({".cc", ".cpp", ".cxx", ".hpp"}),
    "shell": frozenset({".sh", ".bash", ".zsh"}),
    "pdf": frozenset({".pdf"}),
    "html": frozenset({".html", ".htm"}),
    "docx": frozenset({".docx"}),
    "xlsx": frozenset({".xlsx"}),
    "pptx": frozenset({".pptx"}),
    "image": frozenset({".png", ".jpg", ".jpeg", ".gif", ".webp", ".tif", ".tiff"}),
    "audio": frozenset({".wav", ".mp3", ".m4a", ".flac", ".ogg"}),
    "domain": frozenset({".domain"}),
}

_SECRET_CONTENT_PATTERNS = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        rb"-----BEGIN [A-Z ]*PRIVATE KEY-----",
        rb"\bsk-(?:proj-)?[A-Za-z0-9_-]{8,}\b",
        rb"\b(?:api[_-]?key|access[_-]?token|password|secret)\s*[:=]\s*[^\s]+",
    )
)


class DiscoveryDisposition(StrEnum):
    INCLUDED = "included"
    EXCLUDED = "excluded"
    REJECTED = "rejected"
    UNMATCHED = "unmatched"


class DiscoveryReason(StrEnum):
    REGISTERED_INCLUDE = "registered_include"
    REGISTERED_EXCLUSION = "registered_exclusion"
    DEFAULT_DENY = "default_deny_unmatched"
    UNSAFE_PATH = "unsafe_path"
    SYMLINK = "symlink_not_allowed"
    MISSING = "source_missing"
    NOT_REGULAR = "not_regular_file"
    GIT_IGNORED = "git_ignored"
    GENERATED_PATH = "generated_or_cache_path"
    SECRET_PATH = "secret_path"  # noqa: S105 - classification label
    SECRET_CONTENT = "secret_content_detected"  # noqa: S105 - classification label
    OVERSIZED = "source_too_large"
    UNSUPPORTED_FORMAT = "unsupported_format"
    AMBIGUOUS = "ambiguous_include_rules"
    PATTERN_EMPTY = "registered_pattern_unmatched"
    EXTERNAL_REQUIRES_CONTENT = "external_requires_explicit_content"


@dataclass(frozen=True, slots=True)
class DiscoveryDecision:
    path_or_uri: str
    disposition: DiscoveryDisposition
    reason: DiscoveryReason
    rule_ids: tuple[str, ...]
    source_id: str | None = None
    detail: str | None = None


@dataclass(frozen=True, slots=True)
class DiscoveryReport:
    project_id: str
    project_root: Path
    generated_at: datetime
    records: tuple[SourceRecord, ...]
    decisions: tuple[DiscoveryDecision, ...]

    @property
    def included(self) -> tuple[DiscoveryDecision, ...]:
        return tuple(
            item for item in self.decisions if item.disposition is DiscoveryDisposition.INCLUDED
        )

    @property
    def excluded(self) -> tuple[DiscoveryDecision, ...]:
        return tuple(
            item for item in self.decisions if item.disposition is not DiscoveryDisposition.INCLUDED
        )

    def explanation_for(self, path_or_uri: str) -> DiscoveryDecision | None:
        return next((item for item in self.decisions if item.path_or_uri == path_or_uri), None)


class SourceDiscovery:
    """Resolve registered sources without initializing any derived storage."""

    def __init__(
        self,
        *,
        project_root: Path,
        project_id: str,
        entries: Iterable[SourceRegistryEntry],
        max_file_bytes: int = 8 * 1024 * 1024,
        max_candidates: int = 10_000,
        respect_gitignore: bool = True,
        secret_scan: bool = True,
    ) -> None:
        if not project_root.is_absolute() or project_root.is_symlink() or not project_root.is_dir():
            raise PathBoundaryError(
                "project root must be an absolute existing non-symlink directory"
            )
        if max_file_bytes <= 0 or max_candidates <= 0:
            raise ValueError("discovery limits must be positive")
        self.project_root = project_root.resolve(strict=True)
        self.project_id = project_id
        self.entries = tuple(entry for entry in entries if entry.project_id == project_id)
        self.max_file_bytes = max_file_bytes
        self.max_candidates = max_candidates
        self.respect_gitignore = respect_gitignore
        self.secret_scan = secret_scan

    def discover(self, *, candidate_paths: Iterable[str] = ()) -> DiscoveryReport:
        """Discover registered repository files and explain every considered path."""

        candidates: dict[str, None] = {}
        decisions: list[DiscoveryDecision] = []
        include_patterns = tuple(entry for entry in self.entries if not entry.is_exclusion)
        repository_entries = tuple(entry for entry in include_patterns if not entry.is_external)

        for candidate in candidate_paths:
            normalized = self._normalize_candidate(candidate)
            if normalized is None:
                decisions.append(
                    DiscoveryDecision(
                        candidate,
                        DiscoveryDisposition.REJECTED,
                        DiscoveryReason.UNSAFE_PATH,
                        (),
                    )
                )
                continue
            candidates[normalized] = None

        for entry in repository_entries:
            if entry.path_or_uri is not None:
                candidates[entry.path_or_uri] = None
                continue
            assert entry.path_pattern is not None
            matches = self._expand_pattern(entry.path_pattern)
            if not matches:
                decisions.append(
                    DiscoveryDecision(
                        entry.path_pattern,
                        DiscoveryDisposition.UNMATCHED,
                        DiscoveryReason.PATTERN_EMPTY,
                        (entry.source_id,),
                    )
                )
            for match in matches:
                candidates[match] = None

        for entry in include_patterns:
            if entry.is_external:
                assert entry.path_or_uri is not None
                decisions.append(
                    DiscoveryDecision(
                        entry.path_or_uri,
                        DiscoveryDisposition.UNMATCHED,
                        DiscoveryReason.EXTERNAL_REQUIRES_CONTENT,
                        (entry.source_id,),
                        source_id=entry.source_id,
                    )
                )

        if len(candidates) > self.max_candidates:
            raise ValueError(
                f"discovery candidate limit exceeded: {len(candidates)} > {self.max_candidates}"
            )

        records: list[SourceRecord] = []
        for candidate in sorted(candidates):
            decision, record = self._inspect_candidate(candidate, read_content=True)
            decisions.append(decision)
            if record is not None:
                records.append(record)

        records.sort(key=lambda item: (item.path_or_uri, item.source_id))
        decisions.sort(key=lambda item: (item.path_or_uri, item.reason.value, item.rule_ids))
        return DiscoveryReport(
            project_id=self.project_id,
            project_root=self.project_root,
            generated_at=utc_now(),
            records=tuple(records),
            decisions=tuple(decisions),
        )

    def explain_path(self, candidate: str) -> DiscoveryDecision:
        """Explain policy and metadata checks without reading file content."""

        normalized = self._normalize_candidate(candidate)
        if normalized is None:
            return DiscoveryDecision(
                candidate,
                DiscoveryDisposition.REJECTED,
                DiscoveryReason.UNSAFE_PATH,
                (),
            )
        decision, _ = self._inspect_candidate(normalized, read_content=False)
        return decision

    def discover_external(
        self,
        entry: SourceRegistryEntry,
        *,
        content: bytes,
        retrieved_at: datetime | None = None,
        licensing_metadata: Mapping[str, str | int | float | bool | None] | None = None,
        access_metadata: Mapping[str, str | int | float | bool | None] | None = None,
    ) -> SourceRecord:
        """Create metadata for explicitly supplied external bytes; never fetch a URI."""

        if entry.project_id != self.project_id or not entry.is_external or entry.is_exclusion:
            raise ValueError("entry is not an included external registration for this project")
        if len(content) > self.max_file_bytes:
            raise ValueError("external source exceeds the configured byte limit")
        if self.secret_scan and _contains_secret(content):
            raise ValueError("external source contains secret-like content")
        assert entry.path_or_uri is not None
        timestamp = ensure_utc(retrieved_at) if retrieved_at is not None else utc_now()
        digest = hashlib.sha256(content).hexdigest()
        return SourceRecord(
            schema_version=SCHEMA_VERSION,
            api_version=API_VERSION,
            source_id=entry.source_id,
            project_id=entry.project_id,
            path_or_uri=entry.path_or_uri,
            path_pattern=entry.path_pattern,
            source_kind="external",
            format=entry.format,
            canonicality=entry.canonicality,
            content_role=entry.source_role,
            authority_tier=entry.authority_tier,
            trust_class=entry.trust_class,
            sensitivity=entry.sensitivity,
            namespace=entry.namespace,
            scope=ScopeReference(level=MemoryScope.PROJECT, scope_id=entry.project_id),
            profile_id=entry.profile_id,
            ingestion_adapter=entry.ingestion_adapter,
            chunking_profile=entry.chunking_profile,
            schema_ref=entry.schema_ref,
            refresh_mode=entry.refresh_mode,
            retention_policy=entry.retention_policy,
            owner=entry.owner,
            write_policy=entry.write_policy,
            include_flag=True,
            notes=entry.notes,
            content_sha256=digest,
            locator={
                "origin_uri": entry.path_or_uri,
                "registry_rule_id": entry.source_id,
                "registry_content_role": entry.content_role,
                "one_time_registration": entry.one_time,
            },
            git_commit=None,
            git_blob_sha=None,
            working_tree_state=None,
            origin_uri=entry.path_or_uri,
            retrieved_at=timestamp,
            licensing_metadata=dict(licensing_metadata or {}),
            access_metadata=dict(access_metadata or {}),
            generated_from=entry.generated_from,
        )

    def _expand_pattern(self, pattern: str) -> tuple[str, ...]:
        matches: list[str] = []
        for candidate in self.project_root.glob(pattern):
            relative = candidate.relative_to(self.project_root).as_posix()
            matches.append(relative)
            if len(matches) > self.max_candidates:
                raise ValueError("discovery candidate limit exceeded while expanding a rule")
        return tuple(sorted(set(matches)))

    @staticmethod
    def _normalize_candidate(candidate: str) -> str | None:
        if not candidate or "\\" in candidate:
            return None
        path = PurePosixPath(candidate)
        if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
            return None
        return path.as_posix()

    def _matching_rules(
        self, relative_path: str
    ) -> tuple[tuple[SourceRegistryEntry, ...], tuple[SourceRegistryEntry, ...]]:
        includes: list[SourceRegistryEntry] = []
        excludes: list[SourceRegistryEntry] = []
        for entry in self.entries:
            if entry.is_external:
                continue
            target = entry.path_or_uri
            matches = (
                target == relative_path
                if target is not None
                else _matches_pattern(entry.path_pattern or "", relative_path)
            )
            if not matches:
                continue
            if entry.is_exclusion:
                excludes.append(entry)
            else:
                includes.append(entry)
        return tuple(includes), tuple(excludes)

    def _inspect_candidate(
        self, relative_path: str, *, read_content: bool
    ) -> tuple[DiscoveryDecision, SourceRecord | None]:
        includes, excludes = self._matching_rules(relative_path)
        if excludes:
            return (
                DiscoveryDecision(
                    relative_path,
                    DiscoveryDisposition.EXCLUDED,
                    DiscoveryReason.REGISTERED_EXCLUSION,
                    tuple(sorted(entry.source_id for entry in excludes)),
                ),
                None,
            )
        hard_reason = _hard_exclusion(relative_path)
        if hard_reason is not None:
            return (
                DiscoveryDecision(
                    relative_path,
                    DiscoveryDisposition.EXCLUDED,
                    hard_reason,
                    (),
                ),
                None,
            )
        if not includes:
            return (
                DiscoveryDecision(
                    relative_path,
                    DiscoveryDisposition.UNMATCHED,
                    DiscoveryReason.DEFAULT_DENY,
                    (),
                ),
                None,
            )
        if len(includes) != 1:
            return (
                DiscoveryDecision(
                    relative_path,
                    DiscoveryDisposition.REJECTED,
                    DiscoveryReason.AMBIGUOUS,
                    tuple(sorted(entry.source_id for entry in includes)),
                ),
                None,
            )
        entry = includes[0]
        try:
            resolved = resolve_within(self.project_root, relative_path)
        except FileNotFoundError:
            return (
                DiscoveryDecision(
                    relative_path,
                    DiscoveryDisposition.REJECTED,
                    DiscoveryReason.MISSING,
                    (entry.source_id,),
                    source_id=entry.source_id,
                ),
                None,
            )
        except PathBoundaryError as error:
            reason = (
                DiscoveryReason.SYMLINK if "symlink" in str(error) else DiscoveryReason.UNSAFE_PATH
            )
            if "does not exist" in str(error):
                reason = DiscoveryReason.MISSING
            return (
                DiscoveryDecision(
                    relative_path,
                    DiscoveryDisposition.REJECTED,
                    reason,
                    (entry.source_id,),
                    source_id=entry.source_id,
                ),
                None,
            )
        try:
            file_stat = resolved.stat()
        except OSError:
            return (
                DiscoveryDecision(
                    relative_path,
                    DiscoveryDisposition.REJECTED,
                    DiscoveryReason.MISSING,
                    (entry.source_id,),
                    source_id=entry.source_id,
                ),
                None,
            )
        if not stat.S_ISREG(file_stat.st_mode):
            return (
                DiscoveryDecision(
                    relative_path,
                    DiscoveryDisposition.REJECTED,
                    DiscoveryReason.NOT_REGULAR,
                    (entry.source_id,),
                    source_id=entry.source_id,
                ),
                None,
            )
        if self.respect_gitignore and self._git_ignored(relative_path):
            return (
                DiscoveryDecision(
                    relative_path,
                    DiscoveryDisposition.EXCLUDED,
                    DiscoveryReason.GIT_IGNORED,
                    (entry.source_id,),
                    source_id=entry.source_id,
                ),
                None,
            )
        if file_stat.st_size > self.max_file_bytes:
            return (
                DiscoveryDecision(
                    relative_path,
                    DiscoveryDisposition.REJECTED,
                    DiscoveryReason.OVERSIZED,
                    (entry.source_id,),
                    source_id=entry.source_id,
                    detail=f"size exceeds configured limit of {self.max_file_bytes} bytes",
                ),
                None,
            )
        if not _format_matches(entry.format, resolved):
            return (
                DiscoveryDecision(
                    relative_path,
                    DiscoveryDisposition.REJECTED,
                    DiscoveryReason.UNSUPPORTED_FORMAT,
                    (entry.source_id,),
                    source_id=entry.source_id,
                ),
                None,
            )
        if not read_content:
            return (
                DiscoveryDecision(
                    relative_path,
                    DiscoveryDisposition.INCLUDED,
                    DiscoveryReason.REGISTERED_INCLUDE,
                    (entry.source_id,),
                    source_id=self._source_id(entry, relative_path),
                    detail="policy and file metadata passed; content was not read",
                ),
                None,
            )
        try:
            with resolved.open("rb") as stream:
                content = stream.read(self.max_file_bytes + 1)
        except OSError:
            return (
                DiscoveryDecision(
                    relative_path,
                    DiscoveryDisposition.REJECTED,
                    DiscoveryReason.MISSING,
                    (entry.source_id,),
                    source_id=entry.source_id,
                ),
                None,
            )
        if len(content) > self.max_file_bytes:
            return (
                DiscoveryDecision(
                    relative_path,
                    DiscoveryDisposition.REJECTED,
                    DiscoveryReason.OVERSIZED,
                    (entry.source_id,),
                    source_id=entry.source_id,
                ),
                None,
            )
        if self.secret_scan and _contains_secret(content):
            return (
                DiscoveryDecision(
                    relative_path,
                    DiscoveryDisposition.EXCLUDED,
                    DiscoveryReason.SECRET_CONTENT,
                    (entry.source_id,),
                    source_id=entry.source_id,
                    detail="content was rejected without retaining the matching value",
                ),
                None,
            )
        digest = hashlib.sha256(content).hexdigest()
        git_commit, git_blob_sha, working_tree_state = self._git_provenance(relative_path)
        source_id = self._source_id(entry, relative_path)
        record = SourceRecord(
            schema_version=SCHEMA_VERSION,
            api_version=API_VERSION,
            source_id=source_id,
            project_id=entry.project_id,
            path_or_uri=relative_path,
            path_pattern=entry.path_pattern,
            source_kind="repository_file",
            format=entry.format,
            canonicality=entry.canonicality,
            content_role=entry.source_role,
            authority_tier=entry.authority_tier,
            trust_class=entry.trust_class,
            sensitivity=entry.sensitivity,
            namespace=entry.namespace,
            scope=ScopeReference(level=MemoryScope.PROJECT, scope_id=entry.project_id),
            profile_id=entry.profile_id,
            ingestion_adapter=entry.ingestion_adapter,
            chunking_profile=entry.chunking_profile,
            schema_ref=entry.schema_ref,
            refresh_mode=entry.refresh_mode,
            retention_policy=entry.retention_policy,
            owner=entry.owner,
            write_policy=entry.write_policy,
            include_flag=True,
            notes=entry.notes,
            content_sha256=digest,
            locator={
                "path": relative_path,
                "registry_rule_id": entry.source_id,
                "registry_content_role": entry.content_role,
                "registered_source_kind": entry.source_kind,
                "one_time_registration": entry.one_time,
            },
            git_commit=git_commit,
            git_blob_sha=git_blob_sha,
            working_tree_state=working_tree_state,
            origin_uri=None,
            retrieved_at=None,
            licensing_metadata={},
            access_metadata={},
            generated_from=entry.generated_from,
        )
        return (
            DiscoveryDecision(
                relative_path,
                DiscoveryDisposition.INCLUDED,
                DiscoveryReason.REGISTERED_INCLUDE,
                (entry.source_id,),
                source_id=source_id,
            ),
            record,
        )

    @staticmethod
    def _source_id(entry: SourceRegistryEntry, relative_path: str) -> str:
        if entry.path_or_uri is not None:
            return entry.source_id
        identifier = stable_id("source", entry.project_id, entry.source_id, relative_path)
        return f"src_{identifier.replace('-', '')}"

    def _git_ignored(self, relative_path: str) -> bool:
        git = shutil.which("git")
        if git is None:
            return False
        top = _run_git(git, self.project_root, "rev-parse", "--show-toplevel")
        if top is None or Path(top).resolve(strict=True) != self.project_root:
            # A registered project does not inherit ignore policy from an
            # unrelated ancestor repository.
            return False
        result = subprocess.run(  # noqa: S603 - fixed executable and non-shell argv
            [
                git,
                "-C",
                str(self.project_root),
                "check-ignore",
                "--no-index",
                "-q",
                "--",
                relative_path,
            ],
            check=False,
            capture_output=True,
            timeout=5,
            env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
        )
        return result.returncode == 0

    def _git_provenance(self, relative_path: str) -> tuple[str | None, str | None, str]:
        git = shutil.which("git")
        if git is None:
            return None, None, "git-unavailable"
        top = _run_git(git, self.project_root, "rev-parse", "--show-toplevel")
        if top is None or Path(top).resolve(strict=True) != self.project_root:
            return None, None, "not-a-git-worktree"
        git_root = Path(top)
        absolute = self.project_root / PurePosixPath(relative_path)
        try:
            git_relative = absolute.relative_to(git_root).as_posix()
        except ValueError:
            return None, None, "outside-detected-git-root"
        commit = _run_git(git, self.project_root, "rev-parse", "HEAD")
        status_line = _run_git(
            git,
            self.project_root,
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
            "--",
            git_relative,
            empty_is_value=True,
        )
        if status_line is None:
            state = "git-status-unavailable"
        elif not status_line:
            state = "clean"
        elif status_line.startswith("??"):
            state = "untracked"
        else:
            state = f"working-tree:{status_line[:2]}"
        index_line = _run_git(
            git, self.project_root, "ls-files", "-s", "--", git_relative, empty_is_value=True
        )
        blob = None
        if index_line:
            fields = index_line.split()
            if len(fields) >= 2 and re.fullmatch(r"[0-9a-f]{40,64}", fields[1]):
                blob = fields[1]
        return commit, blob, state


def _run_git(
    executable: str,
    cwd: Path,
    *arguments: str,
    empty_is_value: bool = False,
) -> str | None:
    result = subprocess.run(  # noqa: S603 - fixed executable and non-shell argv
        [executable, "-C", str(cwd), *arguments],
        check=False,
        capture_output=True,
        text=True,
        timeout=5,
        env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
    )
    if result.returncode != 0:
        return None
    value = result.stdout.strip()
    if value or empty_is_value:
        return value
    return None


def _matches_pattern(pattern: str, relative_path: str) -> bool:
    """Match root-relative glob segments, with ** as the only recursive segment.

    Path.match matches relative patterns from the right, and whole-path fnmatch
    lets * cross slashes. Neither matches the root.glob expansion used for
    discovery: tests/** must not also classify SKILLS-depo/task/tests/**.
    """
    parts = PurePosixPath(relative_path).parts
    positions = {0}
    for segment in PurePosixPath(pattern).parts:
        if not positions:
            return False
        if segment == "**":
            positions = set(range(min(positions), len(parts) + 1))
        else:
            positions = {
                index + 1
                for index in positions
                if index < len(parts) and fnmatch.fnmatchcase(parts[index], segment)
            }
    return len(parts) in positions


def _hard_exclusion(relative_path: str) -> DiscoveryReason | None:
    path = PurePosixPath(relative_path)
    parts = path.parts
    lowered = tuple(part.casefold() for part in parts)
    if any(part in {".git", ".venv", "__pycache__", "node_modules", ".cache"} for part in lowered):
        return DiscoveryReason.GENERATED_PATH
    if len(lowered) >= 2 and lowered[0] == ".sys4ai" and lowered[1] == "memory":
        return DiscoveryReason.GENERATED_PATH
    if any(part in {"build", "dist"} for part in lowered[:-1]):
        return DiscoveryReason.GENERATED_PATH
    name = path.name.casefold()
    if name == ".env" or name.startswith(".env."):
        return DiscoveryReason.SECRET_PATH
    if path.suffix.casefold() in {".pem", ".key", ".p12", ".pfx"}:
        return DiscoveryReason.SECRET_PATH
    return None


def _contains_secret(content: bytes) -> bool:
    return any(pattern.search(content) is not None for pattern in _SECRET_CONTENT_PATTERNS)


def _format_matches(format_name: str, path: Path) -> bool:
    suffixes = _FORMAT_SUFFIXES.get(format_name)
    if suffixes is not None:
        return path.suffix.casefold() in suffixes
    return path.suffix.casefold() == f".{format_name.casefold()}"


def discover_sources(
    *,
    project_root: Path,
    project_id: str,
    entries: Iterable[SourceRegistryEntry],
    candidate_paths: Iterable[str] = (),
    max_file_bytes: int = 8 * 1024 * 1024,
) -> DiscoveryReport:
    """Functional entry point for a one-shot safe discovery dry run."""

    return SourceDiscovery(
        project_root=project_root,
        project_id=project_id,
        entries=entries,
        max_file_bytes=max_file_bytes,
    ).discover(candidate_paths=candidate_paths)
