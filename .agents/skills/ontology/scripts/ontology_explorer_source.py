"""Registered evidence identity and exact, transient plain-text extraction.

No path or URL supplied by a browser reaches a file operation. The caller first
resolves an immutable tuple, then uses SnapshotStore.observe_source. The one
candidate-validation read is hash-bound to its enclosing snapshot observation.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from ontology_core import canonical_bytes, allowed_source_path, decode_json, OntologyError
from ontology_explorer_snapshot import _file


class SourceError(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def references(view, owner_id):
    """Direct record evidence and explicit binding projections stay distinct."""
    record = view.project.by_id.get(owner_id)
    if record is None:
        raise SourceError("source_forbidden")
    rows = [(record, None)] + [(r, r["@id"]) for r in view.project.records
                              if r["kind"] == "binding" and r["entity"] == owner_id]
    result = {}
    for row, binding in rows:
        for src in row.get("sources", ()):
            identity = dict(owner_id=owner_id, binding_id=binding, path=src["path"],
                            locator=src["locator"], recorded_sha256=src["sha256"])
            key = hashlib.sha256(canonical_bytes(identity)).hexdigest()
            marker = view.manifest["files"].get(src["path"], {})
            observed = marker.get("sha256")
            state = "unavailable" if observed is None else "current" if observed == src["sha256"] else "stale"
            result[key] = dict(reference_id=key, **identity, observed_sha256=observed, source_state=state)
    return [result[key] for key in sorted(result)]


def resolve(view, owner_id, reference_id):
    for ref in references(view, owner_id):
        if ref["reference_id"] == reference_id:
            try:
                allowed_source_path(ref["path"])
            except OntologyError:
                raise SourceError("source_forbidden") from None
            if ref["path"] not in view.source_paths:
                raise SourceError("source_forbidden")
            return ref
    raise SourceError("source_forbidden")


def freshness(refs):
    states = {r["source_state"] for r in refs}
    return next((s for s in ("unavailable", "stale", "current") if s in states), "unrecorded")


@dataclass(frozen=True)
class Extraction:
    text: str
    kind: str
    locator: str
    supported: bool
    # Character positions in the decoded original source, or JSON pointer parts.
    span: tuple | None = None
    pointer: tuple | None = None
    encoding: str = "plain"

    def wire(self):
        return dict(kind=self.kind, locator=self.locator, content_type="text/plain",
                    original_locator_supported=self.supported)


def _headings(text):
    lines = text.splitlines(keepends=True)
    result, offset, fence, html, paragraph = [], 0, None, None, []
    for line in lines:
        stripped = line.rstrip("\r\n")
        if html:
            ended = "-->" in stripped if html == "comment" else not stripped.strip()
            if ended: html = None
            offset += len(line); paragraph = []; continue
        if re.match(r"^ {0,3}<!--", stripped):
            if "-->" not in stripped: html = "comment"
            offset += len(line); paragraph = []; continue
        if re.match(r"^ {0,3}<(?:[A-Za-z/!?])", stripped):
            html = "block"; offset += len(line); paragraph = []; continue
        match = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", stripped)
        if match:
            mark = match[1]
            if fence is None: fence = (mark[0], len(mark))
            elif mark[0] == fence[0] and len(mark) >= fence[1] and not match[2].strip(): fence = None
            offset += len(line); paragraph = []; continue
        if fence is not None:
            offset += len(line); continue
        match = re.match(r"^ {0,3}(#{1,6})(?:[ \t]+|$)(.*)$", stripped)
        if match:
            title = re.sub(r"[ \t]+#+[ \t]*$", "", match[2]).strip()
            result.append((title, len(match[1]), offset)); paragraph = []
        elif re.fullmatch(r" {0,3}(?:=+|-+)[ \t]*", stripped) and paragraph:
            # A multiline Setext title is a single structural heading. A locator
            # naming only one of its lines is not an exact heading match.
            result.append(("\n".join(x[0] for x in paragraph), 1 if "=" in stripped else 2, paragraph[0][1]))
            paragraph = []
        elif not stripped.strip() or stripped.startswith(("    ", "\t", ">")):
            paragraph = []
        else:
            paragraph.append((stripped.strip(), offset))
        offset += len(line)
    return result


def extract(raw, locator, *, changed=False):
    """Return exact text or explicitly qualified excerpt; never repair a locator."""
    try:
        text = raw.decode("utf-8", "strict")
    except (AttributeError, UnicodeError):
        raise SourceError("source_unavailable") from None
    try:
        if re.fullmatch(r"lines?:[1-9][0-9]*(?:-[1-9][0-9]*)?", locator):
            bounds = [int(x) for x in locator.split(":")[1].split("-")]
            lines = text.splitlines(keepends=True)
            if not 1 <= bounds[0] <= bounds[-1] <= len(lines):
                raise ValueError()
            start, end = sum(map(len, lines[:bounds[0]-1])), sum(map(len, lines[:bounds[-1]]))
            return Extraction(text[start:end], "exact_lines", locator, True, (start, end))
        if locator.startswith("section:"):
            title = locator[8:].strip()
            matches = [(i, h) for i, h in enumerate(_headings(text)) if h[0] == title]
            if len(matches) == 1:
                headings = _headings(text)
                index, (_, level, start) = matches[0]
                end = next((h[2] for h in headings[index+1:] if h[1] <= level), len(text))
                return Extraction(text[start:end], "exact_section", locator, True, (start, end))
            if title and title in text:
                return Extraction(text, "bounded_excerpt", locator, False)
            raise ValueError()
        if locator.startswith("json:"):
            pointer = locator[5:]
            # Exact compatibility with the canonical check_locator traversal.
            # In this profile json:/ names the whole document; array segments
            # use int(), including its accepted leading-zero/signed spellings.
            parts = pointer.strip("/").split("/") if pointer.strip("/") else []
            parts = [p.replace("~1", "/").replace("~0", "~") for p in parts]
            value = decode_json(raw)
            resolved = []
            for part in parts:
                if isinstance(value, list):
                    index = int(part)
                    resolved.append(("array", index if index >= 0 else len(value) + index))
                    value = value[index]
                else:
                    resolved.append(("object", part))
                    value = value[part]
            return Extraction(canonical_bytes(value).decode(), "exact_json", locator, True,
                              pointer=tuple(resolved), encoding="canonical_json")
        raise ValueError()
    except (ValueError, KeyError, IndexError, TypeError, OntologyError):
        if changed:
            return Extraction(text, "bounded_excerpt", locator, False)
        raise SourceError("source_locator_invalid") from None


def contained(parent, child):
    if not parent.supported or not child.supported:
        return False
    if parent.span is not None and child.span is not None:
        return parent.span[0] <= child.span[0] <= child.span[1] <= parent.span[1]
    if parent.pointer is not None and child.pointer is not None:
        return child.pointer[:len(parent.pointer)] == parent.pointer
    return False


def candidate_bytes(view, ref):
    """Called only inside candidate validation, bracketed by store postchecks."""
    if ref["source_state"] == "unavailable":
        return None
    try:
        raw = _file(view.project.root / ref["path"])
    except OSError:
        raise SourceError("snapshot_changed") from None
    if hashlib.sha256(raw).hexdigest() != ref["observed_sha256"]:
        raise SourceError("snapshot_changed")
    return raw


def observe(store, view, ref, *, deadline=None):
    raw, marker = store.observe_source(view, ref["path"], deadline=deadline)
    if raw is None:
        raise SourceError("source_unavailable")
    observed = hashlib.sha256(raw).hexdigest()
    if observed != marker["sha256"]:
        raise SourceError("snapshot_changed")
    state = "current" if observed == ref["recorded_sha256"] else "stale"
    current = dict(ref, observed_sha256=observed, source_state=state)
    extraction = extract(raw, ref["locator"], changed=state == "stale")
    observation = dict(sha256=observed, state=state, outside_snapshot=observed != ref["observed_sha256"])
    return current, observation, extraction
