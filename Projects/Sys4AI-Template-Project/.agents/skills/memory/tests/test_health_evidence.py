"""Scoped readiness, durable evidence and maintenance regressions in disposable roots."""
import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from test_core import (build_project, make_record, make_payload, make_grant, write,
                       snapshot, SCRIPTS, json_bytes, sha256)
from memory_core import health, health_exit, load_config, load_record, render_record
from memory_evidence import assess_evidence, validate_publication_evidence
from memory_paths import MemoryError
from memory_publish import publish
from memory_capture import capture
from memory_search import collect_documents, search
from basic_memory_projection import render_projection, canonical_json, verify_projection
import basic_memory_adapter as adapter
import memory_maintenance as maintenance


class HealthEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="memory health ")
        self.addCleanup(self.temp.cleanup)
        self.root = build_project(Path(self.temp.name))

    def config(self, enabled=True):
        config = load_config(self.root)
        config["backend"].update(enabled=enabled, semantic_enabled=enabled)
        write(self.root, "memory.yaml", json_bytes(config))
        return config

    def project(self):
        config = load_config(self.root)
        docs, _ = collect_documents(self.root, config)
        files, manifest = render_projection(self.root, config, docs)
        for name, raw in files.items():
            write(self.root, config["state"]["projection"] + "/" + name, raw)
        write(self.root, config["state"]["projection"] + "/manifest.json", canonical_json(manifest))
        return config, manifest

    def observed(self, retained=True):
        script = write(self.root, "Verification/check.py", "from pathlib import Path\nassert 'bounded reusable records' in Path('docs/design.md').read_text()\n")
        command = [sys.executable, "-B", str(script)]
        observed = subprocess.run(command, cwd=self.root, capture_output=True, text=True)
        self.assertEqual(observed.returncode, 0, observed.stderr)
        artifacts = []
        for path in ("docs/design.md", "Verification/check.py"):
            raw = (self.root / path).read_bytes()
            ref = {"path": path, "sha256": sha256(raw)}
            if retained:
                ref["retained_path"] = "Verification/evidence/" + Path(path).name
                write(self.root, ref["retained_path"], raw)
            artifacts.append(ref)
        receipt = {"schema_version": 1, "claim_level": "verified_outcome", "outcome": "passed",
                   "command": " ".join(command), "observed_at": datetime.now(timezone.utc).isoformat(),
                   "artifacts": artifacts, "applicability": "current"}
        write(self.root, "Verification/observed.json", json_bytes(receipt))
        record = make_record(self.root, level="verified_outcome")
        record["metadata"]["sources"] = [{"path": "Verification/observed.json", "sha256": sha256(json_bytes(receipt)),
                                            "locator": "json:/outcome", "kind": "verification"}]
        return record, receipt

    def cli(self, *selection):
        run = subprocess.run([sys.executable, "-B", str(SCRIPTS / "memory.py"), "--project-root", str(self.root),
                              "health", *selection], capture_output=True, text=True)
        return run.returncode, json.loads(run.stdout)

    def test_aggregate_selection_and_exit_json_text_no_writes(self):
        before = snapshot(self.root)
        code, result = self.cli()
        self.assertEqual((code, result["aggregate"], result["ready"]), (0, "ready", True))
        self.assertEqual(result["assessment"]["level"], "static")
        self.assertEqual(result["assessment"]["input_versions"], result["assessment"]["inputs"])
        self.assertEqual(result["assessment"]["components"], result["components"])
        self.assertEqual(result["failed_required"], [])
        self.assertEqual(result["assessment"]["project"]["root"], str(self.root))
        self.assertEqual(result["components"]["backend"]["status"], "not_selected")
        code, result = self.cli("--require", "projection")
        self.assertEqual((code, result["aggregate"]), (1, "degraded"))
        self.assertEqual(result["components"]["projection"]["error"]["code"], "file_absent")
        self.assertEqual(result["failed_required"], ["projection"])
        code, result = self.cli("--require", "unknown")
        self.assertEqual((code, result["aggregate"]), (2, "invalid"))
        run = subprocess.run([sys.executable, "-B", str(SCRIPTS / "memory.py"), "--project-root", str(self.root),
                              "health", "--require", "projection", "--format", "text"], capture_output=True, text=True)
        self.assertEqual(run.returncode, 1)
        self.assertIn("Memory health: degraded", run.stdout)
        self.assertIn("file_absent", run.stdout)
        self.assertEqual(snapshot(self.root), before)
        (self.root / "memory.yaml").unlink()
        before = snapshot(self.root)
        self.assertEqual(self.cli()[0], 1)
        self.assertEqual(self.cli()[1]["aggregate"], "absent")
        self.assertEqual(snapshot(self.root), before)
        write(self.root, "memory.yaml", "{invalid")
        self.assertEqual(self.cli()[0], 2)

    def test_retained_observation_survives_later_code_but_is_not_current(self):
        record, receipt = self.observed()
        payload = make_payload(self.root, record)
        grant = make_grant(self.root, payload)
        result = capture(self.root, payload, grant, "/root", trigger="work-completed")
        self.assertEqual(result["publication"]["state"], "complete")
        path = payload["changes"][0]["path"]
        original_receipt = (self.root / "Verification/observed.json").read_bytes()
        write(self.root, "docs/design.md", "Changed implementation.\n")
        before = snapshot(self.root)
        loaded = load_record(self.root, path)
        evidence = loaded["evidence"]
        self.assertEqual(evidence["historical_support"], "supported")
        self.assertEqual(evidence["current_applicability"], "changed")
        self.assertTrue(evidence["durable"])
        self.assertFalse(evidence["verified_current"])
        diagnostic = next(d for d in loaded["diagnostics"] if d["code"] == "evidence_changed")
        self.assertEqual(diagnostic["path"], "docs/design.md")
        self.assertEqual(diagnostic["expected_sha256"], receipt["artifacts"][0]["sha256"])
        self.assertEqual(diagnostic["current_sha256"], sha256(b"Changed implementation.\n"))
        self.assertEqual(health(self.root)["aggregate"], "degraded")
        found = search(self.root, "bounded", mode="lexical")["results"]
        self.assertTrue(any(r.get("record_id") for r in found))
        self.assertTrue(all(not r.get("verified_current") for r in found))
        self.assertEqual((self.root / "Verification/observed.json").read_bytes(), original_receipt)
        self.assertEqual(snapshot(self.root), before)

    def test_legacy_receipt_remains_readable_without_claiming_durable_support(self):
        record, receipt = self.observed(retained=False)
        self.assertTrue(assess_evidence(self.root, record)["verified_current"])
        self.assertFalse(assess_evidence(self.root, record)["durable"])
        with self.assertRaises(MemoryError) as error:
            validate_publication_evidence(self.root, record)
        self.assertEqual(error.exception.code, "durable_evidence_required")
        write(self.root, "docs/design.md", "Changed\n")
        evidence = assess_evidence(self.root, record)
        self.assertEqual(evidence["historical_support"], "unsupported")
        self.assertIn("historical_evidence_unsupported", [d["code"] for d in evidence["diagnostics"]])

    def test_missing_tampered_and_unsafe_retained_proof_fail_closed(self):
        for variant in ("absent", "tampered", "out_of_scope", "sensitive"):
            record, receipt = self.observed()
            path = receipt["artifacts"][0]["retained_path"]
            if variant == "absent":
                (self.root / path).unlink()
            elif variant == "tampered":
                write(self.root, path, "Different bytes")
            elif variant == "out_of_scope":
                receipt["artifacts"][0]["retained_path"] = "docs/design.md"
            else:
                raw = "api_key=" + "synthetic" * 8
                write(self.root, "docs/design.md", raw)
                write(self.root, path, raw)
                receipt["artifacts"][0]["sha256"] = sha256(raw)
            write(self.root, "Verification/observed.json", json_bytes(receipt))
            record["metadata"]["sources"][0]["sha256"] = sha256(json_bytes(receipt))
            before = snapshot(self.root)
            with self.assertRaises(MemoryError):
                validate_publication_evidence(self.root, record)
            self.assertFalse(assess_evidence(self.root, record)["verified_current"])
            self.assertEqual(snapshot(self.root), before)
            write(self.root, "docs/design.md", "# Approved design\nThe project uses bounded reusable records.\n")

    def test_historical_successor_preserves_old_bytes_claim_and_diagnostics(self):
        old, receipt = self.observed()
        first = make_payload(self.root, old)
        publish(self.root, first, make_grant(self.root, first), "/root")
        old_path = first["changes"][0]["path"]
        old_digest = sha256((self.root / old_path).read_bytes())
        old_body = old["body"]
        write(self.root, "docs/design.md", "Changed source\n")
        operation = "MEMOP-historical-successor-1"
        reason = "Current implementation changed; retain the observed record as historical provenance."
        new = make_record(self.root, record_id="MEM-20260908-B1B2C3D4", operation_id=operation, level="historical_context")
        new["metadata"]["sources"] = copy.deepcopy(old["metadata"]["sources"])
        new["metadata"]["claim"]["summary"] = "The retained receipt reports the earlier fixture result; current implementation is not verified by this note."
        new["metadata"]["lifecycle"].update(supersedes=[old["metadata"]["id"]], reason=reason)
        prior = copy.deepcopy(old)
        prior["metadata"].update(state="superseded", modified=new["metadata"]["modified"])
        prior["metadata"]["publication"] = copy.deepcopy(new["metadata"]["publication"])
        prior["metadata"]["lifecycle"].update(superseded_by=new["metadata"]["id"], reason=reason)
        from memory_publish import transaction_payload
        changes = []
        for record, expected in ((prior, old_digest), (new, None)):
            raw = render_record(record)
            changes.append({"path": "MEMORY/" + record["metadata"]["id"] + ".md", "expected_sha256": expected,
                            "content": raw, "reviewed_record_sha256": sha256(raw)})
        payload = transaction_payload(operation, "supersede", changes, reason)
        publish(self.root, payload, make_grant(self.root, payload), "/root")
        loaded = load_record(self.root, old_path)
        self.assertEqual(loaded["body"], old_body)
        self.assertEqual(loaded["metadata"]["sources"], old["metadata"]["sources"])
        self.assertTrue(loaded["diagnostics"])
        self.assertEqual(health(self.root)["aggregate"], "ready")
        current = load_record(self.root, changes[1]["path"])
        self.assertEqual(current["evidence"]["current_applicability"], "not_claimed")
        self.assertFalse(current["evidence"]["verified_current"])
        # Unknown edits still block replay of the historical operation.
        write(self.root, old_path, (self.root / old_path).read_bytes() + b"Human edit\n")
        with self.assertRaises(MemoryError):
            publish(self.root, payload, make_grant(self.root, payload), "/root")

    def test_projection_detects_added_removed_changed_sources_and_irrelevant_inputs(self):
        config, manifest = self.project()
        before = snapshot(self.root)
        self.assertEqual(health(self.root)["aggregate"], "ready")
        self.assertEqual(snapshot(self.root), before)
        write(self.root, "unrelated.txt", "Not a declared input")
        self.assertEqual(verify_projection(self.root, config), manifest)
        write(self.root, "docs/new.md", "New permitted source\n")
        before = snapshot(self.root)
        result = health(self.root)
        self.assertEqual(result["aggregate"], "degraded")
        self.assertEqual(result["components"]["projection"]["error"]["code"], "projection_corpus_changed")
        self.assertEqual(snapshot(self.root), before)
        (self.root / "docs/new.md").unlink()
        write(self.root, "README.md", "Changed readme\n")
        self.assertEqual(health(self.root)["components"]["projection"]["error"]["code"], "projection_stale")
        (self.root / "README.md").unlink()
        self.assertEqual(health(self.root)["aggregate"], "degraded")
        self.assertEqual(health(self.root, scope="canonical")["aggregate"], "ready")

    def test_previously_built_missing_product_and_producer_changes_are_nonready(self):
        config, manifest = self.project()
        manifest.pop("implementation_inputs")
        write(self.root, config["state"]["projection"] + "/manifest.json", canonical_json(manifest))
        self.assertEqual(health(self.root)["components"]["projection"]["error"]["code"], "projection_implementation_changed")
        write(self.root, config["state"]["maintenance"] + "/backend-history.json", json_bytes({"schema_version": 1, "operation": "reindex", "status": "complete"}))
        before = snapshot(self.root)
        result = health(self.root)
        self.assertEqual(result["components"]["index"]["error"]["code"], "file_absent")
        self.assertEqual(result["aggregate"], "degraded")
        self.assertEqual(snapshot(self.root), before)

    def test_backend_disabled_static_and_operational_failure_diagnostics(self):
        config = load_config(self.root)
        config["backend"]["enabled"] = True
        write(self.root, "memory.yaml", json_bytes(config))
        result = health(self.root)
        self.assertEqual(result["aggregate"], "ready")
        self.assertEqual(result["backend"]["selection"], "enabled_lexical_only")
        self.assertEqual(result["components"]["backend"]["selection"], "enabled_lexical_only")
        self.assertEqual(result["failed_required"], [])
        before = snapshot(self.root)
        with patch.object(adapter, "run_worker", side_effect=AssertionError("static health must not launch runtime")):
            self.assertEqual(health(self.root, level="operational")["aggregate"], "ready")
        self.assertEqual(snapshot(self.root), before)
        config = self.config()
        before = snapshot(self.root)
        self.assertEqual(health(self.root)["aggregate"], "degraded")
        self.assertEqual(health(self.root)["backend"]["error"]["code"], "file_absent")
        self.assertEqual(snapshot(self.root), before)
        fake = ({"profile_id": "fixture"}, {"profile_sha256": "a" * 64}, {"entries": []})
        for error, code in ((MemoryError("backend_adapter_changed", "Stale certification"), "backend_adapter_changed"),
                            (MemoryError("backend_cancelled", "Controlled cancellation"), "backend_cancelled"),
                            (subprocess.TimeoutExpired("fixture", 30), "backend_timeout")):
            with patch.object(adapter, "_read_certificate", return_value=fake), patch.object(adapter, "_runtime_python", return_value=sys.executable), patch.object(adapter, "run_worker", side_effect=error):
                observed = adapter.health(self.root, config, level="operational")
            self.assertFalse(observed["available"])
            self.assertEqual(observed["error"]["code"], code)
        self.assertEqual(snapshot(self.root), before)

    def test_publication_closes_canonical_boundary_and_reports_out_of_scope_reindex(self):
        config, _ = self.project()
        record = make_record(self.root)
        payload = make_payload(self.root, record)
        result = publish(self.root, payload, make_grant(self.root, payload), "/root")
        self.assertEqual(result["state"], "complete")
        self.assertEqual(result["current_readiness"]["status"], "pending")
        pending = result["current_readiness"]["pending"]
        self.assertEqual(pending[0]["component"], "projection")
        self.assertIn("reindex", pending[0]["next_operation"])
        before = snapshot(self.root)
        again = publish(self.root, payload, make_grant(self.root, payload), "/root")
        self.assertEqual(again["records"], result["records"])
        self.assertEqual(again["current_readiness"]["status"], "pending")
        self.assertEqual(health_exit(health(self.root)), 1)

    def test_legacy_companion_is_exact_historical_proof_not_current_renewal(self):
        record, receipt = self.observed(retained=False)
        raw_receipt = (self.root / "Verification/observed.json").read_bytes()
        companion = {"schema_version": 1, "receipt": {"path": "Verification/observed.json", "sha256": sha256(raw_receipt)},
                     "applicability": "historical", "artifacts": []}
        for ref in receipt["artifacts"]:
            retained = "Verification/retained/" + Path(ref["path"]).name
            write(self.root, retained, (self.root / ref["path"]).read_bytes())
            companion["artifacts"].append(dict(ref, retained_path=retained))
        companion_path = "Verification/project-memory/evidence/verification-" + sha256(raw_receipt) + ".json"
        write(self.root, companion_path, json_bytes(companion))
        path = "MEMORY/" + record["metadata"]["id"] + ".md"
        write(self.root, path, render_record(record))
        write(self.root, "docs/design.md", "Later implementation\n")
        before = snapshot(self.root)
        evidence = load_record(self.root, path)["evidence"]
        self.assertEqual(evidence["historical_support"], "supported")
        self.assertTrue(evidence["durable"])
        self.assertFalse(evidence["verified_current"])
        self.assertEqual(evidence["current_applicability"], "changed")
        self.assertTrue(all(d["severity"] == "info" for d in evidence["diagnostics"]))
        historical = search(self.root, "bounded", mode="lexical", historical=True)["results"]
        self.assertTrue(any(r.get("record_id") == record["metadata"]["id"] for r in historical))
        self.assertTrue(all(not r.get("verified_current") for r in historical))
        with self.assertRaises(MemoryError):
            validate_publication_evidence(self.root, record)
        self.assertEqual(snapshot(self.root), before)
        for mutation in ("missing", "mismatched_receipt", "mismatched_artifact", "tampered_archive"):
            candidate = copy.deepcopy(companion)
            if mutation == "missing":
                (self.root / companion_path).unlink()
            else:
                if mutation == "mismatched_receipt":
                    candidate["receipt"]["sha256"] = "a" * 64
                if mutation == "mismatched_artifact":
                    candidate["artifacts"][0]["sha256"] = "b" * 64
                if mutation == "tampered_archive":
                    write(self.root, candidate["artifacts"][0]["retained_path"], "Altered retained bytes")
                write(self.root, companion_path, json_bytes(candidate))
            observed = assess_evidence(self.root, record)
            self.assertEqual(observed["historical_support"], "unsupported", mutation)
            self.assertTrue(any(d["severity"] in {"warning", "error"} for d in observed["diagnostics"]), mutation)
            self.assertFalse(observed["verified_current"])
            if mutation == "missing":
                write(self.root, companion_path, json_bytes(companion))
        self.assertEqual((self.root / "Verification/observed.json").read_bytes(), raw_receipt)

    def test_actual_certificate_version_and_index_byte_faults(self):
        from test_core import contract_source
        config = self.config()
        config, manifest = self.project()
        profile_raw = (contract_source() / "profiles/basic-memory-v0.23.0.json").read_bytes()
        write(self.root, config["contract_root"] + "/profiles/basic-memory-v0.23.0.json", profile_raw)
        database = b"disposable byte-integrity fixture; not vendor runtime evidence"
        write(self.root, config["state"]["index"] + "/basic-memory.db", database)
        write(self.root, config["state"]["index"] + "/manifest.json", canonical_json({"classification": "rebuildable-index", "files": {"basic-memory.db": sha256(database)}}))
        certificate = {"schema_version": 1, "project_id": config["project"]["id"], "project_root": str(self.root),
                       "profile_sha256": sha256(profile_raw), "adapter_sha256": "a" * 64,
                       "projection_sha256": sha256(canonical_json(manifest)), "database_sha256": sha256(database)}
        certificate_path = config["state"]["backend_config"] + "/certification.json"
        write(self.root, certificate_path, canonical_json(certificate))
        before = snapshot(self.root)
        with patch.object(adapter, "run_worker", side_effect=AssertionError("no static runtime")):
            result = health(self.root)
        self.assertEqual(result["components"]["index"]["status"], "ready")
        self.assertEqual(result["backend"]["error"]["code"], "backend_adapter_changed")
        self.assertEqual(result["backend"]["error"]["details"]["expected_sha256"], "a" * 64)
        self.assertEqual(result["aggregate"], "degraded")
        self.assertEqual(snapshot(self.root), before)
        certificate["profile_sha256"] = "b" * 64
        write(self.root, certificate_path, canonical_json(certificate))
        self.assertEqual(health(self.root)["backend"]["error"]["code"], "backend_profile_changed")
        write(self.root, config["state"]["index"] + "/basic-memory.db", database + b"changed")
        before = snapshot(self.root)
        self.assertEqual(health(self.root)["components"]["index"]["error"]["code"], "backend_index_manifest")
        self.assertEqual(snapshot(self.root), before)

    def test_committed_reindex_failed_operational_probe_retains_boundary(self):
        # Worker transport is injected; this is transaction failure evidence only.
        from test_core import contract_source
        config = self.config()
        profile_raw = (contract_source() / "profiles/basic-memory-v0.23.0.json").read_bytes()
        write(self.root, config["contract_root"] + "/profiles/basic-memory-v0.23.0.json", profile_raw)
        payload = maintenance.reindex_payload(self.root)
        canonical_before = {p: v for p, v in snapshot(self.root).items() if not p.startswith(".sys4ai/")}
        def worker(root, cfg, request, *, build=False, **unused):
            if build:
                write(root, request["database"], b"fixture database; no runtime success claim")
                return {"fixture_transport": True, "indexed_documents": len(request["projection_manifest"]["entries"])}
            raise subprocess.TimeoutExpired("fixed health fixture", 30)
        with patch("memory_publish.authorize"), patch.object(adapter, "_model_directory", return_value=self.root), patch.object(adapter, "_runtime_python", return_value=sys.executable), patch.object(adapter, "run_worker", side_effect=worker):
            result = maintenance.reindex(self.root, grant_file="fixture-grant.json", actor="/root", expected_payload_sha256=sha256(canonical_json(payload)))
        self.assertEqual(result["status"], "maintenance_pending")
        self.assertTrue(result["committed"])
        self.assertFalse(result["ready"])
        self.assertEqual(result["readiness"]["backend"]["error"]["code"], "backend_timeout")
        journal = json.loads((self.root / result["journal"]).read_text())
        self.assertEqual(journal["status"], "complete")
        self.assertFalse(journal["readiness"]["ready"])
        self.assertEqual(maintenance.pending_reindexes(self.root, config), [])
        self.assertEqual(canonical_before, {p: v for p, v in snapshot(self.root).items() if not p.startswith(".sys4ai/")})
        with patch("memory_publish.authorize"), self.assertRaises(MemoryError) as error:
            maintenance.reindex(self.root, grant_file="fixture-grant.json", actor="/root", expected_payload_sha256=sha256(canonical_json(payload)))
        self.assertEqual(error.exception.code, "maintenance_request_changed")

    def test_direct_source_archive_is_order_independent_and_validate_reports_current_count(self):
        record, receipt = self.observed()
        direct = {"path": "docs/design.md", "sha256": receipt["artifacts"][0]["sha256"],
                  "kind": "source", "locator": "section:bounded reusable records"}
        record["metadata"]["sources"].append(direct)
        path = "MEMORY/" + record["metadata"]["id"] + ".md"
        write(self.root, path, render_record(record))
        command = [sys.executable, "-B", str(SCRIPTS / "memory.py"), "--project-root", str(self.root), "validate"]
        before = snapshot(self.root)
        current = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(current.returncode, 0, current.stdout + current.stderr)
        self.assertEqual(json.loads(current.stdout)["verified_current_records"], 1)
        self.assertEqual(snapshot(self.root), before)
        write(self.root, "docs/design.md", "Later implementation without the old locator.\n")
        before = snapshot(self.root)
        expected = assess_evidence(self.root, record)
        reversed_record = copy.deepcopy(record)
        reversed_record["metadata"]["sources"].reverse()
        self.assertEqual(assess_evidence(self.root, reversed_record), expected)
        self.assertEqual(expected["historical_support"], "supported")
        self.assertEqual(expected["current_applicability"], "changed")
        self.assertFalse(expected["verified_current"])
        self.assertTrue(all(d["severity"] == "info" for d in expected["diagnostics"]))
        direct_diagnostic = next(d for d in expected["diagnostics"] if d["code"] == "current_source_changed")
        self.assertEqual(direct_diagnostic["retained_path"], receipt["artifacts"][0]["retained_path"])
        self.assertEqual(direct_diagnostic["expected_sha256"], direct["sha256"])
        self.assertEqual(direct_diagnostic["current_sha256"], sha256((self.root / direct["path"]).read_bytes()))
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        validated = json.loads(result.stdout)
        self.assertTrue(validated["valid"])
        self.assertEqual(validated["verified_current_records"], 0)
        self.assertEqual(validated["diagnostics"], expected["diagnostics"])
        self.assertEqual(snapshot(self.root), before)
        (self.root / "docs/design.md").unlink()
        absent = assess_evidence(self.root, reversed_record)
        self.assertEqual(absent["historical_support"], "supported")
        self.assertFalse(absent["verified_current"])
        self.assertTrue(all(d["severity"] == "info" for d in absent["diagnostics"]))

    def test_direct_source_invalid_proof_or_locator_fails_cli_without_writes(self):
        original = (self.root / "docs/design.md").read_bytes()
        for variant in ("archive_missing", "archive_tampered", "path_mismatch", "digest_mismatch", "locator_missing"):
            with self.subTest(variant=variant):
                write(self.root, "docs/design.md", original)
                record, receipt = self.observed()
                direct = {"path": "docs/design.md", "sha256": receipt["artifacts"][0]["sha256"],
                          "kind": "source", "locator": "section:bounded reusable records"}
                record["metadata"]["sources"].insert(0, direct)
                write(self.root, "docs/design.md", "Later code\n")
                archive = self.root / receipt["artifacts"][0]["retained_path"]
                if variant == "archive_missing":
                    archive.unlink()
                elif variant == "archive_tampered":
                    archive.write_bytes(b"Changed retained proof\n")
                elif variant == "path_mismatch":
                    direct["path"] = "docs/different.md"
                    write(self.root, direct["path"], "Different source\n")
                elif variant == "digest_mismatch":
                    direct["sha256"] = "a" * 64
                else:
                    direct["locator"] = "section:no such historical locator"
                path = "MEMORY/" + record["metadata"]["id"] + ".md"
                write(self.root, path, render_record(record))
                before = snapshot(self.root)
                evidence = assess_evidence(self.root, record)
                self.assertEqual(evidence["historical_support"], "unsupported")
                self.assertFalse(evidence["verified_current"])
                self.assertTrue(any(d["severity"] != "info" for d in evidence["diagnostics"]))
                run = subprocess.run([sys.executable, "-B", str(SCRIPTS / "memory.py"), "--project-root", str(self.root),
                                      "validate", path], capture_output=True, text=True)
                self.assertEqual(run.returncode, 1, run.stdout + run.stderr)
                self.assertFalse(json.loads(run.stdout)["valid"])
                self.assertEqual(json.loads(run.stdout)["verified_current_records"], 0)
                self.assertEqual(snapshot(self.root), before)

    def test_accepted_design_cannot_borrow_execution_receipt_for_changed_direct_source(self):
        record, receipt = self.observed()
        record["metadata"]["claim"]["level"] = "accepted_design"
        direct = {"path": "docs/design.md", "sha256": receipt["artifacts"][0]["sha256"],
                  "kind": "source", "locator": "line:2"}
        current_design = write(self.root, "docs/current-design.md", "A distinct current accepted design.\n")
        record["metadata"]["sources"].extend([direct, {"path": "docs/current-design.md", "sha256": sha256(current_design.read_bytes()),
                                                     "kind": "design", "locator": "document"}])
        write(self.root, "docs/design.md", "Changed old source\n")
        before = snapshot(self.root)
        evidence = assess_evidence(self.root, record)
        self.assertEqual(evidence["historical_support"], "unsupported")
        self.assertFalse(evidence["verified_current"])
        self.assertTrue(any(d["severity"] != "info" for d in evidence["diagnostics"]))
        self.assertFalse(any(d["code"] == "current_source_changed" for d in evidence["diagnostics"]))
        self.assertEqual(snapshot(self.root), before)

    def test_direct_source_retained_bytes_are_reread_after_verification(self):
        import memory_evidence
        record, receipt = self.observed()
        record["metadata"]["sources"].insert(0, {"path": "docs/design.md", "sha256": receipt["artifacts"][0]["sha256"],
                                               "kind": "source", "locator": "line:2"})
        write(self.root, "docs/design.md", "Later source\n")
        original = memory_evidence._verification
        archive = self.root / receipt["artifacts"][0]["retained_path"]
        def changed_after_inspection(*args, **kwargs):
            observed = original(*args, **kwargs)
            self.assertEqual(observed["historical_support"], "supported")
            # Controlled concurrent external edit between the two evidence reads.
            archive.write_bytes(b"Changed after the first read\n")
            return observed
        with patch.object(memory_evidence, "_verification", side_effect=changed_after_inspection):
            evidence = assess_evidence(self.root, record)
        self.assertEqual(evidence["historical_support"], "unsupported")
        self.assertFalse(evidence["verified_current"])
        self.assertIn("retained_evidence_changed", [d["code"] for d in evidence["diagnostics"]])

    def test_guard_schema_uses_actual_maintenance_owner_namespace(self):
        import importlib.util
        import inspect
        companion = SCRIPTS.parent.parent / "ontology"
        if not companion.exists():
            self.skipTest("Optional ontology guard companion is absent.")
        script = companion / "scripts/ontology_guards.py"
        self.assertTrue(script.is_file(), "Partial ontology companion lacks its guard schema checker.")
        spec = importlib.util.spec_from_file_location("maintenance_namespace_guard_regression", script)
        guard = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(guard)
        config = load_config(self.root)
        write(self.root, "ontology.yaml", json_bytes({"project": {"id": config["project"]["id"]}}))
        identity = "1" * 32
        journal_path = config["state"]["maintenance"] + "/backend-" + identity + ".json"
        journal = {"schema_version": 1, "operation": "reindex", "operation_id": identity, "status": "failed"}
        write(self.root, journal_path, json_bytes(journal))
        for operation in ("reindex", "recover_reindex"):
            with self.subTest(operation=operation):
                owner = inspect.unwrap(getattr(maintenance, operation))
                namespace = owner.__globals__
                before = snapshot(self.root)
                facts = guard.schema_check(namespace, "memory", operation, self.root, {"operation_id": identity})
                self.assertTrue(facts["input_valid"])
                self.assertEqual(facts["input_type"], "memory-" + operation + "-request")
                self.assertEqual(snapshot(self.root), before)
                write(self.root, "ontology.yaml", json_bytes({"project": {"id": "another-project"}}))
                before = snapshot(self.root)
                self.assertFalse(guard.schema_check(namespace, "memory", operation, self.root, {"operation_id": identity})["input_valid"])
                self.assertEqual(snapshot(self.root), before)
                write(self.root, "ontology.yaml", json_bytes({"project": {"id": config["project"]["id"]}}))
        namespace = inspect.unwrap(maintenance.recover_reindex).__globals__
        journal["status"] = "complete"
        write(self.root, journal_path, json_bytes(journal))
        before = snapshot(self.root)
        self.assertFalse(guard.schema_check(namespace, "memory", "recover_reindex", self.root, {"operation_id": identity})["input_valid"])
        with self.assertRaises(guard.GuardError):
            guard.schema_check(namespace, "memory", "recover_reindex", self.root, {"operation_id": "invalid"})
        self.assertEqual(snapshot(self.root), before)


if __name__ == "__main__":
    unittest.main()
