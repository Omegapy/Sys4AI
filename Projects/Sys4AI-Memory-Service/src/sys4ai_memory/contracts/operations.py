"""Public operation, capability, and MCP tool catalogs."""

from __future__ import annotations

from enum import StrEnum

from ._base import API_VERSION, ApiVersion, ContractModel, NonEmptyString
from .enums import Permission


class CapabilityName(StrEnum):
    SERVICE_HEALTH = "service_health"
    SOURCE_REGISTRY = "source_registry"
    INGESTION = "ingestion"
    EXACT = "exact"
    LEXICAL = "lexical"
    SEMANTIC = "semantic"
    GRAPH = "graph"
    TEMPORAL = "temporal"
    TYPED_WRITES = "typed_writes"
    APPROVAL = "approval"
    LIFECYCLE = "lifecycle"
    IMPROVEMENT = "improvement"
    REBUILD = "rebuild"
    PORTABLE_EXPORT = "portable_export"
    PORTABLE_IMPORT = "portable_import"
    PROVENANCE_EXPLANATION = "provenance_explanation"


class OperationName(StrEnum):
    HEALTH = "memory.health"
    SOURCES_LIST = "memory.sources.list"
    SOURCES_EXPLAIN = "memory.sources.explain"
    SYNC = "memory.sync"
    RECALL = "memory.recall"
    GET = "memory.get"
    GRAPH = "memory.graph"
    PROPOSE = "memory.propose"
    APPROVE = "memory.approve"
    SUPERSEDE = "memory.supersede"
    IMPROVE = "memory.improve"
    FORGET = "memory.forget"
    REBUILD = "memory.rebuild"
    EXPORT = "memory.export"
    IMPORT = "memory.import"
    EXPLAIN = "memory.explain"


class McpToolName(StrEnum):
    HEALTH = "sys4ai_memory_health"
    RECALL = "sys4ai_memory_recall"
    GET = "sys4ai_memory_get"
    GRAPH = "sys4ai_memory_graph"
    PROPOSE = "sys4ai_memory_propose"
    EXPLAIN = "sys4ai_memory_explain"
    APPROVE = "sys4ai_memory_approve"
    IMPROVE = "sys4ai_memory_improve"
    FORGET = "sys4ai_memory_forget"
    REBUILD = "sys4ai_memory_rebuild"
    EXPORT = "sys4ai_memory_export"
    IMPORT = "sys4ai_memory_import"


class CapabilityDefinition(ContractModel):
    api_version: ApiVersion
    name: CapabilityName
    description: NonEmptyString


class OperationDefinition(ContractModel):
    api_version: ApiVersion
    name: OperationName
    purpose: NonEmptyString
    mutating: bool
    mutation_scope: NonEmptyString | None
    destructive: bool
    required_permission: Permission
    required_capabilities: tuple[CapabilityName, ...]


class McpAnnotations(ContractModel):
    read_only: bool
    mutating: bool
    destructive: bool


class McpToolDefinition(ContractModel):
    api_version: ApiVersion
    name: McpToolName
    operation: OperationName
    description: NonEmptyString
    default_enabled: bool
    privileged: bool
    annotations: McpAnnotations


def _capability(name: CapabilityName, description: str) -> CapabilityDefinition:
    return CapabilityDefinition(api_version=API_VERSION, name=name, description=description)


CAPABILITY_CATALOG = (
    _capability(CapabilityName.SERVICE_HEALTH, "Inspect service and dependency health."),
    _capability(CapabilityName.SOURCE_REGISTRY, "Register, list, and explain source policy."),
    _capability(CapabilityName.INGESTION, "Normalize and synchronize registered sources."),
    _capability(CapabilityName.EXACT, "Retrieve literal identifiers and exact source text."),
    _capability(CapabilityName.LEXICAL, "Retrieve token, phrase, prefix, and field matches."),
    _capability(CapabilityName.SEMANTIC, "Retrieve conceptual and paraphrased matches."),
    _capability(CapabilityName.GRAPH, "Retrieve typed relations and authorized paths."),
    _capability(CapabilityName.TEMPORAL, "Resolve current and historical record states."),
    _capability(CapabilityName.TYPED_WRITES, "Validate and stage typed write proposals."),
    _capability(CapabilityName.APPROVAL, "Approve or reject staged proposals."),
    _capability(CapabilityName.LIFECYCLE, "Supersede, expire, withdraw, or erase records."),
    _capability(CapabilityName.IMPROVEMENT, "Apply auditable derived-memory feedback."),
    _capability(CapabilityName.REBUILD, "Reconstruct derived memory from registered sources."),
    _capability(CapabilityName.PORTABLE_EXPORT, "Create a provider-neutral memory package."),
    _capability(CapabilityName.PORTABLE_IMPORT, "Validate and import a memory package."),
    _capability(
        CapabilityName.PROVENANCE_EXPLANATION,
        "Explain provenance, authority, status, and ranking.",
    ),
)


def _operation(
    name: OperationName,
    purpose: str,
    *,
    mutating: bool,
    mutation_scope: str | None,
    destructive: bool,
    permission: Permission,
    capabilities: tuple[CapabilityName, ...],
) -> OperationDefinition:
    return OperationDefinition(
        api_version=API_VERSION,
        name=name,
        purpose=purpose,
        mutating=mutating,
        mutation_scope=mutation_scope,
        destructive=destructive,
        required_permission=permission,
        required_capabilities=capabilities,
    )


PUBLIC_OPERATION_CATALOG = (
    _operation(
        OperationName.HEALTH,
        "Report service, index, registry, provider, and drift status.",
        mutating=False,
        mutation_scope=None,
        destructive=False,
        permission=Permission.READ,
        capabilities=(CapabilityName.SERVICE_HEALTH,),
    ),
    _operation(
        OperationName.SOURCES_LIST,
        "List visible registered sources.",
        mutating=False,
        mutation_scope=None,
        destructive=False,
        permission=Permission.READ,
        capabilities=(CapabilityName.SOURCE_REGISTRY,),
    ),
    _operation(
        OperationName.SOURCES_EXPLAIN,
        "Explain why a path or URI is included or excluded.",
        mutating=False,
        mutation_scope=None,
        destructive=False,
        permission=Permission.READ,
        capabilities=(CapabilityName.SOURCE_REGISTRY,),
    ),
    _operation(
        OperationName.SYNC,
        "Incrementally synchronize registered sources.",
        mutating=True,
        mutation_scope="derived only",
        destructive=False,
        permission=Permission.WRITE_DERIVED,
        capabilities=(CapabilityName.SOURCE_REGISTRY, CapabilityName.INGESTION),
    ),
    _operation(
        OperationName.RECALL,
        "Retrieve an authorized evidence bundle.",
        mutating=False,
        mutation_scope=None,
        destructive=False,
        permission=Permission.READ,
        capabilities=(
            CapabilityName.EXACT,
            CapabilityName.LEXICAL,
            CapabilityName.SEMANTIC,
            CapabilityName.GRAPH,
            CapabilityName.TEMPORAL,
        ),
    ),
    _operation(
        OperationName.GET,
        "Retrieve one record by stable ID.",
        mutating=False,
        mutation_scope=None,
        destructive=False,
        permission=Permission.READ,
        capabilities=(CapabilityName.EXACT,),
    ),
    _operation(
        OperationName.GRAPH,
        "Retrieve authorized relations or graph paths.",
        mutating=False,
        mutation_scope=None,
        destructive=False,
        permission=Permission.READ,
        capabilities=(CapabilityName.GRAPH,),
    ),
    _operation(
        OperationName.PROPOSE,
        "Submit a typed write proposal.",
        mutating=True,
        mutation_scope="staged",
        destructive=False,
        permission=Permission.PROPOSE,
        capabilities=(CapabilityName.TYPED_WRITES,),
    ),
    _operation(
        OperationName.APPROVE,
        "Approve or reject a staged proposal.",
        mutating=True,
        mutation_scope="privileged",
        destructive=False,
        permission=Permission.APPROVE,
        capabilities=(CapabilityName.APPROVAL,),
    ),
    _operation(
        OperationName.SUPERSEDE,
        "Link a replacement to an earlier record.",
        mutating=True,
        mutation_scope="derived",
        destructive=False,
        permission=Permission.WRITE_DERIVED,
        capabilities=(CapabilityName.LIFECYCLE,),
    ),
    _operation(
        OperationName.IMPROVE,
        "Apply feedback or derived provider-side improvement.",
        mutating=True,
        mutation_scope="derived",
        destructive=False,
        permission=Permission.WRITE_DERIVED,
        capabilities=(CapabilityName.IMPROVEMENT,),
    ),
    _operation(
        OperationName.FORGET,
        "Expire, withdraw, delete, or privacy-erase under policy.",
        mutating=True,
        mutation_scope="destructive",
        destructive=True,
        permission=Permission.DELETE,
        capabilities=(CapabilityName.LIFECYCLE,),
    ),
    _operation(
        OperationName.REBUILD,
        "Reconstruct derived memory from canonical sources.",
        mutating=True,
        mutation_scope="administrative",
        destructive=True,
        permission=Permission.REBUILD,
        capabilities=(CapabilityName.REBUILD,),
    ),
    _operation(
        OperationName.EXPORT,
        "Create a portable provider-neutral package.",
        mutating=True,
        mutation_scope="artifact creation",
        destructive=False,
        permission=Permission.SHARE,
        capabilities=(CapabilityName.PORTABLE_EXPORT,),
    ),
    _operation(
        OperationName.IMPORT,
        "Validate and import a portable package.",
        mutating=True,
        mutation_scope="administrative",
        destructive=True,
        permission=Permission.ADMINISTER,
        capabilities=(CapabilityName.PORTABLE_IMPORT,),
    ),
    _operation(
        OperationName.EXPLAIN,
        "Explain provenance, status, authority, and ranking for a record.",
        mutating=False,
        mutation_scope=None,
        destructive=False,
        permission=Permission.READ,
        capabilities=(CapabilityName.PROVENANCE_EXPLANATION,),
    ),
)


def _mcp_tool(
    name: McpToolName,
    operation: OperationName,
    description: str,
    *,
    default_enabled: bool,
    privileged: bool,
    read_only: bool,
    mutating: bool,
    destructive: bool,
) -> McpToolDefinition:
    return McpToolDefinition(
        api_version=API_VERSION,
        name=name,
        operation=operation,
        description=description,
        default_enabled=default_enabled,
        privileged=privileged,
        annotations=McpAnnotations(
            read_only=read_only,
            mutating=mutating,
            destructive=destructive,
        ),
    )


MCP_TOOL_CATALOG = (
    _mcp_tool(
        McpToolName.HEALTH,
        OperationName.HEALTH,
        "Read memory service health and drift status.",
        default_enabled=True,
        privileged=False,
        read_only=True,
        mutating=False,
        destructive=False,
    ),
    _mcp_tool(
        McpToolName.RECALL,
        OperationName.RECALL,
        "Retrieve authorized source-backed evidence.",
        default_enabled=True,
        privileged=False,
        read_only=True,
        mutating=False,
        destructive=False,
    ),
    _mcp_tool(
        McpToolName.GET,
        OperationName.GET,
        "Read one memory record by stable ID.",
        default_enabled=True,
        privileged=False,
        read_only=True,
        mutating=False,
        destructive=False,
    ),
    _mcp_tool(
        McpToolName.GRAPH,
        OperationName.GRAPH,
        "Read authorized typed relations or graph paths.",
        default_enabled=True,
        privileged=False,
        read_only=True,
        mutating=False,
        destructive=False,
    ),
    _mcp_tool(
        McpToolName.PROPOSE,
        OperationName.PROPOSE,
        "Stage a typed write proposal for policy evaluation.",
        default_enabled=True,
        privileged=False,
        read_only=False,
        mutating=True,
        destructive=False,
    ),
    _mcp_tool(
        McpToolName.EXPLAIN,
        OperationName.EXPLAIN,
        "Read provenance, authority, status, and ranking explanations.",
        default_enabled=True,
        privileged=False,
        read_only=True,
        mutating=False,
        destructive=False,
    ),
    _mcp_tool(
        McpToolName.APPROVE,
        OperationName.APPROVE,
        "Approve or reject a staged proposal with privileged authority.",
        default_enabled=False,
        privileged=True,
        read_only=False,
        mutating=True,
        destructive=False,
    ),
    _mcp_tool(
        McpToolName.IMPROVE,
        OperationName.IMPROVE,
        "Apply privileged derived-memory feedback.",
        default_enabled=False,
        privileged=True,
        read_only=False,
        mutating=True,
        destructive=False,
    ),
    _mcp_tool(
        McpToolName.FORGET,
        OperationName.FORGET,
        "Run a policy-controlled destructive lifecycle operation.",
        default_enabled=False,
        privileged=True,
        read_only=False,
        mutating=True,
        destructive=True,
    ),
    _mcp_tool(
        McpToolName.REBUILD,
        OperationName.REBUILD,
        "Rebuild derived memory with administrative permission.",
        default_enabled=False,
        privileged=True,
        read_only=False,
        mutating=True,
        destructive=True,
    ),
    _mcp_tool(
        McpToolName.EXPORT,
        OperationName.EXPORT,
        "Create a policy-filtered portable memory package.",
        default_enabled=False,
        privileged=True,
        read_only=False,
        mutating=True,
        destructive=False,
    ),
    _mcp_tool(
        McpToolName.IMPORT,
        OperationName.IMPORT,
        "Validate and import a portable memory package.",
        default_enabled=False,
        privileged=True,
        read_only=False,
        mutating=True,
        destructive=True,
    ),
)


def operation_by_name(name: OperationName) -> OperationDefinition:
    return next(operation for operation in PUBLIC_OPERATION_CATALOG if operation.name is name)


def mcp_tool_by_name(name: McpToolName) -> McpToolDefinition:
    return next(tool for tool in MCP_TOOL_CATALOG if tool.name is name)
