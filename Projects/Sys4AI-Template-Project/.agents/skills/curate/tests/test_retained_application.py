"""Ordinary retained functions; synthetic observations do not prove dispatch.

Run named cases with explicit isolated SYS4AI_CURATOR_TEST_SOURCE and
SYS4AI_CURATOR_TEST_WORK roots. Existing ontology lifecycle is the real owner;
all supplied event, checkpoint and product observations are fixture data.
"""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import sys
import subprocess
import tempfile
import unittest

SOURCE = Path(os.environ['SYS4AI_CURATOR_TEST_SOURCE']).resolve(strict=True)
WORK = Path(os.environ['SYS4AI_CURATOR_TEST_WORK']).resolve(strict=True)
assert SOURCE != WORK and not SOURCE.is_relative_to(WORK)
sys.path[:0] = [str(SOURCE/'SKILLS-depo/curate/scripts'), str(SOURCE/'SKILLS-depo/ontology/scripts')]
from curator_policy import digest
from curator_events import make_event, commit_signal, catch_up_signal
from curator_queue import DeliveryQueue
from curator_preflight import coalesce, preflight
from curator_snapshots import empty_checkpoint, advance_checkpoint, current_stages, recompute_obligations
from curator_causality import obligations_for, stopping_decision, reduce_outcomes
from curator_knowledge import decision, semantic_rebind, ontology_transition
from curator_products import plan, next_operation, observe
from curator_learning import disposition
from curator_dependencies import pypi_version_response, assess, candidate
from curator_maintenance import technical
import ontology_lifecycle

NOW = '2026-09-12T12:00:00+00:00'
HASH = 'a'*64


def context(root):
    return dict(project_id='fixture-project', repository_id='fixture-repository',
                coordination_root=str(root), branch='main', snapshot=HASH,
                policy_sha256='b'*64, source_sha256='c'*64)


def reference(owner='curate'):
    return dict(owner=owner, path='fixture-observation.json', sha256=HASH)


def outcome(key, attempt, state='failed'):
    return dict(key=key, attempt=attempt, status=state, input_sha256=HASH,
                output_sha256='d'*64 if state=='satisfied' else None,
                finding_sha256=None if state=='satisfied' else 'e'*64,
                reference=reference() if state=='satisfied' else None,
                elapsed_ms=10, bytes=20)


class RetainedApplicationTests(unittest.TestCase):
    def test_neutral_cli_status_and_metadata_review_are_read_only(self):
        with tempfile.TemporaryDirectory(dir=WORK) as raw:
            root=Path(raw);policy=root/'curator.yaml'
            neutral=(SOURCE/'CURATION-depo/starter/curator.yaml').read_bytes();policy.write_bytes(neutral)
            for command in ('status','review'):
                args=[sys.executable,'-B',str(SOURCE/'SKILLS-depo/curate/scripts/curator.py'),command,'--policy',str(policy)]
                if command=='review':args+=['--scope','README.md']
                completed=subprocess.run(args,cwd=root,capture_output=True,text=True,check=False,timeout=10)
                self.assertEqual(completed.returncode,0,completed.stderr)
                value=json.loads(completed.stdout);self.assertEqual(value['state'],'installed_inactive')
                self.assertEqual(value['model_calls'],0);self.assertEqual(value['canonical_writes'],0)
                if command=='review':self.assertFalse(value['analysis_performed'])
            self.assertEqual(policy.read_bytes(),neutral);self.assertEqual(list(root.iterdir()),[policy])

    def test_durable_correction_restart_and_cursor(self):
        with tempfile.TemporaryDirectory(dir=WORK) as raw:
            root=Path(raw);ctx=context(root);q=DeliveryQueue(root,'fixture-project','fixture-repository')
            self.assertEqual(q.status(),[]);self.assertEqual(list(root.iterdir()),[])
            event=make_event(ctx,'manual_correction','correction-1',{'request':reference('project')},created_at=NOW)
            self.assertTrue(q.enqueue(event)['created']);self.assertFalse(q.enqueue(event)['created'])
            held=q.record_delivery(event['event_id'],None,receipt_id='held-1',status='held',reason='Owner unavailable',created_at=NOW)
            cursor=q.advance_cursor('director','main',None,event['event_id'])
            reopened=DeliveryQueue(root,'fixture-project','fixture-repository')
            self.assertEqual(reopened.cursor('director','main')['record'],cursor)
            self.assertEqual(reopened.status()[0]['status'],'held')
            self.assertEqual(reopened.status()[0]['event'],event)
            before={p.relative_to(root):p.read_bytes() for p in root.rglob('*') if p.is_file()}
            replay=reopened.record_delivery(event['event_id'],None,receipt_id='held-1',status='held',reason='Owner unavailable',created_at=NOW)
            self.assertEqual(replay,held)
            self.assertEqual(before,{p.relative_to(root):p.read_bytes() for p in root.rglob('*') if p.is_file()})
            self.assertFalse((root/'Tasks').exists())

    def test_event_preflight_and_causal_followthrough(self):
        ctx=context(WORK);first=commit_signal(ctx,'1'*40,created_at=NOW)
        self.assertIsNone(catch_up_signal(ctx,'1'*40,'1'*40,created_at=NOW))
        catchup=catch_up_signal(ctx,'1'*40,'2'*40,created_at=NOW)
        self.assertEqual(catchup['payload'],{'previous_commit':'1'*40,'commit':'2'*40})
        self.assertEqual(coalesce([first,catchup,first]),coalesce([catchup,first]))
        idle=preflight(ctx,events=[first],ownership={'schema_version':1,'entries':[]},snapshot={},relevant_paths=['docs/*'],now=NOW)
        self.assertEqual(idle['state'],'idle');self.assertTrue(all(n==0 for n in idle['counters'].values()))
        due=preflight(ctx,ownership={'schema_version':1,'entries':[]},snapshot={},relevant_paths=[],now=NOW,
                      due_checks=[{'id':'release','due_at':NOW,'enabled':True}],runtime_available=False)
        self.assertEqual(due['state'],'unavailable');self.assertIn('dependency_due',due['reasons'])
        accepted=make_event(ctx,'accepted_work','repair-1',{'completion':reference('task'),'effect':'repair'},created_at=NOW)
        self.assertEqual([x['obligation'] for x in obligations_for(accepted)],['documentation','knowledge'])
        key=obligations_for(accepted)[0]['key'];rows=[outcome(key,1),outcome(key,2)]
        self.assertEqual(reduce_outcomes(rows),reduce_outcomes(list(reversed(rows))+rows))
        stopped=stopping_decision(key,rows,{'attempts':5,'elapsed_ms':1000,'bytes':1000})
        self.assertIn('unchanged_failure',stopped['reasons']);self.assertEqual(stopped['state'],'pending')

    def test_checkpoint_stages_preserve_prior_observations(self):
        ctx=context(WORK);checkpoint=empty_checkpoint(ctx);obligation=digest('documentation')
        for stage in ('observed','assessed','integrated','reconciled'):
            checkpoint=advance_checkpoint(checkpoint,stage,ctx,evidence=[reference()],obligations=[obligation],satisfied=[obligation])
        self.assertTrue(all(current_stages(checkpoint).values()))
        changed={**ctx,'snapshot':'f'*64}
        successor=advance_checkpoint(checkpoint,'observed',changed)
        self.assertEqual(successor['reconciled'],checkpoint['reconciled'])
        self.assertEqual(current_stages(successor),{'observed':True,'assessed':False,'integrated':False,'reconciled':False})
        # These supplied ancestry observations test the reducer only, not Git.
        delta=recompute_obligations({'context':ctx,'commit':'1'*40},{'context':changed,'commit':'2'*40},ancestor=False,
                                    changes=[{'status':'R100','old_path':'old.md','path':'new.md'},{'status':'D','path':'gone.md'}])
        self.assertEqual({x['kind'] for x in delta['obligations']},{'rewritten_history','source_changed','rename','deletion'})

    def test_knowledge_routes_and_actual_lifecycle_owner(self):
        source={'path':'source.md','sha256':HASH}
        finding=dict(memory=False,ontology=False,supported=True,conflicting=False,new_knowledge=True,stale_products=[],sources=[source])
        for memory,ontology,label in [(False,False,'neither'),(True,False,'memory'),(False,True,'ontology'),(True,True,'both')]:
            value=decision({**finding,'memory':memory,'ontology':ontology})
            self.assertEqual(value['decision'],label);self.assertEqual(value['canonical_writes'],0)
        derived=decision({**finding,'new_knowledge':False,'stale_products':['memory','ontology']})
        self.assertEqual(derived['routes'],['memory.maintenance','ontology.maintenance'])
        original={'@id':'urn:fixture:meaning','kind':'concept','module':'fixture','@type':'Concept','definition':'Preserved meaning','lifecycle':'approved','history':[]}
        untouched=deepcopy(original)
        successor=ontology_transition(ontology_lifecycle,original,'deprecated',reason='Reviewed successor',replacement='urn:fixture:new')
        self.assertEqual(original,untouched);self.assertEqual(successor['history'][0]['definition'],'Preserved meaning')
        self.assertEqual(successor['replacement'],'urn:fixture:new')
        review=dict(before_sha256=digest(original),after_sha256=digest(successor),meaning_preserved=True,applicability='Historical meaning remains applicable',evidence=[source])
        self.assertEqual(semantic_rebind(original,successor,review)['canonical_writes'],0)

    def test_product_order_and_aborted_outcome_stays_pending(self):
        products=[dict(id=key,route=route,required=True,enabled=True,present=False,current=False,input_sha256=HASH,dependencies=[])
                  for key,route in [('canonical','canonical'),('recheck','recertify'),('memory','memory.reindex'),('wiki','ontology.wiki')]]
        products.append(dict(id='optional',route='ontology.semantic',required=False,enabled=False,present=False,current=False,input_sha256=HASH,dependencies=[]))
        value=plan(products,HASH);ref={'path':'owner-observation.json','sha256':HASH}
        for key in ('canonical','recheck'):
            self.assertEqual(next_operation(value,current_snapshot=HASH,inputs={p['id']:HASH for p in products})['item'],key)
            value=observe(value,key,input_sha256=HASH,receipt=ref,outcome='completed')
        value=observe(value,'memory',input_sha256=HASH,receipt=ref,outcome='aborted')
        self.assertEqual(value['state'],'pending');self.assertEqual(next_operation(value,current_snapshot=HASH,inputs={p['id']:HASH for p in products})['item'],'memory')
        for key in ('memory','wiki'):value=observe(value,key,input_sha256=HASH,receipt=ref,outcome='completed')
        self.assertEqual(value['state'],'current');self.assertEqual(value['products'][-1]['state'],'disabled')

    def test_one_learning_disposition_preserves_opt_out_and_owner(self):
        review=dict(completion_id='completion-1',objective='Fix parser',artifact='code/parser.py',source_sha256=HASH,mode='automatic',durable=True,supported=True,cause_established=True,already_repaired=False,remaining_obligations=[])
        value=disposition(review,capture=False)
        self.assertFalse(value['persist']);self.assertFalse(value['new_review']);self.assertEqual(value['benefit'],'unobserved')
        current={k:review[k] for k in ('objective','artifact','source_sha256')};current.update(state='active',owner='current-task-manager')
        owned=disposition(review,capture=True,active_work=[current]);self.assertEqual(owned['route'],'current_owner')
        self.assertEqual(disposition(review,capture=True,consumed=[value['completion_identity']])['state'],'unchanged')
        self.assertEqual(disposition({**review,'already_repaired':True},capture=True)['route'],'contextual_recall')

    def test_cached_release_and_isolated_candidate_choices(self):
        raw=json.dumps({'info':{'name':'fixture-package','version':'1.0.1'}}).encode()
        evidence=pypi_version_response(raw,url='https://pypi.org/pypi/fixture-package/1.0.1/json',expected_name='fixture-package',expected_version='1.0.1',retrieved_at=NOW,published_at=NOW)
        record=dict(kind='package',name='fixture-package',version='1.0.0',source='pyproject.toml',source_sha256=HASH,owner='project')
        observed=assess(record,evidence,now=NOW,due_at=NOW,fresh_until=NOW)
        self.assertEqual(observed['disposition'],'upgrade_candidate');self.assertEqual(observed['network_calls'],0);self.assertFalse(observed['installation'])
        change=dict(declaration=True,package_source=False,runtime_install=False,service_start=False,major=False,backend=False,schema=False,storage=False,environment_sha256=HASH)
        self.assertEqual(candidate(change,['declaration'],checks=[{'passed':True}],current_environment_sha256=HASH)['state'],'verified_candidate')
        self.assertEqual(candidate(change,['declaration'],checks=[{'passed':False}],current_environment_sha256=HASH)['state'],'held')
        self.assertEqual(candidate({**change,'major':True},['declaration'],checks=[{'passed':True}],current_environment_sha256=HASH)['state'],'protected_review')
        finding={'class':'defect','paths':['code/parser.py'],'tools':['python-syntax'],'cause_established':True,'evidence':[{'path':'finding.md','sha256':HASH}],'definition_of_done':['Parser accepts ordinary input']}
        accepted={'target_sha256':HASH,'finding_sha256':digest(finding),'cost':{'work_seconds':5}}
        result=technical(finding,accepted,current_target=HASH,selected_classes=['defect'],selected_paths=['code/*'],selected_tools=['python-syntax'],remaining={'work_seconds':10})
        self.assertEqual(result['route'],'isolated_technical_repair');self.assertEqual(result['canonical_writes'],0)


if __name__=='__main__':unittest.main()
