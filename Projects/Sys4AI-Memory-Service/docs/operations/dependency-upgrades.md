# Dependency upgrades

Dependency upgrades require a compatibility smoke suite, migration review, and
a rollback plan. An unlocked resolver result is not approval to keep the new
version.

## Before changing a constraint

Record the proposed package and version, reason, affected contract or security
boundary, upstream release/advisory evidence, license impact, Python 3.12
support, transitive dependency changes, data/schema/storage compatibility, and
the current `uv.lock` fingerprint. For Cognee, also identify adapter mapping,
runtime configuration, model provider, graph/vector store, migration, COGX,
and native exception-shape changes.

Back up canonical sources through normal project controls. Preserve the current
lockfile and any migration inputs needed to reproduce the accepted version. Do
not use a provider database as the sole rollback asset.

## Candidate workflow

1. Change only the intended version constraint on an isolated reviewed branch
   or equivalent disposable working copy.
2. Regenerate `uv.lock` deliberately and inspect every direct and transitive
   change.
3. Sync the candidate environment without exposing credentials, starting a
   listener, or contacting an unapproved model endpoint.
4. Run static, contract, configuration, provider-boundary, security,
   interface, rebuild, exchange, and observability checks.
5. Run a fake/temp provider smoke first. Then, only with separate authority,
   run a real local provider smoke on disposable derived storage.
6. Produce migration dry-runs for stored schema/profile/provider changes.
   Verify that the prior active generation remains usable on failure.
7. Compare exact, lexical, semantic, graph, temporal, startup, sync, resource,
   and package compatibility results against the accepted baseline where they
   apply.
8. Review redaction, outbound-network, telemetry, path, dataset-isolation, and
   native-interface controls again.
9. Record sanitized versions, fingerprints, commands, results, warnings,
   migration decision, and rollback steps. Never record a secret value.
10. Accept the candidate only through the normal project decision and review
    workflow.

Minimum local checks:

```bash
uv run --frozen ruff check src tests tools
uv run --frozen mypy src tools
uv run --frozen pytest
uv run --frozen python tools/validate_release_evidence.py
```

## Review receipt gate

Before accepting a candidate, record the observed results in one JSON review
receipt and bind it to the exact preserved baseline and candidate lockfiles:

```bash
uv run --frozen python tools/validate_dependency_upgrade.py \
  --review <candidate-review.json> \
  --baseline-lock <preserved-baseline-uv.lock> \
  --candidate-lock <candidate-uv.lock>
```

The validator rejects symlinked artifacts, lock digest mismatches, unknown or
missing checks, duplicate results, secret-like content, naive timestamps, and
an accepted decision with any failed prerequisite. A complete review must
cover macOS and Linux lock/smoke results plus these named checks:
`lock_resolution`, `static_analysis`, `contracts`, `configuration`,
`provider`, `security`, `interfaces`, `rebuild`, `exchange`, `observability`,
`integration`, `profiles`, `migration`, and `rollback`. Cognee candidates
cannot declare migration review unnecessary. An accepted candidate also
requires the migration dry run to preserve the prior generation and the
rollback evidence to be verified.

This command validates a review receipt and its exact lock bytes. It does not
run the checks, obtain release evidence, approve a candidate, or replace the
normal human review workflow. A rejected candidate can have a complete valid
review; `candidate_accepted` remains false.

The exact-index reference benchmark is reproducible with:

```bash
uv run --frozen python tools/benchmark_exact_index.py --fragments 100000 --batch-size 1000 --exact-samples 200
```

That benchmark measures SQLite/FTS5 normalization and exact/lexical queries
only. It does not validate a Cognee upgrade, persistent-disk startup, mixed
concurrency, semantic quality, or recovery.

## Rollback

If any compatibility, migration, security, isolation, or benchmark requirement
fails, restore the prior constraints and lockfile, create a clean environment,
restore or rebuild the last accepted derived generation from canonical inputs,
and verify its fingerprints and representative queries. Revoke or remove any
candidate credential reference or model configuration created solely for the
test. Keep failure evidence without copying sensitive content.

No Cognee dependency upgrade has been evaluated by this procedure. The
executable gate itself is covered by focused tests for complete evidence,
missing platform/check coverage, skipped Cognee migration and rollback, exact
lock binding, and secret rejection. The current pin remains
`cognee[fastembed,ollama]==1.5.3`.
