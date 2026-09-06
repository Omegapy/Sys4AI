"""Conservative redaction for metadata-only logs and safe errors."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

_SENSITIVE_KEY = re.compile(
    r"(?:authorization|cookie|credential|password|private[_-]?key|secret|token)",
    re.IGNORECASE,
)
_BEARER = re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]+")
_CONNECTION_CREDENTIALS = re.compile(r"(?i)(://[^:/\s]+:)[^@/\s]+(@)")


def redact_sensitive(value: Any) -> Any:
    """Return a structurally equivalent value with common secrets removed."""

    if isinstance(value, Mapping):
        return {
            str(key): "[REDACTED]" if _SENSITIVE_KEY.search(str(key)) else redact_sensitive(item)
            for key, item in value.items()
        }
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [redact_sensitive(item) for item in value]
    if isinstance(value, str):
        redacted = _BEARER.sub("Bearer [REDACTED]", value)
        return _CONNECTION_CREDENTIALS.sub(r"\1[REDACTED]\2", redacted)
    return value
