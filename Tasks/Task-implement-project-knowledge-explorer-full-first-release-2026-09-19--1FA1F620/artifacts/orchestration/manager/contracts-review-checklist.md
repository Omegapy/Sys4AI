# Contract review acceptance checklist

Review the assigned solver proposal against the complete CONTRACTS baseline and immutable plan TASK-002, not only its stated perspective. Report mandatory defects with exact source and concrete correction; stop optional improvement once required criteria pass.

- Exact versioned requests, response envelopes, error codes and HTTP statuses must agree. Enumerate unknown keys, field types, text/ID size caps, response byte accounting, coverage/unknown totals and continuation semantics.
- Snapshot/current-input coordination must address active publication, stable partial commits, malformed relevant intents, missing-to-present locks, source staleness, helper/presentation changes, bounded retry/cache lifetime and concurrency. No second publication store or write-creating read lock.
- Ordinary search preserves existing normalization/ranking while disabling only Explorer semantic fallback. Filters precede pagination. Cursor scope includes service start, session, root/project, snapshot and the full query/filter/sort/direction contract.
- Exact record/source identities, relation IDs/endpoints/predicates/qualifiers and typed categories survive projection. A process identity or relation graph does not prove order. Explicit source sections distinguish supported sequence, partial precedence, missing and unexamined evidence.
- Loopback service has bounded transport/work concurrency and request/time/memory limits. Root is server-selected; Host/Origin/session/CSRF and source confinement are specified independently of authoring grants and optional advanced profiles. Bootstrap, cookies, cursor and retry failures disclose no credentials, source bodies or raw exception paths.
- Frontend state distinguishes selection/focus/query/snapshot/expansion/source and preferences. Response race, history, same-project preferences, source-focus restoration, renderer cleanup, independent List and CSP failure behavior remain implementable without a second authority.
- Exact package versions, build-only Node, current primary license/source evidence, runtime notices and reproducible lock/build plan are present. Static assets are manifest-only; package metadata, fixtures and private runtime cannot become HTTP assets.
- Change map preserves reusable sources, owner-mediated neutral Template distribution, exact later root adoption, independent projects, historical initializer editions and shared trusted authoring helpers. Cutover remains after actual production gates.

A proposal is not implementation evidence, a source inspection is not runtime evidence, and no approved contract may claim human comprehension, assistive technology or performance results that have not occurred.
