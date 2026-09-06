"""Stable service-boundary exception normalization."""

from __future__ import annotations

from pydantic import ValidationError

from sys4ai_memory.authorization import CanonicalPermissionError, PermissionDeniedError
from sys4ai_memory.configuration import CapabilityBlocked, ConfigurationError
from sys4ai_memory.contracts import ErrorCategory, ErrorEnvelope, OperationName
from sys4ai_memory.exchange import (
    ExchangeError,
    ImportConflictError,
    PackageValidationError,
)
from sys4ai_memory.ingestion import IngestionFailure
from sys4ai_memory.initialization import InitializationError
from sys4ai_memory.interfaces.dispatcher import ServiceDispatchFailure, error_envelope
from sys4ai_memory.lifecycle import LifecycleStateError
from sys4ai_memory.observability import OperationTransitionError
from sys4ai_memory.providers import MemoryProviderError
from sys4ai_memory.rebuild import RebuildError
from sys4ai_memory.retrieval import RetrievalIntegrityError
from sys4ai_memory.security import (
    AuthorityEscalationError,
    IdempotencyConflictError,
    MemorySecurityError,
    PolicyDisabledError,
    ProjectIsolationError,
    SecretDetectedError,
    StaleStateError,
    UnsafePathError,
)

from .authorization import ProviderAuthorizationError


def _operation_failure_category(operation: object) -> ErrorCategory:
    if operation is OperationName.SYNC:
        return ErrorCategory.INGESTION_FAILED
    if operation is OperationName.RECALL or operation in {
        OperationName.GET,
        OperationName.GRAPH,
        OperationName.EXPLAIN,
    }:
        return ErrorCategory.RETRIEVAL_FAILED
    if operation is OperationName.REBUILD:
        return ErrorCategory.REBUILD_FAILED
    if operation is OperationName.EXPORT:
        return ErrorCategory.EXPORT_FAILED
    if operation is OperationName.IMPORT:
        return ErrorCategory.IMPORT_INVALID
    return ErrorCategory.WRITE_REJECTED


def normalize_service_exception(
    error: BaseException,
    *,
    trace_id: str,
    operation: object,
) -> ErrorEnvelope:
    """Return a public error without copying exception text or native objects."""

    if isinstance(error, MemoryProviderError):
        if error.envelope.error.trace_id == trace_id:
            return error.envelope
        return error_envelope(trace_id, ErrorCategory.PROVIDER_UNAVAILABLE)
    if isinstance(error, ServiceDispatchFailure):
        return error.envelope(trace_id)
    if isinstance(error, (PermissionDeniedError, CanonicalPermissionError, PermissionError)):
        return error_envelope(trace_id, ErrorCategory.PERMISSION_DENIED)
    if isinstance(error, SecretDetectedError):
        return error_envelope(trace_id, ErrorCategory.SENSITIVITY_VIOLATION)
    if isinstance(
        error,
        (
            ProjectIsolationError,
            UnsafePathError,
            AuthorityEscalationError,
            ProviderAuthorizationError,
        ),
    ):
        return error_envelope(trace_id, ErrorCategory.AUTHORITY_VIOLATION)
    if isinstance(error, CapabilityBlocked):
        category = (
            ErrorCategory.MEMORY_NOT_INITIALIZED
            if "memory.enabled is false" in error.gate.issues
            else ErrorCategory.APPROVAL_REQUIRED
        )
        return error_envelope(trace_id, category)
    if isinstance(error, PolicyDisabledError):
        return error_envelope(trace_id, ErrorCategory.APPROVAL_REQUIRED)
    if isinstance(
        error,
        (
            IdempotencyConflictError,
            StaleStateError,
            LifecycleStateError,
            OperationTransitionError,
            ImportConflictError,
            InitializationError,
        ),
    ):
        return error_envelope(trace_id, ErrorCategory.CONFLICT_DETECTED)
    if isinstance(error, IngestionFailure):
        return error_envelope(trace_id, ErrorCategory.INGESTION_FAILED)
    if isinstance(error, RetrievalIntegrityError):
        return error_envelope(trace_id, ErrorCategory.RETRIEVAL_FAILED)
    if isinstance(error, RebuildError):
        return error_envelope(trace_id, ErrorCategory.REBUILD_FAILED)
    if isinstance(error, PackageValidationError):
        return error_envelope(trace_id, ErrorCategory.IMPORT_INVALID)
    if isinstance(error, ExchangeError):
        return error_envelope(trace_id, _operation_failure_category(operation))
    if isinstance(error, (ValidationError, ConfigurationError, ValueError, TypeError, KeyError)):
        return error_envelope(trace_id, ErrorCategory.SCHEMA_INVALID)
    if isinstance(error, MemorySecurityError):
        return error_envelope(trace_id, ErrorCategory.WRITE_REJECTED)
    return error_envelope(trace_id, _operation_failure_category(operation))
