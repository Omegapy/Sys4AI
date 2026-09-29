"""Fixed, hash-compatible read-only owning interfaces and public Work fields."""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import selectors
import signal
import subprocess
import sys
import tempfile
import time

from project_app_sources import AppError, json_bytes, plain, read_bytes, sha

IDENTIFIER = re.compile(r"(?:TASK|TRD|PLAN)-\d{8}-[A-Fa-f0-9]{8}")
OWNER = {"TASK": "task", "TRD": "trd", "PLAN": "plan"}

# All executing owner bytes are copied after exact closure verification. Audit
# checks also cover the memory owner's explicit installed Task/role imports.
RUNNER = r'''
import hashlib,json,os,runpy,sys,resource
packet=json.loads(sys.argv[1]); root=packet['root']; files=packet['files']; entry=packet['entry']; mirror=packet['mirror']
sys.dont_write_bytecode=True
resource.setrlimit(resource.RLIMIT_CPU,(4,4))
try: resource.setrlimit(resource.RLIMIT_AS,(536870912,536870912))
except (ValueError,OSError): pass
trusted={}
for rel,digest in files.items():
    trusted[os.path.join(root,rel)]=digest
    trusted[os.path.join(mirror,rel)]=digest
stdlib=os.path.realpath(os.path.dirname(os.__file__))
def audit(event,args):
    if event == 'open':
        path,mode,flags=args
        if isinstance(path,(str,bytes)):
            path=os.fsdecode(path)
            if (isinstance(mode,str) and any(c in mode for c in 'wax+')) or (isinstance(flags,int) and flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)):
                raise PermissionError('read_only')
            if path.endswith('.pyc') and not os.path.realpath(path).startswith(stdlib+os.sep):
                raise PermissionError('unreviewed_bytecode')
    if event == 'compile' and len(args)>1:
        body,path=args[:2]
        if isinstance(path,str) and path in trusted:
            raw=body.encode() if isinstance(body,str) else body
            if hashlib.sha256(raw).hexdigest()!=trusted[path]: raise PermissionError('owner_changed')
    if event == 'exec':
        path=args[0].co_filename
        if not path.startswith('<') and path not in trusted and not os.path.realpath(path).startswith(stdlib+os.sep):
            raise PermissionError('unreviewed_code')
    if event.startswith(('socket.','subprocess.')) or event in ('os.system','os.remove','os.rename','os.mkdir','os.rmdir','os.chmod','os.link','os.symlink','os.truncate'):
        raise PermissionError('read_only')
sys.addaudithook(audit)
sys.path.insert(0,os.path.dirname(entry))
sys.argv=[entry]+packet['argv']
runpy.run_path(entry,run_name='__main__')
'''


def compatibility(reader, owner):
    manifest = json_bytes(read_bytes(reader.package_root, "assets/project-app/owner-compatibility.json", 262144))
    row = manifest["owners"].get(owner)
    if row is None:
        raise AppError("owner_unavailable")
    bodies = {}
    # Memory evidence can call exactly these owner validators. Include them in
    # the reviewed closure without authorizing their mutation entry points.
    names = (owner, "task", "roles") if owner == "memory" else (owner,)
    for name in names:
        for path, digest in manifest["owners"][name]["files"].items():
            try:
                body = read_bytes(reader.root, path, 2000000)
            except AppError:
                if name != owner and not (reader.root / path).exists():
                    continue
                raise AppError("owner_unavailable") from None
            if sha(body) != digest:
                raise AppError("owner_incompatible")
            bodies[path] = body
    return row, bodies


def owner_read(reader, owner, operation, value=None):
    row, bodies = compatibility(reader, owner)
    if operation not in row["commands"]:
        raise AppError("owner_operation_unavailable")
    if owner in ("task", "trd", "plan"):
        if operation in ("show", "continue") and (not isinstance(value, str) or not IDENTIFIER.fullmatch(value) or OWNER.get(value.split("-")[0]) != owner):
            raise AppError("invalid_request")
        argv = ["--project-root", str(reader.root), operation]
        if operation in ("show", "continue"):
            argv.append(value)
        if operation == "status":
            argv += ["--limit", "5"]
    elif owner == "roles":
        argv = ["--repo-root", str(reader.root), "list", "--format", "json"]
    elif owner == "curate":
        argv = ["status", "--policy", str(reader.root / "curator.yaml")]
    elif owner == "memory":
        if operation == "search":
            if not isinstance(value, str) or not value.strip() or len(value) > 300:
                raise AppError("invalid_request")
            argv = ["--project-root", str(reader.root), "search", value, "--mode", "lexical", "--limit", "15"]
        else:
            if not isinstance(value, str) or not re.fullmatch(r"MEMORY/(?:[A-Za-z0-9_-]+/)*[A-Za-z0-9_-]+\.md", value):
                raise AppError("source_unavailable")
            argv = ["--project-root", str(reader.root), "read", value]
    else:
        raise AppError("owner_unavailable")
    with tempfile.TemporaryDirectory(prefix="sys4ai-app-owner-") as folder:
        mirror = Path(folder)
        for path, body in bodies.items():
            destination = mirror / path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(body)
        packet = {"root": str(reader.root), "mirror": str(mirror), "entry": str(mirror / row["entry"]), "files": {p: sha(b) for p, b in bodies.items()}, "argv": argv}
        proc = subprocess.Popen([sys.executable, "-I", "-S", "-B", "-c", RUNNER, json.dumps(packet)], cwd=mirror,
                                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, start_new_session=True,
                                env={"PATH": "/usr/bin:/bin", "LANG": "en_US.UTF-8"})
        output = bytearray()
        deadline = time.monotonic() + 5
        try:
            with selectors.DefaultSelector() as selector:
                selector.register(proc.stdout, selectors.EVENT_READ)
                while selector.get_map():
                    if time.monotonic() >= deadline:
                        raise AppError("owner_timeout")
                    for key, _ in selector.select(min(.1, max(0, deadline-time.monotonic()))):
                        chunk = os.read(key.fd, 65536)
                        if not chunk:
                            selector.unregister(key.fileobj)
                            break
                        output.extend(chunk)
                        if len(output) > 2000000:
                            raise AppError("owner_output_limit")
            proc.wait(timeout=max(.01, deadline-time.monotonic()))
        except subprocess.TimeoutExpired:
            raise AppError("owner_timeout") from None
        finally:
            if proc.poll() is None:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.wait()
            proc.stdout.close()
        if not output:
            raise AppError("owner_unavailable")
        result = json_bytes(bytes(output))
        if not isinstance(result, dict) or result.get("mutated") is True or result.get("mutation") is True:
            raise AppError("owner_unavailable")
        if result.get("status") in ("error", "invalid") or result.get("ok") is False or result.get("error"):
            raise AppError("owner_unavailable")
        if result.get("project_id") not in (None, reader.project_id) or result.get("project_root") not in (None, str(reader.root)):
            raise AppError("owner_identity_mismatch")
        # A concurrent replacement revokes the entire returned response.
        compatibility(reader, owner)
        return result


def public_source(reader, owner, identifier, title, **kwargs):
    return reader.reference(owner, identifier, title, **kwargs)


def catalog(reader, home=False):
    items, owners = [], []
    for owner in (("task",) if home else ("task", "trd", "plan")):
        try:
            value = owner_read(reader, owner, "status" if home else "list")
            rows = value.get("nonterminal_candidates" if home else "tasks", []) if owner == "task" else value.get("documents", []) if owner == "trd" else value.get("data", {}).get("plans", [])
            if not isinstance(rows, list):
                raise AppError("owner_unavailable")
            owners.append({"owner": owner, "status": "partial" if value.get("warnings") or value.get("errors") or len(rows) > 40 else "ready", "coverage": "bounded", "guidance": "Inspect this owner for complete catalog and integrity details."})
            for row in rows[:5 if home else 40]:
                identifier = row.get({"task": "task_id", "trd": "trd_id", "plan": "plan_id"}[owner])
                if not isinstance(identifier, str) or not IDENTIFIER.fullmatch(identifier):
                    continue
                title = plain(row.get("name", row.get("title", identifier)), 180)
                path = row.get("path") if owner == "trd" else ("Implementation_Plans/" + row["directory"] + "/plan.json") if owner == "plan" and isinstance(row.get("directory"), str) else None
                items.append({"id": identifier, "type": owner, "title": title, "status": plain(row.get("status"), 80),
                              "summary": plain(row.get("description", ""), 1200), "next_step": plain(row.get("next_step", ""), 1000),
                              "revision": row.get("revision"), "updated_at": plain(row.get("updated_at", ""), 80),
                              "source": public_source(reader, owner, identifier, title, path=path, sha256=row.get("sha256"), status="ready")})
        except AppError as exc:
            owners.append({"owner": owner, "status": "unavailable", "reason": exc.code, "guidance": "Review or install the supported owning capability, then refresh."})
    return {"status": "partial" if any(o["status"] != "ready" for o in owners) else "ready", "items": items, "owners": owners,
            "coverage": "At most 40 records per owner; unavailable catalogs are not empty catalogs."}


def strings(value, limit=20):
    return [plain(v, 1200) for v in value[:limit] if isinstance(v, str)] if isinstance(value, list) else []


def work_document(path):
    from project_app_sources import relative
    try:
        parts = relative(path)
    except AppError:
        return False
    return Path(path).suffix.lower() in (".md", ".txt", ".rst") and not any(p.startswith(".") or p.casefold() in ("projects", "tasks", "memory", "roles", "secrets", "credentials", "node_modules") for p in parts) and not re.search(r"(?i)(native|private|candidate|solver|billboard|collaboration|orchestration|transcript)", path)


def task_document(reader, identifier, path):
    value = owner_read(reader, "task", "continue", identifier).get("continuation", {})
    if path not in value.get("relevant_files", []) or not work_document(path):
        raise AppError("source_unavailable")
    raw = read_bytes(reader.root, path)
    return raw


def detail(reader, identifier):
    if not isinstance(identifier, str) or not IDENTIFIER.fullmatch(identifier):
        raise AppError("invalid_request")
    owner = OWNER[identifier.split("-")[0]]
    result = owner_read(reader, owner, "continue" if owner == "task" else "show", identifier)
    value = result.get("continuation", {}) if owner == "task" else result.get("document", {}) if owner == "trd" else result.get("data", {}).get("canonical", {})
    title = plain(value.get("title", value.get("name", identifier)), 180)
    path = value.get("canonical_state_path", value.get("path"))
    digest = value.get("sha256")
    if owner == "plan":
        path = result.get("plan", {}).get("canonical_path")
        digest = result.get("plan", {}).get("sha256")
    if isinstance(path, str) and path.startswith(str(reader.root) + "/"):
        path = path[len(str(reader.root)) + 1:]
    if owner == "task" and isinstance(path, str):
        try:
            raw = read_bytes(reader.root, path, 2000000)
            canonical = json_bytes(raw)
            if canonical.get("task_id") != identifier or canonical.get("revision") != value.get("revision"):
                raise AppError("source_changed")
            digest = sha(raw)
        except AppError:
            raise AppError("source_changed") from None
    source = public_source(reader, owner, identifier, title, path=path, sha256=digest, status="ready")
    links = []
    relevant = strings(value.get("relevant_files", []), 30)
    # Only explicit stable IDs are linked, never names or inferred similarity.
    refs = relevant + [plain(r.get("external_id", r.get("path", "")), 500) for r in value.get("sources", []) if isinstance(r, dict)]
    for ref in refs:
        for linked in IDENTIFIER.findall(ref):
            if linked != identifier and not any(x["id"] == linked for x in links):
                links.append({"id": linked, "label": linked, "relationship": "explicit reference"})
    if owner == "task":
        for rel in relevant[:15]:
            if not work_document(rel):
                continue
            try:
                raw = read_bytes(reader.root, rel)
                raw.decode("utf-8")
                ref = reader.reference("work-artifact", identifier + ":" + rel, rel, task_id=identifier, path=rel, sha256=sha(raw), status="ready")
                links.append({"label": rel, "path": rel, "relationship": "explicit artifact", "source": ref, "source_id": ref["source_id"]})
            except (AppError, UnicodeError):
                links.append({"label": rel, "path": rel, "relationship": "explicit artifact", "status": "unavailable"})
    item = {"id": identifier, "type": owner, "title": title, "status": plain(value.get("status"), 80),
            "objective": plain(value.get("description", value.get("objective", "")), 4000),
            "summary": plain(value.get("current_summary", result.get("body", "")), 10000),
            "next_step": plain(value.get("next_step", ""), 2000), "blockers": strings(value.get("blockers", [])),
            "criteria": strings(value.get("definition_of_done", [])), "links": links, "evidence": [],
            "revision": value.get("revision"), "source": source,
            "distinctions": {"requirements_approval": "Recorded separately by the TRD owner.", "plan_state": "Recorded separately by the plan owner.",
                             "task_completion": "Only the Task lifecycle records Task completion.", "assignments": "Not an observation of current agent activity.",
                             "agent_activity": "Not checked.", "release": "Not recorded unless explicit evidence is shown."}}
    if owner == "task":
        shown = owner_read(reader, owner, "show", identifier).get("task", {})
        if shown.get("revision") != value.get("revision"):
            raise AppError("source_changed")
        if isinstance(path, str) and sha(read_bytes(reader.root, path, 2000000)) != digest:
            raise AppError("source_changed")
        item["title"] = plain(shown.get("name", identifier), 180)
        latest_metadata = shown.get("last_response")
        if isinstance(latest_metadata, dict):
            history = {"coverage": "Latest Task response metadata only. Earlier responses and historical document bytes are not returned by this route."}
            for key in ("response_id", "created_at", "supersedes_response_id"):
                field = latest_metadata.get(key)
                if isinstance(field, str):
                    history[key] = plain(field, 160)
                elif field is None:
                    history[key] = None
            if type(latest_metadata.get("sequence")) is int and 0 <= latest_metadata["sequence"] <= 2**53 - 1:
                history["sequence"] = latest_metadata["sequence"]
            if isinstance(latest_metadata.get("path"), str):
                history["recorded_path"] = plain(latest_metadata["path"], 500)
            item["history"] = [history]
        else:
            item["history"] = ["The supported Task show route returned no latest response metadata. Earlier response history is unavailable through this route."]
        for row in shown.get("completion_evidence", [])[:20]:
            if isinstance(row, dict):
                item["evidence"].append({k: plain(row[k], 2000) for k in ("criterion", "evidence", "result", "verification") if isinstance(row.get(k), str)})
        latest = value.get("latest_response_path")
        canonical = value.get("canonical_state_path")
        if isinstance(latest, str) and isinstance(canonical, str):
            try:
                response_path = Path(latest)
                if response_path.parent != Path(canonical).parent / "responses" or not response_path.name.startswith("Task-Response-") or response_path.suffix != ".md":
                    raise AppError("source_unavailable")
                response = read_bytes(reader.root, response_path.relative_to(reader.root).as_posix(), 262144).decode("utf-8")
                match = re.search(r"^## Verification and evidence\n(.*?)(?=\n## |\Z)", response, re.M | re.S)
                if match:
                    item["evidence"].append({"description": "Latest recorded Task verification and evidence", "result": plain(match[1].strip(), 5000), "source": source})
            except (AppError, ValueError, UnicodeError):
                item["evidence"].append({"description": "Latest recorded evidence is unavailable."})
    if owner == "plan":
        objective = value.get("objective", {})
        item["objective"] = plain(objective.get("summary", ""), 4000) if isinstance(objective, dict) else plain(objective, 4000)
        item["criteria"] = strings(objective.get("success_outcomes", [])) if isinstance(objective, dict) else []
        item["evidence"] = [{k: plain(row[k], 1000) for k in ("description", "result", "source", "locator", "verification_level") if isinstance(row.get(k), str)} for task in value.get("tasks", [])[:40] if isinstance(task, dict) for row in task.get("evidence", [])[:4] if isinstance(row, dict)][:20]
        item["decisions"] = [{"id": plain(row.get("decision_id", ""), 80), "status": plain(row.get("status", ""), 80), "text": plain(row.get("statement", ""), 1500)} for row in value.get("decisions", [])[:12] if isinstance(row, dict)]
        item["history"] = [{"coverage": "Latest up to 12 entries from the current canonical plan history. Earlier entries may be omitted; historical document bytes are not loaded."}]
        history = value.get("history")
        if isinstance(history, list):
            for row in history[-12:]:
                if not isinstance(row, dict):
                    continue
                entry = {}
                for key, limit in (("action_id", 120), ("timestamp", 80), ("status_before", 80), ("status_after", 80), ("summary", 1500)):
                    field = row.get(key)
                    if isinstance(field, str):
                        entry[key] = plain(field, limit)
                    elif field is None and key in ("status_before", "status_after"):
                        entry[key] = None
                if type(row.get("revision")) is int and 0 <= row["revision"] <= 2**53 - 1:
                    entry["revision"] = row["revision"]
                if entry:
                    item["history"].append(entry)
        if len(item["history"]) == 1:
            item["history"].append("No history entries were returned by the supported plan show route.")
    if owner == "trd":
        item["history"] = ["History is unavailable through the supported TRD show route. The current document revision and source hash are shown above."]
    return {"status": "ready", "item": item}
