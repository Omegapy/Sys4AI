"""Credential-pattern detection that never returns or persists matched values."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from .errors import SecretDetectedError


@dataclass(frozen=True, slots=True)
class SecretFinding:
    """A safe finding containing only a rule identifier and field location."""

    rule_id: str
    field_path: str


_VALUE_RULES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("private-key", re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----", re.I)),
    ("openai-key", re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{8,}\b")),
    ("github-token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b")),
    ("aws-access-key", re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")),
    ("bearer-token", re.compile(r"\bbearer\s+[A-Za-z0-9._~+/=-]{8,}", re.I)),
    (
        "assigned-secret",
        re.compile(
            r"\b(?:api[_-]?key|access[_-]?token|password|private[_-]?key|secret)"
            r"\s*[:=]\s*[^\s,;]{4,}",
            re.I,
        ),
    ),
    ("credential-uri", re.compile(r"\b[a-z][a-z0-9+.-]*://[^:/\s]+:[^@/\s]+@", re.I)),
)
_SENSITIVE_KEY = re.compile(
    r"^(?:authorization|cookie|credential|password|private[_-]?key|secret|token)$",
    re.I,
)


def scan_text(value: str, *, field_path: str = "content") -> tuple[SecretFinding, ...]:
    """Report matched rule identifiers without retaining matched text."""

    return tuple(
        SecretFinding(rule_id=rule_id, field_path=field_path)
        for rule_id, pattern in _VALUE_RULES
        if pattern.search(value)
    )


def scan_value(value: Any, *, field_path: str = "content") -> tuple[SecretFinding, ...]:
    """Recursively scan structured input without echoing sensitive values."""

    findings: list[SecretFinding] = []
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key)
            child_path = f"{field_path}.{key_text}"
            if _SENSITIVE_KEY.fullmatch(key_text):
                findings.append(SecretFinding(rule_id="sensitive-field", field_path=child_path))
            findings.extend(scan_value(item, field_path=child_path))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, item in enumerate(value):
            findings.extend(scan_value(item, field_path=f"{field_path}[{index}]"))
    elif isinstance(value, str):
        findings.extend(scan_text(value, field_path=field_path))
    return tuple(findings)


def require_secret_free(value: Any, *, field_path: str = "content") -> None:
    """Reject secret-like input without including the value in the exception."""

    findings = scan_value(value, field_path=field_path)
    if findings:
        rule_ids = ",".join(sorted({finding.rule_id for finding in findings}))
        raise SecretDetectedError(f"secret-like content rejected by rules: {rule_ids}")


def redact_text(value: str) -> str:
    """Replace every detected credential-shaped value with a constant marker."""

    redacted = value
    for _, pattern in _VALUE_RULES:
        redacted = pattern.sub("[REDACTED]", redacted)
    return redacted
