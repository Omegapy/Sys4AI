"""Reconcile unchanged unittest logs, including warning-interrupted result lines."""
import datetime, hashlib, json, pathlib, re
ROOT=pathlib.Path('/Volumes/P-SSD/AngryOwl/Sys4AI')
OUT=ROOT/'Verification/system-health-reassessment-2026-09-10/regression'
SUITES=['ontology','memory','initializer-static','template-contract']
def load(p): return json.loads(p.read_text())
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,value): p.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
summary={'observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Current installed ordinary regression suites and current Template contract; no production repair','runtime':load(OUT/'runtime.json'),'instruction_binding':load(OUT/'instruction-binding.json'),'suites':{},'failures':[]}
all_rows={}
for name in SUITES:
    dest=OUT/name; receipt=load(dest/'receipt.json'); rows=[]; pending=None; warnings=[]
    for lineno,line in enumerate((dest/'stderr.log').read_text().splitlines(),1):
        start=re.match(r'^(test\S*) \(([^)]+)\)(?:.*)? \.\.\. (.*)$',line)
        if start:
            if pending: raise RuntimeError(f'Unresolved result before line {lineno}: {pending}')
            method,owner,tail=start.groups()
            pending={'id':owner if owner.endswith('.'+method) else owner+'.'+method,'start_line':lineno}
            if re.fullmatch(r'ok|FAIL|ERROR|skipped .+|expected failure|unexpected success',tail):
                rows.append({**pending,'outcome':tail,'result_line':lineno}); pending=None
        elif pending and re.fullmatch(r'ok|FAIL|ERROR|skipped .+|expected failure|unexpected success',line):
            rows.append({**pending,'outcome':line,'result_line':lineno});pending=None
        if 'Warning:' in line: warnings.append({'line':lineno,'text':line})
    if pending: raise RuntimeError(f'Unresolved final result: {pending}')
    ids=[r['id'] for r in rows]
    accounting={'stdout_sha256':digest(dest/'stdout.log'),'stderr_sha256':digest(dest/'stderr.log'),'reported_test_count':receipt['reported_test_count'],'initial_single_line_parse_count':receipt['parsed_identity_count'],'reconciled_identity_count':len(rows),'unique_identity_count':len(set(ids)),'warnings':warnings,'identities':rows,'all_results_accounted':len(rows)==receipt['reported_test_count'] and len(set(ids))==len(rows)}
    if not accounting['all_results_accounted']: summary['failures'].append(name+': incomplete identity accounting')
    for row in rows:
        if row['outcome']!='ok': summary['failures'].append(name+': '+row['id']+' '+row['outcome'])
    if receipt['exit_code']!=0: summary['failures'].append(name+': command exit '+str(receipt['exit_code']))
    if receipt['source_changes']: summary['failures'].append(name+': monitored source changes')
    dump(dest/'accounting.json',accounting); all_rows[name]={row['id']:row for row in rows}
    summary['suites'][name]={**receipt,'accounting_path':str((dest/'accounting.json').relative_to(ROOT)),'accounting_sha256':digest(dest/'accounting.json'),'reconciled_identity_count':len(rows),'outcome_counts':{v:sum(r['outcome']==v for r in rows) for v in sorted({r['outcome'] for r in rows})},'warnings':warnings,'monitored_input_count':len(load(dest/'inputs-before.json'))}
inv_path=ROOT/'Verification/ontology-health-repairs/required-test-inventory.json'; inv=load(inv_path)
expected={r['id'] for r in inv['tests']}; baseline={r['id'] for r in inv['tests'] if r.get('baseline') is not None}; actual=set(all_rows['ontology'])
comparison={'inventory_path':str(inv_path.relative_to(ROOT)),'inventory_sha256':digest(inv_path),'expected_identities':len(expected),'original_audit_identities':len(baseline),'actual_identities':len(actual),'missing':sorted(expected-actual),'unclassified':sorted(actual-expected),'original_audit_missing':sorted(baseline-actual),'all_obligations_passed':expected==actual and all(r['outcome']=='ok' for r in all_rows['ontology'].values())}
if not comparison['all_obligations_passed']: summary['failures'].append('Ontology inventory does not exactly match all passing results')
summary['ontology_identity_gate']=comparison;dump(OUT/'ontology/inventory-comparison.json',comparison)
coverage=load(OUT/'fault-coverage-inventory.json')
for row in coverage:
    suite='template-contract' if row['path'].startswith('Projects/') else 'initializer-static' if '/init-new-project/' in row['path'] else 'ontology' if '/ontology/' in row['path'] else 'memory'
    outcome=all_rows[suite].get(row['id']); row['suite']=suite;row['outcome']=outcome['outcome'] if outcome else 'missing'; row['log_line']=outcome['result_line'] if outcome else None
    if row['outcome']!='ok': summary['failures'].append('Fault control not passed: '+row['id'])
dump(OUT/'fault-coverage-results.json',coverage)
summary['fault_controls']={'count':len(coverage),'passed':sum(r['outcome']=='ok' for r in coverage),'path':str((OUT/'fault-coverage-results.json').relative_to(ROOT))}
summary['total_tests']=sum(r['reconciled_identity_count'] for r in summary['suites'].values())
summary['status']='passed' if not summary['failures'] else 'failed'
summary['limits']=['Complete 119-test initializer suite and previous delivered-project installation matrix not rerun.','Memory vendor-runtime faults are controlled fixtures; real-root runtime observations are separate parent evidence.','Ontology selected runtime/model inputs are existing root copies used in disposable fixtures, not fresh provisioning.','No real product adoption, canonical maintenance, source repair, publication, new dependencies, model downloads or recertification.','No separate visual browser QA, case-sensitive filesystem acceptance, or unattended startup test.']
dump(OUT/'summary.json',summary)
print(json.dumps({'status':summary['status'],'total_tests':summary['total_tests'],'counts':{k:v['reconciled_identity_count'] for k,v in summary['suites'].items()},'inventory':comparison,'fault_controls':summary['fault_controls'],'failures':summary['failures']},indent=2))
