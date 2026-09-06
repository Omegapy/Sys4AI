#!/usr/bin/env python3
"""Build and install an immutable, locally verified consumer wheel.

This standard-library tool never initializes memory, imports a provider, edits a
dependency lock, or performs a Git write. Build dependencies are isolated and
hash-locked; consumer dependencies are exported from the product's uv.lock.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

SOURCE_DATE_EPOCH = "315532800"
PACKAGE = "sys4ai-memory-service"


class ArtifactError(RuntimeError):
    """A build, provenance, or consumer boundary could not be established."""


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2) + "\n").encode()


def safe_path(candidate: Path) -> Path:
    if not candidate.is_absolute() or ".." in candidate.parts:
        raise ArtifactError("an absolute path without traversal is required")
    if any(item.is_symlink() for item in (candidate, *candidate.parents)):
        raise ArtifactError("artifact and project paths must not cross symlinks")
    return candidate


def run(arguments: list[str], *, cwd: Path, timeout: int = 600) -> str:
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    env.update(
        PYTHONDONTWRITEBYTECODE="1",
        GIT_OPTIONAL_LOCKS="0",
        SOURCE_DATE_EPOCH=SOURCE_DATE_EPOCH,
        UV_PYTHON_DOWNLOADS="never",
    )
    result = subprocess.run(  # noqa: S603 - explicit argv, no shell
        arguments, cwd=cwd, env=env, capture_output=True, text=True, timeout=timeout, check=False
    )
    if result.returncode:
        # Do not persist resolver logs, environment values, or index credentials.
        raise ArtifactError(
            f"{Path(arguments[0]).name} {arguments[1]} failed ({result.returncode})"
        )
    return result.stdout


def uv_command() -> str:
    executable = shutil.which("uv")
    if executable is None:
        raise ArtifactError("uv is required; install build tooling through an authorized workflow")
    return executable


def source_manifest(root: Path) -> dict[str, str]:
    safe_path(root)
    candidates = [
        root / "pyproject.toml",
        root / "uv.lock",
        root / "README.md",
        root / "tools/build_consumer_artifact.py",
        root / "tools/build-requirements.lock",
        root / "tools/build-requirements.in",
    ]
    package = root / "src/sys4ai_memory"
    for current, directories, filenames in os.walk(package, followlinks=False):
        directories[:] = sorted(name for name in directories if name != "__pycache__")
        if any((Path(current) / name).is_symlink() for name in directories):
            raise ArtifactError("package source contains a symlink")
        candidates.extend(
            Path(current) / name
            for name in filenames
            if not name.endswith((".pyc", ".pyo")) and name != ".DS_Store"
        )
    values = {}
    for candidate in sorted(candidates):
        safe_path(candidate)
        if not candidate.is_file() or candidate.stat().st_nlink != 1:
            raise ArtifactError("build inputs must be regular, non-aliased files")
        values[candidate.relative_to(root).as_posix()] = digest(candidate.read_bytes())
    return values


def repository_observation(root: Path) -> dict[str, object]:
    marker = root / ".git"
    if not marker.exists():
        return {"marker": None, "top_level": None, "head": None}
    safe_path(marker)
    git = shutil.which("git")
    if git is None:
        raise ArtifactError("Git metadata exists but cannot be inspected")
    top = Path(run([git, "rev-parse", "--show-toplevel"], cwd=root).strip()).resolve()
    if top != root:
        raise ArtifactError("ancestor Git metadata cannot identify the product repository")
    return {
        "marker": "directory" if marker.is_dir() else "gitfile",
        "top_level": str(top),
        "head": run([git, "rev-parse", "HEAD"], cwd=root).strip(),
    }


def _write_new(target: Path, data: bytes) -> None:
    safe_path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        if not target.is_file() or target.read_bytes() != data:
            raise ArtifactError(f"existing artifact conflicts: {target.name}")
        return
    with target.open("xb") as stream:
        stream.write(data)


def build_artifact(project_root: Path, *, python: Path | None = None) -> Path:
    root = safe_path(project_root).resolve(strict=True)
    python = python or root / ".venv/bin/python"
    if not python.is_file():
        raise ArtifactError("a project Python 3.12 interpreter is required")
    metadata = tomllib.loads((root / "pyproject.toml").read_text())
    if metadata["project"]["name"] != PACKAGE:
        raise ArtifactError("build root is not Sys4AI Memory Service")
    if metadata["build-system"]["requires"] != ["hatchling==1.32.0"]:
        raise ArtifactError("build backend must match the pinned tooling lock")
    version = str(metadata["project"]["version"])
    if not re.fullmatch(r"\d+\.\d+\.\d+(?:[a-zA-Z0-9.+-]*)", version):
        raise ArtifactError("package version is invalid")
    uv = uv_command()
    before = source_manifest(root)
    repository = repository_observation(root)
    output = safe_path(root / "dist/consumer")
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".build-", dir=output) as name:
        staging = Path(name)
        environment = staging / "environment"
        run([uv, "venv", "--python", str(python), str(environment)], cwd=root)
        executable = environment / "bin/python"
        run(
            [
                uv,
                "pip",
                "install",
                "--python",
                str(executable),
                "--require-hashes",
                "-r",
                str(root / "tools/build-requirements.lock"),
            ],
            cwd=root,
        )
        runtime_requirements = {}
        for profile in ("core", "cognee"):
            path = staging / f"requirements-{profile}.lock"
            arguments = [
                uv,
                "export",
                "--locked",
                "--no-dev",
                "--no-emit-project",
                "--no-header",
                "--no-annotate",
                "--output-file",
                str(path),
            ]
            if profile == "cognee":
                arguments += ["--extra", "cognee"]
            run(arguments, cwd=root)
            runtime_requirements[profile] = path
        # Fixed timestamps plus a pinned isolated backend make equal inputs byte-reproducible.
        run(
            [
                uv,
                "build",
                "--wheel",
                "--no-build-isolation",
                "--python",
                str(executable),
                "--out-dir",
                str(staging / "wheel"),
            ],
            cwd=root,
        )
        wheels = list((staging / "wheel").glob("*.whl"))
        if len(wheels) != 1:
            raise ArtifactError("build did not produce exactly one wheel")
        wheel = wheels[0]
        with zipfile.ZipFile(wheel) as archive:
            wheel_files = {
                item.filename: digest(archive.read(item))
                for item in archive.infolist()
                if not item.is_dir()
            }
        if any(".." in Path(name).parts or name.startswith("/") for name in wheel_files):
            raise ArtifactError("wheel contains an unsafe member")
        if source_manifest(root) != before:
            raise ArtifactError("source changed during build; no artifact receipt was published")
        package_hash = digest(wheel.read_bytes())
        # Different build tooling can produce identical wheel bytes. Keep each
        # source snapshot's provenance immutable without colliding receipts.
        target = output / version / digest(json_bytes(before))
        target.mkdir(parents=True, exist_ok=True)
        _write_new(target / wheel.name, wheel.read_bytes())
        requirement_records = {}
        for profile, path in runtime_requirements.items():
            data = path.read_bytes()
            _write_new(target / path.name, data)
            requirement_records[profile] = {"filename": path.name, "sha256": digest(data)}
        build_environment = json.loads(
            run(
                [
                    str(executable),
                    "-I",
                    "-c",
                    "import importlib.metadata as m,json,platform; "
                    "print(json.dumps({'python':platform.python_version(), "
                    "'distributions':{d.metadata['Name']:d.version for d in m.distributions()}}))",
                ],
                cwd=staging,
            )
        )
        receipt = {
            "schema_version": 1,
            "package": PACKAGE,
            "version": version,
            "wheel": {"filename": wheel.name, "sha256": package_hash, "files": wheel_files},
            "source_root": str(root),
            "source_manifest": before,
            "source_manifest_sha256": digest(json_bytes(before)),
            "repository": repository,
            "runtime_requirements": requirement_records,
            "build_environment": build_environment,
            "uv_version": run([uv, "--version"], cwd=root).strip(),
            "source_date_epoch": SOURCE_DATE_EPOCH,
            "published": False,
        }
        receipt_path = target / "artifact.json"
        _write_new(receipt_path, json_bytes(receipt))
    return receipt_path


def verify_artifact(receipt_path: Path, *, profile: str = "core") -> dict[str, Any]:
    safe_path(receipt_path)
    if not receipt_path.is_file() or receipt_path.stat().st_size > 10_000_000:
        raise ArtifactError("artifact receipt is missing or oversized")
    try:
        receipt: dict[str, Any] = json.loads(receipt_path.read_bytes())
        wheel = receipt["wheel"]
        requirements = receipt["runtime_requirements"][profile]
        if receipt["schema_version"] != 1 or receipt["package"] != PACKAGE:
            raise ArtifactError("unsupported artifact receipt")
        for value in (wheel, requirements):
            name = value["filename"]
            if Path(name).name != name or name in {"", ".", ".."}:
                raise ArtifactError("artifact filename must be a single safe component")
            target = safe_path(receipt_path.parent / name)
            if not target.is_file() or digest(target.read_bytes()) != value["sha256"]:
                raise ArtifactError("artifact bytes do not match the recorded hash")
        if digest(json_bytes(receipt["source_manifest"])) != receipt["source_manifest_sha256"]:
            raise ArtifactError("source manifest does not match its recorded hash")
        return receipt
    except (KeyError, TypeError, ValueError) as error:
        raise ArtifactError("artifact receipt is malformed") from error


def inspect_installation(python: Path, *, cwd: Path) -> dict[str, Any]:
    result: dict[str, Any] = json.loads(
        run(
            [
                str(python),
                "-I",
                "-c",
                "import importlib.metadata as m,importlib.util as u,json,sys; "
                "d=m.distribution('sys4ai-memory-service'); "
                "print(json.dumps({'version':d.version,'origin':u.find_spec('sys4ai_memory').origin,"
                "'direct_url':json.loads(d.read_text('direct_url.json') or '{}'),"
                "'provider_imported':'cognee' in sys.modules,"
                "'dependencies':{x.metadata['Name']:x.version for x in m.distributions()}}))",
            ],
            cwd=cwd,
        )
    )
    return result


def install_artifact(
    receipt_path: Path, project_root: Path, *, python: Path | None = None, with_cognee: bool = False
) -> dict[str, Any]:
    root = safe_path(project_root).resolve(strict=True)
    profile = "cognee" if with_cognee else "core"
    receipt = verify_artifact(receipt_path, profile=profile)
    environment = safe_path(root / ".venv")
    output = safe_path(root / "control_records/memory/runtime-installation.json")
    wheel = receipt_path.parent / receipt["wheel"]["filename"]
    expected = {
        "package": PACKAGE,
        "version": receipt["version"],
        "wheel_sha256": receipt["wheel"]["sha256"],
        "dependency_profile": profile,
    }
    current: dict[str, Any] | None = None
    if output.exists():
        current = json.loads(output.read_bytes())
        if not isinstance(current, dict):
            raise ArtifactError("existing runtime receipt must be an object")
        if any(current.get(key) != value for key, value in expected.items()):
            raise ArtifactError(
                "existing runtime receipt differs; refresh requires explicit adoption"
            )
        if not (environment / "bin/python").is_file():
            raise ArtifactError("recorded consumer environment is missing; repair is required")
    uv = uv_command()
    if not environment.exists():
        run([uv, "venv", "--python", str(python or sys.executable), str(environment)], cwd=root)
    executable = environment / "bin/python"
    if not executable.is_file():
        raise ArtifactError("consumer environment has no Python interpreter")
    if not output.exists():
        requirements = receipt_path.parent / receipt["runtime_requirements"][profile]["filename"]
        run(
            [
                uv,
                "pip",
                "install",
                "--python",
                str(executable),
                "--require-hashes",
                "-r",
                str(requirements),
            ],
            cwd=root,
        )
        # Runtime bytes always come from this verified wheel, never a source directory.
        run(
            [
                uv,
                "pip",
                "install",
                "--python",
                str(executable),
                "--no-deps",
                "--reinstall-package",
                PACKAGE,
                PACKAGE + " @ " + wheel.as_uri() + "#sha256=" + receipt["wheel"]["sha256"],
            ],
            cwd=root,
        )
    observed = inspect_installation(executable, cwd=environment)
    archive = observed["direct_url"].get("archive_info", {})
    if (
        observed["version"] != receipt["version"]
        or not Path(observed["origin"]).is_relative_to(environment)
        or observed["direct_url"].get("dir_info", {}).get("editable")
        or observed["direct_url"].get("url")
        != wheel.as_uri() + "#sha256=" + receipt["wheel"]["sha256"]
        or archive.get("hashes", {}).get("sha256") not in {None, receipt["wheel"]["sha256"]}
        or observed["provider_imported"]
    ):
        raise ArtifactError("installed runtime provenance differs from the verified wheel")
    # Some uv versions omit archive_info hashes for local URLs. Independently
    # compare every installed package member with the verified wheel manifest.
    package_parent = Path(observed["origin"]).parent.parent
    for name, expected_hash in receipt["wheel"]["files"].items():
        if not name.startswith("sys4ai_memory/"):
            continue
        installed_file = safe_path(package_parent / name)
        if not installed_file.is_file() or digest(installed_file.read_bytes()) != expected_hash:
            raise ArtifactError("installed package bytes differ from the immutable wheel")
    if current is not None:
        for name, version in current["observed"]["dependencies"].items():
            if observed["dependencies"].get(name) != version:
                raise ArtifactError("the recorded consumer environment has changed")
    installed = {
        "schema_version": 1,
        **expected,
        "artifact_receipt": str(receipt_path),
        "source_manifest_sha256": receipt["source_manifest_sha256"],
        "source_repository": receipt["repository"],
        "environment": str(environment),
        "observed": observed,
        "installed_at": datetime.now(UTC).isoformat(),
    }
    if current is not None:
        return current
    _write_new(output, json_bytes(installed))
    return installed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    routes = parser.add_subparsers(dest="command", required=True)
    build = routes.add_parser("build")
    build.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[1])
    build.add_argument("--python", type=Path)
    verify = routes.add_parser("verify")
    verify.add_argument("receipt", type=Path)
    install = routes.add_parser("install")
    install.add_argument("receipt", type=Path)
    install.add_argument("--project-root", type=Path, required=True)
    install.add_argument("--python", type=Path)
    install.add_argument("--with-cognee", action="store_true")
    args = parser.parse_args()
    try:
        if args.command == "build":
            result = {
                "artifact_receipt": str(build_artifact(args.project_root, python=args.python))
            }
        elif args.command == "verify":
            receipt = verify_artifact(args.receipt)
            result = {"version": receipt["version"], "wheel_sha256": receipt["wheel"]["sha256"]}
        else:
            result = install_artifact(
                args.receipt, args.project_root, python=args.python, with_cognee=args.with_cognee
            )
        print(json.dumps({"status": "ok", **result}, sort_keys=True))
        return 0
    except (ArtifactError, OSError, subprocess.TimeoutExpired) as error:
        print(json.dumps({"status": "error", "reason": str(error)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
