"""Typed configuration contract for ``config/memory.toml``."""

from __future__ import annotations

import re
from typing import Literal, Self
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ConfigurationModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, validate_default=True)


class ServiceSettings(ConfigurationModel):
    transport: Literal["in_process", "http", "mcp"]
    network_listener_enabled: bool
    bind_host: str
    authentication_posture: str
    single_writer: bool

    @model_validator(mode="after")
    def validate_network_posture(self) -> Self:
        if not self.network_listener_enabled and self.transport != "in_process":
            raise ValueError("disabled network listener requires in_process transport")
        if self.network_listener_enabled and self.transport == "in_process":
            raise ValueError("network listener requires a network transport")
        if self.network_listener_enabled and not self.authentication_posture.startswith(
            "authenticated-"
        ):
            raise ValueError("network listener requires an authenticated posture")
        return self


class CogneeSettings(ConfigurationModel):
    dataset: str
    backend_access_control_posture: str
    accept_local_file_path: bool


class ProviderSettings(ConfigurationModel):
    name: str
    version_constraint: str
    mode: Literal["standalone", "api", "cloud"]
    initialize_on_load: bool
    allow_native_client_access: bool
    outbound_network: Literal["deny", "local-only", "allow"]
    cognee: CogneeSettings


class ExactIndexSettings(ConfigurationModel):
    enabled: bool
    provider: str
    path: str


class ModelRuntimeProfile(ConfigurationModel):
    """Named local or remote model endpoint with references, never secret values."""

    profile_id: str = Field(min_length=1, max_length=255)
    capability: Literal["llm", "embedding"]
    locality: Literal["local", "remote"]
    provider: str = Field(min_length=1, max_length=255)
    model: str = Field(min_length=1, max_length=500)
    endpoint: str | None = None
    dimensions: int | None = Field(default=None, gt=0)
    credential_reference: str | None = None

    @model_validator(mode="after")
    def validate_endpoint_and_secret_boundary(self) -> Self:
        if self.capability == "embedding" and self.dimensions is None:
            raise ValueError("embedding profiles require dimensions")
        if self.capability == "llm" and self.dimensions is not None:
            raise ValueError("LLM profiles cannot declare embedding dimensions")
        parsed = urlsplit(self.endpoint) if self.endpoint is not None else None
        if parsed is not None and (parsed.username is not None or parsed.password is not None):
            raise ValueError("model endpoints cannot contain embedded credentials")
        if self.locality == "local":
            if self.credential_reference is not None:
                raise ValueError("local model profiles cannot require a credential reference")
            if parsed is not None and (
                parsed.scheme not in {"http", "https"}
                or parsed.hostname not in {"localhost", "127.0.0.1", "::1"}
            ):
                raise ValueError("local model endpoints must use an explicit loopback URL")
        else:
            if parsed is None or parsed.scheme != "https" or not parsed.hostname:
                raise ValueError("remote model profiles require an HTTPS endpoint")
            if self.credential_reference is None or re.fullmatch(
                r"(?:environment|keychain|managed-secret):[A-Za-z0-9_.:/@-]+",
                self.credential_reference,
            ) is None:
                raise ValueError("remote models require a supported credential reference")
        return self


class ModelSettings(ConfigurationModel):
    semantic_enabled: bool
    llm_profile: str
    embedding_profile: str
    model_cache_dir: str
    allow_remote: bool
    allow_cloud_fallback: bool
    profiles: tuple[ModelRuntimeProfile, ...] = ()

    @model_validator(mode="after")
    def prevent_implicit_remote_fallback(self) -> Self:
        if self.allow_cloud_fallback and not self.allow_remote:
            raise ValueError("cloud fallback cannot be enabled when remote models are denied")
        if self.semantic_enabled and any(
            value.startswith("pending-") for value in (self.llm_profile, self.embedding_profile)
        ):
            raise ValueError("semantic operation requires resolved LLM and embedding profiles")
        profile_ids = tuple(profile.profile_id for profile in self.profiles)
        if len(profile_ids) != len(set(profile_ids)):
            raise ValueError("model profile IDs must be unique")
        by_id = {profile.profile_id: profile for profile in self.profiles}
        for capability, profile_id in (
            ("llm", self.llm_profile),
            ("embedding", self.embedding_profile),
        ):
            profile = by_id.get(profile_id)
            if profile is None and self.semantic_enabled:
                raise ValueError(f"semantic operation requires a registered {capability} profile")
            if profile is None:
                continue
            if profile.capability != capability:
                raise ValueError(f"{capability} profile selects the wrong capability")
            if profile.locality == "remote" and not self.allow_remote:
                raise ValueError("selected remote model profile requires allow_remote=true")
        return self

    def profile(self, profile_id: str) -> ModelRuntimeProfile | None:
        return next((item for item in self.profiles if item.profile_id == profile_id), None)


class RegistrySettings(ConfigurationModel):
    sources: str
    profiles: str
    relations: str


class SourceSettings(ConfigurationModel):
    respect_gitignore: bool
    default_include: bool
    require_registered_rule: bool
    require_discovery_dry_run: bool


class ControlRecordSettings(ConfigurationModel):
    root: str
    approval_policy_status: str
    reviewer_principal_id: str
    approvals_required: Literal[1]
    self_approval_allowed: Literal[False]
    deny_unresolved_approval: bool


class PermissionSettings(ConfigurationModel):
    general_operations: tuple[str, ...]
    privileged_operations: tuple[str, ...]
    mutation_enabled: bool
    require_canonical_permission: bool


class SecuritySettings(ConfigurationModel):
    secret_scan: bool
    external_content_is_authority: bool
    allow_authority_inheritance: bool
    safe_path_mode: Literal["project-allowlist"]
    allow_arbitrary_local_paths: bool
    require_dry_run_for_destructive: bool
    require_impact_preview: bool
    destructive_execution_enabled: bool


class RetentionSettings(ConfigurationModel):
    policy_status: str
    session_ttl_hours: int = Field(gt=0)
    episodic_ttl_days: int = Field(gt=0)
    session_persistence: bool
    episodic_persistence: bool


class ExportSettings(ConfigurationModel):
    enabled: bool
    format_status: str
    container: Literal["zip"]
    encryption_required: bool
    encryption: Literal["age-x25519"]
    recipient_reference_required: bool
    provider_native_export_enabled: bool


class SharedSettings(ConfigurationModel):
    enabled: bool
    backend_status: str
    authentication_required: bool
    dataset_isolation_required: bool


class FeedbackSettings(ConfigurationModel):
    automatic_collection: bool
    explicit_typed_only: bool
    policy_status: str


class ObservabilitySettings(ConfigurationModel):
    local_audit_log: str
    content_logging: Literal["metadata_only", "disabled"]
    telemetry_export: bool


class MemorySettings(ConfigurationModel):
    enabled: bool
    api_version: Literal["1.0"]
    project_id: str
    project_root: str
    default_memory_profile: str
    deployment_profile: str
    local_data_dir: str
    read_only: bool
    strict_config: bool
    service: ServiceSettings
    provider: ProviderSettings
    exact_index: ExactIndexSettings
    models: ModelSettings
    registries: RegistrySettings
    sources: SourceSettings
    control_records: ControlRecordSettings
    permissions: PermissionSettings
    security: SecuritySettings
    retention: RetentionSettings
    export: ExportSettings
    shared: SharedSettings
    feedback: FeedbackSettings
    observability: ObservabilitySettings

    @model_validator(mode="after")
    def validate_security_invariants(self) -> Self:
        if self.project_root != ".":
            raise ValueError("tracked configuration must resolve project_root from '.'")
        if not self.strict_config:
            raise ValueError("strict_config must remain enabled")
        if self.provider.initialize_on_load:
            raise ValueError("provider initialization on configuration load is prohibited")
        if self.provider.allow_native_client_access:
            raise ValueError("native provider access is prohibited")
        if self.provider.cognee.accept_local_file_path:
            raise ValueError("provider local-file access must remain disabled")
        if self.models.allow_cloud_fallback:
            raise ValueError("implicit cloud fallback is prohibited")
        if self.security.external_content_is_authority:
            raise ValueError("external content cannot become authority by configuration")
        if self.security.allow_authority_inheritance:
            raise ValueError("authority inheritance is prohibited")
        if self.security.allow_arbitrary_local_paths:
            raise ValueError("arbitrary local paths are prohibited")
        if not self.security.secret_scan:
            raise ValueError("secret scanning must remain enabled")
        if self.read_only and self.permissions.mutation_enabled:
            raise ValueError("read_only configuration cannot enable mutation")
        if self.export.enabled and (
            self.export.format_status.startswith("pending-")
            or not self.export.encryption_required
            or not self.export.recipient_reference_required
        ):
            raise ValueError("enabled export requires the approved encrypted package policy")
        if self.shared.enabled and (
            not self.shared.authentication_required or not self.shared.dataset_isolation_required
        ):
            raise ValueError("shared mode requires authentication and dataset isolation")
        if self.shared.enabled and self.shared.backend_status.startswith("disabled-"):
            raise ValueError("shared mode cannot use a disabled backend profile")
        if self.feedback.automatic_collection or not self.feedback.explicit_typed_only:
            raise ValueError("the approved feedback posture permits explicit typed feedback only")
        return self


class MemoryConfiguration(ConfigurationModel):
    config_version: Literal["1.0"]
    configuration_status: str
    memory: MemorySettings


class CapabilityGate(ConfigurationModel):
    capability: str
    ready: bool
    issues: tuple[str, ...] = Field(default_factory=tuple)
