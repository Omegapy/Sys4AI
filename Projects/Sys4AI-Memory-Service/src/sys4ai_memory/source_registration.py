"""Reviewed project-owned source registration through the existing control plane."""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Literal, Self
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

from sys4ai_memory.authorization import (
    AuthorizationRequest,
    AuthorizationService,
    CanonicalPermissionEnvelopeLoader,
    PermissionDeniedError,
)
from sys4ai_memory.configuration import LoadedConfiguration, load_configuration
from sys4ai_memory.contracts import AuthorityTier, MemoryScope, Permission, ScopeReference
from sys4ai_memory.contracts.enums import Sensitivity, TrustClass
from sys4ai_memory.initialization import InitializationError, validate_initialization_paths
from sys4ai_memory.observability import (
    AdministrativeActionExecutor,
    AdministrativeOperation,
    AuditRecorder,
    VersionContext,
)
from sys4ai_memory.profiles import load_profile
from sys4ai_memory.security import JsonlAuditSink, MemorySecurityError, ProjectBoundary
from sys4ai_memory.security.locks import exclusive_file_lock
from sys4ai_memory.security.secrets import require_secret_free
from sys4ai_memory.sources import RegistryBundle, SourceDiscovery, SourceRegistryEntry
from sys4ai_memory.sources.discovery import DiscoveryDisposition
from sys4ai_memory.sources.registry import SOURCE_HEADER, load_registry_bundle
from sys4ai_memory.util import (
    atomic_write_bytes,
    canonical_json_bytes,
    resolve_within,
    sha256_bytes,
)

_FORBIDDEN_PARTS = frozenset(
    {
        "projects",
        ".git",
        ".sys4ai",
        ".venv",
        "venv",
        "env",
        "node_modules",
        "__pycache__",
        ".cache",
        ".ruff_cache",
        ".mypy_cache",
        ".pytest_cache",
        ".uv-cache",
        "models",
        ".cognee",
        ".cognee_system",
        ".data_storage",
        "build",
        "dist",
        ".secrets",
        "secrets",
        "tmp",
        "temp",
        ".tmp",
        "staging",
        "downloads",
        "exports",
        "logs",
        "raw-logs",
        ".locks",
    }
)
_SOURCE_ID = re.compile(r"^src_[A-Za-z0-9][A-Za-z0-9_.:@-]*$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class SourceRegistrationError(ValueError):
    """The reviewed registration is ineligible, conflicting, or stale."""


class ReviewedSourceRegistration(BaseModel):
    """Required review metadata; this document never grants its own authority."""

    model_config = ConfigDict(extra="forbid", frozen=True, validate_default=True)

    project_id: str = Field(min_length=1, max_length=255)
    dataset_id: str = Field(min_length=1, max_length=255)
    source_id: str = Field(min_length=5, max_length=255)
    path: str = Field(min_length=1, max_length=1024)
    file_pattern: str | None = None
    recursive: bool = False
    format: str = Field(min_length=1)
    ingestion_adapter: str = Field(min_length=1)
    namespace: str = Field(min_length=1, max_length=255)
    canonicality: Literal["canonical", "evidential", "episodic", "scratch"]
    content_role: str = Field(min_length=1, max_length=255)
    authority_tier: AuthorityTier
    trust_class: TrustClass
    sensitivity: Sensitivity
    retention_policy: str = Field(min_length=1, max_length=255)
    write_policy: str = Field(min_length=1, max_length=255)
    owner: str = Field(min_length=1, max_length=255)
    relevance: str = Field(min_length=1, max_length=2000)
    profile_id: Literal["base@1"] = "base@1"
    chunking_profile: str = Field(min_length=1, max_length=255)
    refresh_mode: Literal["git-revision", "content-hash"] = "content-hash"

    @model_validator(mode="after")
    def validate_review_metadata(self) -> Self:
        payload = self.model_dump(mode="json")
        if any(
            isinstance(value, str)
            and (
                not value.strip() or value != value.strip() or any(ord(char) < 32 for char in value)
            )
            for value in payload.values()
        ):
            raise ValueError("review metadata must contain nonblank single-line values")
        require_secret_free(payload, field_path="reviewed_source")
        if not _SOURCE_ID.fullmatch(self.source_id):
            raise ValueError("source_id must use the stable src_ prefix")
        _relative_path(self.path)
        if self.file_pattern is not None and (
            not self.file_pattern
            or "/" in self.file_pattern
            or "\\" in self.file_pattern
            or "**" in self.file_pattern
            or self.file_pattern in {".", ".."}
        ):
            raise ValueError("file_pattern must match one filename segment")
        if self.authority_tier in {AuthorityTier.SYSTEM_POLICY, AuthorityTier.SYS4AI_GOVERNANCE}:
            raise ValueError(
                "project registration cannot assign system or depot-governance authority"
            )
        if self.trust_class is TrustClass.SYSTEM_CONTROLLED:
            raise ValueError("project registration cannot assert system-controlled trust")
        return self


@dataclass(frozen=True, slots=True)
class SourceRegistrationReceipt:
    project_id: str
    dataset_id: str
    source_id: str
    changed: bool
    registry_path: str
    registry_sha256_before: str
    registry_sha256_after: str
    reviewed_metadata_sha256: str
    review_reference: str
    review_sha256: str
    admitted_paths: tuple[str, ...]
    audit_outcome: Literal["succeeded"]
    trace_id: str

    def as_dict(self) -> dict[str, Any]:
        from dataclasses import asdict

        return {"status": "registered" if self.changed else "unchanged", **asdict(self)}


def _relative_path(value: str) -> PurePosixPath:
    path = PurePosixPath(value)
    if (
        path.is_absolute()
        or any(ord(char) < 32 for char in value)
        or re.match(r"^[A-Za-z]:", value)
        or "\\" in value
        or any(part in {"", ".", ".."} for part in value.split("/"))
        or any(marker in value for marker in "*?[")
    ):
        raise SourceRegistrationError(
            "registration paths must be normalized project-relative paths"
        )
    return path


def _load_initialized(root: Path) -> LoadedConfiguration:
    if (
        not root.is_absolute()
        or ".." in root.parts
        or not root.is_dir()
        or any(path.is_symlink() for path in (root, *root.parents))
    ):
        raise SourceRegistrationError("project_root must be absolute and must not cross a symlink")
    loaded = load_configuration(root / "config/memory.toml", trusted_project_root=root)
    validate_initialization_paths(loaded)
    data = loaded.resolved_paths["local_data"]
    receipt_path = resolve_within(
        root, (data / "receipts/initialization.json").relative_to(root), must_exist=False
    )
    if not receipt_path.is_file() or not loaded.resolved_paths["exact_index"].is_file():
        raise SourceRegistrationError("source registration requires initialized local exact memory")
    if receipt_path.stat().st_nlink != 1:
        raise SourceRegistrationError("initialization receipt must be one regular file")
    receipt = json.loads(receipt_path.read_bytes())
    memory = loaded.configuration.memory
    if (
        receipt.get("project_id") != memory.project_id
        or receipt.get("dataset_id") != memory.provider.cognee.dataset
        or receipt.get("configuration_fingerprint") != loaded.fingerprint
        or receipt.get("exact_index_initialized") is not True
    ):
        raise SourceRegistrationError("initialization receipt does not match current configuration")
    if (
        memory.sources.default_include
        or not memory.sources.require_registered_rule
        or not memory.sources.respect_gitignore
        or not memory.security.secret_scan
    ):
        raise SourceRegistrationError("registration requires default-deny source and scan policy")
    if memory.observability.content_logging != "metadata_only":
        raise SourceRegistrationError("registration requires persistent metadata-only audit")
    if memory.read_only or not memory.permissions.mutation_enabled:
        raise SourceRegistrationError("canonical configuration disables mutation")
    return loaded


def _registry(loaded: LoadedConfiguration) -> RegistryBundle:
    return load_registry_bundle(
        project_root=loaded.project_root,
        source_registry=loaded.resolved_paths["source_registry"],
        profile_registry=loaded.resolved_paths["profile_registry"],
        relation_registry=loaded.resolved_paths["relation_registry"],
    )


def _owned_path(root: Path, relative: str) -> Path:
    parts = _relative_path(relative).parts
    if any(part.casefold() in _FORBIDDEN_PARTS for part in parts):
        raise SourceRegistrationError("registration targets a protected project or generated path")
    name = parts[-1].casefold()
    if (
        name == "credentials.json"
        or name.startswith((".env", "id_rsa", "id_ed25519", "service-account", "service_account"))
        or PurePosixPath(name).suffix
        in {
            ".pem",
            ".key",
            ".p12",
            ".pfx",
            ".log",
            ".sqlite",
            ".sqlite3",
            ".db",
            ".cogx",
            ".tmp",
            ".temp",
        }
    ):
        raise SourceRegistrationError("registration targets secret or generated source material")
    target = resolve_within(root, relative)
    for ancestor in (target if target.is_dir() else target.parent, *target.parents):
        if ancestor == root:
            break
        if (ancestor / ".git").exists() or (ancestor / ".git").is_symlink():
            raise SourceRegistrationError("registration crosses an independently owned Git project")
    if target.is_dir():
        visited = 0
        for current, directories, filenames in os.walk(target, followlinks=False):
            visited += len(directories) + len(filenames)
            if visited > 10_000:
                raise SourceRegistrationError(
                    "registration folder exceeds the review candidate limit"
                )
            if ".git" in directories or ".git" in filenames:
                raise SourceRegistrationError(
                    "registration contains an independently owned Git project"
                )
            if any((Path(current) / name).is_symlink() for name in (*directories, *filenames)):
                raise SourceRegistrationError("registration folder contains a symlink")
            directories[:] = [
                name for name in directories if name.casefold() not in _FORBIDDEN_PARTS
            ]
    elif not target.is_file() or target.stat().st_nlink != 1:
        raise SourceRegistrationError("source must be one regular file or a project-owned folder")
    return target


def _entry(
    root: Path, source: ReviewedSourceRegistration, review_reference: str
) -> SourceRegistryEntry:
    target = _owned_path(root, source.path)
    if target.is_dir() and source.file_pattern is None:
        raise SourceRegistrationError("folder registration requires an explicit file_pattern")
    if target.is_file() and (source.file_pattern is not None or source.recursive):
        raise SourceRegistrationError(
            "exact-file registration cannot specify a pattern or recursion"
        )
    pattern = (
        None
        if target.is_file()
        else (f"{source.path}/{'**/' if source.recursive else ''}{source.file_pattern}")
    )
    return SourceRegistryEntry(
        source_id=source.source_id,
        project_id=source.project_id,
        path_or_uri=source.path if target.is_file() else None,
        path_pattern=pattern,
        source_kind="file" if target.is_file() else "path_rule",
        format=source.format,
        canonicality=source.canonicality,
        content_role=source.content_role,
        authority_tier=source.authority_tier,
        trust_class=source.trust_class,
        sensitivity=source.sensitivity,
        namespace=source.namespace,
        profile_id=source.profile_id,
        ingestion_adapter=source.ingestion_adapter,
        chunking_profile=source.chunking_profile,
        schema_ref="schemas/memory/source-record.schema.json",
        refresh_mode=source.refresh_mode,
        retention_policy=source.retention_policy,
        owner=source.owner,
        write_policy=source.write_policy,
        include_flag=True,
        notes=f"Relevance: {source.relevance}; reviewed: {review_reference}",
    )


def _row(entry: SourceRegistryEntry) -> dict[str, str]:
    return {
        name: ""
        if (value := getattr(entry, name)) is None
        else "true"
        if value is True
        else "false"
        if value is False
        else str(value)
        for name in SOURCE_HEADER
    }


def _admission(
    root: Path,
    bundle: RegistryBundle,
    entry: SourceRegistryEntry,
    *,
    repeated: bool,
) -> tuple[str, ...]:
    base = load_profile(root / "profiles/base/profile.yaml", trusted_project_root=root).profile
    declared = next(
        (adapter for adapter in base.source_adapters if adapter.id == entry.ingestion_adapter), None
    )
    if declared is None or entry.format not in declared.formats:
        raise SourceRegistrationError("format and adapter must be supported by the base profile")
    if not repeated:
        bundle.with_one_time_sources((entry,))
    for reference in (entry.schema_ref,):
        assert reference is not None
        if not resolve_within(root, reference).is_file():
            raise SourceRegistrationError("source schema reference must be a regular project file")
    # Reuse the exact discovery matcher and current exclusion precedence. Only
    # the requested rule is expanded; unrelated registered folders are not read.
    checked = SourceDiscovery(
        project_root=root,
        project_id=entry.project_id,
        entries=(*tuple(item for item in bundle.sources if item.is_exclusion), entry),
    ).discover()
    if any(item.disposition is DiscoveryDisposition.REJECTED for item in checked.decisions):
        raise SourceRegistrationError(
            "candidate discovery rejected an unsafe or unsupported source"
        )
    admitted = tuple(item.path_or_uri for item in checked.included)
    if not admitted:
        raise SourceRegistrationError(
            "reviewed rule admits no eligible source under current exclusions"
        )
    all_entries = bundle.sources if repeated else (*bundle.sources, entry)
    combined = SourceDiscovery(project_root=root, project_id=entry.project_id, entries=all_entries)
    for relative in admitted:
        _owned_path(root, relative)
        decision = combined.explain_path(relative)
        if decision.disposition is not DiscoveryDisposition.INCLUDED:
            raise SourceRegistrationError("registration conflicts with existing source policy")
    return tuple(sorted(admitted))


def register_reviewed_source(
    project_root: Path,
    principal_id: str,
    reviewed_source: ReviewedSourceRegistration | dict[str, Any],
    *,
    review_reference: str,
    expected_registry_sha256: str,
) -> SourceRegistrationReceipt:
    """Append one reviewed source rule, retaining all existing canonical rows.

    Local exact memory must already be initialized. An action-specific canonical
    grant is reread through AdministrativeActionExecutor; no public memory API,
    provider initialization, model operation or exclusion rewrite is involved.
    """
    source = ReviewedSourceRegistration.model_validate(reviewed_source)
    if not _SHA256.fullmatch(expected_registry_sha256):
        raise SourceRegistrationError("expected_registry_sha256 must be a current SHA-256")
    require_secret_free((principal_id, review_reference), field_path="registration_context")
    review_relative = _relative_path(review_reference).as_posix()
    root = Path(project_root)
    loaded = _load_initialized(root)
    data_root = loaded.resolved_paths["local_data"]
    lock_path = resolve_within(root, (data_root / ".runtime.lock").relative_to(root))
    with exclusive_file_lock(lock_path):
        # Cooperating runtime operations share this lock. Reread all canonical
        # inputs after acquiring it, including configuration and permissions.
        loaded = _load_initialized(root)
        memory = loaded.configuration.memory
        if (
            source.project_id != memory.project_id
            or source.dataset_id != memory.provider.cognee.dataset
        ):
            raise SourceRegistrationError(
                "reviewed source belongs to a different project or dataset"
            )
        registry_path = loaded.resolved_paths["source_registry"]
        relative_registry = registry_path.relative_to(root).as_posix()
        if registry_path.stat().st_nlink != 1:
            raise SourceRegistrationError("source registry must be one regular file")
        before = registry_path.read_bytes()
        if tuple(next(csv.reader(io.StringIO(before.decode()), strict=True), ())) != SOURCE_HEADER:
            raise SourceRegistrationError("registration requires the full canonical CSV header")
        before_hash = sha256_bytes(before)
        if before_hash != expected_registry_sha256:
            raise SourceRegistrationError("source registry changed since review")
        review_path = resolve_within(root, review_relative)
        if not review_path.is_file() or review_path.stat().st_nlink != 1:
            raise SourceRegistrationError("review reference must be one regular project file")
        review_hash = sha256_bytes(review_path.read_bytes())
        bundle = _registry(loaded)
        if any(item.project_id != memory.project_id for item in bundle.sources):
            raise SourceRegistrationError("canonical registry contains a foreign project identity")
        metadata_hash = sha256_bytes(canonical_json_bytes(source.model_dump(mode="json")))
        boundary = ProjectBoundary(memory.project_id, memory.provider.cognee.dataset, root)
        permission_path = (Path(memory.control_records.root) / "permissions.json").as_posix()
        authorization = AuthorizationService(
            CanonicalPermissionEnvelopeLoader(boundary, permission_path)
        )
        audit = AuditRecorder(
            JsonlAuditSink(
                boundary,
                memory.observability.local_audit_log,
                retention_policy_id=memory.retention.policy_status,
            )
        )
        versions = VersionContext(
            configuration_version=loaded.configuration.config_version,
            configuration_fingerprint=loaded.fingerprint,
            profile_versions={},
            profile_fingerprints={},
            provider_name=memory.provider.name,
            provider_version=memory.provider.version_constraint.removeprefix("=="),
            provider_fingerprint=sha256_bytes(
                canonical_json_bytes(memory.provider.model_dump(mode="json"))
            ),
            source_registry_fingerprint=before_hash,
        )
        executor = AdministrativeActionExecutor(
            authorization=authorization,
            audit=audit,
            project_id=memory.project_id,
            dataset_id=memory.provider.cognee.dataset,
            versions=versions,
            policy_decision_ref=permission_path,
        )
        scope = ScopeReference(level=MemoryScope.PROJECT, scope_id=memory.project_id)
        trace_id = "trace_registration_" + uuid4().hex

        def publish() -> SourceRegistrationReceipt:
            entry = _entry(root, source, review_reference)
            existing = next(
                (item for item in bundle.sources if item.source_id == entry.source_id), None
            )
            if existing is not None and _row(existing) != _row(entry):
                raise SourceRegistrationError("source_id conflicts with an existing canonical row")
            admitted = _admission(root, bundle, entry, repeated=existing is not None)
            stream = io.StringIO(newline="")
            writer = csv.DictWriter(stream, fieldnames=SOURCE_HEADER, lineterminator="\n")
            writer.writerow(_row(entry))
            after = (
                before
                if existing is not None
                else (
                    before + (b"" if before.endswith(b"\n") else b"\n") + stream.getvalue().encode()
                )
            )
            after_hash = sha256_bytes(after)
            # Detect revocation or an external canonical edit after discovery and
            # after the executor's authorized audit event, before replacement.
            authorization.require(
                AuthorizationRequest(
                    principal_id=principal_id,
                    project_id=memory.project_id,
                    dataset_id=memory.provider.cognee.dataset,
                    operation=AdministrativeOperation.SOURCE_REGISTER.value,
                    permission=Permission.ADMINISTER,
                    scope=scope,
                    target_path=relative_registry,
                    trace_id=trace_id,
                    require_action_specific=True,
                )
            )
            current = load_configuration(loaded.configuration_path, trusted_project_root=root)
            if (
                current.fingerprint != loaded.fingerprint
                or resolve_within(root, relative_registry).read_bytes() != before
                or sha256_bytes(resolve_within(root, review_relative).read_bytes()) != review_hash
            ):
                raise SourceRegistrationError(
                    "canonical inputs changed before registration publication"
                )
            _owned_path(root, source.path)
            if existing is None:
                atomic_write_bytes(registry_path, after, mode=registry_path.stat().st_mode & 0o777)

            return SourceRegistrationReceipt(
                project_id=memory.project_id,
                dataset_id=memory.provider.cognee.dataset,
                source_id=source.source_id,
                changed=existing is None,
                registry_path=relative_registry,
                registry_sha256_before=before_hash,
                registry_sha256_after=after_hash,
                reviewed_metadata_sha256=metadata_hash,
                review_reference=review_reference,
                review_sha256=review_hash,
                admitted_paths=admitted,
                audit_outcome="succeeded",
                trace_id=trace_id,
            )

        return executor.execute(
            AdministrativeOperation.SOURCE_REGISTER,
            principal_id=principal_id,
            scope=scope,
            trace_id=trace_id,
            target_path=relative_registry,
            target_ids=(
                source.source_id,
                "metadata_" + metadata_hash,
                "review_" + review_hash,
                "before_" + before_hash,
            ),
            action=publish,
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--principal-id", required=True)
    parser.add_argument("--reviewed-source-json", type=Path, required=True)
    parser.add_argument("--review-reference", required=True)
    parser.add_argument("--expected-registry-sha256", required=True)
    args = parser.parse_args(argv)
    try:
        result = register_reviewed_source(
            args.project_root,
            args.principal_id,
            json.loads(args.reviewed_source_json.read_bytes()),
            review_reference=args.review_reference,
            expected_registry_sha256=args.expected_registry_sha256,
        )
    except (
        OSError,
        ValueError,
        MemorySecurityError,
        InitializationError,
        PermissionDeniedError,
    ) as error:
        print(
            json.dumps(
                {
                    "status": "failed",
                    "error_type": type(error).__name__,
                    "reason": str(error)
                    if isinstance(error, SourceRegistrationError)
                    else "Input, canonical state, authorization, or audit validation failed",
                }
            )
        )
        return 2
    print(json.dumps(result.as_dict(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
