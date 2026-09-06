"""Recoverable canonical promotion followed by source-derived synchronization."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from enum import StrEnum
from threading import RLock
from typing import Literal, Protocol, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from sys4ai_memory.contracts import ScopeReference
from sys4ai_memory.security import IdempotencyConflictError, ProjectBoundary, StaleStateError
from sys4ai_memory.util import canonical_json_bytes, ensure_utc, sha256_bytes, sha256_file, utc_now

from .staging import (
    CanonicalPromotionPlanner,
    CanonicalPromotionRequest,
    ReviewReceipt,
    StagedProposalArtifact,
)


class PromotionModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, validate_default=True)


class PreparedCanonicalWrite(PromotionModel):
    """A repository change prepared without changing the canonical target."""

    transaction_id: str = Field(min_length=1, max_length=255)
    proposal_id: str
    proposal_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    target_path: str
    before_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    after_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    repository_change_ref: str = Field(min_length=1, max_length=1000)
    repository_review_ref: str = Field(min_length=1, max_length=1000)
    write_convention: Literal["governed-repository-workflow"] = "governed-repository-workflow"
    canonical_visible: Literal[False] = False


class CanonicalWriteReceipt(PromotionModel):
    transaction_id: str = Field(min_length=1, max_length=255)
    target_path: str
    before_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    after_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    repository_change_ref: str = Field(min_length=1, max_length=1000)
    repository_review_ref: str = Field(min_length=1, max_length=1000)
    atomic_visibility: Literal[True] = True
    committed_at: datetime

    @model_validator(mode="after")
    def validate_time(self) -> Self:
        ensure_utc(self.committed_at)
        return self


class CanonicalRollbackReceipt(PromotionModel):
    transaction_id: str = Field(min_length=1, max_length=255)
    target_path: str
    restored_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    repository_change_ref: str = Field(min_length=1, max_length=1000)
    canonical_restored: Literal[True] = True
    rolled_back_at: datetime

    @model_validator(mode="after")
    def validate_time(self) -> Self:
        ensure_utc(self.rolled_back_at)
        return self


class SourceSynchronizationMode(StrEnum):
    PROMOTION = "promotion"
    ROLLBACK = "rollback"


class CanonicalSourceSynchronizationRequest(PromotionModel):
    transaction_id: str = Field(min_length=1, max_length=255)
    project_id: str = Field(min_length=1, max_length=255)
    dataset_id: str = Field(min_length=1, max_length=255)
    target_path: str
    expected_content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    repository_change_ref: str = Field(min_length=1, max_length=1000)
    mode: SourceSynchronizationMode
    trace_id: str = Field(min_length=1, max_length=255)


class CanonicalSourceSynchronizationReceipt(PromotionModel):
    synchronization_id: str = Field(min_length=1, max_length=255)
    transaction_id: str = Field(min_length=1, max_length=255)
    project_id: str = Field(min_length=1, max_length=255)
    dataset_id: str = Field(min_length=1, max_length=255)
    target_path: str
    synchronized_content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    repository_change_ref: str = Field(min_length=1, max_length=1000)
    mode: SourceSynchronizationMode
    source_ids: tuple[str, ...] = Field(min_length=1)
    completed_at: datetime
    synchronized: Literal[True] = True
    separate_memory_write_performed: Literal[False] = False

    @model_validator(mode="after")
    def validate_receipt(self) -> Self:
        ensure_utc(self.completed_at)
        if any(not source_id.strip() for source_id in self.source_ids):
            raise ValueError("synchronized source IDs must not be blank")
        if len(set(self.source_ids)) != len(self.source_ids):
            raise ValueError("synchronized source IDs must be unique")
        return self


class CanonicalPromotionReceipt(PromotionModel):
    operation_id: str = Field(min_length=1, max_length=255)
    idempotency_key_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    proposal_id: str
    proposal_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    project_id: str = Field(min_length=1, max_length=255)
    dataset_id: str = Field(min_length=1, max_length=255)
    target_path: str
    reviewer_id: str = Field(min_length=1, max_length=255)
    review_policy_id: str
    permission_revision: str
    permission_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    repository_write: CanonicalWriteReceipt
    source_synchronization: CanonicalSourceSynchronizationReceipt
    canonical_write_performed: Literal[True] = True
    synchronization_completed: Literal[True] = True
    separate_memory_write_performed: Literal[False] = False
    public_result: Literal["succeeded"] = "succeeded"
    completed_at: datetime

    @model_validator(mode="after")
    def validate_receipt(self) -> Self:
        ensure_utc(self.completed_at)
        if (
            self.repository_write.transaction_id != self.source_synchronization.transaction_id
            or self.repository_write.target_path != self.target_path
            or self.source_synchronization.target_path != self.target_path
            or self.source_synchronization.project_id != self.project_id
            or self.source_synchronization.dataset_id != self.dataset_id
            or self.source_synchronization.synchronized_content_sha256
            != self.repository_write.after_sha256
            or self.source_synchronization.repository_change_ref
            != self.repository_write.repository_change_ref
            or self.source_synchronization.mode is not SourceSynchronizationMode.PROMOTION
        ):
            raise ValueError("promotion receipt contains inconsistent write or sync evidence")
        return self


class PromotionRecoveryState(StrEnum):
    ROLLED_BACK = "rolled_back"
    RECOVERY_REQUIRED = "recovery_required"


class CanonicalPromotionFailureReceipt(PromotionModel):
    operation_id: str = Field(min_length=1, max_length=255)
    proposal_id: str
    proposal_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    target_path: str
    failed_phase: str = Field(min_length=1, max_length=100)
    failure_code: str = Field(min_length=1, max_length=100)
    recovery_state: PromotionRecoveryState
    canonical_restored: bool
    derived_state_reconciled: bool
    rollback: CanonicalRollbackReceipt | None = None
    rollback_synchronization: CanonicalSourceSynchronizationReceipt | None = None
    public_result: Literal["failed"] = "failed"

    @model_validator(mode="after")
    def validate_recovery(self) -> Self:
        if self.recovery_state is PromotionRecoveryState.ROLLED_BACK and (
            not self.canonical_restored or not self.derived_state_reconciled
        ):
            raise ValueError("rolled-back promotion must restore canonical and derived state")
        if self.canonical_restored and self.rollback is None:
            raise ValueError("canonical restoration requires a rollback receipt")
        if self.rollback_synchronization is not None and not self.canonical_restored:
            raise ValueError("rollback synchronization requires canonical restoration")
        return self


class CanonicalPromotionError(RuntimeError):
    """A promotion failed without exposing a public success result."""

    def __init__(self, message: str, receipt: CanonicalPromotionFailureReceipt) -> None:
        super().__init__(message)
        self.receipt = receipt


class CanonicalPromotionRolledBackError(CanonicalPromotionError):
    """The promotion failed and both canonical and derived state were restored."""


class CanonicalPromotionRecoveryRequiredError(CanonicalPromotionError):
    """A failed promotion needs operator recovery before it can be retried safely."""


class GovernedRepositoryWritePort(Protocol):
    """Normal repository workflow with an atomic commit and compensating rollback."""

    def prepare(
        self,
        request: CanonicalPromotionRequest,
        *,
        operation_id: str,
    ) -> PreparedCanonicalWrite: ...

    def commit(self, prepared: PreparedCanonicalWrite) -> CanonicalWriteReceipt: ...

    def rollback(
        self,
        prepared: PreparedCanonicalWrite,
        committed: CanonicalWriteReceipt | None,
    ) -> CanonicalRollbackReceipt: ...


class CanonicalSourceSynchronizationPort(Protocol):
    """Synchronize only by rereading the changed canonical source."""

    def synchronize(
        self,
        request: CanonicalSourceSynchronizationRequest,
    ) -> CanonicalSourceSynchronizationReceipt: ...


class CanonicalPromotionCoordinator:
    """Publish a canonical repository change only with matching sync evidence."""

    def __init__(
        self,
        boundary: ProjectBoundary,
        planner: CanonicalPromotionPlanner,
        repository: GovernedRepositoryWritePort,
        synchronizer: CanonicalSourceSynchronizationPort,
    ) -> None:
        self._boundary = boundary
        self._planner = planner
        self._repository = repository
        self._synchronizer = synchronizer
        self._lock = RLock()
        self._completed: dict[str, tuple[str, CanonicalPromotionReceipt]] = {}
        self._recovery_required: dict[
            str,
            tuple[str, CanonicalPromotionFailureReceipt],
        ] = {}

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
        canonical_reader: Callable[[str], str | None] | None = None,
    ) -> CanonicalPromotionReceipt:
        if not idempotency_key.strip():
            raise ValueError("canonical promotion requires a nonblank idempotency key")
        self._boundary.require_identity(project_id=project_id, dataset_id=dataset_id)
        key_digest = sha256_bytes(idempotency_key.encode("utf-8"))
        attempt_digest = sha256_bytes(
            canonical_json_bytes(
                {
                    "artifact": artifact.model_dump(mode="json"),
                    "review": review.model_dump(mode="json"),
                    "project_id": project_id,
                    "dataset_id": dataset_id,
                    "scope": scope.model_dump(mode="json"),
                    "record_type": record_type,
                }
            )
        )
        with self._lock:
            completed = self._completed.get(key_digest)
            if completed is not None:
                prior_digest, prior_receipt = completed
                if prior_digest != attempt_digest:
                    raise IdempotencyConflictError(
                        "idempotency key already identifies a different canonical promotion"
                    )
                return prior_receipt
            blocked = self._recovery_required.get(key_digest)
            if blocked is not None:
                prior_digest, failure = blocked
                if prior_digest != attempt_digest:
                    raise IdempotencyConflictError(
                        "idempotency key already identifies a different canonical promotion"
                    )
                raise CanonicalPromotionRecoveryRequiredError(
                    "canonical promotion requires recovery before retry",
                    failure,
                )
            request = self._planner.create_request(
                artifact,
                review,
                project_id=project_id,
                dataset_id=dataset_id,
                scope=scope,
                record_type=record_type,
                trace_id=trace_id,
                canonical_reader=canonical_reader,
            )
            request_digest = sha256_bytes(canonical_json_bytes(request.model_dump(mode="json")))
            operation_id = f"prom_{request_digest[:32]}"
            prepared: PreparedCanonicalWrite | None = None
            committed: CanonicalWriteReceipt | None = None
            commit_attempted = False
            failed_phase = "prepare_repository_change"
            try:
                prepared = PreparedCanonicalWrite.model_validate(
                    self._repository.prepare(request, operation_id=operation_id)
                )
                self._validate_prepared(request, operation_id, prepared)

                failed_phase = "revalidate_review_and_target"
                current_request = self._planner.create_request(
                    artifact,
                    review,
                    project_id=project_id,
                    dataset_id=dataset_id,
                    scope=scope,
                    record_type=record_type,
                    trace_id=trace_id,
                    canonical_reader=canonical_reader,
                )
                if current_request != request:
                    raise StaleStateError("promotion inputs changed after repository preparation")

                failed_phase = "commit_canonical_change"
                commit_attempted = True
                committed = CanonicalWriteReceipt.model_validate(self._repository.commit(prepared))
                self._validate_committed(prepared, committed)
                self._require_canonical_digest(request.target_path, request.proposed_content_sha256)

                failed_phase = "synchronize_canonical_source"
                synchronized = self._synchronize(
                    request=request,
                    transaction_id=prepared.transaction_id,
                    project_id=project_id,
                    dataset_id=dataset_id,
                    trace_id=trace_id,
                    repository_change_ref=prepared.repository_change_ref,
                    mode=SourceSynchronizationMode.PROMOTION,
                    expected_sha256=request.proposed_content_sha256,
                )
                self._require_canonical_digest(request.target_path, request.proposed_content_sha256)
            except Exception as error:
                if prepared is None:
                    raise
                failure = self._recover(
                    request=request,
                    prepared=prepared,
                    committed=committed,
                    commit_attempted=commit_attempted,
                    project_id=project_id,
                    dataset_id=dataset_id,
                    trace_id=trace_id,
                    failed_phase=failed_phase,
                )
                if failure.recovery_state is PromotionRecoveryState.ROLLED_BACK:
                    raise CanonicalPromotionRolledBackError(
                        "canonical promotion failed and was rolled back",
                        failure,
                    ) from error
                self._recovery_required[key_digest] = (attempt_digest, failure)
                raise CanonicalPromotionRecoveryRequiredError(
                    "canonical promotion failed and requires recovery",
                    failure,
                ) from error

            receipt = CanonicalPromotionReceipt(
                operation_id=operation_id,
                idempotency_key_sha256=key_digest,
                proposal_id=request.proposal_id,
                proposal_digest=request.proposal_digest,
                project_id=project_id,
                dataset_id=dataset_id,
                target_path=request.target_path,
                reviewer_id=request.reviewer_id,
                review_policy_id=request.review_policy_id,
                permission_revision=request.permission_revision,
                permission_sha256=request.permission_sha256,
                repository_write=committed,
                source_synchronization=synchronized,
                completed_at=utc_now(),
            )
            self._completed[key_digest] = (attempt_digest, receipt)
            return receipt

    @staticmethod
    def _validate_prepared(
        request: CanonicalPromotionRequest,
        operation_id: str,
        prepared: PreparedCanonicalWrite,
    ) -> None:
        if (
            prepared.transaction_id != operation_id
            or prepared.proposal_id != request.proposal_id
            or prepared.proposal_digest != request.proposal_digest
            or prepared.target_path != request.target_path
            or prepared.before_sha256 != request.base_content_sha256
            or prepared.after_sha256 != request.proposed_content_sha256
        ):
            raise StaleStateError("prepared repository change does not match the promotion")

    @staticmethod
    def _validate_committed(
        prepared: PreparedCanonicalWrite,
        committed: CanonicalWriteReceipt,
    ) -> None:
        if (
            committed.transaction_id != prepared.transaction_id
            or committed.target_path != prepared.target_path
            or committed.before_sha256 != prepared.before_sha256
            or committed.after_sha256 != prepared.after_sha256
            or committed.repository_change_ref != prepared.repository_change_ref
            or committed.repository_review_ref != prepared.repository_review_ref
        ):
            raise StaleStateError("canonical write receipt does not match the prepared change")

    def _synchronize(
        self,
        *,
        request: CanonicalPromotionRequest,
        transaction_id: str,
        project_id: str,
        dataset_id: str,
        trace_id: str,
        repository_change_ref: str,
        mode: SourceSynchronizationMode,
        expected_sha256: str,
    ) -> CanonicalSourceSynchronizationReceipt:
        sync_request = CanonicalSourceSynchronizationRequest(
            transaction_id=transaction_id,
            project_id=project_id,
            dataset_id=dataset_id,
            target_path=request.target_path,
            expected_content_sha256=expected_sha256,
            repository_change_ref=repository_change_ref,
            mode=mode,
            trace_id=trace_id,
        )
        receipt = CanonicalSourceSynchronizationReceipt.model_validate(
            self._synchronizer.synchronize(sync_request)
        )
        if (
            receipt.transaction_id != transaction_id
            or receipt.project_id != project_id
            or receipt.dataset_id != dataset_id
            or receipt.target_path != request.target_path
            or receipt.synchronized_content_sha256 != expected_sha256
            or receipt.repository_change_ref != repository_change_ref
            or receipt.mode is not mode
        ):
            raise StaleStateError("source synchronization receipt does not match canonical state")
        return receipt

    def _recover(
        self,
        *,
        request: CanonicalPromotionRequest,
        prepared: PreparedCanonicalWrite,
        committed: CanonicalWriteReceipt | None,
        commit_attempted: bool,
        project_id: str,
        dataset_id: str,
        trace_id: str,
        failed_phase: str,
    ) -> CanonicalPromotionFailureReceipt:
        try:
            rollback = CanonicalRollbackReceipt.model_validate(
                self._repository.rollback(prepared, committed)
            )
            if (
                rollback.transaction_id != prepared.transaction_id
                or rollback.target_path != request.target_path
                or rollback.restored_sha256 != request.base_content_sha256
                or rollback.repository_change_ref != prepared.repository_change_ref
            ):
                raise StaleStateError("canonical rollback receipt does not match the promotion")
            self._require_canonical_digest(request.target_path, request.base_content_sha256)
        except Exception:
            return self._failure_receipt(
                request,
                prepared.transaction_id,
                failed_phase,
                "canonical_rollback_failed",
                PromotionRecoveryState.RECOVERY_REQUIRED,
                canonical_restored=False,
                derived_state_reconciled=not commit_attempted,
            )

        rollback_sync: CanonicalSourceSynchronizationReceipt | None = None
        if commit_attempted:
            try:
                rollback_sync = self._synchronize(
                    request=request,
                    transaction_id=prepared.transaction_id,
                    project_id=project_id,
                    dataset_id=dataset_id,
                    trace_id=trace_id,
                    repository_change_ref=prepared.repository_change_ref,
                    mode=SourceSynchronizationMode.ROLLBACK,
                    expected_sha256=request.base_content_sha256,
                )
                self._require_canonical_digest(
                    request.target_path,
                    request.base_content_sha256,
                )
            except Exception:
                return self._failure_receipt(
                    request,
                    prepared.transaction_id,
                    failed_phase,
                    "rollback_synchronization_failed",
                    PromotionRecoveryState.RECOVERY_REQUIRED,
                    canonical_restored=True,
                    derived_state_reconciled=False,
                    rollback=rollback,
                )
        return self._failure_receipt(
            request,
            prepared.transaction_id,
            failed_phase,
            "promotion_step_failed",
            PromotionRecoveryState.ROLLED_BACK,
            canonical_restored=True,
            derived_state_reconciled=True,
            rollback=rollback,
            rollback_synchronization=rollback_sync,
        )

    @staticmethod
    def _failure_receipt(
        request: CanonicalPromotionRequest,
        operation_id: str,
        failed_phase: str,
        failure_code: str,
        recovery_state: PromotionRecoveryState,
        *,
        canonical_restored: bool,
        derived_state_reconciled: bool,
        rollback: CanonicalRollbackReceipt | None = None,
        rollback_synchronization: CanonicalSourceSynchronizationReceipt | None = None,
    ) -> CanonicalPromotionFailureReceipt:
        return CanonicalPromotionFailureReceipt(
            operation_id=operation_id,
            proposal_id=request.proposal_id,
            proposal_digest=request.proposal_digest,
            target_path=request.target_path,
            failed_phase=failed_phase,
            failure_code=failure_code,
            recovery_state=recovery_state,
            canonical_restored=canonical_restored,
            derived_state_reconciled=derived_state_reconciled,
            rollback=rollback,
            rollback_synchronization=rollback_synchronization,
        )

    def _require_canonical_digest(self, target_path: str, expected_sha256: str) -> None:
        path = self._boundary.resolve_path(target_path, must_exist=False)
        if path.exists():
            if not path.is_file():
                raise StaleStateError("canonical promotion target is not a regular file")
            observed = sha256_file(path)
        else:
            observed = sha256_bytes(b"")
        if observed != expected_sha256:
            raise StaleStateError("canonical promotion target does not match the expected digest")
