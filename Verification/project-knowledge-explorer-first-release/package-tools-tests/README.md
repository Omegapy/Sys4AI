# Package tooling evidence

`verification-result.json` binds the current seven source/test/starter files and
records **27 passing tests**, with no skips. The final run exercised actual
Node 25.9.0, npm 11.12.1, TypeScript 7.0.2, Vite 8.3.0 and Cytoscape 3.34.3 using
copies of the earlier verified dependency installation. No download, lock
update or package hook ran here.

The disposable minimal production build contains one HTML entry, one CSS file,
one main JS file, and a separate lazy Cytoscape chunk. The publisher validates
and publishes that package. A repeated build produced byte-identical input/output
receipts and the same runtime manifest on this host. This is not a claim of
cross-platform reproducibility. The deliberate TypeScript assignment failure
returned exit 1 with TS2322; its source was restored before the repeated build.

The test suite covers closed manifests, JSON token types, duplicate keys/paths,
metadata binding, safe nested entry resolution, local import closure, computed
and escaped imports, inert versus executable template expressions, remote HTML
and CSS resources, repeated-import memory bounds, exact serving paths, missing
or changed bytes, same-mtime changes, symlinks, hardlinks, FIFO and size ceilings.
Publisher tests exercise actual rebuild/obsolete-file removal, unowned-file
preservation/collision, input/output staleness, unsafe destination links, a helper
changed before execution, staged-write failure cleanup and injected failure of
the final manifest commit. The last case leaves no usable manifest and the
validator refuses the incomplete output.

`minimal-build-receipt.json` contains exact normalized source input hashes and
actual generated output hashes. `minimal-runtime-manifest.json` is the exact
non-HTTP package manifest. The small fixture source is retained beside these
receipts. The 434-kB Cytoscape chunk remains in the disposable fixture and is
bound by its manifest hash; it is not copied into a Task artifact above its
250,000-byte limit. Neither fixture nor chunk is the final Explorer application.

To repeat with the same reviewed installed dependencies:

```sh
.venv/bin/python -B Verification/project-knowledge-explorer-first-release/package-tools-tests/prepare_fixture.py --dependencies /private/tmp/explorer-contracts-implement-g3/node_modules --target /private/tmp/explorer-tools-recheck
.venv/bin/python -B Verification/project-knowledge-explorer-first-release/package-tools-tests/verify_fixture.py --fixture /private/tmp/explorer-tools-recheck/ontology/explorer
```

The target must be absent and beneath real `/private/tmp`. These commands do not
install dependencies, launch a service, or open a browser. Reverification updates
the evidence files; the owning manager must rebind resulting changed hashes.

## Integration obligations

Production `load_assets` callers must bind the actual schema digest, package lock
and notices. The service must validate the whole pinned executing package before
and after static responses and implement sticky `package_changed`; per-member
checks do not replace that rule. For nested manifest entries, aliases must
redirect to the canonical entry path when relative browser resolution would
otherwise change. Runtime metadata, source trees and the manifest are not HTTP
resources. Service headers, Host/Origin controls, CSP and session behavior remain
separate implementation and browser checks.

The initializer, Template distribution, root adoption, complete frontend build,
actual offline browser/CSP behavior, accessibility, owner walkthrough and all
remaining TASK-010 integration requirements are unperformed here. No active
project configuration or canonical knowledge was changed. This evidence freezes
only this tooling slice; concurrent helper additions are not retroactively
covered by these file hashes.

## Preserved earlier failures

Earlier logs are historical and do not replace `*-delivery-v1.log` and the current
result. `failure-history.json` explains the observed corrections, including a
fixture invocation from the wrong directory, backtick import handling in Vite
output, a test injection variable collision and the verification driver's wrong
assumption about the TypeScript error exit code.
