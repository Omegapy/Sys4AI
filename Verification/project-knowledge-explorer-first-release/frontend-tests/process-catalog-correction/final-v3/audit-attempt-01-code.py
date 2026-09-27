"""Read-only current evidence admission. Writes new final-v3 records only."""
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess

ROOT = Path('/Volumes/P-SSD/AngryOwl/Sys4AI')
OUT = Path(__file__).absolute().parent
F = ROOT / 'Verification/project-knowledge-explorer-first-release/frontend-tests'
E = F / 'process-catalog-correction'
S = ROOT / 'Verification/project-knowledge-explorer-first-release/service-tests/service-v3'
M = ROOT / 'Tasks/Task-implement-project-knowledge-explorer-full-first-release-2026-09-19--1FA1F620/artifacts/orchestration/manager'
PACKET = M / 'frontend-final-v3-input-packet.json'
PACKET_SHA = '36bd44e7011ce023ed52b71b29991782e580befd4caf82af823f641ffc192197'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path):
    path = Path(path)
    if not path.is_absolute():
        path = ROOT / path
    assert '..' not in path.parts
    fd = os.open('/', os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in path.parts[1:-1]:
            new = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = new
        member = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
        try:
            before = os.fstat(member)
            assert stat.S_ISREG(before.st_mode) and before.st_nlink == 1, str(path)
            blocks = []
            while block := os.read(member, 1048576):
                blocks.append(block)
            signature = lambda s: (s.st_dev, s.st_ino, s.st_mode, s.st_nlink, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
            assert signature(before) == signature(os.fstat(member)) == signature(os.stat(path.name, dir_fd=fd, follow_symlinks=False)), str(path)
            raw = b''.join(blocks)
            assert len(raw) == before.st_size
            return raw
        finally:
            os.close(member)
    finally:
        os.close(fd)


def ref(path):
    path = Path(path)
    if not path.is_absolute():
        path = ROOT / path
    raw = read(path)
    return {'path': str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path), 'sha256': sha(raw), 'bytes': len(raw)}


def verify(row, base=ROOT):
    path = Path(row['path'])
    raw = read(path if path.is_absolute() else base / path)
    assert sha(raw) == row['sha256'] and ('bytes' not in row or len(raw) == row['bytes']), str(path)
    return raw


def load(path):
    return json.loads(read(path))


def write(name, obj):
    raw = (json.dumps(obj, indent=2, ensure_ascii=False) + '\n').encode()
    assert len(raw) <= 250000
    with (OUT / name).open('xb') as f:
        f.write(raw)


def refs(obj):
    if isinstance(obj, dict):
        if isinstance(obj.get('path'), str) and isinstance(obj.get('sha256'), str):
            yield obj
        for value in obj.values():
            yield from refs(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from refs(value)


def tree(base, exclude=None):
    rows = []
    for parent, dirs, files in os.walk(base, followlinks=False):
        dirs[:] = [d for d in dirs if Path(parent) / d != exclude]
        assert all(not (Path(parent) / d).is_symlink() for d in dirs)
        rows.extend(ref(Path(parent) / name) for name in files)
    return sorted(rows, key=lambda x: x['path'])


def main():
    assert sha(read(PACKET)) == PACKET_SHA
    packet = load(PACKET)
    assert len(packet['references']) == 196 and len(packet['criteria']) == 29
    assert len(packet['original_context_preserved']) == 37 and len(packet['authorized_input_evolution']) == 7
    for row in packet['references'] + packet['original_context_preserved']:
        verify(row)
    for row in packet['authorized_input_evolution']:
        if row['current']:
            verify(row['current'])
        else:
            assert not (ROOT / row['previous']['path']).exists()
    old_tree = tree(F, OUT)
    product_tree = tree(ROOT / 'SKILLS-depo/ontology/explorer')
    # Verify complete immutable evidence inventories, including earlier failures.
    artifact_rows = {}
    queue = [ref(E / 'delivery.json'), ref(S / 'delivery.json')]
    while queue:
        row = queue.pop()
        key = (row['path'], row['sha256'])
        if key in artifact_rows:
            continue
        raw = verify(row)
        artifact_rows[key] = {k: row[k] for k in ('path', 'sha256', 'bytes') if k in row}
        if row['path'].endswith('.json'):
            for child in refs(json.loads(raw)):
                path = child['path']
                # Source preimages embedded in old reports are historical assertions,
                # not current-source admission. Current inputs are checked below.
                if path.startswith('Verification/') or (path.startswith('Tasks/') and '/artifacts/' in path):
                    queue.append(child)
    unit = load(E / 'unit-01.json')
    for row in unit['inputs'] + unit['test_inputs']:
        verify(row)
    assert unit['exit_code'] == 0 and len(json.loads(unit['stdout'])['checks']) == 20
    build = load(E / 'build-inputs-01.json')
    stage = Path(load(E / 'build-01.json')['stage'])
    sources = []
    for row in build['inputs']['record']['files']:
        p = row['path']
        rel = 'ONTOLOGY-depo/schema/' + Path(p).name if p.startswith('$schema/') else 'SKILLS-depo/ontology/scripts/' + Path(p).name if p.startswith('$tooling/') else 'SKILLS-depo/ontology/explorer/' + p
        expected = dict(row, path=rel)
        assert verify(expected) == verify(expected, stage)
        sources.append(expected)
    source_paths = {str(p.relative_to(ROOT / 'SKILLS-depo/ontology/explorer')) for p in (ROOT / 'SKILLS-depo/ontology/explorer/src').rglob('*') if p.is_file()}
    assert source_paths == {r['path'] for r in build['inputs']['record']['files'] if r['path'].startswith('src/')}
    deps = load(E / 'build01-dependency-admission.json')
    depfiles = [r for part in deps['file_parts'] for r in json.loads(verify(part))['files']]
    depbase = Path(deps['root'])
    staged_app = stage / 'SKILLS-depo/ontology/explorer'
    assert len(depfiles) == 1001
    for row in depfiles:
        assert verify(row, depbase) == verify(row, staged_app)
    for base in (depbase, staged_app):
        actual, links = set(), {}
        for parent, dirs, names in os.walk(base / 'node_modules', followlinks=False):
            assert all(not (Path(parent) / d).is_symlink() for d in dirs)
            for name in names:
                p = Path(parent) / name
                rel = str(p.relative_to(base))
                if p.is_symlink():
                    links[rel] = os.readlink(p)
                else:
                    actual.add(rel)
        assert actual == {r['path'] for r in depfiles} | {'node_modules/.package-lock.json'}
        assert links == {r['path']: r['target'] for r in deps['bin_links']}
        for link in deps['bin_links']:
            assert str((base / link['path']).resolve().relative_to(base)) == link['resolved']
    assert verify(deps['hidden_install_lock']) == read(staged_app / 'node_modules/.package-lock.json')
    for tool in deps['tools']:
        assert str(Path(tool['invocation']).resolve()) == tool['resolved']['path']
        verify(tool['resolved'])
    browser = []
    for check in load(E / 'current-checks.json')['checks'][:5]:
        job = json.loads(verify(check['job']))
        inputs = json.loads(verify(check['inputs']))['files']
        for row in inputs:
            verify(row, Path(job['stage']))
            if row['path'].startswith(('SKILLS-depo/', 'ONTOLOGY-depo/')):
                verify(row)
        report = json.loads(verify(check['report']))
        receipt = json.loads(verify(check['receipt']))
        assert receipt['exit_code'] == 0 and receipt['stdout_sha256'] == check['report']['sha256']
        assert receipt['observed_descendants_exited'] and not receipt['post_verification_errors']
        for tool in receipt['external_tools']:
            verify(dict(tool, path=tool['resolved']))
        browser.append({'id': check['id'], 'groups': check['groups'], 'inputs': len(inputs), 'report': check['report'], 'receipt': check['receipt'], 'stage_and_live_product_closure': True})
    assert sum(x['groups'] for x in browser) == 50
    for row in refs(load(S / 'output-manifest.json')):
        verify(row)
    manifest = ref(ROOT / 'SKILLS-depo/ontology/explorer/assets/manifest.json')
    assert read(ROOT / manifest['path']) == read(staged_app / 'assets/manifest.json')
    command = [str(ROOT / '.venv/bin/python'), '-I', '-B', str(S / 'audit-live-runtime.py'), '--expected-manifest', manifest['sha256']]
    run = subprocess.run(command, capture_output=True, timeout=45)
    assert run.returncode == 0 and not run.stderr
    runtime = json.loads(run.stdout)
    assert runtime['status'] == 'passed' and len(runtime['members']) == 5
    for row in packet['references']:
        verify(row)
    assert old_tree == tree(F, OUT) and product_tree == tree(ROOT / 'SKILLS-depo/ontology/explorer')
    write('input-admission.json', {'status': 'passed', 'packet': ref(PACKET), 'references': packet['references'], 'original_context_preserved': packet['original_context_preserved'], 'authorized_input_evolution': packet['authorized_input_evolution'], 'roles': [ref(ROOT / x) for x in ['SOUL.md', 'Roles/project-sub-agent/AGENTS.md', 'Roles/project-sub-agent/ROLE.md']], 'scope': packet['writes']})
    write('preservation-prestate.json', {'status': 'captured_and_rechecked', 'prior_frontend_files': old_tree, 'product_and_tests': product_tree})
    closure = sorted(artifact_rows.values(), key=lambda r: (r['path'], r['sha256']))
    for offset in range(0, len(closure), 300):
        write(f'evidence-closure-{offset // 300:02}.json', {'status': 'passed', 'references': closure[offset:offset + 300], 'meaning': 'Immutable referenced artifact bytes verified recursively; embedded historical source assertions are not current-source admission.'})
    with (OUT / 'live-runtime-raw.json').open('xb') as f:
        f.write(run.stdout)
    write('current-audit.json', {'status': 'passed', 'executor': '/root/explorer_manager_g3/frontend_worker', 'verification_code': ref(Path(__file__)), 'packet_refs': 196, 'original_context_refs': 37, 'authorized_evolutions': 7, 'recursive_artifact_refs': len(closure), 'unit_current_inputs': 20, 'unit_groups': 20, 'authored_build_inputs': sources, 'source_inventory_exact': True, 'build_stage': str(stage), 'dependency_files_live_and_staged': 1001, 'dependency_links_live_and_staged': 4, 'dependency_closure_exact': True, 'browser_current_closure': browser, 'browser_groups': 50, 'runtime_command': command, 'runtime_exit_code': run.returncode, 'runtime_report': ref(OUT / 'live-runtime-raw.json'), 'runtime_executor_qualification': 'This worker executed the unchanged accepted verifier. Its raw Service worker label is static script text, not executor attribution. No new listener/browser/test/build execution.', 'live_manifest': manifest, 'build_id': runtime['build_id'], 'runtime_members': runtime['members'], 'prior_frontend_files_preserved': len(old_tree), 'product_test_files_preserved': len(product_tree)})
    print(json.dumps({'status': 'passed', 'packet_refs': 196, 'recursive_artifact_refs': len(closure), 'unit_groups': 20, 'browser_groups': 50, 'build_inputs': len(sources), 'dependency_files': 1001, 'runtime_members': 5, 'prior_frontend_files': len(old_tree)}))


if __name__ == '__main__':
    main()
