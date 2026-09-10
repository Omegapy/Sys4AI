# Measured SHACL correction

The repaired source validates the complete authored root graph in 5.8784 seconds
under the unchanged 10-second worker deadline. The frozen input contains all
191 records and 3,413 triples: 2,268 asserted, 1,129 derived and 16 external.
The original source times out after 10.0076 seconds on the same input.

Meta-SHACL is the measured bottleneck. Original dataset preparation takes
0.031 seconds and generated-shape construction takes 0.261 seconds; meta-SHACL
starts at 0.343 seconds and does not complete before termination. The repaired
meta-SHACL phase completes in 5.464 seconds, followed by 0.153 seconds of data
validation and result handling. Peak RSS falls from 138,838,016 to 66,142,208
bytes. [The diagnosis](diagnosis.json), [input manifest](input-manifest.json),
[original replay](before-replay.json) and [repaired replay](final-replay.json)
bind the measured inputs, packages, helpers, graphs and limits.

The source now shares equal, fully constructed property shapes and ordered RDF
value lists within one generated graph. There are 2,346 property references but
only 43 distinct property definitions, and 210 list references but only 18
distinct lists. Sharing lowers generated shape triples from 41,424 to 3,868.
Every target and constraint remains present. The cache exists only inside
`shapes_for_records`; a new call rebuilds its graph from the current records.
No persistent cache, package, limit, supervisor or SHACL option changed.

List sharing alone was measured and rejected as insufficient: it still timed
out at the existing 60-second ceiling. The final correction shares entire
immutable property definitions, including cardinalities and list membership.
The generated constraints, custom shapes, meta-SHACL, no-inference setting,
non-executable feature selection, result handling and explicit graph controls
are preserved.

Verification includes:

- [Exact expanded shape comparison](shape-equivalence.json): all 191 targets
  and 2,346 property associations match, including ordered list content.
- [Fifteen actual controls per version](semantic-equivalence.json): status,
  completeness and all focus/path/severity/constraint findings match with
  multiplicity. Raw diagnostic text remains available; its `sh:in` value order
  and generated blank-node labels are not semantic identities.
- [Four focused tests](focused-tests.log) pass. They cover domain/range,
  cardinality, source requirements, changed inputs, external graph selection,
  inferred exclusion, custom and malformed shapes, unsupported features,
  meta-SHACL rejection, input/triple/RSS/output/result limits and cancellation.
- [Full-graph failure controls](failure-controls.json) terminate a one-second
  request after 1.0068 seconds and a cancelled request after 0.2005 seconds.
  Both remain incomplete and record worker exit `-9`.
- [Disposable runtime certification](source-runtime-certification.json) passes
  all ten existing confinement/resource checks using copied existing packages.

The first completed result also exposed the original default graph selection's
12 missing-field findings. The `depot` and `registered-template` records have
external metadata, but the old default selected only asserted and derived
graphs while generating shapes for both records. Selecting every authored
graph resolves those findings without removing constraints. The host owns the
default-scope change; explicit scope still excludes unselected metadata, and
inferred data remains prohibited for authoring validation.

Reproduce the exact recorded comparison from the depot root with:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python Verification/ontology-health-repairs/shacl/profile_shacl.py --variant before --output before-replay.json
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python Verification/ontology-health-repairs/shacl/profile_shacl.py --variant final --output final-replay.json
```

`profile_shacl.py` selects the frozen full payload and the existing root runtime.
Its diagnostic copies only report phases; the source worker's uninstrumented
completion is retained separately in `source-full-result.json` for the original
explicit graph scope. Earlier watchdog/cProfile diagnostic files are retained
as investigation evidence; the watchdog-free replays above determine the final
timings and result.

For source-suite execution, select the separately certified disposable clone:

```sh
export SYS4AI_STANDARDS_PYTHON=/Volumes/P-SSD/AngryOwl/Sys4AI/Verification/ontology-health-repairs/shacl/source-runtime/.venv-ontology-standards/bin/python
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest discover -s SKILLS-depo/ontology/tests -p test_shacl_lists.py -v
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python Verification/ontology-health-repairs/shacl/compare_semantics.py
```

This bounded assignment changes only the reusable SHACL source and its focused
test. Root/Template adoption, the root certificate, default authoring scope,
shared guarded-owner acceptance and final live root replay remain host work.
