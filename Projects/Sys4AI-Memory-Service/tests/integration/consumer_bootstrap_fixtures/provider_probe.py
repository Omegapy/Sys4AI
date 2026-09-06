"""Confined real-adapter initialization probe, invoked only by the opt-in test."""

from __future__ import annotations

import asyncio
import importlib.abc
import json
import os
import socket
import sqlite3
import sys
import traceback
from pathlib import Path
from urllib.parse import unquote, urlsplit


def main() -> None:
    root = Path(sys.argv[1])
    project_id, dataset_id = sys.argv[2:4]
    derived = root / ".sys4ai/memory"
    assert derived.stat().st_mode & 0o077 == 0
    temporary = derived / "probe-tmp"
    temporary.mkdir(mode=0o700, exist_ok=True)
    os.environ["TMPDIR"] = str(temporary)
    network_attempts: list[dict[str, object]] = []
    blocked_ipv6_probes: list[str] = []
    denied_writes: list[str] = []
    native_imports: list[str] = []

    def require_private_write(value: object) -> None:
        if not isinstance(value, str | bytes | os.PathLike):
            return
        target = Path(os.fsdecode(value)).absolute().resolve(strict=False)
        if not target.is_relative_to(derived):
            denied_writes.append(str(target))
            raise PermissionError("probe denied a write outside the derived root")

    def audit(event: str, args: tuple[object, ...]) -> None:
        if event in {"socket.connect", "socket.getaddrinfo", "socket.bind", "socket.sendto"}:
            family = getattr(args[0], "family", "unknown") if args else "unknown"
            frames = traceback.extract_stack(limit=8)
            if (
                event == "socket.bind"
                and family == socket.AF_INET6
                and args[1] == ("::1", 0)
                and any(
                    frame.name == "_has_ipv6"
                    and Path(frame.filename).parts[-3:] == ("urllib3", "util", "connection.py")
                    for frame in frames
                )
            ):
                # urllib3 catches a denied import-time IPv6 feature check. Keep
                # it denied and visible without claiming a connection occurred.
                blocked_ipv6_probes.append("urllib3._has_ipv6")
                raise PermissionError("IPv6 capability bind denied by the provider probe")
            network_attempts.append(
                {
                    "event": event,
                    "family": family,
                    "frames": [
                        (Path(frame.filename).name, frame.name, frame.lineno) for frame in frames
                    ],
                }
            )
            raise PermissionError("provider probe cannot access a network")
        if event == "sqlite3.connect" and args[0] != ":memory:":
            database_path = args[0]
            if isinstance(database_path, str) and database_path.startswith("file:"):
                database_path = unquote(urlsplit(database_path).path)
            require_private_write(database_path)
        if event == "open":
            mode, flags = args[1:3]
            writing = isinstance(mode, str) and any(item in mode for item in "wax+")
            writing = (
                writing
                or isinstance(flags, int)
                and bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND))
            )
            if writing:
                require_private_write(args[0])
        elif event in {"os.mkdir", "os.remove", "os.rmdir", "os.chmod"}:
            require_private_write(args[0])
        elif event in {"os.rename", "os.link", "os.symlink"}:
            require_private_write(args[0])
            require_private_write(args[1])

    class ObserveNativeBoundary(importlib.abc.MetaPathFinder):
        def find_spec(self, fullname: str, path: object = None, target: object = None) -> None:
            del path, target
            if fullname == "cognee" or fullname.startswith("cognee."):
                assert os.environ.get("COGNEE_LOGS_DIR") == str(derived / "cognee/logs")
                native_imports.append(fullname)
            return None

    sys.addaudithook(audit)
    sys.meta_path.insert(0, ObserveNativeBoundary())

    from sys4ai_memory.authorization import (
        AuthorizationService,
        CanonicalPermissionEnvelopeLoader,
    )
    from sys4ai_memory.configuration import load_configuration
    from sys4ai_memory.initialization import preflight_initialization
    from sys4ai_memory.providers import (
        CogneeProviderConfig,
        MemoryProviderError,
        ProviderContext,
        ProviderInitializationRequest,
        ProviderMutation,
        create_provider,
    )
    from sys4ai_memory.security import ProjectBoundary
    from sys4ai_memory.service import ProviderAuthorizationBridge

    loaded = load_configuration(root / "config/memory.toml", trusted_project_root=root)
    preflight_initialization(loaded)
    assert loaded.configuration.memory.project_id == project_id
    assert loaded.configuration.memory.provider.cognee.dataset == dataset_id
    config = CogneeProviderConfig(
        project_id=project_id,
        dataset_id=dataset_id,
        project_root=str(root),
        derived_data_root=str(derived),
        model_cache_root=str(derived / "models"),
        semantic_enabled=False,
    )
    context = ProviderContext(
        project_id=project_id,
        dataset_id=dataset_id,
        principal_id="isolation-owner",
        scope={"level": "project", "scope_id": project_id},
        trace_id="trace_isolated_provider",
    )
    loader = CanonicalPermissionEnvelopeLoader(
        ProjectBoundary(project_id, dataset_id, root), "control_records/memory/permissions.json"
    )
    bridge = ProviderAuthorizationBridge(AuthorizationService(loader), loader)
    grant = bridge.authorize(context, ProviderMutation.INITIALIZE, target_path="config/memory.toml")
    provider = create_provider(config)
    assert "cognee" not in sys.modules
    result = asyncio.run(
        provider.initialize(
            ProviderInitializationRequest(
                context=context,
                configuration_fingerprint=loaded.fingerprint,
                dry_run=False,
                path_boundaries_validated=True,
                exclusions_validated=True,
                discovery_dry_run_approved=True,
                authorization=grant,
            )
        )
    )
    assert result.initialized and result.dataset_id == dataset_id
    assert "cognee" in sys.modules and native_imports
    try:
        asyncio.run(
            provider.capabilities(context.model_copy(update={"dataset_id": "other-memory"}))
        )
    except MemoryProviderError as error:
        crossed_category = error.envelope.error.category.value
    else:
        raise AssertionError("provider accepted a different dataset context")

    databases = []
    for path in (derived / "cognee").rglob("*"):
        if not path.is_file() or path.is_symlink():
            continue
        with path.open("rb") as stream:
            header = stream.read(16)
        if header != b"SQLite format 3\x00":
            continue
        with sqlite3.connect(path.as_uri() + "?mode=ro", uri=True) as database:
            tables = [
                row[0]
                for row in database.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
                )
            ]
        databases.append(
            {"path": str(path), "tables": tables, "mode": oct(path.stat().st_mode & 0o777)}
        )
    assert databases and all(item["tables"] for item in databases)
    assert not any(path.is_file() for path in (derived / "models").rglob("*"))
    if network_attempts or denied_writes:
        print(
            json.dumps(
                {
                    "status": "failed",
                    "network_events": network_attempts,
                    "denied_write_targets": denied_writes,
                }
            )
        )
        raise SystemExit(2)
    print(
        json.dumps(
            {
                "status": "passed",
                "pid": os.getpid(),
                "project_id": result.project_id,
                "dataset_id": result.dataset_id,
                "provider_version": result.provider_version,
                "initialized": result.initialized,
                "semantic_enabled": False,
                "model_files": 0,
                "unexpected_network_attempts": 0,
                "allowed_network_actions": 0,
                "blocked_ipv6_capability_probes": len(blocked_ipv6_probes),
                "outside_write_attempts": 0,
                "native_import_count": len(native_imports),
                "crossed_dataset_error": crossed_category,
                "databases": databases,
                "log_root": str(derived / "cognee/logs"),
                "model_root": str(config.resolved_model_cache_root),
                "private_memory_ancestor_mode": oct(derived.stat().st_mode & 0o777),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        # Native exception text and logging are not an evidence payload.
        trace = traceback.extract_tb(error.__traceback__)
        print(
            json.dumps(
                {
                    "status": "failed",
                    "error_type": type(error).__name__,
                    "error_line": trace[-1].lineno if trace else None,
                    "error_file": Path(trace[-1].filename).name if trace else None,
                }
            )
        )
        raise SystemExit(2) from None
