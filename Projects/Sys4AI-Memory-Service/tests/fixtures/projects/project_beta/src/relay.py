"""Canonical fixture code for project Beta."""

BETA_ROUTE_LABEL = "BETA-ROUTE-7C4B"


def resolve_beta_route(index_ready: bool) -> str:
    """Return the active Beta route only when its exact index is ready."""
    if not index_ready:
        raise RuntimeError("beta exact index unavailable")
    return BETA_ROUTE_LABEL
