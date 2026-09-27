from pathlib import Path
base=Path('SKILLS-depo/collaborate')
p=base/'SKILL.md';s=p.read_text();s=s.replace('Read the selected project\'s SOUL.md,', '''The current initializer enables this complete capability by default for new and
selected existing projects after checked local adoption. Run read-only `health`
to assess the recorded complete package, exact supported owner and default Task
instructions. A customized, incomplete or incompatible installation blocks
readiness and remains preserved. Installation enables the working habit; the
manager still binds each execution's policy and grants.

Read the selected project's SOUL.md,''');p.write_text(s)
p=base/'references/commands.md';s=p.read_text();s=s.replace('All binding options are required;', 'All Task-operation binding options are required;')
s=s.replace('## Installation and recovery\n\nThe current read-owner profile requires exact reviewed installed Task,\norchestration, native-observation, and role-helper bytes. An absent, old,\ncustomized, or changed owner returns COLLAB_OWNER_UNSUPPORTED before executing\nunknown code. A nearby source package does not substitute for the selected\nproject\'s owner. Active depot-root and existing product copies require separately\nauthorized, reviewed adoption; Template distribution alone activates none.', '''## Installation and recovery

`python .agents/skills/collaborate/scripts/collaborate.py --project-root
/absolute/project health` is a read-only static check requiring no Task bindings.
It compares every package file with the completed setup module inventory or
`control_records/collaboration-installation.json` root adoption inventory,
checks exact reviewed owner pins and default Task/Agent Task instruction markers.
An explicit complete path-to-sha256 JSON map can be passed with --inventory-file.
Without a reviewed inventory it reports COLLAB_REVIEWED_INVENTORY_REQUIRED.
Enabled/static readiness does not prove a running native execution.

The current read-owner profile requires exact reviewed installed Task,
orchestration, native-observation and role-helper bytes and supports orchestration
versions 1 and 2. The separately reviewed depot-v1 profile requires its exact
Task/orchestration/role-helper bytes and supports version 1 only. It preserves the
root's existing Task policy and does not offer version 2 broker/current-input role
acknowledgement evidence. Profiles are indivisible: partial matches are rejected.
An absent, unknown, customized or changed owner returns COLLAB_OWNER_UNSUPPORTED
before executing unknown code. A source neighbor cannot substitute for the actual
selected owner. The current initializer automatically adopts the complete neutral
Template capability on create and prepare, including the selected destination of
an earlier completed setup receipt, using its existing module adoption transaction.
Other existing products receive no inferred bulk adoption.''')
s=s.replace('Do not infer\nbulk product adoption or a new initializer edition.', 'Preserve the base setup contract edition when adding collaboration through\nthe existing module receipt. Do not infer bulk product adoption.')
p.write_text(s)
p=base/'references/task-integration.md';s=p.read_text();a=s.index('The adapter preflights');b=s.index('\nReviewer release',a);s=s[:a]+'''The adapter preflights the exact required owner interface before invoking gates.
The current profile uses its protected versioned/native-input API. A separately
reviewed exact depot-v1 profile uses its existing version 1 read APIs and exact
context-reference checks; it cannot admit version 2 or claim its native broker
attestation. Unknown editions return COLLAB_OWNER_UNSUPPORTED. Compatibility
changes no owner validators, schemas or helpers.
'''+s[b:];s=s.replace('provider must match the exact reviewed OWNER_PROFILE', 'provider must match one complete exact reviewed OWNER_PROFILES entry');s=s.replace('for absent, older or customized target bytes.', 'for absent, unknown or customized target bytes.');p.write_text(s)
