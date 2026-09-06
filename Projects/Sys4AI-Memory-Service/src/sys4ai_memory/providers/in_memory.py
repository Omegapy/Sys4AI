"""Deterministic in-memory provider used for conformance and isolation tests."""

from __future__ import annotations

import asyncio
import json
import re
from collections.abc import Iterable
from typing import TypeVar

from sys4ai_memory.contracts import CapabilityName, RecordStatus, RetrievalMode
from sys4ai_memory.contracts.errors import ErrorCategory
from sys4ai_memory.contracts.models import (
    LifecycleMetadata,
    MemoryRecord,
    RelationRecord,
    SourceRecord,
)
from sys4ai_memory.util.time import utc_now

from .base import require_authorization, require_context
from .contracts import (
    IN_MEMORY_PROVIDER_VERSION,
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
    InMemoryProviderConfig,
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
    ProviderSnapshot,
    RecallRequest,
    RememberRequest,
    RememberResult,
    stable_digest,
)
from .errors import provider_error

_T = TypeVar("_T")
_TOKEN = re.compile(r"[A-Za-z0-9_./:@-]+")
_TOKEN_PART = re.compile(r"[A-Za-z0-9]+")
_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_TIMESTAMP_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}[Tt]")
_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "by",
        "can",
        "does",
        "for",
        "from",
        "how",
        "in",
        "is",
        "it",
        "of",
        "on",
        "or",
        "that",
        "the",
        "this",
        "to",
        "was",
        "what",
        "when",
        "which",
        "with",
    }
)
_MIN_QUERY_TOKEN_COVERAGE = 0.6
_CURRENT_STATUSES = frozenset({RecordStatus.ACTIVE, RecordStatus.APPROVED})
_SUPPORTED_CAPABILITIES = (
    CapabilityName.SERVICE_HEALTH,
    CapabilityName.SOURCE_REGISTRY,
    CapabilityName.INGESTION,
    CapabilityName.EXACT,
    CapabilityName.LEXICAL,
    CapabilityName.SEMANTIC,
    CapabilityName.GRAPH,
    CapabilityName.TEMPORAL,
    CapabilityName.TYPED_WRITES,
    CapabilityName.LIFECYCLE,
    CapabilityName.IMPROVEMENT,
    CapabilityName.PORTABLE_EXPORT,
    CapabilityName.PORTABLE_IMPORT,
    CapabilityName.PROVENANCE_EXPLANATION,
)


class InMemoryProvider:
    """A no-I/O reference implementation of the complete provider protocol."""

    def __init__(self, config: InMemoryProviderConfig) -> None:
        self._config = config
        self._initialized = False
        self._records: dict[str, MemoryRecord] = {}
        self._search_text_by_record: dict[str, str] = {}
        self._search_tokens_by_record: dict[str, frozenset[str]] = {}
        self._relations: dict[str, RelationRecord] = {}
        self._relation_ids_by_record: dict[str, set[str]] = {}
        self._sources: dict[str, SourceRecord] = {}
        self._idempotency: dict[str, tuple[str, object]] = {}
        self._lock = asyncio.Lock()

    @property
    def provider_name(self) -> ProviderName:
        return ProviderName.IN_MEMORY

    @property
    def provider_version(self) -> str:
        return IN_MEMORY_PROVIDER_VERSION

    async def initialize(
        self, request: ProviderInitializationRequest
    ) -> ProviderInitializationResult:
        self._validate_context(request.context)
        if not request.dry_run:
            require_authorization(
                request.authorization,
                operation=ProviderMutation.INITIALIZE,
                context=request.context,
            )
            self._initialized = True
        return ProviderInitializationResult(
            provider_name=self.provider_name,
            provider_version=self.provider_version,
            project_id=self._config.project_id,
            dataset_id=self._config.dataset_id,
            initialized=self._initialized,
            dry_run=request.dry_run,
            planned_actions=("initialize volatile project-isolated memory",),
            trace_id=request.context.trace_id,
        )

    async def capabilities(self, context: ProviderContext) -> ProviderCapabilities:
        self._validate_context(context)
        enabled = _SUPPORTED_CAPABILITIES if self._initialized else (CapabilityName.SERVICE_HEALTH,)
        disabled = {
            capability: "provider_not_initialized"
            for capability in _SUPPORTED_CAPABILITIES
            if capability not in enabled
        }
        return ProviderCapabilities(
            provider_name=self.provider_name,
            provider_version=self.provider_version,
            project_id=self._config.project_id,
            dataset_id=self._config.dataset_id,
            supported=_SUPPORTED_CAPABILITIES,
            enabled=enabled,
            disabled_reasons=disabled,
        )

    async def remember(self, request: RememberRequest) -> RememberResult:
        self._before_mutation(request.context, request.authorization, ProviderMutation.REMEMBER)
        fingerprint = stable_digest(
            {
                "project_id": request.context.project_id,
                "dataset_id": request.context.dataset_id,
                "records": [record.to_json_dict() for record in request.records],
                "relations": [relation.to_json_dict() for relation in request.relations],
                "sources": [source.to_json_dict() for source in request.sources],
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

            records = dict(self._records)
            search_text_by_record = dict(self._search_text_by_record)
            search_tokens_by_record = dict(self._search_tokens_by_record)
            relations = dict(self._relations)
            relation_ids_by_record = dict(self._relation_ids_by_record)
            copied_relation_endpoints: set[str] = set()

            def mutable_relation_ids(record_id: str) -> set[str]:
                if record_id not in copied_relation_endpoints:
                    relation_ids_by_record[record_id] = set(
                        relation_ids_by_record.get(record_id, ())
                    )
                    copied_relation_endpoints.add(record_id)
                return relation_ids_by_record[record_id]

            sources = dict(self._sources)
            for record in request.records:
                existing = records.get(record.record_id)
                if (
                    existing is not None
                    and existing != record
                    and record.version <= existing.version
                ):
                    raise provider_error(
                        ErrorCategory.CONFLICT_DETECTED,
                        trace_id=request.context.trace_id,
                        message="A record ID already has a different equal or newer version.",
                        recoverable=False,
                        remediation_hint="Use a new version with explicit lifecycle linkage.",
                    )
                records[record.record_id] = record
                search_text = self._search_text(record)
                search_text_by_record[record.record_id] = search_text
                search_tokens_by_record[record.record_id] = frozenset(
                    self._tokens(search_text, case_sensitive=False)
                )
            for relation in request.relations:
                if (
                    relation.source_record_id not in records
                    or relation.target_record_id not in records
                ):
                    raise provider_error(
                        ErrorCategory.SCHEMA_INVALID,
                        trace_id=request.context.trace_id,
                        message="A relation endpoint is not present in the project dataset.",
                        recoverable=False,
                        remediation_hint=(
                            "Remember both typed endpoint records before the relation."
                        ),
                    )
                previous = relations.get(relation.relation_id)
                if previous is not None:
                    for endpoint in (
                        previous.source_record_id,
                        previous.target_record_id,
                    ):
                        mutable_relation_ids(endpoint).discard(relation.relation_id)
                relations[relation.relation_id] = relation
                for endpoint in (
                    relation.source_record_id,
                    relation.target_record_id,
                ):
                    mutable_relation_ids(endpoint).add(relation.relation_id)
            for source in request.sources:
                sources[source.source_id] = source

            self._records = records
            self._search_text_by_record = search_text_by_record
            self._search_tokens_by_record = search_tokens_by_record
            self._relations = relations
            self._relation_ids_by_record = {
                record_id: relation_ids
                for record_id, relation_ids in relation_ids_by_record.items()
                if relation_ids
            }
            self._sources = sources
            result = RememberResult(
                provider_name=self.provider_name,
                provider_version=self.provider_version,
                request_id=request.request_id,
                project_id=self._config.project_id,
                dataset_id=self._config.dataset_id,
                record_ids=tuple(record.record_id for record in request.records),
                relation_ids=tuple(relation.relation_id for relation in request.relations),
                source_ids=tuple(source.source_id for source in request.sources),
                idempotent_replay=False,
                trace_id=request.context.trace_id,
            )
            self._idempotency[request.idempotency_key] = (fingerprint, result)
            return result

    async def recall(self, request: RecallRequest) -> ProviderRecallResult:
        self._validate_context(request.context)
        self._require_initialized(request.context.trace_id)
        records_by_id = self._records
        relations_by_id = self._relations
        relation_ids_by_record = self._relation_ids_by_record
        records = tuple(
            record
            for record in records_by_id.values()
            if self._record_visible(record, request)
        )
        scored = {
            record.record_id: self._score(record, request)
            for record in records
        }
        matched = {
            record_id
            for record_id, scores in scored.items()
            if self._matches_mode(scores, request.mode)
        }

        relations: tuple[RelationRecord, ...] = ()
        if request.mode in {RetrievalMode.GRAPH, RetrievalMode.HYBRID}:
            relevant_relation_ids = {
                relation_id
                for record_id in tuple(matched)
                for relation_id in relation_ids_by_record.get(record_id, ())
            }
            relations = tuple(
                relation
                for relation_id in sorted(relevant_relation_ids)
                if (relation := relations_by_id.get(relation_id)) is not None
                and self._relation_visible(relation, request)
            )
            for relation in relations:
                if relation.source_record_id in matched:
                    matched.add(relation.target_record_id)
                if relation.target_record_id in matched:
                    matched.add(relation.source_record_id)

        relation_record_ids = {
            endpoint
            for relation in relations
            for endpoint in (relation.source_record_id, relation.target_record_id)
        }
        candidates: list[ProviderRecallCandidate] = []
        for record in records:
            if record.record_id not in matched:
                continue
            scores = scored[record.record_id]
            if record.record_id in relation_record_ids:
                graph = 1.0
                final = max(scores.final, 0.7)
                scores = scores.model_copy(update={"graph": graph, "final": final})
            reasons = self._selection_reasons(scores, request.mode)
            candidates.append(
                ProviderRecallCandidate(record=record, scores=scores, selection_reason=reasons)
            )
        candidates.sort(
            key=lambda candidate: (
                -candidate.scores.final,
                candidate.record.authority.tier.value,
                candidate.record.record_id,
            )
        )
        omitted = max(0, len(candidates) - request.top_k)
        selected = tuple(candidates[: request.top_k])
        returned_relations = relations if request.include_relations else ()
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

    async def improve(self, request: ImproveRequest) -> ImproveResult:
        self._before_mutation(request.context, request.authorization, ProviderMutation.IMPROVE)
        selected = tuple(
            sorted(
                record_id
                for record_id in (request.record_ids or tuple(self._records))
                if record_id in self._records
            )
        )
        fingerprint = stable_digest(
            {
                "records": selected,
                "profiles": request.profile_ids,
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
            result = ImproveResult(
                provider_name=self.provider_name,
                provider_version=self.provider_version,
                request_id=request.request_id,
                project_id=self._config.project_id,
                dataset_id=self._config.dataset_id,
                processed_record_ids=selected,
                changed_record_ids=(),
                idempotent_replay=False,
                trace_id=request.context.trace_id,
            )
            self._idempotency[request.idempotency_key] = (fingerprint, result)
            return result

    async def forget(self, request: ForgetRequest) -> ForgetResult:
        self._before_mutation(request.context, request.authorization, ProviderMutation.FORGET)
        fingerprint = stable_digest(
            {
                "action": request.action,
                "record_ids": sorted(request.record_ids),
                "source_ids": sorted(request.source_ids),
                "replacement_record_id": request.replacement_record_id,
                "project": request.context.project_id,
                "dataset": request.context.dataset_id,
            }
        )
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
            affected = self._affected_record_ids(request)
            affected_relations = tuple(
                sorted(
                    {
                        relation_id
                        for record_id in affected
                        for relation_id in self._relation_ids_by_record.get(record_id, ())
                    }
                )
            )
            impact = stable_digest(
                {
                    "fingerprint": fingerprint,
                    "affected_record_ids": affected,
                    "affected_relation_ids": affected_relations,
                }
            )
            if request.execute:
                if request.preview_digest != impact:
                    raise provider_error(
                        ErrorCategory.CONCURRENT_OPERATION,
                        trace_id=request.context.trace_id,
                        message="The forget impact set changed after its preview.",
                        recoverable=True,
                        remediation_hint="Create and authorize a new forget preview.",
                    )
                require_authorization(
                    request.authorization,
                    operation=ProviderMutation.FORGET,
                    context=request.context,
                    impact_digest=impact,
                )
                self._execute_forget(request, affected, affected_relations)
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
                affected_relation_ids=affected_relations,
                idempotent_replay=False,
                trace_id=request.context.trace_id,
            )
            if request.execute:
                self._idempotency[request.idempotency_key] = (fingerprint, result)
            return result

    async def health(self, request: HealthRequest) -> ProviderHealth:
        self._validate_context(request.context)
        if request.probe is ProviderHealthProbe.LIVENESS:
            state = ProviderHealthState.ALIVE
            code = "in_memory_process_alive"
        elif self._initialized:
            state = ProviderHealthState.READY
            code = "in_memory_provider_ready"
        else:
            state = ProviderHealthState.DEGRADED
            code = "provider_not_initialized"
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
                ProviderHealthComponent(name="runtime", state=state, detail_code=code),
            ),
            trace_id=request.context.trace_id,
        )

    async def export(self, request: ExportRequest) -> ExportResult:
        self._before_mutation(request.context, request.authorization, ProviderMutation.EXPORT)
        if request.format is not ProviderExportFormat.SYS4AI:
            raise provider_error(
                ErrorCategory.PROVIDER_UNSUPPORTED,
                trace_id=request.context.trace_id,
                message="The in-memory provider supports only provider-neutral export.",
                recoverable=False,
                remediation_hint="Request the Sys4AI snapshot format.",
            )
        fingerprint = stable_digest(
            {
                "project": request.context.project_id,
                "dataset": request.context.dataset_id,
                "format": request.format,
                "profiles": request.profile_versions,
                "record_ids": sorted(self._records),
                "relation_ids": sorted(self._relations),
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
            snapshot = ProviderSnapshot.build(
                project_id=self._config.project_id,
                dataset_id=self._config.dataset_id,
                created_at=utc_now(),
                origin_provider=self.provider_name,
                origin_provider_version=self.provider_version,
                profile_versions=dict(request.profile_versions),
                sources=tuple(source for _, source in sorted(self._sources.items())),
                records=tuple(self._records[key] for key in sorted(self._records)),
                relations=tuple(self._relations[key] for key in sorted(self._relations)),
            )
            result = ExportResult(
                provider_name=self.provider_name,
                provider_version=self.provider_version,
                request_id=request.request_id,
                project_id=self._config.project_id,
                dataset_id=self._config.dataset_id,
                format=request.format,
                snapshot=snapshot,
                checksum=snapshot.checksums.package_sha256,
                record_count=len(snapshot.records),
                relation_count=len(snapshot.relations),
                idempotent_replay=False,
                trace_id=request.context.trace_id,
            )
            self._idempotency[request.idempotency_key] = (fingerprint, result)
            return result

    async def import_snapshot(self, request: ImportRequest) -> ImportResult:
        self._before_mutation(request.context, request.authorization, ProviderMutation.IMPORT)
        if request.format is not ProviderExportFormat.SYS4AI or request.snapshot is None:
            raise provider_error(
                ErrorCategory.PROVIDER_UNSUPPORTED,
                trace_id=request.context.trace_id,
                message="The in-memory provider imports only provider-neutral snapshots.",
                recoverable=False,
                remediation_hint="Provide a validated Sys4AI snapshot.",
            )
        snapshot = request.snapshot
        if (
            snapshot.project_id != self._config.project_id
            or snapshot.dataset_id != self._config.dataset_id
        ):
            raise provider_error(
                ErrorCategory.IMPORT_INVALID,
                trace_id=request.context.trace_id,
                message="The snapshot is outside the configured project and dataset boundary.",
                recoverable=False,
                remediation_hint="Import into the provider configured for the snapshot scope.",
            )
        fingerprint = stable_digest(
            {
                "snapshot": snapshot.checksums.package_sha256,
                "replace": request.replace_existing,
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
                if request.preview_digest != impact:
                    raise provider_error(
                        ErrorCategory.CONCURRENT_OPERATION,
                        trace_id=request.context.trace_id,
                        message="The import impact set does not match its preview.",
                        recoverable=True,
                        remediation_hint="Create and authorize a new import preview.",
                    )
                require_authorization(
                    request.authorization,
                    operation=ProviderMutation.IMPORT,
                    context=request.context,
                    impact_digest=impact,
                )
                if self._records and not request.replace_existing:
                    raise provider_error(
                        ErrorCategory.CONFLICT_DETECTED,
                        trace_id=request.context.trace_id,
                        message="Import would replace an existing derived provider generation.",
                        recoverable=False,
                        remediation_hint="Request replacement only after a rollback-safe preview.",
                    )
                self._records = {record.record_id: record for record in snapshot.records}
                self._search_text_by_record = {
                    record.record_id: self._search_text(record)
                    for record in snapshot.records
                }
                self._search_tokens_by_record = {
                    record_id: frozenset(self._tokens(text, case_sensitive=False))
                    for record_id, text in self._search_text_by_record.items()
                }
                self._relations = {
                    relation.relation_id: relation for relation in snapshot.relations
                }
                self._relation_ids_by_record = self._build_relation_index(
                    snapshot.relations
                )
                self._sources = {source.source_id: source for source in snapshot.sources}
            result = ImportResult(
                provider_name=self.provider_name,
                provider_version=self.provider_version,
                request_id=request.request_id,
                project_id=self._config.project_id,
                dataset_id=self._config.dataset_id,
                format=request.format,
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
        fingerprint = stable_digest(
            {
                "source_version": request.source_version,
                "target_version": request.target_version,
                "records": sorted(self._records),
            }
        )
        impact = stable_digest({"fingerprint": fingerprint, "record_ids": sorted(self._records)})
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
            warnings: tuple[str, ...]
            transformed: tuple[str, ...]
            if request.source_version == request.target_version:
                warnings = ("no_version_change",)
                transformed = ()
            else:
                warnings = ("in_memory_provider_has_no_version_transform",)
                transformed = tuple(sorted(self._records))
            if request.execute:
                if request.preview_digest != impact:
                    raise provider_error(
                        ErrorCategory.CONCURRENT_OPERATION,
                        trace_id=request.context.trace_id,
                        message="The migration impact set does not match its preview.",
                        recoverable=True,
                        remediation_hint="Create and authorize a new migration preview.",
                    )
                require_authorization(
                    request.authorization,
                    operation=ProviderMutation.MIGRATE,
                    context=request.context,
                    impact_digest=impact,
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
                transformed_record_ids=transformed if request.execute else (),
                warnings=warnings,
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

    def _require_initialized(self, trace_id: str) -> None:
        if not self._initialized:
            raise provider_error(
                ErrorCategory.MEMORY_NOT_INITIALIZED,
                trace_id=trace_id,
                message="The memory provider is not initialized.",
                recoverable=True,
                remediation_hint=(
                    "Initialize the authorized project provider before this operation."
                ),
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

    def _replay(self, key: str, fingerprint: str, result_type: type[_T]) -> _T | None:
        prior = self._idempotency.get(key)
        if prior is None:
            return None
        prior_fingerprint, prior_result = prior
        if prior_fingerprint != fingerprint:
            trace_id = getattr(prior_result, "trace_id", "trace_provider_conflict")
            raise provider_error(
                ErrorCategory.CONFLICT_DETECTED,
                trace_id=trace_id,
                message="An idempotency key was reused for a different provider mutation.",
                recoverable=False,
                remediation_hint="Reuse a key only for the exact same logical request.",
            )
        if not isinstance(prior_result, result_type):
            trace_id = getattr(prior_result, "trace_id", "trace_provider_conflict")
            raise provider_error(
                ErrorCategory.CONFLICT_DETECTED,
                trace_id=trace_id,
                message="An idempotency key was reused for a different provider operation.",
                recoverable=False,
                remediation_hint="Use a distinct key for each logical mutation.",
            )
        return prior_result

    def _record_visible(self, record: MemoryRecord, request: RecallRequest) -> bool:
        if request.namespaces and record.namespace not in request.namespaces:
            return False
        status = record.lifecycle.status
        if request.status_filters and status not in request.status_filters:
            return False
        if not request.status_filters and request.current_only and status not in _CURRENT_STATUSES:
            return False
        if status is RecordStatus.DELETED:
            return False
        at_time = request.at_time
        if at_time is None:
            return True
        lifecycle = record.lifecycle
        return lifecycle.valid_from <= at_time and (
            lifecycle.valid_to is None or at_time <= lifecycle.valid_to
        )

    def _relation_visible(self, relation: RelationRecord, request: RecallRequest) -> bool:
        if request.relation_types and relation.relation_type not in request.relation_types:
            return False
        if relation.lifecycle.status is RecordStatus.DELETED:
            return False
        if request.current_only and relation.lifecycle.status not in _CURRENT_STATUSES:
            return False
        at_time = request.at_time
        if at_time is None:
            return True
        return relation.temporal.valid_from <= at_time and (
            relation.temporal.valid_to is None or at_time <= relation.temporal.valid_to
        )

    @staticmethod
    def _tokens(value: str, *, case_sensitive: bool) -> set[str]:
        text = value if case_sensitive else value.casefold()
        tokens: set[str] = set()
        for raw in _TOKEN.findall(text):
            if not any(character.isalnum() for character in raw):
                continue
            if _TIMESTAMP_DATE.match(raw):
                tokens.add(raw[:10])
                continue
            if _DATE.match(raw):
                tokens.add(raw)
                continue
            parts = _TOKEN_PART.findall(raw)
            if len(parts) > 1 and raw not in _STOPWORDS:
                tokens.add(raw)
            for part in parts:
                if part in _STOPWORDS or len(part) <= 1:
                    continue
                tokens.update(InMemoryProvider._token_variants(part))
        return tokens

    @staticmethod
    def _token_variants(token: str) -> set[str]:
        """Return conservative morphology variants for deterministic conformance recall."""

        normalized = token
        if len(token) > 5 and token.endswith("ing"):
            normalized = token[:-3]
        elif len(token) > 4 and token.endswith("ed"):
            normalized = token[:-2]
        elif len(token) > 4 and token.endswith("e"):
            normalized = token[:-1]
        return {normalized}

    def _score(self, record: MemoryRecord, request: RecallRequest) -> ProviderChannelScores:
        content = self._search_text_by_record.get(record.record_id)
        if content is None:
            content = self._search_text(record)
        query = request.query if request.case_sensitive else request.query.casefold()
        comparable = content if request.case_sensitive else content.casefold()
        exact = 1.0 if query in comparable else 0.0
        query_tokens = self._tokens(request.query, case_sensitive=request.case_sensitive)
        content_tokens: set[str] | frozenset[str]
        if request.case_sensitive:
            content_tokens = self._tokens(content, case_sensitive=True)
        else:
            cached_tokens = self._search_tokens_by_record.get(record.record_id)
            content_tokens = (
                cached_tokens
                if cached_tokens is not None
                else self._tokens(content, case_sensitive=False)
            )
        overlap = query_tokens & content_tokens
        coverage = len(overlap) / len(query_tokens) if query_tokens else 0.0
        qualified = exact > 0.0 or coverage >= _MIN_QUERY_TOKEN_COVERAGE
        lexical = coverage if qualified else 0.0
        union = query_tokens | content_tokens
        semantic = len(overlap) / len(union) if union and qualified else 0.0
        temporal = 1.0 if self._record_visible(record, request) else 0.0
        weights = {
            RetrievalMode.EXACT: exact,
            RetrievalMode.LEXICAL: lexical,
            RetrievalMode.SEMANTIC: semantic,
            RetrievalMode.GRAPH: max(lexical, semantic),
            RetrievalMode.TEMPORAL: max(exact, lexical, semantic) * temporal,
            RetrievalMode.HYBRID: max(exact, lexical, semantic),
        }
        return ProviderChannelScores(
            exact=exact,
            lexical=lexical,
            semantic=semantic,
            temporal=temporal,
            final=min(1.0, weights[request.mode]),
        )

    @staticmethod
    def _search_text(record: MemoryRecord) -> str:
        return "\n".join(
            (
                record.record_id,
                record.title,
                record.content.exact,
                record.content.summary or "",
                json.dumps(record.content.structured, ensure_ascii=False, sort_keys=True),
            )
        )

    @staticmethod
    def _matches_mode(scores: ProviderChannelScores, mode: RetrievalMode) -> bool:
        score = {
            RetrievalMode.EXACT: scores.exact,
            RetrievalMode.LEXICAL: scores.lexical,
            RetrievalMode.SEMANTIC: scores.semantic,
            RetrievalMode.GRAPH: max(scores.lexical, scores.semantic),
            RetrievalMode.TEMPORAL: scores.final,
            RetrievalMode.HYBRID: scores.final,
        }[mode]
        return score > 0.0

    @staticmethod
    def _selection_reasons(
        scores: ProviderChannelScores, mode: RetrievalMode
    ) -> tuple[str, ...]:
        reasons: list[str] = []
        for label, score in (
            ("exact_match", scores.exact),
            ("lexical_match", scores.lexical),
            ("semantic_match", scores.semantic),
            ("graph_relation", scores.graph),
            ("temporal_match", scores.temporal if mode is RetrievalMode.TEMPORAL else 0.0),
        ):
            if score > 0.0:
                reasons.append(label)
        return tuple(reasons or ("provider_match",))

    def _affected_record_ids(self, request: ForgetRequest) -> tuple[str, ...]:
        selected = set(request.record_ids)
        if request.source_ids:
            selected.update(
                record.record_id
                for record in self._records.values()
                if record.source.source_id in request.source_ids
            )
        return tuple(sorted(record_id for record_id in selected if record_id in self._records))

    def _execute_forget(
        self,
        request: ForgetRequest,
        affected: tuple[str, ...],
        affected_relations: tuple[str, ...],
    ) -> None:
        if request.action in {
            ForgetAction.DELETE_DERIVED,
            ForgetAction.DELETE_SOURCE,
            ForgetAction.PRIVACY_ERASE,
        }:
            for record_id in affected:
                self._records.pop(record_id, None)
                self._search_text_by_record.pop(record_id, None)
                self._search_tokens_by_record.pop(record_id, None)
            for relation_id in affected_relations:
                relation = self._relations.pop(relation_id, None)
                if relation is None:
                    continue
                for endpoint in (
                    relation.source_record_id,
                    relation.target_record_id,
                ):
                    indexed = self._relation_ids_by_record.get(endpoint)
                    if indexed is None:
                        continue
                    indexed.discard(relation_id)
                    if not indexed:
                        self._relation_ids_by_record.pop(endpoint, None)
            if request.action is ForgetAction.DELETE_SOURCE:
                for source_id in request.source_ids:
                    self._sources.pop(source_id, None)
            return

        status = {
            ForgetAction.EXPIRE: RecordStatus.EXPIRED,
            ForgetAction.WITHDRAW: RecordStatus.WITHDRAWN,
            ForgetAction.SUPERSEDE: RecordStatus.SUPERSEDED,
        }[request.action]
        changed_at = utc_now()
        for record_id in affected:
            record = self._records[record_id]
            superseded_by = record.lifecycle.superseded_by
            if request.action is ForgetAction.SUPERSEDE:
                replacement_id = request.replacement_record_id
                if replacement_id not in self._records:
                    raise provider_error(
                        ErrorCategory.SCHEMA_INVALID,
                        trace_id=request.context.trace_id,
                        message="The superseding record is not present in the project dataset.",
                        recoverable=False,
                        remediation_hint=(
                            "Remember the replacement before superseding the old record."
                        ),
                    )
                assert replacement_id is not None
                superseded_by = tuple(dict.fromkeys((*superseded_by, replacement_id)))
            lifecycle = LifecycleMetadata(
                status=status,
                valid_from=record.lifecycle.valid_from,
                valid_to=record.lifecycle.valid_to or changed_at,
                supersedes=record.lifecycle.supersedes,
                superseded_by=superseded_by,
            )
            self._records[record_id] = MemoryRecord.model_validate(
                {**record.to_json_dict(), "lifecycle": lifecycle.to_json_dict()}
            )

        if request.action is ForgetAction.SUPERSEDE:
            replacement_id = request.replacement_record_id
            assert replacement_id is not None
            replacement_record = self._records[replacement_id]
            replacement_lifecycle = LifecycleMetadata(
                status=replacement_record.lifecycle.status,
                valid_from=replacement_record.lifecycle.valid_from,
                valid_to=replacement_record.lifecycle.valid_to,
                supersedes=tuple(
                    dict.fromkeys((*replacement_record.lifecycle.supersedes, *affected))
                ),
                superseded_by=replacement_record.lifecycle.superseded_by,
            )
            self._records[replacement_id] = MemoryRecord.model_validate(
                {
                    **replacement_record.to_json_dict(),
                    "lifecycle": replacement_lifecycle.to_json_dict(),
                }
            )

    @staticmethod
    def _build_relation_index(
        relations: Iterable[RelationRecord],
    ) -> dict[str, set[str]]:
        index: dict[str, set[str]] = {}
        for relation in relations:
            for endpoint in (
                relation.source_record_id,
                relation.target_record_id,
            ):
                index.setdefault(endpoint, set()).add(relation.relation_id)
        return index


__all__ = ["InMemoryProvider"]
