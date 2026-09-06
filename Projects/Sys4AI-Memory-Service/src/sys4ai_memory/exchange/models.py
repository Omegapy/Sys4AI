"""Inspectable provider-neutral memory package contracts."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from sys4ai_memory.authorization import AuthorizationDecision
from sys4ai_memory.contracts import Permission, Sensitivity, TrustClass
from sys4ai_memory.contracts._base import Sha256, UtcDateTime
from sys4ai_memory.providers import ProviderExportFormat


class ExchangeModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, validate_default=True)


class PackageContainer(StrEnum):
    DIRECTORY = "directory"
    ZIP = "zip"


class BackupAssetClass(StrEnum):
    CANONICAL = "canonical"
    DERIVED = "derived"
    OPTIONAL = "optional"
    SENSITIVE = "sensitive"


class PackageFile(ExchangeModel):
    path: str = Field(pattern=r"^[a-z][a-z0-9-]*\.(?:json|jsonl)$")
    media_type: Literal["application/json", "application/x-ndjson"]
    sha256: Sha256
    byte_size: int = Field(ge=0)
    item_count: int = Field(ge=0)


class BackupAsset(ExchangeModel):
    path_class: str = Field(min_length=1)
    asset_class: BackupAssetClass
    package_included: bool
    sensitive: bool
    recovery_role: str = Field(min_length=1)


class OriginProvenance(ExchangeModel):
    record_id: str = Field(pattern=r"^mem_[A-Za-z0-9][A-Za-z0-9_.:@-]*$")
    source_id: str = Field(pattern=r"^src_[A-Za-z0-9][A-Za-z0-9_.:@-]*$")
    origin_project_id: str = Field(min_length=1)
    origin_provider: str = Field(min_length=1)
    origin_provider_version: str = Field(min_length=1)
    origin_content_sha256: Sha256


class MemoryPackageManifest(ExchangeModel):
    schema_version: Literal["1.0"] = "1.0"
    package_format: Literal["sys4ai-memory-package"] = "sys4ai-memory-package"
    package_version: Literal["1.0.0"] = "1.0.0"
    package_id: str = Field(pattern=r"^smp_[A-Za-z0-9_.:@-]+$")
    project_id: str = Field(min_length=1)
    dataset_id: str = Field(min_length=1)
    created_at: UtcDateTime
    origin_provider: str = Field(min_length=1)
    origin_provider_version: str = Field(min_length=1)
    profile_versions: dict[str, str] = Field(min_length=1)
    files: tuple[PackageFile, ...] = Field(min_length=1)
    package_sha256: Sha256
    encryption: Literal["unresolved-test-only-none", "age-x25519"]
    disposable_test_only: bool
    excluded_sensitivity_counts: dict[Sensitivity, int]
    backup_assets: tuple[BackupAsset, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_files(self) -> Self:
        paths = tuple(item.path for item in self.files)
        if len(paths) != len(set(paths)):
            raise ValueError("package manifest files must be unique")
        if any(count < 0 for count in self.excluded_sensitivity_counts.values()):
            raise ValueError("excluded sensitivity counts cannot be negative")
        if self.encryption == "unresolved-test-only-none" and not self.disposable_test_only:
            raise ValueError("unencrypted packages must remain disposable-test-only")
        if self.encryption == "age-x25519" and self.disposable_test_only:
            raise ValueError("approved age packages cannot claim disposable-test-only status")
        return self


class ExportPolicy(ExchangeModel):
    format_decision_status: str = Field(min_length=1)
    encryption_required: bool = True
    approved_encryption: Literal["age-x25519"] | None = None
    allowed_sensitivities: frozenset[Sensitivity] = frozenset(
        {Sensitivity.PUBLIC, Sensitivity.INTERNAL}
    )
    allow_unencrypted_disposable_test_only: bool = False

    @model_validator(mode="after")
    def validate_policy(self) -> Self:
        if Sensitivity.SECRET_PROHIBITED in self.allowed_sensitivities:
            raise ValueError("secret-prohibited material can never be exported")
        if self.approved_encryption is not None and self.format_decision_status.startswith(
            "pending-"
        ):
            raise ValueError("pending format policy cannot name approved encryption")
        if not self.format_decision_status.startswith("pending-") and (
            not self.encryption_required or self.approved_encryption != "age-x25519"
        ):
            raise ValueError("approved package policy requires age-x25519 encryption")
        return self


class PackageCandidate(ExchangeModel):
    destination: str = Field(min_length=1)
    container: PackageContainer
    manifest: MemoryPackageManifest
    manifest_sha256: Sha256
    excluded_record_ids: tuple[str, ...]
    excluded_source_ids: tuple[str, ...]


class ImportPolicy(ExchangeModel):
    target_project_id: str = Field(min_length=1)
    target_dataset_id: str = Field(min_length=1)
    expected_profile_versions: dict[str, str] = Field(min_length=1)
    allowed_trust_classes: frozenset[TrustClass]
    allowed_sensitivities: frozenset[Sensitivity]
    canonical_source_hashes: dict[str, Sha256] = Field(default_factory=dict)
    canonical_path_hashes: dict[str, Sha256] = Field(default_factory=dict)
    max_members: int = Field(default=16, ge=1, le=1000)
    max_member_bytes: int = Field(default=16 * 1024 * 1024, ge=1)
    max_total_bytes: int = Field(default=64 * 1024 * 1024, ge=1)
    max_compression_ratio: float = Field(default=50.0, ge=1.0)
    required_encryption: Literal["age-x25519"] | None = None
    allow_unencrypted_disposable_test_only: bool = False

    @model_validator(mode="after")
    def validate_policy(self) -> Self:
        if Sensitivity.SECRET_PROHIBITED in self.allowed_sensitivities:
            raise ValueError("secret-prohibited material can never be imported")
        if not self.allowed_trust_classes or not self.allowed_sensitivities:
            raise ValueError("import policy requires explicit trust and sensitivity allowlists")
        if self.required_encryption is not None and self.allow_unencrypted_disposable_test_only:
            raise ValueError("required encryption cannot allow an unencrypted test package")
        return self


class ImportPreview(ExchangeModel):
    schema_version: Literal["1.0"] = "1.0"
    package_path: str = Field(min_length=1)
    package_id: str = Field(pattern=r"^smp_[A-Za-z0-9_.:@-]+$")
    package_sha256: Sha256
    project_id: str = Field(min_length=1)
    dataset_id: str = Field(min_length=1)
    profile_versions: dict[str, str] = Field(min_length=1)
    source_count: int = Field(ge=0)
    record_count: int = Field(ge=0)
    relation_count: int = Field(ge=0)
    canonical_references_reused: tuple[str, ...]
    validation_checks: tuple[str, ...] = Field(min_length=1)
    impact_digest: Sha256
    previewed_at: UtcDateTime


class AuthorizedExchangeImpact(ExchangeModel):
    decision: AuthorizationDecision
    impact_digest: Sha256

    @model_validator(mode="after")
    def validate_decision(self) -> Self:
        decision = self.decision
        if not decision.allowed:
            raise ValueError("import authorization must be allowed")
        if decision.operation != "memory.import.activate":
            raise ValueError("authorization is not for import activation")
        if decision.permission is not Permission.ADMINISTER:
            raise ValueError("import activation requires administer permission")
        if decision.permission_revision is None or decision.canonical_sha256 is None:
            raise ValueError("import authorization must identify current canonical policy")
        return self


class StagedImport(ExchangeModel):
    staging_id: str = Field(pattern=r"^sti_[A-Za-z0-9_.:@-]+$")
    package_id: str = Field(pattern=r"^smp_[A-Za-z0-9_.:@-]+$")
    staging_path: str = Field(min_length=1)
    package_sha256: Sha256
    exchange_impact_digest: Sha256
    provider_impact_digest: Sha256
    staged_at: UtcDateTime


class ImportActivationReceipt(ExchangeModel):
    receipt_id: str = Field(pattern=r"^imr_[A-Za-z0-9_.:@-]+$")
    package_id: str = Field(pattern=r"^smp_[A-Za-z0-9_.:@-]+$")
    project_id: str = Field(min_length=1)
    dataset_id: str = Field(min_length=1)
    origin_project_id: str = Field(min_length=1)
    origin_provider: str = Field(min_length=1)
    imported_record_ids: tuple[str, ...]
    imported_relation_ids: tuple[str, ...]
    canonical_sources_overwritten: Literal[False] = False
    active_import_path: str = Field(min_length=1)
    package_sha256: Sha256
    provider_impact_digest: Sha256
    imported_at: UtcDateTime


class MigrationStep(ExchangeModel):
    step_id: str = Field(min_length=1)
    source_version: str = Field(min_length=1)
    target_version: str = Field(min_length=1)
    description: str = Field(min_length=1)


class MigrationDryRun(ExchangeModel):
    package_id: str = Field(pattern=r"^smp_[A-Za-z0-9_.:@-]+$")
    source_version: str = Field(min_length=1)
    target_version: str = Field(min_length=1)
    steps: tuple[MigrationStep, ...]
    affected_record_ids: tuple[str, ...]
    warnings: tuple[str, ...]
    impact_digest: Sha256
    executed: Literal[False] = False


class CogxDelegation(ExchangeModel):
    format: Literal[ProviderExportFormat.COGX] = ProviderExportFormat.COGX
    provider_name: str = Field(min_length=1)
    provider_version: str = Field(min_length=1)
    direction: Literal["export", "import"]
    artifact_path: str = Field(min_length=1)
    provider_owned: Literal[True] = True
    approved: bool
    reason_code: str = Field(min_length=1)
