from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict

from sys4ai_memory.contracts import OperationName
from sys4ai_memory.interfaces import DispatchSuccess
from sys4ai_memory.rebuild import AuthorizedRebuildImpact, RebuildMode
from sys4ai_memory.service import ServiceComponents
from tests.service.test_dispatcher import _request, _service


class _Preview(BaseModel):
    model_config = ConfigDict(frozen=True)

    operation_id: str
    impact_digest: str


class _Receipt(BaseModel):
    model_config = ConfigDict(frozen=True)

    operation_id: str
    impact_digest: str
    outcome: str = "succeeded"


class _RecordingRebuild:
    def __init__(self) -> None:
        self.preview_operation_ids: list[str] = []
        self.executed_operation_ids: list[str] = []

    def preview(
        self,
        *,
        operation_id: str,
        mode: RebuildMode,
        deterministic: bool = True,
    ) -> _Preview:
        assert mode is RebuildMode.FULL
        assert deterministic
        self.preview_operation_ids.append(operation_id)
        return _Preview(operation_id=operation_id, impact_digest="e" * 64)

    async def execute(
        self,
        preview: _Preview,
        *,
        authorization: AuthorizedRebuildImpact,
    ) -> _Receipt:
        assert authorization.impact_digest == preview.impact_digest
        self.executed_operation_ids.append(preview.operation_id)
        return _Receipt(
            operation_id=preview.operation_id,
            impact_digest=preview.impact_digest,
        )


def test_rebuild_preview_and_activation_share_explicit_operation_identity(
    tmp_path: Path,
) -> None:
    rebuild = _RecordingRebuild()
    service, _, _ = _service(
        tmp_path.resolve(),
        components=ServiceComponents(rebuild=rebuild),  # type: ignore[arg-type]
    )
    previewed = service.dispatch(
        _request(
            OperationName.REBUILD,
            {"preview_only": True},
            suffix="rebuild_operation_preview",
            idempotency_key="rebuild-operation-preview",
        )
    )
    assert isinstance(previewed, DispatchSuccess)
    preview = previewed.result["preview"]
    assert isinstance(preview, dict)

    activated = service.dispatch(
        _request(
            OperationName.REBUILD,
            {
                "preview_only": False,
                "operation_id": preview["operation_id"],
                "impact_digest": preview["impact_digest"],
            },
            suffix="rebuild_operation_activate",
            idempotency_key="rebuild-operation-activate",
        )
    )

    assert isinstance(activated, DispatchSuccess)
    receipt = activated.result["receipt"]
    assert isinstance(receipt, dict)
    assert receipt["operation_id"] == preview["operation_id"]
    assert rebuild.preview_operation_ids == [
        preview["operation_id"],
        preview["operation_id"],
    ]
    assert rebuild.executed_operation_ids == [preview["operation_id"]]
