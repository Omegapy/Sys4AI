"""Atomic proposal staging, review authorization, and promotion planning."""

from __future__ import annotations

import difflib
import json
import os
import shutil
import tempfile
from collections.abc import Callable
from datetime import datetime
from enum import StrEnum
from pathlib import Path, PurePosixPath
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from sys4ai_memory.authorization import (
    ApprovalPolicy,
    AuthorizationRequest,
    AuthorizationService,
    CanonicalPermissionEnvelopeLoader,
    PermissionDeniedError,
    ReviewerKind,
)
from sys4ai_memory.contracts import (
    Permission,
    PolicyAction,
    RecordStatus,
    ScopeReference,
    WriteProposal,
)
from sys4ai_memory.security import (
    AuditEvent,
    AuditSink,
    IdempotencyConflictError,
    InMemoryAuditSink,
    PolicyDisabledError,
    ProjectBoundary,
    StaleStateError,
    require_secret_free,
)
from sys4ai_memory.security.locks import exclusive_file_lock
from sys4ai_memory.util import (
    atomic_write_text,
    canonical_json_bytes,
    ensure_utc,
    sha256_bytes,
    utc_now,
)


class StagingModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, arbitrary_types_allowed=True)


class StagedProposalArtifact(StagingModel):
    proposal_id: str = Field(pattern=r"^mwp_[A-Za-z0-9][A-Za-z0-9_.:@-]*$")
    proposal_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    staging_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    base_content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    proposed_content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    patch_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    requester_id: str = Field(min_length=1, max_length=255)
    target_path: str
    artifact_directory: str
    proposal_json_path: str
    patch_path: str
    human_review_path: str
    created: bool


class ReviewDisposition(StrEnum):
    APPROVED = "approved"
    REJECTED = "rejected"


class ReviewReceipt(StagingModel):
    proposal_id: str = Field(pattern=r"^mwp_[A-Za-z0-9][A-Za-z0-9_.:@-]*$")
    proposal_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    reviewer_id: str
    reviewer_kind: ReviewerKind
    higher_system_policy_ref: str | None
    disposition: ReviewDisposition
    rationale_summary: str
    policy_id: str
    permission_revision: str
    permission_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    reviewed_at: datetime

    @model_validator(mode="after")
    def validate_time(self) -> ReviewReceipt:
        ensure_utc(self.reviewed_at)
        return self


class RejectedMetadataField(StrEnum):
    """Non-content proposal metadata that an approved retention policy may select."""

    PROPOSAL_ID = "proposal_id"
    PROPOSAL_DIGEST = "proposal_digest"
    REVIEWER_ID = "reviewer_id"
    REVIEWER_KIND = "reviewer_kind"
    REVIEW_POLICY_ID = "review_policy_id"
    PERMISSION_REVISION = "permission_revision"
    PERMISSION_SHA256 = "permission_sha256"
    REVIEWED_AT = "reviewed_at"


class RejectedProposalRetentionPolicy(StagingModel):
    """Explicit metadata allowlist; unresolved policy retains no proposal data."""

    status: Literal["approved", "pending-user-decision"]
    policy_id: str | None = None
    retained_fields: frozenset[RejectedMetadataField] = frozenset()
    retain_until: datetime | None = None

    @model_validator(mode="after")
    def validate_policy(self) -> Self:
        if self.status == "pending-user-decision":
            if self.policy_id is not None or self.retained_fields or self.retain_until is not None:
                raise ValueError("pending rejection retention cannot retain metadata")
            return self
        if not self.policy_id or not self.policy_id.strip():
            raise ValueError("approved rejection retention requires a policy ID")
        if bool(self.retained_fields) != (self.retain_until is not None):
            raise ValueError(
                "retained rejection metadata requires explicit fields and a retention deadline"
            )
        if self.retain_until is not None:
            ensure_utc(self.retain_until)
        return self


class RejectedProposalDispositionReceipt(StagingModel):
    proposal_id: str = Field(pattern=r"^mwp_[A-Za-z0-9][A-Za-z0-9_.:@-]*$")
    proposal_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    disposition: Literal[ReviewDisposition.REJECTED] = ReviewDisposition.REJECTED
    retention_policy_id: str | None
    retained_fields: tuple[RejectedMetadataField, ...]
    retained_metadata_path: str | None
    proposal_content_removed: Literal[True] = True
    active_knowledge: Literal[False] = False


class CanonicalPromotionRequest(StagingModel):
    """A normal-project-change artifact; it never edits the canonical target."""

    proposal_id: str = Field(pattern=r"^mwp_[A-Za-z0-9][A-Za-z0-9_.:@-]*$")
    proposal_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    target_path: str
    unified_patch: str
    base_content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    proposed_content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    reviewer_id: str
    reviewer_kind: ReviewerKind
    higher_system_policy_ref: str | None
    review_policy_id: str
    policy_action: Literal[PolicyAction.CANONICAL_PROMOTION] = PolicyAction.CANONICAL_PROMOTION
    permission_revision: str
    permission_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    requires_governed_project_workflow: Literal[True] = True
    canonical_write_performed: Literal[False] = False
    synchronize_after_accepted_write: Literal[True] = True


def _render_content(value: object) -> str:
    if isinstance(value, str):
        return value if value.endswith("\n") else value + "\n"
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def _unified_patch(target_path: str, before: str, after: str) -> str:
    return "".join(
        difflib.unified_diff(
            before.splitlines(keepends=True),
            after.splitlines(keepends=True),
            fromfile=f"a/{target_path}",
            tofile=f"b/{target_path}",
        )
    )


class ProposalStager:
    """Serialize idempotent proposals through an atomically published directory."""

    def __init__(
        self,
        boundary: ProjectBoundary,
        staging_root: str,
        authorization: AuthorizationService,
        *,
        audit: AuditSink | None = None,
    ) -> None:
        self._boundary = boundary
        self._root_relative = PurePosixPath(staging_root).as_posix()
        self._root = boundary.resolve_path(staging_root, must_exist=False)
        relative_root = PurePosixPath(self._root_relative)
        lock_name = f".{relative_root.name}.lock"
        self._lock_relative = (
            lock_name
            if relative_root.parent == PurePosixPath(".")
            else (relative_root.parent / lock_name).as_posix()
        )
        self._authorization = authorization
        self._audit = audit or InMemoryAuditSink()

    def stage(
        self,
        proposal: WriteProposal,
        *,
        trace_id: str,
        base_content: str | None = None,
    ) -> StagedProposalArtifact:
        if proposal.status is not RecordStatus.STAGED:
            raise ValueError("only staged proposals can be persisted for review")
        if proposal.policy_result.action.value != "stage_for_review":
            raise ValueError("staged proposal requires a stage-for-review policy decision")
        if proposal.project_id != self._boundary.project_id:
            raise ValueError("proposal project does not match the staging boundary")
        self._boundary.resolve_path(proposal.requested_target.path, must_exist=False)
        require_secret_free(proposal.to_json_dict(), field_path="proposal")
        authorization = self._authorization.require(
            AuthorizationRequest(
                principal_id=proposal.requester.principal_id,
                project_id=proposal.project_id,
                dataset_id=self._boundary.dataset_id,
                operation="memory.propose",
                permission=Permission.PROPOSE,
                scope=proposal.requested_scope,
                target_path=proposal.requested_target.path,
                trace_id=trace_id,
            )
        )

        before = self._canonical_before(proposal.requested_target.path, base_content)
        after = _render_content(proposal.proposal.content)
        patch = _unified_patch(proposal.requested_target.path, before, after)
        proposal_bytes = proposal.to_stable_json().encode("utf-8")
        proposal_digest = sha256_bytes(proposal_bytes)
        base_digest = sha256_bytes(before.encode("utf-8"))
        proposed_content_digest = sha256_bytes(after.encode("utf-8"))
        patch_digest = sha256_bytes(patch.encode("utf-8"))
        staging_digest = sha256_bytes(
            canonical_json_bytes(
                {
                    "proposal_digest": proposal_digest,
                    "base_content_sha256": base_digest,
                    "proposed_content_sha256": proposed_content_digest,
                    "patch_sha256": patch_digest,
                }
            )
        )
        key_digest = sha256_bytes(proposal.idempotency_key.encode("utf-8"))

        self._root.mkdir(parents=True, exist_ok=True)
        self._root = self._boundary.resolve_path(self._root_relative)
        idempotency_relative = f"{self._root_relative}/.idempotency"
        idempotency_root = self._boundary.resolve_path(
            idempotency_relative,
            must_exist=False,
        )
        idempotency_root.mkdir(mode=0o700, exist_ok=True)
        idempotency_root = self._boundary.resolve_path(idempotency_relative)
        lock_path = self._boundary.resolve_path(self._lock_relative, must_exist=False)
        with exclusive_file_lock(lock_path):
            mapping_path = idempotency_root / f"{key_digest}.json"
            if mapping_path.exists():
                if mapping_path.is_symlink() or not mapping_path.is_file():
                    raise StaleStateError("invalid idempotency metadata path")
                mapping = json.loads(mapping_path.read_text(encoding="utf-8"))
                if mapping.get("staging_digest") != staging_digest:
                    raise IdempotencyConflictError(
                        "idempotency key already identifies a different staged request"
                    )
                artifact = self._load_artifact(str(mapping["proposal_id"]), created=False)
                self._record_audit(
                    proposal,
                    artifact,
                    authorization.permission_revision,
                    trace_id,
                )
                return artifact

            final_directory = self._root / proposal.proposal_id
            if final_directory.exists():
                existing = self._load_artifact(proposal.proposal_id, created=False)
                if existing.staging_digest != staging_digest:
                    raise IdempotencyConflictError(
                        "proposal ID already identifies different staged content"
                    )
            else:
                self._publish_directory(
                    final_directory,
                    proposal,
                    patch,
                    proposal_digest,
                    staging_digest,
                    base_digest,
                    proposed_content_digest,
                    patch_digest,
                )
            atomic_write_text(
                mapping_path,
                json.dumps(
                    {"proposal_id": proposal.proposal_id, "staging_digest": staging_digest},
                    sort_keys=True,
                    separators=(",", ":"),
                )
                + "\n",
            )
            artifact = self._load_artifact(proposal.proposal_id, created=True)
            self._record_audit(
                proposal,
                artifact,
                authorization.permission_revision,
                trace_id,
            )
            return artifact

    def discard_rejected(
        self,
        artifact: StagedProposalArtifact,
        review: ReviewReceipt,
    ) -> None:
        """Remove all rejected proposal data while retention policy is unresolved."""

        self.dispose_rejected(artifact, review)

    def dispose_rejected(
        self,
        artifact: StagedProposalArtifact,
        review: ReviewReceipt,
        *,
        retention_policy: RejectedProposalRetentionPolicy | None = None,
    ) -> RejectedProposalDispositionReceipt:
        """Remove proposal content and keep only an approved metadata projection."""

        if review.disposition is not ReviewDisposition.REJECTED:
            raise ValueError("only rejected proposals can be discarded")
        if (
            review.proposal_id != artifact.proposal_id
            or review.proposal_digest != artifact.proposal_digest
        ):
            raise StaleStateError("review does not identify the staged proposal")
        expected_directory = f"{self._root_relative}/{artifact.proposal_id}"
        if artifact.artifact_directory != expected_directory:
            raise StaleStateError("staged artifact is outside the proposal staging root")
        policy = retention_policy or RejectedProposalRetentionPolicy(status="pending-user-decision")
        if (
            policy.status == "approved"
            and policy.retain_until is not None
            and policy.retain_until <= review.reviewed_at
        ):
            raise ValueError("rejection metadata retention must end after review")
        retained = self._rejected_metadata(review, policy.retained_fields)
        require_secret_free(retained, field_path="rejected_proposal.metadata")
        lock_path = self._boundary.resolve_path(self._lock_relative, must_exist=False)
        with exclusive_file_lock(lock_path):
            directory = self._boundary.resolve_path(
                artifact.artifact_directory,
                must_exist=False,
            )
            quarantine_relative = f"{self._root_relative}/.discard-{artifact.proposal_id}"
            quarantine = self._boundary.resolve_path(
                quarantine_relative,
                must_exist=False,
            )
            rejected_relative = f"{self._root_relative}/.rejected/{artifact.proposal_id}.json"
            rejected_path = self._boundary.resolve_path(
                rejected_relative,
                must_exist=False,
            )
            retained_path: str | None = None
            if retained:
                assert policy.policy_id is not None
                assert policy.retain_until is not None
                payload = {
                    "schema_version": "1.0",
                    "retention_policy_id": policy.policy_id,
                    "retain_until": policy.retain_until.isoformat().replace("+00:00", "Z"),
                    "active_knowledge": False,
                    "metadata": retained,
                }
                serialized = json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n"
                if rejected_path.exists():
                    if (
                        not rejected_path.is_file()
                        or rejected_path.read_text(encoding="utf-8") != serialized
                    ):
                        raise IdempotencyConflictError(
                            "rejected proposal metadata conflicts with prior disposition"
                        )
                else:
                    atomic_write_text(rejected_path, serialized)
                retained_path = rejected_relative
            elif rejected_path.exists():
                if not rejected_path.is_file():
                    raise StaleStateError("invalid rejected proposal metadata path")
                rejected_path.unlink()

            if quarantine.exists():
                if not quarantine.is_dir():
                    raise StaleStateError("invalid rejected proposal quarantine path")
                shutil.rmtree(quarantine)
            if directory.exists():
                if not directory.is_dir():
                    raise StaleStateError("invalid staged proposal artifact path")
                os.replace(directory, quarantine)
            if quarantine.exists():
                shutil.rmtree(quarantine)
            self._remove_idempotency_mappings(artifact.proposal_id)
            rejected_root = rejected_path.parent
            if not retained and rejected_root.exists() and not any(rejected_root.iterdir()):
                rejected_root.rmdir()
        return RejectedProposalDispositionReceipt(
            proposal_id=artifact.proposal_id,
            proposal_digest=artifact.proposal_digest,
            retention_policy_id=policy.policy_id,
            retained_fields=tuple(sorted(policy.retained_fields, key=lambda item: item.value)),
            retained_metadata_path=retained_path,
        )

    def _remove_idempotency_mappings(self, proposal_id: str) -> None:
        idempotency_root = self._root / ".idempotency"
        if not idempotency_root.exists():
            return
        for mapping_path in idempotency_root.glob("*.json"):
            if mapping_path.is_symlink() or not mapping_path.is_file():
                raise StaleStateError("invalid idempotency metadata path")
            mapping = json.loads(mapping_path.read_text(encoding="utf-8"))
            if mapping.get("proposal_id") == proposal_id:
                mapping_path.unlink()

    @staticmethod
    def _rejected_metadata(
        review: ReviewReceipt,
        retained_fields: frozenset[RejectedMetadataField],
    ) -> dict[str, str]:
        values = {
            RejectedMetadataField.PROPOSAL_ID: review.proposal_id,
            RejectedMetadataField.PROPOSAL_DIGEST: review.proposal_digest,
            RejectedMetadataField.REVIEWER_ID: review.reviewer_id,
            RejectedMetadataField.REVIEWER_KIND: review.reviewer_kind.value,
            RejectedMetadataField.REVIEW_POLICY_ID: review.policy_id,
            RejectedMetadataField.PERMISSION_REVISION: review.permission_revision,
            RejectedMetadataField.PERMISSION_SHA256: review.permission_sha256,
            RejectedMetadataField.REVIEWED_AT: review.reviewed_at.isoformat().replace(
                "+00:00", "Z"
            ),
        }
        return {
            field.value: values[field]
            for field in sorted(retained_fields, key=lambda item: item.value)
        }

    def _canonical_before(self, target_path: str, supplied: str | None) -> str:
        if supplied is not None:
            return supplied
        candidate = self._boundary.resolve_path(target_path, must_exist=False)
        if not candidate.exists():
            return ""
        if not candidate.is_file():
            raise ValueError("canonical proposal target must be a regular file")
        return candidate.read_text(encoding="utf-8")

    def _publish_directory(
        self,
        final_directory: Path,
        proposal: WriteProposal,
        patch: str,
        proposal_digest: str,
        staging_digest: str,
        base_digest: str,
        proposed_content_digest: str,
        patch_digest: str,
    ) -> None:
        temporary = Path(tempfile.mkdtemp(prefix=".proposal-", dir=self._root))
        try:
            atomic_write_text(temporary / "proposal.json", proposal.to_stable_json() + "\n")
            atomic_write_text(temporary / "proposal.patch", patch)
            review = self._render_review(proposal, patch, proposal_digest, base_digest)
            atomic_write_text(temporary / "REVIEW.md", review)
            metadata = {
                "proposal_id": proposal.proposal_id,
                "proposal_digest": proposal_digest,
                "staging_digest": staging_digest,
                "base_content_sha256": base_digest,
                "proposed_content_sha256": proposed_content_digest,
                "patch_sha256": patch_digest,
                "target_path": proposal.requested_target.path,
                "requester_id": proposal.requester.principal_id,
            }
            atomic_write_text(
                temporary / "metadata.json",
                json.dumps(metadata, sort_keys=True, separators=(",", ":")) + "\n",
            )
            os.replace(temporary, final_directory)
        except BaseException:
            shutil.rmtree(temporary, ignore_errors=True)
            raise

    @staticmethod
    def _render_review(
        proposal: WriteProposal,
        patch: str,
        proposal_digest: str,
        base_digest: str,
    ) -> str:
        evidence = "\n".join(
            f"- `{item.record_id or item.source_id}`" for item in proposal.evidence
        )
        reasons = "\n".join(f"- {reason}" for reason in proposal.policy_result.reasons)
        scope_label = f"{proposal.requested_scope.level.value}:{proposal.requested_scope.scope_id}"
        policy_label = f"{proposal.policy_result.policy_id} / {proposal.policy_result.action.value}"
        return (
            f"# Memory write proposal {proposal.proposal_id}\n\n"
            f"- Target: `{proposal.requested_target.path}`\n"
            f"- Type: `{proposal.requested_record_type}`\n"
            f"- Scope: `{scope_label}`\n"
            f"- Policy: `{policy_label}`\n"
            f"- Proposal SHA-256: `{proposal_digest}`\n"
            f"- Base SHA-256: `{base_digest}`\n\n"
            f"## Policy reasons\n\n{reasons}\n\n"
            f"## Evidence\n\n{evidence}\n\n"
            f"## Proposed diff\n\n```diff\n{patch}```\n"
        )

    def _load_artifact(self, proposal_id: str, *, created: bool) -> StagedProposalArtifact:
        if not proposal_id or PurePosixPath(proposal_id).name != proposal_id:
            raise ValueError("invalid proposal ID")
        directory = self._boundary.resolve_path(f"{self._root_relative}/{proposal_id}")
        metadata_path = self._boundary.resolve_path(
            f"{self._root_relative}/{proposal_id}/metadata.json"
        )
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        relative_directory = directory.relative_to(self._boundary.root.resolve()).as_posix()
        return StagedProposalArtifact(
            **metadata,
            artifact_directory=relative_directory,
            proposal_json_path=f"{relative_directory}/proposal.json",
            patch_path=f"{relative_directory}/proposal.patch",
            human_review_path=f"{relative_directory}/REVIEW.md",
            created=created,
        )

    def _record_audit(
        self,
        proposal: WriteProposal,
        artifact: StagedProposalArtifact,
        permission_revision: str | None,
        trace_id: str,
    ) -> None:
        self._audit.record(
            AuditEvent(
                event_id=f"{proposal.proposal_id}:stage",
                occurred_at=utc_now(),
                principal_id=proposal.requester.principal_id,
                project_id=proposal.project_id,
                dataset_id=self._boundary.dataset_id,
                operation="memory.propose.stage",
                target_ids=(proposal.proposal_id,),
                policy_decision=proposal.policy_result.action.value,
                outcome="created" if artifact.created else "idempotent",
                trace_id=trace_id,
                policy_id=proposal.policy_result.policy_id,
                permission_revision=permission_revision,
                counts=(("proposals", 1),),
            )
        )


def _prefix_allows(target_path: str, prefixes: tuple[str, ...]) -> bool:
    target = PurePosixPath(target_path)
    return any(
        target == PurePosixPath(prefix) or PurePosixPath(prefix) in target.parents
        for prefix in prefixes
    )


class ReviewerAuthorizationGate:
    """Authorize a reviewer only from a freshly reread canonical document."""

    def __init__(
        self,
        authorization: AuthorizationService,
        loader: CanonicalPermissionEnvelopeLoader,
        *,
        audit: AuditSink | None = None,
    ) -> None:
        self._authorization = authorization
        self._loader = loader
        self._audit = audit or InMemoryAuditSink()

    def require_reviewer(
        self,
        *,
        reviewer_id: str,
        project_id: str,
        dataset_id: str,
        scope: ScopeReference,
        target_path: str,
        record_type: str,
        trace_id: str,
    ) -> tuple[str, str, ApprovalPolicy]:
        decision = self._authorization.require(
            AuthorizationRequest(
                principal_id=reviewer_id,
                project_id=project_id,
                dataset_id=dataset_id,
                operation="memory.approve",
                permission=Permission.APPROVE,
                scope=scope,
                target_path=target_path,
                trace_id=trace_id,
                require_action_specific=True,
            )
        )
        snapshot = self._loader.load_snapshot()
        if (
            decision.permission_revision != snapshot.document.revision
            or decision.canonical_sha256 != snapshot.content_sha256
        ):
            raise StaleStateError("canonical permission changed during reviewer authorization")
        policy = snapshot.document.approval_policy
        if policy is None:
            raise PolicyDisabledError("canonical reviewer policy is unresolved")
        reviewer = policy.reviewer(reviewer_id)
        if reviewer is None:
            raise PermissionDeniedError("reviewer is not named by the canonical approval policy")
        if record_type not in policy.record_types:
            raise PermissionDeniedError("reviewer policy does not cover the proposal record type")
        if not _prefix_allows(target_path, policy.target_prefixes):
            raise PermissionDeniedError("reviewer policy does not cover the proposal target")
        return snapshot.document.revision, snapshot.content_sha256, policy

    def decide(
        self,
        artifact: StagedProposalArtifact,
        *,
        reviewer_id: str,
        project_id: str,
        dataset_id: str,
        scope: ScopeReference,
        record_type: str,
        disposition: ReviewDisposition,
        rationale_summary: str,
        trace_id: str,
        reviewed_at: datetime | None = None,
    ) -> ReviewReceipt:
        require_secret_free(rationale_summary, field_path="review.rationale_summary")
        if not rationale_summary.strip():
            raise ValueError("review rationale must not be blank")
        if disposition is ReviewDisposition.APPROVED and reviewer_id == artifact.requester_id:
            raise PermissionDeniedError("a proposal requester cannot approve its own proposal")
        revision, content_sha256, policy = self.require_reviewer(
            reviewer_id=reviewer_id,
            project_id=project_id,
            dataset_id=dataset_id,
            scope=scope,
            target_path=artifact.target_path,
            record_type=record_type,
            trace_id=trace_id,
        )
        reviewer = policy.reviewer(reviewer_id)
        if reviewer is None:
            raise PermissionDeniedError("reviewer is not named by the canonical approval policy")
        timestamp = reviewed_at or utc_now()
        receipt = ReviewReceipt(
            proposal_id=artifact.proposal_id,
            proposal_digest=artifact.proposal_digest,
            reviewer_id=reviewer_id,
            reviewer_kind=reviewer.kind,
            higher_system_policy_ref=reviewer.higher_system_policy_ref,
            disposition=disposition,
            rationale_summary=rationale_summary,
            policy_id=policy.policy_id,
            permission_revision=revision,
            permission_sha256=content_sha256,
            reviewed_at=timestamp,
        )
        self._audit.record(
            AuditEvent(
                event_id=f"{artifact.proposal_id}:review:{reviewer_id}",
                occurred_at=timestamp,
                principal_id=reviewer_id,
                project_id=project_id,
                dataset_id=dataset_id,
                operation="memory.approve",
                target_ids=(artifact.proposal_id,),
                policy_decision=disposition.value,
                outcome=disposition.value,
                trace_id=trace_id,
                policy_id=policy.policy_id,
                permission_revision=revision,
                counts=(("proposals", 1),),
            )
        )
        return receipt


class CanonicalPromotionPlanner:
    """Create a governed change request after a fresh reviewer and target reread."""

    def __init__(self, boundary: ProjectBoundary, gate: ReviewerAuthorizationGate) -> None:
        self._boundary = boundary
        self._gate = gate

    def create_request(
        self,
        artifact: StagedProposalArtifact,
        review: ReviewReceipt,
        *,
        project_id: str,
        dataset_id: str,
        scope: ScopeReference,
        record_type: str,
        trace_id: str,
        canonical_reader: Callable[[str], str | None] | None = None,
    ) -> CanonicalPromotionRequest:
        if review.disposition is not ReviewDisposition.APPROVED:
            raise PermissionDeniedError("a rejected proposal cannot request promotion")
        if (
            review.proposal_id != artifact.proposal_id
            or review.proposal_digest != artifact.proposal_digest
        ):
            raise StaleStateError("review does not identify the staged proposal digest")
        if review.reviewer_id == artifact.requester_id:
            raise PermissionDeniedError("a proposal requester cannot approve its own proposal")
        revision, content_sha256, policy = self._gate.require_reviewer(
            reviewer_id=review.reviewer_id,
            project_id=project_id,
            dataset_id=dataset_id,
            scope=scope,
            target_path=artifact.target_path,
            record_type=record_type,
            trace_id=trace_id,
        )
        if (
            review.permission_revision != revision
            or review.permission_sha256 != content_sha256
            or review.policy_id != policy.policy_id
        ):
            raise StaleStateError("review authorization changed before promotion")
        current = self._read_current(artifact.target_path, canonical_reader)
        if sha256_bytes(current.encode("utf-8")) != artifact.base_content_sha256:
            raise StaleStateError("canonical target changed after proposal staging")
        patch_path = self._boundary.resolve_path(artifact.patch_path)
        patch = patch_path.read_text(encoding="utf-8")
        if sha256_bytes(patch.encode("utf-8")) != artifact.patch_sha256:
            raise StaleStateError("staged patch no longer matches its digest")
        proposal_path = self._boundary.resolve_path(artifact.proposal_json_path)
        serialized = proposal_path.read_text(encoding="utf-8")
        if not serialized.endswith("\n"):
            raise StaleStateError("staged proposal serialization is invalid")
        proposal_json = serialized[:-1]
        if sha256_bytes(proposal_json.encode("utf-8")) != artifact.proposal_digest:
            raise StaleStateError("staged proposal no longer matches its digest")
        proposal = WriteProposal.model_validate_json(proposal_json)
        if proposal.requester.principal_id != artifact.requester_id:
            raise StaleStateError("staged proposal requester no longer matches its metadata")
        proposed_content = _render_content(proposal.proposal.content)
        if sha256_bytes(proposed_content.encode("utf-8")) != artifact.proposed_content_sha256:
            raise StaleStateError("staged proposal content no longer matches its digest")
        if _unified_patch(artifact.target_path, current, proposed_content) != patch:
            raise StaleStateError("staged patch does not reproduce the proposed content")
        return CanonicalPromotionRequest(
            proposal_id=artifact.proposal_id,
            proposal_digest=artifact.proposal_digest,
            target_path=artifact.target_path,
            unified_patch=patch,
            base_content_sha256=artifact.base_content_sha256,
            proposed_content_sha256=artifact.proposed_content_sha256,
            reviewer_id=review.reviewer_id,
            reviewer_kind=review.reviewer_kind,
            higher_system_policy_ref=review.higher_system_policy_ref,
            review_policy_id=policy.policy_id,
            permission_revision=revision,
            permission_sha256=content_sha256,
        )

    def _read_current(
        self,
        target_path: str,
        canonical_reader: Callable[[str], str | None] | None,
    ) -> str:
        if canonical_reader is not None:
            return canonical_reader(target_path) or ""
        path = self._boundary.resolve_path(target_path, must_exist=False)
        if not path.exists():
            return ""
        if not path.is_file():
            raise StaleStateError("canonical target is no longer a regular file")
        return path.read_text(encoding="utf-8")
