"""Exact isolated candidate checks and impact; success is never publication authority."""
import copy
from pathlib import Path
import tempfile

from ontology_core import (OntologyError, canonical_bytes, sha256, safe_path, read_bytes,
                           read_json, load_project, require)
from ontology_publication import _root, check_proposal, preview
from ontology_proposals import open_proposal, store_validation, semantic_diff, utc_now, _event


def snapshot(root):
    project = load_project(root, validate=False)
    result = project.context()
    result["selected_sources"] = {}
    for relative in project.config["source_allowlist"]:
        source = safe_path(root, relative, must_exist=False)
        result["selected_sources"][relative] = sha256(source) if source.exists() else None
    companion = safe_path(root, "ontology-advanced.yaml", must_exist=False)
    if companion.exists():
        from ontology_advanced import load_advanced, load_extensions
        cfg = load_advanced(root)
        result["advanced_inputs"] = {"ontology-advanced.yaml": sha256(companion)}
        for ref in cfg["extensions"]:
            result["advanced_inputs"][ref["path"]] = sha256(safe_path(root, ref["path"]))
            extension = read_json(safe_path(root, ref["path"]))
            for shape in extension.get("shapes", []):
                result["advanced_inputs"][shape["path"]] = sha256(safe_path(root, shape["path"]))
        # Parse the exact selected extension so malformed locks cannot produce a review token.
        load_extensions(project, cfg)
        if cfg["profiles"].get("standards", {}).get("enabled"):
            from ontology_standards import _prepare, health
            result["standards_context"] = _prepare(root)[1]["context"]
            result["standards_readiness"] = health(root)
    result["review_target_sha256"] = sha256(canonical_bytes(result))
    return result


def _isolated(root, project, candidate, destination):
    inputs = set(project.snapshot["inputs"]) | set(project.config["source_allowlist"])
    for name in ("SOUL.md", "AGENTS.md", "ROLE.md", "SPECS.md"):
        if safe_path(root, name, must_exist=False).exists():
            inputs.add(name)
    for relative in inputs:
        source = safe_path(root, relative, must_exist=False)
        if source.exists():
            output = safe_path(destination, relative, must_exist=False)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(read_bytes(source))
    # Advanced validation uses selected original-root overrides; this copy is core-only.
    selected = set(project.config["project_files"] + project.config["binding_files"] + project.config.get("competency_files", []))
    for change in candidate["changes"]:
        if change["path"] in selected:
            output = safe_path(destination, change["path"], must_exist=False)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(change["content"].encode())


def validate_candidate(root, proposal_id, *, expected_revision):
    root = _root(root)
    current = open_proposal(root, proposal_id)
    record = current["revision"]
    require(record["revision"] == expected_revision, "draft_conflict", "A newer candidate superseded this validation request.")
    candidate = record["candidate"]
    findings, pre = [], None
    project = load_project(root, validate=False)
    target = snapshot(root)
    report = {"schema_version": 1, "proposal_id": proposal_id, "revision": expected_revision,
              "revision_sha256": record["revision_sha256"], "candidate_sha256": record["candidate_sha256"],
              "checked_at": utc_now(), "target_snapshot": target, "preview": None,
              "eligible": False, "findings": findings, "semantic_diff": semantic_diff(root, candidate),
              "core": {"valid": False}, "standards": {"status": "not_applicable"},
              "inference": {"status": "not_applicable"}, "competency": {"valid": False, "results": []},
              "impact": {}, "canonical_mutated": False}
    try:
        check_proposal(root, candidate)
        pre = preview(root, candidate)
        report["preview"] = pre
    except OntologyError as exc:
        findings.append(exc.as_dict())
    from check_ontology import run_checks
    baseline = run_checks(root)
    report["baseline_competency"] = baseline["competency"]
    with tempfile.TemporaryDirectory(prefix="ontology-proposal-check-") as temp:
        destination = Path(temp).resolve()
        _isolated(root, project, candidate, destination)
        checked = run_checks(destination)
        report["core"] = checked["structural"]
        report["competency"] = checked["competency"]
        findings.extend(checked["structural"].get("diagnostics", []))
        for case in checked["competency"]["results"]:
            if not case["valid"]:
                findings.append({"code": "competency_failure", "record_id": None, "path": case.get("file"),
                                 "message": "Competency " + case["id"] + " failed: " + "; ".join(case.get("failures", [])), "severity": "error"})
        if checked["structural"]["valid"]:
            from ontology_wiki import render_wiki
            from ontology_knowledge import knowledge
            proposed = load_project(destination)
            old_wiki, new_wiki = render_wiki(project), render_wiki(proposed)
            changed_pages = [key for key in sorted(old_wiki.keys() | new_wiki.keys()) if old_wiki.get(key) != new_wiki.get(key)]
            changed_ids = [d["id"] for d in report["semantic_diff"] if d["id"]]
            queries = []
            for rid in changed_ids[:20]:
                row = proposed.by_id.get(rid)
                if row:
                    query = row.get("label", rid)
                    queries.append({"query": query, "before": knowledge(project, query, intent="definition"),
                                    "after": knowledge(proposed, query, intent="definition")})
            report["impact"] = {"changed_ids": changed_ids, "wiki_pages": changed_pages,
                                "wiki_previews": [{"path": key, "before": old_wiki.get(key, b"").decode()[:12000],
                                                   "after": new_wiki.get(key, b"").decode()[:12000]} for key in changed_pages[:10]],
                                "query_results": queries,
                                "relationships": [r for r in proposed.relations if r["@id"] in changed_ids or r["subject"] in changed_ids or r["object"] in changed_ids][:100],
                                "truncated": len(changed_pages) > 10 or len(changed_ids) > 20}
    companion = safe_path(root, "ontology-advanced.yaml", must_exist=False)
    if companion.exists():
        from ontology_advanced import load_advanced
        cfg = load_advanced(root)
        overrides = {c["path"]: c["content"].encode() for c in candidate["changes"]}
        for name, operation in (("standards", "validate"), ("inference", "infer")):
            profile = cfg["profiles"].get(name, {})
            if profile.get("enabled"):
                try:
                    import ontology_standards
                    result = getattr(ontology_standards, operation)(root, overrides=overrides)
                except ImportError:
                    result = {"status": "unavailable", "diagnostics": [{"code": "backend_unavailable", "message": "Standards profile implementation is unavailable."}]}
                except OntologyError as exc:
                    result = {"status": "failed", "diagnostics": [exc.as_dict()]}
                report[name] = result
                if result.get("complete") is not True or operation == "validate" and result.get("conforms") is not True or operation == "infer" and result.get("status") != "ok":
                    findings.append({"code": "candidate_" + name, "record_id": None, "path": "ontology-advanced.yaml",
                                     "message": "Candidate " + name + " is not a completed conformant/consistent result: " + str(result.get("status")), "severity": "error"})
                for item in result.get("diagnostics", []):
                    if isinstance(item, dict) and item.get("severity") == "error":
                        findings.append(item)
        if candidate["schema_version"] == 2 and not cfg["profiles"].get("standards", {}).get("enabled"):
            findings.append({"code": "standards_required", "record_id": None, "path": "ontology-advanced.yaml", "severity": "error",
                             "message": "Advanced extension publication requires the enabled standards validation profile."})
    unique = {sha256(canonical_bytes(f)): f for f in findings}
    report["findings"] = [dict(value, finding_id="FIND-" + key[:12]) for key, value in sorted(unique.items())]
    old = {r["id"]:r["valid"] for r in baseline["competency"]["results"]}
    new = {r["id"]:r["valid"] for r in report["competency"]["results"]}
    report["competency_comparison"] = {"regressions": [i for i in old if old[i] and not new.get(i)],
                                       "improvements": [i for i in new if new[i] and not old.get(i)],
                                       "unchanged": [i for i in new if old.get(i) == new[i]]}
    report["eligible"] = bool(pre) and report["core"]["valid"] and report["competency"]["valid"] and not any(f.get("severity", "error") == "error" for f in report["findings"])
    require(snapshot(root) == target, "validation_inputs_changed", "Inputs changed during validation. The saved draft is preserved; validate it again.")
    return store_validation(root, proposal_id, expected_revision, report)


def assert_review_current(root, current):
    validation = current.get("validation")
    require(validation and validation["eligible"], "validation_required", "An eligible current validation is required.")
    require(snapshot(root) == validation["target_snapshot"], "stale_review", "Sources, helpers, configuration or canonical targets changed after validation.")
    require(preview(root, current["revision"]["candidate"])["preview_sha256"] == validation["preview"]["preview_sha256"],
            "stale_review", "Current publication preview differs from the validated candidate.")


def publish_revision(root, proposal_id, grant, *, expected_revision, expected_review_sha256, fail_at=None):
    current = open_proposal(root, proposal_id)
    require(current["head"]["revision"] == expected_revision and current["head"]["state"] == "reviewed"
            and current["head"]["review_sha256"] == expected_review_sha256, "stale_review", "Review must bind the current accepted candidate revision.")
    assert_review_current(root, current)
    from ontology_authority import review_binding
    require(grant.get("schema_version") == 2 and grant.get("proposal_review") == review_binding(current),
            "grant_review", "Proposal publication needs a v2 grant binding this exact revision, validation and review.")
    from ontology_publication import publish
    receipt = publish(root, current["revision"]["candidate"], grant,
                      expected_preview_sha256=current["validation"]["preview"]["preview_sha256"], fail_at=fail_at)
    reopened = []
    for item in receipt.get("files", []):
        path = safe_path(root, item["path"], must_exist=False)
        actual = sha256(path) if path.exists() else None
        reopened.append({"path": item["path"], "actual_sha256": actual, "matches_candidate": actual == item["sha256"]})
    complete = receipt.get("status") == "complete" and all(r["matches_candidate"] for r in reopened)
    _event(root, proposal_id, expected_revision, "published" if complete else "partial", {"receipt": receipt, "reopened": reopened})
    return {"status": "published" if complete else "partial", "receipt": receipt, "reopened": reopened,
            "proposal": open_proposal(root, proposal_id)}
