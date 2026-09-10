"""Run the same frozen competency cases through lexical and real local semantic retrieval."""
import argparse
import json
from pathlib import Path
import resource
import sys
import time

REPO = Path(__file__).resolve().parents[2]
INSTALLED = "--installed" in sys.argv
sys.path.insert(0, str((REPO / ".agents/skills/ontology/scripts") if INSTALLED else (REPO / "SKILLS-depo/ontology/scripts")))
from ontology_core import OntologyError, canonical_bytes, load_project, read_json, sha256
from ontology_retrieval import search as lexical
from ontology_semantic import INDEX, build_index, load_index, search as semantic


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--installed", action="store_true")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    cases_path = REPO / "SKILLS-depo/ontology/tests/fixtures/advanced_competency.json"
    cases = read_json(cases_path)
    build = build_index(root) if args.build else None
    project = load_project(root)
    index = load_index(project)
    observations = []
    for case in cases["cases"]:
        row = dict(case)
        for name, run in (("first_release_lexical", lambda: lexical(project, case["query"], limit=5, semantic=False)),
                          ("semantic", lambda: semantic(project, case["query"], limit=5))):
            started = time.monotonic(); before = resource.getrusage(resource.RUSAGE_CHILDREN)
            try:
                result = run()
                ids = [r["@id"] for r in result["results"]]
                after = resource.getrusage(resource.RUSAGE_CHILDREN)
                row[name] = {"status": result["status"], "ids": ids,
                             "correct_at_1": bool(ids and ids[0] == case["expected"]) if case["expected"] else not ids,
                             "correct_at_5": case["expected"] in ids if case["expected"] else not ids,
                             "attribution": [{"id": r["@id"], "sources": r["source_status"], "reason": r["match_reason"]} for r in result["results"]],
                             "elapsed_seconds": time.monotonic()-started,
                             "child_cpu_seconds": after.ru_utime+after.ru_stime-before.ru_utime-before.ru_stime,
                             "child_maxrss_raw": after.ru_maxrss, "semantic": result.get("semantic")}
            except OntologyError as exc:
                row[name] = {"status": "failed", "diagnostic": exc.as_dict(), "correct_at_1": False, "correct_at_5": False,
                             "elapsed_seconds": time.monotonic()-started}
        observations.append(row)
    report = {"schema_version": 1, "package": "installed root" if INSTALLED else "depot source", "project_root": str(root), "project_id": project.project_id,
              "dataset": {"path": str(cases_path.relative_to(REPO)), "sha256": sha256(cases_path)},
              "context": project.context(), "model": index["runtime"], "index_sha256": sha256(root / INDEX),
              "build": build, "observations": observations,
              "summary": {name: {metric: sum(r[name][metric] for r in observations) for metric in ("correct_at_1", "correct_at_5")}
                          for name in ("first_release_lexical", "semantic")},
              "interpretation": "Observed local cases only. Negative and neutral outcomes are retained. Similarity is neither equivalence nor approval. No extracted graph was published."}
    Path(args.output).write_bytes(canonical_bytes(report))
    print(json.dumps(report["summary"]))


if __name__ == "__main__":
    main()
