"""Canonical fixture code for project Alpha."""

ALPHA_ROUTE_LABEL = "ALPHA-ROUTE-9F2A"


def resolve_alpha_route(index_ready: bool) -> str:
    """Return the active Alpha route only when its exact index is ready."""
    if not index_ready:
        raise RuntimeError("alpha exact index unavailable")
    return ALPHA_ROUTE_LABEL
