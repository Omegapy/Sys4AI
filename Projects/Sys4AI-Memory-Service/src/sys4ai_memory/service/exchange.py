"""Disposable, policy-gated service adapter for provider-neutral package exchange."""

from __future__ import annotations

from pathlib import Path

from sys4ai_memory.authorization import (
    AuthorizationDecision,
    AuthorizationRequest,
    AuthorizationService,
)
from sys4ai_memory.contracts import Permission, Sensitivity
from sys4ai_memory.exchange import (
    AuthorizedExchangeImpact,
    ExchangePolicyError,
    ExportPolicy,
    ImportConflictError,
    ImportPreview,
    MemoryPackageExporter,
    MemoryPackageImporter,
    PackageContainer,
    ProviderImportStage,
)
from sys4ai_memory.providers import (
    ExportRequest,
    ExportResult,
    MemoryProvider,
    ProviderExportFormat,
    ProviderMutation,
)
from sys4ai_memory.providers.in_memory import InMemoryProvider
from sys4ai_memory.security import ProjectBoundary, StaleStateError

from .authorization import ProviderAuthorizationBridge
from .models import PortableExportCall, PortableImportCall, PortResult


def _require_provider_export_result(
    result: ExportResult,
    *,
    provider: MemoryProvider,
    call: PortableExportCall,
    profile_versions: dict[str, str],
) -> None:
    snapshot = result.snapshot
    identity_matches = (
        result.provider_name is provider.provider_name
        and result.provider_version == provider.provider_version
        and result.request_id == call.request_id
        and result.project_id == call.context.project_id
        and result.dataset_id == call.context.dataset_id
        and result.format is ProviderExportFormat.SYS4AI
        and result.trace_id == call.context.trace_id
    )
    snapshot_matches = snapshot is not None and (
        snapshot.project_id == call.context.project_id
        and snapshot.dataset_id == call.context.dataset_id
        and snapshot.origin_provider is provider.provider_name
        and snapshot.origin_provider_version == provider.provider_version
        and snapshot.profile_versions == profile_versions
        and result.record_count == len(snapshot.records)
        and result.relation_count == len(snapshot.relations)
        and result.checksum == snapshot.checksums.package_sha256
    )
    if not identity_matches or not snapshot_matches:
        raise ExchangePolicyError("provider export result does not match the requested snapshot")


class MemoryPackageExchange:
    """Policy-aware public exchange over provider-neutral package contracts."""

    def __init__(
        self,
        *,
        boundary: ProjectBoundary,
        provider: MemoryProvider,
        import_stage_provider: MemoryProvider | None = None,
        authorization: AuthorizationService,
        provider_authorization: ProviderAuthorizationBridge,
        exporter: MemoryPackageExporter,
        importer: MemoryPackageImporter,
        export_policy: ExportPolicy,
        profile_versions: dict[str, str],
        container: PackageContainer = PackageContainer.ZIP,
    ) -> None:
        production_ready = not export_policy.format_decision_status.startswith("pending-")
        if not production_ready and not isinstance(provider, InMemoryProvider):
            raise ValueError("disposable exchange supports only the in-memory provider")
        if import_stage_provider is not None and import_stage_provider is provider:
            raise ValueError("import requires a provider generation distinct from active state")
        if not production_ready and import_stage_provider is not None and not isinstance(
            import_stage_provider, InMemoryProvider
        ):
            raise ValueError("disposable import supports only an in-memory staging provider")
        if not production_ready and not export_policy.allow_unencrypted_disposable_test_only:
            raise ValueError("disposable exchange requires the explicit test-only export policy")
        if production_ready and (
            export_policy.approved_encryption != "age-x25519"
            or exporter.age_tool is None
            or container is not PackageContainer.ZIP
        ):
            raise ValueError("approved exchange requires ZIP and configured age tooling")
        if not profile_versions:
            raise ValueError("disposable exchange requires profile versions")
        if importer.boundary.root != boundary.root:
            raise ValueError("exchange importer does not match the project boundary")
        try:
            exporter.disposable_root.relative_to(boundary.root)
        except ValueError as error:
            raise ValueError("disposable export root is outside the project boundary") from error
        self._boundary = boundary
        self._active_provider = provider
        self._import_stage_provider = import_stage_provider
        self._authorization = authorization
        self._provider_authorization = provider_authorization
        self._exporter = exporter
        self._importer = importer
        self._export_policy = export_policy
        self._profile_versions = dict(profile_versions)
        self._container = container
        self._production_ready = production_ready

    async def export(self, call: PortableExportCall) -> PortResult:
        """Export one test candidate from a validated provider-neutral snapshot."""

        self._require_context(call.context.project_id, call.context.dataset_id)
        if call.format != ProviderExportFormat.SYS4AI.value:
            raise ExchangePolicyError("disposable exchange does not enable provider-native export")
        if call.include_sensitive and not self._production_ready:
            raise ExchangePolicyError("disposable unencrypted export cannot include sensitive data")
        exported = await self._active_provider.export(
            ExportRequest(
                context=call.context,
                request_id=call.request_id,
                idempotency_key=call.idempotency_key,
                format=ProviderExportFormat.SYS4AI,
                profile_versions=self._profile_versions,
                destination=call.output_path,
                authorization=call.authorization,
            )
        )
        _require_provider_export_result(
            exported,
            provider=self._active_provider,
            call=call,
            profile_versions=self._profile_versions,
        )
        assert exported.snapshot is not None
        destination = self._boundary.resolve_path(call.output_path, must_exist=False)
        effective_policy = self._export_policy
        if not call.include_sensitive:
            effective_policy = effective_policy.model_copy(
                update={
                    "allowed_sensitivities": frozenset(
                        {Sensitivity.PUBLIC, Sensitivity.INTERNAL}
                    )
                }
            )
        candidate = self._exporter.export_snapshot(
            exported.snapshot,
            destination=destination,
            container=self._container,
            policy=effective_policy,
            disposable_test_only=not self._production_ready,
            age_recipient=call.age_recipient,
        )
        return PortResult(
            result={
                "candidate": candidate.model_dump(mode="json"),
                "provider": exported.model_dump(mode="json"),
                "production_ready": self._production_ready,
            },
            target_ids=(candidate.manifest.package_id,),
            impact_digest=candidate.manifest.package_sha256,
        )

    async def preview_import(self, call: PortableImportCall) -> PortResult:
        """Validate a package and return its current activation digest without writes."""

        self._require_context(call.context.project_id, call.context.dataset_id)
        if call.activate:
            raise ValueError("import preview call cannot request activation")
        preview = self._preview(call)
        return PortResult(
            result={
                "preview": preview.model_dump(mode="json"),
                "production_ready": self._production_ready,
            },
            target_ids=(preview.package_id,),
            impact_digest=preview.impact_digest,
        )

    async def import_package(self, call: PortableImportCall) -> PortResult:
        """Stage and activate an authorized package into an isolated test provider."""

        self._require_context(call.context.project_id, call.context.dataset_id)
        if not call.activate:
            raise ValueError("import activation call must set activate=true")
        if self._import_stage_provider is None:
            raise ImportConflictError("no isolated import provider is available")
        assert call.authorization is not None
        assert call.activation_decision is not None
        assert call.accepted_impact_digest is not None
        preview = self._preview(call)
        if preview.impact_digest != call.accepted_impact_digest:
            raise ImportConflictError("accepted import impact does not match the current preview")
        current_decision = self._fresh_activation_decision(call)
        if current_decision != call.activation_decision:
            raise StaleStateError("canonical import authorization changed before staging")
        exchange_authorization = AuthorizedExchangeImpact(
            decision=current_decision,
            impact_digest=preview.impact_digest,
        )
        provider_stage = ProviderImportStage(
            provider=self._import_stage_provider,
            active_provider=self._active_provider,
            context=call.context,
            preview_authorization=call.authorization,
            isolated_generation=True,
        )
        staged = await self._importer.stage(
            preview,
            authorization=exchange_authorization,
            provider_stage=provider_stage,
        )
        current_decision = self._fresh_activation_decision(call)
        if current_decision != call.activation_decision:
            raise StaleStateError("canonical import authorization changed after staging")
        execution_authorization = self._provider_authorization.authorize(
            call.context,
            ProviderMutation.IMPORT,
            authorization_operation="memory.import.activate",
            target_path=call.package_path,
            impact_digest=staged.provider_impact_digest,
        )
        receipt = await self._importer.activate(
            staged,
            authorization=AuthorizedExchangeImpact(
                decision=current_decision,
                impact_digest=preview.impact_digest,
            ),
            provider_stage=provider_stage,
            execution_authorization=execution_authorization,
        )
        self._active_provider = self._import_stage_provider
        self._import_stage_provider = None
        return PortResult(
            result={
                "staged": staged.model_dump(mode="json"),
                "receipt": receipt.model_dump(mode="json"),
                "production_ready": self._production_ready,
            },
            target_ids=(*receipt.imported_record_ids, *receipt.imported_relation_ids),
            impact_digest=preview.impact_digest,
        )

    def _preview(self, call: PortableImportCall) -> ImportPreview:
        package_path = self._boundary.resolve_path(call.package_path)
        preview = self._importer.validator.preview(Path(package_path))
        if call.expected_sha256 is not None and call.expected_sha256 != preview.package_sha256:
            raise ImportConflictError("expected package SHA-256 does not match the package")
        return preview

    def _fresh_activation_decision(
        self,
        call: PortableImportCall,
    ) -> AuthorizationDecision:
        return self._authorization.require(
            AuthorizationRequest(
                principal_id=call.context.principal_id,
                project_id=call.context.project_id,
                dataset_id=call.context.dataset_id,
                operation="memory.import.activate",
                permission=Permission.ADMINISTER,
                scope=call.context.scope,
                target_path=call.package_path,
                trace_id=call.context.trace_id,
                require_action_specific=True,
            )
        )

    def _require_context(self, project_id: str, dataset_id: str) -> None:
        self._boundary.require_identity(project_id=project_id, dataset_id=dataset_id)


class DisposableMemoryPackageExchange(MemoryPackageExchange):
    """Backward-compatible name for the explicitly disposable policy profile."""
