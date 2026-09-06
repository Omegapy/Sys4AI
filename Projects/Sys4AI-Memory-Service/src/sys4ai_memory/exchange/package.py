"""Deterministic package creation, hostile-input validation, and staged import."""

from __future__ import annotations

import io
import json
import os
import stat
import zipfile
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from pydantic import ValidationError

from sys4ai_memory.contracts import MemoryRecord, RelationRecord, Sensitivity, SourceRecord
from sys4ai_memory.providers import (
    ImportRequest,
    ImportResult,
    MemoryProvider,
    PolicyEnvelope,
    ProviderContext,
    ProviderExportFormat,
    ProviderMutation,
    ProviderName,
    ProviderSnapshot,
)
from sys4ai_memory.security import SecretDetectedError, require_secret_free
from sys4ai_memory.security.isolation import ProjectBoundary
from sys4ai_memory.util import atomic_write_bytes, canonical_json_bytes, sha256_bytes, stable_id
from sys4ai_memory.util.time import utc_now

from .age import AgeTool, AgeToolError
from .models import (
    AuthorizedExchangeImpact,
    BackupAsset,
    BackupAssetClass,
    ExportPolicy,
    ImportActivationReceipt,
    ImportPolicy,
    ImportPreview,
    MemoryPackageManifest,
    OriginProvenance,
    PackageCandidate,
    PackageContainer,
    PackageFile,
    StagedImport,
)

_MANIFEST = "manifest.json"
_SOURCES = "sources.jsonl"
_RECORDS = "records.jsonl"
_RELATIONS = "relations.jsonl"
_PROVENANCE = "provenance.jsonl"
_PROFILES = "profiles.json"
_STATUS = "status.json"
_BACKUP = "backup-assets.json"
_DATA_MEMBERS = (_BACKUP, _PROFILES, _PROVENANCE, _RECORDS, _RELATIONS, _SOURCES, _STATUS)
_ALL_MEMBERS = frozenset((*_DATA_MEMBERS, _MANIFEST))


class ExchangeError(RuntimeError):
    """Base for policy, package, and import failures."""


class ExchangePolicyError(ExchangeError):
    """Current canonical policy does not authorize this package operation."""


class PackageValidationError(ExchangeError):
    """Package bytes or metadata failed closed validation."""


class ImportConflictError(ExchangeError):
    """An import would cross scope or contradict canonical source state."""


@dataclass(frozen=True, slots=True)
class ValidatedPackage:
    package_path: Path
    container: PackageContainer
    manifest: MemoryPackageManifest
    manifest_sha256: str
    snapshot: ProviderSnapshot
    provenance: tuple[OriginProvenance, ...]
    members: Mapping[str, bytes]
    canonical_references_reused: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ProviderImportStage:
    provider: MemoryProvider
    active_provider: MemoryProvider
    context: ProviderContext
    preview_authorization: PolicyEnvelope
    isolated_generation: bool = True

    def __post_init__(self) -> None:
        if not self.isolated_generation or self.provider is self.active_provider:
            raise ValueError("provider import stage must be distinct from the active provider")


def _require_provider_import_result(
    result: ImportResult,
    *,
    provider: MemoryProvider,
    request_id: str,
    context: ProviderContext,
    snapshot: ProviderSnapshot,
    executed: bool,
    expected_impact_digest: str | None = None,
) -> None:
    """Reject a provider response that does not describe the requested import."""

    expected_record_ids = {record.record_id for record in snapshot.records}
    expected_relation_ids = {relation.relation_id for relation in snapshot.relations}
    actual_record_ids = set(result.imported_record_ids)
    actual_relation_ids = set(result.imported_relation_ids)
    identity_matches = (
        result.provider_name is provider.provider_name
        and result.provider_version == provider.provider_version
        and result.request_id == request_id
        and result.project_id == context.project_id
        and result.dataset_id == context.dataset_id
        and result.format is ProviderExportFormat.SYS4AI
        and result.executed is executed
        and result.trace_id == context.trace_id
    )
    ids_match = (
        len(result.imported_record_ids) == len(actual_record_ids)
        and len(result.imported_relation_ids) == len(actual_relation_ids)
        and actual_record_ids == expected_record_ids
        and actual_relation_ids == expected_relation_ids
    )
    impact_matches = (
        expected_impact_digest is None or result.impact_digest == expected_impact_digest
    )
    if not identity_matches or not ids_match or not impact_matches:
        raise ImportConflictError("provider import result does not match the requested snapshot")


def _reject_duplicate_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise PackageValidationError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def _strict_json(content: bytes) -> object:
    try:
        return json.loads(content, object_pairs_hook=_reject_duplicate_pairs)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise PackageValidationError("package JSON is invalid") from error


def _json_lines(values: tuple[Mapping[str, Any], ...]) -> bytes:
    return b"".join(canonical_json_bytes(value) for value in values)


def _line_count(value: bytes) -> int:
    return len(tuple(line for line in value.splitlines() if line.strip()))


def _package_digest(manifest: MemoryPackageManifest | Mapping[str, Any]) -> str:
    if isinstance(manifest, MemoryPackageManifest):
        payload = manifest.model_dump(mode="json")
    else:
        payload = dict(manifest)
    payload.pop("package_sha256", None)
    return sha256_bytes(canonical_json_bytes(payload))


def _backup_assets() -> tuple[BackupAsset, ...]:
    return (
        BackupAsset(
            path_class="registered canonical project sources",
            asset_class=BackupAssetClass.CANONICAL,
            package_included=False,
            sensitive=False,
            recovery_role="authoritative inputs must be backed up through repository controls",
        ),
        BackupAsset(
            path_class="provider-neutral records, relations, and source metadata",
            asset_class=BackupAssetClass.DERIVED,
            package_included=True,
            sensitive=False,
            recovery_role="portable derived generation that never replaces canonical sources",
        ),
        BackupAsset(
            path_class="provider-native databases and COGX artifacts",
            asset_class=BackupAssetClass.OPTIONAL,
            package_included=False,
            sensitive=False,
            recovery_role="optional acceleration data; canonical rebuild remains authoritative",
        ),
        BackupAsset(
            path_class="credentials, secret fixtures, restricted caches, and model weights",
            asset_class=BackupAssetClass.SENSITIVE,
            package_included=False,
            sensitive=True,
            recovery_role="excluded; manage under separate approved secret and backup controls",
        ),
    )


class MemoryPackageExporter:
    """Create a provider-neutral package inside an explicit confined export root."""

    def __init__(self, *, disposable_root: Path, age_tool: AgeTool | None = None) -> None:
        if (
            not disposable_root.is_absolute()
            or not disposable_root.is_dir()
            or disposable_root.is_symlink()
        ):
            raise ValueError("disposable export root must be an absolute non-symlink directory")
        self.disposable_root = disposable_root.resolve(strict=True)
        self.age_tool = age_tool

    def _destination(self, destination: Path) -> Path:
        resolved = destination.resolve(strict=False)
        try:
            resolved.relative_to(self.disposable_root)
        except ValueError as error:
            raise ExchangePolicyError(
                "package destination must remain inside the configured export root"
            ) from error
        if resolved == self.disposable_root or resolved.exists():
            raise ExchangePolicyError("package destination must be a new child path")
        cursor = self.disposable_root
        for part in resolved.relative_to(self.disposable_root).parts[:-1]:
            cursor /= part
            if cursor.is_symlink():
                raise ExchangePolicyError("package destination crosses a symlink")
        return resolved

    @staticmethod
    def _require_policy(policy: ExportPolicy, *, disposable_test_only: bool) -> bool:
        production_ready = not policy.format_decision_status.startswith("pending-") and (
            not policy.encryption_required or policy.approved_encryption is not None
        )
        if production_ready:
            if disposable_test_only:
                raise ExchangePolicyError(
                    "approved encrypted export cannot be disposable-test-only"
                )
            return True
        if not (disposable_test_only and policy.allow_unencrypted_disposable_test_only):
            raise ExchangePolicyError(
                "export is denied until archive/encryption policy is approved; "
                "only an explicit disposable-test-only candidate is available"
            )
        return False

    def export_snapshot(
        self,
        snapshot: ProviderSnapshot,
        *,
        destination: Path,
        container: PackageContainer,
        policy: ExportPolicy,
        disposable_test_only: bool = False,
        age_recipient: str | None = None,
    ) -> PackageCandidate:
        production_ready = self._require_policy(
            policy, disposable_test_only=disposable_test_only
        )
        if production_ready and container is not PackageContainer.ZIP:
            raise ExchangePolicyError("approved memory packages require a ZIP container")
        if production_ready and (self.age_tool is None or age_recipient is None):
            raise ExchangePolicyError("approved memory packages require an age recipient")
        target = self._destination(destination)
        allowed = policy.allowed_sensitivities
        source_by_id = {source.source_id: source for source in snapshot.sources}
        included_sources = {
            source_id: source
            for source_id, source in source_by_id.items()
            if source.sensitivity in allowed
        }
        records = tuple(
            sorted(
                (
                    record
                    for record in snapshot.records
                    if record.security.sensitivity in allowed
                    and record.source.source_id in included_sources
                ),
                key=lambda item: item.record_id,
            )
        )
        record_ids = {record.record_id for record in records}
        relations = tuple(
            sorted(
                (
                    relation
                    for relation in snapshot.relations
                    if relation.source_record_id in record_ids
                    and relation.target_record_id in record_ids
                ),
                key=lambda item: item.relation_id,
            )
        )
        referenced_sources = {record.source.source_id for record in records}
        sources = tuple(included_sources[source_id] for source_id in sorted(referenced_sources))
        selected_source_by_id = {source.source_id: source for source in sources}
        if any(
            record.source.content_sha256
            != selected_source_by_id[record.source.source_id].content_sha256
            or (
                record.source.path is not None
                and record.source.path != selected_source_by_id[record.source.source_id].path_or_uri
            )
            or (
                record.source.origin_uri is not None
                and record.source.origin_uri
                not in {
                    selected_source_by_id[record.source.source_id].origin_uri,
                    selected_source_by_id[record.source.source_id].path_or_uri,
                }
            )
            for record in records
        ):
            raise ExchangePolicyError("record source anchors conflict with package source metadata")
        excluded_record_ids = tuple(
            sorted(
                record.record_id
                for record in snapshot.records
                if record.record_id not in record_ids
            )
        )
        included_source_ids = {source.source_id for source in sources}
        excluded_source_ids = tuple(
            sorted(
                source.source_id
                for source in snapshot.sources
                if source.source_id not in included_source_ids
            )
        )
        excluded_counts = {
            sensitivity: sum(
                1
                for record in snapshot.records
                if record.security.sensitivity is sensitivity and record.record_id not in record_ids
            )
            for sensitivity in Sensitivity
        }
        filtered = ProviderSnapshot.build(
            project_id=snapshot.project_id,
            dataset_id=snapshot.dataset_id,
            created_at=snapshot.created_at,
            origin_provider=snapshot.origin_provider,
            origin_provider_version=snapshot.origin_provider_version,
            profile_versions=dict(snapshot.profile_versions),
            sources=sources,
            records=records,
            relations=relations,
        )
        try:
            require_secret_free(
                {
                    "sources": [source.to_json_dict() for source in sources],
                    "records": [record.to_json_dict() for record in records],
                    "relations": [relation.to_json_dict() for relation in relations],
                },
                field_path="memory_package",
            )
        except SecretDetectedError as error:
            raise ExchangePolicyError(
                "secret-like content cannot enter a memory package"
            ) from error
        provenance = tuple(
            OriginProvenance(
                record_id=record.record_id,
                source_id=record.source.source_id,
                origin_project_id=snapshot.project_id,
                origin_provider=snapshot.origin_provider.value,
                origin_provider_version=snapshot.origin_provider_version,
                origin_content_sha256=record.source.content_sha256,
            )
            for record in records
        )
        assets = _backup_assets()
        members: dict[str, bytes] = {
            _SOURCES: _json_lines(tuple(source.to_json_dict() for source in sources)),
            _RECORDS: _json_lines(tuple(record.to_json_dict() for record in records)),
            _RELATIONS: _json_lines(tuple(relation.to_json_dict() for relation in relations)),
            _PROVENANCE: _json_lines(tuple(item.model_dump(mode="json") for item in provenance)),
            _PROFILES: canonical_json_bytes(
                {
                    "schema_version": "1.0",
                    "profiles": dict(sorted(filtered.profile_versions.items())),
                }
            ),
            _STATUS: canonical_json_bytes(
                {
                    "schema_version": "1.0",
                    "records": [
                        {
                            "record_id": record.record_id,
                            "status": record.lifecycle.status.value,
                            "version": record.version,
                        }
                        for record in records
                    ],
                }
            ),
            _BACKUP: canonical_json_bytes(
                {
                    "schema_version": "1.0",
                    "assets": [item.model_dump(mode="json") for item in assets],
                }
            ),
        }
        files = tuple(
            PackageFile(
                path=name,
                media_type=(
                    "application/x-ndjson" if name.endswith(".jsonl") else "application/json"
                ),
                sha256=sha256_bytes(value),
                byte_size=len(value),
                item_count=(_line_count(value) if name.endswith(".jsonl") else 1),
            )
            for name, value in sorted(members.items())
        )
        package_identity = stable_id(
            "sys4ai-memory-package",
            filtered.checksums.package_sha256,
            "\x1f".join(sorted(item.value for item in allowed)),
        ).replace("-", "")
        base_manifest: dict[str, Any] = {
            "schema_version": "1.0",
            "package_format": "sys4ai-memory-package",
            "package_version": "1.0.0",
            "package_id": f"smp_{package_identity}",
            "project_id": filtered.project_id,
            "dataset_id": filtered.dataset_id,
            "created_at": filtered.created_at.isoformat().replace("+00:00", "Z"),
            "origin_provider": filtered.origin_provider.value,
            "origin_provider_version": filtered.origin_provider_version,
            "profile_versions": dict(sorted(filtered.profile_versions.items())),
            "files": [item.model_dump(mode="json") for item in files],
            "encryption": "age-x25519" if production_ready else "unresolved-test-only-none",
            "disposable_test_only": not production_ready,
            "excluded_sensitivity_counts": {
                key.value: value for key, value in excluded_counts.items()
            },
            "backup_assets": [item.model_dump(mode="json") for item in assets],
        }
        base_manifest["package_sha256"] = _package_digest(base_manifest)
        manifest = MemoryPackageManifest.model_validate(base_manifest)
        manifest_bytes = canonical_json_bytes(manifest.model_dump(mode="json"))
        members[_MANIFEST] = manifest_bytes
        target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        if production_ready:
            assert self.age_tool is not None
            assert age_recipient is not None
            if target.suffix != ".age":
                raise ExchangePolicyError("approved age envelope destination must end in .age")
            try:
                envelope = self.age_tool.encrypt(
                    self._zip_bytes(members),
                    recipient=age_recipient,
                )
            except AgeToolError as error:
                raise ExchangePolicyError("age encryption failed") from error
            atomic_write_bytes(target, envelope)
        elif container is PackageContainer.DIRECTORY:
            target.mkdir(mode=0o700)
            for name, content in sorted(members.items()):
                atomic_write_bytes(target / name, content)
        else:
            self._write_zip(target, members)
        return PackageCandidate(
            destination=str(target),
            container=container,
            manifest=manifest,
            manifest_sha256=sha256_bytes(manifest_bytes),
            excluded_record_ids=excluded_record_ids,
            excluded_source_ids=excluded_source_ids,
        )

    @staticmethod
    def _zip_bytes(members: Mapping[str, bytes]) -> bytes:
        stream = io.BytesIO()
        with zipfile.ZipFile(
            stream,
            mode="w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=9,
        ) as archive:
            for name, content in sorted(members.items()):
                info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o600 << 16
                info.create_system = 3
                archive.writestr(info, content)
        return stream.getvalue()

    @classmethod
    def _write_zip(cls, target: Path, members: Mapping[str, bytes]) -> None:
        atomic_write_bytes(target, cls._zip_bytes(members))


class MemoryPackageValidator:
    """Validate all package bytes before constructing provider-neutral contracts."""

    def __init__(
        self,
        policy: ImportPolicy,
        *,
        age_tool: AgeTool | None = None,
        identity_file: Path | None = None,
    ) -> None:
        self.policy = policy
        self.age_tool = age_tool
        self.identity_file = identity_file

    def validate(self, package_path: Path) -> ValidatedPackage:
        members, container, age_encrypted = self._read_members(package_path)
        try:
            manifest_value = _strict_json(members[_MANIFEST])
            manifest = MemoryPackageManifest.model_validate(manifest_value)
        except (KeyError, ValidationError, PackageValidationError) as error:
            raise PackageValidationError("package manifest is absent or invalid") from error
        if age_encrypted:
            if manifest.encryption != "age-x25519" or manifest.disposable_test_only:
                raise PackageValidationError("age envelope manifest is inconsistent")
        else:
            if manifest.encryption != "unresolved-test-only-none":
                raise PackageValidationError("plaintext package cannot claim encryption")
            if self.policy.required_encryption is not None:
                raise ExchangePolicyError("import policy requires an age-encrypted package")
            if not self.policy.allow_unencrypted_disposable_test_only:
                raise ExchangePolicyError(
                    "unencrypted candidate import is disabled by package policy"
                )
        expected_members = {_MANIFEST, *(item.path for item in manifest.files)}
        if set(members) != expected_members or expected_members != _ALL_MEMBERS:
            raise PackageValidationError("package members do not match the closed manifest")
        if _package_digest(manifest) != manifest.package_sha256:
            raise PackageValidationError("package manifest digest is invalid")
        by_name = {item.path: item for item in manifest.files}
        for name in _DATA_MEMBERS:
            content = members[name]
            metadata = by_name[name]
            count = _line_count(content) if name.endswith(".jsonl") else 1
            if (
                metadata.byte_size != len(content)
                or metadata.sha256 != sha256_bytes(content)
                or metadata.item_count != count
            ):
                raise PackageValidationError(f"package member checksum failed: {name}")
        if (
            manifest.project_id != self.policy.target_project_id
            or manifest.dataset_id != self.policy.target_dataset_id
        ):
            raise ImportConflictError("package crosses the target project or dataset boundary")
        if manifest.profile_versions != self.policy.expected_profile_versions:
            raise ImportConflictError("package profile versions are not compatible with target")
        sources = self._parse_jsonl(members[_SOURCES], SourceRecord)
        records = self._parse_jsonl(members[_RECORDS], MemoryRecord)
        relations = self._parse_jsonl(members[_RELATIONS], RelationRecord)
        provenance = self._parse_jsonl(members[_PROVENANCE], OriginProvenance)
        typed_sources = tuple(item for item in sources if isinstance(item, SourceRecord))
        typed_records = tuple(item for item in records if isinstance(item, MemoryRecord))
        typed_relations = tuple(item for item in relations if isinstance(item, RelationRecord))
        typed_provenance = tuple(item for item in provenance if isinstance(item, OriginProvenance))
        if len(typed_sources) != len(sources) or len(typed_records) != len(records):
            raise PackageValidationError("package typed record conversion failed")
        if len(typed_relations) != len(relations) or len(typed_provenance) != len(provenance):
            raise PackageValidationError("package typed relation conversion failed")
        if any(
            source.trust_class not in self.policy.allowed_trust_classes
            or source.sensitivity not in self.policy.allowed_sensitivities
            for source in typed_sources
        ):
            raise PackageValidationError("source trust or sensitivity is outside import policy")
        source_by_id = {source.source_id: source for source in typed_sources}
        if any(record.source.source_id not in source_by_id for record in typed_records):
            raise PackageValidationError("record source metadata is missing from the package")
        if any(
            record.source.content_sha256 != source_by_id[record.source.source_id].content_sha256
            or (
                record.source.path is not None
                and record.source.path != source_by_id[record.source.source_id].path_or_uri
            )
            or (
                record.source.origin_uri is not None
                and record.source.origin_uri
                not in {
                    source_by_id[record.source.source_id].origin_uri,
                    source_by_id[record.source.source_id].path_or_uri,
                }
            )
            for record in typed_records
        ):
            raise PackageValidationError("record source anchors conflict with source metadata")
        if any(
            record.authority.trust_class not in self.policy.allowed_trust_classes
            or record.security.sensitivity not in self.policy.allowed_sensitivities
            for record in typed_records
        ):
            raise PackageValidationError("record trust or sensitivity is outside import policy")
        try:
            require_secret_free(
                {
                    "sources": [source.to_json_dict() for source in typed_sources],
                    "records": [record.to_json_dict() for record in typed_records],
                    "relations": [relation.to_json_dict() for relation in typed_relations],
                },
                field_path="memory_package",
            )
        except SecretDetectedError as error:
            raise PackageValidationError("package contains secret-like content") from error
        reused = self._canonical_collisions(typed_sources)
        try:
            snapshot = ProviderSnapshot.build(
                project_id=manifest.project_id,
                dataset_id=manifest.dataset_id,
                created_at=manifest.created_at,
                origin_provider=ProviderName(manifest.origin_provider),
                origin_provider_version=manifest.origin_provider_version,
                profile_versions=dict(manifest.profile_versions),
                sources=typed_sources,
                records=typed_records,
                relations=typed_relations,
            )
        except (ValueError, ValidationError) as error:
            raise PackageValidationError("provider-neutral snapshot is invalid") from error
        record_ids = {record.record_id for record in typed_records}
        if {item.record_id for item in typed_provenance} != record_ids:
            raise PackageValidationError("origin provenance does not cover exactly the records")
        if any(
            item.origin_project_id != manifest.project_id
            or item.origin_provider != manifest.origin_provider
            or item.origin_provider_version != manifest.origin_provider_version
            for item in typed_provenance
        ):
            raise PackageValidationError("origin provenance conflicts with the manifest")
        record_by_id = {record.record_id: record for record in typed_records}
        if any(
            item.source_id != record_by_id[item.record_id].source.source_id
            or item.origin_content_sha256 != record_by_id[item.record_id].source.content_sha256
            for item in typed_provenance
        ):
            raise PackageValidationError("origin provenance conflicts with record anchors")
        self._validate_auxiliary_members(members, typed_records, manifest)
        return ValidatedPackage(
            package_path=package_path.resolve(strict=True),
            container=container,
            manifest=manifest,
            manifest_sha256=sha256_bytes(members[_MANIFEST]),
            snapshot=snapshot,
            provenance=typed_provenance,
            members=members,
            canonical_references_reused=reused,
        )

    @staticmethod
    def _parse_jsonl(
        content: bytes,
        model: type[SourceRecord]
        | type[MemoryRecord]
        | type[RelationRecord]
        | type[OriginProvenance],
    ) -> tuple[SourceRecord | MemoryRecord | RelationRecord | OriginProvenance, ...]:
        values: list[SourceRecord | MemoryRecord | RelationRecord | OriginProvenance] = []
        for raw in content.splitlines():
            if not raw.strip():
                continue
            try:
                values.append(model.model_validate(_strict_json(raw)))
            except (ValidationError, PackageValidationError) as error:
                raise PackageValidationError("package JSONL contract validation failed") from error
        return tuple(values)

    def _canonical_collisions(self, sources: tuple[SourceRecord, ...]) -> tuple[str, ...]:
        reused: set[str] = set()
        for source in sources:
            if source.canonicality.casefold() not in {"canonical", "authoritative"}:
                continue
            assert source.content_sha256 is not None
            by_id = self.policy.canonical_source_hashes.get(source.source_id)
            by_path = self.policy.canonical_path_hashes.get(source.path_or_uri)
            for existing in (by_id, by_path):
                if existing is not None and existing != source.content_sha256:
                    raise ImportConflictError(
                        "package canonical metadata conflicts with current canonical source"
                    )
            if by_id is not None or by_path is not None:
                reused.add(source.source_id)
        return tuple(sorted(reused))

    @staticmethod
    def _validate_auxiliary_members(
        members: Mapping[str, bytes],
        records: tuple[MemoryRecord, ...],
        manifest: MemoryPackageManifest,
    ) -> None:
        try:
            profiles = _strict_json(members[_PROFILES])
            statuses = _strict_json(members[_STATUS])
            backup = _strict_json(members[_BACKUP])
        except PackageValidationError as error:
            raise PackageValidationError("package JSON metadata is invalid") from error
        if not isinstance(profiles, dict) or profiles.get("profiles") != manifest.profile_versions:
            raise PackageValidationError("profile metadata conflicts with the manifest")
        expected_statuses = [
            {
                "record_id": record.record_id,
                "status": record.lifecycle.status.value,
                "version": record.version,
            }
            for record in records
        ]
        if not isinstance(statuses, dict) or statuses.get("records") != expected_statuses:
            raise PackageValidationError("status metadata conflicts with records")
        expected_assets = [item.model_dump(mode="json") for item in manifest.backup_assets]
        if not isinstance(backup, dict) or backup.get("assets") != expected_assets:
            raise PackageValidationError("backup asset metadata conflicts with manifest")

    def _read_members(
        self, package_path: Path
    ) -> tuple[dict[str, bytes], PackageContainer, bool]:
        if package_path.is_symlink():
            raise PackageValidationError("package path must not be a symlink")
        if package_path.is_dir():
            members: dict[str, bytes] = {}
            children = tuple(package_path.iterdir())
            if len(children) > self.policy.max_members:
                raise PackageValidationError("package member count exceeds policy")
            total = 0
            for child in children:
                if child.is_symlink() or not child.is_file() or child.parent != package_path:
                    raise PackageValidationError("directory package contains an unsafe member")
                if child.name.casefold() in {name.casefold() for name in members}:
                    raise PackageValidationError("directory package contains duplicate members")
                size = child.stat().st_size
                if size > self.policy.max_member_bytes:
                    raise PackageValidationError("package member exceeds size policy")
                total += size
                if total > self.policy.max_total_bytes:
                    raise PackageValidationError("package exceeds total size policy")
                members[child.name] = child.read_bytes()
            return members, PackageContainer.DIRECTORY, False
        if not package_path.is_file():
            raise PackageValidationError("package must be a regular directory, ZIP, or age file")
        if zipfile.is_zipfile(package_path):
            return self._read_zip(package_path), PackageContainer.ZIP, False
        if self.age_tool is None or self.identity_file is None:
            raise ExchangePolicyError("age-encrypted package requires local identity tooling")
        envelope_limit = self.policy.max_total_bytes + 1024 * 1024
        if package_path.stat().st_size > envelope_limit:
            raise PackageValidationError("age envelope exceeds package size policy")
        try:
            plaintext = self.age_tool.decrypt(
                package_path.read_bytes(),
                identity_file=self.identity_file,
                max_output_bytes=envelope_limit,
            )
        except AgeToolError as error:
            raise PackageValidationError("age envelope decryption failed") from error
        if not zipfile.is_zipfile(io.BytesIO(plaintext)):
            raise PackageValidationError("age envelope does not contain a ZIP package")
        return self._read_zip_bytes(plaintext), PackageContainer.ZIP, True

    def _read_zip(self, package_path: Path) -> dict[str, bytes]:
        with zipfile.ZipFile(package_path, mode="r") as archive:
            return self._read_zip_archive(archive)

    def _read_zip_bytes(self, content: bytes) -> dict[str, bytes]:
        with zipfile.ZipFile(io.BytesIO(content), mode="r") as archive:
            return self._read_zip_archive(archive)

    def _read_zip_archive(self, archive: zipfile.ZipFile) -> dict[str, bytes]:
        members: dict[str, bytes] = {}
        infos = archive.infolist()
        if len(infos) > self.policy.max_members:
            raise PackageValidationError("ZIP member count exceeds policy")
        total = 0
        names: set[str] = set()
        for info in infos:
            name = info.filename
            path = PurePosixPath(name)
            if (
                info.is_dir()
                or path.is_absolute()
                or "\\" in name
                or len(path.parts) != 1
                or any(part in {"", ".", ".."} for part in path.parts)
            ):
                raise PackageValidationError("ZIP contains an unsafe member path")
            folded = name.casefold()
            if folded in names:
                raise PackageValidationError("ZIP contains duplicate member names")
            names.add(folded)
            mode = info.external_attr >> 16
            if mode and stat.S_ISLNK(mode):
                raise PackageValidationError("ZIP symbolic links are prohibited")
            if info.flag_bits & 0x1:
                raise PackageValidationError("encrypted ZIP members are not supported")
            if info.compress_type not in {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED}:
                raise PackageValidationError("ZIP compression method is not supported")
            if info.file_size > self.policy.max_member_bytes:
                raise PackageValidationError("ZIP member exceeds size policy")
            total += info.file_size
            if total > self.policy.max_total_bytes:
                raise PackageValidationError("ZIP exceeds total size policy")
            if info.file_size:
                if info.compress_size == 0:
                    raise PackageValidationError("ZIP member has an invalid compressed size")
                if info.file_size / info.compress_size > self.policy.max_compression_ratio:
                    raise PackageValidationError("ZIP compression ratio exceeds bomb policy")
        for info in infos:
            with archive.open(info, mode="r") as stream:
                content = stream.read(self.policy.max_member_bytes + 1)
            if len(content) != info.file_size or len(content) > self.policy.max_member_bytes:
                raise PackageValidationError("ZIP member size changed during read")
            members[info.filename] = content
        return members

    def preview(self, package_path: Path) -> ImportPreview:
        validated = self.validate(package_path)
        manifest = validated.manifest
        checks = (
            "closed_member_set",
            "member_sizes_and_checksums",
            "package_manifest_digest",
            "provider_neutral_schema",
            "project_and_dataset_scope",
            "profile_compatibility",
            "trust_and_sensitivity_policy",
            "canonical_source_non_overwrite",
            "origin_provenance",
        )
        payload = {
            "package_id": manifest.package_id,
            "package_sha256": manifest.package_sha256,
            "manifest_sha256": validated.manifest_sha256,
            "project_id": manifest.project_id,
            "dataset_id": manifest.dataset_id,
            "profiles": manifest.profile_versions,
            "record_ids": [record.record_id for record in validated.snapshot.records],
            "relation_ids": [relation.relation_id for relation in validated.snapshot.relations],
            "canonical_references_reused": validated.canonical_references_reused,
        }
        return ImportPreview(
            package_path=str(validated.package_path),
            package_id=manifest.package_id,
            package_sha256=manifest.package_sha256,
            project_id=manifest.project_id,
            dataset_id=manifest.dataset_id,
            profile_versions=dict(manifest.profile_versions),
            source_count=len(validated.snapshot.sources),
            record_count=len(validated.snapshot.records),
            relation_count=len(validated.snapshot.relations),
            canonical_references_reused=validated.canonical_references_reused,
            validation_checks=checks,
            impact_digest=sha256_bytes(canonical_json_bytes(payload)),
            previewed_at=utc_now(),
        )


class MemoryPackageImporter:
    """Stage a validated neutral package and activate only an isolated provider generation."""

    def __init__(
        self,
        *,
        boundary: ProjectBoundary,
        derived_root: str,
        policy: ImportPolicy,
        age_tool: AgeTool | None = None,
        identity_file: Path | None = None,
    ) -> None:
        path = PurePosixPath(derived_root)
        if path.is_absolute() or path.parts[:2] != (".sys4ai", "memory") or ".." in path.parts:
            raise ValueError("import root must remain below .sys4ai/memory")
        boundary.require_identity(
            project_id=policy.target_project_id,
            dataset_id=policy.target_dataset_id,
        )
        self.boundary = boundary
        self.derived_relative = path.as_posix()
        self.derived_root = boundary.resolve_path(path.as_posix(), must_exist=False)
        self.policy = policy
        self.validator = MemoryPackageValidator(
            policy,
            age_tool=age_tool,
            identity_file=identity_file,
        )

    def _require_authorization(
        self,
        preview: ImportPreview,
        authorization: AuthorizedExchangeImpact,
    ) -> None:
        decision = authorization.decision
        if authorization.impact_digest != preview.impact_digest:
            raise ExchangePolicyError("import authorization does not match preview")
        if (
            decision.project_id != self.boundary.project_id
            or decision.dataset_id != self.boundary.dataset_id
        ):
            raise ExchangePolicyError("import authorization crosses project scope")

    async def stage(
        self,
        preview: ImportPreview,
        *,
        authorization: AuthorizedExchangeImpact,
        provider_stage: ProviderImportStage,
    ) -> StagedImport:
        current = self.validator.preview(Path(preview.package_path))
        if current.impact_digest != preview.impact_digest:
            raise ImportConflictError("package changed after import preview")
        self._require_authorization(current, authorization)
        if (
            provider_stage.context.project_id != self.boundary.project_id
            or provider_stage.context.dataset_id != self.boundary.dataset_id
            or not provider_stage.isolated_generation
        ):
            raise ImportConflictError("provider import stage crosses project scope")
        validated = self.validator.validate(Path(preview.package_path))
        request_suffix = stable_id("provider-import-preview", preview.package_id)
        provider_preview_request_id = f"mrq_import_preview_{request_suffix}"
        provider_preview = await provider_stage.provider.import_snapshot(
            ImportRequest(
                context=provider_stage.context,
                request_id=provider_preview_request_id,
                idempotency_key=f"import-preview:{preview.package_id}",
                format=ProviderExportFormat.SYS4AI,
                snapshot=validated.snapshot,
                execute=False,
                replace_existing=False,
                authorization=provider_stage.preview_authorization,
            )
        )
        _require_provider_import_result(
            provider_preview,
            provider=provider_stage.provider,
            request_id=provider_preview_request_id,
            context=provider_stage.context,
            snapshot=validated.snapshot,
            executed=False,
        )
        staging_identity = stable_id(
            "memory-package-import-stage",
            preview.package_id,
            preview.impact_digest,
            provider_preview.impact_digest,
        ).replace("-", "")
        staging_id = f"sti_{staging_identity}"
        stage_root = self.derived_root / "import-staging" / staging_id
        final_root = self.derived_root / "imports" / preview.package_id
        if stage_root.exists() or final_root.exists():
            raise ImportConflictError("import stage or final generation already exists")
        stage_root.mkdir(parents=True, exist_ok=False, mode=0o700)
        package_root = stage_root / "package"
        package_root.mkdir(mode=0o700)
        for name, content in sorted(validated.members.items()):
            atomic_write_bytes(package_root / name, content)
        staged = StagedImport(
            staging_id=staging_id,
            package_id=preview.package_id,
            staging_path=str(stage_root.relative_to(self.boundary.root)),
            package_sha256=preview.package_sha256,
            exchange_impact_digest=preview.impact_digest,
            provider_impact_digest=provider_preview.impact_digest,
            staged_at=utc_now(),
        )
        atomic_write_bytes(
            stage_root / "staged-import.json",
            canonical_json_bytes(staged.model_dump(mode="json")),
        )
        return staged

    async def activate(
        self,
        staged: StagedImport,
        *,
        authorization: AuthorizedExchangeImpact,
        provider_stage: ProviderImportStage,
        execution_authorization: PolicyEnvelope,
    ) -> ImportActivationReceipt:
        if authorization.impact_digest != staged.exchange_impact_digest:
            raise ExchangePolicyError("import activation authorization changed after stage")
        if (
            provider_stage.context.project_id != self.boundary.project_id
            or provider_stage.context.dataset_id != self.boundary.dataset_id
            or not provider_stage.isolated_generation
        ):
            raise ImportConflictError("provider import stage crosses project scope")
        stage_root = self.boundary.resolve_path(staged.staging_path)
        if not stage_root.is_dir() or stage_root.is_symlink():
            raise ImportConflictError("staged import root is unavailable")
        validated = self.validator.validate(stage_root / "package")
        preview = self.validator.preview(stage_root / "package")
        self._require_authorization(preview, authorization)
        if (
            validated.manifest.package_id != staged.package_id
            or validated.manifest.package_sha256 != staged.package_sha256
        ):
            raise ImportConflictError("staged package identity changed")
        request_suffix = stable_id("provider-import-execute", staged.staging_id)
        repeated_preview_request_id = f"mrq_import_recheck_{request_suffix}"
        repeated_preview = await provider_stage.provider.import_snapshot(
            ImportRequest(
                context=provider_stage.context,
                request_id=repeated_preview_request_id,
                idempotency_key=f"import-recheck:{staged.staging_id}",
                format=ProviderExportFormat.SYS4AI,
                snapshot=validated.snapshot,
                execute=False,
                replace_existing=False,
                authorization=provider_stage.preview_authorization,
            )
        )
        _require_provider_import_result(
            repeated_preview,
            provider=provider_stage.provider,
            request_id=repeated_preview_request_id,
            context=provider_stage.context,
            snapshot=validated.snapshot,
            executed=False,
            expected_impact_digest=staged.provider_impact_digest,
        )
        if repeated_preview.impact_digest != staged.provider_impact_digest:
            raise ImportConflictError("provider import impact changed after stage")
        if (
            execution_authorization.operation is not ProviderMutation.IMPORT
            or execution_authorization.impact_digest != staged.provider_impact_digest
        ):
            raise ExchangePolicyError("provider authorization does not match staged impact")
        execute_request_id = f"mrq_import_execute_{request_suffix}"
        result = await provider_stage.provider.import_snapshot(
            ImportRequest(
                context=provider_stage.context,
                request_id=execute_request_id,
                idempotency_key=f"import-execute:{staged.staging_id}",
                format=ProviderExportFormat.SYS4AI,
                snapshot=validated.snapshot,
                execute=True,
                replace_existing=False,
                preview_digest=staged.provider_impact_digest,
                authorization=execution_authorization,
            )
        )
        _require_provider_import_result(
            result,
            provider=provider_stage.provider,
            request_id=execute_request_id,
            context=provider_stage.context,
            snapshot=validated.snapshot,
            executed=True,
            expected_impact_digest=staged.provider_impact_digest,
        )
        imported_at = utc_now()
        provenance = tuple(
            {
                **item.model_dump(mode="json"),
                "imported_from_package": staged.package_id,
                "imported_at": imported_at.isoformat().replace("+00:00", "Z"),
            }
            for item in validated.provenance
        )
        atomic_write_bytes(stage_root / "import-provenance.jsonl", _json_lines(provenance))
        receipt_identity = stable_id("memory-package-import-receipt", staged.staging_id).replace(
            "-", ""
        )
        final_relative = f"{self.derived_relative}/imports/{staged.package_id}"
        receipt = ImportActivationReceipt(
            receipt_id=f"imr_{receipt_identity}",
            package_id=staged.package_id,
            project_id=self.boundary.project_id,
            dataset_id=self.boundary.dataset_id,
            origin_project_id=validated.manifest.project_id,
            origin_provider=validated.manifest.origin_provider,
            imported_record_ids=result.imported_record_ids,
            imported_relation_ids=result.imported_relation_ids,
            active_import_path=final_relative,
            package_sha256=staged.package_sha256,
            provider_impact_digest=staged.provider_impact_digest,
            imported_at=imported_at,
        )
        atomic_write_bytes(
            stage_root / "import-receipt.json",
            canonical_json_bytes(receipt.model_dump(mode="json")),
        )
        final_root = self.derived_root / "imports" / staged.package_id
        final_root.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        if final_root.exists():
            raise ImportConflictError("final import generation appeared during activation")
        os.replace(stage_root, final_root)
        pointer = {
            "schema_version": "1.0",
            "project_id": self.boundary.project_id,
            "dataset_id": self.boundary.dataset_id,
            "package_id": staged.package_id,
            "active_import_path": final_relative,
            "package_sha256": staged.package_sha256,
            "activated_at": imported_at.isoformat().replace("+00:00", "Z"),
        }
        atomic_write_bytes(self.derived_root / "active-import.json", canonical_json_bytes(pointer))
        return receipt
