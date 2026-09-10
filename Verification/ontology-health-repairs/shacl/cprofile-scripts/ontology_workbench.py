"""Project-scoped loopback workbench with trusted in-memory sessions and no browser grants."""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import copy
import json
import secrets
import threading
import time
import uuid
from urllib.parse import urlsplit

from ontology_core import (OntologyError, CORE, canonical_bytes, sha256, safe_path, read_bytes,
                           read_json, load_project, require, exact, source_status, decode_json)
from ontology_publication import _root
from ontology_proposals import save, list_proposals, open_proposal, decide

ASSETS = Path(__file__).resolve().parents[1] / "workbench"
CSP = "default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'"


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
    def __init__(self, root, authority=None, *, host="127.0.0.1", port=None):
        self.root = _root(root)
        require(host == "127.0.0.1", "workbench_host", "Workbench supports loopback only; remote deployment is a separate operation.")
        self.project = load_project(self.root)
        from ontology_advanced import load_advanced
        cfg = load_advanced(self.root)
        profile = cfg["profiles"].get("workbench", {"enabled": False}) if cfg else {"enabled": False}
        require(profile.get("enabled"), "workbench_disabled", "Enable the selected local workbench profile before starting its service.")
        self.session_seconds = profile.get("session_seconds", 900)
        self.max_request_bytes = profile.get("max_request_bytes", 1000000)
        self.authority = authority
        if authority:
            authority.validate(self.root)
        self.scope = tuple(authority.scope) if authority else ()
        self.sessions, self.bootstrap = {}, {}
        self.mutex = threading.RLock()
        service = self

        class Handler(BaseHTTPRequestHandler):
            server_version = "Sys4AIWorkbench"
            sys_version = ""

            def log_message(self, format, *args):
                pass  # Session bootstrap and source data never enter an access log.

            def _headers(self, code, content_type, length, cookie=None):
                self.send_response(code)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(length))
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Security-Policy", CSP)
                self.send_header("X-Content-Type-Options", "nosniff")
                self.send_header("Referrer-Policy", "no-referrer")
                self.send_header("Cross-Origin-Resource-Policy", "same-origin")
                if cookie:
                    self.send_header("Set-Cookie", cookie)
                self.end_headers()

            def _json(self, code, data, cookie=None):
                raw = canonical_bytes(data)
                self._headers(code, "application/json; charset=utf-8", len(raw), cookie)
                self.wfile.write(raw)

            def _origin(self, *, mutation=False):
                require(self.headers.get("Host") == service.host_header, "host_forbidden", "This request does not name the selected local service.")
                origin = self.headers.get("Origin")
                require((not mutation and origin is None) or origin == service.origin, "origin_forbidden", "Only this workbench's local origin may call its endpoints.")
                require(self.headers.get("Sec-Fetch-Site") not in {"cross-site"}, "origin_forbidden", "Cross-site requests are forbidden.")

            def do_GET(self):
                try:
                    self._origin()
                    selected = urlsplit(self.path)
                    require(not selected.query and selected.path in {"/", "/index.html", "/app.js", "/editor.js", "/review.js", "/advanced.js", "/styles.css"}, "resource_forbidden", "Select an available local workbench resource.")
                    name = "index.html" if selected.path == "/" else selected.path[1:]
                    path = ASSETS / name
                    require(path.is_file() and not path.is_symlink(), "resource_forbidden", "Workbench asset unavailable.")
                    raw = read_bytes(path)
                    mime = "text/html" if name.endswith(".html") else "text/css" if name.endswith(".css") else "text/javascript"
                    self._headers(200, mime + "; charset=utf-8", len(raw))
                    self.wfile.write(raw)
                except OntologyError as exc:
                    self._json(403, {"status": "rejected", "error": exc.as_dict()})

            def do_POST(self):
                try:
                    self._origin(mutation=True)
                    require(self.headers.get("Content-Type", "").split(";")[0] == "application/json", "content_type", "Workbench endpoints require JSON data.")
                    length = self.headers.get("Content-Length", "")
                    require(length.isdigit() and 0 < int(length) <= service.max_request_bytes, "request_size", "Request body is missing or exceeds the selected budget.")
                    body = decode_json(self.rfile.read(int(length)))
                    require(isinstance(body, dict), "invalid_request", "Expected an endpoint request object.")
                    require(not any(k in body for k in ("actor", "actor_id", "actor_kind", "grant", "native_receipt", "project_root", "scope")),
                            "browser_authority", "Browser requests cannot supply actor authority, grants or project scope.")
                    if self.path == "/api/session":
                        exact(body, ("bootstrap",))
                        with service.mutex:
                            token = body["bootstrap"]
                            require(isinstance(token, str) and token in service.bootstrap and service.bootstrap[token] >= time.monotonic(), "session_expired", "Open a current trusted bootstrap link.")
                            del service.bootstrap[token]
                            existing = SimpleCookie()
                            existing.load(self.headers.get("Cookie", ""))
                            current = existing.get(service.cookie_name)
                            sid = current.value if current else None
                            session = service.sessions.get(sid)
                            if not session or session["expires"] < time.monotonic():
                                sid = secrets.token_urlsafe(32)
                                session = {"csrf": secrets.token_urlsafe(32), "expires": time.monotonic() + service.session_seconds}
                                service.sessions[sid] = session
                            csrf = session["csrf"]
                        self._json(200, {"status": "connected", "csrf": csrf}, service.cookie_name + "=" + sid + "; HttpOnly; SameSite=Strict; Path=/")
                        return
                    cookie = SimpleCookie()
                    cookie.load(self.headers.get("Cookie", ""))
                    sid = cookie.get(service.cookie_name)
                    session = service.sessions.get(sid.value if sid else "")
                    require(session and session["expires"] >= time.monotonic(), "session_expired", "Session expired. Saved proposals remain available after trusted reconnect.")
                    csrf = self.headers.get("X-Ontology-CSRF", "")
                    require(isinstance(csrf, str) and secrets.compare_digest(csrf, session["csrf"]), "csrf_forbidden", "A current same-session request token is required.")
                    result = service.dispatch(self.path, body)
                    self._json(200, result)
                except OntologyError as exc:
                    code = 409 if exc.code in {"draft_conflict", "target_conflict", "stale_review", "expected_changed", "write_conflict", "operation_locked"} else 403 if exc.code in {"host_forbidden", "origin_forbidden", "csrf_forbidden", "session_expired", "browser_authority", "session_scope", "publication_unavailable", "grant_expired"} else 422
                    self._json(code, {"status": "conflict" if code == 409 else "unavailable" if code == 403 else "invalid", "error": exc.as_dict(), "draft_preserved": True})
                except (OSError, ValueError, TypeError, KeyError) as exc:
                    self._json(422, {"status": "invalid", "error": {"code": "request_failed", "message": str(exc)[:500]}, "draft_preserved": True})

            def do_OPTIONS(self):
                self._json(403, {"status": "rejected", "error": {"code": "origin_forbidden", "message": "Cross-origin access is unsupported."}})

        self.server = ThreadingHTTPServer((host, profile.get("port", 0) if port is None else port), Handler)
        self.server.daemon_threads = True
        self.server.timeout = 1
        # Browser cookies are host-scoped, not port-scoped. Concurrent local
        # services must not overwrite each other's session identifiers.
        self.cookie_name = "sys4ai_ontology_session_" + str(self.server.server_port)
        self.origin = f"http://127.0.0.1:{self.server.server_port}"
        self.host_header = f"127.0.0.1:{self.server.server_port}"
        self.thread = None

    def bootstrap_url(self):
        token = secrets.token_urlsafe(32)
        with self.mutex:
            self.bootstrap[token] = time.monotonic() + 60
        return self.origin + "/#bootstrap=" + token

    def start(self):
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        return self

    def close(self):
        if self.thread:
            self.server.shutdown()
            self.thread.join(timeout=5)
        self.server.server_close()
        self.sessions.clear()
        self.bootstrap.clear()

    def _authoring(self):
        require(self.authority is not None, "publication_unavailable", "This is a browsing session. Trusted local authority is required for authoring.")
        self.authority.validate(self.root)

    def dispatch(self, endpoint, body):
        project = load_project(self.root)
        if endpoint == "/api/state":
            exact(body, ())
            from ontology_standards import health
            from ontology_proposals import list_rdf_imports
            return {"status": "ready", "project": project.config["project"], "context": project.context(),
                    "readiness": health(self.root), "authoring": bool(self.authority),
                    "scope": list(self.scope), "targets": [{"path": p, "sha256": sha256(safe_path(self.root, p))} for p in self.scope],
                    "source_choices": project.config["source_allowlist"], "proposals": list_proposals(self.root),
                    "rdf_imports": [{k:item[k] for k in ("import_id", "disposition", "diagnostics", "proposal_id")} for item in list_rdf_imports(self.root)],
                    "authority_boundary": "Trusted local session; current native authority and exact review are rechecked at publication."}
        if endpoint == "/api/records":
            exact(body, (), ("query", "module", "kind", "type", "lifecycle", "fact_kind", "limit"))
            limit = body.get("limit", 100)
            require(type(limit) is int and 1 <= limit <= 100, "invalid_limit", "Choose one to one hundred records.")
            query = body.get("query", "").casefold().strip()
            rows = []
            for record in project.records:
                terms = [record["@id"], record.get("label", ""), *record.get("aliases", [])]
                if query and not any(query in term.casefold() for term in terms):
                    continue
                if any(body.get(key) and record.get(key) != body[key] for key in ("module", "kind", "lifecycle", "fact_kind")):
                    continue
                if body.get("type") and body["type"] not in record["@type"]:
                    continue
                location = project.locations[record["@id"]].split("#")[0]
                rows.append({**record, "location": location, "editable": location in self.scope,
                             "classification": "imported assertion" if record["@id"].startswith(CORE) else record["fact_kind"],
                             "target_sha256": sha256(safe_path(self.root, location))})
            return {"status": "complete", "records": rows[:limit], "truncated": len(rows) > limit,
                    "filters": {"modules": sorted({r["module"] for r in project.records}), "types": sorted({t for r in project.records for t in r["@type"]})}}
        if endpoint == "/api/inspect":
            exact(body, ("id",))
            require(body["id"] in project.by_id, "unknown_identity", "Selected identity is unavailable.")
            from ontology_graph import neighbors
            from ontology_retrieval import explain
            record = project.by_id[body["id"]]
            related = [r for r in project.relations if record["@id"] in (r["subject"], r["object"])]
            row = explain(project, record)
            location = project.locations[record["@id"]].split("#")[0]
            row.update(location=location, editable=location in self.scope, target_sha256=sha256(safe_path(self.root, location)))
            return {"status": "complete", "record": row, "graph": neighbors(project, record["@id"], hops=1, limit=50),
                    "relations": related[:50], "truncated": len(related) > 50}
        if endpoint == "/api/source":
            exact(body, ("reference",))
            ref = _source(project, body["reference"])
            return {"status": "current", "reference": ref, "text": read_bytes(safe_path(self.root, ref["path"]), max_bytes=250000).decode("utf-8")}
        if endpoint == "/api/proposal":
            exact(body, ("id",), ("revision",))
            return open_proposal(self.root, body["id"], revision=body.get("revision"))
        if endpoint == "/api/draft":
            exact(body, ("form", "expected_target_sha256"), ("proposal_id", "expected_revision"))
            self._authoring()
            return draft_form(self.root, body["form"], expected_target_sha256=body["expected_target_sha256"],
                              proposal_id=body.get("proposal_id"), expected_revision=body.get("expected_revision"), scope=self.scope)
        if endpoint == "/api/validate":
            exact(body, ("id", "revision"))
            self._authoring()
            from ontology_proposal_validation import validate_candidate
            return validate_candidate(self.root, body["id"], expected_revision=body["revision"])
        if endpoint == "/api/decide":
            exact(body, ("id", "revision", "decision", "reason"), ("validation_sha256", "superseded_by"))
            self._authoring()
            return decide(self.root, body["id"], expected_revision=body["revision"], decision=body["decision"], reason=body["reason"],
                          validation_sha256=body.get("validation_sha256"), superseded_by=body.get("superseded_by"))
        if endpoint == "/api/publish":
            exact(body, ("id", "revision", "review_sha256"))
            self._authoring()
            current = open_proposal(self.root, body["id"])
            from ontology_proposal_validation import publish_revision
            return publish_revision(self.root, body["id"], self.authority.grant(self.root, current), expected_revision=body["revision"], expected_review_sha256=body["review_sha256"])
        if endpoint == "/api/recover":
            exact(body, ("id", "revision"))
            self._authoring()
            current = open_proposal(self.root, body["id"])
            require(current["head"]["revision"] == body["revision"] and current["head"]["state"] == "partial", "stale_review", "Select the current partially committed operation.")
            from ontology_publication import recover
            from ontology_proposals import _event
            receipt = recover(self.root, current["revision"]["candidate"]["operation_id"], self.authority.grant(self.root, current))
            reopened = [{"path": c["path"], "actual_sha256": sha256(safe_path(self.root, c["path"])),
                         "matches_candidate": sha256(safe_path(self.root, c["path"])) == c["sha256"]} for c in current["revision"]["candidate"]["changes"]]
            complete = receipt.get("status") == "complete" and all(item["matches_candidate"] for item in reopened)
            result = _event(self.root, body["id"], body["revision"], "published" if complete else "partial", {"receipt": receipt, "reopened": reopened})
            return {"status": "published" if complete else "partial", "receipt": receipt, "reopened": reopened, "proposal": result}
        if endpoint == "/api/advanced":
            exact(body, ("operation",), ("query", "graphs", "goals"))
            import ontology_standards as standards
            require(body["operation"] in {"query", "infer", "validate", "health"}, "unsupported_operation", "Select a supported read-only advanced operation.")
            if body["operation"] == "query":
                return standards.query(self.root, body.get("query", ""), graphs=body.get("graphs"))
            if body["operation"] == "infer":
                return standards.infer(self.root, goals=body.get("goals"))
            if body["operation"] == "validate":
                return standards.validate(self.root, graphs=body.get("graphs"))
            return standards.health(self.root)
        if endpoint == "/api/generate":
            exact(body, ("sources", "context_ids", "instruction"), ("previous_request", "findings", "proposal_id"))
            self._authoring()
            from ontology_generation import prepare
            # Browsers prepare requests; only a trusted current native invocation captures results.
            return prepare(self.root, sources=[_source(project, s) for s in body["sources"]],
                           context_ids=body["context_ids"], instruction=body["instruction"],
                           runtime={"kind": "native_agent", "tool": "native-current-agent",
                                    "settings": {"model": None, "reasoning_effort": None, "observed": False},
                                    "authorization": "Trusted local workbench request; current native agent must confirm permitted runtime before invocation."},
                           previous_request=body.get("previous_request"), findings=body.get("findings"), proposal_id=body.get("proposal_id"))
        if endpoint == "/api/import":
            exact(body, ("source", "format", "reason"), ("manifest", "target_extension"))
            self._authoring()
            reference = _source(project, body["source"])
            if body.get("target_extension"):
                # Browser session scopes contain core target files only; advanced imports remain staged.
                require(body["target_extension"] in self.scope, "session_scope", "Extension conversion requires separately scoped trusted authoring authority.")
            from ontology_standards import stage_import
            from ontology_proposals import stage_rdf_import
            staged = stage_import(self.root, read_bytes(safe_path(self.root, reference["path"])).decode("utf-8"), body["format"], manifest=body.get("manifest"))
            if not staged.get("complete"):
                return staged
            return stage_rdf_import(self.root, staged, reference, body["reason"], body.get("target_extension"))
        if endpoint == "/api/rdf-import":
            exact(body, ("id",))
            from ontology_proposals import read_rdf_import
            return read_rdf_import(self.root, body["id"])
        require(False, "resource_forbidden", "This workbench endpoint is unavailable.")
