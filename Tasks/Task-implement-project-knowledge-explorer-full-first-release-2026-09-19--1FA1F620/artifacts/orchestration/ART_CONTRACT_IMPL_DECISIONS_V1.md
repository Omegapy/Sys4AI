# TASK-002 implementation decisions and observed evidence

Current status: **TASK-002 implementation checks complete; awaiting owning-manager acceptance**. All 62 locked package archives and 70 license/notice members have been inspected; 19 exact unique texts are preserved. Installed Node/npm/TypeScript/Vite/Rolldown and the native dependency smoke checks passed on darwin-arm64. The download and package-inspection blockers recorded below are resolved by host provisioning and the subsequent direct checks. Production service/frontend/build/browser/accessibility/user acceptance remains later plan work.

The current live reusable schema is SHA256 `8e6d0ceb47c98e77d518f4d7c935986ab6982d1a1c15e12377a726e90fbbb7a4`. The corrected maximum fixed error envelope is **659 bytes**, from all 31 codes crossed with all six operations (186 combinations). Earlier 658-byte observations tested only neighborhood and are retained as narrower historical evidence, not the global maximum. The final completion section below records current delivery evidence. Package pins and all accepted runtime rules remain unchanged.

## Retained earlier inspection history

The earlier partial statuses, unavailable dependencies, prior schema hashes and narrower error-size checks below are historical. They are preserved for evidence continuity and superseded where the final completion section supplies direct current observations.


Status: **partial; CONTRACTS is not verified**. The accepted design has been transcribed into the normative contract and a closed schema, and npm generated a real lock. Actual package artifact, installed-bin, license-text and transitive-hook-body checks remain incomplete. No production build or runtime behavior is claimed.

## Exact authority and scope

PLAN-20260920-9B9964BA revision 1 remains unchanged at SHA256 `35d6fe54aaa9871867d5fe1d1f0d4e96e58790a0baf8e9585561f75672b6c78b`. Accepted synthesis SHA256 `21238a8c00030d433315c8ffa3abb5237e8001fea0cee6b9f9153550e1d64785`; acceptance `ACC_CONTRACTS_V1`; assignment `CONTRACTS_IMPLEMENT_G3`. All eight frozen assignment input hashes matched before work. The only persistent worker writes are the seven TASK-002 paths. Staging/scripts/cache are disposable under `/tmp/explorer-contracts-implement-g3`. No root/Template package, canonical knowledge, memory, Task state, initializer edition or Git publication was intentionally written by this worker. The automatic Template pipeline remains its separate owner.

## Runtime toolchain and dependency evidence

Directly observed Node `v25.9.0`, npm `11.12.1`; packageManager is `npm@11.12.1`. Direct pins remain Cytoscape3.34.3, Vite8.3.0 and TypeScript7.0.2. Exact scripts are typecheck=`tsc --noEmit`, build=`npm run typecheck && vite build`, package:runtime=`node scripts/package-runtime.mjs`. Packaging source and a real production build belong to later tasks. No global compiler/npx fallback was used.

Observed command, from disposable staging:

```sh
npm install --package-lock-only --ignore-scripts --no-audit --no-fund --cache /tmp/explorer-contracts-implement-g3/npm-cache
```

Exit 0, output `up to date in 7s`; npm generated lockfileVersion3 with62 dependency packages plus the root. All62 tarball/integrity values matched exact-version entries in cached registry metadata whose cache-integrity hashes were checked. The three direct integrities match the frozen official evidence. This establishes a generated metadata resolution, not downloaded artifact integrity verification.

The subsequent sandbox command `npm ci --ignore-scripts --no-audit --no-fund --cache /tmp/explorer-contracts-implement-g3/npm-cache` exited1 with `npm error Exit handler never called!` and no successful installation. A separate exact-URL `npm pack --ignore-scripts --json --pack-destination /tmp/explorer-contracts-implement-g3/tarballs --cache /tmp/explorer-contracts-implement-g3/npm-cache ...` failed `ENOTFOUND registry.npmjs.org`. These are install/network/tool observations, not evidence of compiler or renderer incompatibility. The full exact pack argv is retained below.

The same required npm ci command was submitted with `require_escalated`, scoped justification and npm-ci prefix. It remained pending approval; the tool later returned `aborted by user after 148.6s`. The observed causal action was the manager calling native interrupt_agent to release that unresolved wait and permit independent work. No direct user cancellation message or automatic approval-review rejection reason was received. The user's scoped authorization persists, while actual download permission/execution remained unresolved. The interrupted command was not replayed or bypassed.

Reopened staging had zero tarballs and zero installed package.json files. The cache contains registry metadata, not downloaded package archives. TypeScript metadata declares bin `tsc: bin/tsc`; the executable itself remains unobserved. Hook metadata is recorded below, but no hook body or script execution is inferred. THIRD_PARTY_NOTICES.md is marked incomplete; later offline inspection added seven actual cached license texts without inventing the missing55.

Pending actual command (same staging directory):

```sh
npm ci --ignore-scripts --no-audit --no-fund --cache /tmp/explorer-contracts-implement-g3/npm-cache
```

Exact pack argv, pending artifact inspection only:

```json
[
  "npm",
  "pack",
  "--ignore-scripts",
  "--json",
  "--pack-destination",
  "/tmp/explorer-contracts-implement-g3/tarballs",
  "--cache",
  "/tmp/explorer-contracts-implement-g3/npm-cache",
  "https://registry.npmjs.org/@oxc-project/types/-/types-0.150.0.tgz",
  "https://registry.npmjs.org/@rolldown/binding-android-arm-eabi/-/binding-android-arm-eabi-1.2.9.tgz",
  "https://registry.npmjs.org/@rolldown/binding-android-arm64/-/binding-android-arm64-1.2.9.tgz",
  "https://registry.npmjs.org/@rolldown/binding-darwin-arm64/-/binding-darwin-arm64-1.2.9.tgz",
  "https://registry.npmjs.org/@rolldown/binding-darwin-x64/-/binding-darwin-x64-1.2.9.tgz",
  "https://registry.npmjs.org/@rolldown/binding-freebsd-x64/-/binding-freebsd-x64-1.2.9.tgz",
  "https://registry.npmjs.org/@rolldown/binding-linux-arm-gnueabihf/-/binding-linux-arm-gnueabihf-1.2.9.tgz",
  "https://registry.npmjs.org/@rolldown/binding-linux-arm64-gnu/-/binding-linux-arm64-gnu-1.2.9.tgz",
  "https://registry.npmjs.org/@rolldown/binding-linux-arm64-musl/-/binding-linux-arm64-musl-1.2.9.tgz",
  "https://registry.npmjs.org/@rolldown/binding-linux-ppc64-gnu/-/binding-linux-ppc64-gnu-1.2.9.tgz",
  "https://registry.npmjs.org/@rolldown/binding-linux-s390x-gnu/-/binding-linux-s390x-gnu-1.2.9.tgz",
  "https://registry.npmjs.org/@rolldown/binding-linux-x64-gnu/-/binding-linux-x64-gnu-1.2.9.tgz",
  "https://registry.npmjs.org/@rolldown/binding-linux-x64-musl/-/binding-linux-x64-musl-1.2.9.tgz",
  "https://registry.npmjs.org/@rolldown/binding-openharmony-arm64/-/binding-openharmony-arm64-1.2.9.tgz",
  "https://registry.npmjs.org/@rolldown/binding-win32-arm64-msvc/-/binding-win32-arm64-msvc-1.2.9.tgz",
  "https://registry.npmjs.org/@rolldown/binding-win32-x64-msvc/-/binding-win32-x64-msvc-1.2.9.tgz",
  "https://registry.npmjs.org/@rolldown/pluginutils/-/pluginutils-1.0.1.tgz",
  "https://registry.npmjs.org/@typescript/typescript-aix-ppc64/-/typescript-aix-ppc64-7.0.2.tgz",
  "https://registry.npmjs.org/@typescript/typescript-darwin-arm64/-/typescript-darwin-arm64-7.0.2.tgz",
  "https://registry.npmjs.org/@typescript/typescript-darwin-x64/-/typescript-darwin-x64-7.0.2.tgz",
  "https://registry.npmjs.org/@typescript/typescript-freebsd-arm64/-/typescript-freebsd-arm64-7.0.2.tgz",
  "https://registry.npmjs.org/@typescript/typescript-freebsd-x64/-/typescript-freebsd-x64-7.0.2.tgz",
  "https://registry.npmjs.org/@typescript/typescript-linux-arm/-/typescript-linux-arm-7.0.2.tgz",
  "https://registry.npmjs.org/@typescript/typescript-linux-arm64/-/typescript-linux-arm64-7.0.2.tgz",
  "https://registry.npmjs.org/@typescript/typescript-linux-loong64/-/typescript-linux-loong64-7.0.2.tgz",
  "https://registry.npmjs.org/@typescript/typescript-linux-mips64el/-/typescript-linux-mips64el-7.0.2.tgz",
  "https://registry.npmjs.org/@typescript/typescript-linux-ppc64/-/typescript-linux-ppc64-7.0.2.tgz",
  "https://registry.npmjs.org/@typescript/typescript-linux-riscv64/-/typescript-linux-riscv64-7.0.2.tgz",
  "https://registry.npmjs.org/@typescript/typescript-linux-s390x/-/typescript-linux-s390x-7.0.2.tgz",
  "https://registry.npmjs.org/@typescript/typescript-linux-x64/-/typescript-linux-x64-7.0.2.tgz",
  "https://registry.npmjs.org/@typescript/typescript-netbsd-arm64/-/typescript-netbsd-arm64-7.0.2.tgz",
  "https://registry.npmjs.org/@typescript/typescript-netbsd-x64/-/typescript-netbsd-x64-7.0.2.tgz",
  "https://registry.npmjs.org/@typescript/typescript-openbsd-arm64/-/typescript-openbsd-arm64-7.0.2.tgz",
  "https://registry.npmjs.org/@typescript/typescript-openbsd-x64/-/typescript-openbsd-x64-7.0.2.tgz",
  "https://registry.npmjs.org/@typescript/typescript-sunos-x64/-/typescript-sunos-x64-7.0.2.tgz",
  "https://registry.npmjs.org/@typescript/typescript-win32-arm64/-/typescript-win32-arm64-7.0.2.tgz",
  "https://registry.npmjs.org/@typescript/typescript-win32-x64/-/typescript-win32-x64-7.0.2.tgz",
  "https://registry.npmjs.org/cytoscape/-/cytoscape-3.34.3.tgz",
  "https://registry.npmjs.org/detect-libc/-/detect-libc-2.1.2.tgz",
  "https://registry.npmjs.org/fdir/-/fdir-6.5.0.tgz",
  "https://registry.npmjs.org/fsevents/-/fsevents-2.3.3.tgz",
  "https://registry.npmjs.org/lightningcss/-/lightningcss-1.33.0.tgz",
  "https://registry.npmjs.org/lightningcss-android-arm64/-/lightningcss-android-arm64-1.33.0.tgz",
  "https://registry.npmjs.org/lightningcss-darwin-arm64/-/lightningcss-darwin-arm64-1.33.0.tgz",
  "https://registry.npmjs.org/lightningcss-darwin-x64/-/lightningcss-darwin-x64-1.33.0.tgz",
  "https://registry.npmjs.org/lightningcss-freebsd-x64/-/lightningcss-freebsd-x64-1.33.0.tgz",
  "https://registry.npmjs.org/lightningcss-linux-arm-gnueabihf/-/lightningcss-linux-arm-gnueabihf-1.33.0.tgz",
  "https://registry.npmjs.org/lightningcss-linux-arm64-gnu/-/lightningcss-linux-arm64-gnu-1.33.0.tgz",
  "https://registry.npmjs.org/lightningcss-linux-arm64-musl/-/lightningcss-linux-arm64-musl-1.33.0.tgz",
  "https://registry.npmjs.org/lightningcss-linux-x64-gnu/-/lightningcss-linux-x64-gnu-1.33.0.tgz",
  "https://registry.npmjs.org/lightningcss-linux-x64-musl/-/lightningcss-linux-x64-musl-1.33.0.tgz",
  "https://registry.npmjs.org/lightningcss-win32-arm64-msvc/-/lightningcss-win32-arm64-msvc-1.33.0.tgz",
  "https://registry.npmjs.org/lightningcss-win32-x64-msvc/-/lightningcss-win32-x64-msvc-1.33.0.tgz",
  "https://registry.npmjs.org/nanoid/-/nanoid-3.3.19.tgz",
  "https://registry.npmjs.org/picocolors/-/picocolors-1.1.1.tgz",
  "https://registry.npmjs.org/picomatch/-/picomatch-4.0.7.tgz",
  "https://registry.npmjs.org/postcss/-/postcss-8.5.28.tgz",
  "https://registry.npmjs.org/rolldown/-/rolldown-1.2.9.tgz",
  "https://registry.npmjs.org/source-map-js/-/source-map-js-1.2.1.tgz",
  "https://registry.npmjs.org/tinyglobby/-/tinyglobby-0.2.17.tgz",
  "https://registry.npmjs.org/typescript/-/typescript-7.0.2.tgz",
  "https://registry.npmjs.org/vite/-/vite-8.3.0.tgz"
]
```

## Contract and schema checks

Historical evidence: this section and the earlier final-file checks target schema SHA256 `352b4c34f0582bb6f90ffb687c5537609ea8c8b2d6515132705763633987d1c6`. The placement correction and current schema validation are recorded at the end of this file; the earlier observations are retained without being represented as current-byte evidence.

The schema has126 named definitions,31 fixed error variants and20 lowerable configuration-limit keys. Static inspection resolves418 local references and finds no open protocol/configuration objects. CanonicalJson is the sole intentional arbitrary-key data value; operation scope objects are closed by discriminated branches. Duplicate JSON keys, numeric-token types, full UTF-8 budgets, canonical source membership, identity equality, monotonic HMAC scope and runtime coherence remain explicit semantic-validator obligations. No runtime validator is implemented in this task.

A disposable independent subset evaluator exercised123 targeted cases covering neutral/invalid configuration, unknown keys, exact ID/path shapes, booleans/floats as integers, search sorting/filters/snapshots, empty chunks, process-part mixing, fixed/pre-auth errors and arbitrary error-message rejection. It is not a full Draft2020-12 conformance validator. The initial inspected roots lacked a validator. A later authorized read-only check used the already installed `.venv-memory-pilot/bin/python -B` with jsonschema4.26.0: Draft202012Validator.check_schema passed, and all123 targeted cases were rerun through the full validator with the contract-required exact integer-token and UTF-8-byte semantic extensions. No memory service, corpus or configuration was used or changed. All31 fixed authenticated error envelopes were serialized with the longest request ID/operation and largest limits; maximum658 UTF-8 bytes fits1024.

The actual detailed check report follows:

```json
{
  "level": "Draft 2020-12 meta-schema validation and targeted cases with required integer/UTF-8 semantic checks",
  "full_draft202012_validator": "jsonschema 4.26.0; Draft202012Validator.check_schema passed; targeted cases use strict integer-token and UTF-8 semantic extensions",
  "schema_sha256": "352b4c34f0582bb6f90ffb687c5537609ea8c8b2d6515132705763633987d1c6",
  "definitions": 126,
  "local_references_checked": 418,
  "unclosed_protocol_objects": [],
  "targeted_cases": 123,
  "cases": [
    {
      "name": "neutral config",
      "result": "pass",
      "definition": "configuration"
    },
    {
      "name": "unknown root",
      "result": "pass",
      "definition": "configuration"
    },
    {
      "name": "unknown nested limit",
      "result": "pass",
      "definition": "configuration"
    },
    {
      "name": "boolean limit",
      "result": "pass",
      "definition": "configuration"
    },
    {
      "name": "float limit",
      "result": "pass",
      "definition": "configuration"
    },
    {
      "name": "lower response below minimum",
      "result": "pass",
      "definition": "configuration"
    },
    {
      "name": "nonconfig request rejected",
      "result": "pass",
      "definition": "configuration"
    },
    {
      "name": "label control rejected",
      "result": "pass",
      "definition": "DisplayLabel"
    },
    {
      "name": "blank display label rejected",
      "result": "pass",
      "definition": "DisplayLabel"
    },
    {
      "name": "invalid ID case preserved",
      "result": "pass",
      "definition": "Id"
    },
    {
      "name": "unsafe path ../x",
      "result": "pass",
      "definition": "RelativePath"
    },
    {
      "name": "unsafe path a/../x",
      "result": "pass",
      "definition": "RelativePath"
    },
    {
      "name": "unsafe path a//b",
      "result": "pass",
      "definition": "RelativePath"
    },
    {
      "name": "unsafe path /etc/passwd",
      "result": "pass",
      "definition": "RelativePath"
    },
    {
      "name": "unsafe path a/./b",
      "result": "pass",
      "definition": "RelativePath"
    },
    {
      "name": "unsafe path a\\b",
      "result": "pass",
      "definition": "RelativePath"
    },
    {
      "name": "safe relative path",
      "result": "pass",
      "definition": "RelativePath"
    },
    {
      "name": "search request",
      "result": "pass",
      "definition": "SearchRequest"
    },
    {
      "name": "nonempty label sort rejected",
      "result": "pass",
      "definition": "SearchRequest"
    },
    {
      "name": "empty browse",
      "result": "pass",
      "definition": "SearchRequest"
    },
    {
      "name": "empty lifecycle rejected",
      "result": "pass",
      "definition": "SearchRequest"
    },
    {
      "name": "source selector injection rejected",
      "result": "pass",
      "definition": "SearchRequest"
    },
    {
      "name": "search snapshot required",
      "result": "pass",
      "definition": "SearchRequest"
    },
    {
      "name": "context initial request",
      "result": "pass",
      "definition": "ContextRequest"
    },
    {
      "name": "header continuation rejected",
      "result": "pass",
      "definition": "EntryRequest"
    },
    {
      "name": "nonempty Unicode chunk",
      "result": "pass",
      "definition": "TextChunk"
    },
    {
      "name": "empty advancing chunk rejected",
      "result": "pass",
      "definition": "TextChunk"
    },
    {
      "name": "process text",
      "result": "pass",
      "definition": "ProcessField"
    },
    {
      "name": "mixed process parts rejected",
      "result": "pass",
      "definition": "ProcessField"
    },
    {
      "name": "missing header rejected",
      "result": "pass",
      "definition": "EntryData"
    },
    {
      "name": "fixed error invalid_request",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "preauth error invalid_request",
      "result": "pass",
      "definition": "PreAuthErrorResponse"
    },
    {
      "name": "error text closed invalid_request",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "fixed error cursor_invalid",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "preauth error cursor_invalid",
      "result": "pass",
      "definition": "PreAuthErrorResponse"
    },
    {
      "name": "error text closed cursor_invalid",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "fixed error request_too_large",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "preauth error request_too_large",
      "result": "pass",
      "definition": "PreAuthErrorResponse"
    },
    {
      "name": "error text closed request_too_large",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "fixed error content_type_invalid",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "preauth error content_type_invalid",
      "result": "pass",
      "definition": "PreAuthErrorResponse"
    },
    {
      "name": "error text closed content_type_invalid",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "fixed error session_expired",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "preauth error session_expired",
      "result": "pass",
      "definition": "PreAuthErrorResponse"
    },
    {
      "name": "error text closed session_expired",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "fixed error session_invalid",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "preauth error session_invalid",
      "result": "pass",
      "definition": "PreAuthErrorResponse"
    },
    {
      "name": "error text closed session_invalid",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "fixed error host_forbidden",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "preauth error host_forbidden",
      "result": "pass",
      "definition": "PreAuthErrorResponse"
    },
    {
      "name": "error text closed host_forbidden",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "fixed error origin_forbidden",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "preauth error origin_forbidden",
      "result": "pass",
      "definition": "PreAuthErrorResponse"
    },
    {
      "name": "error text closed origin_forbidden",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "fixed error csrf_forbidden",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "preauth error csrf_forbidden",
      "result": "pass",
      "definition": "PreAuthErrorResponse"
    },
    {
      "name": "error text closed csrf_forbidden",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "fixed error source_forbidden",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "preauth error source_forbidden",
      "result": "pass",
      "definition": "PreAuthErrorResponse"
    },
    {
      "name": "error text closed source_forbidden",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "fixed error resource_forbidden",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "preauth error resource_forbidden",
      "result": "pass",
      "definition": "PreAuthErrorResponse"
    },
    {
      "name": "error text closed resource_forbidden",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "fixed error identity_unavailable",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "preauth error identity_unavailable",
      "result": "pass",
      "definition": "PreAuthErrorResponse"
    },
    {
      "name": "error text closed identity_unavailable",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "fixed error endpoint_unavailable",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "preauth error endpoint_unavailable",
      "result": "pass",
      "definition": "PreAuthErrorResponse"
    },
    {
      "name": "error text closed endpoint_unavailable",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "fixed error method_forbidden",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "preauth error method_forbidden",
      "result": "pass",
      "definition": "PreAuthErrorResponse"
    },
    {
      "name": "error text closed method_forbidden",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "fixed error snapshot_changed",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "preauth error snapshot_changed",
      "result": "pass",
      "definition": "PreAuthErrorResponse"
    },
    {
      "name": "error text closed snapshot_changed",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "fixed error cursor_scope_changed",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "preauth error cursor_scope_changed",
      "result": "pass",
      "definition": "PreAuthErrorResponse"
    },
    {
      "name": "error text closed cursor_scope_changed",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "fixed error cursor_expired",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "preauth error cursor_expired",
      "result": "pass",
      "definition": "PreAuthErrorResponse"
    },
    {
      "name": "error text closed cursor_expired",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "fixed error source_observation_changed",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "preauth error source_observation_changed",
      "result": "pass",
      "definition": "PreAuthErrorResponse"
    },
    {
      "name": "error text closed source_observation_changed",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "fixed error package_changed",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "preauth error package_changed",
      "result": "pass",
      "definition": "PreAuthErrorResponse"
    },
    {
      "name": "error text closed package_changed",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "fixed error canonical_invalid",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "preauth error canonical_invalid",
      "result": "pass",
      "definition": "PreAuthErrorResponse"
    },
    {
      "name": "error text closed canonical_invalid",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "fixed error presentation_invalid",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "preauth error presentation_invalid",
      "result": "pass",
      "definition": "PreAuthErrorResponse"
    },
    {
      "name": "error text closed presentation_invalid",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "fixed error configuration_needed",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "preauth error configuration_needed",
      "result": "pass",
      "definition": "PreAuthErrorResponse"
    },
    {
      "name": "error text closed configuration_needed",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "fixed error identity_mismatch",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "preauth error identity_mismatch",
      "result": "pass",
      "definition": "PreAuthErrorResponse"
    },
    {
      "name": "error text closed identity_mismatch",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "fixed error source_unavailable",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "preauth error source_unavailable",
      "result": "pass",
      "definition": "PreAuthErrorResponse"
    },
    {
      "name": "error text closed source_unavailable",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "fixed error source_locator_invalid",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "preauth error source_locator_invalid",
      "result": "pass",
      "definition": "PreAuthErrorResponse"
    },
    {
      "name": "error text closed source_locator_invalid",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "fixed error service_busy",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "preauth error service_busy",
      "result": "pass",
      "definition": "PreAuthErrorResponse"
    },
    {
      "name": "error text closed service_busy",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "fixed error knowledge_updating",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "preauth error knowledge_updating",
      "result": "pass",
      "definition": "PreAuthErrorResponse"
    },
    {
      "name": "error text closed knowledge_updating",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "fixed error package_incomplete",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "preauth error package_incomplete",
      "result": "pass",
      "definition": "PreAuthErrorResponse"
    },
    {
      "name": "error text closed package_incomplete",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "fixed error resource_limit",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "preauth error resource_limit",
      "result": "pass",
      "definition": "PreAuthErrorResponse"
    },
    {
      "name": "error text closed resource_limit",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "fixed error deadline_exceeded",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "preauth error deadline_exceeded",
      "result": "pass",
      "definition": "PreAuthErrorResponse"
    },
    {
      "name": "error text closed deadline_exceeded",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "fixed error internal_error",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "preauth error internal_error",
      "result": "pass",
      "definition": "PreAuthErrorResponse"
    },
    {
      "name": "error text closed internal_error",
      "result": "pass",
      "definition": "ErrorResponse"
    }
  ],
  "errors": [
    {
      "code": "invalid_request",
      "http_status": 400,
      "serialized_bytes": 628
    },
    {
      "code": "cursor_invalid",
      "http_status": 400,
      "serialized_bytes": 608
    },
    {
      "code": "request_too_large",
      "http_status": 413,
      "serialized_bytes": 627
    },
    {
      "code": "content_type_invalid",
      "http_status": 415,
      "serialized_bytes": 613
    },
    {
      "code": "session_expired",
      "http_status": 401,
      "serialized_bytes": 636
    },
    {
      "code": "session_invalid",
      "http_status": 401,
      "serialized_bytes": 621
    },
    {
      "code": "host_forbidden",
      "http_status": 403,
      "serialized_bytes": 626
    },
    {
      "code": "origin_forbidden",
      "http_status": 403,
      "serialized_bytes": 625
    },
    {
      "code": "csrf_forbidden",
      "http_status": 403,
      "serialized_bytes": 631
    },
    {
      "code": "source_forbidden",
      "http_status": 403,
      "serialized_bytes": 629
    },
    {
      "code": "resource_forbidden",
      "http_status": 403,
      "serialized_bytes": 630
    },
    {
      "code": "identity_unavailable",
      "http_status": 404,
      "serialized_bytes": 640
    },
    {
      "code": "endpoint_unavailable",
      "http_status": 404,
      "serialized_bytes": 622
    },
    {
      "code": "method_forbidden",
      "http_status": 405,
      "serialized_bytes": 629
    },
    {
      "code": "snapshot_changed",
      "http_status": 409,
      "serialized_bytes": 637
    },
    {
      "code": "cursor_scope_changed",
      "http_status": 409,
      "serialized_bytes": 640
    },
    {
      "code": "cursor_expired",
      "http_status": 409,
      "serialized_bytes": 643
    },
    {
      "code": "source_observation_changed",
      "http_status": 409,
      "serialized_bytes": 650
    },
    {
      "code": "package_changed",
      "http_status": 409,
      "serialized_bytes": 650
    },
    {
      "code": "canonical_invalid",
      "http_status": 422,
      "serialized_bytes": 630
    },
    {
      "code": "presentation_invalid",
      "http_status": 422,
      "serialized_bytes": 634
    },
    {
      "code": "configuration_needed",
      "http_status": 503,
      "serialized_bytes": 658
    },
    {
      "code": "identity_mismatch",
      "http_status": 422,
      "serialized_bytes": 633
    },
    {
      "code": "source_unavailable",
      "http_status": 422,
      "serialized_bytes": 619
    },
    {
      "code": "source_locator_invalid",
      "http_status": 422,
      "serialized_bytes": 645
    },
    {
      "code": "service_busy",
      "http_status": 429,
      "serialized_bytes": 623
    },
    {
      "code": "knowledge_updating",
      "http_status": 503,
      "serialized_bytes": 640
    },
    {
      "code": "package_incomplete",
      "http_status": 503,
      "serialized_bytes": 629
    },
    {
      "code": "resource_limit",
      "http_status": 503,
      "serialized_bytes": 652
    },
    {
      "code": "deadline_exceeded",
      "http_status": 504,
      "serialized_bytes": 624
    },
    {
      "code": "internal_error",
      "http_status": 500,
      "serialized_bytes": 626
    }
  ],
  "max_error_bytes": 658,
  "lockfile_version": 3,
  "locked_packages": 62,
  "lock_sha256": "c56e429ba8b70fe0e56ab5f879853f5267083eb7facbc0a6da36322b94afdbf9",
  "direct_integrities_match_frozen_evidence": true,
  "installed_bins": "not available",
  "runtime_behavior": "not implemented or tested"
}
```

Disposable check source hashes: `schema.py` 1c2363e4d704aa50e889562d01e7e95f57cec42c3686a6b52b558b50cf7c8267, `check_schema.py` b89b9bcee9c546f09ae390e2f466f54de8ef9fa0267c1e8871121dc75638fc1e. These are supporting scratch evidence, not shipped runtime files.

## Immutable plan target to chosen responsibility

The approved plan is unchanged. The accepted synthesis consolidates responsibilities at the following exact paths. These mappings preserve each planned task's behavior and checks; they do not silently delete a requirement or assert a runtime file exists.

| Planned target | Chosen target responsibility | Plan task |
| --- | --- | --- |
| `SKILLS-depo/ontology/scripts/ontology_explorer_search.py` | `SKILLS-depo/ontology/scripts/ontology_explorer_read.py` | TASK-005 |
| `SKILLS-depo/ontology/scripts/ontology_explorer_sources.py` | `SKILLS-depo/ontology/scripts/ontology_explorer_source.py` | TASK-007 |
| `SKILLS-depo/ontology/scripts/ontology_explorer_session.py` | `SKILLS-depo/ontology/scripts/ontology_explorer.py` | TASK-009 |
| `SKILLS-depo/ontology/scripts/ontology_explorer_processes.py` | `SKILLS-depo/ontology/scripts/ontology_explorer_read.py` | TASK-016 |
| `SKILLS-depo/ontology/explorer/src/app.ts` | `SKILLS-depo/ontology/explorer/src/main.ts` | TASK-013 |
| `SKILLS-depo/ontology/explorer/src/overview.ts` | `SKILLS-depo/ontology/explorer/src/views.ts` | TASK-013 |
| `SKILLS-depo/ontology/explorer/src/map/data.ts` | `SKILLS-depo/ontology/explorer/src/model.ts` | TASK-017 |
| `SKILLS-depo/ontology/explorer/src/map/list.ts` | `SKILLS-depo/ontology/explorer/src/list.ts` | TASK-017 |
| `SKILLS-depo/ontology/explorer/src/map/renderer.ts` | `SKILLS-depo/ontology/explorer/src/renderer.ts` | TASK-018 |
| `SKILLS-depo/ontology/explorer/src/map/controller.ts` | `SKILLS-depo/ontology/explorer/src/state.ts`, `SKILLS-depo/ontology/explorer/src/renderer.ts` | TASK-018 |

Focused plan modules not renamed by the accepted ownership map (preferences/search/entry/sources/processes/feedback) remain planned consumers beneath the main/views/state ownership. No implementation was created for them in TASK-002. Directory targets are represented by concrete planned members; fixture-directory README is an inventory placeholder, and actual fixture files must be enumerated by TASK-003. Runtime hashed assets cannot be guessed: TASK-010 must expand real manifest members before any build/adoption apply. The screenshots directory expands to the nine required named captures, all pending.

## Distribution, initializer and preservation

Reusable source maps to the registered neutral Template via the updater, and separately to exact root destinations after the root adoption manifest is reviewed. Source package declarations, lock/schema and partial notices are not proof of an installed production package. Do not hand-edit Template, install node_modules into distributed source, relax updater dist/build exclusions, or propagate to other products. `depot/projects.json` stays factual inventory.

Current initializer v12 must be archived through exact source manifest/resource evidence before the current base advances to governance-starter-v13 plus ontology-explorer-v1. Preserve historical v1-v12 dispatch, v9 advanced-resource meanings and v11 provenance; existing receipts acquire no reader on replay. The new explicit capability must cover helpers, schema/config, manifest, notices and assets. No archive filename is invented here: TASK-026 must use the existing edition machinery and expand actual archive paths before apply.

Old active workbench files are enumerated individually as planned removals, contingent on actual reader production/security/isolation/nonmutation/current-initializer gates. Shared authority symbols remain governed by caller inventory. Baseline liveness is inconclusive; no service was stopped in this task. Rollback replaces only exact reader code/assets/config from a reviewed current manifest, preserving newer valid ontology/memory/proposals/receipts. Root mappings and ordered process evidence need their later exact inspected adoption, with no invented order.

Change-map rows use null after hashes for future bytes. The map's own final byte digest is recorded externally by the canonical Task artifact/final manifest, avoiding an impossible embedded self digest. Such null rows are not completed publication evidence. Every row is a boundary/inventory record, not a write grant. The current root retained files have exact observed digests; mutable future targets must be rechecked at apply.

## Frozen metadata inspection

Metadata fields below are registry declarations, hash-verified locally from npm cache and matched to the generated lock. The actual_artifact_inspected/license_text_inspected flags refer only to the subsequent seven cached-artifact inspections described separately; all other bodies remain unavailable.

```json
[
  {
    "name": "@oxc-project/types",
    "version": "0.150.0",
    "role": "build only",
    "license_declared": "MIT",
    "tarball": "https://registry.npmjs.org/@oxc-project/types/-/types-0.150.0.tgz",
    "integrity": "sha512-rDS5/31E9HfPl/CIzGrn0DOlvBbXFseQ5URJ9sYMfstbKLD/c6Gm9vmRzRGDdAXyOIL4zmO37lc9RIwYqVruZw==",
    "repository": {
      "url": "git+https://github.com/oxc-project/oxc.git",
      "type": "git",
      "directory": "npm/oxc-types"
    },
    "metadata_bin": null,
    "metadata_hooks": {},
    "lock_hasInstallScript": false,
    "metadata_sha256": "a6f876f920bfc2da8d7d54792e86402819d27b9e375118e8d4925b7e09c7f22d",
    "actual_artifact_inspected": false,
    "license_text_inspected": false
  },
  {
    "name": "@rolldown/binding-android-arm-eabi",
    "version": "1.2.9",
    "role": "build only",
    "license_declared": "MIT",
    "tarball": "https://registry.npmjs.org/@rolldown/binding-android-arm-eabi/-/binding-android-arm-eabi-1.2.9.tgz",
    "integrity": "sha512-tNISae1QEf/vkb3xkRcjV5SEdzPE97We5IVaa2Z8jSszQPZ8U60B/YCYpw4QI7VidYsBtKavczXf+DyDs9WGxw==",
    "repository": {
      "type": "git",
      "url": "git+https://github.com/rolldown/rolldown.git",
      "directory": "packages/rolldown"
    },
    "metadata_bin": null,
    "metadata_hooks": {},
    "lock_hasInstallScript": false,
    "metadata_sha256": "10e05b9fc5ea08c40957823221d5f838afda2aa649d71a13e0cd76125a026573",
    "actual_artifact_inspected": false,
    "license_text_inspected": false
  },
  {
    "name": "@rolldown/binding-android-arm64",
    "version": "1.2.9",
    "role": "build only",
    "license_declared": "MIT",
    "tarball": "https://registry.npmjs.org/@rolldown/binding-android-arm64/-/binding-android-arm64-1.2.9.tgz",
    "integrity": "sha512-YC8YsI30o606GTZi0VyzYlsDKFP8W61i/QzayHDkLbNEz/IShqAmTa+hsJRj13xTHA0H+6fk4b2UmGn+Q/cMlg==",
    "repository": {
      "url": "git+https://github.com/rolldown/rolldown.git",
      "type": "git",
      "directory": "packages/rolldown"
    },
    "metadata_bin": null,
    "metadata_hooks": {},
    "lock_hasInstallScript": false,
    "metadata_sha256": "cfe355c3e4115bbd3165ac4b4ab9685c8a8df6120ed4c0c61d360dd981fbecfd",
    "actual_artifact_inspected": false,
    "license_text_inspected": false
  },
  {
    "name": "@rolldown/binding-darwin-arm64",
    "version": "1.2.9",
    "role": "build only",
    "license_declared": "MIT",
    "tarball": "https://registry.npmjs.org/@rolldown/binding-darwin-arm64/-/binding-darwin-arm64-1.2.9.tgz",
    "integrity": "sha512-IwhlH3qK5urrY8hZiEgGkHKEFN901p/p2bjxCxJlr4GyNnF7wYpUvK+Y43uaRYuC4hpfjzbR3SJC3arX1jGvmw==",
    "repository": {
      "url": "git+https://github.com/rolldown/rolldown.git",
      "type": "git",
      "directory": "packages/rolldown"
    },
    "metadata_bin": null,
    "metadata_hooks": {},
    "lock_hasInstallScript": false,
    "metadata_sha256": "2e2f250805f28f8dd8256d3b5f76b1e9e1b6bfee4230f6f7da1c47f7f01e80c4",
    "actual_artifact_inspected": false,
    "license_text_inspected": false
  },
  {
    "name": "@rolldown/binding-darwin-x64",
    "version": "1.2.9",
    "role": "build only",
    "license_declared": "MIT",
    "tarball": "https://registry.npmjs.org/@rolldown/binding-darwin-x64/-/binding-darwin-x64-1.2.9.tgz",
    "integrity": "sha512-XxpJfVzFh+jilRxIXUqcfYAYcunIc/XEzIizsOL1fcJee5Sf7H3mH8WlLmfHfluz5amqR88QQo9izKtmMlavAw==",
    "repository": {
      "url": "git+https://github.com/rolldown/rolldown.git",
      "type": "git",
      "directory": "packages/rolldown"
    },
    "metadata_bin": null,
    "metadata_hooks": {},
    "lock_hasInstallScript": false,
    "metadata_sha256": "cd09170d038368fa31e85635534081a79fe7eb507a90c22786f9dad52389a4f9",
    "actual_artifact_inspected": false,
    "license_text_inspected": false
  },
  {
    "name": "@rolldown/binding-freebsd-x64",
    "version": "1.2.9",
    "role": "build only",
    "license_declared": "MIT",
    "tarball": "https://registry.npmjs.org/@rolldown/binding-freebsd-x64/-/binding-freebsd-x64-1.2.9.tgz",
    "integrity": "sha512-kSfvhmgeWyfkbT3p/1s5vSgboogoah2zkm9fX2zjg2hHxSV7T4KhMWRUUaRk4OXNqoD3QAUeRqLcs1aZOK4U1g==",
    "repository": {
      "url": "git+https://github.com/rolldown/rolldown.git",
      "type": "git",
      "directory": "packages/rolldown"
    },
    "metadata_bin": null,
    "metadata_hooks": {},
    "lock_hasInstallScript": false,
    "metadata_sha256": "649b68e3752b90c94a2cddd09a09c643278dd8fe5b284a83a1c46f9370c839a7",
    "actual_artifact_inspected": false,
    "license_text_inspected": false
  },
  {
    "name": "@rolldown/binding-linux-arm-gnueabihf",
    "version": "1.2.9",
    "role": "build only",
    "license_declared": "MIT",
    "tarball": "https://registry.npmjs.org/@rolldown/binding-linux-arm-gnueabihf/-/binding-linux-arm-gnueabihf-1.2.9.tgz",
    "integrity": "sha512-1RVzG17pxqbTfYLC352JlLt6kKLG+6Hr30n8DlIJqsnV5luUDd2Qdx9Ayw1Cabfyb1K9k0jXEZ7evxkRoT+uiw==",
    "repository": {
      "url": "git+https://github.com/rolldown/rolldown.git",
      "type": "git",
      "directory": "packages/rolldown"
    },
    "metadata_bin": null,
    "metadata_hooks": {},
    "lock_hasInstallScript": false,
    "metadata_sha256": "467fafb2b41afb36d280acb6df384fd36cb1d1347c7f871f9c84e565a01f3c0f",
    "actual_artifact_inspected": false,
    "license_text_inspected": false
  },
  {
    "name": "@rolldown/binding-linux-arm64-gnu",
    "version": "1.2.9",
    "role": "build only",
    "license_declared": "MIT",
    "tarball": "https://registry.npmjs.org/@rolldown/binding-linux-arm64-gnu/-/binding-linux-arm64-gnu-1.2.9.tgz",
    "integrity": "sha512-BXqPvZ2drqVD+/Z8UpKwcs4Mp7grM+eGFku4CAEKrEtcbAsUpzREphK1sogCRZGreVPiMkiiBtw0n3TPteuqvw==",
    "repository": {
      "url": "git+https://github.com/rolldown/rolldown.git",
      "type": "git",
      "directory": "packages/rolldown"
    },
    "metadata_bin": null,
    "metadata_hooks": {},
    "lock_hasInstallScript": false,
    "metadata_sha256": "56e99012d96eedf74b49995970ea9086d9756849acb24f2492e4be61f5a0def9",
    "actual_artifact_inspected": false,
    "license_text_inspected": false
  },
  {
    "name": "@rolldown/binding-linux-arm64-musl",
    "version": "1.2.9",
    "role": "build only",
    "license_declared": "MIT",
    "tarball": "https://registry.npmjs.org/@rolldown/binding-linux-arm64-musl/-/binding-linux-arm64-musl-1.2.9.tgz",
    "integrity": "sha512-11vWvo8YDwLzukt27J3aYDWU+gg2P7J+ZOmiJ0hkF5BXZDW7pVya7r40MXDy6ya0i9KamoENSVKIugvJNgFXIA==",
    "repository": {
      "url": "git+https://github.com/rolldown/rolldown.git",
      "type": "git",
      "directory": "packages/rolldown"
    },
    "metadata_bin": null,
    "metadata_hooks": {},
    "lock_hasInstallScript": false,
    "metadata_sha256": "20616e5029ba6b9cffa1a64fcf8f060444b482b6a7f9d949de0310b7004449cb",
    "actual_artifact_inspected": false,
    "license_text_inspected": false
  },
  {
    "name": "@rolldown/binding-linux-ppc64-gnu",
    "version": "1.2.9",
    "role": "build only",
    "license_declared": "MIT",
    "tarball": "https://registry.npmjs.org/@rolldown/binding-linux-ppc64-gnu/-/binding-linux-ppc64-gnu-1.2.9.tgz",
    "integrity": "sha512-a1tijMkdwsIARtc0F39ApURROkf3NwqinI6TOiSSWCTR7dT96dffNvMUtDHnq64wKNTIZOIlzKrFvvFUznJiyw==",
    "repository": {
      "url": "git+https://github.com/rolldown/rolldown.git",
      "type": "git",
      "directory": "packages/rolldown"
    },
    "metadata_bin": null,
    "metadata_hooks": {},
    "lock_hasInstallScript": false,
    "metadata_sha256": "15aaaab698a976389ac4da619399d568fae02fd3a46ef42c0a2704f17b2c0b43",
    "actual_artifact_inspected": false,
    "license_text_inspected": false
  },
  {
    "name": "@rolldown/binding-linux-s390x-gnu",
    "version": "1.2.9",
    "role": "build only",
    "license_declared": "MIT",
    "tarball": "https://registry.npmjs.org/@rolldown/binding-linux-s390x-gnu/-/binding-linux-s390x-gnu-1.2.9.tgz",
    "integrity": "sha512-x6SQNdAvv4c3hWqTMaWuawzMX9myaCs/yEmlGsxJzkdClnHW7FbrjQuSiRDhuSYzEYoEMhsaJy9qHG/XNemJPQ==",
    "repository": {
      "url": "git+https://github.com/rolldown/rolldown.git",
      "type": "git",
      "directory": "packages/rolldown"
    },
    "metadata_bin": null,
    "metadata_hooks": {},
    "lock_hasInstallScript": false,
    "metadata_sha256": "39fa0711629b0fd514d95c1caf3b02323635666764db51ab24aa8b447d29f191",
    "actual_artifact_inspected": false,
    "license_text_inspected": false
  },
  {
    "name": "@rolldown/binding-linux-x64-gnu",
    "version": "1.2.9",
    "role": "build only",
    "license_declared": "MIT",
    "tarball": "https://registry.npmjs.org/@rolldown/binding-linux-x64-gnu/-/binding-linux-x64-gnu-1.2.9.tgz",
    "integrity": "sha512-9s0AZ8BFK5/n7B/TBoa2yJE3gI3KURrbXcPBlsAsvjU4VeJKgE90y1YtNxyEUIcHPQkg6/yfF3qihUrcM/Kf0Q==",
    "repository": {
      "url": "git+https://github.com/rolldown/rolldown.git",
      "type": "git",
      "directory": "packages/rolldown"
    },
    "metadata_bin": null,
    "metadata_hooks": {},
    "lock_hasInstallScript": false,
    "metadata_sha256": "f00d4fa01ee1659e41918233d0daae562ad183653b6143a265ed9dcd993f89c9",
    "actual_artifact_inspected": false,
    "license_text_inspected": false
  },
  {
    "name": "@rolldown/binding-linux-x64-musl",
    "version": "1.2.9",
    "role": "build only",
    "license_declared": "MIT",
    "tarball": "https://registry.npmjs.org/@rolldown/binding-linux-x64-musl/-/binding-linux-x64-musl-1.2.9.tgz",
    "integrity": "sha512-P7VWAmV+WdJluH7ovnRGoiv2i8To7GAZ+kGzfGup635cyL7SyYl3lSUaA3Gp5THf0n/Co5EyEqb2zbqq+nMOHQ==",
    "repository": {
      "url": "git+https://github.com/rolldown/rolldown.git",
      "type": "git",
      "directory": "packages/rolldown"
    },
    "metadata_bin": null,
    "metadata_hooks": {},
    "lock_hasInstallScript": false,
    "metadata_sha256": "d9b29240862bcd532608e13b34811c7563b5e7167ed4e74553f3c783c8bf0ab7",
    "actual_artifact_inspected": false,
    "license_text_inspected": false
  },
  {
    "name": "@rolldown/binding-openharmony-arm64",
    "version": "1.2.9",
    "role": "build only",
    "license_declared": "MIT",
    "tarball": "https://registry.npmjs.org/@rolldown/binding-openharmony-arm64/-/binding-openharmony-arm64-1.2.9.tgz",
    "integrity": "sha512-1qixtsE4BK8h+yS3BfmZ09UhA7O/N4IACva6YBr7EBvCJraByTuRcgOTaiA62Tm0vey3UcKXLOaoGHtYmNGEVg==",
    "repository": {
      "url": "git+https://github.com/rolldown/rolldown.git",
      "type": "git",
      "directory": "packages/rolldown"
    },
    "metadata_bin": null,
    "metadata_hooks": {},
    "lock_hasInstallScript": false,
    "metadata_sha256": "b8e4654cff61871a9f4844b5bcd8235ae88fb1e8dfddb410d8aa16f30c16e7fe",
    "actual_artifact_inspected": false,
    "license_text_inspected": false
  },
  {
    "name": "@rolldown/binding-win32-arm64-msvc",
    "version": "1.2.9",
    "role": "build only",
    "license_declared": "MIT",
    "tarball": "https://registry.npmjs.org/@rolldown/binding-win32-arm64-msvc/-/binding-win32-arm64-msvc-1.2.9.tgz",
    "integrity": "sha512-ok8IQjcEPs1AKZfuEUznVBrJw+gK4soq+bx8b1X2XoMqVClarc1q5JDmVtWXY1xfr6ZuHTAsPXHTgTrqKTZeww==",
    "repository": {
      "url": "git+https://github.com/rolldown/rolldown.git",
      "type": "git",
      "directory": "packages/rolldown"
    },
    "metadata_bin": null,
    "metadata_hooks": {},
    "lock_hasInstallScript": false,
    "metadata_sha256": "cc33fa71d7061fa6d58e2fced42bf2015c6d81d1285f3109232d755e529b09e2",
    "actual_artifact_inspected": false,
    "license_text_inspected": false
  },
  {
    "name": "@rolldown/binding-win32-x64-msvc",
    "version": "1.2.9",
    "role": "build only",
    "license_declared": "MIT",
    "tarball": "https://registry.npmjs.org/@rolldown/binding-win32-x64-msvc/-/binding-win32-x64-msvc-1.2.9.tgz",
    "integrity": "sha512-Ip2mXoU0hM0boq3Rf+ekuT653OROSo6aSYcPT1VHE4q52KvyxgFkQgrgb/IEsxOuvQ2fZZbs8khJAyCEPM24/g==",
    "repository": {
      "url": "git+https://github.com/rolldown/rolldown.git",
      "type": "git",
      "directory": "packages/rolldown"
    },
    "metadata_bin": null,
    "metadata_hooks": {},
    "lock_hasInstallScript": false,
    "metadata_sha256": "d85044e09a1e7bcd38500e5baccd11729529144ed4477690509ab1728b62cf40",
    "actual_artifact_inspected": false,
    "license_text_inspected": false
  },
  {
    "name": "@rolldown/pluginutils",
    "version": "1.0.1",
    "role": "build only",
    "license_declared": "MIT",
    "tarball": "https://registry.npmjs.org/@rolldown/pluginutils/-/pluginutils-1.0.1.tgz",
    "integrity": "sha512-2j9bGt5Jh8hj+vPtgzPtl72j0yRxHAyumoo6TNfAjsLB04UtpSvPbPcDcBMxz7n+9CYB0c1GxQFxYRg2jimqGw==",
    "repository": {
      "type": "git",
      "url": "git+https://github.com/rolldown/plugins.git",
      "directory": "packages/pluginutils"
    },
    "metadata_bin": null,
    "metadata_hooks": {},
    "lock_hasInstallScript": false,
    "metadata_sha256": "26ddd89b5e6497f32c12bb1245078d66e0045babf12708feb4bde2bf15038c20",
    "actual_artifact_inspected": true,
    "license_text_inspected": true
  },
  {
    "name": "@typescript/typescript-aix-ppc64",
    "version": "7.0.2",
    "role": "build only",
    "license_declared": "Apache-2.0",
    "tarball": "https://registry.npmjs.org/@typescript/typescript-aix-ppc64/-/typescript-aix-ppc64-7.0.2.tgz",
    "integrity": "sha512-MTKKkWB7p/0E9xi1d1tHtZ5PiLkGEMIq88pK2CubZjOsLtYTLqhgIgi6zepFa+9GHZ6h05NMCkQxGKiPXMxXtQ==",
    "repository": {
      "type": "git",
      "url": "git+https://github.com/microsoft/TypeScript.git"
    },
    "metadata_bin": null,
    "metadata_hooks": {},
    "lock_hasInstallScript": false,
    "metadata_sha256": "b66b40c3948b0cc8e3299dc9a4685348b47e440366ccf202cbb5e35d5eb096b1",
    "actual_artifact_inspected": false,
    "license_text_inspected": false
  },
  {
    "name": "@typescript/typescript-darwin-arm64",
    "version": "7.0.2",
    "role": "build only",
    "license_declared": "Apache-2.0",
    "tarball": "https://registry.npmjs.org/@typescript/typescript-darwin-arm64/-/typescript-darwin-arm64-7.0.2.tgz",
    "integrity": "sha512-gowzar9MwS/aRWp6f3a4KUqzRjAZjOsmGNCM6LcTgXum+dBfgsBVMN+AgvOCCbguXyick6LJhpBszxMebJ8syA==",
    "repository": {
      "url": "git+https://github.com/microsoft/TypeScript.git",
      "type": "git"
    },
    "metadata_bin": null,
    "metadata_hooks": {},
    "lock_hasInstallScript": false,
    "metadata_sha256": "e5a6dfb02a0cbb8b2944f86905a4fab2afc01f6ab8221835542257765af05b6a",
    "actual_artifact_inspected": false,
    "license_text_inspected": false
  },
  {
    "name": "@typescript/typescript-darwin-x64",
    "version": "7.0.2",
    "role": "build only",
    "license_declared": "Apache-2.0",
    "tarball": "https://registry.npmjs.org/@typescript/typescript-darwin-x64/-/typescript-darwin-x64-7.0.2.tgz",
    "integrity": "sha512-SZ9xZInqApNlNGc9s0W1VSsktYSOe9cFqNOIqmN1Gs8SmkjKZYFt017G4VwPxASInODuAdbTW7sXiFUf893RgA==",
    "repository": {
      "url": "git+https://github.com/microsoft/TypeScript.git",
      "type": "git"
    },
    "metadata_bin": null,
    "metadata_hooks": {},
    "lock_hasInstallScript": false,
    "metadata_sha256": "861a587cabd47c940a6512978a2f546a966bfc64588fa7ca9bbd0aed79b755db",
    "actual_artifact_inspected": false,
    "license_text_inspected": false
  },
  {
    "name": "@typescript/typescript-freebsd-arm64",
    "version": "7.0.2",
    "role": "build only",
    "license_declared": "Apache-2.0",
    "tarball": "https://registry.npmjs.org/@typescript/typescript-freebsd-arm64/-/typescript-freebsd-arm64-7.0.2.tgz",
    "integrity": "sha512-W5NH4y/J0plIIS5b2xvTEkU7JFxyqdMAOgf+Ilhl0vHQXKO5dZoxd+C/jEtq56c4F3wk71RB4BMRQ2XdI+bwYQ==",
    "repository": {
      "type": "git",
      "url": "git+https://github.com/microsoft/TypeScript.git"
    },
    "metadata_bin": null,
    "metadata_hooks": {},
    "lock_hasInstallScript": false,
    "metadata_sha256": "9a48dfcfb0ed3fb58decc8effe1043b7d179b0e7160f07c93e122548290abcb4",
    "actual_artifact_inspected": false,
    "license_text_inspected": false
  },
  {
    "name": "@typescript/typescript-freebsd-x64",
    "version": "7.0.2",
    "role": "build only",
    "license_declared": "Apache-2.0",
    "tarball": "https://registry.npmjs.org/@typescript/typescript-freebsd-x64/-/typescript-freebsd-x64-7.0.2.tgz",
    "integrity": "sha512-UMGDx5sTpzNw3WiPebH7l90IWfJggEd+egHt/q6p7/Cm3zqoV7VxkGXt+3DxPIw8CcmvAB0j3sVVfbhX+M4Tpw==",
    "repository": {
      "type": "git",
      "url": "git+https://github.com/microsoft/TypeScript.git"
    },
    "metadata_bin": null,
    "metadata_hooks": {},
    "lock_hasInstallScript": false,
    "metadata_sha256": "35ab9577a74d57e9d98998ec3dc2ed1046c88d717d56e67086591056da4fa32a",
    "actual_artifact_inspected": false,
    "license_text_inspected": false
  },
  {
    "name": "@typescript/typescript-linux-arm",
    "version": "7.0.2",
    "role": "build only",
    "license_declared": "Apache-2.0",
    "tarball": "https://registry.npmjs.org/@typescript/typescript-linux-arm/-/typescript-linux-arm-7.0.2.tgz",
    "integrity": "sha512-gffT3xPz9sR7j/YJExkyPntrI0P2EP9XbOyWzth2/Gs0RstK+90RBcO0ncXoXy/beYll1SXw846Nf2zdnEz0QQ==",
    "repository": {
      "url": "git+https://github.com/microsoft/TypeScript.git",
      "type": "git"
    },
    "metadata_bin": null,
    "metadata_hooks": {},
    "lock_hasInstallScript": false,
    "metadata_sha256": "d982229c3824ffa3c5f1c4081a914ada0f1afafd20629fab25bbb781c1839ade",
    "actual_artifact_inspected": false,
    "license_text_inspected": false
  },
  {
    "name": "@typescript/typescript-linux-arm64",
    "version": "7.0.2",
    "role": "build only",
    "license_declared": "Apache-2.0",
    "tarball": "https://registry.npmjs.org/@typescript/typescript-linux-arm64/-/typescript-linux-arm64-7.0.2.tgz",
    "integrity": "sha512-Qh4eU4/y3yDjnfjjyPYihMj5/ODIlmt+Bzu17OI+fiSRDW57QmU5SiN63exPRNJPKUzcc1INa1NXdrJ+MqHjUQ==",
    "repository": {
      "url": "git+https://github.com/microsoft/TypeScript.git",
      "type": "git"
    },
    "metadata_bin": null,
    "metadata_hooks": {},
    "lock_hasInstallScript": false,
    "metadata_sha256": "35c13de4ab3eb8e3007945f6a332a13b20fd073a105a346572d0b3d16e17a37f",
    "actual_artifact_inspected": false,
    "license_text_inspected": false
  },
  {
    "name": "@typescript/typescript-linux-loong64",
    "version": "7.0.2",
    "role": "build only",
    "license_declared": "Apache-2.0",
    "tarball": "https://registry.npmjs.org/@typescript/typescript-linux-loong64/-/typescript-linux-loong64-7.0.2.tgz",
    "integrity": "sha512-uEHck9i8hoAzXPiYRib1O7miOnz23SxIeVl6F4LXox+qov1K35jHcEW6VHKvZI+pyvl7fZEP4MCU5LYvIq1GuQ==",
    "repository": {
      "type": "git",
      "url": "git+https://github.com/microsoft/TypeScript.git"
    },
    "metadata_bin": null,
    "metadata_hooks": {},
    "lock_hasInstallScript": false,
    "metadata_sha256": "ee890820fae252e8428e3b5f8ae6fb3206b1b13d8ce1d2ac79f33ef8f2ecdeb8",
    "actual_artifact_inspected": false,
    "license_text_inspected": false
  },
  {
    "name": "@typescript/typescript-linux-mips64el",
    "version": "7.0.2",
    "role": "build only",
    "license_declared": "Apache-2.0",
    "tarball": "https://registry.npmjs.org/@typescript/typescript-linux-mips64el/-/typescript-linux-mips64el-7.0.2.tgz",
    "integrity": "sha512-R4KvAMnE43W5Qeqb0Ly56O3mWMWIAgsMyz36DCaycd5nbg/9kzm0liw3JocfRqyJY0KPmzFjbswozXyW0DnIYA==",
    "repository": {
      "type": "git",
      "url": "git+https://github.com/microsoft/TypeScript.git"
    },
    "metadata_bin": null,
    "metadata_hooks": {},
    "lock_hasInstallScript": false,
    "metadata_sha256": "b25879e1b03a9cbb6d96f7c1b733a12294e5489051c2f03731d8b53d7d41c58c",
    "actual_artifact_inspected": false,
    "license_text_inspected": false
  },
  {
    "name": "@typescript/typescript-linux-ppc64",
    "version": "7.0.2",
    "role": "build only",
    "license_declared": "Apache-2.0",
    "tarball": "https://registry.npmjs.org/@typescript/typescript-linux-ppc64/-/typescript-linux-ppc64-7.0.2.tgz",
    "integrity": "sha512-DORx5b3sd/4S7eayxm4FQv+A7CrkUIGRaHiwI8oiHTAI1fAPWhF4J0vAlkC8biAlHSVVwxMQ3tjZ2/DVbnQiiA==",
    "repository": {
      "type": "git",
      "url": "git+https://github.com/microsoft/TypeScript.git"
    },
    "metadata_bin": null,
    "metadata_hooks": {},
    "lock_hasInstallScript": false,
    "metadata_sha256": "952b7e3c77469f96873c92d47554ea3e39f43cc86fdb68a5788de5423fc89222",
    "actual_artifact_inspected": false,
    "license_text_inspected": false
  },
  {
    "name": "@typescript/typescript-linux-riscv64",
    "version": "7.0.2",
    "role": "build only",
    "license_declared": "Apache-2.0",
    "tarball": "https://registry.npmjs.org/@typescript/typescript-linux-riscv64/-/typescript-linux-riscv64-7.0.2.tgz",
    "integrity": "sha512-wf0jqEDOjrPRnKwYRyyJDRo11KMbvMFrU+q4zqKyChODBzvlkbhNQfKvLxQCcwTpdDaXSHZTVuh0JoCrKCUMHQ==",
    "repository": {
      "type": "git",
      "url": "git+https://github.com/microsoft/TypeScript.git"
    },
    "metadata_bin": null,
    "metadata_hooks": {},
    "lock_hasInstallScript": false,
    "metadata_sha256": "37a7696453ef1b4b179affff3568e346dba807233e06f6d0f0b9759d96fb24dd",
    "actual_artifact_inspected": false,
    "license_text_inspected": false
  },
  {
    "name": "@typescript/typescript-linux-s390x",
    "version": "7.0.2",
    "role": "build only",
    "license_declared": "Apache-2.0",
    "tarball": "https://registry.npmjs.org/@typescript/typescript-linux-s390x/-/typescript-linux-s390x-7.0.2.tgz",
    "integrity": "sha512-IkwJc3L7yhytWd/ewjyxNDfOmswCm9GWMJT/ue/dU4aZNbwZeYAetq42VyLmsmSjvoX7z74X6ZaYCtzAr0EuGw==",
    "repository": {
      "type": "git",
      "url": "git+https://github.com/microsoft/TypeScript.git"
    },
    "metadata_bin": null,
    "metadata_hooks": {},
    "lock_hasInstallScript": false,
    "metadata_sha256": "570dde05e616e8ef1a13bea8f89c291ccd47fc15eecb849a89480e53592811a4",
    "actual_artifact_inspected": false,
    "license_text_inspected": false
  },
  {
    "name": "@typescript/typescript-linux-x64",
    "version": "7.0.2",
    "role": "build only",
    "license_declared": "Apache-2.0",
    "tarball": "https://registry.npmjs.org/@typescript/typescript-linux-x64/-/typescript-linux-x64-7.0.2.tgz",
    "integrity": "sha512-EYdf2cNg7rgCWJnxCdJ+F3V39O8ihb37eHAu1LK8oAFizgTQbPOK7zHHXbPt8rX24COqODXeI3sIf0fCXG7H/A==",
    "repository": {
      "url": "git+https://github.com/microsoft/TypeScript.git",
      "type": "git"
    },
    "metadata_bin": null,
    "metadata_hooks": {},
    "lock_hasInstallScript": false,
    "metadata_sha256": "6c115f5efe67f250f517d4e0b8aa47d6e94bef626cda35fb55bdaabe874fcefa",
    "actual_artifact_inspected": false,
    "license_text_inspected": false
  },
  {
    "name": "@typescript/typescript-netbsd-arm64",
    "version": "7.0.2",
    "role": "build only",
    "license_declared": "Apache-2.0",
    "tarball": "https://registry.npmjs.org/@typescript/typescript-netbsd-arm64/-/typescript-netbsd-arm64-7.0.2.tgz",
    "integrity": "sha512-+polYF4MF04aPpO5FTkHran9yUQDSXqy5GiSDKpsll5jy3l3+g9QLhpf39T+ePtefhXLOGrLl0QIjkQP6VnelA==",
    "repository": {
      "type": "git",
      "url": "git+https://github.com/microsoft/TypeScript.git"
    },
    "metadata_bin": null,
    "metadata_hooks": {},
    "lock_hasInstallScript": false,
    "metadata_sha256": "008fcbc4a7d4f1630c3241fa1da07bce4cb189f035e62a655024d628851bd08e",
    "actual_artifact_inspected": false,
    "license_text_inspected": false
  },
  {
    "name": "@typescript/typescript-netbsd-x64",
    "version": "7.0.2",
    "role": "build only",
    "license_declared": "Apache-2.0",
    "tarball": "https://registry.npmjs.org/@typescript/typescript-netbsd-x64/-/typescript-netbsd-x64-7.0.2.tgz",
    "integrity": "sha512-8YIT0EHM/3dq10ZOVF/A7pc/YSMtbcecct4rWtexrnSCHOPcpC2KTLXfTCR6vDpnSiY12heNb1GiN/wu+T/FyA==",
    "repository": {
      "type": "git",
      "url": "git+https://github.com/microsoft/TypeScript.git"
    },
    "metadata_bin": null,
    "metadata_hooks": {},
    "lock_hasInstallScript": false,
    "metadata_sha256": "019a407fb8072daa2ab3c27ff9988927b27b2de59b91595b7856045884a31586",
    "actual_artifact_inspected": false,
    "license_text_inspected": false
  },
  {
    "name": "@typescript/typescript-openbsd-arm64",
    "version": "7.0.2",
    "role": "build only",
    "license_declared": "Apache-2.0",
    "tarball": "https://registry.npmjs.org/@typescript/typescript-openbsd-arm64/-/typescript-openbsd-arm64-7.0.2.tgz",
    "integrity": "sha512-APT8+ClYnuYm1u9+kgGXoMj2VzWzcymwh2gNSQVySHfkRDGOTVkoWLjCmOQSaO+PoqQ57B0flRp9SA+7GnnkzQ==",
    "repository": {
      "type": "git",
      "url": "git+https://github.com/microsoft/TypeScript.git"
    },
    "metadata_bin": null,
    "metadata_hooks": {},
    "lock_hasInstallScript": false,
    "metadata_sha256": "a7c2f2e4caf350d2d1e7dd05659119296c20cda813643ddafc924b5a81350aaa",
    "actual_artifact_inspected": false,
    "license_text_inspected": false
  },
  {
    "name": "@typescript/typescript-openbsd-x64",
    "version": "7.0.2",
    "role": "build only",
    "license_declared": "Apache-2.0",
    "tarball": "https://registry.npmjs.org/@typescript/typescript-openbsd-x64/-/typescript-openbsd-x64-7.0.2.tgz",
    "integrity": "sha512-yX7s+Q0Dln0Dt9tEzZsAjXXR/+ytBM7AlglaqyeMPxQszJ1JhlJdZ6jLA+IzldHtflX81em7lDao1xXu+aRRkg==",
    "repository": {
      "type": "git",
      "url": "git+https://github.com/microsoft/TypeScript.git"
    },
    "metadata_bin": null,
    "metadata_hooks": {},
    "lock_hasInstallScript": false,
    "metadata_sha256": "5da7959ac67d5ac6b3390ff643504998a6a0cbba42605b91ed6cc8cfbe170adf",
    "actual_artifact_inspected": false,
    "license_text_inspected": false
  },
  {
    "name": "@typescript/typescript-sunos-x64",
    "version": "7.0.2",
    "role": "build only",
    "license_declared": "Apache-2.0",
    "tarball": "https://registry.npmjs.org/@typescript/typescript-sunos-x64/-/typescript-sunos-x64-7.0.2.tgz",
    "integrity": "sha512-dLJDGaLZ1D4HPQn62u1n8mBDkJREwMsAkCdkwd4Ieqw+x3TUyTsqY0YiBCtE6H6OzzgGk3iuZ3vFWRS+E8/d1g==",
    "repository": {
      "type": "git",
      "url": "git+https://github.com/microsoft/TypeScript.git"
    },
    "metadata_bin": null,
    "metadata_hooks": {},
    "lock_hasInstallScript": false,
    "metadata_sha256": "9d7893f8fea4c8dfac4679e3a134ddbbde6f169fe672026b423d695e3bb13545",
    "actual_artifact_inspected": false,
    "license_text_inspected": false
  },
  {
    "name": "@typescript/typescript-win32-arm64",
    "version": "7.0.2",
    "role": "build only",
    "license_declared": "Apache-2.0",
    "tarball": "https://registry.npmjs.org/@typescript/typescript-win32-arm64/-/typescript-win32-arm64-7.0.2.tgz",
    "integrity": "sha512-Gyl1Vy6OsWesLzmq+EP0Fb7b4Nid5232AvcA2SFcdYreldpNtYFFofPjnt62y9hQy7VTaZp65ICJjuAQRaVcIQ==",
    "repository": {
      "url": "git+https://github.com/microsoft/TypeScript.git",
      "type": "git"
    },
    "metadata_bin": null,
    "metadata_hooks": {},
    "lock_hasInstallScript": false,
    "metadata_sha256": "836143a875cd2ce780d6b065f8f47b8303049575e07423fad87ddb36221d3643",
    "actual_artifact_inspected": false,
    "license_text_inspected": false
  },
  {
    "name": "@typescript/typescript-win32-x64",
    "version": "7.0.2",
    "role": "build only",
    "license_declared": "Apache-2.0",
    "tarball": "https://registry.npmjs.org/@typescript/typescript-win32-x64/-/typescript-win32-x64-7.0.2.tgz",
    "integrity": "sha512-0BQ3HkAHHlKLSp1qRvf3SUhGpGsDuhB/jgFw75guyqbxJqEaS0Cw/VFO8i2nHglJUzQCRtMMR/IBAKE3ETMC4g==",
    "repository": {
      "url": "git+https://github.com/microsoft/TypeScript.git",
      "type": "git"
    },
    "metadata_bin": null,
    "metadata_hooks": {},
    "lock_hasInstallScript": false,
    "metadata_sha256": "59f99fbd4b675815a79da8a05ce9895e94b1d42d6cb965d84fd16a006bace3bc",
    "actual_artifact_inspected": false,
    "license_text_inspected": false
  },
  {
    "name": "cytoscape",
    "version": "3.34.3",
    "role": "shipped renderer",
    "license_declared": "MIT",
    "tarball": "https://registry.npmjs.org/cytoscape/-/cytoscape-3.34.3.tgz",
    "integrity": "sha512-yfYGhRcGAntq6YBD583j4n0Eg3jIxvWmZtz/5uz9UYkeIStSlMxuUja+ec5j3iBD8nv1rwaOAYMW09tBdkSeaQ==",
    "repository": {
      "url": "git+https://github.com/cytoscape/cytoscape.js.git",
      "type": "git"
    },
    "metadata_bin": null,
    "metadata_hooks": {},
    "lock_hasInstallScript": false,
    "metadata_sha256": "e30d8ec4747b525a9feabea428ef044c03789c0a67268f549f6d366366627714",
    "actual_artifact_inspected": false,
    "license_text_inspected": false
  },
  {
    "name": "detect-libc",
    "version": "2.1.2",
    "role": "build only",
    "license_declared": "Apache-2.0",
    "tarball": "https://registry.npmjs.org/detect-libc/-/detect-libc-2.1.2.tgz",
    "integrity": "sha512-Btj2BOOO83o3WyH59e8MgXsxEQVcarkUOpEYrubB0urwnN10yQ364rsiByU11nZlqWYZm05i/of7io4mzihBtQ==",
    "repository": {
      "type": "git",
      "url": "git://github.com/lovell/detect-libc.git"
    },
    "metadata_bin": null,
    "metadata_hooks": {},
    "lock_hasInstallScript": false,
    "metadata_sha256": "3e3027d62db04ffc50efae3fb75f6184aa79fb06d8454324597c889b4e5fe68f",
    "actual_artifact_inspected": true,
    "license_text_inspected": true
  },
  {
    "name": "fdir",
    "version": "6.5.0",
    "role": "build only",
    "license_declared": "MIT",
    "tarball": "https://registry.npmjs.org/fdir/-/fdir-6.5.0.tgz",
    "integrity": "sha512-tIbYtZbucOs0BRGqPJkshJUYdL+SDH7dVM8gjy+ERp3WAUjLEFJE+02kanyHtwjWOnwrKYBiwAmM0p4kLJAnXg==",
    "repository": {
      "type": "git",
      "url": "git+https://github.com/thecodrr/fdir.git"
    },
    "metadata_bin": null,
    "metadata_hooks": {
      "prepublishOnly": "npm run test && npm run build"
    },
    "lock_hasInstallScript": false,
    "metadata_sha256": "f76bdfd3664808631d6cb55ebffecd5dfba5a2ea87c85d811d2e49299bca6b2e",
    "actual_artifact_inspected": true,
    "license_text_inspected": true
  },
  {
    "name": "fsevents",
    "version": "2.3.3",
    "role": "build only",
    "license_declared": "MIT",
    "tarball": "https://registry.npmjs.org/fsevents/-/fsevents-2.3.3.tgz",
    "integrity": "sha512-5xoDfX+fL7faATnagmWPpbFtwh/R77WmMMqqHGS65C3vvB0YHrgF+B1YmZ3441tMj5n63k0212XNoJwzlhffQw==",
    "repository": {
      "url": "git+https://github.com/fsevents/fsevents.git",
      "type": "git"
    },
    "metadata_bin": null,
    "metadata_hooks": {
      "install": "node-gyp rebuild",
      "prepublishOnly": "npm run build"
    },
    "lock_hasInstallScript": true,
    "metadata_sha256": "d9b0c2fb585a7d0057ea758444d9b219fad5bf24a8326031b1cca0c6ef509d97",
    "actual_artifact_inspected": true,
    "license_text_inspected": true
  },
  {
    "name": "lightningcss",
    "version": "1.33.0",
    "role": "build only",
    "license_declared": "MPL-2.0",
    "tarball": "https://registry.npmjs.org/lightningcss/-/lightningcss-1.33.0.tgz",
    "integrity": "sha512-WkUDrojuJs0xkgGf2udWxa3yGBRxPtxUkB79i6aCZLRgc7PM8fZe9TosfPDcvEpQZbuFASnHYmRLBLUbmLOIIA==",
    "repository": {
      "type": "git",
      "url": "git+https://github.com/parcel-bundler/lightningcss.git"
    },
    "metadata_bin": null,
    "metadata_hooks": {
      "prepare": "patch-package",
      "prepublishOnly": "node scripts/build-flow.js"
    },
    "lock_hasInstallScript": false,
    "metadata_sha256": "e140223d5b4c81e91e6c304fa4aa14e22f6660b6e0cc341241353f907f05b450",
    "actual_artifact_inspected": false,
    "license_text_inspected": false
  },
  {
    "name": "lightningcss-android-arm64",
    "version": "1.33.0",
    "role": "build only",
    "license_declared": "MPL-2.0",
    "tarball": "https://registry.npmjs.org/lightningcss-android-arm64/-/lightningcss-android-arm64-1.33.0.tgz",
    "integrity": "sha512-gEpRTalKdosp4Bb8qWtc2iOgE5SeIHlpS1up9bFq2wAyYhl1UdTObYiHe98zEM9SQvSoqQZ1IQD0JNpg3Ml5pg==",
    "repository": {
      "type": "git",
      "url": "git+https://github.com/parcel-bundler/lightningcss.git"
    },
    "metadata_bin": null,
    "metadata_hooks": {},
    "lock_hasInstallScript": false,
    "metadata_sha256": "53e056b8aa9bf897da01619cf35d548da1897152352d5543a015b17b6399a38c",
    "actual_artifact_inspected": false,
    "license_text_inspected": false
  },
  {
    "name": "lightningcss-darwin-arm64",
    "version": "1.33.0",
    "role": "build only",
    "license_declared": "MPL-2.0",
    "tarball": "https://registry.npmjs.org/lightningcss-darwin-arm64/-/lightningcss-darwin-arm64-1.33.0.tgz",
    "integrity": "sha512-Sciaz8eenNTKn9b3t7+xr0ipTp9YxKQY4npwQ3mrRuL0BAVHBLyZxofhaKBAVtzmtRZ/zTyo0/to4B1uWG/Djg==",
    "repository": {
      "type": "git",
      "url": "git+https://github.com/parcel-bundler/lightningcss.git"
    },
    "metadata_bin": null,
    "metadata_hooks": {},
    "lock_hasInstallScript": false,
    "metadata_sha256": "a4973cbc352c4148b87aae06fbb984b5b05d4f1e38c096737f3eb42472882716",
    "actual_artifact_inspected": false,
    "license_text_inspected": false
  },
  {
    "name": "lightningcss-darwin-x64",
    "version": "1.33.0",
    "role": "build only",
    "license_declared": "MPL-2.0",
    "tarball": "https://registry.npmjs.org/lightningcss-darwin-x64/-/lightningcss-darwin-x64-1.33.0.tgz",
    "integrity": "sha512-Z5UPAxzrjlWNNyGy6i65cJzzvgJ5D3T6wMvs+gWpY9d7qRhANrxqAp6LhxIgZhWEw18RfJTGcRxjuLIBr+m8XQ==",
    "repository": {
      "type": "git",
      "url": "git+https://github.com/parcel-bundler/lightningcss.git"
    },
    "metadata_bin": null,
    "metadata_hooks": {},
    "lock_hasInstallScript": false,
    "metadata_sha256": "abad7a7b3f0a19f3607a6b2709e86f6dc53d14331114f88167222809fab1dbfa",
    "actual_artifact_inspected": false,
    "license_text_inspected": false
  },
  {
    "name": "lightningcss-freebsd-x64",
    "version": "1.33.0",
    "role": "build only",
    "license_declared": "MPL-2.0",
    "tarball": "https://registry.npmjs.org/lightningcss-freebsd-x64/-/lightningcss-freebsd-x64-1.33.0.tgz",
    "integrity": "sha512-QQM/Ti/hQajJwCY+RiWuCZ9sdtI/XQk7nDK5vC8kkdwixezOlDgvDx7+RT+QjK6FcFT4MpsuoBnHIo/O3StRRg==",
    "repository": {
      "type": "git",
      "url": "git+https://github.com/parcel-bundler/lightningcss.git"
    },
    "metadata_bin": null,
    "metadata_hooks": {},
    "lock_hasInstallScript": false,
    "metadata_sha256": "5ce77722b84cd50663953bf3f9e1c0c6bc10ca63bd2ac7c091332594718524b4",
    "actual_artifact_inspected": false,
    "license_text_inspected": false
  },
  {
    "name": "lightningcss-linux-arm-gnueabihf",
    "version": "1.33.0",
    "role": "build only",
    "license_declared": "MPL-2.0",
    "tarball": "https://registry.npmjs.org/lightningcss-linux-arm-gnueabihf/-/lightningcss-linux-arm-gnueabihf-1.33.0.tgz",
    "integrity": "sha512-N7FVBe6iS24MlM6R/4RBTxGhQheZGs7tiQ9U32UtF75NzP5Q7xWPRqLBCKxlRQRk3rY1jCIPLzx7WzOhuUIRLQ==",
    "repository": {
      "type": "git",
      "url": "git+https://github.com/parcel-bundler/lightningcss.git"
    },
    "metadata_bin": null,
    "metadata_hooks": {},
    "lock_hasInstallScript": false,
    "metadata_sha256": "184e448e6bf394e73d758b3c34358c1a1a8cca439bc2c6b1b5dc6a98a71740e6",
    "actual_artifact_inspected": false,
    "license_text_inspected": false
  },
  {
    "name": "lightningcss-linux-arm64-gnu",
    "version": "1.33.0",
    "role": "build only",
    "license_declared": "MPL-2.0",
    "tarball": "https://registry.npmjs.org/lightningcss-linux-arm64-gnu/-/lightningcss-linux-arm64-gnu-1.33.0.tgz",
    "integrity": "sha512-j2v/itmy4HlNxlc6voKXYgBqNi0Ng2LShg4z7GufpEgs05P+2suBVyi9I6YHq5uoVFx9ETin3eCEhLVyXGQnKg==",
    "repository": {
      "type": "git",
      "url": "git+https://github.com/parcel-bundler/lightningcss.git"
    },
    "metadata_bin": null,
    "metadata_hooks": {},
    "lock_hasInstallScript": false,
    "metadata_sha256": "3dbea88c8f7ae102139f98ec432a41ecf86736458dbd794e60b7b0775a3429af",
    "actual_artifact_inspected": false,
    "license_text_inspected": false
  },
  {
    "name": "lightningcss-linux-arm64-musl",
    "version": "1.33.0",
    "role": "build only",
    "license_declared": "MPL-2.0",
    "tarball": "https://registry.npmjs.org/lightningcss-linux-arm64-musl/-/lightningcss-linux-arm64-musl-1.33.0.tgz",
    "integrity": "sha512-yiO5ROMuYQgXbC60yjZU5CYSFZGKXL0HFATXt9mHJn1+zW55oCtMI9NfcVhYLMFDL7gV7oBPon/EmMMGg2OvtQ==",
    "repository": {
      "type": "git",
      "url": "git+https://github.com/parcel-bundler/lightningcss.git"
    },
    "metadata_bin": null,
    "metadata_hooks": {},
    "lock_hasInstallScript": false,
    "metadata_sha256": "16922c4c327d27f36f8b6e75fad3430d9fb98d4c23e660f31e637d87689e96e0",
    "actual_artifact_inspected": false,
    "license_text_inspected": false
  },
  {
    "name": "lightningcss-linux-x64-gnu",
    "version": "1.33.0",
    "role": "build only",
    "license_declared": "MPL-2.0",
    "tarball": "https://registry.npmjs.org/lightningcss-linux-x64-gnu/-/lightningcss-linux-x64-gnu-1.33.0.tgz",
    "integrity": "sha512-ar+Ju7LmcN0Jo4FpL4hpFybwNG9/3A/Br5KW2n2jyODg3MEZXaDYADdemoNS+BDNfMgKvylJLj4S5tyRActuAg==",
    "repository": {
      "type": "git",
      "url": "git+https://github.com/parcel-bundler/lightningcss.git"
    },
    "metadata_bin": null,
    "metadata_hooks": {},
    "lock_hasInstallScript": false,
    "metadata_sha256": "2d548c91c4e9eb461dea0d65a190905f78f138e1fb58ae1b1fb7e8c2163cfd2e",
    "actual_artifact_inspected": false,
    "license_text_inspected": false
  },
  {
    "name": "lightningcss-linux-x64-musl",
    "version": "1.33.0",
    "role": "build only",
    "license_declared": "MPL-2.0",
    "tarball": "https://registry.npmjs.org/lightningcss-linux-x64-musl/-/lightningcss-linux-x64-musl-1.33.0.tgz",
    "integrity": "sha512-RYiYbkokw0trfKqqzfF55lginwEPrD3OJDfTuJzFs1MK6iFnDenaz1fqLLtX4ITG3OktJQXOeTaw1awrBAlZPw==",
    "repository": {
      "type": "git",
      "url": "git+https://github.com/parcel-bundler/lightningcss.git"
    },
    "metadata_bin": null,
    "metadata_hooks": {},
    "lock_hasInstallScript": false,
    "metadata_sha256": "6c7219a881ff91f775e163123540d87ff07ae6b812a18bef445503677ac13262",
    "actual_artifact_inspected": false,
    "license_text_inspected": false
  },
  {
    "name": "lightningcss-win32-arm64-msvc",
    "version": "1.33.0",
    "role": "build only",
    "license_declared": "MPL-2.0",
    "tarball": "https://registry.npmjs.org/lightningcss-win32-arm64-msvc/-/lightningcss-win32-arm64-msvc-1.33.0.tgz",
    "integrity": "sha512-1K+MPfLSFVpphzpdbfkhlWk6wBrTObBzS2T6db10PNOZgR9GoVsAWzwNyuhUYYbTp23j+4RrncfujZ4uAzXvwA==",
    "repository": {
      "type": "git",
      "url": "git+https://github.com/parcel-bundler/lightningcss.git"
    },
    "metadata_bin": null,
    "metadata_hooks": {},
    "lock_hasInstallScript": false,
    "metadata_sha256": "6d5e3ced1871c6d9e0571aea2e81ad9a84b31866e9a8a9a5bcfe059263c1c147",
    "actual_artifact_inspected": false,
    "license_text_inspected": false
  },
  {
    "name": "lightningcss-win32-x64-msvc",
    "version": "1.33.0",
    "role": "build only",
    "license_declared": "MPL-2.0",
    "tarball": "https://registry.npmjs.org/lightningcss-win32-x64-msvc/-/lightningcss-win32-x64-msvc-1.33.0.tgz",
    "integrity": "sha512-OlEICDx/Xl0FqSp4bry8zFnCvGpig3Gl4gCquvYwHuqJKEC1+n9NgDniFvqHGmMv1ZkqDJrDqKKSykTDX+ehuA==",
    "repository": {
      "type": "git",
      "url": "git+https://github.com/parcel-bundler/lightningcss.git"
    },
    "metadata_bin": null,
    "metadata_hooks": {},
    "lock_hasInstallScript": false,
    "metadata_sha256": "c4579a35756dd62e6c3160c7c99099b969bb76b4cc56a0fdac60518db98a03f5",
    "actual_artifact_inspected": false,
    "license_text_inspected": false
  },
  {
    "name": "nanoid",
    "version": "3.3.19",
    "role": "build only",
    "license_declared": "MIT",
    "tarball": "https://registry.npmjs.org/nanoid/-/nanoid-3.3.19.tgz",
    "integrity": "sha512-Y2tUNy4ouw6tq5oDSKeQYGOyhkUBhNOcGV/02KC+6kd9eDGqdZd++mjMiIDilrBYvjEnCYvVtsuHCuP+okSfug==",
    "repository": {
      "url": "git+https://github.com/ai/nanoid.git",
      "type": "git"
    },
    "metadata_bin": {
      "nanoid": "bin/nanoid.cjs"
    },
    "metadata_hooks": {},
    "lock_hasInstallScript": false,
    "metadata_sha256": "1002010e38870be3807d7b744791976e2c46310b1a82daaf1498671809dcdfee",
    "actual_artifact_inspected": false,
    "license_text_inspected": false
  },
  {
    "name": "picocolors",
    "version": "1.1.1",
    "role": "build only",
    "license_declared": "ISC",
    "tarball": "https://registry.npmjs.org/picocolors/-/picocolors-1.1.1.tgz",
    "integrity": "sha512-xceH2snhtb5M9liqDsmEw56le376mTZkEX/jEb/RxNFyegNul7eNslCXP9FDj/Lcu0X8KEyMceP2ntpaHrDEVA==",
    "repository": {
      "type": "git",
      "url": "git+https://github.com/alexeyraspopov/picocolors.git"
    },
    "metadata_bin": null,
    "metadata_hooks": {},
    "lock_hasInstallScript": false,
    "metadata_sha256": "6d25362e0a56809b0bd10cabc19426363c8f9f10883c4b0d4242c7d8e0767ad9",
    "actual_artifact_inspected": true,
    "license_text_inspected": true
  },
  {
    "name": "picomatch",
    "version": "4.0.7",
    "role": "build only",
    "license_declared": "MIT",
    "tarball": "https://registry.npmjs.org/picomatch/-/picomatch-4.0.7.tgz",
    "integrity": "sha512-qcJu88Q2IWqJsDD529JKMdwGm/dvInW4HvQnRwiH9JtihJvzGOscDtHE3x1pBKeUOTysQ8kVmLnJ2kJu7yhcGA==",
    "repository": {
      "url": "git+https://github.com/micromatch/picomatch.git",
      "type": "git"
    },
    "metadata_bin": null,
    "metadata_hooks": {},
    "lock_hasInstallScript": false,
    "metadata_sha256": "9a8e64f1208fef4d18c27f48267e00c639b65743484cf3f5e788d018195b6fbb",
    "actual_artifact_inspected": false,
    "license_text_inspected": false
  },
  {
    "name": "postcss",
    "version": "8.5.28",
    "role": "build only",
    "license_declared": "MIT",
    "tarball": "https://registry.npmjs.org/postcss/-/postcss-8.5.28.tgz",
    "integrity": "sha512-RRuzqDtt5Y9h3quz5hWhK+TPnsmVs6WwSU6LkJMeY4HstUEDuYTG8UJSdawMRzmzAtV+KEoG8N3Qg2qLy5vM/A==",
    "repository": {
      "url": "git+https://github.com/postcss/postcss.git",
      "type": "git"
    },
    "metadata_bin": null,
    "metadata_hooks": {},
    "lock_hasInstallScript": false,
    "metadata_sha256": "8489169776a9208416f158b4e9d5a2037adcadcfdb25c837c91a62ad4313db9f",
    "actual_artifact_inspected": false,
    "license_text_inspected": false
  },
  {
    "name": "rolldown",
    "version": "1.2.9",
    "role": "build only",
    "license_declared": "MIT",
    "tarball": "https://registry.npmjs.org/rolldown/-/rolldown-1.2.9.tgz",
    "integrity": "sha512-hx/Pv0N1haXRb11qkfnK5MXB/iqr7i0yjWQqmO9uHqZpBgQSqzc8UsSnEpalsh+j1I8qQ2CkXAkJC8Br3dKSlg==",
    "repository": {
      "url": "git+https://github.com/rolldown/rolldown.git",
      "type": "git",
      "directory": "packages/rolldown"
    },
    "metadata_bin": {
      "rolldown": "./bin/cli.mjs"
    },
    "metadata_hooks": {},
    "lock_hasInstallScript": false,
    "metadata_sha256": "c7a178f625f67390ced6c6b7506c55471ef8a4c1508d8bc8cd019f2a7c420048",
    "actual_artifact_inspected": false,
    "license_text_inspected": false
  },
  {
    "name": "source-map-js",
    "version": "1.2.1",
    "role": "build only",
    "license_declared": "BSD-3-Clause",
    "tarball": "https://registry.npmjs.org/source-map-js/-/source-map-js-1.2.1.tgz",
    "integrity": "sha512-UXWMKhLOwVKb728IUtQPXxfYU+usdybtUrK/8uGE8CQMvrhOpwvzDBwj0QhSL7MQc7vIsISBG8VQ8+IDQxpfQA==",
    "repository": {
      "type": "git",
      "url": "git+https://github.com/7rulnik/source-map-js.git"
    },
    "metadata_bin": null,
    "metadata_hooks": {},
    "lock_hasInstallScript": false,
    "metadata_sha256": "a4d82cd21d0cdd29219e6ee1bd7bec1cbffc0a0e960eab222393d7f8566071a9",
    "actual_artifact_inspected": true,
    "license_text_inspected": true
  },
  {
    "name": "tinyglobby",
    "version": "0.2.17",
    "role": "build only",
    "license_declared": "MIT",
    "tarball": "https://registry.npmjs.org/tinyglobby/-/tinyglobby-0.2.17.tgz",
    "integrity": "sha512-wXR/dYpcqKmfWpEdZjiKJOwCNFndD0DMnrW/cYjVGttEkBfVgcLFHoNrlj47mjOVic9yyNu65alsgF4NQyTa2g==",
    "repository": {
      "url": "git+https://github.com/SuperchupuDev/tinyglobby.git",
      "type": "git"
    },
    "metadata_bin": null,
    "metadata_hooks": {},
    "lock_hasInstallScript": false,
    "metadata_sha256": "c4fe05dc2665a12e8215a443030b51a2c1b9a99d23ef911407c7a86d40747bc6",
    "actual_artifact_inspected": true,
    "license_text_inspected": true
  },
  {
    "name": "typescript",
    "version": "7.0.2",
    "role": "build only",
    "license_declared": "Apache-2.0",
    "tarball": "https://registry.npmjs.org/typescript/-/typescript-7.0.2.tgz",
    "integrity": "sha512-8FYau96o3NKOhbjKi/qNvG/W5jhzxkbdm5sj9AbZ/5T5sWqn3hJgLfGx27sRKZWTvyzCP8dLRBTf5tBTSRVUNA==",
    "repository": {
      "url": "git+https://github.com/microsoft/TypeScript.git",
      "type": "git"
    },
    "metadata_bin": {
      "tsc": "bin/tsc"
    },
    "metadata_hooks": {},
    "lock_hasInstallScript": false,
    "metadata_sha256": "4de8d2f015a981ec52e72716913e5e781ee34beacaa96085dbd48071508bd43f",
    "actual_artifact_inspected": false,
    "license_text_inspected": false
  },
  {
    "name": "vite",
    "version": "8.3.0",
    "role": "build only",
    "license_declared": "MIT",
    "tarball": "https://registry.npmjs.org/vite/-/vite-8.3.0.tgz",
    "integrity": "sha512-lhZBVvEHefgE+HQZC9O7EBJgCU/nVzFNl7vkS4RE0APtWLP02/8QVIkQtzBxPquh7lq5/78NHipTj7ODQ6XuyQ==",
    "repository": {
      "url": "git+https://github.com/vitejs/vite.git",
      "type": "git",
      "directory": "packages/vite"
    },
    "metadata_bin": {
      "vite": "bin/vite.js"
    },
    "metadata_hooks": {},
    "lock_hasInstallScript": false,
    "metadata_sha256": "6e6637eac1bfd034ccf0f103b3dc383ecb1a18418ef0d3c54edc468d0ef0c361",
    "actual_artifact_inspected": false,
    "license_text_inspected": false
  }
]
```

## Outstanding acceptance work

Complete integrity-bound package downloads, remaining55 artifact/license/copyright/transitive notices, remaining hook-body inspection and installed tsc/Vite/native-bin checks remain pending. Full Draft2020-12 schema validation and the123 targeted cases passed offline using the existing test interpreter. The renderer/layout/build choices are contractual only. Service, sources, frontend, production bundle/CSP, sessions, concurrency/RSS, actual browsers, keyboard/VoiceOver, user comprehension, root/Template/fixture isolation, cutover and rollback remain their planned tasks. This partial implementation must not be marked CONTRACTS verified or used to imply any AT pass.


## Local delivery boundary and full release traceability

The following project-specific delivery/traceability sections remain local. They preserve the accepted scope and are not runtime or source-package status claims.

## Exact source, Template, root and initializer boundary map

TASK-002 acceptance requires these seven exact outputs: `SKILLS-depo/ontology/references/explorer-contract.md`, `SKILLS-depo/ontology/explorer/package.json`, `SKILLS-depo/ontology/explorer/package-lock.json`, `SKILLS-depo/ontology/explorer/THIRD_PARTY_NOTICES.md`, `ONTOLOGY-depo/schema/explorer-v1.json`, `Verification/project-knowledge-explorer-first-release/change-map.json`, and `Verification/project-knowledge-explorer-first-release/implementation-decisions.md`. The contract/schema must implement the unified rules in this proposal, package/lock/notices must contain real inspected artifact evidence, and decisions/change map must preserve source/Template/root/history separation. Commands/files needed for later consumers remain explicit plan work, not fake completed contract-package deliverables. TASK-002 implementer writes only those seven artifact targets named by the baseline. The following rows are the concrete subsequent change map those artifacts must record; they are not permission for this solver to edit them.

| Source or selected active target | Generated Template destination / separately adopted root destination | Boundary |
| --- | --- | --- |
| `SKILLS-depo/ontology/scripts/ontology_explorer*.py`, `references/explorer-contract.md`, `explorer/` package | `Projects/Sys4AI-Template-Project/.agents/skills/ontology/...`; root `.agents/skills/ontology/...` | Reusable source authored first. Updater owns only Template. Root copy requires inspected exact add/replace/delete manifest and destination instructions. Runtime asset manifest resolves exact hashed filenames before adoption. |
| `ONTOLOGY-depo/schema/explorer-v1.json`, `starter/ontology-explorer.yaml` | Template `reference-assets/ONTOLOGY-depo/schema/explorer-v1.json`, starter reference and explicit root `ontology-explorer.yaml` mapping; root corresponding reference and separately specialized config | Add explicit starter mapping in `depot/template-update.json`. Starter remains neutral. Active root mappings enumerate exact root IDs and retain canonical configuration unchanged. |
| `SKILLS-depo/ontology/scripts/ontology.py`, `ontology_advanced_cli.py`, `references/commands.md`, `README.md`, `SKILL.md`, relevant verification/compatibility docs | Same package relative paths in Template and separately inspected root package | Add reader CLI before cutover; deprecate workbench only after the production gates. Keep agent operations and historical evidence. No broad SKILL rewrite. |
| `SKILLS-depo/ontology/scripts/ontology_workbench.py`, `ontology_health.py`, authority callers identified in caller inventory | Same relative package paths under exact migration manifest | Preserve shared authority/import interfaces. Retire active HTTP authoring separately from compatibility symbols. No wholesale module deletion that breaks verified callers. |
| Old source `SKILLS-depo/ontology/workbench/{index.html,app.js,editor.js,review.js,advanced.js,styles.css}` | Exact mapped Template deletions and separately authorized root deletions | Removal from active distribution occurs only after current initializer path works and reader security/isolation gates pass. Preserve archived historical edition assets/receipts/evidence, not an active old tab. |
| `SKILLS-depo/init-new-project/scripts/init_new_project.py`, `init_ontology_advanced.py`, `init_static_health.py`, new `init_ontology_explorer.py`; `assets/static-capability-v1.json` and capability tests/docs | Template `.agents/skills/init-new-project/...`; root only through an independently scoped initializer adoption | Current v12 source has legacy v9 coupling. Add explicit `ontology-explorer-v1` capability inventory/assessment and current-edition branch. Pin/check all required reader helpers/schema/config/build manifest/notices/assets. Do not mutate historical v9/v11 or earlier receipt requirements. |
| `Verification/project-knowledge-explorer-first-release/change-map.json`, `implementation-decisions.md`, later adoption/cutover/rollback/traceability evidence | No Template/runtime distribution | Local verification outputs only; every changed file maps to requirement/task/owner/evidence. |

Current initializer handling must not merely substitute Explorer assets for v9's required workbench files. Preserve the historical validator/resource edition for existing receipts. Introduce an explicit current capability variant selected by its manifest/receipt evidence, not by guessing that files are missing. The reader changes the current base copy contract: archive its exact v12 source manifest/resource definition and select governance-starter-v13 through the existing edition machinery for new/first-prepared projects. Preserve v1-v12 receipt dispatch and advanced v9 resource meaning; do not relabel an existing v12 receipt or overwrite v11. The new capability can be selected for current new/first-prepared projects and through explicit reviewed adoption for existing projects. It specializes `ontology-explorer.yaml` alongside canonical identity but enables no advanced profile/service. The new inventory checks exact production manifest closure and current static helper signatures before setup can claim completeness. TASK-026 must wire exact explicit v13/ontology-explorer-v1 capability selection through new setup, receipt replay, module adoption and static assessment, with tests for each current/historical branch. Existing receipt reruns do not silently acquire Explorer; explicit selected adoption uses the existing checked append/provenance model.

`change-map.json` is `{schema_version:1,plan_id:"PLAN-20260920-9B9964BA",plan_revision:1,rows:[ChangeRow]}`. Each ChangeRow has exactly `{path,operation,owner,source_path,source_sha256,before_sha256,after_sha256,destination_project,distribution_stage,requirement_ids,plan_task_ids,preservation,verification}`. path/source_path are project-relative POSIX strings (source_path may be null for a local newly authored file); operation is add/replace/delete/retain; owner is the responsible source/manager/updater identifier; digests are Digest|null; destination_project is a selected registry identity or explicit fixture label, not a grant; distribution_stage is source/template/root/fixture/history/evidence; requirement_ids and plan_task_ids are nonempty unique exact IDs; preservation and verification are nonempty string arrays naming constraints and evidence paths/commands. Future planned members may have null after hashes but must be expanded to real exact files before apply. Null after digests denote planned bytes until produced; they cannot be reported as completed. At publication/adoption every selected row has actual reviewed before/after digests. Enumerate actual files, not broad recursive delete patterns. Preserve `.gitignore`, project-owned customizations, canonical/memory data, source bindings, proposals, receipts and unrelated local edits. `depot/projects.json` remains factual inventory, never an adoption grant.

Template checks run through `tools/template_update.py check` and its reviewed apply path; never hand-edit Template as source. Verify a neutral Template package honestly: unresolved neutral identity is a truthful startup error, and runtime can be exercised in a disposable explicit specialization. Also verify root and a second explicitly selected fixture namespace with one same-label/different-meaning entry. Root/session/cache/cursor/source/preference/route isolation must be proved with those distinct roots. Do not register or update other product projects.

Cutover prerequisites are actual production reader/map/source/session/CSP/non-mutation/isolation gates plus current initializer compatibility. Stop/reconcile the exact old service only when its live handle is known and within the cutover authority; the baseline's failed loopback observation cannot identify it as stopped. Fresh reader sessions are mandatory. Code/asset/configuration rollback uses reviewed release manifests and rechecks current destination before replacing. Rollback never restores baseline ontology/memory/proposals/receipts over newer valid knowledge. Source-reference/helper-certification changes are inventoried after implementation; any authorized provenance maintenance uses its separate current procedure and evidence, never opportunistic hash repair by the reader.

## Full-scope traceability and evidence boundary

Every row remains required. Contract coverage preserves these requirements; only current downstream implementation/runtime/manual evidence can mark them met. The immutable TRD acceptance text and plan verification steps remain controlling, including qualified proposed timing/layout/fixture targets and unavailable-platform/participant reporting. TASK-002 makes no completion claim for any row.

| Requirement | Required behavior/evidence scope | Plan implementation/evidence owners |
| --- | --- | --- |
| REQ-001 | Replace the human authoring interface with four reading destinations | TASK-002, TASK-013, TASK-021, TASK-029, TASK-033 |
| REQ-002 | Read the selected canonical ontology without creating another authority | TASK-001, TASK-002, TASK-004, TASK-006, TASK-033 |
| REQ-003 | Keep status, evidence, meaning, and authority distinct | TASK-002, TASK-003, TASK-004, TASK-006, TASK-015, TASK-033 |
| REQ-004 | Offer source-backed starting points | TASK-002, TASK-005, TASK-013, TASK-033 |
| REQ-005 | Search deterministically without optional AI | TASK-002, TASK-005, TASK-014, TASK-021, TASK-030, TASK-033 |
| REQ-006 | Make results and discovery understandable | TASK-002, TASK-003, TASK-005, TASK-013, TASK-014, TASK-033 |
| REQ-007 | Filter and page search without losing valid matches | TASK-003, TASK-005, TASK-014, TASK-033 |
| REQ-008 | Present faithful readable entries | TASK-006, TASK-015, TASK-033 |
| REQ-009 | Preserve inspectable relationship meaning and direction | TASK-002, TASK-003, TASK-006, TASK-015, TASK-017, TASK-018, TASK-033 |
| REQ-010 | Explain processes only to the extent sources support them | TASK-001, TASK-002, TASK-003, TASK-016, TASK-021, TASK-025, TASK-033 |
| REQ-011 | Inspect exact evidence without losing reading context | TASK-007, TASK-015, TASK-016, TASK-033 |
| REQ-012 | Preserve navigation state through stable identities | TASK-009, TASK-012, TASK-021, TASK-033 |
| REQ-013 | Keep harmless preferences separate from knowledge | TASK-010, TASK-012, TASK-013, TASK-019, TASK-033 |
| REQ-014 | Start the map with a bounded focused neighborhood | TASK-002, TASK-006, TASK-018, TASK-033 |
| REQ-015 | Separate map selection, focus, and deliberate expansion | TASK-012, TASK-017, TASK-018, TASK-033 |
| REQ-016 | Keep the visual graph semantically faithful | TASK-003, TASK-006, TASK-017, TASK-018, TASK-033 |
| REQ-017 | Keep map presentation readable and stable | TASK-018, TASK-019, TASK-022, TASK-033 |
| REQ-018 | Explain limits without inventing completeness | TASK-002, TASK-003, TASK-005, TASK-006, TASK-014, TASK-017, TASK-018, TASK-019, TASK-024, TASK-033 |
| REQ-019 | Give the relationship list full map equivalence | TASK-006, TASK-017, TASK-021, TASK-022, TASK-025, TASK-033 |
| REQ-020 | Preserve usable context in empty and failure states | TASK-007, TASK-008, TASK-009, TASK-011, TASK-012, TASK-013, TASK-015, TASK-016, TASK-019, TASK-021, TASK-033 |
| REQ-021 | Display one coherent canonical snapshot | TASK-002, TASK-004, TASK-019, TASK-033 |
| REQ-022 | Cache validated views with bounded lifetime | TASK-002, TASK-004, TASK-024, TASK-033 |
| REQ-023 | Provide compact validated read responses | TASK-002, TASK-005, TASK-006, TASK-008, TASK-021, TASK-033 |
| REQ-024 | Validate continuation against its original read scope | TASK-002, TASK-005, TASK-006, TASK-033 |
| REQ-025 | Reject stale responses and clean up inactive views | TASK-002, TASK-012, TASK-018, TASK-019, TASK-021, TASK-024, TASK-033 |
| REQ-026 | Make browsing observably non-mutating | TASK-001, TASK-004, TASK-007, TASK-008, TASK-020, TASK-023, TASK-030, TASK-031, TASK-032, TASK-033 |
| REQ-027 | Keep memory and generated wiki independent | TASK-007, TASK-016, TASK-023, TASK-030, TASK-033 |
| REQ-028 | Run locally with installed production assets | TASK-002, TASK-008, TASK-009, TASK-010, TASK-011, TASK-020, TASK-021, TASK-023, TASK-026, TASK-028, TASK-029, TASK-032, TASK-033 |
| REQ-029 | Enforce local reading-session isolation | TASK-002, TASK-008, TASK-009, TASK-011, TASK-020, TASK-028, TASK-033 |
| REQ-030 | Keep bootstrap credentials out of routes and evidence | TASK-002, TASK-009, TASK-011, TASK-012, TASK-020, TASK-028, TASK-033 |
| REQ-031 | Remove browser access to every write dispatcher | TASK-002, TASK-008, TASK-009, TASK-020, TASK-023, TASK-029, TASK-033 |
| REQ-032 | Constrain source and asset access | TASK-002, TASK-007, TASK-010, TASK-015, TASK-020, TASK-033 |
| REQ-033 | Bound service resources and protect diagnostics | TASK-002, TASK-004, TASK-006, TASK-008, TASK-018, TASK-020, TASK-024, TASK-033 |
| REQ-034 | Make ordinary reading accessible | TASK-013, TASK-014, TASK-017, TASK-022, TASK-033 |
| REQ-035 | Preserve predictable focus and feedback | TASK-012, TASK-014, TASK-015, TASK-019, TASK-022, TASK-033 |
| REQ-036 | Support narrow screens, zoom, themes, and reduced motion | TASK-013, TASK-019, TASK-022, TASK-033 |
| REQ-037 | Keep reusable source and Template distribution explicit | TASK-001, TASK-002, TASK-010, TASK-026, TASK-028, TASK-029, TASK-032, TASK-033 |
| REQ-038 | Preserve independent project adoption and isolation | TASK-001, TASK-002, TASK-003, TASK-020, TASK-026, TASK-027, TASK-028, TASK-029, TASK-031, TASK-032, TASK-033 |
| REQ-039 | Define launch, health, and command compatibility honestly | TASK-002, TASK-008, TASK-010, TASK-011, TASK-021, TASK-026, TASK-027, TASK-028, TASK-029, TASK-032, TASK-033 |
| REQ-040 | Preserve agent operations and historical knowledge during cutover | TASK-001, TASK-002, TASK-011, TASK-026, TASK-027, TASK-028, TASK-029, TASK-030, TASK-031, TASK-032, TASK-033 |
| REQ-041 | Keep provenance maintenance and rollback separate from browsing | TASK-001, TASK-002, TASK-023, TASK-026, TASK-027, TASK-030, TASK-031, TASK-032, TASK-033 |
| REQ-042 | Establish current baseline and process-content coverage | TASK-001, TASK-016, TASK-030, TASK-033 |
| REQ-043 | Verify the production product against every acceptance scenario | TASK-003, TASK-020, TASK-021, TASK-022, TASK-023, TASK-024, TASK-025, TASK-028, TASK-030, TASK-032, TASK-033 |
| REQ-044 | Record accessibility evidence beyond automated scanning | TASK-022, TASK-032, TASK-033 |
| REQ-045 | Measure proposed performance targets honestly | TASK-024, TASK-032, TASK-033 |
| REQ-046 | Exercise representative and pathological workloads | TASK-003, TASK-024, TASK-032, TASK-033 |
| REQ-047 | Validate knowledge comprehension with people | TASK-025, TASK-032, TASK-033 |
| REQ-048 | Deliver inspectable evidence and operational documentation | TASK-026, TASK-027, TASK-031, TASK-032, TASK-033 |
| REQ-049 | Implement independently with explicit dependency provenance | TASK-002, TASK-010, TASK-021, TASK-026, TASK-032, TASK-033 |

All eight phases and 33 tasks are retained:

| Plan task | Phase | Required work |
| --- | --- | --- |
| TASK-001 | PHASE-001 | Freeze implementation baseline and content/caller inventory |
| TASK-002 | PHASE-001 | Bind implementation contracts and dependency choices |
| TASK-003 | PHASE-001 | Prepare canonical acceptance fixtures and matrix |
| TASK-004 | PHASE-002 | Materialize coherent immutable reader snapshots |
| TASK-005 | PHASE-002 | Adapt deterministic discovery with stable continuation |
| TASK-006 | PHASE-002 | Project exact entries and typed neighborhoods |
| TASK-007 | PHASE-002 | Implement precise registered source inspection |
| TASK-008 | PHASE-002 | Build read-only HTTP operations and bounded errors |
| TASK-009 | PHASE-002 | Enforce bootstrap and project-isolated sessions |
| TASK-010 | PHASE-002 | Package explicit offline production assets |
| TASK-011 | PHASE-002 | Add explicit reader launch and bounded health inspection |
| TASK-012 | PHASE-003 | Implement shared read client, state and safe route foundations |
| TASK-013 | PHASE-003 | Implement semantic reader shell and Overview |
| TASK-014 | PHASE-003 | Implement discoverable accessible search and browsing |
| TASK-015 | PHASE-003 | Implement faithful entries and evidence drawer |
| TASK-016 | PHASE-003 | Implement source-supported process reading |
| TASK-017 | PHASE-004 | Implement normalized relationship data and independent List |
| TASK-018 | PHASE-004 | Implement focused graph renderer and controls |
| TASK-019 | PHASE-004 | Integrate truthful loading and failure recovery |
| TASK-020 | PHASE-005 | Verify dedicated service security and isolation |
| TASK-021 | PHASE-005 | Verify actual production offline user workflows |
| TASK-022 | PHASE-005 | Record keyboard and assistive technology acceptance |
| TASK-023 | PHASE-005 | Prove end-to-end browsing nonmutation |
| TASK-024 | PHASE-005 | Benchmark bounded representative and pathological workloads |
| TASK-025 | PHASE-005 | Validate comprehension with people |
| TASK-026 | PHASE-006 | Update current delivery inventories and distribute neutral Template assets |
| TASK-027 | PHASE-006 | Prepare exact active-root adoption and rollback manifest |
| TASK-028 | PHASE-006 | Adopt and verify the production reader in the root |
| TASK-029 | PHASE-007 | Retire active workbench destinations after reader gates |
| TASK-030 | PHASE-007 | Verify preserved agent workflows and recovery |
| TASK-031 | PHASE-007 | Assess provenance effects and verify reversible migration |
| TASK-032 | PHASE-008 | Deliver production visuals and operational handoff |
| TASK-033 | PHASE-008 | Close requirement and acceptance evidence coverage |

| Acceptance case | Required direct evidence | Governing requirements |
| --- | --- | --- |
| AT-01 | Only reading destinations; no loaded authoring modules | REQ-001 |
| AT-02 | Deterministic exact/label/alias/definition search, semantic=False | REQ-005 |
| AT-03 | Equal-label/alias ambiguity, distinct identities | REQ-006 |
| AT-04 | Filter before multi-page results | REQ-007 |
| AT-05 | Stable continuation without duplicate/skipped identities | REQ-007, REQ-024 |
| AT-06 | Honest byte/time/visited/item incomplete coverage | REQ-018 |
| AT-07 | Faithful optional and required entry fields | REQ-008 |
| AT-08 | Deprecated exact-ID historical definition/replacement | REQ-003 |
| AT-09 | Draft/inferred classifications remain distinct | REQ-003 |
| AT-10 | Selection leaves camera/focus unchanged | REQ-015 |
| AT-11 | Explicit focus and Back restoration | REQ-015 |
| AT-12 | Bounded high-degree expansion and omitted coverage | REQ-018 |
| AT-13 | Parallel relationship IDs, meanings and evidence | REQ-009 |
| AT-14 | Incoming traversal preserves canonical direction | REQ-009 |
| AT-15 | Loops/cycles/qualifiers preserved without infinite expansion | REQ-016 |
| AT-16 | Map/List substantive equivalence and preserved state | REQ-019 |
| AT-17 | Only supported process fields/sequence, ordered text first | REQ-010 |
| AT-18 | Exact missing-order statement and documented relationships | REQ-010 |
| AT-19 | Correct identity/reference selects authorized evidence | REQ-011 |
| AT-20 | Changed source bytes visibly distinguished without repair | REQ-011 |
| AT-21 | Mixed snapshot rejection and atomic refresh | REQ-021 |
| AT-22 | Late response cannot replace current selection | REQ-025 |
| AT-23 | Expiry/stopped service preserves context and explains reopening | REQ-020 |
| AT-24 | Every direct old/write endpoint denied without mutation | REQ-031 |
| AT-25 | Host/Origin/CSRF/session/service isolation | REQ-029 |
| AT-26 | Traversal/symlink/unselected source/asset denial | REQ-032 |
| AT-27 | Script-like text/malicious links inert under actual CSP | REQ-032 |
| AT-28 | Production graph/reader offline with installed assets | REQ-028 |
| AT-29 | Major reading/exploration tasks by keyboard/List | REQ-019, REQ-034 |
| AT-30 | 320 CSS-pixel reflow/zoom and readable controls | REQ-036 |
| AT-31 | Root/neutral Template/second namespace isolation | REQ-038 |
| AT-32 | Core reads with optional services absent and no hidden startup | REQ-028 |
| AT-33 | Full workflow protected hash/timestamp non-mutation | REQ-026 |
| AT-34 | Renderer failure retains List/entry/source actions | REQ-020 |
| AT-35 | Independent agent/publication/recovery/Template regressions | REQ-040 |
| AT-36 | Repeated representative/stress timing, memory/limits and graceful degradation | REQ-045, REQ-046 |

The final matrix additionally records the actual production build/source hashes, commands, browser and assistive-technology versions, independent light/dark/reduced-motion checks, 200% text and 400%/320-pixel reflow, macOS VoiceOver/Safari knowledge-task walkthrough, optional Windows limitation, actual human/owner comprehension results, content gaps and unexamined sources. Qualified target measurements are cold first readable screen about 2 s, warm search p95 200 ms excluding debounce, bounded entry p95 250 ms, 25-node/50-edge graph about 1.5 s, and loaded selection feedback 100 ms; report median/p95 with hardware/browser/build/dataset/payload/cold-warm conditions, source-validation cost separately, and compressed bundle baseline. Suggested small/representative/stress fixtures remain approximately 50/100, 1000/5000, 5000/50000 entries/relations; loader caps and honest degradation govern. Include duplicate/long labels, aliases, many sources, parallel predicates, loops/cycles/hubs, broken references and large definitions, not only random graphs.

Production screenshots must cover Overview, search results, populated entry, process page, focused map, parallel edges, source drawer, incomplete response and narrow screen. Screenshots alone do not prove workflows, comprehension, accessibility or preservation. User validation retains task completion, wrong turns, reversed-relation/layout-causality misunderstandings and participant wording; high-impact misunderstandings block usability acceptance. If only the owner is available document that walkthrough and broader unperformed validation explicitly. No contract review invents a human outcome.

Release evidence must prove current exact source/Template/root/fixture manifests, reader safety/isolation before cutover, fresh sessions, actual old-service handle reconciliation, current/historical initializer compatibility, agent regressions, exact exempt runtime files, full protected non-mutation and rollback after newer valid knowledge. Documentation/reporting/provenance maintenance remain separately attributable. Skips, missing participants, unavailable platforms, pre-existing failures and untested behavior are distinct from passes.


## Subsequent offline artifact and schema verification

The manager supplied a bounded exact-SRI inventory of seven preexisting npm cache tarballs (observation SHA256 `e6eaeb21995f4df267773f98ed1b5c90f4a3331187399590f2be7b60c36677a8`). Each tarball was independently SHA512 matched to the lock, parsed in memory with no extraction, and inspected for license/notice/copyright members and package script declarations. No symlink/hardlink tar member was present. Actual texts were read and copied exactly to the incomplete notice file. All seven are build-only transitives; the55 missing packages include all three selected direct dependencies. No installed compiler or native dependency was obtained and no package script executed.

The fsevents2.3.3 lock hasInstallScript flag is true, while its actual tarball package.json declares only clean/build/test/prepublishOnly scripts and contains no install.js or binding.gyp. This distinction is recorded, not treated as successful installation or permission to run a native build. The package has a shipped fsevents.node member; it was not executed.

Observed cached artifact summary:

```json
[
  {
    "name": "@rolldown/pluginutils",
    "version": "1.0.1",
    "integrity": "sha512-2j9bGt5Jh8hj+vPtgzPtl72j0yRxHAyumoo6TNfAjsLB04UtpSvPbPcDcBMxz7n+9CYB0c1GxQFxYRg2jimqGw==",
    "tarball_sha256": "13fcb3423d37f95a8e861c172e4b62fd24f22412be4e942087367242476e3400",
    "members": 8,
    "scripts": {
      "dev": "tsdown --watch",
      "build": "tsdown",
      "test": "vitest --project pluginutils",
      "test:types": "vitest --project pluginutils --typecheck.only"
    },
    "license": "MIT",
    "license_members": [
      {
        "member": "package/LICENSE",
        "sha256": "e1919b3b98b8bf6c1b99fcc60a0ed46027c97ac947432e1278446c9606f50161"
      }
    ]
  },
  {
    "name": "detect-libc",
    "version": "2.1.2",
    "integrity": "sha512-Btj2BOOO83o3WyH59e8MgXsxEQVcarkUOpEYrubB0urwnN10yQ364rsiByU11nZlqWYZm05i/of7io4mzihBtQ==",
    "tarball_sha256": "270dec0fc06cff86481da8af2dd8f18dee6b602790b14ef0e1c2c18d7da39427",
    "members": 8,
    "scripts": {
      "test": "semistandard && nyc --reporter=text --check-coverage --branches=100 ava test/unit.js",
      "changelog": "conventional-changelog -i CHANGELOG.md -s",
      "bench": "node benchmark/detect-libc",
      "bench:calls": "node benchmark/call-familySync.js && sleep 1 && node benchmark/call-isNonGlibcLinuxSync.js && sleep 1 && node benchmark/call-versionSync.js"
    },
    "license": "Apache-2.0",
    "license_members": [
      {
        "member": "package/LICENSE",
        "sha256": "b40930bbcf80744c86c46a12bc9da056641d722716c378f5659b9e555ef833e1"
      }
    ]
  },
  {
    "name": "fdir",
    "version": "6.5.0",
    "integrity": "sha512-tIbYtZbucOs0BRGqPJkshJUYdL+SDH7dVM8gjy+ERp3WAUjLEFJE+02kanyHtwjWOnwrKYBiwAmM0p4kLJAnXg==",
    "tarball_sha256": "241ddcd9f31e2a1fca405326017dbb8333ce174198e887f0f96387c29f0d365e",
    "members": 7,
    "scripts": {
      "prepublishOnly": "npm run test && npm run build",
      "build": "tsdown",
      "format": "prettier --write src __tests__ benchmarks",
      "test": "vitest run __tests__/",
      "test:coverage": "vitest run --coverage __tests__/",
      "test:watch": "vitest __tests__/",
      "bench": "ts-node benchmarks/benchmark.js",
      "bench:glob": "ts-node benchmarks/glob-benchmark.ts",
      "bench:fdir": "ts-node benchmarks/fdir-benchmark.ts",
      "release": "./scripts/release.sh"
    },
    "license": "MIT",
    "license_members": [
      {
        "member": "package/LICENSE",
        "sha256": "9a39f2aadab11a3697edd668ff2d8ad885b649737b7ab4d3bf12b34e5ada0c86"
      }
    ]
  },
  {
    "name": "fsevents",
    "version": "2.3.3",
    "integrity": "sha512-5xoDfX+fL7faATnagmWPpbFtwh/R77WmMMqqHGS65C3vvB0YHrgF+B1YmZ3441tMj5n63k0212XNoJwzlhffQw==",
    "tarball_sha256": "c77e7a5d5ff31dd7acea7c44d4a0455e0528cdacbd24a8cb6c82b66d239b587e",
    "members": 6,
    "scripts": {
      "clean": "node-gyp clean && rm -f fsevents.node",
      "build": "node-gyp clean && rm -f fsevents.node && node-gyp rebuild && node-gyp clean",
      "test": "/bin/bash ./test.sh 2>/dev/null",
      "prepublishOnly": "npm run build"
    },
    "license": "MIT",
    "license_members": [
      {
        "member": "package/LICENSE",
        "sha256": "2a8a5d6197bb97a018b8a190dd3ed853d750ca87c8e80c17aad41d6c6ff448e1"
      }
    ]
  },
  {
    "name": "picocolors",
    "version": "1.1.1",
    "integrity": "sha512-xceH2snhtb5M9liqDsmEw56le376mTZkEX/jEb/RxNFyegNul7eNslCXP9FDj/Lcu0X8KEyMceP2ntpaHrDEVA==",
    "tarball_sha256": "d3aedb2807967b7eb37fd11b03b7e3701e725af79c650d0812ff7213f8f882d9",
    "members": 7,
    "scripts": {},
    "license": "ISC",
    "license_members": [
      {
        "member": "package/LICENSE",
        "sha256": "6582629e2979466878f6014313dcc2f3756c9616148682227ce3063dde310750"
      }
    ]
  },
  {
    "name": "source-map-js",
    "version": "1.2.1",
    "integrity": "sha512-UXWMKhLOwVKb728IUtQPXxfYU+usdybtUrK/8uGE8CQMvrhOpwvzDBwj0QhSL7MQc7vIsISBG8VQ8+IDQxpfQA==",
    "tarball_sha256": "f126a6f9fca487a43219d8cb8c3a955279187a966119d548eb5cd47e999d4853",
    "members": 18,
    "scripts": {
      "test": "npm run build && node test/run-tests.js",
      "build": "webpack --color",
      "toc": "doctoc --title '## Table of Contents' README.md && doctoc --title '## Table of Contents' CONTRIBUTING.md"
    },
    "license": "BSD-3-Clause",
    "license_members": [
      {
        "member": "package/LICENSE",
        "sha256": "6cb0631f71c7749763fd3dd1d5bee52dd1070ec17f2edc1710079ad070bd2fbd"
      }
    ]
  },
  {
    "name": "tinyglobby",
    "version": "0.2.17",
    "integrity": "sha512-wXR/dYpcqKmfWpEdZjiKJOwCNFndD0DMnrW/cYjVGttEkBfVgcLFHoNrlj47mjOVic9yyNu65alsgF4NQyTa2g==",
    "tarball_sha256": "afb4afae9175f8b873ac13e1d21cea0997a0bcb40c3598613a834490058cb562",
    "members": 7,
    "scripts": {
      "bench": "node benchmark/bench.ts",
      "bench:setup": "node benchmark/setup.ts",
      "build": "tsdown",
      "check": "biome check",
      "check:fix": "biome check --write --unsafe",
      "format": "biome format --write",
      "lint": "biome lint",
      "test": "node --test \"test/**/*.ts\"",
      "test:coverage": "node --test --experimental-test-coverage \"test/**/*.ts\"",
      "test:only": "node --test --test-only \"test/**/*.ts\"",
      "typecheck": "tsc --noEmit"
    },
    "license": "MIT",
    "license_members": [
      {
        "member": "package/LICENSE",
        "sha256": "22c68811e174cbbfb3813d4135918df4f540959c14d872e601d9abe83d3cde8f"
      }
    ]
  }
]
```

Read-only full schema command: `.venv-memory-pilot/bin/python -B /tmp/explorer-contracts-implement-g3/check_schema_full.py`. jsonschema4.26.0 validates the Draft2020-12 meta-schema; the123 targeted cases use its validator plus declared strict integer-token/UTF-8 checks. Scratch validator SHA256 `046a46d3b89ec171308ed815749421d3fc2bece8d427b1927446ccf5e83f876c`. This test-only reuse introduces no runtime dependency.


## Lossless change-map inventory comparison

```json
{
  "rows_before": 268,
  "rows_after": 268,
  "all_identity_path_digest_authority_stage_requirement_task_fields_unchanged": true,
  "changes": "Concise equivalent repeated preservation/verification prose only. Complete shared policy remains in decisions and contract.",
  "original_bytes": 273865,
  "original_sha256": "19a5d2119e19c55f3a93c493b2b8723bbbef5397036db0d3077b0d6db6833d0c"
}
```

The original generated map remains in disposable `/tmp/explorer-contracts-implement-g3/change-map-original.json`. Every row and all non-prose fields were compared directly before current output hashes were refreshed. Only repeated generic prose was shortened; row-specific boundaries and all exact paths/IDs/stages/owners/digests were retained.


## Final file and inventory checks

The seven output paths were reopened. Draft202012Validator.check_schema passed on the written schema. The written change map validates against $defs/ChangeMap; its268 path/stage pairs are unique, and every non-null current after/source digest matched reopened bytes before the final evidence refresh. All seven copied license texts match the extracted archive members byte-for-byte. Reusable contract inspection contains no native assignment identity, manager path or private Task record. `git diff --check` reported no tracked diff errors for the seven scoped paths; these new files were also parsed/read directly because an untracked-file diff check alone is insufficient. No production runtime or overall requirement is marked complete.


## CONTRACT_IMPL_NEUTRALITY_01: current correction evidence

The nine exact correction packet input hashes matched before work. Only `$defs.ChangeMap` and `$defs.ChangeRow` were removed from the reusable schema. Their complete exact definitions, plus unchanged RelativePath/Digest dependencies, are retained in the local schema below. All124 runtime/configuration/wire/session/cursor/build definitions and every other top-level schema field were compared by parsed value and are unchanged. The source schema contains no hardcoded current plan ID or release-specific ChangeMap/ChangeRow definitions. The actual local map remains PLAN-20260920-9B9964BA revision1 with268 exact rows.

Previous schema SHA256: `352b4c34f0582bb6f90ffb687c5537609ea8c8b2d6515132705763633987d1c6`. Current schema SHA256: `8e6d0ceb47c98e77d518f4d7c935986ab6982d1a1c15e12377a726e90fbbb7a4`. Earlier checks remain historical; this current check uses the actual changed schema. No runtime rule, dependency pin, build, download or acceptance gate changed. Complete dependency/license/native-bin checks remain blocked as previously recorded.

Current command: `.venv-memory-pilot/bin/python -B /tmp/explorer-contracts-implement-g3/check_schema_neutrality.py`. The preexisting jsonschema4.26.0 Draft202012Validator meta-schema check and123 targeted cases passed with the same explicit integer-token/UTF-8 semantic checks.412 local references resolve; all31 fixed errors still fit1024 bytes, maximum658. Checker SHA256 `459341102c3e79e085c42528217d3e2114f40bee7de105bb8fdbfcd2eaaf3412`.

```json
{
  "level": "Draft 2020-12 meta-schema validation and targeted cases with required integer/UTF-8 semantic checks",
  "full_draft202012_validator": "jsonschema 4.26.0; Draft202012Validator.check_schema passed; targeted cases use strict integer-token and UTF-8 semantic extensions",
  "schema_sha256": "8e6d0ceb47c98e77d518f4d7c935986ab6982d1a1c15e12377a726e90fbbb7a4",
  "definitions": 124,
  "local_references_checked": 412,
  "unclosed_protocol_objects": [],
  "targeted_cases": 123,
  "cases": [
    {
      "name": "neutral config",
      "result": "pass",
      "definition": "configuration"
    },
    {
      "name": "unknown root",
      "result": "pass",
      "definition": "configuration"
    },
    {
      "name": "unknown nested limit",
      "result": "pass",
      "definition": "configuration"
    },
    {
      "name": "boolean limit",
      "result": "pass",
      "definition": "configuration"
    },
    {
      "name": "float limit",
      "result": "pass",
      "definition": "configuration"
    },
    {
      "name": "lower response below minimum",
      "result": "pass",
      "definition": "configuration"
    },
    {
      "name": "nonconfig request rejected",
      "result": "pass",
      "definition": "configuration"
    },
    {
      "name": "label control rejected",
      "result": "pass",
      "definition": "DisplayLabel"
    },
    {
      "name": "blank display label rejected",
      "result": "pass",
      "definition": "DisplayLabel"
    },
    {
      "name": "invalid ID case preserved",
      "result": "pass",
      "definition": "Id"
    },
    {
      "name": "unsafe path ../x",
      "result": "pass",
      "definition": "RelativePath"
    },
    {
      "name": "unsafe path a/../x",
      "result": "pass",
      "definition": "RelativePath"
    },
    {
      "name": "unsafe path a//b",
      "result": "pass",
      "definition": "RelativePath"
    },
    {
      "name": "unsafe path /etc/passwd",
      "result": "pass",
      "definition": "RelativePath"
    },
    {
      "name": "unsafe path a/./b",
      "result": "pass",
      "definition": "RelativePath"
    },
    {
      "name": "unsafe path a\\b",
      "result": "pass",
      "definition": "RelativePath"
    },
    {
      "name": "safe relative path",
      "result": "pass",
      "definition": "RelativePath"
    },
    {
      "name": "search request",
      "result": "pass",
      "definition": "SearchRequest"
    },
    {
      "name": "nonempty label sort rejected",
      "result": "pass",
      "definition": "SearchRequest"
    },
    {
      "name": "empty browse",
      "result": "pass",
      "definition": "SearchRequest"
    },
    {
      "name": "empty lifecycle rejected",
      "result": "pass",
      "definition": "SearchRequest"
    },
    {
      "name": "source selector injection rejected",
      "result": "pass",
      "definition": "SearchRequest"
    },
    {
      "name": "search snapshot required",
      "result": "pass",
      "definition": "SearchRequest"
    },
    {
      "name": "context initial request",
      "result": "pass",
      "definition": "ContextRequest"
    },
    {
      "name": "header continuation rejected",
      "result": "pass",
      "definition": "EntryRequest"
    },
    {
      "name": "nonempty Unicode chunk",
      "result": "pass",
      "definition": "TextChunk"
    },
    {
      "name": "empty advancing chunk rejected",
      "result": "pass",
      "definition": "TextChunk"
    },
    {
      "name": "process text",
      "result": "pass",
      "definition": "ProcessField"
    },
    {
      "name": "mixed process parts rejected",
      "result": "pass",
      "definition": "ProcessField"
    },
    {
      "name": "missing header rejected",
      "result": "pass",
      "definition": "EntryData"
    },
    {
      "name": "fixed error invalid_request",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "preauth error invalid_request",
      "result": "pass",
      "definition": "PreAuthErrorResponse"
    },
    {
      "name": "error text closed invalid_request",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "fixed error cursor_invalid",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "preauth error cursor_invalid",
      "result": "pass",
      "definition": "PreAuthErrorResponse"
    },
    {
      "name": "error text closed cursor_invalid",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "fixed error request_too_large",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "preauth error request_too_large",
      "result": "pass",
      "definition": "PreAuthErrorResponse"
    },
    {
      "name": "error text closed request_too_large",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "fixed error content_type_invalid",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "preauth error content_type_invalid",
      "result": "pass",
      "definition": "PreAuthErrorResponse"
    },
    {
      "name": "error text closed content_type_invalid",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "fixed error session_expired",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "preauth error session_expired",
      "result": "pass",
      "definition": "PreAuthErrorResponse"
    },
    {
      "name": "error text closed session_expired",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "fixed error session_invalid",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "preauth error session_invalid",
      "result": "pass",
      "definition": "PreAuthErrorResponse"
    },
    {
      "name": "error text closed session_invalid",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "fixed error host_forbidden",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "preauth error host_forbidden",
      "result": "pass",
      "definition": "PreAuthErrorResponse"
    },
    {
      "name": "error text closed host_forbidden",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "fixed error origin_forbidden",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "preauth error origin_forbidden",
      "result": "pass",
      "definition": "PreAuthErrorResponse"
    },
    {
      "name": "error text closed origin_forbidden",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "fixed error csrf_forbidden",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "preauth error csrf_forbidden",
      "result": "pass",
      "definition": "PreAuthErrorResponse"
    },
    {
      "name": "error text closed csrf_forbidden",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "fixed error source_forbidden",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "preauth error source_forbidden",
      "result": "pass",
      "definition": "PreAuthErrorResponse"
    },
    {
      "name": "error text closed source_forbidden",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "fixed error resource_forbidden",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "preauth error resource_forbidden",
      "result": "pass",
      "definition": "PreAuthErrorResponse"
    },
    {
      "name": "error text closed resource_forbidden",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "fixed error identity_unavailable",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "preauth error identity_unavailable",
      "result": "pass",
      "definition": "PreAuthErrorResponse"
    },
    {
      "name": "error text closed identity_unavailable",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "fixed error endpoint_unavailable",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "preauth error endpoint_unavailable",
      "result": "pass",
      "definition": "PreAuthErrorResponse"
    },
    {
      "name": "error text closed endpoint_unavailable",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "fixed error method_forbidden",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "preauth error method_forbidden",
      "result": "pass",
      "definition": "PreAuthErrorResponse"
    },
    {
      "name": "error text closed method_forbidden",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "fixed error snapshot_changed",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "preauth error snapshot_changed",
      "result": "pass",
      "definition": "PreAuthErrorResponse"
    },
    {
      "name": "error text closed snapshot_changed",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "fixed error cursor_scope_changed",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "preauth error cursor_scope_changed",
      "result": "pass",
      "definition": "PreAuthErrorResponse"
    },
    {
      "name": "error text closed cursor_scope_changed",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "fixed error cursor_expired",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "preauth error cursor_expired",
      "result": "pass",
      "definition": "PreAuthErrorResponse"
    },
    {
      "name": "error text closed cursor_expired",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "fixed error source_observation_changed",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "preauth error source_observation_changed",
      "result": "pass",
      "definition": "PreAuthErrorResponse"
    },
    {
      "name": "error text closed source_observation_changed",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "fixed error package_changed",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "preauth error package_changed",
      "result": "pass",
      "definition": "PreAuthErrorResponse"
    },
    {
      "name": "error text closed package_changed",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "fixed error canonical_invalid",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "preauth error canonical_invalid",
      "result": "pass",
      "definition": "PreAuthErrorResponse"
    },
    {
      "name": "error text closed canonical_invalid",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "fixed error presentation_invalid",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "preauth error presentation_invalid",
      "result": "pass",
      "definition": "PreAuthErrorResponse"
    },
    {
      "name": "error text closed presentation_invalid",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "fixed error configuration_needed",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "preauth error configuration_needed",
      "result": "pass",
      "definition": "PreAuthErrorResponse"
    },
    {
      "name": "error text closed configuration_needed",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "fixed error identity_mismatch",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "preauth error identity_mismatch",
      "result": "pass",
      "definition": "PreAuthErrorResponse"
    },
    {
      "name": "error text closed identity_mismatch",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "fixed error source_unavailable",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "preauth error source_unavailable",
      "result": "pass",
      "definition": "PreAuthErrorResponse"
    },
    {
      "name": "error text closed source_unavailable",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "fixed error source_locator_invalid",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "preauth error source_locator_invalid",
      "result": "pass",
      "definition": "PreAuthErrorResponse"
    },
    {
      "name": "error text closed source_locator_invalid",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "fixed error service_busy",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "preauth error service_busy",
      "result": "pass",
      "definition": "PreAuthErrorResponse"
    },
    {
      "name": "error text closed service_busy",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "fixed error knowledge_updating",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "preauth error knowledge_updating",
      "result": "pass",
      "definition": "PreAuthErrorResponse"
    },
    {
      "name": "error text closed knowledge_updating",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "fixed error package_incomplete",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "preauth error package_incomplete",
      "result": "pass",
      "definition": "PreAuthErrorResponse"
    },
    {
      "name": "error text closed package_incomplete",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "fixed error resource_limit",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "preauth error resource_limit",
      "result": "pass",
      "definition": "PreAuthErrorResponse"
    },
    {
      "name": "error text closed resource_limit",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "fixed error deadline_exceeded",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "preauth error deadline_exceeded",
      "result": "pass",
      "definition": "PreAuthErrorResponse"
    },
    {
      "name": "error text closed deadline_exceeded",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "fixed error internal_error",
      "result": "pass",
      "definition": "ErrorResponse"
    },
    {
      "name": "preauth error internal_error",
      "result": "pass",
      "definition": "PreAuthErrorResponse"
    },
    {
      "name": "error text closed internal_error",
      "result": "pass",
      "definition": "ErrorResponse"
    }
  ],
  "errors": [
    {
      "code": "invalid_request",
      "http_status": 400,
      "serialized_bytes": 628
    },
    {
      "code": "cursor_invalid",
      "http_status": 400,
      "serialized_bytes": 608
    },
    {
      "code": "request_too_large",
      "http_status": 413,
      "serialized_bytes": 627
    },
    {
      "code": "content_type_invalid",
      "http_status": 415,
      "serialized_bytes": 613
    },
    {
      "code": "session_expired",
      "http_status": 401,
      "serialized_bytes": 636
    },
    {
      "code": "session_invalid",
      "http_status": 401,
      "serialized_bytes": 621
    },
    {
      "code": "host_forbidden",
      "http_status": 403,
      "serialized_bytes": 626
    },
    {
      "code": "origin_forbidden",
      "http_status": 403,
      "serialized_bytes": 625
    },
    {
      "code": "csrf_forbidden",
      "http_status": 403,
      "serialized_bytes": 631
    },
    {
      "code": "source_forbidden",
      "http_status": 403,
      "serialized_bytes": 629
    },
    {
      "code": "resource_forbidden",
      "http_status": 403,
      "serialized_bytes": 630
    },
    {
      "code": "identity_unavailable",
      "http_status": 404,
      "serialized_bytes": 640
    },
    {
      "code": "endpoint_unavailable",
      "http_status": 404,
      "serialized_bytes": 622
    },
    {
      "code": "method_forbidden",
      "http_status": 405,
      "serialized_bytes": 629
    },
    {
      "code": "snapshot_changed",
      "http_status": 409,
      "serialized_bytes": 637
    },
    {
      "code": "cursor_scope_changed",
      "http_status": 409,
      "serialized_bytes": 640
    },
    {
      "code": "cursor_expired",
      "http_status": 409,
      "serialized_bytes": 643
    },
    {
      "code": "source_observation_changed",
      "http_status": 409,
      "serialized_bytes": 650
    },
    {
      "code": "package_changed",
      "http_status": 409,
      "serialized_bytes": 650
    },
    {
      "code": "canonical_invalid",
      "http_status": 422,
      "serialized_bytes": 630
    },
    {
      "code": "presentation_invalid",
      "http_status": 422,
      "serialized_bytes": 634
    },
    {
      "code": "configuration_needed",
      "http_status": 503,
      "serialized_bytes": 658
    },
    {
      "code": "identity_mismatch",
      "http_status": 422,
      "serialized_bytes": 633
    },
    {
      "code": "source_unavailable",
      "http_status": 422,
      "serialized_bytes": 619
    },
    {
      "code": "source_locator_invalid",
      "http_status": 422,
      "serialized_bytes": 645
    },
    {
      "code": "service_busy",
      "http_status": 429,
      "serialized_bytes": 623
    },
    {
      "code": "knowledge_updating",
      "http_status": 503,
      "serialized_bytes": 640
    },
    {
      "code": "package_incomplete",
      "http_status": 503,
      "serialized_bytes": 629
    },
    {
      "code": "resource_limit",
      "http_status": 503,
      "serialized_bytes": 652
    },
    {
      "code": "deadline_exceeded",
      "http_status": 504,
      "serialized_bytes": 624
    },
    {
      "code": "internal_error",
      "http_status": 500,
      "serialized_bytes": 626
    }
  ],
  "max_error_bytes": 658,
  "lockfile_version": 3,
  "locked_packages": 62,
  "lock_sha256": "c56e429ba8b70fe0e56ab5f879853f5267083eb7facbc0a6da36322b94afdbf9",
  "direct_integrities_match_frozen_evidence": true,
  "installed_bins": "not available",
  "runtime_behavior": "not implemented or tested"
}
```

### Local release map schema, excluded from reusable distribution

This exact JSON is the complete preserved local definition. Its disposable copy is `/tmp/explorer-contracts-implement-g3/local-change-map-schema.json`, SHA256 `a7bb68b0d1193242a8462790d805dcc9840d0c5662208006a4a10f2c7d54224c`. Offline Draft202012Validator.check_schema and validation of the current268-row map passed; wrong plan ID, revision and unknown root key were rejected. The actual map hashes are refreshed after this evidence file is finalized. No self hash is embedded in the map.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "Local Project Knowledge Explorer release change map",
  "description": "Project-specific release evidence only; never distributed as runtime schema.",
  "$ref": "#/$defs/ChangeMap",
  "$defs": {
    "ChangeMap": {
      "type": "object",
      "properties": {
        "schema_version": {
          "const": 1
        },
        "plan_id": {
          "const": "PLAN-20260920-9B9964BA"
        },
        "plan_revision": {
          "const": 1
        },
        "rows": {
          "type": "array",
          "items": {
            "$ref": "#/$defs/ChangeRow"
          },
          "minItems": 1,
          "maxItems": 10000
        }
      },
      "required": [
        "schema_version",
        "plan_id",
        "plan_revision",
        "rows"
      ],
      "additionalProperties": false
    },
    "ChangeRow": {
      "type": "object",
      "properties": {
        "path": {
          "$ref": "#/$defs/RelativePath"
        },
        "operation": {
          "enum": [
            "add",
            "replace",
            "delete",
            "retain"
          ]
        },
        "owner": {
          "type": "string",
          "minLength": 1,
          "maxLength": 160
        },
        "source_path": {
          "oneOf": [
            {
              "$ref": "#/$defs/RelativePath"
            },
            {
              "type": "null"
            }
          ]
        },
        "source_sha256": {
          "oneOf": [
            {
              "$ref": "#/$defs/Digest"
            },
            {
              "type": "null"
            }
          ]
        },
        "before_sha256": {
          "oneOf": [
            {
              "$ref": "#/$defs/Digest"
            },
            {
              "type": "null"
            }
          ]
        },
        "after_sha256": {
          "oneOf": [
            {
              "$ref": "#/$defs/Digest"
            },
            {
              "type": "null"
            }
          ]
        },
        "destination_project": {
          "type": "string",
          "minLength": 1,
          "maxLength": 160
        },
        "distribution_stage": {
          "enum": [
            "source",
            "template",
            "root",
            "fixture",
            "history",
            "evidence"
          ]
        },
        "requirement_ids": {
          "type": "array",
          "items": {
            "type": "string",
            "minLength": 7,
            "maxLength": 7,
            "pattern": "^REQ-0(?:0[1-9]|[1-4][0-9])$"
          },
          "minItems": 1,
          "maxItems": 49,
          "uniqueItems": true
        },
        "plan_task_ids": {
          "type": "array",
          "items": {
            "type": "string",
            "minLength": 8,
            "maxLength": 8,
            "pattern": "^TASK-0(?:0[1-9]|[12][0-9]|3[0-3])$"
          },
          "minItems": 1,
          "maxItems": 33,
          "uniqueItems": true
        },
        "preservation": {
          "type": "array",
          "items": {
            "type": "string",
            "minLength": 1,
            "maxLength": 2048
          },
          "minItems": 1,
          "maxItems": 32
        },
        "verification": {
          "type": "array",
          "items": {
            "type": "string",
            "minLength": 1,
            "maxLength": 2048
          },
          "minItems": 1,
          "maxItems": 32
        }
      },
      "required": [
        "path",
        "operation",
        "owner",
        "source_path",
        "source_sha256",
        "before_sha256",
        "after_sha256",
        "destination_project",
        "distribution_stage",
        "requirement_ids",
        "plan_task_ids",
        "preservation",
        "verification"
      ],
      "additionalProperties": false
    },
    "RelativePath": {
      "type": "string",
      "minLength": 1,
      "maxLength": 1024,
      "pattern": "^(?!/)(?!.*(?:^|/)(?:\\.|\\.\\.)(?:/|$))[^\\\\\\u0000-\\u001f/]+(?:/[^\\\\\\u0000-\\u001f/]+)*$",
      "x-max-utf8-bytes": 1024,
      "description": "Canonical relative_path grammar; selected-source paths additionally pass allowed_source_path and exact source allowlist membership."
    },
    "Digest": {
      "type": "string",
      "minLength": 64,
      "maxLength": 64,
      "pattern": "^[0-9a-f]{64}$"
    }
  }
}
```

## Current dependency and contract completion evidence

All 12 hashes in correction/resume packet `EV_G3_IMPL_DEPENDENCY_INPUTS` matched before work. Host provisioning is attributed to `/root`: receipt SHA256 `e377bb1b138589065fdfe133e94c437dc837623884080d007a664bf3ea692054` records successful `npm ci --ignore-scripts --no-audit --no-fund --cache /tmp/explorer-contracts-implement-g3/npm-cache` (19 packages) and exact-URL npm pack of62 archives. The implementer independently rechecked every current archive SHA512 against the live delivered lock and verified actual package names/versions. All1001 regular installed files across19 packages equal their verified archive members. The staging package and lock equal the delivered source package and lock.

Every actual license/notice/copyright-named text member was read in full by the archive inspector, indexed and retained without modification.70 member instances map to19 exact SHA256-deduplicated texts (214256 original text bytes). The235874-byte first complete notice rendering was cosmetically spaced to235876 bytes without altering the19 fenced texts. A final raw-byte comparison caught universal-newline normalization in a prose-edit read; the notice was restored from its exact UTF-8 source and all19 raw text byte sequences, including original CRLF, were verified again. This was a notice-generation correction, not an upstream package change. Each exact text is linked to every originating member; every package maps to notice blocks and its exact tarball, and repository provenance is preserved. The complete TypeScript NOTICE, bundled vscode-jsonrpc license and Vite bundled-dependency document are included. This is actual artifact text, not metadata substitution.

Fifteen @rolldown/binding-* archives contain no independent license/notice file. Their actual manifests match rolldown1.2.9 repository and package directory, and declare MIT; their index rows explicitly associate the inspected parent LICENSE and THIRD-PARTY-LICENSE. The absence is preserved rather than inventing a native-archive member. Other platform archives are inspected but not executed.

No archive declares preinstall/install/postinstall. fdir and fsevents declare publication-only commands; lightningcss declares prepare=`patch-package` and prepublishOnly=`node scripts/build-flow.js`. These command bodies were inspected in actual manifests. Their repository-only build scripts/tools are not included in the registry artifacts, are unnecessary for the already-built package, and were not executed. The fsevents lock hasInstallScript flag differs from its actual absence of install scripts/binding.gyp; it is not interpreted as an unobserved action. Host installation and archive packaging ignored scripts. The functioning installed native tools needed no manual postinstall.

Installed TypeScript launcher/import mapping and Vite launcher were inspected before scoped executable tests. The local `.bin` links resolve inside the same canonical staging node_modules. Node25.9.0/npm11.12.1, TypeScript7.0.2, Vite8.3.0 and Rolldown1.2.9 were observed directly. Strict TypeScript checking with skipLibCheck=false accepts Cytoscape's own bundled declarations; a deliberate wrong assignment yields TS2322/exit1. No @types package or global npx fallback was added. The headless Cytoscape test observes builtin preset positions, two parallel edges, a self-loop and clean disposal. Lightning CSS executes its darwin-arm64 native transform. Rolldown bundles only a disposable one-line module. These are package/toolchain tests, not a production Explorer build, DOM/canvas/CSP test or user acceptance.

One disposable checker initially compared resolved `/private/tmp` paths with unresolved `/tmp`, producing an assertion after tool checks. The checker was corrected to compare canonical staging paths, then rerun successfully. No package defect or failed compiler operation was inferred from that test-path issue.

### Actual artifact and hook inventory

The following compact JSON retains all62 exact artifact identities, integrity values, license-member hashes and inspected hook declarations. Complete package member-name inventory is disposable `all-artifacts.json`; the actual archive/lock identities are independently recorded here.

```json
[{"name":"cytoscape","version":"3.34.3","archive_bytes":1378263,"archive_sha256":"5d9e479216ed58a5f1ac639e746fd7d9770c4393f8c355dd133abc90bcc9ff3f","integrity":"sha512-yfYGhRcGAntq6YBD583j4n0Eg3jIxvWmZtz/5uz9UYkeIStSlMxuUja+ec5j3iBD8nv1rwaOAYMW09tBdkSeaQ==","tarball":"https://registry.npmjs.org/cytoscape/-/cytoscape-3.34.3.tgz","license":"MIT","repository":{"type":"git","url":"https://github.com/cytoscape/cytoscape.js.git"},"licenses":[{"member":"package/LICENSE","bytes":1082,"sha256":"eb319c6e6f233607f71e8e2f450391751883cfc0eeb3ca7ef574c13d1d9c2203"}],"hooks":{},"bin":null,"types":"index.d.ts","binding_gyp_present":false,"lock_hasInstallScript":false},{"name":"detect-libc","version":"2.1.2","archive_bytes":7776,"archive_sha256":"270dec0fc06cff86481da8af2dd8f18dee6b602790b14ef0e1c2c18d7da39427","integrity":"sha512-Btj2BOOO83o3WyH59e8MgXsxEQVcarkUOpEYrubB0urwnN10yQ364rsiByU11nZlqWYZm05i/of7io4mzihBtQ==","tarball":"https://registry.npmjs.org/detect-libc/-/detect-libc-2.1.2.tgz","license":"Apache-2.0","repository":{"type":"git","url":"git://github.com/lovell/detect-libc.git"},"licenses":[{"member":"package/LICENSE","bytes":11357,"sha256":"b40930bbcf80744c86c46a12bc9da056641d722716c378f5659b9e555ef833e1"}],"hooks":{},"bin":null,"types":"index.d.ts","binding_gyp_present":false,"lock_hasInstallScript":false},{"name":"fdir","version":"6.5.0","archive_bytes":9742,"archive_sha256":"241ddcd9f31e2a1fca405326017dbb8333ce174198e887f0f96387c29f0d365e","integrity":"sha512-tIbYtZbucOs0BRGqPJkshJUYdL+SDH7dVM8gjy+ERp3WAUjLEFJE+02kanyHtwjWOnwrKYBiwAmM0p4kLJAnXg==","tarball":"https://registry.npmjs.org/fdir/-/fdir-6.5.0.tgz","license":"MIT","repository":{"type":"git","url":"git+https://github.com/thecodrr/fdir.git"},"licenses":[{"member":"package/LICENSE","bytes":1053,"sha256":"9a39f2aadab11a3697edd668ff2d8ad885b649737b7ab4d3bf12b34e5ada0c86"}],"hooks":{"prepublishOnly":"npm run test && npm run build"},"bin":null,"types":"./dist/index.d.cts","binding_gyp_present":false,"lock_hasInstallScript":false},{"name":"fsevents","version":"2.3.3","archive_bytes":22808,"archive_sha256":"c77e7a5d5ff31dd7acea7c44d4a0455e0528cdacbd24a8cb6c82b66d239b587e","integrity":"sha512-5xoDfX+fL7faATnagmWPpbFtwh/R77WmMMqqHGS65C3vvB0YHrgF+B1YmZ3441tMj5n63k0212XNoJwzlhffQw==","tarball":"https://registry.npmjs.org/fsevents/-/fsevents-2.3.3.tgz","license":"MIT","repository":{"type":"git","url":"https://github.com/fsevents/fsevents.git"},"licenses":[{"member":"package/LICENSE","bytes":1133,"sha256":"2a8a5d6197bb97a018b8a190dd3ed853d750ca87c8e80c17aad41d6c6ff448e1"}],"hooks":{"prepublishOnly":"npm run build"},"bin":null,"types":"fsevents.d.ts","binding_gyp_present":false,"lock_hasInstallScript":true},{"name":"lightningcss","version":"1.33.0","archive_bytes":87655,"archive_sha256":"d492f4278bb7234ceaa3c2638ef944e108ea17a23db7c6a2367c14fa725598cf","integrity":"sha512-WkUDrojuJs0xkgGf2udWxa3yGBRxPtxUkB79i6aCZLRgc7PM8fZe9TosfPDcvEpQZbuFASnHYmRLBLUbmLOIIA==","tarball":"https://registry.npmjs.org/lightningcss/-/lightningcss-1.33.0.tgz","license":"MPL-2.0","repository":{"type":"git","url":"https://github.com/parcel-bundler/lightningcss.git"},"licenses":[{"member":"package/LICENSE","bytes":15648,"sha256":"5eba353fe5076ac3432177f8ab1cf75e3afcd0584251e37c3bfead5f447d040e"}],"hooks":{"prepare":"patch-package","prepublishOnly":"node scripts/build-flow.js"},"bin":null,"types":"node/index.d.ts","binding_gyp_present":false,"lock_hasInstallScript":false},{"name":"lightningcss-android-arm64","version":"1.33.0","archive_bytes":3632951,"archive_sha256":"e6fd2befa439a4934dd50a9283820a7b95725246a3251c60588f074aff20509a","integrity":"sha512-gEpRTalKdosp4Bb8qWtc2iOgE5SeIHlpS1up9bFq2wAyYhl1UdTObYiHe98zEM9SQvSoqQZ1IQD0JNpg3Ml5pg==","tarball":"https://registry.npmjs.org/lightningcss-android-arm64/-/lightningcss-android-arm64-1.33.0.tgz","license":"MPL-2.0","repository":{"type":"git","url":"https://github.com/parcel-bundler/lightningcss.git"},"licenses":[{"member":"package/LICENSE","bytes":15648,"sha256":"5eba353fe5076ac3432177f8ab1cf75e3afcd0584251e37c3bfead5f447d040e"}],"hooks":{},"bin":null,"types":null,"binding_gyp_present":false,"lock_hasInstallScript":false},{"name":"lightningcss-darwin-arm64","version":"1.33.0","archive_bytes":3455710,"archive_sha256":"06e9d271513d7e3f08e680d5e48bb70543c13161ff41bc5b56934726d9a2e913","integrity":"sha512-Sciaz8eenNTKn9b3t7+xr0ipTp9YxKQY4npwQ3mrRuL0BAVHBLyZxofhaKBAVtzmtRZ/zTyo0/to4B1uWG/Djg==","tarball":"https://registry.npmjs.org/lightningcss-darwin-arm64/-/lightningcss-darwin-arm64-1.33.0.tgz","license":"MPL-2.0","repository":{"type":"git","url":"https://github.com/parcel-bundler/lightningcss.git"},"licenses":[{"member":"package/LICENSE","bytes":15648,"sha256":"5eba353fe5076ac3432177f8ab1cf75e3afcd0584251e37c3bfead5f447d040e"}],"hooks":{},"bin":null,"types":null,"binding_gyp_present":false,"lock_hasInstallScript":false},{"name":"lightningcss-darwin-x64","version":"1.33.0","archive_bytes":3875799,"archive_sha256":"c0b555fe6ec4c5c660503b1e87aad7ac90ba5af1e2cb1742155d485a39d5b973","integrity":"sha512-Z5UPAxzrjlWNNyGy6i65cJzzvgJ5D3T6wMvs+gWpY9d7qRhANrxqAp6LhxIgZhWEw18RfJTGcRxjuLIBr+m8XQ==","tarball":"https://registry.npmjs.org/lightningcss-darwin-x64/-/lightningcss-darwin-x64-1.33.0.tgz","license":"MPL-2.0","repository":{"type":"git","url":"https://github.com/parcel-bundler/lightningcss.git"},"licenses":[{"member":"package/LICENSE","bytes":15648,"sha256":"5eba353fe5076ac3432177f8ab1cf75e3afcd0584251e37c3bfead5f447d040e"}],"hooks":{},"bin":null,"types":null,"binding_gyp_present":false,"lock_hasInstallScript":false},{"name":"lightningcss-freebsd-x64","version":"1.33.0","archive_bytes":3863824,"archive_sha256":"828e9a915d504a2796bdbe56643397d3ac639bf9abc629ba11163e7b7ef150a6","integrity":"sha512-QQM/Ti/hQajJwCY+RiWuCZ9sdtI/XQk7nDK5vC8kkdwixezOlDgvDx7+RT+QjK6FcFT4MpsuoBnHIo/O3StRRg==","tarball":"https://registry.npmjs.org/lightningcss-freebsd-x64/-/lightningcss-freebsd-x64-1.33.0.tgz","license":"MPL-2.0","repository":{"type":"git","url":"https://github.com/parcel-bundler/lightningcss.git"},"licenses":[{"member":"package/LICENSE","bytes":15648,"sha256":"5eba353fe5076ac3432177f8ab1cf75e3afcd0584251e37c3bfead5f447d040e"}],"hooks":{},"bin":null,"types":null,"binding_gyp_present":false,"lock_hasInstallScript":false},{"name":"lightningcss-linux-arm-gnueabihf","version":"1.33.0","archive_bytes":3536007,"archive_sha256":"b2a0af78c27da36a2449c2fe71eb3730e6c40d7aaab20bdc3689282432bb3117","integrity":"sha512-N7FVBe6iS24MlM6R/4RBTxGhQheZGs7tiQ9U32UtF75NzP5Q7xWPRqLBCKxlRQRk3rY1jCIPLzx7WzOhuUIRLQ==","tarball":"https://registry.npmjs.org/lightningcss-linux-arm-gnueabihf/-/lightningcss-linux-arm-gnueabihf-1.33.0.tgz","license":"MPL-2.0","repository":{"type":"git","url":"https://github.com/parcel-bundler/lightningcss.git"},"licenses":[{"member":"package/LICENSE","bytes":15648,"sha256":"5eba353fe5076ac3432177f8ab1cf75e3afcd0584251e37c3bfead5f447d040e"}],"hooks":{},"bin":null,"types":null,"binding_gyp_present":false,"lock_hasInstallScript":false},{"name":"lightningcss-linux-arm64-gnu","version":"1.33.0","archive_bytes":3593473,"archive_sha256":"257b51498dfd90fc99b87afd28408ff9b53162e521db4e06a493e356b8536711","integrity":"sha512-j2v/itmy4HlNxlc6voKXYgBqNi0Ng2LShg4z7GufpEgs05P+2suBVyi9I6YHq5uoVFx9ETin3eCEhLVyXGQnKg==","tarball":"https://registry.npmjs.org/lightningcss-linux-arm64-gnu/-/lightningcss-linux-arm64-gnu-1.33.0.tgz","license":"MPL-2.0","repository":{"type":"git","url":"https://github.com/parcel-bundler/lightningcss.git"},"licenses":[{"member":"package/LICENSE","bytes":15648,"sha256":"5eba353fe5076ac3432177f8ab1cf75e3afcd0584251e37c3bfead5f447d040e"}],"hooks":{},"bin":null,"types":null,"binding_gyp_present":false,"lock_hasInstallScript":false},{"name":"lightningcss-linux-arm64-musl","version":"1.33.0","archive_bytes":3592480,"archive_sha256":"048a00d8ef519a413e01907a5a50e01d7c4e86ddcde49a5020eed7747196b9f6","integrity":"sha512-yiO5ROMuYQgXbC60yjZU5CYSFZGKXL0HFATXt9mHJn1+zW55oCtMI9NfcVhYLMFDL7gV7oBPon/EmMMGg2OvtQ==","tarball":"https://registry.npmjs.org/lightningcss-linux-arm64-musl/-/lightningcss-linux-arm64-musl-1.33.0.tgz","license":"MPL-2.0","repository":{"type":"git","url":"https://github.com/parcel-bundler/lightningcss.git"},"licenses":[{"member":"package/LICENSE","bytes":15648,"sha256":"5eba353fe5076ac3432177f8ab1cf75e3afcd0584251e37c3bfead5f447d040e"}],"hooks":{},"bin":null,"types":null,"binding_gyp_present":false,"lock_hasInstallScript":false},{"name":"lightningcss-linux-x64-gnu","version":"1.33.0","archive_bytes":3855795,"archive_sha256":"fd485dfd57082c4ef864dd867fa87fd8e1a9b5d58ee85c2b76e28e42c8f3e1d3","integrity":"sha512-ar+Ju7LmcN0Jo4FpL4hpFybwNG9/3A/Br5KW2n2jyODg3MEZXaDYADdemoNS+BDNfMgKvylJLj4S5tyRActuAg==","tarball":"https://registry.npmjs.org/lightningcss-linux-x64-gnu/-/lightningcss-linux-x64-gnu-1.33.0.tgz","license":"MPL-2.0","repository":{"type":"git","url":"https://github.com/parcel-bundler/lightningcss.git"},"licenses":[{"member":"package/LICENSE","bytes":15648,"sha256":"5eba353fe5076ac3432177f8ab1cf75e3afcd0584251e37c3bfead5f447d040e"}],"hooks":{},"bin":null,"types":null,"binding_gyp_present":false,"lock_hasInstallScript":false},{"name":"lightningcss-linux-x64-musl","version":"1.33.0","archive_bytes":3853971,"archive_sha256":"f3a1a10f3c393db5ce03438035b94fcd48bc7b7b52bb97f76a3ed52784624441","integrity":"sha512-RYiYbkokw0trfKqqzfF55lginwEPrD3OJDfTuJzFs1MK6iFnDenaz1fqLLtX4ITG3OktJQXOeTaw1awrBAlZPw==","tarball":"https://registry.npmjs.org/lightningcss-linux-x64-musl/-/lightningcss-linux-x64-musl-1.33.0.tgz","license":"MPL-2.0","repository":{"type":"git","url":"https://github.com/parcel-bundler/lightningcss.git"},"licenses":[{"member":"package/LICENSE","bytes":15648,"sha256":"5eba353fe5076ac3432177f8ab1cf75e3afcd0584251e37c3bfead5f447d040e"}],"hooks":{},"bin":null,"types":null,"binding_gyp_present":false,"lock_hasInstallScript":false},{"name":"lightningcss-win32-arm64-msvc","version":"1.33.0","archive_bytes":3429085,"archive_sha256":"9c211ef0a63a92626091f7c0a97b0ddb39b4278da5b11d13512b7eed9680bd7d","integrity":"sha512-1K+MPfLSFVpphzpdbfkhlWk6wBrTObBzS2T6db10PNOZgR9GoVsAWzwNyuhUYYbTp23j+4RrncfujZ4uAzXvwA==","tarball":"https://registry.npmjs.org/lightningcss-win32-arm64-msvc/-/lightningcss-win32-arm64-msvc-1.33.0.tgz","license":"MPL-2.0","repository":{"type":"git","url":"https://github.com/parcel-bundler/lightningcss.git"},"licenses":[{"member":"package/LICENSE","bytes":15648,"sha256":"5eba353fe5076ac3432177f8ab1cf75e3afcd0584251e37c3bfead5f447d040e"}],"hooks":{},"bin":null,"types":null,"binding_gyp_present":false,"lock_hasInstallScript":false},{"name":"lightningcss-win32-x64-msvc","version":"1.33.0","archive_bytes":3706526,"archive_sha256":"feb506faf3bdf4139826f521777c71b53c355f8eb6bcdd3220e16c5e131f1197","integrity":"sha512-OlEICDx/Xl0FqSp4bry8zFnCvGpig3Gl4gCquvYwHuqJKEC1+n9NgDniFvqHGmMv1ZkqDJrDqKKSykTDX+ehuA==","tarball":"https://registry.npmjs.org/lightningcss-win32-x64-msvc/-/lightningcss-win32-x64-msvc-1.33.0.tgz","license":"MPL-2.0","repository":{"type":"git","url":"https://github.com/parcel-bundler/lightningcss.git"},"licenses":[{"member":"package/LICENSE","bytes":15648,"sha256":"5eba353fe5076ac3432177f8ab1cf75e3afcd0584251e37c3bfead5f447d040e"}],"hooks":{},"bin":null,"types":null,"binding_gyp_present":false,"lock_hasInstallScript":false},{"name":"nanoid","version":"3.3.19","archive_bytes":5694,"archive_sha256":"4e371b71e3d5081fa0052356d5c1904e7a60e049864c26f0724cfd32dc303849","integrity":"sha512-Y2tUNy4ouw6tq5oDSKeQYGOyhkUBhNOcGV/02KC+6kd9eDGqdZd++mjMiIDilrBYvjEnCYvVtsuHCuP+okSfug==","tarball":"https://registry.npmjs.org/nanoid/-/nanoid-3.3.19.tgz","license":"MIT","repository":"ai/nanoid","licenses":[{"member":"package/LICENSE","bytes":1095,"sha256":"da4db1480d9beea3483a2eda5c53b22238d0827d57da162b48f122e04d2d9987"}],"hooks":{},"bin":"./bin/nanoid.cjs","types":"./index.d.ts","binding_gyp_present":false,"lock_hasInstallScript":false},{"name":"@oxc-project/types","version":"0.150.0","archive_bytes":7677,"archive_sha256":"a05790e81e949ec9483aa013851236c02f19a9b503a8ff84783e48a448e33feb","integrity":"sha512-rDS5/31E9HfPl/CIzGrn0DOlvBbXFseQ5URJ9sYMfstbKLD/c6Gm9vmRzRGDdAXyOIL4zmO37lc9RIwYqVruZw==","tarball":"https://registry.npmjs.org/@oxc-project/types/-/types-0.150.0.tgz","license":"MIT","repository":{"type":"git","url":"git+https://github.com/oxc-project/oxc.git","directory":"npm/oxc-types"},"licenses":[{"member":"package/LICENSE","bytes":1119,"sha256":"95ced5ecf1133fbf41d409b5555c86c344f83f3b019926057ddbc07cfdcc27b3"}],"hooks":{},"bin":null,"types":"types.d.ts","binding_gyp_present":false,"lock_hasInstallScript":false},{"name":"picocolors","version":"1.1.1","archive_bytes":2625,"archive_sha256":"d3aedb2807967b7eb37fd11b03b7e3701e725af79c650d0812ff7213f8f882d9","integrity":"sha512-xceH2snhtb5M9liqDsmEw56le376mTZkEX/jEb/RxNFyegNul7eNslCXP9FDj/Lcu0X8KEyMceP2ntpaHrDEVA==","tarball":"https://registry.npmjs.org/picocolors/-/picocolors-1.1.1.tgz","license":"ISC","repository":"alexeyraspopov/picocolors","licenses":[{"member":"package/LICENSE","bytes":787,"sha256":"6582629e2979466878f6014313dcc2f3756c9616148682227ce3063dde310750"}],"hooks":{},"bin":null,"types":"./picocolors.d.ts","binding_gyp_present":false,"lock_hasInstallScript":false},{"name":"picomatch","version":"4.0.7","archive_bytes":24326,"archive_sha256":"697b463be3cdbd9ffc8f4194fd5019a69ddf95875fb703d78b2b115cc9e740a8","integrity":"sha512-qcJu88Q2IWqJsDD529JKMdwGm/dvInW4HvQnRwiH9JtihJvzGOscDtHE3x1pBKeUOTysQ8kVmLnJ2kJu7yhcGA==","tarball":"https://registry.npmjs.org/picomatch/-/picomatch-4.0.7.tgz","license":"MIT","repository":"micromatch/picomatch","licenses":[{"member":"package/LICENSE","bytes":1091,"sha256":"d0cd141b0c322fded5dfad1d4645bb2fedfc05b7321fe1009469638190d59ef9"}],"hooks":{},"bin":null,"types":null,"binding_gyp_present":false,"lock_hasInstallScript":false},{"name":"postcss","version":"8.5.28","archive_bytes":52195,"archive_sha256":"f63d6d9bce28989cd083add85af717c0264e44323d35c909ae99ac934e9641a6","integrity":"sha512-RRuzqDtt5Y9h3quz5hWhK+TPnsmVs6WwSU6LkJMeY4HstUEDuYTG8UJSdawMRzmzAtV+KEoG8N3Qg2qLy5vM/A==","tarball":"https://registry.npmjs.org/postcss/-/postcss-8.5.28.tgz","license":"MIT","repository":"postcss/postcss","licenses":[{"member":"package/LICENSE","bytes":1095,"sha256":"5be1f3465bba68a626777f984878814aaf35e7ef8e9fd314d469bcf887050fb8"}],"hooks":{},"bin":null,"types":"./lib/postcss.d.ts","binding_gyp_present":false,"lock_hasInstallScript":false},{"name":"rolldown","version":"1.2.9","archive_bytes":197948,"archive_sha256":"68c344a0cfab1cca11288b0175bab84a6702cb7b0c7f60aa4322fb69782d34f8","integrity":"sha512-hx/Pv0N1haXRb11qkfnK5MXB/iqr7i0yjWQqmO9uHqZpBgQSqzc8UsSnEpalsh+j1I8qQ2CkXAkJC8Br3dKSlg==","tarball":"https://registry.npmjs.org/rolldown/-/rolldown-1.2.9.tgz","license":"MIT","repository":{"type":"git","url":"git+https://github.com/rolldown/rolldown.git","directory":"packages/rolldown"},"licenses":[{"member":"package/LICENSE","bytes":1302,"sha256":"23ecfff35a5a2e80d92142f75228912c3b1abc4b5a8337a821ff4397e2f9f734"},{"member":"package/THIRD-PARTY-LICENSE","bytes":2209,"sha256":"a877291d800ed43692f3f9ae09d8e01cc6f7293ad39d43896059c188ffbb8b7c"}],"hooks":{},"bin":{"rolldown":"./bin/cli.mjs"},"types":"./dist/index.d.mts","binding_gyp_present":false,"lock_hasInstallScript":false},{"name":"@rolldown/binding-android-arm-eabi","version":"1.2.9","archive_bytes":6517667,"archive_sha256":"2a7fc7d6ebbe4840fb4c05b846301b1d49e3032dc2182aac829fe501687439f9","integrity":"sha512-tNISae1QEf/vkb3xkRcjV5SEdzPE97We5IVaa2Z8jSszQPZ8U60B/YCYpw4QI7VidYsBtKavczXf+DyDs9WGxw==","tarball":"https://registry.npmjs.org/@rolldown/binding-android-arm-eabi/-/binding-android-arm-eabi-1.2.9.tgz","license":"MIT","repository":{"type":"git","url":"git+https://github.com/rolldown/rolldown.git","directory":"packages/rolldown"},"licenses":[],"hooks":{},"bin":null,"types":null,"binding_gyp_present":false,"lock_hasInstallScript":false},{"name":"@rolldown/binding-android-arm64","version":"1.2.9","archive_bytes":7486202,"archive_sha256":"0329058d7bdd75a884dcc2d691c2082e4ee2731946e375c2f552c2b992384215","integrity":"sha512-YC8YsI30o606GTZi0VyzYlsDKFP8W61i/QzayHDkLbNEz/IShqAmTa+hsJRj13xTHA0H+6fk4b2UmGn+Q/cMlg==","tarball":"https://registry.npmjs.org/@rolldown/binding-android-arm64/-/binding-android-arm64-1.2.9.tgz","license":"MIT","repository":{"type":"git","url":"git+https://github.com/rolldown/rolldown.git","directory":"packages/rolldown"},"licenses":[],"hooks":{},"bin":null,"types":null,"binding_gyp_present":false,"lock_hasInstallScript":false},{"name":"@rolldown/binding-darwin-arm64","version":"1.2.9","archive_bytes":7185650,"archive_sha256":"7b7da204879507a070d723323439f107d879cb8e11a4f2e2f0a9d3ee81ffbf80","integrity":"sha512-IwhlH3qK5urrY8hZiEgGkHKEFN901p/p2bjxCxJlr4GyNnF7wYpUvK+Y43uaRYuC4hpfjzbR3SJC3arX1jGvmw==","tarball":"https://registry.npmjs.org/@rolldown/binding-darwin-arm64/-/binding-darwin-arm64-1.2.9.tgz","license":"MIT","repository":{"type":"git","url":"git+https://github.com/rolldown/rolldown.git","directory":"packages/rolldown"},"licenses":[],"hooks":{},"bin":null,"types":null,"binding_gyp_present":false,"lock_hasInstallScript":false},{"name":"@rolldown/binding-darwin-x64","version":"1.2.9","archive_bytes":7533249,"archive_sha256":"a37d9166d018006a02a9694d8b0b8adc6675fd2702553d0ffa6d93b7109dc10a","integrity":"sha512-XxpJfVzFh+jilRxIXUqcfYAYcunIc/XEzIizsOL1fcJee5Sf7H3mH8WlLmfHfluz5amqR88QQo9izKtmMlavAw==","tarball":"https://registry.npmjs.org/@rolldown/binding-darwin-x64/-/binding-darwin-x64-1.2.9.tgz","license":"MIT","repository":{"type":"git","url":"git+https://github.com/rolldown/rolldown.git","directory":"packages/rolldown"},"licenses":[],"hooks":{},"bin":null,"types":null,"binding_gyp_present":false,"lock_hasInstallScript":false},{"name":"@rolldown/binding-freebsd-x64","version":"1.2.9","archive_bytes":7880701,"archive_sha256":"365cf63d714518bb2ab009b9fdb05c3148462f5765df838d14f8ef9187056f7c","integrity":"sha512-kSfvhmgeWyfkbT3p/1s5vSgboogoah2zkm9fX2zjg2hHxSV7T4KhMWRUUaRk4OXNqoD3QAUeRqLcs1aZOK4U1g==","tarball":"https://registry.npmjs.org/@rolldown/binding-freebsd-x64/-/binding-freebsd-x64-1.2.9.tgz","license":"MIT","repository":{"type":"git","url":"git+https://github.com/rolldown/rolldown.git","directory":"packages/rolldown"},"licenses":[],"hooks":{},"bin":null,"types":null,"binding_gyp_present":false,"lock_hasInstallScript":false},{"name":"@rolldown/binding-linux-arm-gnueabihf","version":"1.2.9","archive_bytes":7240757,"archive_sha256":"5a1430961129ccfdccdd8e4c2319fb01e365d4843e7b2f946a784d84bd149cd8","integrity":"sha512-1RVzG17pxqbTfYLC352JlLt6kKLG+6Hr30n8DlIJqsnV5luUDd2Qdx9Ayw1Cabfyb1K9k0jXEZ7evxkRoT+uiw==","tarball":"https://registry.npmjs.org/@rolldown/binding-linux-arm-gnueabihf/-/binding-linux-arm-gnueabihf-1.2.9.tgz","license":"MIT","repository":{"type":"git","url":"git+https://github.com/rolldown/rolldown.git","directory":"packages/rolldown"},"licenses":[],"hooks":{},"bin":null,"types":null,"binding_gyp_present":false,"lock_hasInstallScript":false},{"name":"@rolldown/binding-linux-arm64-gnu","version":"1.2.9","archive_bytes":7508338,"archive_sha256":"3c1356d59dea6c214370445893e269c6c88e2f74f310e8a21487c560ac82b508","integrity":"sha512-BXqPvZ2drqVD+/Z8UpKwcs4Mp7grM+eGFku4CAEKrEtcbAsUpzREphK1sogCRZGreVPiMkiiBtw0n3TPteuqvw==","tarball":"https://registry.npmjs.org/@rolldown/binding-linux-arm64-gnu/-/binding-linux-arm64-gnu-1.2.9.tgz","license":"MIT","repository":{"type":"git","url":"git+https://github.com/rolldown/rolldown.git","directory":"packages/rolldown"},"licenses":[],"hooks":{},"bin":null,"types":null,"binding_gyp_present":false,"lock_hasInstallScript":false},{"name":"@rolldown/binding-linux-arm64-musl","version":"1.2.9","archive_bytes":7528422,"archive_sha256":"e89c3714ecca4c5e4a9e386765d71b3ce624ca4c796b1709ebe11ae58a301852","integrity":"sha512-11vWvo8YDwLzukt27J3aYDWU+gg2P7J+ZOmiJ0hkF5BXZDW7pVya7r40MXDy6ya0i9KamoENSVKIugvJNgFXIA==","tarball":"https://registry.npmjs.org/@rolldown/binding-linux-arm64-musl/-/binding-linux-arm64-musl-1.2.9.tgz","license":"MIT","repository":{"type":"git","url":"git+https://github.com/rolldown/rolldown.git","directory":"packages/rolldown"},"licenses":[],"hooks":{},"bin":null,"types":null,"binding_gyp_present":false,"lock_hasInstallScript":false},{"name":"@rolldown/binding-linux-ppc64-gnu","version":"1.2.9","archive_bytes":8782585,"archive_sha256":"aa6bf25391b2d901bb3b73595ccec8f79cea1782ca474b2166b36df7a4dd647b","integrity":"sha512-a1tijMkdwsIARtc0F39ApURROkf3NwqinI6TOiSSWCTR7dT96dffNvMUtDHnq64wKNTIZOIlzKrFvvFUznJiyw==","tarball":"https://registry.npmjs.org/@rolldown/binding-linux-ppc64-gnu/-/binding-linux-ppc64-gnu-1.2.9.tgz","license":"MIT","repository":{"type":"git","url":"git+https://github.com/rolldown/rolldown.git","directory":"packages/rolldown"},"licenses":[],"hooks":{},"bin":null,"types":null,"binding_gyp_present":false,"lock_hasInstallScript":false},{"name":"@rolldown/binding-linux-s390x-gnu","version":"1.2.9","archive_bytes":8008901,"archive_sha256":"e5c556e73fd01be057ddf6b99121dce6bacb69cbff4c6f5e827c196a1f6bdb39","integrity":"sha512-x6SQNdAvv4c3hWqTMaWuawzMX9myaCs/yEmlGsxJzkdClnHW7FbrjQuSiRDhuSYzEYoEMhsaJy9qHG/XNemJPQ==","tarball":"https://registry.npmjs.org/@rolldown/binding-linux-s390x-gnu/-/binding-linux-s390x-gnu-1.2.9.tgz","license":"MIT","repository":{"type":"git","url":"git+https://github.com/rolldown/rolldown.git","directory":"packages/rolldown"},"licenses":[],"hooks":{},"bin":null,"types":null,"binding_gyp_present":false,"lock_hasInstallScript":false},{"name":"@rolldown/binding-linux-x64-gnu","version":"1.2.9","archive_bytes":7926785,"archive_sha256":"cc5912bf3748daf3aa9aa5a60a2b63b68d985367d2af72ebb1db65a8c95d6d8d","integrity":"sha512-9s0AZ8BFK5/n7B/TBoa2yJE3gI3KURrbXcPBlsAsvjU4VeJKgE90y1YtNxyEUIcHPQkg6/yfF3qihUrcM/Kf0Q==","tarball":"https://registry.npmjs.org/@rolldown/binding-linux-x64-gnu/-/binding-linux-x64-gnu-1.2.9.tgz","license":"MIT","repository":{"type":"git","url":"git+https://github.com/rolldown/rolldown.git","directory":"packages/rolldown"},"licenses":[],"hooks":{},"bin":null,"types":null,"binding_gyp_present":false,"lock_hasInstallScript":false},{"name":"@rolldown/binding-linux-x64-musl","version":"1.2.9","archive_bytes":7912751,"archive_sha256":"35dc9646962d891c15ea1c2cb93e160d1395e174988a1e7d86d9dfe51832c89d","integrity":"sha512-P7VWAmV+WdJluH7ovnRGoiv2i8To7GAZ+kGzfGup635cyL7SyYl3lSUaA3Gp5THf0n/Co5EyEqb2zbqq+nMOHQ==","tarball":"https://registry.npmjs.org/@rolldown/binding-linux-x64-musl/-/binding-linux-x64-musl-1.2.9.tgz","license":"MIT","repository":{"type":"git","url":"git+https://github.com/rolldown/rolldown.git","directory":"packages/rolldown"},"licenses":[],"hooks":{},"bin":null,"types":null,"binding_gyp_present":false,"lock_hasInstallScript":false},{"name":"@rolldown/binding-openharmony-arm64","version":"1.2.9","archive_bytes":7440516,"archive_sha256":"9e335127acd141d3fdbc83158ed399072327cc9376f4e753c85a53341ba59cde","integrity":"sha512-1qixtsE4BK8h+yS3BfmZ09UhA7O/N4IACva6YBr7EBvCJraByTuRcgOTaiA62Tm0vey3UcKXLOaoGHtYmNGEVg==","tarball":"https://registry.npmjs.org/@rolldown/binding-openharmony-arm64/-/binding-openharmony-arm64-1.2.9.tgz","license":"MIT","repository":{"type":"git","url":"git+https://github.com/rolldown/rolldown.git","directory":"packages/rolldown"},"licenses":[],"hooks":{},"bin":null,"types":null,"binding_gyp_present":false,"lock_hasInstallScript":false},{"name":"@rolldown/binding-win32-arm64-msvc","version":"1.2.9","archive_bytes":7615786,"archive_sha256":"c0249bb3cae06c97045294b28cd1bc2446ea60db02ccc20c7d4bc456cfcdad18","integrity":"sha512-ok8IQjcEPs1AKZfuEUznVBrJw+gK4soq+bx8b1X2XoMqVClarc1q5JDmVtWXY1xfr6ZuHTAsPXHTgTrqKTZeww==","tarball":"https://registry.npmjs.org/@rolldown/binding-win32-arm64-msvc/-/binding-win32-arm64-msvc-1.2.9.tgz","license":"MIT","repository":{"type":"git","url":"git+https://github.com/rolldown/rolldown.git","directory":"packages/rolldown"},"licenses":[],"hooks":{},"bin":null,"types":null,"binding_gyp_present":false,"lock_hasInstallScript":false},{"name":"@rolldown/binding-win32-x64-msvc","version":"1.2.9","archive_bytes":7993949,"archive_sha256":"eab52dc8846b438bb55727b65883b31d1716f686d3740f4ce4d18a5690fc1508","integrity":"sha512-Ip2mXoU0hM0boq3Rf+ekuT653OROSo6aSYcPT1VHE4q52KvyxgFkQgrgb/IEsxOuvQ2fZZbs8khJAyCEPM24/g==","tarball":"https://registry.npmjs.org/@rolldown/binding-win32-x64-msvc/-/binding-win32-x64-msvc-1.2.9.tgz","license":"MIT","repository":{"type":"git","url":"git+https://github.com/rolldown/rolldown.git","directory":"packages/rolldown"},"licenses":[],"hooks":{},"bin":null,"types":null,"binding_gyp_present":false,"lock_hasInstallScript":false},{"name":"@rolldown/pluginutils","version":"1.0.1","archive_bytes":6681,"archive_sha256":"13fcb3423d37f95a8e861c172e4b62fd24f22412be4e942087367242476e3400","integrity":"sha512-2j9bGt5Jh8hj+vPtgzPtl72j0yRxHAyumoo6TNfAjsLB04UtpSvPbPcDcBMxz7n+9CYB0c1GxQFxYRg2jimqGw==","tarball":"https://registry.npmjs.org/@rolldown/pluginutils/-/pluginutils-1.0.1.tgz","license":"MIT","repository":{"type":"git","url":"git+https://github.com/rolldown/plugins.git","directory":"packages/pluginutils"},"licenses":[{"member":"package/LICENSE","bytes":1106,"sha256":"e1919b3b98b8bf6c1b99fcc60a0ed46027c97ac947432e1278446c9606f50161"}],"hooks":{},"bin":null,"types":null,"binding_gyp_present":false,"lock_hasInstallScript":false},{"name":"source-map-js","version":"1.2.1","archive_bytes":35340,"archive_sha256":"f126a6f9fca487a43219d8cb8c3a955279187a966119d548eb5cd47e999d4853","integrity":"sha512-UXWMKhLOwVKb728IUtQPXxfYU+usdybtUrK/8uGE8CQMvrhOpwvzDBwj0QhSL7MQc7vIsISBG8VQ8+IDQxpfQA==","tarball":"https://registry.npmjs.org/source-map-js/-/source-map-js-1.2.1.tgz","license":"BSD-3-Clause","repository":"7rulnik/source-map-js","licenses":[{"member":"package/LICENSE","bytes":1526,"sha256":"6cb0631f71c7749763fd3dd1d5bee52dd1070ec17f2edc1710079ad070bd2fbd"}],"hooks":{},"bin":null,"types":"source-map.d.ts","binding_gyp_present":false,"lock_hasInstallScript":false},{"name":"tinyglobby","version":"0.2.17","archive_bytes":7873,"archive_sha256":"afb4afae9175f8b873ac13e1d21cea0997a0bcb40c3598613a834490058cb562","integrity":"sha512-wXR/dYpcqKmfWpEdZjiKJOwCNFndD0DMnrW/cYjVGttEkBfVgcLFHoNrlj47mjOVic9yyNu65alsgF4NQyTa2g==","tarball":"https://registry.npmjs.org/tinyglobby/-/tinyglobby-0.2.17.tgz","license":"MIT","repository":{"type":"git","url":"git+https://github.com/SuperchupuDev/tinyglobby.git"},"licenses":[{"member":"package/LICENSE","bytes":1076,"sha256":"22c68811e174cbbfb3813d4135918df4f540959c14d872e601d9abe83d3cde8f"}],"hooks":{},"bin":null,"types":"./dist/index.d.cts","binding_gyp_present":false,"lock_hasInstallScript":false},{"name":"typescript","version":"7.0.2","archive_bytes":365612,"archive_sha256":"da2513f4b95176d6dde8b51aab7afe8a927656c9d277369793f77f7e59371c08","integrity":"sha512-8FYau96o3NKOhbjKi/qNvG/W5jhzxkbdm5sj9AbZ/5T5sWqn3hJgLfGx27sRKZWTvyzCP8dLRBTf5tBTSRVUNA==","tarball":"https://registry.npmjs.org/typescript/-/typescript-7.0.2.tgz","license":"Apache-2.0","repository":{"type":"git","url":"https://github.com/microsoft/TypeScript.git"},"licenses":[{"member":"package/LICENSE","bytes":9197,"sha256":"a7d00bfd54525bc694b6e32f64c7ebcf5e6b7ae3657be5cc12767bce74654a47"},{"member":"package/vendor/vscode-jsonrpc/License.txt","bytes":1095,"sha256":"ec9ee83580841e8eb687aca9867f221503809ba6426c7f876ede17d91b9fcfd0"},{"member":"package/NOTICE.txt","bytes":48860,"sha256":"f5c708b59114507b8b27b48181b6883d106bbca0c1634bbee45b5e344237b66b"}],"hooks":{},"bin":{"tsc":"./bin/tsc"},"types":null,"binding_gyp_present":false,"lock_hasInstallScript":false},{"name":"@typescript/typescript-aix-ppc64","version":"7.0.2","archive_bytes":9671145,"archive_sha256":"b6e558bbdc9206b7b99f6f4f4ce4fa4f6157640ab580cc7d563703767d43d8cc","integrity":"sha512-MTKKkWB7p/0E9xi1d1tHtZ5PiLkGEMIq88pK2CubZjOsLtYTLqhgIgi6zepFa+9GHZ6h05NMCkQxGKiPXMxXtQ==","tarball":"https://registry.npmjs.org/@typescript/typescript-aix-ppc64/-/typescript-aix-ppc64-7.0.2.tgz","license":"Apache-2.0","repository":{"type":"git","url":"https://github.com/microsoft/TypeScript.git"},"licenses":[{"member":"package/LICENSE","bytes":9197,"sha256":"a7d00bfd54525bc694b6e32f64c7ebcf5e6b7ae3657be5cc12767bce74654a47"},{"member":"package/NOTICE.txt","bytes":48860,"sha256":"f5c708b59114507b8b27b48181b6883d106bbca0c1634bbee45b5e344237b66b"}],"hooks":{},"bin":null,"types":null,"binding_gyp_present":false,"lock_hasInstallScript":false},{"name":"@typescript/typescript-darwin-arm64","version":"7.0.2","archive_bytes":9270373,"archive_sha256":"902e2fe1cf0799198ef902c6b8c310a450fef629a6baba41d45641ef75c04ebd","integrity":"sha512-gowzar9MwS/aRWp6f3a4KUqzRjAZjOsmGNCM6LcTgXum+dBfgsBVMN+AgvOCCbguXyick6LJhpBszxMebJ8syA==","tarball":"https://registry.npmjs.org/@typescript/typescript-darwin-arm64/-/typescript-darwin-arm64-7.0.2.tgz","license":"Apache-2.0","repository":{"type":"git","url":"https://github.com/microsoft/TypeScript.git"},"licenses":[{"member":"package/LICENSE","bytes":9197,"sha256":"a7d00bfd54525bc694b6e32f64c7ebcf5e6b7ae3657be5cc12767bce74654a47"},{"member":"package/NOTICE.txt","bytes":48860,"sha256":"f5c708b59114507b8b27b48181b6883d106bbca0c1634bbee45b5e344237b66b"}],"hooks":{},"bin":null,"types":null,"binding_gyp_present":false,"lock_hasInstallScript":false},{"name":"@typescript/typescript-darwin-x64","version":"7.0.2","archive_bytes":10057523,"archive_sha256":"eba158cb54050f723d5ff781438f33de5640054440bb4f2bd170cfe9bc2eb551","integrity":"sha512-SZ9xZInqApNlNGc9s0W1VSsktYSOe9cFqNOIqmN1Gs8SmkjKZYFt017G4VwPxASInODuAdbTW7sXiFUf893RgA==","tarball":"https://registry.npmjs.org/@typescript/typescript-darwin-x64/-/typescript-darwin-x64-7.0.2.tgz","license":"Apache-2.0","repository":{"type":"git","url":"https://github.com/microsoft/TypeScript.git"},"licenses":[{"member":"package/LICENSE","bytes":9197,"sha256":"a7d00bfd54525bc694b6e32f64c7ebcf5e6b7ae3657be5cc12767bce74654a47"},{"member":"package/NOTICE.txt","bytes":48860,"sha256":"f5c708b59114507b8b27b48181b6883d106bbca0c1634bbee45b5e344237b66b"}],"hooks":{},"bin":null,"types":null,"binding_gyp_present":false,"lock_hasInstallScript":false},{"name":"@typescript/typescript-freebsd-arm64","version":"7.0.2","archive_bytes":8865805,"archive_sha256":"42d23a91be92d7e761cc808b10c34430f1f5f6cb6dc9c594e832fdf7d65d4c5b","integrity":"sha512-W5NH4y/J0plIIS5b2xvTEkU7JFxyqdMAOgf+Ilhl0vHQXKO5dZoxd+C/jEtq56c4F3wk71RB4BMRQ2XdI+bwYQ==","tarball":"https://registry.npmjs.org/@typescript/typescript-freebsd-arm64/-/typescript-freebsd-arm64-7.0.2.tgz","license":"Apache-2.0","repository":{"type":"git","url":"https://github.com/microsoft/TypeScript.git"},"licenses":[{"member":"package/LICENSE","bytes":9197,"sha256":"a7d00bfd54525bc694b6e32f64c7ebcf5e6b7ae3657be5cc12767bce74654a47"},{"member":"package/NOTICE.txt","bytes":48860,"sha256":"f5c708b59114507b8b27b48181b6883d106bbca0c1634bbee45b5e344237b66b"}],"hooks":{},"bin":null,"types":null,"binding_gyp_present":false,"lock_hasInstallScript":false},{"name":"@typescript/typescript-freebsd-x64","version":"7.0.2","archive_bytes":9636659,"archive_sha256":"d982b0db967346becc4ccbc8cdac69e0335995c419bf129616e18a87832edb8c","integrity":"sha512-UMGDx5sTpzNw3WiPebH7l90IWfJggEd+egHt/q6p7/Cm3zqoV7VxkGXt+3DxPIw8CcmvAB0j3sVVfbhX+M4Tpw==","tarball":"https://registry.npmjs.org/@typescript/typescript-freebsd-x64/-/typescript-freebsd-x64-7.0.2.tgz","license":"Apache-2.0","repository":{"type":"git","url":"https://github.com/microsoft/TypeScript.git"},"licenses":[{"member":"package/LICENSE","bytes":9197,"sha256":"a7d00bfd54525bc694b6e32f64c7ebcf5e6b7ae3657be5cc12767bce74654a47"},{"member":"package/NOTICE.txt","bytes":48860,"sha256":"f5c708b59114507b8b27b48181b6883d106bbca0c1634bbee45b5e344237b66b"}],"hooks":{},"bin":null,"types":null,"binding_gyp_present":false,"lock_hasInstallScript":false},{"name":"@typescript/typescript-linux-arm","version":"7.0.2","archive_bytes":9123633,"archive_sha256":"33a15a7badb207a38957373c410b970319baac8960109232ab64502497caea06","integrity":"sha512-gffT3xPz9sR7j/YJExkyPntrI0P2EP9XbOyWzth2/Gs0RstK+90RBcO0ncXoXy/beYll1SXw846Nf2zdnEz0QQ==","tarball":"https://registry.npmjs.org/@typescript/typescript-linux-arm/-/typescript-linux-arm-7.0.2.tgz","license":"Apache-2.0","repository":{"type":"git","url":"https://github.com/microsoft/TypeScript.git"},"licenses":[{"member":"package/LICENSE","bytes":9197,"sha256":"a7d00bfd54525bc694b6e32f64c7ebcf5e6b7ae3657be5cc12767bce74654a47"},{"member":"package/NOTICE.txt","bytes":48860,"sha256":"f5c708b59114507b8b27b48181b6883d106bbca0c1634bbee45b5e344237b66b"}],"hooks":{},"bin":null,"types":null,"binding_gyp_present":false,"lock_hasInstallScript":false},{"name":"@typescript/typescript-linux-arm64","version":"7.0.2","archive_bytes":8900516,"archive_sha256":"c83d931ac9dd7549cde6e71246aa9d6a9812843023df3e277fe3b5dcf41dd0ea","integrity":"sha512-Qh4eU4/y3yDjnfjjyPYihMj5/ODIlmt+Bzu17OI+fiSRDW57QmU5SiN63exPRNJPKUzcc1INa1NXdrJ+MqHjUQ==","tarball":"https://registry.npmjs.org/@typescript/typescript-linux-arm64/-/typescript-linux-arm64-7.0.2.tgz","license":"Apache-2.0","repository":{"type":"git","url":"https://github.com/microsoft/TypeScript.git"},"licenses":[{"member":"package/LICENSE","bytes":9197,"sha256":"a7d00bfd54525bc694b6e32f64c7ebcf5e6b7ae3657be5cc12767bce74654a47"},{"member":"package/NOTICE.txt","bytes":48860,"sha256":"f5c708b59114507b8b27b48181b6883d106bbca0c1634bbee45b5e344237b66b"}],"hooks":{},"bin":null,"types":null,"binding_gyp_present":false,"lock_hasInstallScript":false},{"name":"@typescript/typescript-linux-loong64","version":"7.0.2","archive_bytes":9258075,"archive_sha256":"4d0a2d19f0563df4d12b1e4197a5aefc9827b2977aa48282e7647926085d3c1f","integrity":"sha512-uEHck9i8hoAzXPiYRib1O7miOnz23SxIeVl6F4LXox+qov1K35jHcEW6VHKvZI+pyvl7fZEP4MCU5LYvIq1GuQ==","tarball":"https://registry.npmjs.org/@typescript/typescript-linux-loong64/-/typescript-linux-loong64-7.0.2.tgz","license":"Apache-2.0","repository":{"type":"git","url":"https://github.com/microsoft/TypeScript.git"},"licenses":[{"member":"package/LICENSE","bytes":9197,"sha256":"a7d00bfd54525bc694b6e32f64c7ebcf5e6b7ae3657be5cc12767bce74654a47"},{"member":"package/NOTICE.txt","bytes":48860,"sha256":"f5c708b59114507b8b27b48181b6883d106bbca0c1634bbee45b5e344237b66b"}],"hooks":{},"bin":null,"types":null,"binding_gyp_present":false,"lock_hasInstallScript":false},{"name":"@typescript/typescript-linux-mips64el","version":"7.0.2","archive_bytes":8613623,"archive_sha256":"6743a786c65e33b5b17d34bd9f2a66446dce95dc028cf21b6e6a975e7f576352","integrity":"sha512-R4KvAMnE43W5Qeqb0Ly56O3mWMWIAgsMyz36DCaycd5nbg/9kzm0liw3JocfRqyJY0KPmzFjbswozXyW0DnIYA==","tarball":"https://registry.npmjs.org/@typescript/typescript-linux-mips64el/-/typescript-linux-mips64el-7.0.2.tgz","license":"Apache-2.0","repository":{"type":"git","url":"https://github.com/microsoft/TypeScript.git"},"licenses":[{"member":"package/LICENSE","bytes":9197,"sha256":"a7d00bfd54525bc694b6e32f64c7ebcf5e6b7ae3657be5cc12767bce74654a47"},{"member":"package/NOTICE.txt","bytes":48860,"sha256":"f5c708b59114507b8b27b48181b6883d106bbca0c1634bbee45b5e344237b66b"}],"hooks":{},"bin":null,"types":null,"binding_gyp_present":false,"lock_hasInstallScript":false},{"name":"@typescript/typescript-linux-ppc64","version":"7.0.2","archive_bytes":8984686,"archive_sha256":"8c30ad95ff40cff8bba2ab294abde3bfee6fa12b2b649f80ec90ef3188842db1","integrity":"sha512-DORx5b3sd/4S7eayxm4FQv+A7CrkUIGRaHiwI8oiHTAI1fAPWhF4J0vAlkC8biAlHSVVwxMQ3tjZ2/DVbnQiiA==","tarball":"https://registry.npmjs.org/@typescript/typescript-linux-ppc64/-/typescript-linux-ppc64-7.0.2.tgz","license":"Apache-2.0","repository":{"type":"git","url":"https://github.com/microsoft/TypeScript.git"},"licenses":[{"member":"package/LICENSE","bytes":9197,"sha256":"a7d00bfd54525bc694b6e32f64c7ebcf5e6b7ae3657be5cc12767bce74654a47"},{"member":"package/NOTICE.txt","bytes":48860,"sha256":"f5c708b59114507b8b27b48181b6883d106bbca0c1634bbee45b5e344237b66b"}],"hooks":{},"bin":null,"types":null,"binding_gyp_present":false,"lock_hasInstallScript":false},{"name":"@typescript/typescript-linux-riscv64","version":"7.0.2","archive_bytes":9119178,"archive_sha256":"b5afba89cef6c1c9e6142893018fdbd04183abe1e281a710fe31bb9578d2dc72","integrity":"sha512-wf0jqEDOjrPRnKwYRyyJDRo11KMbvMFrU+q4zqKyChODBzvlkbhNQfKvLxQCcwTpdDaXSHZTVuh0JoCrKCUMHQ==","tarball":"https://registry.npmjs.org/@typescript/typescript-linux-riscv64/-/typescript-linux-riscv64-7.0.2.tgz","license":"Apache-2.0","repository":{"type":"git","url":"https://github.com/microsoft/TypeScript.git"},"licenses":[{"member":"package/LICENSE","bytes":9197,"sha256":"a7d00bfd54525bc694b6e32f64c7ebcf5e6b7ae3657be5cc12767bce74654a47"},{"member":"package/NOTICE.txt","bytes":48860,"sha256":"f5c708b59114507b8b27b48181b6883d106bbca0c1634bbee45b5e344237b66b"}],"hooks":{},"bin":null,"types":null,"binding_gyp_present":false,"lock_hasInstallScript":false},{"name":"@typescript/typescript-linux-s390x","version":"7.0.2","archive_bytes":9418111,"archive_sha256":"badc50ce68cd84c462fcbddfe0c8a7acf9b16a334397cc73e889f6e783f1903d","integrity":"sha512-IkwJc3L7yhytWd/ewjyxNDfOmswCm9GWMJT/ue/dU4aZNbwZeYAetq42VyLmsmSjvoX7z74X6ZaYCtzAr0EuGw==","tarball":"https://registry.npmjs.org/@typescript/typescript-linux-s390x/-/typescript-linux-s390x-7.0.2.tgz","license":"Apache-2.0","repository":{"type":"git","url":"https://github.com/microsoft/TypeScript.git"},"licenses":[{"member":"package/LICENSE","bytes":9197,"sha256":"a7d00bfd54525bc694b6e32f64c7ebcf5e6b7ae3657be5cc12767bce74654a47"},{"member":"package/NOTICE.txt","bytes":48860,"sha256":"f5c708b59114507b8b27b48181b6883d106bbca0c1634bbee45b5e344237b66b"}],"hooks":{},"bin":null,"types":null,"binding_gyp_present":false,"lock_hasInstallScript":false},{"name":"@typescript/typescript-linux-x64","version":"7.0.2","archive_bytes":9669334,"archive_sha256":"7ecad6f67377e831856367ab062ef394f21506a611405bf8ac0ff039348637d3","integrity":"sha512-EYdf2cNg7rgCWJnxCdJ+F3V39O8ihb37eHAu1LK8oAFizgTQbPOK7zHHXbPt8rX24COqODXeI3sIf0fCXG7H/A==","tarball":"https://registry.npmjs.org/@typescript/typescript-linux-x64/-/typescript-linux-x64-7.0.2.tgz","license":"Apache-2.0","repository":{"type":"git","url":"https://github.com/microsoft/TypeScript.git"},"licenses":[{"member":"package/LICENSE","bytes":9197,"sha256":"a7d00bfd54525bc694b6e32f64c7ebcf5e6b7ae3657be5cc12767bce74654a47"},{"member":"package/NOTICE.txt","bytes":48860,"sha256":"f5c708b59114507b8b27b48181b6883d106bbca0c1634bbee45b5e344237b66b"}],"hooks":{},"bin":null,"types":null,"binding_gyp_present":false,"lock_hasInstallScript":false},{"name":"@typescript/typescript-netbsd-arm64","version":"7.0.2","archive_bytes":8847820,"archive_sha256":"afc662ba78fe126f96209b39d6c64c08088ff12b6df363c4bae04a6b79a26000","integrity":"sha512-+polYF4MF04aPpO5FTkHran9yUQDSXqy5GiSDKpsll5jy3l3+g9QLhpf39T+ePtefhXLOGrLl0QIjkQP6VnelA==","tarball":"https://registry.npmjs.org/@typescript/typescript-netbsd-arm64/-/typescript-netbsd-arm64-7.0.2.tgz","license":"Apache-2.0","repository":{"type":"git","url":"https://github.com/microsoft/TypeScript.git"},"licenses":[{"member":"package/LICENSE","bytes":9197,"sha256":"a7d00bfd54525bc694b6e32f64c7ebcf5e6b7ae3657be5cc12767bce74654a47"},{"member":"package/NOTICE.txt","bytes":48860,"sha256":"f5c708b59114507b8b27b48181b6883d106bbca0c1634bbee45b5e344237b66b"}],"hooks":{},"bin":null,"types":null,"binding_gyp_present":false,"lock_hasInstallScript":false},{"name":"@typescript/typescript-netbsd-x64","version":"7.0.2","archive_bytes":9615512,"archive_sha256":"9eb8b25b298b61912cb821e598d883742fa24778267fa88dc94b86acfe3edfe7","integrity":"sha512-8YIT0EHM/3dq10ZOVF/A7pc/YSMtbcecct4rWtexrnSCHOPcpC2KTLXfTCR6vDpnSiY12heNb1GiN/wu+T/FyA==","tarball":"https://registry.npmjs.org/@typescript/typescript-netbsd-x64/-/typescript-netbsd-x64-7.0.2.tgz","license":"Apache-2.0","repository":{"type":"git","url":"https://github.com/microsoft/TypeScript.git"},"licenses":[{"member":"package/LICENSE","bytes":9197,"sha256":"a7d00bfd54525bc694b6e32f64c7ebcf5e6b7ae3657be5cc12767bce74654a47"},{"member":"package/NOTICE.txt","bytes":48860,"sha256":"f5c708b59114507b8b27b48181b6883d106bbca0c1634bbee45b5e344237b66b"}],"hooks":{},"bin":null,"types":null,"binding_gyp_present":false,"lock_hasInstallScript":false},{"name":"@typescript/typescript-openbsd-arm64","version":"7.0.2","archive_bytes":8857975,"archive_sha256":"c8729f2a2ea9a0f0efb0c36ea7b638ebdaad0eaf31943406a488ab3083e13b5a","integrity":"sha512-APT8+ClYnuYm1u9+kgGXoMj2VzWzcymwh2gNSQVySHfkRDGOTVkoWLjCmOQSaO+PoqQ57B0flRp9SA+7GnnkzQ==","tarball":"https://registry.npmjs.org/@typescript/typescript-openbsd-arm64/-/typescript-openbsd-arm64-7.0.2.tgz","license":"Apache-2.0","repository":{"type":"git","url":"https://github.com/microsoft/TypeScript.git"},"licenses":[{"member":"package/LICENSE","bytes":9197,"sha256":"a7d00bfd54525bc694b6e32f64c7ebcf5e6b7ae3657be5cc12767bce74654a47"},{"member":"package/NOTICE.txt","bytes":48860,"sha256":"f5c708b59114507b8b27b48181b6883d106bbca0c1634bbee45b5e344237b66b"}],"hooks":{},"bin":null,"types":null,"binding_gyp_present":false,"lock_hasInstallScript":false},{"name":"@typescript/typescript-openbsd-x64","version":"7.0.2","archive_bytes":9624925,"archive_sha256":"90aeadb743517361f902c6e7ef1e57113175aaf483fb5f2abc1701c8246c66a4","integrity":"sha512-yX7s+Q0Dln0Dt9tEzZsAjXXR/+ytBM7AlglaqyeMPxQszJ1JhlJdZ6jLA+IzldHtflX81em7lDao1xXu+aRRkg==","tarball":"https://registry.npmjs.org/@typescript/typescript-openbsd-x64/-/typescript-openbsd-x64-7.0.2.tgz","license":"Apache-2.0","repository":{"type":"git","url":"https://github.com/microsoft/TypeScript.git"},"licenses":[{"member":"package/LICENSE","bytes":9197,"sha256":"a7d00bfd54525bc694b6e32f64c7ebcf5e6b7ae3657be5cc12767bce74654a47"},{"member":"package/NOTICE.txt","bytes":48860,"sha256":"f5c708b59114507b8b27b48181b6883d106bbca0c1634bbee45b5e344237b66b"}],"hooks":{},"bin":null,"types":null,"binding_gyp_present":false,"lock_hasInstallScript":false},{"name":"@typescript/typescript-sunos-x64","version":"7.0.2","archive_bytes":9600388,"archive_sha256":"a625970be8f04944de633929eb0777c2c60c6c242590b79fc37750cf4a577e85","integrity":"sha512-dLJDGaLZ1D4HPQn62u1n8mBDkJREwMsAkCdkwd4Ieqw+x3TUyTsqY0YiBCtE6H6OzzgGk3iuZ3vFWRS+E8/d1g==","tarball":"https://registry.npmjs.org/@typescript/typescript-sunos-x64/-/typescript-sunos-x64-7.0.2.tgz","license":"Apache-2.0","repository":{"type":"git","url":"https://github.com/microsoft/TypeScript.git"},"licenses":[{"member":"package/LICENSE","bytes":9197,"sha256":"a7d00bfd54525bc694b6e32f64c7ebcf5e6b7ae3657be5cc12767bce74654a47"},{"member":"package/NOTICE.txt","bytes":48860,"sha256":"f5c708b59114507b8b27b48181b6883d106bbca0c1634bbee45b5e344237b66b"}],"hooks":{},"bin":null,"types":null,"binding_gyp_present":false,"lock_hasInstallScript":false},{"name":"@typescript/typescript-win32-arm64","version":"7.0.2","archive_bytes":8900840,"archive_sha256":"0a73534e6ee50cdbb2a29ac48657ca0ad13cf0f424cf63808e4df7baeb87b8be","integrity":"sha512-Gyl1Vy6OsWesLzmq+EP0Fb7b4Nid5232AvcA2SFcdYreldpNtYFFofPjnt62y9hQy7VTaZp65ICJjuAQRaVcIQ==","tarball":"https://registry.npmjs.org/@typescript/typescript-win32-arm64/-/typescript-win32-arm64-7.0.2.tgz","license":"Apache-2.0","repository":{"type":"git","url":"https://github.com/microsoft/TypeScript.git"},"licenses":[{"member":"package/LICENSE","bytes":9197,"sha256":"a7d00bfd54525bc694b6e32f64c7ebcf5e6b7ae3657be5cc12767bce74654a47"},{"member":"package/NOTICE.txt","bytes":48860,"sha256":"f5c708b59114507b8b27b48181b6883d106bbca0c1634bbee45b5e344237b66b"}],"hooks":{},"bin":null,"types":null,"binding_gyp_present":false,"lock_hasInstallScript":false},{"name":"@typescript/typescript-win32-x64","version":"7.0.2","archive_bytes":9776626,"archive_sha256":"61fc4e141d2bc687db580e71bbfa63b9c209f0310645d82ca1b457eb3a24fd19","integrity":"sha512-0BQ3HkAHHlKLSp1qRvf3SUhGpGsDuhB/jgFw75guyqbxJqEaS0Cw/VFO8i2nHglJUzQCRtMMR/IBAKE3ETMC4g==","tarball":"https://registry.npmjs.org/@typescript/typescript-win32-x64/-/typescript-win32-x64-7.0.2.tgz","license":"Apache-2.0","repository":{"type":"git","url":"https://github.com/microsoft/TypeScript.git"},"licenses":[{"member":"package/LICENSE","bytes":9197,"sha256":"a7d00bfd54525bc694b6e32f64c7ebcf5e6b7ae3657be5cc12767bce74654a47"},{"member":"package/NOTICE.txt","bytes":48860,"sha256":"f5c708b59114507b8b27b48181b6883d106bbca0c1634bbee45b5e344237b66b"}],"hooks":{},"bin":null,"types":null,"binding_gyp_present":false,"lock_hasInstallScript":false},{"name":"vite","version":"8.3.0","archive_bytes":582410,"archive_sha256":"8341c0e40cf1700c68998ce5e7b1c715b9f89d700abf6c41f5d8af067a270a72","integrity":"sha512-lhZBVvEHefgE+HQZC9O7EBJgCU/nVzFNl7vkS4RE0APtWLP02/8QVIkQtzBxPquh7lq5/78NHipTj7ODQ6XuyQ==","tarball":"https://registry.npmjs.org/vite/-/vite-8.3.0.tgz","license":"MIT","repository":{"type":"git","url":"git+https://github.com/vitejs/vite.git","directory":"packages/vite"},"licenses":[{"member":"package/LICENSE.md","bytes":112425,"sha256":"387dd7baa307083401a27c58c362c30832f5ba1dba84f10cc22c33401523f45c"}],"hooks":{},"bin":{"vite":"bin/vite.js"},"types":null,"binding_gyp_present":false,"lock_hasInstallScript":false}]
```

### Actual executable checks

```json
{
  "checks": [
    {
      "argv": [
        "node",
        "--version"
      ],
      "exit_code": 0,
      "stdout": "v25.9.0\n",
      "stderr": ""
    },
    {
      "argv": [
        "npm",
        "--version"
      ],
      "exit_code": 0,
      "stdout": "11.12.1\n",
      "stderr": ""
    },
    {
      "argv": [
        "node",
        "node_modules/typescript/bin/tsc",
        "--version"
      ],
      "exit_code": 0,
      "stdout": "Version 7.0.2\n",
      "stderr": ""
    },
    {
      "argv": [
        "node",
        "node_modules/vite/bin/vite.js",
        "--version"
      ],
      "exit_code": 0,
      "stdout": "vite/8.3.0 darwin-arm64 node-v25.9.0\n",
      "stderr": ""
    },
    {
      "argv": [
        "node",
        "node_modules/rolldown/bin/cli.mjs",
        "--version"
      ],
      "exit_code": 0,
      "stdout": "rolldown v1.2.9\n",
      "stderr": ""
    },
    {
      "argv": [
        "node",
        "node_modules/typescript/bin/tsc",
        "--project",
        "tsconfig.contract.json"
      ],
      "exit_code": 0,
      "stdout": "",
      "stderr": ""
    },
    {
      "argv": [
        "node",
        "runtime-contract-smoke.mjs"
      ],
      "exit_code": 0,
      "stdout": "{\"cytoscape\":\"3.34.3\",\"preset\":true,\"parallel_edges\":2,\"self_loop\":true,\"disposed\":true,\"lightningcss_native_transform\":\".item{color:red}\",\"browser_or_csp_test\":false}\n",
      "stderr": ""
    },
    {
      "argv": [
        "node",
        "node_modules/typescript/bin/tsc",
        "--noEmit",
        "--strict",
        "--ignoreConfig",
        "bad-types-smoke.ts"
      ],
      "exit_code": 1,
      "stdout": "bad-types-smoke.ts(1,7): error TS2322: Type 'string' is not assignable to type 'number'.\n",
      "stderr": ""
    },
    {
      "argv": [
        "node",
        "node_modules/rolldown/bin/cli.mjs",
        "rolldown-input-smoke.js",
        "--file",
        "rolldown-output-smoke.js"
      ],
      "exit_code": 0,
      "stdout": "<DIR>/rolldown-output-smoke.js  chunk \u2502 size: 0.09 kB\n\n\u2714 rolldown v1.2.9 Finished in 6.92 ms\n",
      "stderr": ""
    }
  ],
  "installed_packages": [
    {
      "name": "@oxc-project/types",
      "version": "0.150.0",
      "archive_files_equal": 4
    },
    {
      "name": "@rolldown/binding-darwin-arm64",
      "version": "1.2.9",
      "archive_files_equal": 3
    },
    {
      "name": "@rolldown/pluginutils",
      "version": "1.0.1",
      "archive_files_equal": 8
    },
    {
      "name": "@typescript/typescript-darwin-arm64",
      "version": "7.0.2",
      "archive_files_equal": 113
    },
    {
      "name": "cytoscape",
      "version": "3.34.3",
      "archive_files_equal": 205
    },
    {
      "name": "detect-libc",
      "version": "2.1.2",
      "archive_files_equal": 8
    },
    {
      "name": "fdir",
      "version": "6.5.0",
      "archive_files_equal": 7
    },
    {
      "name": "fsevents",
      "version": "2.3.3",
      "archive_files_equal": 6
    },
    {
      "name": "lightningcss",
      "version": "1.33.0",
      "archive_files_equal": 14
    },
    {
      "name": "lightningcss-darwin-arm64",
      "version": "1.33.0",
      "archive_files_equal": 4
    },
    {
      "name": "nanoid",
      "version": "3.3.19",
      "archive_files_equal": 25
    },
    {
      "name": "picocolors",
      "version": "1.1.1",
      "archive_files_equal": 7
    },
    {
      "name": "picomatch",
      "version": "4.0.7",
      "archive_files_equal": 10
    },
    {
      "name": "postcss",
      "version": "8.5.28",
      "archive_files_equal": 55
    },
    {
      "name": "rolldown",
      "version": "1.2.9",
      "archive_files_equal": 54
    },
    {
      "name": "source-map-js",
      "version": "1.2.1",
      "archive_files_equal": 18
    },
    {
      "name": "tinyglobby",
      "version": "0.2.17",
      "archive_files_equal": 7
    },
    {
      "name": "typescript",
      "version": "7.0.2",
      "archive_files_equal": 416
    },
    {
      "name": "vite",
      "version": "8.3.0",
      "archive_files_equal": 37
    }
  ],
  "installed_bins": [
    {
      "bin": "tsc",
      "target": "node_modules/typescript/bin/tsc",
      "sha256": "2219f428a7e55aaf1f7ad85b9b0f0cf5078aeb76ccc9a7c6036c92d48f492ffd"
    },
    {
      "bin": "vite",
      "target": "node_modules/vite/bin/vite.js",
      "sha256": "de5833362e640673962f16e255bf8738d4380a68601b9af26217eee4e1bac36d"
    },
    {
      "bin": "rolldown",
      "target": "node_modules/rolldown/bin/cli.mjs",
      "sha256": "98d6df62aa3c84284db17944a2a8017f911640e9c4d3de907a9f93b467ee47c8"
    }
  ],
  "installed_file_count": 1001,
  "platform": "darwin-arm64",
  "production_build": false,
  "browser_csp": false,
  "other_platform_binaries_executed": false
}
```

### Current live-schema and error-envelope checks

Current checks read the delivered schema/package/lock directly from their source paths. They do not validate an immutable artifact copy in place of the live files. Draft202012Validator.check_schema passes; all123 targeted cases and412 local references pass, with the explicit integer-token/UTF-8 semantic checks. The full31-by-six error matrix independently confirms the manager's659-byte finding, attained by configuration_needed with operation relationships. Earlier neighborhood-only658-byte observations are narrower and are not relabeled as maximum coverage.

```json
{
  "level": "Draft 2020-12 meta-schema validation and targeted cases with required integer/UTF-8 semantic checks",
  "full_draft202012_validator": "jsonschema 4.26.0; Draft202012Validator.check_schema passed; targeted cases use strict integer-token and UTF-8 semantic extensions",
  "schema_sha256": "8e6d0ceb47c98e77d518f4d7c935986ab6982d1a1c15e12377a726e90fbbb7a4",
  "definitions": 124,
  "local_references_checked": 412,
  "unclosed_protocol_objects": [],
  "targeted_cases": 123,
  "max_error_bytes": 659,
  "lockfile_version": 3,
  "locked_packages": 62,
  "lock_sha256": "c56e429ba8b70fe0e56ab5f879853f5267083eb7facbc0a6da36322b94afdbf9",
  "direct_integrities_match_frozen_evidence": true,
  "installed_bins": "Observed independently in toolchain-results.json; tsc7.0.2, Vite8.3.0, Rolldown1.2.9 on darwin-arm64",
  "runtime_behavior": "not implemented or tested",
  "prior_neighborhood_only_max_bytes": 658,
  "exhaustive_error_operation_combinations": 186,
  "maximum_error_cases": [
    {
      "code": "configuration_needed",
      "operation": "relationships",
      "bytes": 659
    }
  ],
  "schema_source": "live delivered ONTOLOGY-depo/schema/explorer-v1.json"
}
```

Commands: `.venv-memory-pilot/bin/python -B /tmp/explorer-contracts-implement-g3/check_schema_final.py` and `python3 /tmp/explorer-contracts-implement-g3/toolchain_checks.py`. This reuses a preexisting test-only JSON Schema library; no memory system or runtime dependency was changed.

### Current delivery and future freshness

The seven-file scope remains exact. Source contracts, schema and package declarations are frozen after TASK-002 acceptance; future delivery evidence belongs in later release manifests. If a delivered source file changes, its recorded live result hash must be revalidated or replaced through the owning Task process. Copying an old artifact does not make a changed live implementation current. This rule applies to the notices, contract, package and schema as well as code. The map self digest remains externally recorded by the Task/final manifest; no circular self hash is embedded.

The268-row map retains exact source/Template/root/fixture/history/evidence ownership and immutable plan path translations. Only current dependency evidence and actual hashes are refreshed. No existing product/root/Template adoption, canonical content, Task ledger or Git publication is performed by this worker. All later production/security/accessibility/user/rollback gates remain required. There is no remaining package-download or installed-toolchain blocker within TASK-002; manager acceptance is separate from this worker's observed checks.

Scratch evidence identities (supporting, never substitutes for current source files):

- `inspect_all_artifacts.py`: SHA256 `e414b29a901501f73e1b06d864d67dbe55b7f26cf9d61f6e1f87c42731c11af5`.
- `all-artifacts.json`: SHA256 `14d08e95ecb1310f838fb09edb3b01e5de757d3017599ddfe0201dbd1688b4c3`.
- `all-license-texts.json`: SHA256 `8016dd9e584cc53725fa89a2725c6d7dc0c02739620d4f79078a6ab0d7c9c5b1`.
- `toolchain_checks.py`: SHA256 `40dfdbc7f3c2c296d1703e9b1721c9ef7e5a70341f92a59f3b3e78dfac91bea4`.
- `toolchain-results.json`: SHA256 `8257bf538e4ddafea0ce8be7921eb446509cc70f93d74bb686234b9e552aba58`.
- `check_schema_final.py`: SHA256 `3cbd386390d4e9aae40bcec20339c378b29bb2f5b2415c18f9d5228f8c1eddc1`.
- `full-checks-final.json`: SHA256 `de32c92b537238d481ebe02c116fe00cb39f7c80518fd4041ddb74f90eb6040d`.
