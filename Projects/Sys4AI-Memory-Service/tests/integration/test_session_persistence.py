from __future__ import annotations

from datetime import UTC, datetime
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
from sys4ai_memory.exact_index import ExactIndex, IndexGeneration
from sys4ai_memory.ingestion import IngestionSynchronizer
from sys4ai_memory.interfaces import DispatchSuccess, InterfaceIdentity, MemoryClient
from sys4ai_memory.retrieval import RetrievalEngine
from sys4ai_memory.security import ProjectBoundary
from sys4ai_memory.service import ServiceComponents
from sys4ai_memory.sources import SourceDiscovery, SourceRegistryEntry
from tests.service.test_dispatcher import DATASET_ID, PROJECT_ID, _service

pytestmark = [pytest.mark.integration, pytest.mark.security, pytest.mark.acceptance]

NOW = datetime(2026, 9, 3, 18, tzinfo=UTC)


def _source() -> SourceRegistryEntry:
    return SourceRegistryEntry(
        source_id="src_session_persistence",
        project_id=PROJECT_ID,
        path_or_uri="docs/session-memory.md",
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
        notes="cross-session persistence fixture",
    )


def _client_for_index(root: Path, index: ExactIndex, *, run_id: str) -> MemoryClient:
    components = ServiceComponents(exact_index=index)
    service, _, _ = _service(root, components=components)
    authorization = AuthorizationService(
        CanonicalPermissionEnvelopeLoader(
            ProjectBoundary(PROJECT_ID, DATASET_ID, root),
            "control_records/memory/permissions.json",
        )
    )
    components.retrieval = RetrievalEngine(
        project_id=PROJECT_ID,
        dataset_id=DATASET_ID,
        authorizer=authorization,
        exact_backend=index,
        exact_record_resolver=index,
    )
    return MemoryClient(
        service,
        identity=InterfaceIdentity(
            principal_id="agent-service",
            agent_type="persistence-test-agent",
            run_id=run_id,
        ),
        project_id=PROJECT_ID,
        dataset_id=DATASET_ID,
    )


def test_fresh_agent_session_recalls_existing_source_anchored_index(
    tmp_path: Path,
) -> None:
    root = tmp_path.resolve()
    source_path = root / "docs/session-memory.md"
    source_path.parent.mkdir()
    source_path.write_text(
        "# Persistent requirement\n\nSESSION-MEMORY-042 remains available across sessions.\n",
        encoding="utf-8",
    )
    report = SourceDiscovery(
        project_root=root,
        project_id=PROJECT_ID,
        entries=(_source(),),
        respect_gitignore=False,
    ).discover()
    synchronized = IngestionSynchronizer(project_root=root).synchronize(report, force=True)
    assert not synchronized.failures
    database = root / ".sys4ai/memory/exact_index/index.sqlite3"
    with ExactIndex(database) as builder:
        builder.rebuild(
            IndexGeneration(
                generation_id="gen_session_persistence",
                project_id=PROJECT_ID,
                configuration_fingerprint="a" * 64,
                profile_versions=(("base@1", "1.0.0"),),
                adapter_versions=(("markdown", "1.0.0"),),
                created_at=NOW,
            ),
            synchronized.documents,
        )

    with ExactIndex(database) as first_index:
        first = _client_for_index(root, first_index, run_id="run_persistence_first").recall(
            "SESSION-MEMORY-042",
            mode=RetrievalMode.EXACT,
            request_id="mrq_persistence_first",
            trace_id="trace_persistence_first",
        )
    with ExactIndex(database) as reopened_index:
        second = _client_for_index(
            root,
            reopened_index,
            run_id="run_persistence_second",
        ).recall(
            "SESSION-MEMORY-042",
            mode=RetrievalMode.EXACT,
            request_id="mrq_persistence_second",
            trace_id="trace_persistence_second",
        )

    assert isinstance(first, DispatchSuccess)
    assert isinstance(second, DispatchSuccess)
    first_rows = first.result["retrieval"]["results"]  # type: ignore[index]
    second_rows = second.result["retrieval"]["results"]  # type: ignore[index]
    assert [row["record_id"] for row in first_rows] == [  # type: ignore[index]
        row["record_id"] for row in second_rows  # type: ignore[index]
    ]
    assert second_rows[0]["source"]["source_id"] == "src_session_persistence"  # type: ignore[index]
    assert second_rows[0]["source"]["path"] == "docs/session-memory.md"  # type: ignore[index]
    assert second_rows[0]["content"] == source_path.read_text(  # type: ignore[index]
        encoding="utf-8"
    )
