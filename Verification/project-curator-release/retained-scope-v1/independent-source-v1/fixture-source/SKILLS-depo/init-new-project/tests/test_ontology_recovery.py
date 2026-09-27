"""Ontology module transactions replay exact requests and reject altered evidence."""
from copy import deepcopy
import json
import shutil
import unittest
from unittest.mock import patch

import test_initializer as fixture
import test_ontology_adoption as adoption_fixture


class OntologyRecoveryTests(unittest.TestCase):
    setUp = fixture.InitializerTests.setUp
    run_setup = fixture.InitializerTests.run_setup
    historical = adoption_fixture.OntologyAdoptionTests.historical
    adopt = adoption_fixture.OntologyAdoptionTests.adopt
    assert_base = adoption_fixture.OntologyAdoptionTests.assert_base

    def test_interrupted_adoption_rejects_changed_selection_sources_and_conflicting_bytes(self):
        first = self.historical()
        write = self.helper.atomic_write
        count = 0
        def interrupt(target, data, expected, **kwargs):
            nonlocal count
            if str(target).startswith(str(self.target / "ONTOLOGY")):
                count += 1
                if count == 2:
                    raise self.helper.InitializationError("injected ontology publication interruption")
            return write(target, data, expected, **kwargs)
        with patch.object(self.helper, "atomic_write", side_effect=interrupt), self.assertRaises(self.helper.InitializationError) as caught:
            self.adopt()
        pending = caught.exception.report["module_adoptions"][-1]
        receipt_before = (self.target / self.helper.RECORD).read_bytes()
        with self.assertRaisesRegex(self.helper.InitializationError, "exact pending"):
            self.adopt(refresh=True)
        self.assertEqual(receipt_before, (self.target / self.helper.RECORD).read_bytes())
        changed = self.target / next(name for name in pending["files"] if name.startswith("ONTOLOGY/") and (self.target / name).is_file())
        saved = changed.read_bytes(); changed.write_bytes(saved + b"\nConcurrent edit.\n")
        before = fixture.manifest(self.root)
        with self.assertRaisesRegex(self.helper.InitializationError, "target changed|conflicting content"):
            self.adopt()
        self.assertEqual(before, fixture.manifest(self.root)); changed.write_bytes(saved)
        source = self.root / self.helper.TEMPLATE / self.helper.ONTOLOGY_ROOT / "profile.md"
        raw = source.read_bytes(); source.write_bytes(raw + b"\nChanged source edition.\n")
        before = fixture.manifest(self.root)
        with self.assertRaisesRegex(self.helper.InitializationError, "sources changed"):
            self.adopt()
        self.assertEqual(before, fixture.manifest(self.root)); source.write_bytes(raw)
        after = self.adopt()
        self.assert_base(first, after)
        operation = after["module_adoptions"][-1]
        self.assertEqual(pending["operation_id"], operation["operation_id"])
        self.assertEqual(pending["manifest_sha256"], operation["manifest_sha256"])
        self.assertEqual("available", operation["capabilities"]["structural_readiness"])

    def test_config_publication_and_final_receipt_interruptions_resume_same_binding(self):
        for stage in ("configuration", "verification", "completed-receipt"):
            with self.subTest(stage=stage):
                if stage != "configuration":
                    self.setUp()
                self.historical()
                write = self.helper.atomic_write
                injected = False
                def interrupt(target, data, expected, **kwargs):
                    nonlocal injected
                    selected = target == self.target / "ontology.yaml" and stage == "configuration"
                    if target == self.target / self.helper.RECORD and stage == "completed-receipt":
                        selected = json.loads(data).get("module_adoptions", [{}])[-1].get("status") == "completed"
                    if selected and not injected:
                        injected = True
                        raise self.helper.InitializationError("injected ontology stage boundary")
                    return write(target, data, expected, **kwargs)
                with patch.object(self.helper, "atomic_write", side_effect=interrupt):
                    if stage == "verification":
                        with patch.object(self.helper, "verify_module_current", side_effect=self.helper.InitializationError("injected verification")), self.assertRaises(self.helper.InitializationError) as caught:
                            self.adopt()
                    else:
                        with self.assertRaises(self.helper.InitializationError) as caught:
                            self.adopt()
                pending = caught.exception.report["module_adoptions"][-1]
                completed = self.adopt()["module_adoptions"][-1]
                self.assertEqual(pending["manifest_sha256"], completed["manifest_sha256"])
                self.assertEqual("current", completed["capabilities"]["director_binding"])

    def test_tampered_manifest_cannot_widen_refresh_or_write_preserved_packages(self):
        self.historical()
        after = self.adopt()
        for field, value in (("module_id", "unexpected"), ("new_memory", True), ("refresh_dependencies", ["memory"]), ("refresh_modules", ["other"]), ("new_ontology", [])):
            with self.subTest(field=field):
                altered = deepcopy(after)
                op = altered["module_adoptions"][-1]; op[field] = value
                op["manifest_sha256"] = self.helper.sha(self.helper.encoded({name: op[name] for name in self.helper.module_frozen(op)}))
                with self.assertRaises(self.helper.InitializationError):
                    self.helper.validate_record(altered, self.target, after["identity"])
        altered = deepcopy(after)
        op = altered["module_adoptions"][-1]
        op["files"]["memory.yaml"] = {"before": "0" * 64, "after": "1" * 64}
        op["manifest_sha256"] = self.helper.sha(self.helper.encoded({name: op[name] for name in self.helper.module_frozen(op)}))
        with self.assertRaisesRegex(self.helper.InitializationError, "outside its selected scope"):
            self.helper.validate_record(altered, self.target, after["identity"])

    def test_interrupted_new_setup_detects_added_ontology_content_and_resumes(self):
        write = self.helper.atomic_write
        count = 0
        def interrupt(target, data, expected, **kwargs):
            nonlocal count
            if str(target).startswith(str(self.target / "ONTOLOGY")):
                count += 1
                if count == 2:
                    raise self.helper.InitializationError("injected new setup interruption")
            return write(target, data, expected, **kwargs)
        with patch.object(self.helper, "atomic_write", side_effect=interrupt), self.assertRaises(self.helper.InitializationError):
            self.run_setup()
        extra = self.target / "ONTOLOGY/unreviewed.json"
        extra.write_text("{}\n")
        before = fixture.manifest(self.root)
        with self.assertRaisesRegex(self.helper.InitializationError, "ontology installation changed"):
            self.run_setup()
        self.assertEqual(before, fixture.manifest(self.root))
        extra.unlink()
        after = self.run_setup()
        self.assertEqual("available", after["ontology"]["structural_readiness"])


if __name__ == "__main__":
    unittest.main()
