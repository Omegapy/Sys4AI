"""Fail-closed composition root for the provider-neutral memory service."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Callable, Coroutine, Mapping
from concurrent.futures import ThreadPoolExecutor
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from threading import RLock
from time import perf_counter
from typing import Any

from pydantic import BaseModel, JsonValue, TypeAdapter

from sys4ai_memory.authorization import (
    AuthorizationDecision,
    AuthorizationRequest,
    AuthorizationService,
    PermissionDeniedError,
)
from sys4ai_memory.configuration import LoadedConfiguration, load_configuration
from sys4ai_memory.contracts import (
    API_VERSION,
    SCHEMA_VERSION,
    ErrorCategory,
    EvidenceState,
    OperationName,
    Permission,
    PolicyAction,
    RecordStatus,
    RetrievalMode,
    RetrievalResult,
    WriteProposal,
)
from sys4ai_memory.contracts.models import RequesterIdentity
from sys4ai_memory.contracts.operations import operation_by_name
from sys4ai_memory.ingestion import SourceManifest, SyncCheckpoint
from sys4ai_memory.initialization import (
    InitializationPreview,
    apply_initialization,
    build_initialization_preview,
    initialize_memory,
    preflight_initialization,
)
from sys4ai_memory.interfaces.dispatcher import ServiceDispatchFailure, error_envelope
from sys4ai_memory.interfaces.models import (
    MUTATING_ACTIONS,
    ApproveInput,
    ControlAction,
    DispatchRequest,
    DispatchResponse,
    DispatchSuccess,
    ExplainInput,
    ExportInput,
    ForgetInput,
    GetInput,
    GraphInput,
    HealthInput,
    ImportInput,
    ImproveInput,
    InitializationApplyInput,
    InitializationDirectInput,
    InitializationPreviewInput,
    InterfaceAction,
    LongOperationReference,
    OperationInput,
    OperationStatusInput,
    ProposeInput,
    RebuildInput,
    RecallInput,
    SourcesExplainInput,
    SourcesListInput,
    SupersedeInput,
    SyncInput,
)
from sys4ai_memory.lifecycle import DestructiveRequest, ForgetMode
from sys4ai_memory.observability import (
    AuditRecorder,
    CountMetric,
    MetricsCollector,
    OperationState,
    OperationStatus,
    OperationTracker,
    RecallChannelCount,
    RecallFilterTrace,
    RecallRankingTrace,
    RecallTrace,
    VersionContext,
)
from sys4ai_memory.policies import (
    ImprovementRequest,
    ReviewDisposition,
    StagedProposalArtifact,
    WriteRequest,
)
from sys4ai_memory.providers import (
    ImproveRequest as ProviderImproveRequest,
)
from sys4ai_memory.providers import (
    ProviderContext,
    ProviderMutation,
    RememberRequest,
)
from sys4ai_memory.rebuild import AuthorizedRebuildImpact, RebuildMode
from sys4ai_memory.retrieval import ContextBudget, RecallQuery
from sys4ai_memory.security import IdempotencyConflictError, ProjectIsolationError
from sys4ai_memory.sources import RegistryBundle, SourceDiscovery, SourceRegistryEntry
from sys4ai_memory.util import canonical_json_bytes, sha256_bytes, stable_id, utc_now

from .authorization import ProviderAuthorizationBridge
from .errors import normalize_service_exception
from .models import (
    EvidenceSynthesisRequest,
    EvidenceSynthesisResult,
    ImprovementSubmission,
    PortableExportCall,
    PortableImportCall,
    PortResult,
    ProposalSubmission,
)
from .ports import ServiceComponents

_JSON_OBJECT = TypeAdapter(dict[str, JsonValue])

type ServiceHandler = Callable[
    [DispatchRequest, OperationInput],
    PortResult | Coroutine[Any, Any, PortResult],
]


@dataclass(frozen=True, slots=True)
class _IdempotentResult:
    fingerprint: str
    result: dict[str, JsonValue]
    target_ids: tuple[str, ...]
    operation_id: str | None
    recall_trace: RecallTrace | None


def _run_coroutine[T](coroutine: Coroutine[Any, Any, T]) -> T:
    """Run one adapter coroutine from sync clients or an active ASGI event loop."""

    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coroutine)
    with ThreadPoolExecutor(max_workers=1, thread_name_prefix="sys4ai-memory") as executor:
        return executor.submit(asyncio.run, coroutine).result()


def _model_object(model: BaseModel) -> dict[str, JsonValue]:
    return _JSON_OBJECT.validate_python(model.model_dump(mode="json", exclude_none=False))


def _source_projection(entry: SourceRegistryEntry) -> dict[str, JsonValue]:
    return {
        "source_id": entry.source_id,
        "project_id": entry.project_id,
        "path_or_uri": entry.path_or_uri,
        "path_pattern": entry.path_pattern,
        "source_kind": entry.source_kind,
        "format": entry.format,
        "canonicality": entry.canonicality,
        "content_role": entry.content_role,
        "authority_tier": entry.authority_tier.value,
        "trust_class": entry.trust_class.value,
        "sensitivity": entry.sensitivity.value,
        "namespace": entry.namespace,
        "profile_id": entry.profile_id,
        "ingestion_adapter": entry.ingestion_adapter,
        "chunking_profile": entry.chunking_profile,
        "refresh_mode": entry.refresh_mode,
        "retention_policy": entry.retention_policy,
        "owner": entry.owner,
        "write_policy": entry.write_policy,
        "include_flag": entry.include_flag,
        "one_time": entry.one_time,
    }


class MemoryService:
    """Authorize, gate, route, audit, meter, and track every interface request."""

    def __init__(
        self,
        *,
        configuration: LoadedConfiguration,
        authorization: AuthorizationService,
        audit: AuditRecorder,
        versions: VersionContext,
        components: ServiceComponents | None = None,
        provider_authorization: ProviderAuthorizationBridge | None = None,
        metrics: MetricsCollector | None = None,
        operations: OperationTracker | None = None,
        handlers: Mapping[InterfaceAction, ServiceHandler] | None = None,
        policy_decision_ref: str = "control_records/memory/permissions.json",
        initialize_provider: Callable[[], bool] | None = None,
        sync_manifest: SourceManifest | None = None,
        sync_checkpoint: SyncCheckpoint | None = None,
    ) -> None:
        memory = configuration.configuration.memory
        self._configuration = configuration
        self._authorization = authorization
        self._audit = audit
        self._versions = versions
        self._components = components or ServiceComponents()
        self._provider_authorization = provider_authorization
        self._metrics = metrics or MetricsCollector(memory.project_id)
        self._operations = operations or OperationTracker()
        self._handlers = dict(handlers or {})
        self._policy_decision_ref = policy_decision_ref
        self._initialize_provider = initialize_provider
        self._project_id = memory.project_id
        self._dataset_id = memory.provider.cognee.dataset
        self._mutation_lock = RLock()
        self._state_lock = RLock()
        self._idempotency: dict[str, _IdempotentResult] = {}
        self._attempt_fingerprints: dict[str, str] = {}
        self._manifest = sync_manifest
        self._checkpoint = sync_checkpoint
        self._proposals: dict[str, WriteProposal] = {}
        self._artifacts: dict[str, StagedProposalArtifact] = {}

    @property
    def metrics(self) -> MetricsCollector:
        return self._metrics

    @property
    def operations(self) -> OperationTracker:
        return self._operations

    def dispatch(self, request: DispatchRequest) -> DispatchResponse:
        """Execute one validated request without leaking internal exceptions."""

        typed = request.typed_payload()
        started = perf_counter()
        decision = self._authorize(request, typed)
        if not decision.allowed:
            return self._deny(request, decision)

        long_status: OperationStatus | None = None
        try:
            self._require_configuration(request.operation, typed)
            replay = self._idempotent_replay(request)
            if replay is not None:
                trace = replay.recall_trace or self._recall_trace(request, typed, replay.result)
                self._capture_audit(
                    request,
                    decision,
                    "idempotent_replay",
                    target_ids=replay.target_ids,
                    recall=trace,
                )
                return self._success(
                    request,
                    replay.result,
                    operation_id=replay.operation_id,
                    replay=True,
                )
            self._bind_attempt(request)

            if request.operation in MUTATING_ACTIONS:
                self._capture_audit(request, decision, "authorized")
            if isinstance(request.operation, OperationName) and request.operation in {
                OperationName.SYNC,
                OperationName.IMPROVE,
                OperationName.FORGET,
                OperationName.REBUILD,
                OperationName.EXPORT,
                OperationName.IMPORT,
            }:
                assert request.idempotency_key is not None
                long_status = self._operations.create(
                    project_id=request.authorization.project_id,
                    operation=request.operation,
                    trace_id=request.trace_id,
                    idempotency_key=request.idempotency_key,
                    total_units=1,
                )
                if long_status.state is OperationState.PENDING:
                    long_status = self._operations.start(long_status.operation_id)
                    long_status = self._operations.checkpoint(
                        long_status.operation_id,
                        checkpoint_ref="service_dispatch_started",
                        checkpoint_metadata={
                            "request_fingerprint": self._request_fingerprint(request)
                        },
                    )
                elif long_status.state in {
                    OperationState.FAILED,
                    OperationState.CANCELLED,
                }:
                    long_status = self._operations.resume(long_status.operation_id)
                else:
                    raise IdempotencyConflictError(
                        "operation status exists without a matching service result"
                    )

            if request.operation in MUTATING_ACTIONS:
                with self._mutation_lock:
                    outcome = self._invoke(request, typed)
            else:
                outcome = self._invoke(request, typed)

            if long_status is not None:
                long_status = self._operations.update_progress(
                    long_status.operation_id,
                    completed_units=1,
                )
                long_status = self._operations.succeed(long_status.operation_id)

            elapsed_ms = (perf_counter() - started) * 1000
            self._record_success_metrics(request.operation, typed, outcome.result, elapsed_ms)
            recall = outcome.recall_trace or self._recall_trace(request, typed, outcome.result)
            self._capture_audit(
                request,
                decision,
                "succeeded",
                target_ids=outcome.target_ids,
                recall=recall,
            )
            operation_id = None if long_status is None else long_status.operation_id
            self._remember_idempotent(request, outcome, operation_id)
            return self._success(request, outcome.result, operation_id=operation_id)
        except Exception as error:  # noqa: BLE001 - the service boundary fails closed
            if long_status is not None and long_status.state is OperationState.RUNNING:
                with suppress(Exception):
                    self._operations.fail(
                        long_status.operation_id,
                        error_code="service_operation_failed",
                    )
            if isinstance(request.operation, OperationName):
                self._metrics.record_failure(request.operation)
            with suppress(Exception):
                self._capture_audit(request, decision, "failed")
            return normalize_service_exception(
                error,
                trace_id=request.trace_id,
                operation=request.operation,
            )

    def _authorize(
        self,
        request: DispatchRequest,
        payload: OperationInput,
    ) -> AuthorizationDecision:
        permission = self._permission(request.operation)
        try:
            decision = self._authorization.evaluate(
                AuthorizationRequest(
                    principal_id=request.authorization.identity.principal_id,
                    project_id=request.authorization.project_id,
                    dataset_id=request.authorization.dataset_id,
                    operation=request.operation.value,
                    permission=permission,
                    scope=request.authorization.scope,
                    target_path=self._authorization_target(payload),
                    query_project_ids=request.authorization.query_project_ids,
                    explicit_cross_project=request.authorization.explicit_cross_project,
                    trace_id=request.trace_id,
                    require_action_specific=(
                        request.operation in MUTATING_ACTIONS
                        or request.operation is ControlAction.INITIALIZE_PREVIEW
                    ),
                )
            )
        except Exception:  # noqa: BLE001 - malformed or unreadable policy is a denial
            decision = AuthorizationDecision(
                allowed=False,
                reason_code="canonical_permission_unavailable",
                principal_id=request.authorization.identity.principal_id,
                project_id=request.authorization.project_id,
                dataset_id=request.authorization.dataset_id,
                operation=request.operation.value,
                permission=permission,
                permission_revision=None,
                canonical_sha256=None,
                grant_id=None,
            )
        boundary_matches = (
            request.authorization.project_id == self._project_id
            and request.authorization.dataset_id == self._dataset_id
            and request.authorization.identity.principal_id == decision.principal_id
        )
        if decision.allowed and not boundary_matches:
            return decision.model_copy(
                update={
                    "allowed": False,
                    "reason_code": "service_boundary_mismatch",
                    "grant_id": None,
                }
            )
        return decision

    def _require_fresh_authorization(
        self,
        request: DispatchRequest,
        payload: OperationInput,
    ) -> AuthorizationDecision:
        decision = self._authorize(request, payload)
        if not decision.allowed:
            with suppress(Exception):
                self._capture_audit(request, decision, "denied")
            raise PermissionDeniedError(f"permission denied: {decision.reason_code}")
        return decision

    @staticmethod
    def _permission(action: InterfaceAction) -> Permission:
        if isinstance(action, OperationName):
            return operation_by_name(action).required_permission
        if action is ControlAction.OPERATION_STATUS:
            return Permission.READ
        return Permission.ADMINISTER

    @staticmethod
    def _authorization_target(payload: OperationInput) -> str | None:
        if isinstance(payload, ExportInput):
            return payload.output_path
        if isinstance(payload, ImportInput):
            return payload.package_path
        if isinstance(
            payload,
            InitializationPreviewInput | InitializationApplyInput | InitializationDirectInput,
        ):
            return payload.configuration_path
        return None

    def _deny(
        self,
        request: DispatchRequest,
        decision: AuthorizationDecision,
    ) -> DispatchResponse:
        with suppress(Exception):
            self._capture_audit(request, decision, "denied")
        if isinstance(request.operation, OperationName):
            self._metrics.record_failure(request.operation)
        return error_envelope(request.trace_id, ErrorCategory.PERMISSION_DENIED)

    def _require_configuration(self, action: InterfaceAction, payload: OperationInput) -> None:
        capability = "health"
        if action is OperationName.SOURCES_LIST:
            capability = "sources_list"
        elif action is OperationName.SOURCES_EXPLAIN:
            capability = "sources_explain"
        elif action is OperationName.SYNC:
            assert isinstance(payload, SyncInput)
            capability = "dry_run" if payload.dry_run else "sync"
        elif action is OperationName.RECALL:
            assert isinstance(payload, RecallInput)
            capability = payload.mode.value
            if payload.mode is RetrievalMode.HYBRID:
                capability = "recall"
        elif action in {OperationName.GET, OperationName.EXPLAIN}:
            capability = "exact"
        elif action is OperationName.GRAPH:
            capability = "graph"
        elif action is OperationName.PROPOSE:
            capability = "propose"
        elif action is OperationName.APPROVE:
            capability = "approve"
        elif action is OperationName.SUPERSEDE:
            capability = "improve"
        elif action is OperationName.IMPROVE:
            capability = "feedback"
            self._configuration.require("improve")
        elif action is OperationName.FORGET:
            capability = "forget"
        elif action is OperationName.REBUILD:
            assert isinstance(payload, RebuildInput)
            capability = "dry_run" if payload.preview_only else "rebuild"
        elif action is OperationName.EXPORT:
            capability = "export"
        elif action is OperationName.IMPORT:
            assert isinstance(payload, ImportInput)
            capability = "dry_run" if not payload.activate else "import"
        elif action is ControlAction.INITIALIZE_PREVIEW:
            capability = "dry_run"
        elif action in {ControlAction.INITIALIZE_APPLY, ControlAction.INITIALIZE_DIRECT}:
            capability = "exact"
        self._configuration.require(capability)
        if (
            action is OperationName.RECALL
            and isinstance(payload, RecallInput)
            and payload.synthesize
        ):
            self._configuration.require("semantic")

    def _invoke(self, request: DispatchRequest, payload: OperationInput) -> PortResult:
        handler = self._handlers.get(request.operation)
        if handler is not None:
            result = handler(request, payload)
            if isinstance(result, Coroutine):
                result = _run_coroutine(result)
            if not isinstance(result, PortResult):
                raise TypeError("service handler must return PortResult")
            return result
        return self._invoke_builtin(request, payload)

    def _invoke_builtin(self, request: DispatchRequest, payload: OperationInput) -> PortResult:
        action = request.operation
        if action is OperationName.HEALTH:
            return self._health(payload)
        if action is OperationName.SOURCES_LIST:
            return self._sources_list(payload)
        if action is OperationName.SOURCES_EXPLAIN:
            return self._sources_explain(payload)
        if action is OperationName.SYNC:
            return self._sync(request, payload)
        if action is OperationName.RECALL:
            return self._recall(request, payload)
        if action is OperationName.GET:
            return self._get(request, payload)
        if action is OperationName.GRAPH:
            return self._graph(request, payload)
        if action is OperationName.PROPOSE:
            return self._propose(request, payload)
        if action is OperationName.APPROVE:
            return self._approve(request, payload)
        if action is OperationName.SUPERSEDE:
            return self._supersede(request, payload)
        if action is OperationName.IMPROVE:
            return self._improve(request, payload)
        if action is OperationName.FORGET:
            return self._forget(request, payload)
        if action is OperationName.REBUILD:
            return self._rebuild(request, payload)
        if action is OperationName.EXPORT:
            return self._export(request, payload)
        if action is OperationName.IMPORT:
            return self._import(request, payload)
        if action is OperationName.EXPLAIN:
            return self._explain(request, payload)
        if action is ControlAction.INITIALIZE_PREVIEW:
            return self._initialize_preview(payload)
        if action is ControlAction.INITIALIZE_DIRECT:
            return self._initialize_direct(payload)
        if action is ControlAction.INITIALIZE_APPLY:
            return self._initialize_apply(payload)
        if action is ControlAction.OPERATION_STATUS:
            return self._operation_status(request, payload)
        raise ServiceDispatchFailure(ErrorCategory.PROVIDER_UNSUPPORTED)

    def _health(self, payload: OperationInput) -> PortResult:
        assert isinstance(payload, HealthInput)
        memory = self._configuration.configuration.memory
        result: dict[str, JsonValue] = {
            "configuration_status": self._configuration.configuration.configuration_status,
            "memory_enabled": memory.enabled,
            "read_only": memory.read_only,
            "network_listener_enabled": memory.service.network_listener_enabled,
            "provider_name": memory.provider.name,
            "provider_composed": self._components.provider is not None,
            "exact_index_composed": self._components.exact_index is not None,
            "retrieval_composed": self._components.retrieval is not None,
        }
        if self._components.health is not None:
            result["health"] = _model_object(
                self._components.health.check(project_id=self._project_id)
            )
        if payload.detailed:
            result["metrics"] = _model_object(self._metrics.snapshot())
        return PortResult(result=result)

    def _registry(self) -> RegistryBundle:
        if self._components.registry_loader is None:
            raise ServiceDispatchFailure(ErrorCategory.MEMORY_NOT_INITIALIZED)
        return self._components.registry_loader()

    def _sources_list(self, payload: OperationInput) -> PortResult:
        assert isinstance(payload, SourcesListInput)
        entries = tuple(
            entry
            for entry in self._registry().sources
            if entry.project_id == self._project_id
            and (payload.include_excluded or not entry.is_exclusion)
        )
        rows: list[JsonValue] = [
            _source_projection(entry) for entry in sorted(entries, key=lambda item: item.source_id)
        ]
        return PortResult(result={"sources": rows, "source_count": len(rows)})

    def _source_discovery(self, entries: tuple[SourceRegistryEntry, ...]) -> SourceDiscovery:
        settings = self._configuration.configuration.memory
        return SourceDiscovery(
            project_root=self._configuration.project_root,
            project_id=self._project_id,
            entries=entries,
            respect_gitignore=settings.sources.respect_gitignore,
            secret_scan=settings.security.secret_scan,
        )

    def _sources_explain(self, payload: OperationInput) -> PortResult:
        assert isinstance(payload, SourcesExplainInput)
        registry = self._registry()
        external = next(
            (
                entry
                for entry in registry.sources
                if entry.is_external and entry.path_or_uri == payload.target
            ),
            None,
        )
        if external is not None:
            return PortResult(
                result={
                    "path_or_uri": payload.target,
                    "disposition": "registered_external",
                    "reason": "external_requires_explicit_content",
                    "rule_ids": [external.source_id],
                }
            )
        decision = self._source_discovery(registry.sources).explain_path(payload.target)
        return PortResult(
            result={
                "path_or_uri": decision.path_or_uri,
                "disposition": decision.disposition.value,
                "reason": decision.reason.value,
                "rule_ids": list(decision.rule_ids),
                "source_id": decision.source_id,
                "detail": decision.detail,
            }
        )

    def _selected_entries(
        self,
        entries: tuple[SourceRegistryEntry, ...],
        source_ids: tuple[str, ...],
    ) -> tuple[SourceRegistryEntry, ...]:
        if not source_ids:
            return entries
        known = {entry.source_id for entry in entries if not entry.is_exclusion}
        unknown = set(source_ids) - known
        if unknown:
            raise ValueError("sync requested an unregistered source ID")
        requested = set(source_ids)
        return tuple(
            entry for entry in entries if entry.is_exclusion or entry.source_id in requested
        )

    def _provider_context(self, request: DispatchRequest) -> ProviderContext:
        return ProviderContext(
            project_id=request.authorization.project_id,
            dataset_id=request.authorization.dataset_id,
            principal_id=request.authorization.identity.principal_id,
            scope=request.authorization.scope,
            trace_id=request.trace_id,
        )

    def _sync(self, request: DispatchRequest, payload: OperationInput) -> PortResult:
        assert isinstance(payload, SyncInput)
        registry = self._registry()
        entries = self._selected_entries(registry.sources, payload.source_ids)
        report = self._source_discovery(entries).discover()
        if payload.dry_run:
            return PortResult(
                result={
                    "dry_run": True,
                    "included_source_count": len(report.records),
                    "excluded_candidate_count": len(report.excluded),
                    "failure_count": 0,
                },
                target_ids=tuple(item.source_id for item in report.records),
            )
        semantic = self._configuration.configuration.memory.models.semantic_enabled
        if self._components.synchronizer is None or (
            semantic
            and (self._components.provider is None or self._provider_authorization is None)
        ):
            raise ServiceDispatchFailure(ErrorCategory.MEMORY_NOT_INITIALIZED)
        with self._state_lock:
            previous = None if payload.full else self._manifest
            checkpoint = self._checkpoint
        generation_id = "gen_" + stable_id(
            "incremental-sync",
            request.authorization.project_id,
            self._operation_id(request),
        ).replace("-", "")
        synchronized = self._components.synchronizer.synchronize(
            report,
            previous_manifest=previous,
            checkpoint=checkpoint,
            generation_id=generation_id,
            force=payload.full,
        )
        records = tuple(
            record for document in synchronized.documents for record in document.records
        )
        provider_result: dict[str, JsonValue] | None = None
        if records and self._components.provider is not None:
            assert request.idempotency_key is not None
            if self._provider_authorization is None:
                raise ServiceDispatchFailure(ErrorCategory.MEMORY_NOT_INITIALIZED)
            context = self._provider_context(request)
            authorization = self._provider_authorization.authorize(
                context,
                ProviderMutation.REMEMBER,
                authorization_operation=OperationName.SYNC.value,
            )
            remembered = _run_coroutine(
                self._components.provider.remember(
                    RememberRequest(
                        context=context,
                        request_id=request.request_id,
                        idempotency_key=request.idempotency_key,
                        records=records,
                        sources=tuple(document.source for document in synchronized.documents),
                        authorization=authorization,
                    )
                )
            )
            provider_result = _model_object(remembered)
        with self._state_lock:
            self._manifest = synchronized.manifest
            self._checkpoint = synchronized.checkpoint
        failure_rows: list[JsonValue] = [
            _JSON_OBJECT.validate_python(failure.as_metadata()) for failure in synchronized.failures
        ]
        delta_counts: dict[str, JsonValue] = {}
        for change in synchronized.delta.changes:
            key = change.change.value
            current = delta_counts.get(key, 0)
            delta_counts[key] = current + 1 if isinstance(current, int) else 1
        manifest = _JSON_OBJECT.validate_python(synchronized.manifest.to_json_dict())
        manifest_sha256 = sha256_bytes(canonical_json_bytes(manifest))
        source_revisions: list[JsonValue] = [
            {
                "source_id": item.source_id,
                "path": item.path,
                "content_sha256": item.content_sha256,
                "revision": item.revision,
                "status": item.status,
            }
            for item in synchronized.manifest.entries
        ]
        checkpoint_payload: dict[str, JsonValue] = {
            "completed_revisions": [
                {"source_id": source_id, "content_sha256": content_sha256}
                for source_id, content_sha256 in synchronized.checkpoint.completed_revisions
            ],
            "failed_sources": [
                {"source_id": source_id, "error_category": category}
                for source_id, category in synchronized.checkpoint.failed_sources
            ],
            "updated_at": (
                None
                if synchronized.checkpoint.updated_at is None
                else synchronized.checkpoint.updated_at.isoformat().replace("+00:00", "Z")
            ),
        }
        receipt: dict[str, JsonValue] = {
            "project_id": request.authorization.project_id,
            "request_id": request.request_id,
            "trace_id": request.trace_id,
            "generation_id": generation_id,
            "configuration_fingerprint": self._configuration.fingerprint,
            "source_manifest_sha256": manifest_sha256,
            "source_revisions": source_revisions,
            "delta": delta_counts,
            "failure_count": len(synchronized.failures),
            "outcome": "succeeded" if not synchronized.failures else "completed_with_failures",
        }
        receipt["receipt_sha256"] = sha256_bytes(canonical_json_bytes(receipt))
        return PortResult(
            result={
                "dry_run": False,
                "generation_id": generation_id,
                "document_count": len(synchronized.documents),
                "record_count": len(records),
                "failure_count": len(synchronized.failures),
                "failures": failure_rows,
                "skipped_source_ids": list(synchronized.skipped_source_ids),
                "delta": delta_counts,
                "manifest": manifest,
                "checkpoint": checkpoint_payload,
                "receipt": receipt,
                "provider": provider_result,
            },
            target_ids=tuple(document.source.source_id for document in synchronized.documents),
        )

    def _recall(self, request: DispatchRequest, payload: OperationInput) -> PortResult:
        assert isinstance(payload, RecallInput)
        if self._components.retrieval is None:
            raise ServiceDispatchFailure(ErrorCategory.MEMORY_NOT_INITIALIZED)
        if payload.synthesize and self._components.synthesis is None:
            raise ServiceDispatchFailure(ErrorCategory.MEMORY_NOT_INITIALIZED)
        identity = request.authorization.identity
        requester = RequesterIdentity(
            principal_id=identity.principal_id,
            agent_type=identity.agent_type,
            run_id=identity.run_id,
        )
        result, trace = _run_coroutine(
            self._components.retrieval.recall_with_trace(
                RecallQuery(
                    request_id=request.request_id,
                    trace_id=request.trace_id,
                    project_id=request.authorization.project_id,
                    dataset_id=request.authorization.dataset_id,
                    requester=requester,
                    scope=request.authorization.scope,
                    query=payload.query,
                    mode=payload.mode,
                    requested_project_ids=request.authorization.query_project_ids,
                    explicit_cross_project=request.authorization.explicit_cross_project,
                    namespaces=payload.namespaces,
                    current_only=payload.current_only,
                    budget=ContextBudget(max_records=payload.limit),
                )
            )
        )
        synthesis: EvidenceSynthesisResult | None = None
        synthesis_state = "not_requested"
        if payload.synthesize:
            synthesis_state = "insufficient_evidence"
            if result.results:
                assert self._components.synthesis is not None
                self._require_fresh_authorization(request, payload)
                synthesis = EvidenceSynthesisResult.model_validate(
                    _run_coroutine(
                        self._components.synthesis.synthesize(
                            EvidenceSynthesisRequest(
                                request_id=request.request_id,
                                project_id=request.authorization.project_id,
                                requester=requester,
                                llm_profile_id=(
                                    self._configuration.configuration.memory.models.llm_profile
                                ),
                                evidence=result,
                                trace_id=request.trace_id,
                            )
                        )
                    )
                )
                self._require_fresh_authorization(request, payload)
                self._validate_synthesis(
                    synthesis,
                    result,
                    expected_model_profile_id=(
                        self._configuration.configuration.memory.models.llm_profile
                    ),
                )
                synthesis_state = "completed"
        return PortResult(
            result={
                "retrieval": _model_object(result),
                "trace": _model_object(trace),
                "synthesis_requested": payload.synthesize,
                "synthesis_state": synthesis_state,
                "synthesis": None if synthesis is None else _model_object(synthesis),
            },
            target_ids=tuple(item.record_id for item in result.results),
            recall_trace=trace,
        )

    @staticmethod
    def _validate_synthesis(
        synthesis: EvidenceSynthesisResult,
        evidence: RetrievalResult,
        *,
        expected_model_profile_id: str,
    ) -> None:
        if (
            synthesis.request_id != evidence.request_id
            or synthesis.project_id != evidence.project_id
            or synthesis.trace_id != evidence.trace_id
            or synthesis.model_profile_id != expected_model_profile_id
        ):
            raise ValueError("synthesis result does not match its evidence boundary")
        evidence_by_id = {item.record_id: item for item in evidence.results}
        for claim in synthesis.claims:
            for citation in claim.citations:
                retrieved = evidence_by_id.get(citation.record_id)
                if (
                    retrieved is None
                    or citation.source_id != retrieved.source.source_id
                    or citation.source != retrieved.source
                ):
                    raise ValueError("synthesis citation is outside the evidence bundle")

    def _get(self, request: DispatchRequest, payload: OperationInput) -> PortResult:
        assert isinstance(payload, GetInput)
        if self._components.exact_index is None:
            raise ServiceDispatchFailure(ErrorCategory.MEMORY_NOT_INITIALIZED)
        matches = self._components.exact_index.query_exact(
            project_id=request.authorization.project_id,
            query=payload.record_id,
            case_sensitive=True,
            field="record_id",
            current_only=not payload.include_history,
            limit=100 if payload.include_history else 2,
        )
        exact = tuple(item for item in matches if item.record_id == payload.record_id)
        rows: list[JsonValue] = [_model_object(item) for item in exact]
        return PortResult(
            result={"found": bool(exact), "records": rows},
            target_ids=tuple(item.record_id for item in exact),
        )

    def _graph(self, request: DispatchRequest, payload: OperationInput) -> PortResult:
        assert isinstance(payload, GraphInput)
        if self._components.retrieval is None:
            raise ServiceDispatchFailure(ErrorCategory.MEMORY_NOT_INITIALIZED)
        graph, result, _trace = _run_coroutine(
            self._components.retrieval.graph_paths_with_trace(
                RecallQuery(
                    request_id=request.request_id,
                    trace_id=request.trace_id,
                    project_id=request.authorization.project_id,
                    dataset_id=request.authorization.dataset_id,
                    requester=RequesterIdentity(
                        principal_id=request.authorization.identity.principal_id,
                        agent_type=request.authorization.identity.agent_type,
                        run_id=request.authorization.identity.run_id,
                    ),
                    scope=request.authorization.scope,
                    query=payload.record_id,
                    mode=RetrievalMode.GRAPH,
                    requested_project_ids=request.authorization.query_project_ids,
                    explicit_cross_project=request.authorization.explicit_cross_project,
                    relation_types=payload.relation_types,
                    authorization_operation=OperationName.GRAPH.value,
                    budget=ContextBudget(max_records=20, max_relation_depth=payload.max_depth),
                ),
                start_record_id=payload.record_id,
            )
        )
        target_ids = tuple(
            dict.fromkeys(
                (
                    *(item.record_id for item in result.results),
                    *(item.relation.relation_id for item in graph.paths),
                )
            )
        )
        return PortResult(
            result={"graph": _model_object(graph), "retrieval": _model_object(result)},
            target_ids=target_ids,
        )

    def _propose(self, request: DispatchRequest, payload: OperationInput) -> PortResult:
        assert isinstance(payload, ProposeInput)
        if self._components.write_policy is None:
            raise ServiceDispatchFailure(ErrorCategory.MEMORY_NOT_INITIALIZED)
        submission = ProposalSubmission.model_validate(payload.proposal)
        identity = request.authorization.identity
        expected_requester = RequesterIdentity(
            principal_id=identity.principal_id,
            agent_type=identity.agent_type,
            run_id=identity.run_id,
        )
        if (
            submission.project_id != request.authorization.project_id
            or submission.requester != expected_requester
            or submission.requested_scope != request.authorization.scope
        ):
            raise ProjectIsolationError("proposal identity does not match the request boundary")
        assert request.idempotency_key is not None
        write_request = WriteRequest(
            project_id=submission.project_id,
            dataset_id=request.authorization.dataset_id,
            requester=submission.requester,
            record_type=submission.requested_record_type,
            target_class=submission.target_class,
            scope=submission.requested_scope,
            evidence_ids=tuple(
                item.record_id or item.source_id or "" for item in submission.evidence
            ),
            requested_status=submission.requested_status,
            trust_class=submission.trust_class,
            sensitivity=submission.sensitivity,
            authority_tier=submission.authority_tier,
            requested_target=submission.requested_target.path,
            idempotency_key=request.idempotency_key,
            trace_id=request.trace_id,
            content=submission.proposal.content,
            external_source=submission.external_source,
            automatic_feedback=submission.automatic_feedback,
        )
        policy = self._components.write_policy.evaluate(write_request)
        status = {
            PolicyAction.REJECT: RecordStatus.REJECTED,
            PolicyAction.STAGE_FOR_REVIEW: RecordStatus.STAGED,
        }.get(policy.action, RecordStatus.ACTIVE)
        proposal = WriteProposal(
            schema_version=SCHEMA_VERSION,
            api_version=API_VERSION,
            proposal_id=submission.proposal_id,
            idempotency_key=request.idempotency_key,
            project_id=submission.project_id,
            requester=submission.requester,
            requested_record_type=submission.requested_record_type,
            requested_scope=submission.requested_scope,
            requested_target=submission.requested_target,
            proposal=submission.proposal,
            evidence=submission.evidence,
            trust_class=submission.trust_class,
            sensitivity=submission.sensitivity,
            policy_result=policy.to_contract(),
            status=status,
            created_at=submission.created_at,
        )
        effect = policy.action.value
        artifact: StagedProposalArtifact | None = None
        provider_result: dict[str, JsonValue] | None = None
        if policy.action is PolicyAction.STAGE_FOR_REVIEW:
            if self._components.proposal_stager is None:
                raise ServiceDispatchFailure(ErrorCategory.MEMORY_NOT_INITIALIZED)
            artifact = self._components.proposal_stager.stage(
                proposal,
                trace_id=request.trace_id,
                base_content=submission.base_content,
            )
            with self._state_lock:
                self._proposals[proposal.proposal_id] = proposal
                self._artifacts[proposal.proposal_id] = artifact
        elif policy.action is PolicyAction.SESSION_ONLY:
            if self._components.session_store is None or submission.session_entry is None:
                raise ServiceDispatchFailure(ErrorCategory.MEMORY_NOT_INITIALIZED)
            self._configuration.require("session")
            self._components.session_store.put(submission.session_entry)
        elif policy.action is PolicyAction.EPISODIC_COMMIT:
            if self._components.episodic_store is None or submission.episodic_entry is None:
                raise ServiceDispatchFailure(ErrorCategory.MEMORY_NOT_INITIALIZED)
            self._configuration.require("episodic")
            self._components.episodic_store.record(submission.episodic_entry)
        elif policy.action is PolicyAction.DERIVED_COMMIT:
            if (
                self._components.provider is None
                or self._provider_authorization is None
                or not submission.records
            ):
                raise ServiceDispatchFailure(ErrorCategory.MEMORY_NOT_INITIALIZED)
            context = self._provider_context(request)
            authorization = self._provider_authorization.authorize(
                context,
                ProviderMutation.REMEMBER,
                authorization_operation=OperationName.PROPOSE.value,
                target_path=submission.requested_target.path,
            )
            remembered = _run_coroutine(
                self._components.provider.remember(
                    RememberRequest(
                        context=context,
                        request_id=request.request_id,
                        idempotency_key=request.idempotency_key,
                        records=submission.records,
                        relations=submission.relations,
                        sources=submission.sources,
                        authorization=authorization,
                    )
                )
            )
            provider_result = _model_object(remembered)
        result: dict[str, JsonValue] = {
            "policy": _model_object(policy),
            "proposal": _model_object(proposal),
            "effect": effect,
            "artifact": None if artifact is None else _model_object(artifact),
            "provider": provider_result,
        }
        return PortResult(result=result, target_ids=(proposal.proposal_id,))

    def _approve(self, request: DispatchRequest, payload: OperationInput) -> PortResult:
        assert isinstance(payload, ApproveInput)
        if self._components.reviewer_gate is None or self._components.proposal_stager is None:
            raise ServiceDispatchFailure(ErrorCategory.MEMORY_NOT_INITIALIZED)
        with self._state_lock:
            proposal = self._proposals.get(payload.proposal_id)
            artifact = self._artifacts.get(payload.proposal_id)
        if proposal is None or artifact is None:
            raise ServiceDispatchFailure(ErrorCategory.WRITE_REJECTED)
        disposition = (
            ReviewDisposition.APPROVED
            if payload.decision == "approve"
            else ReviewDisposition.REJECTED
        )
        review = self._components.reviewer_gate.decide(
            artifact,
            reviewer_id=request.authorization.identity.principal_id,
            project_id=request.authorization.project_id,
            dataset_id=request.authorization.dataset_id,
            scope=proposal.requested_scope,
            record_type=proposal.requested_record_type,
            disposition=disposition,
            rationale_summary=payload.reason,
            trace_id=request.trace_id,
        )
        promotion_request: dict[str, JsonValue] | None = None
        promotion_receipt: dict[str, JsonValue] | None = None
        rejected_disposition: dict[str, JsonValue] | None = None
        if disposition is ReviewDisposition.APPROVED:
            if self._components.promotion is not None:
                assert request.idempotency_key is not None
                promotion_receipt = _model_object(
                    self._components.promotion.execute(
                        artifact,
                        review,
                        project_id=request.authorization.project_id,
                        dataset_id=request.authorization.dataset_id,
                        scope=proposal.requested_scope,
                        record_type=proposal.requested_record_type,
                        trace_id=request.trace_id,
                        idempotency_key=request.idempotency_key,
                    )
                )
            elif self._components.promotion_planner is not None:
                promotion_request = _model_object(
                    self._components.promotion_planner.create_request(
                        artifact,
                        review,
                        project_id=request.authorization.project_id,
                        dataset_id=request.authorization.dataset_id,
                        scope=proposal.requested_scope,
                        record_type=proposal.requested_record_type,
                        trace_id=request.trace_id,
                    )
                )
            else:
                raise ServiceDispatchFailure(ErrorCategory.MEMORY_NOT_INITIALIZED)
        else:
            rejected_disposition = _model_object(
                self._components.proposal_stager.dispose_rejected(artifact, review)
            )
            with self._state_lock:
                self._proposals.pop(payload.proposal_id, None)
                self._artifacts.pop(payload.proposal_id, None)
        return PortResult(
            result={
                "review": _model_object(review),
                "promotion_request": promotion_request,
                "promotion_receipt": promotion_receipt,
                "rejected_disposition": rejected_disposition,
            },
            target_ids=(payload.proposal_id,),
        )

    def _supersede(self, request: DispatchRequest, payload: OperationInput) -> PortResult:
        assert isinstance(payload, SupersedeInput)
        if self._components.lifecycle is None:
            raise ServiceDispatchFailure(ErrorCategory.MEMORY_NOT_INITIALIZED)
        current = (
            self._components.lifecycle.get(payload.record_id),
            self._components.lifecycle.get(payload.replacement_record_id),
        )
        if any(
            item.project_id != request.authorization.project_id
            or item.dataset_id != request.authorization.dataset_id
            for item in current
        ):
            raise ProjectIsolationError("lifecycle records are outside the request boundary")
        if self._components.lifecycle_index is None:
            raise ServiceDispatchFailure(ErrorCategory.MEMORY_NOT_INITIALIZED)
        self._components.lifecycle.validate_supersession(
            payload.record_id,
            payload.replacement_record_id,
        )
        effective_at = utc_now()
        indexed_prior, indexed_replacement = self._components.lifecycle_index.supersede_records(
            project_id=request.authorization.project_id,
            prior_record_id=payload.record_id,
            replacement_record_id=payload.replacement_record_id,
            at=effective_at,
        )
        prior, replacement = self._components.lifecycle.supersede(
            payload.record_id,
            payload.replacement_record_id,
            at=effective_at,
        )
        if (
            indexed_prior.lifecycle.status is not prior.status
            or indexed_replacement.lifecycle.status is not replacement.status
            or indexed_prior.lifecycle.superseded_by != prior.superseded_by
            or indexed_replacement.lifecycle.supersedes != replacement.supersedes
        ):
            raise RuntimeError("lifecycle catalog and exact index diverged")
        if any(
            item.project_id != request.authorization.project_id
            or item.dataset_id != request.authorization.dataset_id
            for item in (prior, replacement)
        ):
            raise ProjectIsolationError("lifecycle result crossed the request boundary")
        return PortResult(
            result={
                "prior": _model_object(prior),
                "replacement": _model_object(replacement),
                "canonical_write_performed": False,
                "deterministic_index_updated": True,
            },
            target_ids=(payload.record_id, payload.replacement_record_id),
        )

    def _improve(self, request: DispatchRequest, payload: OperationInput) -> PortResult:
        assert isinstance(payload, ImproveInput)
        if (
            self._components.improvement is None
            or self._components.provider is None
            or self._provider_authorization is None
        ):
            raise ServiceDispatchFailure(ErrorCategory.MEMORY_NOT_INITIALIZED)
        submission = ImprovementSubmission.model_validate(payload.feedback)
        targets = tuple(sorted({item.target_record_id for item in submission.feedback}))
        if payload.record_id is not None:
            if payload.record_id not in targets:
                raise ValueError("improvement record_id does not match its feedback")
            targets = (payload.record_id,)
        improvement_request = ImprovementRequest(
            principal_id=request.authorization.identity.principal_id,
            project_id=request.authorization.project_id,
            dataset_id=request.authorization.dataset_id,
            profile_id=submission.profile_id,
            scope=request.authorization.scope,
            trace_id=request.trace_id,
            target_record_ids=targets,
            feedback=submission.feedback,
            configuration_fingerprint=self._configuration.fingerprint,
        )
        pattern: dict[str, JsonValue] | None = None
        if submission.action == "reweight":
            assert submission.receipt_id is not None
            receipt = self._components.improvement.reweight(
                improvement_request,
                receipt_id=submission.receipt_id,
                authority=submission.authority,
                trust=submission.trust,
            )
        else:
            assert submission.consolidation_record_id is not None
            derived, receipt = self._components.improvement.consolidate(
                improvement_request,
                record_id=submission.consolidation_record_id,
                inputs=submission.consolidation_inputs,
            )
            pattern = _model_object(derived)
        assert request.idempotency_key is not None
        context = self._provider_context(request)
        authorization = self._provider_authorization.authorize(
            context,
            ProviderMutation.IMPROVE,
        )
        provider = _run_coroutine(
            self._components.provider.improve(
                ProviderImproveRequest(
                    context=context,
                    request_id=request.request_id,
                    idempotency_key=request.idempotency_key,
                    record_ids=targets,
                    profile_ids=(submission.profile_id,),
                    authorization=authorization,
                )
            )
        )
        return PortResult(
            result={
                "receipt": _model_object(receipt),
                "derived_pattern": pattern,
                "provider": _model_object(provider),
            },
            target_ids=targets,
        )

    def _forget(self, request: DispatchRequest, payload: OperationInput) -> PortResult:
        assert isinstance(payload, ForgetInput)
        if self._components.destructive is None:
            raise ServiceDispatchFailure(ErrorCategory.MEMORY_NOT_INITIALIZED)
        mode = ForgetMode(payload.action)
        operation_id = self._operation_id(request, explicit=payload.operation_id)
        destructive_request = DestructiveRequest(
            operation_id=operation_id,
            principal_id=request.authorization.identity.principal_id,
            project_id=request.authorization.project_id,
            dataset_id=request.authorization.dataset_id,
            scope=request.authorization.scope,
            mode=mode,
            selector_ids=payload.record_ids,
            trace_id=request.trace_id,
        )
        preview = self._components.destructive.preview(destructive_request)
        if not payload.execute:
            canonical_request: dict[str, JsonValue] | None = None
            if mode is ForgetMode.DELETE_SOURCE:
                canonical_request = _model_object(
                    self._components.destructive.canonical_change_request(preview)
                )
            return PortResult(
                result={
                    "preview": _model_object(preview),
                    "canonical_change_request": canonical_request,
                    "provider_forget_executed": False,
                },
                target_ids=payload.record_ids,
                impact_digest=preview.impact_digest,
            )
        if payload.impact_digest != preview.impact_digest:
            raise IdempotencyConflictError("forget impact changed after client preview")
        receipt = self._components.destructive.execute(destructive_request, preview)
        return PortResult(
            result={
                "receipt": _model_object(receipt),
                "provider_forget_executed": False,
            },
            target_ids=payload.record_ids,
            impact_digest=preview.impact_digest,
        )

    def _rebuild(self, request: DispatchRequest, payload: OperationInput) -> PortResult:
        assert isinstance(payload, RebuildInput)
        if self._components.rebuild is None:
            raise ServiceDispatchFailure(ErrorCategory.MEMORY_NOT_INITIALIZED)
        preview = self._components.rebuild.preview(
            operation_id=self._operation_id(request, explicit=payload.operation_id),
            mode=RebuildMode.FULL,
            deterministic=True,
        )
        if payload.preview_only:
            return PortResult(
                result={"preview": _model_object(preview)},
                impact_digest=preview.impact_digest,
            )
        if payload.impact_digest != preview.impact_digest:
            raise IdempotencyConflictError("rebuild impact changed after client preview")
        activation = self._authorization.require(
            AuthorizationRequest(
                principal_id=request.authorization.identity.principal_id,
                project_id=request.authorization.project_id,
                dataset_id=request.authorization.dataset_id,
                operation="memory.rebuild.activate",
                permission=Permission.REBUILD,
                scope=request.authorization.scope,
                trace_id=request.trace_id,
                require_action_specific=True,
            )
        )
        receipt = _run_coroutine(
            self._components.rebuild.execute(
                preview,
                authorization=AuthorizedRebuildImpact(
                    decision=activation,
                    impact_digest=preview.impact_digest,
                ),
            )
        )
        return PortResult(
            result={"receipt": _model_object(receipt)},
            impact_digest=preview.impact_digest,
        )

    def _export(self, request: DispatchRequest, payload: OperationInput) -> PortResult:
        assert isinstance(payload, ExportInput)
        if self._components.exchange is None or self._provider_authorization is None:
            raise ServiceDispatchFailure(ErrorCategory.MEMORY_NOT_INITIALIZED)
        assert request.idempotency_key is not None
        context = self._provider_context(request)
        authorization = self._provider_authorization.authorize(
            context,
            ProviderMutation.EXPORT,
            target_path=payload.output_path,
        )
        return _run_coroutine(
            self._components.exchange.export(
                PortableExportCall(
                    context=context,
                    request_id=request.request_id,
                    idempotency_key=request.idempotency_key,
                    output_path=payload.output_path,
                    format=payload.format,
                    include_sensitive=payload.include_sensitive,
                    age_recipient=payload.age_recipient,
                    authorization=authorization,
                )
            )
        )

    def _import(self, request: DispatchRequest, payload: OperationInput) -> PortResult:
        assert isinstance(payload, ImportInput)
        if self._components.exchange is None:
            raise ServiceDispatchFailure(ErrorCategory.MEMORY_NOT_INITIALIZED)
        assert request.idempotency_key is not None
        context = self._provider_context(request)
        authorization = None
        activation_decision = None
        if payload.activate:
            if self._provider_authorization is None:
                raise ServiceDispatchFailure(ErrorCategory.MEMORY_NOT_INITIALIZED)
            activation_decision = self._authorization.require(
                AuthorizationRequest(
                    principal_id=request.authorization.identity.principal_id,
                    project_id=request.authorization.project_id,
                    dataset_id=request.authorization.dataset_id,
                    operation="memory.import.activate",
                    permission=Permission.ADMINISTER,
                    scope=request.authorization.scope,
                    target_path=payload.package_path,
                    trace_id=request.trace_id,
                    require_action_specific=True,
                )
            )
            authorization = self._provider_authorization.authorize(
                context,
                ProviderMutation.IMPORT,
                target_path=payload.package_path,
                impact_digest=payload.impact_digest,
            )
        call = PortableImportCall(
            context=context,
            request_id=request.request_id,
            idempotency_key=request.idempotency_key,
            package_path=payload.package_path,
            activate=payload.activate,
            expected_sha256=payload.expected_sha256,
            accepted_impact_digest=payload.impact_digest,
            authorization=authorization,
            activation_decision=activation_decision,
        )
        if payload.activate:
            return _run_coroutine(self._components.exchange.import_package(call))
        return _run_coroutine(self._components.exchange.preview_import(call))

    def _explain(self, request: DispatchRequest, payload: OperationInput) -> PortResult:
        assert isinstance(payload, ExplainInput)
        got = self._get(
            request,
            GetInput(record_id=payload.record_id, include_history=True),
        )
        records = got.result.get("records", [])
        first = records[0] if isinstance(records, list) and records else None
        return PortResult(
            result={
                "found": first is not None,
                "record": first,
                "explanation_fields": [
                    "source",
                    "authority",
                    "lifecycle",
                    "scores",
                    "selection_reason",
                ],
            },
            target_ids=got.target_ids,
        )

    def _loaded_for_path(self, relative_path: str) -> LoadedConfiguration:
        candidate = self._configuration.project_root / Path(relative_path)
        loaded = load_configuration(
            candidate,
            trusted_project_root=self._configuration.project_root,
        )
        memory = loaded.configuration.memory
        if (
            memory.project_id != self._project_id
            or memory.provider.cognee.dataset != self._dataset_id
        ):
            raise ProjectIsolationError("configuration identity changed")
        return loaded

    def _build_initialization_preview(
        self,
        loaded: LoadedConfiguration,
    ) -> InitializationPreview:
        report = preflight_initialization(
            loaded, registry=self._registry(), require_enabled=False
        ).discovery
        return build_initialization_preview(
            loaded,
            included_source_count=len(report.records),
            excluded_source_count=len(report.excluded),
            warnings=("provider_not_initialized",),
        )

    def _initialize_preview(self, payload: OperationInput) -> PortResult:
        assert isinstance(payload, InitializationPreviewInput)
        loaded = self._loaded_for_path(payload.configuration_path)
        preview = self._build_initialization_preview(loaded)
        return PortResult(
            result={"preview": _model_object(preview)},
            impact_digest=preview.impact_digest,
        )

    def _initialize_apply(self, payload: OperationInput) -> PortResult:
        assert isinstance(payload, InitializationApplyInput)
        loaded = self._loaded_for_path(payload.configuration_path)
        preview = self._build_initialization_preview(loaded)
        receipt = apply_initialization(
            loaded,
            preview,
            accepted_impact_digest=payload.impact_digest,
            authorized=True,
            registry=self._registry(),
            initialize_provider=self._initialize_provider,
        )
        return PortResult(
            result={
                "impact_digest": preview.impact_digest,
                "receipt_path": receipt.relative_to(loaded.project_root).as_posix(),
                "provider_initialized": json.loads(receipt.read_text())["provider_initialized"],
            },
            impact_digest=preview.impact_digest,
        )

    def _initialize_direct(self, payload: OperationInput) -> PortResult:
        assert isinstance(payload, InitializationDirectInput)
        loaded = self._loaded_for_path(payload.configuration_path)
        receipt = initialize_memory(
            loaded,
            authorized=True,
            registry=self._registry(),
            initialize_provider=self._initialize_provider,
        )
        receipt_payload = _JSON_OBJECT.validate_json(receipt.read_bytes())
        return PortResult(
            result={
                "receipt_path": receipt.relative_to(loaded.project_root).as_posix(),
                "initialization": receipt_payload,
            }
        )

    def _operation_status(
        self,
        request: DispatchRequest,
        payload: OperationInput,
    ) -> PortResult:
        assert isinstance(payload, OperationStatusInput)
        status = self._operations.get(payload.operation_id)
        if status.project_id != request.authorization.project_id:
            raise ProjectIsolationError("operation status belongs to another project")
        return PortResult(result={"status": _model_object(status)})

    def _operation_id(
        self,
        request: DispatchRequest,
        *,
        explicit: str | None = None,
    ) -> str:
        if explicit is not None:
            return explicit
        assert request.idempotency_key is not None
        identifier = stable_id(
            "service-operation",
            request.authorization.project_id,
            request.operation.value,
            sha256_bytes(request.idempotency_key.encode("utf-8")),
        )
        return f"op_{identifier.replace('-', '')}"

    def _idempotent_replay(self, request: DispatchRequest) -> _IdempotentResult | None:
        if request.idempotency_key is None:
            return None
        key_hash = sha256_bytes(request.idempotency_key.encode("utf-8"))
        fingerprint = self._request_fingerprint(request)
        with self._state_lock:
            existing = self._idempotency.get(key_hash)
        if existing is None:
            return None
        if existing.fingerprint != fingerprint:
            raise IdempotencyConflictError(
                "idempotency key already identifies a different service request"
            )
        return existing

    def _bind_attempt(self, request: DispatchRequest) -> None:
        if request.idempotency_key is None:
            return
        key_hash = sha256_bytes(request.idempotency_key.encode("utf-8"))
        fingerprint = self._request_fingerprint(request)
        with self._state_lock:
            existing = self._attempt_fingerprints.get(key_hash)
            if existing is not None and existing != fingerprint:
                raise IdempotencyConflictError(
                    "idempotency key already identifies a different service attempt"
                )
            self._attempt_fingerprints[key_hash] = fingerprint

    def _remember_idempotent(
        self,
        request: DispatchRequest,
        outcome: PortResult,
        operation_id: str | None,
    ) -> None:
        if request.idempotency_key is None:
            return
        key_hash = sha256_bytes(request.idempotency_key.encode("utf-8"))
        candidate = _IdempotentResult(
            fingerprint=self._request_fingerprint(request),
            result=outcome.result,
            target_ids=outcome.target_ids,
            operation_id=operation_id,
            recall_trace=outcome.recall_trace,
        )
        with self._state_lock:
            existing = self._idempotency.get(key_hash)
            if existing is not None and existing != candidate:
                raise IdempotencyConflictError(
                    "idempotency state changed while publishing the result"
                )
            self._idempotency[key_hash] = candidate

    @staticmethod
    def _request_fingerprint(request: DispatchRequest) -> str:
        return sha256_bytes(
            canonical_json_bytes(
                {
                    "operation": request.operation.value,
                    "principal_id": request.authorization.identity.principal_id,
                    "project_id": request.authorization.project_id,
                    "dataset_id": request.authorization.dataset_id,
                    "scope": request.authorization.scope.model_dump(mode="json"),
                    "query_project_ids": request.authorization.query_project_ids,
                    "payload": request.payload,
                }
            )
        )

    def _success(
        self,
        request: DispatchRequest,
        result: dict[str, JsonValue],
        *,
        operation_id: str | None,
        replay: bool = False,
    ) -> DispatchSuccess:
        payload = dict(result)
        if replay:
            payload["idempotent_replay"] = True
        status_ref = None
        if isinstance(request.operation, OperationName) and request.operation in {
            OperationName.SYNC,
            OperationName.IMPROVE,
            OperationName.FORGET,
            OperationName.REBUILD,
            OperationName.EXPORT,
            OperationName.IMPORT,
        }:
            if operation_id is None:
                raise ValueError("long operation is missing its operation ID")
            status = self._operations.get(operation_id)
            status_ref = LongOperationReference(
                operation_id=status.operation_id,
                project_id=status.project_id,
                operation=status.operation,
                trace_id=request.trace_id,
                state=status.state,
                retry_safe=status.retry_safe,
                retry_after_seconds=None,
            )
        return DispatchSuccess(
            operation=request.operation,
            project_id=request.authorization.project_id,
            request_id=request.request_id,
            trace_id=request.trace_id,
            result=payload,
            operation_status=status_ref,
        )

    def _capture_audit(
        self,
        request: DispatchRequest,
        decision: AuthorizationDecision,
        outcome: str,
        *,
        target_ids: tuple[str, ...] = (),
        recall: RecallTrace | None = None,
    ) -> None:
        self._audit.capture(
            decision=decision,
            actor_id=request.authorization.identity.principal_id,
            policy_decision_ref=self._policy_decision_ref,
            outcome_code=outcome,
            trace_id=request.trace_id,
            versions=self._versions,
            target_ids=target_ids,
            counts=(CountMetric(name="target_count", value=len(target_ids)),),
            recall=recall,
        )

    @staticmethod
    def _channels(mode: RetrievalMode) -> tuple[RetrievalMode, ...]:
        if mode is RetrievalMode.HYBRID:
            return (
                RetrievalMode.EXACT,
                RetrievalMode.LEXICAL,
                RetrievalMode.SEMANTIC,
                RetrievalMode.GRAPH,
                RetrievalMode.TEMPORAL,
            )
        return (mode,)

    def _recall_trace(
        self,
        request: DispatchRequest,
        payload: OperationInput,
        result: dict[str, JsonValue],
    ) -> RecallTrace | None:
        if request.operation is not OperationName.RECALL or not isinstance(payload, RecallInput):
            return None
        raw_trace = result.get("trace")
        if isinstance(raw_trace, dict):
            return RecallTrace.model_validate(raw_trace)
        retrieval = result.get("retrieval")
        rows: list[JsonValue] = []
        omitted = 0
        if isinstance(retrieval, dict):
            raw_rows = retrieval.get("results")
            if isinstance(raw_rows, list):
                rows = raw_rows
            filters = retrieval.get("filters_applied")
            if isinstance(filters, dict):
                raw_omitted = filters.get("omitted_result_count")
                if isinstance(raw_omitted, int) and raw_omitted >= 0:
                    omitted = raw_omitted
        source_ids: set[str] = set()
        for row in rows:
            if not isinstance(row, dict):
                continue
            source = row.get("source")
            source_id = source.get("source_id") if isinstance(source, dict) else None
            if isinstance(source_id, str):
                source_ids.add(source_id)
        channels = self._channels(payload.mode)
        examined = len(rows) + omitted
        return RecallTrace(
            selected_channels=channels,
            candidates=tuple(
                RecallChannelCount(channel=channel, candidate_count=len(rows))
                for channel in channels
            ),
            filters=(
                RecallFilterTrace(
                    filter_code="service_filters",
                    examined_count=examined,
                    excluded_count=omitted,
                    reason_codes=("omitted_by_policy_or_budget",) if omitted else (),
                ),
            ),
            ranking_stages=(
                RecallRankingTrace(
                    stage_code="service_ranked",
                    input_count=examined,
                    output_count=len(rows),
                ),
            ),
            returned_source_ids=tuple(sorted(source_ids)),
            omitted_result_count=omitted,
        )

    def _record_success_metrics(
        self,
        action: InterfaceAction,
        payload: OperationInput,
        result: dict[str, JsonValue],
        elapsed_ms: float,
    ) -> None:
        if action is OperationName.RECALL and isinstance(payload, RecallInput):
            retrieval = result.get("retrieval")
            rows: list[JsonValue] = []
            sufficient = False
            if isinstance(retrieval, dict):
                raw_rows = retrieval.get("results")
                if isinstance(raw_rows, list):
                    rows = raw_rows
                sufficient = retrieval.get("evidence_state") == EvidenceState.SUFFICIENT.value
            sources = {
                source_id
                for row in rows
                if isinstance(row, dict)
                and isinstance((source := row.get("source")), dict)
                and isinstance((source_id := source.get("source_id")), str)
            }
            self._metrics.record_recall(
                channel=payload.mode,
                latency_ms=elapsed_ms,
                sufficient=sufficient,
                returned_source_count=len(sources),
            )
        elif action is OperationName.SYNC:
            succeeded = result.get("document_count", 0)
            failed = result.get("failure_count", 0)
            self._metrics.record_ingestion(
                succeeded=succeeded if isinstance(succeeded, int) else 0,
                failed=failed if isinstance(failed, int) else 0,
                lag_seconds=0.0,
            )
        elif action is OperationName.APPROVE and isinstance(payload, ApproveInput):
            self._metrics.record_approval(approved=payload.decision == "approve")
