from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import pytest

from sys4ai_memory.authorization import (
    AuthorizationService,
    CanonicalPermissionEnvelopeLoader,
)
from sys4ai_memory.contracts import (
    MemoryRecord,
    MemoryScope,
    RetrievalMode,
    RetrievalResult,
    ScopeReference,
)
from sys4ai_memory.interfaces import DispatchResponse, DispatchSuccess, MemoryClient
from sys4ai_memory.providers import (
    CogneeProviderConfig,
    InMemoryProviderConfig,
    MemoryProvider,
    ProviderContext,
    ProviderInitializationRequest,
    ProviderMutation,
    RememberRequest,
)
from sys4ai_memory.providers.cognee import CogneeProvider
from sys4ai_memory.providers.in_memory import InMemoryProvider
from sys4ai_memory.retrieval import RetrievalEngine
from sys4ai_memory.security import InMemoryAuditSink, ProjectBoundary
from sys4ai_memory.service import MemoryService, ServiceComponents
from tests.providers.helpers import policy
from tests.providers.test_cognee import FakeCogneeRuntime
from tests.retrieval.helpers import memory_record
from tests.service.test_dispatcher import DATASET_ID, PROJECT_ID, _identity, _service

pytestmark = [pytest.mark.integration, pytest.mark.security, pytest.mark.acceptance]


def _context(trace_id: str) -> ProviderContext:
    return ProviderContext(
        project_id=PROJECT_ID,
        dataset_id=DATASET_ID,
        principal_id=_identity().principal_id,
        scope=ScopeReference(level=MemoryScope.PROJECT, scope_id=PROJECT_ID),
        trace_id=trace_id,
    )


def _provider_record() -> MemoryRecord:
    return memory_record(
        "mem_PROVIDER_SUBSTITUTION",
        project_id=PROJECT_ID,
        title="Provider substitution",
        content="Provider-neutral call shape survives adapter replacement.",
    )


async def _initialize_and_remember(provider: MemoryProvider) -> None:
    context = _context("trace_provider_substitution_setup")
    await provider.initialize(
        ProviderInitializationRequest(
            context=context,
            configuration_fingerprint="c" * 64,
            dry_run=False,
            path_boundaries_validated=True,
            exclusions_validated=True,
            discovery_dry_run_approved=True,
            authorization=policy(ProviderMutation.INITIALIZE, context),
        )
    )
    await provider.remember(
        RememberRequest(
            context=context,
            request_id="mrq_provider_substitution_seed",
            idempotency_key="provider-substitution-seed",
            records=(_provider_record(),),
            authorization=policy(ProviderMutation.REMEMBER, context),
        )
    )


def _compose_service(
    root: Path,
    provider: MemoryProvider,
) -> tuple[MemoryService, InMemoryAuditSink]:
    components = ServiceComponents()
    service, audit, _ = _service(root, components=components)
    boundary = ProjectBoundary(PROJECT_ID, DATASET_ID, root)
    authorization = AuthorizationService(
        CanonicalPermissionEnvelopeLoader(
            boundary,
            "control_records/memory/permissions.json",
        )
    )
    components.retrieval = RetrievalEngine(
        project_id=PROJECT_ID,
        dataset_id=DATASET_ID,
        authorizer=authorization,
        provider=provider,
    )
    return service, audit


def _agent_recall(service: MemoryService) -> DispatchResponse:
    return MemoryClient(
        service,
        identity=_identity(),
        project_id=PROJECT_ID,
        dataset_id=DATASET_ID,
    ).recall(
        "provider-neutral adapter replacement",
        mode=RetrievalMode.SEMANTIC,
        limit=5,
        request_id="mrq_provider_substitution_recall",
        trace_id="trace_provider_substitution_recall",
    )


def test_same_public_recall_shape_survives_provider_substitution(tmp_path: Path) -> None:
    real_cognee_was_loaded = "cognee" in sys.modules
    in_memory = InMemoryProvider(
        InMemoryProviderConfig(project_id=PROJECT_ID, dataset_id=DATASET_ID)
    )
    fake_runtime = FakeCogneeRuntime()
    cognee_root = (tmp_path / "cognee-project").resolve()
    cognee = CogneeProvider(
        CogneeProviderConfig(
            project_id=PROJECT_ID,
            dataset_id=DATASET_ID,
            project_root=str(cognee_root),
            derived_data_root=str(cognee_root / ".sys4ai/memory"),
            semantic_enabled=True,
            llm_provider="ollama",
            llm_model="local-test-model",
            llm_endpoint="http://127.0.0.1:11434",
            embedding_provider="fastembed",
            embedding_model="local-test-embedding",
            embedding_dimensions=384,
        ),
        runtime=fake_runtime,
    )
    asyncio.run(_initialize_and_remember(in_memory))
    asyncio.run(_initialize_and_remember(cognee))
    fake_runtime.recall_result = [
        {"score": 0.91, "external_metadata": item.external_metadata}
        for item in fake_runtime.items
        if item.external_metadata["sys4ai"]["kind"] == "record"  # type: ignore[index]
    ]

    in_memory_service, in_memory_audit = _compose_service(
        (tmp_path / "in-memory-service").resolve(),
        in_memory,
    )
    cognee_service, cognee_audit = _compose_service(
        (tmp_path / "cognee-service").resolve(),
        cognee,
    )
    in_memory_response = _agent_recall(in_memory_service)
    cognee_response = _agent_recall(cognee_service)

    assert isinstance(in_memory_response, DispatchSuccess)
    assert isinstance(cognee_response, DispatchSuccess)
    in_memory_result = RetrievalResult.model_validate(in_memory_response.result["retrieval"])
    cognee_result = RetrievalResult.model_validate(cognee_response.result["retrieval"])
    assert in_memory_result.request_id == cognee_result.request_id
    assert in_memory_result.trace_id == cognee_result.trace_id
    assert in_memory_result.mode is cognee_result.mode is RetrievalMode.SEMANTIC
    assert [item.record_id for item in in_memory_result.results] == [
        "mem_PROVIDER_SUBSTITUTION"
    ]
    assert [item.record_id for item in cognee_result.results] == [
        "mem_PROVIDER_SUBSTITUTION"
    ]
    assert in_memory_result.results[0].content == cognee_result.results[0].content
    assert in_memory_result.results[0].source == cognee_result.results[0].source
    assert set(in_memory_response.result) == set(cognee_response.result)
    assert [event.outcome for event in in_memory_audit.events()] == ["succeeded"]
    assert [event.outcome for event in cognee_audit.events()] == ["succeeded"]
    assert fake_runtime.calls == ["configure", "remember", "recall"]
    assert ("cognee" in sys.modules) is real_cognee_was_loaded
