"""In-process Python client for the provider-neutral memory service."""

from __future__ import annotations

from collections.abc import Mapping

from pydantic import JsonValue

from sys4ai_memory.contracts import OperationName, RetrievalMode, ScopeReference

from .common import invoke_dispatcher, project_authorization
from .dispatcher import MemoryServiceDispatcher
from .models import (
    AuthorizationContext,
    ControlAction,
    DispatchResponse,
    InterfaceAction,
    InterfaceIdentity,
    InterfaceKind,
)


class MemoryClient:
    """Stable synchronous client; all work remains inside the injected dispatcher."""

    def __init__(
        self,
        dispatcher: MemoryServiceDispatcher,
        *,
        identity: InterfaceIdentity,
        project_id: str,
        dataset_id: str,
        scope: ScopeReference | None = None,
        query_project_ids: tuple[str, ...] | None = None,
        explicit_cross_project: bool = False,
        client_id: str = "sys4ai-python-client",
    ) -> None:
        self._dispatcher = dispatcher
        self._authorization = project_authorization(
            identity,
            project_id=project_id,
            dataset_id=dataset_id,
            scope=scope,
            query_project_ids=query_project_ids,
            explicit_cross_project=explicit_cross_project,
        )
        self._client_id = client_id

    @property
    def authorization(self) -> AuthorizationContext:
        return self._authorization

    def invoke(
        self,
        operation: InterfaceAction,
        payload: Mapping[str, JsonValue] | None = None,
        *,
        idempotency_key: str | None = None,
        request_id: str | None = None,
        trace_id: str | None = None,
        purpose: str = "memory operation",
    ) -> DispatchResponse:
        return invoke_dispatcher(
            self._dispatcher,
            operation=operation,
            authorization=self._authorization,
            interface=InterfaceKind.PYTHON,
            client_id=self._client_id,
            purpose=purpose,
            payload=payload,
            idempotency_key=idempotency_key,
            request_id=request_id,
            trace_id=trace_id,
        )

    def health(
        self, *, detailed: bool = False, request_id: str | None = None, trace_id: str | None = None
    ) -> DispatchResponse:
        return self.invoke(
            OperationName.HEALTH,
            {"detailed": detailed},
            request_id=request_id,
            trace_id=trace_id,
            purpose="inspect memory health",
        )

    def sources_list(
        self,
        *,
        include_excluded: bool = False,
        request_id: str | None = None,
        trace_id: str | None = None,
    ) -> DispatchResponse:
        return self.invoke(
            OperationName.SOURCES_LIST,
            {"include_excluded": include_excluded},
            request_id=request_id,
            trace_id=trace_id,
            purpose="list registered memory sources",
        )

    def sources_explain(
        self,
        target: str,
        *,
        request_id: str | None = None,
        trace_id: str | None = None,
    ) -> DispatchResponse:
        return self.invoke(
            OperationName.SOURCES_EXPLAIN,
            {"target": target},
            request_id=request_id,
            trace_id=trace_id,
            purpose="explain memory source policy",
        )

    def sync(
        self,
        *,
        idempotency_key: str,
        source_ids: tuple[str, ...] = (),
        full: bool = False,
        dry_run: bool = False,
        request_id: str | None = None,
        trace_id: str | None = None,
    ) -> DispatchResponse:
        return self.invoke(
            OperationName.SYNC,
            {"source_ids": list(source_ids), "full": full, "dry_run": dry_run},
            idempotency_key=idempotency_key,
            request_id=request_id,
            trace_id=trace_id,
            purpose="synchronize registered memory sources",
        )

    def recall(
        self,
        query: str,
        *,
        mode: RetrievalMode = RetrievalMode.HYBRID,
        limit: int = 10,
        namespaces: tuple[str, ...] = (),
        current_only: bool = True,
        request_id: str | None = None,
        trace_id: str | None = None,
    ) -> DispatchResponse:
        return self.invoke(
            OperationName.RECALL,
            {
                "query": query,
                "mode": mode.value,
                "limit": limit,
                "namespaces": list(namespaces),
                "current_only": current_only,
            },
            request_id=request_id,
            trace_id=trace_id,
            purpose="recall source-backed memory",
        )

    def get(
        self,
        record_id: str,
        *,
        include_history: bool = False,
        request_id: str | None = None,
        trace_id: str | None = None,
    ) -> DispatchResponse:
        return self.invoke(
            OperationName.GET,
            {"record_id": record_id, "include_history": include_history},
            request_id=request_id,
            trace_id=trace_id,
            purpose="get one memory record",
        )

    def graph(
        self,
        record_id: str,
        *,
        relation_types: tuple[str, ...] = (),
        request_id: str | None = None,
        trace_id: str | None = None,
    ) -> DispatchResponse:
        return self.invoke(
            OperationName.GRAPH,
            {"record_id": record_id, "max_depth": 1, "relation_types": list(relation_types)},
            request_id=request_id,
            trace_id=trace_id,
            purpose="inspect authorized memory relations",
        )

    def propose(
        self,
        proposal: Mapping[str, JsonValue],
        *,
        idempotency_key: str,
        request_id: str | None = None,
        trace_id: str | None = None,
    ) -> DispatchResponse:
        return self.invoke(
            OperationName.PROPOSE,
            {"proposal": dict(proposal)},
            idempotency_key=idempotency_key,
            request_id=request_id,
            trace_id=trace_id,
            purpose="stage a typed memory proposal",
        )

    def approve(
        self,
        proposal_id: str,
        *,
        decision: str,
        reason: str,
        idempotency_key: str,
        request_id: str | None = None,
        trace_id: str | None = None,
    ) -> DispatchResponse:
        return self.invoke(
            OperationName.APPROVE,
            {"proposal_id": proposal_id, "decision": decision, "reason": reason},
            idempotency_key=idempotency_key,
            request_id=request_id,
            trace_id=trace_id,
            purpose="review a staged memory proposal",
        )

    def supersede(
        self,
        record_id: str,
        replacement_record_id: str,
        *,
        reason: str,
        idempotency_key: str,
        request_id: str | None = None,
        trace_id: str | None = None,
    ) -> DispatchResponse:
        return self.invoke(
            OperationName.SUPERSEDE,
            {
                "record_id": record_id,
                "replacement_record_id": replacement_record_id,
                "reason": reason,
            },
            idempotency_key=idempotency_key,
            request_id=request_id,
            trace_id=trace_id,
            purpose="supersede a memory record",
        )

    def improve(
        self,
        feedback: Mapping[str, JsonValue],
        *,
        idempotency_key: str,
        record_id: str | None = None,
        request_id: str | None = None,
        trace_id: str | None = None,
    ) -> DispatchResponse:
        return self.invoke(
            OperationName.IMPROVE,
            {"record_id": record_id, "feedback": dict(feedback)},
            idempotency_key=idempotency_key,
            request_id=request_id,
            trace_id=trace_id,
            purpose="apply derived memory feedback",
        )

    def forget(
        self,
        record_ids: tuple[str, ...],
        *,
        action: str,
        reason: str,
        idempotency_key: str,
        execute: bool = False,
        operation_id: str | None = None,
        impact_digest: str | None = None,
        request_id: str | None = None,
        trace_id: str | None = None,
    ) -> DispatchResponse:
        return self.invoke(
            OperationName.FORGET,
            {
                "record_ids": list(record_ids),
                "action": action,
                "reason": reason,
                "execute": execute,
                "operation_id": operation_id,
                "impact_digest": impact_digest,
            },
            idempotency_key=idempotency_key,
            request_id=request_id,
            trace_id=trace_id,
            purpose="preview or execute a memory lifecycle action",
        )

    def rebuild(
        self,
        *,
        idempotency_key: str,
        preview_only: bool = True,
        generation_label: str | None = None,
        operation_id: str | None = None,
        impact_digest: str | None = None,
        request_id: str | None = None,
        trace_id: str | None = None,
    ) -> DispatchResponse:
        return self.invoke(
            OperationName.REBUILD,
            {
                "preview_only": preview_only,
                "generation_label": generation_label,
                "operation_id": operation_id,
                "impact_digest": impact_digest,
            },
            idempotency_key=idempotency_key,
            request_id=request_id,
            trace_id=trace_id,
            purpose="preview or activate a memory rebuild",
        )

    def export(
        self,
        output_path: str,
        *,
        idempotency_key: str,
        format: str = "sys4ai",
        include_sensitive: bool = False,
        age_recipient: str | None = None,
        request_id: str | None = None,
        trace_id: str | None = None,
    ) -> DispatchResponse:
        return self.invoke(
            OperationName.EXPORT,
            {
                "output_path": output_path,
                "format": format,
                "include_sensitive": include_sensitive,
                "age_recipient": age_recipient,
            },
            idempotency_key=idempotency_key,
            request_id=request_id,
            trace_id=trace_id,
            purpose="export a portable memory package",
        )

    def import_package(
        self,
        package_path: str,
        *,
        idempotency_key: str,
        activate: bool = False,
        expected_sha256: str | None = None,
        impact_digest: str | None = None,
        request_id: str | None = None,
        trace_id: str | None = None,
    ) -> DispatchResponse:
        return self.invoke(
            OperationName.IMPORT,
            {
                "package_path": package_path,
                "activate": activate,
                "expected_sha256": expected_sha256,
                "impact_digest": impact_digest,
            },
            idempotency_key=idempotency_key,
            request_id=request_id,
            trace_id=trace_id,
            purpose="validate or import a memory package",
        )

    def explain(
        self,
        record_id: str,
        *,
        request_id: str | None = None,
        trace_id: str | None = None,
    ) -> DispatchResponse:
        return self.invoke(
            OperationName.EXPLAIN,
            {"record_id": record_id},
            request_id=request_id,
            trace_id=trace_id,
            purpose="explain memory provenance and ranking",
        )

    def initialize(
        self,
        *,
        idempotency_key: str,
        configuration_path: str = "config/memory.toml",
        request_id: str | None = None,
        trace_id: str | None = None,
    ) -> DispatchResponse:
        """Initialize project memory in one request without a preview artifact."""

        return self.invoke(
            ControlAction.INITIALIZE_DIRECT,
            {"configuration_path": configuration_path},
            idempotency_key=idempotency_key,
            request_id=request_id,
            trace_id=trace_id,
            purpose="initialize project memory",
        )

    def initialize_preview(
        self,
        *,
        configuration_path: str = "config/memory.toml",
        request_id: str | None = None,
        trace_id: str | None = None,
    ) -> DispatchResponse:
        return self.invoke(
            ControlAction.INITIALIZE_PREVIEW,
            {"configuration_path": configuration_path},
            request_id=request_id,
            trace_id=trace_id,
            purpose="preview memory initialization",
        )

    def initialize_apply(
        self,
        impact_digest: str,
        *,
        idempotency_key: str,
        configuration_path: str = "config/memory.toml",
        request_id: str | None = None,
        trace_id: str | None = None,
    ) -> DispatchResponse:
        return self.invoke(
            ControlAction.INITIALIZE_APPLY,
            {"configuration_path": configuration_path, "impact_digest": impact_digest},
            idempotency_key=idempotency_key,
            request_id=request_id,
            trace_id=trace_id,
            purpose="apply reviewed memory initialization",
        )

    def operation_status(
        self,
        operation_id: str,
        *,
        request_id: str | None = None,
        trace_id: str | None = None,
    ) -> DispatchResponse:
        return self.invoke(
            ControlAction.OPERATION_STATUS,
            {"operation_id": operation_id},
            request_id=request_id,
            trace_id=trace_id,
            purpose="inspect long-running memory operation status",
        )
