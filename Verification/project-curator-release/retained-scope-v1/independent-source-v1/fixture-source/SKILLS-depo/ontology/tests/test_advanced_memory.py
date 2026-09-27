"""Actual advanced mixed retrieval preserves the existing memory v1 boundary."""
import os
from pathlib import Path
import tempfile
import unittest

from advanced_support import make_advanced, wiki
from support import record, proposal, canonical_bytes, sha256
from test_query_memory import setup_memory, note
from ontology_core import load_project
from ontology_knowledge import knowledge
from ontology_proposals import save


class AdvancedMemoryTests(unittest.TestCase):
    def test_actual_mixed_sources_and_unpublished_proposal_preserve_memory(self):
        with tempfile.TemporaryDirectory() as directory:
            root=make_advanced(Path(directory)/'project');records=wiki(root)
            setup_memory(root);memory_path=note(root,body='The wiki artifact was discussed as historical evidence; this note grants no authority.')
            memory_before={p.relative_to(root).as_posix():sha256(p) for p in [root/memory_path,root/'memory.yaml']}
            saved=save(root,proposal(root,[*records,record('wiki-suggestion')]),rationale='An unpublished wiki suggestion remains distinct from approved semantics.')
            canonical_before=sha256(root/'ONTOLOGY/modules/project/project.jsonld')
            combined=knowledge(root,'wiki',intent='mixed',advanced=True)
            kinds={row['source_type'] for row in combined['results']}
            self.assertTrue({'ontology','historical_memory','ontology_inference','ontology_proposal'}<=kinds,combined)
            for row in combined['results']:
                if row['source_type'] in {'ontology_inference','ontology_proposal'}:self.assertIs(row['authority'],False)
            self.assertNotIn(record('wiki-suggestion')['@id'],load_project(root).by_id)
            ordinary=knowledge(root,'wiki',intent='mixed')
            self.assertFalse(any(row['source_type']=='ontology_proposal' for row in ordinary['results']))
            self.assertEqual(memory_before,{p:sha256(root/p) for p in memory_before})
            self.assertEqual(canonical_before,sha256(root/'ONTOLOGY/modules/project/project.jsonld'))
            output=os.environ.get('SYS4AI_ADVANCED_MEMORY_EVIDENCE')
            if output:
                Path(output).write_bytes(canonical_bytes({'schema_version':1,'status':'passed','backend':'actual selected standards; actual memory v1 lexical helper; synthetic historical fixture record','mixed':combined,'ordinary':ordinary,'proposal_id':saved['head']['proposal_id'],'memory_before':memory_before,'memory_after':{p:sha256(root/p) for p in memory_before},'canonical_ontology_sha256':canonical_before,'unpublished_identity_absent':True}))


if __name__=='__main__':unittest.main()
