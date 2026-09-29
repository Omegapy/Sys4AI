"""Static capability availability and supported installed help metadata."""
from __future__ import annotations

import re

from project_app_sources import AppError, json_bytes, plain, read_bytes
from project_app_work import compatibility, owner_read
from project_app_knowledge import configured


def capabilities(reader):
    rows = []
    for owner, label in (("task", "Tasks"), ("trd", "Requirements"), ("plan", "Implementation plans"), ("memory", "Lessons and decisions"), ("roles", "Project roles"), ("curate", "Curator notices")):
        try:
            compatibility(reader, owner)
            state = "installed"
        except AppError as exc:
            state = "incompatible" if exc.code == "owner_incompatible" else "unavailable"
        if owner == "memory" and state == "installed":
            state = configured(reader, "memory")
        rows.append({"id": owner, "label": label, "status": state, "checked": "static",
                     "effect": "This installed owner can provide bounded reading." if state in ("installed", "configured") else "This optional view is unavailable; other pages remain usable.",
                     "recovery": "Open this view to read its current state." if state in ("installed", "configured") else "Review the project's selected installation and configuration through its existing owner."})
    state = configured(reader, "knowledge")
    rows.append({"id": "knowledge", "label": "Project knowledge", "status": state, "checked": "static", "effect": "Knowledge is checked when opened.", "recovery": "Open Project knowledge or review ontology.yaml through its owner."})
    return rows


def health(reader):
    notices = []
    try:
        config = json_bytes(read_bytes(reader.root, "curator.yaml", 65536))
        if config.get("project", {}).get("id") != reader.project_id or config.get("project", {}).get("coordination_root") not in (None, str(reader.root), "."):
            raise AppError("owner_identity_mismatch")
        value = owner_read(reader, "curate", "status")
        for item in value.get("awareness", {}).get("notices", [])[:10]:
            notices.append({"id": plain(item.get("id", ""), 160), "level": plain(item.get("level", "information"), 80),
                            "impact": plain(item.get("impact", ""), 2000), "action": plain(item.get("action", ""), 1500)})
        if value.get("pending_assessment"):
            notices.append({"id": "curator-pending", "level": "information", "impact": "The existing Curator delivery queue has not been assessed for this repository.", "action": "Use the Curator owner when session maintenance is needed. Browsing does not run it."})
    except (AppError, AttributeError):
        notices.append({"id": "curator-unavailable", "level": "information", "impact": "Existing Curator notices are unavailable.", "action": "Review the Curator owner and configuration if this capability is needed."})
    for path in ("control_records/project-setup.json", "control_records/project-app-adoption.json"):
        try:
            value = json_bytes(read_bytes(reader.root, path, 262144))
            for item in value.get("warnings", [])[:5]:
                if isinstance(item, str):
                    notices.append({"id": "setup", "level": "information", "impact": plain(item, 1500), "action": "Review the existing project setup receipt through the initializer owner."})
        except (AppError, AttributeError):
            pass
    return {"status": "ready", "capabilities": capabilities(reader), "notices": notices,
            "guidance": "Availability is a static inspection. No runtime assessment, maintenance, repair or service startup was requested."}


def help_view(reader):
    def extract(text, names):
        match = re.search(r"^#{1,3} (?:" + names + r")\s*\n(.*?)(?=\n#{1,3} |\Z)", text, re.M | re.S | re.I)
        return plain(match[1].strip(), 300) if match else "Read the installed definition for the applicable requirements."
    def usage(text):
        return {"inputs": extract(text, "Expected inputs|Inputs|Required inputs"), "outputs": extract(text, "Expected outputs|Outputs|Output contract"),
                "limits": extract(text, "Authority limits|Boundaries|Scope|Scope and authority|Non-goals")}
    skills = []
    path = reader.root / ".agents/skills"
    if path.is_dir() and not path.is_symlink():
        for directory in sorted(path.iterdir())[:60]:
            if directory.is_symlink() or not directory.is_dir():
                continue
            rel = ".agents/skills/" + directory.name + "/SKILL.md"
            try:
                text = read_bytes(reader.root, rel, 100000).decode("utf-8")
                if not text.startswith("---\n"):
                    continue
                metadata = text.split("---", 2)[1]
                fields = {}
                for line in metadata.splitlines():
                    if ":" in line:
                        k, v = line.split(":", 1)
                        if k in ("name", "description"):
                            fields[k] = plain(v.strip().strip('"\''), 1500)
                if fields.get("name") and fields.get("description"):
                    skills.append({**fields, "path": rel, **usage(text)})
            except (AppError, UnicodeError):
                continue
    roles, issues = [], []
    try:
        value = owner_read(reader, "roles", "list")
        for row in value.get("valid_roles", [])[:30]:
            try:
                text = read_bytes(reader.root, row["role_file"], 100000).decode("utf-8")
            except (AppError, UnicodeError):
                continue
            roles.append({"name": plain(row.get("name", ""), 160), "description": plain(row.get("description", ""), 1500), "path": plain(row.get("role_file", ""), 500),
                          "agents_path": plain(row.get("agents_file", ""), 500), "sha256": row.get("role_sha256"), "activity": "Not checked. An installed role does not identify a running agent.", **usage(text)})
        if value.get("invalid_roles"):
            issues.append("Some role bundles are invalid and are omitted from usable roles.")
    except AppError:
        issues.append("The supported role catalog is unavailable.")
    instructions = [
        {"title": "Start reading", "text": "Use Home to understand this project. Start here opens a selected document; Search finds permitted document, work and knowledge matches."},
        {"title": "Read work", "text": "Work shows recorded state. Requirements approval, plan progress, Task completion and release evidence have separate owners."},
        {"title": "Use sources", "text": "Open a source to inspect its current permitted text. Copy reference copies a logical reference; it does not run a command."},
        {"title": "Close reading", "text": "Closing this tab leaves the service running. Close reading session revokes this session. Stop app stops this project's owned service."},
        {"title": "Use installed tools", "text": "A skill describes work an agent can perform. A role describes a permitted assignment. Read the installed file and provide explicit instructions before starting work."},
    ]
    return {"status": "partial" if issues else "ready", "skills": skills, "roles": roles, "instructions": instructions, "issues": issues}
