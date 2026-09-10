"""Record reviewed criterion coverage with hashes of the actual evidence."""
from final_audit import ROOT, OUT, PLAN, TEMPLATE, read, digest, stamp, write

O = 'SKILLS-depo/ontology/tests/'
I = 'SKILLS-depo/init-new-project/tests/'
V = 'Verification/ontology-first-release/'

# These explanations are human-reviewed coverage conclusions, not conclusions
# inferred by the script from file existence or passing counts.
REVIEW = {
1: ('Canonical ontology, configuration, projections and durable control records have declared independent ownership. Real reads, publication and linking preserve root memory, governance and Task state.', 'installed-interface-observations.json preservation-audit.json memory-integration-observations.json', 'test_loading.py test_publication.py test_authority.py'),
2: ('Explicit root, saved identity and namespace are checked before selected-file loading. Neutral/mismatched identities, unsafe aliases and sibling references are rejected; separate initialized projects retain separate identities.', 'initializer-observations.json installed-health.json', 'test_loading.py'),
3: ('Exact allowlists describe factual registry metadata without traversing child ontologies. Independent project inventories are preserved and later fixture source changes do not propagate into products.', 'preservation-audit.json initializer-observations.json', 'test_loading.py'),
4: ('A strict compact JSON-LD graph profile and JSON-subset configuration use standard-library parsing. Canonical sources and generated products have separate declared paths.', 'service-independent-check.json root-rebuild-verification.json', 'test_loading.py test_build.py'),
5: ('Only the pinned vendored context is accepted. Remote, nested, unknown and escaping references fail before target content is read; no general JSON-LD or RDF processing is advertised.', 'adversarial-profile-verification.json service-independent-check.json', 'test_loading.py'),
6: ('Repeated root compile and wiki builds are byte-identical and retain canonical bytes. Deleted generated data rebuilds; unknown or edited destinations are preserved. Transaction tests distinguish durable intent/receipt recovery from generated output.', 'root-rebuild-verification.json root-publication-receipt.json', 'test_build.py test_publication.py'),
7: ('Core 1.0.0 provides 65 portable concept/predicate/relation records, including the required vocabulary. The same core is locked in source, neutral starter, root and Template; project instances remain outside it.', 'distribution-parity.json final-competency-check.json', 'test_modules.py'),
8: ('Version, complete content-map digest and manifest hash identify each import. Missing, extra or altered bytes and wrong versions fail; receipt-owned explicit refresh is separate from ordinary reruns.', 'distribution-parity.json initializer-refresh-observations.json', 'test_modules.py'),
9: ('Local subtypes and distinct project IDs extend the core. Core redefinitions, duplicate and foreign namespace identities fail, and local extensions do not alter imported or sibling data.', 'distribution-parity.json preservation-audit.json', 'test_modules.py'),
10: ('Stable absolute semantic IDs remain independent of label and binding path. Local subtype/label movement retains identity; lifecycle validation rejects deletion and type/meaning recycling.', 'final-competency-check.json', 'test_modules.py test_lifecycle.py'),
11: ('Approved/deprecated records require explanatory metadata and exact provenance. Aliases target the stable record; optional scope/examples and semantic relationships survive retrieval and wiki rendering.', 'installed-task.json wiki-walkthrough.md', 'test_validation.py test_query_retrieval.py'),
12: ('Task, TRD, ImplementationPlan, NativeGoal and conversation meanings are distinct. Root competency checks and actual Task/TRD output preserve approval/activation/completion and verification/validation boundaries.', 'installed-task.json installed-trd.json final-competency-check.json', 'test_query_retrieval.py'),
13: ('Record kind distinguishes concept types from concrete skills and artifact bindings. Actual memory capability output identifies both the shared capability and installed provider; skill artifact identities remain separate.', 'installed-memory-capability.json installed-skill-capabilities.json final-competency-check.json', 'test_query_memory.py'),
14: ('Registered predicates declare domain, range, direction, cardinality and qualifiers. The deterministic validator rejects dangling or incorrectly typed endpoints and invalid configured cardinality/qualifiers.', 'installed-neighbors.json final-competency-check.json', 'test_validation.py test_query_retrieval.py'),
15: ('Fact kind and exact provenance are retained in results, graph and generated pages. Derived memory associations remain versioned sidecars; classifying inferred facts does not run an inference engine.', 'installed-neighbors.json root-compile.json memory-integration-observations.json wiki-walkthrough.md', 'test_query_memory.py'),
16: ('The root binds only exact selected governance, skill, role-pair and registry sources. Traversal, child roots, private state, credentials and aliases are rejected; memory exclusions/configuration are byte-preserved.', 'root-seed/manifest.json preservation-audit.json', 'test_loading.py'),
17: ('Results expose source paths, hashes and typed locators plus complete configuration/module/helper context. Changed/missing source bytes are explicitly stale/unavailable, while current-authority reads expose the newly read source and discrepancy.', 'installed-task.json installed-current-governance.json release-candidate.json', 'test_loading.py test_query_retrieval.py'),
18: ('Retrieval describes meaning and capability without invoking skills or assigning authority. Current-source discrepancies are surfaced. Exact ontology grants and existing Task writer gates govern separate mutations; no execution interception is installed.', 'installed-interface-observations.json native-task-observations.json preservation-audit.json', 'test_authority.py test_query_retrieval.py'),
19: ('Publication binds reviewed payload/reason/current digest and exact current Director or manager scope. Child, stale, memory-only and conflicting-owner grants fail. Accepted transactions and bounded partial recovery preserve unrelated bytes.', 'root-publication-receipt.json memory-integration-observations.json native-task-observations.json', 'test_authority.py test_publication.py'),
20: ('Deprecated IDs retain historical meanings and replacement metadata. Approved semantic edits need renewed review/history; deletion, identity recycling and unchanged approval of revised meaning fail.', 'installed-deprecated.json native-task-observations.json', 'test_lifecycle.py'),
21: ('Suggestion transitions create provisional candidates, leaving inputs unchanged. Draft or ambiguous memory associations cannot rewrite an approved canonical definition.', 'memory-integration-observations.json', 'test_lifecycle.py test_query_memory.py'),
22: ('Duplicate IDs and unresolved typed endpoints fail with stable actionable record diagnostics; valid equivalents pass the same deterministic check.', 'final-competency-check.json adversarial-profile-verification.json', 'test_modules.py test_validation.py'),
23: ('Unmodeled label/alias collisions fail; explicitly mutual ambiguity declarations require distinctions and return distinct candidate IDs instead of a guessed exact match.', 'test-results.json', 'test_validation.py test_query_retrieval.py'),
24: ('Required metadata, typed relations, cardinalities, qualifiers and declared acyclic predicates have executable negative cases. Non-acyclic cycles remain valid; reordered records produce stable diagnostics without a service.', 'service-independent-check.json test-results.json', 'test_validation.py'),
25: ('Every installed read scenario preserved 490 observed paths including bytes, mtimes and ctimes. Missing/stale generated-state tests prove reads create no directory or repair; no read creates Tasks or publishes.', 'installed-interface-observations.json final-root-task-status.json', 'test_loading.py test_query_retrieval.py'),
26: ('Stable IDs and exact labels precede aliases and lexical matches with deterministic tie breaks. Unknown/ambiguous vocabulary is explicit, and lexical/core lookup succeeds with site packages disabled.', 'installed-exact-read.json installed-lexical.json installed-unknown.json service-independent-term.json', 'test_query_retrieval.py'),
27: ('Typed incoming/outgoing traversal and predicate filters retain direction. Cycles terminate with declared hop/result/serialized-byte limits and explicit truncation; actual Task neighbors and Task-to-MemoryRecord path are recorded.', 'installed-neighbors.json installed-path.json', 'test_query_retrieval.py'),
28: ('Machine and human results identify the same stable identity, source evidence and match reason. Lifecycle and source freshness remain explicit; deprecated replacement and lexical truncation are observed.', 'installed-task.json installed-lexical.json installed-deprecated.json', 'test_query_retrieval.py'),
29: ('Health distinguishes missing identity/config, import errors, empty usable extensions, source freshness and missing/stale projections. Reads retain valid canonical results and leave repairs explicit.', 'installed-health.json initializer-observations.json', 'test_loading.py test_build.py test_query_retrieval.py'),
30: ('Generated Task pages state their TRD distinction, owning canonical location, fact classification and source versions. Edited generated content is never parsed as canonical knowledge.', 'wiki-walkthrough.md root-rebuild-verification.json', 'test_query_retrieval.py'),
31: ('The actual index-to-Task and memory-capability walkthrough follows relationships and local sources. Stable filenames and repeated bytes were verified; a deliberately broken link is detected in tests.', 'wiki-walkthrough.md root-rebuild-verification.json', 'test_query_retrieval.py'),
32: ('Actual capability/skill queries identify installed memory and to-trd sources and execution limits. Core competency checks enforce the TRD-not-Task distinction; changed provider sources are stale and discovery invokes nothing.', 'installed-memory-capability.json installed-skill-capabilities.json final-competency-check.json', 'test_query_memory.py'),
33: ('Role bindings contain their exact same-directory AGENTS.md/ROLE.md pairs. Queries distinguish host Director, confirmed Task manager and ordinary child without editing those roles or the Task ledger.', 'installed-manager-role.json root-seed/manifest.json preservation-audit.json', 'test_loading.py test_query_memory.py'),
34: ('Definition, relationship, capability, current, history and mixed routes use the intended ontology, graph, current-source and installed-memory interfaces. Actual current-governance and historical outputs retain their source categories.', 'installed-current-governance.json installed-mixed-after-links.json installed-memory-capability.json', 'test_query_memory.py test_query_retrieval.py'),
35: ('Actual reciprocal publication proves ontology writes/linking preserve schema-1 memory, while real memory supersession preserves ontology. Root memory corpus, records, backend and capture setting remain unchanged.', 'memory-integration-observations.json root-memory-links-observation.json preservation-audit.json automatic-capture-checkpoint.json', 'test_publication.py test_query_memory.py'),
36: ('Explicit sidecars link accessible record versions to resolvable concepts; ambiguity/unmatched results are recorded. A real supersession makes links stale, excludes them from current evidence, and explicit rebuild restores current links without canonical writes.', 'memory-integration-observations.json root-memory-links-observation.json', 'test_query_memory.py'),
37: ('Ontology terms expand queries through supported memory reads and preserve memory exclusions. Actual prior-manager query returns real historical evidence; unavailable/no-match and frozen-new-record cases do not invent evidence or provision a backend.', 'installed-mixed-after-links.json memory-integration-observations.json', 'test_query_memory.py test_query_packets.py'),
38: ('Mixed results label ontology definitions, memory record identities/versions and current governing sources separately. Concept matches and historical associations never become event proof or operational permission.', 'installed-mixed-after-links.json memory-integration-observations.json', 'test_query_memory.py'),
39: ('A confirmed native manager freezes/registers exact packets through current Task artifacts, baseline and assignment APIs. External artifact digests avoid self-hashes; empty/oversize/owner/scope and sibling inputs are tested without a Task schema change.', 'native-task-observations.json native-context-comparison.json', 'test_query_packets.py'),
40: ('Two actual independent solver contexts received identical 13-record packet/source inputs. A later publication remained excluded in both; changing a selected source rejected the old packet, and current retrieval stayed within the frozen selection.', 'native-context-comparison.json native-task-observations.json', 'test_query_packets.py'),
41: ('Ontology routines never create or complete Tasks. The real confirmed manager used existing reserve/input/reconcile/version/senior/acceptance gates for same-ID material reassessment and documented immaterial late-content isolation.', 'native-task-observations.json native-context-comparison.json final-root-task-status.json', 'test_authority.py test_query_packets.py'),
42: ('Seventy-five reviewed source files were promoted under the existing updater lock; the real updater applied 57 additions and 16 updates with zero deletes. Final Template mapping is current, and independent projects remain unchanged.', 'change-manifest.json source-promotion-receipt.json template-update.json distribution-parity.json preservation-audit.json', ''),
43: ('Root adoption records exact source/root hashes and published seed scope. Installed commands resolve sys4ai-depot with 28 passing competency questions; memory, learning, Task, role, licenses, old runtime absence and independent projects are preserved.', 'root-adoption-preview.json root-publication-receipt.json distribution-parity.json preservation-audit.json final-competency-check.json', ''),
44: ('The actual Template has null project identity/namespace, disabled unbound publication, empty extension/bindings and locked portable core. It contains no root ontology instances, derived links, wiki or ontology runtime/control state.', 'distribution-parity.json', ''),
45: ('Actual create and first preparation specialize distinct IDs/namespaces and local Director bindings. Their receipts separate copied/configured/preserved/static-ready state from runtime and current grants; no service or package is provisioned.', 'initializer-observations.json initializer-native-create.json initializer-first-prepare.json', ''),
46: ('Actual v7 reruns install no ontology and retain the original edition. Selected adoption appends scoped module receipts; later unchanged-owned refresh is explicit. No real existing product is adopted.', 'initializer-observations.json initializer-edition-observations.json initializer-refresh-observations.json preservation-audit.json', ''),
47: ('A real customized incomplete package stays whole with precise unavailable diagnostics. Governance/licensing/memory/capture settings survive; deterministic interruption/tamper tests enforce exact same-request recovery and reject drift.', 'initializer-observations.json', ''),
48: ('Installed core lookup and all structural/competency checks pass with Python site packages disabled. Optional-memory unavailable cases retain valid ontology results and report limitations; nothing installs dependencies or starts services.', 'service-independent-term.json service-independent-check.json installed-mixed-after-links.json', 'test_query_memory.py'),
49: ('Installed/source documentation provides authoring, retrieval, graph, wiki, review/grant and integration examples. It distinguishes semantics, history, current authority and setup readiness and labels future RDF/inference/service features out of scope.', 'wiki-walkthrough.md release-candidate.json', ''),
50: ('Fourteen core and fourteen root competency questions assert concrete IDs, distinctions, sources, capabilities, relationships and no-result expectations. Project questions are separately selected without rewriting core vocabulary.', 'final-competency-check.json', 'test_query_retrieval.py'),
51: ('The combined entry point reports structural and competency results plus complete context; either negative group fails the run. Profile/semantic/path adversarial cases and documented local CI commands are exercised.', 'final-competency-check.json adversarial-profile-verification.json service-independent-check.json test-results.json', 'test_validation.py test_loading.py test_query_retrieval.py'),
52: ('Fifteen actual installed CLI scenarios record project, source context, route and results for terminology, capability, traversal/path, deprecated replacement, current sources, history and no-match; this is separate from deterministic suite evidence.', 'installed-interface-observations.json installed-mixed-after-links.json', ''),
53: ('Actual create, first-prepare, prior-edition rerun/adoption, customization and refresh receipts demonstrate identity specialization and preservation. A fixture-only source change did not propagate to the initialized child; root lookup remained local.', 'initializer-observations.json initializer-refresh-observations.json preservation-audit.json installed-interface-observations.json', 'test_loading.py'),
54: ('Actual reciprocal ontology/memory transactions, immutable native packets delivered to two independent contexts and same-ID reassessment have exact receipts. Byte/timestamp nonmutation and real ordinary-child rejection are recorded separately from synthetic unit scenarios.', 'memory-integration-observations.json native-task-observations.json native-context-comparison.json installed-interface-observations.json test-results.json', 'test_authority.py test_query_packets.py'),
}

ALIASES = {
    **{O + name: [O + 'test_query_retrieval.py'] for name in ('test_retrieval.py', 'test_graph.py', 'test_cli.py', 'test_wiki.py', 'test_wiki_navigation.py', 'test_bindings.py', 'test_competency.py')},
    **{O + name: [O + 'test_query_memory.py'] for name in ('test_routing.py', 'test_memory_links.py', 'test_mixed_queries.py')},
    **{O + name: [O + 'test_query_packets.py'] for name in ('test_packets.py', 'test_task_integration.py')},
    'ONTOLOGY-depo/policy.md': ['ONTOLOGY-depo/profile.md', 'ONTOLOGY-depo/publication-and-recovery.md', 'ONTOLOGY-depo/state-paths.md'],
    'control_records/ontology/publications/': ['control_records/ontology/intents/', 'control_records/ontology/receipts/'],
    'Applicable canonical implementation-plan evidence and final Task Response': [V + 'final-plan-validation.json', V + 'native-task-observations.json'],
}


def refs(paths):
    result = []
    for relative in sorted(set(paths)):
        if relative == V + 'requirement-audit.json':
            result.append({'path': relative, 'digest_location': V + 'final-release-manifest.json',
                           'note': 'Self-reference: the final external release manifest records this report digest.'})
            continue
        path = ROOT / relative
        assert path.exists(), relative
        if path.is_file():
            result.append({'path': relative, 'sha256': digest(path)})
        else:
            members = [p for p in sorted(path.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.name != '.DS_Store']
            result.append({'path': relative, 'files': [{'path': str(p.relative_to(ROOT)), 'sha256': digest(p)} for p in members]})
    return result


def run():
    plan = read(PLAN)
    assert len(plan['requirements']) == len(REVIEW) == 54
    assert read(OUT / 'native-task-observations.json')['status'] == 'completed'
    assert read(OUT / 'native-handoff-verification.json')['status'] == 'passed'
    assert read(OUT / 'test-results.json')['all_passed']
    assert read(OUT / 'preservation-audit.json')['all_preserved']
    tasks = []
    for task in plan['tasks']:
        actual = []
        for target in task['target_artifacts']:
            actual.extend(ALIASES.get(target, [target]))
        tasks.append({'task_id': task['task_id'], 'title': task['title'], 'requirement_ids': task['requirement_ids'],
                      'technical_delivery': 'verified', 'managed_task_status': task['status'],
                      'acceptance_criteria': task['acceptance_criteria'], 'artifacts': refs(actual),
                      'layout_adjustments': [{'planned': t, 'actual': ALIASES[t]} for t in task['target_artifacts'] if t in ALIASES]})
    requirements = []
    for req in plan['requirements']:
        number = int(req['requirement_id'].split('-')[1])
        explanation, evidence, tests = REVIEW[number]
        inputs = [V + p for p in evidence.split()] + [O + p for p in tests.split()]
        if 45 <= number <= 47 or number == 53:
            inputs += [I + p for p in ('test_ontology_setup.py', 'test_ontology_adoption.py', 'test_ontology_recovery.py')]
        evidence_refs = refs(inputs)
        related = [t['task_id'] for t in tasks if req['requirement_id'] in t['requirement_ids']]
        requirements.append({'requirement_id': req['requirement_id'], 'title': req['title'],
            'status': 'verified', 'reviewed_conclusion': explanation, 'task_ids': related,
            'acceptance_criteria': [{'criterion': i, 'text': c, 'status': 'verified', 'evidence': evidence_refs}
                                    for i, c in enumerate(req['acceptance_criteria'], 1)]})
    changed = set(x['destination'] for x in read(OUT / 'change-manifest.json')['source_entries'])
    changed.update(x['destination'] for x in read(ROOT / 'control_records/ontology/root-adoption.json')['entries'])
    update = read(OUT / 'template-update.json')
    changed.update('Projects/Sys4AI-Template-Project/' + p for p in update['additions'] + update['updates'])
    for base in ('ONTOLOGY', 'control_records/ontology', '.sys4ai/ontology'):
        changed.update(str(p.relative_to(ROOT)) for p in (ROOT / base).rglob('*') if p.is_file() and p.name != '.DS_Store')
    changed.update(('README.md', 'SPECS.md', '.gitignore', 'ontology.yaml'))
    reverse = []
    for relative in sorted(changed):
        if not (ROOT / relative).is_file():
            continue
        owners = set()
        for t in tasks:
            for artifact in t['artifacts']:
                a = artifact['path']
                if relative == a or a.endswith('/') and relative.startswith(a):
                    owners.add(t['task_id'])
        if relative.startswith('SKILLS-depo/ontology/tests/'):
            owners.update(('TASK-004', 'TASK-031', 'TASK-037'))
        if relative.startswith('SKILLS-depo/init-new-project/'):
            owners.update(('TASK-024', 'TASK-025', 'TASK-026', 'TASK-030', 'TASK-037'))
        if relative.startswith('ONTOLOGY-depo/'):
            owners.update(('TASK-002', 'TASK-005', 'TASK-023', 'TASK-030'))
        if relative.startswith('ONTOLOGY/'):
            owners.update(('TASK-023', 'TASK-028', 'TASK-029'))
        if relative.startswith('Projects/Sys4AI-Template-Project/'):
            owners.update(('TASK-027', 'TASK-037'))
        if relative.startswith(('control_records/ontology/', '.sys4ai/ontology/')):
            owners.update(('TASK-028', 'TASK-029', 'TASK-035'))
        if not owners:
            raise AssertionError('No reverse requirement basis: ' + relative)
        ids = sorted({r for t in tasks if t['task_id'] in owners for r in t['requirement_ids']})
        reverse.append({'path': relative, 'sha256': digest(ROOT / relative), 'task_ids': sorted(owners), 'requirement_ids': ids})
    write('requirement-audit.json', {'schema_version': 1, 'observed_at': stamp(), 'plan_id': plan['plan_id'],
          'plan_revision': plan['revision'], 'plan_sha256': digest(PLAN), 'status': 'verified',
          'requirement_count': len(requirements), 'criterion_count': sum(len(r['acceptance_criteria']) for r in requirements),
          'task_count': len(tasks), 'unverified_requirements': [], 'unmapped_changed_production_files': [],
          'method': 'Reviewed each criterion against implementation, current deterministic tests and separately identified actual operation/native receipts. This report is evidence, not a mutation of managed plan or Task state.',
          'requirements': requirements, 'tasks': tasks, 'reverse_artifacts': reverse,
          'layout_adjustment_reason': 'Tests share three focused query suites; policy is integrated in the profile/state/publication contracts; durable operations use explicit intents and receipts directories. The original technical requirements and acceptance behavior are unchanged.',
          'evidence_artifact_basis': 'All files in Verification/ontology-first-release are scoped implementation/acceptance records for TASK-001 and TASK-031 through TASK-039. Disposable staging and native/initializer fixtures are excluded from source publication.',
          'native_task_scope': 'The completed native Task belongs only to the disposable representative project; the real root ledger and selected managed plan remain unchanged.'})
    print('Coverage verified: 54 requirements, ' + str(sum(len(r['acceptance_criteria']) for r in requirements)) + ' criteria, 39 tasks, ' + str(len(reverse)) + ' production artifacts.')


if __name__ == '__main__':
    run()
