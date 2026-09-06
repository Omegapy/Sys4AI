"""Shared request construction used by every interface adapter."""

from __future__ import annotations

import re
from collections.abc import Mapping
from uuid import uuid4

from pydantic import JsonValue, ValidationError

from sys4ai_memory.contracts import ErrorCategory, MemoryScope, ScopeReference
from sys4ai_memory.security import SecretDetectedError

from .dispatcher import MemoryServiceDispatcher, error_envelope, safe_dispatch
from .models import (
    AuditContext,
    AuthorizationContext,
    DispatchRequest,
    DispatchResponse,
    InterfaceAction,
    InterfaceIdentity,
    InterfaceKind,
)

_REQUEST_ID = re.compile(r"^mrq_[A-Za-z0-9][A-Za-z0-9_.:@-]*$")
_TRACE_ID = re.compile(r"^trace_[A-Za-z0-9][A-Za-z0-9_.:@-]*$")


def new_request_id() -> str:
    return f"mrq_{uuid4().hex}"


def new_trace_id() -> str:
    return f"trace_{uuid4().hex}"


def safe_trace_id(candidate: object) -> str:
    """Reuse a well-formed trace ID; never echo malformed caller input."""

    if isinstance(candidate, str) and len(candidate) <= 255 and _TRACE_ID.fullmatch(candidate):
        return candidate
    return new_trace_id()


def safe_request_id(candidate: object) -> str:
    if isinstance(candidate, str) and len(candidate) <= 255 and _REQUEST_ID.fullmatch(candidate):
        return candidate
    return new_request_id()


def project_authorization(
    identity: InterfaceIdentity,
    *,
    project_id: str,
    dataset_id: str,
    scope: ScopeReference | None = None,
    query_project_ids: tuple[str, ...] | None = None,
    explicit_cross_project: bool = False,
) -> AuthorizationContext:
    resolved_scope = scope or ScopeReference(level=MemoryScope.PROJECT, scope_id=project_id)
    return AuthorizationContext(
        identity=identity,
        project_id=project_id,
        dataset_id=dataset_id,
        scope=resolved_scope,
        query_project_ids=query_project_ids or (project_id,),
        explicit_cross_project=explicit_cross_project,
    )


def invoke_dispatcher(
    dispatcher: MemoryServiceDispatcher,
    *,
    operation: InterfaceAction,
    authorization: AuthorizationContext,
    interface: InterfaceKind,
    client_id: str,
    purpose: str,
    payload: Mapping[str, JsonValue] | None = None,
    idempotency_key: str | None = None,
    request_id: str | None = None,
    trace_id: str | None = None,
) -> DispatchResponse:
    """Build, validate, and dispatch one identical service request."""

    resolved_trace_id = safe_trace_id(trace_id)
    try:
        request = DispatchRequest(
            operation=operation,
            request_id=safe_request_id(request_id),
            trace_id=resolved_trace_id,
            authorization=authorization,
            audit=AuditContext(
                interface=interface,
                client_id=client_id,
                purpose=purpose,
            ),
            idempotency_key=idempotency_key,
            payload=dict(payload or {}),
        )
    except SecretDetectedError:
        return error_envelope(resolved_trace_id, ErrorCategory.SENSITIVITY_VIOLATION)
    except (ValidationError, ValueError, TypeError):
        return error_envelope(resolved_trace_id, ErrorCategory.SCHEMA_INVALID)
    return safe_dispatch(dispatcher, request)
