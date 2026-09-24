"""Legacy trusted authoring helpers; the browser workbench is retired.

TrustedAuthority, trusted_authority and draft_form retain their existing local
interfaces. Historical workbench assets remain inert compatibility resources.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import copy
import uuid

from ontology_core import (canonical_bytes, sha256, safe_path, read_bytes,
                           read_json, load_project, require, exact, source_status, decode_json)
from ontology_publication import _root
from ontology_proposals import save, open_proposal


def assess_service(root, origin, *, timeout=2):
    """Compatibility result only; no listener or legacy endpoint is contacted."""
    return {"status": "retired", "enabled": False, "running": None,
            "service_state": "retired", "mutated": False,
            "next_operation": "explore --open"}


@dataclass
class TrustedAuthority:
    """Created/refreshed only by a trusted local CLI or agent, outside HTTP input."""
    actor_id: str
    actor_kind: str
    native_receipt: dict
    observed_at: str
    expires_at: str
    scope: tuple
    task: dict | None = None

    def validate(self, root):
        from ontology_authority import validate_native_observation, validate_director_binding, validate_manager_binding, active_managers, within
        validate_native_observation(vars(self))
        project = load_project(root)
        require(project.config["publication"]["enabled"], "publication_disabled", "Current ontology publication is disabled.")
        configured = set(project.config["project_files"] + project.config["binding_files"] + project.config.get("competency_files", []))
        core_selected = set(configured)
        from ontology_advanced import load_advanced
        advanced = load_advanced(root)
        if advanced and advanced.get("publication", {}).get("enabled"):
            configured.add("ontology-advanced.yaml")
            for ref in advanced["extensions"]:
                configured.add(ref["path"])
                configured.update(item["path"] for item in read_json(safe_path(root, ref["path"])).get("shapes", []))
        require(self.scope and set(self.scope) <= configured, "session_scope", "Session authoring scope must name selected canonical project files.")
        if self.actor_kind == "director":
            binding = validate_director_binding(project, self.actor_id)
            require(self.task is None and all(any(within(path, prefix) for prefix in binding["scope"]) for path in self.scope if path in core_selected),
                    "session_scope", "Session exceeds the current Director's bound canonical scope.")
            if set(self.scope) - core_selected:
                advanced_binding = advanced["publication"]["binding"]
                require(advanced_binding["actor_id"] == self.actor_id and all(any(within(path, prefix) for prefix in advanced_binding["scope"]) for path in self.scope if path not in core_selected),
                        "session_scope", "Advanced session scope exceeds its separate current publication binding.")
                for ref in advanced_binding["authority"]:
                    require(sha256(safe_path(root, ref["path"])) == ref["sha256"], "authority_changed", "Advanced session governing authority changed.")
            for _, _, assignment in active_managers(project.root):
                require(not any(within(path, prefix) or within(prefix, path) for path in self.scope for prefix in assignment.get("fit", {}).get("writes", [])),
                        "manager_owns_scope", "An unreconciled active manager owns overlapping session targets.")
        else:
            require(isinstance(self.task, dict) and isinstance(self.task.get("path"), str), "manager_unconfirmed", "A manager session needs its exact confirmed Task.")
            validate_manager_binding(project, self.actor_id, self.task, self.scope)
        return project

    def grant(self, root, current):
        self.validate(root)
        from ontology_authority import review_binding
        proposal = current["revision"]["candidate"]
        require(set(c["path"] for c in proposal["changes"]) <= set(self.scope), "session_scope", "Candidate publication exceeds trusted session scope.")
        config = safe_path(root, "ontology-advanced.yaml", must_exist=False)
        return {"schema_version": 2, "grant_id": "ONTGRANT-workbench-" + uuid.uuid4().hex,
                "project_id": current["revision"]["project_id"], "actor_id": self.actor_id,
                "actor_kind": self.actor_kind, "operation": "publish",
                "payload_sha256": sha256(canonical_bytes(proposal)),
                "preview_sha256": current["validation"]["preview"]["preview_sha256"],
                "config_sha256": sha256(safe_path(root, "ontology.yaml")),
                "advanced_config_sha256": current["validation"]["target_snapshot"].get("advanced_inputs", {}).get("ontology-advanced.yaml", sha256(config) if config.exists() else None),
                "proposal_review": review_binding(current), "scope": [c["path"] for c in proposal["changes"]],
                "native_receipt": copy.deepcopy(self.native_receipt), "observed_at": self.observed_at,
                "expires_at": self.expires_at, "task": copy.deepcopy(self.task),
                "reviewed_records": [{k:c[k] for k in ("path", "sha256", "expected_sha256")} for c in proposal["changes"]]}


def trusted_authority(root, *, actor_id, actor_kind, native_receipt, observed_at, scope, task=None):
    observed = datetime.fromisoformat(observed_at.replace("Z", "+00:00"))
    value = TrustedAuthority(actor_id, actor_kind, copy.deepcopy(native_receipt), observed_at,
                             (observed + timedelta(minutes=5)).isoformat(), tuple(scope), copy.deepcopy(task))
    value.validate(_root(root))
    return value


def _source(project, reference):
    exact(reference, ("path", "locator"), ("sha256",))
    permitted = set(project.config["source_allowlist"])
    for module in project.modules:
        permitted.update(module["path"] + "/" + name for name in module["files"])
    require(reference["path"] in permitted, "source_unselected", "Only a selected ontology source can be opened.")
    path = safe_path(project.root, reference["path"])
    raw = read_bytes(path, max_bytes=250000)
    ref = {"path": reference["path"], "sha256": reference.get("sha256", sha256(raw)), "locator": reference["locator"]}
    require(source_status(project, ref)["status"] == "current", "source_not_current", "Source evidence changed; choose its current version.")
    return ref


def draft_form(root, form, *, expected_target_sha256, proposal_id=None, expected_revision=None, scope):
    """The form edits supported fields; it has no actor, file, grant or executable input."""
    root = _root(root)
    project = load_project(root)
    exact(form, ("id", "kind", "label", "definition", "types", "aliases", "sources", "reason"),
          ("scope_note", "lifecycle", "replacement", "deprecation_reason", "domain", "range", "acyclic", "cardinality",
           "qualifier_schema", "qualifiers", "subject", "predicate", "object", "entity", "binding_type"))
    kind = form["kind"]
    require(kind in {"concept", "instance", "predicate", "relation", "binding"}, "unsupported_kind", "Choose a supported ontology record kind.")
    rid = form["id"]
    require(isinstance(rid, str) and rid.startswith(project.namespace), "core_redefinition", "Imported identities are protected. Use a distinct project identity.")
    canonical = project.by_id.get(rid)
    selected_path = project.locations[rid].split("#")[0] if canonical else project.config["binding_files" if kind == "binding" else "project_files"][0]
    require(selected_path in scope, "session_scope", "This record is outside the trusted authoring scope.")
    actual = sha256(safe_path(root, selected_path))
    require(actual == expected_target_sha256, "target_conflict", "Canonical content changed. Your entered draft is preserved; reopen its current target before saving.")
    candidate = None
    if proposal_id:
        existing = open_proposal(root, proposal_id)
        require(existing["head"]["revision"] == expected_revision, "draft_conflict", "A newer saved draft exists. Your form input is preserved.")
        candidate = copy.deepcopy(existing["revision"]["candidate"])
        require(all(c["path"] in scope for c in candidate["changes"]), "session_scope", "Saved candidate exceeds trusted authoring scope.")
    if candidate is None:
        candidate = {"schema_version": 1, "operation_id": "ONTOP-" + uuid.uuid4().hex,
                     "operation": "publish", "reason": form["reason"], "changes": []}
    # Every revision is a new unaccepted operation; only recovery reuses an accepted operation ID.
    candidate["operation_id"] = "ONTOP-" + uuid.uuid4().hex
    candidate["reason"] = form["reason"]
    change = next((c for c in candidate["changes"] if c["path"] == selected_path), None)
    document = decode_json(change["content"].encode()) if change else read_json(safe_path(root, selected_path))
    previous = next((r for r in document["@graph"] if r["@id"] == rid), None)
    record = copy.deepcopy(previous or {})
    record.update({"@id": rid, "@type": form["types"], "kind": kind, "label": form["label"],
                   "definition": form["definition"], "aliases": form["aliases"], "module": "project",
                   "fact_kind": "asserted", "lifecycle": form.get("lifecycle", "approved"),
                   "sources": [_source(project, source) for source in form["sources"]]})
    allowed = {"scope_note"}
    if kind == "predicate":
        allowed.update(("domain", "range", "acyclic", "cardinality"))
        record["qualifiers"] = form.get("qualifier_schema", {})
    elif kind == "relation":
        allowed.update(("subject", "predicate", "object", "qualifiers"))
    elif kind == "binding":
        allowed.update(("entity", "binding_type"))
    for key in allowed:
        if key in form and form[key] not in (None, ""):
            record[key] = form[key]
    # No ID recycling or silent destruction.  History always links the previous canonical meaning.
    if canonical:
        require(canonical["kind"] == kind and canonical["@type"] == record["@type"], "identity_recycled", "Existing identity kind and types are protected; create a distinct identity.")
        require(canonical.get("lifecycle") != "deprecated" or record["definition"] == canonical["definition"] and record["lifecycle"] == "deprecated",
                "retired_identity", "Deprecated identities retain their historical meaning.")
        if record != canonical:
            from ontology_lifecycle import transition
            history = transition(canonical, record["lifecycle"], reason=form["reason"], replacement=form.get("replacement"))
            record["history"] = history["history"]
    if record["lifecycle"] == "deprecated":
        record["deprecation_reason"] = form.get("deprecation_reason") or form["reason"]
        if form.get("replacement"):
            record["replacement"] = form["replacement"]
    else:
        record.pop("deprecation_reason", None)
        record.pop("replacement", None)
    document["@graph"] = [record if r["@id"] == rid else r for r in document["@graph"]]
    if previous is None:
        document["@graph"].append(record)
    raw = canonical_bytes(document)
    from ontology_core import parse_document
    parse_document(raw, project.config["context"]["path"], selected_path)
    new_change = {"path": selected_path, "expected_sha256": actual, "content": raw.decode(), "sha256": sha256(raw)}
    candidate["changes"] = [new_change if c["path"] == selected_path else c for c in candidate["changes"]]
    if change is None:
        candidate["changes"].append(new_change)
    return save(root, candidate, proposal_id=proposal_id, expected_revision=expected_revision,
                rationale=form["reason"], evidence=record["sources"], uncertainty=[],
                generator={"kind": "human_form", "runtime_invoked": False})


class Workbench:
    """Retained import name; an old caller cannot start an authoring listener."""
    def __init__(self, root, authority=None, *, host="127.0.0.1", port=None):
        require(False, "workbench_retired",
                "The browser workbench is retired. Use explore --open for the read-only Explorer; use trusted proposal commands for authoring.")
