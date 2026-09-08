"""Bounded native recovery evidence; every Task mutation uses the public CLI."""
from pathlib import Path
import datetime
import hashlib
import json
import os
import subprocess
import uuid
import validation_api as api

def call(label, kind=None, data=None, expected_error=None, command=None, extra=None, summary=None):
    task = api.state()
    canonical = Path(json.loads((api.PROJECT/'coordination/bootstrap.json').read_text())['task_folder'])/'task.json'
    before = canonical.read_bytes()
    assert task['orchestration']['writer'] == '/root/recovery_manager'
    assert task['orchestration']['execution_id'] == api.EXECUTION and task['orchestration']['generation'] == 1
    args = [command or 'orchestrate', task['task_id'], '--expected-revision', str(task['revision'])]
    response = api.response(summary or ('Observed '+label+'.'))
    if kind:
        payload = {'event': {'event_id': 'event_'+uuid.uuid4().hex, 'actor': '/root/recovery_manager', 'execution_id': api.EXECUTION, 'generation': 1, 'kind': kind, 'data': data}, 'response': response}
    else:
        payload = {**response, 'actor': '/root/recovery_manager', 'execution_id': api.EXECUTION, 'generation': 1, **(extra or {})}
    actual_command = [api.PYTHON, str(api.HELPER), '--project-root', str(api.PROJECT), *args]
    cp = subprocess.run(actual_command, input=json.dumps(payload), text=True, capture_output=True, env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
    after = canonical.read_bytes()
    receipt = {'label': label, 'observed_at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'command': actual_command, 'payload': payload, 'expected_error': expected_error, 'exit_code': cp.returncode, 'result': json.loads(cp.stdout), 'stderr': cp.stderr, 'canonical_before_sha256': hashlib.sha256(before).hexdigest(), 'canonical_after_sha256': hashlib.sha256(after).hexdigest(), 'canonical_unchanged': before == after, 'revision_before': task['revision'], 'revision_after': json.loads(after)['revision']}
    path = api.PROJECT/'coordination'/('control-'+label+'.json')
    with path.open('x') as stream:
        json.dump(receipt, stream, indent=2)
        stream.write('\n')
    if expected_error:
        assert cp.returncode and receipt['result']['errors'][0]['code'] == expected_error and before == after, receipt
    else:
        assert cp.returncode == 0, receipt
    print(json.dumps({'label': label, 'exit_code': cp.returncode, 'errors': receipt['result']['errors'], 'revision_after': receipt['revision_after'], 'canonical_unchanged': receipt['canonical_unchanged'], 'receipt': str(path)}))
    return receipt
