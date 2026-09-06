"""Embedded deterministic exact and lexical index."""

from .models import (
    ExclusionExplanation,
    IndexGeneration,
    IndexHealth,
    IndexMutationResult,
    RebuildResult,
)
from .sqlite import INDEX_SCHEMA_VERSION, ExactIndex, Fts5UnavailableError

__all__ = [
    "INDEX_SCHEMA_VERSION",
    "ExactIndex",
    "ExclusionExplanation",
    "Fts5UnavailableError",
    "IndexGeneration",
    "IndexHealth",
    "IndexMutationResult",
    "RebuildResult",
]
