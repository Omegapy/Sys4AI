"""Software-engineering profile adapter built on deterministic Python AST units."""

from __future__ import annotations

from collections.abc import Mapping

from sys4ai_memory.contracts.models import SourceRecord

from .adapters import OptionalAdapterUnit, PythonAdapter


class SoftwareEngineeringPythonAdapter:
    """Classify Python symbols into the approved software-engineering types."""

    adapter_id = "software-python-ast@1"
    adapter_version = "1.0.0"
    formats = frozenset({"python"})

    def units(
        self,
        raw_bytes: bytes,
        source: SourceRecord,
    ) -> tuple[OptionalAdapterUnit, ...]:
        text = raw_bytes.decode("utf-8")
        units = PythonAdapter().units(text, source.path_or_uri)
        classified: list[OptionalAdapterUnit] = []
        for unit in units:
            record_type = self._record_type(unit.structured)
            classified.append(
                OptionalAdapterUnit(
                    title=unit.title,
                    exact=unit.exact,
                    locator=dict(unit.locator),
                    structured={
                        **unit.structured,
                        "profile_classification": record_type,
                    },
                    record_type=record_type,
                    profile_type=f"software-engineering@1:{record_type}",
                )
            )
        return tuple(classified)

    @staticmethod
    def _record_type(structured: Mapping[str, object]) -> str:
        symbol = str(structured.get("symbol", ""))
        kind = str(structured.get("symbol_kind", ""))
        if kind == "function" and symbol.startswith("test_"):
            return "TestCase"
        if kind == "class" and symbol.endswith(("Error", "Failure")):
            return "FailurePattern"
        if kind == "assignment" and "TARGET" in symbol.upper():
            return "BuildTarget"
        return "CodeSymbol"


def software_engineering_adapter() -> SoftwareEngineeringPythonAdapter:
    """Return the versioned adapter without mutating global adapter state."""

    return SoftwareEngineeringPythonAdapter()


__all__ = ["SoftwareEngineeringPythonAdapter", "software_engineering_adapter"]
