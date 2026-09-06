"""Stable provider-neutral identifiers."""

from __future__ import annotations

import uuid

_SYS4AI_NAMESPACE = uuid.UUID("501a8244-10e1-5e09-a873-7baf1f64007a")


def stable_id(kind: str, *identity_parts: str) -> str:
    """Create a stable UUIDv5 identifier from normalized identity components."""

    if not kind.strip() or not identity_parts or any(not part.strip() for part in identity_parts):
        raise ValueError("kind and identity parts must be nonblank")
    normalized = "\x1f".join((kind.strip().lower(), *(part.strip() for part in identity_parts)))
    return str(uuid.uuid5(_SYS4AI_NAMESPACE, normalized))
