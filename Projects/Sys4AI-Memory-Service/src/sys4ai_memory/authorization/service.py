"""Permission and scope enforcement using fresh canonical envelopes."""

from __future__ import annotations

from datetime import datetime
from pathlib import PurePosixPath

from sys4ai_memory.contracts import ScopeReference
from sys4ai_memory.util import ensure_utc, utc_now

from .loader import CanonicalPermissionEnvelopeLoader, CanonicalPermissionError
from .models import (
    AuthorizationDecision,
    AuthorizationRequest,
    PermissionEnvelope,
    PermissionGrant,
)


class PermissionDeniedError(RuntimeError):
    """The current canonical permission state denied an operation."""


def _scope_identities(scope: ScopeReference) -> frozenset[tuple[str, str]]:
    pending = [scope]
    identities: set[tuple[str, str]] = set()
    while pending:
        current = pending.pop()
        identity = (current.level.value, current.scope_id)
        if identity in identities:
            continue
        identities.add(identity)
        pending.extend(current.parent_scopes)
    return frozenset(identities)


class ScopeResolver:
    """Resolve grant inheritance only through explicit scope ancestry."""

    @staticmethod
    def allows(grant: PermissionGrant, requested: ScopeReference) -> bool:
        requested_identities = _scope_identities(requested)
        return any(
            (scope.level.value, scope.scope_id) in requested_identities for scope in grant.scopes
        )


def _target_allowed(grant: PermissionGrant, target_path: str | None) -> bool:
    if not grant.target_prefixes:
        return True
    if target_path is None:
        return False
    target = PurePosixPath(target_path)
    return any(
        target == PurePosixPath(prefix) or PurePosixPath(prefix) in target.parents
        for prefix in grant.target_prefixes
    )


class AuthorizationService:
    """Evaluate each operation against the current canonical permission source."""

    def __init__(
        self,
        loader: CanonicalPermissionEnvelopeLoader,
        *,
        scope_resolver: ScopeResolver | None = None,
    ) -> None:
        self._loader = loader
        self._scope_resolver = scope_resolver or ScopeResolver()

    def resolve_envelope(self, principal_id: str) -> PermissionEnvelope:
        return self._loader.resolve(principal_id)

    def evaluate(
        self,
        request: AuthorizationRequest,
        *,
        now: datetime | None = None,
    ) -> AuthorizationDecision:
        """Return a non-sensitive decision; invalid canonical state is a denial."""

        try:
            envelope = self.resolve_envelope(request.principal_id)
        except CanonicalPermissionError:
            return self._decision(
                request, False, "canonical_permission_unavailable", None, None, None
            )
        if request.project_id != envelope.project_id or request.dataset_id != envelope.dataset_id:
            return self._decision(
                request,
                False,
                "project_dataset_mismatch",
                envelope.revision,
                envelope.canonical_sha256,
                None,
            )
        effective_now = ensure_utc(now or utc_now())
        for grant in envelope.grants:
            if request.permission not in grant.permissions:
                continue
            if request.require_action_specific and request.operation not in grant.operations:
                continue
            if grant.operations and request.operation not in grant.operations:
                continue
            if grant.valid_until is not None and grant.valid_until <= effective_now:
                continue
            if not self._scope_resolver.allows(grant, request.scope):
                continue
            if not _target_allowed(grant, request.target_path):
                continue
            requested_projects = frozenset(request.query_project_ids)
            if requested_projects:
                if envelope.project_id not in requested_projects:
                    continue
                cross_projects = requested_projects - {envelope.project_id}
                if cross_projects and not request.explicit_cross_project:
                    continue
                if not cross_projects.issubset(grant.shared_project_ids):
                    continue
            return self._decision(
                request,
                True,
                "allowed",
                envelope.revision,
                envelope.canonical_sha256,
                grant.grant_id,
            )
        return self._decision(
            request,
            False,
            "no_matching_current_grant",
            envelope.revision,
            envelope.canonical_sha256,
            None,
        )

    def require(
        self,
        request: AuthorizationRequest,
        *,
        now: datetime | None = None,
    ) -> AuthorizationDecision:
        decision = self.evaluate(request, now=now)
        if not decision.allowed:
            raise PermissionDeniedError(f"permission denied: {decision.reason_code}")
        return decision

    @staticmethod
    def _decision(
        request: AuthorizationRequest,
        allowed: bool,
        reason_code: str,
        revision: str | None,
        canonical_sha256: str | None,
        grant_id: str | None,
    ) -> AuthorizationDecision:
        return AuthorizationDecision(
            allowed=allowed,
            reason_code=reason_code,
            principal_id=request.principal_id,
            project_id=request.project_id,
            dataset_id=request.dataset_id,
            operation=request.operation,
            permission=request.permission,
            permission_revision=revision,
            canonical_sha256=canonical_sha256,
            grant_id=grant_id,
        )
