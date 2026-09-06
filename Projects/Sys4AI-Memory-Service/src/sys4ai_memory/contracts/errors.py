"""Versioned, provider-neutral public error contract."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ValidationInfo, field_validator

from ._base import (
    ContractModel,
    NonEmptyString,
    TraceId,
    VersionedContract,
    reject_sensitive_error_text,
)


class ErrorCategory(StrEnum):
    MEMORY_NOT_INITIALIZED = "MEMORY_NOT_INITIALIZED"
    PROJECT_NOT_FOUND = "PROJECT_NOT_FOUND"
    SOURCE_NOT_REGISTERED = "SOURCE_NOT_REGISTERED"
    SOURCE_EXCLUDED = "SOURCE_EXCLUDED"
    SCHEMA_INVALID = "SCHEMA_INVALID"
    PROFILE_INCOMPATIBLE = "PROFILE_INCOMPATIBLE"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    AUTHORITY_VIOLATION = "AUTHORITY_VIOLATION"
    SENSITIVITY_VIOLATION = "SENSITIVITY_VIOLATION"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    PROVIDER_UNSUPPORTED = "PROVIDER_UNSUPPORTED"
    INDEX_DRIFT = "INDEX_DRIFT"
    INGESTION_FAILED = "INGESTION_FAILED"
    RETRIEVAL_FAILED = "RETRIEVAL_FAILED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    WRITE_REJECTED = "WRITE_REJECTED"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    CONFLICT_DETECTED = "CONFLICT_DETECTED"
    DELETION_RESTRICTED = "DELETION_RESTRICTED"
    REBUILD_FAILED = "REBUILD_FAILED"
    IMPORT_INVALID = "IMPORT_INVALID"
    EXPORT_FAILED = "EXPORT_FAILED"
    CONCURRENT_OPERATION = "CONCURRENT_OPERATION"


class ErrorDetail(ContractModel):
    category: ErrorCategory
    message: NonEmptyString
    trace_id: TraceId
    recoverable: bool
    remediation_hint: NonEmptyString

    @field_validator("message", "remediation_hint")
    @classmethod
    def validate_safe_text(cls, value: str, info: ValidationInfo) -> str:
        return reject_sensitive_error_text(value, info.field_name or "error text")


class ErrorEnvelope(VersionedContract):
    error: ErrorDetail
