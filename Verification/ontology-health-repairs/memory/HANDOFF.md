# Frozen source and host actions

The source memory suite passed 89 tests with no skips, failures or errors:

`PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest discover -s SKILLS-depo/memory/tests -q`

Raw output: `source-memory-tests.txt`. The 12 new scoped regressions cover health
selection/JSON/text/exit, retained and legacy evidence, exact historical companion
binding, missing/tampered/unsafe proof, historical-only supersession, source and
producer freshness, prior-build absence, actual byte/certificate faults, pending
publication maintenance, and committed reindex plus failed operational probe.
These are disposable fixture controls. Mocked worker responses in failure tests
are transaction/failure evidence only; no actual semantic model acceptance was run.

Source and package freeze hashes are in `source-result.json`. The initializer's
pure inspector pins are:

- `memory_core.py`: `48592604ac950e32e4c80aab24edd2e90d26d09df1b6af912dcad24bbc490a54`
- `memory_paths.py`: `5e7c01db65adf4296d97b166945a80a18875055a46811eeb30c701ab7040f7de` (unchanged)

The core config validator retains only its existing memory_paths import needs;
new health/evidence/backend imports remain lazy.

The original verified observation's exact five artifact versions and original
receipt are now retained. The old initializer bytes came from Git commit
`2ea00dd2f201a5e4d5eebe61353d4ec62ca6d580`; original capture bytes came from the
matching Git HEAD version. All six original test log digests still match. This
supports historical integrity and does not renew current applicability.

Host review/apply sequence:

1. Reopen `retained-artifact-manifest.json`, verify every raw-byte digest, confirm
   the original record still matches its expected version, and confirm companion
   destination is absent. The companion destination is under the current root's
   already granted `Verification/project-memory` evidence scope. Do not widen
   memory.yaml or publish the companion under ungranted control_records paths.
2. Publish the exact reviewed `historical-proof-companion.json` only to
   `Verification/project-memory/evidence/verification-06bad7195d7fabed2b8d7328a7bbe22c751b9262582ca151403cc436dba479e0.json`.
   This is a historical proof locator and no current execution assertion.
3. Review `historical-supersession-payload.json` and
   `historical-successor-review.md`. The proposed successor is
   `MEM-20260910-0C531031`; original body/claim/source provenance are retained in
   its superseded predecessor. Recalculate the payload digest before applying;
   `source-result.json` records the frozen candidate digest. If approval changes
   any candidate bytes, regenerate the corresponding record and payload hashes.
4. Obtain a current native running-actor observation. Use the installed
   memory publication grant contract with operation `supersede`, the exact payload
   digest, current memory.yaml digest, actual actor/kind, permitted MEMORY scope,
   exact two reviewed record hashes/expected hashes, null Task for this non-Task
   operation, and fresh observed/expiry times (maximum five minutes). The
   independent companion evidence scope is not a canonical-memory grant.
5. Run the installed `memory.py --project-root <real-root> supersede <payload>
   --grant-file <fresh-grant> --actor <actual-director>` after source adoption and
   required guard/binding repair. Reopen both records and the durable canonical
   transaction receipt. Old historical proof should report supported; successor
   context is active and verified_current remains false.
6. Only after final source/canonical/config bytes settle, obtain exact reindex
   payload and granted memory maintenance. Reindex, probe the selected existing
   runtime, refresh ontology links and other affected products under their own
   scopes, then verify final aggregate readiness and original audited workflows.

No installed root, live MEMORY/config/backend, Template, plan, Task, ontology,
initializer, or control-record files were directly edited by this worker. The
existing Template watcher may publish source changes independently. No dependency
installation, model download, live semantic probe, Git publication or nested agent
was performed. Project-level acceptance remains with the host.
