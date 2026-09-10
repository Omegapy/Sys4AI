"""Read-only adapters to the installed memory package and explicit derived links."""
import json
import os
import re
import subprocess
import sys

from ontology_core import OntologyError, canonical_bytes, read_bytes, read_json, require, safe_path, sha256
from ontology_retrieval import limits, normalize, project, query_text, ranked


def _installed(p, operation, **arguments):
    """Call current installed public APIs in a separate import namespace."""
    scripts = safe_path(p.root, ".agents/skills/memory/scripts", must_exist=False)
    if not scripts.is_dir() or not safe_path(p.root, ".agents/skills/memory/scripts/memory.py", must_exist=False).is_file():
        return {"status": "unavailable", "results": [], "limitations": ["Installed project memory interface is unavailable."]}
    code = '''import json,sys
sys.dont_write_bytecode=True
sys.path.insert(0,sys.argv[1])
from memory_core import MemoryError,load_config,load_record,load_records
from memory_search import search
data=json.load(sys.stdin)
try:
 config=load_config(data['root'],optional=True)
 if config is None:
  result={'status':'unconfigured','results':[],'limitations':['No project memory configuration.']}
 elif config['project']['id']!=data['project_id']:
  result={'status':'identity_mismatch','results':[],'limitations':['Memory and ontology project identities differ.']}
 elif data['operation']=='search':
  result=search(data['root'],data['query'],config=config,packet=data.get('packet'),limit=data['limit'],mode='lexical')
 elif data['operation']=='read':
  result={'status':'ok','project_id':config['project']['id'],'record':load_record(data['root'],data['path'],config)}
 elif data['operation']=='records':
  result={'status':'ok','project_id':config['project']['id'],'records':load_records(data['root'],config)}
 else:
  raise ValueError('Unsupported ontology memory operation')
 print(json.dumps(result,sort_keys=True))
except MemoryError as error:
 print(json.dumps({'status':'error','error':error.as_dict(),'results':[]}))
 sys.exit(2)
'''
    data = {"root": str(p.root), "project_id": p.project_id, "operation": operation, **arguments}
    try:
        run = subprocess.run([sys.executable, "-B", "-c", code, str(scripts)],
                             input=json.dumps(data), text=True, capture_output=True, timeout=30,
                             env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    except (OSError, subprocess.TimeoutExpired) as error:
        return {"status": "unavailable", "results": [], "limitations": [f"Installed memory interface unavailable ({type(error).__name__})."]}
    try:
        value = json.loads(run.stdout)
    except ValueError:
        raise OntologyError("memory_interface_failed", "Installed memory interface did not return JSON.") from None
    if run.returncode and value.get("error"):
        error = value["error"]
        if arguments.get("packet") or error.get("code") in {"excluded_source", "unsafe_path", "project_identity", "symlink_path"}:
            raise OntologyError("memory_" + error.get("code", "error"), error.get("message", "Memory input rejected."))
        value["status"] = "unavailable"
        value["limitations"] = ["Memory retrieval rejected the input: " + error.get("code", "error")]
    elif run.returncode:
        raise OntologyError("memory_interface_failed", "Installed memory interface failed.")
    return value


def expand_query(p, query):
    query = query_text(query)
    terms = [query]
    concepts = []
    rows = ranked(p, query, kinds={"concept", "instance"})
    for _, record in rows[:3]:
        if record["lifecycle"] != "approved":
            continue
        concepts.append(record["@id"])
        terms.extend([record["label"], *record.get("aliases", [])])
        for relation in p.relations:
            if relation["subject"] == record["@id"] and relation["predicate"].rsplit(":", 1)[-1] in {"relatedTo", "broader", "narrower"}:
                related = p.by_id[relation["object"]]
                if related["lifecycle"] == "approved":
                    terms.append(related["label"])
    unique = list(dict.fromkeys(t.strip() for t in terms if t.strip()))[:8]
    return {"queries": unique, "concept_ids": sorted(set(concepts)), "max_queries": 8,
            "route": "original, resolved concepts, aliases and one-hop related vocabulary"}


def search_memory(value, query, *, limit=None, packet=None, frozen_ontology=False):
    p = project(value)
    frozen_ontology = frozen_ontology or hasattr(p, "frozen_packet")
    bound = limits(p, limit)
    expansion = expand_query(p, query)
    if frozen_ontology and packet is None:
        return {"status": "unavailable", "source_type": "historical_memory", "results": [],
                "expansion": expansion, "mutated": False,
                "limitations": ["Frozen ontology queries require an exact frozen memory packet before historical retrieval."]}
    found, limitations, excluded = {}, [], []
    mode, state = "lexical", "no_matching_historical_evidence"
    for term in expansion["queries"]:
        result = _installed(p, "search", query=term, packet=packet, limit=bound["limit"])
        limitations.extend(result.get("limitations", []))
        if result["status"] in {"unavailable", "unconfigured", "identity_mismatch"}:
            state = "unavailable"
            break
        mode = result.get("mode", "lexical")
        for row in result.get("results", []):
            # An ontology expansion never relaxes active-record/evidence policy.
            if row.get("kind") != "memory":
                continue
            if row.get("state") != "active" or row.get("diagnostics"):
                excluded.append({"record_id": row.get("record_id"), "reason": "inactive_or_unverified_evidence"})
                continue
            key = (row["record_id"], row["sha256"])
            if key not in found:
                found[key] = {**row, "source_type": "historical_memory", "freshness": "current",
                              "match_reason": "ontology_expanded_memory_" + mode, "matched_queries": [],
                              "authority": "Historical memory evidence; it does not establish current operational authority."}
            found[key]["matched_queries"].append(term)
    results = sorted(found.values(), key=lambda r: (-r["score"], r["record_id"], r["path"]))[:bound["limit"]]
    return {"status": "ok" if results else state, "mode": mode, "source_type": "historical_memory",
            "project_id": p.project_id, "results": results, "expansion": expansion, "packet": packet,
            "excluded": sorted(excluded, key=lambda r: r["record_id"] or ""),
            "limitations": sorted(set(limitations + ["Ontology requests deterministic lexical memory retrieval; backend configuration is unchanged."])), "mutated": False}


def link_memory(value, *, record_paths=(), concept_queries=()):
    from ontology_build import write_generated
    p = project(value)
    records = []
    if record_paths:
        for path in sorted(set(record_paths)):
            result = _installed(p, "read", path=path)
            if result["status"] != "ok":
                raise OntologyError("memory_unavailable", "A selected memory record is unavailable or rejected.", path=path)
            records.append(result["record"])
    else:
        result = _installed(p, "records")
        if result["status"] != "ok":
            raise OntologyError("memory_unavailable", "Accessible project memory records are unavailable.")
        records = result["records"]
    associations, exclusions, versions = [], [], []
    vocabulary = sorted({word for r in p.records if r["kind"] in {"concept", "instance"}
                         for word in [r["label"], *r.get("aliases", [])]})
    for record in records:
        meta = record["metadata"]
        if meta["state"] != "active" or record["diagnostics"]:
            exclusions.append({"record_id": meta["id"], "reason": "inactive_or_unverified_evidence"})
            continue
        versions.append({"record_id": meta["id"], "path": record["path"], "sha256": record["sha256"],
                         "sources": meta["sources"]})
        content = normalize(meta["title"] + " " + record["body"])
        queries = list(concept_queries) if concept_queries else [q for q in vocabulary if re.search(r"(?<!\w)" + re.escape(normalize(q)) + r"(?!\w)", content)]
        if not queries:
            associations.append({"record_id": meta["id"], "status": "unmatched", "concept_ids": [], "query": None})
        for query in sorted(set(queries)):
            rows = ranked(p, query, kinds={"concept", "instance"})
            if rows:
                rows = [(m, r) for m, r in rows if m[:2] == rows[0][0][:2]]
            identities = sorted(r["@id"] for _, r in rows if r["lifecycle"] == "approved")
            associations.append({"record_id": meta["id"], "query": query, "concept_ids": identities,
                                 "status": "unmatched" if not identities else "ambiguous" if len(identities) > 1 else "derived_association"})
    sidecar = {"schema_version": 1, "kind": "derived-memory-concept-links", "project_id": p.project_id,
               "source_type": "derived_association", "ontology_context": p.context(),
               "records": sorted(versions, key=lambda r: r["record_id"]),
               "associations": associations, "excluded": exclusions,
               "authority": "Rebuildable associations; no canonical memory or ontology claim is created."}
    # Reopen exact selected records and evidence before publishing the sidecar.
    for r in sidecar["records"]:
        current = _installed(p, "read", path=r["path"])
        if current["status"] != "ok" or current["record"]["sha256"] != r["sha256"] or current["record"]["diagnostics"]:
            raise OntologyError("memory_changed", "Selected memory changed during link generation.", path=r["path"])
    return write_generated(p, {".sys4ai/ontology/links/memory-records.json": canonical_bytes(sidecar)}, operation="link-memory")


def read_links(value):
    p = project(value)
    target = safe_path(p.root, ".sys4ai/ontology/links/memory-records.json", must_exist=False)
    if not target.exists():
        return {"status": "missing", "source_type": "derived_association", "results": [], "mutated": False}
    data = read_json(target)
    require(isinstance(data, dict) and set(data) == {"schema_version", "kind", "project_id", "source_type", "ontology_context", "records", "associations", "excluded", "authority"}, "invalid_sidecar", "Derived memory links have an unsupported shape.")
    if data.get("kind") != "derived-memory-concept-links" or data.get("project_id") != p.project_id:
        raise OntologyError("invalid_sidecar", "Derived memory links have a different project identity or kind.")
    require(data["schema_version"] == 1 and isinstance(data["ontology_context"], dict)
            and isinstance(data["ontology_context"].get("snapshot_sha256"), str)
            and isinstance(data["records"], list) and isinstance(data["associations"], list)
            and isinstance(data["excluded"], list), "invalid_sidecar", "Derived memory links have incomplete versions or association lists.")
    for r in data["records"]:
        require(isinstance(r, dict) and set(r) == {"record_id", "path", "sha256", "sources"}
                and all(isinstance(r[k], str) for k in ("record_id", "path", "sha256")) and isinstance(r["sources"], list),
                "invalid_sidecar", "A derived memory record version is malformed.")
    for a in data["associations"]:
        require(isinstance(a, dict) and set(a) == {"record_id", "query", "concept_ids", "status"}
                and isinstance(a["concept_ids"], list) and all(isinstance(i, str) for i in a["concept_ids"])
                and a["status"] in {"derived_association", "ambiguous", "unmatched"}, "invalid_sidecar", "A derived association is malformed.")
    ownership_file = safe_path(p.root, ".sys4ai/ontology/manifests/link-memory.json", must_exist=False)
    ownership = read_json(ownership_file) if ownership_file.exists() else {}
    require(isinstance(ownership, dict) and isinstance(ownership.get("outputs", {}), dict), "invalid_manifest", "Memory link ownership manifest is malformed.")
    stale = data["ontology_context"]["snapshot_sha256"] != p.context()["snapshot_sha256"] or ownership.get("outputs", {}).get(".sys4ai/ontology/links/memory-records.json") != sha256(read_bytes(target))
    for r in data["records"]:
        current = _installed(p, "read", path=r["path"])
        stale = stale or current["status"] != "ok" or current.get("record", {}).get("sha256") != r["sha256"] or bool(current.get("record", {}).get("diagnostics"))
    return {"status": "stale" if stale else "current", "source_type": "derived_association",
            "path": ".sys4ai/ontology/links/memory-records.json", "sha256": sha256(read_bytes(target)),
            "results": [] if stale else data["associations"], "records": data["records"], "mutated": False,
            "limitations": ["Stale associations require an explicit link-memory rebuild."] if stale else []}
