from pathlib import Path
ROOT=Path.cwd();OUT=ROOT/'Verification/collaboration-enablement-20260927'
for path in ('README.md','SPECS.md'):
 raw=(ROOT/path).read_bytes();(OUT/'root-retained'/path).write_bytes(raw)
p=ROOT/'README.md';s=p.read_text();s=s.replace("Its reusable source and Template capability remain separate from this depot's\nunadopted live collaboration installation. Memory and ontology record the verified\nrelease and its limits through their separate publication workflows.",'''Collaboration is now [installed and enabled in this root](./.agents/skills/collaborate/SKILL.md).
The current [initializer](./.agents/skills/init-new-project/SKILL.md) enables it
for new and selected existing projects automatically. The complete neutral
Template supplies its package and default Task instructions. See the
[enablement evidence](./Verification/collaboration-enablement-20260927/RESULT.md).
Memory and ontology retain the current state and historical release boundaries.''');p.write_text(s)
p=ROOT/'SPECS.md';s=p.read_text();start=s.index('The reusable source and neutral Template contain the capability.',s.index('## Shared agent'));s=s[:start]+'''The reusable source, neutral Template and depot root now contain the complete
capability. The root installation is enabled through exact package inventory,
reviewed depot-v1 Task-owner compatibility and default Task/Agent Task
collaboration instructions. Its read-only `health` assessment passes. The existing
root Task helper, all canonical Task records, role pairs and root governance
remain preserved; version 1 compatibility grants no version 2 native broker proof.

The current initializer automatically enables collaboration on create and first
prepare-existing, and adds missing capability to the selected earlier completed
setup through its existing module adoption transaction. Base receipt editions,
identity, history, configurations and project-owned content remain preserved.
A complete reviewed package, one whole exact owner profile and default instruction
markers are required. Customized, incomplete or unsupported package/guidance/owner
combinations block enabled readiness without execution or overwrite. Reruns are
idempotent; interrupted collaboration adoption resumes the same frozen operation.
No other registered product is refreshed implicitly.

Static-ready installation enables the default working habit. Each Task manager
still verifies common-store topology, registers its scoped policy, binds exact
baseline/current inputs and supplies participant grants before dispatch. Required
read checkpoints, independent candidate/first-review seals, material owner
assessment and input-before-wake gates remain in force. Setup starts no service,
installs no dependency/model, creates no Task and provides no automatic idle wake.

[Enablement verification](./Verification/collaboration-enablement-20260927/RESULT.md)
covers actual root static preflight, current owner gates, scoped depot-v1 exchange,
initializer create/prepare/earlier-receipt/recovery/idempotence/conflict cases and
exact Source/Template/root adoption. Confined receipts and injected failures are
deterministic evidence. Historical generic V1/extra-complex V2 native results and
current package deterministic/adoption checks remain distinct; this enablement
performs no new native pilot and claims no performance or quality advantage.
See [commands](./.agents/skills/collaborate/references/commands.md),
[Task integration](./.agents/skills/collaborate/references/task-integration.md) and
[knowledge proposals](./.agents/skills/collaborate/references/knowledge-and-maintenance.md).
''';p.write_text(s)
