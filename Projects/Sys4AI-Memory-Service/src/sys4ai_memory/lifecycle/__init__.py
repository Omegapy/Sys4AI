"""Provider-neutral lifecycle transitions and destructive-operation protocol."""

from .destructive import (
    CanonicalDeletionChangeRequest,
    DeletionReceipt,
    DestructiveLifecycleService,
    DestructiveRequest,
    FilesystemImpactResolver,
    ForgetMode,
    GovernedCanonicalDeletionExecutor,
    ImpactPreview,
    ImpactResolver,
    ImpactResource,
    ResourceSpec,
    StorageLocation,
)
from .state import LifecycleCatalog, LifecycleRecord, LifecycleStateError

__all__ = [
    "CanonicalDeletionChangeRequest",
    "DeletionReceipt",
    "DestructiveLifecycleService",
    "DestructiveRequest",
    "FilesystemImpactResolver",
    "ForgetMode",
    "GovernedCanonicalDeletionExecutor",
    "ImpactPreview",
    "ImpactResolver",
    "ImpactResource",
    "LifecycleCatalog",
    "LifecycleRecord",
    "LifecycleStateError",
    "ResourceSpec",
    "StorageLocation",
]
