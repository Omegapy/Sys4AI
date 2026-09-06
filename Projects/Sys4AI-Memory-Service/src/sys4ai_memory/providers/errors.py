"""Safe provider-error construction and normalization."""

from __future__ import annotations

from collections.abc import Mapping

from sys4ai_memory.contracts import API_VERSION, SCHEMA_VERSION
from sys4ai_memory.contracts.errors import ErrorCategory, ErrorDetail, ErrorEnvelope


class MemoryProviderError(RuntimeError):
    """Provider failure carrying only the stable, redacted Sys4AI envelope."""

    def __init__(self, envelope: ErrorEnvelope) -> None:
        self.envelope = envelope
        super().__init__(envelope.error.message)


def provider_error(
    category: ErrorCategory,
    *,
    trace_id: str,
    message: str,
    recoverable: bool,
    remediation_hint: str,
) -> MemoryProviderError:
    """Build one provider-neutral error without retaining a native exception."""

    return MemoryProviderError(
        ErrorEnvelope(
            schema_version=SCHEMA_VERSION,
            api_version=API_VERSION,
            error=ErrorDetail(
                category=category,
                message=message,
                trace_id=trace_id,
                recoverable=recoverable,
                remediation_hint=remediation_hint,
            ),
        )
    )


def normalize_provider_exception(
    error: BaseException,
    *,
    trace_id: str,
    operation: str,
) -> MemoryProviderError:
    """Map an arbitrary provider exception without copying its text or objects."""

    error_type = type(error).__name__.casefold()
    type_categories: tuple[tuple[tuple[str, ...], ErrorCategory, bool, str], ...] = (
        (
            ("modulenotfound", "importerror", "packagenotfound"),
            ErrorCategory.PROVIDER_UNAVAILABLE,
            False,
            "Restore the locked provider dependency environment.",
        ),
        (
            ("datasetnotfound", "projectnotfound"),
            ErrorCategory.PROJECT_NOT_FOUND,
            False,
            "Verify the authorized project and dataset mapping.",
        ),
        (
            ("authentication", "permission", "forbidden", "unauthorized"),
            ErrorCategory.PERMISSION_DENIED,
            False,
            "Refresh the canonical permission decision and retry within its scope.",
        ),
        (
            ("timeout", "connection", "database", "unavailable"),
            ErrorCategory.PROVIDER_UNAVAILABLE,
            True,
            "Check the configured local provider dependencies and retry.",
        ),
        (
            ("validation", "valueerror", "typeerror"),
            ErrorCategory.SCHEMA_INVALID,
            False,
            "Validate the provider-neutral request before retrying.",
        ),
    )
    match = next(
        (entry for entry in type_categories if any(name in error_type for name in entry[0])),
        None,
    )
    if match is None:
        category = _operation_category(operation)
        recoverable = True
        hint = "Inspect the sanitized provider diagnostics and retry after correction."
    else:
        _, category, recoverable, hint = match

    return provider_error(
        category,
        trace_id=trace_id,
        message=f"The memory provider could not complete {operation}.",
        recoverable=recoverable,
        remediation_hint=hint,
    )


def _operation_category(operation: str) -> ErrorCategory:
    categories: Mapping[str, ErrorCategory] = {
        "remember": ErrorCategory.INGESTION_FAILED,
        "recall": ErrorCategory.RETRIEVAL_FAILED,
        "import": ErrorCategory.IMPORT_INVALID,
        "export": ErrorCategory.EXPORT_FAILED,
        "migrate": ErrorCategory.REBUILD_FAILED,
        "initialize": ErrorCategory.MEMORY_NOT_INITIALIZED,
    }
    return categories.get(operation, ErrorCategory.PROVIDER_UNAVAILABLE)
