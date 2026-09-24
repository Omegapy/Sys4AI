"""Independent qualification against real HTTP in owned disposable projects.

Never runs writes against the depot or an installed product. Secret-bearing
responses stay in memory; observations contain fixed assertion names/counts.
"""
import ast
import hashlib
import json
import os
from pathlib import Path
import sys
import unittest
from test_explorer_service import Harness,OBSERVATIONS,inventory

class SecurityTests(unittest.TestCase):
    def setUp(self):
        self.h=Harness(identity='explorer-alpha').start();self.s=self.h.connect()
        self.ctx=self.ok(self.h.read(self.s));self.snap=self.ctx['snapshot']
    def tearDown(self):self.h.close()
    def ok(self,result):
        self.assertEqual(result[0],200);return json.loads(result[2])
    def denied(self,result,codes=None):
        status,headers,raw=result;self.assertGreaterEqual(status,400)
        self.assertLessEqual(len(raw),1024)
        value=json.loads(raw);self.assertEqual(value['status'],'error')
        for name in ('data','project','snapshot','session_scope','service_instance'):
            self.assertIsNone(value[name],name)
        self.assertEqual(headers['Cache-Control'],'no-store')
        self.assertFalse(any(k.lower().startswith('access-control-allow') for k in headers))
        for secret in (self.s['value']['csrf'],self.s['cookie'].split('=',1)[1],str(self.h.root)):
            self.assertTrue(secret.encode() not in raw,'diagnostic_secret_redaction')
        if codes:self.assertIn(value['error']['code'],codes)
        return value['error']['code']
    def entry(self,ident,section='header'):
        return self.ok(self.h.read(self.s,'entry',dict(id=ident,section=section,cursor=None),self.snap))
    def test_at24_every_old_write_family_is_closed(self):
        h=self.h;before=inventory(h.root)
        names=['draft','proposal','validate','decide','publish','recover','generate','advanced','import','rdf-import',
               'profile','task','task-mutate','execute','dispatch','skill','agent','build','wiki','memory']
        count=0
        for prefix in ('/api/','/api/explorer/v1/'):
            for name in names:
                self.denied(h.request(prefix+name,{'action':name,'root':'/etc','command':'publish'},
                    headers={'Cookie':self.s['cookie'],'X-Explorer-CSRF':self.s['value']['csrf']}));count+=1
        self.assertEqual(before,inventory(h.root))
        OBSERVATIONS.append({'case':'AT-24','requests':count,'families':names,'protected_files_unchanged':True})
    def test_at25_host_origin_credentials_and_root_selection(self):
        h=self.h;cases=[{'Host':'localhost:'+str(h.service.port)},{'Host':'other.invalid'},
          {'Origin':'null'},{'Origin':'https://outside.invalid'},{'Origin':h.service.origin+'.outside.invalid'},
          {'X-Explorer-CSRF':'wrong'},{'Cookie':'wrong=value'},{'Cookie':self.s['cookie']+'; '+self.s['cookie']},
          {'Sec-Fetch-Site':'cross-site'}]
        for headers in cases:self.denied(h.read(self.s,headers=headers))
        for field in ('root','project_root','project','path','command','operation'):
            self.denied(h.read(self.s,body={field:'../sibling'}),['invalid_request'])
        other=Harness(identity='explorer-beta').start()
        try:
            b=other.connect();bctx=self.ok(other.read(b))
            self.denied(other.read(self.s),['session_invalid'])
            self.denied(other.read(b,headers={'X-Explorer-CSRF':self.s['value']['csrf']}),['csrf_forbidden'])
            params=dict(query='Alignment',category=None,lifecycles=['approved'],fact_kinds=['asserted'],sort='relevance',limit=1,cursor=None)
            asearch=self.ok(h.read(self.s,'search',params,self.snap));bsearch=self.ok(other.read(b,'search',params,bctx['snapshot']))
            self.assertTrue(asearch['page']['next_cursor']);self.assertTrue(bsearch['page']['next_cursor'])
            self.denied(other.read(b,'search',{**params,'cursor':asearch['page']['next_cursor']},bctx['snapshot']),['cursor_invalid'])
            aid=asearch['data']['items'][0]['entry']['id'];bid=bsearch['data']['items'][0]['entry']['id']
            self.assertNotEqual(aid,bid);self.assertEqual(asearch['data']['items'][0]['entry']['label'],bsearch['data']['items'][0]['entry']['label'])
            av=self.entry(h.ids['focus'],'definition');bv=self.ok(other.read(b,'entry',dict(id=other.ids['focus'],section='definition',cursor=None),bctx['snapshot']))
            atext=''.join(c['text'] for c in av['data']['chunks']);btext=''.join(c['text'] for c in bv['data']['chunks'])
            self.assertEqual(atext,'Alignment means matching fixture document coordinates.')
            self.assertEqual(btext,'Alignment means scheduling independent fixture inspection windows.')
            self.assertNotEqual(atext,btext);self.assertNotEqual(self.ctx['project']['root_scope_id'],bctx['project']['root_scope_id'])
            self.denied(h.read(self.s,'entry',dict(id=other.ids['focus'],section='header',cursor=None),self.snap),['identity_unavailable'])
        finally:other.close()
        OBSERVATIONS.append({'case':'AT-25','hostile_headers':len(cases),'root_selector_fields':6,'simultaneous_namespaces':2,'credential_cursor_and_identity_isolation':True})
    def test_at26_paths_and_registered_source_owner(self):
        h=self.h
        paths=['/../ontology.yaml','/%2e%2e/ontology.yaml','/%252e%252e/ontology.yaml','//etc/passwd',
          '/%2fetc%2fpasswd','/C:%5cWindows%5cwin.ini','/health?root=../sibling','/docs/inert.md',
          '/.sys4ai/ontology/explorer/identity.json','/manifest.json','/node_modules/package.json']
        for path in paths:self.denied(h.request(path))
        ref=self.entry(h.ids['focus'],'sources')['data']['references'][0]
        self.denied(h.read(self.s,'source',dict(owner_id=h.ids['duplicate'],reference_id=ref['reference_id'],cursor=None),self.snap),['source_forbidden'])
        self.denied(h.read(self.s,'source',dict(owner_id=h.ids['focus'],reference_id='0'*64,cursor=None),self.snap),['source_forbidden'])
        for field in ('path','root','url','locator'):
            self.denied(h.read(self.s,'source',dict(owner_id=h.ids['focus'],reference_id=ref['reference_id'],cursor=None,**{field:'/etc/passwd'}),self.snap),['invalid_request'])
        OBSERVATIONS.append({'case':'AT-26-route-authority','path_variants':len(paths),'wrong_owner_and_reference_denied':True,'browser_file_selector_fields_denied':4})
    def test_at26_source_replacement_never_follows_or_repairs(self):
        h=self.h;ident='urn:sys4ai:ontology:project:explorer-alpha:entry-00010'
        ref=self.entry(ident,'sources')['data']['references'][0];path=h.root/ref['path'];raw=path.read_bytes()
        params=dict(owner_id=ident,reference_id=ref['reference_id'],cursor=None)
        protected={p:v for p,v in inventory(h.root).items() if p!=ref['path']}
        outside=h.base/'outside-secret.txt';outside.write_text('UNSELECTED SENTINEL')
        variants=[]
        for variant in ('symlink','oversized','binary','missing'):
            if path.exists() or path.is_symlink():path.unlink()
            if variant=='symlink':path.symlink_to(outside)
            elif variant=='oversized':path.write_bytes(b'x'*(2_000_000+1))
            elif variant=='binary':path.write_bytes(b'\xff\xfe')
            response=h.read(self.s,'source',params,self.snap)
            expected_status,expected_code=(503,'resource_limit') if variant=='oversized' else (422,'source_unavailable')
            code=self.denied(response,[expected_code]);self.assertEqual(response[0],expected_status)
            variants.append({'variant':variant,'http_status':response[0],'observed_error_code':code})
            self.assertEqual(protected,{p:v for p,v in inventory(h.root).items() if p!=ref['path']})
        path.write_bytes(raw)
        OBSERVATIONS.append({'case':'AT-26-file-authority','variants':variants,'symlink_escape_oversize_binary_missing_denied':True,'no_provenance_repair':True})
    def test_at27_inert_wire_text_and_minimal_csp(self):
        h=self.h;ident='urn:sys4ai:ontology:project:explorer-alpha:entry-00010'
        head=self.entry(ident);ref=self.entry(ident,'sources')['data']['references'][0]
        value=self.ok(h.read(self.s,'source',dict(owner_id=ident,reference_id=ref['reference_id'],cursor=None),self.snap))
        self.assertEqual(value['data']['extraction']['content_type'],'text/plain')
        text=''.join(x['text'] for x in value['data']['chunks']);self.assertIn('<script>',text);self.assertIn('javascript:',text)
        response=h.request('/');self.assertEqual(response[0],200);csp=response[1]['Content-Security-Policy']
        for forbidden in ('unsafe-eval','unsafe-inline','https:','http:','data:','*'):self.assertNotIn(forbidden,csp)
        self.assertIn("script-src 'self'",csp);self.assertIn("object-src 'none'",csp)
        OBSERVATIONS.append({'case':'AT-27-wire','plain_text_preserves_script_and_link_bytes':True,'strict_production_csp':True,'qualification':'Browser execution/DOM assertions are recorded separately.'})

class CallAuditTests(unittest.TestCase):
    def test_actual_reader_forbidden_call_instrumentation(self):
        h=Harness(identity='explorer-audit');store=None
        try:
            mod=h.package.modules['ontology_explorer_read'];snap=h.package.modules['ontology_explorer_snapshot']
            store=snap.SnapshotStore(h.root,h.package)
            reader=mod.Reader(store,service_instance='1'*32,build_id=h.assets.manifest['build_id'],schema_sha256=hashlib.sha256(h.package.member_bytes['schema']).hexdigest(),service_secret=b'x'*32)
            forbidden={'write_json','atomic_write','atomic_write_json','publish','recover','proposal','draft','generate','build_wiki','ensure_backend','provision','execute','run_skill','run_agent'}
            calls=set();old=sys.getprofile()
            def profile(frame,event,arg):
                if event=='call' and frame.f_code.co_filename.startswith(str(h.scripts)):
                    name=frame.f_code.co_name;calls.add(name)
                    if name in forbidden:raise AssertionError('Forbidden operation invoked: '+name)
            before=inventory(h.root);sys.setprofile(profile)
            def read(op,params,snapshot=None):
                value=reader.read(op,dict(schema_version=1,request_id='audit',code_epoch=h.package.code_epoch,snapshot=snapshot,params=params),session_scope='2'*32)
                self.assertIn(value['status'],('ok','ambiguous','incomplete','empty'))
                self.assertIsNotNone(value['data']);self.assertEqual(value['operation'],op)
                self.assertTrue(mod.validate(value,op.title()+'Response',reader.schema),'valid_read_response')
                return value
            try:
                ctx=read('context',{'refresh':False});sid=ctx['snapshot'];ident=h.ids['focus']
                read('search',dict(query='Alignment',category=None,lifecycles=['approved'],fact_kinds=['asserted'],sort='relevance',limit=3,cursor=None),sid)
                for section in ('header','sources','details'):read('entry',dict(id=ident,section=section,cursor=None),sid)
                graph=dict(id=ident,direction='both',predicate_ids=[],lifecycles=['approved'],fact_kinds=['asserted'],limit=3,cursor=None)
                read('relationships',graph,sid);read('neighborhood',{**graph,'node_limit':3},sid)
                ref=read('entry',dict(id=ident,section='sources',cursor=None),sid)['data']['references'][0]
                read('source',dict(owner_id=ident,reference_id=ref['reference_id'],cursor=None),sid)
            finally:sys.setprofile(old)
            self.assertEqual(before,inventory(h.root));self.assertFalse(calls&forbidden)
            allowed=set(mod.READ_CLOSURE)|{'ontology_explorer','ontology_explorer_worker','ontology_explorer_assets','ontology_explorer_health'}
            imported=set()
            for name in allowed:
                tree=ast.parse((h.scripts/(name+'.py')).read_bytes())
                for node in ast.walk(tree):
                    if isinstance(node,ast.Import):imported.update(x.name for x in node.names if x.name.startswith('ontology'))
                    elif isinstance(node,ast.ImportFrom) and node.module and node.module.startswith('ontology'):imported.add(node.module)
            self.assertEqual(imported-allowed,{'ontology_advanced_packet','ontology_semantic'})
            self.assertTrue(set(h.package.loaded_digests)<=allowed,'loaded_module_allowlist')
            self.assertTrue(all(not any(n in name for n in ('semantic','advanced_packet')) for name in h.package.loaded_digests),'optional_modules_not_loaded')
            OBSERVATIONS.append({'case':'forbidden-call-audit','actual_reader_operations':6,'profiled_function_count':len(calls),'forbidden_function_names':sorted(forbidden),'forbidden_calls':0,'lexical_project_imports':sorted(imported),'actual_loaded_modules':sorted(h.package.loaded_digests),'deferred_optional_imports':'ontology_retrieval.search lines119/124 are conditional on semantic; Explorer uses semantic=False and neither module loaded or ran','protected_files_unchanged':True,'qualification':'Instrumentation observes exact captured in-process Reader. Real service transport is tested separately; no instrumented source replaces accepted production bytes.'})
        finally:
            if store:store.close()
            h.close()
