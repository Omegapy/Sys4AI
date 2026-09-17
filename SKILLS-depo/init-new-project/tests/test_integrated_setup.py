"""v12 setup semantics and explicit exact adoption using isolated depot fixtures."""
from test_curator_setup import fixture_directory, compose, source_root
from pathlib import Path
import unittest, shutil, json, subprocess, sys, hashlib, os
from datetime import datetime,timedelta,timezone


def grant_for(pre):
    prop=pre['proposal'];now=datetime.now(timezone.utc)
    return {'schema_version':1,'grant_id':'ONTIGRANT-disposable-fixture','operation':'integrate-curator','project_id':pre['before']['project_id'],
      'actor_id':'/root','actor_kind':'director','native_receipt':{'tool':'collaboration.list_agents','result':{'agents':[{'agent_name':'/root','agent_status':'running'}]}},
      'observed_at':now.isoformat(),'expires_at':(now+timedelta(minutes=5)).isoformat(),'task':None,'payload_sha256':pre['payload_sha256'],
      'preview_sha256':pre['preview_sha256'],'config_sha256':prop['changes'][-1]['expected_sha256'],'scope':[c['path'] for c in prop['changes']],
      'reviewed_records':[{k:c[k] for k in ('path','expected_sha256','sha256')} for c in prop['changes']],
      'resources':prop['resources'],'sources':prop['sources'],'helpers':pre['before']['helpers']}


class IntegratedSetupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=fixture_directory('integration');cls.root,cls.h,_,_,_=compose(cls.temp.name)
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    def make(self,name):
        target=self.root/'Projects'/name
        return target,dict(destination=target,project_id=name,project_name=name.title(),purpose='Verify integrated '+name)
    def retain(self,name,target,*,command=None,protected=None):
        selected=os.environ.get('SYS4AI_INTEGRATION_EVIDENCE')
        if not selected:return
        out=Path(selected).resolve()/name;out.mkdir(parents=True,exist_ok=True)
        raw=(target/self.h.RECORD).read_bytes();(out/'setup-receipt.json').write_bytes(raw)
        record=json.loads(raw)
        with self.h.INTEGRATION.owner(self.h) as api:
            import check_ontology
            checks=check_ontology.run_checks(target)
            result={'valid':checks['valid'],'structural_valid':checks['structural']['valid'],'competency':checks['competency']}
        self.assertTrue(result['valid'],result)
        (out/'competencies.json').write_text(json.dumps(result,indent=2)+'\n')
        files={}
        for path in [*self.h.INTEGRATION.GENERATED,'ontology.yaml','curator.yaml','curator-session.yaml','memory.yaml','project.json','Roles/INDEX.md']:
            copied=out/path;copied.parent.mkdir(parents=True,exist_ok=True);copied.write_bytes((target/path).read_bytes());files[path]=hashlib.sha256(copied.read_bytes()).hexdigest()
        integrations=[record.get('curator_integration',{}),*[op.get('curator_integration',{}) for op in record.get('module_adoptions',[])]]
        for item in integrations:
            ref=item.get('owner_receipt')
            if ref:
                copied=out/ref['path'];copied.parent.mkdir(parents=True,exist_ok=True);copied.write_bytes((target/ref['path']).read_bytes())
        proof={'route':name,'invocation':command or 'actual reusable run_initialization API in isolated depot','command_exit':0,'verification':'actual disposable setup; synthetic native grants where an owner grant is selected',
            'fixture_root':str(target),'receipt_sha256':hashlib.sha256(raw).hexdigest(),'status':record['status'],'setup_contract':record['setup_contract'],'identity':record['identity'],'files':files,
            'source_inventory':{r['destination']:r['destination_sha256'] for r in record['sources']},'protected':{key:{'before_sha256':hashlib.sha256(value).hexdigest(),'after_sha256':hashlib.sha256((target/key).read_bytes()).hexdigest(),'preserved':value==(target/key).read_bytes()} for key,value in (protected or {}).items()}}
        (out/'route.json').write_text(json.dumps(proof,indent=2)+'\n')
    def test_create_cli_and_missing_function_is_not_ready(self):
        target,args=self.make('create-integration')
        command=[sys.executable,'-B',str(self.root/'SKILLS-depo/init-new-project/scripts/init_new_project.py'),'create']
        for k,v in args.items():command.extend(['--'+k.replace('_','-'),str(v)])
        run=subprocess.run(command,capture_output=True,text=True,timeout=90)
        self.assertEqual(run.returncode,0,run.stdout+run.stderr)
        record=json.loads((target/self.h.RECORD).read_text());self.assertEqual(record['setup_contract'],'governance-starter-v12')
        self.assertTrue(self.h._integration('assess',target)['compatible'])
        self.retain('create-cli',target,command=command)
        graph=target/self.h.INTEGRATION.GENERATED[0];raw=graph.read_bytes();d=json.loads(raw);d['@graph']=[r for r in d['@graph'] if not r['@id'].endswith('function-status')];graph.write_text(json.dumps(d))
        self.assertFalse(self.h._integration('assess',target)['compatible']);graph.write_bytes(raw)
    def test_first_prepare_and_manual_copy(self):
        for name,manual in [('prepare-integration',False),('manual-integration',True)]:
            target,args=self.make(name)
            if manual:shutil.copytree(self.root/self.h.TEMPLATE,target,ignore=shutil.ignore_patterns('.template','__pycache__'))
            else:target.mkdir()
            (target/'authored.txt').write_text('Preserve authored purpose.\n')
            record=self.h.run_initialization(mode='prepare-existing',**args)
            self.assertTrue(record['static_ready']);self.assertEqual((target/'authored.txt').read_text(),'Preserve authored purpose.\n')
            self.assertTrue(self.h._integration('assess',target)['compatible'])
            self.retain(name,target,protected={'authored.txt':b'Preserve authored purpose.\n'})
    def test_v12_refresh_is_explicit_and_unchanged_repeat_deduplicates(self):
        target,args=self.make('refresh-integration')
        base=self.h.run_initialization(mode='create',**args)
        rerun=self.h.run_initialization(mode='prepare-existing',**args)
        self.assertFalse(rerun.get('module_adoptions'))
        adopted=self.h.run_initialization(mode='prepare-existing',adopt_module='curator',refresh_module=['curator'],integration_grant_file=grant_for,**args)
        op=adopted['module_adoptions'][-1];self.assertEqual(op['schema_version'],2);self.assertEqual(op['status'],'completed')
        again=self.h.run_initialization(mode='prepare-existing',adopt_module='curator',refresh_module=['curator'],integration_grant_file=grant_for,**args)
        self.assertEqual(len(again['module_adoptions']),1);self.assertEqual(again['setup_contract'],base['setup_contract'])
        self.retain('v12-explicit-refresh',target)
    def test_session_capture_and_publication_opt_outs_are_preserved(self):
        target,args=self.make('off-integration')
        self.h.run_initialization(mode='create',**args)
        for name,key in [('curator-session.yaml','enabled'),('memory.yaml','integration')]:
            cfg=json.loads((target/name).read_text())
            if key=='integration':cfg[key]['automatic_capture']=False
            else:cfg[key]=False
            (target/name).write_text(json.dumps(cfg,indent=2)+'\n')
        before={name:(target/name).read_bytes() for name in ('curator-session.yaml','memory.yaml')}
        final=self.h.run_initialization(mode='prepare-existing',adopt_module='curator',refresh_module=['curator'],integration_grant_file=grant_for,**args)
        self.assertTrue(final['static_ready']);self.assertEqual(before,{name:(target/name).read_bytes() for name in before})
        self.retain('session-capture-off',target,protected=before)
        cfg=json.loads((target/'ontology.yaml').read_text());cfg['publication']['enabled']=False;(target/'ontology.yaml').write_text(json.dumps(cfg,indent=2)+'\n')
        self.assertTrue(self.h._integration('assess',target)['compatible'])
    def test_generated_setup_asset_registration_and_verification_recovery(self):
        from unittest.mock import patch
        for phase in ('asset','registration','verification'):
            target,args=self.make('fault-'+phase)
            original_write=self.h.atomic_write;original_register=self.h.register_project;original_static=self.h._static
            fired=[]
            def writer(path,raw,*values,**options):
                result=original_write(path,raw,*values,**options)
                if phase=='asset' and path==target/self.h.INTEGRATION.GENERATED[0] and not fired:
                    fired.append(True);raise OSError('Exact fixture asset boundary')
                return result
            def register(*values,**options):
                if phase=='registration' and not fired:fired.append(True);raise OSError('Exact fixture registration boundary')
                return original_register(*values,**options)
            def static(name,*values,**options):
                if phase=='verification' and name=='apply' and not fired:fired.append(True);raise OSError('Exact fixture verification boundary')
                return original_static(name,*values,**options)
            with patch.object(self.h,'atomic_write',side_effect=writer),patch.object(self.h,'register_project',side_effect=register),patch.object(self.h,'_static',side_effect=static):
                with self.assertRaises(self.h.InitializationError):self.h.run_initialization(mode='create',**args)
            held=json.loads((target/self.h.RECORD).read_text());self.assertEqual(held['status'],'partial');op=held['operation_id']
            final=self.h.run_initialization(mode='create',**args);self.assertEqual(final['status'],'completed');self.assertEqual(final['operation_id'],op)
            self.assertTrue(self.h._integration('assess',target)['compatible'])
            self.retain('recovery-'+phase,target)
    def test_owner_receipt_link_failure_reopens_same_owner_result(self):
        from unittest.mock import patch
        target,args=self.make('owner-link')
        self.h.run_initialization(mode='create',**args)
        for path in self.h.INTEGRATION.GENERATED:(target/path).unlink()
        cfg=json.loads((target/'ontology.yaml').read_text())
        for key in ('project_files','binding_files','competency_files'):cfg[key]=[p for p in cfg.get(key,[]) if p not in self.h.INTEGRATION.GENERATED]
        (target/'ontology.yaml').write_text(json.dumps(cfg,indent=2)+'\n');(target/self.h.RECORD).unlink()
        original=self.h.atomic_write;fired=[]
        def writer(path,raw,*values,**options):
            if path==target/self.h.RECORD and b'"owner_receipt"' in raw and not fired:
                fired.append(True);raise OSError('Exact setup link boundary after owner completion')
            return original(path,raw,*values,**options)
        original_read=self.h.file_bytes
        def reader(path):
            try:return original_read(path)
            except self.h.InitializationError as exc:raise self.h.InitializationError(str(path)+': '+str(exc)) from exc
        with patch.object(self.h,'atomic_write',side_effect=writer),patch.object(self.h,'file_bytes',side_effect=reader):
            with self.assertRaises(self.h.InitializationError) as failure:self.h.run_initialization(mode='prepare-existing',integration_grant_file=grant_for,**args)
        receipts=list((target/'control_records/ontology/integrations/receipts').glob('*.json'));self.assertEqual(len(receipts),1,str(failure.exception)+' '+str(failure.exception.report and failure.exception.report.get('recovery'))+' cause '+str(failure.exception.__cause__));before=receipts[0].read_bytes()
        final=self.h.run_initialization(mode='prepare-existing',integration_grant_file=grant_for,**args)
        self.assertEqual(final['status'],'completed');self.assertEqual(receipts[0].read_bytes(),before)
        self.assertEqual(len(list(receipts[0].parent.glob('*.json'))),1)
        self.retain('recovery-owner-link',target)
    def historical(self,name,*,without_ontology=False):
        target,args=self.make(name)
        record=self.h.run_initialization(mode='create',**args)
        roots=['.agents/skills/curate','reference-assets/CURATION-depo',*["Roles/"+r for r in self.h.CURATOR.ROLES]]
        names=set(self.h.CURATOR.STARTERS)|set(self.h.INTEGRATION.GENERATED)
        if without_ontology:
            roots+=list(self.h.ONTOLOGY_TREES)
            names.update({'ontology.yaml','ontology-advanced.yaml','.ontology-toolchain.json'})
        for root in sorted(set(roots),key=len):
            path=target/root
            if path.exists():shutil.rmtree(path)
        for name in names:
            path=target/name
            if path.is_file():path.unlink()
        if not without_ontology:
            cfg=json.loads((target/'ontology.yaml').read_text())
            for key in ('project_files','binding_files','competency_files'):cfg[key]=[p for p in cfg.get(key,[]) if p not in self.h.INTEGRATION.GENERATED]
            (target/'ontology.yaml').write_text(json.dumps(cfg,indent=2)+'\n')
        for key in ('generated_files','curator_integration'):record.pop(key,None)
        record['setup_contract']='governance-starter-v7' if without_ontology else 'governance-starter-v9'
        if without_ontology:
            for key in ('preserved_ontology','current_ontology','ontology','ontology_advanced'):record.pop(key,None)
        # Historical fixture retains an exact supported prior inventory. Restore
        # the reviewed earlier bytes, not merely old edition labels.
        pre=source_root()/'Verification/integrated-curator-ontology/implementation/preimages'
        for path in pre.rglob('*'):
            if not path.is_file():continue
            relative=path.relative_to(pre).as_posix()
            destination=('.agents/skills/'+relative.removeprefix('SKILLS-depo/') if relative.startswith('SKILLS-depo/') else
                'reference-assets/'+relative if relative.startswith(('ONTOLOGY-depo/','CURATION-depo/')) else None)
            if destination and (target/destination).is_file():(target/destination).write_bytes(path.read_bytes())
        (target/'Roles/INDEX.md').write_bytes(self.h.planned_role_index(target,{},{}))
        record['sources']=[r for r in record['sources'] if (target/r['destination']).is_file()]
        for r in record['sources']:
            digest=hashlib.sha256((target/r['destination']).read_bytes()).hexdigest()
            r.update(destination_sha256=digest)
            if r['adoption']=='adopted':r.update(source_sha256=digest,source_version='sha256:'+digest)
        record['owned_files']={r['destination']:r['destination_sha256'] for r in record['sources'] if r['adoption'] in ('adopted','specialized')}
        record['preserved_files']={r['destination']:r['destination_sha256'] for r in record['sources'] if r['adoption']=='preserved-project-owned'}
        (target/self.h.RECORD).write_bytes(self.h.encoded(record))
        return target,args,record
    def test_prior_setup_without_curator_and_without_ontology(self):
        for name,missing in [('prior-no-curator',False),('prior-no-ontology',True)]:
            target,args,base=self.historical(name,without_ontology=missing)
            self.h.validate_record(base,target,base['identity'])
            adopted=self.h.run_initialization(mode='prepare-existing',adopt_module='curator',integration_grant_file=grant_for,**args)
            self.assertEqual(adopted['status'],'completed');self.assertEqual(adopted['setup_contract'],base['setup_contract'])
            self.assertTrue(self.h._integration('assess',target)['compatible'])
            if missing:self.assertEqual(adopted['module_adoptions'][-1]['curator_integration']['mode'],'setup-generated')
            self.retain(name,target)
    def test_authored_ontology_owner_hold_and_exact_continuation(self):
        target,args=self.make('authored-integration')
        self.h.run_initialization(mode='create',**args)
        # Reconstructed earlier authored installation: retain canonical base graphs
        # and identity, remove only fixture integration/setup ownership evidence.
        for path in self.h.INTEGRATION.GENERATED:(target/path).unlink()
        cfg=json.loads((target/'ontology.yaml').read_text())
        for key in ('project_files','binding_files','competency_files'):cfg[key]=[p for p in cfg.get(key,[]) if p not in self.h.INTEGRATION.GENERATED]
        (target/'ontology.yaml').write_text(json.dumps(cfg,indent=2)+'\n')
        (target/self.h.RECORD).unlink()
        shutil.rmtree(target/self.h.INTEGRATION.RECIPE)
        source=(target/'ONTOLOGY/modules/project/project.jsonld').read_bytes()
        with self.assertRaises(self.h.InitializationError) as error:self.h.run_initialization(mode='prepare-existing',**args)
        self.assertIn('grant-required',error.exception.report['recovery']['reason'])
        held=json.loads((target/self.h.RECORD).read_text());self.assertEqual(held['status'],'partial')
        final=self.h.run_initialization(mode='prepare-existing',integration_grant_file=grant_for,**args)
        self.assertEqual(final['status'],'completed');self.assertEqual(final['curator_integration']['status'],'completed')
        self.assertEqual((target/'ONTOLOGY/modules/project/project.jsonld').read_bytes(),source)
        self.retain('authored-first-prepare',target,protected={'ONTOLOGY/modules/project/project.jsonld':source})

if __name__=='__main__':unittest.main()
