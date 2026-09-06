"""Shared primitives for versioned provider-neutral contracts."""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, PlainSerializer, StringConstraints

SchemaVersion = Literal["1.0"]
ApiVersion = Literal["1.0"]
SCHEMA_VERSION: SchemaVersion = "1.0"
API_VERSION: ApiVersion = "1.0"
NonEmptyString = Annotated[str, StringConstraints(min_length=1)]
StableIdentifier = Annotated[
    str,
    StringConstraints(pattern=r"^[A-Za-z][A-Za-z0-9_.:@/-]*$", min_length=1, max_length=255),
]
MemoryRecordId = Annotated[
    str,
    StringConstraints(pattern=r"^mem_[A-Za-z0-9][A-Za-z0-9_.:@-]*$", max_length=255),
]
SourceId = Annotated[
    str,
    StringConstraints(pattern=r"^src_[A-Za-z0-9][A-Za-z0-9_.:@-]*$", max_length=255),
]
RelationId = Annotated[
    str,
    StringConstraints(pattern=r"^rel_[A-Za-z0-9][A-Za-z0-9_.:@-]*$", max_length=255),
]
ProposalId = Annotated[
    str,
    StringConstraints(pattern=r"^mwp_[A-Za-z0-9][A-Za-z0-9_.:@-]*$", max_length=255),
]
RequestId = Annotated[
    str,
    StringConstraints(pattern=r"^mrq_[A-Za-z0-9][A-Za-z0-9_.:@-]*$", max_length=255),
]
TraceId = Annotated[
    str,
    StringConstraints(pattern=r"^trace_[A-Za-z0-9][A-Za-z0-9_.:@-]*$", max_length=255),
]
RebuildReceiptId = Annotated[
    str,
    StringConstraints(pattern=r"^rbr_[A-Za-z0-9][A-Za-z0-9_.:@-]*$", max_length=255),
]
Sha256 = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
SemanticVersion = Annotated[
    str,
    StringConstraints(
        pattern=r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
        r"(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$"
    ),
]


def _ensure_utc(value: datetime) -> datetime:
    """Reject naive and non-UTC timestamps, then normalize the UTC identity."""

    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError("timestamp must include a UTC offset")
    return value.astimezone(UTC)


def _serialize_utc(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


UtcDateTime = Annotated[
    datetime,
    AfterValidator(_ensure_utc),
    PlainSerializer(_serialize_utc, return_type=str, when_used="json"),
]


def require_non_blank(value: str, field_name: str) -> str:
    if not value.strip():
        raise ValueError(f"{field_name} must not be blank")
    return value


class ContractModel(BaseModel):
    """Closed, immutable model with deterministic public serialization."""

    model_config = ConfigDict(extra="forbid", frozen=True, validate_default=True)

    def to_json_dict(self) -> dict[str, Any]:
        """Return the JSON-compatible representation, including explicit nulls."""

        return self.model_dump(mode="json", exclude_none=False)

    def to_stable_json(self) -> str:
        """Return a canonical textual form suitable for hashing and fixtures."""

        return json.dumps(
            self.to_json_dict(),
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )


class VersionedContract(ContractModel):
    """Common version fields required at each public contract boundary."""

    schema_version: SchemaVersion
    api_version: ApiVersion


_SENSITIVE_TEXT_PATTERNS = tuple(
    re.compile(pattern, flags=re.IGNORECASE)
    for pattern in (
        r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
        r"\bsk-(?:proj-)?[A-Za-z0-9_-]{8,}\b",
        r"\b(?:api[_-]?key|access[_-]?token|password|secret)\s*[:=]\s*\S+",
    )
)


def reject_sensitive_error_text(value: str, field_name: str) -> str:
    """Apply a narrow last-line defense against common credential disclosures."""

    require_non_blank(value, field_name)
    if any(pattern.search(value) for pattern in _SENSITIVE_TEXT_PATTERNS):
        raise ValueError(f"{field_name} must not contain secret-like content")
    return value
