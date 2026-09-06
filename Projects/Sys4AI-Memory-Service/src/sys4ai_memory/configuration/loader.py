"""Load and evaluate configuration without provider or filesystem side effects."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

from pydantic import ValidationError

from sys4ai_memory.util import canonical_json_bytes, resolve_within, sha256_bytes

from .models import CapabilityGate, MemoryConfiguration


class ConfigurationError(ValueError):
    """The configuration cannot be safely loaded."""


class CapabilityBlocked(ConfigurationError):
    """A requested capability is unavailable under the current safe policy."""

    def __init__(self, gate: CapabilityGate) -> None:
        self.gate = gate
        super().__init__(f"{gate.capability} is blocked: {'; '.join(gate.issues)}")


@dataclass(frozen=True, slots=True)
class LoadedConfiguration:
    configuration: MemoryConfiguration
    project_root: Path
    configuration_path: Path
    resolved_paths: dict[str, Path]
    fingerprint: str

    def gate(self, capability: str) -> CapabilityGate:
        """Evaluate one capability without changing process or filesystem state."""

        memory = self.configuration.memory
        issues: list[str] = []
        safe_introspection = {"health", "dry_run", "sources_list", "sources_explain"}
        if not memory.enabled and capability not in safe_introspection:
            issues.append("memory.enabled is false")
        if (
            self.configuration.configuration_status.startswith("stage0-")
            and capability not in safe_introspection
        ):
            issues.append("configuration is Stage 0 only")

        if capability in {"exact", "lexical", "sync", "recall"}:
            if not memory.exact_index.enabled:
                issues.append("exact index is disabled")
            if memory.exact_index.provider.startswith("pending-"):
                issues.append("exact-index provider decision is pending")
        if capability in {"semantic", "graph", "temporal", "recall"}:
            if not memory.models.semantic_enabled:
                issues.append("semantic providers are disabled")
            if any(
                value.startswith("pending-")
                for value in (
                    memory.models.llm_profile,
                    memory.models.embedding_profile,
                )
            ):
                issues.append("local model profile decision is pending")
        if capability in {"propose", "approve", "improve", "forget", "rebuild", "import"} and (
            memory.read_only or not memory.permissions.mutation_enabled
        ):
            issues.append("mutation is disabled")
        if capability == "forget" and not memory.security.destructive_execution_enabled:
            issues.append("destructive execution is disabled")
        if capability in {"approve", "promote", "forget"} and (
            memory.control_records.approval_policy_status.startswith("pending-")
        ):
            issues.append("canonical approval policy is pending")
        if capability in {"session", "episodic"} and memory.retention.policy_status.startswith(
            "pending-"
        ):
            issues.append("retention policy is pending")
        if capability == "export":
            if not memory.export.enabled:
                issues.append("export is disabled")
            if memory.export.format_status.startswith("pending-"):
                issues.append("export format decision is pending")
        if capability == "shared":
            if not memory.shared.enabled:
                issues.append("shared mode is disabled")
            if memory.shared.backend_status.startswith("pending-"):
                issues.append("shared backend decision is pending")
        if capability == "feedback" and memory.feedback.policy_status.startswith("pending-"):
            issues.append("feedback policy is pending")
        if capability == "network" and not memory.service.network_listener_enabled:
            issues.append("network listener is disabled")

        return CapabilityGate(capability=capability, ready=not issues, issues=tuple(issues))

    def require(self, capability: str) -> None:
        gate = self.gate(capability)
        if not gate.ready:
            raise CapabilityBlocked(gate)


def _regular_configuration_path(path: Path, project_root: Path) -> Path:
    if not project_root.is_absolute() or project_root.is_symlink() or not project_root.is_dir():
        raise ConfigurationError("trusted project root must be an absolute non-symlink directory")
    if path.is_symlink() or not path.is_file():
        raise ConfigurationError("configuration must be a regular non-symlink file")
    resolved = path.resolve(strict=True)
    try:
        resolved.relative_to(project_root.resolve(strict=True))
    except ValueError as error:
        raise ConfigurationError("configuration path escapes the trusted project root") from error
    return resolved


def _resolve_paths(configuration: MemoryConfiguration, project_root: Path) -> dict[str, Path]:
    memory = configuration.memory
    paths = {
        "local_data": resolve_within(project_root, memory.local_data_dir, must_exist=False),
        "exact_index": resolve_within(project_root, memory.exact_index.path, must_exist=False),
        "model_cache": resolve_within(
            project_root, memory.models.model_cache_dir, must_exist=False
        ),
        "source_registry": resolve_within(project_root, memory.registries.sources),
        "profile_registry": resolve_within(project_root, memory.registries.profiles),
        "relation_registry": resolve_within(project_root, memory.registries.relations),
        "control_records": resolve_within(project_root, memory.control_records.root),
        "audit_log": resolve_within(
            project_root,
            memory.observability.local_audit_log,
            must_exist=False,
        ),
    }
    derived = paths["local_data"]
    if derived == project_root:
        raise ConfigurationError("derived memory must be below the project root")
    for name in ("exact_index", "model_cache", "audit_log"):
        if paths[name] == derived or not paths[name].is_relative_to(derived):
            raise ConfigurationError(f"{name} must be below the local derived-data boundary")
    return paths


def load_configuration(path: Path, *, trusted_project_root: Path) -> LoadedConfiguration:
    """Parse, strictly validate, and fingerprint a tracked configuration file."""

    if trusted_project_root.is_symlink():
        raise ConfigurationError("trusted project root must not be a symlink")
    project_root = trusted_project_root.resolve(strict=True)
    configuration_path = _regular_configuration_path(path, project_root)
    try:
        payload = tomllib.loads(configuration_path.read_text(encoding="utf-8"))
        configuration = MemoryConfiguration.model_validate(payload)
        resolved_paths = _resolve_paths(configuration, project_root)
    except (OSError, tomllib.TOMLDecodeError, ValidationError, ValueError) as error:
        if isinstance(error, ConfigurationError):
            raise
        raise ConfigurationError(str(error)) from error

    fingerprint = sha256_bytes(canonical_json_bytes(configuration.model_dump(mode="json")))
    return LoadedConfiguration(
        configuration=configuration,
        project_root=project_root,
        configuration_path=configuration_path,
        resolved_paths=resolved_paths,
        fingerprint=fingerprint,
    )
