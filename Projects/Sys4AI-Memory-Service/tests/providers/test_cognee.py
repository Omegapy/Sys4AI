"""Non-initializing Cognee adapter tests using an injected runtime."""

from __future__ import annotations

import importlib
import inspect
import json
import os
import shutil
import socket
import sys
import tempfile
from pathlib import Path
from types import ModuleType

import pytest

from sys4ai_memory.contracts import RetrievalMode, Sensitivity
from sys4ai_memory.contracts.errors import ErrorCategory
from sys4ai_memory.providers import (
    CogneeProviderConfig,
    ExportRequest,
    ForgetAction,
    ForgetRequest,
    HealthRequest,
    ImportRequest,
    ImproveRequest,
    MigrationRequest,
    ProviderContext,
    ProviderExportFormat,
    ProviderHealthProbe,
    ProviderHealthState,
    ProviderInitializationRequest,
    ProviderMutation,
    RecallRequest,
    RememberRequest,
)
from sys4ai_memory.providers.cognee import (
    COGNEE_API_UNCERTAINTIES,
    CogneeMappedItem,
    CogneeProvider,
    LazyCogneeRuntime,
)
from sys4ai_memory.providers.errors import MemoryProviderError

from .helpers import context, memory_record, policy, relation_record, source_record


class FakeCogneeRuntime:
    def __init__(self, *, version: str = "1.5.3") -> None:
        self.version = version
        self.loaded = False
        self.calls: list[str] = []
        self.items: tuple[CogneeMappedItem, ...] = ()
        self.recall_result: object = []
        self.fail_operation: str | None = None

    def installed_version(self) -> str:
        return self.version

    async def configure(self, config: CogneeProviderConfig) -> None:
        del config
        self._call("configure")
        self.loaded = True

    async def remember(
        self, items: tuple[CogneeMappedItem, ...], config: CogneeProviderConfig
    ) -> object:
        del config
        self._call("remember")
        self.items = items
        return {"status": "completed", "items_processed": len(items)}

    async def recall(self, request: RecallRequest, config: CogneeProviderConfig) -> object:
        del request, config
        self._call("recall")
        return self.recall_result

    async def improve(self, request: ImproveRequest, config: CogneeProviderConfig) -> object:
        del request, config
        self._call("improve")
        return {"status": "completed"}

    async def forget(
        self,
        data_ids: tuple[object, ...],
        request: ForgetRequest,
        config: CogneeProviderConfig,
    ) -> object:
        del request, config
        self._call("forget")
        return {"status": "completed", "count": len(data_ids)}

    async def export(self, request: ExportRequest, config: CogneeProviderConfig) -> object:
        del request, config
        self._call("export")
        return {"status": "completed", "num_nodes": 2, "num_edges": 1}

    async def import_snapshot(
        self, request: ImportRequest, config: CogneeProviderConfig
    ) -> object:
        del request, config
        self._call("import")
        return {"status": "completed"}

    async def migrate(self, request: MigrationRequest, config: CogneeProviderConfig) -> object:
        del request, config
        self._call("migrate")
        return {"status": "completed"}

    def _call(self, operation: str) -> None:
        self.calls.append(operation)
        if self.fail_operation == operation:
            raise RuntimeError("provider failed with api_key=should-never-escape")


def cognee_config(tmp_path: Path, **overrides: object) -> CogneeProviderConfig:
    project_root = tmp_path / "project"
    values: dict[str, object] = {
        "project_id": "project-alpha",
        "dataset_id": "project-alpha-memory",
        "project_root": str(project_root),
        "derived_data_root": str(project_root / ".sys4ai" / "memory"),
        "semantic_enabled": True,
        "llm_provider": "ollama",
        "llm_model": "local-test-model",
        "llm_endpoint": "http://127.0.0.1:11434",
        "embedding_provider": "fastembed",
        "embedding_model": "BAAI/bge-small-en-v1.5",
        "embedding_dimensions": 384,
    }
    values.update(overrides)
    return CogneeProviderConfig.model_validate(values)


async def initialize(
    provider: CogneeProvider,
    runtime: FakeCogneeRuntime,
    provider_context: ProviderContext | None = None,
) -> None:
    selected_context = context() if provider_context is None else provider_context
    await provider.initialize(
        ProviderInitializationRequest(
            context=selected_context,
            configuration_fingerprint="d" * 64,
            dry_run=False,
            path_boundaries_validated=True,
            exclusions_validated=True,
            discovery_dry_run_approved=True,
            authorization=policy(ProviderMutation.INITIALIZE, selected_context),
        )
    )
    assert runtime.calls == ["configure"]


def remember_request(*, authorization: bool = True) -> RememberRequest:
    provider_context = context()
    return RememberRequest(
        context=provider_context,
        request_id="mrq_cognee_remember",
        idempotency_key="cognee-remember-1",
        records=(memory_record("mem_ALPHA"), memory_record("mem_BETA")),
        relations=(relation_record(),),
        sources=(source_record(),),
        authorization=(
            policy(ProviderMutation.REMEMBER, provider_context) if authorization else None
        ),
    )


@pytest.mark.asyncio
async def test_liveness_and_capabilities_do_not_load_cognee(tmp_path: Path) -> None:
    runtime = FakeCogneeRuntime()
    provider = CogneeProvider(cognee_config(tmp_path), runtime=runtime)

    liveness = await provider.health(
        HealthRequest(context=context(), probe=ProviderHealthProbe.LIVENESS)
    )
    capabilities = await provider.capabilities(context())

    assert liveness.state is ProviderHealthState.ALIVE
    assert runtime.loaded is False
    assert runtime.calls == []
    assert capabilities.native_interface_exposed is False
    assert capabilities.enabled == (capabilities.supported[0],)


@pytest.mark.asyncio
async def test_adapter_maps_only_declared_semantic_fields_and_normalizes_recall(
    tmp_path: Path,
) -> None:
    runtime = FakeCogneeRuntime()
    provider = CogneeProvider(cognee_config(tmp_path), runtime=runtime)
    await initialize(provider, runtime)

    result = await provider.remember(remember_request())
    replay = await provider.remember(
        remember_request().model_copy(update={"request_id": "mrq_cognee_remember_replay"})
    )
    record_items = [
        item
        for item in runtime.items
        if item.external_metadata["sys4ai"]["kind"] == "record"  # type: ignore[index]
    ]
    relation_items = [
        item
        for item in runtime.items
        if item.external_metadata["sys4ai"]["kind"] == "relation"  # type: ignore[index]
    ]
    assert result.record_ids == ("mem_ALPHA", "mem_BETA")
    assert replay.idempotent_replay is True
    assert runtime.calls.count("remember") == 1
    assert len(record_items) == 2
    assert len(relation_items) == 1
    assert "Provider abstraction keeps agent contracts stable." in record_items[0].text
    assert "Canonical exact content must not be embedded." not in record_items[0].text
    assert record_items[0].data_id == record_items[0].data_id

    runtime.recall_result = [
        {"score": 0.91, "external_metadata": item.external_metadata}
        for item in runtime.items
    ] + [
        {
            "score": 1.0,
            "provider_native_edge": {
                "source": "mem_ALPHA",
                "target": "mem_BETA",
                "validation": "verified",
            },
        }
    ]
    recalled = await provider.recall(
        RecallRequest(
            context=context(),
            request_id="mrq_cognee_recall",
            query="provider abstraction",
            mode=RetrievalMode.HYBRID,
        )
    )

    assert {candidate.record.record_id for candidate in recalled.candidates} == {
        "mem_ALPHA",
        "mem_BETA",
    }
    assert tuple(relation.relation_id for relation in recalled.relations) == (
        "rel_ALPHA_DEPENDS_ON_BETA",
    )
    serialized = json.dumps(recalled.to_json_dict())
    assert "FakeCogneeRuntime" not in serialized
    assert "raw_result" not in serialized


@pytest.mark.asyncio
async def test_readiness_does_not_call_writeful_cognee_health(tmp_path: Path) -> None:
    runtime = FakeCogneeRuntime()
    provider = CogneeProvider(cognee_config(tmp_path), runtime=runtime)
    await initialize(provider, runtime)

    readiness = await provider.health(
        HealthRequest(context=context(), probe=ProviderHealthProbe.READINESS)
    )

    assert readiness.state is ProviderHealthState.DEGRADED
    assert readiness.components[0].detail_code == "writeful_cognee_readiness_probe_disabled"
    assert runtime.calls == ["configure"]


@pytest.mark.asyncio
async def test_adapter_rejects_unauthorized_mutations_before_runtime_calls(
    tmp_path: Path,
) -> None:
    runtime = FakeCogneeRuntime()
    config = cognee_config(
        tmp_path,
        allow_improve=True,
        allow_forget=True,
        allow_native_export=True,
        allow_native_import=True,
        allow_migrate=True,
    )
    provider = CogneeProvider(config, runtime=runtime)
    await initialize(provider, runtime)
    derived_root = Path(config.derived_data_root)
    provider_context = context()
    operations = (
        (
            provider.remember,
            remember_request(authorization=False),
        ),
        (
            provider.improve,
            ImproveRequest(
                context=provider_context,
                request_id="mrq_improve",
                idempotency_key="improve-1",
            ),
        ),
        (
            provider.forget,
            ForgetRequest(
                context=provider_context,
                request_id="mrq_forget",
                idempotency_key="forget-1",
                action=ForgetAction.DELETE_DERIVED,
                record_ids=("mem_ALPHA",),
            ),
        ),
        (
            provider.export,
            ExportRequest(
                context=provider_context,
                request_id="mrq_export",
                idempotency_key="export-1",
                format=ProviderExportFormat.COGX,
                destination=str(derived_root / "export.cogx"),
            ),
        ),
        (
            provider.import_snapshot,
            ImportRequest(
                context=provider_context,
                request_id="mrq_import",
                idempotency_key="import-1",
                format=ProviderExportFormat.COGX,
                source=str(derived_root / "export.cogx"),
                source_checksum="e" * 64,
            ),
        ),
        (
            provider.migrate,
            MigrationRequest(
                context=provider_context,
                request_id="mrq_migrate",
                idempotency_key="migrate-1",
                source_version="1.5.3",
                target_version="1.5.3",
            ),
        ),
    )

    for method, request in operations:
        with pytest.raises(MemoryProviderError) as denied:
            await method(request)  # type: ignore[arg-type]
        assert denied.value.envelope.error.category is ErrorCategory.APPROVAL_REQUIRED
    assert runtime.calls == ["configure"]


@pytest.mark.asyncio
async def test_authorized_privileged_calls_use_scoped_fake_runtime(tmp_path: Path) -> None:
    runtime = FakeCogneeRuntime()
    config = cognee_config(
        tmp_path,
        allow_improve=True,
        allow_forget=True,
        allow_native_export=True,
        allow_native_import=True,
        allow_migrate=True,
    )
    provider = CogneeProvider(config, runtime=runtime)
    await initialize(provider, runtime)
    provider_context = context()
    derived_root = Path(config.derived_data_root)

    await provider.improve(
        ImproveRequest(
            context=provider_context,
            request_id="mrq_authorized_improve",
            idempotency_key="authorized-improve",
            record_ids=("mem_ALPHA",),
            authorization=policy(ProviderMutation.IMPROVE, provider_context),
        )
    )

    forget_preview = await provider.forget(
        ForgetRequest(
            context=provider_context,
            request_id="mrq_authorized_forget_preview",
            idempotency_key="authorized-forget",
            action=ForgetAction.DELETE_DERIVED,
            record_ids=("mem_ALPHA",),
            authorization=policy(ProviderMutation.FORGET, provider_context),
        )
    )
    await provider.forget(
        ForgetRequest(
            context=provider_context,
            request_id="mrq_authorized_forget_execute",
            idempotency_key="authorized-forget",
            action=ForgetAction.DELETE_DERIVED,
            record_ids=("mem_ALPHA",),
            execute=True,
            preview_digest=forget_preview.impact_digest,
            authorization=policy(
                ProviderMutation.FORGET,
                provider_context,
                impact_digest=forget_preview.impact_digest,
            ),
        )
    )

    await provider.export(
        ExportRequest(
            context=provider_context,
            request_id="mrq_authorized_export",
            idempotency_key="authorized-export",
            format=ProviderExportFormat.COGX,
            destination=str(derived_root / "export.cogx"),
            authorization=policy(ProviderMutation.EXPORT, provider_context),
        )
    )

    import_preview = await provider.import_snapshot(
        ImportRequest(
            context=provider_context,
            request_id="mrq_authorized_import_preview",
            idempotency_key="authorized-import",
            format=ProviderExportFormat.COGX,
            source=str(derived_root / "export.cogx"),
            source_checksum="e" * 64,
            authorization=policy(ProviderMutation.IMPORT, provider_context),
        )
    )
    await provider.import_snapshot(
        ImportRequest(
            context=provider_context,
            request_id="mrq_authorized_import_execute",
            idempotency_key="authorized-import",
            format=ProviderExportFormat.COGX,
            source=str(derived_root / "export.cogx"),
            source_checksum="e" * 64,
            execute=True,
            preview_digest=import_preview.impact_digest,
            authorization=policy(
                ProviderMutation.IMPORT,
                provider_context,
                impact_digest=import_preview.impact_digest,
            ),
        )
    )

    migration_preview = await provider.migrate(
        MigrationRequest(
            context=provider_context,
            request_id="mrq_authorized_migrate_preview",
            idempotency_key="authorized-migrate",
            source_version="1.5.3",
            target_version="1.5.3",
            authorization=policy(ProviderMutation.MIGRATE, provider_context),
        )
    )
    await provider.migrate(
        MigrationRequest(
            context=provider_context,
            request_id="mrq_authorized_migrate_execute",
            idempotency_key="authorized-migrate",
            source_version="1.5.3",
            target_version="1.5.3",
            execute=True,
            preview_digest=migration_preview.impact_digest,
            authorization=policy(
                ProviderMutation.MIGRATE,
                provider_context,
                impact_digest=migration_preview.impact_digest,
            ),
        )
    )

    assert runtime.calls == ["configure", "improve", "forget", "export", "import", "migrate"]


@pytest.mark.asyncio
async def test_adapter_rejects_restricted_or_secret_like_embedding_content(
    tmp_path: Path,
) -> None:
    runtime = FakeCogneeRuntime()
    provider = CogneeProvider(cognee_config(tmp_path), runtime=runtime)
    await initialize(provider, runtime)
    provider_context = context()
    restricted = memory_record().model_copy(
        update={
            "security": memory_record().security.model_copy(
                update={"sensitivity": Sensitivity.RESTRICTED}
            )
        }
    )
    secret_like = memory_record(
        "mem_SECRET_LIKE",
        summary="A prohibited api_key=should-never-enter-embedding value.",
    )

    for record, key in ((restricted, "restricted"), (secret_like, "secret-like")):
        request = RememberRequest(
            context=provider_context,
            request_id=f"mrq_{key}",
            idempotency_key=key,
            records=(record,),
            authorization=policy(ProviderMutation.REMEMBER, provider_context),
        )
        with pytest.raises(MemoryProviderError) as rejected:
            await provider.remember(request)
        assert rejected.value.envelope.error.category is ErrorCategory.SENSITIVITY_VIOLATION

    assert runtime.calls == ["configure"]


@pytest.mark.asyncio
async def test_exact_version_gate_precedes_cognee_configuration(tmp_path: Path) -> None:
    runtime = FakeCogneeRuntime(version="1.5.4")
    provider = CogneeProvider(cognee_config(tmp_path), runtime=runtime)

    with pytest.raises(MemoryProviderError) as incompatible:
        await provider.initialize(
            ProviderInitializationRequest(
                context=context(),
                configuration_fingerprint="d" * 64,
                dry_run=False,
                path_boundaries_validated=True,
                exclusions_validated=True,
                discovery_dry_run_approved=True,
                authorization=policy(ProviderMutation.INITIALIZE, context()),
            )
        )

    assert incompatible.value.envelope.error.category is ErrorCategory.PROVIDER_UNSUPPORTED
    assert runtime.calls == []
    assert runtime.loaded is False


@pytest.mark.asyncio
async def test_native_exception_is_redacted_and_not_chained(tmp_path: Path) -> None:
    runtime = FakeCogneeRuntime()
    provider = CogneeProvider(cognee_config(tmp_path), runtime=runtime)
    await initialize(provider, runtime)
    runtime.fail_operation = "recall"

    with pytest.raises(MemoryProviderError) as failure:
        await provider.recall(
            RecallRequest(
                context=context(),
                request_id="mrq_cognee_failure",
                query="provider",
                mode=RetrievalMode.SEMANTIC,
            )
        )

    assert failure.value.envelope.error.category is ErrorCategory.RETRIEVAL_FAILED
    assert "should-never-escape" not in failure.value.envelope.to_stable_json()
    assert failure.value.__cause__ is None


@pytest.mark.asyncio
async def test_lazy_runtime_sets_security_environment_before_import(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = cognee_config(tmp_path)
    observed: dict[str, str | None] = {}
    module = ModuleType("cognee")
    module.__version__ = "1.5.3"  # type: ignore[attr-defined]

    async def unused(*args: object, **kwargs: object) -> object:
        del args, kwargs
        observed["operation_telemetry"] = os.environ.get("TELEMETRY_DISABLED")
        observed["operation_caching"] = os.environ.get("CACHING")
        observed["operation_fastembed_cache"] = os.environ.get("FASTEMBED_CACHE_PATH")
        return {}

    class ConfigApi:
        def data_root_directory(self, value: str) -> None:
            observed["data_root"] = value

        def system_root_directory(self, value: str) -> None:
            observed["system_root"] = value

    module.remember = unused  # type: ignore[attr-defined]
    module.recall = unused  # type: ignore[attr-defined]
    module.improve = unused  # type: ignore[attr-defined]
    module.forget = unused  # type: ignore[attr-defined]
    module.export = unused  # type: ignore[attr-defined]
    module.config = ConfigApi()  # type: ignore[attr-defined]
    relational = ModuleType("cognee.infrastructure.databases.relational")

    async def create_db_and_tables() -> None:
        observed["relational_initialized"] = "true"

    relational.create_db_and_tables = create_db_and_tables  # type: ignore[attr-defined]

    def importer(name: str) -> ModuleType:
        assert name in {"cognee", "cognee.infrastructure.databases.relational"}
        observed["dotenv"] = os.environ.get("PYTHON_DOTENV_DISABLED")
        observed["telemetry"] = os.environ.get("TELEMETRY_DISABLED")
        observed["tracing"] = os.environ.get("COGNEE_TRACING_ENABLED")
        observed["cost_map"] = os.environ.get("LITELLM_LOCAL_MODEL_COST_MAP")
        observed["local_key"] = os.environ.get("LLM_API_KEY")
        observed["hf_home"] = os.environ.get("HF_HOME")
        observed["torch_home"] = os.environ.get("TORCH_HOME")
        observed["file_logs"] = os.environ.get("COGNEE_LOGS_DIR")
        return module if name == "cognee" else relational

    monkeypatch.setenv("PYTHON_DOTENV_DISABLED", "0")
    monkeypatch.setenv("TELEMETRY_DISABLED", "0")
    monkeypatch.setenv("COGNEE_TRACING_ENABLED", "true")
    monkeypatch.setenv("LITELLM_LOCAL_MODEL_COST_MAP", "False")
    monkeypatch.delenv("FASTEMBED_CACHE_PATH", raising=False)
    monkeypatch.setenv("HF_HOME", "/caller/cache")
    runtime = LazyCogneeRuntime(importer=importer, version_reader=lambda _: "1.5.3")
    await runtime.configure(config)
    await runtime.export(
        ExportRequest(
            context=context(),
            request_id="mrq_runtime_environment_export",
            idempotency_key="runtime-environment-export",
            format=ProviderExportFormat.COGX,
            destination=str(Path(config.derived_data_root) / "environment.cogx"),
        ),
        config,
    )

    assert observed["dotenv"] == "1"
    assert observed["telemetry"] == "1"
    assert observed["tracing"] == "false"
    assert observed["cost_map"] == "True"
    assert observed["local_key"] == "local-provider-no-auth"
    assert observed["relational_initialized"] == "true"
    assert observed["operation_telemetry"] == "1"
    assert observed["operation_caching"] == "false"
    assert observed["operation_fastembed_cache"] == str(
        config.resolved_model_cache_root / "fastembed"
    )
    assert observed["hf_home"] == str(config.resolved_model_cache_root / "huggingface")
    assert observed["torch_home"] == str(config.resolved_model_cache_root / "torch")
    assert Path(observed["file_logs"]).is_relative_to(Path(config.derived_data_root))
    with pytest.raises(RuntimeError, match="cannot be reused across project boundaries"):
        await runtime.configure(cognee_config(tmp_path, dataset_id="another-project-memory"))
    assert os.environ["PYTHON_DOTENV_DISABLED"] == "0"
    assert os.environ["TELEMETRY_DISABLED"] == "0"
    assert os.environ["COGNEE_TRACING_ENABLED"] == "true"
    assert os.environ["LITELLM_LOCAL_MODEL_COST_MAP"] == "False"
    assert "LLM_API_KEY" not in os.environ
    assert "FASTEMBED_CACHE_PATH" not in os.environ
    assert os.environ["HF_HOME"] == "/caller/cache"
    assert runtime.loaded is True
    assert not Path(config.derived_data_root).exists()


def test_installed_version_metadata_check_does_not_import_cognee() -> None:
    runtime = LazyCogneeRuntime()
    was_loaded = "cognee" in sys.modules

    assert runtime.installed_version() == "1.5.3"
    assert ("cognee" in sys.modules) is was_loaded
    assert len(COGNEE_API_UNCERTAINTIES) == 5


@pytest.mark.asyncio
async def test_preimported_cognee_is_rejected_before_any_provider_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setitem(sys.modules, "cognee", ModuleType("cognee"))
    config = cognee_config(tmp_path)
    before = dict(os.environ)
    with pytest.raises(RuntimeError, match="imported before the hardened adapter boundary"):
        await LazyCogneeRuntime().configure(config)
    assert dict(os.environ) == before
    assert not Path(config.derived_data_root).exists()


def test_custom_model_cache_is_private_and_environment_is_restored(tmp_path: Path) -> None:
    paths: list[set[str]] = []
    for name in ("first", "second"):
        root = tmp_path / name
        config = cognee_config(root, model_cache_root=str(root / "project/.sys4ai/memory/custom"))
        before = dict(os.environ)
        with LazyCogneeRuntime._security_environment(config):
            scoped = {os.environ[key] for key in (
                "DATA_ROOT_DIRECTORY", "SYSTEM_ROOT_DIRECTORY", "CACHE_ROOT_DIRECTORY",
                "COGNEE_LOGS_DIR", "FASTEMBED_CACHE_PATH", "HF_HOME", "HF_HUB_CACHE",
                "HUGGINGFACE_HUB_CACHE", "TRANSFORMERS_CACHE", "SENTENCE_TRANSFORMERS_HOME",
                "TORCH_HOME", "XDG_CACHE_HOME",
            )}
            assert all(
                Path(value).is_relative_to(Path(config.derived_data_root)) for value in scoped
            )
            assert os.environ["FASTEMBED_CACHE_PATH"] == str(
                config.resolved_model_cache_root / "fastembed"
            )
            paths.append(scoped)
        assert dict(os.environ) == before
    assert paths[0].isdisjoint(paths[1])


@pytest.mark.asyncio
async def test_path_changed_to_symlink_is_rejected_before_provider_import(tmp_path: Path) -> None:
    config = cognee_config(tmp_path)
    memory = Path(config.derived_data_root)
    memory.mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    config.resolved_model_cache_root.symlink_to(outside, target_is_directory=True)
    imported: list[str] = []

    def importer(name: str) -> ModuleType:
        imported.append(name)
        raise AssertionError("must reject before provider import")

    before = dict(os.environ)
    runtime = LazyCogneeRuntime(importer=importer, version_reader=lambda _: "1.5.3")
    with pytest.raises(ValueError, match="model-cache root|symlinks"):
        await runtime.configure(config)
    assert imported == []
    assert list(outside.iterdir()) == []
    assert dict(os.environ) == before


@pytest.mark.asyncio
@pytest.mark.cognee
@pytest.mark.skipif(
    os.environ.get("SYS4AI_RUN_LOCAL_COGNEE") != "1",
    reason="set SYS4AI_RUN_LOCAL_COGNEE=1 with the approved loopback model running",
)
async def test_approved_local_cognee_profile_creates_and_recalls_real_representations(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    product_root = Path(__file__).parents[2].resolve()
    assert (product_root / "models/fastembed").is_dir()
    original_connect = socket.socket.connect
    original_create_connection = socket.create_connection
    with original_create_connection(("127.0.0.1", 11434), timeout=2):
        pass

    allowed_attempts: list[tuple[str, int]] = []
    blocked_attempts: list[object] = []

    def allowed(address: object) -> bool:
        return (
            isinstance(address, tuple)
            and len(address) >= 2
            and str(address[0]) in {"127.0.0.1", "::1", "localhost"}
            and int(address[1]) == 11434
        )

    def guarded_connect(instance: socket.socket, address: object) -> None:
        if not allowed(address):
            blocked_attempts.append(address)
            raise AssertionError("local Cognee profile attempted non-loopback network access")
        assert isinstance(address, tuple)
        allowed_attempts.append((str(address[0]), int(address[1])))
        original_connect(instance, address)

    monkeypatch.setattr(socket.socket, "connect", guarded_connect)
    spike_parent = product_root / ".sys4ai" / "memory" / "spikes"
    spike_parent.mkdir(parents=True, exist_ok=True)
    try:
        with tempfile.TemporaryDirectory(prefix="real-cognee-", dir=spike_parent) as name:
            derived_root = Path(name)
            shutil.copytree(product_root / "models/fastembed", derived_root / "models/fastembed")
            dataset_id = f"local-profile-{derived_root.name}"
            config = CogneeProviderConfig(
                project_id="project-alpha",
                dataset_id=dataset_id,
                project_root=str(product_root),
                derived_data_root=str(derived_root),
                semantic_enabled=True,
                llm_provider="ollama",
                llm_model="llama3.1:8b",
                llm_endpoint="http://127.0.0.1:11434",
                embedding_provider="fastembed",
                embedding_model="sentence-transformers/all-MiniLM-L6-v2",
                embedding_dimensions=384,
            )
            provider_context = context(dataset_id=dataset_id)
            runtime = LazyCogneeRuntime()
            provider = CogneeProvider(config, runtime=runtime)
            await provider.initialize(
                ProviderInitializationRequest(
                    context=provider_context,
                    configuration_fingerprint="d" * 64,
                    dry_run=False,
                    path_boundaries_validated=True,
                    exclusions_validated=True,
                    discovery_dry_run_approved=True,
                    authorization=policy(ProviderMutation.INITIALIZE, provider_context),
                )
            )
            alpha = memory_record(
                "mem_ALPHA",
                title="Alpha service",
                exact="Alpha service depends on the Beta index.",
            )
            beta = memory_record(
                "mem_BETA",
                title="Beta index",
                exact="Beta index is the dependency target for Alpha.",
            )
            relation = relation_record("mem_ALPHA", "mem_BETA")
            remembered = await provider.remember(
                RememberRequest(
                    context=provider_context,
                    request_id="mrq_real_local_remember",
                    idempotency_key="real-local-remember",
                    sources=(source_record(),),
                    records=(alpha, beta),
                    relations=(relation,),
                    authorization=policy(ProviderMutation.REMEMBER, provider_context),
                )
            )
            recalled = await provider.recall(
                RecallRequest(
                    context=provider_context,
                    request_id="mrq_real_local_recall",
                    query="Beta dependency target",
                    mode=RetrievalMode.SEMANTIC,
                    top_k=5,
                )
            )

            assert set(remembered.record_ids) == {"mem_ALPHA", "mem_BETA"}
            assert remembered.relation_ids == (relation.relation_id,)
            assert {item.record.record_id for item in recalled.candidates} & {
                "mem_ALPHA",
                "mem_BETA",
            }
            with runtime._security_environment(config):
                graph_module = importlib.import_module(
                    "cognee.infrastructure.databases.graph"
                )
                graph = await graph_module.get_graph_engine()
                nodes, edges = await graph.get_graph_data()
                await graph.close()
                relational = importlib.import_module(
                    "cognee.infrastructure.databases.relational"
                )
                await relational.get_relational_engine().engine.dispose()
            assert nodes
            assert edges
            assert any(path.is_file() for path in derived_root.rglob("*"))
    finally:
        for path in (spike_parent, spike_parent.parent, spike_parent.parent.parent):
            try:
                path.rmdir()
            except OSError:
                break

    assert allowed_attempts
    assert blocked_attempts == []


@pytest.mark.asyncio
@pytest.mark.cognee
async def test_pinned_distribution_provider_initialization_and_cogx_archive_are_compatible(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    network_attempts = 0

    def reject_network(*_args: object, **_kwargs: object) -> None:
        nonlocal network_attempts
        network_attempts += 1
        raise AssertionError("COGX compatibility probe attempted network access")

    monkeypatch.setattr(socket.socket, "connect", reject_network)
    monkeypatch.setattr(socket, "create_connection", reject_network)
    config = cognee_config(
        tmp_path,
        semantic_enabled=False,
        llm_provider=None,
        llm_model=None,
        llm_endpoint=None,
        embedding_provider=None,
        embedding_model=None,
        embedding_dimensions=None,
    )
    runtime = LazyCogneeRuntime()
    provider = CogneeProvider(config, runtime=runtime)
    environment_before = {
        name: os.environ.get(name)
        for name in (
            "PYTHON_DOTENV_DISABLED",
            "TELEMETRY_DISABLED",
            "COGNEE_TRACING_ENABLED",
            "HF_HUB_OFFLINE",
            "TRANSFORMERS_OFFLINE",
            "LITELLM_LOCAL_MODEL_COST_MAP",
        )
    }
    archive = Path(config.derived_data_root) / "compatibility" / "archive.cogx"

    with runtime._security_environment(config):
        initialized = await provider.initialize(
            ProviderInitializationRequest(
                context=context(),
                configuration_fingerprint="d" * 64,
                dry_run=False,
                path_boundaries_validated=True,
                exclusions_validated=True,
                discovery_dry_run_approved=True,
                authorization=policy(ProviderMutation.INITIALIZE, context()),
            )
        )
        cognee = importlib.import_module("cognee")
        base_config = importlib.import_module("cognee.base_config").get_base_config()
        relational = importlib.import_module("cognee.infrastructure.databases.relational")
        relational_engine = relational.get_relational_engine()
        relational_tables = await relational_engine.get_table_names()
        relational_database = Path(relational_engine.db_path)
        cogx = importlib.import_module("cognee.modules.migration.cogx")
        export_parameters = inspect.signature(cognee.export).parameters
        assert {"dataset", "format", "destination", "include_permissions"} <= set(
            export_parameters
        )
        archive.parent.mkdir(parents=True, exist_ok=True)
        with cogx.COGXArchiveWriter(archive, source_system="cognee") as writer:
            writer.write(
                cogx.COGXEntity(
                    external_system="cognee",
                    external_id="entity-alpha",
                    name="Alpha",
                )
            )
            writer.write(
                cogx.COGXEntity(
                    external_system="cognee",
                    external_id="entity-beta",
                    name="Beta",
                )
            )
            writer.write(
                cogx.COGXFact(
                    external_system="cognee",
                    external_id="fact-alpha-depends-beta",
                    subject_ref="entity-alpha",
                    predicate="DEPENDS_ON",
                    object_ref="entity-beta",
                )
            )
        manifest = cogx.read_manifest(archive)
        records = list(cogx.read_archive(archive))
        source = cognee.migration.COGXArchiveSource(archive)
        streamed = [record async for record in source.records()]
        await relational_engine.engine.dispose()

    assert cognee.__version__ == "1.5.3"
    assert runtime.loaded is True
    assert initialized.initialized is True
    assert initialized.provider_name.value == "cognee"
    assert Path(base_config.data_root_directory) == (
        Path(config.derived_data_root) / "cognee" / "data"
    )
    assert Path(base_config.system_root_directory) == (
        Path(config.derived_data_root) / "cognee" / "system"
    )
    assert relational_database.is_file()
    assert relational_database.is_relative_to(Path(config.derived_data_root))
    assert {"datasets", "data", "dataset_database", "permissions"} <= set(
        relational_tables
    )
    assert Path(base_config.cache_root_directory) == (
        Path(config.derived_data_root) / "cognee" / "cache"
    )
    assert Path(base_config.logs_root_directory) == (
        Path(config.derived_data_root) / "cognee" / "logs"
    )
    assert manifest is not None
    assert manifest.cogx_version == "0.1"
    assert manifest.counts == {"entity": 2, "fact": 1}
    assert [record.kind for record in records] == ["entity", "entity", "fact"]
    assert [record.model_dump(mode="json") for record in streamed] == [
        record.model_dump(mode="json") for record in records
    ]
    assert source.mode == "preserve"
    assert not (archive / "permissions.json").exists()
    assert network_attempts == 0
    assert {
        name: os.environ.get(name) for name in environment_before
    } == environment_before
