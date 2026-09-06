from __future__ import annotations

from datetime import UTC, datetime

import pytest

from sys4ai_memory.observability import VersionContext


@pytest.fixture
def observed_at() -> datetime:
    return datetime(2026, 9, 3, 18, 0, tzinfo=UTC)


@pytest.fixture
def versions() -> VersionContext:
    return VersionContext(
        configuration_version="1.0",
        configuration_fingerprint="a" * 64,
        profile_versions={"base": "1.0.0"},
        profile_fingerprints={"base": "b" * 64},
        provider_name="in_memory",
        provider_version="1.0.0",
        provider_fingerprint="c" * 64,
        source_registry_fingerprint="d" * 64,
    )
