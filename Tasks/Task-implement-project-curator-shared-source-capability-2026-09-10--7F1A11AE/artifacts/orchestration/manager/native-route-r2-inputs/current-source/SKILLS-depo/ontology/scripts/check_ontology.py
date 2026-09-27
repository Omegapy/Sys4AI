#!/usr/bin/env python3
"""One local CI entry point for structural and module-owned competency checks."""
import argparse
import json
import sys
sys.dont_write_bytecode = True

from ontology_core import OntologyError, canonical_bytes, load_project, read_json, require, safe_path
from ontology_knowledge import knowledge
from ontology_validate import validate_project


def run_checks(root):
    try:
        p = load_project(root, validate=False)
    except OntologyError as error:
        return {"valid": False, "mutated": False, "structural": {"valid": False, "diagnostics": [error.as_dict()]},
                "competency": {"valid": False, "status": "unavailable_invalid_inputs", "results": []}}
    structural = validate_project(p, require_current=True)
    if not structural["valid"]:
        return {"valid": False, "mutated": False, "structural": structural, "context": p.context(),
                "competency": {"valid": False, "status": "unavailable_invalid_structure", "results": []}}
    files = [m["path"] + "/competency.json" for m in p.modules if "competency.json" in m["files"]]
    files.extend(p.config.get("competency_files", []))
    results, seen = [], set()
    for path in sorted(files):
        try:
            suite = read_json(safe_path(p.root, path))
            require(isinstance(suite, dict) and set(suite) == {"schema_version", "questions"} and suite["schema_version"] == 1
                    and isinstance(suite["questions"], list), "invalid_competency", "Competency file requires schema_version 1 and questions.", path=path)
            for question in suite["questions"]:
                allowed = {"id", "intent", "query", "expected_ids", "expected_terms", "expected_relations", "expected_sources", "expected_status", "absent_ids"}
                require(isinstance(question, dict) and {"id", "intent", "query"} <= set(question) <= allowed
                        and isinstance(question["id"], str) and question["id"] not in seen,
                        "invalid_competency", "Competency question has unsupported fields, duplicate identity or missing inputs.", path=path)
                require(isinstance(question["query"], str) and question["query"].strip() and isinstance(question["intent"], str)
                        and question["intent"] in {"definition", "relationship", "capability", "current", "history", "mixed"}, "invalid_competency", "Competency query and intent must be supported strings.", path=path)
                for field in ("expected_ids", "expected_terms", "expected_sources", "absent_ids"):
                    require(isinstance(question.get(field, []), list) and all(isinstance(v, str) and v for v in question.get(field, [])), "invalid_competency", "Competency expectation must be an array of nonempty strings.", path=path)
                require(isinstance(question.get("expected_relations", []), list) and all(isinstance(e, dict) and set(e) == {"subject", "predicate", "object"} and all(isinstance(v, str) and v for v in e.values()) for e in question.get("expected_relations", [])), "invalid_competency", "Expected relations require subject, predicate and object identities.", path=path)
                require("expected_status" not in question or isinstance(question["expected_status"], str), "invalid_competency", "Expected status must be a string.", path=path)
                require(any(question[key] for key in question if key.startswith("expected_") or key == "absent_ids"), "invalid_competency", "Competency questions need nonempty observable assertions.", path=path)
                seen.add(question["id"])
                response = knowledge(p, question["query"], intent=question["intent"], limit=100)
                ids = {r.get("@id") for r in response["results"]}
                text = canonical_bytes(response["results"]).decode().casefold()
                sources = {s["path"] for r in response["results"] for s in r.get("source_status", r.get("sources", []))}
                sources.update(r["path"] for r in response["results"] if r.get("source_type") == "current_governance")
                relations = [edge for r in response["results"] for edge in ([r] if r.get("kind") == "relation" else r.get("relationships", []))]
                failures = []
                for identity in question.get("expected_ids", []):
                    if identity not in ids: failures.append("Missing identity: " + identity)
                for identity in question.get("absent_ids", []):
                    if identity in ids: failures.append("Unexpected identity: " + identity)
                for term in question.get("expected_terms", []):
                    if term.casefold() not in text: failures.append("Missing expected text: " + term)
                for source in question.get("expected_sources", []):
                    if source not in sources: failures.append("Missing source: " + source)
                for edge in question.get("expected_relations", []):
                    if not any(all(r.get(k) == v for k, v in edge.items()) for r in relations):
                        failures.append("Missing typed relation: " + json.dumps(edge, sort_keys=True))
                if "expected_status" in question and response["status"] != question["expected_status"]:
                    failures.append("Unexpected query status: " + response["status"])
                if response.get("truncation", {}).get("truncated"):
                    failures.append("Competency result was truncated; narrow the question or improve its bounded route.")
                results.append({"id": question["id"], "file": path, "valid": not failures, "failures": failures,
                                "result_ids": sorted(i for i in ids if i), "status": response["status"]})
        except OntologyError as error:
            results.append({"id": path, "file": path, "valid": False, "diagnostic": error.as_dict()})
    competency = {"valid": bool(results) and all(r["valid"] for r in results), "status": "checked" if files else "missing", "results": results}
    return {"valid": structural["valid"] and competency["valid"], "structural": structural, "competency": competency,
            "context": p.context(), "mutated": False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", required=True)
    args = parser.parse_args(argv)
    result = run_checks(args.project_root)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
