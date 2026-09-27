"""Service worker read-only live runtime audit; emits bounded attributed evidence.

Run with isolated Python and an exact expected current manifest SHA. This uses
the accepted publisher/runtime verifier on live files, not historical copies.
Task result_current does not recursively inspect manifest-named runtime members.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import types


ROOT = Path('/Volumes/P-SSD/AngryOwl/Sys4AI')
HELPER = ROOT / 'SKILLS-depo/ontology/scripts/ontology_explorer_assets.py'
HELPER_SHA = '215f2f5043c9f7de4abb02b32e9d28961733d11c120e3b0dec5a0e1b90894db6'
SCHEMA = ROOT / 'ONTOLOGY-depo/schema/explorer-v1.json'


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def captured(path, limit):
    fd = os.open('/', os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in path.absolute().parts[1:-1]:
            new = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = new
        member = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
        try:
            before = os.fstat(member)
            assert stat.S_ISREG(before.st_mode) and before.st_nlink == 1
            assert 0 < before.st_size <= limit
            parts = []
            total = 0
            while True:
                part = os.read(member, min(65536, limit + 1 - total))
                if not part:
                    break
                total += len(part)
                assert total <= limit
                parts.append(part)
            after = os.fstat(member)
            fields = lambda s: (s.st_dev, s.st_ino, s.st_nlink, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
            assert fields(before) == fields(after) and total == before.st_size
            return b''.join(parts)
        finally:
            os.close(member)
    finally:
        os.close(fd)


def ref(path, raw):
    return {'path': str(path.relative_to(ROOT)), 'sha256': digest(raw), 'bytes': len(raw)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--expected-manifest', required=True)
    parser.add_argument('--assets-root', default='SKILLS-depo/ontology/explorer/assets')
    args = parser.parse_args()
    relative = Path(args.assets_root)
    assert not relative.is_absolute() and '..' not in relative.parts
    assets = ROOT / relative
    explorer = assets.parent
    helper_raw = captured(HELPER, 250000)
    assert digest(helper_raw) == HELPER_SHA
    module = types.ModuleType('_accepted_explorer_assets_service_v2_audit')
    module.__file__ = str(HELPER)
    sys.modules[module.__name__] = module
    exec(compile(helper_raw, str(HELPER), 'exec', dont_inherit=True), module.__dict__)
    schema_raw = captured(SCHEMA, 250000)
    schema_sha = digest(schema_raw)
    assert schema_sha == '8e6d0ceb47c98e77d518f4d7c935986ab6982d1a1c15e12377a726e90fbbb7a4'
    manifest_path = assets / 'manifest.json'
    before = captured(manifest_path, 250000)
    assert digest(before) == args.expected_manifest
    options = {'schema_sha256': schema_sha, 'lock_path': explorer / 'package-lock.json',
               'notices_path': explorer / 'THIRD_PARTY_NOTICES.md'}
    first = module.load_assets(assets, **options)
    assert first.manifest_bytes == before
    manifest = json.loads(before)
    observed = []
    for member in manifest['assets']:
        path = assets / member['path']
        raw = module.read_regular(path, member['bytes'])
        assert len(raw) == member['bytes'] and digest(raw) == member['sha256']
        observed.append(ref(path, raw))
    second = module.load_assets(assets, **options)
    assert second.manifest_bytes == before and second.root_identity == first.root_identity
    assert captured(HELPER, 250000) == helper_raw and captured(SCHEMA, 250000) == schema_raw
    assert captured(manifest_path, 250000) == before
    print(json.dumps({'status': 'passed', 'executor': 'Service worker read-only isolated Python',
        'verification_code': ref(Path(__file__).absolute(), captured(Path(__file__).absolute(), 250000)),
        'accepted_asset_helper': ref(HELPER, helper_raw), 'schema': ref(SCHEMA, schema_raw),
        'live_manifest': ref(manifest_path, before), 'build_id': manifest['build_id'],
        'members': observed, 'members_over_helper_evidence_limit': [x for x in observed if x['bytes'] > 250000],
        'checks': ['Exact expected live manifest', 'No-follow parent descriptors and regular single-link members',
                   'Every current member byte count and SHA256', 'Schema, lock, notices and build identity',
                   'Closed HTML/JS/CSS import graph', 'Repeated full package validation and unchanged manifest/root identity'],
        'qualification': 'Current live runtime member validation only. Task result_current alone cannot detect drift of manifest-named members; repeat this audit at each acceptance, affected reverification and final gate. No claim of browser behavior or live authored-source build correspondence.'}, sort_keys=True))


if __name__ == '__main__':
    main()
