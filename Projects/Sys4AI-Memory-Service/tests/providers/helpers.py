"""Small typed fixtures shared by provider tests."""

from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime

from sys4ai_memory.contracts import API_VERSION, SCHEMA_VERSION, MemoryScope, Permission
from sys4ai_memory.contracts.models import (
    MemoryRecord,
    RelationRecord,
    ScopeReference,
    SourceRecord,
)
from sys4ai_memory.providers import (
    PolicyEnvelope,
    ProviderContext,
    ProviderMutation,
)
from tests.contracts.cases import MEMORY_RECORD, RELATION_RECORD, SOURCE_RECORD

NOW = datetime(2026, 9, 3, tzinfo=UTC)
SHA_C = "c" * 64


def context(
    project_id: str = "project-alpha",
    dataset_id: str = "project-alpha-memory",
    *,
    trace_id: str = "trace_provider_test",
) -> ProviderContext:
    return ProviderContext(
        project_id=project_id,
        dataset_id=dataset_id,
        principal_id="agent_test",
        scope=ScopeReference(level=MemoryScope.PROJECT, scope_id=project_id),
        trace_id=trace_id,
    )


def policy(
    operation: ProviderMutation,
    provider_context: ProviderContext,
    *,
    allowed: bool = True,
    impact_digest: str | None = None,
) -> PolicyEnvelope:
    expected_permission = {
        ProviderMutation.INITIALIZE: Permission.ADMINISTER,
        ProviderMutation.REMEMBER: Permission.WRITE_DERIVED,
        ProviderMutation.IMPROVE: Permission.WRITE_DERIVED,
        ProviderMutation.FORGET: Permission.DELETE,
        ProviderMutation.EXPORT: Permission.SHARE,
        ProviderMutation.IMPORT: Permission.ADMINISTER,
        ProviderMutation.MIGRATE: Permission.ADMINISTER,
    }[operation]
    return PolicyEnvelope(
        schema_version=SCHEMA_VERSION,
        api_version=API_VERSION,
        decision_id=f"decision_{operation.value}",
        operation=operation,
        principal_id=provider_context.principal_id,
        project_id=provider_context.project_id,
        dataset_id=provider_context.dataset_id,
        scope=provider_context.scope,
        permission=expected_permission,
        allowed=allowed,
        policy_id="provider-policy@1",
        policy_revision="revision-1",
        canonical_source="control_records/memory/permissions/test.json",
        evaluated_at=NOW,
        trace_id=provider_context.trace_id,
        impact_digest=impact_digest,
    )


def memory_record(
    record_id: str = "mem_ALPHA",
    *,
    title: str = "Provider boundary",
    exact: str = "Canonical exact content must not be embedded.",
    summary: str = "Provider abstraction keeps agent contracts stable.",
    status: str = "active",
    valid_from: str = "2026-09-03T00:00:00Z",
    valid_to: str | None = None,
    version: int = 1,
) -> MemoryRecord:
    value = deepcopy(MEMORY_RECORD)
    value["record_id"] = record_id
    value["project_id"] = "project-alpha"
    value["scope"]["scope_id"] = "project-alpha"
    value["title"] = title
    value["content"]["exact"] = exact
    value["content"]["summary"] = summary
    value["lifecycle"]["status"] = status
    value["lifecycle"]["valid_from"] = valid_from
    value["lifecycle"]["valid_to"] = valid_to
    value["created_at"] = valid_from
    value["updated_at"] = valid_from
    value["version"] = version
    return MemoryRecord.model_validate(value)


def relation_record(
    source_id: str = "mem_ALPHA", target_id: str = "mem_BETA"
) -> RelationRecord:
    value = deepcopy(RELATION_RECORD)
    value["relation_id"] = "rel_ALPHA_DEPENDS_ON_BETA"
    value["project_id"] = "project-alpha"
    value["relation_type"] = "DEPENDS_ON"
    value["source_record_id"] = source_id
    value["target_record_id"] = target_id
    value["temporal"]["valid_from"] = "2026-09-03T00:00:00Z"
    return RelationRecord.model_validate(value)


def source_record() -> SourceRecord:
    value = deepcopy(SOURCE_RECORD)
    value["project_id"] = "project-alpha"
    value["scope"]["scope_id"] = "project-alpha"
    value["content_sha256"] = SHA_C
    return SourceRecord.model_validate(value)
