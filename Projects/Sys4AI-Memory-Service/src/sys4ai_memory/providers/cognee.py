"""Lazy, policy-gated Cognee 1.5.3 provider adapter.

The module intentionally has no top-level ``import cognee``.  The real runtime
is loaded only after a validated local configuration and explicit provider
initialization.  Public methods return only Sys4AI provider contracts.
"""

from __future__ import annotations

import asyncio
import importlib
import importlib.metadata
import json
import os
import re
import sys
from collections.abc import Callable, Iterable, Iterator, Mapping
from contextlib import contextmanager, suppress
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any, Protocol, TypeVar, cast
from uuid import NAMESPACE_URL, UUID, uuid5

from pydantic import ValidationError

from sys4ai_memory.contracts import CapabilityName, RecordStatus, RetrievalMode, Sensitivity
from sys4ai_memory.contracts.errors import ErrorCategory
from sys4ai_memory.contracts.models import MemoryRecord, RelationRecord
from sys4ai_memory.util.time import utc_now

from .base import require_authorization, require_context
from .contracts import (
    COGNEE_PROVIDER_VERSION,
    CogneeProviderConfig,
    ExportRequest,
    ExportResult,
    ForgetAction,
    ForgetRequest,
    ForgetResult,
    HealthRequest,
    ImportRequest,
    ImportResult,
    ImproveRequest,
    ImproveResult,
    MigrationRequest,
    MigrationResult,
    PolicyEnvelope,
    ProviderCapabilities,
    ProviderChannelScores,
    ProviderContext,
    ProviderExportFormat,
    ProviderHealth,
    ProviderHealthComponent,
    ProviderHealthProbe,
    ProviderHealthState,
    ProviderInitializationRequest,
    ProviderInitializationResult,
    ProviderMutation,
    ProviderName,
    ProviderRecallCandidate,
    ProviderRecallResult,
    RecallRequest,
    RememberRequest,
    RememberResult,
    stable_digest,
)
from .errors import MemoryProviderError, normalize_provider_exception, provider_error

_T = TypeVar("_T")
_SENSITIVE_CONTENT = re.compile(
    r"(?:-----BEGIN [A-Z ]*PRIVATE KEY-----|\bsk-(?:proj-)?[A-Za-z0-9_-]{8,}\b|"
    r"\b(?:api[_-]?key|access[_-]?token|password|secret)\s*[:=]\s*\S+)",
    flags=re.IGNORECASE,
)
_SENSITIVE_FIELD = re.compile(
    r"(?:^|\.)(?:api[_-]?key|access[_-]?token|password|secret|credential|private[_-]?key)(?:\.|$)",
    flags=re.IGNORECASE,
)
_SUPPORTED_CAPABILITIES = (
    CapabilityName.SERVICE_HEALTH,
    CapabilityName.INGESTION,
    CapabilityName.LEXICAL,
    CapabilityName.SEMANTIC,
    CapabilityName.GRAPH,
    CapabilityName.TEMPORAL,
    CapabilityName.PORTABLE_IMPORT,
    CapabilityName.LIFECYCLE,
    CapabilityName.IMPROVEMENT,
)
_SEMANTIC_CAPABILITIES = frozenset(
    {
        CapabilityName.INGESTION,
        CapabilityName.LEXICAL,
        CapabilityName.SEMANTIC,
        CapabilityName.GRAPH,
        CapabilityName.TEMPORAL,
        CapabilityName.PORTABLE_IMPORT,
    }
)
_SAFE_ENVIRONMENT = {
    "PYTHON_DOTENV_DISABLED": "1",
    "TELEMETRY_DISABLED": "1",
    "COGNEE_TRACING_ENABLED": "false",
    "CACHING": "false",
    "ENABLE_BACKEND_ACCESS_CONTROL": "false",
    "STORAGE_BACKEND": "local",
    "HF_HUB_OFFLINE": "1",
    "TRANSFORMERS_OFFLINE": "1",
    "LITELLM_LOCAL_MODEL_COST_MAP": "True",
    "DO_NOT_TRACK": "1",
    "ANONYMIZED_TELEMETRY": "false",
}
_CLEARED_REMOTE_ENVIRONMENT = (
    "LLM_API_KEY",
    "EMBEDDING_API_KEY",
    "FALLBACK_API_KEY",
    "FALLBACK_ENDPOINT",
    "FALLBACK_MODEL",
    "LANGFUSE_PUBLIC_KEY",
    "LANGFUSE_SECRET_KEY",
    "LANGFUSE_HOST",
    "LANGFUSE_BASE_URL",
    "OTEL_EXPORTER_OTLP_ENDPOINT",
    "OTEL_EXPORTER_OTLP_HEADERS",
)
_LOCAL_NO_AUTH_SENTINEL = "local-provider-no-auth"


COGNEE_API_UNCERTAINTIES = (
    "Cognee recall result shapes vary by search type; CHUNKS metadata rejoin is verified, "
    "while other native result shapes remain normalized defensively.",
    "DataItem external_metadata and stable data_id mapping are verified for local semantic "
    "remember/recall on Cognee 1.5.3.",
    "Typed Sys4AI relations create native graph representations, but provider-native edge "
    "semantics remain subordinate to Sys4AI relation contracts.",
    "Cognee health probes can create or write storage, so the adapter does not call them.",
    "Database-backed COGX dataset export/import and migration still require a "
    "disposable-generation smoke test; the native archive API alone is verified.",
)


@dataclass(frozen=True, slots=True)
class CogneeMappedItem:
    """Allowlisted data passed to Cognee after Sys4AI policy and schema checks."""

    data_id: UUID
    text: str
    label: str
    external_metadata: dict[str, object]


class CogneeRuntime(Protocol):
    """Small injectable seam around the installed Cognee package."""

    @property
    def loaded(self) -> bool: ...

    def installed_version(self) -> str: ...

    async def configure(self, config: CogneeProviderConfig) -> None: ...

    async def remember(
        self, items: tuple[CogneeMappedItem, ...], config: CogneeProviderConfig
    ) -> object: ...

    async def recall(self, request: RecallRequest, config: CogneeProviderConfig) -> object: ...

    async def improve(self, request: ImproveRequest, config: CogneeProviderConfig) -> object: ...

    async def forget(
        self, data_ids: tuple[UUID, ...], request: ForgetRequest, config: CogneeProviderConfig
    ) -> object: ...

    async def export(self, request: ExportRequest, config: CogneeProviderConfig) -> object: ...

    async def import_snapshot(
        self, request: ImportRequest, config: CogneeProviderConfig
    ) -> object: ...

    async def migrate(self, request: MigrationRequest, config: CogneeProviderConfig) -> object: ...


class LazyCogneeRuntime:
    """Real runtime bridge that imports Cognee only at the first authorized use."""

    def __init__(
        self,
        *,
        importer: Callable[[str], ModuleType] = importlib.import_module,
        version_reader: Callable[[str], str] = importlib.metadata.version,
    ) -> None:
        self._importer = importer
        self._version_reader = version_reader
        self._module: ModuleType | None = None
        self._project_binding: tuple[str, ...] | None = None

    @property
    def loaded(self) -> bool:
        return self._module is not None

    def installed_version(self) -> str:
        return self._version_reader("cognee")

    async def configure(self, config: CogneeProviderConfig) -> None:
        # Initialization is the one authorized writeful provider operation that
        # may create derived storage. Keep both package import and database
        # creation inside the hardened environment so Cognee cannot fall back to
        # host paths, dotenv credentials, telemetry, or a remote backend.
        with self._security_environment(config):
            module = self._load(config)
            config_api = getattr(module, "config", None)
            if config_api is None:
                raise RuntimeError("Cognee configuration API is unavailable")
            derived_root = Path(config.derived_data_root)
            settings = {
                "data_root_directory": derived_root / "cognee" / "data",
                "system_root_directory": derived_root / "cognee" / "system",
            }
            for method_name, value in settings.items():
                setter = getattr(config_api, method_name, None)
                if not callable(setter):
                    raise RuntimeError(
                        f"Cognee configuration setter is unavailable: {method_name}"
                    )
                setter(str(value))

            relational = self._importer("cognee.infrastructure.databases.relational")
            create_database = getattr(relational, "create_db_and_tables", None)
            if not callable(create_database):
                raise RuntimeError("Cognee relational database initializer is unavailable")
            await create_database()

    async def remember(
        self, items: tuple[CogneeMappedItem, ...], config: CogneeProviderConfig
    ) -> object:
        with self._security_environment(config):
            module = self._load(config)
            data_item_module = self._importer("cognee.tasks.ingestion.data_item")
            data_item_type = data_item_module.DataItem
            native_items = [
                data_item_type(
                    data=item.text,
                    label=item.label,
                    external_metadata=item.external_metadata,
                    data_id=item.data_id,
                )
                for item in items
            ]
            llm_config, embedding_config = self._model_configs(config)
            return await module.remember(
                native_items,
                dataset_name=config.dataset_id,
                run_in_background=False,
                self_improvement=False,
                llm_config=llm_config,
                embedding_config=embedding_config,
            )

    async def recall(self, request: RecallRequest, config: CogneeProviderConfig) -> object:
        with self._security_environment(config):
            module = self._load(config)
            query_type_name = {
                RetrievalMode.LEXICAL: "CHUNKS_LEXICAL",
                RetrievalMode.SEMANTIC: "CHUNKS",
                RetrievalMode.GRAPH: "GRAPH_COMPLETION",
                RetrievalMode.TEMPORAL: "TEMPORAL",
                RetrievalMode.HYBRID: "HYBRID_COMPLETION",
            }[request.mode]
            search_type = module.SearchType[query_type_name]
            llm_config, embedding_config = self._model_configs(config)
            raw = await module.recall(
                request.query,
                query_type=search_type,
                datasets=[config.dataset_id],
                top_k=request.top_k,
                auto_route=False,
                scope="graph",
                # CHUNKS and CHUNKS_LEXICAL preserve document_id only in their
                # normalized payload result. ``only_context=True`` collapses
                # those payloads into one plain string and destroys the stable
                # metadata rejoin key.
                only_context=False,
                include_references=True,
                llm_config=llm_config,
                embedding_config=embedding_config,
            )
            return await self._join_external_metadata(raw)

    async def improve(self, request: ImproveRequest, config: CogneeProviderConfig) -> object:
        with self._security_environment(config):
            module = self._load(config)
            llm_config, embedding_config = self._model_configs(config)
            return await module.improve(
                dataset=config.dataset_id,
                run_in_background=False,
                node_name=list(request.record_ids) or None,
                llm_config=llm_config,
                embedding_config=embedding_config,
            )

    async def forget(
        self, data_ids: tuple[UUID, ...], request: ForgetRequest, config: CogneeProviderConfig
    ) -> object:
        with self._security_environment(config):
            module = self._load(config)
            results = []
            for data_id in data_ids:
                results.append(
                    await module.forget(
                        data_id=data_id,
                        dataset=config.dataset_id,
                        memory_only=request.action is ForgetAction.DELETE_DERIVED,
                    )
                )
            return results

    async def export(self, request: ExportRequest, config: CogneeProviderConfig) -> object:
        with self._security_environment(config):
            module = self._load(config)
            return await module.export(
                config.dataset_id,
                format="cogx",
                destination=request.destination,
                include_permissions=False,
            )

    async def import_snapshot(
        self, request: ImportRequest, config: CogneeProviderConfig
    ) -> object:
        with self._security_environment(config):
            module = self._load(config)
            source = module.migration.COGXArchiveSource(request.source)
            return await module.remember(source, dataset_name=config.dataset_id)

    async def migrate(self, request: MigrationRequest, config: CogneeProviderConfig) -> object:
        del request, config
        raise NotImplementedError("Cognee data migration needs a disposable smoke test")

    def _load(self, config: CogneeProviderConfig) -> ModuleType:
        binding = (
            str(config.project_id), str(config.dataset_id), config.project_root,
            config.derived_data_root, str(config.resolved_model_cache_root),
        )
        if self._project_binding is not None and binding != self._project_binding:
            raise RuntimeError("A Cognee runtime cannot be reused across project boundaries")
        if self._module is not None:
            return self._module
        if self._importer is importlib.import_module and "cognee" in sys.modules:
            raise RuntimeError("Cognee was imported before the hardened adapter boundary")
        with self._security_environment(config):
            module = self._importer("cognee")
        module_version = getattr(module, "__version__", None)
        if module_version != COGNEE_PROVIDER_VERSION:
            raise RuntimeError("The imported Cognee version is incompatible")
        required = ("remember", "recall", "improve", "forget", "export", "config")
        if any(not hasattr(module, name) for name in required):
            raise RuntimeError("The installed Cognee API surface is incomplete")
        self._module = module
        self._project_binding = binding
        return module

    @staticmethod
    @contextmanager
    def _security_environment(config: CogneeProviderConfig) -> Iterator[None]:
        """Apply import-time hardening without clobbering the host process environment."""

        # Recheck immediately before provider use; paths may have changed since
        # the frozen configuration was constructed.
        CogneeProviderConfig.model_validate(config.model_dump())
        model_cache = config.resolved_model_cache_root
        values = dict(_SAFE_ENVIRONMENT)
        values.update({name: "" for name in _CLEARED_REMOTE_ENVIRONMENT})
        values.update(
            {
                "DATA_ROOT_DIRECTORY": str(Path(config.derived_data_root) / "cognee" / "data"),
                "SYSTEM_ROOT_DIRECTORY": str(
                    Path(config.derived_data_root) / "cognee" / "system"
                ),
                "CACHE_ROOT_DIRECTORY": str(Path(config.derived_data_root) / "cognee" / "cache"),
                "COGNEE_LOGS_DIR": str(Path(config.derived_data_root) / "cognee" / "logs"),
                "FASTEMBED_CACHE_PATH": str(model_cache / "fastembed"),
                "HF_HOME": str(model_cache / "huggingface"),
                "HF_HUB_CACHE": str(model_cache / "huggingface" / "hub"),
                "HUGGINGFACE_HUB_CACHE": str(model_cache / "huggingface" / "hub"),
                "TRANSFORMERS_CACHE": str(model_cache / "transformers"),
                "SENTENCE_TRANSFORMERS_HOME": str(model_cache / "sentence-transformers"),
                "TORCH_HOME": str(model_cache / "torch"),
                "XDG_CACHE_HOME": str(model_cache / "cache"),
            }
        )
        if config.semantic_enabled:
            assert config.llm_provider is not None
            assert config.llm_model is not None
            assert config.llm_endpoint is not None
            assert config.embedding_provider is not None
            assert config.embedding_model is not None
            assert config.embedding_dimensions is not None
            values.update(
                {
                    "LLM_PROVIDER": config.llm_provider,
                    "LLM_MODEL": config.llm_model,
                    "LLM_ENDPOINT": config.llm_endpoint,
                    "EMBEDDING_PROVIDER": config.embedding_provider,
                    "EMBEDDING_MODEL": config.embedding_model,
                    "EMBEDDING_DIMENSIONS": str(config.embedding_dimensions),
                }
            )
            if config.llm_provider.casefold() == "ollama":
                # Cognee 1.5.3 requires the Ollama model, endpoint, and key
                # variables to be present as a complete set during import.
                # Ollama's loopback API does not authenticate this value.
                values["LLM_API_KEY"] = _LOCAL_NO_AUTH_SENTINEL

        missing = object()
        previous: dict[str, str | object] = {
            name: os.environ.get(name, missing) for name in values
        }
        os.environ.update(values)
        try:
            yield
        finally:
            for name, prior in previous.items():
                if prior is missing:
                    os.environ.pop(name, None)
                else:
                    os.environ[name] = cast(str, prior)

    def _model_configs(self, config: CogneeProviderConfig) -> tuple[object, object]:
        if not config.semantic_enabled:
            raise RuntimeError("Cognee semantic operations are disabled")
        llm_module = self._importer("cognee.infrastructure.llm.config")
        embedding_module = self._importer(
            "cognee.infrastructure.databases.vector.embeddings.config"
        )
        llm_config = llm_module.LLMConfig(
            _env_file=None,
            llm_provider=config.llm_provider,
            llm_model=config.llm_model,
            llm_endpoint=config.llm_endpoint,
            llm_api_key=(
                _LOCAL_NO_AUTH_SENTINEL
                if config.llm_provider == "ollama"
                else None
            ),
            fallback_api_key="",
            fallback_endpoint="",
            fallback_model="",
        )
        embedding_config = embedding_module.EmbeddingConfig(
            _env_file=None,
            embedding_provider=config.embedding_provider,
            embedding_model=config.embedding_model,
            embedding_dimensions=config.embedding_dimensions,
            embedding_endpoint=None,
            embedding_api_key=None,
        )
        return llm_config, embedding_config

    async def _join_external_metadata(self, raw: object) -> object:
        """Rejoin Cognee chunk hits to persisted Sys4AI metadata by stable data ID.

        Cognee 1.5.3 stores ``DataItem.external_metadata`` in its relational
        ``data`` table, while CHUNKS recall returns only the originating
        ``data_id``. Rejoining inside the private runtime bridge preserves the
        provider-neutral public contract across process restarts without
        exposing a native database handle to callers.
        """

        items = tuple(raw) if isinstance(raw, (list, tuple)) else (raw,)
        identifiers = {
            identifier
            for item in items
            for identifier in self._native_data_ids(item)
        }
        if not identifiers:
            return raw

        sqlalchemy = self._importer("sqlalchemy")
        data_module = self._importer("cognee.modules.data.models.Data")
        relational = self._importer("cognee.infrastructure.databases.relational")
        data_model = data_module.Data
        engine = relational.get_relational_engine()
        async with engine.get_async_session() as session:
            result = await session.execute(
                sqlalchemy.select(data_model).where(data_model.id.in_(identifiers))
            )
            rows = tuple(result.scalars().all())
        metadata_by_id = {
            row.id: row.external_metadata
            for row in rows
            if isinstance(row.external_metadata, Mapping)
        }
        if not metadata_by_id:
            return raw

        enriched: list[object] = []
        for item in items:
            native = self._native_plain(item)
            metadata = [
                metadata_by_id[identifier]
                for identifier in self._native_data_ids(item)
                if identifier in metadata_by_id
            ]
            enriched.append(
                {
                    "native_result": native,
                    "external_metadata": metadata,
                }
                if metadata
                else item
            )
        return enriched

    @staticmethod
    def _native_plain(value: object) -> object:
        if isinstance(value, Mapping):
            return {str(key): item for key, item in value.items()}
        model_dump = getattr(value, "model_dump", None)
        if callable(model_dump):
            try:
                return model_dump(mode="json")
            except (TypeError, ValueError):
                return model_dump()
        return value

    @classmethod
    def _native_data_ids(cls, value: object) -> tuple[UUID, ...]:
        pending = [cls._native_plain(value)]
        visited: set[int] = set()
        found: set[UUID] = set()
        while pending:
            current = pending.pop()
            identity = id(current)
            if identity in visited:
                continue
            visited.add(identity)
            if isinstance(current, Mapping):
                for key, item in current.items():
                    if key in {"data_id", "document_id"}:
                        with suppress(TypeError, ValueError, AttributeError):
                            found.add(UUID(str(item)))
                    pending.append(item)
            elif isinstance(current, (list, tuple)):
                pending.extend(current)
        return tuple(sorted(found, key=str))


class CogneeProvider:
    """Cognee adapter that enforces Sys4AI identity, policy, and result shapes."""

    def __init__(
        self,
        config: CogneeProviderConfig,
        *,
        runtime: CogneeRuntime | None = None,
    ) -> None:
        self._config = config
        self._runtime = runtime or LazyCogneeRuntime()
        self._initialized = False
        self._idempotency: dict[str, tuple[str, object]] = {}
        self._lock = asyncio.Lock()

    @property
    def provider_name(self) -> ProviderName:
        return ProviderName.COGNEE

    @property
    def provider_version(self) -> str:
        return COGNEE_PROVIDER_VERSION

    async def initialize(
        self, request: ProviderInitializationRequest
    ) -> ProviderInitializationResult:
        self._validate_context(request.context)
        actions = (
            "verify Cognee 1.5.3",
            "disable dotenv, telemetry, tracing, remote models, and cloud fallback",
            "initialize project-isolated Cognee relational storage without exposing native handles",
        )
        if request.dry_run:
            return ProviderInitializationResult(
                provider_name=self.provider_name,
                provider_version=self.provider_version,
                project_id=self._config.project_id,
                dataset_id=self._config.dataset_id,
                initialized=self._initialized,
                dry_run=True,
                planned_actions=actions,
                trace_id=request.context.trace_id,
            )
        require_authorization(
            request.authorization,
            operation=ProviderMutation.INITIALIZE,
            context=request.context,
        )
        if not (
            request.path_boundaries_validated
            and request.exclusions_validated
            and request.discovery_dry_run_approved
        ):
            raise provider_error(
                ErrorCategory.SCHEMA_INVALID,
                trace_id=request.context.trace_id,
                message="Cognee initialization prerequisites are incomplete.",
                recoverable=False,
                remediation_hint="Validate paths, exclusions, and the discovery dry run first.",
            )
        self._verify_version(request.context.trace_id)
        await self._invoke(
            "initialize",
            request.context.trace_id,
            self._runtime.configure(self._config),
        )
        self._initialized = True
        return ProviderInitializationResult(
            provider_name=self.provider_name,
            provider_version=self.provider_version,
            project_id=self._config.project_id,
            dataset_id=self._config.dataset_id,
            initialized=True,
            dry_run=False,
            planned_actions=actions,
            trace_id=request.context.trace_id,
        )

    async def capabilities(self, context: ProviderContext) -> ProviderCapabilities:
        self._validate_context(context)
        self._verify_version(context.trace_id)
        enabled: list[CapabilityName] = [CapabilityName.SERVICE_HEALTH]
        disabled: dict[CapabilityName, str] = {}
        for capability in _SUPPORTED_CAPABILITIES:
            if capability is CapabilityName.SERVICE_HEALTH:
                continue
            if not self._initialized:
                disabled[capability] = "provider_not_initialized"
            elif capability in _SEMANTIC_CAPABILITIES and not self._config.semantic_enabled:
                disabled[capability] = "local_model_profile_not_approved"
            elif capability is CapabilityName.IMPROVEMENT and not self._config.allow_improve:
                disabled[capability] = "improvement_policy_disabled"
            elif capability is CapabilityName.LIFECYCLE and not self._config.allow_forget:
                disabled[capability] = "forget_policy_disabled"
            else:
                enabled.append(capability)
        return ProviderCapabilities(
            provider_name=self.provider_name,
            provider_version=self.provider_version,
            project_id=self._config.project_id,
            dataset_id=self._config.dataset_id,
            supported=_SUPPORTED_CAPABILITIES,
            enabled=tuple(enabled),
            disabled_reasons=disabled,
        )

    async def remember(self, request: RememberRequest) -> RememberResult:
        self._before_mutation(request.context, request.authorization, ProviderMutation.REMEMBER)
        self._require_semantic(request.context.trace_id)
        fingerprint = stable_digest(
            {
                "records": [record.to_json_dict() for record in request.records],
                "relations": [relation.to_json_dict() for relation in request.relations],
                "project": request.context.project_id,
                "dataset": request.context.dataset_id,
            }
        )
        async with self._lock:
            replay = self._replay(request.idempotency_key, fingerprint, RememberResult)
            if replay is not None:
                return replay.model_copy(
                    update={
                        "request_id": request.request_id,
                        "trace_id": request.context.trace_id,
                        "idempotent_replay": True,
                    }
                )
            items: list[CogneeMappedItem] = []
            skipped: list[str] = []
            mapped_record_ids: list[str] = []
            for record in request.records:
                mapped = self._map_record(record, request.context.trace_id)
                if mapped is None:
                    skipped.append(record.record_id)
                else:
                    items.append(mapped)
                    mapped_record_ids.append(record.record_id)
            items.extend(self._map_relation(relation) for relation in request.relations)
            if items:
                raw = await self._invoke(
                    "remember",
                    request.context.trace_id,
                    self._runtime.remember(tuple(items), self._config),
                )
                if self._result_failed(raw):
                    raise provider_error(
                        ErrorCategory.INGESTION_FAILED,
                        trace_id=request.context.trace_id,
                        message="Cognee reported an unsuccessful remember operation.",
                        recoverable=True,
                        remediation_hint="Inspect sanitized provider diagnostics before retrying.",
                    )
            result = RememberResult(
                provider_name=self.provider_name,
                provider_version=self.provider_version,
                request_id=request.request_id,
                project_id=self._config.project_id,
                dataset_id=self._config.dataset_id,
                record_ids=tuple(mapped_record_ids),
                relation_ids=tuple(relation.relation_id for relation in request.relations),
                source_ids=tuple(source.source_id for source in request.sources),
                skipped_record_ids=tuple(skipped),
                idempotent_replay=False,
                trace_id=request.context.trace_id,
            )
            self._idempotency[request.idempotency_key] = (fingerprint, result)
            return result

    async def recall(self, request: RecallRequest) -> ProviderRecallResult:
        self._validate_context(request.context)
        self._require_initialized(request.context.trace_id)
        self._require_semantic(request.context.trace_id)
        if request.mode is RetrievalMode.EXACT:
            raise provider_error(
                ErrorCategory.PROVIDER_UNSUPPORTED,
                trace_id=request.context.trace_id,
                message="Exact recall is served by the independent deterministic index.",
                recoverable=False,
                remediation_hint="Route exact mode to the Sys4AI exact retrieval channel.",
            )
        raw = await self._invoke(
            "recall",
            request.context.trace_id,
            self._runtime.recall(request, self._config),
        )
        return self._normalize_recall(raw, request)

    async def improve(self, request: ImproveRequest) -> ImproveResult:
        self._before_mutation(request.context, request.authorization, ProviderMutation.IMPROVE)
        self._require_semantic(request.context.trace_id)
        if not self._config.allow_improve:
            self._unsupported("improve", request.context.trace_id)
        fingerprint = stable_digest(
            {
                "records": sorted(request.record_ids),
                "profiles": sorted(request.profile_ids),
                "project": request.context.project_id,
            }
        )
        async with self._lock:
            replay = self._replay(request.idempotency_key, fingerprint, ImproveResult)
            if replay is not None:
                return replay.model_copy(
                    update={
                        "request_id": request.request_id,
                        "trace_id": request.context.trace_id,
                        "idempotent_replay": True,
                    }
                )
            await self._invoke(
                "improve",
                request.context.trace_id,
                self._runtime.improve(request, self._config),
            )
            result = ImproveResult(
                provider_name=self.provider_name,
                provider_version=self.provider_version,
                request_id=request.request_id,
                project_id=self._config.project_id,
                dataset_id=self._config.dataset_id,
                processed_record_ids=tuple(sorted(request.record_ids)),
                changed_record_ids=(),
                idempotent_replay=False,
                trace_id=request.context.trace_id,
            )
            self._idempotency[request.idempotency_key] = (fingerprint, result)
            return result

    async def forget(self, request: ForgetRequest) -> ForgetResult:
        self._before_mutation(request.context, request.authorization, ProviderMutation.FORGET)
        if not self._config.allow_forget:
            self._unsupported("forget", request.context.trace_id)
        if request.action not in {ForgetAction.DELETE_DERIVED, ForgetAction.PRIVACY_ERASE}:
            self._unsupported("provider-native lifecycle mutation", request.context.trace_id)
        fingerprint = stable_digest(
            {
                "action": request.action,
                "record_ids": sorted(request.record_ids),
                "source_ids": sorted(request.source_ids),
                "project": request.context.project_id,
                "dataset": request.context.dataset_id,
            }
        )
        affected = tuple(sorted(set(request.record_ids)))
        impact = stable_digest({"fingerprint": fingerprint, "affected_record_ids": affected})
        async with self._lock:
            replay = self._replay(request.idempotency_key, fingerprint, ForgetResult)
            if replay is not None:
                return replay.model_copy(
                    update={
                        "request_id": request.request_id,
                        "trace_id": request.context.trace_id,
                        "idempotent_replay": True,
                    }
                )
            if request.execute:
                self._require_preview(
                    request.preview_digest, impact, "forget", request.context.trace_id
                )
                require_authorization(
                    request.authorization,
                    operation=ProviderMutation.FORGET,
                    context=request.context,
                    impact_digest=impact,
                )
                data_ids = tuple(
                    self._cognee_uuid(record_id, request.context.project_id)
                    for record_id in affected
                )
                await self._invoke(
                    "forget",
                    request.context.trace_id,
                    self._runtime.forget(data_ids, request, self._config),
                )
            result = ForgetResult(
                provider_name=self.provider_name,
                provider_version=self.provider_version,
                request_id=request.request_id,
                project_id=self._config.project_id,
                dataset_id=self._config.dataset_id,
                action=request.action,
                executed=request.execute,
                impact_digest=impact,
                affected_record_ids=affected,
                affected_relation_ids=(),
                idempotent_replay=False,
                trace_id=request.context.trace_id,
            )
            if request.execute:
                self._idempotency[request.idempotency_key] = (fingerprint, result)
            return result

    async def health(self, request: HealthRequest) -> ProviderHealth:
        self._validate_context(request.context)
        try:
            installed = self._runtime.installed_version()
        except importlib.metadata.PackageNotFoundError:
            installed = "not-installed"
        if installed != COGNEE_PROVIDER_VERSION:
            state = ProviderHealthState.UNAVAILABLE
            detail = "cognee_version_unavailable_or_incompatible"
        elif request.probe is ProviderHealthProbe.LIVENESS:
            state = ProviderHealthState.ALIVE
            detail = "cognee_distribution_pinned"
        elif self._initialized:
            state = ProviderHealthState.DEGRADED
            detail = "writeful_cognee_readiness_probe_disabled"
        else:
            state = ProviderHealthState.DEGRADED
            detail = "provider_not_initialized"
        return ProviderHealth(
            provider_name=self.provider_name,
            provider_version=self.provider_version,
            project_id=self._config.project_id,
            dataset_id=self._config.dataset_id,
            probe=request.probe,
            state=state,
            checked_at=utc_now(),
            initialized=self._initialized,
            components=(
                ProviderHealthComponent(name="cognee_runtime", state=state, detail_code=detail),
            ),
            trace_id=request.context.trace_id,
        )

    async def export(self, request: ExportRequest) -> ExportResult:
        self._before_mutation(request.context, request.authorization, ProviderMutation.EXPORT)
        if request.format is not ProviderExportFormat.COGX or not self._config.allow_native_export:
            self._unsupported("Cognee native export", request.context.trace_id)
        assert request.destination is not None
        self._validate_derived_path(request.destination, request.context.trace_id)
        fingerprint = stable_digest(
            {
                "project": request.context.project_id,
                "dataset": request.context.dataset_id,
                "format": request.format,
                "destination": request.destination,
            }
        )
        async with self._lock:
            replay = self._replay(request.idempotency_key, fingerprint, ExportResult)
            if replay is not None:
                return replay.model_copy(
                    update={
                        "request_id": request.request_id,
                        "trace_id": request.context.trace_id,
                        "idempotent_replay": True,
                    }
                )
            raw = await self._invoke(
                "export",
                request.context.trace_id,
                self._runtime.export(request, self._config),
            )
            plain = self._plain_root(raw)
            record_count = self._safe_count(plain, "num_nodes")
            relation_count = self._safe_count(plain, "num_edges")
            result = ExportResult(
                provider_name=self.provider_name,
                provider_version=self.provider_version,
                request_id=request.request_id,
                project_id=self._config.project_id,
                dataset_id=self._config.dataset_id,
                format=request.format,
                destination=request.destination,
                record_count=record_count,
                relation_count=relation_count,
                idempotent_replay=False,
                trace_id=request.context.trace_id,
            )
            self._idempotency[request.idempotency_key] = (fingerprint, result)
            return result

    async def import_snapshot(self, request: ImportRequest) -> ImportResult:
        self._before_mutation(request.context, request.authorization, ProviderMutation.IMPORT)
        if request.format is ProviderExportFormat.SYS4AI:
            return await self._import_provider_neutral_snapshot(request)
        if request.format is not ProviderExportFormat.COGX or not self._config.allow_native_import:
            self._unsupported("Cognee native import", request.context.trace_id)
        assert request.source is not None
        assert request.source_checksum is not None
        self._validate_derived_path(request.source, request.context.trace_id)
        fingerprint = stable_digest(
            {
                "project": request.context.project_id,
                "dataset": request.context.dataset_id,
                "source_checksum": request.source_checksum,
                "replace": request.replace_existing,
            }
        )
        impact = stable_digest({"fingerprint": fingerprint, "source": request.source})
        async with self._lock:
            replay = self._replay(request.idempotency_key, fingerprint, ImportResult)
            if replay is not None:
                return replay.model_copy(
                    update={
                        "request_id": request.request_id,
                        "trace_id": request.context.trace_id,
                        "idempotent_replay": True,
                    }
                )
            if request.execute:
                self._require_preview(
                    request.preview_digest, impact, "import", request.context.trace_id
                )
                require_authorization(
                    request.authorization,
                    operation=ProviderMutation.IMPORT,
                    context=request.context,
                    impact_digest=impact,
                )
                await self._invoke(
                    "import",
                    request.context.trace_id,
                    self._runtime.import_snapshot(request, self._config),
                )
            result = ImportResult(
                provider_name=self.provider_name,
                provider_version=self.provider_version,
                request_id=request.request_id,
                project_id=self._config.project_id,
                dataset_id=self._config.dataset_id,
                format=request.format,
                executed=request.execute,
                impact_digest=impact,
                imported_record_ids=(),
                imported_relation_ids=(),
                idempotent_replay=False,
                trace_id=request.context.trace_id,
            )
            if request.execute:
                self._idempotency[request.idempotency_key] = (fingerprint, result)
            return result

    async def _import_provider_neutral_snapshot(self, request: ImportRequest) -> ImportResult:
        self._require_semantic(request.context.trace_id)
        if request.replace_existing:
            self._unsupported("provider-neutral import replacement", request.context.trace_id)
        assert request.snapshot is not None
        snapshot = request.snapshot
        if (
            snapshot.project_id != self._config.project_id
            or snapshot.dataset_id != self._config.dataset_id
        ):
            raise provider_error(
                ErrorCategory.IMPORT_INVALID,
                trace_id=request.context.trace_id,
                message="The provider-neutral snapshot crosses the configured dataset boundary.",
                recoverable=False,
                remediation_hint="Use a clean Cognee stage configured for the snapshot scope.",
            )
        mapped_records = tuple(
            self._map_record(record, request.context.trace_id) for record in snapshot.records
        )
        if any(item is None for item in mapped_records):
            raise provider_error(
                ErrorCategory.IMPORT_INVALID,
                trace_id=request.context.trace_id,
                message="A provider-neutral record has no eligible semantic representation.",
                recoverable=False,
                remediation_hint="Correct the profile or record before creating a new package.",
            )
        items = tuple(item for item in mapped_records if item is not None) + tuple(
            self._map_relation(relation) for relation in snapshot.relations
        )
        fingerprint = stable_digest(
            {
                "project": request.context.project_id,
                "dataset": request.context.dataset_id,
                "snapshot": snapshot.checksums.package_sha256,
                "replace": False,
            }
        )
        impact = stable_digest(
            {
                "fingerprint": fingerprint,
                "record_ids": [record.record_id for record in snapshot.records],
                "relation_ids": [relation.relation_id for relation in snapshot.relations],
            }
        )
        async with self._lock:
            replay = self._replay(request.idempotency_key, fingerprint, ImportResult)
            if replay is not None:
                return replay.model_copy(
                    update={
                        "request_id": request.request_id,
                        "trace_id": request.context.trace_id,
                        "idempotent_replay": True,
                    }
                )
            if request.execute:
                self._require_preview(
                    request.preview_digest,
                    impact,
                    "provider-neutral import",
                    request.context.trace_id,
                )
                require_authorization(
                    request.authorization,
                    operation=ProviderMutation.IMPORT,
                    context=request.context,
                    impact_digest=impact,
                )
                if items:
                    raw = await self._invoke(
                        "import",
                        request.context.trace_id,
                        self._runtime.remember(items, self._config),
                    )
                    if self._result_failed(raw):
                        raise provider_error(
                            ErrorCategory.IMPORT_INVALID,
                            trace_id=request.context.trace_id,
                            message="Cognee rejected the provider-neutral import.",
                            recoverable=True,
                            remediation_hint=(
                                "Inspect sanitized provider diagnostics before retrying."
                            ),
                        )
            result = ImportResult(
                provider_name=self.provider_name,
                provider_version=self.provider_version,
                request_id=request.request_id,
                project_id=self._config.project_id,
                dataset_id=self._config.dataset_id,
                format=ProviderExportFormat.SYS4AI,
                executed=request.execute,
                impact_digest=impact,
                imported_record_ids=tuple(record.record_id for record in snapshot.records),
                imported_relation_ids=tuple(
                    relation.relation_id for relation in snapshot.relations
                ),
                idempotent_replay=False,
                trace_id=request.context.trace_id,
            )
            if request.execute:
                self._idempotency[request.idempotency_key] = (fingerprint, result)
            return result

    async def migrate(self, request: MigrationRequest) -> MigrationResult:
        self._before_mutation(request.context, request.authorization, ProviderMutation.MIGRATE)
        if not self._config.allow_migrate:
            self._unsupported("Cognee migration", request.context.trace_id)
        fingerprint = stable_digest(
            {
                "source_version": request.source_version,
                "target_version": request.target_version,
                "project": request.context.project_id,
                "dataset": request.context.dataset_id,
            }
        )
        impact = stable_digest({"fingerprint": fingerprint, "dataset": self._config.dataset_id})
        async with self._lock:
            replay = self._replay(request.idempotency_key, fingerprint, MigrationResult)
            if replay is not None:
                return replay.model_copy(
                    update={
                        "request_id": request.request_id,
                        "trace_id": request.context.trace_id,
                        "idempotent_replay": True,
                    }
                )
            if request.execute:
                self._require_preview(
                    request.preview_digest, impact, "migration", request.context.trace_id
                )
                require_authorization(
                    request.authorization,
                    operation=ProviderMutation.MIGRATE,
                    context=request.context,
                    impact_digest=impact,
                )
                await self._invoke(
                    "migrate",
                    request.context.trace_id,
                    self._runtime.migrate(request, self._config),
                )
            result = MigrationResult(
                provider_name=self.provider_name,
                provider_version=self.provider_version,
                request_id=request.request_id,
                project_id=self._config.project_id,
                dataset_id=self._config.dataset_id,
                source_version=request.source_version,
                target_version=request.target_version,
                executed=request.execute,
                impact_digest=impact,
                transformed_record_ids=(),
                warnings=("provider_native_migration_requires_disposable_smoke_test",),
                idempotent_replay=False,
                trace_id=request.context.trace_id,
            )
            if request.execute:
                self._idempotency[request.idempotency_key] = (fingerprint, result)
            return result

    def _validate_context(self, context: ProviderContext) -> None:
        require_context(
            context,
            project_id=self._config.project_id,
            dataset_id=self._config.dataset_id,
        )

    def _verify_version(self, trace_id: str) -> None:
        try:
            version = self._runtime.installed_version()
        except importlib.metadata.PackageNotFoundError:
            raise provider_error(
                ErrorCategory.PROVIDER_UNAVAILABLE,
                trace_id=trace_id,
                message="The pinned Cognee distribution is not installed.",
                recoverable=False,
                remediation_hint="Install the locked Cognee 1.5.3 project extra.",
            ) from None
        if version != COGNEE_PROVIDER_VERSION:
            raise provider_error(
                ErrorCategory.PROVIDER_UNSUPPORTED,
                trace_id=trace_id,
                message="The installed Cognee version does not match the pinned adapter version.",
                recoverable=False,
                remediation_hint="Restore the locked Cognee 1.5.3 environment.",
            )

    def _before_mutation(
        self,
        context: ProviderContext,
        authorization: PolicyEnvelope | None,
        operation: ProviderMutation,
    ) -> None:
        self._validate_context(context)
        self._require_initialized(context.trace_id)
        require_authorization(
            authorization,
            operation=operation,
            context=context,
        )
        self._verify_version(context.trace_id)

    def _require_initialized(self, trace_id: str) -> None:
        if not self._initialized:
            raise provider_error(
                ErrorCategory.MEMORY_NOT_INITIALIZED,
                trace_id=trace_id,
                message="The Cognee adapter is not initialized.",
                recoverable=True,
                remediation_hint="Run authorized provider initialization first.",
            )

    def _require_semantic(self, trace_id: str) -> None:
        if not self._config.semantic_enabled:
            raise provider_error(
                ErrorCategory.PROVIDER_UNSUPPORTED,
                trace_id=trace_id,
                message="Cognee semantic operations are disabled by the active local profile.",
                recoverable=False,
                remediation_hint="Approve and configure explicit local LLM and embedding profiles.",
            )

    @staticmethod
    def _unsupported(operation: str, trace_id: str) -> None:
        raise provider_error(
            ErrorCategory.PROVIDER_UNSUPPORTED,
            trace_id=trace_id,
            message=f"The active Cognee profile does not enable {operation}.",
            recoverable=False,
            remediation_hint="Enable the capability only after its Sys4AI policy gate is approved.",
        )

    @staticmethod
    def _require_preview(
        supplied: str | None, expected: str, operation: str, trace_id: str
    ) -> None:
        if supplied != expected:
            raise provider_error(
                ErrorCategory.CONCURRENT_OPERATION,
                trace_id=trace_id,
                message=f"The {operation} impact set does not match its preview.",
                recoverable=True,
                remediation_hint=f"Create and authorize a new {operation} preview.",
            )

    async def _invoke(self, operation: str, trace_id: str, call: Any) -> object:
        try:
            return await call
        except MemoryProviderError:
            raise
        except Exception as error:
            raise normalize_provider_exception(
                error, trace_id=trace_id, operation=operation
            ) from None

    def _replay(self, key: str, fingerprint: str, result_type: type[_T]) -> _T | None:
        prior = self._idempotency.get(key)
        if prior is None:
            return None
        prior_fingerprint, prior_result = prior
        if prior_fingerprint != fingerprint or not isinstance(prior_result, result_type):
            trace_id = cast(str, getattr(prior_result, "trace_id", "trace_provider_conflict"))
            raise provider_error(
                ErrorCategory.CONFLICT_DETECTED,
                trace_id=trace_id,
                message="An idempotency key was reused for a different provider mutation.",
                recoverable=False,
                remediation_hint="Use one idempotency key for one logical mutation.",
            )
        return prior_result

    def _map_record(self, record: MemoryRecord, trace_id: str) -> CogneeMappedItem | None:
        if record.security.sensitivity is Sensitivity.RESTRICTED:
            raise provider_error(
                ErrorCategory.SENSITIVITY_VIOLATION,
                trace_id=trace_id,
                message="Restricted content is not eligible for Cognee embedding.",
                recoverable=False,
                remediation_hint="Use an approved isolated storage profile or omit the record.",
            )
        record_data = record.to_json_dict()
        semantic_values: list[str] = []
        for field_path in record.indexing.semantic_fields:
            if _SENSITIVE_FIELD.search(field_path):
                raise provider_error(
                    ErrorCategory.SENSITIVITY_VIOLATION,
                    trace_id=trace_id,
                    message="A sensitive field was declared for semantic embedding.",
                    recoverable=False,
                    remediation_hint="Remove credential-bearing fields from the memory profile.",
                )
            value = self._read_field(record_data, field_path)
            if value is None:
                continue
            text = value if isinstance(value, str) else json.dumps(value, sort_keys=True)
            if _SENSITIVE_CONTENT.search(text):
                raise provider_error(
                    ErrorCategory.SENSITIVITY_VIOLATION,
                    trace_id=trace_id,
                    message="Secret-like content was rejected before provider embedding.",
                    recoverable=False,
                    remediation_hint="Remove the prohibited value and run the secret scan again.",
                )
            if text.strip():
                semantic_values.append(text)
        if not semantic_values:
            return None
        exact_properties = {
            field_path: self._read_field(record_data, field_path)
            for field_path in record.indexing.exact_fields
        }
        metadata: dict[str, object] = {
            "sys4ai": {
                "kind": "record",
                "record_id": record.record_id,
                "project_id": record.project_id,
                "dataset_id": self._config.dataset_id,
                "namespace": record.namespace,
                "source_id": record.source.source_id,
                "authority_tier": record.authority.tier.value,
                "trust_class": record.authority.trust_class.value,
                "lifecycle_status": record.lifecycle.status.value,
                "valid_from": record.lifecycle.valid_from.isoformat(),
                "valid_to": (
                    record.lifecycle.valid_to.isoformat()
                    if record.lifecycle.valid_to is not None
                    else None
                ),
                "semantic_fields": list(record.indexing.semantic_fields),
                "exact_properties": exact_properties,
                "record": record_data,
            }
        }
        return CogneeMappedItem(
            data_id=self._cognee_uuid(record.record_id, record.project_id),
            text="\n\n".join(semantic_values),
            label=f"sys4ai:{record.record_type}",
            external_metadata=metadata,
        )

    def _map_relation(self, relation: RelationRecord) -> CogneeMappedItem:
        metadata: dict[str, object] = {
            "sys4ai": {
                "kind": "relation",
                "relation_id": relation.relation_id,
                "project_id": relation.project_id,
                "dataset_id": self._config.dataset_id,
                "validation_state": relation.validation.state,
                "relation": relation.to_json_dict(),
            }
        }
        return CogneeMappedItem(
            data_id=self._cognee_uuid(relation.relation_id, relation.project_id),
            text=(
                f"{relation.source_record_id} {relation.relation_type} "
                f"{relation.target_record_id}"
            ),
            label="sys4ai:Relation",
            external_metadata=metadata,
        )

    @staticmethod
    def _cognee_uuid(stable_id: str, project_id: str) -> UUID:
        return uuid5(NAMESPACE_URL, f"sys4ai:{project_id}:{stable_id}")

    @staticmethod
    def _read_field(value: Mapping[str, object], field_path: str) -> object | None:
        current: object = value
        for segment in field_path.split("."):
            if not isinstance(current, Mapping) or segment not in current:
                return None
            current = current[segment]
        return current

    def _normalize_recall(self, raw: object, request: RecallRequest) -> ProviderRecallResult:
        records: dict[str, ProviderRecallCandidate] = {}
        relations: dict[str, RelationRecord] = {}
        for item in self._top_level_items(raw):
            plain = self._plain_root(item)
            score = self._extract_score(plain)
            for metadata in self._sys4ai_metadata(plain):
                kind = metadata.get("kind")
                if kind == "record" and isinstance(metadata.get("record"), Mapping):
                    try:
                        record = MemoryRecord.model_validate(metadata["record"])
                    except ValidationError:
                        continue
                    if not self._record_visible(record, request):
                        continue
                    candidate = ProviderRecallCandidate(
                        record=record,
                        scores=self._channel_scores(request.mode, score),
                        selection_reason=(f"cognee_{request.mode.value}_match",),
                    )
                    prior = records.get(record.record_id)
                    if prior is None or prior.scores.final < candidate.scores.final:
                        records[record.record_id] = candidate
                elif kind == "relation" and isinstance(metadata.get("relation"), Mapping):
                    try:
                        relation = RelationRecord.model_validate(metadata["relation"])
                    except ValidationError:
                        continue
                    if relation.project_id == self._config.project_id:
                        relations[relation.relation_id] = relation

        candidates = sorted(
            records.values(),
            key=lambda candidate: (-candidate.scores.final, candidate.record.record_id),
        )
        omitted = max(0, len(candidates) - request.top_k)
        selected = tuple(candidates[: request.top_k])
        selected_ids = {candidate.record.record_id for candidate in selected}
        returned_relations = (
            tuple(
                relation
                for _, relation in sorted(relations.items())
                if relation.source_record_id in selected_ids
                or relation.target_record_id in selected_ids
            )
            if request.include_relations
            else ()
        )
        return ProviderRecallResult(
            provider_name=self.provider_name,
            provider_version=self.provider_version,
            request_id=request.request_id,
            project_id=self._config.project_id,
            dataset_id=self._config.dataset_id,
            query=request.query,
            mode=request.mode,
            candidates=selected,
            relations=returned_relations,
            omitted_result_count=omitted,
            trace_id=request.context.trace_id,
        )

    @staticmethod
    def _top_level_items(raw: object) -> tuple[object, ...]:
        if isinstance(raw, (list, tuple)):
            return tuple(raw)
        plain = CogneeProvider._plain_root(raw)
        for key in ("results", "items", "data"):
            value = plain.get(key)
            if isinstance(value, list):
                return tuple(value)
        return (raw,)

    @staticmethod
    def _plain_root(value: object) -> dict[str, object]:
        if isinstance(value, Mapping):
            return {str(key): item for key, item in value.items()}
        model_dump = getattr(value, "model_dump", None)
        if callable(model_dump):
            try:
                dumped = model_dump(mode="json")
            except (TypeError, ValueError):
                dumped = model_dump()
            if isinstance(dumped, Mapping):
                return {str(key): item for key, item in dumped.items()}
        return {}

    @classmethod
    def _walk_mappings(cls, value: object) -> Iterable[Mapping[str, object]]:
        pending = [value]
        visited: set[int] = set()
        while pending:
            current = pending.pop()
            identity = id(current)
            if identity in visited:
                continue
            visited.add(identity)
            if not isinstance(current, (Mapping, list, tuple)):
                current = cls._plain_root(current)
            if isinstance(current, Mapping):
                mapping = {str(key): item for key, item in current.items()}
                yield mapping
                pending.extend(mapping.values())
            elif isinstance(current, (list, tuple)):
                pending.extend(current)

    @classmethod
    def _sys4ai_metadata(cls, value: object) -> Iterable[Mapping[str, object]]:
        for mapping in cls._walk_mappings(value):
            sys4ai = mapping.get("sys4ai")
            if isinstance(sys4ai, Mapping) and sys4ai.get("kind") in {"record", "relation"}:
                yield {str(key): item for key, item in sys4ai.items()}
            if mapping.get("kind") in {"record", "relation"} and (
                "record" in mapping or "relation" in mapping
            ):
                yield mapping

    @classmethod
    def _extract_score(cls, value: object) -> float:
        for mapping in cls._walk_mappings(value):
            for key in ("score", "similarity", "similarity_score", "certainty"):
                candidate = mapping.get(key)
                if isinstance(candidate, (int, float)) and not isinstance(candidate, bool):
                    return max(0.0, min(1.0, float(candidate)))
            distance = mapping.get("distance")
            if isinstance(distance, (int, float)) and not isinstance(distance, bool):
                return 1.0 / (1.0 + max(0.0, float(distance)))
        return 0.5

    @staticmethod
    def _channel_scores(mode: RetrievalMode, score: float) -> ProviderChannelScores:
        values = {
            "lexical": 0.0,
            "semantic": 0.0,
            "graph": 0.0,
            "temporal": 0.0,
            "final": score,
        }
        if mode is RetrievalMode.HYBRID:
            values["semantic"] = score
            values["graph"] = score
        else:
            values[mode.value] = score
        return ProviderChannelScores(**values)

    @staticmethod
    def _record_visible(record: MemoryRecord, request: RecallRequest) -> bool:
        if record.project_id != request.context.project_id:
            return False
        if request.namespaces and record.namespace not in request.namespaces:
            return False
        status = record.lifecycle.status
        if status is RecordStatus.DELETED:
            return False
        if request.status_filters and status not in request.status_filters:
            return False
        if not request.status_filters and request.current_only and status not in {
            RecordStatus.ACTIVE,
            RecordStatus.APPROVED,
        }:
            return False
        if request.at_time is None:
            return True
        return record.lifecycle.valid_from <= request.at_time and (
            record.lifecycle.valid_to is None or request.at_time <= record.lifecycle.valid_to
        )

    def _validate_derived_path(self, value: str, trace_id: str) -> None:
        candidate = Path(value).expanduser()
        root = Path(self._config.derived_data_root).resolve(strict=False)
        if not candidate.is_absolute():
            candidate = root / candidate
        resolved = candidate.resolve(strict=False)
        if resolved == root or root in resolved.parents:
            return
        raise provider_error(
            ErrorCategory.PERMISSION_DENIED,
            trace_id=trace_id,
            message="The provider artifact path is outside the approved derived-data root.",
            recoverable=False,
            remediation_hint="Use a prevalidated path below the configured derived-data root.",
        )

    @staticmethod
    def _safe_count(value: Mapping[str, object], key: str) -> int:
        count = value.get(key, 0)
        return count if isinstance(count, int) and not isinstance(count, bool) and count >= 0 else 0

    @classmethod
    def _result_failed(cls, raw: object) -> bool:
        plain = cls._plain_root(raw)
        status = plain.get("status")
        return isinstance(status, str) and status.casefold() in {"error", "errored", "failed"}


__all__ = [
    "COGNEE_API_UNCERTAINTIES",
    "CogneeMappedItem",
    "CogneeProvider",
    "CogneeRuntime",
    "LazyCogneeRuntime",
]
