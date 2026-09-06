"""JSON Schema 2020-12 generation for the public contract set."""

from __future__ import annotations

from typing import Any

from ._base import SCHEMA_VERSION, VersionedContract
from .errors import ErrorEnvelope
from .models import (
    MemoryProfile,
    MemoryRecord,
    RebuildReceipt,
    RelationRecord,
    RetrievalResult,
    SourceRecord,
    WriteProposal,
)

JSON_SCHEMA_DIALECT = "https://json-schema.org/draft/2020-12/schema"

PUBLIC_CONTRACT_MODELS: dict[str, type[VersionedContract]] = {
    "memory-record.schema.json": MemoryRecord,
    "source-record.schema.json": SourceRecord,
    "relation-record.schema.json": RelationRecord,
    "write-proposal.schema.json": WriteProposal,
    "retrieval-result.schema.json": RetrievalResult,
    "memory-profile.schema.json": MemoryProfile,
    "rebuild-receipt.schema.json": RebuildReceipt,
    "error-envelope.schema.json": ErrorEnvelope,
}


def public_contract_schema(filename: str) -> dict[str, Any]:
    """Build one closed public schema with an explicit dialect and identity."""

    model = PUBLIC_CONTRACT_MODELS[filename]
    generated = model.model_json_schema(mode="validation")
    return {
        "$schema": JSON_SCHEMA_DIALECT,
        "$id": filename,
        "x-sys4ai-schema-version": SCHEMA_VERSION,
        **generated,
    }


def public_contract_schemas() -> dict[str, dict[str, Any]]:
    """Build every public schema in stable filename order."""

    return {
        filename: public_contract_schema(filename)
        for filename in sorted(PUBLIC_CONTRACT_MODELS)
    }

