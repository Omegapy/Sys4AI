"""Provider-neutral in-memory doubles used by retrieval tests."""

from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime

from sys4ai_memory.authorization import AuthorizationDecision, AuthorizationRequest
from sys4ai_memory.contracts import (
    API_VERSION,
    SCHEMA_VERSION,
    AuthorityTier,
    Permission,
    RecordStatus,
    TrustClass,
)
from sys4ai_memory.contracts.models import (
    MemoryRecord,
    RelationRecord,
    RetrievalAuthority,
    RetrievalLifecycle,
    RetrievalScores,
    RetrievalSource,
    RetrievedRecord,
)
from sys4ai_memory.providers import (
    IN_MEMORY_PROVIDER_VERSION,
    ProviderChannelScores,
    ProviderName,
    ProviderRecallCandidate,
    ProviderRecallResult,
    RecallRequest,
)
from tests.contracts.cases import MEMORY_RECORD, RELATION_RECORD

NOW = datetime(2026, 9, 3, 12, tzinfo=UTC)


def memory_record(
    record_id: str,
    *,
    project_id: str = "project-alpha",
    source_id: str = "src_alpha",
    path: str | None = "docs/source.md",
    origin_uri: str | None = None,
    namespace: str = "project/knowledge",
    title: str = "Evidence record",
    content: str = "Evidence-backed content for the requested project.",
    tier: AuthorityTier = AuthorityTier.CANONICAL_PROJECT_KNOWLEDGE,
    trust: TrustClass = TrustClass.PROJECT_AUTHORED,
    canonical: bool = True,
    status: RecordStatus = RecordStatus.ACTIVE,
    valid_from: str = "2026-01-01T00:00:00Z",
    valid_to: str | None = None,
    line_start: int = 1,
    line_end: int = 4,
    parsed_by: str = "markdown-adapter",
    model_extracted: bool = False,
    record_type: str = "Statement",
    content_sha256: str = "d" * 64,
) -> MemoryRecord:
    payload = deepcopy(MEMORY_RECORD)
    payload["record_id"] = record_id
    payload["record_type"] = record_type
    payload["project_id"] = project_id
    payload["namespace"] = namespace
    payload["scope"] = {
        "level": "project",
        "scope_id": project_id,
        "parent_scopes": [],
    }
    payload["title"] = title
    payload["content"]["exact"] = content
    payload["content"]["summary"] = f"Summary of {title}."
    payload["source"].update(
        {
            "source_id": source_id,
            "source_kind": "external" if origin_uri else "git_file",
            "path": path,
            "origin_uri": origin_uri,
            "locator": {"line_start": line_start, "line_end": line_end},
            "git_commit": None if origin_uri else "fixture-commit",
            "working_tree_state": None,
            "content_sha256": content_sha256,
        }
    )
    payload["authority"] = {
        "tier": tier.value,
        "trust_class": trust.value,
        "canonical": canonical,
    }
    payload["epistemic"] = {
        "status": "claim" if model_extracted else "source_statement",
        "verification": "model-extracted" if model_extracted else "source-anchored",
        "confidence": 0.6 if model_extracted else None,
    }
    payload["lifecycle"] = {
        "status": status.value,
        "valid_from": valid_from,
        "valid_to": valid_to,
        "supersedes": [],
        "superseded_by": [],
    }
    payload["processing"].update(
        {
            "parsed_by": parsed_by,
            "deterministic_fields": (
                ["title", "source.locator"]
                if model_extracted
                else ["title", "content.exact", "source.locator"]
            ),
            "model_extracted_fields": ["content.exact"] if model_extracted else [],
            "model_id": "fixture-model" if model_extracted else None,
            "prompt_fingerprint": "e" * 64 if model_extracted else None,
            "processed_at": valid_from,
        }
    )
    payload["created_at"] = valid_from
    payload["updated_at"] = valid_from
    return MemoryRecord.model_validate(payload)


def retrieved(
    record: MemoryRecord,
    *,
    exact: float = 0.0,
    lexical: float = 0.0,
    semantic: float = 0.0,
    graph: float = 0.0,
    temporal: float = 0.0,
) -> RetrievedRecord:
    locator = dict(record.source.locator)
    locator["source_revision"] = (
        f"git:{record.source.git_commit}"
        if record.source.git_commit is not None
        else f"sha256:{record.source.content_sha256}"
    )
    return RetrievedRecord(
        record_id=record.record_id,
        record_type=record.record_type,
        title=record.title,
        content=record.content.exact,
        source=RetrievalSource(
            source_id=record.source.source_id,
            path=record.source.path,
            origin_uri=record.source.origin_uri,
            git_commit=record.source.git_commit,
            content_sha256=record.source.content_sha256,
            locator=locator,
        ),
        authority=RetrievalAuthority(
            tier=record.authority.tier,
            trust_class=record.authority.trust_class,
        ),
        lifecycle=RetrievalLifecycle(status=record.lifecycle.status),
        scores=RetrievalScores(
            exact=exact,
            lexical=lexical,
            semantic=semantic,
            graph=graph,
            temporal=temporal,
            authority_boost=0.0,
            trust=0.0,
            freshness=0.0,
            duplicate_penalty=0.0,
            superseded_penalty=0.0,
            scope_distance_penalty=0.0,
            unverified_penalty=0.0,
            final=max(exact, lexical, semantic, graph, temporal),
        ),
        selection_reason=("fixture_exact_channel",),
    )


def provider_candidate(
    record: MemoryRecord,
    *,
    exact: float = 0.0,
    lexical: float = 0.0,
    semantic: float = 0.0,
    graph: float = 0.0,
    temporal: float = 0.0,
) -> ProviderRecallCandidate:
    return ProviderRecallCandidate(
        record=record,
        scores=ProviderChannelScores(
            exact=exact,
            lexical=lexical,
            semantic=semantic,
            graph=graph,
            temporal=temporal,
            final=max(exact, lexical, semantic, graph, temporal),
        ),
        selection_reason=("fixture_provider_match",),
    )


def relation_record(
    relation_id: str,
    source_record_id: str,
    target_record_id: str,
    *,
    state: str,
    confidence: float | None,
) -> RelationRecord:
    payload = deepcopy(RELATION_RECORD)
    payload.update(
        {
            "relation_id": relation_id,
            "project_id": "project-alpha",
            "source_record_id": source_record_id,
            "target_record_id": target_record_id,
        }
    )
    payload["source"] = {
        "source_id": "src_relation_evidence",
        "locator": {"line_start": 20, "line_end": 20},
    }
    payload["validation"] = {"state": state, "confidence": confidence}
    return RelationRecord.model_validate(payload)


class StaticExactBackend:
    def __init__(
        self,
        *,
        exact: tuple[RetrievedRecord, ...] = (),
        lexical: tuple[RetrievedRecord, ...] = (),
        records: tuple[MemoryRecord, ...] = (),
    ) -> None:
        self.exact_results = exact
        self.lexical_results = lexical
        self.records = {record.record_id: record for record in records}
        self.exact_calls = 0
        self.lexical_calls = 0

    def query_exact(
        self,
        *,
        project_id: str,
        query: str,
        case_sensitive: bool = True,
        field: str | None = None,
        current_only: bool = True,
        limit: int = 20,
    ) -> tuple[RetrievedRecord, ...]:
        del project_id, query, case_sensitive, field, current_only
        self.exact_calls += 1
        return self.exact_results[:limit]

    def query_lexical(
        self,
        *,
        project_id: str,
        query: str,
        phrase: bool = False,
        prefix: bool = False,
        field: str | None = None,
        current_only: bool = True,
        limit: int = 20,
    ) -> tuple[RetrievedRecord, ...]:
        del project_id, query, phrase, prefix, field, current_only
        self.lexical_calls += 1
        return self.lexical_results[:limit]

    def resolve_record(
        self,
        *,
        project_id: str,
        record_id: str,
        source_revision: str,
        source_path: str,
    ) -> MemoryRecord | None:
        del source_revision
        record = self.records.get(record_id)
        if record is None:
            return None
        if record.project_id != project_id:
            return None
        if source_path not in {record.source.path, record.source.origin_uri}:
            return None
        return record


class StaticProvider:
    def __init__(
        self,
        candidates: tuple[ProviderRecallCandidate, ...] = (),
        *,
        relations: tuple[RelationRecord, ...] = (),
        omitted: int = 0,
    ) -> None:
        self.candidates = candidates
        self.relations = relations
        self.omitted = omitted
        self.requests: list[RecallRequest] = []

    async def recall(self, request: RecallRequest) -> ProviderRecallResult:
        self.requests.append(request)
        return ProviderRecallResult(
            schema_version=SCHEMA_VERSION,
            api_version=API_VERSION,
            provider_name=ProviderName.IN_MEMORY,
            provider_version=IN_MEMORY_PROVIDER_VERSION,
            request_id=request.request_id,
            project_id=request.context.project_id,
            dataset_id=request.context.dataset_id,
            query=request.query,
            mode=request.mode,
            candidates=self.candidates,
            relations=self.relations,
            omitted_result_count=self.omitted,
            trace_id=request.context.trace_id,
        )


class AllowAuthorizer:
    def __init__(self, *, deny_on_call: int | None = None) -> None:
        self.requests: list[AuthorizationRequest] = []
        self.deny_on_call = deny_on_call

    def require(
        self,
        request: AuthorizationRequest,
        *,
        now: datetime | None = None,
    ) -> AuthorizationDecision:
        del now
        self.requests.append(request)
        if self.deny_on_call == len(self.requests):
            from sys4ai_memory.authorization import PermissionDeniedError

            raise PermissionDeniedError("permission denied: fixture_revocation")
        return AuthorizationDecision(
            allowed=True,
            reason_code="allowed",
            principal_id=request.principal_id,
            project_id=request.project_id,
            dataset_id=request.dataset_id,
            operation=request.operation,
            permission=Permission.READ,
            permission_revision="fixture-revision",
            canonical_sha256="f" * 64,
            grant_id="fixture-read-grant",
        )
