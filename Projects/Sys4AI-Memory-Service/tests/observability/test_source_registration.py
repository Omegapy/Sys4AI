from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from pathlib import Path

import pytest

from sys4ai_memory.authorization import PermissionDeniedError
from sys4ai_memory.bootstrap import prepare_project_memory
from sys4ai_memory.interfaces import DispatchSuccess, InterfaceIdentity, MemoryClient
from sys4ai_memory.runtime import LocalMemoryRuntime
from sys4ai_memory.security import JsonlAuditSink
from sys4ai_memory.source_registration import (
    SourceRegistrationError,
    register_reviewed_source,
)
from sys4ai_memory.sources import SourceDiscovery, load_source_registry
from sys4ai_memory.util import sha256_bytes


@pytest.fixture
def consumer(tmp_path: Path) -> Path:
    root = tmp_path / "consumer"
    root.mkdir()
    (root / "README.md").write_text("# Registration fixture\n")
    prepare_project_memory(
        root,
        "registration-fixture",
        "Registration Fixture",
        "owner",
        allow_source_registration=True,
    )
    client = MemoryClient(
        LocalMemoryRuntime(root),
        identity=InterfaceIdentity(
            principal_id="owner", agent_type="fixture", run_id="fixture-run"
        ),
        project_id="registration-fixture",
        dataset_id="registration-fixture-memory",
    )
    result = client.initialize(idempotency_key="fixture-initialization")
    assert isinstance(result, DispatchSuccess), result
    (root / "Verification").mkdir()
    (root / "Verification/source-review.md").write_text(
        "Owner review of bounded future project sources.\n"
    )
    (root / "Future").mkdir()
    (root / "Future/notes.md").write_text("# Future source\n\nREGISTERED_FUTURE_MARKER\n")
    (root / "Future/data.txt").write_text("This format is outside the reviewed rule.\n")
    (root / "Elsewhere").mkdir()
    (root / "Elsewhere/notes.md").write_text("Unrelated folder remains excluded.\n")
    return root


def data(**changes: object) -> dict[str, object]:
    return {
        "project_id": "registration-fixture",
        "dataset_id": "registration-fixture-memory",
        "source_id": "src_future_notes",
        "path": "Future",
        "file_pattern": "*.md",
        "recursive": True,
        "format": "markdown",
        "ingestion_adapter": "markdown",
        "namespace": "project:future",
        "canonicality": "canonical",
        "content_role": "project-knowledge",
        "authority_tier": "A3",
        "trust_class": "project-authored",
        "sensitivity": "internal",
        "retention_policy": "canonical",
        "write_policy": "deny",
        "owner": "owner",
        "relevance": "Reviewed project design notes",
        "chunking_profile": "heading-blocks@1",
        **changes,
    }


def registry(root: Path) -> Path:
    return root / "registries/memory_source_registry.csv"


def register(
    root: Path,
    reviewed: dict[str, object] | None = None,
    *,
    principal: str = "owner",
    expected: str | None = None,
) -> object:
    return register_reviewed_source(
        root,
        principal,
        reviewed or data(),
        review_reference="Verification/source-review.md",
        expected_registry_sha256=expected or sha256_bytes(registry(root).read_bytes()),
    )


def discover(root: Path) -> SourceDiscovery:
    return SourceDiscovery(
        project_root=root,
        project_id="registration-fixture",
        entries=load_source_registry(registry(root)),
    )


def audit_events(root: Path) -> list[dict[str, object]]:
    return [
        json.loads(line)
        for line in (root / ".sys4ai/memory/audit/events.jsonl").read_text().splitlines()
        if json.loads(line)["operation"] == "memory.sources.register"
    ]


def test_reviewed_registration_admits_only_eligible_folder_and_preserves_exclusions(
    consumer: Path,
) -> None:
    before = registry(consumer).read_bytes()
    excluded = [asdict(row) for row in load_source_registry(registry(consumer)) if row.is_exclusion]
    assert (
        discover(consumer).explain_path("Future/notes.md").reason.value == "default_deny_unmatched"
    )
    receipt = register(consumer)
    assert receipt.changed and receipt.admitted_paths == ("Future/notes.md",)
    assert registry(consumer).read_bytes().startswith(before)
    assert receipt.registry_sha256_before == sha256_bytes(before)
    assert receipt.registry_sha256_after == sha256_bytes(registry(consumer).read_bytes())
    assert receipt.audit_outcome == "succeeded"
    assert [
        asdict(row) for row in load_source_registry(registry(consumer)) if row.is_exclusion
    ] == excluded
    assert discover(consumer).explain_path("Future/notes.md").disposition.value == "included"
    assert (
        discover(consumer).explain_path("Future/data.txt").reason.value == "default_deny_unmatched"
    )
    assert (
        discover(consumer).explain_path("Elsewhere/notes.md").reason.value
        == "default_deny_unmatched"
    )
    events = audit_events(consumer)
    assert [event["outcome"] for event in events] == ["authorized", "succeeded"]
    assert "metadata_" + receipt.reviewed_metadata_sha256 in events[-1]["target_ids"]
    assert not any("REGISTERED_FUTURE_MARKER" in json.dumps(event) for event in events)


def test_equivalent_rerun_has_no_duplicate_or_registry_write(consumer: Path) -> None:
    register(consumer)
    before, mtime = registry(consumer).read_bytes(), registry(consumer).stat().st_mtime_ns
    receipt = register(consumer)
    assert not receipt.changed and receipt.registry_sha256_before == receipt.registry_sha256_after
    assert registry(consumer).read_bytes() == before
    assert registry(consumer).stat().st_mtime_ns == mtime
    assert (
        sum(row.source_id == "src_future_notes" for row in load_source_registry(registry(consumer)))
        == 1
    )


def test_another_folder_uses_same_data_driven_operation(consumer: Path) -> None:
    register(consumer)
    receipt = register(
        consumer, data(source_id="src_second_notes", path="Elsewhere", namespace="project:other")
    )
    assert receipt.changed and receipt.admitted_paths == ("Elsewhere/notes.md",)


def test_current_exclusion_inside_reviewed_folder_keeps_precedence(consumer: Path) -> None:
    (consumer / "Future/private.md").write_text("Explicitly excluded content.\n")
    with registry(consumer).open(newline="") as stream:
        reader = csv.DictReader(stream)
        fields = reader.fieldnames
        exclusion = next(row for row in reader if row["include_flag"] == "false")
    exclusion.update(
        source_id="src_private_exclusion", path_or_uri="", path_pattern="Future/private.md"
    )
    with registry(consumer).open("a", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writerow(exclusion)
    before = registry(consumer).read_bytes()
    receipt = register(consumer)
    assert receipt.admitted_paths == ("Future/notes.md",)
    assert registry(consumer).read_bytes().startswith(before)
    assert (
        discover(consumer).explain_path("Future/private.md").reason.value == "registered_exclusion"
    )


def test_concurrent_registration_uses_fresh_hash_under_shared_runtime_lock(consumer: Path) -> None:
    expected = sha256_bytes(registry(consumer).read_bytes())

    def attempt(payload: dict[str, object]) -> str:
        try:
            register(consumer, payload, expected=expected)
        except SourceRegistrationError as error:
            assert "changed since review" in str(error)
            return "stale"
        return "registered"

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(attempt, [data(), data(source_id="src_other", path="Elsewhere")]))
    assert sorted(outcomes) == ["registered", "stale"]
    assert (
        sum(
            row.source_id in {"src_future_notes", "src_other"}
            for row in load_source_registry(registry(consumer))
        )
        == 1
    )


@pytest.mark.parametrize(
    "relative",
    [
        "Projects/anything",
        ".sys4ai/memory/additional",
        ".venv",
        "venv",
        "env",
        "node_modules",
        "__pycache__",
        ".cache",
        ".pytest_cache",
        "models",
        ".cognee",
        ".cognee_system",
        "secrets",
        ".secrets",
        "staging",
        "tmp",
        "temp",
        "downloads",
        "exports",
        "logs",
        "raw-logs",
    ],
)
def test_forbidden_folder_classes_remain_refused(consumer: Path, relative: str) -> None:
    target = consumer / relative
    target.mkdir(parents=True, exist_ok=True)
    (target / "notes.md").write_text("Must remain excluded.\n")
    before = registry(consumer).read_bytes()
    with pytest.raises(SourceRegistrationError, match="protected"):
        register(consumer, data(path=relative))
    assert registry(consumer).read_bytes() == before


@pytest.mark.parametrize(
    "relative", [".env", ".envrc", "credentials.json", "local.key", "trace.log"]
)
def test_secret_and_raw_log_files_cannot_be_registered(consumer: Path, relative: str) -> None:
    (consumer / relative).write_text("Even harmless fixture content remains excluded.\n")
    before = registry(consumer).read_bytes()
    with pytest.raises(SourceRegistrationError, match="secret or generated"):
        register(consumer, data(path=relative, file_pattern=None, recursive=False))
    assert registry(consumer).read_bytes() == before


@pytest.mark.parametrize(
    "relative", ["../outside", "/absolute", "Future/../Elsewhere", "Future//notes.md"]
)
def test_unsafe_paths_fail_before_registry_changes(consumer: Path, relative: str) -> None:
    before = registry(consumer).read_bytes()
    with pytest.raises(ValueError):
        register(consumer, data(path=relative))
    assert registry(consumer).read_bytes() == before


@pytest.mark.parametrize("marker_kind", ["directory", "gitfile"])
def test_nested_git_ownership_is_refused(consumer: Path, marker_kind: str) -> None:
    marker = consumer / "Future/nested/.git"
    marker.parent.mkdir()
    if marker_kind == "directory":
        marker.mkdir()
    else:
        marker.write_text("gitdir: external-checkout\n")
    before = registry(consumer).read_bytes()
    with pytest.raises(SourceRegistrationError, match="independently owned"):
        register(consumer)
    assert registry(consumer).read_bytes() == before


def test_symlink_source_is_refused(consumer: Path) -> None:
    (consumer / "Future/alias.md").symlink_to(consumer / "Elsewhere/notes.md")
    before = registry(consumer).read_bytes()
    with pytest.raises(SourceRegistrationError, match="symlink"):
        register(consumer)
    assert registry(consumer).read_bytes() == before


@pytest.mark.parametrize(
    "field", ["owner", "relevance", "namespace", "format", "retention_policy", "write_policy"]
)
def test_required_metadata_cannot_be_omitted(consumer: Path, field: str) -> None:
    payload = data()
    del payload[field]
    before = registry(consumer).read_bytes()
    with pytest.raises(ValueError):
        register(consumer, payload)
    assert registry(consumer).read_bytes() == before


def test_wrong_principal_is_audited_and_cannot_read_candidate_content(
    consumer: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden(*args: object, **kwargs: object) -> object:
        pytest.fail("unauthorized caller reached candidate discovery")

    monkeypatch.setattr(SourceDiscovery, "discover", forbidden)
    before = registry(consumer).read_bytes()
    with pytest.raises(PermissionDeniedError):
        register(consumer, principal="intruder")
    assert registry(consumer).read_bytes() == before
    assert audit_events(consumer)[-1]["outcome"] == "denied"


def test_general_admin_without_action_specific_grant_cannot_register(consumer: Path) -> None:
    permission = consumer / "control_records/memory/permissions.json"
    payload = json.loads(permission.read_text())
    for grant in payload["grants"]:
        if "memory.sources.register" in grant["operations"]:
            grant["operations"] = []
    permission.write_text(json.dumps(payload))
    before = registry(consumer).read_bytes()
    with pytest.raises(PermissionDeniedError):
        register(consumer)
    assert registry(consumer).read_bytes() == before


def test_wrong_format_adapter_pair_fails_before_registry_replacement(consumer: Path) -> None:
    before = registry(consumer).read_bytes()
    with pytest.raises(SourceRegistrationError, match="format and adapter"):
        register(consumer, data(ingestion_adapter="json"))
    assert registry(consumer).read_bytes() == before


@pytest.mark.parametrize("changed", [{"project_id": "foreign"}, {"dataset_id": "foreign-memory"}])
def test_foreign_identity_is_refused(consumer: Path, changed: dict[str, str]) -> None:
    before = registry(consumer).read_bytes()
    with pytest.raises(SourceRegistrationError, match="different project or dataset"):
        register(consumer, data(**changed))
    assert registry(consumer).read_bytes() == before


def test_stale_hash_and_conflicting_identifier_fail(consumer: Path) -> None:
    old_hash = sha256_bytes(registry(consumer).read_bytes())
    register(consumer)
    before = registry(consumer).read_bytes()
    with pytest.raises(SourceRegistrationError, match="changed since review"):
        register(consumer, expected=old_hash)
    with pytest.raises(SourceRegistrationError, match="conflicts"):
        register(consumer, data(namespace="changed:policy"))
    with pytest.raises(SourceRegistrationError, match="conflicts"):
        register(consumer, data(source_id="src_duplicate_path"))
    assert registry(consumer).read_bytes() == before


def test_permission_revoked_after_authorized_audit_fails_before_publication(
    consumer: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = JsonlAuditSink.record
    permission = consumer / "control_records/memory/permissions.json"

    def revoke(sink: JsonlAuditSink, event: object) -> None:
        original(sink, event)
        if event.operation == "memory.sources.register" and event.outcome == "authorized":
            payload = json.loads(permission.read_text())
            payload["grants"] = []
            permission.write_text(json.dumps(payload))

    monkeypatch.setattr(JsonlAuditSink, "record", revoke)
    before = registry(consumer).read_bytes()
    with pytest.raises(PermissionDeniedError):
        register(consumer)
    assert registry(consumer).read_bytes() == before
    assert [event["outcome"] for event in audit_events(consumer)] == ["authorized", "failed"]


def test_uninitialized_consumer_does_not_create_derived_state(tmp_path: Path) -> None:
    prepare_project_memory(
        tmp_path,
        "registration-fixture",
        "Registration Fixture",
        "owner",
        allow_source_registration=True,
    )
    before = registry(tmp_path).read_bytes()
    with pytest.raises(SourceRegistrationError, match="requires initialized"):
        register(tmp_path)
    assert not (tmp_path / ".sys4ai").exists()
    assert registry(tmp_path).read_bytes() == before


@pytest.mark.parametrize("principal", ["owner", "ungranted-reviewer"])
def test_data_cli_exercises_same_registered_operation(consumer: Path, principal: str) -> None:
    payload = consumer / "Verification/registration.json"
    payload.write_text(json.dumps(data()))
    before = registry(consumer).read_bytes()
    process = subprocess.run(  # noqa: S603 - fixed interpreter and disposable consumer paths
        [
            sys.executable,
            "-m",
            "sys4ai_memory.source_registration",
            "--project-root",
            str(consumer),
            "--principal-id",
            principal,
            "--reviewed-source-json",
            str(payload),
            "--review-reference",
            "Verification/source-review.md",
            "--expected-registry-sha256",
            sha256_bytes(registry(consumer).read_bytes()),
        ],
        cwd=consumer,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "GIT_OPTIONAL_LOCKS": "0"},
    )
    result = json.loads(process.stdout)
    if principal == "owner":
        assert process.returncode == 0, process.stdout + process.stderr
        assert result["status"] == "registered"
        assert result["admitted_paths"] == ["Future/notes.md"]
    else:
        assert process.returncode == 2
        assert result["status"] == "failed"
        assert result["error_type"] == "PermissionDeniedError"
        assert not process.stderr
        assert registry(consumer).read_bytes() == before
    assert "cognee" not in sys.modules
