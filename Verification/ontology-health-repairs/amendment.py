"""Freeze and adopt a bounded correction after the recorded first adoption."""
from pathlib import Path
import difflib
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(OUT))
from execution import digest, save


def freeze():
    manifest = json.loads((OUT / 'change-manifest.json').read_text())
    allowed = {'SKILLS-depo/memory/scripts/memory_maintenance.py',
               'SKILLS-depo/memory/tests/test_health_evidence.py'}
    changes = []
    for row in manifest['changes']:
        installed = (ROOT / row['path']).read_bytes()
        assert digest(installed) == row['sha256'], row['path']
        source = (ROOT / row['source']).read_bytes()
        if digest(source) != row['sha256']:
            assert row['source'] in allowed, row['source']
            changes.append({**row, 'expected_sha256': row['sha256'], 'sha256': digest(source)})
            row['sha256'] = digest(source)
    assert {r['source'] for r in changes} == allowed
    save(OUT / 'maintenance-amendment.json', {'reason': 'Observed guarded reindex namespace lookup failed before mutation.',
                                           'changes': changes})
    save(OUT / 'change-manifest.json', manifest)
    patch = []
    for row in manifest['changes']:
        old = OUT / 'root-baseline' / row['path']
        before = old.read_text() if old.exists() else ''
        patch.extend(difflib.unified_diff(before.splitlines(True), (ROOT / row['source']).read_text().splitlines(True),
                                         fromfile=row['path'], tofile=row['source']))
    (OUT / 'source-review.patch').write_text(''.join(patch))
    print(json.dumps({'amendment_changes': len(changes), 'final_artifacts': len(manifest['changes'])}))


def finish():
    sys.path.insert(0, str(ROOT / '.agents/skills/ontology/scripts'))
    from ontology_core import atomic_write
    amendment = json.loads((OUT / 'maintenance-amendment.json').read_text())
    for row in amendment['changes']:
        source = (ROOT / row['source']).read_bytes()
        assert digest(source) == row['sha256']
        if row['owner'] == 'exact-root-adoption':
            atomic_write(ROOT, row['path'], source, row['expected_sha256'])
        assert digest((ROOT / row['path']).read_bytes()) == row['sha256']
    manifest = json.loads((OUT / 'change-manifest.json').read_text())
    observed = {row['path']: digest((ROOT / row['path']).read_bytes()) for row in manifest['changes']}
    assert all(observed[row['path']] == row['sha256'] == digest((ROOT / row['source']).read_bytes()) for row in manifest['changes'])
    save(OUT / 'root-adoption.json', {'status': 'adopted', 'manifest_sha256': digest((OUT / 'change-manifest.json').read_bytes()),
                                    'initial_receipt': 'initial-adoption/root-adoption.json',
                                    'amendment': 'maintenance-amendment.json', 'guard_receipt': 'root-guard-receipt.json',
                                    'reopened': observed})
    print(json.dumps({'adopted': len(observed), 'reopened': True}))


if __name__ == '__main__':
    {'freeze': freeze, 'finish': finish}[sys.argv[1]]()
