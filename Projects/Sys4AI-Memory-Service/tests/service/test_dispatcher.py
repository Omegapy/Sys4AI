from __future__ import annotations

import asyncio
import json
from collections.abc import Callable, Mapping
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from threading import Lock
from time import sleep

from pydantic import JsonValue

from sys4ai_memory.authorization import (
    AuthorizationService,
    CanonicalPermissionEnvelopeLoader,
)
from sys4ai_memory.configuration import LoadedConfiguration, load_configuration
from sys4ai_memory.contracts import (
    AuthorityTier,
    ErrorCategory,
    ErrorEnvelope,
    MemoryScope,
    OperationName,
    Permission,
    RecordStatus,
    ScopeReference,
    Sensitivity,
    TrustClass,
)
from sys4ai_memory.exact_index import ExactIndex
from sys4ai_memory.ingestion import IngestionSynchronizer
from sys4ai_memory.interfaces import (
    MUTATING_ACTIONS,
    AuditContext,
    AuthorizationContext,
    ControlAction,
    DispatchRequest,
    DispatchSuccess,
    InterfaceAction,
    InterfaceIdentity,
    InterfaceKind,
)
from sys4ai_memory.lifecycle import LifecycleCatalog, LifecycleRecord
from sys4ai_memory.observability import AuditRecorder, VersionContext
from sys4ai_memory.providers import (
    InMemoryProviderConfig,
    PolicyEnvelope,
    ProviderContext,
    ProviderInitializationRequest,
    ProviderMutation,
)
from sys4ai_memory.providers.in_memory import InMemoryProvider
from sys4ai_memory.retrieval import RetrievalEngine
from sys4ai_memory.security import InMemoryAuditSink, ProjectBoundary
from sys4ai_memory.service import (
    EvidenceSynthesisRequest,
    EvidenceSynthesisResult,
    MemoryService,
    PortResult,
    ProviderAuthorizationBridge,
    ServiceComponents,
    SynthesisCitation,
    SynthesizedClaim,
)
from sys4ai_memory.sources import RegistryBundle, SourceRegistryEntry
from tests.retrieval.helpers import (
    StaticProvider,
    memory_record,
    provider_candidate,
    relation_record,
)

PROJECT_ROOT = Path(__file__).parents[2]
PROJECT_ID = "sys4ai-memory-service"
DATASET_ID = "sys4ai-memory-service"


def _configuration(
    root: Path,
    *,
    active: bool = True,
    read_only: bool = False,
) -> LoadedConfiguration:
    for relative in (
        "registries/memory_source_registry.csv",
        "registries/memory_profile_registry.csv",
        "registries/memory_relation_registry.csv",
        "control_records/memory/README.md",
    ):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("fixture\n", encoding="utf-8")
    text = (PROJECT_ROOT / "config/memory.toml").read_text(encoding="utf-8")
    if active:
        text = text.replace(
            "destructive_execution_enabled = false",
            "destructive_execution_enabled = true",
            1,
        )
        replacements = {
            'configuration_status = "approved-local-profile-inactive-provider"': (
                'configuration_status = "active-test"'
            ),
            'approval_policy_status = "approved-local-owner-single-review@1"': (
                'approval_policy_status = "approved-test"'
            ),
        }
        for before, after in replacements.items():
            text = text.replace(before, after)
    else:
        text = text.replace(
            'configuration_status = "approved-local-profile-inactive-provider"',
            'configuration_status = "disabled-test"',
            1,
        )
        text = text.replace("enabled = true", "enabled = false", 1)
    if read_only:
        text = text.replace("read_only = false", "read_only = true", 1)
        text = text.replace("mutation_enabled = true", "mutation_enabled = false", 1)
    path = root / "config/memory.toml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return load_configuration(path, trusted_project_root=root)


def _permissions(root: Path, *, operations: tuple[str, ...]) -> Path:
    path = root / "control_records/memory/permissions.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "revision": "permissions-service-1",
                "project_id": PROJECT_ID,
                "dataset_id": DATASET_ID,
                "issued_at": "2026-09-03T18:00:00Z",
                "grants": [
                    {
                        "grant_id": "service-all-operations",
                        "principal_id": "agent-service",
                        "permissions": [permission.value for permission in Permission],
                        "operations": list(operations),
                        "scopes": [
                            {
                                "level": "project",
                                "scope_id": PROJECT_ID,
                                "parent_scopes": [],
                            }
                        ],
                        "target_prefixes": [],
                        "shared_project_ids": [],
                        "valid_until": None,
                    }
                ],
                "approval_policy": None,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return path


def _versions() -> VersionContext:
    return VersionContext(
        configuration_version="1.0",
        configuration_fingerprint="a" * 64,
        profile_versions={"base": "1.0.0"},
        profile_fingerprints={"base": "b" * 64},
        provider_name="test-provider",
        provider_version="1.0.0",
        provider_fingerprint="c" * 64,
        source_registry_fingerprint="d" * 64,
    )


def _identity() -> InterfaceIdentity:
    return InterfaceIdentity(
        principal_id="agent-service",
        agent_type="test-agent",
        run_id="run-service",
    )


def _request(
    action: InterfaceAction,
    payload: Mapping[str, JsonValue],
    *,
    suffix: str,
    idempotency_key: str | None = None,
) -> DispatchRequest:
    return DispatchRequest(
        operation=action,
        request_id=f"mrq_{suffix}",
        trace_id=f"trace_{suffix}",
        authorization=AuthorizationContext(
            identity=_identity(),
            project_id=PROJECT_ID,
            dataset_id=DATASET_ID,
            scope={
                "level": "project",
                "scope_id": PROJECT_ID,
                "parent_scopes": [],
            },
            query_project_ids=(PROJECT_ID,),
        ),
        audit=AuditContext(
            interface=InterfaceKind.PYTHON,
            client_id="dispatcher-test",
            purpose="verify service dispatch",
        ),
        idempotency_key=idempotency_key,
        payload=dict(payload),
    )


def _payloads() -> dict[InterfaceAction, dict[str, JsonValue]]:
    return {
        OperationName.HEALTH: {"detailed": False},
        OperationName.SOURCES_LIST: {"include_excluded": False},
        OperationName.SOURCES_EXPLAIN: {"target": "README.md"},
        OperationName.SYNC: {"source_ids": [], "full": False, "dry_run": True},
        OperationName.RECALL: {"query": "source authority", "mode": "hybrid"},
        OperationName.GET: {"record_id": "mem_ALPHA"},
        OperationName.GRAPH: {"record_id": "mem_ALPHA"},
        OperationName.PROPOSE: {"proposal": {"record_type": "Observation"}},
        OperationName.APPROVE: {
            "proposal_id": "mwp_ALPHA",
            "decision": "approve",
            "reason": "reviewed",
        },
        OperationName.SUPERSEDE: {
            "record_id": "mem_ALPHA",
            "replacement_record_id": "mem_BETA",
            "reason": "new evidence",
        },
        OperationName.IMPROVE: {"feedback": {"relevant": True}},
        OperationName.FORGET: {
            "record_ids": ["mem_ALPHA"],
            "action": "expire",
            "reason": "retention",
            "execute": False,
        },
        OperationName.REBUILD: {"preview_only": True},
        OperationName.EXPORT: {"output_path": "exports/memory.zip"},
        OperationName.IMPORT: {"package_path": "imports/memory.zip", "activate": False},
        OperationName.EXPLAIN: {"record_id": "mem_ALPHA"},
        ControlAction.INITIALIZE_PREVIEW: {"configuration_path": "config/memory.toml"},
        ControlAction.INITIALIZE_DIRECT: {"configuration_path": "config/memory.toml"},
        ControlAction.INITIALIZE_APPLY: {
            "configuration_path": "config/memory.toml",
            "impact_digest": "e" * 64,
        },
    }


def _service(
    root: Path,
    *,
    active: bool = True,
    read_only: bool = False,
    handlers: Mapping[InterfaceAction, object] | None = None,
    components: ServiceComponents | None = None,
) -> tuple[MemoryService, InMemoryAuditSink, Path]:
    configuration = _configuration(root, active=active, read_only=read_only)
    operations = tuple(action.value for action in _payloads()) + (
        ControlAction.OPERATION_STATUS.value,
        "memory.initialize",
        "memory.import.activate",
        "memory.rebuild.activate",
    )
    permission_path = _permissions(root, operations=operations)
    boundary = ProjectBoundary(PROJECT_ID, DATASET_ID, root)
    loader = CanonicalPermissionEnvelopeLoader(
        boundary,
        "control_records/memory/permissions.json",
    )
    sink = InMemoryAuditSink()
    authorization = AuthorizationService(loader)
    service = MemoryService(
        configuration=configuration,
        authorization=authorization,
        audit=AuditRecorder(sink),
        versions=_versions(),
        components=components,
        provider_authorization=ProviderAuthorizationBridge(authorization, loader),
        handlers=handlers,  # type: ignore[arg-type]
    )
    return service, sink, permission_path


def test_dispatches_every_public_and_control_action_through_one_guarded_boundary(
    tmp_path: Path,
) -> None:
    calls: list[InterfaceAction] = []

    def handler(request: DispatchRequest, _payload: object) -> PortResult:
        calls.append(request.operation)
        if request.operation is OperationName.RECALL:
            return PortResult(
                result={
                    "retrieval": {
                        "evidence_state": "insufficient",
                        "results": [],
                        "filters_applied": {"omitted_result_count": 0},
                    }
                }
            )
        return PortResult(result={"handled": request.operation.value})

    handlers = {action: handler for action in _payloads()}
    service, sink, _ = _service(tmp_path.resolve(), handlers=handlers)
    long_operation_id: str | None = None

    for index, (action, payload) in enumerate(_payloads().items()):
        response = service.dispatch(
            _request(
                action,
                payload,
                suffix=f"all_{index}",
                idempotency_key=f"key-all-{index}" if action in MUTATING_ACTIONS else None,
            )
        )
        assert isinstance(response, DispatchSuccess)
        if response.operation_status is not None:
            assert response.operation_status.state.value == "succeeded"
            long_operation_id = response.operation_status.operation_id

    assert long_operation_id is not None
    status = service.dispatch(
        _request(
            ControlAction.OPERATION_STATUS,
            {"operation_id": long_operation_id},
            suffix="all_status",
        )
    )
    assert isinstance(status, DispatchSuccess)
    assert status.result["status"]["state"] == "succeeded"  # type: ignore[index]
    assert set(calls) == set(_payloads())
    audited = {event.operation for event in sink.events()}
    assert audited == {action.value for action in (*_payloads(), ControlAction.OPERATION_STATUS)}


def test_authorization_is_reread_and_project_boundary_fails_closed(tmp_path: Path) -> None:
    calls = 0

    def handler(_request: DispatchRequest, _payload: object) -> PortResult:
        nonlocal calls
        calls += 1
        return PortResult(result={"healthy": True})

    service, sink, permission_path = _service(
        tmp_path.resolve(),
        handlers={OperationName.HEALTH: handler},
    )
    first = service.dispatch(_request(OperationName.HEALTH, {}, suffix="fresh_first"))
    assert isinstance(first, DispatchSuccess)

    document = json.loads(permission_path.read_text(encoding="utf-8"))
    document["revision"] = "permissions-service-2"
    document["grants"] = []
    permission_path.write_text(json.dumps(document), encoding="utf-8")
    denied = service.dispatch(_request(OperationName.HEALTH, {}, suffix="fresh_denied"))

    assert isinstance(denied, ErrorEnvelope)
    assert denied.error.category is ErrorCategory.PERMISSION_DENIED
    assert calls == 1
    assert sink.events()[-1].outcome == "denied"


def test_disabled_configuration_blocks_work_but_keeps_health_available(tmp_path: Path) -> None:
    calls: list[str] = []

    def handler(request: DispatchRequest, _payload: object) -> PortResult:
        calls.append(request.operation.value)
        return PortResult(result={"handled": True})

    service, _, _ = _service(
        tmp_path.resolve(),
        active=False,
        handlers={OperationName.HEALTH: handler, OperationName.RECALL: handler},
    )
    health = service.dispatch(_request(OperationName.HEALTH, {}, suffix="disabled_health"))
    recall = service.dispatch(
        _request(
            OperationName.RECALL,
            {"query": "must remain disabled", "mode": "hybrid"},
            suffix="disabled_recall",
        )
    )

    assert isinstance(health, DispatchSuccess)
    assert isinstance(recall, ErrorEnvelope)
    assert recall.error.category is ErrorCategory.MEMORY_NOT_INITIALIZED
    assert calls == [OperationName.HEALTH.value]


def test_mutation_idempotency_prevents_duplicate_work_and_rejects_key_reuse(
    tmp_path: Path,
) -> None:
    calls = 0

    def handler(_request: DispatchRequest, _payload: object) -> PortResult:
        nonlocal calls
        calls += 1
        return PortResult(result={"sync_count": calls}, target_ids=("src_fixture",))

    service, _, _ = _service(
        tmp_path.resolve(),
        handlers={OperationName.SYNC: handler},
    )
    first = service.dispatch(
        _request(
            OperationName.SYNC,
            {"dry_run": True},
            suffix="idempotent_first",
            idempotency_key="same-logical-sync",
        )
    )
    replay = service.dispatch(
        _request(
            OperationName.SYNC,
            {"dry_run": True},
            suffix="idempotent_replay",
            idempotency_key="same-logical-sync",
        )
    )
    conflict = service.dispatch(
        _request(
            OperationName.SYNC,
            {"dry_run": True, "full": True},
            suffix="idempotent_conflict",
            idempotency_key="same-logical-sync",
        )
    )

    assert isinstance(first, DispatchSuccess)
    assert isinstance(replay, DispatchSuccess)
    assert replay.result["idempotent_replay"] is True
    assert first.operation_status is not None and replay.operation_status is not None
    assert first.operation_status.operation_id == replay.operation_status.operation_id
    assert isinstance(conflict, ErrorEnvelope)
    assert conflict.error.category is ErrorCategory.CONFLICT_DETECTED
    assert calls == 1


def test_failed_long_operation_can_retry_same_bound_attempt_then_replay(tmp_path: Path) -> None:
    calls = 0

    def handler(_request: DispatchRequest, _payload: object) -> PortResult:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("transient provider detail")
        return PortResult(result={"sync_count": calls})

    service, _, _ = _service(
        tmp_path.resolve(),
        handlers={OperationName.SYNC: handler},
    )
    first = service.dispatch(
        _request(
            OperationName.SYNC,
            {"dry_run": True},
            suffix="retry_failed",
            idempotency_key="retryable-sync",
        )
    )
    second = service.dispatch(
        _request(
            OperationName.SYNC,
            {"dry_run": True},
            suffix="retry_succeeded",
            idempotency_key="retryable-sync",
        )
    )
    third = service.dispatch(
        _request(
            OperationName.SYNC,
            {"dry_run": True},
            suffix="retry_replay",
            idempotency_key="retryable-sync",
        )
    )

    assert isinstance(first, ErrorEnvelope)
    assert first.error.category is ErrorCategory.INGESTION_FAILED
    assert isinstance(second, DispatchSuccess)
    assert isinstance(third, DispatchSuccess)
    assert second.operation_status is not None
    status = service.operations.get(second.operation_status.operation_id)
    assert status.state.value == "succeeded"
    assert status.attempt == 2
    assert third.result["idempotent_replay"] is True
    assert calls == 2


def test_failures_are_normalized_and_detailed_health_exposes_metadata_only_metrics(
    tmp_path: Path,
) -> None:
    def failure(_request: DispatchRequest, _payload: object) -> PortResult:
        raise RuntimeError("password=must-not-escape")

    failed_service, _, _ = _service(
        (tmp_path / "failed").resolve(),
        handlers={OperationName.HEALTH: failure},
    )
    failed = failed_service.dispatch(_request(OperationName.HEALTH, {}, suffix="safe_failure"))
    assert isinstance(failed, ErrorEnvelope)
    assert "must-not-escape" not in json.dumps(failed.model_dump(mode="json"))

    health_service, _, _ = _service((tmp_path / "health").resolve())
    detailed = health_service.dispatch(
        _request(OperationName.HEALTH, {"detailed": True}, suffix="detailed_health")
    )
    assert isinstance(detailed, DispatchSuccess)
    assert detailed.result["metrics"]["project_id"] == PROJECT_ID  # type: ignore[index]
    assert "configuration_status" in detailed.result


def test_supersede_rejects_foreign_records_before_lifecycle_mutation(tmp_path: Path) -> None:
    lifecycle = LifecycleCatalog()
    observed = datetime(2026, 9, 3, 18, tzinfo=UTC)
    for record_id in ("mem_FOREIGN_OLD", "mem_FOREIGN_NEW"):
        lifecycle.add(
            LifecycleRecord(
                record_id=record_id,
                project_id="foreign-project",
                dataset_id="foreign-dataset",
                status=RecordStatus.ACTIVE,
                authority_tier=AuthorityTier.CANONICAL_PROJECT_KNOWLEDGE,
                trust_class=TrustClass.PROJECT_AUTHORED,
                sensitivity=Sensitivity.INTERNAL,
                canonical=False,
                source_ids=("src_foreign",),
                valid_from=observed,
            )
        )
    service, _, _ = _service(
        tmp_path.resolve(),
        components=ServiceComponents(lifecycle=lifecycle),
    )

    response = service.dispatch(
        _request(
            OperationName.SUPERSEDE,
            {
                "record_id": "mem_FOREIGN_OLD",
                "replacement_record_id": "mem_FOREIGN_NEW",
                "reason": "must not cross project boundary",
            },
            suffix="foreign_supersede",
            idempotency_key="foreign-supersede-key",
        )
    )

    assert isinstance(response, ErrorEnvelope)
    assert response.error.category is ErrorCategory.AUTHORITY_VIOLATION
    assert lifecycle.get("mem_FOREIGN_OLD").status is RecordStatus.ACTIVE
    assert lifecycle.get("mem_FOREIGN_NEW").status is RecordStatus.ACTIVE


def test_builtin_sync_returns_revision_delta_checkpoint_generation_and_receipt(
    tmp_path: Path,
) -> None:
    root = tmp_path.resolve()
    source_path = root / "docs/source.md"
    source_path.parent.mkdir(parents=True)
    source_path.write_text(
        "# Requirement\n\nREQ-SYNC-001 requires source-first synchronization.\n",
        encoding="utf-8",
    )
    source = SourceRegistryEntry(
        source_id="src_sync_fixture",
        project_id=PROJECT_ID,
        path_or_uri="docs/source.md",
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
        notes="sync fixture",
    )
    registry = RegistryBundle(sources=(source,), profiles=(), relations=())
    provider = InMemoryProvider(
        InMemoryProviderConfig(project_id=PROJECT_ID, dataset_id=DATASET_ID)
    )
    context = ProviderContext(
        project_id=PROJECT_ID,
        dataset_id=DATASET_ID,
        principal_id="agent-service",
        scope=ScopeReference(level=MemoryScope.PROJECT, scope_id=PROJECT_ID),
        trace_id="trace_provider_initialize",
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
                    decision_id="decision_initialize_fixture",
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

    with ExactIndex(":memory:") as index:
        components = ServiceComponents(
            registry_loader=lambda: registry,
            synchronizer=IngestionSynchronizer(project_root=root, index_writer=index),
            exact_index=index,
            provider=provider,
        )
        service, _, _ = _service(root, components=components)
        response = service.dispatch(
            _request(
                OperationName.SYNC,
                {"dry_run": False, "full": False, "source_ids": []},
                suffix="builtin_sync",
                idempotency_key="builtin-sync-key",
            )
        )

        assert isinstance(response, DispatchSuccess)
        assert response.result["generation_id"].startswith("gen_")  # type: ignore[union-attr]
        assert response.result["delta"]["added"] == 1  # type: ignore[index]
        assert response.result["manifest"]["sources"][0]["source_id"] == (  # type: ignore[index]
            "src_sync_fixture"
        )
        assert response.result["checkpoint"]["completed_revisions"][0][  # type: ignore[index]
            "source_id"
        ] == "src_sync_fixture"
        receipt = response.result["receipt"]
        assert receipt["source_manifest_sha256"]  # type: ignore[index]
        assert receipt["receipt_sha256"]  # type: ignore[index]
        assert receipt["generation_id"] == response.result["generation_id"]  # type: ignore[index]
        assert response.result["provider"]["record_ids"]  # type: ignore[index]
        assert index.query_exact(
            project_id=PROJECT_ID,
            query="REQ-SYNC-001",
            case_sensitive=True,
        )


def test_builtin_graph_returns_typed_one_hop_path_and_retrieval_trace(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    components = ServiceComponents()
    service, sink, _ = _service(root, components=components)
    boundary = ProjectBoundary(PROJECT_ID, DATASET_ID, root)
    authorization = AuthorizationService(
        CanonicalPermissionEnvelopeLoader(
            boundary,
            "control_records/memory/permissions.json",
        )
    )
    start = memory_record(
        "mem_service_graph_start",
        project_id=PROJECT_ID,
        source_id="src_service_graph_start",
    )
    end = memory_record(
        "mem_service_graph_end",
        project_id=PROJECT_ID,
        source_id="src_service_graph_end",
    )
    relation = relation_record(
        "rel_service_graph",
        start.record_id,
        end.record_id,
        state="deterministic",
        confidence=None,
    ).model_copy(update={"project_id": PROJECT_ID})
    components.retrieval = RetrievalEngine(
        project_id=PROJECT_ID,
        dataset_id=DATASET_ID,
        authorizer=authorization,
        provider=StaticProvider(
            (
                provider_candidate(start, graph=1.0),
                provider_candidate(end, graph=0.9),
            ),
            relations=(relation,),
        ),
        clock=lambda: datetime(2026, 9, 3, 18, tzinfo=UTC),
    )

    response = service.dispatch(
        _request(
            OperationName.GRAPH,
            {
                "record_id": start.record_id,
                "max_depth": 1,
                "relation_types": ["IMPLEMENTS"],
            },
            suffix="builtin_graph",
        )
    )

    assert isinstance(response, DispatchSuccess)
    graph = response.result["graph"]
    assert graph["evidence_state"] == "sufficient"  # type: ignore[index]
    assert graph["paths"][0]["start_record_id"] == start.record_id  # type: ignore[index]
    assert graph["paths"][0]["end_record_id"] == end.record_id  # type: ignore[index]
    assert graph["paths"][0]["relation"]["relation_id"] == relation.relation_id  # type: ignore[index]
    assert response.result["retrieval"]["results"]  # type: ignore[index]
    graph_event = sink.events()[-1]
    assert graph_event.operation == OperationName.GRAPH.value
    assert graph_event.target_ids == (
        end.record_id,
        start.record_id,
        relation.relation_id,
    )


class _FixtureSynthesizer:
    def __init__(self) -> None:
        self.calls: list[EvidenceSynthesisRequest] = []
        self.return_invalid_anchor = False
        self.after_call: Callable[[], None] | None = None

    async def synthesize(
        self,
        request: EvidenceSynthesisRequest,
    ) -> EvidenceSynthesisResult:
        self.calls.append(request)
        evidence = request.evidence.results[0]
        source = evidence.source
        if self.return_invalid_anchor:
            source = source.model_copy(update={"path": "docs/not-in-evidence.md"})
        result = EvidenceSynthesisResult(
            request_id=request.request_id,
            project_id=request.project_id,
            provider_name="fixture-synthesizer",
            model_profile_id=request.llm_profile_id,
            answer="The cited source contains the requested evidence.",
            claims=(
                SynthesizedClaim(
                    claim="The requested evidence is present.",
                    citations=(
                        SynthesisCitation(
                            record_id=evidence.record_id,
                            source_id=evidence.source.source_id,
                            source=source,
                        ),
                    ),
                ),
            ),
            trace_id=request.trace_id,
        )
        if self.after_call is not None:
            self.after_call()
        return result


def test_recall_synthesis_is_explicit_and_rejects_uncited_evidence(
    tmp_path: Path,
) -> None:
    root = tmp_path.resolve()
    components = ServiceComponents()
    service, sink, permission_path = _service(root, components=components)
    original_permissions = permission_path.read_text(encoding="utf-8")
    boundary = ProjectBoundary(PROJECT_ID, DATASET_ID, root)
    authorization = AuthorizationService(
        CanonicalPermissionEnvelopeLoader(
            boundary,
            "control_records/memory/permissions.json",
        )
    )
    evidence = memory_record(
        "mem_synthesis_evidence",
        project_id=PROJECT_ID,
        source_id="src_synthesis_evidence",
        content="The source-backed fixture establishes the requested fact.",
    )
    components.retrieval = RetrievalEngine(
        project_id=PROJECT_ID,
        dataset_id=DATASET_ID,
        authorizer=authorization,
        provider=StaticProvider((provider_candidate(evidence, semantic=0.9),)),
        clock=lambda: datetime(2026, 9, 3, 18, tzinfo=UTC),
    )
    missing_port = service.dispatch(
        _request(
            OperationName.RECALL,
            {
                "query": "What fact is established?",
                "mode": "semantic",
                "synthesize": True,
            },
            suffix="recall_with_missing_synthesis_port",
        )
    )
    assert isinstance(missing_port, ErrorEnvelope)
    assert missing_port.error.category is ErrorCategory.MEMORY_NOT_INITIALIZED

    synthesizer = _FixtureSynthesizer()
    components.synthesis = synthesizer

    retrieval_only = service.dispatch(
        _request(
            OperationName.RECALL,
            {"query": "What fact is established?", "mode": "semantic"},
            suffix="recall_without_synthesis",
        )
    )
    assert isinstance(retrieval_only, DispatchSuccess)
    assert retrieval_only.result["synthesis_requested"] is False
    assert retrieval_only.result["synthesis_state"] == "not_requested"
    assert retrieval_only.result["synthesis"] is None
    assert not synthesizer.calls

    synthesized = service.dispatch(
        _request(
            OperationName.RECALL,
            {
                "query": "What fact is established?",
                "mode": "semantic",
                "synthesize": True,
            },
            suffix="recall_with_synthesis",
        )
    )
    assert isinstance(synthesized, DispatchSuccess)
    assert synthesized.result["synthesis_state"] == "completed"
    answer = synthesized.result["synthesis"]
    assert answer["material_claims_cited"] is True  # type: ignore[index]
    assert answer["claims"][0]["citations"][0]["record_id"] == evidence.record_id  # type: ignore[index]
    assert len(synthesizer.calls) == 1

    synthesizer.return_invalid_anchor = True
    invalid = service.dispatch(
        _request(
            OperationName.RECALL,
            {
                "query": "What fact is established?",
                "mode": "semantic",
                "synthesize": True,
            },
            suffix="recall_with_invalid_synthesis",
        )
    )
    assert isinstance(invalid, ErrorEnvelope)
    assert invalid.error.category is ErrorCategory.SCHEMA_INVALID

    def revoke_permission() -> None:
        document = json.loads(permission_path.read_text(encoding="utf-8"))
        document["revision"] = "permissions-revoked-during-synthesis"
        document["grants"] = []
        permission_path.write_text(json.dumps(document), encoding="utf-8")

    synthesizer.return_invalid_anchor = False
    synthesizer.after_call = revoke_permission
    revoked = service.dispatch(
        _request(
            OperationName.RECALL,
            {
                "query": "What fact is established?",
                "mode": "semantic",
                "synthesize": True,
            },
            suffix="recall_revoked_during_synthesis",
        )
    )
    assert isinstance(revoked, ErrorEnvelope)
    assert revoked.error.category is ErrorCategory.PERMISSION_DENIED
    assert any(event.outcome == "denied" for event in sink.events())
    permission_path.write_text(original_permissions, encoding="utf-8")

    synthesizer.after_call = None
    components.retrieval = RetrievalEngine(
        project_id=PROJECT_ID,
        dataset_id=DATASET_ID,
        authorizer=authorization,
        provider=StaticProvider(),
        clock=lambda: datetime(2026, 9, 3, 18, tzinfo=UTC),
    )
    call_count = len(synthesizer.calls)
    insufficient = service.dispatch(
        _request(
            OperationName.RECALL,
            {
                "query": "What fact is established?",
                "mode": "semantic",
                "synthesize": True,
            },
            suffix="recall_with_insufficient_evidence",
        )
    )
    assert isinstance(insufficient, DispatchSuccess)
    assert insufficient.result["synthesis_state"] == "insufficient_evidence"
    assert insufficient.result["synthesis"] is None
    assert len(synthesizer.calls) == call_count


def test_service_serializes_concurrent_mutations(tmp_path: Path) -> None:
    counter_lock = Lock()
    active_calls = 0
    maximum_active = 0

    def handler(_request: DispatchRequest, _payload: object) -> PortResult:
        nonlocal active_calls, maximum_active
        with counter_lock:
            active_calls += 1
            maximum_active = max(maximum_active, active_calls)
        sleep(0.005)
        with counter_lock:
            active_calls -= 1
        return PortResult(result={"serialized": True})

    service, _, _ = _service(
        tmp_path.resolve(),
        handlers={OperationName.PROPOSE: handler},
    )

    def dispatch(index: int):
        return service.dispatch(
            _request(
                OperationName.PROPOSE,
                {"proposal": {"record_type": "Observation"}},
                suffix=f"concurrent_{index}",
                idempotency_key=f"concurrent-key-{index}",
            )
        )

    with ThreadPoolExecutor(max_workers=8) as executor:
        responses = tuple(executor.map(dispatch, range(16)))

    assert all(isinstance(response, DispatchSuccess) for response in responses)
    assert maximum_active == 1


def test_read_only_service_disables_mutation_before_handler(tmp_path: Path) -> None:
    calls = 0

    def handler(_request: DispatchRequest, _payload: object) -> PortResult:
        nonlocal calls
        calls += 1
        return PortResult(result={"must_not_run": True})

    service, _, _ = _service(
        tmp_path.resolve(),
        active=True,
        read_only=True,
        handlers={OperationName.PROPOSE: handler},
    )
    response = service.dispatch(
        _request(
            OperationName.PROPOSE,
            {"proposal": {"record_type": "Observation"}},
            suffix="read_only_propose",
            idempotency_key="read-only-propose",
        )
    )

    assert isinstance(response, ErrorEnvelope)
    assert response.error.category is ErrorCategory.APPROVAL_REQUIRED
    assert calls == 0


def test_builtin_initialization_preview_reports_sources_without_writing(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    source_path = root / "README.md"
    source_path.write_text("# Fixture\n", encoding="utf-8")
    source = SourceRegistryEntry(
        source_id="src_initialize_fixture",
        project_id=PROJECT_ID,
        path_or_uri="README.md",
        path_pattern=None,
        source_kind="file",
        format="markdown",
        canonicality="canonical",
        content_role="project-guide",
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
        notes="initialization fixture",
    )
    registry = RegistryBundle(sources=(source,), profiles=(), relations=())
    service, _, _ = _service(
        root,
        active=False,
        components=ServiceComponents(registry_loader=lambda: registry),
    )

    response = service.dispatch(
        _request(
            ControlAction.INITIALIZE_PREVIEW,
            {"configuration_path": "config/memory.toml"},
            suffix="builtin_initialize_preview",
        )
    )

    assert isinstance(response, DispatchSuccess)
    preview = response.result["preview"]
    assert preview["included_source_count"] == 1  # type: ignore[index]
    assert preview["impact_digest"]  # type: ignore[index]
    assert {
        item["relative_path"] for item in preview["planned_paths"]  # type: ignore[index,union-attr]
    } == {
        ".sys4ai/memory",
        ".sys4ai/memory/exact_index",
        ".sys4ai/memory/provider",
        ".sys4ai/memory/generations",
        ".sys4ai/memory/staging",
        ".sys4ai/memory/exports",
        ".sys4ai/memory/audit",
        ".sys4ai/memory/receipts",
        ".sys4ai/memory/models",
    }
    assert not (root / ".sys4ai/memory").exists()
