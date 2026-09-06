"""Deterministic source-manifest reconciliation."""

from __future__ import annotations

from collections import defaultdict

from .models import (
    SourceChange,
    SourceChangeKind,
    SourceDelta,
    SourceManifest,
    SourceManifestEntry,
)


def compare_manifests(before: SourceManifest, after: SourceManifest) -> SourceDelta:
    """Classify lifecycle changes by stable ID first, then unique content hash."""

    if before.project_id != after.project_id:
        raise ValueError("cannot compare manifests from different projects")
    before_by_id = {item.source_id: item for item in before.entries}
    after_by_id = {item.source_id: item for item in after.entries}
    changes: list[SourceChange] = []

    common = sorted(before_by_id.keys() & after_by_id.keys())
    for source_id in common:
        previous = before_by_id[source_id]
        current = after_by_id[source_id]
        if current.status == "failed":
            kind = SourceChangeKind.FAILED
        elif previous.status == "failed" and current.status != "failed":
            kind = SourceChangeKind.RESUMED
        elif previous.content_sha256 == current.content_sha256 and previous.path == current.path:
            kind = SourceChangeKind.UNCHANGED
        elif previous.content_sha256 == current.content_sha256:
            kind = SourceChangeKind.MOVED
        else:
            kind = SourceChangeKind.CHANGED
        changes.append(SourceChange(kind, source_id, previous, current, "source_id"))

    unmatched_before = {
        source_id: item for source_id, item in before_by_id.items() if source_id not in after_by_id
    }
    unmatched_after = {
        source_id: item for source_id, item in after_by_id.items() if source_id not in before_by_id
    }

    # A unique hash match recovers identity for registries whose path-derived ID
    # changed during a rename.  Ambiguous duplicate-content sets remain a delete
    # plus add rather than guessing identity.
    before_hashes: dict[str, list[SourceManifestEntry]] = defaultdict(list)
    after_hashes: dict[str, list[SourceManifestEntry]] = defaultdict(list)
    for item in unmatched_before.values():
        before_hashes[item.content_sha256].append(item)
    for item in unmatched_after.values():
        after_hashes[item.content_sha256].append(item)
    for digest in sorted(before_hashes.keys() & after_hashes.keys()):
        old_items = before_hashes[digest]
        new_items = after_hashes[digest]
        if len(old_items) != 1 or len(new_items) != 1:
            continue
        previous = old_items[0]
        current = new_items[0]
        changes.append(
            SourceChange(
                SourceChangeKind.MOVED,
                previous.source_id,
                previous,
                current,
                "unique_content_sha256",
            )
        )
        unmatched_before.pop(previous.source_id)
        unmatched_after.pop(current.source_id)

    for source_id, previous in sorted(unmatched_before.items()):
        changes.append(
            SourceChange(SourceChangeKind.DELETED, source_id, previous, None, "source_id")
        )
    for source_id, current in sorted(unmatched_after.items()):
        kind = SourceChangeKind.FAILED if current.status == "failed" else SourceChangeKind.ADDED
        changes.append(SourceChange(kind, source_id, None, current, "source_id"))

    order = {kind: index for index, kind in enumerate(SourceChangeKind)}
    changes.sort(key=lambda item: (order[item.change], item.source_id))
    return SourceDelta(project_id=before.project_id, changes=tuple(changes))
