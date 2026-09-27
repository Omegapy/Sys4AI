"""Bounded POSIX immutable storage. Actor confinement is cooperative, not a sandbox."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import uuid


class CollaborationError(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)  # Never include rejected content or private paths.


def require(condition, code='COLLAB_INVALID'):
    if not condition:
        raise CollaborationError(code)


def exact(value, fields):
    require(type(value) is dict and set(value) == set(fields), 'COLLAB_FIELDS')


def identifier(value):
    require(isinstance(value, str) and re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]{0,95}', value), 'COLLAB_ID')
    return value


def digest(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')


def private_check(value):
    def check_strings(item):
        if isinstance(item, str):
            require(not any(ord(c) < 32 and c not in '\n\t' for c in item), 'COLLAB_PRIVATE')
        elif isinstance(item, dict):
            for key, val in item.items():
                check_strings(key); check_strings(val)
        elif isinstance(item, list):
            for val in item: check_strings(val)
    check_strings(value)
    raw = encoded(value).decode('utf-8')
    require(not re.search(r'(?:(?<![A-Za-z0-9_-])sk-(?:proj-)?[A-Za-z0-9_-]{12,}|AKIA[A-Z0-9]{16}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|(?:password|api[_-]?key|access[_-]?token)\s*[=:]\s*[^\s]{8,})', raw, re.I), 'COLLAB_PRIVATE')
    require(not any(ord(c) < 32 and c not in '\n\t' for c in raw), 'COLLAB_PRIVATE')


def parts(raw):
    require(isinstance(raw, str) and raw and not Path(raw).is_absolute(), 'COLLAB_PATH')
    bits = raw.split('/')
    require(all(x and x not in ('.', '..') and not any(ord(c) < 32 for c in x) for x in bits), 'COLLAB_PATH')
    return bits


def directory(root, raw='', create=False):
    """Walk with directory-relative no-follow descriptors, including root ancestors."""
    require(hasattr(os, 'O_NOFOLLOW') and os.open in os.supports_dir_fd and os.link in os.supports_dir_fd, 'COLLAB_PLATFORM')
    require(Path(root).is_absolute(), 'COLLAB_PATH')
    bits = list(Path(root).parts[1:]) + (parts(raw) if raw else [])
    fd = os.open('/', os.O_RDONLY | os.O_DIRECTORY)
    try:
        for bit in bits:
            try:
                nxt = os.open(bit, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            except FileNotFoundError:
                if not create:
                    raise
                try:
                    os.mkdir(bit, 0o700, dir_fd=fd)
                    os.fsync(fd)
                except FileExistsError:
                    pass
                nxt = os.open(bit, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = nxt
        return fd
    except OSError as exc:
        os.close(fd)
        raise CollaborationError('COLLAB_MISSING' if isinstance(exc, FileNotFoundError) else 'COLLAB_FILE') from exc


def read_bytes(root, raw, limit=250000):
    bits = parts(raw)
    dfd = directory(root, '/'.join(bits[:-1]))
    try:
        fd = os.open(bits[-1], os.O_RDONLY | os.O_NOFOLLOW, dir_fd=dfd)
        try:
            info = os.fstat(fd)
            require(stat.S_ISREG(info.st_mode) and info.st_size <= limit, 'COLLAB_SIZE')
            chunks = []; size = 0
            while True:
                chunk = os.read(fd, min(65536, limit + 1 - size))
                if not chunk:
                    break
                chunks.append(chunk); size += len(chunk)
                require(size <= limit, 'COLLAB_SIZE')
            return b''.join(chunks)
        finally:
            os.close(fd)
    except OSError as exc:
        raise CollaborationError('COLLAB_FILE') from exc
    finally:
        os.close(dfd)


def read_json(root, raw, limit=250000):
    try:
        return json.loads(read_bytes(root, raw, limit))
    except (ValueError, UnicodeError) as exc:
        if isinstance(exc, CollaborationError):
            raise
        raise CollaborationError('COLLAB_CORRUPT') from exc


def reference(root, ref, limit=250000):
    exact(ref, ('path', 'sha256'))
    require(isinstance(ref['sha256'], str) and re.fullmatch('[0-9a-f]{64}', ref['sha256']), 'COLLAB_HASH')
    raw = read_bytes(root, ref['path'], limit)
    require(digest(raw) == ref['sha256'], 'COLLAB_HASH')
    return raw


def publish(root, raw, payload, limit=65536):
    """Publish complete bytes exclusively; same payload retry returns same reference."""
    private_check(payload)
    content = encoded({'payload': payload, 'sha256': digest(encoded(payload))}) + b'\n'
    require(len(content) <= limit, 'COLLAB_SIZE')
    bits = parts(raw); dfd = directory(root, '/'.join(bits[:-1]), create=True)
    tmp = '.pending-' + uuid.uuid4().hex
    try:
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=dfd)
        try:
            remaining = memoryview(content)
            while remaining:
                remaining = remaining[os.write(fd, remaining):]
            os.fsync(fd)
        finally:
            os.close(fd)
        try:
            os.link(tmp, bits[-1], src_dir_fd=dfd, dst_dir_fd=dfd, follow_symlinks=False)
        except FileExistsError:
            require(read_bytes(root, raw, limit) == content, 'COLLAB_COLLISION')
        os.fsync(dfd)
    except OSError as exc:
        raise CollaborationError('COLLAB_FILE') from exc
    finally:
        try:
            os.unlink(tmp, dir_fd=dfd)
            os.fsync(dfd)
        finally:
            os.close(dfd)
    return {'path': raw, 'sha256': digest(content)}


def record(root, raw, limit=65536):
    data = read_bytes(root, raw, limit)
    try: obj = json.loads(data)
    except (ValueError, UnicodeError) as exc: raise CollaborationError('COLLAB_CORRUPT') from exc
    exact(obj, ('payload', 'sha256'))
    require(obj['sha256'] == digest(encoded(obj['payload'])), 'COLLAB_HASH')
    return obj['payload'], {'path': raw, 'sha256': digest(data)}


def records(root, raw, limit=65536):
    # A missing unpublished directory is empty; a symlink is never empty.
    try:
        dfd = directory(root, raw)
    except CollaborationError as exc:
        if exc.code == 'COLLAB_MISSING': return []
        raise
    try:
        names = sorted(os.listdir(dfd))
    finally:
        os.close(dfd)
    return [record(root, raw + '/' + n, limit) for n in names if not n.startswith('.') and n.endswith('.json')]


def rebuild(root, raw, content, limit=32768):
    """The caller authorizes only its derived view; atomically replace that view."""
    require(len(content) <= limit, 'COLLAB_SIZE')
    bits = parts(raw); dfd = directory(root, '/'.join(bits[:-1]), create=True)
    tmp = '.view-' + uuid.uuid4().hex
    try:
        try:
            target = os.stat(bits[-1], dir_fd=dfd, follow_symlinks=False)
            require(stat.S_ISREG(target.st_mode), 'COLLAB_FILE')
        except FileNotFoundError:
            pass
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=dfd)
        try:
            remaining = memoryview(content)
            while remaining:
                remaining = remaining[os.write(fd, remaining):]
            os.fsync(fd)
        finally:
            os.close(fd)
        os.replace(tmp, bits[-1], src_dir_fd=dfd, dst_dir_fd=dfd); os.fsync(dfd)
    finally:
        try:
            os.unlink(tmp, dir_fd=dfd)
        except FileNotFoundError:
            pass
        os.close(dfd)
