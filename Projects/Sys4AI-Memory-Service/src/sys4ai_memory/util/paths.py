"""Project-root path confinement."""

from __future__ import annotations

from pathlib import Path


class PathBoundaryError(ValueError):
    """A path escaped its declared project root or crossed a symlink."""


def resolve_within(
    root: Path,
    candidate: str | Path,
    *,
    must_exist: bool = True,
    allow_symlink: bool = False,
) -> Path:
    """Resolve a relative path inside an existing, non-symlink project root."""

    if not root.is_absolute():
        raise PathBoundaryError("project root must be absolute")
    if root.is_symlink() or not root.is_dir():
        raise PathBoundaryError("project root must be an existing non-symlink directory")
    raw = Path(candidate)
    if raw.is_absolute():
        raise PathBoundaryError("candidate path must be project-relative")
    if any(part in {"", ".", ".."} for part in raw.parts):
        raise PathBoundaryError("candidate path contains an unsafe segment")

    root_resolved = root.resolve(strict=True)
    joined = root_resolved / raw
    cursor = root_resolved
    for part in raw.parts:
        cursor = cursor / part
        if cursor.is_symlink() and not allow_symlink:
            raise PathBoundaryError(f"symlink is not allowed: {cursor}")
    resolved = joined.resolve(strict=must_exist)
    try:
        resolved.relative_to(root_resolved)
    except ValueError as error:
        raise PathBoundaryError("candidate path escapes the project root") from error
    if must_exist and not resolved.exists():
        raise PathBoundaryError("candidate path does not exist")
    return resolved
