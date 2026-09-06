"""Canonical permission-document and effective-envelope models."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from pathlib import PurePosixPath
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from sys4ai_memory.contracts import MemoryScope, Permission, ScopeReference
from sys4ai_memory.util import ensure_utc


def _validate_relative_prefix(value: str) -> str:
    if not value.strip():
        raise ValueError("target prefix must not be blank")
    if "\\" in value:
        raise ValueError("target prefix must use POSIX separators")
    candidate = PurePosixPath(value)
    if candidate.is_absolute() or any(part in {"", ".", ".."} for part in candidate.parts):
        raise ValueError("target prefix must be a normalized project-relative path")
    return candidate.as_posix().rstrip("/")


class AuthorizationModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, validate_default=True)


class ReviewerKind(StrEnum):
    HUMAN = "human"
    SYSTEM_AUTOMATION = "system-automation"


class ReviewerIdentity(AuthorizationModel):
    principal_id: str = Field(min_length=1, max_length=255)
    kind: ReviewerKind
    higher_system_policy_ref: str | None = None

    @model_validator(mode="after")
    def validate_automation_authority(self) -> Self:
        if self.kind is ReviewerKind.SYSTEM_AUTOMATION and not self.higher_system_policy_ref:
            raise ValueError("automated approval requires a higher system policy reference")
        if self.kind is ReviewerKind.HUMAN and self.higher_system_policy_ref is not None:
            raise ValueError("human reviewer must not claim an automation policy reference")
        return self


class PermissionGrant(AuthorizationModel):
    grant_id: str = Field(min_length=1, max_length=255)
    principal_id: str = Field(min_length=1, max_length=255)
    permissions: frozenset[Permission] = Field(min_length=1)
    operations: frozenset[str] = frozenset()
    scopes: tuple[ScopeReference, ...] = Field(min_length=1)
    target_prefixes: tuple[str, ...] = ()
    shared_project_ids: frozenset[str] = frozenset()
    valid_until: datetime | None = None

    @field_validator("target_prefixes")
    @classmethod
    def validate_target_prefixes(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        normalized = tuple(_validate_relative_prefix(item) for item in value)
        if len(set(normalized)) != len(normalized):
            raise ValueError("target_prefixes must not contain duplicates")
        return normalized

    @field_validator("operations")
    @classmethod
    def validate_operations(cls, value: frozenset[str]) -> frozenset[str]:
        if any(not operation.strip() for operation in value):
            raise ValueError("grant operations must not be blank")
        return value

    @field_validator("valid_until")
    @classmethod
    def validate_valid_until(cls, value: datetime | None) -> datetime | None:
        return None if value is None else ensure_utc(value)

    @model_validator(mode="after")
    def validate_unique_scopes(self) -> Self:
        identities = tuple((scope.level, scope.scope_id) for scope in self.scopes)
        if len(set(identities)) != len(identities):
            raise ValueError("grant scopes must not contain duplicates")
        if any(not project_id.strip() for project_id in self.shared_project_ids):
            raise ValueError("shared project identities must not be blank")
        return self


class ApprovalPolicy(AuthorizationModel):
    status: Literal["approved"]
    policy_id: str = Field(min_length=1, max_length=255)
    reviewers: tuple[ReviewerIdentity, ...] = Field(min_length=1)
    record_types: frozenset[str] = Field(min_length=1)
    target_prefixes: tuple[str, ...] = Field(min_length=1)
    human_review_required: Literal[True] = True
    approvals_required: Literal[1] = 1
    self_approval_allowed: Literal[False] = False

    @model_validator(mode="after")
    def validate_reviewers(self) -> Self:
        principal_ids = tuple(reviewer.principal_id for reviewer in self.reviewers)
        if len(set(principal_ids)) != len(principal_ids):
            raise ValueError("approval reviewers must not contain duplicates")
        if len(self.reviewers) != self.approvals_required:
            raise ValueError("approval policy must name exactly the required reviewers")
        return self

    def reviewer(self, principal_id: str) -> ReviewerIdentity | None:
        return next(
            (reviewer for reviewer in self.reviewers if reviewer.principal_id == principal_id),
            None,
        )

    @field_validator("target_prefixes")
    @classmethod
    def validate_target_prefixes(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        normalized = tuple(_validate_relative_prefix(item) for item in value)
        if len(set(normalized)) != len(normalized):
            raise ValueError("approval target_prefixes must not contain duplicates")
        return normalized


class CanonicalPermissionDocument(AuthorizationModel):
    schema_version: Literal["1.0"]
    revision: str = Field(min_length=1, max_length=255)
    project_id: str = Field(min_length=1, max_length=255)
    dataset_id: str = Field(min_length=1, max_length=255)
    issued_at: datetime
    grants: tuple[PermissionGrant, ...]
    approval_policy: ApprovalPolicy | None = None

    @field_validator("issued_at")
    @classmethod
    def validate_issued_at(cls, value: datetime) -> datetime:
        return ensure_utc(value)

    @model_validator(mode="after")
    def validate_document(self) -> Self:
        grant_ids = tuple(grant.grant_id for grant in self.grants)
        if len(set(grant_ids)) != len(grant_ids):
            raise ValueError("grant_id values must be unique")
        for grant in self.grants:
            for scope in grant.scopes:
                all_scopes = (scope, *scope.parent_scopes)
                for item in all_scopes:
                    if item.level is MemoryScope.PROJECT and item.scope_id != self.project_id:
                        raise ValueError("grant scope crosses the permission document project")
        return self


class PermissionSnapshot(AuthorizationModel):
    document: CanonicalPermissionDocument
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_path: str = Field(min_length=1)


class PermissionEnvelope(AuthorizationModel):
    """Effective grants reread from one canonical permission document."""

    principal_id: str
    project_id: str
    dataset_id: str
    revision: str
    canonical_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    grants: tuple[PermissionGrant, ...]


class AuthorizationRequest(AuthorizationModel):
    principal_id: str = Field(min_length=1, max_length=255)
    project_id: str = Field(min_length=1, max_length=255)
    dataset_id: str = Field(min_length=1, max_length=255)
    operation: str = Field(min_length=1, max_length=255)
    permission: Permission
    scope: ScopeReference
    target_path: str | None = None
    query_project_ids: tuple[str, ...] = ()
    explicit_cross_project: bool = False
    trace_id: str = Field(min_length=1, max_length=255)
    require_action_specific: bool = False

    @field_validator("target_path")
    @classmethod
    def validate_target_path(cls, value: str | None) -> str | None:
        return None if value is None else _validate_relative_prefix(value)

    @model_validator(mode="after")
    def validate_query_scope(self) -> Self:
        if len(set(self.query_project_ids)) != len(self.query_project_ids):
            raise ValueError("query_project_ids must not contain duplicates")
        return self


class AuthorizationDecision(AuthorizationModel):
    allowed: bool
    reason_code: str
    principal_id: str
    project_id: str
    dataset_id: str
    operation: str
    permission: Permission
    permission_revision: str | None
    canonical_sha256: str | None
    grant_id: str | None
