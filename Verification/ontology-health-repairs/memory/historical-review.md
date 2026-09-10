# Historical observation review

The original `MEM-20260909-89C402A6` record and receipt are preserved as exact audit
copies in `original-record.md` and `original-verification.json`. The receipt digest
is `06bad7195d7fabed2b8d7328a7bbe22c751b9262582ca151403cc436dba479e0`.
All six cited test-log digests match the current retained logs. This review did
not rerun the old command or enlarge its recorded test coverage and limitations.

Two live implementation files differ from the recorded observed versions:

- `.agents/skills/memory/scripts/memory_capture.py`: expected
  `ef9d35c3ec0bc72a19292c78aacd986b8f4f0cb5ad0d128c2e64d511a1a5f67d`.
  Exact bytes were recovered from Git HEAD and retained as
  `historical-memory_capture.py`.
- `.agents/skills/init-new-project/scripts/init_new_project.py`: expected
  `8616e439dafedb057f46e685788cdc292b3300ab2c120ee90c2750c71bbe07bf`.
  Exact bytes were recovered from commit
  `2ea00dd2f201a5e4d5eebe61353d4ec62ca6d580` at both installed/source paths,
  then retained as `historical-init_new_project.py`.

The initial direct-version search in `evidence-inventory.json` found no matching
initializer bytes in current files or Git HEAD. The subsequent bounded history
search in `bounded-history-search.json` resolves that provisional proof gap.
The old `memory.yaml`, `memory_core.py` and config schema still matched their
recorded hashes when retained. Every retained original passes exact SHA256 and
the existing text privacy filter. `retained-artifact-manifest.json` is the final
five-artifact inventory; it supersedes the provisional availability conclusion
without rewriting the original diagnostic evidence.

The evidence supports historical observation integrity. It does not support
renewing the claim against today's implementations. The prepared disposition
therefore retains a historical-only companion proof locator, supersedes the old
record with `MEM-20260910-0C531031` using claim `historical_context`, and preserves
the predecessor's original claim, body, sources, IDs and historical transaction
provenance. The companion is permanently historical; it cannot set
`verified_current: true`.

Host action is still required. `historical-supersession-payload.json` and
`historical-proof-companion.json` are review candidates, not executed publication
receipts. Reopen the exact current original record, all retained artifacts and
companion destination before applying the reviewed disposition. Use a current
native actor observation and operation-scoped grant through the installed memory
supersede helper. Source installation, root guard/config bindings, memory reindex,
ontology links and runtime acceptance remain host-owned phases.
