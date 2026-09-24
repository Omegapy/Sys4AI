"""Registered tuple authority, exact locator compatibility and transient evidence."""
import hashlib
import json
import os
import unittest
from test_explorer_read import ReaderCase
from ontology_core import check_locator, canonical_bytes
from ontology_explorer_source import extract, contained


class SourceTests(ReaderCase):
    def ref(self,ident=None):return self.entry(ident or self.ids['focus'],'sources')['data']['references'][0]
    def source_params(self,ref,**kw):return dict(owner_id=ref['owner_id'],reference_id=ref['reference_id'],cursor=kw.get('cursor'))

    def test_full_tuple_identity_direct_binding_and_owner_projection(self):
        refs=self.entry(self.ids['focus'],'sources')['data']['references']
        self.assertEqual(len(refs),2)
        self.assertEqual(len({r['reference_id'] for r in refs}),2)
        self.assertEqual({r['binding_id'] for r in refs},{None,self.ids['binding']})
        direct=self.entry(self.ids['binding'],'sources')['data']['references'][0]
        self.assertNotIn(direct['reference_id'],{r['reference_id'] for r in refs})
        for r in refs+[direct]:
            identity={k:r[k] for k in ('owner_id','binding_id','path','locator','recorded_sha256')}
            self.assertEqual(r['reference_id'],hashlib.sha256(canonical_bytes(identity)).hexdigest())
        self.error('source_forbidden','source',dict(owner_id=self.ids['duplicate'],reference_id=refs[0]['reference_id'],cursor=None))
        self.error('source_forbidden','source',dict(owner_id=self.ids['focus'],reference_id='0'*64,cursor=None))

    def test_source_exact_json_lines_sections_and_inert_text(self):
        ident='urn:sys4ai:ontology:project:explorer-alpha:entry-00012'
        ref=self.ref(ident);result=self.call('source',self.source_params(ref))
        self.assertEqual(result['data']['extraction']['kind'],'exact_json')
        self.assertEqual(json.loads(''.join(c['text'] for c in result['data']['chunks'])),'Exact JSON evidence')
        ident='urn:sys4ai:ontology:project:explorer-alpha:entry-00010'
        ref=self.ref(ident);result=self.call('source',self.source_params(ref))
        text=''.join(c['text'] for c in result['data']['chunks'])
        self.assertIn('<script>',text);self.assertEqual(result['data']['extraction']['content_type'],'text/plain')
        self.assertEqual(result['data']['extraction']['kind'],'exact_section')
        ref=self.entry('urn:sys4ai:ontology:project:explorer-alpha:entry-00011','sources')['data']['references'][0]
        result=self.call('source',self.source_params(ref));self.assertEqual(result['data']['extraction']['kind'],'exact_lines')

    def test_ambiguous_nonheading_and_markdown_structural_boundaries(self):
        cases=[(b'# Repeated\none\n# Repeated\ntwo\n','section:Repeated'),
               (b'```\n# Hidden\n```\n','section:Hidden'),
               (b'    Not a heading\n---\nTail\n','section:Not a heading'),
               (b'First\nSecond\n---\nBody\n','section:Second'),
               (b'<!--\n# Hidden title\n-->\nTail\n','section:Hidden title'),
               (b'<div>\n# Hidden title\n</div>\n','section:Hidden title')]
        for raw,locator in cases:
            with self.subTest(locator=locator,raw=raw):
                check_locator(raw,locator);self.assertEqual(extract(raw,locator).kind,'bounded_excerpt')
        result=extract(b'# A\nOne\n\nB\n=\nTwo\n','section:A')
        self.assertEqual(result.text,'# A\nOne\n\n')
        result=extract(b'# A\nOne\n\nFirst\nSecond\n---\nTwo\n','section:A')
        self.assertEqual(result.text,'# A\nOne\n\nFirst\nSecond\n---\nTwo\n') # level2 is inside A
        result=extract(b'## A\nOne\n\nFirst\nSecond\n---\nTwo\n','section:A')
        self.assertEqual(result.text,'## A\nOne\n\n')

    def test_canonical_json_legacy_pointer_semantics_and_resolved_containment(self):
        for raw,locator,expected in [(b'{"":{"x":2}}','json:/',{'':{'x':2}}),(b'{"a":1}','json:/a/',1),(b'{"a":1}','json:a',1),
            (b'["first","second"]','json:/-1','second'),(b'["first","second"]','json:/00','first'),
            (b'{"a/b":{"~x":3}}','json:/a~1b/~0x',3)]:
            check_locator(raw,locator);value=extract(raw,locator)
            self.assertEqual(value.kind,'exact_json');self.assertEqual(json.loads(value.text),expected)
        raw=b'[{"value":1},{"value":2}]'
        self.assertTrue(contained(extract(raw,'json:/00'),extract(raw,'json:/0/value')))
        self.assertTrue(contained(extract(raw,'json:/-1'),extract(raw,'json:/1/value')))
        self.assertFalse(contained(extract(raw,'json:/0'),extract(raw,'json:/1/value')))

    def test_source_only_change_keeps_reference_snapshot_and_continuation_hash(self):
        ref=self.ref('urn:sys4ai:ontology:project:explorer-alpha:entry-00010');path=self.root/ref['path'];original=self.snapshot
        raw=path.read_bytes();stat=path.stat();path.write_bytes(raw+b'\nChanged evidence.\n');os.utime(path,ns=(stat.st_atime_ns,stat.st_mtime_ns))
        result=self.call('source',self.source_params(ref));self.assertEqual(result['status'],'source_changed')
        self.assertEqual(result['snapshot'],original);self.assertEqual(self.store.current.snapshot_id,original)
        self.assertTrue(result['data']['observation']['outside_snapshot']);self.assertEqual(result['data']['reference']['recorded_sha256'],ref['recorded_sha256'])
        self.error('snapshot_changed','entry',dict(id=ref['owner_id'],section='header',cursor=None))
        self.snapshot=self.call('context',{'refresh':True})['snapshot']
        self.configure(lambda c:c['limits'].update(page_items=1,source_excerpt_bytes=256))
        ref=self.ref('urn:sys4ai:ontology:project:explorer-alpha:entry-00010');path.write_bytes(b'# Inert evidence\n'+b'plain selected evidence\n'*100)
        first=self.call('source',self.source_params(ref));self.assertIsNotNone(first['page']['next_cursor'])
        path.write_bytes(path.read_bytes()+b'another change\n')
        self.error('source_observation_changed','source',self.source_params(ref,cursor=first['page']['next_cursor']))

    def test_source_page_aggregate_bytes_and_exact_continuation(self):
        ref=self.ref('urn:sys4ai:ontology:project:explorer-alpha:entry-00010')
        path=self.root/ref['path'];body='# Inert evidence\n'+'界🙂 exact source\n'*1800;path.write_text(body)
        chunks,pages=self.page_all('source',self.source_params(ref),'chunks')
        self.assertEqual(''.join(c['text'] for c in chunks),body)
        for page in pages:self.assertLessEqual(sum(len(c['text'].encode()) for c in page['data']['chunks']),8192)
        offset=0
        for chunk in chunks:self.assertEqual(chunk['offset'],offset);offset+=len(chunk['text'].encode())

    def test_many_refs_paged_and_source_body_not_retained(self):
        params=dict(id='urn:sys4ai:ontology:project:explorer-alpha:entry-00011',section='sources',cursor=None)
        refs,pages=self.page_all('entry',params,'references')
        self.assertEqual(len(refs),130);self.assertEqual([r['reference_id'] for r in refs],sorted({r['reference_id'] for r in refs}))
        ref=refs[0];before=set(vars(self.reader));self.call('source',self.source_params(ref));self.assertEqual(before,set(vars(self.reader)))

    def test_missing_binary_symlink_and_canonical_drift_fail_safely(self):
        ref=self.ref('urn:sys4ai:ontology:project:explorer-alpha:entry-00010');path=self.root/ref['path']
        original=path.read_bytes();path.unlink();self.error('source_unavailable','source',self.source_params(ref))
        path.write_bytes(b'\xff\xfe');self.error('source_unavailable','source',self.source_params(ref))
        path.unlink();path.symlink_to(self.root/'SPECS.md');self.error('source_unavailable','source',self.source_params(ref))
        path.unlink();path.write_bytes(original)
        self.edit_record(ref['owner_id'],lambda r:r.update(definition='Different canonical text'))
        self.error('snapshot_changed','source',self.source_params(ref))


if __name__=='__main__':unittest.main()
