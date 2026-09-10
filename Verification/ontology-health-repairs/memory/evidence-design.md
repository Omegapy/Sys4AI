# Memory repair design and host handoff

Record schema v1, config schema v1, the original receipt and original provenance
remain unchanged. Verification receipt schema v1 gains optional artifact
`retained_path` and receipt `applicability` fields. New `verified_outcome`
publications require explicit current applicability and retained exact observed
bytes. Legacy records remain readable and report durability honestly; legacy
failure/performed/cancelled publication remains compatible.

Historical proof companions are optional exact proof locators under the existing
governed evidence path. They have no current-verification authority. A matching
companion uses the original receipt digest in its filename, binds original path
and digest, and preserves the ordered observed artifact path/digest list. Wrong
receipt/artifact binding, altered archives, unsafe paths and absent proof remain
warning/error diagnostics. Intact history with changed live inputs emits info
applicability diagnostics. Strict current packets still exclude diagnostic-bearing
claims. Historical ontology consumers can accept info-only supported evidence
while preserving the current-applicability limitation; evidence assessment hashes
must participate in derived-input freshness.

Memory health schema v2 uses the shared `health-contract.md`: canonical/selected
scope, static/operational level, explicit required components, aggregate status and
exit 0/1/2. Existing backend, counts and diagnostics remain. Readiness checks are
read-only. Projection/index absence after a prior build remains required, current
corpus additions are detected, producer versions are explicit, and index bytes,
certification, profile, model and runtime prerequisites remain distinct checks.
Operational health uses the existing worker and a bounded hybrid query; it never
starts a service or provisions a runtime. Semantic-query success does not establish
write dispatch coverage.

Canonical publication/capture receipts stay separate from current derived
readiness. Out-of-scope required maintenance is explicit pending work. Reindex
finishes and records its committed product boundary before its final operational
check; a timeout after commit retains that boundary and returns non-ready pending
status. Current inputs are checked again after the probe. Pre-commit interrupted
rebuilds preserve the existing exact recovery route. No new ledger or daemon was
added.

Host sequence: finish exact source/root adoption and bindings; verify original
and retained hashes; publish the reviewed companion only to its named absent
destination; prepare a fresh scoped grant for the exact supersession payload;
run the installed supersede helper; reinspect old/successor evidence; authorize
memory reindex against the final source/canonical/config bytes; then refresh
ontology associations and other affected derived products in their owning order.
Run selected actual-runtime health/query acceptance after that final boundary.
No memory publication grant implicitly supplies reindex or ontology scope.
