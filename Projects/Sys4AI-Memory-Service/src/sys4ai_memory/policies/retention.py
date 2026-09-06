"""Short-lived session and episodic stores with explicit retention gates."""

from __future__ import annotations

from datetime import datetime, timedelta
from threading import RLock
from typing import Literal, Protocol, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from sys4ai_memory.contracts import AuthorityTier, ScopeReference, TrustClass
from sys4ai_memory.security import (
    IdempotencyConflictError,
    PolicyDisabledError,
    require_secret_free,
)
from sys4ai_memory.util import ensure_utc, utc_now


class RetentionModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, validate_default=True)


class RetentionPolicy(RetentionModel):
    status: Literal["approved", "pending-user-decision"]
    policy_id: str | None = None
    session_ttl_seconds: int | None = Field(default=None, gt=0)
    episodic_ttl_seconds: int | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def validate_decision(self) -> Self:
        values = (self.policy_id, self.session_ttl_seconds, self.episodic_ttl_seconds)
        if self.status == "approved" and any(value is None for value in values):
            raise ValueError("approved retention requires a policy ID and both TTL values")
        if self.status != "approved" and any(value is not None for value in values):
            raise ValueError("pending retention cannot invent policy IDs or durations")
        return self


APPROVED_LOCAL_RETENTION_POLICY = RetentionPolicy(
    status="approved",
    policy_id="retention-72h-365d@1",
    session_ttl_seconds=72 * 60 * 60,
    episodic_ttl_seconds=365 * 24 * 60 * 60,
)


class SessionEntry(RetentionModel):
    entry_id: str
    project_id: str
    session_id: str
    scope: ScopeReference
    content: object
    created_at: datetime
    expires_at: datetime
    authority_tier: Literal[AuthorityTier.SESSION_SCRATCH] = AuthorityTier.SESSION_SCRATCH
    trust_class: TrustClass
    durable_authority: Literal[False] = False

    @model_validator(mode="after")
    def validate_session(self) -> Self:
        created = ensure_utc(self.created_at)
        expires = ensure_utc(self.expires_at)
        if expires <= created:
            raise ValueError("session expiration must follow creation")
        if self.scope.level.value != "session" or self.scope.scope_id != self.session_id:
            raise ValueError("session entry requires its exact session scope")
        require_secret_free(self.content, field_path="session.content")
        return self


class EpisodicEntry(RetentionModel):
    episode_id: str
    project_id: str
    task_id: str
    actor_id: str
    started_at: datetime
    completed_at: datetime
    tools: tuple[str, ...]
    input_refs: tuple[str, ...]
    output_refs: tuple[str, ...]
    outcome: str
    related_record_ids: tuple[str, ...]
    rationale_summary: str = Field(max_length=2000)
    evidence_refs: tuple[str, ...]
    expires_at: datetime
    authority_tier: Literal[AuthorityTier.AGENT_DURABLE_MATERIAL] = (
        AuthorityTier.AGENT_DURABLE_MATERIAL
    )
    trust_class: Literal[TrustClass.AGENT_GENERATED] = TrustClass.AGENT_GENERATED
    durable_authority: Literal[False] = False

    @model_validator(mode="after")
    def validate_episode(self) -> Self:
        started = ensure_utc(self.started_at)
        completed = ensure_utc(self.completed_at)
        expires = ensure_utc(self.expires_at)
        if completed < started:
            raise ValueError("episode completion cannot precede its start")
        if expires <= completed:
            raise ValueError("episode expiration must follow completion")
        if not self.task_id.strip() or not self.actor_id.strip() or not self.outcome.strip():
            raise ValueError("episode task, actor, and outcome must not be blank")
        if not self.evidence_refs:
            raise ValueError("episode requires referenced evidence")
        require_secret_free(
            {
                "actor_id": self.actor_id,
                "tools": self.tools,
                "input_refs": self.input_refs,
                "output_refs": self.output_refs,
                "outcome": self.outcome,
                "related_record_ids": self.related_record_ids,
                "rationale_summary": self.rationale_summary,
                "evidence_refs": self.evidence_refs,
            },
            field_path="episode",
        )
        return self


class SessionPersistence(Protocol):
    def save(self, entry: SessionEntry) -> None: ...

    def delete(self, entry_ids: tuple[str, ...]) -> None: ...


class EpisodicPersistence(Protocol):
    def save(self, entry: EpisodicEntry) -> None: ...

    def delete(self, episode_ids: tuple[str, ...]) -> None: ...


def _approved_policy(policy: RetentionPolicy | None) -> RetentionPolicy:
    if policy is None or policy.status != "approved":
        raise PolicyDisabledError("durable retention is disabled until policy is approved")
    return policy


class SessionMemoryStore:
    """Thread-safe TTL session state; optional persistence is explicitly gated."""

    def __init__(
        self,
        *,
        retention_policy: RetentionPolicy | None = None,
        persistence: SessionPersistence | None = None,
    ) -> None:
        if persistence is not None:
            _approved_policy(retention_policy)
        self._retention_policy = retention_policy
        self._persistence = persistence
        self._entries: dict[str, SessionEntry] = {}
        self._lock = RLock()

    @property
    def durable_enabled(self) -> bool:
        return self._persistence is not None

    def put(self, entry: SessionEntry) -> None:
        policy = self._retention_policy
        if self._persistence is not None:
            approved = _approved_policy(policy)
            assert approved.session_ttl_seconds is not None
            if entry.expires_at - entry.created_at > timedelta(
                seconds=approved.session_ttl_seconds
            ):
                raise ValueError("session expiration exceeds the approved retention TTL")
        with self._lock:
            existing = self._entries.get(entry.entry_id)
            if existing is not None:
                if existing != entry:
                    raise IdempotencyConflictError(
                        "session entry ID already identifies different content"
                    )
                return
            if self._persistence is not None:
                self._persistence.save(entry)
            self._entries[entry.entry_id] = entry

    def get(self, entry_id: str, *, now: datetime | None = None) -> SessionEntry | None:
        effective_now = ensure_utc(now or utc_now())
        with self._lock:
            entry = self._entries.get(entry_id)
            if entry is None:
                return None
            if entry.expires_at <= effective_now:
                self._delete_ids((entry_id,))
                return None
            return entry

    def purge_expired(self, *, now: datetime | None = None) -> tuple[str, ...]:
        effective_now = ensure_utc(now or utc_now())
        with self._lock:
            expired = tuple(
                sorted(
                    entry_id
                    for entry_id, entry in self._entries.items()
                    if entry.expires_at <= effective_now
                )
            )
            self._delete_ids(expired)
            return expired

    def delete_session(self, session_id: str) -> tuple[str, ...]:
        """Delete only entries in the session store; canonical memory is untouched."""

        with self._lock:
            selected = tuple(
                sorted(
                    entry_id
                    for entry_id, entry in self._entries.items()
                    if entry.session_id == session_id
                )
            )
            self._delete_ids(selected)
            return selected

    def _delete_ids(self, entry_ids: tuple[str, ...]) -> None:
        if entry_ids and self._persistence is not None:
            self._persistence.delete(entry_ids)
        for entry_id in entry_ids:
            self._entries.pop(entry_id, None)


class EpisodicMemoryStore:
    """Event records containing concise rationale and references, not hidden reasoning."""

    def __init__(
        self,
        *,
        retention_policy: RetentionPolicy | None = None,
        persistence: EpisodicPersistence | None = None,
    ) -> None:
        if persistence is not None:
            _approved_policy(retention_policy)
        self._retention_policy = retention_policy
        self._persistence = persistence
        self._entries: dict[str, EpisodicEntry] = {}
        self._lock = RLock()

    @property
    def durable_enabled(self) -> bool:
        return self._persistence is not None

    def record(self, entry: EpisodicEntry) -> None:
        if self._persistence is not None:
            approved = _approved_policy(self._retention_policy)
            assert approved.episodic_ttl_seconds is not None
            if entry.expires_at - entry.completed_at > timedelta(
                seconds=approved.episodic_ttl_seconds
            ):
                raise ValueError("episode expiration exceeds the approved retention TTL")
        with self._lock:
            existing = self._entries.get(entry.episode_id)
            if existing is not None:
                if existing != entry:
                    raise IdempotencyConflictError(
                        "episode ID already identifies different content"
                    )
                return
            if self._persistence is not None:
                self._persistence.save(entry)
            self._entries[entry.episode_id] = entry

    def get(self, episode_id: str, *, now: datetime | None = None) -> EpisodicEntry | None:
        effective_now = ensure_utc(now or utc_now())
        with self._lock:
            entry = self._entries.get(episode_id)
            if entry is None:
                return None
            if entry.expires_at <= effective_now:
                self._delete_ids((episode_id,))
                return None
            return entry

    def purge_expired(self, *, now: datetime | None = None) -> tuple[str, ...]:
        effective_now = ensure_utc(now or utc_now())
        with self._lock:
            expired = tuple(
                sorted(
                    episode_id
                    for episode_id, entry in self._entries.items()
                    if entry.expires_at <= effective_now
                )
            )
            self._delete_ids(expired)
            return expired

    def _delete_ids(self, episode_ids: tuple[str, ...]) -> None:
        if episode_ids and self._persistence is not None:
            self._persistence.delete(episode_ids)
        for episode_id in episode_ids:
            self._entries.pop(episode_id, None)
