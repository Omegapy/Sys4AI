"""Opt-in installed-wheel and real-adapter isolation checks for two consumers."""

from __future__ import annotations

import hashlib
import json
import os
import stat
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from tools.build_consumer_artifact import install_artifact, verify_artifact

pytestmark = [pytest.mark.integration, pytest.mark.security, pytest.mark.acceptance]
PRODUCT_ROOT = Path(__file__).parents[2]
PROBE = Path(__file__).parent / "consumer_bootstrap_fixtures/provider_probe.py"


def _metadata(root: Path) -> dict[str, dict[str, int]]:
    """Observe names/stat metadata only; never read user-wide Cognee content."""
    if not root.exists() and not root.is_symlink():
        return {}
    candidates = [root]
    if root.is_dir() and not root.is_symlink():
        for directory, subdirectories, files in os.walk(root, followlinks=False):
            candidates.extend(Path(directory) / name for name in (*subdirectories, *files))
    return {
        candidate.relative_to(root).as_posix(): {
            "mode": metadata.st_mode,
            "size": metadata.st_size,
            "mtime_ns": metadata.st_mtime_ns,
            "ctime_ns": metadata.st_ctime_ns,
            "device": metadata.st_dev,
            "inode": metadata.st_ino,
        }
        for candidate in sorted(set(candidates))
        for metadata in (candidate.lstat(),)
    }


def _manifest(root: Path) -> dict[str, dict[str, Any]]:
    manifest = {}
    for candidate in sorted((root / ".sys4ai/memory").rglob("*")):
        metadata = candidate.lstat()
        assert not stat.S_ISLNK(metadata.st_mode)
        manifest[candidate.relative_to(root).as_posix()] = {
            "kind": "file" if candidate.is_file() else "directory",
            "mode": oct(stat.S_IMODE(metadata.st_mode)),
            "size": metadata.st_size,
            "device": metadata.st_dev,
            "inode": metadata.st_ino,
            "sha256": hashlib.sha256(candidate.read_bytes()).hexdigest()
            if candidate.is_file()
            else None,
        }
    return manifest


def _run(arguments: list[str], *, cwd: Path, expected: int = 0) -> dict[str, Any]:
    environment = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "GIT_OPTIONAL_LOCKS": "0"}
    environment.pop("PYTHONPATH", None)
    completed = subprocess.run(  # noqa: S603 - explicit local programs and disposable fixture roots
        arguments,
        cwd=cwd,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    try:
        result = json.loads(completed.stdout)
    except json.JSONDecodeError:
        # The provider may print non-sensitive startup messages. Retain its final
        # structured result rather than copying native output into evidence.
        result = json.loads(completed.stdout.splitlines()[-1])
    assert completed.returncode == expected, {
        "returncode": completed.returncode,
        "result": result,
        "stderr_characters": len(completed.stderr),
    }
    return result


def _arguments(
    root: Path, project_id: str, *command: str, dataset_id: str | None = None
) -> list[str]:
    return [
        str(root / ".venv/bin/sys4ai-memory"),
        "--project-root",
        str(root),
        "--project-id",
        project_id,
        "--dataset-id",
        dataset_id or project_id + "-memory",
        "--principal-id",
        "isolation-owner",
        "--agent-type",
        "isolation-check",
        "--run-id",
        "two-project-probe",
        *command,
    ]


def _prepare(python: Path, root: Path, project_id: str) -> dict[str, Any]:
    return _run(
        [
            str(python),
            "-I",
            "-m",
            "sys4ai_memory.bootstrap",
            "prepare",
            "--project-root",
            str(root),
            "--project-id",
            project_id,
            "--project-name",
            "Disposable " + project_id,
            "--principal-id",
            "isolation-owner",
        ],
        cwd=root,
    )


@pytest.fixture(scope="module")
def consumers(tmp_path_factory: pytest.TempPathFactory) -> Iterator[dict[str, Any]]:
    selected = os.environ.get("SYS4AI_CONSUMER_ARTIFACT")
    if not selected:
        pytest.skip("Set SYS4AI_CONSUMER_ARTIFACT to permit two disposable locked installations")
    artifact_path = Path(selected)
    artifact = verify_artifact(artifact_path)
    base = tmp_path_factory.mktemp("consumer-isolation").resolve()
    user_cognee = Path.home() / ".cognee"
    before = _metadata(user_cognee)
    evidence: dict[str, Any] = {
        "artifact_receipt": str(artifact_path),
        "wheel_sha256": artifact["wheel"]["sha256"],
        "source_manifest_sha256": artifact["source_manifest_sha256"],
        "projects": [],
        "user_cognee_before": before,
        "base": str(base),
    }
    try:
        for project_id in ("isolation-alpha", "isolation-beta"):
            root = base / project_id
            root.mkdir()
            installed = install_artifact(artifact_path, root, python=Path(sys.executable))
            assert installed["wheel_sha256"] == artifact["wheel"]["sha256"]
            assert installed["dependency_profile"] == "core"
            assert "cognee" not in {
                name.casefold() for name in installed["observed"]["dependencies"]
            }
            assert Path(installed["observed"]["origin"]).is_relative_to(root / ".venv")
            assert (
                installed["observed"]["direct_url"].get("dir_info", {}).get("editable") is not True
            )
            assert not installed["observed"]["provider_imported"]
            assert not (root / ".sys4ai").exists()
            marker = project_id.upper().replace("-", "_") + "_UNIQUE_MARKER"
            (root / "README.md").write_text(
                f"# {project_id}\n\n`{marker}` belongs to this project.\n"
            )
            prepared = _prepare(root / ".venv/bin/python", root, project_id)
            assert prepared["initialization_performed"] is False
            assert prepared["dataset_id"] == project_id + "-memory"
            assert not (root / ".sys4ai").exists()
            assert not (root / "src").exists()
            evidence["projects"].append(
                {
                    "project_id": project_id,
                    "dataset_id": prepared["dataset_id"],
                    "root": str(root),
                    "marker": marker,
                    "installed": installed,
                }
            )
        yield evidence
    finally:
        after = _metadata(user_cognee)
        evidence["user_cognee_after"] = after
        evidence["user_cognee_unchanged"] = before == after
        for project in evidence["projects"]:
            project["derived_manifest"] = _manifest(Path(project["root"]))
        (base / "consumer-isolation-evidence.json").write_text(
            json.dumps(evidence, indent=2, sort_keys=True)
        )
        assert after == before, "User-wide Cognee metadata changed during confined checks"


def test_installed_consumers_keep_bootstrap_and_exact_recall_isolated(
    consumers: dict[str, Any],
) -> None:
    projects = consumers["projects"]
    for own, other in ((projects[0], projects[1]), (projects[1], projects[0])):
        root = Path(own["root"])
        initialized = _run(
            _arguments(
                root, own["project_id"], "init-memory", "--idempotency-key", "direct-isolation-init"
            ),
            cwd=root,
        )
        assert "preview" not in json.dumps(initialized)
        assert "impact_digest" not in json.dumps(initialized)
        receipt = initialized["result"]["initialization"]
        assert receipt["project_id"] == own["project_id"]
        assert receipt["dataset_id"] == own["dataset_id"]
        assert receipt["exact_index_initialized"] is True
        assert receipt["provider_initialized"] is False
        assert receipt["models_activated"] is False
        synchronized = _run(
            _arguments(
                root, own["project_id"], "sync", "--idempotency-key", "direct-isolation-sync"
            ),
            cwd=root,
        )
        assert synchronized["result"]["failure_count"] == 0
        own_result = _run(
            _arguments(root, own["project_id"], "recall", own["marker"], "--mode", "exact"),
            cwd=root,
        )
        other_result = _run(
            _arguments(root, own["project_id"], "recall", other["marker"], "--mode", "exact"),
            cwd=root,
        )
        assert own_result["result"]["retrieval"]["results"]
        assert other_result["result"]["retrieval"]["results"] == []
        before = _manifest(root)
        for crossed_project, crossed_dataset in (
            (other["project_id"], other["dataset_id"]),
            (own["project_id"], other["dataset_id"]),
        ):
            rejected = _run(
                _arguments(
                    root,
                    crossed_project,
                    "recall",
                    other["marker"],
                    "--mode",
                    "exact",
                    dataset_id=crossed_dataset,
                ),
                cwd=root,
                expected=2,
            )
            assert rejected["error"]["category"] in {"PERMISSION_DENIED", "AUTHORITY_VIOLATION"}
        assert _manifest(root) == before
        assert (root / ".sys4ai/memory").stat().st_mode & 0o077 == 0
        assert all(int(item["mode"], 8) & 0o077 == 0 for item in before.values())
        own["direct_bootstrap"] = receipt
        own["exact_own_count"] = len(own_result["result"]["retrieval"]["results"])
        own["exact_other_count"] = 0
        own["crossed_contexts_rejected"] = 2
        own["bootstrap_manifest"] = before
    inodes = [
        {(item["device"], item["inode"]) for item in project["bootstrap_manifest"].values()}
        for project in projects
    ]
    assert inodes[0].isdisjoint(inodes[1])

    # A third disposable directory reuses the first installed executable only;
    # invalid storage configuration must fail before any committed derived state.
    failed_root = Path(consumers["base"]) / "invalid-storage"
    failed_root.mkdir()
    _prepare(Path(projects[0]["root"]) / ".venv/bin/python", failed_root, "invalid-storage")
    config = failed_root / "config/memory.toml"
    config.write_text(
        config.read_text().replace(
            'path = ".sys4ai/memory/exact_index/index.sqlite3"', 'path = "config/memory.toml"'
        )
    )
    preserved = config.read_bytes()
    arguments = _arguments(
        failed_root, "invalid-storage", "init-memory", "--idempotency-key", "invalid-init"
    )
    arguments[0] = str(Path(projects[0]["root"]) / ".venv/bin/sys4ai-memory")
    _run(arguments, cwd=failed_root, expected=2)
    assert config.read_bytes() == preserved
    assert not (failed_root / ".sys4ai").exists()
    consumers["prewrite_failure_preserved"] = True


@pytest.mark.cognee
def test_real_adapter_initializes_each_project_without_shared_paths_or_network(
    consumers: dict[str, Any],
) -> None:
    observed = []
    for project in consumers["projects"]:
        root = Path(project["root"])
        if not (root / ".sys4ai/memory/receipts/initialization.json").exists():
            _run(
                _arguments(
                    root,
                    project["project_id"],
                    "init-memory",
                    "--idempotency-key",
                    "provider-probe-init",
                ),
                cwd=root,
            )
        result = _run(
            [
                str(PRODUCT_ROOT / ".venv/bin/python"),
                str(PROBE),
                str(root),
                project["project_id"],
                project["dataset_id"],
            ],
            cwd=root,
        )
        assert result["status"] == "passed"
        assert result["project_id"] == project["project_id"]
        assert result["dataset_id"] == project["dataset_id"]
        assert result["crossed_dataset_error"] in {"AUTHORITY_VIOLATION", "PERMISSION_DENIED"}
        assert result["unexpected_network_attempts"] == 0
        assert result["allowed_network_actions"] == 0
        assert result["blocked_ipv6_capability_probes"] in (0, 1)
        assert result["outside_write_attempts"] == 0
        assert result["model_files"] == 0
        assert int(result["private_memory_ancestor_mode"], 8) & 0o077 == 0
        for database in result["databases"]:
            assert Path(database["path"]).is_relative_to(root / ".sys4ai/memory")
        project["provider_probe"] = result
        observed.append(result)
    assert observed[0]["pid"] != observed[1]["pid"]
    assert observed[0]["dataset_id"] != observed[1]["dataset_id"]
    for key in ("log_root", "model_root"):
        assert observed[0][key] != observed[1][key]
    assert {item["path"] for item in observed[0]["databases"]}.isdisjoint(
        item["path"] for item in observed[1]["databases"]
    )
