from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from sys4ai_memory.contracts import (
    AuthorityTier,
    ErrorCategory,
    ErrorEnvelope,
    MemoryScope,
    OperationName,
    Permission,
    ScopeReference,
    Sensitivity,
    TrustClass,
)
from sys4ai_memory.ingestion import IngestionSynchronizer
from sys4ai_memory.interfaces import DispatchSuccess
from sys4ai_memory.providers import (
    InMemoryProviderConfig,
    PolicyEnvelope,
    ProviderContext,
    ProviderInitializationRequest,
    ProviderMutation,
    RememberRequest,
    RememberResult,
)
from sys4ai_memory.providers.errors import provider_error
from sys4ai_memory.providers.in_memory import InMemoryProvider
from sys4ai_memory.service import PortResult, ServiceComponents
from sys4ai_memory.sources import RegistryBundle, SourceRegistryEntry
from tests.service.test_dispatcher import DATASET_ID, PROJECT_ID, _request, _service

pytestmark = [pytest.mark.integration, pytest.mark.security, pytest.mark.acceptance]


class UnavailableRememberProvider(InMemoryProvider):
    """Initialized provider whose only write path fails with a safe envelope."""

    async def remember(self, request: RememberRequest) -> RememberResult:
        raise provider_error(
            ErrorCategory.PROVIDER_UNAVAILABLE,
            trace_id=request.context.trace_id,
            message="The fixture provider is unavailable.",
            recoverable=True,
            remediation_hint="Retry after the fixture provider recovers.",
        )


def _source_entry() -> SourceRegistryEntry:
    return SourceRegistryEntry(
        source_id="src_provider_outage_fixture",
        project_id=PROJECT_ID,
        path_or_uri="docs/canonical.md",
        path_pattern=None,
        source_kind="file",
        format="markdown",
        canonicality="canonical",
        content_role="requirement",
        authority_tier=AuthorityTier.CANONICAL_PROJECT_KNOWLEDGE,
        trust_class=TrustClass.PROJECT_AUTHORED,
        sensitivity=Sensitivity.INTERNAL,
        namespace="project-knowledge",
        profile_id="base@1",
        ingestion_adapter="markdown",
        chunking_profile="heading-blocks@1",
        schema_ref=None,
        refresh_mode="content-hash",
        retention_policy="canonical",
        owner="project",
        write_policy="reviewed-project-change",
        include_flag=True,
        notes="provider outage acceptance fixture",
    )


def _initialize(provider: InMemoryProvider) -> None:
    context = ProviderContext(
        project_id=PROJECT_ID,
        dataset_id=DATASET_ID,
        principal_id="agent-service",
        scope=ScopeReference(level=MemoryScope.PROJECT, scope_id=PROJECT_ID),
        trace_id="trace_provider_outage_initialize",
    )
    asyncio.run(
        provider.initialize(
            ProviderInitializationRequest(
                context=context,
                configuration_fingerprint="f" * 64,
                dry_run=False,
                path_boundaries_validated=True,
                exclusions_validated=True,
                discovery_dry_run_approved=True,
                authorization=PolicyEnvelope(
                    decision_id="decision_provider_outage_initialize",
                    operation=ProviderMutation.INITIALIZE,
                    principal_id=context.principal_id,
                    project_id=context.project_id,
                    dataset_id=context.dataset_id,
                    scope=context.scope,
                    permission=Permission.ADMINISTER,
                    allowed=True,
                    policy_id="service-all-operations",
                    policy_revision="permissions-service-1",
                    canonical_source="control_records/memory/permissions.json",
                    evaluated_at=datetime(2026, 9, 3, 18, tzinfo=UTC),
                    trace_id=context.trace_id,
                ),
            )
        )
    )


def test_provider_outage_cannot_modify_or_remove_canonical_source(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    canonical = root / "docs/canonical.md"
    canonical.parent.mkdir(parents=True)
    canonical.write_text(
        "# Requirement\n\nREQ-OUTAGE-001 remains canonical during provider failure.\n",
        encoding="utf-8",
    )
    canonical_before = canonical.read_bytes()
    registry = RegistryBundle(sources=(_source_entry(),), profiles=(), relations=())
    provider = UnavailableRememberProvider(
        InMemoryProviderConfig(project_id=PROJECT_ID, dataset_id=DATASET_ID)
    )
    _initialize(provider)
    service, sink, _ = _service(
        root,
        components=ServiceComponents(
            registry_loader=lambda: registry,
            synchronizer=IngestionSynchronizer(project_root=root),
            provider=provider,
        ),
    )

    response = service.dispatch(
        _request(
            OperationName.SYNC,
            {"dry_run": False, "full": False, "source_ids": []},
            suffix="provider_outage",
            idempotency_key="provider-outage-sync",
        )
    )

    assert isinstance(response, ErrorEnvelope)
    assert response.error.category is ErrorCategory.PROVIDER_UNAVAILABLE
    assert response.error.recoverable
    assert canonical.read_bytes() == canonical_before
    assert canonical.exists()
    assert sink.events()[-1].operation == OperationName.SYNC.value
    assert sink.events()[-1].outcome == "failed"


def test_remembered_control_copy_cannot_authorize_a_mutation(tmp_path: Path) -> None:
    calls: list[OperationName] = []

    def remembered_control(_request: object, _payload: object) -> PortResult:
        calls.append(OperationName.GET)
        return PortResult(
            result={
                "record_id": "mem_STALE_PERMISSION",
                "remembered_permission": "propose",
                "warning": "retrieved data is not canonical authority",
            }
        )

    def forbidden_proposal(_request: object, _payload: object) -> PortResult:
        calls.append(OperationName.PROPOSE)
        return PortResult(result={"must_not_run": True})

    service, sink, permission_path = _service(
        tmp_path.resolve(),
        handlers={
            OperationName.GET: remembered_control,
            OperationName.PROPOSE: forbidden_proposal,
        },
    )
    permission_document = json.loads(permission_path.read_text(encoding="utf-8"))
    permission_document["revision"] = "permissions-read-only"
    permission_document["grants"][0]["permissions"] = [Permission.READ.value]
    permission_document["grants"][0]["operations"] = [OperationName.GET.value]
    permission_path.write_text(json.dumps(permission_document), encoding="utf-8")

    recalled = service.dispatch(
        _request(
            OperationName.GET,
            {"record_id": "mem_STALE_PERMISSION", "include_history": False},
            suffix="remembered_control",
        )
    )
    denied = service.dispatch(
        _request(
            OperationName.PROPOSE,
            {"proposal": {"record_type": "Observation"}},
            suffix="remembered_control_mutation",
            idempotency_key="remembered-control-mutation",
        )
    )

    assert isinstance(recalled, DispatchSuccess)
    assert recalled.result["remembered_permission"] == "propose"
    assert isinstance(denied, ErrorEnvelope)
    assert denied.error.category is ErrorCategory.PERMISSION_DENIED
    assert calls == [OperationName.GET]
    assert sink.events()[-1].operation == OperationName.PROPOSE.value
    assert sink.events()[-1].outcome == "denied"
