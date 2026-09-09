"""Project-confined filesystem access. No discovery outside the explicit root."""
from __future__ import annotations

import fnmatch
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys
import unicodedata


class MemoryError(Exception):
    def __init__(self, code, message, details=None):
        super().__init__(message)
        self.code = code
        self.details = details or {}

    def as_dict(self):
        return {"code": self.code, "message": str(self), "details": self.details}


def require(condition, code, message, details=None):
    if not condition:
        raise MemoryError(code, message, details)


def relative_path(value):
    require(isinstance(value, str) and value and "\\" not in value and
            not any(ord(c) < 32 for c in value), "unsafe_path", "Expected a project-relative POSIX path.")
    p = PurePosixPath(value)
    require(not p.is_absolute() and value == p.as_posix() and
            all(x not in (".", "..") for x in p.parts), "unsafe_path", "Non-canonical relative path rejected.")
    return p


def _fold(value):
    return unicodedata.normalize("NFC", value).casefold()


def _finder_info(path):
    """Darwin CPython omits os.getxattr; use its documented libc interface."""
    import errno
    missing = {getattr(errno, "ENOATTR", -1), getattr(errno, "ENODATA", -2), errno.ENOTSUP}
    if hasattr(os, "getxattr"):
        try:
            return os.getxattr(path, "com.apple.FinderInfo", follow_symlinks=False)
        except OSError as exc:
            require(exc.errno in missing, "unsafe_alias", "Could not inspect alias metadata.")
            return b""
    if sys.platform == "darwin":
        import ctypes
        libc = ctypes.CDLL(None, use_errno=True)
        read = libc.getxattr
        read.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_void_p,
                         ctypes.c_size_t, ctypes.c_uint32, ctypes.c_int]
        read.restype = ctypes.c_ssize_t
        buffer = ctypes.create_string_buffer(32)
        size = read(os.fsencode(path), b"com.apple.FinderInfo", buffer, len(buffer), 0, 0x0001)
        if size < 0:
            require(ctypes.get_errno() in missing, "unsafe_alias", "Could not inspect Darwin alias metadata.")
            return b""
        return buffer.raw[:size]
    return b""


def _check_entry(path, *, root=False):
    info = path.lstat()
    require(not stat.S_ISLNK(info.st_mode), "unsafe_symlink", "Symlink access is prohibited.")
    require(stat.S_ISREG(info.st_mode) or stat.S_ISDIR(info.st_mode), "unsafe_file", "Only regular files and directories are supported.")
    if stat.S_ISREG(info.st_mode):
        require(info.st_nlink == 1, "unsafe_hardlink", "Hard-linked files are prohibited.")
        finder = _finder_info(path)
        require(len(finder) < 10 or not (int.from_bytes(finder[8:10], "big") & 0x8000),
                "unsafe_alias", "Finder aliases are prohibited.")
    return info


def project_root(root):
    supplied = Path(root).absolute()
    require(supplied.is_dir(), "project_absent", "Explicit project root is not a directory.")
    resolved = supplied.resolve(strict=True)
    require(supplied == resolved, "unsafe_root", "Project root must use its real path without aliases or symlinks.")
    _check_entry(resolved, root=True)
    return resolved


def sensitive_path(rel):
    parts = [_fold(p) for p in relative_path(str(rel)).parts]
    for part in parts:
        if part in {"secrets", "credentials", ".ssh", ".aws", ".gnupg", "keychain"}:
            return True
        if part == ".env" or part.startswith(".env.") or part.endswith((".pem", ".key", ".p12", ".pfx", ".keychain-db")):
            return True
        if re.search(r"(?:^|[_.-])(?:secret|secrets|credential|credentials|passwords|tokens)(?:[_.-]|$)", part):
            return True
    return False


def safe_path(root, rel, must_exist=True, kind="file"):
    root = project_root(root)
    rel = relative_path(str(rel))
    require(not sensitive_path(rel), "sensitive_path", "Credential or secret paths are outside memory access.")
    require(not any(_fold(p) == "projects" for p in rel.parts), "project_boundary", "Child project paths are outside the owning project.")
    cursor = root
    missing = False
    for index, part in enumerate(rel.parts):
        if not missing:
            entries = [name for name in os.listdir(cursor) if _fold(name) == _fold(part)]
            require(not entries or entries == [part], "ambiguous_path", "Case or Unicode path aliases are prohibited.")
        cursor = cursor / part
        if cursor.exists() or cursor.is_symlink():
            info = _check_entry(cursor)
            if index < len(rel.parts) - 1:
                require(stat.S_ISDIR(info.st_mode), "unsafe_path", "Intermediate path is not a directory.")
                require(not (cursor / "memory.yaml").exists(), "project_boundary", "Nested project memory boundary rejected.")
        else:
            missing = True
    require(not must_exist or not missing, "file_absent", "Required project file is absent.", {"path": str(rel)})
    if not missing:
        require(kind == "any" or (kind == "file" and cursor.is_file()) or
                (kind == "dir" and cursor.is_dir()), "unsafe_file", "Unexpected filesystem object type.")
    return cursor


def safe_read_bytes(root, rel, *, max_bytes=16_000_000):
    """Open every directory by descriptor, rejecting swaps at the read boundary."""
    root = project_root(root)
    target = safe_path(root, rel)
    parts = relative_path(str(rel)).parts
    dir_fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    file_fd = None
    try:
        for part in parts[:-1]:
            next_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=dir_fd)
            os.close(dir_fd)
            dir_fd = next_fd
        file_fd = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW, dir_fd=dir_fd)
        before = os.fstat(file_fd)
        require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and before.st_size <= max_bytes,
                "unsafe_file", "File is linked, unsupported, or too large.")
        with os.fdopen(file_fd, "rb", closefd=False) as stream:
            raw = stream.read(max_bytes + 1)
        after = os.fstat(file_fd)
        actual = safe_path(root, rel).stat()
        identity = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_nlink)
        require(identity(before) == identity(after) == identity(actual) and len(raw) <= max_bytes,
                "file_changed", "File changed while being inspected.")
        return raw
    except OSError as exc:
        raise MemoryError("unsafe_read", "Confined file read failed.", {"path": str(rel)}) from exc
    finally:
        if file_fd is not None:
            os.close(file_fd)
        os.close(dir_fd)


EXCLUDED_DIRS = {"projects", "tasks", "roles", "sub-agent-roles", "reference-assets", "memory",
                 ".git", ".hg", ".svn", ".venv", "venv", "node_modules", ".sys4ai", ".agents", ".codex",
                 "build", "dist", "target", "__pycache__", ".pytest_cache", ".mypy_cache"}


def _glob_match(rel, pattern):
    """POSIX segment glob: * excludes '/', ** includes zero or more segments."""
    parts = rel.split("/")
    pats = pattern.split("/")
    def match(i, j):
        if j == len(pats):
            return i == len(parts)
        if pats[j] == "**":
            return match(i, j + 1) or (i < len(parts) and match(i + 1, j))
        return i < len(parts) and fnmatch.fnmatchcase(parts[i], pats[j]) and match(i + 1, j + 1)
    return match(0, 0)


def corpus_allowed(rel, config):
    rel = str(relative_path(str(rel)))
    parts = rel.split("/")
    if sensitive_path(rel) or any(_fold(p) in EXCLUDED_DIRS or _fold(p).endswith("-depo") or
                                 _fold(p).startswith(".venv") for p in parts):
        return False
    corpus = config["corpus"]
    return any(_glob_match(rel, p) for p in corpus["include"]) and not any(
        _glob_match(rel.casefold(), p.casefold()) for p in corpus["exclude"])


def iter_corpus(root, config):
    root = project_root(root)
    found = []
    # Only permitted top-level source locations are traversed; excluded trees
    # and their filenames are never returned in retrieval diagnostics.
    for dirname in ("docs", "research"):
        base = root / dirname
        if not base.exists() and not base.is_symlink():
            continue
        safe_path(root, dirname, kind="dir")
        for current, dirs, files in os.walk(base, followlinks=False):
            dirs[:] = sorted(d for d in dirs if _fold(d) not in EXCLUDED_DIRS and
                             not _fold(d).endswith("-depo") and not sensitive_path(d))
            for name in sorted(files):
                rel = (Path(current) / name).relative_to(root).as_posix()
                if corpus_allowed(rel, config):
                    found.append(safe_path(root, rel))
    if (root / "README.md").exists() and corpus_allowed("README.md", config):
        found.append(safe_path(root, "README.md"))
    return sorted(found, key=lambda p: p.relative_to(root).as_posix())
