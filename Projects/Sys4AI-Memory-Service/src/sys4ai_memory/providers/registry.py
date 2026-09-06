"""Lazy provider registry and factory."""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from types import MappingProxyType

from sys4ai_memory.contracts.errors import ErrorCategory

from .base import MemoryProvider
from .contracts import ProviderConfig, ProviderName
from .errors import provider_error


@dataclass(frozen=True, slots=True)
class ProviderRegistration:
    name: ProviderName
    module: str
    factory: str


class ProviderRegistry:
    """Resolve one selected adapter without importing optional providers early."""

    def __init__(self, registrations: tuple[ProviderRegistration, ...]) -> None:
        by_name = {registration.name: registration for registration in registrations}
        if len(by_name) != len(registrations):
            raise ValueError("provider registrations must have unique names")
        self._registrations = MappingProxyType(by_name)

    @property
    def names(self) -> tuple[ProviderName, ...]:
        return tuple(sorted(self._registrations, key=str))

    def create(self, config: ProviderConfig) -> MemoryProvider:
        registration = self._registrations.get(ProviderName(config.provider_name))
        if registration is None:
            raise provider_error(
                ErrorCategory.PROVIDER_UNSUPPORTED,
                trace_id="trace_provider_factory",
                message="The selected memory provider is not registered.",
                recoverable=False,
                remediation_hint="Select a provider from the configured registry.",
            )
        module = importlib.import_module(registration.module)
        factory = getattr(module, registration.factory, None)
        if not isinstance(factory, type):
            raise provider_error(
                ErrorCategory.PROVIDER_UNAVAILABLE,
                trace_id="trace_provider_factory",
                message="The registered memory provider factory is unavailable.",
                recoverable=False,
                remediation_hint="Repair the installed provider adapter package.",
            )
        provider = factory(config)
        if not isinstance(provider, MemoryProvider):
            raise provider_error(
                ErrorCategory.PROVIDER_UNSUPPORTED,
                trace_id="trace_provider_factory",
                message="The selected adapter does not satisfy the MemoryProvider contract.",
                recoverable=False,
                remediation_hint="Use an adapter that implements the complete async contract.",
            )
        return provider


DEFAULT_PROVIDER_REGISTRY = ProviderRegistry(
    (
        ProviderRegistration(
            name=ProviderName.IN_MEMORY,
            module="sys4ai_memory.providers.in_memory",
            factory="InMemoryProvider",
        ),
        ProviderRegistration(
            name=ProviderName.COGNEE,
            module="sys4ai_memory.providers.cognee",
            factory="CogneeProvider",
        ),
    )
)


def create_provider(config: ProviderConfig) -> MemoryProvider:
    """Create the configured provider through the built-in lazy registry."""

    return DEFAULT_PROVIDER_REGISTRY.create(config)


__all__ = [
    "DEFAULT_PROVIDER_REGISTRY",
    "ProviderRegistration",
    "ProviderRegistry",
    "create_provider",
]
