"""Collect actual queue/preflight outputs into a bounded metric projection.

Outcome and checkpoint rows are explicitly synthetic; no owner completion,
global total, external observation or benefit baseline is inferred.
"""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from test_retained_application import WORK,NOW,HASH,context,outcome
from curator_events import commit_signal,make_event
from curator_queue import DeliveryQueue
from curator_preflight import preflight
from curator_causality import obligations_for
from curator_snapshots import empty_checkpoint,advance_checkpoint
from curator_metrics import metrics,operational_measures


class RetainedMetricsTests(unittest.TestCase):
    def test_queue_and_idle_preflight_collection(self):
        with tempfile.TemporaryDirectory(dir=WORK) as raw:
            root=Path(raw);ctx=context(root);queue=DeliveryQueue(root,ctx['project_id'],ctx['repository_id'])
            first=commit_signal(ctx,'1'*40,created_at=NOW)
            repeat=commit_signal(ctx,'1'*40,created_at='2026-09-12T12:00:01+00:00')
            due=make_event(ctx,'dependency_due','dependency-1',{'check_id':'declared-package','due_at':NOW},created_at=NOW)
            for event in (first,repeat,due,first):queue.enqueue(event)
            events=[row['event'] for row in queue.status()]
            idle=preflight(ctx,ownership={'schema_version':1,'entries':[]},snapshot={},relevant_paths=[],now=NOW)
            preflight_raw=json.dumps(idle,sort_keys=True).encode();(root/'preflight.json').write_bytes(preflight_raw)
            key=obligations_for(due)[0]['key'];outcomes=[outcome(key,1),outcome(key,2)]
            checkpoint=advance_checkpoint(empty_checkpoint(ctx),'observed',ctx)
            projection={'reference':{'owner':'curate','path':'preflight.json','sha256':hashlib.sha256(preflight_raw).hexdigest()},'value':{'state':idle['state'],'counters':idle['counters']}}
            before={p.relative_to(root):p.read_bytes() for p in root.rglob('*') if p.is_file()}
            base=metrics(events,outcomes,[checkpoint]);measures=operational_measures(events,outcomes,[checkpoint],observations={'runtime':[projection]})
            self.assertEqual((base['delivery_records'],base['logical_events']),(3,2))
            self.assertEqual(measures['duplicate_signals'],1);self.assertEqual(measures['unchanged_repeated_failures'],1)
            self.assertEqual(measures['unresolved_staleness'],1);self.assertEqual(measures['idle_model_calls'],0)
            self.assertEqual(measures['observed_task_writes'],0);self.assertEqual(measures['observed_knowledge_writes'],0)
            self.assertIsNone(measures['benefit_baseline']);self.assertIsNone(measures['reconciliation_delay_ms'])
            self.assertEqual(before,{p.relative_to(root):p.read_bytes() for p in root.rglob('*') if p.is_file()})
            evidence={'kind':'RetainedMetricCollectionScenario','provenance':{'events':'Actual DeliveryQueue.status from four enqueue calls including one exact replay; three immutable event records.','runtime':'Actual idle preflight result; only state and counters projected with exact saved source digest.','outcomes':'Synthetic two failed attempts with identical finding/input for one obligation.','checkpoint':'Synthetic observed-only transition through the actual pure checkpoint function.'},'source_records':{'events':events,'outcomes':outcomes,'checkpoint':checkpoint,'preflight':idle,'preflight_sha256':projection['reference']['sha256']},'projection':projection,'base':base,'measures':measures,'observed_calculator_file_changes':0,'limits':'No connected owner/runtime, global total, timing measurement or benefit baseline claimed.'}
            (WORK/'metric-scenarios.json').write_text(json.dumps(evidence,indent=2)+'\n')


if __name__=='__main__':unittest.main()
