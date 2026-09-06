from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

pytestmark = [pytest.mark.integration, pytest.mark.acceptance]

PRODUCT_ROOT = Path(__file__).parents[2]
GIT = shutil.which("git")
GREP = shutil.which("grep")
if GIT is None or GREP is None:
    raise RuntimeError("canonical portability checks require git and grep")
CANONICAL_FILES = (
    Path("PRDs/Sys4AI_Memory_Service_PRD.md"),
    Path("registries/memory_source_registry.csv"),
    Path("registries/memory_profile_registry.csv"),
    Path("registries/memory_relation_registry.csv"),
    Path("schemas/memory/memory-record.schema.json"),
)


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(  # noqa: S603 - executable and arguments are test-controlled
        (GIT, *args),
        cwd=root,
        check=True,
        capture_output=True,
        env={
            **os.environ,
            "GIT_AUTHOR_NAME": "Sys4AI portability fixture",
            "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
            "GIT_COMMITTER_NAME": "Sys4AI portability fixture",
            "GIT_COMMITTER_EMAIL": "fixture@example.invalid",
        },
    )


def test_canonical_memory_is_round_trip_readable_by_git_and_text_tools(
    tmp_path: Path,
) -> None:
    repository = (tmp_path / "canonical-memory").resolve()
    repository.mkdir()
    expected: dict[Path, bytes] = {}
    for relative in CANONICAL_FILES:
        source = PRODUCT_ROOT / relative
        destination = repository / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        expected[relative] = source.read_bytes()

    _git(repository, "init", "--quiet")
    _git(repository, "add", *(relative.as_posix() for relative in CANONICAL_FILES))
    _git(repository, "commit", "--quiet", "-m", "canonical memory fixture")

    for relative, original in expected.items():
        committed = _git(repository, "show", f"HEAD:{relative.as_posix()}").stdout
        assert committed == original
    requirement = subprocess.run(  # noqa: S603 - executable and arguments are fixed
        (GREP, "-F", "MEM-FR-001", "PRDs/Sys4AI_Memory_Service_PRD.md"),
        cwd=repository,
        check=True,
        capture_output=True,
    )
    assert b"MEM-FR-001" in requirement.stdout
    assert _git(repository, "status", "--porcelain").stdout == b""
