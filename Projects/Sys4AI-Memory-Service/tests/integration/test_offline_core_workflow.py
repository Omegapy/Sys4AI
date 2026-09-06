from __future__ import annotations

import socket
from pathlib import Path

import pytest

from sys4ai_memory.authorization import (
    AuthorizationService,
    CanonicalPermissionEnvelopeLoader,
)
from sys4ai_memory.contracts import (
    AuthorityTier,
    RetrievalMode,
    Sensitivity,
    TrustClass,
)
from sys4ai_memory.exact_index import ExactIndex
from sys4ai_memory.ingestion import IngestionSynchronizer, available_adapters
from sys4ai_memory.interfaces import DispatchSuccess, MemoryClient
from sys4ai_memory.providers import (
    IN_MEMORY_PROVIDER_VERSION,
    InMemoryProviderConfig,
    ProviderInitializationRequest,
    ProviderMutation,
)
from sys4ai_memory.providers.in_memory import InMemoryProvider
from sys4ai_memory.rebuild import GenerationRebuilder, ProviderStage
from sys4ai_memory.retrieval import RetrievalEngine
from sys4ai_memory.security import ProjectBoundary
from sys4ai_memory.service import ServiceComponents
from sys4ai_memory.sources import RegistryBundle, SourceRegistryEntry
from tests.integration.test_exchange_flow import (
    _attach_disposable_exchange,
    _initialize_provider,
)
from tests.providers.helpers import context, policy
from tests.service.test_dispatcher import DATASET_ID, PROJECT_ID, _identity, _service

pytestmark = [pytest.mark.integration, pytest.mark.security, pytest.mark.acceptance]


class _OfflineProviderStageFactory:
    async def __call__(self, generation_root: Path, generation_id: str) -> ProviderStage:
        assert generation_root.name == "provider"
        provider = InMemoryProvider(
            InMemoryProviderConfig(project_id=PROJECT_ID, dataset_id=DATASET_ID)
        )
        provider_context = context(
            PROJECT_ID,
            DATASET_ID,
            trace_id=f"trace_offline_{generation_id}",
        )
        await provider.initialize(
            ProviderInitializationRequest(
                context=provider_context,
                configuration_fingerprint="c" * 64,
                dry_run=False,
                path_boundaries_validated=True,
                exclusions_validated=True,
                discovery_dry_run_approved=True,
                authorization=policy(ProviderMutation.INITIALIZE, provider_context),
            )
        )
        return ProviderStage(
            provider=provider,
            context=provider_context,
            remember_authorization=policy(ProviderMutation.REMEMBER, provider_context),
            export_authorization=policy(ProviderMutation.EXPORT, provider_context),
        )


def _source() -> SourceRegistryEntry:
    return SourceRegistryEntry(
        source_id="src_offline_core",
        project_id=PROJECT_ID,
        path_or_uri="docs/offline-core.md",
        path_pattern=None,
        source_kind="file",
        format="markdown",
        canonicality="canonical",
        content_role="requirement",
        authority_tier=AuthorityTier.CANONICAL_PROJECT_KNOWLEDGE,
        trust_class=TrustClass.PROJECT_AUTHORED,
        sensitivity=Sensitivity.INTERNAL,
        namespace="project/offline",
        profile_id="base@1",
        ingestion_adapter="markdown",
        chunking_profile="heading-blocks@1",
        schema_ref=None,
        refresh_mode="content-hash",
        retention_policy="canonical",
        owner="project",
        write_policy="reviewed-project-change",
        include_flag=True,
        notes="offline core acceptance fixture",
    )


def test_core_service_workflow_completes_with_all_network_access_denied(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def reject_network(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("offline core workflow attempted network access")

    monkeypatch.setattr(socket.socket, "connect", reject_network)
    monkeypatch.setattr(socket, "create_connection", reject_network)
    root = tmp_path.resolve()
    canonical = root / "docs/offline-core.md"
    canonical.parent.mkdir()
    canonical.write_text(
        "# Offline core requirement\n\n"
        "OFFLINE-CORE-001 requires local operation without a managed cloud service.\n",
        encoding="utf-8",
    )
    canonical_before = canonical.read_bytes()
    registry = RegistryBundle(sources=(_source(),), profiles=(), relations=())
    provider = InMemoryProvider(
        InMemoryProviderConfig(project_id=PROJECT_ID, dataset_id=DATASET_ID)
    )
    _initialize_provider(provider)

    with ExactIndex(":memory:") as index:
        components = ServiceComponents(
            registry_loader=lambda: registry,
            synchronizer=IngestionSynchronizer(project_root=root, index_writer=index),
            exact_index=index,
            provider=provider,
        )
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
            exact_backend=index,
            exact_record_resolver=index,
            provider=provider,
        )
        components.rebuild = GenerationRebuilder(
            boundary=boundary,
            registry=registry,
            derived_root=".sys4ai/memory",
            profile_versions={"base@1": "1.0.0"},
            profile_registry_sha256="b" * 64,
            schema_paths=(),
            configuration_sha256="c" * 64,
            adapter_versions={name: "1.0.0" for name in available_adapters()},
            provider_name="in_memory",
            provider_version=IN_MEMORY_PROVIDER_VERSION,
            model_identifiers=("deterministic-no-model",),
            provider_factory=_OfflineProviderStageFactory(),
        )
        _attach_disposable_exchange(root, provider, components)
        client = MemoryClient(
            service,
            identity=_identity(),
            project_id=PROJECT_ID,
            dataset_id=DATASET_ID,
        )

        listed = client.sources_list(
            request_id="mrq_offline_sources",
            trace_id="trace_offline_sources",
        )
        synchronized = client.sync(
            idempotency_key="offline-sync",
            request_id="mrq_offline_sync",
            trace_id="trace_offline_sync",
        )
        recalled = client.recall(
            "OFFLINE-CORE-001",
            mode=RetrievalMode.HYBRID,
            request_id="mrq_offline_recall",
            trace_id="trace_offline_recall",
        )
        rebuild_preview = client.rebuild(
            idempotency_key="offline-rebuild-preview",
            request_id="mrq_offline_rebuild_preview",
            trace_id="trace_offline_rebuild_preview",
        )
        assert isinstance(rebuild_preview, DispatchSuccess)
        preview = rebuild_preview.result["preview"]
        assert isinstance(preview, dict)
        rebuilt = client.rebuild(
            idempotency_key="offline-rebuild-execute",
            preview_only=False,
            operation_id=preview["operation_id"],
            impact_digest=preview["impact_digest"],
            request_id="mrq_offline_rebuild_execute",
            trace_id="trace_offline_rebuild_execute",
        )
        exported = client.export(
            "exports/offline-memory.zip",
            idempotency_key="offline-export",
            request_id="mrq_offline_export",
            trace_id="trace_offline_export",
        )
        healthy = client.health(
            detailed=True,
            request_id="mrq_offline_health",
            trace_id="trace_offline_health",
        )

    for response in (listed, synchronized, recalled, rebuilt, exported, healthy):
        assert isinstance(response, DispatchSuccess)
    assert listed.result["source_count"] == 1  # type: ignore[union-attr]
    assert synchronized.result["record_count"] >= 1  # type: ignore[union-attr]
    rows = recalled.result["retrieval"]["results"]  # type: ignore[index, union-attr]
    assert any(row["source"]["source_id"] == "src_offline_core" for row in rows)  # type: ignore[index]
    assert rebuilt.result["receipt"]["activated"] is True  # type: ignore[index, union-attr]
    assert exported.result["production_ready"] is False  # type: ignore[union-attr]
    assert healthy.result["configuration_status"] == "active-test"  # type: ignore[union-attr]
    assert (root / "exports/offline-memory.zip").is_file()
    assert canonical.read_bytes() == canonical_before
    assert [event.outcome for event in audit.events()].count("failed") == 0
