"""A disposable Basic Memory representation; canonical bytes never round-trip."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from memory_paths import MemoryError, corpus_allowed, require, safe_path, safe_read_bytes

VERSION = 1
NEUTRAL_SOURCE_TIME = "1970-01-01T00:00:00+00:00"


def digest(value):
    return hashlib.sha256(value).hexdigest()


def canonical_json(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n").encode()


def implementation_inputs():
    """Only producers of projected identity, text, eligibility and metadata."""
    directory = Path(__file__).resolve().parent
    names = ("basic_memory_projection.py", "memory_search.py", "memory_normalization.py",
             "memory_normalize_html.py", "memory_normalize_tex.py", "memory_normalize_pdf.py")
    return {name: digest((directory / name).read_bytes()) for name in names}


def _eligible(root, config, document):
    kind, rel = document.get("kind"), document.get("path")
    require(kind in {"source", "memory"}, "projection_kind", "Only source and memory documents can be projected.")
    if kind == "source":
        require(corpus_allowed(rel, config), "projection_scope", "Source is outside the allowed corpus.")
    else:
        from memory_core import load_record
        record = load_record(root, rel, config)
        require(record["metadata"]["state"] == "active", "projection_lifecycle", "Only active memories can be projected.")
        require(record["metadata"] == document.get("metadata"), "projection_metadata", "Canonical memory metadata changed.")
    raw = safe_read_bytes(root, rel)
    require(digest(raw) == document.get("sha256"), "projection_stale", "Canonical document changed before projection.")
    return raw


def render_projection(root, config, documents):
    """Return exact projection files and manifest in memory, without writes."""
    files, entries = {}, []
    for document in sorted(documents, key=lambda d: (d["kind"], d["path"])):
        _eligible(root, config, document)
        require(isinstance(document.get("source_identity"), str) and document["source_identity"],
                "projection_identity", "Each document needs an explicit source identity.")
        metadata = document.get("metadata") or {}
        # Only canonical timestamps govern a curated record. Source mtime is not
        # interpreted as an approval date; unknown chronology stays neutral.
        created = metadata.get("created", NEUTRAL_SOURCE_TIME)
        modified = metadata.get("modified", created)
        identity = digest(canonical_json({"project": config["project"]["id"],
                                          "kind": document["kind"], "path": document["path"]}))
        filename = identity + ".md"
        title = metadata.get("title") or document["path"]
        frontmatter = {
            "title": title, "type": "note", "permalink": "sys4ai/" + identity,
            "created": created, "modified": modified,
            "sys4ai_kind": document["kind"], "sys4ai_project": config["project"]["id"],
            "sys4ai_path": document["path"], "sys4ai_sha256": document["sha256"],
            "sys4ai_source_identity": document["source_identity"],
            "sys4ai_metadata": metadata,
        }
        segments = document.get("segments", [])
        require(isinstance(segments, list) and all(isinstance(s.get("text"), str) for s in segments),
                "projection_segments", "Projection requires normalized text segments.")
        text = "\n\n".join(s["text"] for s in segments)
        raw = b"---\n" + canonical_json(frontmatter) + b"---\n\n" + text.encode() + b"\n"
        files[filename] = raw
        entries.append({"projection_path": filename, "projection_sha256": digest(raw),
                        "path": document["path"], "sha256": document["sha256"],
                        "kind": document["kind"], "source_identity": document["source_identity"],
                        "metadata": metadata, "created": created, "modified": modified,
                        "title": title, "permalink": frontmatter["permalink"],
                        "segments": [{k: v for k, v in s.items() if k != "text"} for s in segments],
                        "limitations": document.get("limitations", [])})
    manifest = {"schema_version": VERSION, "project_id": config["project"]["id"],
                "config_sha256": digest(safe_read_bytes(root, "memory.yaml")),
                "entries": entries, "classification": "rebuildable-projection",
                "implementation_inputs": implementation_inputs()}
    return files, manifest


def verify_projection(root, config, manifest=None, *, current_documents=None):
    """Read-only verification of every projected byte and its canonical source."""
    rel = config["state"]["projection"]
    raw = safe_read_bytes(root, rel + "/manifest.json")
    stored = json.loads(raw)
    require(manifest is None or manifest == stored, "projection_manifest_changed", "Projection manifest changed.")
    require(stored.get("schema_version") == VERSION and stored.get("classification") == "rebuildable-projection",
            "projection_manifest", "Unsupported projection manifest.")
    require(stored.get("project_id") == config["project"]["id"], "projection_project", "Projection belongs to another project.")
    require(stored.get("config_sha256") == digest(safe_read_bytes(root, "memory.yaml")),
            "projection_config", "Projection configuration is stale.")
    entries = stored.get("entries", [])
    require(isinstance(entries, list), "projection_manifest", "Projection entries must be a list.")
    require(stored.get("implementation_inputs") == implementation_inputs(), "projection_implementation_changed",
            "Projection producer versions changed or were not recorded; explicit reindex is required.",
            {"expected": stored.get("implementation_inputs"), "current": implementation_inputs()})
    if current_documents is None:
        from memory_search import collect_documents
        current_documents, _ = collect_documents(root, config)
    expected = {"manifest.json"}
    known = {(d["kind"], d["path"]): d for d in current_documents} if current_documents is not None else None
    for entry in entries:
        name = entry.get("projection_path", "")
        require(Path(name).name == name and name.endswith(".md") and name not in expected,
                "projection_manifest", "Invalid or duplicate projection path.")
        expected.add(name)
        require(digest(safe_read_bytes(root, rel + "/" + name)) == entry.get("projection_sha256"),
                "projection_changed", "Backend projection was modified outside maintenance.")
        if entry.get("kind") == "source":
            require(corpus_allowed(entry.get("path"), config), "projection_scope", "Projected source is no longer allowed.")
        elif entry.get("kind") == "memory":
            from memory_core import load_record
            current = load_record(root, entry["path"], config)
            require(current["metadata"]["state"] == "active" and current["metadata"] == entry.get("metadata"),
                    "projection_lifecycle", "Projected memory lifecycle or metadata changed.")
        else:
            raise MemoryError("projection_kind", "Invalid projected document kind.")
        require(digest(safe_read_bytes(root, entry["path"])) == entry.get("sha256"),
                "projection_stale", "A projected canonical document changed.",
                {"path": entry["path"], "expected_sha256": entry.get("sha256"),
                 "current_sha256": digest(safe_read_bytes(root, entry["path"]))})
        if known is not None:
            current = known.get((entry["kind"], entry["path"]))
            require(current is not None and current["sha256"] == entry["sha256"] and
                    current["source_identity"] == entry["source_identity"],
                    "projection_scope", "Projection contains a document absent from current permitted retrieval.")
    require({(entry["kind"], entry["path"]) for entry in entries} == set(known), "projection_corpus_changed",
            "Current permitted corpus differs from the indexed corpus; explicit reindex is required.",
            {"added": sorted(path for kind, path in set(known) - {(e["kind"], e["path"]) for e in entries}),
             "removed": sorted(path for kind, path in {(e["kind"], e["path"]) for e in entries} - set(known))})
    directory = safe_path(root, rel, kind="dir")
    require({p.name for p in directory.iterdir()} == expected, "unclassified_projection",
            "Unknown files or directories block use of the projection.")
    return stored
