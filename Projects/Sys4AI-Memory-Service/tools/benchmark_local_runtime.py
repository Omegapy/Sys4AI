#!/usr/bin/env python3
"""Benchmark guarded local runtime paths with disposable synthetic data."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import math
import os
import platform
import resource
import sqlite3
import statistics
import sys
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter

from pydantic import JsonValue

from sys4ai_memory.authorization import (
    AuthorizationService,
    CanonicalPermissionEnvelopeLoader,
)
from sys4ai_memory.configuration import LoadedConfiguration, load_configuration
from sys4ai_memory.contracts import (
    API_VERSION,
    SCHEMA_VERSION,
    AuthorityTier,
    CoreRecordType,
    MemoryScope,
    OperationName,
    Permission,
    RecordStatus,
    RelationRecord,
    RetrievalMode,
    ScopeReference,
    Sensitivity,
    SourceRole,
    TrustClass,
)
from sys4ai_memory.contracts.models import (
    MemoryRecord,
    RelationLifecycle,
    RelationSource,
    RelationValidation,
    SourceRecord,
    TemporalMetadata,
)
from sys4ai_memory.exact_index import ExactIndex
from sys4ai_memory.ingestion import IngestionSynchronizer, normalize_bytes
from sys4ai_memory.interfaces import (
    AuditContext,
    AuthorizationContext,
    DispatchRequest,
    DispatchSuccess,
    InterfaceIdentity,
    InterfaceKind,
)
from sys4ai_memory.observability import AuditRecorder, VersionContext
from sys4ai_memory.providers import (
    IN_MEMORY_PROVIDER_VERSION,
    InMemoryProviderConfig,
    ProviderContext,
    ProviderInitializationRequest,
    ProviderMutation,
    RememberRequest,
)
from sys4ai_memory.providers.in_memory import InMemoryProvider
from sys4ai_memory.retrieval import RetrievalEngine
from sys4ai_memory.security import InMemoryAuditSink, ProjectBoundary
from sys4ai_memory.service import (
    MemoryService,
    ProviderAuthorizationBridge,
    ServiceComponents,
)
from sys4ai_memory.sources import RegistryBundle, SourceRegistryEntry
from sys4ai_memory.util import canonical_json_bytes, sha256_bytes

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ID = "benchmark-project"
DATASET_ID = "benchmark-project"
PRINCIPAL_ID = "agent-local-benchmark"
FIXED_TIME = datetime(2026, 9, 3, tzinfo=UTC)


def _percentile(values: Sequence[float], percentile: float) -> float:
    if not values:
        raise ValueError("latency samples must not be empty")
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, math.ceil(len(ordered) * percentile) - 1))
    return ordered[index]


def _latency_summary(values: Sequence[float]) -> dict[str, JsonValue]:
    return {
        "samples": len(values),
        "p50_ms": round(statistics.median(values), 3),
        "p95_ms": round(_percentile(values, 0.95), 3),
        "max_ms": round(max(values), 3),
    }


def _replace_once(text: str, before: str, after: str) -> str:
    if text.count(before) != 1:
        raise RuntimeError(f"benchmark configuration expected one occurrence of {before!r}")
    return text.replace(before, after, 1)


def _write_benchmark_configuration(root: Path) -> Path:
    for relative in (
        "registries/memory_source_registry.csv",
        "registries/memory_profile_registry.csv",
        "registries/memory_relation_registry.csv",
        "control_records/memory/README.md",
    ):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("disposable synthetic benchmark\n", encoding="utf-8")

    text = (PROJECT_ROOT / "config/memory.toml").read_text(encoding="utf-8")
    replacements = (
        (
            'configuration_status = "approved-local-profile-inactive-provider"',
            'configuration_status = "benchmark"',
        ),
        ('project_id = "sys4ai-memory-service"', f'project_id = "{PROJECT_ID}"'),
        ('name = "cognee"', 'name = "in-memory"'),
        (
            'version_constraint = "==1.5.3"',
            f'version_constraint = "=={IN_MEMORY_PROVIDER_VERSION}"',
        ),
        ('dataset = "sys4ai-memory-service"', f'dataset = "{DATASET_ID}"'),
        ("respect_gitignore = true", "respect_gitignore = false"),
    )
    for before, after in replacements:
        text = _replace_once(text, before, after)
    path = root / "config/memory.toml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _write_permissions(root: Path) -> None:
    path = root / "control_records/memory/permissions.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "revision": "benchmark-permissions-1",
                "project_id": PROJECT_ID,
                "dataset_id": DATASET_ID,
                "issued_at": FIXED_TIME.isoformat().replace("+00:00", "Z"),
                "grants": [
                    {
                        "grant_id": "benchmark-local-runtime",
                        "principal_id": PRINCIPAL_ID,
                        "permissions": [permission.value for permission in Permission],
                        "operations": [
                            OperationName.HEALTH.value,
                            OperationName.RECALL.value,
                            OperationName.SYNC.value,
                            "memory.initialize",
                        ],
                        "scopes": [
                            {
                                "level": MemoryScope.PROJECT.value,
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


def _authorization(
    root: Path,
) -> tuple[AuthorizationService, CanonicalPermissionEnvelopeLoader]:
    loader = CanonicalPermissionEnvelopeLoader(
        ProjectBoundary(PROJECT_ID, DATASET_ID, root),
        "control_records/memory/permissions.json",
    )
    return AuthorizationService(loader), loader


def _versions(configuration: LoadedConfiguration) -> VersionContext:
    return VersionContext(
        configuration_version="1.0",
        configuration_fingerprint=configuration.fingerprint,
        profile_versions={"base": "1.0.0"},
        profile_fingerprints={"base": "b" * 64},
        provider_name="in-memory",
        provider_version=IN_MEMORY_PROVIDER_VERSION,
        provider_fingerprint="c" * 64,
        source_registry_fingerprint="d" * 64,
    )


def _provider_context(trace_id: str) -> ProviderContext:
    return ProviderContext(
        project_id=PROJECT_ID,
        dataset_id=DATASET_ID,
        principal_id=PRINCIPAL_ID,
        scope=ScopeReference(level=MemoryScope.PROJECT, scope_id=PROJECT_ID),
        trace_id=trace_id,
    )


def _identity() -> InterfaceIdentity:
    return InterfaceIdentity(
        principal_id=PRINCIPAL_ID,
        agent_type="benchmark-agent",
        run_id="run-local-runtime-benchmark",
    )


def _request(
    operation: OperationName,
    payload: Mapping[str, JsonValue],
    *,
    suffix: str,
    idempotency_key: str | None = None,
) -> DispatchRequest:
    return DispatchRequest(
        operation=operation,
        request_id=f"mrq_benchmark_{suffix}",
        trace_id=f"trace_benchmark_{suffix}",
        authorization=AuthorizationContext(
            identity=_identity(),
            project_id=PROJECT_ID,
            dataset_id=DATASET_ID,
            scope=ScopeReference(level=MemoryScope.PROJECT, scope_id=PROJECT_ID),
            query_project_ids=(PROJECT_ID,),
        ),
        audit=AuditContext(
            interface=InterfaceKind.PYTHON,
            client_id="local-runtime-benchmark",
            purpose="measure disposable guarded local runtime paths",
        ),
        idempotency_key=idempotency_key,
        payload=dict(payload),
    )


def _source(batch: int, raw: bytes) -> SourceRecord:
    path = f"benchmark/corpus-{batch:04d}.jsonl"
    return SourceRecord(
        schema_version=SCHEMA_VERSION,
        api_version=API_VERSION,
        source_id=f"src_RUNTIME{batch:04d}",
        project_id=PROJECT_ID,
        path_or_uri=path,
        path_pattern=None,
        source_kind="generated",
        format="jsonl",
        canonicality="evidential",
        content_role=SourceRole.EVIDENTIAL,
        authority_tier=AuthorityTier.AGENT_DURABLE_MATERIAL,
        trust_class=TrustClass.PROJECT_AUTHORED,
        sensitivity=Sensitivity.INTERNAL,
        namespace="benchmark/runtime",
        scope=ScopeReference(level=MemoryScope.PROJECT, scope_id=PROJECT_ID),
        profile_id="base@1",
        ingestion_adapter="jsonl",
        chunking_profile="row@1",
        schema_ref=None,
        refresh_mode="disposable-benchmark",
        retention_policy="disposable-benchmark",
        owner="benchmark",
        write_policy="deny",
        include_flag=True,
        notes="Synthetic non-sensitive local runtime benchmark source",
        content_sha256=hashlib.sha256(raw).hexdigest(),
        locator={"path": path, "label": f"runtime benchmark batch {batch}"},
        git_commit=None,
        git_blob_sha=None,
        working_tree_state="disposable-benchmark",
        origin_uri=None,
        retrieved_at=None,
        licensing_metadata={},
        access_metadata={},
        generated_from=("src_RUNTIME_RECIPE",),
    )


def _batch_bytes(start: int, count: int) -> bytes:
    return b"".join(
        (
            json.dumps(
                {
                    "event_id": f"RUNTIME-ID-{number:06d}",
                    "text": (
                        f"Synthetic runtime record RUNTIME-ID-{number:06d} "
                        f"topic group {number % 100}."
                    ),
                },
                separators=(",", ":"),
                sort_keys=True,
            )
            + "\n"
        ).encode("utf-8")
        for number in range(start, start + count)
    )


def _initialize_provider(
    provider: InMemoryProvider,
    bridge: ProviderAuthorizationBridge,
    configuration: LoadedConfiguration,
) -> None:
    context = _provider_context("trace_benchmark_provider_initialize")
    authorization = bridge.authorize(context, ProviderMutation.INITIALIZE)
    result = asyncio.run(
        provider.initialize(
            ProviderInitializationRequest(
                context=context,
                configuration_fingerprint=configuration.fingerprint,
                dry_run=False,
                path_boundaries_validated=True,
                exclusions_validated=True,
                discovery_dry_run_approved=True,
                authorization=authorization,
            )
        )
    )
    if not result.initialized:
        raise RuntimeError("in-memory benchmark provider did not initialize")


def _build_corpus(
    *,
    index: ExactIndex,
    provider: InMemoryProvider,
    bridge: ProviderAuthorizationBridge,
    fragments: int,
    batch_size: int,
) -> tuple[float, int, tuple[str, ...], tuple[MemoryRecord, ...]]:
    started = perf_counter()
    source_count = 0
    fragment_record_ids: list[str] = []
    endpoint_records: list[MemoryRecord] = []
    for batch_start in range(0, fragments, batch_size):
        count = min(batch_size, fragments - batch_start)
        raw = _batch_bytes(batch_start, count)
        document = normalize_bytes(_source(source_count, raw), raw, processed_at=FIXED_TIME)
        index.upsert_document(document)
        fragment_records = tuple(
            record
            for record in document.records
            if record.record_type != CoreRecordType.SOURCE_ARTIFACT.value
        )
        fragment_record_ids.extend(record.record_id for record in fragment_records)
        endpoint_records.extend(fragment_records[: max(0, 2 - len(endpoint_records))])
        context = _provider_context(f"trace_benchmark_corpus_{source_count:04d}")
        remembered = asyncio.run(
            provider.remember(
                RememberRequest(
                    context=context,
                    request_id=f"mrq_benchmark_corpus_{source_count:04d}",
                    idempotency_key=f"benchmark-corpus-{source_count:04d}",
                    records=document.records,
                    sources=(document.source,),
                    authorization=bridge.authorize(
                        context,
                        ProviderMutation.REMEMBER,
                        authorization_operation=OperationName.SYNC.value,
                    ),
                )
            )
        )
        if len(remembered.record_ids) != len(document.records):
            raise RuntimeError("in-memory provider did not retain the corpus batch")
        source_count += 1
    if len(fragment_record_ids) != fragments:
        raise RuntimeError("normalized fragment count did not match the requested corpus")
    return (
        perf_counter() - started,
        source_count,
        tuple(fragment_record_ids),
        tuple(endpoint_records),
    )


def _relation(
    number: int,
    source_record_id: str,
    target_record_id: str,
) -> RelationRecord:
    return RelationRecord(
        schema_version=SCHEMA_VERSION,
        api_version=API_VERSION,
        relation_id=f"rel_RUNTIME{number:09d}",
        project_id=PROJECT_ID,
        relation_type="REFERENCES",
        source_record_id=source_record_id,
        target_record_id=target_record_id,
        source=RelationSource(
            source_id="src_RUNTIME_RELATIONS",
            locator={"relation_number": number},
        ),
        validation=RelationValidation(state="deterministic-synthetic", confidence=None),
        temporal=TemporalMetadata(valid_from=FIXED_TIME, valid_to=None),
        lifecycle=RelationLifecycle(status=RecordStatus.ACTIVE),
    )


def _load_relations(
    *,
    provider: InMemoryProvider,
    bridge: ProviderAuthorizationBridge,
    record_ids: tuple[str, ...],
    endpoint_records: tuple[MemoryRecord, ...],
    relation_count: int,
    batch_size: int,
) -> tuple[float, list[float]]:
    total_started = perf_counter()
    latencies: list[float] = []
    for batch_start in range(0, relation_count, batch_size):
        started = perf_counter()
        count = min(batch_size, relation_count - batch_start)
        relations: list[RelationRecord] = []
        for number in range(batch_start, batch_start + count):
            source_index = number % len(record_ids)
            target_index = (number * 7919 + 1) % len(record_ids)
            if target_index == source_index:
                target_index = (target_index + 1) % len(record_ids)
            relations.append(_relation(number, record_ids[source_index], record_ids[target_index]))
        batch_number = batch_start // batch_size
        context = _provider_context(f"trace_benchmark_relations_{batch_number:04d}")
        remembered = asyncio.run(
            provider.remember(
                RememberRequest(
                    context=context,
                    request_id=f"mrq_benchmark_relations_{batch_number:04d}",
                    idempotency_key=f"benchmark-relations-{batch_number:04d}",
                    records=endpoint_records,
                    relations=tuple(relations),
                    authorization=bridge.authorize(
                        context,
                        ProviderMutation.REMEMBER,
                        authorization_operation=OperationName.SYNC.value,
                    ),
                )
            )
        )
        if len(remembered.relation_ids) != count:
            raise RuntimeError("in-memory provider did not retain the relation batch")
        latencies.append((perf_counter() - started) * 1000)
    return perf_counter() - total_started, latencies


def _service(
    configuration: LoadedConfiguration,
    authorization: AuthorizationService,
    loader: CanonicalPermissionEnvelopeLoader,
    *,
    components: ServiceComponents,
) -> MemoryService:
    return MemoryService(
        configuration=configuration,
        authorization=authorization,
        audit=AuditRecorder(InMemoryAuditSink()),
        versions=_versions(configuration),
        components=components,
        provider_authorization=ProviderAuthorizationBridge(authorization, loader),
    )


def _require_success(response: object, operation: str) -> DispatchSuccess:
    if not isinstance(response, DispatchSuccess):
        raise RuntimeError(f"{operation} benchmark request failed")
    return response


def _measure_hybrid_recall(
    service: MemoryService,
    *,
    fragments: int,
    samples: int,
    warmups: int,
) -> tuple[list[float], int]:
    sample_step = max(1, fragments // samples)
    sample_numbers = tuple(range(0, fragments, sample_step))[:samples]
    for warmup in range(warmups):
        number = sample_numbers[warmup % len(sample_numbers)]
        _require_success(
            service.dispatch(
                _request(
                    OperationName.RECALL,
                    {
                        "query": f"RUNTIME-ID-{number:06d}",
                        "mode": RetrievalMode.HYBRID.value,
                        "limit": 10,
                    },
                    suffix=f"recall_warmup_{warmup:04d}_{number:06d}",
                )
            ),
            "hybrid recall warmup",
        )

    latencies: list[float] = []
    returned_records = 0
    for sample, number in enumerate(sample_numbers):
        started = perf_counter()
        response = _require_success(
            service.dispatch(
                _request(
                    OperationName.RECALL,
                    {
                        "query": f"RUNTIME-ID-{number:06d}",
                        "mode": RetrievalMode.HYBRID.value,
                        "limit": 10,
                    },
                    suffix=f"recall_{sample:04d}_{number:06d}",
                )
            ),
            "hybrid recall",
        )
        latencies.append((perf_counter() - started) * 1000)
        retrieval = response.result.get("retrieval")
        if not isinstance(retrieval, dict) or retrieval.get("evidence_state") != "sufficient":
            raise RuntimeError("hybrid recall did not return sufficient synthetic evidence")
        results = retrieval.get("results")
        if not isinstance(results, list) or not results:
            raise RuntimeError("hybrid recall returned no synthetic records")
        returned_records += len(results)
        trace = response.result.get("trace")
        selected_channels = trace.get("selected_channels") if isinstance(trace, dict) else None
        if not isinstance(selected_channels, list) or len(selected_channels) != 5:
            raise RuntimeError("hybrid recall did not execute all five planned channels")
    return latencies, returned_records


def _sync_entry() -> SourceRegistryEntry:
    return SourceRegistryEntry(
        source_id="src_RUNTIME_SYNC",
        project_id=PROJECT_ID,
        path_or_uri="benchmark-sync.txt",
        path_pattern=None,
        source_kind="file",
        format="text",
        canonicality="evidential",
        content_role="benchmark-evidence",
        authority_tier=AuthorityTier.AGENT_DURABLE_MATERIAL,
        trust_class=TrustClass.PROJECT_AUTHORED,
        sensitivity=Sensitivity.INTERNAL,
        namespace="benchmark/runtime",
        profile_id="base@1",
        ingestion_adapter="text",
        chunking_profile="paragraph@1",
        schema_ref=None,
        refresh_mode="content-hash",
        retention_policy="disposable-benchmark",
        owner="benchmark",
        write_policy="deny",
        include_flag=True,
        notes="Synthetic small text source for incremental sync timing",
    )


def _write_sync_version(path: Path, version: int) -> int:
    content = (
        "Synthetic non-sensitive incremental synchronization benchmark.\n\n"
        f"RUNTIME-SYNC-{version:06d} is the current disposable revision.\n"
    )
    path.write_text(content, encoding="utf-8")
    return len(content.encode("utf-8"))


def _measure_incremental_sync(
    *,
    root: Path,
    configuration: LoadedConfiguration,
    authorization: AuthorizationService,
    loader: CanonicalPermissionEnvelopeLoader,
    index: ExactIndex,
    provider: InMemoryProvider,
    samples: int,
    warmups: int,
) -> tuple[list[float], int]:
    source_path = root / "benchmark-sync.txt"
    _write_sync_version(source_path, 0)
    registry = RegistryBundle(sources=(_sync_entry(),), profiles=(), relations=())
    service = _service(
        configuration,
        authorization,
        loader,
        components=ServiceComponents(
            registry_loader=lambda: registry,
            synchronizer=IngestionSynchronizer(project_root=root, index_writer=index),
            exact_index=index,
            provider=provider,
        ),
    )
    initial = _require_success(
        service.dispatch(
            _request(
                OperationName.SYNC,
                {"source_ids": [], "full": False, "dry_run": False},
                suffix="sync_initial",
                idempotency_key="benchmark-sync-initial",
            )
        ),
        "initial sync",
    )
    initial_delta = initial.result.get("delta")
    if not isinstance(initial_delta, dict) or initial_delta.get("added") != 1:
        raise RuntimeError("initial benchmark source was not classified as added")

    for version in range(1, warmups + 1):
        _write_sync_version(source_path, version)
        response = _require_success(
            service.dispatch(
                _request(
                    OperationName.SYNC,
                    {"source_ids": [], "full": False, "dry_run": False},
                    suffix=f"sync_warmup_{version:04d}",
                    idempotency_key=f"benchmark-sync-warmup-{version:04d}",
                )
            ),
            "incremental sync warmup",
        )
        delta = response.result.get("delta")
        if not isinstance(delta, dict) or delta.get("changed") != 1:
            raise RuntimeError("sync warmup did not classify one changed source")

    latencies: list[float] = []
    maximum_source_bytes = 0
    for sample in range(samples):
        version = warmups + sample + 1
        maximum_source_bytes = max(
            maximum_source_bytes,
            _write_sync_version(source_path, version),
        )
        started = perf_counter()
        response = _require_success(
            service.dispatch(
                _request(
                    OperationName.SYNC,
                    {"source_ids": [], "full": False, "dry_run": False},
                    suffix=f"sync_{sample:04d}",
                    idempotency_key=f"benchmark-sync-{sample:04d}",
                )
            ),
            "incremental sync",
        )
        latencies.append((perf_counter() - started) * 1000)
        delta = response.result.get("delta")
        if not isinstance(delta, dict) or delta.get("changed") != 1:
            raise RuntimeError("timed sync did not classify exactly one changed source")
        if response.result.get("failure_count") != 0:
            raise RuntimeError("timed sync reported a failure")
        provider_result = response.result.get("provider")
        if not isinstance(provider_result, dict) or not provider_result.get("record_ids"):
            raise RuntimeError("timed sync did not reach the in-memory provider")
        query = f"RUNTIME-SYNC-{version:06d}"
        if not index.query_exact(project_id=PROJECT_ID, query=query, case_sensitive=True):
            raise RuntimeError("timed sync did not update the exact index")
    return latencies, maximum_source_bytes


def _measure_guarded_startup(
    *,
    root: Path,
    configuration_path: Path,
    index_path: Path,
    expected_record_count: int,
    samples: int,
    warmups: int,
) -> list[float]:
    latencies: list[float] = []
    for sample in range(warmups + samples):
        started = perf_counter()
        configuration = load_configuration(configuration_path, trusted_project_root=root)
        authorization, loader = _authorization(root)
        index = ExactIndex(index_path)
        try:
            if index.health(PROJECT_ID).current_record_count < expected_record_count:
                raise RuntimeError("existing exact database lost benchmark records")
            retrieval = RetrievalEngine(
                project_id=PROJECT_ID,
                dataset_id=DATASET_ID,
                authorizer=authorization,
                exact_backend=index,
            )
            service = _service(
                configuration,
                authorization,
                loader,
                components=ServiceComponents(exact_index=index, retrieval=retrieval),
            )
            response = _require_success(
                service.dispatch(
                    _request(
                        OperationName.HEALTH,
                        {"detailed": False},
                        suffix=f"startup_{sample:04d}",
                    )
                ),
                "guarded startup health",
            )
            if response.result.get("exact_index_composed") is not True:
                raise RuntimeError("startup health did not report the exact index")
            elapsed_ms = (perf_counter() - started) * 1000
        finally:
            index.close()
        if sample >= warmups:
            latencies.append(elapsed_ms)
    return latencies


def _physical_memory_gb() -> float | None:
    try:
        pages = int(os.sysconf("SC_PHYS_PAGES"))
        page_size = int(os.sysconf("SC_PAGE_SIZE"))
    except (AttributeError, OSError, TypeError, ValueError):
        return None
    return round(pages * page_size / (1024**3), 3)


def _peak_rss_mb() -> float:
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    divisor = 1024 * 1024 if platform.system() == "Darwin" else 1024
    return round(value / divisor, 3)


def _database_bytes(path: Path) -> int:
    return sum(
        candidate.stat().st_size
        for candidate in path.parent.glob(f"{path.name}*")
        if candidate.is_file()
    )


def _validate_sizes(
    *,
    fragments: int,
    batch_size: int,
    relations: int,
    relation_batch_size: int,
    recall_samples: int,
    startup_samples: int,
    sync_samples: int,
    warmups: int,
) -> None:
    positive = {
        "fragments": fragments,
        "batch_size": batch_size,
        "relations": relations,
        "relation_batch_size": relation_batch_size,
        "recall_samples": recall_samples,
        "startup_samples": startup_samples,
        "sync_samples": sync_samples,
    }
    if any(value <= 0 for value in positive.values()):
        raise ValueError("benchmark sizes and sample counts must be positive")
    if fragments < 2:
        raise ValueError("relation capacity requires at least two fragments")
    if recall_samples > fragments:
        raise ValueError("recall sample count cannot exceed fragment count")
    if warmups < 0:
        raise ValueError("warmup count must not be negative")


def run_benchmark(
    *,
    fragments: int,
    batch_size: int,
    relations: int,
    relation_batch_size: int,
    recall_samples: int,
    startup_samples: int,
    sync_samples: int,
    warmups: int,
) -> dict[str, JsonValue]:
    """Run all local measurements without retaining product or provider state."""

    _validate_sizes(
        fragments=fragments,
        batch_size=batch_size,
        relations=relations,
        relation_batch_size=relation_batch_size,
        recall_samples=recall_samples,
        startup_samples=startup_samples,
        sync_samples=sync_samples,
        warmups=warmups,
    )
    measured_at = datetime.now(UTC)
    recipe = {
        "version": "sys4ai-local-runtime-synthetic-v1",
        "fragments": fragments,
        "batch_size": batch_size,
        "relations": relations,
        "relation_batch_size": relation_batch_size,
        "recall_samples": recall_samples,
        "startup_samples": startup_samples,
        "sync_samples": sync_samples,
        "warmups": warmups,
    }
    with TemporaryDirectory(prefix="sys4ai-memory-runtime-benchmark-") as temporary:
        root = Path(temporary).resolve()
        configuration_path = _write_benchmark_configuration(root)
        _write_permissions(root)
        configuration = load_configuration(configuration_path, trusted_project_root=root)
        authorization, loader = _authorization(root)
        bridge = ProviderAuthorizationBridge(authorization, loader)
        provider = InMemoryProvider(
            InMemoryProviderConfig(project_id=PROJECT_ID, dataset_id=DATASET_ID)
        )
        _initialize_provider(provider, bridge, configuration)
        index_path = configuration.resolved_paths["exact_index"]

        with ExactIndex(index_path) as index:
            build_seconds, source_count, fragment_record_ids, endpoint_records = _build_corpus(
                index=index,
                provider=provider,
                bridge=bridge,
                fragments=fragments,
                batch_size=batch_size,
            )
            indexed_records = index.health(PROJECT_ID).current_record_count
            relation_seconds, relation_latencies = _load_relations(
                provider=provider,
                bridge=bridge,
                record_ids=fragment_record_ids,
                endpoint_records=endpoint_records,
                relation_count=relations,
                batch_size=relation_batch_size,
            )
            retrieval = RetrievalEngine(
                project_id=PROJECT_ID,
                dataset_id=DATASET_ID,
                authorizer=authorization,
                exact_backend=index,
                provider=provider,
            )
            recall_service = _service(
                configuration,
                authorization,
                loader,
                components=ServiceComponents(
                    exact_index=index,
                    retrieval=retrieval,
                    provider=provider,
                ),
            )
            recall_latencies, returned_records = _measure_hybrid_recall(
                recall_service,
                fragments=fragments,
                samples=recall_samples,
                warmups=warmups,
            )
            sync_latencies, maximum_source_bytes = _measure_incremental_sync(
                root=root,
                configuration=configuration,
                authorization=authorization,
                loader=loader,
                index=index,
                provider=provider,
                samples=sync_samples,
                warmups=warmups,
            )
            database_bytes = _database_bytes(index_path)

        startup_latencies = _measure_guarded_startup(
            root=root,
            configuration_path=configuration_path,
            index_path=index_path,
            expected_record_count=indexed_records,
            samples=startup_samples,
            warmups=warmups,
        )

        hybrid = _latency_summary(recall_latencies)
        hybrid["warmups"] = warmups
        hybrid["target_p95_ms"] = 3000
        hybrid["measured_path_p95_within_target"] = _percentile(recall_latencies, 0.95) <= 3000
        hybrid["returned_records_total"] = returned_records
        hybrid["requirement_verified"] = False

        startup = _latency_summary(startup_latencies)
        startup["warmups"] = warmups
        startup["target_ms"] = 15000
        startup["measured_path_p95_within_target"] = _percentile(startup_latencies, 0.95) <= 15000
        startup["requirement_verified"] = False

        sync = _latency_summary(sync_latencies)
        sync["warmups"] = warmups
        sync["target_p95_ms"] = 10000
        sync["measured_path_p95_within_target"] = _percentile(sync_latencies, 0.95) <= 10000
        sync["changed_sources_per_sample"] = 1
        sync["maximum_source_bytes"] = maximum_source_bytes
        sync["measured_path"] = (
            "guarded-memory-service-source-discovery-normalization-sqlite-in-memory-provider"
        )
        sync["guarded_provider_path_measured"] = True
        sync["requirement_verified"] = False

        relation_batches = _latency_summary(relation_latencies)
        relation_batches["batch_size"] = relation_batch_size
        relation_batches["total_seconds"] = round(relation_seconds, 3)

        return {
            "schema_version": "1.0",
            "benchmark": "sys4ai-local-runtime-synthetic-v1",
            "measured_at": measured_at.isoformat().replace("+00:00", "Z"),
            "environment": {
                "platform": platform.platform(),
                "machine": platform.machine(),
                "python": platform.python_version(),
                "sqlite": sqlite3.sqlite_version,
                "logical_cpus": os.cpu_count(),
                "physical_memory_gb": _physical_memory_gb(),
                "peak_process_rss_mb": _peak_rss_mb(),
            },
            "corpus": {
                "synthetic": True,
                "non_sensitive": True,
                "fragments": fragments,
                "source_artifacts": source_count,
                "indexed_records_before_sync": indexed_records,
                "provider": "in-memory-conformance",
                "relations": relations,
                "exact_database_bytes": database_bytes,
                "recipe_sha256": sha256_bytes(canonical_json_bytes(recipe)),
                "disposable_storage_removed_after_run": True,
            },
            "corpus_build_seconds": round(build_seconds, 3),
            "hybrid_recall": hybrid,
            "guarded_startup": startup,
            "incremental_sync": sync,
            "relation_capacity": {
                "loaded_relations": relations,
                "target_relations": 1_000_000,
                "full_relation_target_exercised": relations >= 1_000_000,
                "fragment_target_exercised": fragments >= 100_000,
                "batch_load_latency": relation_batches,
                "included_in_hybrid_provider_recall": True,
                "relation_indexed_by_endpoint": True,
                "full_relation_scan_per_recall": False,
                "requirement_verified": False,
            },
            "evidence_boundaries": [
                "Hybrid recall used MemoryService, canonical file authorization, "
                "RetrievalEngine, SQLite ExactIndex, and the in-memory conformance provider.",
                "The semantic and graph scores are deterministic token/relation fixtures, "
                "not model quality or real Cognee evidence.",
                "Startup measured configuration load, existing SQLite open/health, service "
                "and exact-only retrieval construction, and authorized health; it did not "
                "open a Cognee database or start a process/listener.",
                "Incremental sync changed one small text source per sample and measured the "
                "guarded MemoryService, discovery, normalization, record revision assignment, "
                "SQLite update, in-memory provider write, audit, and operation receipt path.",
                "Relation capacity measured in-memory contract validation, load, and "
                "endpoint-indexed one-hop recall; it does not prove real local-profile or "
                "Cognee capacity.",
                "No model, Cognee runtime, network listener, credential, or canonical product "
                "state was started, contacted, or changed.",
            ],
        }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fragments", type=int, default=100_000)
    parser.add_argument("--batch-size", type=int, default=1_000)
    parser.add_argument("--relations", type=int, default=100_000)
    parser.add_argument("--relation-batch-size", type=int, default=10_000)
    parser.add_argument("--recall-samples", type=int, default=20)
    parser.add_argument("--startup-samples", type=int, default=20)
    parser.add_argument("--sync-samples", type=int, default=20)
    parser.add_argument("--warmups", type=int, default=3)
    args = parser.parse_args(argv)
    result = run_benchmark(
        fragments=args.fragments,
        batch_size=args.batch_size,
        relations=args.relations,
        relation_batch_size=args.relation_batch_size,
        recall_samples=args.recall_samples,
        startup_samples=args.startup_samples,
        sync_samples=args.sync_samples,
        warmups=args.warmups,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
