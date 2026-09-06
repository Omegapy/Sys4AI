from __future__ import annotations

from collections.abc import Mapping

import pytest
from pydantic import JsonValue

from sys4ai_memory.contracts import ErrorCategory, ErrorEnvelope, OperationName
from sys4ai_memory.interfaces import (
    MUTATING_ACTIONS,
    DispatchSuccess,
    MemoryClient,
)
from tests.interfaces.helpers import IDENTITY, REQUEST_ID, TRACE_ID, RecordingDispatcher


def _payloads() -> Mapping[OperationName, dict[str, JsonValue]]:
    return {
        OperationName.HEALTH: {"detailed": False},
        OperationName.SOURCES_LIST: {"include_excluded": False},
        OperationName.SOURCES_EXPLAIN: {"target": "docs/requirements.md"},
        OperationName.SYNC: {"source_ids": [], "full": False, "dry_run": True},
        OperationName.RECALL: {"query": "source authority"},
        OperationName.GET: {"record_id": "mem_ALPHA"},
        OperationName.GRAPH: {"record_id": "mem_ALPHA"},
        OperationName.PROPOSE: {"proposal": {"record_type": "Observation"}},
        OperationName.APPROVE: {
            "proposal_id": "mwp_ALPHA",
            "decision": "approve",
            "reason": "reviewed",
        },
        OperationName.SUPERSEDE: {
            "record_id": "mem_ALPHA",
            "replacement_record_id": "mem_BETA",
            "reason": "new evidence",
        },
        OperationName.IMPROVE: {"feedback": {"relevant": True}},
        OperationName.FORGET: {
            "record_ids": ["mem_ALPHA"],
            "action": "expire",
            "reason": "retention",
            "execute": False,
        },
        OperationName.REBUILD: {"preview_only": True},
        OperationName.EXPORT: {"output_path": "exports/memory.zip"},
        OperationName.IMPORT: {"package_path": "imports/memory.zip", "activate": False},
        OperationName.EXPLAIN: {"record_id": "mem_ALPHA"},
    }


def test_python_client_maps_every_public_operation_to_one_dispatcher() -> None:
    dispatcher = RecordingDispatcher()
    client = MemoryClient(
        dispatcher,
        identity=IDENTITY,
        project_id="project-alpha",
        dataset_id="dataset-alpha",
    )

    for operation, payload in _payloads().items():
        response = client.invoke(
            operation,
            payload,
            idempotency_key="retry-key" if operation in MUTATING_ACTIONS else None,
        )
        assert isinstance(response, DispatchSuccess)

    assert {request.operation for request in dispatcher.requests} == set(OperationName)
    assert all(
        request.authorization.project_id == "project-alpha" for request in dispatcher.requests
    )


def test_python_client_validation_returns_stable_error_without_dispatch() -> None:
    dispatcher = RecordingDispatcher()
    client = MemoryClient(
        dispatcher,
        identity=IDENTITY,
        project_id="project-alpha",
        dataset_id="dataset-alpha",
    )

    response = client.invoke(
        OperationName.RECALL,
        {"query": ""},
        request_id=REQUEST_ID,
        trace_id=TRACE_ID,
    )

    assert isinstance(response, ErrorEnvelope)
    assert response.error.category is ErrorCategory.SCHEMA_INVALID
    assert response.error.trace_id == TRACE_ID
    assert not dispatcher.requests


@pytest.mark.parametrize(
    "failure",
    [RuntimeError("password=do-not-return"), ValueError("private backend detail")],
)
def test_python_client_never_returns_raw_dispatcher_errors(failure: Exception) -> None:
    dispatcher = RecordingDispatcher(failure=failure)
    client = MemoryClient(
        dispatcher,
        identity=IDENTITY,
        project_id="project-alpha",
        dataset_id="dataset-alpha",
    )

    response = client.health(trace_id=TRACE_ID)

    assert isinstance(response, ErrorEnvelope)
    serialized = response.model_dump_json()
    assert "do-not-return" not in serialized
    assert "backend detail" not in serialized
    assert response.error.trace_id == TRACE_ID
