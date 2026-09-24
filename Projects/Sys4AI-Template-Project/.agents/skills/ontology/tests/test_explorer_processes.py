"""Configured process identities and evidence-supported order only."""
import json
import unittest
from test_explorer_read import ReaderCase


class ProcessTests(ReaderCase):
    def test_ordered_unordered_partial_stale_states_and_exact_purpose(self):
        expected=['recorded','missing','partial','recorded']
        for ident,state in zip(self.ids['processes'],expected):
            result=self.entry(ident,'process');self.assertEqual(result['data']['process']['order_state'],state)
            purpose=[x['text'] for x in result['data']['process_items'] if x['kind']=='field' and x['name']=='purpose']
            self.assertEqual(''.join(purpose),self.store.current.project.by_id[ident]['definition'])
            if state!='recorded':self.assertTrue(any(x['code']=='ordering_unavailable' for x in result['diagnostics']))
            steps=[x for x in result['data']['process_items'] if x['kind']=='ordered_step']
            self.assertEqual(bool(steps),state=='recorded')
        ident=self.ids['processes'][-1];path=self.root/'docs/process-stale.md';path.write_text(path.read_text()+'\nChanged.\n')
        self.snapshot=self.call('context',{'refresh':True})['snapshot']
        result=self.entry(ident,'process');self.assertEqual(result['data']['process']['order_state'],'stale')
        self.assertFalse(any(x['kind']=='ordered_step' for x in result['data']['process_items']))
        self.assertTrue(any(x['code']=='source_changed' for x in result['diagnostics']))

    def test_process_support_and_text_fragments_page_losslessly(self):
        ident=self.ids['processes'][0];original=self.entry(ident,'process')['data']['process_items']
        self.configure(lambda c:c['limits'].update(page_items=1,source_excerpt_bytes=256))
        items,pages=self.page_all('entry',dict(id=ident,section='process',cursor=None),'process_items')
        self.assertEqual(items,original)
        for i,x in enumerate(items):
            if x['kind']=='field' and x['part']=='text' and x['name']=='applicability':
                self.assertEqual(items[i-1]['part'],'references');self.assertEqual(items[i-1]['item_index'],x['item_index'])
        self.assertTrue(all(len(r['data']['process_items'])<=1 for r in pages))

    def test_configured_identity_not_name_or_type_and_invalid_selector_rejected(self):
        result=self.entry(self.ids['focus'],'process');self.assertEqual(result['data']['process']['order_state'],'missing');self.assertEqual(result['status'],'empty')
        old=self.store.current
        path=self.root/'ontology-explorer.yaml';config=json.loads(path.read_text())
        config['process_views'][0]['field_relations']['roles']=[dict(predicate_id=self.ids['focus'],direction='outgoing')]
        path.write_text(json.dumps(config))
        self.error('presentation_invalid','context',{'refresh':True});self.assertIs(self.store.current,old)

    def test_invalid_source_owner_widening_and_overlapping_steps_rejected(self):
        path=self.root/'ontology-explorer.yaml';original=path.read_text();config=json.loads(original)
        ref=self.entry(self.ids['duplicate'],'sources')['data']['references'][0]
        config['process_views'][0]['field_sources']['roles']=[dict(owner_id=ref['owner_id'],reference_id=ref['reference_id'],extract_locator=None)]
        path.write_text(json.dumps(config));self.error('presentation_invalid','context',{'refresh':True})
        config=json.loads(original);config['process_views'][0]['ordered_source']['steps'][1]['locator']='lines:3-4'
        path.write_text(json.dumps(config));self.error('presentation_invalid','context',{'refresh':True})

    def test_source_change_during_candidate_callback_never_accepts_mixed_order(self):
        original=self.reader.source_bytes;changed=False
        def race(view,ref,cache):
            nonlocal changed
            raw=original(view,ref,cache)
            if not changed and ref['path']=='docs/process-ordered.md':
                changed=True;path=self.root/ref['path'];path.write_bytes(raw+b'\nChanged during callback.\n')
            return raw
        self.reader.source_bytes=race
        self.edit_record(self.ids['focus'],lambda r:r.update(definition='Force a new candidate.'))
        self.snapshot=self.call('context',{'refresh':True})['snapshot']
        self.assertTrue(changed)
        result=self.entry(self.ids['processes'][0],'process')
        self.assertEqual(result['data']['process']['order_state'],'stale')
        self.assertFalse(any(x['kind']=='ordered_step' for x in result['data']['process_items']))

    def test_process_missing_source_retains_definition_and_no_order(self):
        ident=self.ids['processes'][0];(self.root/'docs/process-ordered.md').unlink()
        self.snapshot=self.call('context',{'refresh':True})['snapshot']
        result=self.entry(ident,'process');self.assertEqual(result['data']['process']['order_state'],'unavailable')
        self.assertTrue(any(x['kind']=='field' and x['name']=='purpose' for x in result['data']['process_items']))


if __name__=='__main__':unittest.main()
