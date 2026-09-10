"""Explicit deterministic Markdown generation and navigation validation."""
import hashlib
import posixpath
import re
from pathlib import PurePosixPath
from urllib.parse import quote, unquote

from ontology_core import canonical_bytes, read_bytes, safe_path
from ontology_retrieval import explain, project


def filename(identifier):
    local = re.sub(r"[^A-Za-z0-9_-]", "-", identifier.rsplit(":", 1)[-1])[:60] or "entity"
    return local + "-" + hashlib.sha256(identifier.encode()).hexdigest()[:12] + ".md"


def label(text):
    return text.replace("\\", "\\\\").replace("[", "\\[").replace("]", "\\]").replace("\n", " ")


def link(record):
    return f"[{label(record['label'])}]({filename(record['@id'])})"


def render_wiki(value):
    p = project(value)
    outputs = {}
    header = "> Generated from canonical ontology. Edit the owning canonical record, then run build-wiki explicitly.\n"
    indexes = {"concepts.md": ("Concepts and instances", lambda r: r["kind"] in {"concept", "instance"}),
               "relationships.md": ("Relationships", lambda r: r["kind"] in {"predicate", "relation"}),
               "capabilities.md": ("Capabilities and skills", lambda r: any(t.rsplit(":", 1)[-1] in {"Skill", "Capability"} for t in r["@type"]))}
    intro = ["# Ontology wiki", "", header, f"Project: `{p.project_id}`", "",
             "- [Concepts and instances](concepts.md)", "- [Relationships](relationships.md)",
             "- [Modules](modules.md)", "- [Capabilities and skills](capabilities.md)", "",
             f"Input snapshot: `{p.context()['snapshot_sha256']}`", ""]
    outputs["ONTOLOGY/WIKI/INDEX.md"] = "\n".join(intro).encode()
    for name, (title, predicate) in indexes.items():
        text = ["# " + title, "", header, "[Wiki index](INDEX.md)", ""]
        text.extend("- " + link(r) + f" ({r['kind']}; {r['lifecycle']})" for r in p.records if predicate(r))
        outputs["ONTOLOGY/WIKI/" + name] = ("\n".join(text) + "\n").encode()
    module_text = ["# Modules", "", header, "[Wiki index](INDEX.md)", ""]
    for module in sorted({r["module"] for r in p.records}):
        module_text.extend(["## " + module, ""])
        module_text.extend("- " + link(r) for r in p.records if r["module"] == module)
        module_text.append("")
    outputs["ONTOLOGY/WIKI/modules.md"] = ("\n".join(module_text) + "\n").encode()
    for record in p.records:
        row = explain(p, record)
        text = ["# " + record["label"], "", header, "[Wiki index](INDEX.md)", "",
                f"Stable ID: `{record['@id']}`", "",
                f"Kind: {record['kind']}. Lifecycle: **{record['lifecycle']}**. Fact classification: {record['fact_kind']}.",
                f"Module: {record['module']} {row['module_version'] or '(project-local)'}. Source freshness: {row['freshness']}.", "",
                record["definition"], ""]
        owner = p.locations.get(record["@id"], "")
        owner_path, _, locator = owner.partition("#")
        text.extend([f"Canonical edit location: [{label(owner)}](<../../{quote(owner_path)}>) `{locator}`", ""])
        for field, title in (("aliases", "Aliases"), ("scope_note", "Scope and distinctions"),
                             ("examples", "Examples"), ("non_examples", "Non-examples"),
                             ("deprecation_reason", "Deprecation reason")):
            if record.get(field):
                value = record[field]
                text.extend(["## " + title, "", "\n".join("- " + str(v) for v in value) if isinstance(value, list) else str(value), ""])
        if record.get("replacement"):
            text.extend(["Replacement: " + link(p.by_id[record["replacement"]]), ""])
        text.extend(["## Relationships", ""])
        relations = [record] if record["kind"] == "relation" else row["relationships"]
        for edge in relations:
            text.append("- " + link(p.by_id[edge["subject"]]) + " → " + link(p.by_id[edge["predicate"]]) + " → " +
                        link(p.by_id[edge["object"]]) + f" ({edge['fact_kind']}; {edge['lifecycle']})")
            if edge.get("qualifiers"):
                text.append("  Qualifiers: `" + canonical_bytes(edge["qualifiers"]).decode().strip().replace("\n", " ") + "`")
        text.extend(["", "## Sources", ""])
        for source in row["source_status"]:
            text.append(f"- [{label(source['path'])}](<../../{quote(source['path'])}>) `{source['locator']}` "
                        f"SHA256 `{source['sha256']}` ({source['status']})")
        text.extend(["", "## Backlinks", ""])
        backlinks = [r for r in p.records if r["@id"] != record["@id"] and
                     (r.get("entity") == record["@id"] or r.get("replacement") == record["@id"] or
                      record["@id"] in (r.get("subject"), r.get("object"), r.get("predicate")))]
        text.extend("- " + link(r) for r in backlinks)
        outputs["ONTOLOGY/WIKI/" + filename(record["@id"])] = ("\n".join(text) + "\n").encode()
    return outputs


def validate_links(root, outputs=None):
    if outputs is None:
        folder = safe_path(root, "ONTOLOGY/WIKI", must_exist=False)
        if not folder.exists():
            return {"valid": False, "diagnostics": [{"code": "wiki_missing", "path": "ONTOLOGY/WIKI"}], "mutated": False}
        outputs = {"ONTOLOGY/WIKI/" + f.name: read_bytes(safe_path(root, "ONTOLOGY/WIKI/" + f.name))
                   for f in sorted(folder.iterdir()) if f.suffix == ".md"}
    diagnostics = []
    for path, raw in sorted(outputs.items()):
        for match in re.finditer(r"\]\((?:<([^>]+)>|([^\s)]+))\)", raw.decode("utf-8")):
            target = unquote(match.group(1) or match.group(2)).split("#", 1)[0]
            if not target:
                continue
            resolved = posixpath.normpath(str(PurePosixPath(path).parent / target))
            if resolved.startswith("ONTOLOGY/WIKI/"):
                exists = resolved in outputs
            else:
                exists = safe_path(root, resolved, must_exist=False).is_file()
            if not exists:
                diagnostics.append({"code": "wiki_broken_link", "path": path, "target": target})
    return {"valid": not diagnostics, "diagnostics": diagnostics, "mutated": False}


def build_wiki(value):
    from ontology_build import write_generated
    from ontology_core import OntologyError
    p = project(value)
    outputs = render_wiki(p)
    check = validate_links(p.root, outputs)
    if not check["valid"]:
        raise OntologyError("wiki_broken_link", str(check["diagnostics"]))
    return write_generated(p, outputs, operation="build-wiki")
