"""Bounded existing-reader API discovery on a disposable synthetic project."""
import hashlib,json,sys
from pathlib import Path
root=Path.cwd();sys.path.insert(0,str(root/'SKILLS-depo/ontology/tests'))
from test_explorer_read import ReaderCase

case=ReaderCase();case.setUp()
try:
    process=case.ids['processes'][0]
    items,_=case.page_all('entry',dict(id=process,section='process',cursor=None),'process_items')
    relation=next(i['relation_ids'][0] for i in items if i['kind']=='field' and i['part']=='relations' and i['relation_ids'])
    chunks,_=case.page_all('entry',dict(id=relation,section='details',cursor=None),'chunks')
    endpoint=json.loads(''.join(x['text'] for x in chunks))['object']
    endpoint_ref=case.entry(endpoint,'sources')['data']['references'][0]
    original_source=dict(case.store.current.project.by_id[process]['sources'][0])
    binding=case.ids['binding']
    case.edit_record(binding,lambda r:r.update(entity=process,sources=[original_source]))
    case.snapshot=case.call('context',{'refresh':True})['snapshot']
    binding_ref=case.entry(binding,'sources')['data']['references'][0]
    cfg_path=case.root/'ontology-explorer.yaml';cfg=json.loads(cfg_path.read_text())
    mapping=cfg['process_views'][0]
    mapping['field_sources']['roles']=[dict(owner_id=endpoint,reference_id=endpoint_ref['reference_id'],extract_locator=None)]
    mapping['field_sources']['inputs']=[dict(owner_id=binding,reference_id=binding_ref['reference_id'],extract_locator=None)]
    mapping['ordered_source'].update(owner_id=binding,reference_id=binding_ref['reference_id'])
    cfg_path.write_text(json.dumps(cfg))
    case.snapshot=case.call('context',{'refresh':True})['snapshot']

    # From this point discovery uses only the process ID and admitted responses;
    # it does not inspect the server's configuration or internal record index.
    operations=0
    def entry_pages(ident,section,array):
        global operations
        values,pages=case.page_all('entry',dict(id=ident,section=section,cursor=None),array)
        operations+=len(pages);return values,pages
    items,pages=entry_pages(process,'process','process_items')
    wanted={ref for item in items if item['kind']=='field' for ref in item['reference_ids']}
    wanted.update(item['reference_id'] for item in items if item['kind']=='ordered_step')
    candidates={process};process_refs,_=entry_pages(process,'sources','references')
    candidates.update(r['binding_id'] for r in process_refs if r['binding_id'] is not None)
    relation_ids={rid for item in items if item['kind']=='field' for rid in item['relation_ids']}
    for rid in relation_ids:
        chunks,_=entry_pages(rid,'details','chunks')
        record=json.loads(''.join(x['text'] for x in chunks))
        assert record['@id']==rid and record['kind']=='relation'
        candidates.update((rid,record['subject'],record['object']))
    found={}
    for ident in sorted(candidates):
        refs=process_refs if ident==process else entry_pages(ident,'sources','references')[0]
        for ref in refs:
            if ref['reference_id'] in wanted:
                assert ref['owner_id']==ident
                assert ref['reference_id'] not in found
                found[ref['reference_id']]=ref
    assert set(found)==wanted and {r['owner_id'] for r in found.values()}=={process,binding,endpoint}
    for digest,ref in found.items():
        response=case.call('source',dict(owner_id=ref['owner_id'],reference_id=digest,cursor=None));operations+=1
        assert response['data']['reference']['owner_id']==ref['owner_id'] and response['data']['reference']['reference_id']==digest
    projected=next(r for r in process_refs if r['binding_id']==binding)
    assert projected['reference_id']!=binding_ref['reference_id']
    report={'status':'passed','configured_nonprocess_endpoint_and_direct_binding_sources':True,'ordered_source_owner_is_direct_binding':True,
      'process_candidate_count':len(candidates),'reference_count':len(found),'reader_calls':operations,
      'discovery_inputs':'Only exact process ID plus admitted same-snapshot process, source-descriptor and canonical relation-detail responses.',
      'direct_and_projected_binding_reference_ids_distinct':True,
      'qualification':'Finite synthetic existing-API capability probe only. Python json preserves large integers here. Frontend still must implement bounded visible continuation/cancellation, same-generation correlation and lossless string-field extraction when canonical details contain unsafe JavaScript numeric tokens; no frontend/HTTP/browser/performance acceptance.'}
    print(json.dumps(report,sort_keys=True))
finally:case.tearDown()
