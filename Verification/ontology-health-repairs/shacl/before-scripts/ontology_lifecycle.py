"""Candidate lifecycle changes. Only the publication operation accepts canonical edits."""
import copy
from ontology_core import canonical_bytes, sha256, require


def transition(record, state, *, reason, replacement=None):
    require(state in {"draft", "approved", "deprecated"}, "invalid_lifecycle", "Unsupported lifecycle transition.")
    require(isinstance(reason, str) and reason.strip(), "missing_reason", "Lifecycle review requires a reason.")
    require(record.get("lifecycle") != "deprecated" or state == "deprecated", "retired_identity", "Deprecated identities cannot be reactivated or recycled.")
    result = copy.deepcopy(record)
    result.setdefault("history", []).append({"sha256": sha256(canonical_bytes(record)), "definition": record.get("definition", ""), "lifecycle": record.get("lifecycle", "draft"), "reason": reason})
    result["lifecycle"] = state
    if state == "deprecated":
        result["deprecation_reason"] = reason
        if replacement is not None: result["replacement"] = replacement
    else:
        result.pop("deprecation_reason", None); result.pop("replacement", None)
    return result


def validate_transition(old_records, new_records):
    old = {r["@id"]: r for r in old_records}
    new = {r["@id"]: r for r in new_records}
    findings = []
    def add(code, text, rid): findings.append({"code": code, "message": text, "record_id": rid, "path": None, "severity": "error"})
    for rid, previous in old.items():
        if rid not in new:
            add("identity_removed", "Retain old stable identities; deprecate them instead of deleting history.", rid); continue
        current = new[rid]
        if previous == current: continue
        if any(previous.get(k) != current.get(k) for k in ("kind", "module", "@type")):
            add("identity_recycled", "Kind, module and type identity cannot be recycled; create a new ID.", rid)
        if previous.get("lifecycle") == "deprecated" and (current.get("lifecycle") != "deprecated" or current.get("definition") != previous.get("definition")):
            add("retired_identity", "Deprecated identities retain their lifecycle and historical meaning.", rid)
        semantics_changed = any(previous.get(k) != current.get(k) for k in ("definition", "domain", "range", "acyclic", "cardinality", "subject", "predicate", "object", "qualifiers"))
        if previous.get("lifecycle") in {"approved", "deprecated"} and semantics_changed and current.get("lifecycle") != "draft":
            histories = current.get("history", [])
            expected = sha256(canonical_bytes(previous))
            if not any(h.get("sha256") == expected and h.get("definition") == previous.get("definition") and h.get("lifecycle") == previous.get("lifecycle") and h.get("reason") for h in histories if isinstance(h, dict)):
                add("renewed_review_required", "Changed approved semantics require retained previous bytes and a new exact scoped review, or a draft transition.", rid)
        if current.get("history", [])[:len(previous.get("history", []))] != previous.get("history", []):
            add("history_removed", "Previously retained semantic history must remain intact.", rid)
    return sorted(findings, key=lambda f: (f["code"], f["record_id"]))
