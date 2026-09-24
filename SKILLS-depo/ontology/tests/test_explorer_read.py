"""Reader integration tests against canonical disposable fixtures and wire schema."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import time
import unittest

SCRIPTS=Path(__file__).resolve().parents[1]/'scripts'
ROOT=SCRIPTS.parents[2]
sys.path[:0]=[str(SCRIPTS),str(Path(__file__).parent)]
from explorer_support import make_explorer_project
from ontology_explorer_snapshot import VerifiedPackage
import ontology_explorer_read as ordinary


class ReaderCase(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='explorer-reader-test-',dir='/private/tmp')
        self.base=Path(self.temp.name)
        self.fixture=make_explorer_project(self.base/'project')
        self.root=self.fixture['root']
        self.scripts=self.base/'helpers';self.scripts.mkdir()
        for path in SCRIPTS.glob('ontology*.py'):shutil.copyfile(path,self.scripts/path.name)
        self.schema_path=ROOT/'ONTOLOGY-depo/schema/explorer-v1.json'
        self.package=VerifiedPackage(self.scripts,{'schema':self.schema_path},allowed_modules=ordinary.READ_CLOSURE)
        self.module=self.package.load('ontology_explorer_read')
        self.snapshot_module=self.package.load('ontology_explorer_snapshot')
        self.store=self.snapshot_module.SnapshotStore(self.root,self.package)
        self.reader=self.module.Reader(self.store,service_instance='1'*32,build_id='2'*64,
            schema_sha256=hashlib.sha256(self.package.member_bytes['schema']).hexdigest(),service_secret=b'x'*32)
        self.session='3'*32
        self.snapshot=None
        self.context=self.call('context',{'refresh':False})
        self.snapshot=self.context['snapshot']
        self.ids=self.fixture['ids']

    def tearDown(self):
        self.store.close();self.temp.cleanup()

    def call(self,op,params,**kw):
        request=dict(schema_version=1,request_id='test',code_epoch=self.package.code_epoch,snapshot=self.snapshot,params=params)
        request.update(kw.pop('request',{}))
        result=self.reader.read(op,request,session_scope=kw.pop('session',self.session),**kw)
        self.assertTrue(self.module.validate(result,op.title()+'Response',self.reader.schema))
        self.assertLessEqual(len(self.module.compact(result)),result['limits']['bytes'])
        try:
            import jsonschema
        except ImportError:
            pass
        else:
            schema={'$ref':'#/$defs/'+op.title()+'Response','$defs':self.reader.schema['$defs']}
            jsonschema.Draft202012Validator(schema).validate(result)
        return result

    def error(self,code,op,params,**kwargs):
        with self.assertRaises(self.reader.error_type) as caught:self.call(op,params,**kwargs)
        self.assertEqual(caught.exception.code,code)
        return caught.exception

    def entry(self,ident,section='header',cursor=None):return self.call('entry',dict(id=ident,section=section,cursor=cursor))

    def search_params(self,**kw):
        result=dict(query='',category=None,lifecycles=['draft','approved','deprecated'],fact_kinds=['asserted','derived','inferred','external'],sort='label',limit=20,cursor=None)
        result.update(kw);return result

    def graph_params(self,**kw):
        result=dict(id=self.ids['focus'],direction='both',predicate_ids=[],lifecycles=['draft','approved','deprecated'],fact_kinds=['asserted','derived','inferred','external'],limit=20,cursor=None)
        result.update(kw);return result

    def configure(self,update):
        path=self.root/'ontology-explorer.yaml';value=json.loads(path.read_text());update(value);path.write_text(json.dumps(value))
        # Tests may inspect a newly admitted snapshot even when deliberately
        # selecting a budget too small for atomic context. Product never does.
        with self.store.lease() as view:self.snapshot=view.snapshot_id

    def edit_record(self,ident,update):
        cfg=json.loads((self.root/'ontology.yaml').read_text())
        for relative in cfg['project_files']+cfg['binding_files']:
            path=self.root/relative;doc=json.loads(path.read_text())
            for record in doc['@graph']:
                if record['@id']==ident:
                    update(record);path.write_text(json.dumps(doc,ensure_ascii=False));return
        raise AssertionError(ident)

    def page_all(self,operation,params,array='items'):
        rows=[];seen=set();responses=[]
        for _ in range(1000):
            result=self.call(operation,params);responses.append(result);rows.extend(result['data'][array])
            token=result['page']['next_cursor']
            if token is None:return rows,responses
            self.assertNotIn(token,seen);seen.add(token);params={**params,'cursor':token}
        self.fail('Continuation did not terminate')


class ReadTests(ReaderCase):
    def test_context_is_compact_exact_and_no_whole_graph(self):
        data=self.context['data'];self.assertEqual(data['project']['name'],self.store.current.project.config['project']['name'])
        self.assertEqual(len(data['starting_points']),1);self.assertEqual(data['local_additions'],'present')
        self.assertFalse(data['capabilities']['authoring']);self.assertNotIn('records',data)
        self.assertEqual(data['root_scope_id'],self.context['project']['root_scope_id'])

    def test_exact_header_deprecated_details_history_and_status(self):
        record=next(r for r in self.store.current.project.records if r['lifecycle']=='deprecated')
        h=self.entry(record['@id'])['data']['header'];self.assertEqual(h['lifecycle'],'deprecated')
        chunks,_=self.page_all('entry',dict(id=record['@id'],section='details',cursor=None),'chunks')
        value=json.loads(''.join(c['text'] for c in chunks));self.assertEqual(value['replacement'],record['replacement'])
        chunks,_=self.page_all('entry',dict(id=self.ids['focus'],section='details',cursor=None),'chunks')
        self.assertEqual(json.loads(''.join(c['text'] for c in chunks))['history'],ordinary.thaw(self.store.current.project.by_id[self.ids['focus']]['history']))
        draft=next(r for r in self.store.current.project.records if r['kind']!='binding' and r['lifecycle']=='draft' and not r['sources'])
        self.assertEqual(self.entry(draft['@id'])['data']['header']['source_state'],'unrecorded')

    def test_lossless_unicode_text_and_optional_absence(self):
        ident=next(r['@id'] for r in self.store.current.project.records if len(r['definition'])>10000)
        expected=self.store.current.project.by_id[ident]['definition']
        self.configure(lambda c:c['limits'].update(page_items=2,response_bytes=6000,source_excerpt_bytes=256))
        chunks,responses=self.page_all('entry',dict(id=ident,section='definition',cursor=None),'chunks')
        self.assertEqual(''.join(c['text'] for c in chunks),expected)
        offset=0
        for c in chunks:self.assertEqual(c['offset'],offset);offset+=len(c['text'].encode())
        self.assertTrue(any(r['page']['has_more'] for r in responses))
        empty=self.entry(self.ids['camelcase'],'examples');self.assertEqual(empty['status'],'empty');self.assertEqual(empty['data']['chunks'],[])
        label,_=self.page_all('entry',dict(id=self.ids['long_label'],section='label',cursor=None),'chunks')
        self.assertEqual(''.join(c['text'] for c in label),self.store.current.project.by_id[self.ids['long_label']]['label'])

    def test_exact_relations_loops_parallel_qualifiers_and_direction(self):
        rows,pages=self.page_all('relationships',self.graph_params(limit=5))
        ids=[x['edge']['id'] if x['kind']=='edge' else x['id'] for x in rows]
        expected=sorted(set(self.store.current.incoming.get(self.ids['focus'],()))|set(self.store.current.outgoing.get(self.ids['focus'],())))
        self.assertEqual(ids,expected);self.assertEqual(len(ids),len(set(ids)))
        self.assertTrue(set(self.ids['parallel_relations'])<=set(ids))
        self.assertTrue(any(x['kind']=='detail_required' and x['detail']['section']=='qualifiers' for x in rows))
        for page in pages:
            nodes={n['id'] for n in page['data']['nodes']}
            for item in page['data']['items']:
                if item['kind']=='edge':
                    edge=item['edge'];original=self.store.current.project.by_id[edge['id']]
                    self.assertEqual((edge['subject'],edge['object']),(original['subject'],original['object']))
                    self.assertTrue({edge['subject'],edge['object']}<=nodes)
        incoming=self.call('relationships',self.graph_params(direction='incoming'))
        for item in incoming['data']['items']:
            if item['kind']=='edge':self.assertEqual(item['edge']['object'],self.ids['focus'])

    def test_neighborhood_node_limit_markers_and_scope(self):
        rows,pages=self.page_all('neighborhood',self.graph_params(limit=5,node_limit=1))
        self.assertTrue(any(i['kind']=='detail_required' and i['reason']=='visited_limit' for i in rows))
        self.assertTrue(all(len(p['data']['nodes'])<=1 for p in pages))
        self.assertTrue(all(p['coverage']['complete']==False for p in pages if any(i['kind']=='detail_required' for i in p['data']['items'])))

    def test_unsafe_numeric_qualifiers_mark_edge_and_preserve_exact_detail(self):
        predicate='urn:sys4ai:ontology:project:explorer-alpha:documents'
        self.edit_record(predicate,lambda r:r['qualifiers'].update(count={'type':'integer','required':False},ratio={'type':'number','required':False}))
        ids=['urn:sys4ai:ontology:project:explorer-alpha:relation-'+f'{i:06d}' for i in (0,2,4,12)]
        self.edit_record(ids[0],lambda r:r.update(qualifiers={'count':9007199254740993}))
        self.edit_record(ids[1],lambda r:r.update(qualifiers={'count':9007199254740991,'ratio':1.5}))
        self.edit_record(ids[2],lambda r:r.update(qualifiers={'count':10**350}))
        self.edit_record(ids[3],lambda r:r.update(qualifiers={'ratio':-0.0}))
        self.snapshot=self.call('context',{'refresh':True})['snapshot']
        rows,pages=self.page_all('relationships',self.graph_params(limit=5))
        for ident in (ids[0],ids[2],ids[3]):
            item=next(x for x in rows if x.get('id')==ident)
            self.assertEqual(item['reason'],'field_limit');self.assertEqual(item['detail']['section'],'qualifiers')
            chunks,_=self.page_all('entry',dict(id=ident,section='qualifiers',cursor=None),'chunks')
            text=''.join(c['text'] for c in chunks)
            if ident==ids[3]:self.assertIn('-0.0',text)
            value=json.loads(text)
            self.assertEqual(value,dict(self.store.current.project.by_id[ident]['qualifiers']))
        safe=next(x for x in rows if x['kind']=='edge' and x['edge']['id']==ids[1])
        self.assertEqual(safe['edge']['qualifiers'],{'count':9007199254740991,'ratio':1.5})
        self.assertTrue(any(x['kind']=='edge' and x['edge']['id']>ids[2] for x in rows))

    def test_tight_graph_final_coverage_fits_without_skipping_identities(self):
        self.configure(lambda c:c['limits'].update(response_bytes=3400))
        rows,pages=self.page_all('neighborhood',self.graph_params(limit=20,node_limit=2))
        ids=[x['edge']['id'] if x['kind']=='edge' else x['id'] for x in rows]
        expected=sorted(set(self.store.current.outgoing[self.ids['focus']])|set(self.store.current.incoming[self.ids['focus']]))
        self.assertEqual(ids,expected)
        self.assertTrue(any('visited_limit' in r['coverage']['reasons'] for r in pages))
        self.assertTrue(all(len(self.module.compact(r))<=3400 for r in pages))

    def test_atomic_1024_refusal_and_all_fixed_error_envelopes(self):
        self.configure(lambda c:c['limits'].update(response_bytes=1024))
        self.error('resource_limit','context',{'refresh':False})
        self.error('resource_limit','search',self.search_params())
        maximum=0
        for code in self.reader.errors:
            for operation in ordinary.OPERATIONS:
                http,result=self.reader.error_response(code,operation=operation,request_id='a'*32,limits=dict(items=100,bytes=32000,visited_nodes=100,seconds=5))
                maximum=max(maximum,len(self.module.compact(result)));self.assertTrue(400<=http<=599)
                self.assertIsNone(result['project']);self.assertEqual(result['scope'],{})
        self.assertLessEqual(maximum,1024)

    def test_closed_request_rejects_unknown_boolean_and_bad_ids(self):
        params=self.search_params(limit=True);self.error('invalid_request','search',params)
        self.error('invalid_request','entry',dict(id='../../SPECS.md',section='header',cursor=None))
        self.error('invalid_request','context',{'refresh':False,'root':'/private'})
        self.error('invalid_request','search',self.search_params(query='word',sort='label'))
        self.error('invalid_request','search',self.search_params(lifecycles=[]))
        self.error('invalid_request','search',self.search_params(query='\ud800',sort='relevance'))

    def test_deadline_and_lowered_canonical_limits_never_widen(self):
        self.error('deadline_exceeded','search',self.search_params(),deadline=time.monotonic()-1)
        cfgpath=self.root/'ontology.yaml';cfg=json.loads(cfgpath.read_text())
        cfg['retrieval']['max_limit']=4;cfg['retrieval']['default_limit']=2
        cfgpath.write_text(json.dumps(cfg))
        self.snapshot=self.call('context',{'refresh':True})['snapshot']
        policy=self.reader.policy(self.store.current)
        self.assertEqual(policy['page_items'],4);self.assertEqual(policy['visited_nodes'],4)
        self.assertEqual(policy['default_page_items'],2)
        self.error('invalid_request','search',self.search_params(limit=5))
        self.error('invalid_request','neighborhood',self.graph_params(limit=4,node_limit=5))

    def test_no_write_or_optional_imports_and_same_mtime_snapshot_change(self):
        before={p.relative_to(self.root).as_posix():(hashlib.sha256(p.read_bytes()).hexdigest(),p.stat().st_mtime_ns) for p in self.root.rglob('*') if p.is_file()}
        self.call('search',self.search_params());self.entry(self.ids['focus']);self.call('relationships',self.graph_params())
        after={p.relative_to(self.root).as_posix():(hashlib.sha256(p.read_bytes()).hexdigest(),p.stat().st_mtime_ns) for p in self.root.rglob('*') if p.is_file()}
        self.assertEqual(before,after)
        self.assertEqual(set(self.package.loaded_digests),set(ordinary.READ_CLOSURE))
        self.edit_record(self.ids['focus'],lambda r:r.update(definition='Current changed definition.'))
        self.error('snapshot_changed','entry',dict(id=self.ids['focus'],section='header',cursor=None))
        new=self.call('context',{'refresh':True});self.assertNotEqual(new['snapshot'],self.snapshot)


if __name__=='__main__':unittest.main()
