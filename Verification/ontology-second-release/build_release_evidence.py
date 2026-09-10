"""Reopen release evidence without mutating canonical project state.

The reports are evidence projections, not lifecycle changes to the managed plan.
Ignored runtime trees have timestamp evidence only: their missing pre-run hashes
are explicitly retained as a limitation.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "Verification/ontology-second-release"
PLAN_PATH = "Implementation_Plans/Plan_sys4ai-ontology-knowledge-system-second-release_2026-09-09_4B15BB49/plan.json"
PLAN_SHA = "631b0d2dd3b58ff0d2f7085ba6ee5cb75f93cdb3d8b110ca387b9966c0f14c5e"
PACKAGES = ("ontology", "memory", "agent-task", "to-trd", "to-implementation-plan", "manage-subagent-roles", "init-new-project")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(name):
    return json.loads((OUT / name).read_text())


def write(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def ref(path):
    p = Path(path)
    if not p.is_absolute():
        p = ROOT / p
    assert p.is_file(), str(p)
    return {"path": p.relative_to(ROOT).as_posix(), "sha256": sha(p)}


def now():
    return datetime.now(timezone.utc).isoformat()


def preserved(path):
    # The exact source packages, root copies and registered Template are the
    # implementation scope. Everything else in the starting inventory stays
    # protected except the explicitly selected root integration artifacts.
    if "/modules/sys4ai-core/1.0.0/" in path or path.endswith("contexts/context-v1.jsonld") or path.endswith("schema/record-v1.json"):
        return True
    roots = ["ONTOLOGY-depo/", "reference-assets/ONTOLOGY-depo/", "ONTOLOGY/WIKI/",
             "Projects/Sys4AI-Template-Project/", "Verification/ontology-second-release/"]
    roots += [f"SKILLS-depo/{p}/" for p in PACKAGES]
    roots += [f".agents/skills/{p}/" for p in PACKAGES]
    selected = {".gitignore", "README.md", "SPECS.md", "depot/template-update.json", "depot/template-update.md",
                "tools/template_update.py", "tests/test_repository_contract.py", "SPECS-depo/project-template.gitignore",
                "SPECS-depo/template-tests/test_template_contract.py", "ONTOLOGY/bindings/artifacts.json",
                "ONTOLOGY/bindings/skills.json", "ONTOLOGY/modules/project/project.jsonld",
                "ONTOLOGY/modules/project/competency.json"}
    return path not in selected and not any(path.startswith(prefix) for prefix in roots)


def preservation():
    baseline = read("baseline.json")
    exact = {p: row for p, row in baseline["files"].items() if preserved(p)}
    write("preservation-manifest.json", {
        "schema_version": 1, "baseline": ref(OUT / "baseline.json"),
        "basis": "Selection from the actual pre-implementation file-hash inventory; no backdated observations.",
        "files": exact, "ignored_runtime_basis": "Separate timestamp-only observation; no pre-run content digest exists.",
        "explicit_root_semantic_changes": ref(OUT / "root-semantic-publication.json"),
    })
    rows = []
    for p, original in exact.items():
        f = ROOT / p
        actual = sha(f) if f.is_file() and not f.is_symlink() else None
        rows.append({"path": p, "before_sha256": original["sha256"], "after_sha256": actual,
                     "unchanged": actual == original["sha256"]})
    bad = [row for row in rows if not row["unchanged"]]
    runtime = []
    for name in (".venv", ".venv-memory-pilot", ".sys4ai/memory", "control_records/memory"):
        files = [p for p in (ROOT / name).rglob("*") if p.is_file() and not p.is_symlink()]
        changed = [p.relative_to(ROOT).as_posix() for p in files if p.stat().st_mtime >= 1788986611]
        runtime.append({"path": name, "file_count": len(files), "modified_since_goal_start": changed})
    registry = json.loads((ROOT / "depot/projects.json").read_text())
    products = [p for p in registry["projects"] if p["kind"] not in {"depot-manager", "project-template"}]
    canonical = read("root-semantic-publication.json")
    canonical_checks = [{**row, "current_sha256": sha(ROOT / row["path"])} for row in canonical["files"]]
    assert all(row["current_sha256"] == row["sha256"] for row in canonical_checks)
    # Original ID identity and meaning remain intact; selected source digests
    # are the only modifications to preexisting root records.
    record_path = "ONTOLOGY/modules/project/project.jsonld"
    stable = {"existing_ids_preserved": None, "basis": "Publication change inspected separately."}
    intent_path = ROOT / "control_records/ontology/intents/ONTOP-root-advanced-adoption-20260909.json"
    intent = json.loads(intent_path.read_text())
    prior = intent["prior_contents"][record_path].encode()
    if hashlib.sha256(prior).hexdigest() == baseline["files"][record_path]["sha256"]:
        old = json.loads(prior)["@graph"]
        new = json.loads((ROOT / record_path).read_text())["@graph"]
        old_ids = {r["@id"] for r in old}; new_ids = {r["@id"] for r in new}
        def semantic_content(value):
            if isinstance(value, dict):
                return {key: semantic_content(item) for key, item in value.items() if key != "sha256"}
            if isinstance(value, list):
                return [semantic_content(item) for item in value]
            return value
        indexed = {row["@id"]: row for row in new}
        meaning_changes = [row["@id"] for row in old if row["@id"] not in indexed or semantic_content(row) != semantic_content(indexed[row["@id"]])]
        assert not meaning_changes, meaning_changes
        stable = {"existing_ids_preserved": old_ids <= new_ids, "old_count": len(old_ids),
                  "new_count": len(new_ids), "removed_ids": sorted(old_ids - new_ids),
                  "existing_non_hash_content_changes": meaning_changes,
                  "added_ids": sorted(new_ids - old_ids), "basis": "Publisher's retained prior bytes verified equal to baseline SHA256 before ID comparison.",
                  "prior_bytes_source": ref(intent_path)}
    report = {"schema_version": 1, "observed_at": now(), "status": "passed" if not bad and not products else "failed",
              "manifest": ref(OUT / "preservation-manifest.json"), "protected_count": len(rows),
              "protected_groups": dict(Counter(p.split('/')[0] for p in exact)), "files": rows, "differences": bad,
              "registry": ref("depot/projects.json"), "ordinary_registered_products": products,
              "root_semantic_publication_reopened": canonical_checks, "root_identity_preservation": stable,
              "runtime_observations": runtime,
              "runtime_limit": "Ignored runtime trees were not hashed before execution; unchanged timestamps are corroboration, not byte-for-byte pre/post proof.",
              "git": {"baseline_head": baseline["head"], "current_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                      "publication_performed": False},
              "canonical_plan": {**ref(PLAN_PATH), "status": json.loads((ROOT / PLAN_PATH).read_text())["status"], "mutated": False}}
    assert not bad, bad
    assert not products, "Reassess actual products before claiming no product adoption"
    assert report["git"]["current_head"] == baseline["head"]
    assert sha(ROOT / PLAN_PATH) == PLAN_SHA
    assert stable["existing_ids_preserved"] is True
    write("preservation-audit.json", report)
    print(json.dumps({"preservation": report["status"], "protected_files": len(rows), "runtime_recent": {r['path']: len(r['modified_since_goal_start']) for r in runtime}}))


def native():
    fixture = OUT / "fixtures/native-context"
    summary_path = fixture / "control_records/native-context/manager-v2/final-task-summary.json"
    summary = json.loads(summary_path.read_text())
    references = {}
    for key in ("task", "acceptance_report", "accepted_synthesis", "terminal_validation", "last_response"):
        bound = summary[key]; p = fixture / bound["path"]
        assert sha(p) == bound["sha256"], key
        references[key] = ref(p)
    acceptance = json.loads((fixture / summary["acceptance_report"]["path"]).read_text())
    for bound in acceptance["artifacts"].values():
        assert sha(fixture / bound["path"]) == bound["sha256"], bound
    task = json.loads((fixture / summary["task"]["path"]).read_text())
    assert task["status"] == "completed" and task["revision"] == 50
    bindings = acceptance["bindings"]
    assert bindings["solver_a_g2"]["packet"] == bindings["solver_b_g2"]["packet"]
    assert all(b["status"] == "bound" for b in bindings.values())
    assert all(a["state"] == "completed" for a in acceptance["native_assignments"].values())
    report = {"schema_version": 1, "observed_at": now(), "status": "passed", "fixture": str(fixture),
              "summary": ref(summary_path), "reopened_references": references,
              "task_id": summary["task_id"], "task_revision": 50, "execution_stage": summary["execution_stage"],
              "actual_manager": summary["writer"], "generation": 2,
              "initial_packet_sha256": acceptance["artifacts"]["packet_g2_r1"]["sha256"],
              "reassessed_packet_sha256": acceptance["artifacts"]["packet_g2_r2"]["sha256"],
              "native_assignments": {k: {"native_id": v["native_id"], "state": v["state"]} for k, v in acceptance["native_assignments"].items()},
              "criteria": acceptance["main_criteria"], "bindings": bindings,
              "protected_files": acceptance["protected_files"], "limits": summary["limitations"],
              "evidence_kind": "Actual native orchestration, actual installed standards worker, actual scoped publication and exact reopened artifacts; no synthetic identities used to claim launches."}
    write("native-context-evidence.json", report)
    print(json.dumps({"native_context": "passed", "references_reopened": len(references) + len(acceptance['artifacts'])}))


def destinations():
    log = (OUT / "final-v9-destination-tests.log").read_text()
    assert "Ran 10 tests" in log and log.rstrip().endswith("OK")
    cases = [line.split(" (", 1)[0] for line in log.splitlines() if line.startswith("test_") and line.endswith(" ... ok")]
    assert len(cases) == 10
    report = {"schema_version": 1, "observed_at": now(), "status": "passed", "evidence_kind": "Actual installed initializer helper in disposable fixture destinations, not ordinary product adoption.",
              "log": ref(OUT / "final-v9-destination-tests.log"), "original_full_suite": ref(OUT / "initializer-v9-tests.json"),
              "cases": [{"name": n, "status": "passed"} for n in cases],
              "destinations": ["new v9 project", "first prepare of existing project", "manual neutral Template copy", "populated v8 selected advanced adoption", "earlier receipt selected prerequisite and upgrade", "customized or absent capability rejection", "partial exact recovery", "changed Template/capability during recovery", "authored edit preservation during pending upgrade"],
              "versions": {"initializer": 11, "new_base_edition": "governance-starter-v9", "prior_receipts": "preserved"},
              "limits": ["One full-suite fixture for simultaneous case-equivalent directories is skipped on this case-insensitive filesystem; it is not counted as exercised.", "No ordinary registered product project was upgraded."]}
    write("destination-matrix.json", report)


def checkpoint():
    report = {"schema_version": 1, "observed_at": now(), "status": "reviewed", "automatic_capture_enabled": True,
              "evidence": [ref(OUT / p) for p in ("learning-contract-check.json", "memory-capture-status.json", "completion-memory-search.json")],
              "disposition": "Useful observations are already implemented in this release and retained with reproducible tests. The plan's explicit canonical-memory preservation boundary is retained; no memory schema, record or runtime migration is part of this release.",
              "findings": [
                  {"finding": "Host-scoped browser cookies collide across different loopback ports; repeated same-port bootstraps must preserve current tabs.", "disposition": "implemented", "evidence": ref(OUT / "workbench-cookie-regression.log")},
                  {"finding": "Tests switching installed helper packages must restore process imports so deleted fixture modules cannot contaminate later checks.", "disposition": "implemented", "evidence": ref(OUT / "import-isolation-regression.log")},
                  {"finding": "Explicit advanced mixed retrieval must retain proposals and historical memory as distinct source types.", "disposition": "implemented", "evidence": ref(OUT / "advanced-memory-acceptance.json")}],
              "memory_writes": False, "personal_memory_update_authorized": False,
              "recall_limit": "Read-only memory lookup reported a stale README normalization and used current lexical source text without maintaining its cache."}
    write("completion-checkpoint.json", report)


TEST_DIR = "SKILLS-depo/ontology/tests/"
STD = "test_advanced_standards.py"
# Planned test files were consolidated into suites sharing the same real
# backend fixtures. Preserve that design deviation explicitly, including the
# concrete test methods; never create empty files to simulate plan coverage.
TEST_ALTERNATIVES = {
    "test_advanced_worker.py": [STD], "test_rdf_dataset.py": [STD],
    "test_rdf_provenance.py": [STD], "test_interchange.py": [STD, "test_advanced_publication.py"],
    "test_sparql.py": [STD], "test_shacl.py": [STD, "test_advanced_publication.py"],
    "test_reasoning_rules.py": [STD], "test_derivations.py": [STD],
    "test_reasoning_conflicts.py": [STD], "test_reasoning_limits.py": [STD, "test_advanced_packets.py"],
    "test_proposal_validation.py": ["test_proposals.py", "test_advanced_publication.py"],
    "test_refinement.py": ["test_generation_contract.py"],
    "test_action_contracts.py": ["test_action_semantics.py", "test_guard_engine.py", "test_guarded_dispatch.py"],
    "test_guarded_ontology.py": ["test_guarded_dispatch.py", "test_guard_recovery.py"],
    "test_ontology_guards.py": ["test_guarded_dispatch.py", "test_guard_recovery.py"],
    "test_workbench_drafts.py": ["test_workbench_security.py"],
    "test_workbench_conflicts.py": ["test_workbench_security.py", "test_proposals.py"],
    "test_advanced_reassessment.py": ["test_advanced_packets.py", "test_semantic_packet.py"],
}

ASSESSMENTS = {
    1: "All four required areas and both reasoning modes have working source and installed interfaces, with actual backend, model, native and browser evidence joined in the integrated acceptance report.",
    2: "Core v1 commands run with site packages disabled; exact core and historical-state hashes are preserved. Wrapper version2 is explicit and rejected by unsupported readers. No automatic product adoption or canonical memory/Task migration occurred.",
    3: "Separate exact package/model runtimes were explicitly prepared. Core-only and disabled cases do not provision dependencies; unavailable enabled profiles report non-success. Root readiness distinguishes selection, installation and validation.",
    4: "Actual confined worker probes observe network/file/process denial. Parsed context/import/XML/query/extension policies reject unselected access, with canonical preservation checks rather than string-denylist-only evidence.",
    5: "The RDF adapter distinguishes asserted, inferred, derived and external graph contexts, carries exact project/module/source versions and preserves canonical bytes. Dataset selection does not import linked projects.",
    6: "Actual JSON-LD/Turtle/RDF-XML staging and dataset manifests preserve graph identity, typed/language literals and blank-node semantic equivalence. Unsupported lossless conversions and conflicting imports fail without canonical publication.",
    7: "PROV-O entities, source/activity attribution and derivation links survive selected interchange. Freshness checks expose changed sources and provide no authority; final provenance and negative-assertion cases extend the original report.",
    8: "Actual SELECT, ASK, CONSTRUCT and DESCRIBE cases run over selected local named graphs and return versioned result forms. Graph output is transient; deterministic restrictions and DESCRIBE scope are documented.",
    9: "Actual update, SERVICE and disallowed FROM cases are rejected. Cancellation, invalid syntax and bounded execution retain distinct non-success states. Snapshot and timestamp checks show queries do not build persistent state.",
    10: "Actual pySHACL cases test valid and invalid graphs, compatible core checks, definitions, endpoints, provenance/cardinality, invalid/unsupported shapes and incomplete results. Inference cannot supply authoring approval.",
    11: "The finite rule engine derives the generated wiki Artifact type and declared property conclusions, with an independent owlrl oracle for supported examples. Drafts and lexical similarity are excluded from premises; unsupported axioms are explicit.",
    12: "Assertions, derived proofs and suggestions retain separate fact/source types in APIs and the browser. Selected proofs expose exact premises and rules; neither recomputation nor a reasoning result publishes assertions or grants authority.",
    13: "Actual unproven, explicit-negative, inconsistent and unsupported cases retain their distinct outcomes. A conflicting closure is untrusted, and explicit validation/authorization remains independent.",
    14: "Actual finite budgets/cancellation and stale-input cases fail truthfully; pinned repeat runs preserve normalized proofs. Frozen solver packets remain immutable when live approved facts change.",
    15: "Two actual native generation runs used exact permitted source packets and captured structured candidates. The embedded source instruction did not become a candidate instruction or expand the permitted output; source/runtime gates were separately tested.",
    16: "Durable revisions retain exact bytes, generator attribution, semantic diff and superseded review history. Browser inspection showed actual native request/result attribution, with model/effort names explicitly unobserved rather than invented.",
    17: "Real candidate validation runs core, SHACL, competency and formal-impact checks in an isolated overlay. Unsupported or malformed candidates cannot become eligible, and review exposes affected records and downstream changes.",
    18: "Exact grant, source and target hashes are checked by the existing publisher. Actual native and browser publication receipts were reopened; stale/rejected/partial cases preserve their true committed boundary and durable recovery state.",
    19: "The second native candidate addressed a named stale-target finding while preserving concurrent work and source lineage. Bounded revision tests stop repeated failures and retain neutral/negative evaluation outcomes.",
    20: "The actual local embedding model recovered a missed paraphrase and retained exact-identity priority. Model/index/helper/source versions and freshness are explicit. Frozen search uses captured vectors only; similarity grants no equivalence or authority.",
    21: "The reproducible comparison records exact corpus/config/model versions, sources, expectations, time/resource observations and false positives. Root top5 correctness was3/6 lexical and5/6 semantic, while top1 stayed3/6; no promised study percentage is adopted.",
    22: "Every declared consequential helper operation is bound to an exact contract. The REVIEW-001 correction adds real target/input/lifecycle/capability semantics while retaining the current owner authorizer as a separate gate.",
    23: "Real owning dispatch adapters validate structure, run enabled semantics, then retain owner authorization and execution. Natural invalid requests prove that the continuation is not invoked. Coverage explicitly excludes arbitrary shell and third-party paths.",
    24: "Enabled guards reject invalid or ambiguous inputs, unsupported contracts, stale state and backend failure. Failure diagnostics retain action/context evidence and an actionable condition; retry cannot silently disable the guard.",
    25: "Decision hashes bind exact requests, targets, sources, role/Task context and selected contracts. Actual changes inside each family's existing lock reject stale decisions. No cross-system atomicity is claimed.",
    26: "Successful guard receipts link the semantic check, exact request/context, owner result and reopened state. Independent authorization and partial-failure receipts remain distinct; observations contain bounded evidence, not hidden reasoning or credentials.",
    27: "The actual root and fixture browsers displayed project/readiness identity, ID/label/alias search, filters, typed relations and source navigation, with separate assertion/inference/proposal labels and a non-graph inspector.",
    28: "Actual browser forms created and revised a sourced project instance; real service tests create composite concepts/relations, reject invalid endpoints and preserve deprecation/replacement history. Locked core edits are denied.",
    29: "The browser inspected actual native proposal attribution, reviewed an exact diff, rejected/reopened a candidate, and published only through a current trusted-author session and normal guarded publisher. Receipt and canonical result were reopened.",
    30: "Two actual browser tabs produced a rejected stale save with the pending text retained. Reload preserved proposal/review identity; invalid/rejected drafts and partial publisher tests leave canonical data at the truthful pre/post boundary.",
    31: "Keyboard search and form/review controls completed the non-graph workflow. Field/validation errors retained input; actual narrow500px content had no horizontal overflow. No390px browser run is claimed.",
    32: "The service binds loopback and checks Host, Origin, CSRF, current actor and exact targets. Actual HTTP negatives reject forged authority and escaping sources; an actual browser renders an executable-looking label as literal text without an image or script execution.",
    33: "Actual independent initial native solvers received identical frozen version2 packet/baseline digests before any sibling candidate was imported. Captured scope and existing Task path/hash bounds remain intact, including separately tested frozen semantic vectors.",
    34: "The actual confirmed manager published a scoped late fact after initial forks, recorded materiality, reconciled solvers and delivered same-ID revised input handoffs before followup dispatch. Initial packet bytes stayed unchanged; current guard checks remain separate.",
    35: "Exact root memory hashes remain unchanged. Actual advanced mixed retrieval retains ontology, historical_memory, ontology_inference and ontology_proposal identities/source types without promoting history or drafts to authority.",
    36: "Exact source/root adoption receipts and final package/Template comparisons bind the installed capability. Neutral reusable assets contain no root records or prepared runtime state. Root-local Task intake policy is preserved as an explicit merge exception.",
    37: "Installed v9 initializer cases cover distinct new/first-prepared identities, neutral profile selections, populated prior-edition adoption, customized-package rejection and exact interrupted recovery. Original receipts, memory choices and licensing remain preserved.",
    38: "Installed/source command and verification guides document setup, inference/query/validation, proposal generation/review/publication, browser use and guard recovery. Durable proposals/receipts are kept separate from rebuildable graphs and indexes, and capability states are reported explicitly.",
    39: "The real pinned backend test suite observes all supported query forms, typed/language/provenance round trips, conformance/violations/failure, parser access restrictions and actual worker resource controls. Synthetic validator outputs are not the acceptance basis.",
    40: "Actual rule-engine evidence includes type and property conclusions, premise/rule inspection, unproven/contradictory/unsupported outcomes, stale-premise rejection and incomplete bounded/cancelled runs, checked with current source tests.",
    41: "Actual native candidates, an observed named-finding revision and reopened governed publication establish generation acceptance. Changed evidence, stale review and source-instruction boundaries are retained separately from parser/fixture tests.",
    42: "The corrected current dispatch matrix combines real backend natural-negative cases with valid owner actions and reopened results, per-boundary coverage, under-lock changes and recovery. Fixture native receipts are labeled synthetic; actual browser/native authority is separate evidence.",
    43: "Actual CUA sessions searched, inspected a derivation, edited and corrected a draft, reviewed/rejected/reopened/published exact content, and verified canonical publication. Separate actual read-only and two-tab conflict cases prove the required negative paths.",
    44: "The selected generation-native project joins sourced native generation, current concept retrieval/inference, optional embeddings and browser publication through enabled guards. Separate actual native manager/solver acceptance and exact preservation/destination reports complete the integrated evidence.",
}


def requirement_evidence(number):
    names = []
    tests = []
    if number in set(range(3, 15)) | {17, 39, 40}:
        names += ["standards-acceptance.json", "reasoning-acceptance.json", "root-inference-final.json"]
        tests += [STD, "test_advanced_profiles.py"]
    if number in {1, 2, 3, 36, 37, 38, 44}:
        names += ["root-core-final.json", "root-readiness-final.json", "template-distribution.json", "destination-matrix.json", "preservation-audit.json"]
        tests += ["test_loading.py", "test_advanced_profiles.py"]
    if number in set(range(15, 20)) | {21, 41}:
        names += ["generation-acceptance.json", "native-generation-validation-002.json", "native-generation-publication-002.json"]
        tests += ["test_proposals.py", "test_advanced_publication.py", "test_generation_contract.py"]
    if number in {3, 20, 21, 33, 35, 44}:
        names += ["root-retrieval-comparison-final.json", "semantic-packet-acceptance.json", "advanced-memory-acceptance.json"]
        tests += ["test_semantic_index.py", "test_semantic_retrieval.py", "test_semantic_packet.py", "test_advanced_memory.py"]
    if number in set(range(22, 27)) | {18, 25, 34, 42}:
        names += ["dispatch-acceptance.json", "guard-semantics-correction.json", "guard-correction-review.json", "guard-deadline-acceptance.json"]
        tests += ["test_action_semantics.py", "test_guard_engine.py", "test_guarded_dispatch.py", "test_guard_recovery.py", "test_guard_profiles.py", "test_guard_deadline.py"]
    if number in set(range(27, 33)) | {16, 18, 43, 44}:
        names += ["browser-acceptance.json", "browser-guard-correction-acceptance.json", "root-browser-acceptance.json", "workbench-accessibility.md"]
        tests += ["test_workbench_security.py", "test_proposals.py"]
    if number in {1, 14, 33, 34, 44}:
        names += ["native-context-evidence.json", "integrated-acceptance.json"]
        tests += ["test_advanced_packets.py"]
    if number in {2, 35, 36, 37, 38, 44}:
        names += ["preservation-audit.json", "completion-checkpoint.json"]
    if number == 38:
        names += ["RELEASE.md"]
    return sorted(set(names)), sorted(set(tests))


def test_methods(path):
    tree = ast.parse(path.read_text())
    return [{"name": node.name, "line": node.lineno} for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_")]


def audits(final=False):
    plan = json.loads((ROOT / PLAN_PATH).read_text())
    assert sha(ROOT / PLAN_PATH) == PLAN_SHA
    artifacts, absent = [], []
    for task in plan["tasks"]:
        if task["task_id"] == "TASK-054":
            # These reports describe themselves without circular hash bindings.
            continue
        for target in task["target_artifacts"]:
            path = ROOT / target
            selected = [target] if path.exists() else [TEST_DIR + f for f in TEST_ALTERNATIVES.get(path.name, [])]
            if not selected:
                absent.append(target)
                continue
            refs = []
            for actual in selected:
                p = ROOT / actual
                if p.is_dir():
                    refs.append({"path": actual, "kind": "directory", "file_inventory": "final-manifest.json"})
                else:
                    entry = ref(p)
                    if p.name.startswith("test_") and p.suffix == ".py":
                        entry["test_methods"] = test_methods(p)
                    refs.append(entry)
            artifacts.append({"task_id": task["task_id"], "requirement_ids": task["requirement_ids"],
                              "planned_path": target, "delivered": refs,
                              "mapping": "as planned" if selected == [target] else "Tests consolidated into shared actual-backend suites; behavior retained."})
    rows = []
    unresolved = []
    for requirement in plan["requirements"]:
        number = int(requirement["requirement_id"].split("-")[1])
        names, tests = requirement_evidence(number)
        missing = [n for n in names if not (OUT / n).is_file()]
        state = "verified" if final and not missing else "pending_final_acceptance"
        if missing:
            unresolved += missing
        row = {"requirement_id": requirement["requirement_id"], "title": requirement["title"],
               "source_ids": requirement["source_ids"], "status": state, "assessment": ASSESSMENTS[number],
               "acceptance_criteria": [{"criterion_number": i, "text": c, "status": state} for i, c in enumerate(requirement["acceptance_criteria"], 1)],
               "evidence": [ref(OUT / name) for name in names if (OUT / name).is_file()],
               "tests": [{**ref(TEST_DIR + name), "methods": test_methods(ROOT / TEST_DIR / name)} for name in tests],
               "task_ids": [t["task_id"] for t in plan["tasks"] if requirement["requirement_id"] in t["requirement_ids"]],
               "missing_evidence": missing}
        rows.append(row)
    result = {"schema_version": 1, "observed_at": now(), "status": "passed" if final and not absent and not unresolved else "in_progress",
              "canonical_plan": ref(PLAN_PATH), "canonical_state_mutated": False, "requirements": rows,
              "criterion_count": sum(len(r["acceptance_criteria"]) for r in rows), "artifact_mappings": artifacts,
              "missing_artifacts": sorted(set(absent)), "missing_evidence": sorted(set(unresolved)),
              "verification_basis": "Criterion-by-criterion host review of the actual implementation, current passing suites, scoped reviewer findings, and reopened native/browser/backend evidence. Each evidence file retains its own versions and limits."}
    write("requirement-audit.json", result)
    print(json.dumps({"requirement_audit": result["status"], "requirements": len(rows), "criteria": result['criterion_count'], "missing": result['missing_artifacts'] + result['missing_evidence']}))
    return result


def distribution():
    template = ROOT / "Projects/Sys4AI-Template-Project"
    state = json.loads((ROOT / ".sys4ai/template-update/state.json").read_text())
    managed = []
    for destination, bound in state["files"].items():
        d = template / destination
        source = ROOT / bound["source"]
        row = {"source": bound["source"], "destination": d.relative_to(ROOT).as_posix(),
               "source_sha256": sha(source), "destination_sha256": sha(d),
               "managed_sha256": bound["sha256"]}
        if "generated" in bound:
            # The role index is generated from exact role pairs, not a byte
            # copy of the Python generator. The updater's current check
            # independently regenerates it; verify every bound input here.
            assert bound["generated"]["kind"] == "role-index-v1"
            inputs = [{"destination": target, **value,
                       "source_matches": sha(ROOT / value["source"]) == value["sha256"],
                       "destination_matches": sha(template / target) == value["sha256"]}
                      for target, value in bound["generated"]["inputs"].items()]
            row["generated"] = {"kind": "role-index-v1", "inputs": inputs}
            row["matches"] = sha(d) == bound["sha256"] and all(i["source_matches"] and i["destination_matches"] for i in inputs)
        else:
            row["matches"] = sha(d) == sha(source) == bound["sha256"]
        managed.append(row)
    assert all(r["matches"] for r in managed), [r for r in managed if not r["matches"]]
    neutral = json.loads((template / "ontology-advanced.yaml").read_text())
    assert neutral["project_id"] is None and not neutral["extensions"] and not neutral["publication"]["enabled"]
    assert all(p == {"enabled": False} for p in neutral["profiles"].values())
    assert json.loads((template / "ONTOLOGY/modules/project/project.jsonld").read_text())["@graph"] == []
    assert not (template / ".venv-ontology-standards").exists()
    assert not (template / ".venv-ontology-semantic").exists()
    assert not (template / "ONTOLOGY/proposals").exists()
    assert not (template / "control_records/ontology/proposals").exists()
    check = read("template-final-check.json")
    watcher = read("template-watcher-current.json")
    assert check["status"] == "current" and not check["conflicts"]
    assert watcher["ready"] and not watcher["check_stale"]
    assert watcher["pid"] == watcher["last_check"]["pid"]
    exceptions = {".agents/skills/agent-task/" + p for p in ("SKILL.md", "assets/INDEX.md.template", "references/task-system-contract.md", "scripts/task_state.py", "tests/test_task_state.py")}
    root_rows = []
    for package in PACKAGES:
        for source in sorted((ROOT / "SKILLS-depo" / package).rglob("*")):
            if not source.is_file() or source.name == ".DS_Store" or "__pycache__" in source.parts:
                continue
            dest = ROOT / ".agents/skills" / source.relative_to(ROOT / "SKILLS-depo")
            relative = dest.relative_to(ROOT).as_posix()
            match = dest.is_file() and sha(dest) == sha(source)
            preserved_policy = relative in exceptions
            assert match or preserved_policy, relative
            root_rows.append({"source": source.relative_to(ROOT).as_posix(), "source_sha256": sha(source),
                              "destination": relative, "destination_sha256": sha(dest), "matches": match,
                              "root_policy_exception": preserved_policy})
    report = {"schema_version": 1, "observed_at": now(), "status": "passed",
              "registry": ref("depot/projects.json"), "mapping": ref("depot/template-update.json"),
              "managed_state": ref(".sys4ai/template-update/state.json"), "managed_file_count": len(managed),
              "managed_files": managed, "root_files": root_rows,
              "neutral_template": neutral, "publication_route": "Explicit checked template_update.py pipeline; no manual destination overwrite.",
              "root_policy_preservation": "Five root Agent Task files retain the existing depot intake/30-day policy. The changed Task helper has an exact baseline merge plus its optional intake guard; root-intake-tests.log verifies the retained policy.",
              "evidence": [ref(OUT / n) for n in ("template-final-check.json", "template-watcher-current.json", "root-intake-tests.log", "root-adoption-manifest.json", "root-adoption-receipt.json")],
              "product_adoption": "None; registry contains only depot and registered Template."}
    write("template-distribution.json", report)
    print(json.dumps({"distribution": "passed", "managed_files": len(managed), "root_files": len(root_rows)}))


def integrated():
    browser = read("browser-acceptance.json")
    generation = read("generation-acceptance.json")
    native_report = read("native-context-evidence.json")
    retrieval = read("combined-retrieval-final.json")
    assert browser["status"] == "passed" and generation["status"] == "published" and native_report["status"] == "passed"
    fixture = OUT / "fixtures/generation-native"
    assert browser["project_root"] == str(fixture)
    target = fixture / "ONTOLOGY/modules/project/project.jsonld"
    # Additional corrected-guard browser publication may advance the target;
    # its exact chained receipt is separate from the original observed flow.
    original = browser["published_sha256"]
    current = sha(target)
    latest = OUT / "browser-guard-correction-acceptance.json"
    if current != original:
        assert latest.is_file(), "A changed combined target needs current observed publication evidence"
        correction = json.loads(latest.read_text())
        assert correction["status"] == "passed" and correction["published_sha256"] == current
    assert retrieval["status"] == "ok" and retrieval["semantic"]["used"] is True
    assert retrieval["results"][0]["@id"].endswith(":ReleaseEvidenceBundle")
    assert retrieval["results"][0]["match_reason"] == "semantic_similarity"
    records = {r["@id"]: r for r in json.loads(target.read_text())["@graph"]}
    for identity in generation["published_ids"]:
        assert identity in records
    inference = read("combined-inference-final.json")
    query = read("combined-inferred-query-final.json")
    assert inference["status"] == "ok" and inference["complete"] is True and inference["trusted"] is True
    assert query["status"] == "ok" and query["complete"] is True and query["answer"] is True
    assert all(result["context"]["inputs"]["ONTOLOGY/modules/project/project.jsonld"] == current
               for result in (inference, query))
    assert any(triple[0].endswith(":browser-release-bundle") and triple[2].endswith(":Artifact") for triple in inference["inferred"])
    assert any(proof["rule"] == "cax-sco" and proof["premises"] for proof in inference["proofs"])
    report = {"schema_version": 1, "observed_at": now(), "status": "passed", "project_root": str(fixture),
              "flow": [
                  {"operation": "native source packet to concrete proposal and finding-directed revision", "evidence": ref(OUT / "generation-acceptance.json"), "native_runs": 2},
                  {"operation": "governed native proposal publication and exact reopening", "evidence": ref(OUT / "native-generation-publication-002.json")},
                  {"operation": "browser alias search, sourced concept and relation inspection", "evidence": ref(OUT / "browser-acceptance.json")},
                  {"operation": "selected real semantic model retrieval in the same approved project", "evidence": ref(OUT / "combined-retrieval-final.json")},
                  {"operation": "actual form edit, invalid validation, revision, conflict, review and guarded publication", "evidence": ref(OUT / "browser-acceptance.json"), "canonical_sha256_at_publication": original},
                  {"operation": "actual browser derived Artifact proof and selected inferred-graph ASK", "evidence": [ref(OUT / "browser-evidence/inference.json"), ref(OUT / "browser-evidence/inferred-query.json")]},
                  {"operation": "current final canonical inference and inferred-graph ASK reopened through installed CLI", "evidence": [ref(OUT / "combined-inference-final.json"), ref(OUT / "combined-inferred-query-final.json")]},
              ], "canonical_reopened": ref(target),
              "independent_solver_context": ref(OUT / "native-context-evidence.json"),
              "frozen_semantic_model": ref(OUT / "semantic-packet-acceptance.json"),
              "memory_scope": ref(OUT / "advanced-memory-acceptance.json"),
              "root_browser": ref(OUT / "root-browser-acceptance.json"),
              "root_runtime": ref(OUT / "root-readiness-final.json"),
              "root_inference": ref(OUT / "root-inference-final.json"),
              "temporary_services": ref(OUT / "workbench-cleanup.json"),
              "destination_setup": ref(OUT / "destination-matrix.json"),
              "preservation": ref(OUT / "preservation-audit.json"),
              "limits": ["Actual native context experiment is a distinct explicitly scoped fixture, with its disclosed cooperative read-scope qualification.",
                         "Synthetic native receipts in unit/dispatch fixtures do not establish real native launches; native and browser observations are separate.",
                         "Models and backend were deliberately installed for acceptance; neutral Template profiles remain disabled."]}
    if latest.is_file():
        report["corrected_guard_browser"] = ref(latest)
    write("integrated-acceptance.json", report)


def dispatch_acceptance():
    matrix = read("root-guarded-dispatch-corrected.json")
    assert matrix["status"] == "passed" and matrix["backend"] == "actual-selected-standards"
    families = {"ontology", "memory", "task", "trd", "plan", "role", "template", "setup"}
    required = {"positive", "invalid", "unauthorized", "stale", "ambiguous", "backend-failure"}
    grouped = {}
    for family in sorted(families):
        rows = [r for r in matrix["observations"] if r["family"] == family]
        assert required <= {r["case"] for r in rows}
        assert all(r["passed"] for r in rows)
        assert all(r.get("intended_side_effect") is False for r in rows if r["case"] != "positive")
        grouped[family] = rows
    root_guard = json.loads((ROOT / "ontology-advanced.yaml").read_text())["profiles"]["guards"]
    current_adapters = json.loads((ROOT / root_guard["adapters"]["path"]).read_text())
    normalized = json.dumps(current_adapters, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    assert hashlib.sha256(normalized).hexdigest() == matrix["adapters_sha256"]
    for row in matrix["observations"]:
        if row["case"] == "positive":
            helpers = row["receipt"]["ontology_guard"]["backend_context"]["helpers"]
            for filename in ("ontology_guards.py", "ontology_guard_setup.py"):
                assert helpers[filename] == sha(ROOT / ".agents/skills/ontology/scripts" / filename)
    review = read("guard-correction-review.json")
    assert review["status"] == "passed" and not review.get("unresolved_findings", [])
    report = {"schema_version": 1, "observed_at": now(), "status": "passed",
              "current_matrix": ref(OUT / "root-guarded-dispatch-corrected.json"),
              "families": grouped, "coverage": read("root-boundary-coverage-corrected.json"),
              "root_enabled_selection": root_guard,
              "corrected_semantic_contract": ref("reference-assets/ONTOLOGY-depo/actions/contracts-v1.json"),
              "repair_receipts": [ref(OUT / (name + "-guard-correction-receipt.json")) for name in ("root", "combined", "root-deadline", "combined-deadline")],
              "deadline": ref(OUT / "guard-deadline-acceptance.json"),
              "independent_review": ref(OUT / "guard-correction-review.json"),
              "prior_review": ref(OUT / "independent-review.json"),
              "superseded_evidence": "The original matrix tested SHACL failure with an impossible added shape. REVIEW-001 required real typed semantics and natural invalid requests; the corrected matrix is the acceptance basis.",
              "evidence_kind": "Actual selected standards backend and real owning helper continuations in disposable projects copied from the current installed root. Native fixture receipts are synthetic, explicitly separate from actual native/browser acceptance.",
              "limits": ["Arbitrary host, shell and third-party writes are outside these project dispatch adapters.", "Private low-level primitives are not advertised as a universal interception boundary.", "Existing owning transactions and locks remain authoritative; there is no cross-system atomicity guarantee."]}
    write("dispatch-acceptance.json", report)


def verification_summary():
    names = {"ontology": "final-ontology-tests-r7.log", "actual_semantic_packet": "semantic-packet-acceptance-final.log",
             "repository": "repository-contract-final.log", "template_contract": "template-contract-final.log",
             "installed_destinations": "final-v9-destination-tests.log", "root_intake": "root-intake-tests.log"}
    rows = {}
    for name, filename in names.items():
        raw = (OUT / filename).read_text()
        count = re.search(r"Ran (\d+) tests? in ([\d.]+)s", raw)
        result = re.search(r"\nOK(?: \(skipped=(\d+)\))?\s*$", raw)
        assert count and result, filename
        rows[name] = {"tests_run": int(count[1]), "skipped": int(result[1] or 0), "elapsed_seconds": float(count[2]),
                      "status": "passed", "evidence": ref(OUT / filename)}
    write("verification-summary.json", {"schema_version": 1, "observed_at": now(), "status": "passed", "suites": rows,
          "original_initializer": ref(OUT / "initializer-v9-tests.json"),
          "original_owner_regressions": ref(OUT / "guard-final-manifest.json"),
          "limit": "Suite counts are not added across overlapping runs. Skips and earlier failed logs remain explicit; actual native/browser evidence is separate."})
    return rows


def adoption_chain():
    baseline = read("baseline.json")["files"]
    chain = {p: row["sha256"] for p, row in baseline.items()}
    chain_sources = []
    for name in ("root-adoption-manifest.json", "semantic-default-adoption.json", "workbench-cookie-adoption.json", "semantic-packet-test-adoption.json", "final-integration-adoption.json", "root-extension-doc-adaptation.json", "verification-adoption.json", "guard-correction-adoption.json", "guard-deadline-adoption.json"):
        d = read(name)
        for row in d.get("changes", [d]):
            dest = row.get("destination", row.get("path"))
            if dest.startswith(str(ROOT) + "/"):
                dest = Path(dest).relative_to(ROOT).as_posix()
            # Destination-only extension README was first installed by the
            # separately selected companion adoption and is checked below.
            if dest == "ONTOLOGY/extensions/README.md" and dest not in chain:
                chain[dest] = row["expected_sha256"]
            assert chain.get(dest) == row["expected_sha256"], (name, dest, chain.get(dest), row["expected_sha256"])
            chain[dest] = row["sha256"]
        chain_sources.append(ref(OUT / name))
    selected = set()
    for name in chain_sources:
        data = json.loads((ROOT / name["path"]).read_text())
        for row in data.get("changes", [data]):
            selected.add(row.get("destination", row.get("path")))
    observed = []
    for p in sorted(selected):
        assert sha(ROOT / p) == chain[p], p
        observed.append({"path": p, "expected_sha256": chain[p], "current_sha256": sha(ROOT / p)})
    return {"status": "passed", "manifests": chain_sources, "reopened": observed,
            "historical_receipts": "Original accepted manifests remain immutable; later exact correction records advance only their named files."}


def final_manifest(audit):
    baseline = read("baseline.json")["files"]
    paths = subprocess.check_output(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=ROOT).decode().split("\0")
    paths += [p.relative_to(ROOT).as_posix() for p in OUT.glob("*.log")]
    excluded = {"Verification/ontology-second-release/final-manifest.json", "Verification/ontology-second-release/final-status.json"}
    changed, outside = [], []
    mappings = audit["artifact_mappings"]
    for p in sorted(set(paths) - excluded):
        f = ROOT / p
        if not f.is_file() or f.is_symlink() or f.name == ".DS_Store":
            continue
        current = sha(f)
        original = baseline.get(p, {}).get("sha256")
        if current == original:
            continue
        if p in {".sys4ai/role-catalog.lock", ".sys4ai/roles-case-rename.json"}:
            outside.append({**ref(p), "mtime": f.stat().st_mtime, "disposition": "Preexisting role runtime, omitted from original file inventory; not a release modification or publication selection."})
            continue
        origin = p
        if p.startswith(".agents/skills/"):
            origin = p.replace(".agents/skills/", "SKILLS-depo/", 1)
        elif p.startswith("reference-assets/ONTOLOGY-depo/"):
            origin = p.removeprefix("reference-assets/")
        elif p.startswith("Projects/Sys4AI-Template-Project/"):
            target = p.removeprefix("Projects/Sys4AI-Template-Project/")
            state = json.loads((ROOT / ".sys4ai/template-update/state.json").read_text())
            origin = state["files"].get(target, {}).get("source", p)
        tasks, requirements = set(), set()
        for mapping in mappings:
            for actual in mapping["delivered"]:
                if origin == actual["path"] or (actual.get("kind") == "directory" and origin.startswith(actual["path"].rstrip("/") + "/")):
                    tasks.add(mapping["task_id"]); requirements.update(mapping["requirement_ids"])
        if p.startswith("Verification/ontology-second-release/"):
            tasks.add("TASK-054"); requirements.update(r["requirement_id"] for r in audit["requirements"])
        elif p.startswith("control_records/ontology/") or p == "ontology-advanced.yaml" or p.startswith("ONTOLOGY/"):
            tasks.update({"TASK-046", "TASK-052"}); requirements.update({"REQ-002", "REQ-025", "REQ-035", "REQ-036", "REQ-044"})
        if not tasks:
            # Package glue, runtime exclusion and distribution documentation
            # implement the explicit packaging/operational tasks.
            assert origin.startswith(("SKILLS-depo/", "ONTOLOGY-depo/", "SPECS-depo/", "depot/")) or origin in {".gitignore", "README.md", "SPECS.md", "tests/test_repository_contract.py", "tools/template_update.py"}, origin
            tasks.update({"TASK-042", "TASK-053"}); requirements.update({"REQ-036", "REQ-037", "REQ-038"})
        changed.append({"path": p, "baseline_sha256": original, "sha256": current, "size": f.stat().st_size,
                        "change": "added" if original is None else "modified", "source_origin": origin,
                        "task_ids": sorted(tasks), "requirement_ids": sorted(requirements)})
    report = {"schema_version": 1, "observed_at": now(), "status": "passed", "canonical_plan": ref(PLAN_PATH),
              "files": changed, "file_count": len(changed), "outside_release_selection": outside,
              "adoption_chain": adoption_chain(), "forward_traceability": ref(OUT / "requirement-audit.json"),
              "preservation": ref(OUT / "preservation-audit.json"), "distribution": ref(OUT / "template-distribution.json"),
              "self_binding": "final-status.json binds this manifest; both are excluded from this manifest to avoid a circular hash.",
              "evidence_boundaries": "Ignored disposable projects/models are bound by their explicit acceptance report references, not indiscriminately selected for Git. This inventory is not a Git staging or publication manifest."}
    write("final-manifest.json", report)
    print(json.dumps({"final_manifest_files": len(changed), "adoption_chain": "passed"}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("support", "audit-preview", "distribution", "assemble", "final"))
    args = parser.parse_args()
    if args.mode == "support":
        preservation(); native(); destinations(); checkpoint()
    elif args.mode == "audit-preview":
        audits()
    elif args.mode == "distribution":
        distribution()
    elif args.mode == "assemble":
        preservation(); native(); destinations(); checkpoint(); distribution(); dispatch_acceptance(); integrated(); verification_summary(); audits()
    elif args.mode == "final":
        audit = audits(final=True)
        assert audit["status"] == "passed"
        assert read("dispatch-acceptance.json")["status"] == read("integrated-acceptance.json")["status"] == "passed"
        assert read("verification-summary.json")["status"] == "passed"
        final_manifest(audit)
        result = {"schema_version": 1, "observed_at": now(), "status": "complete", "plan_id": "PLAN-20260909-4B15BB49",
                  "canonical_plan": ref(PLAN_PATH), "plan_lifecycle_mutated": False, "requirements_verified": len(audit["requirements"]),
                  "acceptance_criteria_verified": audit["criterion_count"],
                  "highest_verification_level": "Local integrated implementation with actual confined standards/model backends, native generation and independent solver workflow, real browser publication, installed dispatch acceptance, source/root/Template parity and exact protected-file verification.",
                  "evidence": [ref(OUT / n) for n in ("RELEASE.md", "requirement-audit.json", "final-manifest.json", "verification-summary.json", "preservation-audit.json", "integrated-acceptance.json", "dispatch-acceptance.json", "template-distribution.json", "root-task-status-final.json", "completion-checkpoint.json")],
                  "unresolved_required_work": [], "external_publication": "Not performed; no commit, push, PR, hosted service or product adoption was requested.",
                  "limits": ["Darwin-only verified worker confinement; finite documented rule profile.", "Native-agent scope is cooperative with the disclosed style-read exception.", "Ignored old runtimes have timestamp-only pre/post corroboration, not missing baseline hashes invented after the fact.", "Current root Task ledger has21 terminal and0 nonterminal Tasks; the native acceptance Task lives only in its disposable project.", "Temporary workbench services were stopped after acceptance; enabled configuration does not mean a server is left running."]}
        write("final-status.json", result)
        print(json.dumps({"status": result["status"], "requirements": len(audit['requirements']), "criteria": audit['criterion_count']}))
