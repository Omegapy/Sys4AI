from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from sys4ai_memory.configuration import load_configuration
from sys4ai_memory.initialization import (
    InitializationError,
    apply_initialization,
    build_initialization_preview,
    initialize_memory,
)

SOURCE_ROOT = Path(__file__).parents[2]


def _active_root(tmp_path: Path) -> tuple[Path, Path]:
    root = tmp_path / "project"
    (root / "config").mkdir(parents=True)
    (root / "registries").mkdir()
    (root / "control_records/memory").mkdir(parents=True)
    for registry in SOURCE_ROOT.glob("registries/*.csv"):
        shutil.copyfile(registry, root / "registries" / registry.name)
    for relative in ("schemas", "profiles"):
        shutil.copytree(SOURCE_ROOT / relative, root / relative)
    (root / "docs/architecture").mkdir(parents=True)
    shutil.copyfile(
        SOURCE_ROOT / "docs/architecture/system-architecture.md",
        root / "docs/architecture/system-architecture.md",
    )
    text = (SOURCE_ROOT / "config/memory.toml").read_text(encoding="utf-8")
    replacements = {
        'configuration_status = "approved-local-profile-inactive-provider"': (
            'configuration_status = "active-test"'
        ),
    }
    for old, new in replacements.items():
        text = text.replace(old, new, 1)
    (root / "config/memory.toml").write_text(text, encoding="utf-8")
    return root, root / "config/memory.toml"


def test_preview_is_non_mutating_and_deterministic(tmp_path: Path) -> None:
    root, config = _active_root(tmp_path)
    loaded = load_configuration(config, trusted_project_root=root.resolve())
    first = build_initialization_preview(
        loaded,
        included_source_count=9,
        excluded_source_count=4,
    )
    second = build_initialization_preview(
        loaded,
        included_source_count=9,
        excluded_source_count=4,
    )
    assert first == second
    assert first.impact_digest == second.impact_digest
    assert not (root / ".sys4ai").exists()
    assert all(item.relative_path.startswith(".sys4ai/memory") for item in first.planned_paths)


def test_apply_requires_authorization_and_matching_digest(tmp_path: Path) -> None:
    root, config = _active_root(tmp_path)
    loaded = load_configuration(config, trusted_project_root=root.resolve())
    preview = build_initialization_preview(
        loaded,
        included_source_count=1,
        excluded_source_count=1,
    )
    with pytest.raises(InitializationError, match="authorization"):
        apply_initialization(
            loaded,
            preview,
            accepted_impact_digest=preview.impact_digest,
            authorized=False,
        )
    with pytest.raises(InitializationError, match="does not match"):
        apply_initialization(
            loaded,
            preview,
            accepted_impact_digest="0" * 64,
            authorized=True,
        )
    assert not (root / ".sys4ai").exists()


def test_apply_creates_only_private_derived_paths_and_receipt(tmp_path: Path) -> None:
    root, config = _active_root(tmp_path)
    loaded = load_configuration(config, trusted_project_root=root.resolve())
    preview = build_initialization_preview(
        loaded,
        included_source_count=2,
        excluded_source_count=3,
    )
    receipt = apply_initialization(
        loaded,
        preview,
        accepted_impact_digest=preview.impact_digest,
        authorized=True,
    )
    payload = json.loads(receipt.read_text(encoding="utf-8"))
    assert payload["provider_initialized"] is False
    assert payload["impact_digest"] == preview.impact_digest
    for item in preview.planned_paths:
        target = root / item.relative_path
        assert target.is_dir()
        assert target.stat().st_mode & 0o777 == 0o700
    assert not (root / ".cognee_system").exists()
    assert not (root / ".data_storage").exists()


def test_apply_rejects_symlinked_derived_root(tmp_path: Path) -> None:
    root, config = _active_root(tmp_path)
    loaded = load_configuration(config, trusted_project_root=root.resolve())
    preview = build_initialization_preview(
        loaded,
        included_source_count=1,
        excluded_source_count=1,
    )
    outside = tmp_path / "outside"
    outside.mkdir()
    (root / ".sys4ai").mkdir()
    (root / ".sys4ai/memory").symlink_to(outside, target_is_directory=True)
    with pytest.raises(InitializationError, match="symlink"):
        apply_initialization(
            loaded,
            preview,
            accepted_impact_digest=preview.impact_digest,
            authorized=True,
        )
    assert list(outside.iterdir()) == []


def test_direct_initialization_checks_authority_and_current_configuration(tmp_path: Path) -> None:
    root, config = _active_root(tmp_path)
    loaded = load_configuration(config, trusted_project_root=root.resolve())
    with pytest.raises(InitializationError, match="authorization"):
        initialize_memory(loaded, authorized=False)
    config.write_text(
        config.read_text().replace(
            'project_id = "sys4ai-memory-service"', 'project_id = "changed-project"'
        )
    )
    with pytest.raises(InitializationError, match="configuration changed"):
        initialize_memory(loaded, authorized=True)
    assert not (root / ".sys4ai").exists()


@pytest.mark.parametrize("stage", ["directories", "index", "provider", "receipt"])
def test_direct_failure_never_publishes_success_and_can_retry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, stage: str
) -> None:
    root, config = _active_root(tmp_path)
    loaded = load_configuration(config, trusted_project_root=root.resolve())
    canonical = config.read_bytes()

    def fail(*_args: object, **_kwargs: object) -> bool:
        raise OSError("injected initialization failure")

    targets = {
        "directories": "_mkdir_private",
        "index": "ExactIndex",
        "receipt": "atomic_write_text",
    }
    with monkeypatch.context() as scoped:
        if stage != "provider":
            scoped.setattr(f"sys4ai_memory.initialization.service.{targets[stage]}", fail)
        with pytest.raises(OSError, match="injected initialization failure"):
            initialize_memory(
                loaded,
                authorized=True,
                initialize_provider=fail if stage == "provider" else None,
            )
    assert config.read_bytes() == canonical
    assert not (root / ".sys4ai/memory/receipts/initialization.json").exists()
    receipt = initialize_memory(loaded, authorized=True)
    assert json.loads(receipt.read_text())["initialization_mode"] == "direct"
