"""Executable conformance tests for the deterministic in-memory provider."""

from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from sys4ai_memory.contracts import RetrievalMode
from sys4ai_memory.contracts.errors import ErrorCategory
from sys4ai_memory.providers import (
    ExportRequest,
    ForgetAction,
    ForgetRequest,
    HealthRequest,
    ImportRequest,
    InMemoryProviderConfig,
    MemoryProvider,
    MigrationRequest,
    ProviderExportFormat,
    ProviderHealthProbe,
    ProviderHealthState,
    ProviderInitializationRequest,
    ProviderMutation,
    ProviderSnapshot,
    RecallRequest,
    RememberRequest,
)
from sys4ai_memory.providers.errors import MemoryProviderError
from sys4ai_memory.providers.in_memory import InMemoryProvider

from .helpers import context, memory_record, policy, relation_record, source_record


async def initialize(provider: MemoryProvider) -> None:
    provider_context = context()
    await provider.initialize(
        ProviderInitializationRequest(
            context=provider_context,
            configuration_fingerprint="d" * 64,
            dry_run=False,
            authorization=policy(ProviderMutation.INITIALIZE, provider_context),
        )
    )


def remember_request(*, idempotency_key: str = "remember-1") -> RememberRequest:
    provider_context = context()
    return RememberRequest(
        context=provider_context,
        request_id="mrq_remember_1",
        idempotency_key=idempotency_key,
        records=(
            memory_record(
                "mem_ALPHA",
                title="Alpha requirement",
                summary="Alpha depends on the beta provider component.",
            ),
            memory_record(
                "mem_BETA",
                title="Beta provider component",
                summary="Beta supplies the replaceable provider boundary.",
            ),
        ),
        relations=(relation_record(),),
        sources=(source_record(),),
        authorization=policy(ProviderMutation.REMEMBER, provider_context),
    )


@pytest.mark.asyncio
async def test_in_memory_provider_conforms_and_is_idempotent() -> None:
    provider = InMemoryProvider(
        InMemoryProviderConfig(project_id="project-alpha", dataset_id="project-alpha-memory")
    )
    assert isinstance(provider, MemoryProvider)

    dry_run = await provider.initialize(
        ProviderInitializationRequest(
            context=context(),
            configuration_fingerprint="d" * 64,
        )
    )
    assert dry_run.dry_run is True
    assert dry_run.initialized is False

    await initialize(provider)
    first = await provider.remember(remember_request())
    replay = await provider.remember(
        remember_request(idempotency_key="remember-1").model_copy(
            update={"request_id": "mrq_remember_2"}
        )
    )

    assert first.idempotent_replay is False
    assert replay.idempotent_replay is True
    assert replay.record_ids == ("mem_ALPHA", "mem_BETA")
    assert replay.relation_ids == ("rel_ALPHA_DEPENDS_ON_BETA",)

    result = await provider.recall(
        RecallRequest(
            context=context(),
            request_id="mrq_recall_graph",
            query="Alpha requirement",
            mode=RetrievalMode.GRAPH,
        )
    )
    assert {candidate.record.record_id for candidate in result.candidates} == {
        "mem_ALPHA",
        "mem_BETA",
    }
    assert tuple(relation.relation_id for relation in result.relations) == (
        "rel_ALPHA_DEPENDS_ON_BETA",
    )
    json.dumps(result.to_json_dict())


@pytest.mark.asyncio
async def test_in_memory_recall_filters_current_and_historical_lifecycle() -> None:
    provider = InMemoryProvider(
        InMemoryProviderConfig(project_id="project-alpha", dataset_id="project-alpha-memory")
    )
    await initialize(provider)
    provider_context = context()
    request = RememberRequest(
        context=provider_context,
        request_id="mrq_remember_history",
        idempotency_key="remember-history",
        records=(
            memory_record(
                "mem_OLD",
                title="Historic provider decision",
                summary="Provider history before replacement.",
                status="superseded",
                valid_from="2026-09-01T00:00:00Z",
                valid_to="2026-09-02T23:59:59Z",
            ),
            memory_record(
                "mem_NEW",
                title="Current provider decision",
                summary="Provider history after replacement.",
            ),
        ),
        authorization=policy(ProviderMutation.REMEMBER, provider_context),
    )
    await provider.remember(request)

    current = await provider.recall(
        RecallRequest(
            context=provider_context,
            request_id="mrq_current",
            query="provider history",
            mode=RetrievalMode.HYBRID,
        )
    )
    historical = await provider.recall(
        RecallRequest(
            context=provider_context,
            request_id="mrq_historical",
            query="provider history",
            mode=RetrievalMode.TEMPORAL,
            current_only=False,
            at_time=datetime(2026, 9, 1, 12, tzinfo=UTC),
        )
    )

    assert tuple(candidate.record.record_id for candidate in current.candidates) == ("mem_NEW",)
    assert tuple(candidate.record.record_id for candidate in historical.candidates) == (
        "mem_OLD",
    )


@pytest.mark.asyncio
async def test_conformance_matching_rejects_weak_overlap_and_normalizes_word_forms() -> None:
    provider = InMemoryProvider(
        InMemoryProviderConfig(project_id="project-alpha", dataset_id="project-alpha-memory")
    )
    await initialize(provider)
    provider_context = context()
    await provider.remember(
        RememberRequest(
            context=provider_context,
            request_id="mrq_remember_conformance_matching",
            idempotency_key="remember-conformance-matching",
            records=(
                memory_record(
                    "mem_CURRENT_ROUTE",
                    title="Current route decision",
                    summary="Route telemetry through the resilient polar relay.",
                ),
                memory_record(
                    "mem_RUNTIME_ZERO",
                    title="RUNTIME-ID-000000",
                    exact="Synthetic runtime record RUNTIME-ID-000000.",
                    summary="Exact compound identifier zero.",
                ),
                memory_record(
                    "mem_RUNTIME_ONE",
                    title="RUNTIME-ID-000001",
                    exact="Synthetic runtime record RUNTIME-ID-000001.",
                    summary="Exact compound identifier one.",
                ),
            ),
            authorization=policy(ProviderMutation.REMEMBER, provider_context),
        )
    )

    paraphrased = await provider.recall(
        RecallRequest(
            context=provider_context,
            request_id="mrq_recall_routing_form",
            query="Which routing decision is current?",
            mode=RetrievalMode.SEMANTIC,
        )
    )
    unsupported = await provider.recall(
        RecallRequest(
            context=provider_context,
            request_id="mrq_recall_unsupported_budget",
            query="What is project alpha's lunar propellant budget?",
            mode=RetrievalMode.HYBRID,
        )
    )
    compound_identifier = await provider.recall(
        RecallRequest(
            context=provider_context,
            request_id="mrq_recall_compound_identifier",
            query="RUNTIME-ID-000000",
            mode=RetrievalMode.HYBRID,
        )
    )

    assert [candidate.record.record_id for candidate in paraphrased.candidates] == [
        "mem_CURRENT_ROUTE"
    ]
    assert paraphrased.candidates[0].scores.semantic > 0.0
    assert unsupported.candidates == ()
    assert [candidate.record.record_id for candidate in compound_identifier.candidates] == [
        "mem_RUNTIME_ZERO"
    ]


@pytest.mark.asyncio
async def test_graph_recall_uses_a_bounded_one_hop_relation_index() -> None:
    provider = InMemoryProvider(
        InMemoryProviderConfig(project_id="project-alpha", dataset_id="project-alpha-memory")
    )
    await initialize(provider)
    provider_context = context()
    records = tuple(
        memory_record(
            f"mem_{name}",
            title=f"{name} evidence",
            exact=(
                "UNIQUE-ALPHA-SIGNAL"
                if name == "ALPHA"
                else f"Unrelated graph content {name}."
            ),
            summary=f"Graph evidence {name}.",
        )
        for name in ("ALPHA", "BETA", "GAMMA", "DELTA")
    )
    relations = tuple(
        relation_record(left.record_id, right.record_id).model_copy(
            update={"relation_id": f"rel_{left.record_id}_{right.record_id}"}
        )
        for left, right in zip(records[:-1], records[1:], strict=True)
    )
    await provider.remember(
        RememberRequest(
            context=provider_context,
            request_id="mrq_remember_relation_chain",
            idempotency_key="remember-relation-chain",
            records=records,
            relations=relations,
            authorization=policy(ProviderMutation.REMEMBER, provider_context),
        )
    )

    recalled = await provider.recall(
        RecallRequest(
            context=provider_context,
            request_id="mrq_recall_one_hop",
            query="UNIQUE-ALPHA-SIGNAL",
            mode=RetrievalMode.GRAPH,
        )
    )

    assert {candidate.record.record_id for candidate in recalled.candidates} == {
        "mem_ALPHA",
        "mem_BETA",
    }
    assert [relation.relation_id for relation in recalled.relations] == [
        "rel_mem_ALPHA_mem_BETA"
    ]


@pytest.mark.asyncio
async def test_record_version_update_replaces_cached_search_material() -> None:
    provider = InMemoryProvider(
        InMemoryProviderConfig(project_id="project-alpha", dataset_id="project-alpha-memory")
    )
    await initialize(provider)
    provider_context = context()
    first = memory_record(
        "mem_CACHE_UPDATE",
        title="Cache update fixture",
        exact="PRIORONLYTOKEN",
        summary="Prior cached search material.",
    )
    await provider.remember(
        RememberRequest(
            context=provider_context,
            request_id="mrq_remember_cache_prior",
            idempotency_key="remember-cache-prior",
            records=(first,),
            authorization=policy(ProviderMutation.REMEMBER, provider_context),
        )
    )
    replacement = memory_record(
        "mem_CACHE_UPDATE",
        title="Cache update fixture",
        exact="REPLACEMENTONLYTOKEN",
        summary="Replacement cached search material.",
        version=2,
    )
    await provider.remember(
        RememberRequest(
            context=provider_context,
            request_id="mrq_remember_cache_replacement",
            idempotency_key="remember-cache-replacement",
            records=(replacement,),
            authorization=policy(ProviderMutation.REMEMBER, provider_context),
        )
    )

    prior = await provider.recall(
        RecallRequest(
            context=provider_context,
            request_id="mrq_recall_cache_prior",
            query="PRIORONLYTOKEN",
            mode=RetrievalMode.SEMANTIC,
        )
    )
    current = await provider.recall(
        RecallRequest(
            context=provider_context,
            request_id="mrq_recall_cache_current",
            query="REPLACEMENTONLYTOKEN",
            mode=RetrievalMode.SEMANTIC,
        )
    )

    assert prior.candidates == ()
    assert [candidate.record.record_id for candidate in current.candidates] == [
        "mem_CACHE_UPDATE"
    ]


@pytest.mark.asyncio
async def test_project_isolation_and_missing_authorization_fail_closed() -> None:
    provider = InMemoryProvider(
        InMemoryProviderConfig(project_id="project-alpha", dataset_id="project-alpha-memory")
    )
    await initialize(provider)
    request = remember_request().model_copy(update={"authorization": None})
    with pytest.raises(MemoryProviderError) as denied:
        await provider.remember(request)
    assert denied.value.envelope.error.category is ErrorCategory.APPROVAL_REQUIRED

    foreign_context = context("project-beta", "project-beta-memory")
    with pytest.raises(MemoryProviderError) as isolated:
        await provider.health(HealthRequest(context=foreign_context))
    assert isolated.value.envelope.error.category is ErrorCategory.PERMISSION_DENIED


@pytest.mark.asyncio
async def test_forget_uses_matching_preview_and_is_idempotent() -> None:
    provider = InMemoryProvider(
        InMemoryProviderConfig(project_id="project-alpha", dataset_id="project-alpha-memory")
    )
    await initialize(provider)
    await provider.remember(remember_request())
    provider_context = context()
    preview = await provider.forget(
        ForgetRequest(
            context=provider_context,
            request_id="mrq_forget_preview",
            idempotency_key="forget-alpha",
            action=ForgetAction.DELETE_DERIVED,
            record_ids=("mem_ALPHA",),
            authorization=policy(ProviderMutation.FORGET, provider_context),
        )
    )
    execute_request = ForgetRequest(
        context=provider_context,
        request_id="mrq_forget_execute",
        idempotency_key="forget-alpha",
        action=ForgetAction.DELETE_DERIVED,
        record_ids=("mem_ALPHA",),
        execute=True,
        preview_digest=preview.impact_digest,
        authorization=policy(
            ProviderMutation.FORGET,
            provider_context,
            impact_digest=preview.impact_digest,
        ),
    )
    executed = await provider.forget(execute_request)
    replay = await provider.forget(
        execute_request.model_copy(update={"request_id": "mrq_forget_replay"})
    )

    assert executed.executed is True
    assert executed.canonical_source_changed is False
    assert replay.idempotent_replay is True
    remaining = await provider.recall(
        RecallRequest(
            context=provider_context,
            request_id="mrq_after_forget",
            query="Alpha requirement",
            mode=RetrievalMode.EXACT,
        )
    )
    assert remaining.candidates == ()


@pytest.mark.asyncio
async def test_snapshot_export_import_and_noop_migration_are_provider_neutral() -> None:
    provider_context = context()
    provider = InMemoryProvider(
        InMemoryProviderConfig(project_id="project-alpha", dataset_id="project-alpha-memory")
    )
    await initialize(provider)
    await provider.remember(remember_request())
    exported = await provider.export(
        ExportRequest(
            context=provider_context,
            request_id="mrq_export",
            idempotency_key="export-1",
            profile_versions={"base": "1.0.0"},
            authorization=policy(ProviderMutation.EXPORT, provider_context),
        )
    )
    assert exported.snapshot is not None
    assert exported.snapshot.checksums.package_sha256 == exported.checksum
    assert exported.record_count == 2
    json.dumps(exported.snapshot.to_json_dict())
    tampered = exported.snapshot.to_json_dict()
    tampered["records"][0]["title"] = "tampered without checksum update"
    with pytest.raises(ValidationError, match="checksum validation failed"):
        ProviderSnapshot.model_validate(tampered)

    target = InMemoryProvider(
        InMemoryProviderConfig(project_id="project-alpha", dataset_id="project-alpha-memory")
    )
    await initialize(target)
    preview = await target.import_snapshot(
        ImportRequest(
            context=provider_context,
            request_id="mrq_import_preview",
            idempotency_key="import-1",
            format=ProviderExportFormat.SYS4AI,
            snapshot=exported.snapshot,
            authorization=policy(ProviderMutation.IMPORT, provider_context),
        )
    )
    imported = await target.import_snapshot(
        ImportRequest(
            context=provider_context,
            request_id="mrq_import_execute",
            idempotency_key="import-1",
            format=ProviderExportFormat.SYS4AI,
            snapshot=exported.snapshot,
            execute=True,
            preview_digest=preview.impact_digest,
            authorization=policy(
                ProviderMutation.IMPORT,
                provider_context,
                impact_digest=preview.impact_digest,
            ),
        )
    )
    assert imported.executed is True
    recalled = await target.recall(
        RecallRequest(
            context=provider_context,
            request_id="mrq_imported_recall",
            query="Beta provider component",
            mode=RetrievalMode.EXACT,
        )
    )
    assert recalled.candidates

    migration_preview = await target.migrate(
        MigrationRequest(
            context=provider_context,
            request_id="mrq_migration_preview",
            idempotency_key="migrate-1",
            source_version="1.0.0",
            target_version="1.0.0",
            authorization=policy(ProviderMutation.MIGRATE, provider_context),
        )
    )
    migrated = await target.migrate(
        MigrationRequest(
            context=provider_context,
            request_id="mrq_migration_execute",
            idempotency_key="migrate-1",
            source_version="1.0.0",
            target_version="1.0.0",
            execute=True,
            preview_digest=migration_preview.impact_digest,
            authorization=policy(
                ProviderMutation.MIGRATE,
                provider_context,
                impact_digest=migration_preview.impact_digest,
            ),
        )
    )
    assert migrated.executed is True
    assert migrated.transformed_record_ids == ()


@pytest.mark.asyncio
async def test_liveness_is_available_before_initialization() -> None:
    provider = InMemoryProvider(
        InMemoryProviderConfig(project_id="project-alpha", dataset_id="project-alpha-memory")
    )
    liveness = await provider.health(
        HealthRequest(context=context(), probe=ProviderHealthProbe.LIVENESS)
    )
    readiness = await provider.health(
        HealthRequest(context=context(), probe=ProviderHealthProbe.READINESS)
    )

    assert liveness.state is ProviderHealthState.ALIVE
    assert readiness.state is ProviderHealthState.DEGRADED
