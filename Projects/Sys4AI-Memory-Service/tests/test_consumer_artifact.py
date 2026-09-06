"""Immutable build/installation checks; dependency installation is explicit opt-in."""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import sys
from pathlib import Path

import pytest

PRODUCT = Path(__file__).parents[1].resolve()
SPEC = importlib.util.spec_from_file_location(
    "consumer_artifact", PRODUCT / "tools/build_consumer_artifact.py"
)
assert SPEC is not None and SPEC.loader is not None
artifact = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(artifact)


def test_artifact_verification_rejects_tampered_wheel_before_environment_creation(
    tmp_path: Path,
) -> None:
    root = tmp_path.resolve()
    (root / "package.whl").write_bytes(b"tampered")
    (root / "requirements.lock").write_bytes(b"")
    receipt = {
        "schema_version": 1,
        "package": "sys4ai-memory-service",
        "version": "0.1.0",
        "wheel": {"filename": "package.whl", "sha256": "0" * 64},
        "runtime_requirements": {
            "core": {
                "filename": "requirements.lock",
                "sha256": artifact.digest(b""),
            }
        },
        "source_manifest": {},
        "source_manifest_sha256": artifact.digest(artifact.json_bytes({})),
    }
    record = root / "artifact.json"
    record.write_bytes(artifact.json_bytes(receipt))
    with pytest.raises(artifact.ArtifactError, match="recorded hash"):
        artifact.install_artifact(record, root)
    assert not (root / ".venv").exists()
    assert not (root / "control_records").exists()


def test_artifact_paths_refuse_symlink_aliases(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    real = root / "real"
    real.mkdir()
    link = root / "alias"
    link.symlink_to(real, target_is_directory=True)
    with pytest.raises(artifact.ArtifactError, match="symlinks"):
        artifact.safe_path(link / "artifact.json")


@pytest.mark.skipif(
    os.environ.get("SYS4AI_RUN_ARTIFACT_BUILD") != "1",
    reason="opt in to local build tooling and locked dependency installation",
)
def test_reproducible_wheel_and_independent_consumer_bytes(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    source = root / "build-source"
    source.mkdir()
    for name in ("pyproject.toml", "uv.lock", "README.md"):
        shutil.copyfile(PRODUCT / name, source / name)
    (source / "tools").mkdir()
    for name in ("build_consumer_artifact.py", "build-requirements.in", "build-requirements.lock"):
        shutil.copyfile(PRODUCT / "tools" / name, source / "tools" / name)
    shutil.copytree(PRODUCT / "src", source / "src", ignore=shutil.ignore_patterns("__pycache__"))
    first = artifact.build_artifact(source, python=Path(sys.executable))
    before = first.read_bytes()
    second = artifact.build_artifact(source, python=Path(sys.executable))
    assert first == second
    assert first.read_bytes() == before
    receipt = artifact.verify_artifact(first)
    assert receipt["repository"] == {"marker": None, "top_level": None, "head": None}
    assert receipt["build_environment"]["distributions"]["hatchling"] == "1.32.0"
    consumer = root / "consumer"
    consumer.mkdir()
    installed = artifact.install_artifact(first, consumer, python=Path(sys.executable))
    module = Path(installed["observed"]["origin"])
    original = artifact.digest(module.read_bytes())
    source_module = source / "src/sys4ai_memory/__init__.py"
    source_module.write_text(source_module.read_text() + "\n# Disposable source edit.\n")
    assert artifact.digest(module.read_bytes()) == original
    assert artifact.install_artifact(first, consumer) == installed
    assert installed["wheel_sha256"] == receipt["wheel"]["sha256"]
    assert not installed["observed"]["provider_imported"]
    assert not (consumer / ".sys4ai").exists()
    evidence = {
        "artifact_receipt": str(first),
        "wheel_sha256": installed["wheel_sha256"],
        "source_manifest_sha256": receipt["source_manifest_sha256"],
        "repeat_build_equal": True,
        "installed_source_mutation_independent": True,
        "consumer": str(consumer),
        "installation": installed,
    }
    (root / "verification.json").write_text(json.dumps(evidence, indent=2) + "\n")
