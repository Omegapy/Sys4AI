"""Provider protocol, configuration, lazy factory, and code-isolation checks."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

from sys4ai_memory.providers import (
    CogneeProviderConfig,
    InMemoryProviderConfig,
    MemoryProvider,
    ProviderName,
    create_provider,
)


def test_factory_creates_conforming_in_memory_provider_without_cognee_import() -> None:
    was_loaded = "cognee" in sys.modules
    provider = create_provider(
        InMemoryProviderConfig(project_id="project-alpha", dataset_id="project-alpha-memory")
    )

    assert isinstance(provider, MemoryProvider)
    assert provider.provider_name is ProviderName.IN_MEMORY
    assert ("cognee" in sys.modules) is was_loaded


def test_cognee_config_is_local_exact_and_deny_safe(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    data_root = project_root / ".sys4ai" / "memory"
    config = CogneeProviderConfig(
        project_id="project-alpha",
        dataset_id="project-alpha-memory",
        project_root=str(project_root),
        derived_data_root=str(data_root),
    )

    assert config.expected_version == "1.5.3"
    assert config.version_constraint == "==1.5.3"
    assert config.initialize_on_load is False
    assert config.allow_native_client_access is False
    assert config.allow_remote is False
    assert config.allow_cloud_fallback is False
    assert config.telemetry_enabled is False
    assert config.resolved_model_cache_root == data_root / "models"

    was_loaded = "cognee" in sys.modules
    provider = create_provider(config)
    assert provider.provider_name is ProviderName.COGNEE
    assert ("cognee" in sys.modules) is was_loaded


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"project_root": ".", "derived_data_root": ".data"}, "absolute"),
        ({"dataset_id": "main_dataset"}, "default dataset"),
        (
            {"derived_data_root": "/var/empty/sys4ai-provider-outside"},
            "below the project root",
        ),
        ({"semantic_enabled": True}, "explicit local model profiles"),
        (
            {
                "semantic_enabled": True,
                "llm_provider": "ollama",
                "llm_model": "local-model",
                "llm_endpoint": "https://remote.example.test",
                "embedding_provider": "fastembed",
                "embedding_model": "local-embedding",
                "embedding_dimensions": 384,
            },
            "loopback",
        ),
    ],
)
def test_cognee_config_rejects_unsafe_profiles(
    tmp_path: Path, overrides: dict[str, object], message: str
) -> None:
    project_root = tmp_path / "project"
    values: dict[str, object] = {
        "project_id": "project-alpha",
        "dataset_id": "project-alpha-memory",
        "project_root": str(project_root),
        "derived_data_root": str(project_root / ".sys4ai" / "memory"),
    }
    values.update(overrides)
    with pytest.raises(ValidationError, match=message):
        CogneeProviderConfig.model_validate(values)


def test_only_the_cognee_adapter_may_import_the_cognee_distribution() -> None:
    package_root = Path(__file__).parents[2] / "src" / "sys4ai_memory"
    violations: list[str] = []
    for path in package_root.rglob("*.py"):
        if path == package_root / "providers/cognee.py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import) and any(
                alias.name == "cognee" or alias.name.startswith("cognee.")
                for alias in node.names
            ):
                violations.append(str(path))
            if isinstance(node, ast.ImportFrom) and node.module is not None and (
                node.module == "cognee" or node.module.startswith("cognee.")
            ):
                violations.append(str(path))

    assert violations == []


def test_model_cache_requires_a_private_derived_path(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    values = {
        "project_id": "project-alpha",
        "dataset_id": "project-alpha-memory",
        "project_root": str(root),
        "derived_data_root": str(root / ".sys4ai/memory"),
    }
    with pytest.raises(ValidationError, match="below the derived-data root"):
        CogneeProviderConfig(**values, model_cache_root=str(root / "models"))
    custom = root / ".sys4ai/memory/private-models"
    configured = CogneeProviderConfig(**values, model_cache_root=str(custom))
    assert configured.resolved_model_cache_root == custom
