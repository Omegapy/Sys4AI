"""Focused reproducible fixture/coverage checks; never an Explorer runtime pass."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import os
import platform
import resource
import subprocess
import sys
import tempfile
import time

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
TESTS = HERE.parents[1]
ROOT = HERE.parents[4]
sys.path.insert(0, str(TESTS))
from explorer_support import *
from explorer_support import _counts
from ontology_core import OntologyError, check_locator, parse_document, read_bytes
from ontology_validate import validate_project
from check_ontology import run_checks
from ontology_retrieval import search, term, ranked


def manifest(root):
    return {p.relative_to(root).as_posix(): {"sha256": hashlib.sha256(p.read_bytes()).hexdigest(), "mtime_ns": p.stat().st_mtime_ns}
            for p in root.rglob("*") if p.is_file()}


def worker(root):
    started = time.perf_counter()
    before = manifest(root)
    observed = inspect_fixture(root)
    loaded = time.perf_counter() - started
    print(json.dumps({"stage":"canonical_loader_complete","canonical_loader":observed,"load_elapsed_seconds":loaded,
                      "peak_rss_native":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss},ensure_ascii=False),flush=True)
    competency = run_checks(root)
    after = manifest(root)
    return {"canonical_loader": observed, "load_elapsed_seconds": loaded,
            "canonical_competency": competency, "elapsed_seconds": time.perf_counter()-started,
            "peak_rss_native": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "peak_rss_units": "bytes" if sys.platform == "darwin" else "KiB",
            "fixture_nonmutation": before == after, "protected_file_count": len(before),
            "verification_level": "canonical_loader_and_competency_only"}


def run(output):
    output.mkdir(parents=True, exist_ok=True)
    result={"schema_version":1, "kind":"fixture_validation_receipt", "python":sys.version, "platform":platform.platform(),
            "status":"running", "checks":[], "scales":[], "limitations":[]}
    def check(name,condition,detail=None):
        result["checks"].append({"id":name,"passed":bool(condition),"detail":detail})
        if not condition: raise AssertionError((name,detail))
    with tempfile.TemporaryDirectory(prefix="explorer-fixtures-") as tmp:
        workspace=Path(tmp).resolve()
        small=make_explorer_project(workspace/'small')
        p=load_project(small['root'],validate=True)
        initial=manifest(small['root'])
        check('small_actual_counts',len(p.records)==216 and len(p.relations)==109,small['counts'])
        check('canonical_schema_valid',validate_project(p,require_current=True)['valid'])
        check('distinct_parallel_edges',p.by_id[small['ids']['parallel_relations'][0]]['predicate'] != p.by_id[small['ids']['parallel_relations'][1]]['predicate'])
        check('cycle_and_self_loop',any(e['subject']==e['object'] for e in p.relations) and
              all(project_id(f'relation-{i:06d}','explorer-alpha') in p.by_id for i in (0,3,4)))
        check('many_source_refs_and_long_fields',len(p.by_id[project_id('entry-00011','explorer-alpha')]['sources'])==130 and len(p.by_id[small['ids']['long_label']]['label'])>4096)
        found=term(p,'Orientation')
        check('canonical_alias_ambiguity',found['status']=='ambiguous' and {r['@id'] for reason,r in ranked(p,'Orientation')}=={small['ids']['focus'],small['ids']['duplicate']}, {'term_status':found['status'],'term_truncation':found['truncation'],'qualification':'Canonical ranking preserves both candidates; legacy full-context term response can omit them under its unchanged byte cap.'})
        check('canonical_explicit_semantic_false',search(p,'FixtureTaskManager',semantic=False)==search(p,'FixtureTaskManager',semantic=False))
        cfg=read_json(small['root']/'ontology-explorer.yaml')
        for mapping in cfg['process_views']:
            row=p.by_id[mapping['id']]; source=row['sources'][0]
            selected=mapping['field_sources']['applicability'][0]
            check('process_reference_'+row['label'].split()[1],selected['reference_id']==reference_id(row['@id'],source))
        ordered=cfg['process_views'][0]['ordered_source']
        source=p.by_id[ordered['owner_id']]['sources'][0]
        lines=(small['root']/source['path']).read_text().splitlines()
        check('ordered_source_original_numbers',all(lines[int(s['locator'].split(':')[1])-1].startswith(f"{s['number']}. ") for s in ordered['steps']))
        check('unordered_designation_absent',cfg['process_views'][1]['ordered_source'] is None)
        partial=cfg['process_views'][2]['ordered_source']
        partial_source=p.by_id[partial['owner_id']]['sources'][0]
        check('partial_precedence_not_order',not any(line.startswith('1. ') for line in (small['root']/partial_source['path']).read_text().splitlines()))
        check('json_and_repeated_heading_are_canonical',all(s['status']=='current' for s in p.sources),
              'Canonical section check proves substring presence only; exact/excerpt extraction is future service evidence.')
        bound=p.by_id[small['ids']['binding']]
        check('binding_tuple_separate',reference_id(bound['entity'],bound['sources'][0],bound['@id']) != reference_id(bound['entity'],bound['sources'][0]))
        check('small_reads_nonmutating',manifest(small['root'])==initial)
        again=make_explorer_project(workspace/'repeat')
        check('deterministic_bytes',{k:v['sha256'] for k,v in initial.items()}=={k:v['sha256'] for k,v in manifest(again['root']).items()})
        beta=make_explorer_project(workspace/'beta',identity='explorer-beta')
        pb=load_project(beta['root'],validate=True)
        a,b=p.by_id[small['ids']['focus']],pb.by_id[beta['ids']['focus']]
        check('second_namespace_same_label_different_meaning',a['label']==b['label'] and a['definition']!=b['definition'] and a['@id']!=b['@id'])
        neutral=make_neutral_project(workspace/'neutral')
        pn=load_project(neutral,validate=True)
        check('neutral_import_only',len(pn.records)==65 and all(r['module']!='project' for r in pn.records))
        neutral_checks=run_checks(neutral)
        check('neutral_competency',neutral_checks['valid'],len(neutral_checks['competency']['results']))
        unspecialized=make_neutral_project(workspace/'unspecialized',unspecialized=True)
        try: load_project(unspecialized,validate=True)
        except OntologyError as exc: check('unspecialized_refusal',exc.code=='unresolved_identity',exc.code)
        else: check('unspecialized_refusal',False)
        for variant in ('broken_reference','unmodeled_ambiguity','duplicate_identity','unsupported_property','unselected_source','invalid_qualifier','stale_source','missing_source','same_mtime_source'):
            sample=make_explorer_project(workspace/variant)
            expectation=mutate_fixture(sample['root'],variant)
            before=manifest(sample['root'])
            try:
                observed=inspect_fixture(sample['root'])
                check(variant,not expectation['fatal'] and expectation['expected'] in observed['diagnostic_codes'],observed['diagnostic_codes'])
            except OntologyError as exc:
                check(variant,expectation['fatal'] and exc.code==expectation['expected'],exc.code)
            check(variant+'_nonmutation',before==manifest(sample['root']))
        # Measure the offset from actual imported/binding tuples, rather than
        # confusing distinct paths with the owner-specific wire tuple count.
        probe=make_explorer_project(workspace/'probe',entries=10,relationships=0,pathological=False)
        offset=probe['counts']['owner_source_reference_tuples']-10
        for wanted in (1024,1025):
            sample=make_explorer_project(workspace/f'boundary-{wanted}',entries=wanted-offset,relationships=0,pathological=False)
            observed=inspect_fixture(sample['root'])
            check(f'owner_reference_boundary_{wanted}',sample['counts']['owner_source_reference_tuples']==wanted,observed)
        # The first unsupported *single-file* loader thresholds are distinct
        # from aggregate reader admission. Exercise exact boundary neighbors.
        rows=[{}]*10000
        try: parse_document(canonical_bytes({'@context':CONTEXT_PATH,'@graph':rows}),CONTEXT_PATH,'synthetic.jsonld')
        except OntologyError as exc: check('graph10000_passes_array_cap',exc.code=='unsupported_kind',exc.code)
        try: parse_document(canonical_bytes({'@context':CONTEXT_PATH,'@graph':rows+[{}]}),CONTEXT_PATH,'synthetic.jsonld')
        except OntologyError as exc: check('graph10001_rejected',exc.code=='invalid_graph',exc.code)
        target=workspace/'file-cap.txt';target.write_bytes(b'x'*2000000)
        check('file2000000_read',len(read_bytes(target))==2000000)
        target.write_bytes(b'x'*2000001)
        try: read_bytes(target)
        except OntologyError as exc: check('file2000001_rejected',exc.code=='input_too_large',exc.code)
        for scale in SCALES:
            sample=small if scale=='small' else make_explorer_project(workspace/scale,scale=scale)
            command=[sys.executable,'-B',str(Path(__file__).resolve()),'--worker',str(sample['root'])]
            started=time.perf_counter()
            try:
                cp=subprocess.run(command,capture_output=True,text=True,timeout=45,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
                stdout,stderr,exit_code=cp.stdout,cp.stderr,cp.returncode
                observed=json.loads(stdout.splitlines()[-1]) if exit_code==0 else None
                state='canonical_checks_passed' if observed and observed['canonical_competency']['valid'] and observed['fixture_nonmutation'] else 'canonical_check_failed'
            except subprocess.TimeoutExpired as exc:
                stdout=exc.stdout or b'';stderr=exc.stderr or b''
                stdout=stdout.decode() if isinstance(stdout,bytes) else stdout
                stderr=stderr.decode() if isinstance(stderr,bytes) else stderr
                exit_code=None;observed=None;state='canonical_probe_timeout'
                progress=[json.loads(line) for line in stdout.splitlines() if line.strip()]
                if progress and progress[-1].get('stage')=='canonical_loader_complete':
                    state='canonical_loader_passed_competency_timeout'
            paths=[]
            for suffix,body in [('stdout.jsonl',stdout),('stderr.txt',stderr)]:
                path=output/f'{scale}-{suffix}';path.write_text(body); paths.append({'path':path.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size})
            scale_result={'scale':scale,'requested_local_entries':SCALES[scale][0],'requested_local_relations':SCALES[scale][1],
                          'counts':sample['counts'],'canonical_result':state,'exit_code':exit_code,'probe_timeout_seconds':45,
                          'wall_seconds':time.perf_counter()-started,'raw_evidence':paths,
                          'reader_admission':sample['expected_reader_admission'],
                          'reader_admission_observed':False}
            if not observed and stdout.strip():
                scale_result['completed_stage']=json.loads(stdout.splitlines()[-1])
            if observed:
                scale_result.update(load_elapsed_seconds=observed['load_elapsed_seconds'],peak_rss_native=observed['peak_rss_native'],peak_rss_units=observed['peak_rss_units'],competency_count=len(observed['canonical_competency']['competency']['results']))
            result['scales'].append(scale_result)
            check(scale+'_partition_within_caps',sample['counts']['largest_canonical_document_bytes']<200000 and sample['counts']['largest_canonical_document_records']<=500)
            check(scale+'_canonical_result_accounted',state in ('canonical_checks_passed','canonical_probe_timeout','canonical_loader_passed_competency_timeout'),scale_result)
        spec=importlib.util.spec_from_file_location('build_matrix',HERE/'build_matrix.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
        matrix_path=ROOT/mod.DEST
        check('matrix_reproducible',matrix_path.read_bytes()==mod.build())
        matrix=json.loads(matrix_path.read_text())
        check('complete_coverage',[len(matrix[k]) for k in ('requirements','acceptance_scenarios','plan_tasks','phases')]==[49,36,33,8])
        check('no_at_pass_claims',all(a['status']=='not_run' and not a['evidence'] for a in matrix['acceptance_scenarios']))
        check('all_scenarios_resolve',all(set(r['scenario_ids'])<={s['scenario_id'] for s in matrix['scenario_catalog']} for r in matrix['requirements']))
        # No production asset manifest exists at TASK003. Source location and
        # contract exclusion are inspectable; installed HTTP exclusion is not.
        assets=ROOT/'SKILLS-depo/ontology/explorer/assets/manifest.json'
        check('fixture_source_outside_runtime_assets','/explorer/assets/' not in str(HERE))
        result['distribution_inspection']={'fixture_source':HERE.relative_to(ROOT).as_posix(),'runtime_manifest_present':assets.exists(),
             'observed':'source_placement_and_accepted_contract_exclusion_only','http_bundle_exclusion':'not_exercised',
             'note':'Existing updater can copy tests as installed test resources; that is separate from HTTP runtime assets. Later actual bundle/manifest/HTTP evidence remains mandatory.'}
    result['limitations']=[
      'These are canonical fixtures and coverage/protocols. No production reader, HTTP dispatcher, signed cursor, session, renderer, browser, accessibility, human walkthrough or timing target was tested.',
      'load_elapsed_seconds and RSS are single canonical-loader observations in an isolated test subprocess, not production latency p95, reader RSS limits or browser performance.',
      'Representative/stress source tuples exceed the accepted 1024 cap. Resource_limit is predicted from counts, not an observed service response. Stress may also exceed aggregate byte/relation budgets after imports; retain actual counts.',
      '45-second canonical probe timeout is a fixture-test bound, not the five-second service deadline. Any timeout means loading not established for that exact workload, not permission to increase shared caps.',
      'Graph10000 probe uses invalid placeholder records to isolate array-count admission; unsupported_kind at10000 does not establish semantic validity. Normal generated shards validate separately.',
      'Exact source extraction, process partial/stale projection and source/hash admission need future reader tests; canonical substring presence is not proof of exact section extraction.',
      'No general aggregate canonical loader capacity guarantee or all-threshold search is claimed. Exact single-file byte/record boundaries and near owner-tuple admission cases are separately measured.',
      'No production asset manifest exists at this stage; source placement and normative exclusions alone do not establish installed HTTP exclusion.'
    ]
    result['status']='fixture_checks_passed'
    result['artifacts']=[{'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in [TESTS/'explorer_support.py',HERE/'build_matrix.py',HERE/'protocol-cases.json',Path(__file__).resolve(),ROOT/'Verification/project-knowledge-explorer-first-release/acceptance-matrix.json']]
    (output/'result.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({'status':result['status'],'checks':len(result['checks']),'scales':result['scales']},indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker',type=Path)
    parser.add_argument('--output',type=Path,default=HERE/'validation')
    args=parser.parse_args()
    if args.worker: print(json.dumps(worker(args.worker),ensure_ascii=False))
    else: run(args.output)
