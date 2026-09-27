# Command routes

Use the selected project interpreter and its installed `scripts/curator.py`.
`status --policy /absolute/project/curator.yaml` reports existing configuration and
pending metadata. `review --policy ... --scope path` restricts notices to the
requested paths; repeat scope for multiple paths. This standalone metadata view
reports `analysis_performed: false`. Neither invokes a model,
creates a Task or writes canonical state. `validate --policy ...` checks schema.

`update`, `correct`, `retry`, `pause` and `resume` accept `--policy` and an exact
`--selection` JSON file with operation ID, payload digest and payload. Standalone
commands return `held: authenticated_application_required` with a nonzero exit;
the file is not authority. The native host constructs `Application` around its
actual verified Broker with `application_controls=True`. `Application.run` uses
the same callbacks for manual and automatic accepted operations. Wrong origin,
request, tool, permission, owner, source or native context denies before effect.

For an explicit bounded source-ownership review, the authenticated host calls
`Application.review(affected_paths=paths, request=request, context=callback)` with
an accepted `target.classify` operation of permission class `analysis` and exact
payload `{"analysis":"source-ownership","paths":["selected/path"]}`. It reads
the exact selected source bytes, checks their ownership/section routing, and
returns source identities and classifications. The maximum is 50 distinct paths,
2 MB per source and the smaller of 8 MB or the accepted byte budget overall.
It issues no write grant and performs no canonical writes or model analysis.
Other analyses are not implied by this fixed analysis selection.

Status is observation, pending is unfinished obligation, unavailable means a
required current resource cannot be observed, and blocked means a known scope,
owner or authority conflict. Installed/inactive and selected/unverified are not
runtime-ready. An exact retry retains the original operation and journal while
using fresh authentic recovery transport. Aborted maintenance may be reconciled
and consumed while its products still require a separate subsequent rebuild.

`tick --selection /absolute/selected.json` computes due status for the exact policy
hash and existing scheduling state. It cannot activate native work on its own.
The operational `Application.tick` embedding uses an actual current native
callback and pool and the same automatic owner route. It retains issued costs,
finite iterations, exact receipt replay and unavailable-runtime holds; see
[scheduling](../../../CURATION-depo/scheduling.md). A standalone actor/session
wake bridge remains incomplete and is not synthesized from selection JSON.
See [conversation](conversation.md) for contextual selection and the unchanged
summary-first log commands in [SKILL.md](../SKILL.md).
