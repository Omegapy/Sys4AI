"""Actual pinned semantic model with Task fixture ownership, explicitly selected for acceptance."""
import copy
import json
import os
from pathlib import Path
import shutil
import unittest
from unittest.mock import patch

from support import core_id, write_json, semantic_acceptance_root
import test_query_packets as packet_fixtures
from ontology_core import OntologyError, canonical_bytes, sha256
from ontology_packet import freeze_packet, load_packet, search_packet, validate_assignment
from ontology_semantic import build_index


@unittest.skipUnless(os.environ.get('SYS4AI_SEMANTIC_ACCEPTANCE_ROOT'), 'Select an existing local pinned semantic runtime for actual model acceptance.')
class ActualSemanticPacketTests(unittest.TestCase):
    def test_selected_vectors_freeze_without_live_model_or_corpus_expansion(self):
        fixture = packet_fixtures.PacketTests('test_wrong_owner_scope_empty_size_and_immutability')
        fixture.setUp()
        try:
            origin = semantic_acceptance_root()
            root = fixture.root.resolve()
            for relative in ('.venv-ontology-semantic', '.sys4ai/ontology/semantic'):
                shutil.copytree(origin / relative, root / relative, symlinks=True,
                                ignore=shutil.ignore_patterns('__pycache__', '*.pyc', 'index-v1.json'))
            write_json(root / 'ontology-advanced.yaml', {'schema_version':1, 'profiles':{'semantic':{'enabled':True}}, 'extensions':[], 'limits':{}})
            built = build_index(root)
            packet = fixture.build(advanced=True, concept_ids=[core_id('MemoryRecord'),core_id('Task')], semantic_queries=['recollections'])
            reference = freeze_packet(root, packet, 'packets/semantic-v2.json', actor=fixture.driver.actor)
            registered = fixture.register(reference, artifact='actual_semantic_packet')
            d=fixture.driver;d.context=[*d.context,registered];d.define('complex',False);d.assign('solver1','solver1');d.assign('solver2','solver2')
            bindings=[validate_assignment(root,registered,task_path=fixture.task_path,assignment_id=aid) for aid in ('solver1','solver2')]
            original=(root/reference['path']).read_bytes()
            with patch('ontology_semantic._embed',side_effect=AssertionError('Frozen query invoked a live model')):
                result=search_packet(root,registered,'recollections')
                self.assertEqual(result['results'][0]['@id'],core_id('MemoryRecord'))
                outside=search_packet(root,registered,'photosynthetic chlorophyll')
                self.assertFalse(outside['results'])
                self.assertEqual(load_packet(root,registered),packet)
            self.assertEqual(original,(root/reference['path']).read_bytes())
            forged=copy.deepcopy(packet);forged['advanced']['semantic_queries'][0]['matches'][0]['score']=0.123456
            with self.assertRaises(OntologyError):
                freeze_packet(root,forged,'packets/forged-vectors.json',actor=d.actor)
            changed=root/'.sys4ai/ontology/semantic/index-v1.json';changed.write_bytes(changed.read_bytes()+b'\n')
            with self.assertRaises(OntologyError) as stale:load_packet(root,registered)
            self.assertEqual(stale.exception.code,'stale_packet')
            output=os.environ.get('SYS4AI_SEMANTIC_PACKET_EVIDENCE')
            if output:
                Path(output).write_bytes(canonical_bytes({'schema_version':1,'status':'passed','backend':'actual-selected-pinned-semantic-model','native_ownership':'synthetic Task fixture receipts; actual native ownership is verified separately','build':built,'packet_sha256':sha256(original),'packet':packet,'bindings':bindings,'captured_query':result,'uncaptured_query':outside,'frozen_query_live_model_calls':0,'forged_score_rejected':True,'changed_index_rejected':stale.exception.code}))
        finally:
            fixture.tearDown()


if __name__=='__main__':unittest.main()
