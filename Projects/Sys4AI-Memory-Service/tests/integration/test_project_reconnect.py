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

CONTEXT_SOURCES = (
    (
        "src_reconnect_governance",
        "control/governance.md",
        "governance",
        AuthorityTier.SYS4AI_GOVERNANCE,
        TrustClass.HUMAN_APPROVED,
        "Current governance RECONNECT-CONTEXT\n\nThe project follows governed task delivery.\n",
    ),
    (
        "src_reconnect_decisions",
        "docs/decisions.md",
        "decision",
        AuthorityTier.PROJECT_CONTROL,
        TrustClass.HUMAN_APPROVED,
        "Active decision RECONNECT-CONTEXT\n\nUse provider-neutral memory contracts.\n",
    ),
    (
        "src_reconnect_requirements",
        "docs/requirements.md",
        "requirement",
        AuthorityTier.CANONICAL_PROJECT_KNOWLEDGE,
        TrustClass.PROJECT_AUTHORED,
        "Relevant requirement RECONNECT-CONTEXT\n\nEvery answer cites its canonical source.\n",
    ),
    (
        "src_reconnect_architecture",
        "docs/architecture.md",
        "architecture",
        AuthorityTier.CANONICAL_PROJECT_KNOWLEDGE,
        TrustClass.PROJECT_AUTHORED,
        "Current architecture RECONNECT-CONTEXT\n\nAgents use one stable service boundary.\n",
    ),
    (
        "src_reconnect_outcomes",
        "docs/verified-outcomes.md",
        "verification",
        AuthorityTier.PROJECT_CONTROL,
        TrustClass.SCHEMA_VALIDATED,
        "Recent verified outcome RECONNECT-CONTEXT\n\nThe focused contract suite passed.\n",
    ),
)


def _entry(
    source_id: str,
    path: str,
    role: str,
    tier: AuthorityTier,
    trust: TrustClass,
) -> SourceRegistryEntry:
    return SourceRegistryEntry(
        source_id=source_id,
        project_id=PROJECT_ID,
        path_or_uri=path,
        path_pattern=None,
        source_kind="file",
        format="markdown",
        canonicality="canonical",
        content_role=role,
        authority_tier=tier,
        trust_class=trust,
        sensitivity=Sensitivity.INTERNAL,
        namespace="project/reconnect",
        profile_id="base@1",
        ingestion_adapter="markdown",
        chunking_profile="heading-blocks@1",
        schema_ref=None,
        refresh_mode="content-hash",
        retention_policy="canonical",
        owner="project",
        write_policy="reviewed-project-change",
        include_flag=True,
        notes="project reconnect acceptance fixture",
    )


def test_new_agent_session_recalls_complete_current_project_context(
    tmp_path: Path,
) -> None:
    root = tmp_path.resolve()
    entries = []
    for source_id, relative, role, tier, trust, body in CONTEXT_SOURCES:
        source_path = root / relative
        source_path.parent.mkdir(parents=True, exist_ok=True)
        source_path.write_text(f"# {body}", encoding="utf-8")
        entries.append(_entry(source_id, relative, role, tier, trust))
    report = SourceDiscovery(
        project_root=root,
        project_id=PROJECT_ID,
        entries=tuple(entries),
        respect_gitignore=False,
    ).discover()
    synchronized = IngestionSynchronizer(project_root=root).synchronize(report, force=True)
    assert not synchronized.failures
    database = root / ".sys4ai/memory/exact_index/index.sqlite3"
    with ExactIndex(database) as builder:
        builder.rebuild(
            IndexGeneration(
                generation_id="gen_project_reconnect",
                project_id=PROJECT_ID,
                configuration_fingerprint="a" * 64,
                profile_versions=(("base@1", "1.0.0"),),
                adapter_versions=(("markdown", "1.0.0"),),
                created_at=NOW,
            ),
            synchronized.documents,
        )

    with ExactIndex(database) as reopened:
        components = ServiceComponents(exact_index=reopened)
        service, audit, _ = _service(root, components=components)
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
            exact_backend=reopened,
            exact_record_resolver=reopened,
        )
        client = MemoryClient(
            service,
            identity=InterfaceIdentity(
                principal_id="agent-service",
                agent_type="project-director",
                run_id="run_fresh_project_reconnect",
            ),
            project_id=PROJECT_ID,
            dataset_id=DATASET_ID,
        )
        response = client.recall(
            "RECONNECT-CONTEXT",
            mode=RetrievalMode.EXACT,
            limit=10,
            request_id="mrq_project_reconnect",
            trace_id="trace_project_reconnect",
        )

    assert isinstance(response, DispatchSuccess)
    retrieval = response.result["retrieval"]
    assert isinstance(retrieval, dict)
    rows = retrieval["results"]
    assert isinstance(rows, list)
    expected_paths = {item[1] for item in CONTEXT_SOURCES}
    assert {row["source"]["path"] for row in rows} == expected_paths
    assert all(row["lifecycle"]["status"] == "active" for row in rows)
    assert all(row["source"]["source_id"] for row in rows)
    assert all(row["source"]["content_sha256"] for row in rows)
    assert all(row["source"]["locator"] for row in rows)
    assert [event.outcome for event in audit.events()] == ["succeeded"]
