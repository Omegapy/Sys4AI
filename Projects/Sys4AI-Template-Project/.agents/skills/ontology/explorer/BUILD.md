# Build the local Explorer package

The installed reader serves a reviewed static package. Launch never runs npm,
installs dependencies, rebuilds assets, or activates an advanced profile. A missing
or invalid package reports `package_incomplete`; maintenance is explicit.

Use Node **25.9.0**, npm **11.12.1**, the exact checked-in lock, and Python **3.12**.
The lock pins TypeScript **7.0.2**, Vite **8.3.0**, and Cytoscape **3.34.3**. The
actual selected dependency archives, licenses, and hooks must be reviewed before
installation. In an authorized build workspace, use `npm ci --ignore-scripts
--no-audit --no-fund`; no runtime startup provisions these tools. There is no
`npx` fallback or dependency update in the publisher.

From this directory, set `EXPLORER_PYTHON` to the selected Python interpreter and,
when the standard source/installed layout is unavailable, set `EXPLORER_SCHEMA`
to the exact selected `explorer-v1.json`. Run:

```sh
npm run build && npm run package:runtime
```

`npm run build` first runs strict TypeScript checking and then the actual Vite
production build. Vite targets Chrome/Edge 111, Firefox 114, and Safari 16.4, uses
relative local paths, disables dotenv loading, public-file copying and source
maps, and emits to excluded `dist/`. These are compilation targets; report actual
browser versions separately. Application code must load Cytoscape through a lazy
`import('cytoscape')` renderer boundary. Production tests must verify that boundary
and actual CSP behavior. Build configuration alone is not browser evidence.

Frontend code reads the injected literals
`import.meta.env.EXPLORER_BUILD_ID` and
`import.meta.env.EXPLORER_SCHEMA_SHA256`. Never generate a source identity stub.
No timestamp, absolute directory, Git status, or secret enters build identity.

## Exact build identity

`dist/.explorer-build.json` is the exact dirty-source input record for this build;
it is build metadata and is never published or served. Preserve that record with
release evidence. The receipt also binds every generated output path, size and
hash so stale or tampered build output is rejected. Its `inputs.record` is exactly `{domain:"sys4ai-explorer-sources-v1",
files,toolchain}`. `files` contains sorted logical path, byte length, and SHA256
triples for `index.html`, package/lock/notices, this BUILD document, Vite and
TypeScript configuration, the publisher, every authored file under `src/`, plus
`$schema/explorer-v1.json` and `$tooling/ontology_explorer_assets.py`.
Normalization means deterministic logical paths and order; authored bytes are
hashed exactly, including line endings. Accepted source extensions are `.ts`,
`.css`, `.html`, and `.json`. Symlinks/hardlinks, hidden sources, generated
identity stubs, unrecognized source extensions, and oversized inputs are not
accepted. Keep generated output outside `src/`.

`source_digest` hashes that record using the existing core `canonical_bytes`
representation: sorted object keys, UTF-8 with unescaped Unicode, two-space indent,
no non-finite numbers, and one final newline. `build_id` hashes exactly
`{domain:"sys4ai-explorer-build-v1",source_digest,lock_sha256,notices_sha256,
node:"25.9.0",npm,api_version:1,schema_sha256}` with the same representation.
Asset hashes do not feed back into the injected identity. Before and after build,
and again before publishing, exact input hashes must agree.

## Publication and runtime validation

The plain-JS publisher creates a private complete stage, constructs the closed
manifest, and invokes one fixed embedded Python standard-library body with
`python -I -B -c`, no shell and bounded JSON data. This build-only body imports
only the selected pure asset validator. It performs descriptor-relative,
no-follow writes and keeps publication code out of the runtime module. It stages
and validates all bytes, checks the prior manifest and every owned file, replaces
only prior manifest-owned files or absent destinations, removes only unchanged
obsolete inventory members, then atomically replaces the manifest last.
Unmanifested files are preserved; conflicting unowned destinations block the
operation. Publication requires one writer. An interruption can leave an
incomplete package which fails validation; it cannot authenticate a partial
rebuild. Rerun explicit maintenance after inspecting the failure. No automatic
repair or broad directory cleanup occurs.

The non-HTTP manifest names only one HTML entry and local JS/CSS. It excludes
itself, lock/package metadata, notices sources, TypeScript, maps, node_modules,
tests, fixtures, and repository trees. The runtime validator applies 64-file,
8-MiB/file, 16-MiB/total, and 128-KiB/manifest limits before bounded reads. It checks
closed keys, JSON token types, duplicate paths/keys, MIME, hashes, local reachable
import closure, regular single-link files and every no-follow parent. Its import
lexer accepts the bundled ESM subset and rejects computed/escaped imports rather
than inferring a path. HTML has no inline script, style or event attributes.

Service integration uses `load_assets(root, schema_sha256=..., lock_path=...,
notices_path=...)` and retains the returned immutable `AssetPackage`.
`read_asset(package, request_target)` returns bytes and the exact MIME for GET or
HEAD; HEAD omits the returned body. Only `/`, `/index.html`, and exact manifested
paths resolve. A manifest may name a nested HTML entry; imports resolve relative
to that actual entry directory. The service must redirect document aliases to
the canonical entry path when nesting would change browser-relative resolution.
Production callers must supply all three real metadata bindings (schema digest,
lock and notices); optional arguments exist for isolated validator fixtures.
The service must still revalidate its complete pinned executing
closure and enforce sticky `package_changed`, Host/Origin checks, no-store,
nosniff, referrer policy and CSP. This module does not implement HTTP or sessions.

The neutral `ontology-explorer.yaml` uses `project_id:null`. It permits static
starter inspection and cannot activate a reader until separately specialized.
Template discovery, root adoption, full frontend production/CSP checks and live
browser acceptance each require their own current evidence.
