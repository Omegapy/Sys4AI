"""Narrow injectable ports used by the unified memory-service dispatcher."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from sys4ai_memory.contracts import ScopeReference
from sys4ai_memory.contracts.models import MemoryRecord, RetrievedRecord
from sys4ai_memory.ingestion import IngestionSynchronizer
from sys4ai_memory.lifecycle import DestructiveLifecycleService, LifecycleCatalog
from sys4ai_memory.observability import HealthAggregator
from sys4ai_memory.policies import (
    AuthorizedImprovementService,
    AuthorizedWritePolicy,
    CanonicalPromotionPlanner,
    CanonicalPromotionReceipt,
    EpisodicMemoryStore,
    ProposalStager,
    ReviewerAuthorizationGate,
    ReviewReceipt,
    SessionMemoryStore,
    StagedProposalArtifact,
)
from sys4ai_memory.providers import MemoryProvider
from sys4ai_memory.rebuild import (
    AuthorizedRebuildImpact,
    RebuildExecutionReceipt,
    RebuildMode,
    RebuildPreview,
)
from sys4ai_memory.retrieval import RetrievalEngine
from sys4ai_memory.sources import RegistryBundle

from .models import (
    EvidenceSynthesisRequest,
    EvidenceSynthesisResult,
    PortableExportCall,
    PortableImportCall,
    PortResult,
)


class ExactIndexPort(Protocol):
    """Read operations needed from the deterministic index."""

    def query_exact(
        self,
        *,
        project_id: str,
        query: str,
        case_sensitive: bool = True,
        field: str | None = None,
        current_only: bool = True,
        limit: int = 20,
    ) -> tuple[RetrievedRecord, ...]: ...


class LifecycleIndexPort(Protocol):
    """Apply lifecycle changes to the deterministic retrieval projection."""

    def supersede_records(
        self,
        *,
        project_id: str,
        prior_record_id: str,
        replacement_record_id: str,
        at: datetime | None = None,
    ) -> tuple[MemoryRecord, MemoryRecord]: ...


class RebuildPort(Protocol):
    """Generation rebuild boundary used without exposing storage internals."""

    def preview(
        self,
        *,
        operation_id: str,
        mode: RebuildMode,
        deterministic: bool = True,
    ) -> RebuildPreview: ...

    async def execute(
        self,
        preview: RebuildPreview,
        *,
        authorization: AuthorizedRebuildImpact,
    ) -> RebuildExecutionReceipt: ...


class PortableExchangePort(Protocol):
    """Optional policy-aware package exchange implementation."""

    async def export(self, call: PortableExportCall) -> PortResult: ...

    async def preview_import(self, call: PortableImportCall) -> PortResult: ...

    async def import_package(self, call: PortableImportCall) -> PortResult: ...


class CanonicalPromotionPort(Protocol):
    """Execute a reviewed canonical change and return matching sync evidence."""

    def execute(
        self,
        artifact: StagedProposalArtifact,
        review: ReviewReceipt,
        *,
        project_id: str,
        dataset_id: str,
        scope: ScopeReference,
        record_type: str,
        trace_id: str,
        idempotency_key: str,
    ) -> CanonicalPromotionReceipt: ...


class EvidenceSynthesisPort(Protocol):
    """Optional explicit-answer synthesis over an authorized evidence bundle."""

    async def synthesize(
        self,
        request: EvidenceSynthesisRequest,
    ) -> EvidenceSynthesisResult: ...


@dataclass(slots=True)
class ServiceComponents:
    """All optional subsystems; construction performs no provider or storage I/O."""

    registry_loader: Callable[[], RegistryBundle] | None = None
    synchronizer: IngestionSynchronizer | None = None
    exact_index: ExactIndexPort | None = None
    retrieval: RetrievalEngine | None = None
    synthesis: EvidenceSynthesisPort | None = None
    write_policy: AuthorizedWritePolicy | None = None
    proposal_stager: ProposalStager | None = None
    reviewer_gate: ReviewerAuthorizationGate | None = None
    promotion_planner: CanonicalPromotionPlanner | None = None
    promotion: CanonicalPromotionPort | None = None
    session_store: SessionMemoryStore | None = None
    episodic_store: EpisodicMemoryStore | None = None
    lifecycle: LifecycleCatalog | None = None
    lifecycle_index: LifecycleIndexPort | None = None
    destructive: DestructiveLifecycleService | None = None
    improvement: AuthorizedImprovementService | None = None
    provider: MemoryProvider | None = None
    health: HealthAggregator | None = None
    rebuild: RebuildPort | None = None
    exchange: PortableExchangePort | None = None
