"""Canonical ranked search and authenticated keyset progression regressions."""
import copy
import hashlib
import json
import unittest
from test_explorer_read import ReaderCase
from ontology_retrieval import match, normalize


class SearchTests(ReaderCase):
    def test_duplicates_aliases_preferred_identity_and_canonical_ranking(self):
        params=self.search_params(query='Alignment',sort='relevance',limit=1)
        rows,pages=self.page_all('search',params)
        self.assertEqual([x['entry']['id'] for x in rows],[self.ids['focus'],self.ids['duplicate']])
        self.assertEqual(pages[-1]['status'],'ambiguous')
        alias=self.call('search',self.search_params(query='Orientation',sort='relevance'))
        self.assertEqual([x['entry']['id'] for x in alias['data']['items']],[self.ids['focus'],self.ids['duplicate']])
        self.assertTrue(all(x['entry']['matched_alias']=='Orientation' and x['entry']['match_reason']=='alias' for x in alias['data']['items']))
        rows,_=self.page_all('search',self.search_params(query='FixtureTaskManager',sort='relevance',limit=2))
        expected=[]
        for r in self.store.current.project.records:
            if r['kind']=='binding':continue
            found=match(r,'FixtureTaskManager')
            if found:expected.append(((found[0],-found[1],r['@id']),r['@id']))
        self.assertEqual([x['entry']['id'] if x['kind']=='entry' else x['id'] for x in rows],[x[1] for x in sorted(expected)])

    def test_filters_before_paging_and_oversized_label_consumes_once(self):
        params=self.search_params(category='artifacts',lifecycles=['approved'],fact_kinds=['asserted'],limit=3)
        rows,pages=self.page_all('search',params)
        group=next(c for c in self.reader.categories(self.store.current)[0] if c['id']=='artifacts')
        expected=sorted((normalize(r['label']),r['@id']) for r in self.store.current.project.records if r['kind']!='binding' and r['lifecycle']=='approved' and r['fact_kind']=='asserted' and self.reader.in_category(r,group))
        ids=[x['entry']['id'] if x['kind']=='entry' else x['id'] for x in rows]
        self.assertEqual(ids,[x[1] for x in expected]);self.assertEqual(len(ids),len(set(ids)))
        omitted=next(x for x in rows if x.get('id')==self.ids['long_label'])
        self.assertEqual(omitted['reason'],'field_limit');self.assertEqual(omitted['detail']['section'],'label')
        self.assertTrue(all(p['coverage']['filter_exclusions']>0 for p in pages))

    def test_deferred_fitting_items_never_become_markers(self):
        self.configure(lambda c:c['limits'].update(response_bytes=4000))
        params=self.search_params(query='Fixture entry',sort='relevance',limit=20)
        rows,pages=self.page_all('search',params)
        self.assertGreater(len(pages),1)
        self.assertTrue(all(x['kind']=='entry' for x in rows))
        self.assertTrue(any('byte_limit' in p['coverage']['reasons'] for p in pages))
        ids=[x['entry']['id'] for x in rows];self.assertEqual(len(ids),len(set(ids)))

    def test_oversized_summary_byte_marker_preserves_later_identities(self):
        ident='urn:sys4ai:ontology:project:explorer-alpha:entry-00020'
        self.edit_record(ident,lambda r:r.update(label='AAA '+('x'*3000),definition='A selected bulky summary.'))
        self.configure(lambda c:c['limits'].update(response_bytes=4000))
        rows,pages=self.page_all('search',self.search_params(limit=20))
        ids=[x['entry']['id'] if x['kind']=='entry' else x['id'] for x in rows]
        self.assertEqual(len(ids),len(set(ids)))
        bulky=next(x for x in rows if x.get('id')==ident)
        self.assertEqual(bulky['reason'],'byte_limit')
        self.assertTrue(ids.index(ident)<len(ids)-1)
        # An irreducible marker/cursor envelope does not consume its identity.
        self.configure(lambda c:c['limits'].update(response_bytes=1024))
        self.error('resource_limit','search',self.search_params(limit=20))

    def test_exact_query_case_interior_whitespace_and_outer_whitespace(self):
        params=self.search_params(query=' Fixture ',sort='relevance',limit=1)
        first=self.call('search',params);token=first['page']['next_cursor'];self.assertIsNotNone(token)
        same=self.call('search',{**params,'query':'Fixture','cursor':token});self.assertEqual(same['scope']['query'],'Fixture')
        self.error('cursor_scope_changed','search',{**params,'query':'fixture','cursor':token})
        self.error('cursor_scope_changed','search',{**params,'query':'Fix ture','cursor':token})
        ident='urn:sys4ai:ontology:core:Task'
        first=self.call('search',self.search_params(query=ident,sort='relevance',limit=1))
        self.assertIsNotNone(first['page']['next_cursor'])
        self.error('cursor_scope_changed','search',self.search_params(query=ident[:-4]+'task',sort='relevance',limit=1,cursor=first['page']['next_cursor']))
        # Give three existing distinct identities the canonical CamelCase query
        # in their definition; this is a disposable fixture change only.
        for suffix in ('00020','00021','00022'):
            self.edit_record('urn:sys4ai:ontology:project:explorer-alpha:entry-'+suffix,lambda r:r.update(definition='TaskManager manages this recorded fixture.'))
        self.snapshot=self.call('context',{'refresh':True})['snapshot']
        first=self.call('search',self.search_params(query='TaskManager',sort='relevance',limit=1))
        self.assertIsNotNone(first['page']['next_cursor'])
        self.error('cursor_scope_changed','search',self.search_params(query='taskmanager',sort='relevance',limit=1,cursor=first['page']['next_cursor']))

    def test_scope_session_service_root_policy_and_tampering(self):
        params=self.search_params(limit=1);first=self.call('search',params);cursor=first['page']['next_cursor'];continuation={**params,'cursor':cursor}
        self.error('cursor_scope_changed','search',continuation,session='4'*32)
        self.error('cursor_scope_changed','search',{**continuation,'limit':2})
        self.error('cursor_scope_changed','search',{**continuation,'lifecycles':['approved']})
        original=self.reader.instance;self.reader.instance='5'*32
        self.error('cursor_scope_changed','search',continuation);self.reader.instance=original
        self.error('cursor_invalid','search',{**continuation,'cursor':cursor[:-1]+('A' if cursor[-1]!='A' else 'B')})
        view=self.store.current;policy=self.reader.policy(view);scope=self.reader.scope('search',params,view,policy)
        base=self.reader._cursor_base(view,'search',scope,policy,self.session,'label')
        changed={**base,'root_scope':'0'*64}
        key=self.reader.decode_cursor(cursor,base,policy)
        wrong=self.reader.encode_cursor(changed,key,policy,self.reader.now())
        self.error('cursor_scope_changed','search',{**continuation,'cursor':wrong})
        changed={**base,'project_id':'other-project'}
        wrong=self.reader.encode_cursor(changed,key,policy,self.reader.now())
        self.error('cursor_scope_changed','search',{**continuation,'cursor':wrong})
        key['label_sha256']='0'*64
        wrong=self.reader.encode_cursor(base,key,policy,self.reader.now())
        self.error('cursor_invalid','search',{**continuation,'cursor':wrong})

    def test_cursor_expiry_and_graph_direction(self):
        params=self.search_params(limit=1);first=self.call('search',params);cursor=first['page']['next_cursor']
        old=self.reader.clock;self.reader.clock=lambda:old()+301
        self.error('cursor_expired','search',{**params,'cursor':cursor})
        self.reader.clock=old
        params=self.graph_params(limit=1);first=self.call('relationships',params)
        self.error('cursor_scope_changed','relationships',{**params,'direction':'incoming','cursor':first['page']['next_cursor']})


if __name__=='__main__':unittest.main()
