"""Canonical authorization and scope-resolution API."""

from .loader import CanonicalPermissionEnvelopeLoader, CanonicalPermissionError
from .models import (
    ApprovalPolicy,
    AuthorizationDecision,
    AuthorizationRequest,
    CanonicalPermissionDocument,
    PermissionEnvelope,
    PermissionGrant,
    PermissionSnapshot,
    ReviewerIdentity,
    ReviewerKind,
)
from .service import AuthorizationService, PermissionDeniedError, ScopeResolver

__all__ = [
    "ApprovalPolicy",
    "AuthorizationDecision",
    "AuthorizationRequest",
    "AuthorizationService",
    "CanonicalPermissionDocument",
    "CanonicalPermissionEnvelopeLoader",
    "CanonicalPermissionError",
    "PermissionDeniedError",
    "PermissionEnvelope",
    "PermissionGrant",
    "PermissionSnapshot",
    "ReviewerIdentity",
    "ReviewerKind",
    "ScopeResolver",
]
