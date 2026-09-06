from __future__ import annotations

import json
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path

import pytest

from sys4ai_memory.authorization import (
    AuthorizationService,
    CanonicalPermissionEnvelopeLoader,
)
from sys4ai_memory.contracts import (
    AuthorityTier,
    RecordStatus,
    RetrievalMode,
    Sensitivity,
    SourceRecord,
    TrustClass,
)
from sys4ai_memory.exact_index import ExactIndex
from sys4ai_memory.ingestion import NormalizedDocument
from sys4ai_memory.interfaces import DispatchSuccess, MemoryClient
from sys4ai_memory.lifecycle import (
    DestructiveLifecycleService,
    FilesystemImpactResolver,
    LifecycleCatalog,
    LifecycleRecord,
    ResourceSpec,
    StorageLocation,
)
from sys4ai_memory.retrieval import RetrievalEngine
from sys4ai_memory.security import ProjectBoundary
from sys4ai_memory.service import ServiceComponents
from tests.contracts.cases import SOURCE_RECORD
from tests.retrieval.helpers import StaticProvider, memory_record, provider_candidate
from tests.service.test_dispatcher import DATASET_ID, PROJECT_ID, _identity, _service

pytestmark = [pytest.mark.integration, pytest.mark.security, pytest.mark.acceptance]

NOW = datetime(2026, 9, 3, 18, tzinfo=UTC)


def _record(record_id: str) -> LifecycleRecord:
    return LifecycleRecord(
        record_id=record_id,
        project_id=PROJECT_ID,
        dataset_id=DATASET_ID,
        status=RecordStatus.ACTIVE,
        authority_tier=AuthorityTier.AGENT_DURABLE_MATERIAL,
        trust_class=TrustClass.AGENT_GENERATED,
        sensitivity=Sensitivity.INTERNAL,
        canonical=False,
        source_ids=("src_lifecycle_acceptance",),
        valid_from=NOW,
    )


def test_public_supersession_and_two_phase_deletion_share_governed_lifecycle(
    tmp_path: Path,
) -> None:
    root = tmp_path.resolve()
    components = ServiceComponents()
    service, audit, permission_path = _service(root, components=components)
    permissions = json.loads(permission_path.read_text(encoding="utf-8"))
    permissions["grants"][0]["operations"].append("memory.forget.delete-derived")
    permission_path.write_text(json.dumps(permissions, sort_keys=True), encoding="utf-8")

    lifecycle = LifecycleCatalog()
    for record_id in ("mem_PRIOR", "mem_REPLACEMENT", "mem_DELETE_TARGET"):
        lifecycle.add(_record(record_id))
    raw = b"disposable lifecycle acceptance fixture"
    source_payload = deepcopy(SOURCE_RECORD)
    source_payload.update(
        {
            "source_id": "src_lifecycle_acceptance",
            "project_id": PROJECT_ID,
            "path_or_uri": "docs/lifecycle.md",
            "canonicality": "derived",
            "authority_tier": AuthorityTier.AGENT_DURABLE_MATERIAL.value,
            "trust_class": TrustClass.AGENT_GENERATED.value,
            "namespace": "project/lifecycle",
            "scope": {
                "level": "project",
                "scope_id": PROJECT_ID,
                "parent_scopes": [],
            },
            "content_sha256": "d" * 64,
            "locator": {"path": "docs/lifecycle.md"},
        }
    )
    source = SourceRecord.model_validate(source_payload)
    indexed_records = tuple(
        memory_record(
            record_id,
            project_id=PROJECT_ID,
            source_id="src_lifecycle_acceptance",
            path="docs/lifecycle.md",
            title=record_id,
            content=f"Lifecycle evidence for {record_id}.",
            tier=AuthorityTier.AGENT_DURABLE_MATERIAL,
            trust=TrustClass.AGENT_GENERATED,
            canonical=False,
        )
        for record_id in ("mem_PRIOR", "mem_REPLACEMENT", "mem_DELETE_TARGET")
    )
    index = ExactIndex(":memory:")
    index.upsert_document(
        NormalizedDocument(
            source=source,
            raw_bytes=raw,
            records=indexed_records,
            adapter_id="lifecycle-test",
            adapter_version="1.0.0",
            profile_version="1.0.0",
            processed_at=NOW,
        )
    )
    derived = root / ".sys4ai/memory/provider/delete-target.bin"
    derived.parent.mkdir(parents=True)
    derived.write_text("disposable derived representation", encoding="utf-8")
    boundary = ProjectBoundary(PROJECT_ID, DATASET_ID, root)
    authorization = AuthorizationService(
        CanonicalPermissionEnvelopeLoader(
            boundary,
            "control_records/memory/permissions.json",
        )
    )
    components.lifecycle = lifecycle
    components.lifecycle_index = index
    components.retrieval = RetrievalEngine(
        project_id=PROJECT_ID,
        dataset_id=DATASET_ID,
        authorizer=authorization,
        exact_backend=index,
        exact_record_resolver=index,
        provider=StaticProvider(
            tuple(provider_candidate(record, semantic=0.9) for record in indexed_records)
        ),
    )
    components.destructive = DestructiveLifecycleService(
        boundary,
        authorization,
        FilesystemImpactResolver(
            boundary,
            (
                ResourceSpec(
                    resource_id="mem_DELETE_TARGET",
                    project_id=PROJECT_ID,
                    dataset_id=DATASET_ID,
                    location=StorageLocation.DERIVED_PROVIDER,
                    relative_path=".sys4ai/memory/provider/delete-target.bin",
                    record_id="mem_DELETE_TARGET",
                    source_id=None,
                    sensitivity=Sensitivity.INTERNAL,
                    canonical=False,
                ),
            ),
        ),
        deletable_roots=(".sys4ai/memory",),
        lifecycle=lifecycle,
    )
    client = MemoryClient(
        service,
        identity=_identity(),
        project_id=PROJECT_ID,
        dataset_id=DATASET_ID,
    )

    superseded = client.supersede(
        "mem_PRIOR",
        "mem_REPLACEMENT",
        reason="new source-backed replacement",
        idempotency_key="lifecycle-supersede",
        request_id="mrq_lifecycle_supersede",
        trace_id="trace_lifecycle_supersede",
    )
    assert isinstance(superseded, DispatchSuccess)
    assert superseded.result["prior"]["status"] == "superseded"  # type: ignore[index]
    assert superseded.result["replacement"]["supersedes"] == [  # type: ignore[index]
        "mem_PRIOR"
    ]
    assert superseded.result["deterministic_index_updated"] is True
    assert not index.query_exact(project_id=PROJECT_ID, query="mem_PRIOR")
    historical_prior = index.query_exact(
        project_id=PROJECT_ID,
        query="mem_PRIOR",
        current_only=False,
    )[0]
    assert historical_prior.lifecycle.status is RecordStatus.SUPERSEDED
    current_recall = client.recall(
        "mem_PRIOR",
        mode=RetrievalMode.HYBRID,
        request_id="mrq_lifecycle_current_recall",
        trace_id="trace_lifecycle_current_recall",
    )
    historical_recall = client.recall(
        "mem_PRIOR",
        mode=RetrievalMode.HYBRID,
        current_only=False,
        request_id="mrq_lifecycle_historical_recall",
        trace_id="trace_lifecycle_historical_recall",
    )
    assert isinstance(current_recall, DispatchSuccess)
    current_rows = current_recall.result["retrieval"]["results"]  # type: ignore[index]
    assert all(row["record_id"] != "mem_PRIOR" for row in current_rows)  # type: ignore[index]
    assert isinstance(historical_recall, DispatchSuccess)
    history_rows = historical_recall.result["retrieval"]["results"]  # type: ignore[index]
    assert history_rows[0]["record_id"] == "mem_PRIOR"  # type: ignore[index]
    assert history_rows[0]["lifecycle"]["status"] == "superseded"  # type: ignore[index]

    previewed = client.forget(
        ("mem_DELETE_TARGET",),
        action="delete-derived",
        reason="approved disposable cleanup",
        idempotency_key="lifecycle-delete-preview",
        request_id="mrq_lifecycle_delete_preview",
        trace_id="trace_lifecycle_delete_preview",
    )
    assert isinstance(previewed, DispatchSuccess)
    preview = previewed.result["preview"]
    assert isinstance(preview, dict)
    assert preview["mutating"] is False
    assert derived.is_file()

    executed = client.forget(
        ("mem_DELETE_TARGET",),
        action="delete-derived",
        reason="approved disposable cleanup",
        idempotency_key="lifecycle-delete-execute",
        execute=True,
        operation_id=preview["operation_id"],
        impact_digest=preview["impact_digest"],
        request_id="mrq_lifecycle_delete_execute",
        trace_id="trace_lifecycle_delete_execute",
    )
    assert isinstance(executed, DispatchSuccess)
    receipt = executed.result["receipt"]
    assert isinstance(receipt, dict)
    assert receipt["operation_id"] == preview["operation_id"]
    assert receipt["impact_digest"] == preview["impact_digest"]
    assert receipt["outcome"] == "succeeded"
    assert receipt["transitioned_record_ids"] == ["mem_DELETE_TARGET"]
    assert not derived.exists()
    assert lifecycle.get("mem_DELETE_TARGET").status is RecordStatus.DELETED
    assert [event.outcome for event in audit.events()] == [
        "authorized",
        "succeeded",
        "succeeded",
        "succeeded",
        "authorized",
        "succeeded",
        "authorized",
        "succeeded",
    ]
    index.close()
