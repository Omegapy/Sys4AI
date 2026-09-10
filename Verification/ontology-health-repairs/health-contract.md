# Health result compatibility contract

Health result version 2 retains existing component details and adds
`health_schema_version: 2`, `assessment`, `aggregate`, and `ready`.
`assessment` identifies the resolved project, scope, level, observation time
and relevant input versions. `aggregate` is `ready`, `degraded`, `invalid`,
or `absent`; top-level `status` mirrors that aggregate. `ready` is true only
when every required check for that exact selection passes. Exit 0 means ready,
exit 1 means a completed non-ready health assessment, and exit 2 means invalid
request/configuration or an assessment that could not be performed. Existing
nested diagnostics remain available. Callers formerly treating exit 0 as JSON
delivery must now handle the health result and exit code together.

The default scope is `selected`: canonical integrity plus already-built derived
products and explicitly enabled optional profiles. `canonical` selects only
canonical configuration/data/evidence readiness. Explicit `--require` component
names may additionally require never-built products. Unknown component names
are rejected. Disabled/unselected optional components do not degrade readiness.

The default level is `static`: installed capability, valid configuration,
certification and current derived-state inputs are assessed without starting
services or invoking a vendor runtime. This is never an observed operational
success. `operational` additionally requires bounded representative read-only
operations for the selected runtime; unavailable, failed, timed-out or
unverified required operation is non-ready. Operations never install, download,
publish, toggle, rebuild or start a service through health.

| Selection/observation | Aggregate | Meaning |
| --- | --- | --- |
| Requested configuration absent | absent | Capability cannot be assessed |
| Invalid configuration/request | invalid | Fix the exact reported input |
| Valid neutral canonical/static capability | ready | Static capability only; runtime not exercised |
| Required selected product stale/missing/invalid | degraded | Explicit owning maintenance is needed |
| Enabled backend missing/stale certification | degraded | Existing-runtime check or authorized setup needed |
| Required runtime timeout/cancellation/failure | degraded | No completed operational result |
| Optional on-demand workbench without endpoint | ready for static selection | Service state not assessed; no running claim |
| Explicit workbench endpoint wrong/unreachable | degraded | Selected service is not verified |

Workbench observations accept only explicit loopback endpoints, use finite
timeouts and match the current project identity. Probe results retain no
credentials. Historical evidence integrity and applicability to current source
versions are separate; missing proof remains unsupported. A static healthy
historical-only record does not establish a verified-current claim.

Read results include observation time and exact relevant input context rather
than a reusable promise. Publication/setup/maintenance receipts describe their
committed boundary separately from current operational readiness; invalidated
required products are reported with precise next operations, never silently
repaired without scope.
