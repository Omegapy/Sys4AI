"""JSON Schema and Pydantic parity checks for every public contract."""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import pytest
from jsonschema import Draft202012Validator, ValidationError  # type: ignore[import-untyped]
from pydantic import ValidationError as PydanticValidationError

from sys4ai_memory.contracts.schema import (
    PUBLIC_CONTRACT_MODELS,
    public_contract_schema,
)

from .cases import VALID_PAYLOADS, invalid_payloads

SCHEMA_DIRECTORY = Path(__file__).parents[2] / "schemas" / "memory"
SCHEMA_FILENAMES = tuple(sorted(PUBLIC_CONTRACT_MODELS))


def _load_schema(filename: str) -> dict[str, object]:
    return cast(
        dict[str, object],
        json.loads((SCHEMA_DIRECTORY / filename).read_text(encoding="utf-8")),
    )


@pytest.mark.parametrize("filename", SCHEMA_FILENAMES)
def test_schema_is_draft_2020_12_and_accepts_valid_case(filename: str) -> None:
    schema = _load_schema(filename)
    Draft202012Validator.check_schema(schema)
    required = schema["required"]
    assert isinstance(required, list)
    assert {"schema_version", "api_version"} <= set(required)
    Draft202012Validator(schema).validate(VALID_PAYLOADS[filename])
    PUBLIC_CONTRACT_MODELS[filename].model_validate(VALID_PAYLOADS[filename])


@pytest.mark.parametrize("filename", SCHEMA_FILENAMES)
def test_schema_and_model_reject_representative_invalid_case(filename: str) -> None:
    payload = invalid_payloads()[filename]
    schema = _load_schema(filename)
    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(payload)
    with pytest.raises(PydanticValidationError):
        PUBLIC_CONTRACT_MODELS[filename].model_validate(payload)


@pytest.mark.parametrize("filename", SCHEMA_FILENAMES)
def test_checked_in_schema_matches_model(filename: str) -> None:
    assert _load_schema(filename) == public_contract_schema(filename)
