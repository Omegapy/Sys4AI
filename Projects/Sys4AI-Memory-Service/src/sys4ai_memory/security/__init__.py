"""Security boundaries for provider-neutral memory operations."""

from .audit import AuditEvent, AuditSink, InMemoryAuditSink, JsonlAuditSink
from .authority import (
    DerivedAuthority,
    authority_rank,
    bind_derived_authority,
    least_authoritative,
    require_no_authority_elevation,
)
from .errors import (
    AuthorityEscalationError,
    IdempotencyConflictError,
    MemorySecurityError,
    PolicyDisabledError,
    ProjectIsolationError,
    SecretDetectedError,
    StaleStateError,
    UnsafePathError,
)
from .isolation import (
    DatasetIsolationMap,
    DeploymentMode,
    DeploymentSecurityPosture,
    ProjectBoundary,
    require_explicit_query_scope,
    require_shared_security,
)
from .secrets import SecretFinding, redact_text, require_secret_free, scan_text, scan_value
from .untrusted import UntrustedContent, classify_external_content

__all__ = [
    "AuditEvent",
    "AuditSink",
    "AuthorityEscalationError",
    "DatasetIsolationMap",
    "DeploymentMode",
    "DeploymentSecurityPosture",
    "DerivedAuthority",
    "IdempotencyConflictError",
    "InMemoryAuditSink",
    "JsonlAuditSink",
    "MemorySecurityError",
    "PolicyDisabledError",
    "ProjectBoundary",
    "ProjectIsolationError",
    "SecretDetectedError",
    "SecretFinding",
    "StaleStateError",
    "UnsafePathError",
    "UntrustedContent",
    "authority_rank",
    "bind_derived_authority",
    "classify_external_content",
    "least_authoritative",
    "redact_text",
    "require_explicit_query_scope",
    "require_no_authority_elevation",
    "require_secret_free",
    "require_shared_security",
    "scan_text",
    "scan_value",
]
