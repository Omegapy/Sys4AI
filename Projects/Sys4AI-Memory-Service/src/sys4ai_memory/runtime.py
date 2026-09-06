"""Project-local composition for installed CLI and Python consumers.

``LocalMemoryRuntime`` accepts only a trusted root and project-relative config.
Construction performs no I/O. Dispatch loads canonical policy before opening
derived storage, and optional provider code is activated only when needed.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from pydantic import JsonValue, TypeAdapter

from sys4ai_memory.authorization import (
    AuthorizationRequest,
    AuthorizationService,
    CanonicalPermissionEnvelopeLoader,
)
from sys4ai_memory.configuration import LoadedConfiguration, load_configuration
from sys4ai_memory.contracts import (
    ErrorCategory,
    OperationName,
    Permission,
    RecordStatus,
    RetrievalMode,
)
from sys4ai_memory.contracts.models import RetrievedRecord
from sys4ai_memory.contracts.operations import operation_by_name
from sys4ai_memory.exact_index import ExactIndex
from sys4ai_memory.ingestion import (
    IngestionSynchronizer,
    SoftwareEngineeringPythonAdapter,
    SourceManifest,
    SyncCheckpoint,
)
from sys4ai_memory.initialization import preflight_initialization, validate_initialization_paths
from sys4ai_memory.interfaces.dispatcher import ServiceDispatchFailure
from sys4ai_memory.interfaces.models import (
    MUTATING_ACTIONS,
    ControlAction,
    DispatchRequest,
    DispatchResponse,
    DispatchSuccess,
    ExportInput,
    ImportInput,
    InitializationApplyInput,
    InitializationDirectInput,
    InitializationPreviewInput,
    RecallInput,
    SyncInput,
)
from sys4ai_memory.observability import AuditRecorder, VersionContext
from sys4ai_memory.profiles import ProfileSet, load_profile_set
from sys4ai_memory.providers import (
    CogneeProviderConfig,
    MemoryProvider,
    ProviderContext,
    ProviderInitializationRequest,
    ProviderMutation,
    create_provider,
)
from sys4ai_memory.retrieval import RetrievalEngine
from sys4ai_memory.security import (
    InMemoryAuditSink,
    JsonlAuditSink,
    ProjectBoundary,
    ProjectIsolationError,
)
from sys4ai_memory.security.locks import exclusive_file_lock
from sys4ai_memory.service import MemoryService, ProviderAuthorizationBridge, ServiceComponents
from sys4ai_memory.service.dispatcher import _run_coroutine
from sys4ai_memory.service.errors import normalize_service_exception
from sys4ai_memory.sources import (
    DiscoveryDisposition,
    DiscoveryReason,
    RegistryBundle,
    SourceDiscovery,
    load_registry_bundle,
)
from sys4ai_memory.util import atomic_write_text, canonical_json_bytes, resolve_within, sha256_bytes

_JSON_OBJECT = TypeAdapter(dict[str, JsonValue])
_INITIALIZATION_ACTIONS = {
    ControlAction.INITIALIZE_DIRECT,
    ControlAction.INITIALIZE_PREVIEW,
    ControlAction.INITIALIZE_APPLY,
}
_INSPECTION_ACTIONS = {
    OperationName.HEALTH,
    OperationName.SOURCES_LIST,
    OperationName.SOURCES_EXPLAIN,
    ControlAction.OPERATION_STATUS,
}


def _load_registry(loaded: LoadedConfiguration) -> RegistryBundle:
    registry = load_registry_bundle(
        source_registry=loaded.resolved_paths["source_registry"],
        profile_registry=loaded.resolved_paths["profile_registry"],
        relation_registry=loaded.resolved_paths["relation_registry"],
        project_root=loaded.project_root,
    )
    if any(
        source.project_id != loaded.configuration.memory.project_id for source in registry.sources
    ):
        raise ProjectIsolationError("source registry belongs to a different project")
    return registry


def _verify_current_sources(
    loaded: LoadedConfiguration, index: ExactIndex, response: DispatchSuccess
) -> None:
    """Reread only sources supporting returned current records, before delivery."""

    raw_records: object
    if response.operation is OperationName.RECALL:
        retrieval = _JSON_OBJECT.validate_python(response.result["retrieval"])
        raw_records = retrieval["results"]
    elif response.operation is OperationName.GET:
        raw_records = response.result["records"]
    else:
        raw_record = response.result["record"]
        raw_records = [] if raw_record is None else [raw_record]
    records = TypeAdapter(tuple[RetrievedRecord, ...]).validate_python(raw_records)
    current = tuple(
        record
        for record in records
        if record.lifecycle.status in {RecordStatus.ACTIVE, RecordStatus.APPROVED}
    )
    if not current:
        return
    # Registry revocations made during backend work must take effect too.
    registry = _load_registry(loaded)
    memory = loaded.configuration.memory
    discovery = SourceDiscovery(
        project_root=loaded.project_root,
        project_id=memory.project_id,
        entries=registry.sources,
        respect_gitignore=memory.sources.respect_gitignore,
        secret_scan=memory.security.secret_scan,
    )
    by_rule = {entry.source_id: entry for entry in registry.sources}
    hashes: dict[str, str] = {}
    for record in current:
        source = record.source
        if source.path is None or source.content_sha256 is None:
            raise ServiceDispatchFailure(
                ErrorCategory.INDEX_DRIFT,
                message="The current exact result has no verifiable local source.",
                remediation_hint="Synchronize a registered local source before using this result.",
            )
        decision = discovery.explain_path(source.path)
        if decision.disposition is not DiscoveryDisposition.INCLUDED:
            category = (
                ErrorCategory.INDEX_DRIFT
                if decision.reason in {DiscoveryReason.MISSING, DiscoveryReason.NOT_REGULAR}
                else ErrorCategory.SOURCE_EXCLUDED
            )
            raise ServiceDispatchFailure(category)
        if decision.source_id != source.source_id:
            raise ServiceDispatchFailure(ErrorCategory.INDEX_DRIFT)
        revision = source.locator.get("source_revision")
        if not isinstance(revision, str):
            raise ServiceDispatchFailure(ErrorCategory.INDEX_DRIFT)
        hydrated = index.resolve_record(
            project_id=memory.project_id,
            record_id=record.record_id,
            source_revision=revision,
            source_path=source.path,
        )
        rule = by_rule[decision.rule_ids[0]]
        if hydrated is None or (
            hydrated.authority.tier != rule.authority_tier
            or hydrated.authority.trust_class != rule.trust_class
            or hydrated.authority.canonical != (rule.canonicality == "canonical")
            or hydrated.security.sensitivity != rule.sensitivity
            or hydrated.namespace != rule.namespace
            or hydrated.processing.profile_id != rule.profile_id
        ):
            raise ServiceDispatchFailure(ErrorCategory.INDEX_DRIFT)
        if source.path not in hashes:
            try:
                path = resolve_within(loaded.project_root, source.path)
                with path.open("rb") as stream:
                    content = stream.read(discovery.max_file_bytes + 1)
                if len(content) > discovery.max_file_bytes:
                    raise ServiceDispatchFailure(ErrorCategory.INDEX_DRIFT)
                hashes[source.path] = sha256_bytes(content)
            except OSError as error:
                raise ServiceDispatchFailure(ErrorCategory.INDEX_DRIFT) from error
        if hashes[source.path] != source.content_sha256:
            raise ServiceDispatchFailure(ErrorCategory.INDEX_DRIFT)


def _load_profiles(loaded: LoadedConfiguration, registry: RegistryBundle) -> ProfileSet:
    by_id = {item.profile_id: item for item in registry.profiles}
    selected: set[str] = set()
    pending = [loaded.configuration.memory.default_memory_profile]
    while pending:
        profile_id = pending.pop()
        if profile_id in selected:
            continue
        profile = by_id[profile_id]
        selected.add(profile_id)
        if profile.extends_profile_id is not None:
            pending.append(profile.extends_profile_id)
    capabilities = {
        "service_health",
        "source_registry",
        "ingestion",
        "exact",
        "lexical",
        "provenance_explanation",
    }
    if loaded.configuration.memory.models.semantic_enabled:
        capabilities.update({"semantic", "graph", "temporal"})
    return load_profile_set(
        tuple(
            resolve_within(
                loaded.project_root,
                "profiles/base/profile.yaml" if item == "base@1" else by_id[item].config_ref,
            )
            for item in sorted(selected)
        ),
        trusted_project_root=loaded.project_root,
        enabled_capabilities=frozenset(capabilities),
    )


def _configured_provider(loaded: LoadedConfiguration) -> CogneeProviderConfig:
    memory = loaded.configuration.memory
    if memory.provider.name != "cognee":
        raise ServiceDispatchFailure(ErrorCategory.PROVIDER_UNSUPPORTED)
    llm = memory.models.profile(memory.models.llm_profile)
    embedding = memory.models.profile(memory.models.embedding_profile)
    if llm is None or embedding is None:
        raise ServiceDispatchFailure(ErrorCategory.PROFILE_INCOMPATIBLE)
    if (
        memory.provider.mode != "standalone"
        or memory.provider.outbound_network not in {"deny", "local-only"}
        or memory.models.allow_remote
        or llm.locality != "local"
        or embedding.locality != "local"
    ):
        raise ServiceDispatchFailure(ErrorCategory.PROVIDER_UNSUPPORTED)
    return CogneeProviderConfig.model_validate(
        {
            "project_id": memory.project_id,
            "dataset_id": memory.provider.cognee.dataset,
            "version_constraint": memory.provider.version_constraint,
            "project_root": str(loaded.project_root),
            "derived_data_root": str(loaded.resolved_paths["local_data"]),
            "model_cache_root": str(loaded.resolved_paths["model_cache"]),
            "semantic_enabled": memory.models.semantic_enabled,
            "llm_provider": llm.provider,
            "llm_model": llm.model,
            "llm_endpoint": llm.endpoint,
            "embedding_provider": embedding.provider,
            "embedding_model": embedding.model,
            "embedding_dimensions": embedding.dimensions,
        }
    )


def _initialization_receipt(loaded: LoadedConfiguration) -> dict[str, JsonValue] | None:
    root = loaded.project_root
    relative = (loaded.resolved_paths["local_data"] / "receipts/initialization.json").relative_to(
        root
    )
    path = resolve_within(root, relative, must_exist=False)
    if not path.is_file():
        return None
    receipt = _JSON_OBJECT.validate_json(path.read_bytes())
    memory = loaded.configuration.memory
    if (
        receipt.get("project_id") != memory.project_id
        or receipt.get("dataset_id") != memory.provider.cognee.dataset
        or receipt.get("configuration_fingerprint") != loaded.fingerprint
        or receipt.get("exact_index_initialized") is not True
        or not loaded.resolved_paths["exact_index"].is_file()
    ):
        raise ServiceDispatchFailure(ErrorCategory.MEMORY_NOT_INITIALIZED)
    validate_initialization_paths(loaded)
    return receipt


def _sync_state(loaded: LoadedConfiguration) -> tuple[SourceManifest | None, SyncCheckpoint | None]:
    relative = (loaded.resolved_paths["local_data"] / "receipts/sync-state.json").relative_to(
        loaded.project_root
    )
    target = resolve_within(loaded.project_root, relative, must_exist=False)
    if not target.is_file():
        return None, None
    value = _JSON_OBJECT.validate_json(target.read_bytes())
    if value.get("configuration_fingerprint") != loaded.fingerprint:
        raise ServiceDispatchFailure(ErrorCategory.INDEX_DRIFT)
    raw_manifest = value.get("manifest")
    raw_checkpoint = value.get("checkpoint")
    if not isinstance(raw_manifest, dict) or not isinstance(raw_checkpoint, dict):
        raise ValueError("persisted synchronization state is invalid")
    manifest = SourceManifest.from_json_dict(raw_manifest)
    if manifest.project_id != loaded.configuration.memory.project_id:
        raise ValueError("persisted synchronization state belongs to another project")
    completed = raw_checkpoint.get("completed_revisions", [])
    failed = raw_checkpoint.get("failed_sources", [])
    if not isinstance(completed, list) or not isinstance(failed, list):
        raise ValueError("persisted synchronization checkpoint is invalid")
    timestamp = raw_checkpoint.get("updated_at")
    checkpoint = SyncCheckpoint(
        project_id=manifest.project_id,
        completed_revisions=tuple(
            (str(item["source_id"]), str(item["content_sha256"]))
            for item in completed
            if isinstance(item, dict)
        ),
        failed_sources=tuple(
            (str(item["source_id"]), str(item["error_category"]))
            for item in failed
            if isinstance(item, dict)
        ),
        updated_at=datetime.fromisoformat(timestamp) if isinstance(timestamp, str) else None,
    )
    return manifest, checkpoint


@dataclass(frozen=True, slots=True)
class LocalMemoryRuntime:
    """Executable dispatcher for one configured local project, without a server."""

    project_root: Path
    configuration_path: str = "config/memory.toml"

    def dispatch(self, request: DispatchRequest) -> DispatchResponse:
        try:
            return self._dispatch(request)
        except Exception as error:  # noqa: BLE001 - public failures never expose local content
            return normalize_service_exception(
                error, trace_id=request.trace_id, operation=request.operation
            )

    def _dispatch(self, request: DispatchRequest) -> DispatchResponse:
        payload = request.typed_payload()
        configuration_path = (
            payload.configuration_path
            if isinstance(
                payload,
                InitializationDirectInput | InitializationPreviewInput | InitializationApplyInput,
            )
            else self.configuration_path
        )
        config_path = resolve_within(self.project_root, configuration_path, must_exist=False)
        if not config_path.exists():
            raise ServiceDispatchFailure(ErrorCategory.MEMORY_NOT_INITIALIZED)
        loaded = load_configuration(config_path, trusted_project_root=self.project_root)
        memory = loaded.configuration.memory
        boundary = ProjectBoundary(
            memory.project_id, memory.provider.cognee.dataset, loaded.project_root
        )
        authorization_path = (Path(memory.control_records.root) / "permissions.json").as_posix()
        loader = CanonicalPermissionEnvelopeLoader(boundary, authorization_path)
        authorization = AuthorizationService(loader)
        permission = (
            operation_by_name(request.operation).required_permission
            if isinstance(request.operation, OperationName)
            else Permission.READ
            if request.operation is ControlAction.OPERATION_STATUS
            else Permission.ADMINISTER
        )
        target = (
            payload.configuration_path
            if isinstance(
                payload,
                InitializationDirectInput | InitializationPreviewInput | InitializationApplyInput,
            )
            else None
        )
        if isinstance(payload, ExportInput):
            target = payload.output_path
        elif isinstance(payload, ImportInput):
            target = payload.package_path
        authorization.require(
            AuthorizationRequest(
                principal_id=request.authorization.identity.principal_id,
                project_id=request.authorization.project_id,
                dataset_id=request.authorization.dataset_id,
                operation=request.operation.value,
                permission=permission,
                scope=request.authorization.scope,
                target_path=target,
                query_project_ids=request.authorization.query_project_ids,
                explicit_cross_project=request.authorization.explicit_cross_project,
                trace_id=request.trace_id,
                require_action_specific=request.operation in MUTATING_ACTIONS
                or request.operation is ControlAction.INITIALIZE_PREVIEW,
            )
        )
        registry = _load_registry(loaded)
        profiles = _load_profiles(loaded, registry)
        bridge = ProviderAuthorizationBridge(authorization, loader)
        provider: MemoryProvider | None = None
        initialization = request.operation in _INITIALIZATION_ACTIONS
        inspection = request.operation in _INSPECTION_ACTIONS or (
            isinstance(payload, SyncInput) and payload.dry_run
        )
        needs_provider = memory.models.semantic_enabled and (
            request.operation is OperationName.SYNC
            and not inspection
            or request.operation is OperationName.GRAPH
            or isinstance(payload, RecallInput)
            and payload.mode not in {RetrievalMode.EXACT, RetrievalMode.LEXICAL}
        )
        exact_read = request.operation in {OperationName.GET, OperationName.EXPLAIN} or (
            request.operation is OperationName.RECALL
            and isinstance(payload, RecallInput)
            and payload.mode in {RetrievalMode.EXACT, RetrievalMode.LEXICAL}
            and not payload.synthesize
        )
        provider_config = (
            _configured_provider(loaded)
            if memory.models.semantic_enabled and (initialization or needs_provider)
            else None
        )
        context = ProviderContext(
            project_id=memory.project_id,
            dataset_id=memory.provider.cognee.dataset,
            principal_id=request.authorization.identity.principal_id,
            scope=request.authorization.scope,
            trace_id=request.trace_id,
        )
        provider_operation = (
            ControlAction.INITIALIZE_APPLY.value
            if request.operation is ControlAction.INITIALIZE_APPLY
            else ControlAction.INITIALIZE_DIRECT.value
        )
        provider_grant = (
            bridge.authorize(
                context,
                ProviderMutation.INITIALIZE,
                authorization_operation=provider_operation,
                target_path=configuration_path,
            )
            if provider_config is not None
            and request.operation is not ControlAction.INITIALIZE_PREVIEW
            else None
        )

        def initialize_provider() -> bool:
            nonlocal provider
            if provider_config is None:
                return False
            assert provider_grant is not None
            provider = create_provider(provider_config)
            result = _run_coroutine(
                provider.initialize(
                    ProviderInitializationRequest(
                        context=context,
                        configuration_fingerprint=loaded.fingerprint,
                        dry_run=False,
                        path_boundaries_validated=True,
                        exclusions_validated=True,
                        discovery_dry_run_approved=True,
                        authorization=provider_grant,
                    )
                )
            )
            if not result.initialized:
                raise ServiceDispatchFailure(ErrorCategory.PROVIDER_UNAVAILABLE)
            return True

        sink = InMemoryAuditSink()
        versions = VersionContext(
            configuration_version=loaded.configuration.config_version,
            configuration_fingerprint=loaded.fingerprint,
            profile_versions={
                item.profile.profile_id: item.profile.version for item in profiles.profiles
            },
            profile_fingerprints={
                item.profile.profile_id: item.content_sha256 for item in profiles.profiles
            },
            provider_name=memory.provider.name,
            provider_version=memory.provider.version_constraint.removeprefix("=="),
            provider_fingerprint=sha256_bytes(
                canonical_json_bytes(memory.provider.model_dump(mode="json"))
            ),
            source_registry_fingerprint=sha256_bytes(
                loaded.resolved_paths["source_registry"].read_bytes()
            ),
        )
        components = ServiceComponents(registry_loader=lambda: _load_registry(loaded))

        def invoke(index: ExactIndex | None = None) -> DispatchResponse:
            manifest: SourceManifest | None = None
            checkpoint: SyncCheckpoint | None = None
            if index is not None:
                manifest, checkpoint = _sync_state(loaded)
                components.exact_index = index
                components.lifecycle_index = index
                components.synchronizer = IngestionSynchronizer(
                    project_root=loaded.project_root,
                    index_writer=index,
                    profile_set=profiles,
                    optional_adapters=(SoftwareEngineeringPythonAdapter(),)
                    if "software-engineering@1" in profiles.profile_ids
                    else (),
                )
                components.provider = provider
                components.retrieval = RetrievalEngine(
                    project_id=memory.project_id,
                    dataset_id=memory.provider.cognee.dataset,
                    authorizer=authorization,
                    exact_backend=index,
                    exact_record_resolver=index,
                    lifecycle_resolver=index,
                    provider=provider,
                )
            service = MemoryService(
                configuration=loaded,
                authorization=authorization,
                audit=AuditRecorder(sink),
                versions=versions,
                components=components,
                provider_authorization=bridge,
                initialize_provider=initialize_provider,
                sync_manifest=manifest,
                sync_checkpoint=checkpoint,
                policy_decision_ref=authorization_path,
            )
            response = service.dispatch(request)
            if exact_read and isinstance(response, DispatchSuccess):
                assert index is not None
                _verify_current_sources(loaded, index, response)
            if (
                isinstance(response, DispatchSuccess)
                and request.operation is OperationName.SYNC
                and not inspection
            ):
                state = {
                    "configuration_fingerprint": loaded.fingerprint,
                    "manifest": response.result["manifest"],
                    "checkpoint": response.result["checkpoint"],
                }
                atomic_write_text(
                    loaded.resolved_paths["local_data"] / "receipts/sync-state.json",
                    json.dumps(state, sort_keys=True, separators=(",", ":")) + "\n",
                )
            return response

        if initialization or inspection:
            response = invoke()
        else:
            receipt = _initialization_receipt(loaded)
            if receipt is None:
                raise ServiceDispatchFailure(ErrorCategory.MEMORY_NOT_INITIALIZED)
            # Current exact reads validate their returned sources below. Full
            # discovery still precedes every mutation and provider activation.
            if not exact_read:
                preflight_initialization(loaded, registry=registry)
            derived = loaded.resolved_paths["local_data"]
            lock = resolve_within(
                loaded.project_root,
                (derived / ".runtime.lock").relative_to(loaded.project_root),
                must_exist=False,
            )
            with exclusive_file_lock(lock):
                if needs_provider:
                    if receipt.get("provider_initialized") is not True:
                        raise ServiceDispatchFailure(ErrorCategory.MEMORY_NOT_INITIALIZED)
                    initialize_provider()
                with ExactIndex(loaded.resolved_paths["exact_index"]) as index:
                    response = invoke(index)

        if (
            isinstance(response, DispatchSuccess)
            and request.operation is not ControlAction.INITIALIZE_PREVIEW
        ):
            receipt = _initialization_receipt(loaded)
            if receipt is not None and memory.observability.content_logging != "disabled":
                audit = JsonlAuditSink(
                    boundary,
                    memory.observability.local_audit_log,
                    retention_policy_id=memory.retention.policy_status,
                )
                for event in sink.events():
                    audit.record(event)
        return response
