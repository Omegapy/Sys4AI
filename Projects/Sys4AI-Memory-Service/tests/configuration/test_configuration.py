from __future__ import annotations

from pathlib import Path

import pytest

from sys4ai_memory.configuration import (
    CapabilityBlocked,
    ConfigurationError,
    ModelRuntimeProfile,
    load_configuration,
)

PROJECT_ROOT = Path(__file__).parents[2]
CONFIGURATION = PROJECT_ROOT / "config/memory.toml"


def test_approved_local_configuration_load_is_side_effect_free_and_deterministic() -> None:
    generated = PROJECT_ROOT / ".sys4ai/memory"
    assert not generated.exists()
    first = load_configuration(CONFIGURATION, trusted_project_root=PROJECT_ROOT.resolve())
    second = load_configuration(CONFIGURATION, trusted_project_root=PROJECT_ROOT.resolve())
    assert first.fingerprint == second.fingerprint
    assert first.configuration.memory.provider.version_constraint == "==1.5.3"
    assert first.configuration.memory.enabled is True
    assert first.configuration.memory.provider.initialize_on_load is False
    assert first.configuration.memory.exact_index.enabled is True
    assert first.configuration.memory.models.semantic_enabled is True
    assert first.configuration.memory.control_records.approvals_required == 1
    assert first.configuration.memory.control_records.self_approval_allowed is False
    assert first.configuration.memory.retention.session_ttl_hours == 72
    assert first.configuration.memory.retention.episodic_ttl_days == 365
    assert first.configuration.memory.export.encryption == "age-x25519"
    assert first.configuration.memory.shared.enabled is False
    assert first.configuration.memory.security.destructive_execution_enabled is False
    assert first.configuration.memory.models.allow_cloud_fallback is False
    assert first.gate("health").ready is True
    assert first.gate("dry_run").ready is True
    assert not generated.exists()


def test_index_affecting_configuration_change_updates_fingerprint(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    for relative in (
        "registries/memory_source_registry.csv",
        "registries/memory_profile_registry.csv",
        "registries/memory_relation_registry.csv",
        "control_records/memory/README.md",
    ):
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("fixture\n", encoding="utf-8")
    candidate = root / "config/memory.toml"
    candidate.parent.mkdir(parents=True)
    original = CONFIGURATION.read_text(encoding="utf-8")
    candidate.write_text(original, encoding="utf-8")
    first = load_configuration(candidate, trusted_project_root=root)

    candidate.write_text(
        original.replace(
            'default_memory_profile = "software-engineering@1"',
            'default_memory_profile = "base@1"',
        ),
        encoding="utf-8",
    )
    changed = load_configuration(candidate, trusted_project_root=root)

    assert changed.fingerprint != first.fingerprint


@pytest.mark.parametrize(
    "capability",
    [
        "exact",
        "semantic",
        "approve",
        "session",
        "episodic",
        "export",
        "feedback",
    ],
)
def test_approved_local_capabilities_are_ready(capability: str) -> None:
    loaded = load_configuration(CONFIGURATION, trusted_project_root=PROJECT_ROOT.resolve())
    assert loaded.gate(capability).ready is True
    loaded.require(capability)


@pytest.mark.parametrize(
    ("capability", "expected_issue"),
    [
        ("shared", "shared backend decision is pending"),
        ("network", "network listener is disabled"),
        ("forget", "destructive execution is disabled"),
    ],
)
def test_deliberately_disabled_capability_fails_closed(
    capability: str, expected_issue: str
) -> None:
    loaded = load_configuration(CONFIGURATION, trusted_project_root=PROJECT_ROOT.resolve())
    gate = loaded.gate(capability)
    assert gate.ready is False
    if capability == "shared":
        assert "shared mode is disabled" in gate.issues
    else:
        assert expected_issue in gate.issues
    with pytest.raises(CapabilityBlocked, match="blocked"):
        loaded.require(capability)


def test_unknown_key_is_rejected(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    (root / "config").mkdir()
    candidate = root / "config/memory.toml"
    candidate.write_text(CONFIGURATION.read_text() + "\nunknown = true\n", encoding="utf-8")
    with pytest.raises(ConfigurationError, match="unknown"):
        load_configuration(candidate, trusted_project_root=root)


@pytest.mark.parametrize(
    ("original", "replacement"),
    [
        ('path = ".sys4ai/memory/exact_index/index.sqlite3"', 'path = "exact.sqlite3"'),
        ('model_cache_dir = ".sys4ai/memory/models"', 'model_cache_dir = "models"'),
        ('local_audit_log = ".sys4ai/memory/audit/events.jsonl"',
         'local_audit_log = "audit/events.jsonl"'),
    ],
)
def test_derived_paths_cannot_escape_memory_boundary(
    tmp_path: Path, original: str, replacement: str
) -> None:
    root = tmp_path.resolve()
    for relative in (
        "registries/memory_source_registry.csv",
        "registries/memory_profile_registry.csv",
        "registries/memory_relation_registry.csv",
        "control_records/memory/README.md",
    ):
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("fixture\n", encoding="utf-8")
    candidate = root / "config/memory.toml"
    candidate.parent.mkdir()
    text = CONFIGURATION.read_text(encoding="utf-8")
    assert original in text
    candidate.write_text(text.replace(original, replacement), encoding="utf-8")
    with pytest.raises(ConfigurationError, match="local derived-data boundary"):
        load_configuration(candidate, trusted_project_root=root)
    assert not (root / ".sys4ai").exists()


def test_configuration_must_be_inside_trusted_root(tmp_path: Path) -> None:
    with pytest.raises(ConfigurationError, match="escapes"):
        load_configuration(CONFIGURATION, trusted_project_root=tmp_path.resolve())


def test_symlinked_configuration_is_rejected(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    (root / "config").mkdir()
    target = root / "real.toml"
    target.write_text(CONFIGURATION.read_text(), encoding="utf-8")
    link = root / "config/memory.toml"
    link.symlink_to(target)
    with pytest.raises(ConfigurationError, match="non-symlink"):
        load_configuration(link, trusted_project_root=root)


def test_symlinked_project_root_is_rejected(tmp_path: Path) -> None:
    root = tmp_path / "project"
    (root / "config").mkdir(parents=True)
    candidate = root / "config/memory.toml"
    candidate.write_text(CONFIGURATION.read_text(), encoding="utf-8")
    link = tmp_path / "project-link"
    link.symlink_to(root, target_is_directory=True)
    with pytest.raises(ConfigurationError, match="root must not be a symlink"):
        load_configuration(candidate, trusted_project_root=link)


def test_configuration_represents_local_and_remote_model_profiles_without_side_effects(
    tmp_path: Path,
) -> None:
    root = tmp_path.resolve()
    for relative in (
        "registries/memory_source_registry.csv",
        "registries/memory_profile_registry.csv",
        "registries/memory_relation_registry.csv",
        "control_records/memory/README.md",
    ):
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("fixture\n", encoding="utf-8")
    candidate = root / "config/memory.toml"
    candidate.parent.mkdir(parents=True)
    candidate.write_text(
        CONFIGURATION.read_text(encoding="utf-8")
        + """

[[memory.models.profiles]]
profile_id = "local-llm@1"
capability = "llm"
locality = "local"
provider = "ollama"
model = "local-generation-model"
endpoint = "http://127.0.0.1:11434/v1"

[[memory.models.profiles]]
profile_id = "remote-llm@1"
capability = "llm"
locality = "remote"
provider = "openai-compatible"
model = "remote-generation-model"
endpoint = "https://models.example.invalid/v1"
credential_reference = "managed-secret:sys4ai/remote-llm"

[[memory.models.profiles]]
profile_id = "local-embedding@1"
capability = "embedding"
locality = "local"
provider = "fastembed"
model = "local-embedding-model"
dimensions = 384

[[memory.models.profiles]]
profile_id = "remote-embedding@1"
capability = "embedding"
locality = "remote"
provider = "openai-compatible"
model = "remote-embedding-model"
endpoint = "https://embeddings.example.invalid/v1"
dimensions = 1536
credential_reference = "keychain:sys4ai/remote-embedding"
""",
        encoding="utf-8",
    )

    loaded = load_configuration(candidate, trusted_project_root=root)

    profiles = loaded.configuration.memory.models.profiles
    assert len(profiles) == 6
    assert loaded.configuration.memory.models.profile("local-llm@1") is not None
    assert loaded.configuration.memory.models.profile("local-llm@1").locality == "local"  # type: ignore[union-attr]
    assert (
        loaded.configuration.memory.models.profile("remote-llm@1").credential_reference  # type: ignore[union-attr]
        == "managed-secret:sys4ai/remote-llm"
    )
    assert loaded.configuration.memory.models.profile("local-embedding@1").dimensions == 384  # type: ignore[union-attr]
    assert loaded.configuration.memory.models.semantic_enabled is True
    assert loaded.configuration.memory.models.allow_remote is False


@pytest.mark.parametrize(
    ("values", "message"),
    [
        (
            {
                "profile_id": "remote-http@1",
                "capability": "llm",
                "locality": "remote",
                "provider": "remote",
                "model": "model",
                "endpoint": "http://models.example.invalid/v1",
                "credential_reference": "managed-secret:model",
            },
            "HTTPS endpoint",
        ),
        (
            {
                "profile_id": "inline-secret@1",
                "capability": "llm",
                "locality": "remote",
                "provider": "remote",
                "model": "model",
                "endpoint": "https://user:value@models.example.invalid/v1",
                "credential_reference": "managed-secret:model",
            },
            "embedded credentials",
        ),
        (
            {
                "profile_id": "local-credential@1",
                "capability": "llm",
                "locality": "local",
                "provider": "ollama",
                "model": "model",
                "endpoint": "http://127.0.0.1:11434/v1",
                "credential_reference": "environment:MODEL_KEY",
            },
            "local model profiles cannot require",
        ),
        (
            {
                "profile_id": "embedding-no-dimensions@1",
                "capability": "embedding",
                "locality": "local",
                "provider": "fastembed",
                "model": "model",
            },
            "require dimensions",
        ),
    ],
)
def test_model_profile_contract_rejects_unsafe_or_incomplete_profiles(
    values: dict[str, object],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        ModelRuntimeProfile.model_validate(values)


def test_semantic_configuration_requires_both_selected_profiles_in_the_catalog() -> None:
    loaded = load_configuration(CONFIGURATION, trusted_project_root=PROJECT_ROOT.resolve())
    values = loaded.configuration.memory.models.model_dump()
    values["profiles"] = ()
    with pytest.raises(ValueError, match="registered llm profile"):
        type(loaded.configuration.memory.models).model_validate(values)


def test_network_configuration_rejects_a_no_auth_listener() -> None:
    loaded = load_configuration(CONFIGURATION, trusted_project_root=PROJECT_ROOT.resolve())
    values = loaded.configuration.memory.service.model_dump()
    values.update(
        {
            "transport": "http",
            "network_listener_enabled": True,
            "authentication_posture": "no-auth-development",
        }
    )
    with pytest.raises(ValueError, match="authenticated posture"):
        type(loaded.configuration.memory.service).model_validate(values)
