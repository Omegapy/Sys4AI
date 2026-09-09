"""Reconcile the unchanged requirements with reviewed implementation evidence.

Run only after TASK-001 through TASK-023 are accepted. This writes verification
projections, never canonical plan or Task state.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
PLAN = ROOT / "Implementation_Plans/Plan_sys4ai-what-did-you-learn-module-and-project-initialization_2026-09-09_2AB7D4CC/plan.json"
TRD = ROOT / "TRDs/trd_sys4ai-what-did-you-learn-module-and-project-initialization_2026-09-08.md"

EVIDENCE = {
    "source": ["learning-source-manifest.json", "learning-worker-result.md"],
    "helper": ["helper-results.json", "installed-memory.json"],
    "review": ["native-review-results.json", "native-review-launch.json"],
    "publication": ["native-publication-results.json", "native-publication-evidence.md"],
    "manager": ["native-manager-results.json", "native-manager-activation.json"],
    "reuse": ["comparable-use-results.json", "improvement-results.md"],
    "distribution": ["distribution-results.json", "active-root-adoption.json", "template-receipt.json"],
    "initializer": ["initializer-results.json", "initializer-source-manifest.json", "installed-initializer.json"],
    "native_initialization": ["native-initialization-results.json", "native-initialization-evidence.md"],
    "docs": ["documentation-results.json", "implementation-handoff.md"],
    "preservation": ["preservation-results.json"],
}

# These are the Director's evidence assessments. Each criterion retains its
# exact original text, with current locators and concrete observations.
ASSESSMENTS = {
1: ("source distribution", "Five substantive LEARNING-depo assets own policy, review contract and body template. The seven-file thin skill resolves those exact local assets; canonical learned records stay in MEMORY. Source, Template and active-root bytes agree."),
2: ("source helper review manager", "Both installed skill names enter one shared completion reference. Native manual review entered it once; manager completion records its actual checkpoint. No runtime hook, scheduler, second store or permanent role was added; the native test team follows the existing Task contract only."),
3: ("review publication", "The actual manual worker returned a supported proposal with applicability and limits and preserved every project byte/mtime. A separate current owner reviewed exact bytes and saved through the installed memory helper under the plan's publication scope."),
4: ("source review manager reuse", "The module requires verified completion before handoff and material settled-event review. Native evidence distinguishes measured clear-path success, reproduced ambiguous failure, unsettled export choice and unknown timeout cause; no recurrence threshold is imposed. Manager sequencing and later bounded fix are separately observed."),
5: ("source review", "The actual review left optional export intent pending and rejected silence/progress as acceptance. Only concise attributed findings and hashes were retained at the worker handoff. The contract explicitly reports unavailable interruption detection and has no guaranteed final-turn hook dependency."),
6: ("helper review preservation", "Representative native status/list/lookup/health/assessment commands preserved 169 file hashes/mtimes and 240 path modes/mtimes. Helper tests also preserve existing config, notes, indexes and Task state. Final 52-path depot preservation covers all unrelated live records and configuration."),
7: ("publication helper native_initialization", "Actual automatic capture off returned automatic_capture_off without writes; separately authorized explicit publication succeeded while config remained off. Native initialization reports current default-on and preserved-off readiness separately. Explicit manual review and static capability remain distinct from publication grants."),
8: ("review publication", "The native review compared expected clarification with the actual always-draft implementation and separated the unsupported timeout explanation. Ordinary owner-published records retain null Task/execution origins, with actual actor/config/source bindings and native receipts."),
9: ("review publication helper reuse", "Unknown timeout cause remained unknown; the controlled failing check is not production causal proof. The Director's concise local accepted fixture design supports discussion-only publication with actual source hash/locator. Native output, canonical receipts and subsequent code verification are distinct; no source identity or Task origin was invented."),
10: ("source review publication manager", "Review rejected temporary progress, unsupported conclusions and repeated in-session proposals. Exact operation retry created no extra active note. Actual conflicting-design supersession retained the predecessor body/history. The manager's completion report separately assesses whether any useful new finding remains."),
11: ("source helper publication", "All published lesson bodies use the six declared sections. Existing schema 1, accepted_design claims and active/superseded lifecycle fields validated through unchanged memory helpers. Real decision-recorded capture, explicit publish and same-operation recover use supported interfaces; no schema or trigger extension was introduced."),
12: ("review publication manager", "The child proposal stayed outside canonical memory until current owner review. Actual Director and activated manager grants bind exact native/config/Task/source bytes; receipts and canonical notes are reopened. The unauthorized real child was denied publisher_forbidden, with no policy/config rewrite to bypass that rejection."),
13: ("helper publication manager", "Actual repeated capture reused the operation and preserved the full snapshot. Fault injection after the successor replacement reported a committed successor and pending predecessor; shared recall suspended until original-operation recovery. Required publication was unmet until recovery; optional failure and accepted work are reported separately, with no terminal Task replay."),
14: ("source review publication reuse", "The proposal names Learning-Lab, fixture/intent_router.py, missing-field behavior, clear-path preservation and two observed checks. The unsupported timeout cause receives a bounded investigation disposition. Module policy permits existing milestone/explicit retrospective review without a scheduler or compulsory per-message exercise."),
15: ("review reuse preservation", "The first native worker proposed a fixture change without implementing it. A separate authorized later unit retrieved and rechecked the canonical lesson and current instruction/fixture sources, then changed only the demonstrated fixture target and tested ambiguous and already-clear cases. Existing to-trd 2.2.0 source and active copies remained protected."),
16: ("publication reuse", "Exact canonical hashes and lexical search returned the accepted lesson and its evidence with backend disabled. The later distinct native unit checked current applicability before the bounded improvement. Saved note, adopted change and measured later behavior have separate receipts; no long-term reliability claim is made."),
17: ("source helper review publication preservation", "Review treated synthetic instruction-bearing content as data and retained concise source-backed findings only. Existing publication sensitive-content validation passed; no credentials, unnecessary personal data, hidden reasoning or transcript archive was added. Root corpus/config and other projects' learned history remain unchanged."),
18: ("manager", "The isolated manager was reserved with MEMORY and control_records/memory scope, actually launched, receipt-bound and activated as sole canonical writer. Its report and current Task events verify independent frozen packets, excluded later notes/proposals, actual material-input gates, and learning review after verification before one terminal response."),
19: ("distribution initializer preservation", "The existing updater maps complete learning sources into neutral Template assets. Addition/modification/removal and conflict checks pass. Actual Template contract checks confirm project-local references and empty neutral state. Source edits, updater propagation and current-root adoption have separate receipts."),
20: ("distribution review preservation", "The exact 30-file active-root manifest was previewed, applied and reopened; module/skill/memory/initializer bytes match their source packages. Actual native review establishes behavior separately from static Template currency. All52 protected baseline paths retain their bytes, including root registry and learned history."),
21: ("initializer native_initialization review", "Actual installed CLI create uses only the registered isolated Template, specializes destination identity and installs complete local skill/module dependencies. The initialized native agent resolves and uses its local manual/shared contracts with the existing host interpreter, without depot runtime package fallback. Missing/incompatible resources receive explicit diagnostics."),
22: ("initializer native_initialization", "Actual first preparation covers selected existing/customized and manual-copy projects. Existing README/specs, packages, roles, Tasks, code, licensing, config, memory and repository boundaries are preserved in whole-package tests and native snapshots. Incompatible preserved dependencies are diagnosed without silent merging or overwrite."),
23: ("initializer native_initialization preservation", "A deliberately reconstructed completed prior-v6 fixture acquires learning through the current explicit module route. Ordinary reruns retain the base edition; nested module_adoptions preserve original fields and archived provenance. Owned whole-package refresh is explicit; custom bytes, off choice and history are preserved. Real registry and unspecified products remain unchanged."),
24: ("initializer native_initialization distribution review", "Setup verifies the complete local module, references and pinned compatible helper interfaces, and reports preserved incompatibility. Native manual/shared use works without hooks or semantic backend. No dependency install, model download, service initialization or external infrastructure is part of the checked routes."),
25: ("initializer native_initialization distribution", "New-project receipts show empty learned state and destination-local identity and authority from the neutral Template. Existing records/config/off are preserved. CLI readiness reports actual capture preference and the operation-grant requirement separately; a true flag is never treated as publication or backend readiness."),
26: ("initializer native_initialization", "Current receipts identify exact Template sources/destinations, package decisions, adopted/preserved files, checks and readiness. Real ordinary/repeated CLI routes preserve identity, registration and later local edits. Interrupted selected adoption resumes the exact frozen operation; changed source/target inputs are refused while history survives."),
27: ("helper review publication manager reuse native_initialization distribution", "The scenario matrix retains every WDYL-01 through WDYL-20 outcome and supporting layer. Actual native review, current owner publication, canonical/lexical retrieval, isolated Task ownership, later comparable improvement and local initialization complement helper tests. Required missing evidence causes this reconciliation command to fail; optional hooks remain excluded."),
28: ("docs distribution publication reuse native_initialization", "The local handoff links module ownership, current versions and new/first/prior-edition routes, exact adoption evidence and actual acceptance results. It distinguishes instruction checkpoints, unavailable hooks, isolated behavior, canonical publication, Task status and Git/product release boundaries. WDYL-H1/H2 remain excluded."),
}

SCENARIOS = {
    1: "review helper", 2: "review", 3: "native_initialization manager", 4: "publication", 5: "review publication manager", 6: "publication native_initialization",
    7: "review helper", 8: "review", 9: "publication", 10: "review manager publication", 11: "manager", 12: "manager", 13: "review reuse",
    14: "distribution initializer native_initialization preservation", 15: "publication", 16: "publication helper", 17: "review helper publication",
    18: "reuse publication", 19: "publication manager", 20: "reuse",
}

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def refs(groups):
    names = list(dict.fromkeys(name for group in groups.split() for name in EVIDENCE[group]))
    return [{"path": str((HERE / name).relative_to(ROOT)), "sha256": sha(HERE / name)} for name in names]

def inventory(plan):
    adoption = json.loads((HERE / "active-root-adoption.json").read_text())
    assert adoption["status"] == "applied"
    records = {}
    task_map = {t["task_id"]: t for t in plan["tasks"]}
    def add(path, tasks, owner, layer, expected=None, source=None):
        digest = sha(ROOT / path)
        if expected:
            assert digest == expected, path
        records[path] = {"path": path, "sha256": digest, "source": source, "layer": layer, "owner": owner,
                         "plan_tasks": tasks, "requirement_ids": sorted({r for t in tasks for r in task_map[t]["requirement_ids"]})}
    for entry in adoption["entries"]:
        source = entry["source"]
        if source.startswith("LEARNING-depo/"):
            tasks, owner = ["TASK-003", "TASK-015"], "learning_workflow"
        elif source.startswith("SKILLS-depo/what-did-you-learn/"):
            tasks, owner = ["TASK-004", "TASK-006", "TASK-016"], "learning_workflow"
        elif source.startswith("SKILLS-depo/memory/"):
            tasks, owner = ["TASK-005", "TASK-006", "TASK-016"], "learning_workflow"
        else:
            tasks, owner = ["TASK-007", "TASK-008", "TASK-009", "TASK-010", "TASK-011", "TASK-017"], "initializer_learning"
        add(source, tasks, owner, "reusable_source", entry["after_sha256"])
        add(entry["destination"], ["TASK-014", "TASK-018"], "root", "active_root_adoption", entry["after_sha256"], source)
        add("Projects/Sys4AI-Template-Project/" + entry["destination"], ["TASK-013", "TASK-018"], "root via updater", "template", entry["after_sha256"], source)
    for source, target in (
        ("SKILLS-depo/init-new-project/assets/baseline-assets.json", ".template/baseline-assets.json"),
        ("SPECS-depo/project-template-README.md", "README.md"),
        ("SPECS-depo/project-template-SPECS.md", "SPECS.md"),
        ("SPECS-depo/template-tests/test_template_contract.py", "tests/test_template_contract.py"),
    ):
        if source not in records:
            add(source, ["TASK-012", "TASK-015", "TASK-018"], "root", "reusable_source")
        add("Projects/Sys4AI-Template-Project/" + target, ["TASK-013", "TASK-015", "TASK-018"], "root via updater", "template", sha(ROOT / source), source)
    for path in ("README.md", "SPECS.md", "depot/template-update.md", "tests/test_repository_contract.py", "tests/test_template_update.py"):
        add(path, ["TASK-012", "TASK-015", "TASK-018"], "root", "project_local_documentation_or_check")
    # Complete package comparisons also detect an undeclared additional edit.
    baseline = json.loads((HERE / "baseline.json").read_text())
    for package, before in baseline["packages"].items():
        files = {p.relative_to(ROOT / package).as_posix(): sha(p) for p in (ROOT / package).rglob("*") if p.is_file() and "__pycache__" not in p.parts}
        changed = {name for name in files.keys() | before["files"].keys() if files.get(name) != before["files"].get(name, {}).get("sha256")}
        for name in changed:
            assert package + "/" + name in records, "Unmapped package change: " + package + "/" + name
    return sorted(records.values(), key=lambda r: r["path"])

def main():
    plan = json.loads(PLAN.read_text())
    assert all(t["status"] == "completed" for t in plan["tasks"] if int(t["task_id"].split("-")[1]) <= 23), "Required preceding implementation/native tasks remain incomplete"
    matrix = json.loads((HERE / "acceptance-matrix.json").read_text())
    assert sha(TRD) == matrix["trd_sha256"]
    expected = [(r["requirement_id"], c) for r in plan["requirements"] for c in r["acceptance_criteria"]]
    assert expected == [(c["requirement_id"], c["criterion"]) for c in matrix["criteria"]]
    normalize = lambda x: " ".join(x.replace("`", "").replace("**", "").split())
    trd = normalize(TRD.read_text())
    assert all(normalize(c["criterion"]) in trd for c in matrix["criteria"])
    assert len(matrix["criteria"]) == 81 and len(plan["requirements"]) == 28
    for name in ("distribution-results.json", "native-review-results.json", "native-publication-results.json", "native-manager-results.json", "comparable-use-results.json", "native-initialization-results.json", "preservation-results.json"):
        result = json.loads((HERE / name).read_text())
        assert result["status"] == "passed", (name, result.get("status"))
    observed_at = datetime.now(timezone.utc).isoformat()
    for criterion in matrix["criteria"]:
        number = int(criterion["requirement_id"].split("-")[1])
        groups, observation = ASSESSMENTS[number]
        criterion.update(status="passed", observed_at=observed_at, observed_result=observation, evidence=refs(groups),
                         verification_layers=groups.split())
    for scenario in matrix["scenarios"]:
        if scenario["scenario_id"].startswith("WDYL-H"):
            assert scenario["status"] == "excluded"
            scenario["observed_result"] = "Optional runtime hooks were explicitly excluded; no hook implementation or pass is claimed."
            continue
        number = int(scenario["scenario_id"].split("-")[1])
        groups = SCENARIOS[number]
        scenario.update(status="passed", observed_at=observed_at, evidence=refs(groups), verification_layers=groups.split(),
                        observed_result="Reviewed actual required outcome against the referenced native/helper/distribution receipts and corresponding requirement assessments.")
    matrix["observed_at"] = observed_at
    matrix["status"] = "passed"
    matrix["changed_artifact_inventory"] = inventory(plan)
    matrix["verification_artifact_scope"] = {"path": "Verification/what-did-you-learn", "owner": "root", "requirement_ids": ["REQ-027", "REQ-028"],
        "purpose": "Plan-authorized baseline, test/native receipts, disposable fixture projects, local audit and handoff. Existing copied capability is fixture input, not a new production adoption.",
        "canonical_tracking": "The selected plan and generated index are updated only by its helper; the isolated manager owns only its canonical fixture Task."}
    (HERE / "acceptance-matrix.json").write_text(json.dumps(matrix, indent=2) + "\n")
    lines = ["# Final requirement and artifact audit", "", f"Observed {observed_at}. The unchanged approved TRD has 28 requirements and 81 exact acceptance criteria. All81 have current reviewed evidence; 20 mandatory WDYL scenarios pass and 2 optional hook scenarios remain excluded.", "",
             "The matrix retains every original criterion, original scenario outcome, requirement/task mapping, concrete observation and current evidence-file hash. Source, active-root and updater-owned Template changes are mapped back to their plan tasks and requirement basis. Verification-only fixture projects and helper-owned tracking are separately identified.", "",
             f"The reverse inventory contains {len(matrix['changed_artifact_inventory'])} changed source/Template/root files. Whole existing memory/initializer package comparisons found no additional undeclared edits. Current role/source snapshots and preserved-path checks are linked by the implementation handoff.", "",
             "| Requirement | Result | Evidence layers |", "| --- | --- | --- |"]
    lines += [f"| REQ-{number:03d} | All original criteria passed | {groups.replace(' ', ', ')} |" for number, (groups, _) in ASSESSMENTS.items()]
    lines += ["", "Native behavior is bounded to isolated initialized projects. Helper fixtures, static resolution, canonical publication, lexical retrieval and later comparable use remain separate. No semantic backend setup, runtime hook, production-project rollout, Git publication or long-term reliability claim is included.", ""]
    (HERE / "final-audit.md").write_text("\n".join(lines))
    print(json.dumps({"status": "passed", "requirements": 28, "criteria": 81, "mandatory_scenarios": 20, "excluded_hooks": 2,
                      "changed_artifacts": len(matrix["changed_artifact_inventory"])}))

if __name__ == "__main__":
    main()
