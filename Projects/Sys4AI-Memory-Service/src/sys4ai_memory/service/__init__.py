"""Shared service-layer composition primitives."""

from .authorization import (
    PROVIDER_AUTHORIZATION_OPERATIONS,
    PROVIDER_OPERATION_NAMES,
    ProviderAuthorizationBridge,
    ProviderAuthorizationError,
)
from .dispatcher import MemoryService, ServiceHandler
from .exchange import DisposableMemoryPackageExchange, MemoryPackageExchange
from .models import (
    EvidenceSynthesisRequest,
    EvidenceSynthesisResult,
    ImprovementSubmission,
    PortableExportCall,
    PortableImportCall,
    PortResult,
    ProposalSubmission,
    SynthesisCitation,
    SynthesizedClaim,
)
from .ports import (
    CanonicalPromotionPort,
    EvidenceSynthesisPort,
    ExactIndexPort,
    LifecycleIndexPort,
    PortableExchangePort,
    RebuildPort,
    ServiceComponents,
)

__all__ = [
    "PROVIDER_AUTHORIZATION_OPERATIONS",
    "PROVIDER_OPERATION_NAMES",
    "CanonicalPromotionPort",
    "DisposableMemoryPackageExchange",
    "EvidenceSynthesisPort",
    "EvidenceSynthesisRequest",
    "EvidenceSynthesisResult",
    "ExactIndexPort",
    "LifecycleIndexPort",
    "ImprovementSubmission",
    "MemoryService",
    "MemoryPackageExchange",
    "PortResult",
    "PortableExchangePort",
    "PortableExportCall",
    "PortableImportCall",
    "ProposalSubmission",
    "ProviderAuthorizationBridge",
    "ProviderAuthorizationError",
    "RebuildPort",
    "ServiceComponents",
    "ServiceHandler",
    "SynthesisCitation",
    "SynthesizedClaim",
]
