#!/usr/bin/env python3
"""Publish validated depot files into the one Sys4AI project template.

The receipt owns individual destination bytes, never a whole directory. A
pending record permits forward recovery after interrupted per-file atomic
writes; this is not a transactionally swapped template tree. Initializers
coordinate their template reads with a shared lock on the same lock file.
"""

from __future__ import annotations

import argparse
import ast
import base64
import binascii
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import tempfile
import unicodedata
from typing import Any, Iterator

TEMPLATE = "Projects/Sys4AI-Template-Project"
MANIFEST = "depot/template-update.json"
CONTROL = ".sys4ai/template-update"
STATE = CONTROL + "/state.json"
PENDING = CONTROL + "/pending.json"
LOCK = CONTROL + "/lock"
BASELINE_SKILLS = (
    "agent-task", "communication", "manage-subagent-roles", "task",
    "to-implementation-plan", "to-trd",
)
BASELINE_FILES = {
    "SOUL.md", "AGENTS.md", "ROLE.md", "SPECS.md", ".gitignore",
    "sub-agent-roles/project-sub-agent/AGENTS.md",
    "sub-agent-roles/project-sub-agent/ROLE.md", ".template/baseline-assets.json",
    ".template/project-readme.md",
    *(f".agents/skills/{name}/SKILL.md" for name in BASELINE_SKILLS),
}
EXCLUDED = {
    ".git", ".gitmodules", ".gitignore_global", ".venv", "venv", "env",
    ".sys4ai", "__pycache__", ".ds_store", ".pytest_cache", ".ruff_cache",
    ".mypy_cache", ".cache", "models", "logs", ".cognee", ".cognee_system",
    ".data_storage", "dist", "build", "node_modules", ".env", ".envrc",
    ".secrets", "secrets", "credentials", ".credentials", "credentials.json",
    ".credentials.json", ".aws", ".ssh", ".netrc", ".pypirc", ".npmrc",
    "id_rsa", "id_ed25519",
}
EXCLUDED_SUFFIXES = (
    ".pyc", ".pyo", ".log", ".zip", ".whl", ".egg", ".pem", ".key",
    ".p12", ".pfx", ".swp", ".swo", "~",
)
HASH = re.compile(r"[0-9a-f]{64}\Z")
SKILL_NAME = re.compile(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*\Z")


class UpdateError(RuntimeError):
    def __init__(self, message: str, *, report: dict[str, Any] | None = None):
        super().__init__(message)
        self.report = report or {"status": "blocked", "conflicts": [message]}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def encoded(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def json_document(raw: bytes) -> Any:
    def unique(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in items:
            if key in result:
                raise UpdateError("duplicate JSON key")
            result[key] = value
        return result

    try:
        return json.loads(raw, object_pairs_hook=unique)
    except (UnicodeError, ValueError) as error:
        raise UpdateError("invalid JSON document") from error


def relative(value: str) -> str:
    if (
        not isinstance(value, str) or not value or "\\" in value
        or any(ord(char) < 32 for char in value)
        or PurePosixPath(value).is_absolute()
        or any(part in {".", "..", ""} for part in value.split("/"))
    ):
        raise UpdateError("expected a relative path without traversal")
    return value


def safe(path: Path) -> Path:
    if not path.is_absolute() or ".." in path.parts:
        raise UpdateError("absolute paths without traversal are required")
    for item in reversed((path, *path.parents)):
        try:
            info = item.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode):
            raise UpdateError(f"symbolic link is not allowed: {item}")
        if item != path and not stat.S_ISDIR(info.st_mode):
            raise UpdateError(f"parent is not a directory: {item}")
    return path


def read_file(path: Path, *, optional: bool = False) -> bytes | None:
    safe(path)
    try:
        before = path.lstat()
    except FileNotFoundError:
        if optional:
            return None
        raise UpdateError(f"required file is missing: {path}")
    if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
        raise UpdateError(f"expected a regular non-aliased file: {path}")
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as stream:
        opened = os.fstat(stream.fileno())
        if (before.st_dev, before.st_ino) != (opened.st_dev, opened.st_ino):
            raise UpdateError(f"file changed while opening: {path}")
        data = stream.read()
        after = os.fstat(stream.fileno())
    current = path.lstat()
    signature = lambda item: (
        item.st_dev, item.st_ino, item.st_size, item.st_mtime_ns, item.st_ctime_ns
    )
    if signature(before) != signature(after) or signature(after) != signature(current):
        raise UpdateError(f"file changed while reading: {path}")
    return data


def excluded(path: str) -> bool:
    parts = PurePosixPath(path).parts
    return any(
        part.lower() in EXCLUDED or part.lower().startswith(("._", ".env."))
        for part in parts
    ) or parts[-1].lower().endswith(EXCLUDED_SUFFIXES)


def destination(value: str) -> str:
    value = relative(value)
    if excluded(value):
        raise UpdateError(f"destination is a protected or transient path: {value}")
    return value


def source(value: str) -> str:
    value = relative(value)
    parts = value.split("/")
    if len(parts) < 2 or not parts[0].endswith("-depo") or excluded(value):
        raise UpdateError(f"source must be a nontransient depot file: {value}")
    return value


def validate_skill(name: str, raw: bytes) -> None:
    try:
        text = raw.decode("utf-8")
    except UnicodeError as error:
        raise UpdateError(f"skill metadata must be UTF-8: {name}") from error
    front = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|\Z)", text, re.S)
    if not SKILL_NAME.fullmatch(name) or not front:
        raise UpdateError(f"skill needs a valid name and frontmatter: {name}")
    fields: dict[str, str] = {}
    lines = front.group(1).splitlines()
    for index, line in enumerate(lines):
        field = re.match(r"^([a-zA-Z][a-zA-Z0-9_-]*):\s*(.*)$", line)
        if not field:
            continue
        key, value = field.groups()
        if key in fields:
            raise UpdateError(f"duplicate skill metadata field: {name}/{key}")
        if value in {">", "|", ">-", "|-", ">+", "|+"}:
            continuation = []
            for following in lines[index + 1:]:
                if following and not following[0].isspace():
                    break
                continuation.append(following.strip())
            value = " ".join(continuation).strip()
        if value.startswith(("\"", "'")):
            if len(value) < 2 or value[-1] != value[0]:
                raise UpdateError(f"unterminated skill metadata value: {name}/{key}")
            value = value[1:-1]
        fields[key] = value
    if fields.get("name") != name or not fields.get("description", "").strip():
        raise UpdateError(f"skill name must match its folder and have a description: {name}")


def snapshot(root: Path) -> dict[str, Any]:
    """Read one validated source snapshot without touching the template."""
    safe(root)
    if not root.is_dir():
        raise UpdateError("depot root is missing")
    manifest_raw = read_file(root / MANIFEST)
    manifest = json_document(manifest_raw)
    if (
        not isinstance(manifest, dict) or manifest.get("schema_version") != 1
        or manifest.get("template") != TEMPLATE
        or set(manifest) != {"schema_version", "template", "overrides", "mirrors"}
    ):
        raise UpdateError("expected a schema-1 manifest for the Sys4AI template")
    for key in ("overrides", "mirrors"):
        if not isinstance(manifest[key], dict):
            raise UpdateError(f"manifest {key} must contain exact file mappings")
        for origin, target in manifest[key].items():
            source(origin)
            destination(target)

    mapped_sources = set(manifest["overrides"]) | set(manifest["mirrors"])
    collections: list[str] = []
    blobs: dict[str, bytes] = {}
    modes: dict[str, int] = {}
    skill_dirs: list[str] = []

    def walk(folder: Path) -> None:
        for item in sorted(folder.iterdir()):
            rel = item.relative_to(root).as_posix()
            info = item.lstat()
            if stat.S_ISLNK(info.st_mode):
                raise UpdateError(f"symbolic link in depot source: {rel}")
            if excluded(rel):
                continue
            if stat.S_ISDIR(info.st_mode):
                if item.parent == root / "SKILLS-depo":
                    skill_dirs.append(item.name)
                walk(item)
            elif stat.S_ISREG(info.st_mode):
                raw = read_file(item)
                if item.suffix == ".json":
                    try:
                        json_document(raw)
                    except UpdateError as error:
                        raise UpdateError(f"invalid JSON source: {rel}") from error
                if item.suffix == ".py":
                    try:
                        ast.parse(raw, filename=rel)
                    except (SyntaxError, ValueError) as error:
                        raise UpdateError(f"invalid Python source: {rel}") from error
                blobs[rel] = raw
                modes[rel] = 0o755 if info.st_mode & 0o111 else 0o644
            else:
                raise UpdateError(f"non-regular depot source: {rel}")

    for folder in sorted(root.iterdir()):
        if folder.name.endswith("-depo"):
            safe(folder)
            if not folder.is_dir():
                raise UpdateError(f"depot collection is not a directory: {folder.name}")
            collections.append(folder.name)
            walk(folder)
    missing_mapped = sorted(mapped_sources - blobs.keys())
    if missing_mapped:
        raise UpdateError("mapped source is missing: " + ", ".join(missing_mapped))
    for name in skill_dirs:
        header = blobs.get(f"SKILLS-depo/{name}/SKILL.md")
        if header is None:
            raise UpdateError(f"incomplete skill package, SKILL.md is missing: {name}")
        validate_skill(name, header)

    files: dict[str, dict[str, Any]] = {}
    identities: dict[str, str] = {}
    for origin, raw in sorted(blobs.items()):
        parts = origin.split("/")
        default = (
            ".agents/skills/" + "/".join(parts[1:])
            if parts[0] == "SKILLS-depo" and len(parts) > 2
            else "reference-assets/" + origin
        )
        targets = [manifest["overrides"].get(origin, default)]
        if origin in manifest["mirrors"]:
            targets.append(manifest["mirrors"][origin])
        for target in targets:
            destination(target)
            identity = unicodedata.normalize("NFD", target).casefold()
            if identity in identities:
                raise UpdateError(f"duplicate template destination: {target}")
            identities[identity] = target
            files[target] = {"source": origin, "sha256": digest(raw), "mode": modes[origin]}
    for key in identities:
        if any(parent.as_posix() in identities for parent in PurePosixPath(key).parents):
            raise UpdateError(f"template file/directory mapping collision: {identities[key]}")
    missing = sorted(BASELINE_FILES - files.keys())
    if missing:
        raise UpdateError("required template governance source is missing: " + ", ".join(missing))
    for target in BASELINE_FILES:
        if not blobs[files[target]["source"]].strip():
            raise UpdateError(f"required template governance source is empty: {target}")
    policy = json_document(blobs[files[".template/baseline-assets.json"]["source"]])
    if (not isinstance(policy, dict) or type(policy.get("schema_version")) is not int
            or policy["schema_version"] != 2):
        raise UpdateError("template initialization policy must use schema 2")
    state = {"schema_version": 1, "template": TEMPLATE, "collections": collections, "files": files}
    return {
        "state": state, "blobs": blobs,
        "fingerprint": digest(manifest_raw + encoded(state)),
    }


def validate_state(state: Any) -> dict[str, Any]:
    if (
        not isinstance(state, dict) or state.get("schema_version") != 1
        or state.get("template") != TEMPLATE
        or not isinstance(state.get("collections"), list)
        or not isinstance(state.get("files"), dict)
    ):
        raise UpdateError("invalid template update state")
    collections = state["collections"]
    if any(
        not isinstance(name, str) or "/" in relative(name) or not name.endswith("-depo")
        for name in collections
    ) or len(set(collections)) != len(collections):
        raise UpdateError("invalid recorded depot collections")
    for target, entry in state["files"].items():
        destination(target)
        if (
            not isinstance(entry, dict)
            or not isinstance(entry.get("sha256"), str)
            or not HASH.fullmatch(entry["sha256"])
            or not isinstance(entry.get("mode"), int)
            or entry.get("mode") not in {0o644, 0o755}
        ):
            raise UpdateError("invalid recorded destination ownership")
        if source(entry.get("source")).split("/")[0] not in collections:
            raise UpdateError("recorded source collection is missing")
    return state


def load_state(root: Path) -> dict[str, Any]:
    raw = read_file(root / STATE, optional=True)
    if raw is None:
        return {"schema_version": 1, "template": TEMPLATE, "collections": [], "files": {}}
    return validate_state(json_document(raw))


def file_hash(path: Path) -> str | None:
    raw = read_file(path, optional=True)
    return None if raw is None else digest(raw)


def retirement_targets(
    root: Path, before: dict[str, Any], after: dict[str, Any], collection: str,
) -> list[str]:
    """Validate the exact collection transition independently of destination bytes."""
    if "/" in relative(collection) or not collection.endswith("-depo"):
        raise UpdateError("retirement requires one exact depot collection name")
    if collection not in before["collections"]:
        raise UpdateError("retired collection is not in the recorded state")
    if safe(root / collection).exists() or collection in after["collections"]:
        raise UpdateError("retired source collection must be absent")
    lost = set(before["collections"]) - set(after["collections"])
    if lost != {collection}:
        raise UpdateError("unexpected missing source collection during retirement")
    targets = sorted(
        target for target, entry in before["files"].items()
        if entry["source"].split("/")[0] == collection
    )
    if set(targets) & after["files"].keys():
        raise UpdateError("retired collection destinations must not be remapped")
    return targets


def plan(
    root: Path, before: dict[str, Any], after: dict[str, Any],
    *, retire_collection: str | None = None,
) -> dict[str, Any]:
    template = safe(root / TEMPLATE)
    if not template.is_dir():
        raise UpdateError("template directory is missing; updater never creates a replacement root")
    report: dict[str, Any] = {
        "status": "current", "additions": [], "updates": [], "deletions": [],
        "adoptions": [], "conflicts": [], "managed_files": len(after["files"]),
        "source_files": len({item["source"] for item in after["files"].values()}),
    }
    lost = sorted(set(before["collections"]) - set(after["collections"]))
    if retire_collection is not None:
        report["retired_collection"] = retire_collection
        report["retired_destinations"] = retirement_targets(root, before, after, retire_collection)
        lost.remove(retire_collection)
    if lost:
        report["conflicts"].append("recorded source collection is missing: " + ", ".join(lost))
    for target in sorted(before["files"].keys() | after["files"].keys()):
        previous = before["files"].get(target)
        desired = after["files"].get(target)
        try:
            current = file_hash(template / target)
        except (UpdateError, OSError) as error:
            report["conflicts"].append(f"{target}: {error}")
            continue
        if previous:
            if current != previous["sha256"] and not (
                retire_collection is None and current is None and desired is None
            ):
                report["conflicts"].append(f"managed destination was customized: {target}")
            elif desired is None:
                report["deletions"].append(target)
            elif previous != desired:
                report["updates"].append(target)
        elif current is None:
            report["additions"].append(target)
        elif current == desired["sha256"]:
            report["adoptions"].append(target)
        else:
            report["conflicts"].append(f"unmanaged destination differs from source: {target}")
    if report["conflicts"]:
        report["status"] = "conflict"
    elif before != after:
        report["status"] = "outdated"
    return report


def atomic_write(path: Path, data: bytes, mode: int = 0o644) -> None:
    safe(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    safe(path.parent)
    fd, temporary = tempfile.mkstemp(prefix=".template-update-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fchmod(stream.fileno(), mode)
            os.fsync(stream.fileno())
        safe(path)
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


@contextmanager
def locked(root: Path, *, readonly: bool = False) -> Iterator[None]:
    path = safe(root / LOCK)
    if readonly and not path.exists():
        yield
        return
    if not readonly:
        path.parent.mkdir(parents=True, exist_ok=True)
        safe(path.parent)
    flags = os.O_RDONLY if readonly else os.O_RDWR | os.O_CREAT
    fd = os.open(path, flags | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise UpdateError("template lock must be a regular non-aliased file")
        try:
            fcntl.flock(fd, (fcntl.LOCK_SH if readonly else fcntl.LOCK_EX) | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise UpdateError("template is busy; another update or initializer holds the lock") from error
        yield
    finally:
        os.close(fd)


def make_pending(
    before: dict[str, Any], snap: dict[str, Any],
    *, retirement: dict[str, str] | None = None,
) -> dict[str, Any]:
    after = snap["state"]
    payloads = {
        target: base64.b64encode(snap["blobs"][entry["source"]]).decode("ascii")
        for target, entry in after["files"].items()
        if before["files"].get(target) != entry
    }
    pending = {"schema_version": 1, "before": before, "after": after, "payloads": payloads}
    if retirement is not None:
        pending["retirement"] = retirement
    return pending


def recover(root: Path, pending: dict[str, Any]) -> None:
    """Resume only if every destination still has its recorded old or new bytes."""
    if not isinstance(pending, dict) or pending.get("schema_version") != 1:
        raise UpdateError("invalid pending template update")
    before = validate_state(pending.get("before"))
    after = validate_state(pending.get("after"))
    if not BASELINE_FILES.issubset(after["files"]):
        raise UpdateError("pending update would remove required template governance")
    state_raw = read_file(root / STATE, optional=True)
    current_state = load_state(root)
    if current_state not in (before, after):
        raise UpdateError("template state changed after the interrupted update")
    retirement = pending.get("retirement")
    if retirement is not None:
        if (not isinstance(retirement, dict)
                or set(retirement) != {"collection", "state_sha256"}
                or not isinstance(retirement["state_sha256"], str)
                or not HASH.fullmatch(retirement["state_sha256"])):
            raise UpdateError("invalid pending collection retirement")
        retirement_targets(root, before, after, retirement["collection"])
        # Recheck the surviving sources before resuming any partial deletion.
        retirement_targets(root, before, snapshot(root)["state"], retirement["collection"])
        if current_state == before and (
            state_raw is None or digest(state_raw) != retirement["state_sha256"]
        ):
            raise UpdateError("retirement state digest changed after the interrupted update")
    elif set(before["collections"]) - set(after["collections"]):
        raise UpdateError("pending collection loss requires an explicit retirement record")
    payloads = pending.get("payloads")
    expected = {
        target for target, entry in after["files"].items()
        if before["files"].get(target) != entry
    }
    if not isinstance(payloads, dict) or set(payloads) != expected:
        raise UpdateError("pending update payload inventory is invalid")
    decoded: dict[str, bytes] = {}
    for target, payload in payloads.items():
        try:
            decoded[target] = base64.b64decode(payload, validate=True)
        except (ValueError, TypeError, binascii.Error) as error:
            raise UpdateError("pending update payload is invalid") from error
        if digest(decoded[target]) != after["files"][target]["sha256"]:
            raise UpdateError(f"pending update payload checksum mismatch: {target}")
    template = safe(root / TEMPLATE)
    if not template.is_dir():
        raise UpdateError("template directory is missing during recovery")
    targets = sorted(before["files"].keys() | after["files"].keys())
    conflicts = []
    observed: dict[str, str | None] = {}
    for target in targets:
        old = before["files"].get(target, {}).get("sha256")
        new = after["files"].get(target, {}).get("sha256")
        observed[target] = file_hash(template / target)
        if observed[target] not in {old, new}:
            conflicts.append(f"destination changed during interrupted update: {target}")
    if conflicts:
        raise UpdateError("recovery conflict", report={"status": "conflict", "conflicts": conflicts})
    for target in targets:
        desired = after["files"].get(target)
        new = None if desired is None else desired["sha256"]
        candidate = template / target
        if file_hash(candidate) != observed[target]:
            raise UpdateError(f"destination changed during update: {target}")
        if observed[target] == new:
            continue
        if desired is None:
            safe(candidate).unlink()
            parent = candidate.parent
            while parent != template:
                safe(parent)
                try:
                    parent.rmdir()
                except OSError:
                    break
                parent = parent.parent
        else:
            atomic_write(candidate, decoded[target], desired["mode"])
    for target in targets:
        expected_hash = after["files"].get(target, {}).get("sha256")
        if file_hash(template / target) != expected_hash:
            raise UpdateError(f"post-write verification failed: {target}")
    if read_file(root / STATE, optional=True) != state_raw:
        raise UpdateError("template state changed during update")
    if current_state != after:
        atomic_write(root / STATE, encoded(after), 0o600)
    safe(root / PENDING).unlink()


def update(
    root: Path, command: str, *, retire_collection: str | None = None,
    expected_state_sha256: str | None = None,
) -> dict[str, Any]:
    root = safe(root.absolute())
    if command not in {"check", "apply"}:
        raise UpdateError("expected check or apply")
    if (retire_collection is None) != (expected_state_sha256 is None):
        raise UpdateError("collection retirement requires both collection and expected state digest")
    if expected_state_sha256 is not None and (
        not isinstance(expected_state_sha256, str) or not HASH.fullmatch(expected_state_sha256)
    ):
        raise UpdateError("expected state digest must be a lowercase SHA256")
    if not root.is_dir():
        raise UpdateError("depot root is missing")
    with locked(root, readonly=command == "check"):
        pending_raw = read_file(root / PENDING, optional=True)
        recovered = pending_raw is not None
        if recovered:
            if retire_collection is not None:
                raise UpdateError("pending update must recover with ordinary apply before starting retirement")
            if command == "check":
                raise UpdateError("interrupted update needs recovery; run apply")
            recover(root, json_document(pending_raw))
        before = load_state(root)
        if expected_state_sha256 is not None and file_hash(root / STATE) != expected_state_sha256:
            raise UpdateError("expected state digest is stale or the recorded state is missing")
        first = snapshot(root)
        report = plan(root, before, first["state"], retire_collection=retire_collection)
        if report["conflicts"]:
            raise UpdateError("template update has conflicts", report=report)
        second = snapshot(root)
        if first["fingerprint"] != second["fingerprint"]:
            raise UpdateError("depot source changed during preflight; retry after edits settle")
        if load_state(root) != before:
            raise UpdateError("template state changed during preflight")
        if expected_state_sha256 is not None and file_hash(root / STATE) != expected_state_sha256:
            raise UpdateError("expected state digest changed during preflight")
        # Repeat the destination preflight after reading the source a second time.
        final_report = plan(root, before, second["state"], retire_collection=retire_collection)
        if final_report != report:
            raise UpdateError("template destination changed during preflight")
        if command == "apply" and report["status"] == "outdated":
            retirement = None if retire_collection is None else {
                "collection": retire_collection, "state_sha256": expected_state_sha256,
            }
            pending = make_pending(before, second, retirement=retirement)
            atomic_write(root / PENDING, encoded(pending), 0o600)
            recover(root, pending)
            report["status"] = "applied"
        report["recovered"] = recovered
        return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path(__file__).absolute().parents[1])
    parser.add_argument("command", choices=("check", "apply"))
    parser.add_argument("--retire-collection", help="exact recorded collection, already absent and unmapped")
    parser.add_argument("--expected-state-sha256", help="SHA256 of the current raw state.json; required for retirement")
    args = parser.parse_args(argv)
    try:
        report = update(
            args.project_root, args.command, retire_collection=args.retire_collection,
            expected_state_sha256=args.expected_state_sha256,
        )
    except UpdateError as error:
        print(json.dumps(error.report, sort_keys=True))
        return 2
    except OSError as error:
        print(json.dumps({"status": "blocked", "conflicts": [str(error)]}, sort_keys=True))
        return 2
    print(json.dumps(report, sort_keys=True))
    return 1 if report["status"] == "outdated" else 0


if __name__ == "__main__":
    raise SystemExit(main())
