#!/usr/bin/env python3
"""Read-only live checks using installed APIs; session credentials stay in memory."""
import hashlib
import http.client
import json
from pathlib import Path
import sys
from urllib.parse import urlsplit

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / '.agents/skills/ontology/scripts'))


def workbench():
    from ontology_workbench import Workbench, assess_service
    from audit import run, PYTHON, ONTOLOGY, OUT
    service = Workbench(ROOT, authority=None, port=0).start()
    checks = []

    def request(method, endpoint, body=None, headers=None):
        client = http.client.HTTPConnection('127.0.0.1', service.server.server_port, timeout=15)
        try:
            client.request(method, endpoint, body=body, headers=headers or {})
            response = client.getresponse()
            return response.status, dict(response.getheaders()), response.read()
        finally:
            client.close()

    try:
        for asset in ('/', '/app.js', '/editor.js', '/review.js', '/advanced.js', '/styles.css'):
            code, headers, data = request('GET', asset)
            assert code == 200 and data, (asset, code)
            assert headers.get('Cache-Control') == 'no-store'
            checks.append({'endpoint': asset, 'status': code, 'bytes': len(data),
                           'sha256': hashlib.sha256(data).hexdigest()})
        bootstrap = urlsplit(service.bootstrap_url()).fragment.split('=', 1)[1]
        headers = {'Content-Type': 'application/json', 'Origin': service.origin}
        code, response_headers, data = request('POST', '/api/session', json.dumps({'bootstrap': bootstrap}), headers)
        assert code == 200
        session = json.loads(data)
        headers['Cookie'] = response_headers['Set-Cookie'].split(';', 1)[0]
        headers['X-Ontology-CSRF'] = session['csrf']
        for endpoint, body in (('/api/state', {}), ('/api/records', {'query': 'Task', 'limit': 20})):
            code, _, data = request('POST', endpoint, json.dumps(body), headers)
            result = json.loads(data)
            assert code == 200 and result['status'] in ('ready', 'complete')
            if endpoint == '/api/state':
                assert result['authoring'] is False and result['scope'] == []
                assert result['project']['id'] == 'sys4ai-depot'
                checks.append({'endpoint': endpoint, 'status': code, 'project_id': result['project']['id'],
                               'authoring': False, 'readiness': result['readiness']['status']})
            else:
                assert any(r['@id'] == 'urn:sys4ai:ontology:core:Task' for r in result['records'])
                checks.append({'endpoint': endpoint, 'status': code, 'records': len(result['records']),
                               'expected_task_found': True})
        receipt = run('ontology-advanced-operational',
                      [PYTHON, ONTOLOGY, '--project-root', str(ROOT), 'advanced-health',
                       '--level', 'operational', '--workbench-url', service.origin], emit=False)
        advanced = json.loads((OUT / 'live/ontology-advanced-operational.json').read_text())
        assert receipt['exit_code'] == 0 and advanced['ready'] is True, advanced['assessment']['failed_required']
        operational = {'aggregate': advanced['aggregate'],
                       'failed_required': advanced['assessment']['failed_required'],
                       'components': {k: {'required': v.get('required'), 'ready': v.get('ready')}
                                      for k, v in advanced['assessment']['components'].items()},
                       'receipt': 'live/ontology-advanced-operational.receipt.json'}
    finally:
        service.close()
    assert not service.thread.is_alive()
    stopped_receipt = run('ontology-workbench-stopped',
                          [PYTHON, ONTOLOGY, '--project-root', str(ROOT), 'advanced-health',
                           '--scope', 'canonical', '--workbench-url', service.origin], emit=False)
    stopped = json.loads((OUT / 'live/ontology-workbench-stopped.json').read_text())
    assert stopped_receipt['exit_code'] == 1 and stopped['ready'] is False
    assert stopped['profiles']['workbench']['running'] is False
    return {'status': 'passed', 'project_id': 'sys4ai-depot', 'checks': checks,
            'service_stopped': True, 'session_persisted': False, 'canonical_mutations': False,
            'operational_health': operational,
            'stopped_service': {'aggregate': stopped['aggregate'], 'exit_code': stopped_receipt['exit_code'],
                                'state': stopped['profiles']['workbench']['service_state'],
                                'expected_negative_control': True},
            'boundary': 'Live loopback HTTP and API checks; browser rendering and authoring not exercised.'}


def guards():
    from ontology_guards import _context, profile
    selected = profile(ROOT)
    assert selected and selected['enabled']
    contract, adapters, context = _context(ROOT, selected, {})
    return {'status': 'passed', 'families': sorted(adapters['families']),
            'adapter_bindings': sum(len(v) for v in adapters['families'].values()),
            'context_entries': len(context), 'contract': selected['contract'],
            'bootstrap': selected['bootstrap'], 'mutated': False,
            'boundary': 'Exact current bindings and complete adapter family coverage; no real-root mutation dispatched.'}


if __name__ == '__main__':
    if sys.argv[1] == 'wiki':
        from ontology_wiki import validate_links
        result = validate_links(ROOT)
    elif sys.argv[1] == 'guards':
        result = guards()
    else:
        result = workbench()
    print(json.dumps(result, indent=2, sort_keys=True))
