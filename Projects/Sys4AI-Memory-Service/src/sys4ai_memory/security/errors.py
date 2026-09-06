"""Fail-closed policy and security errors with non-sensitive diagnostics."""

from __future__ import annotations


class MemorySecurityError(RuntimeError):
    """Base class for a rejected security-sensitive operation."""

    code = "SECURITY_POLICY_REJECTED"


class AuthorityEscalationError(MemorySecurityError):
    """A derived artifact attempted to gain authority from its content."""

    code = "AUTHORITY_ESCALATION"


class SecretDetectedError(MemorySecurityError):
    """Secret-like content was detected at a durable boundary."""

    code = "SECRET_DETECTED"


class ProjectIsolationError(MemorySecurityError):
    """An operation crossed its declared project or dataset boundary."""

    code = "PROJECT_ISOLATION_VIOLATION"


class UnsafePathError(MemorySecurityError):
    """A path did not remain inside its registered allowed root."""

    code = "UNSAFE_PATH"


class PolicyDisabledError(MemorySecurityError):
    """A capability is disabled until its canonical policy is resolved."""

    code = "POLICY_UNRESOLVED"


class StaleStateError(MemorySecurityError):
    """Canonical state changed after a preview or review artifact was created."""

    code = "STALE_CANONICAL_STATE"


class IdempotencyConflictError(MemorySecurityError):
    """An idempotency key was reused for a different request."""

    code = "IDEMPOTENCY_CONFLICT"
