"""Resolved file identities and proof admission. A manifest is not OS proof."""
from contextlib import contextmanager
import hashlib
import os
from pathlib import Path
import stat
import unicodedata

from curator_policy import PolicyError, bounded, digest, exact, require, texts

CHANNELS = frozenset(('commandExecution', 'fileChange', 'dynamicToolCall', 'mcpToolCall',
    'collabAgentToolCall', 'webSearch', 'imageView', 'imageGeneration', 'permissionEscalation'))


def canonical_root(path):
    p = Path(path)
    require(p.is_absolute(), 'root', 'Root must be absolute.')
    resolved = p.resolve(strict=True)
    require(resolved.is_dir(), 'root', 'Root must be a directory.')
    return resolved


@contextmanager
def parent_descriptor(root, relative):
    root = canonical_root(root); p = Path(relative)
    require(not p.is_absolute() and p.parts and '..' not in p.parts and str(p) == relative,
            'path', 'Expected normalized relative path.')
    descriptor = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for part in p.parts[:-1]:
            actual = os.listdir(descriptor)
            matches = [n for n in actual if unicodedata.normalize('NFC', n).casefold() == unicodedata.normalize('NFC', part).casefold()]
            require(matches == [part], 'alias', 'Directory spelling or normalization is ambiguous.')
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=descriptor)
            os.close(descriptor); descriptor = child
        matches = [n for n in os.listdir(descriptor) if unicodedata.normalize('NFC', n).casefold() == unicodedata.normalize('NFC', p.name).casefold()]
        require(matches in ([], [p.name]), 'alias', 'File spelling or normalization is ambiguous.')
        yield descriptor, p.name
    finally:
        os.close(descriptor)


def file_snapshot(root, relative, max_bytes=25000000):
    with parent_descriptor(root, relative) as (parent, name):
        try:fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
        except OSError as exc:
            raise PolicyError('file_open_held','File is unavailable or became an unsafe alias before its no-follow open.') from exc
        try:
            before = os.fstat(fd)
            require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and before.st_size <= max_bytes,
                    'unsafe_file', 'Expected bounded single-link regular file.')
            hasher = hashlib.sha256(); size = 0
            while True:
                data = os.read(fd, min(65536, max_bytes + 1 - size))
                if not data: break
                hasher.update(data); size += len(data)
                require(size <= max_bytes, 'file_limit', 'File grew beyond bound.')
            after = os.fstat(fd); current = os.stat(name, dir_fd=parent, follow_symlinks=False)
            identity = lambda s: (s.st_dev, s.st_ino, s.st_mode, s.st_nlink, s.st_size, s.st_mtime_ns)
            require(identity(before) == identity(after) == identity(current), 'file_changed', 'File identity changed during read.')
            return {'path': relative, 'sha256': hasher.hexdigest(),
                    'device': after.st_dev, 'inode': after.st_ino, 'size': size, 'mode': stat.S_IMODE(after.st_mode)}
        finally:
            os.close(fd)


def source_manifest(root, paths):
    root = canonical_root(root); texts(paths)
    entries = [file_snapshot(root, name) for name in sorted(paths)]
    return {'schema_version': 1, 'root': str(root), 'device': root.stat().st_dev,
            'inode': root.stat().st_ino, 'files': entries}


def verify_manifest(manifest):
    exact(manifest, ('schema_version', 'root', 'device', 'inode', 'files'))
    require(manifest['schema_version'] == 1, 'manifest_version', 'Unsupported source manifest.')
    current = source_manifest(manifest['root'], [e['path'] for e in manifest['files']])
    require(current == manifest, 'trusted_source_changed', 'Frozen trusted source/import closure changed.')
    return current


def validate_profile(profile):
    bounded(profile)
    exact(profile, ('schema_version', 'name', 'read_roots', 'write_roots', 'denied_roots',
                    'executables', 'channels', 'network', 'config_sha256'))
    require(profile['schema_version'] == 1, 'profile_version', 'Unsupported profile.')
    for key in ('read_roots', 'write_roots', 'denied_roots', 'executables', 'network'): texts(profile[key])
    for key in ('read_roots', 'write_roots', 'denied_roots'):
        for raw in profile[key]:
            require(str(canonical_root(raw)) == raw, 'root_alias', 'Profile requires canonical resolved roots.')
    for candidate in profile['read_roots'] + profile['write_roots']:
        for protected in profile['denied_roots']:
            require(not Path(protected).is_relative_to(candidate) and not Path(candidate).is_relative_to(protected),
                    'profile_overlap', 'Allowed roots overlap protected roots.')
    exact(profile['channels'], CHANNELS)
    require(all(mode in ('disabled', 'broker', 'confined') for mode in profile['channels'].values()), 'channel', 'Unknown channel selection.')
    require(profile['channels']['permissionEscalation'] == 'disabled', 'escalation', 'Candidate escalation must be disabled.')
    for executable in profile['executables']:
        require(str(Path(executable).resolve(strict=True)) == executable, 'executable_alias', 'Use resolved executable and interpreter paths.')
        require(Path(executable).is_file() and os.access(executable, os.X_OK), 'executable', 'Missing selected executable.')
    return profile


def proof_gate(profile, manifest, runtime_binding, proof):
    """Admission consumes trusted release evidence; candidate-supplied booleans are insufficient."""
    validate_profile(profile); verify_manifest(manifest)
    exact(proof, ('state', 'profile_sha256', 'manifest_sha256', 'runtime', 'channels', 'cases'))
    require(proof['state'] == 'passed' and proof['profile_sha256'] == digest(profile)
            and proof['manifest_sha256'] == digest(manifest) and proof['runtime'] == runtime_binding,
            'enforcement_unproven', 'No current source-bound native confinement proof.')
    exact(proof['channels'], CHANNELS)
    require(all(v in ('observed_denied', 'observed_confined', 'observed_disabled', 'observed_broker') for v in proof['channels'].values()),
            'channel_unproven', 'Every enabled channel requires direct evidence.')
    require(set(proof['cases']) >= {'NP-007','NP-010','NP-011','NP-012'} and
            all(v == 'passed' for v in proof['cases'].values()), 'enforcement_unproven', 'Required native adversarial cases are not passed.')
    return True

class VerificationAdmission:
    """Trusted-only first-proof admission; never a production readiness receipt."""
    def __init__(self, packet, reviewed_sha256):
        from curator_policy import moment
        from datetime import datetime, timezone
        exact(packet, ('schema_version','scope_id','root','device','inode','marker_sha256',
                       'manifest_sha256','profile_sha256','runtime','tools','expires_at','synthetic_only'))
        require(packet['schema_version'] == 1 and packet['synthetic_only'] is True,
                'verification_scope', 'Only a newly created synthetic proof scope is eligible.')
        require(digest(packet) == reviewed_sha256, 'verification_review', 'Host review does not bind this exact scope.')
        require(datetime.now(timezone.utc) < moment(packet['expires_at']), 'verification_expired', 'Proof scope expired.')
        self.packet = dict(packet); self.reviewed_sha256 = reviewed_sha256

    def check(self, root, profile, manifest, runtime, tool):
        from curator_policy import moment
        from datetime import datetime, timezone
        packet = self.packet
        require(digest(packet) == self.reviewed_sha256 and datetime.now(timezone.utc) < moment(packet['expires_at']),
                'verification_expired', 'Exact reviewed scope is stale or changed.')
        selected = canonical_root(root)
        require(str(selected) == packet['root'] and selected.stat().st_dev == packet['device']
                and selected.stat().st_ino == packet['inode'], 'verification_root', 'Disposable scope identity changed.')
        marker = file_snapshot(selected,'.curator-disposable-proof.json')
        require(marker['sha256'] == packet['marker_sha256'], 'verification_root', 'Disposable proof marker changed.')
        require(digest(manifest) == packet['manifest_sha256'] and digest(profile) == packet['profile_sha256']
                and runtime == packet['runtime'] and tool in packet['tools'], 'verification_scope', 'Runtime, source, profile or tool exceeds reviewed proof scope.')
        validate_profile(profile); verify_manifest(manifest)
        return True
