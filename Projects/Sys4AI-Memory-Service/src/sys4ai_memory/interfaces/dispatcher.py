"""Single dispatcher protocol and failure normalization for public adapters."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from pydantic import ValidationError

from sys4ai_memory.authorization import PermissionDeniedError
from sys4ai_memory.contracts import (
    API_VERSION,
    SCHEMA_VERSION,
    ErrorCategory,
    ErrorDetail,
    ErrorEnvelope,
    OperationName,
)
from sys4ai_memory.security import (
    AuthorityEscalationError,
    ProjectIsolationError,
    SecretDetectedError,
)

from .models import DispatchRequest, DispatchResponse, DispatchSuccess, InterfaceAction


@runtime_checkable
class MemoryServiceDispatcher(Protocol):
    """Provider-neutral service boundary used by Python, HTTP, CLI, and MCP."""

    def dispatch(self, request: DispatchRequest) -> DispatchResponse: ...


_DEFAULT_ERROR_TEXT: dict[ErrorCategory, tuple[str, bool, str]] = {
    ErrorCategory.MEMORY_NOT_INITIALIZED: (
        "The project memory service is not initialized for this configuration.",
        True,
        "Validate project configuration, then run the authorized init-memory command.",
    ),
    ErrorCategory.SCHEMA_INVALID: (
        "Request validation failed.",
        True,
        "Correct the request fields and retry.",
    ),
    ErrorCategory.PROJECT_NOT_FOUND: (
        "The requested project is unavailable.",
        False,
        "Use a registered project within the authorized scope.",
    ),
    ErrorCategory.SOURCE_NOT_REGISTERED: (
        "The requested source is not registered.",
        False,
        "Register the source through the governed project workflow.",
    ),
    ErrorCategory.SOURCE_EXCLUDED: (
        "The requested source is excluded by policy.",
        False,
        "Inspect the source registry explanation before changing policy.",
    ),
    ErrorCategory.PROFILE_INCOMPATIBLE: (
        "The selected memory profile is incompatible.",
        False,
        "Validate the profile and complete any required migration.",
    ),
    ErrorCategory.PERMISSION_DENIED: (
        "The operation is not authorized.",
        False,
        "Request the required permission through canonical project policy.",
    ),
    ErrorCategory.AUTHORITY_VIOLATION: (
        "The operation would violate an authority boundary.",
        False,
        "Use an authorized source and scope for this operation.",
    ),
    ErrorCategory.SENSITIVITY_VIOLATION: (
        "Sensitive content was rejected.",
        False,
        "Remove sensitive content and use an approved secure workflow.",
    ),
    ErrorCategory.RETRIEVAL_FAILED: (
        "The retrieval operation failed.",
        True,
        "Inspect service health and retry with the same trace ID.",
    ),
    ErrorCategory.INGESTION_FAILED: (
        "The synchronization operation failed.",
        True,
        "Inspect operation status before retrying with the same idempotency key.",
    ),
    ErrorCategory.REBUILD_FAILED: (
        "The rebuild operation failed.",
        True,
        "Inspect operation status before retrying with the same idempotency key.",
    ),
    ErrorCategory.EXPORT_FAILED: (
        "The export operation failed.",
        True,
        "Inspect operation status before retrying with the same idempotency key.",
    ),
    ErrorCategory.IMPORT_INVALID: (
        "The import operation failed validation.",
        False,
        "Validate the package and project scope before retrying.",
    ),
    ErrorCategory.WRITE_REJECTED: (
        "The write operation was rejected.",
        False,
        "Inspect policy and operation status before retrying.",
    ),
    ErrorCategory.PROVIDER_UNAVAILABLE: (
        "The memory service is unavailable.",
        True,
        "Inspect service health and retry.",
    ),
    ErrorCategory.PROVIDER_UNSUPPORTED: (
        "The configured provider does not support this operation.",
        False,
        "Select a supported provider capability without changing the public API.",
    ),
    ErrorCategory.INDEX_DRIFT: (
        "The derived index does not match current source state.",
        True,
        "Inspect drift and rebuild from registered canonical sources.",
    ),
    ErrorCategory.INSUFFICIENT_EVIDENCE: (
        "No authorized source provides sufficient evidence.",
        False,
        "Add or register evidence instead of inferring an answer.",
    ),
    ErrorCategory.APPROVAL_REQUIRED: (
        "The operation requires an unresolved approval or product decision.",
        False,
        "Resolve the named decision through the governed workflow.",
    ),
    ErrorCategory.CONFLICT_DETECTED: (
        "The request conflicts with current state.",
        False,
        "Refresh the current state and submit a new reviewed request.",
    ),
    ErrorCategory.DELETION_RESTRICTED: (
        "The requested deletion is restricted.",
        False,
        "Use the governed deletion workflow and a current impact preview.",
    ),
    ErrorCategory.CONCURRENT_OPERATION: (
        "A conflicting operation is already active.",
        True,
        "Inspect operation status before retrying.",
    ),
}


class ServiceDispatchFailure(RuntimeError):
    """A dispatcher failure carrying only prevalidated public error metadata."""

    def __init__(
        self,
        category: ErrorCategory,
        *,
        message: str | None = None,
        recoverable: bool | None = None,
        remediation_hint: str | None = None,
    ) -> None:
        defaults = _DEFAULT_ERROR_TEXT.get(
            category,
            _DEFAULT_ERROR_TEXT[ErrorCategory.WRITE_REJECTED],
        )
        self.category = category
        self.public_message = message or defaults[0]
        self.recoverable = defaults[1] if recoverable is None else recoverable
        self.remediation_hint = remediation_hint or defaults[2]
        ErrorDetail(
            category=category,
            message=self.public_message,
            trace_id="trace_dispatch_failure_validation",
            recoverable=self.recoverable,
            remediation_hint=self.remediation_hint,
        )
        super().__init__(category.value)

    def envelope(self, trace_id: str) -> ErrorEnvelope:
        return error_envelope(
            trace_id,
            self.category,
            message=self.public_message,
            recoverable=self.recoverable,
            remediation_hint=self.remediation_hint,
        )


def error_envelope(
    trace_id: str,
    category: ErrorCategory,
    *,
    message: str | None = None,
    recoverable: bool | None = None,
    remediation_hint: str | None = None,
) -> ErrorEnvelope:
    defaults = _DEFAULT_ERROR_TEXT.get(category, _DEFAULT_ERROR_TEXT[ErrorCategory.WRITE_REJECTED])
    return ErrorEnvelope(
        schema_version=SCHEMA_VERSION,
        api_version=API_VERSION,
        error=ErrorDetail(
            category=category,
            message=message or defaults[0],
            trace_id=trace_id,
            recoverable=defaults[1] if recoverable is None else recoverable,
            remediation_hint=remediation_hint or defaults[2],
        ),
    )


_READ_OPERATIONS = frozenset(
    {
        OperationName.HEALTH,
        OperationName.SOURCES_LIST,
        OperationName.SOURCES_EXPLAIN,
        OperationName.RECALL,
        OperationName.GET,
        OperationName.GRAPH,
        OperationName.EXPLAIN,
    }
)


def _failure_category(operation: InterfaceAction) -> ErrorCategory:
    if operation is OperationName.SYNC:
        return ErrorCategory.INGESTION_FAILED
    if operation is OperationName.REBUILD:
        return ErrorCategory.REBUILD_FAILED
    if operation is OperationName.EXPORT:
        return ErrorCategory.EXPORT_FAILED
    if operation is OperationName.IMPORT:
        return ErrorCategory.IMPORT_INVALID
    if operation in _READ_OPERATIONS:
        return ErrorCategory.RETRIEVAL_FAILED
    return ErrorCategory.WRITE_REJECTED


def _validated_response(request: DispatchRequest, response: DispatchResponse) -> DispatchResponse:
    if isinstance(response, ErrorEnvelope):
        if response.error.trace_id != request.trace_id:
            raise ValueError("dispatcher error trace mismatch")
        return response
    result = DispatchSuccess.model_validate(response)
    if (
        result.operation != request.operation
        or result.project_id != request.authorization.project_id
        or result.request_id != request.request_id
        or result.trace_id != request.trace_id
    ):
        raise ValueError("dispatcher result identity mismatch")
    return result


def safe_dispatch(
    dispatcher: MemoryServiceDispatcher,
    request: DispatchRequest,
) -> DispatchResponse:
    """Dispatch once and convert every boundary failure to a safe stable envelope."""

    try:
        return _validated_response(request, dispatcher.dispatch(request))
    except ServiceDispatchFailure as error:
        return error.envelope(request.trace_id)
    except (PermissionDeniedError, PermissionError):
        return error_envelope(request.trace_id, ErrorCategory.PERMISSION_DENIED)
    except (ProjectIsolationError, AuthorityEscalationError):
        return error_envelope(request.trace_id, ErrorCategory.AUTHORITY_VIOLATION)
    except SecretDetectedError:
        return error_envelope(request.trace_id, ErrorCategory.SENSITIVITY_VIOLATION)
    except (ValidationError, ValueError, TypeError):
        return error_envelope(request.trace_id, _failure_category(request.operation))
    except Exception:  # noqa: BLE001 - the interface must never expose provider exceptions
        return error_envelope(request.trace_id, _failure_category(request.operation))
