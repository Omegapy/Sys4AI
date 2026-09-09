"""License adoption, preservation and receipt edition recovery in isolated depots."""

from copy import deepcopy
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch

import test_initializer as fixture


class LicensingTests(unittest.TestCase):
    setUp = fixture.InitializerTests.setUp
    run_setup = fixture.InitializerTests.run_setup

    def test_both_routes_adopt_the_complete_template_trio(self):
        template = self.root / self.helper.TEMPLATE
        for mode in ("create", "prepare-existing"):
            with self.subTest(mode=mode):
                target = self.root / "Projects" / mode
                if mode == "prepare-existing":
                    target.mkdir()
                    (target / "project-data.txt").write_text("retain existing data")
                report = self.run_setup(mode=mode, destination=target,
                    project_id=mode, project_name=mode)
                self.assertEqual("governance-starter-v5", report["setup_contract"])
                self.assertEqual({}, report["preserved_licenses"])
                for name in self.helper.LICENSE_FILES:
                    raw = (template / name).read_bytes()
                    self.assertEqual(raw, (target / name).read_bytes())
                    source = next(item for item in report["sources"] if item["destination"] == name)
                    self.assertEqual(f"{self.helper.TEMPLATE}/{name}", source["source"])
                    self.assertEqual("adopted", source["adoption"])
                    self.assertEqual(self.helper.sha(raw), source["source_sha256"])
                    self.assertEqual(source["source_sha256"], report["owned_files"][name])
                if mode == "prepare-existing":
                    self.assertEqual("retain existing data", (target / "project-data.txt").read_text())

    def test_existing_license_systems_are_preserved_as_a_whole_on_setup_and_rerun(self):
        cases = [
            {"LICENSE": "MIT project terms\n"},
            {"LICENSE-DOCS": "Existing document terms\n"},
            {name: "Project-specific " + name for name in self.helper.LICENSE_FILES},
            {"LICENSE.md": "Existing Markdown terms"},
            {"licence.txt": "Existing alternate spelling"},
            {"license": "Existing lowercase terms"},
            {"COPYING": "Existing copying terms"},
            {"COPYRIGHT": "Existing copyright notice"},
            {"UNLICENSE": "Existing unlicense notice"},
            {"LICENSES/vendor.txt": "Vendor terms"},
            {"LICENSE/terms.txt": "Existing license directory"},
            {"LICENSE-CODE/terms.txt": "Existing code license directory"},
        ]
        for index, files in enumerate(cases):
            with self.subTest(files=tuple(files)):
                target = self.root / "Projects" / f"Licensed-{index}"
                for name, content in files.items():
                    path = target / name
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(content)
                before = self.helper.license_inventory(target)
                arguments = {"mode": "prepare-existing", "destination": target,
                             "project_id": f"licensed-{index}", "project_name": f"Licensed {index}"}
                report = self.run_setup(**arguments)
                self.assertEqual(before, report["preserved_licenses"])
                self.assertEqual(before, self.helper.license_inventory(target))
                for entry in report["sources"]:
                    if entry["destination"] in self.helper.LICENSE_FILES:
                        exists = (target / entry["destination"]).is_file()
                        self.assertEqual("preserved-project-owned" if exists else "skipped-existing-license",
                                         entry["adoption"])
                for name, content in files.items():
                    self.assertEqual(content, (target / name).read_text())
                repeated = self.run_setup(**arguments)
                self.assertEqual(report["sources"], repeated["sources"])
                self.assertEqual(before, repeated["current_licenses"])

    def test_preserved_marker_edits_are_observed_without_rewriting_history(self):
        self.target.mkdir()
        marker = self.target / "LICENSE.md"
        marker.write_text("Original project terms")
        first = self.run_setup(mode="prepare-existing")
        marker.write_text("Project-owned revised terms")
        repeated = self.run_setup(mode="prepare-existing")
        self.assertEqual(first["preserved_licenses"], repeated["preserved_licenses"])
        self.assertEqual(first["sources"], repeated["sources"])
        self.assertNotEqual(first["current_licenses"], repeated["current_licenses"])
        self.assertFalse((self.target / "LICENSE").exists())

    def test_aliased_preserved_marker_rejects_rerun_before_receipt_changes(self):
        self.target.mkdir()
        marker = self.target / "LICENSE.md"
        marker.write_text("Project terms")
        self.run_setup(mode="prepare-existing")
        os.link(marker, self.target / "marker-alias.txt")
        before = fixture.manifest(self.root)
        with self.assertRaisesRegex(self.helper.InitializationError, "non-aliased"):
            self.helper.run_initialization(**{**self.arguments, "mode": "prepare-existing"})
        self.assertEqual(before, fixture.manifest(self.root))

    def test_missing_sources_and_forged_preservation_fail_before_mutation(self):
        self.target.mkdir()
        (self.target / "LICENSE.md").write_text("Project terms")
        report = self.run_setup(mode="prepare-existing")
        forged = []
        missing = deepcopy(report)
        missing["sources"] = [entry for entry in missing["sources"] if entry["destination"] != "LICENSE-CODE"]
        forged.append(missing)
        no_markers = deepcopy(report); no_markers["preserved_licenses"] = {}; forged.append(no_markers)
        invalid = deepcopy(report); invalid["preserved_licenses"] = {"README.md": "0" * 64}; forged.append(invalid)
        old = deepcopy(report); old["setup_contract"] = self.helper.PRE_LICENSE_CONTRACT; forged.append(old)
        wrong_skip = deepcopy(report)
        next(entry for entry in wrong_skip["sources"] if entry["destination"] == "LICENSE")["adoption"] = "skipped-existing-package"
        forged.append(wrong_skip)
        for candidate in forged:
            with self.subTest(candidate=candidate.get("setup_contract")):
                (self.target / self.helper.RECORD).write_bytes(self.helper.encoded(candidate))
                before = fixture.manifest(self.root)
                with self.assertRaises(self.helper.InitializationError):
                    self.helper.run_initialization(**{**self.arguments, "mode": "prepare-existing"})
                self.assertEqual(before, fixture.manifest(self.root))

    def test_partial_license_adoption_recovers_and_rejects_new_license_markers(self):
        atomic = self.helper.atomic_write

        def interrupt(target, *args, **kwargs):
            if target == self.target / "LICENSE-CODE":
                raise self.helper.InitializationError("injected license interruption")
            return atomic(target, *args, **kwargs)

        with patch.object(self.helper, "atomic_write", side_effect=interrupt):
            with self.assertRaises(self.helper.InitializationError):
                self.helper.run_initialization(**self.arguments)
        self.assertTrue((self.target / "LICENSE").exists())
        self.assertFalse((self.target / "LICENSE-CODE").exists())
        marker = self.target / "LICENSE.md"
        marker.write_text("A competing license appeared")
        before = fixture.manifest(self.root)
        with self.assertRaisesRegex(self.helper.InitializationError, "licensing changed"):
            self.helper.run_initialization(**self.arguments)
        self.assertEqual(before, fixture.manifest(self.root))
        marker.unlink()
        report = self.run_setup()
        self.assertEqual(self.helper.LICENSE_FILES, set(report["current_licenses"]))

    def test_preserved_marker_drift_blocks_interrupted_recovery(self):
        self.target.mkdir()
        marker = self.target / "licence.txt"
        marker.write_text("Reviewed project terms")
        atomic = self.helper.atomic_write

        def interrupt(target, *args, **kwargs):
            if target == self.target / "AGENTS.md":
                raise self.helper.InitializationError("injected asset interruption")
            return atomic(target, *args, **kwargs)

        with patch.object(self.helper, "atomic_write", side_effect=interrupt):
            with self.assertRaises(self.helper.InitializationError):
                self.helper.run_initialization(**{**self.arguments, "mode": "prepare-existing"})
        marker.write_text("Changed while setup was incomplete")
        before = fixture.manifest(self.root)
        with self.assertRaisesRegex(self.helper.InitializationError, "licensing changed"):
            self.helper.run_initialization(**{**self.arguments, "mode": "prepare-existing"})
        self.assertEqual(before, fixture.manifest(self.root))

    def test_missing_template_license_refuses_both_routes_before_writes(self):
        (self.root / self.helper.TEMPLATE / "LICENSE-DOCS").unlink()
        for mode in ("create", "prepare-existing"):
            if mode == "prepare-existing":
                self.target.mkdir()
            before = fixture.manifest(self.root)
            with self.assertRaises((self.helper.InitializationError, OSError)):
                self.helper.run_initialization(**{**self.arguments, "mode": mode})
            self.assertEqual(before, fixture.manifest(self.root))

    def test_pre_license_v3_partial_and_completed_receipts_keep_their_edition(self):
        template = self.root / self.helper.TEMPLATE
        fixture.remove_memory_edition(template)
        policy_path = template / self.helper.TEMPLATE_POLICY
        current_policy = policy_path.read_bytes()
        policy = json.loads(current_policy)
        policy["starter_files"] = sorted(self.helper.required_starters(self.helper.PRE_LICENSE_CONTRACT))
        policy_path.write_bytes(self.helper.encoded(policy))
        identity = {"schema_version": 1, "project_id": "orchard", "project_name": "Orchard",
                    "purpose": self.arguments["purpose"], "relative_path": "Projects/Orchard"}
        proposed, sources, _ = self.helper.source_snapshot(self.root, fixture.SOURCE_SKILL, identity,
                                                         contract=self.helper.PRE_LICENSE_CONTRACT)
        for entry in sources:
            entry["adoption"] = "adopted"
        record = {"schema_version": 1, "setup_contract": self.helper.PRE_LICENSE_CONTRACT,
                  "status": "partial", "mode": "create", "operation_id": "project-setup-" + "3" * 32,
                  "identity": identity, "project_root": str(self.target), "sources": sources,
                  "owned_files": {name: self.helper.sha(raw) for name, raw in proposed.items()},
                  "preserved_files": {}, "recovery_before": {name: None for name in proposed},
                  "completed_stages": [], "active_stage": "assets", "checks": [],
                  "created_at": "2026-09-08T00:00:00+00:00", "git_setup": "separate"}
        receipt = self.target / self.helper.RECORD
        receipt.parent.mkdir(parents=True)
        receipt.write_bytes(self.helper.encoded(record))
        policy_path.write_bytes(current_policy)
        before = fixture.manifest(self.root)
        with self.assertRaises(self.helper.InitializationError):
            self.helper.run_initialization(**self.arguments)
        self.assertEqual(before, fixture.manifest(self.root))
        policy_path.write_bytes(self.helper.encoded(policy))
        first = self.run_setup()
        policy_path.write_bytes(current_policy)
        repeated = self.run_setup()
        self.assertEqual(self.helper.PRE_LICENSE_CONTRACT, repeated["setup_contract"])
        self.assertEqual(first["sources"], repeated["sources"])
        self.assertNotIn("preserved_licenses", repeated)
        self.assertFalse(any((self.target / name).exists() for name in self.helper.LICENSE_FILES))
        self.assertFalse(any((self.target / name).exists() for name in self.helper.MEMORY_FILES))
        self.assertFalse((self.target / ".agents/skills/memory").exists())
