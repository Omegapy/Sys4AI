"""Current read-only closure/preservation audit; writes new bounded Q evidence only."""
import difflib
import importlib.util
import json
import os
from pathlib import Path
import subprocess

ROOT = Path('/Volumes/P-SSD/AngryOwl/Sys4AI')
OUT = Path(__file__).absolute().parent
APP = ROOT / 'SKILLS-depo/ontology/explorer'
M = ROOT / 'Tasks/Task-implement-project-knowledge-explorer-full-first-release-2026-09-19--1FA1F620/artifacts/orchestration/manager'
spec = importlib.util.spec_from_file_location('readonly_audit', OUT.parent / 'process-catalog-correction/final-v3/audit.py')
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)
PACKET_SHA = 'c05649cb9c9bbb4407541f44aeaa7c9c6694805a9072b7268137df1ffe7ea479'
MANIFEST_SHA = 'b27225ad7b3d57277cb962f4cebbff0b778563a327ec4b0dce0cfa324cdbcb37'
CHANGED = {str(APP.relative_to(ROOT) / p) for p in ['src/app.ts', 'src/sources.ts', 'src/styles.css', 'tests/frontend/narrow.cjs']}

def write(name, obj):
    raw = (json.dumps(obj, indent=2, ensure_ascii=False) + '\n').encode()
    assert len(raw) <= 250000
    with (OUT / name).open('xb') as f:
        f.write(raw)

def is_asset(path):
    return path.startswith('SKILLS-depo/ontology/explorer/assets/')

def main():
    packet_ref = {'path': str(M / 'frontend-narrow-repair-v4-input-packet-02.json'), 'sha256': PACKET_SHA}
    packet = json.loads(a.verify(packet_ref))
    assert len(packet['references']) == 233 and len(packet['criteria']) == 29
    initial = a.load(OUT / 'input-admission.json')
    before = a.load(OUT / 'preservation-before.json')
    assert initial['references'] == packet['references']
    for row in initial['roles'] + packet['baseline_inputs']:
        a.verify(row)
    preimages = {r['live']['path']: r for r in initial['preimages']}
    for r in preimages.values():
        assert a.sha(a.verify(r['preimage'])) == r['live']['sha256']
    old = {r['path']: r for r in before['all_product_and_tests']}
    current_tree = a.tree(APP)
    current = {r['path']: r for r in current_tree}
    deltas = []
    for p in sorted(set(old) | set(current)):
        previous, present = old.get(p), current.get(p)
        if previous == present:
            continue
        assert p in CHANGED or is_asset(p), p
        if previous:
            assert p in preimages and previous == preimages[p]['live']
        deltas.append({'path': p, 'previous': previous, 'current': present, 'preimage': preimages[p]['preimage'] if previous else None})
    assert {r['path'] for r in deltas if not is_asset(r['path'])} == CHANGED
    assert before['prior_frontend_evidence'] == a.tree(OUT.parent, OUT)
    evolutions = []
    unchanged = []
    for row in packet['references']:
        path = row['path']
        actual = a.ref(ROOT / path) if (ROOT / path).exists() else None
        if actual and actual['sha256'] == row['sha256'] and actual['bytes'] == row['bytes']:
            unchanged.append(actual)
        else:
            assert path in CHANGED or is_asset(path), path
            assert path in preimages and preimages[path]['live']['sha256'] == row['sha256']
            evolutions.append({'previous_packet_ref': row, 'preserved_preimage': preimages[path]['preimage'], 'current': actual, 'reason': 'Explicit round4 narrow-layout correction; generated member renames/removal follow accepted manifest-last publisher.'})
    stage = Path(a.load(OUT / 'build-03.json')['stage'])
    sources = []
    for row in a.load(OUT / 'build-inputs-03.json')['inputs']['record']['files']:
        p = row['path']
        rel = 'ONTOLOGY-depo/schema/' + Path(p).name if p.startswith('$schema/') else 'SKILLS-depo/ontology/scripts/' + Path(p).name if p.startswith('$tooling/') else 'SKILLS-depo/ontology/explorer/' + p
        expected = dict(row, path=rel)
        assert a.verify(expected) == a.verify(expected, stage)
        sources.append(expected)
    assert {str(p.relative_to(APP)) for p in (APP / 'src').rglob('*') if p.is_file()} == {r['path'][len('SKILLS-depo/ontology/explorer/'):] for r in sources if '/src/' in r['path']}
    deps = a.load(OUT / 'build01-dependency-admission.json')
    depfiles = [r for part in deps['file_parts'] for r in json.loads(a.verify(part))['files']]
    assert len(depfiles) == 1001
    depbase = Path(deps['root'])
    staged_app = stage / 'SKILLS-depo/ontology/explorer'
    for row in depfiles:
        assert a.verify(row, depbase) == a.verify(row, staged_app)
    assert a.verify(deps['hidden_install_lock']) == a.read(staged_app / 'node_modules/.package-lock.json')
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
    for tool in deps['tools']:
        assert str(Path(tool['invocation']).resolve()) == tool['resolved']['path']
        a.verify(tool['resolved'])
    units = []
    for name, groups in [('unit-06.json', 6), ('unit-07.json', 20)]:
        record = a.load(OUT / name)
        for row in record['inputs'] + record['test_inputs']:
            a.verify(row)
        report = json.loads(record['stdout'])
        assert record['exit_code'] == 0 and not record['stderr'] and report['status'] == 'passed'
        assert len(report['checks']) == groups and all(r['status'] == 'passed' for r in report['checks'])
        units.append({'id': 'focused_unit' if groups == 6 else 'existing_unit', 'receipt': a.ref(OUT / name), 'groups': groups, 'input_refs': record['inputs'] + record['test_inputs'], 'qualification': report['qualification']})
    browser = []
    for number, groups in [(14, 1), (15, 13), (16, 28), (17, 4), (18, 7)]:
        job_path = OUT / f'host-browser-job-{number:02}.json'
        job = a.load(job_path)
        inputs_ref = a.ref(OUT / f'stage-browser-{number:02}-inputs.json')
        assert a.verify(job['manifest']) == a.verify(inputs_ref)
        inputs = json.loads(a.verify(inputs_ref))['files']
        live = []
        for row in inputs:
            a.verify(row, Path(job['stage']))
            if row['path'].startswith(('SKILLS-depo/', 'ONTOLOGY-depo/')):
                a.verify(row)
                live.append(row)
        assert len(live) == 107
        kind = job['kind']
        stage_only = {'host-playwright-driver.py': OUT / f'host-{kind}.py', f'browser-{kind}.cjs': OUT / f'browser-{kind}.cjs', 'headless-runtime.json': ROOT / job['headless_runtime_admission']['path']}
        if kind in ('narrow', 'advanced', 'session'):
            stage_only['fixture.py'] = OUT / 'fixture.py'
        if kind == 'advanced':
            stage_only['mutate-snapshot.py'] = OUT / 'mutate-snapshot.py'
        for p, source in stage_only.items():
            assert a.read(Path(job['stage']) / p) == a.read(source)
        assert json.loads(a.read(Path(job['stage']) / 'external-tools.json'))['tools'] == job['external_tools']
        assert {r['path'] for r in inputs if r not in live} == set(stage_only) | {'external-tools.json'}
        for tool in job['external_tools']:
            assert str(Path(tool['path']).resolve()) == tool['resolved']
            a.verify(dict(tool, path=tool['resolved']))
        assert len(job['external_tools']) == 28
        folder = OUT / f'host-{number:02}'
        report, receipt = a.load(folder / 'stdout.json'), a.load(folder / 'receipt.json')
        assert receipt['job']['sha256'] == a.ref(job_path)['sha256']
        assert receipt['manifest_sha256'] == job['manifest']['sha256']
        assert receipt['stdout_sha256'] == a.ref(folder / 'stdout.json')['sha256']
        assert receipt['status'] == report['status'] == 'passed' and receipt['exit_code'] == 0
        assert not receipt['post_verification_errors'] and not receipt['remaining_owned_descendants']
        assert not receipt['stderr_bytes'] and not receipt['timed_out'] and not receipt['emergency_signals']
        assert not report['csp_violations'] and not report['page_errors'] and not report['nonlocal_requests']
        assert report['owned_read_worker_reaped'] and report['observed_browser_descendants_exited']
        assert len(report['checks']) == groups
        for row in a.load(folder / 'attribution.json')['images']:
            assert a.verify(row['original']) == a.verify(row['copy'])
        browser.append({'id': f'browser{number:02}', 'groups': groups, 'job': a.ref(job_path), 'inputs': inputs_ref, 'report': a.ref(folder / 'stdout.json'), 'receipt': a.ref(folder / 'receipt.json'), 'attribution': a.ref(folder / 'attribution.json'), 'stage_files': len(inputs), 'current_live_files': len(live), 'external_tools': 28, 'stage_only_driver_closure': True})
    manifest = a.ref(APP / 'assets/manifest.json')
    assert manifest['sha256'] == MANIFEST_SHA and a.read(APP / 'assets/manifest.json') == a.read(staged_app / 'assets/manifest.json')
    verifier = ROOT / 'Verification/project-knowledge-explorer-first-release/service-tests/service-v3/audit-live-runtime.py'
    assert a.ref(verifier)['sha256'] == '254c07109033e34f69d59f718cb79c0e5777134196cfeed50832a1df2b48f515'
    command = [str(ROOT / '.venv/bin/python'), '-I', '-B', str(verifier), '--expected-manifest', MANIFEST_SHA]
    run = subprocess.run(command, capture_output=True, timeout=45)
    assert run.returncode == 0 and not run.stderr
    runtime = json.loads(run.stdout)
    assert runtime['status'] == 'passed' and len(runtime['members']) == 5
    with (OUT / 'live-runtime-current-raw.json').open('xb') as f:
        f.write(run.stdout)
    assert before['prior_frontend_evidence'] == a.tree(OUT.parent, OUT)
    assert current_tree == a.tree(APP)
    patch = []
    for p in sorted(CHANGED):
        previous = a.read(ROOT / preimages[p]['preimage']['path']).decode() if p in preimages else ''
        present = a.read(ROOT / p).decode()
        patch.extend(difflib.unified_diff(previous.splitlines(True), present.splitlines(True), fromfile='original/' + p, tofile='current/' + p))
    with (OUT / 'authored-changes-current.patch').open('x') as f:
        f.write(''.join(patch))
    write('current-input-evolution.json', {'status': 'passed', 'packet': a.ref(M / 'frontend-narrow-repair-v4-input-packet-02.json'), 'packet_refs': 233, 'unchanged_refs': unchanged, 'intentional_evolutions': evolutions, 'rule': 'Current packet bindings are checked directly. Only explicitly authorized changed source/assets use exact initial preimages. Historical receipts are preserved as historical, never substituted for current bytes.'})
    write('preservation-current.json', {'status': 'passed', 'prior_frontend_evidence_files_preserved': 319, 'before': a.ref(OUT / 'preservation-before.json'), 'initial_preimages_preserved': 29, 'product_changes': deltas, 'current_product_and_tests': current_tree, 'unowned_product_and_tests_unchanged': True, 'all_changes_within_nine_path_authority': True})
    write('current-audit.json', {'status': 'passed', 'executor': '/root/explorer_manager_g3/frontend_worker', 'audit_script': a.ref(Path(__file__)), 'read_helper': a.ref(Path(spec.origin)), 'roles': initial['roles'], 'packet_refs': 233, 'packet_current_unchanged': len(unchanged), 'packet_intentional_evolutions': len(evolutions), 'source_preimages': a.ref(OUT / 'input-admission.json'), 'authored_build_inputs': sources, 'source_inventory_exact': True, 'stage': str(stage), 'dependency_files_staged_and_live': 1001, 'dependency_links_staged_and_live': 4, 'build_dependency_admission': a.ref(OUT / 'build01-dependency-admission.json'), 'unit_closure': units, 'browser_closure': browser, 'browser_behavior_groups': 53, 'theme_diagnostic_excluded': True, 'runtime_command': command, 'runtime_exit_code': run.returncode, 'runtime_report': a.ref(OUT / 'live-runtime-current-raw.json'), 'runtime_executor_qualification': 'This frontend worker executed the unchanged accepted read-only verifier. The raw static Service worker label is not executor attribution; no new service/browser/build execution.', 'runtime_manifest': manifest, 'build_id': runtime['build_id'], 'runtime_members': runtime['members'], 'preservation': a.ref(OUT / 'preservation-current.json'), 'evolution': a.ref(OUT / 'current-input-evolution.json'), 'diff': a.ref(OUT / 'authored-changes-current.patch')})
    print(json.dumps({'status': 'passed', 'packet_unchanged': len(unchanged), 'authorized_evolutions': len(evolutions), 'prior_evidence_preserved': 319, 'unit_groups': 26, 'browser_groups': 53, 'runtime_members': 5, 'build_inputs': len(sources), 'dependencies': 1001, 'manifest': MANIFEST_SHA}))

if __name__ == '__main__':
    main()
