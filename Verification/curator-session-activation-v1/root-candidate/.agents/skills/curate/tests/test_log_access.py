"""Bounded log behavior; all generated files and Broker Tasks are disposable."""
import base64
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

PACKAGE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PACKAGE/'scripts'))
from curator_logs import DEFAULTS,MAXIMA,LogService,register_log
from curator_policy import PolicyError,canonical
from curator_confinement import source_manifest

# Authentic selected output only, from native-p1-attempt11 poststop-owned-cells
# 01a091b2-edae-7ad0-a0e7-109c19413adf-060.json (SHA256 cd712e3e9104f5f22432366aa207f8c16b078940b22c3ce51b97e7a6065c6974).
# The surrounding header, activity and padding below are synthetic, not a log copy.
AUTHENTIC_OUTPUT=base64.b64decode('eyJ0aW1lc3RhbXAiOiIyMDI2LTA5LTExVDE4OjQzOjQ3LjQ5OFoiLCJvcmRpbmFsIjo2MzIsInR5cGUiOiJyZXNwb25zZV9pdGVtIiwicGF5bG9hZCI6eyJ0eXBlIjoiY3VzdG9tX3Rvb2xfY2FsbF9vdXRwdXQiLCJpZCI6ImN0Y29fMDFhMDkxYzgtNzBhYS03YjIzLTgwZDYtMGY2NGM2YjEwNWJjIiwiY2FsbF9pZCI6ImNhbGxfZTRscjRGSnpvZG1uTUpQRGJIWXdjdGQwIiwib3V0cHV0IjpbeyJ0eXBlIjoiaW5wdXRfdGV4dCIsInRleHQiOiJTY3JpcHQgY29tcGxldGVkXG5XYWxsIHRpbWUgMC40IHNlY29uZHNcbk91dHB1dDpcbiJ9LHsidHlwZSI6ImlucHV0X3RleHQiLCJ0ZXh0IjoidW5zYWZlX2ZpbGUifV0sImludGVybmFsX2NoYXRfbWVzc2FnZV9tZXRhZGF0YV9wYXNzdGhyb3VnaCI6eyJ0dXJuX2lkIjoiMDFhMDkxYzUtZWVmZS03NDEwLWIyMGYtODM2YWQ4ZTA3OWRjIiwiY3JlYXRlX3RpbWUiOjE3ODkxNTIyMjcuNDk4NTA1fX19Cg==')
ACTOR='01a091b2-edae-7ad0-a0e7-109c19413adf';TURN='01a091c5-eefe-7410-b20f-836ad8e079dc'


def record(value):return canonical(value)+b'\n'
def output(value):return record({'type':'response_item','payload':{'type':'custom_tool_call_output','call_id':'test-call','output':value}})


def reconstructed_log():
    header=record({'type':'session_meta','payload':{'id':ACTOR}})
    turn=record({'type':'event_msg','payload':{'type':'task_started','turn_id':TURN}})
    def filler(count,total):
        base=record({'type':'response_item','payload':{'type':'message','role':'user','content':[{'type':'input_text','text':''}]}})
        budget=total-len(base)*count;assert budget>=0
        quotient,remainder=divmod(budget,count)
        return b''.join(base.replace(b'"text":""',b'"text":"'+b'X'*(quotient+(index<remainder))+b'"') for index in range(count))
    before=header+turn;before+=filler(391,2493880-len(before))
    raw=before+AUTHENTIC_OUTPUT;raw+=filler(8,2500473-len(raw))
    assert len(raw)==2500473 and len(raw.splitlines())==402
    return raw


class LogAccessTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name).resolve()

    def service(self,raw,*,native=False,readers=()):
        path=self.root/('log-'+str(len(list(self.root.iterdir())))+'.jsonl');path.write_bytes(raw)
        entry=register_log(self.root,path.name,actor=ACTOR if native else None,format='native-jsonl' if native else 'text',readers=readers)
        return LogService({'log':entry}),path

    def test_authentic_list_output_is_visible_in_synthetic_large_log_with_exact_refs(self):
        self.assertEqual(hashlib.sha256(AUTHENTIC_OUTPUT).hexdigest(),'62574bc0c84a5ebd1a1c4a1709bb366ec0829761f6ee176f5dae51253d349c5c')
        service,path=self.service(reconstructed_log(),native=True);before=hashlib.sha256(path.read_bytes()).hexdigest()
        summary=service.summary('log');self.assertTrue(summary['coverage']['complete_source']);self.assertLessEqual(len(canonical(summary))+1,DEFAULTS['response_bytes'])
        found=next(item for item in summary['significant'] if 'unsafe_file' in item.get('excerpt',''))
        self.assertEqual((found['line'],found['byte_start'],found['byte_end']),(394,2493880,2494358))
        self.assertEqual(found['turn_id'],TURN);self.assertEqual(found['event_ordinal'],632)
        self.assertEqual(found['call_id'],'call_e4lr4FJzodmnMJPDbHYwctd0')
        self.assertEqual(found['record_sha256'],hashlib.sha256(AUTHENTIC_OUTPUT).hexdigest())
        query=service.query('log',{'literal':'unsafe_file'});self.assertEqual(query['matches'][0]['line'],394)
        excerpt=service.query('log',{'mode':'excerpt','start_line':394,'lines':1});self.assertEqual(excerpt['matches'][0]['record_sha256'],found['record_sha256'])
        self.assertNotIn('XXXXX',json.dumps(summary));self.assertEqual(before,hashlib.sha256(path.read_bytes()).hexdigest())

    def test_literal_search_precedes_clipping_and_match_centered_excerpt(self):
        service,_=self.service(('A'*1600+'TARGET-LITERAL'+'z'*100+'\n').encode())
        result=service.query('log',{'literal':'TARGET-LITERAL','projection':'tool_output'})
        self.assertEqual(len(result['matches']),1);self.assertIn('TARGET-LITERAL',result['matches'][0]['excerpt'])
        self.assertTrue(result['matches'][0]['excerpt_truncated']);self.assertLessEqual(len(result['matches'][0]['excerpt'].encode()),768)
        self.assertEqual(service.query('log',{'literal':'A.*TARGET','projection':'tool_output'})['matches'],[])
        service,_=self.service(('TARGET-PREFIX '+'a'*2000+' error at end\n').encode())
        result=service.query('log',{'literal':'TARGET-PREFIX','projection':'tool_output'})
        self.assertEqual(len(result['matches']),1);self.assertIn('TARGET-PREFIX',result['matches'][0]['excerpt'])
        header=record({'type':'session_meta','payload':{'id':ACTOR}})
        blocks=[{'type':'input_text','text':'ordinary'} for _ in range(100)]+[{'type':'input_text','text':'LAST-BLOCK'}]
        service,_=self.service(header+output(blocks),native=True)
        self.assertEqual(len(service.query('log',{'literal':'LAST-BLOCK','projection':'tool_output'})['matches']),1)

    def test_scan_boundary_does_not_discard_valid_record(self):
        service,_=self.service(b'a'*600+b'\n'+b'b'*600+b'needle\n')
        request={'literal':'needle','projection':'tool_output','scan_bytes':1024}
        first=service.query('log',request);self.assertEqual(first['matches'],[]);self.assertIsNotNone(first['cursor'])
        second=service.query('log',{**request,'cursor':first['cursor']});self.assertEqual([item['line'] for item in second['matches']],[2])
        service,_=self.service(b'a'*1600+b'needle\n')
        with self.assertRaises(PolicyError) as caught:service.query('log',request)
        self.assertEqual(caught.exception.code,'log_scan_bound')

    def test_response_pagination_keeps_every_undelivered_match(self):
        service,_=self.service(b''.join(('needle '+str(i)+'x'*650+'\n').encode() for i in range(30)))
        request={'literal':'needle','projection':'tool_output','response_bytes':4096};seen=[];cursor=None
        for _ in range(40):
            result=service.query('log',{**request,**({'cursor':cursor} if cursor else {})});self.assertLessEqual(len(canonical(result))+1,4096)
            seen.extend(item['line'] for item in result['matches']);cursor=result['cursor']
            if cursor is None:break
        self.assertEqual(seen,list(range(1,31)));self.assertIsNone(cursor)

    def test_typed_success_is_not_overridden_by_documentation_error_words(self):
        header=record({'type':'session_meta','payload':{'id':ACTOR}})
        raw=header+output([{'type':'input_text','text':json.dumps({'exit_code':0,'output':'Documentation: if an error occurs, preserve it; failed is an example.'})}])
        service,_=self.service(raw,native=True);result=service.summary('log')
        self.assertEqual(result['significant'],[]);self.assertEqual(result['recent'][-1]['status'],'succeeded')
        service,_=self.service(header+output({'exit_code':1,'output':'Permission denied'}),native=True)
        self.assertEqual(service.summary('log')['significant'][0]['status'],'failed')

    def test_private_records_bulk_and_raw_instructions_are_omitted_by_default(self):
        header=record({'type':'session_meta','payload':{'id':ACTOR,'instructions':'SECRET-HEADER'}})
        private=[{'type':'response_item','payload':{'type':'reasoning','text':'SECRET-REASONING'}},
            {'type':'response_item','payload':{'type':'message','role':'developer','content':'SECRET-DEVELOPER'}},
            {'type':'event_msg','payload':{'type':'token_count','data':'SECRET-TOKEN'}}]
        service,_=self.service(header+b''.join(record(row) for row in private)+output({'exit_code':0,'output':json.dumps({'contents':{'role':'SECRET-ROLE'}})}),native=True)
        for result in (service.summary('log'),service.query('log',{'literal':'SECRET'})):
            self.assertNotIn('SECRET',json.dumps(result));self.assertEqual(result.get('matches',[]),[])

    def test_malformed_oversized_partial_utf8_records_and_explicit_bounds(self):
        header=record({'type':'session_meta','payload':{'id':ACTOR}})
        service,_=self.service(header+b'{bad}\n'+b'\xff\n'+b'x'*500+b'\n'+b'{partial',native=True)
        result=service.summary('log',options={'record_bytes':256});self.assertEqual(result['counts']['malformed_record'],2)
        self.assertEqual(result['counts']['oversized_record'],1);self.assertTrue(result['coverage']['partial_last_record'])
        self.assertFalse(result['coverage']['complete_source'])
        for key,maximum in MAXIMA.items():
            with self.subTest(key=key),self.assertRaises(PolicyError):service.summary('log',options={key:maximum+1})
        with self.assertRaises(PolicyError):service.query('log',{'literal':'x','path':'elsewhere'})
        service,_=self.service((b'x'*500+b'\n')*30);request={'literal':'oversized_record','record_bytes':256,'response_bytes':4096}
        seen=[];cursor=None
        for _ in range(40):
            result=service.query('log',{**request,**({'cursor':cursor} if cursor else {})});seen.extend(item['line'] for item in result['matches']);cursor=result['cursor']
            if cursor is None:break
        self.assertEqual(seen,list(range(1,31)))

    def test_reader_epoch_cursor_growth_replacement_and_discovery_bounds(self):
        reader={'thread_id':'manager','session_id':'s','connection_id':'c','load_epoch':1}
        service,path=self.service(b'needle\n'*20,readers=[reader]);self.assertEqual(service.discover({**reader,'load_epoch':2})['logs'],[])
        with self.assertRaises(PolicyError):service.summary('log',reader={**reader,'thread_id':'peer'})
        first=service.query('log',{'literal':'needle','projection':'tool_output'},reader=reader)
        with path.open('ab') as target:target.write(b'append\n')
        with self.assertRaises(PolicyError):service.query('log',{'literal':'needle','projection':'tool_output','cursor':first['cursor']},reader=reader)
        self.assertTrue(service.summary('log',reader=reader)['coverage']['complete_source'])
        replacement=self.root/'replacement';replacement.write_bytes(path.read_bytes());os.replace(replacement,path)
        with self.assertRaises(PolicyError):service.summary('log',reader=reader)
        service,path=self.service(b'line\n');entry=service.entries['log'];many=LogService({('h'+str(i)+'x'*90):entry for i in range(50)})
        self.assertLessEqual(len(canonical(many.discover()))+1,16000)
        with self.assertRaises(PolicyError):LogService({str(i):entry for i in range(51)})
        with self.assertRaises(PolicyError):LogService({'🔥'*100:entry})

    def test_cli_registration_summary_search_excerpt_and_unchanged_log(self):
        log=self.root/'run.jsonl';log.write_bytes(reconstructed_log());registry=self.root/'registry.json';cli=PACKAGE/'scripts/curator.py'
        def command(*args):
            result=subprocess.run([sys.executable,'-B',str(cli),*args],env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),capture_output=True,timeout=15)
            self.assertEqual(result.returncode,0,result.stderr.decode()+result.stdout.decode());return json.loads(result.stdout)
        before=hashlib.sha256(log.read_bytes()).hexdigest()
        registered=command('log-register','--registry',str(registry),'--root',str(self.root),'--path',log.name,'--actor',ACTOR)
        handle=registered['handle'];self.assertEqual(command('log-list','--registry',str(registry))['logs'][0]['handle'],handle)
        self.assertEqual(command('log-summary','--registry',str(registry),'--handle',handle)['query_handle'],handle)
        self.assertEqual(command('log-query','--registry',str(registry),'--handle',handle,'--literal','unsafe_file')['matches'][0]['line'],394)
        self.assertEqual(command('log-query','--registry',str(registry),'--handle',handle,'--mode','excerpt','--start-line','394','--lines','1')['matches'][0]['line'],394)
        self.assertEqual(before,hashlib.sha256(log.read_bytes()).hexdigest())


class BrokerLogTests(unittest.TestCase):
    def test_actual_current_broker_discovery_artifact_summary_query_and_nonlog_preservation(self):
        from test_broker import ForkBrokerTests
        from curator_broker import Broker,native_tool_specs
        from curator_runtime_codex import shape
        f=ForkBrokerTests();f.setUp();self.addCleanup(f.doCleanups);fixture=f.fixture
        log=f.root/'selected.jsonl';log.write_bytes(reconstructed_log());actor=copy.deepcopy(fixture.actors[fixture.actor])
        entry=register_log(f.root,log.name,actor=ACTOR,readers=[actor])
        paths={item['path'] for item in f.manifest['files']}|{str(p.resolve()).lstrip('/') for p in (PACKAGE/'scripts').glob('*.py')}
        manifest=source_manifest('/',sorted(paths));input_path=f.root/'role-input.txt';input_path.write_bytes(b'FULL REQUIRED ROLE INPUT')
        artifacts={'log1':{'kind':'log','log':entry},'role':{'readers':[fixture.actor],'root':str(f.root),'path':input_path.name,
            'max_bytes':1000,'sha256':hashlib.sha256(input_path.read_bytes()).hexdigest()}}
        kwargs=dict(owners=f.owners,adapter=f.adapter,policy_path=f.root/'curator.yaml',ownership_map=f.broker.ownership_map,
            manifest=manifest,profile=f.profile,runtime_binding={},enforcement_proof=None,private_directory=f.root/'log-private',
            issuer='fixture-logs',accepted_operations={},artifacts=artifacts,runtime_pool=f.pool)
        (f.root/'log-private').mkdir();broker=Broker(**kwargs);before=(fixture.folder/'task.json').read_bytes()
        def invoke(tool,request):
            context=fixture.context(tool)
            with fixture.authority.invoke(context):return broker.dispatch_verified(context,request)
        self.assertEqual(invoke('log_summary',{})['logs'][0]['handle'],'log1')
        summary=invoke('artifact_read',{'handle':'log1'});self.assertEqual(summary['state'],'summary');self.assertNotIn('content',summary)
        self.assertEqual(invoke('log_query',{'handle':'log1','literal':'unsafe_file'})['matches'][0]['line'],394)
        self.assertEqual(base64.b64decode(invoke('artifact_read',{'handle':'role'})['content']),input_path.read_bytes())
        broker.logs.entries['log1']['readers']=[{**actor,'load_epoch':actor['load_epoch']+1}]
        with self.assertRaises(PolicyError):invoke('log_summary',{'handle':'log1'})
        self.assertEqual(invoke('log_summary',{})['logs'],[]);self.assertEqual(before,(fixture.folder/'task.json').read_bytes())
        missing=copy.deepcopy(manifest);missing['files']=[row for row in missing['files'] if not row['path'].endswith('/curator_logs.py')]
        (f.root/'missing-helper').mkdir()
        with self.assertRaises(PolicyError):Broker(**{**kwargs,'manifest':missing,'private_directory':f.root/'missing-helper'})
        specs={row['name']:row for row in native_tool_specs()}
        shape({},specs['log_summary']['inputSchema'],{});shape({'handle':'log1','literal':'unsafe_file'},specs['log_query']['inputSchema'],{})
        with self.assertRaises(PolicyError):shape({'handle':'log1','path':'secret'},specs['log_query']['inputSchema'],{})


if __name__=='__main__':unittest.main()
