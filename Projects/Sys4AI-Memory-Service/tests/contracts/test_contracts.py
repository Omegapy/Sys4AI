"""Focused enum, invariant, serialization, and catalog tests."""

from __future__ import annotations

from copy import deepcopy

import pytest
from pydantic import ValidationError

from sys4ai_memory.contracts import (
    MCP_TOOL_CATALOG,
    PUBLIC_OPERATION_CATALOG,
    AuthorityTier,
    CoreRecordType,
    CoreRelation,
    EpistemicStatus,
    ErrorCategory,
    ErrorEnvelope,
    MemoryRecord,
    MemoryScope,
    RecordStatus,
    SourceRecord,
    TrustClass,
)
from sys4ai_memory.contracts.operations import McpToolName, OperationName

from .cases import ERROR_ENVELOPE, MEMORY_RECORD, SOURCE_RECORD


def test_prd_enums_are_complete() -> None:
    assert {item.value for item in MemoryScope} == {
        "system",
        "workspace",
        "project",
        "agent_type",
        "agent_instance",
        "task",
        "session",
        "user",
    }
    assert {item.value for item in AuthorityTier} == {f"A{index}" for index in range(8)}
    assert {item.value for item in TrustClass} == {
        "system-controlled",
        "human-approved",
        "schema-validated",
        "project-authored",
        "externally-authenticated",
        "external-unverified",
        "agent-generated",
        "model-extracted",
        "user-supplied",
        "untrusted",
    }
    assert {item.value for item in RecordStatus} == {
        "proposed",
        "staged",
        "approved",
        "active",
        "superseded",
        "rejected",
        "invalidated",
        "expired",
        "withdrawn",
        "deleted",
    }
    assert {item.value for item in EpistemicStatus} == {
        "source_statement",
        "observation",
        "claim",
        "fact_candidate",
        "verified_fact",
        "hypothesis",
        "inference",
        "decision",
        "procedure",
        "preference",
        "constraint",
        "result",
        "counterexample",
        "unknown",
    }
    assert {item.value for item in CoreRecordType} == {
        "SourceArtifact",
        "SourceFragment",
        "Entity",
        "Statement",
        "Requirement",
        "Decision",
        "Procedure",
        "Event",
        "Observation",
        "Outcome",
        "Feedback",
        "Relation",
        "Tombstone",
        "ExtensionRecord",
    }
    assert {item.value for item in CoreRelation} == {
        "CONTAINS",
        "DEFINES",
        "DESCRIBES",
        "IMPLEMENTS",
        "VALIDATES",
        "DEPENDS_ON",
        "BLOCKS",
        "ENABLES",
        "DERIVED_FROM",
        "GENERATED_FROM",
        "CITES",
        "SUPPORTS",
        "CONTRADICTS",
        "SUPERSEDES",
        "INVALIDATES",
        "APPLIES_TO",
        "OWNED_BY",
        "CREATED_BY",
        "REVIEWED_BY",
        "OBSERVED_DURING",
        "RESULTED_IN",
        "SIMILAR_TO",
        "RELATED_TO",
        "HAS_SOURCE",
        "HAS_EVIDENCE",
        "HAS_STATUS",
        "USES",
        "PRODUCES",
    }
    assert {item.value for item in ErrorCategory} == {
        "MEMORY_NOT_INITIALIZED",
        "PROJECT_NOT_FOUND",
        "SOURCE_NOT_REGISTERED",
        "SOURCE_EXCLUDED",
        "SCHEMA_INVALID",
        "PROFILE_INCOMPATIBLE",
        "PERMISSION_DENIED",
        "AUTHORITY_VIOLATION",
        "SENSITIVITY_VIOLATION",
        "PROVIDER_UNAVAILABLE",
        "PROVIDER_UNSUPPORTED",
        "INDEX_DRIFT",
        "INGESTION_FAILED",
        "RETRIEVAL_FAILED",
        "INSUFFICIENT_EVIDENCE",
        "WRITE_REJECTED",
        "APPROVAL_REQUIRED",
        "CONFLICT_DETECTED",
        "DELETION_RESTRICTED",
        "REBUILD_FAILED",
        "IMPORT_INVALID",
        "EXPORT_FAILED",
        "CONCURRENT_OPERATION",
    }


def test_stable_serialization_keeps_versions_nulls_and_utc_z() -> None:
    record = MemoryRecord.model_validate(MEMORY_RECORD)
    serialized = record.to_stable_json()
    assert serialized == record.to_stable_json()
    assert '"api_version":"1.0"' in serialized
    assert '"profile_type":null' in serialized
    assert '"created_at":"2026-09-03T00:00:00Z"' in serialized
    with pytest.raises(ValidationError, match="frozen"):
        record.record_id = "mem_changed"


def test_memory_record_requires_utc_and_model_provenance() -> None:
    non_utc = deepcopy(MEMORY_RECORD)
    non_utc["created_at"] = "2026-09-03T00:00:00-06:00"
    with pytest.raises(ValidationError, match="UTC"):
        MemoryRecord.model_validate(non_utc)

    extracted = deepcopy(MEMORY_RECORD)
    extracted["processing"]["model_extracted_fields"] = ["content.summary"]
    with pytest.raises(ValidationError, match="model_id"):
        MemoryRecord.model_validate(extracted)


def test_generated_source_requires_input_lineage_and_cannot_be_canonical() -> None:
    generated = deepcopy(SOURCE_RECORD)
    generated["source_kind"] = "generated_file"
    generated["content_role"] = "generated"
    generated["git_commit"] = None
    with pytest.raises(ValidationError, match="canonical inputs"):
        SourceRecord.model_validate(generated)

    generated["generated_from"] = ["src_prd_memory"]
    with pytest.raises(ValidationError, match="canonical authority"):
        SourceRecord.model_validate(generated)


def test_error_envelope_rejects_secret_like_text() -> None:
    unsafe = deepcopy(ERROR_ENVELOPE)
    unsafe["error"]["message"] = "provider failed with api_key=secret-value"
    with pytest.raises(ValidationError, match="secret-like"):
        ErrorEnvelope.model_validate(unsafe)


def test_public_operation_catalog_matches_prd() -> None:
    assert {operation.name for operation in PUBLIC_OPERATION_CATALOG} == set(OperationName)
    assert len(PUBLIC_OPERATION_CATALOG) == 16
    assert all(
        operation.mutating or operation.mutation_scope is None
        for operation in PUBLIC_OPERATION_CATALOG
    )
    assert all(
        operation.destructive <= operation.mutating
        for operation in PUBLIC_OPERATION_CATALOG
    )


def test_mcp_catalog_has_six_default_and_six_privileged_tools() -> None:
    assert {tool.name for tool in MCP_TOOL_CATALOG} == set(McpToolName)
    default_tools = tuple(tool for tool in MCP_TOOL_CATALOG if tool.default_enabled)
    privileged_tools = tuple(tool for tool in MCP_TOOL_CATALOG if tool.privileged)
    assert len(default_tools) == 6
    assert len(privileged_tools) == 6
    assert not any(tool.annotations.destructive for tool in default_tools)
    assert all(not tool.default_enabled for tool in privileged_tools)
    assert all(tool.annotations.read_only != tool.annotations.mutating for tool in MCP_TOOL_CATALOG)
