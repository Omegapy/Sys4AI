"""Version-1 project memory contracts and strictly read-only inspection."""
from __future__ import annotations

import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

from memory_paths import (MemoryError, require, relative_path, project_root,
                          safe_path, safe_read_bytes, corpus_allowed)

SCHEMA_VERSION = 1
RECORD_TYPES = {"decision", "finding", "experiment", "lesson", "handoff"}
STATES = {"draft", "active", "superseded", "retracted"}
CLAIM_LEVELS = {"accepted_design", "performed_work", "verified_outcome", "observed_failure", "cancelled_work", "historical_context"}
STATE_PATHS = {name: ".sys4ai/memory/" + leaf for name, leaf in {
    "projection": "projection", "normalized": "normalized", "index": "index",
    "model_cache": "model-cache", "backend_config": "backend-config", "maintenance": "maintenance"}.items()}
DEFAULT_EXCLUSIONS = ["Projects/**", "Tasks/**", "Roles/**", "roles/**", "sub-agent-roles/**",
                      "**/*-depo/**", "reference-assets/**", ".git/**", ".venv*/**", "venv/**",
                      ".sys4ai/**", ".agents/**", ".codex/**", "node_modules/**", "build/**", "dist/**",
                      "target/**", "**/__pycache__/**", "**/.env*", "**/secrets/**", "**/credentials/**",
                      "**/*.pem", "**/*.key"]


def sha256(raw):
    return hashlib.sha256(raw.encode("utf-8") if isinstance(raw, str) else raw).hexdigest()


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n").encode("utf-8")


def exact(value, required, optional=()):
    require(isinstance(value, dict), "invalid_shape", "Expected an object.")
    require(all(isinstance(key, str) for key in value), "invalid_fields", "Object keys must be strings.")
    require(set(required) <= set(value) and set(value) <= set(required) | set(optional),
            "invalid_fields", "Required fields are missing or unknown fields are present.",
            {"missing": sorted(set(required) - set(value)), "unknown": sorted(set(value) - set(required) - set(optional))})


def text(value, *, nullable=False):
    if value is None and nullable:
        return
    require(isinstance(value, str) and value.strip() and len(value) <= 20000 and
            not re.search(r"\b(?:TODO|TBD|CHANGEME|REPLACE_ME)\b|\{\{[^}]+\}\}", value),
            "invalid_value", "Expected resolved nonempty text.")


def strings(value, *, nonempty=False):
    require(isinstance(value, list) and len(value) <= 200 and (value or not nonempty),
            "invalid_value", "Expected a bounded text list.")
    for item in value:
        text(item)


def enum(value, choices, code, message):
    require(isinstance(value, str) and value in choices, code, message)


def digest(value, *, nullable=False):
    require((nullable and value is None) or (isinstance(value, str) and re.fullmatch(r"[a-f0-9]{64}", value)),
            "invalid_digest", "Expected a lowercase SHA256 digest.")


def timestamp(value):
    text(value)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise MemoryError("invalid_time", "Expected an ISO8601 timestamp with timezone.") from exc
    require(parsed.tzinfo is not None and "T" in value, "invalid_time", "Timestamp must include a timezone.")
    return parsed


def decode_json_yaml(raw):
    """The supported YAML subset is exactly JSON, including duplicate rejection."""
    def pairs(items):
        obj = {}
        for key, value in items:
            require(key not in obj, "duplicate_key", "Duplicate object key rejected.")
            obj[key] = value
        return obj
    def constant(_):
        raise MemoryError("unsupported_yaml", "Non-finite JSON numbers are unsupported.")
    require(isinstance(raw, (str, bytes, bytearray)), "invalid_encoding", "Document input must be UTF-8 text or bytes.")
    try:
        value = json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise MemoryError("unsupported_yaml", "Use a JSON object, the supported JSON-compatible YAML subset; general YAML syntax is unsupported.") from exc
    require(isinstance(value, dict), "invalid_shape", "Document must contain one object.")
    return value


_SENSITIVE = [
    ("credential", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|\b(?:sk-(?:proj-)?[A-Za-z0-9_-]{16,}|gh[pousr]_[A-Za-z0-9]{20,}|AKIA[A-Z0-9]{16})\b")),
    ("credential_assignment", re.compile(r"(?im)\b(?:api[_ -]?key|access[_ -]?token|client[_ -]?secret|password|authorization)\s*[:=]\s*[\"']?(?!null\b|none\b|redacted\b|\[REDACTED\]|\$\{|<)[A-Za-z0-9/+_=-]{8,}")),
    ("personal_identifier", re.compile(r"\b\d{3}-\d{2}-\d{4}\b|(?i:credit.card)\s*[:=]\s*\d[\d -]{11,}")),
    ("hidden_reasoning", re.compile(r"(?is)<(?:analysis|think|thinking)>|(?:^|\n)\s*(?:private chain.of.thought|hidden reasoning)\s*:")),
    ("transcript", re.compile(r"(?is)(?:^|\n)\s*(?:user|assistant|system)\s*:\s*.{1,2000}(?:\n\s*(?:user|assistant|system)\s*:){1}")),
]


def sensitive_findings(value):
    return [{"code": "sensitive_content", "category": name} for name, pattern in _SENSITIVE if pattern.search(value)]


def reject_sensitive(value):
    findings = sensitive_findings(value)
    require(not findings, "sensitive_content", "Content is excluded from memory; sensitive text is not echoed.", {"findings": findings})


def default_config(project_id=None, name=None):
    return {"schema_version": 1, "project": {"id": project_id, "name": name, "root": "."},
            "canonical_root": "MEMORY", "contract_root": "reference-assets/MEMORY-depo",
            "backend": {"name": "basic-memory", "enabled": False, "semantic_enabled": False},
            "retrieval": {"mode": "lexical", "max_results": 20},
            "corpus": {"include": ["README.md", "docs/**/*.md", "research/**/*.md", "research/**/*.tex", "research/**/*.pdf", "research/**/*.html"],
                       "exclude": list(DEFAULT_EXCLUSIONS), "source_groups": []},
            "state": dict(STATE_PATHS), "integration": {"task_packets": True, "automatic_capture": False},
            "publication": {"director": None}}


def validate_config(value, allow_template=False):
    exact(value, ("schema_version", "project", "canonical_root", "contract_root", "backend", "retrieval", "corpus", "state", "integration", "publication"))
    require(type(value["schema_version"]) is int and value["schema_version"] == 1, "unsupported_schema", "Only configuration schema 1 is supported; no automatic migration.")
    identity = value["project"]
    exact(identity, ("id", "name", "root"))
    if allow_template and identity["id"] is None and identity["name"] is None:
        pass
    else:
        require(isinstance(identity["id"], str) and len(identity["id"]) <= 100 and re.fullmatch(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*", identity["id"]), "project_uninitialized", "Project identity must be specialized before use.")
        text(identity["name"])
    require(identity["root"] == "." and value["canonical_root"] == "MEMORY" and
            value["contract_root"] == "reference-assets/MEMORY-depo", "invalid_config_path", "Version 1 uses fixed project-relative canonical and contract paths.")
    backend = value["backend"]
    exact(backend, ("name", "enabled", "semantic_enabled"))
    require(backend["name"] == "basic-memory" and type(backend["enabled"]) is bool and
            type(backend["semantic_enabled"]) is bool and (not backend["semantic_enabled"] or backend["enabled"]),
            "unsupported_backend", "Unsupported or inconsistent local backend configuration.")
    exact(value["retrieval"], ("mode", "max_results"))
    require(isinstance(value["retrieval"]["mode"], str) and value["retrieval"]["mode"] in {"lexical", "auto", "hybrid"} and
            type(value["retrieval"]["max_results"]) is int and 1 <= value["retrieval"]["max_results"] <= 200,
            "invalid_retrieval", "Retrieval mode or result limit is invalid.")
    corpus = value["corpus"]
    exact(corpus, ("include", "exclude", "source_groups"))
    strings(corpus["include"], nonempty=True); strings(corpus["exclude"])
    for pattern in corpus["include"] + corpus["exclude"]:
        relative_path(pattern)
        require("**" not in pattern.replace("/**/", "/").removeprefix("**/").removesuffix("/**"), "invalid_glob", "Recursive ** must occupy a whole path segment.")
    allowed_roots = ("README.md", "docs/", "research/")
    require(all(p == "README.md" or p.startswith(allowed_roots[1:]) for p in corpus["include"]), "invalid_corpus", "Version 1 permits only README, docs, and research source profiles.")
    require(isinstance(corpus["source_groups"], list) and len(corpus["source_groups"]) <= 200, "invalid_groups", "Expected bounded source groups.")
    seen_ids, seen_paths = set(), set()
    for group in corpus["source_groups"]:
        exact(group, ("id", "paths", "evidence")); text(group["id"]); strings(group["paths"], nonempty=True)
        require(group["id"] not in seen_ids and len(group["paths"]) >= 2, "invalid_groups", "Source group must have unique identity and at least two paths.")
        seen_ids.add(group["id"])
        for path in group["paths"]:
            require(corpus_allowed(path, value) and path not in seen_paths, "invalid_groups", "Grouped sources must be permitted and assigned only once.")
            seen_paths.add(path)
        exact(group["evidence"], ("path", "sha256")); digest(group["evidence"]["sha256"])
        require(corpus_allowed(group["evidence"]["path"], value), "invalid_groups", "Relationship evidence must be an allowed source.")
    require(value["state"] == STATE_PATHS, "invalid_state_paths", "Version 1 state classes have fixed confined paths.")
    exact(value["integration"], ("task_packets", "automatic_capture"))
    require(type(value["integration"]["task_packets"]) is bool and value["integration"]["automatic_capture"] is False,
            "invalid_integration", "Automatic capture is unsupported.")
    exact(value["publication"], ("director",))
    director = value["publication"]["director"]
    if director is not None:
        exact(director, ("actor_id", "scope", "authority")); text(director["actor_id"]); strings(director["scope"], nonempty=True)
        require(re.fullmatch(r"/(?:[A-Za-z0-9_-]+/)*[A-Za-z0-9_-]+", director["actor_id"]), "invalid_actor", "Expected native actor ID.")
        require(isinstance(director["authority"], list) and len(director["authority"]) >= 3, "authority_absent", "Director binding needs current governing source references.")
        for ref in director["authority"]:
            exact(ref, ("path", "sha256")); relative_path(ref["path"]); digest(ref["sha256"])
        require({"SOUL.md", "AGENTS.md", "ROLE.md"} <= {ref["path"] for ref in director["authority"]}, "authority_absent", "Director binding must name root SOUL, AGENTS and ROLE.")
        for path in director["scope"]:
            relative_path(path)
            require(path in {"MEMORY", "Verification", "control_records", ".sys4ai/memory"} or path.startswith(("MEMORY/", ".sys4ai/memory/", "Verification/", "control_records/")), "invalid_scope", "Publisher scope must be an explicit memory or evidence path.")
    return value


def load_config(root, optional=False, allow_template=False):
    root = project_root(root)
    candidate = safe_path(root, "memory.yaml", must_exist=False)
    if not candidate.exists():
        require(optional, "config_absent", "Project memory configuration is absent.")
        return None
    return validate_config(decode_json_yaml(safe_read_bytes(root, "memory.yaml", max_bytes=250000)), allow_template=allow_template)


def parse_record(value):
    if isinstance(value, bytes):
        try:
            value = value.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise MemoryError("invalid_encoding", "Records must use UTF-8.") from exc
    require(isinstance(value, str) and len(value.encode("utf-8")) <= 250000 and value.startswith("---\n"), "invalid_record", "Record must have bounded JSON-compatible YAML frontmatter.")
    parts = value.split("\n---\n", 1)
    require(len(parts) == 2, "invalid_record", "Frontmatter closing delimiter is absent.")
    return {"metadata": decode_json_yaml(parts[0][4:]), "body": parts[1]}


def validate_record(record, project_id=None):
    exact(record, ("metadata", "body"), ("path", "sha256", "diagnostics"))
    meta = record["metadata"]
    exact(meta, ("schema_version", "id", "project_id", "type", "title", "state", "created", "modified", "claim", "applicability", "limitations", "confidence", "sources", "origin", "lifecycle", "publication"))
    require(type(meta["schema_version"]) is int and meta["schema_version"] == 1, "unsupported_schema", "Only record schema 1 is supported; no automatic migration.")
    require(isinstance(meta["id"], str) and re.fullmatch(r"MEM-[0-9]{8}-[A-F0-9]{8}", meta["id"]), "invalid_id", "Expected a stable MEM-YYYYMMDD-XXXXXXXX record ID.")
    try:
        datetime.strptime(meta["id"][4:12], "%Y%m%d")
    except ValueError as exc:
        raise MemoryError("invalid_id", "Record ID date is invalid.") from exc
    require(isinstance(meta["project_id"], str) and len(meta["project_id"]) <= 100 and re.fullmatch(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*", meta["project_id"]), "invalid_project", "Invalid owning project ID.")
    require(project_id is None or meta["project_id"] == project_id, "project_mismatch", "Record belongs to a different project.")
    enum(meta["type"], RECORD_TYPES, "invalid_record_kind", "Unsupported record type.")
    enum(meta["state"], STATES, "invalid_record_kind", "Unsupported lifecycle state.")
    text(meta["title"]); text(record["body"])
    require(timestamp(meta["created"]) <= timestamp(meta["modified"]), "invalid_chronology", "Modification precedes creation.")
    exact(meta["claim"], ("level", "summary")); text(meta["claim"]["summary"])
    enum(meta["claim"]["level"], CLAIM_LEVELS, "invalid_claim", "Unsupported evidence claim level.")
    enum(meta["confidence"], {"low", "medium", "high"}, "invalid_confidence", "Confidence must be low, medium, or high.")
    strings(meta["applicability"], nonempty=True); strings(meta["limitations"])
    require(isinstance(meta["sources"], list) and 1 <= len(meta["sources"]) <= 200, "evidence_absent", "Records require bounded cited evidence.")
    for ref in meta["sources"]:
        exact(ref, ("path", "sha256", "locator", "kind")); relative_path(ref["path"]); digest(ref["sha256"]); text(ref["locator"])
        enum(ref["kind"], {"source", "design", "verification"}, "invalid_evidence", "Unsupported source kind.")
    origin = meta["origin"]
    exact(origin, ("task_id", "task_path", "execution_id", "generation", "role"))
    require((origin["task_id"] is None) == (origin["task_path"] is None), "invalid_origin", "Task ID and path must both be present or null.")
    if origin["task_id"] is not None:
        text(origin["task_id"])
        require(re.fullmatch(r"TASK-[0-9]{8}-[A-F0-9]{8}", origin["task_id"]), "invalid_origin", "Malformed Task origin ID.")
        relative_path(origin["task_path"])
        require(origin["task_path"].startswith("Tasks/") and origin["task_path"].endswith("/task.json"), "invalid_origin", "Task origin must point to canonical task.json.")
    require((origin["execution_id"] is None) == (origin["generation"] is None), "invalid_origin", "Execution ID and generation must both be present or null.")
    if origin["execution_id"] is not None:
        text(origin["execution_id"])
        require(origin["task_id"] is not None and type(origin["generation"]) is int and origin["generation"] > 0, "invalid_origin", "Execution origin requires a real Task and positive generation.")
    if origin["role"] is not None:
        role = origin["role"]
        exact(role, ("name", "agents_path", "role_path", "agents_sha256", "role_sha256")); text(role["name"])
        require(re.fullmatch(r"[a-z0-9][a-z0-9-]*", role["name"]), "invalid_origin", "Invalid role name.")
        for key, filename in (("agents_path", "AGENTS.md"), ("role_path", "ROLE.md")):
            require(role[key] == f"Roles/{role['name']}/{filename}", "invalid_origin", "Role provenance must identify an exact active Roles pair.")
        digest(role["agents_sha256"]); digest(role["role_sha256"])
    lifecycle = meta["lifecycle"]
    exact(lifecycle, ("supersedes", "superseded_by", "reason")); strings(lifecycle["supersedes"])
    text(lifecycle["superseded_by"], nullable=True)
    for value in lifecycle["supersedes"] + ([lifecycle["superseded_by"]] if lifecycle["superseded_by"] else []):
        require(re.fullmatch(r"MEM-[0-9]{8}-[A-F0-9]{8}", value) and value != meta["id"], "invalid_lifecycle", "Invalid self-referential or malformed lifecycle link.")
    require(len(set(lifecycle["supersedes"])) == len(lifecycle["supersedes"]), "invalid_lifecycle", "Duplicate supersession link.")
    if meta["state"] in {"superseded", "retracted"} or lifecycle["supersedes"]:
        text(lifecycle["reason"])
    else:
        text(lifecycle["reason"], nullable=True)
    require((meta["state"] == "superseded") == (lifecycle["superseded_by"] is not None), "invalid_lifecycle", "Only superseded records identify a replacement.")
    publication = meta["publication"]
    if meta["state"] == "draft":
        require(publication is None, "invalid_publication", "Drafts cannot claim publication.")
    else:
        exact(publication, ("actor_id", "actor_kind", "operation_id", "approved_at"))
        text(publication["actor_id"]); text(publication["operation_id"]); timestamp(publication["approved_at"])
        enum(publication["actor_kind"], {"director", "manager"}, "invalid_publication", "Children cannot be canonical publishers.")
        require(timestamp(meta["created"]) <= timestamp(publication["approved_at"]) <= timestamp(meta["modified"]), "invalid_chronology", "Publication must be inside record chronology.")
    if meta["type"] == "handoff":
        require(meta["claim"]["level"] == "historical_context" and meta["limitations"], "invalid_handoff", "Handoff records require historical context and explicit limits.")
    reject_sensitive(json.dumps(meta, ensure_ascii=False) + "\n" + record["body"])
    return record


def render_record(record):
    validate_record(record)
    return "---\n" + json_bytes(record["metadata"]).decode("utf-8") + "---\n" + record["body"].rstrip() + "\n"


def load_record(root, path, config=None):
    root = project_root(root)
    config = config or load_config(root)
    rel = str(relative_path(str(path)))
    require(rel.startswith("MEMORY/") and rel.endswith(".md") and rel != "MEMORY/README.md", "record_path", "Canonical record must be a Markdown file under MEMORY/.")
    raw = safe_read_bytes(root, rel, max_bytes=250000)
    record = validate_record(parse_record(raw), config["project"]["id"])
    require(Path(rel).name == record["metadata"]["id"] + ".md", "record_identity", "Record filename must equal its stable ID.")
    from memory_evidence import inspect_evidence
    record.update(path=rel, sha256=sha256(raw), diagnostics=inspect_evidence(root, record, config))
    from memory_recovery import pending_transactions
    pending = [operation for operation in pending_transactions(root) if any(change["path"] == rel for change in operation["records"])]
    if pending:
        record["diagnostics"].append({"code": "recovery_required", "severity": "warning", "message": "This record participates in an incomplete canonical transaction.", "operations": [p["operation_id"] for p in pending]})
    return record


inspect_record = load_record


def load_records(root, config=None, historical=False):
    root = project_root(root)
    config = config or load_config(root)
    from memory_recovery import pending_transactions
    pending = pending_transactions(root)
    require(not pending, "recovery_required", "Shared recall is suspended while a canonical transaction needs recovery.", {"pending": pending})
    base = safe_path(root, "MEMORY", must_exist=False, kind="dir")
    if not base.exists():
        return []
    import os
    records, seen = [], set()
    for directory, dirs, files in os.walk(base, followlinks=False):
        for dirname in dirs:
            safe_path(root, (Path(directory) / dirname).relative_to(root).as_posix(), kind="dir")
        for name in sorted(files):
            rel = (Path(directory) / name).relative_to(root).as_posix()
            if rel == "MEMORY/README.md":
                continue
            require(name.endswith(".md"), "unclassified_memory", "Canonical MEMORY contains an unclassified file.", {"path": rel})
            record = load_record(root, rel, config)
            require(record["metadata"]["id"] not in seen, "duplicate_identity", "Duplicate canonical record identity.")
            seen.add(record["metadata"]["id"])
            if historical or record["metadata"]["state"] == "active":
                records.append(record)
    return sorted(records, key=lambda item: item["path"])


def health(root):
    root = project_root(root)
    try:
        config = load_config(root, optional=True)
        if config is None:
            return {"status": "absent", "backend": "unavailable", "records": 0, "read_only": True}
        for relative in ("README.md", "policy.md", "publication-and-recovery.md", "schema/record-v1.json", "schema/config-v1.json"):
            content = safe_read_bytes(root, config["contract_root"] + "/" + relative, max_bytes=250000)
            if relative.endswith(".json"):
                decode_json_yaml(content)
        records = load_records(root, config, historical=True)
        backend = "disabled"
        if config["backend"]["enabled"]:
            from basic_memory_adapter import health as backend_health
            backend = backend_health(root, config)
        return {"status": "ready", "project_id": config["project"]["id"], "records": len(records),
                "backend": backend,
                "read_only": True, "diagnostics": [d for r in records for d in r["diagnostics"]]}
    except MemoryError as exc:
        return {"status": "invalid", "read_only": True, "error": exc.as_dict()}
