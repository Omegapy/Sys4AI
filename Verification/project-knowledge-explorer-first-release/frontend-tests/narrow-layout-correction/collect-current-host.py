"""Copy exact safe root receipts; this script does not run a browser."""
import importlib.util
import json
from pathlib import Path

ROOT = Path('/Volumes/P-SSD/AngryOwl/Sys4AI')
OUT = Path(__file__).absolute().parent
spec = importlib.util.spec_from_file_location('readonly_audit', OUT.parent / 'process-catalog-correction/final-v3/audit.py')
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)
RUNS = [
    (14, 'mpl27bfv', '5e03403604e4e4c7492c66f0783d1e7a26cf524f1a44b98a741887aa77847d67', 1),
    (15, 'jnd5m437', '2e04c008568b43b48424a218daa13ab3b77a67c45288fdbb0a13aa073e36cb18', 13),
    (16, 'hblfn6b6', 'dbb280d7a7f0f462c4ee6eae8f2ec5639da3fb956365c2e44a268918498d0fdd', 28),
    (17, 't0ae5b5b', 'a9a8b6e79615b2e8abad12fbce0c2b338f7d623a51ec3b638aa93d62a3845695', 4),
    (18, 'siv71_1_', 'df4e18e43fc11b898337711a686ffb6b28736debbced02303613e1b002bc7d9e', 7),
]

for number, suffix, digest, count in RUNS:
    source = Path('/private/tmp/explorer-narrow-v4-host-' + suffix)
    raw_receipt = a.verify({'path': str(source / 'receipt.json'), 'sha256': digest})
    receipt = json.loads(raw_receipt)
    raw_report = a.verify({'path': str(source / 'stdout.json'), 'sha256': receipt['stdout_sha256'], 'bytes': receipt['stdout_bytes']})
    report = json.loads(raw_report)
    assert receipt['actor'] == '/root' and receipt['status'] == report['status'] == 'passed'
    assert receipt['exit_code'] == 0 and not receipt['stderr_bytes'] and not receipt['post_verification_errors']
    assert not receipt['remaining_owned_descendants'] and not receipt['emergency_signals'] and not receipt['timed_out']
    assert len(report['checks']) == count and all(x['status'] == 'passed' for x in report['checks'])
    assert not report['csp_violations'] and not report['page_errors'] and not report['nonlocal_requests']
    assert report['owned_read_worker_reaped'] and report['observed_browser_descendants_exited']
    assert report['stage_inputs_unchanged'] and report['headless_runtime_files_unchanged'] == 20
    if number == 16:
        assert report['fixture_changes'] == ['ONTOLOGY/modules/project/part-0000.jsonld', 'docs/inert.md', 'ontology-explorer.yaml']
        assert report['fixture_changes_within_declared_test_paths']
    else:
        assert report['fixture_regular_files_unchanged']
    dest = OUT / f'host-{number:02}'
    dest.mkdir(exist_ok=False)
    for name, raw in [('receipt.json', raw_receipt), ('stdout.json', raw_report)]:
        with (dest / name).open('xb') as f:
            f.write(raw)
    images = []
    for row in receipt['images']:
        target = dest / Path(row['path']).name
        with target.open('xb') as f:
            f.write(a.verify(row))
        images.append({'original': row, 'copy': a.ref(target)})
    record = {
        'actual_executor': '/root',
        'attribution': 'Primary host executed this exact manager-reviewed frozen job once. This worker verified and copied safe outputs; no child listener/browser execution.',
        'original_receipt': a.ref(source / 'receipt.json'),
        'original_report': a.ref(source / 'stdout.json'),
        'receipt': a.ref(dest / 'receipt.json'), 'report': a.ref(dest / 'stdout.json'),
        'job': a.ref(OUT / f'host-browser-job-{number:02}.json'),
        'inputs': a.ref(OUT / f'stage-browser-{number:02}-inputs.json'),
        'status': 'passed', 'behavior_groups': count, 'images': images,
        'fixture_qualification': 'Exactly three declared disposable fixture paths changed; other fixture files unchanged. This is path-scoped preservation, not an assertion that every field within the three changed files is unchanged.' if number == 16 else 'Every disposable fixture regular file unchanged.',
        'limits': 'No native Safari, speech, assistive technology, native browser zoom, participant comprehension or full-release acceptance inferred.'
    }
    if number == 15:
        record['theme_diagnostic'] = report['theme_diagnostic']
        record['theme_count_qualification'] = 'No selection change was observed for either app sequence; original sequence also made no change in a minimal native select. Excluded from all behavior pass counts; no app-specific defect or native keyboard-selection success established.'
    raw = (json.dumps(record, indent=2) + '\n').encode()
    assert len(raw) <= 250000
    with (dest / 'attribution.json').open('xb') as f:
        f.write(raw)
    print(json.dumps({'job': number, 'groups': count, 'report': a.ref(dest / 'stdout.json'), 'receipt': a.ref(dest / 'receipt.json')}))
