"""Strict, non-caching canonical permission-envelope loader."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from sys4ai_memory.security import (
    ProjectBoundary,
    SecretDetectedError,
    UnsafePathError,
    require_secret_free,
)
from sys4ai_memory.util import sha256_bytes

from .models import CanonicalPermissionDocument, PermissionEnvelope, PermissionSnapshot


class CanonicalPermissionError(RuntimeError):
    """The current canonical permission source is missing or invalid."""


class CanonicalPermissionEnvelopeLoader:
    """Read and validate the canonical file on every resolution request."""

    def __init__(self, boundary: ProjectBoundary, relative_path: str) -> None:
        self._boundary = boundary
        self._relative_path = relative_path

    @property
    def source_path(self) -> str:
        return self._relative_path

    def load_snapshot(self) -> PermissionSnapshot:
        try:
            path = self._boundary.resolve_path(self._relative_path)
            raw = path.read_bytes()
        except (OSError, ValueError, UnsafePathError) as error:
            raise CanonicalPermissionError("canonical permission source is unavailable") from error
        try:
            decoded = raw.decode("utf-8")
        except UnicodeDecodeError as error:
            raise CanonicalPermissionError("canonical permission source must be UTF-8") from error
        try:
            parsed: object = json.loads(decoded)
            require_secret_free(parsed, field_path="canonical_permission")
            document = CanonicalPermissionDocument.model_validate(parsed)
        except (json.JSONDecodeError, ValidationError, SecretDetectedError, ValueError) as error:
            raise CanonicalPermissionError(
                "canonical permission source failed validation"
            ) from error
        if (
            document.project_id != self._boundary.project_id
            or document.dataset_id != self._boundary.dataset_id
        ):
            raise CanonicalPermissionError(
                "canonical permission source does not match the project/dataset boundary"
            )
        return PermissionSnapshot(
            document=document,
            content_sha256=sha256_bytes(raw),
            source_path=Path(self._relative_path).as_posix(),
        )

    def resolve(self, principal_id: str) -> PermissionEnvelope:
        """Resolve one principal from a fresh canonical read; no stale cache exists."""

        snapshot = self.load_snapshot()
        grants = tuple(
            grant for grant in snapshot.document.grants if grant.principal_id == principal_id
        )
        return PermissionEnvelope(
            principal_id=principal_id,
            project_id=snapshot.document.project_id,
            dataset_id=snapshot.document.dataset_id,
            revision=snapshot.document.revision,
            canonical_sha256=snapshot.content_sha256,
            grants=grants,
        )
