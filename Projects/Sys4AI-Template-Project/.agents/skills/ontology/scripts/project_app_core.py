"""Independent project identity, reviewed Home content and closed read dispatch."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import hmac
import json
from pathlib import Path
import re
import secrets

from project_app_sources import AppError, document_allowed, json_bytes, plain, read_bytes, sha

OPERATIONS = ("context", "home", "work", "task", "search", "source", "health", "help", "memory", "knowledge")
STATUSES = ("ready", "partial", "unavailable", "disabled", "error")
NAVIGATION = [
    {"id": "home", "label": "Home", "description": "Understand this project and find a place to start."},
    {"id": "work", "label": "Work", "description": "Read recorded Tasks, requirements, plans and evidence."},
    {"id": "knowledge", "label": "Project knowledge", "description": "Explore terms, processes and their documented relationships."},
    {"id": "health", "label": "Health and setup", "description": "See available capabilities and setup guidance."},
    {"id": "help", "label": "Tools and help", "description": "Find installed skills, valid roles and reading instructions."},
]


def validate_response(value):
    if not isinstance(value, dict) or value.get("schema_version") != 1 or value.get("status") not in STATUSES:
        return False
    if value.get("project_id") is not None and not isinstance(value["project_id"], str):
        return False
    if not isinstance(value.get("observed_at"), str) or not isinstance(value.get("issues"), list):
        return False
    if value.get("operation") not in (*OPERATIONS, None):
        return False
    try:
        return len(json.dumps(value, ensure_ascii=False, allow_nan=False).encode()) <= 65536
    except (TypeError, ValueError, RecursionError):
        return False


class ProjectReader:
    def __init__(self, root, package=None):
        selected = Path(root).absolute()
        if any(path.is_symlink() for path in (selected, *selected.parents)) or not selected.is_dir():
            raise AppError("identity_unavailable")
        self.root = selected.resolve(strict=True)
        root_stat = self.root.stat()
        self.root_identity = (root_stat.st_dev, root_stat.st_ino)
        self.package = package
        self.package_root = Path(package.scripts).parent if hasattr(package, "scripts") else Path(package or Path(__file__).parent.parent)
        self.handles = {}
        self.secret = secrets.token_bytes(32)
        self.identity = self._identity()
        self.project_id = self.identity.get("id")

    def _identity(self):
        try:
            try:
                value = json_bytes(read_bytes(self.root, "project.json", 32000))
                if not isinstance(value, dict):
                    raise AppError("identity_unavailable")
                identifier, name = value.get("project_id"), value.get("project_name")
            except AppError:
                if (self.root / "project.json").exists() or (self.root / "project.json").is_symlink():
                    raise
                registry = json_bytes(read_bytes(self.root, "depot/projects.json", 64000))
                rows = [r for r in registry.get("projects", []) if isinstance(r, dict) and r.get("path") == "." and r.get("kind") == "depot-manager" and r.get("registered") is True]
                if len(rows) != 1:
                    raise AppError("identity_unavailable")
                value = rows[0]
                identifier, name = value.get("id"), value.get("name")
            if not isinstance(identifier, str) or not re.fullmatch(r"[a-z][a-z0-9-]{0,79}", identifier) or not isinstance(name, str) or not name.strip():
                raise AppError("identity_unavailable")
            return {"id": identifier, "name": plain(name, 160), "root": str(self.root)}
        except (AppError, AttributeError, TypeError):
            return {"id": None, "name": "Project setup needed", "root": str(self.root)}

    def config(self):
        value = json_bytes(read_bytes(self.root, "project-app.json", 65536))
        if not isinstance(value, dict) or set(value) != {"schema_version", "project_id", "home", "documents", "start_here"} or value["schema_version"] != 1:
            raise AppError("invalid_content")
        if value["project_id"] not in (None, self.project_id):
            raise AppError("identity_mismatch")
        docs, home = value["documents"], value["home"]
        if not isinstance(docs, list) or len(docs) > 24 or not isinstance(home, dict) or set(home) != {"purpose", "scope", "audience", "sections"}:
            raise AppError("invalid_content")
        seen = set()
        for item in docs:
            if not isinstance(item, dict) or set(item) != {"title", "path"} or not isinstance(item["title"], str) or not 1 <= len(item["title"]) <= 160 or not document_allowed(item["path"]) or item["path"] in seen:
                raise AppError("invalid_content")
            seen.add(item["path"])
        if not isinstance(home["sections"], list) or len(home["sections"]) > 6:
            raise AppError("invalid_content")
        for section in [home[k] for k in ("purpose", "scope", "audience")] + home["sections"]:
            if not isinstance(section, dict) or not {"text", "sources", "reviewed_sha256", "reviewed_at"} <= section.keys() or not section.keys() <= {"text", "sources", "reviewed_sha256", "reviewed_at", "title"}:
                raise AppError("invalid_content")
            if not isinstance(section["text"], str) or len(section["text"]) > 3000 or not isinstance(section["sources"], list) or len(section["sources"]) > 6:
                raise AppError("invalid_content")
            for ref in section["sources"]:
                if not isinstance(ref, dict) or set(ref) != {"path", "sha256"} or not document_allowed(ref["path"]) or not isinstance(ref["sha256"], str) or not re.fullmatch(r"[0-9a-f]{64}", ref["sha256"]):
                    raise AppError("invalid_content")
        start = value["start_here"]
        if start is not None and (not isinstance(start, dict) or set(start) != {"label", "path"} or not isinstance(start["label"], str) or not 1 <= len(start["label"]) <= 160 or start["path"] not in seen):
            raise AppError("invalid_content")
        return value

    def reference(self, owner, identifier, title, **metadata):
        key = hmac.new(self.secret, (owner + ":" + identifier).encode(), hashlib.sha256).hexdigest()[:40]
        if len(self.handles) >= 1000 and key not in self.handles:
            raise AppError("resource_limit")
        self.handles[key] = {"owner": owner, "id": identifier, **metadata}
        return {"source_id": key, "owner": owner, "title": plain(title, 160), "observed_at": datetime.now(timezone.utc).isoformat(), **{k: metadata.get(k) for k in ("path", "sha256", "status")}}

    def documents(self, config):
        output = []
        for row in config["documents"]:
            try:
                raw = read_bytes(self.root, row["path"])
                raw.decode("utf-8")
                output.append(self.reference("documents", row["path"], row["title"], path=row["path"], sha256=sha(raw), status="ready"))
            except (AppError, UnicodeError):
                output.append({"title": plain(row["title"], 160), "path": row["path"], "source_id": None, "sha256": None, "status": "unavailable"})
        return output

    def home(self):
        from project_app_work import catalog
        from project_app_capabilities import capabilities
        config = self.config()
        docs = self.documents(config)
        by_path = {row["path"]: row for row in docs}
        issues = []
        def section(row):
            refs = [by_path.get(r["path"]) for r in row["sources"]]
            status = "reviewed"
            text = plain(row["text"], 3000)
            if not text or not refs or row["reviewed_sha256"] != sha(row["text"].encode()):
                status, text = "not_recorded", "Not recorded. Review and save this section in project-app.json."
            elif any(ref is None or ref["status"] != "ready" for ref in refs):
                status, text = "withheld", "Supporting source access is unavailable; this section is withheld."
            elif any(ref["sha256"] != expected["sha256"] for ref, expected in zip(refs, row["sources"])):
                status = "review_needed"
            if status != "reviewed":
                issues.append(status)
            return {"text": text, "status": status, "sources": [{**r, "recorded_sha256": expected["sha256"]} for r, expected in zip(refs, row["sources"]) if r is not None and r["status"] == "ready"], "reviewed_at": row["reviewed_at"], "reviewed_sha256": row["reviewed_sha256"], **({"title": plain(row["title"], 160)} if "title" in row else {})}
        content = {key: section(config["home"][key]) for key in ("purpose", "scope", "audience")}
        content["sections"] = [section(row) for row in config["home"]["sections"]]
        start = config["start_here"]
        content["start_here"] = {"label": plain(start["label"], 160), "source_id": by_path[start["path"]]["source_id"]} if start else None
        content["documents"] = docs
        return {"status": "partial" if issues else "ready", "identity": self.identity, "content": content,
                "review": {"state": "review_needed" if issues else "reviewed", "issues": sorted(set(issues))},
                "work": catalog(self, home=True), "capabilities": capabilities(self)}

    def read(self, operation, params=None):
        params = {} if params is None else params
        result = {"schema_version": 1, "operation": operation if operation in OPERATIONS else None, "project_id": self.project_id, "observed_at": datetime.now(timezone.utc).isoformat(), "issues": []}
        try:
            if operation not in OPERATIONS or not isinstance(params, dict) or len(json.dumps(params).encode()) > 8192:
                raise AppError("invalid_request")
            root_stat = self.root.stat()
            if self._identity() != self.identity or (root_stat.st_dev, root_stat.st_ino) != self.root_identity:
                self.handles.clear()
                raise AppError("identity_changed")
            if self.project_id is None:
                raise AppError("identity_unavailable")
            permission_paths = ("project-app.json", "memory.yaml", "ontology.yaml")
            def permissions():
                values = []
                for path in permission_paths:
                    try:
                        values.append(sha(read_bytes(self.root, path, 65536)))
                    except AppError:
                        values.append(None)
                return values
            before_permissions = permissions()
            if operation == "context":
                from project_app_capabilities import capabilities
                data = {"status": "ready", "identity": self.identity, "navigation": NAVIGATION, "capabilities": capabilities(self)}
            elif operation == "home":
                data = self.home()
            elif operation in ("work", "task"):
                from project_app_work import catalog, detail
                data = catalog(self) if operation == "work" else detail(self, params.get("id"))
            elif operation == "search":
                from project_app_search import search
                data = search(self, params.get("query"))
            elif operation == "source":
                from project_app_sources import source
                data = source(self, params.get("source_id"))
            elif operation in ("memory", "knowledge"):
                from project_app_knowledge import memory, knowledge
                data = memory(self, params) if operation == "memory" else knowledge(self, params)
            elif operation in ("health", "help"):
                from project_app_capabilities import health, help_view
                data = health(self) if operation == "health" else help_view(self)
            if before_permissions != permissions():
                raise AppError("permissions_changed")
            result.update(data)
        except (AppError, OSError, UnicodeError, TypeError, KeyError, AttributeError, ValueError) as exc:
            code = exc.code if isinstance(exc, AppError) else "invalid_content"
            result.update(status="unavailable", issues=[code], guidance="Review the selected project's setup or this source's owning capability, then refresh.")
        if not validate_response(result):
            result = {"schema_version": 1, "operation": operation if operation in OPERATIONS else None, "project_id": self.project_id, "observed_at": result["observed_at"], "status": "partial", "issues": ["response_limit"], "guidance": "This view exceeds the reading limit. Use a narrower search or open one record."}
        return result

    @staticmethod
    def validate_response(value):
        return validate_response(value)
