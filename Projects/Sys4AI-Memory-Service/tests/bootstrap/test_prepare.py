from __future__ import annotations

import importlib
import io
import json
import os
import sys
from pathlib import Path

import pytest

from sys4ai_memory.authorization import (
    AuthorizationRequest,
    AuthorizationService,
    CanonicalPermissionEnvelopeLoader,
)
from sys4ai_memory.bootstrap import PreparationError, prepare_project_memory
from sys4ai_memory.bootstrap.__main__ import main as prepare_main
from sys4ai_memory.cli import main as memory_main
from sys4ai_memory.configuration import load_configuration
from sys4ai_memory.contracts import MemoryScope, Permission, ScopeReference
from sys4ai_memory.security import ProjectBoundary
from sys4ai_memory.sources import SourceDiscovery, load_registry_bundle


def snapshot(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }


def prepare(root: Path, **kwargs: object) -> object:
    return prepare_project_memory(
        root, "fixture-project", "Fixture Project", "fixture-owner", **kwargs
    )


def test_preparation_loads_configuration_registries_and_service_without_storage(
    tmp_path: Path,
) -> None:
    (tmp_path / "README.md").write_text("# Fixture Project\n\nFIXTURE_PREPARATION_MARKER\n")
    result = prepare_project_memory(tmp_path, "fixture-project", "Fixture Project", "fixture-owner")
    assert result.dataset_id == "fixture-project-memory"
    assert result.semantic_status == "deferred"
    assert not result.initialization_performed
    assert not (tmp_path / ".sys4ai").exists()
    assert "cognee" not in sys.modules
    loaded = load_configuration(tmp_path / result.configuration_path, trusted_project_root=tmp_path)
    assert loaded.configuration.memory.default_memory_profile == "base@1"
    assert not loaded.configuration.memory.models.semantic_enabled
    assert loaded.configuration.memory.models.profiles == ()
    assert loaded.resolved_paths["model_cache"] == tmp_path / ".sys4ai/memory/models"
    registry = load_registry_bundle(
        source_registry=loaded.resolved_paths["source_registry"],
        profile_registry=loaded.resolved_paths["profile_registry"],
        relation_registry=loaded.resolved_paths["relation_registry"],
        project_root=tmp_path,
    )
    assert {row.owner for row in registry.sources} == {"fixture-owner"}
    assert {row.project_id for row in registry.sources} == {"fixture-project"}
    assert {row.path_or_uri for row in registry.sources if row.include_flag} == {
        "AGENTS.md",
        "ROLE.md",
        "SOUL.md",
        "README.md",
    }
    output = io.StringIO()
    assert (
        memory_main(
            [
                "--project-root",
                str(tmp_path),
                "--project-id",
                result.project_id,
                "--dataset-id",
                result.dataset_id,
                "--principal-id",
                result.principal_id,
                "--agent-type",
                "fixture",
                "--run-id",
                "fixture-run",
                "health",
            ],
            stdout=output,
        )
        == 0
    ), output.getvalue()
    assert json.loads(output.getvalue())["operation"] == "memory.health"
    assert not (tmp_path / ".sys4ai").exists()


def test_future_paths_are_denied_even_after_they_exist(tmp_path: Path) -> None:
    prepare(tmp_path)
    for relative in ("later/notes.md", "Projects/other/README.md", ".sys4ai/memory/ignored.md"):
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("This source is not admitted.\n")
    loaded = load_configuration(tmp_path / "config/memory.toml", trusted_project_root=tmp_path)
    from sys4ai_memory.sources import load_source_registry

    discovery = SourceDiscovery(
        project_root=tmp_path,
        project_id="fixture-project",
        entries=load_source_registry(loaded.resolved_paths["source_registry"]),
    )
    for relative in ("later/notes.md", "Projects/other/README.md", ".sys4ai/memory/ignored.md"):
        decision = discovery.explain_path(relative)
        assert decision.disposition.value != "included"


def test_equivalent_retry_preserves_canonical_bytes_and_mtimes(tmp_path: Path) -> None:
    prepare(tmp_path)
    permission = tmp_path / "control_records/memory/permissions.json"
    permission.write_text(json.dumps(json.loads(permission.read_text()), sort_keys=True))
    config = tmp_path / "config/memory.toml"
    config.write_text("# Project-owned formatting\n" + config.read_text())
    before = snapshot(tmp_path)
    mtimes = {path: (tmp_path / path).stat().st_mtime_ns for path in before}
    result = prepare_project_memory(tmp_path, "fixture-project", "Fixture Project", "fixture-owner")
    assert result.created_files == () and result.updated_files == ()
    assert snapshot(tmp_path) == before
    assert {path: (tmp_path / path).stat().st_mtime_ns for path in before} == mtimes
    assert not (tmp_path / ".sys4ai").exists()


def test_existing_ignore_rules_are_preserved_and_final_exclusions_are_idempotent(
    tmp_path: Path,
) -> None:
    original = b"# Project rule\ncustom-generated/\n/.sys4ai/memory/\n!/.sys4ai/memory/\n"
    (tmp_path / ".gitignore").write_bytes(original)
    result = prepare_project_memory(tmp_path, "fixture-project", "Fixture Project", "fixture-owner")
    assert result.updated_files == (".gitignore",)
    effective = (tmp_path / ".gitignore").read_bytes()
    assert effective.startswith(original)
    assert effective.rfind(b"/.sys4ai/memory/\n") > effective.rfind(b"!/.sys4ai/memory/\n")
    prepare(tmp_path)
    assert (tmp_path / ".gitignore").read_bytes() == effective


@pytest.mark.parametrize(
    "relative",
    [
        "config/memory.toml",
        "profiles/base/profile.yaml",
        "registries/memory_source_registry.csv",
        "control_records/memory/permissions.json",
    ],
)
def test_conflicts_refuse_every_write(tmp_path: Path, relative: str) -> None:
    target = tmp_path / relative
    target.parent.mkdir(parents=True)
    target.write_text("Conflicting project-owned content\n")
    before = snapshot(tmp_path)
    with pytest.raises(PreparationError, match="conflicting canonical"):
        prepare(tmp_path)
    assert snapshot(tmp_path) == before
    assert not (tmp_path / ".sys4ai").exists()


@pytest.mark.parametrize(
    "changed",
    [
        {"project_id": "another-project"},
        {"project_name": "Another Project"},
        {"principal_id": "another-owner"},
        {"allow_source_registration": True},
    ],
)
def test_changed_identity_or_authority_refuses_existing_configuration(
    tmp_path: Path,
    changed: dict[str, object],
) -> None:
    prepare(tmp_path)
    before = snapshot(tmp_path)
    arguments = {
        "project_root": tmp_path,
        "project_id": "fixture-project",
        "project_name": "Fixture Project",
        "principal_id": "fixture-owner",
        **changed,
    }
    with pytest.raises(PreparationError, match="conflicting canonical"):
        prepare_project_memory(**arguments)
    assert snapshot(tmp_path) == before


@pytest.mark.parametrize(
    ("project_id", "project_name", "principal_id"),
    [
        ("../escape", "Project", "owner"),
        ("Uppercase", "Project", "owner"),
        ("project", "line\nbreak", "owner"),
        ("project", "", "owner"),
        ("project", "Project", "../other"),
        ("project", "Project", ""),
    ],
)
def test_invalid_identity_never_writes(
    tmp_path: Path,
    project_id: str,
    project_name: str,
    principal_id: str,
) -> None:
    with pytest.raises(PreparationError):
        prepare_project_memory(tmp_path, project_id, project_name, principal_id)
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("relative", ["config", ".gitignore", ".sys4ai"])
def test_symlink_destination_never_writes(tmp_path: Path, relative: str) -> None:
    root, outside = tmp_path / "project", tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    (root / relative).symlink_to(outside, target_is_directory=True)
    with pytest.raises(PreparationError, match="unsafe"):
        prepare(root)
    assert list(outside.iterdir()) == []
    assert [path.name for path in root.iterdir()] == [relative]


def test_relative_ancestor_symlink_and_hardlink_roots_are_rejected(tmp_path: Path) -> None:
    root = tmp_path / "project"
    root.mkdir()
    with pytest.raises(PreparationError, match="project_root"):
        prepare(Path("relative"))
    alias = tmp_path / "alias"
    alias.symlink_to(root, target_is_directory=True)
    with pytest.raises(PreparationError, match="project_root"):
        prepare(alias)
    child = root / "child"
    child.mkdir()
    with pytest.raises(PreparationError, match="project_root"):
        prepare(alias / "child")
    original = tmp_path / "shared-ignore"
    original.write_text("preserve\n")
    os.link(original, root / ".gitignore")
    with pytest.raises(PreparationError, match="regular file"):
        prepare(root)
    assert original.read_text() == "preserve\n"


def test_invalid_packaged_configuration_is_rejected_before_live_writes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = importlib.import_module("sys4ai_memory.bootstrap.prepare")
    original = module._render

    def invalid(relative: str, raw: str, substitutions: dict[str, str]) -> bytes:
        rendered = original(relative, raw, substitutions)
        if relative == "config/memory.toml":
            return rendered.replace(b'project_root = "."', b'project_root = ".."')
        return rendered

    monkeypatch.setattr(module, "_render", invalid)
    with pytest.raises(ValueError, match="project_root"):
        prepare(tmp_path)
    assert list(tmp_path.iterdir()) == []


def test_interrupted_publication_retries_without_overwriting_completed_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = importlib.import_module("sys4ai_memory.bootstrap.prepare")
    publish = module._publish_new_file

    def interrupted(root: Path, relative: str, data: bytes) -> None:
        if relative == "profiles/base/profile.yaml":
            raise OSError("fixture interruption")
        publish(root, relative, data)

    monkeypatch.setattr(module, "_publish_new_file", interrupted)
    with pytest.raises(OSError, match="fixture interruption"):
        prepare(tmp_path)
    before = snapshot(tmp_path)
    assert before and not (tmp_path / ".sys4ai").exists()
    monkeypatch.setattr(module, "_publish_new_file", publish)
    prepare(tmp_path)
    after = snapshot(tmp_path)
    assert all(after[path] == content for path, content in before.items())


def test_owner_grants_are_minimal_and_registration_requires_explicit_opt_in(tmp_path: Path) -> None:
    def authorizer(root: Path, registration: bool) -> AuthorizationService:
        root.mkdir()
        prepare_project_memory(
            root,
            "fixture-project",
            "Fixture Project",
            "fixture-owner",
            allow_source_registration=registration,
        )
        return AuthorizationService(
            CanonicalPermissionEnvelopeLoader(
                ProjectBoundary("fixture-project", "fixture-project-memory", root),
                "control_records/memory/permissions.json",
            )
        )

    narrow = authorizer(tmp_path / "narrow", False)
    reviewed = authorizer(tmp_path / "reviewed", True)
    scope = ScopeReference(level=MemoryScope.PROJECT, scope_id="fixture-project")

    def request(
        operation: str,
        permission: Permission,
        principal: str = "fixture-owner",
        target: str | None = None,
    ) -> AuthorizationRequest:
        return AuthorizationRequest(
            principal_id=principal,
            project_id="fixture-project",
            dataset_id="fixture-project-memory",
            operation=operation,
            permission=permission,
            scope=scope,
            trace_id="trc_fixture",
            target_path=target,
            require_action_specific=True,
        )

    assert narrow.evaluate(request("memory.health", Permission.READ)).allowed
    assert narrow.evaluate(request("memory.sync", Permission.WRITE_DERIVED)).allowed
    assert narrow.evaluate(
        request("memory.initialize", Permission.ADMINISTER, target="config/memory.toml")
    ).allowed
    assert not narrow.evaluate(request("memory.health", Permission.READ, "other-agent")).allowed
    assert not narrow.evaluate(request("memory.forget", Permission.ADMINISTER)).allowed
    registration = request(
        "memory.sources.register",
        Permission.ADMINISTER,
        target="registries/memory_source_registry.csv",
    )
    assert not narrow.evaluate(registration).allowed
    assert reviewed.evaluate(registration).allowed
    assert not reviewed.evaluate(
        request("memory.permissions.change", Permission.ADMINISTER)
    ).allowed


def test_cli_uses_same_preparation_and_reports_failure_without_sensitive_input(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    arguments = [
        "prepare",
        "--project-root",
        str(tmp_path),
        "--project-id",
        "fixture-project",
        "--project-name",
        "Fixture Project",
        "--principal-id",
        "fixture-owner",
    ]
    assert prepare_main(arguments) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "prepared" and result["semantic_status"] == "deferred"
    before = snapshot(tmp_path)
    assert prepare_main(arguments) == 0
    assert json.loads(capsys.readouterr().out)["created_files"] == []
    assert snapshot(tmp_path) == before
    arguments[arguments.index("fixture-project")] = "../invalid"
    assert prepare_main(arguments) == 2
    failed = capsys.readouterr().out
    assert "../invalid" not in failed and '"status": "failed"' in failed
