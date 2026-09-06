#!/usr/bin/env python3
"""Run the reproducible synthetic exact/lexical reference-corpus benchmark."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sqlite3
import statistics
import sys
from datetime import UTC, datetime
from time import perf_counter

from sys4ai_memory.contracts import (
    API_VERSION,
    SCHEMA_VERSION,
    AuthorityTier,
    MemoryScope,
    Sensitivity,
    SourceRole,
    TrustClass,
)
from sys4ai_memory.contracts.models import ScopeReference, SourceRecord
from sys4ai_memory.exact_index import ExactIndex
from sys4ai_memory.ingestion import normalize_bytes

PROJECT_ID = "benchmark-project"


def _percentile(values: list[float], percentile: float) -> float:
    ordered = sorted(values)
    index = min(len(ordered) - 1, int(len(ordered) * percentile))
    return ordered[index]


def _source(batch: int, raw: bytes) -> SourceRecord:
    path = f"benchmark/batch-{batch:04d}.jsonl"
    return SourceRecord(
        schema_version=SCHEMA_VERSION,
        api_version=API_VERSION,
        source_id=f"src_BENCH{batch:04d}",
        project_id=PROJECT_ID,
        path_or_uri=path,
        path_pattern=None,
        source_kind="repository_file",
        format="jsonl",
        canonicality="canonical",
        content_role=SourceRole.AUTHORITATIVE,
        authority_tier=AuthorityTier.CANONICAL_PROJECT_KNOWLEDGE,
        trust_class=TrustClass.PROJECT_AUTHORED,
        sensitivity=Sensitivity.INTERNAL,
        namespace="benchmark",
        scope=ScopeReference(level=MemoryScope.PROJECT, scope_id=PROJECT_ID),
        profile_id="base@1",
        ingestion_adapter="jsonl",
        chunking_profile="row@1",
        schema_ref=None,
        refresh_mode="benchmark",
        retention_policy="disposable-benchmark",
        owner="benchmark",
        write_policy="deny",
        include_flag=True,
        notes="Synthetic disposable benchmark source",
        content_sha256=hashlib.sha256(raw).hexdigest(),
        locator={"path": path, "label": f"benchmark batch {batch}"},
        git_commit=None,
        git_blob_sha=None,
        working_tree_state="disposable-benchmark",
        origin_uri=None,
        retrieved_at=None,
        licensing_metadata={},
        access_metadata={},
        generated_from=(),
    )


def _batch_bytes(start: int, count: int) -> bytes:
    return b"".join(
        (
            json.dumps(
                {
                    "event_id": f"BENCH-ID-{number:06d}",
                    "text": (
                        f"Benchmark record BENCH-ID-{number:06d} "
                        f"provider abstraction group {number % 100}."
                    ),
                },
                separators=(",", ":"),
                sort_keys=True,
            )
            + "\n"
        ).encode("utf-8")
        for number in range(start, start + count)
    )


def run_benchmark(*, fragments: int, batch_size: int, exact_samples: int) -> dict[str, object]:
    if fragments <= 0 or batch_size <= 0 or exact_samples <= 0:
        raise ValueError("benchmark sizes must be positive")
    if exact_samples > fragments:
        raise ValueError("exact sample count cannot exceed fragment count")
    processed_at = datetime.now(UTC)
    started = perf_counter()
    source_count = 0
    with ExactIndex(":memory:") as index:
        for batch_start in range(0, fragments, batch_size):
            count = min(batch_size, fragments - batch_start)
            raw = _batch_bytes(batch_start, count)
            source = _source(source_count, raw)
            document = normalize_bytes(source, raw, processed_at=processed_at)
            index.upsert_document(document)
            source_count += 1
        build_seconds = perf_counter() - started

        sample_step = max(1, fragments // exact_samples)
        sample_ids = tuple(range(0, fragments, sample_step))[:exact_samples]
        for number in sample_ids[: min(20, len(sample_ids))]:
            index.query_exact(
                project_id=PROJECT_ID,
                query=f"BENCH-ID-{number:06d}",
                limit=5,
            )
        exact_latencies: list[float] = []
        for number in sample_ids:
            query = f"BENCH-ID-{number:06d}"
            query_started = perf_counter()
            hits = index.query_exact(project_id=PROJECT_ID, query=query, limit=5)
            exact_latencies.append((perf_counter() - query_started) * 1000)
            if not hits or query not in hits[0].content:
                raise RuntimeError(f"exact benchmark query missed: {query}")

        lexical_latencies: list[float] = []
        for group in range(100):
            query_started = perf_counter()
            hits = index.query_lexical(
                project_id=PROJECT_ID,
                query=f"group {group}",
                phrase=True,
                limit=5,
            )
            lexical_latencies.append((perf_counter() - query_started) * 1000)
            if not hits:
                raise RuntimeError(f"lexical benchmark query missed group {group}")
        health = index.health(PROJECT_ID)

    return {
        "schema_version": "1.0",
        "benchmark": "sys4ai-exact-index-synthetic-v1",
        "measured_at": processed_at.isoformat().replace("+00:00", "Z"),
        "environment": {
            "platform": platform.platform(),
            "machine": platform.machine(),
            "python": platform.python_version(),
            "sqlite": sqlite3.sqlite_version,
        },
        "corpus": {
            "fragments": fragments,
            "source_artifacts": source_count,
            "indexed_records": health.current_record_count,
            "in_memory": True,
        },
        "build_seconds": round(build_seconds, 3),
        "exact": {
            "samples": len(exact_latencies),
            "p50_ms": round(statistics.median(exact_latencies), 3),
            "p95_ms": round(_percentile(exact_latencies, 0.95), 3),
            "max_ms": round(max(exact_latencies), 3),
            "target_p95_ms": 500,
            "target_met": _percentile(exact_latencies, 0.95) <= 500,
        },
        "lexical": {
            "samples": len(lexical_latencies),
            "p50_ms": round(statistics.median(lexical_latencies), 3),
            "p95_ms": round(_percentile(lexical_latencies, 0.95), 3),
            "max_ms": round(max(lexical_latencies), 3),
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fragments", type=int, default=100_000)
    parser.add_argument("--batch-size", type=int, default=1_000)
    parser.add_argument("--exact-samples", type=int, default=200)
    args = parser.parse_args(argv)
    result = run_benchmark(
        fragments=args.fragments,
        batch_size=args.batch_size,
        exact_samples=args.exact_samples,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
