from __future__ import annotations

import csv
import json
import os
import shutil
import subprocess
import sys
from io import StringIO
from pathlib import Path

import pytest

from sys4ai_memory.cli import main
from sys4ai_memory.configuration import load_configuration
from sys4ai_memory.contracts import ErrorCategory
from sys4ai_memory.initialization import InitializationError, initialize_memory
from sys4ai_memory.interfaces import ControlAction, DispatchSuccess, InterfaceIdentity, MemoryClient
from sys4ai_memory.interfaces.dispatcher import ServiceDispatchFailure
from sys4ai_memory.providers import CogneeProviderConfig
from sys4ai_memory.runtime import LocalMemoryRuntime

PRODUCT = Path(__file__).parents[1]
PROJECT_ID = "fixture-consumer"


def consumer_root(tmp_path: Path) -> Path:
    root = tmp_path / "consumer"
    root.mkdir()
    for relative in ("registries", "profiles", "schemas"):
        shutil.copytree(PRODUCT / relative, root / relative)
    (root / "tests/golden_queries").mkdir(parents=True)
    shutil.copyfile(
        PRODUCT / "tests/golden_queries/queries.jsonl", root / "tests/golden_queries/queries.jsonl"
    )
    (root / "docs/architecture").mkdir(parents=True)
    shutil.copyfile(
        PRODUCT / "docs/architecture/system-architecture.md",
        root / "docs/architecture/system-architecture.md",
    )
    (root / "config").mkdir()
    config = (PRODUCT / "config/memory.toml").read_text()
    config = config.replace("sys4ai-memory-service", PROJECT_ID)
    config = config.replace(
        'default_memory_profile = "software-engineering@1"', 'default_memory_profile = "base@1"'
    )
    config = config.replace("semantic_enabled = true", "semantic_enabled = false")
    (root / "config/memory.toml").write_text(config)
    sources = root / "registries/memory_source_registry.csv"
    with sources.open(newline="") as stream:
        reader = csv.DictReader(stream)
        fields = reader.fieldnames
        rows = [row for row in reader if row["profile_id"] == "base@1"]
    marker_rule = next(row.copy() for row in rows if row["source_kind"] == "path_rule")
    marker_rule.update(
        source_id="src_FIXTURE_README", path_or_uri="README.md", path_pattern="", source_kind="file"
    )
    rows.append(marker_rule)
    assert fields is not None
    with sources.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fields)
        writer.writeheader()
        writer.writerows({**row, "project_id": PROJECT_ID} for row in rows)
    (root / "README.md").write_text("# Consumer\n\nThe EXACT_FIXTURE_MARKER is project-local.\n")
    (root / ".gitignore").write_text(".sys4ai/memory/\n.venv/\nmodels/\n.env\n.env.*\n")
    (root / "control_records/memory").mkdir(parents=True)
    (root / "control_records/memory/permissions.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "revision": "fixture-policy-1",
                "project_id": PROJECT_ID,
                "dataset_id": PROJECT_ID,
                "issued_at": "2026-09-04T18:00:00Z",
                "approval_policy": None,
                "grants": [
                    {
                        "grant_id": "fixture-owner",
                        "principal_id": "local-owner",
                        "permissions": ["read", "administer", "propose", "write-derived"],
                        "operations": [
                            "memory.initialize",
                            "memory.initialize.preview",
                            "memory.initialize.apply",
                            "memory.sync",
                            "memory.recall",
                            "memory.health",
                            "memory.get",
                            "memory.explain",
                            "memory.sources.list",
                        ],
                        "scopes": [
                            {"level": "project", "scope_id": PROJECT_ID, "parent_scopes": []}
                        ],
                        "target_prefixes": [],
                        "shared_project_ids": [],
                        "valid_until": None,
                    }
                ],
            }
        )
    )
    return root


def cli_arguments(root: Path, *command: str) -> tuple[str, ...]:
    return (
        "--project-root",
        str(root),
        "--project-id",
        PROJECT_ID,
        "--dataset-id",
        PROJECT_ID,
        "--principal-id",
        "local-owner",
        "--agent-type",
        "fixture-agent",
        "--run-id",
        "fixture-run",
        *command,
    )


def invoke(root: Path, *command: str) -> tuple[int, dict[str, object]]:
    output = StringIO()
    code = main(cli_arguments(root, *command), stdout=output)
    return code, json.loads(output.getvalue())


def test_real_cli_initializes_and_reopens_exact_state_across_processes(tmp_path: Path) -> None:
    root = consumer_root(tmp_path)
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "GIT_OPTIONAL_LOCKS": "0"}
    executable = os.environ.get("SYS4AI_MEMORY_TEST_EXECUTABLE")
    prefix = [executable] if executable else [sys.executable, "-m", "sys4ai_memory.cli"]
    for command in (
        ("init-memory", "--idempotency-key", "fixture-init"),
        ("sync", "--idempotency-key", "fixture-sync"),
        ("recall", "EXACT_FIXTURE_MARKER", "--mode", "exact"),
    ):
        completed = subprocess.run(  # noqa: S603 - fixed interpreter, bounded local fixture
            [*prefix, *cli_arguments(root, *command)],
            cwd=tmp_path,
            env=env,
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        assert completed.returncode == 0, completed.stdout + completed.stderr
        result = json.loads(completed.stdout)
    assert result["result"]["retrieval"]["results"]
    receipt = json.loads((root / ".sys4ai/memory/receipts/initialization.json").read_text())
    assert receipt["provider_initialized"] is False
    assert receipt["exact_index_initialized"] is True
    assert "preview" not in json.dumps(receipt)
    assert "impact_digest" not in receipt
    code, repeated = invoke(root, "sync", "--idempotency-key", "fixture-sync-again")
    assert code == 0, repeated
    assert repeated["result"]["document_count"] == 0


def test_direct_python_entry_never_builds_a_preview(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = consumer_root(tmp_path)

    def forbidden(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("direct initialization constructed a preview")

    monkeypatch.setattr("sys4ai_memory.service.dispatcher.build_initialization_preview", forbidden)
    client = MemoryClient(
        LocalMemoryRuntime(root),
        identity=InterfaceIdentity(principal_id="local-owner", agent_type="fixture", run_id="run"),
        project_id=PROJECT_ID,
        dataset_id=PROJECT_ID,
    )
    result = client.initialize(idempotency_key="python-init")
    assert isinstance(result, DispatchSuccess), result
    assert result.operation is ControlAction.INITIALIZE_DIRECT
    assert "preview" not in result.model_dump_json()
    assert "impact_digest" not in result.model_dump_json()


def test_invalid_identity_and_paths_fail_before_derived_writes(tmp_path: Path) -> None:
    root = consumer_root(tmp_path)
    arguments = tuple(
        "intruder" if item == "local-owner" else item
        for item in cli_arguments(root, "init-memory", "--idempotency-key", "denied-init")
    )
    output = StringIO()
    assert main(arguments, stdout=output) == 2
    assert (
        json.loads(output.getvalue())["error"]["category"] == ErrorCategory.PERMISSION_DENIED.value
    )
    assert not (root / ".sys4ai").exists()
    config = root / "config/memory.toml"
    config.write_text(
        config.read_text().replace(
            'path = ".sys4ai/memory/exact_index/index.sqlite3"', 'path = "README.md"'
        )
    )
    assert invoke(root, "init-memory", "--idempotency-key", "bad-path")[0] == 2
    assert not (root / ".sys4ai").exists()
    assert "EXACT_FIXTURE_MARKER" in (root / "README.md").read_text()


def test_legacy_digest_entry_still_uses_reviewed_apply(tmp_path: Path) -> None:
    root = consumer_root(tmp_path)
    code, preview = invoke(root, "init", "preview")
    assert code == 0, preview
    assert not (root / ".sys4ai").exists()
    digest = preview["result"]["preview"]["impact_digest"]
    assert (
        invoke(
            root, "init", "apply", "--impact-digest", "0" * 64, "--idempotency-key", "wrong-digest"
        )[0]
        == 2
    )
    assert not (root / ".sys4ai").exists()
    assert (
        invoke(
            root, "init", "apply", "--impact-digest", digest, "--idempotency-key", "reviewed-init"
        )[0]
        == 0
    )


def test_configured_provider_failure_is_explicit_and_publishes_no_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = consumer_root(tmp_path)
    config = root / "config/memory.toml"
    config.write_text(
        config.read_text().replace("semantic_enabled = false", "semantic_enabled = true")
    )
    observed: list[CogneeProviderConfig] = []

    def unavailable(configuration: CogneeProviderConfig) -> None:
        observed.append(configuration)
        assert configuration.resolved_model_cache_root == root / ".sys4ai/memory/models"
        raise ServiceDispatchFailure(ErrorCategory.PROVIDER_UNAVAILABLE)

    monkeypatch.setattr("sys4ai_memory.runtime.create_provider", unavailable)
    code, response = invoke(root, "init-memory", "--idempotency-key", "provider-failure")
    assert code == 2
    assert response["error"]["category"] == ErrorCategory.PROVIDER_UNAVAILABLE.value
    assert len(observed) == 1
    assert not (root / ".sys4ai/memory/receipts/initialization.json").exists()


@pytest.mark.parametrize("changed_project", [PROJECT_ID, "different-project"])
def test_initialized_folder_cannot_be_rebound_and_preserves_derived_files(
    tmp_path: Path, changed_project: str
) -> None:
    root = consumer_root(tmp_path)
    assert invoke(root, "init-memory", "--idempotency-key", "original-init")[0] == 0
    derived = root / ".sys4ai/memory"
    before = {
        item.relative_to(derived): item.read_bytes()
        for item in derived.rglob("*")
        if item.is_file()
    }
    config = root / "config/memory.toml"
    if changed_project == PROJECT_ID:
        config.write_text(
            config.read_text().replace("session_ttl_hours = 72", "session_ttl_hours = 73")
        )
    else:
        for relative in (
            "config/memory.toml",
            "registries/memory_source_registry.csv",
            "control_records/memory/permissions.json",
        ):
            item = root / relative
            item.write_text(item.read_text().replace(PROJECT_ID, changed_project))
    client = MemoryClient(
        LocalMemoryRuntime(root),
        identity=InterfaceIdentity(principal_id="local-owner", agent_type="fixture", run_id="run"),
        project_id=changed_project,
        dataset_id=changed_project,
    )
    response = client.initialize(idempotency_key="rebind-attempt")
    assert not isinstance(response, DispatchSuccess)
    assert response.error.category is ErrorCategory.CONFLICT_DETECTED
    after = {
        item.relative_to(derived): item.read_bytes()
        for item in derived.rglob("*")
        if item.is_file()
    }
    assert after == before


def test_malformed_existing_receipt_is_preserved_and_not_replaced(tmp_path: Path) -> None:
    root = consumer_root(tmp_path)
    assert invoke(root, "init-memory", "--idempotency-key", "original-init")[0] == 0
    receipt = root / ".sys4ai/memory/receipts/initialization.json"
    receipt.write_text("invalid receipt\n")
    code, response = invoke(root, "init-memory", "--idempotency-key", "invalid-retry")
    assert code == 2
    assert response["error"]["category"] == ErrorCategory.CONFLICT_DETECTED.value
    assert receipt.read_text() == "invalid receipt\n"


def _indexed_consumer(tmp_path: Path) -> tuple[Path, str]:
    root = consumer_root(tmp_path)
    assert invoke(root, "init-memory", "--idempotency-key", "read-init")[0] == 0
    assert invoke(root, "sync", "--idempotency-key", "read-sync")[0] == 0
    code, response = invoke(root, "recall", "EXACT_FIXTURE_MARKER", "--mode", "exact")
    assert code == 0, response
    return root, response["result"]["retrieval"]["results"][0]["record_id"]


def test_initialized_exact_reads_reread_only_returned_sources_without_discovery(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, record_id = _indexed_consumer(tmp_path)
    original_open = Path.open
    reads: list[Path] = []

    def source_open(self: Path, *args: object, **kwargs: object) -> object:
        if self == root / "README.md":
            reads.append(self)
        return original_open(self, *args, **kwargs)

    def forbidden(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("initialized exact reads must not rediscover all project sources")

    monkeypatch.setattr(Path, "open", source_open)
    monkeypatch.setattr("sys4ai_memory.sources.SourceDiscovery.discover", forbidden)
    for command in (
        ("recall", "EXACT_FIXTURE_MARKER", "--mode", "exact"),
        ("recall", "EXACT_FIXTURE_MARKER", "--mode", "lexical"),
        ("get", record_id),
        ("explain", record_id),
    ):
        before = len(reads)
        code, response = invoke(root, *command)
        assert code == 0, response
        assert len(reads) == before + 1


@pytest.mark.parametrize(
    "change", ["changed", "deleted", "revoked", "restricted", "foreign-registry"]
)
def test_current_exact_reads_reject_source_drift_without_discovery(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, change: str
) -> None:
    root, record_id = _indexed_consumer(tmp_path)
    if change == "changed":
        (root / "README.md").write_text("# Replaced source\n")
    elif change == "deleted":
        (root / "README.md").unlink()
    else:
        registry = root / "registries/memory_source_registry.csv"
        with registry.open(newline="") as stream:
            reader = csv.DictReader(stream)
            fields, rows = reader.fieldnames, list(reader)
        row = next(row for row in rows if row["source_id"] == "src_FIXTURE_README")
        field, value = {
            "revoked": ("include_flag", "false"),
            "restricted": ("sensitivity", "restricted"),
            "foreign-registry": ("project_id", "foreign-project"),
        }[change]
        row[field] = value
        assert fields is not None
        with registry.open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fields)
            writer.writeheader()
            writer.writerows(rows)

    def forbidden(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("current source verification must not perform full discovery")

    monkeypatch.setattr("sys4ai_memory.sources.SourceDiscovery.discover", forbidden)
    audit = root / ".sys4ai/memory/audit/events.jsonl"
    audit_before = audit.read_bytes()
    for command in (("recall", "EXACT_FIXTURE_MARKER", "--mode", "exact"), ("get", record_id)):
        code, response = invoke(root, *command)
        assert code == 2, response
        expected = {
            "changed": "INDEX_DRIFT",
            "deleted": "INDEX_DRIFT",
            "revoked": "SOURCE_EXCLUDED",
            "restricted": "INDEX_DRIFT",
            "foreign-registry": "AUTHORITY_VIOLATION",
        }[change]
        assert response["error"]["category"] == expected
        assert "EXACT_FIXTURE_MARKER" not in json.dumps(response)
    assert audit.read_bytes() == audit_before


@pytest.mark.parametrize("alter", ["configuration", "derived-symlink"])
def test_initialized_reads_keep_configuration_and_derived_path_guards(
    tmp_path: Path, alter: str
) -> None:
    root, _ = _indexed_consumer(tmp_path)
    outside = tmp_path / "outside.sqlite3"
    outside.write_bytes(b"protected outside fixture")
    if alter == "configuration":
        configuration = root / "config/memory.toml"
        configuration.write_text(
            configuration.read_text().replace("session_ttl_hours = 72", "session_ttl_hours = 73")
        )
    else:
        index = root / ".sys4ai/memory/exact_index/index.sqlite3"
        index.rename(index.with_suffix(".preserved"))
        index.symlink_to(outside)
    code, response = invoke(root, "recall", "EXACT_FIXTURE_MARKER", "--mode", "exact")
    assert code == 2
    assert response["error"]["category"] in {"MEMORY_NOT_INITIALIZED", "SCHEMA_INVALID"}
    assert outside.read_bytes() == b"protected outside fixture"


def test_explicit_history_stays_historical_after_current_source_changes(tmp_path: Path) -> None:
    root, _ = _indexed_consumer(tmp_path)
    source = root / "README.md"
    source.write_text(
        source.read_text().replace("EXACT_FIXTURE_MARKER", "REPLACEMENT_FIXTURE_MARKER")
    )
    assert invoke(root, "sync", "--idempotency-key", "history-sync")[0] == 0
    code, response = invoke(
        root, "recall", "EXACT_FIXTURE_MARKER", "--mode", "exact", "--include-history"
    )
    assert code == 0, response
    statuses = {
        record["lifecycle"]["status"] for record in response["result"]["retrieval"]["results"]
    }
    assert statuses == {"superseded"}


@pytest.mark.parametrize("semantic", [False, True])
def test_mutation_and_provider_paths_still_require_full_preflight(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, semantic: bool
) -> None:
    root = consumer_root(tmp_path)
    config = root / "config/memory.toml"
    if semantic:
        config.write_text(
            config.read_text().replace("semantic_enabled = false", "semantic_enabled = true")
        )
    loaded = load_configuration(config, trusted_project_root=root)
    initialize_memory(loaded, authorized=True)
    observed: list[str] = []

    def blocked(*_args: object, **_kwargs: object) -> object:
        observed.append("preflight")
        raise InitializationError("preflight failure fixture")

    def forbidden(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("provider activated before preflight")

    monkeypatch.setattr("sys4ai_memory.runtime.preflight_initialization", blocked)
    monkeypatch.setattr("sys4ai_memory.runtime.create_provider", forbidden)
    command = (
        ("recall", "fixture", "--mode", "semantic")
        if semantic
        else ("sync", "--idempotency-key", "preflight-guard")
    )
    code, response = invoke(root, *command)
    assert code == 2
    assert response["error"]["category"] == "CONFLICT_DETECTED"
    assert observed == ["preflight"]
