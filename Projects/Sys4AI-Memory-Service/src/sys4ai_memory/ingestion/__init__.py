"""Deterministic base-format ingestion and incremental synchronization."""

from .adapters import (
    ADAPTER_VERSION,
    DEFAULT_PROFILE_VERSION,
    OptionalAdapterUnit,
    OptionalSourceAdapter,
    available_adapters,
    normalize_bytes,
    normalize_many,
    normalize_source,
)
from .manifest import compare_manifests
from .models import (
    IngestionBatchResult,
    IngestionFailure,
    NormalizedDocument,
    SourceChange,
    SourceChangeKind,
    SourceDelta,
    SourceManifest,
    SourceManifestEntry,
    SyncCheckpoint,
    SyncResult,
    load_manifest,
)
from .software_engineering import (
    SoftwareEngineeringPythonAdapter,
    software_engineering_adapter,
)
from .synchronizer import (
    IndexWriter,
    IngestionSynchronizer,
    RecordHistoryReader,
    synchronize_sources,
)

__all__ = [
    "ADAPTER_VERSION",
    "DEFAULT_PROFILE_VERSION",
    "IndexWriter",
    "IngestionBatchResult",
    "IngestionFailure",
    "IngestionSynchronizer",
    "NormalizedDocument",
    "OptionalAdapterUnit",
    "OptionalSourceAdapter",
    "RecordHistoryReader",
    "SourceChange",
    "SourceChangeKind",
    "SourceDelta",
    "SourceManifest",
    "SourceManifestEntry",
    "SoftwareEngineeringPythonAdapter",
    "SyncCheckpoint",
    "SyncResult",
    "available_adapters",
    "compare_manifests",
    "load_manifest",
    "normalize_bytes",
    "normalize_many",
    "normalize_source",
    "software_engineering_adapter",
    "synchronize_sources",
]
