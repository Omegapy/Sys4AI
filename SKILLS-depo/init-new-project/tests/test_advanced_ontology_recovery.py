"""Exact module_adoptions replay with original v8/base and authored bytes retained."""
import json
from unittest.mock import patch
import unittest

import test_initializer as fixture
import test_advanced_ontology_adoption as advanced_fixture


class AdvancedRecoveryTests(unittest.TestCase):
    setUp=fixture.InitializerTests.setUp
    run_setup=fixture.InitializerTests.run_setup
    historical=advanced_fixture.AdvancedAdoptionTests.historical
    adopt=advanced_fixture.AdvancedAdoptionTests.adopt
    assert_base=advanced_fixture.AdvancedAdoptionTests.assert_base
    populate=advanced_fixture.AdvancedAdoptionTests.populate

    def interrupted(self):
        first=self.historical();self.populate()
        source=self.root/self.helper.TEMPLATE/".agents/skills/ontology/README.md"
        source.write_bytes(source.read_bytes()+b"\nExact selected advanced release.\n")
        original=self.helper.atomic_write
        selected=self.target/".agents/skills/ontology/README.md"
        def fail_after_selected(target,data,before,**kwargs):
            result=original(target,data,before,**kwargs)
            if target==selected:
                raise OSError("Injected after one capability replacement")
            return result
        with patch.object(self.helper,"atomic_write",side_effect=fail_after_selected):
            with self.assertRaisesRegex(self.helper.InitializationError,"incomplete"):
                self.adopt()
        partial=json.loads((self.target/self.helper.RECORD).read_text())
        self.assertEqual(partial["status"],"completed")
        self.assertEqual(partial["module_adoptions"][-1]["status"],"partial")
        self.assert_base(first,partial)
        return first,partial,source

    def test_exact_partial_replay_preserves_base_and_authored_state(self):
        first,partial,_=self.interrupted()
        operation=partial["module_adoptions"][-1]
        protected=dict(operation["protected_inventory"])
        result=self.adopt();self.assert_base(first,result)
        current=result["module_adoptions"][-1]
        self.assertEqual(current["operation_id"],operation["operation_id"])
        self.assertEqual(current["manifest_sha256"],operation["manifest_sha256"])
        self.assertEqual(current["status"],"completed")
        self.assertEqual(current["protected_inventory"],protected)
        self.helper.validate_record(result,self.target,result["identity"])

    def test_conflicting_capability_edit_and_changed_template_block_replay(self):
        _,_,source=self.interrupted()
        path=self.target/".agents/skills/ontology/README.md";accepted=path.read_bytes()
        path.write_bytes(accepted+b"\nUnrelated concurrent user edit.\n")
        before=fixture.manifest(self.root)
        with self.assertRaises(self.helper.InitializationError):self.adopt()
        self.assertEqual(before,fixture.manifest(self.root))
        path.write_bytes(accepted)
        extra=source.parent/"unreviewed-new-file.txt";extra.write_text("A later source release must not join a pending operation.\n")
        before=fixture.manifest(self.root)
        with self.assertRaisesRegex(self.helper.InitializationError,"sources changed"):
            self.adopt()
        self.assertEqual(before,fixture.manifest(self.root))

    def test_authored_edit_during_pending_upgrade_is_preserved_and_diagnosed(self):
        _,_,_=self.interrupted()
        path=self.target/"control_records/ontology/proposals/owned.json";path.write_text("A newer user draft.\n")
        before=fixture.manifest(self.root)
        with self.assertRaisesRegex(self.helper.InitializationError,"changed during"):
            self.adopt()
        self.assertEqual(before,fixture.manifest(self.root))


if __name__=="__main__":
    unittest.main()
