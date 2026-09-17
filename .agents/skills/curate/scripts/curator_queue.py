"""Durable transport only; no Task, publication, cache, or model operations.

One selected local coordination root and cooperative POSIX lock are required.
This file protocol does not provide candidate confinement or cross-owner atomicity.
"""
from contextlib import contextmanager
import fcntl
import hashlib
import os
from pathlib import Path
import stat
import uuid

from curator_events import MAX_EVENT_BYTES, identifier, reference, validate_event
from curator_policy import PolicyError, bounded, canonical, decode, digest, exact, moment, require, sha

MAX_RECORDS = 5000
MAX_RECORD_BYTES = 40000
STATUSES = ('pending', 'delivered', 'held', 'consumed')


def _read(fd, name):
    try:
        file_fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
    except FileNotFoundError: return None
    try:
        before = os.fstat(file_fd)
        require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and before.st_size <= MAX_RECORD_BYTES,
                'record_unsafe', 'Expected a bounded single-link regular record.')
        data = b''
        while len(data) <= MAX_RECORD_BYTES:
            chunk = os.read(file_fd, min(8192, MAX_RECORD_BYTES + 1 - len(data)))
            if not chunk: break
            data += chunk
        after = os.fstat(file_fd)
        require((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) ==
                (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns),
                'record_changed', 'Record changed during read.')
        require(len(data) <= MAX_RECORD_BYTES, 'record_limit', 'Oversized record.')
        value = decode(data)
        require(data == canonical(value) + b'\n', 'record_corrupt', 'Expected exact canonical record bytes.')
        return value
    finally: os.close(file_fd)


def _publish(fd, name, value, *, replace=False):
    bounded(value)
    data = canonical(value) + b'\n'
    require(len(data) <= MAX_RECORD_BYTES, 'record_limit', 'Oversized record.')
    existing = _read(fd, name)
    if existing is not None and not replace:
        require(existing == value, 'record_conflict', 'Immutable identity has different bytes.')
        return False
    temporary = '.pending-' + uuid.uuid4().hex
    tmp = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=fd)
    try:
        with os.fdopen(tmp, 'wb') as stream:
            stream.write(data); stream.flush(); os.fsync(stream.fileno())
        # All readers and writers share the lock. A crash leaves either the old
        # record or the complete new record; unpublished temporary files are ignored.
        os.replace(temporary, name, src_dir_fd=fd, dst_dir_fd=fd)
        os.fsync(fd)
    finally:
        try: os.unlink(temporary, dir_fd=fd)
        except FileNotFoundError: pass
    return True


class DeliveryQueue:
    def __init__(self, coordination_root, project_id, repository_id):
        identifier(project_id); identifier(repository_id)
        self.root = Path(coordination_root)
        require(self.root.is_absolute() and str(self.root.resolve()) == str(self.root), 'root', 'Select an exact canonical root.')
        require(self.root.is_dir(), 'root_unavailable', 'Selected root is unavailable.')
        info = self.root.stat(); self._root_identity = (info.st_dev, info.st_ino)
        self.project_id, self.repository_id = project_id, repository_id

    @contextmanager
    def _directory(self, parts, write=False):
        descriptors = []
        try:
            fd = os.open(self.root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW); descriptors.append(fd)
            info = os.fstat(fd)
            require((info.st_dev, info.st_ino) == self._root_identity, 'root_changed', 'Selected coordination root was replaced.')
            for part in ('control_records', 'curator', *parts):
                if write:
                    try: os.mkdir(part, 0o700, dir_fd=fd); os.fsync(fd)
                    except FileExistsError: pass
                try: next_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                except FileNotFoundError:
                    yield None; return
                fd = next_fd; descriptors.append(fd)
            yield fd
        finally:
            for fd in reversed(descriptors): os.close(fd)

    @contextmanager
    def _locked(self, write=False):
        with self._directory((), write) as fd:
            if fd is None:
                yield False; return
            try: lock = os.open('.delivery.lock', os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
            except FileNotFoundError:
                if not write:
                    # A first writer creates the lock before publishing any records.
                    require(not any(n != '.delivery.lock' for n in os.listdir(fd)), 'lock_missing', 'Existing transport has no lock.')
                    yield False; return
                try: lock = os.open('.delivery.lock', os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=fd)
                except FileExistsError: lock = os.open('.delivery.lock', os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
                os.fsync(fd)
            try:
                info = os.fstat(lock)
                require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and info.st_size == 0,
                        'lock_unsafe', 'Expected an empty single-link lock file.')
                try: fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError as exc: raise PolicyError('transport_busy', 'Transport is busy; retry the same request.') from exc
                yield True
            finally: os.close(lock)

    def _event(self, event_id):
        identifier(event_id)
        with self._directory(('events',)) as fd:
            value = None if fd is None else _read(fd, event_id + '.json')
        require(value is not None, 'event_missing', 'Event is unavailable.')
        validate_event(value)
        require(value['event_id'] == event_id, 'event_identity', 'Filename and event differ.')
        self._scope(value)
        return value

    def _scope(self, event):
        require((event['project_id'], event['repository_id'], event['coordination_root']) ==
                (self.project_id, self.repository_id, str(self.root)), 'event_scope', 'Event belongs to a different coordination root.')

    def enqueue(self, event):
        validate_event(event); self._scope(event)
        with self._locked(True), self._directory(('events',), True) as fd:
            require(len([n for n in os.listdir(fd) if not n.startswith('.pending-')]) < MAX_RECORDS
                    or _read(fd, event['event_id'] + '.json') is not None, 'queue_limit', 'Selected queue bound reached.')
            created = _publish(fd, event['event_id'] + '.json', event)
        return {'event_id': event['event_id'], 'sha256': digest(event), 'created': created}

    def _chain(self, parts, validator):
        with self._directory(parts) as fd:
            if fd is None: return []
            names = [n for n in os.listdir(fd) if n != 'current.json' and not n.startswith('.pending-')]
            require(len(names) <= MAX_RECORDS and all(len(n) == 15 and n[:10].isdigit() and n.endswith('.json') for n in names),
                    'journal_corrupt', 'Unknown or oversized journal contents.')
            records = []
            for index, name in enumerate(sorted(names), 1):
                require(name == f'{index:010d}.json', 'journal_gap', 'Journal revision is missing.')
                record = _read(fd, name); validator(record)
                require(record['revision'] == index and record['previous_sha256'] == (digest(records[-1]) if records else None),
                        'journal_chain', 'Journal chain differs.')
                records.append(record)
            return records

    def _receipts(self, event):
        def validate(record):
            exact(record, ('schema_version', 'revision', 'previous_sha256', 'receipt_id', 'event_id', 'event_sha256', 'status', 'reference', 'reason', 'created_at'))
            require(type(record['schema_version']) is int and record['schema_version'] == 1, 'version', 'Unknown receipt version.')
            require(type(record['revision']) is int, 'revision', 'Expected revision.')
            identifier(record['receipt_id']); moment(record['created_at'])
            require(record['event_id'] == event['event_id'] and record['event_sha256'] == digest(event), 'receipt_scope', 'Receipt does not bind the event.')
            require(record['status'] in STATUSES and type(record['reason']) is str and 0 < len(record['reason']) <= 2000,
                    'receipt_status', 'Receipt describes delivery only.')
            if record['reference'] is not None: reference(record['reference'])
            require(record['status'] != 'consumed' or record['reference'] is not None, 'receipt_reference', 'Consumed delivery requires an attributable owner reference.')
        records = self._chain(('operations', 'deliveries', event['event_id']), validate)
        for previous, current in zip(records, records[1:]):
            require(previous['status'] != 'consumed', 'receipt_terminal', 'Consumed delivery cannot be reopened.')
        require(len({r['receipt_id'] for r in records}) == len(records), 'receipt_duplicate', 'Repeated receipt ID.')
        return records

    def record_delivery(self, event_id, expected_sha256, *, receipt_id, status, reference=None, reason, created_at):
        identifier(receipt_id)
        with self._locked(True):
            event = self._event(event_id); records = self._receipts(event)
            current = records[-1] if records else None
            value = {'schema_version': 1, 'revision': len(records) + 1, 'previous_sha256': expected_sha256,
                     'receipt_id': receipt_id, 'event_id': event_id, 'event_sha256': digest(event),
                     'status': status, 'reference': reference, 'reason': reason, 'created_at': created_at}
            for old in records:
                if old['receipt_id'] == receipt_id:
                    value['revision'] = old['revision']
                    require(value == old, 'receipt_conflict', 'Retried receipt differs.')
                    return old
            require(expected_sha256 == (digest(current) if current else None), 'receipt_stale', 'Delivery state changed.')
            require(current is None or current['status'] != 'consumed', 'receipt_terminal', 'Consumed delivery cannot be reopened.')
            require(status in STATUSES and type(reason) is str and 0 < len(reason) <= 2000, 'receipt_status', 'Delivery status is invalid.')
            moment(created_at)
            if reference is not None:
                from curator_events import reference as validate_reference
                validate_reference(reference)
            require(status != 'consumed' or reference is not None, 'receipt_reference', 'Consumed delivery requires an owner reference.')
            require(value['revision'] <= MAX_RECORDS, 'journal_limit', 'Selected journal bound reached.')
            with self._directory(('operations', 'deliveries', event_id), True) as fd:
                _publish(fd, f'{value["revision"]:010d}.json', value)
            return value

    def status(self):
        """Read-only inventory. A cursor never hides a pending correction."""
        with self._locked() as exists:
            if not exists: return []
            with self._directory(('events',)) as fd:
                if fd is None: return []
                names = sorted(n for n in os.listdir(fd) if not n.startswith('.pending-'))
            require(len(names) <= MAX_RECORDS, 'queue_limit', 'Queue inventory exceeds bound.')
            result = []
            for name in names:
                require(name.endswith('.json'), 'event_corrupt', 'Unknown transport record.')
                event = self._event(name[:-5]); records = self._receipts(event)
                result.append({'event': event, 'sha256': digest(event), 'status': records[-1]['status'] if records else 'pending',
                               'receipt': records[-1] if records else None})
            return result

    def _cursor(self, consumer, branch):
        identifier(consumer)
        key = digest([consumer, branch])
        def validate(value):
            exact(value, ('schema_version', 'revision', 'previous_sha256', 'consumer', 'branch', 'event_id', 'event_sha256'))
            require(type(value['schema_version']) is int and value['schema_version'] == 1 and type(value['revision']) is int,
                    'cursor_version', 'Unknown cursor version.')
            require(value['consumer'] == consumer and value['branch'] == branch, 'cursor_scope', 'Cursor scope changed.')
            event = self._event(value['event_id'])
            require(event['branch'] == branch and value['event_sha256'] == digest(event), 'cursor_binding', 'Cursor is not bound to the immutable delivery.')
        records = self._chain(('cursors', 'delivery-' + key), validate)
        head = records[-1] if records else None
        with self._directory(('cursors', 'delivery-' + key)) as fd:
            pointer = _read(fd, 'current.json') if fd is not None else None
        require(pointer is None or pointer in records, 'cursor_pointer', 'Cursor pointer is not an exact committed revision.')
        return key, head, pointer != head

    def cursor(self, consumer, branch):
        with self._locked() as exists:
            if not exists: return {'record': None, 'recovery_pending': False}
            _, head, pending = self._cursor(consumer, branch)
            return {'record': head, 'recovery_pending': pending}

    def advance_cursor(self, consumer, branch, expected_sha256, event_id):
        with self._locked(True):
            key, head, _ = self._cursor(consumer, branch)
            event = self._event(event_id)
            require(event['branch'] == branch, 'cursor_scope', 'Cursor cannot cross branches.')
            value = {'schema_version': 1, 'revision': 1 if head is None else head['revision'] + 1,
                     'previous_sha256': expected_sha256, 'consumer': consumer, 'branch': branch,
                     'event_id': event_id, 'event_sha256': digest(event)}
            if head and head['previous_sha256'] == expected_sha256 and head['event_id'] == event_id:
                value = head  # Same request after a committed journal / interrupted pointer write.
            else:
                require(expected_sha256 == (digest(head) if head else None), 'cursor_stale', 'Cursor changed.')
            require(value['revision'] <= MAX_RECORDS, 'journal_limit', 'Selected journal bound reached.')
            with self._directory(('cursors', 'delivery-' + key), True) as fd:
                _publish(fd, f'{value["revision"]:010d}.json', value)
                _publish(fd, 'current.json', value, replace=True)
            return value
