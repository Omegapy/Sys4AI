from pathlib import Path
p=Path('SPECS-depo/project-template-SPECS.md');s=p.read_text();assert '## Default Task collaboration' not in s;s+='''
## Default Task collaboration

The complete collaborate package and Task/Agent Task collaboration instructions
are neutral starter assets. Current initializer create and prepare routes enable
collaboration automatically after complete package and exact owner compatibility
checks. Selected earlier completed setup receipts gain the capability through
an additive module transaction; their base edition and history remain preserved.
Custom, incomplete or unsupported package/guidance/owner combinations block
readiness without execution or overwrite. No populated board, Task assignment,
policy, grant, learned record, backend or service belongs to this starter.

The installed collaboration health check verifies recorded package inventory,
one complete reviewed owner profile and default instruction markers. Static
readiness enables the habit; actual Task execution still binds manager-produced
policy, current native assignments, scoped grants and independence checkpoints.
Posts, notification, reported reading and canonical decisions remain distinct.
''';p.write_text(s)
p=Path('SPECS-depo/project-template-README.md');s=p.read_text();s+='''
## Default collaboration

The [collaborate capability](./.agents/skills/collaborate/SKILL.md) is included
with default Task instructions. The current initializer enables it automatically
for new and selected existing projects, preserving old setup editions and custom
files. See [the specifications](./SPECS.md#default-task-collaboration) and the
[initializer guide](./.agents/skills/init-new-project/README.md) for checked adoption
and static health. Execution retains each Task manager's policy and grants.
''';p.write_text(s)
p=Path('AGENTS-depo/project-template-AGENTS.md');s=p.read_text().replace('Adopt the installed `.agents/skills/collaborate/SKILL.md` only with a manager-', 'Current initialization enables the complete compatible collaboration capability\nby default. Follow the installed `.agents/skills/collaborate/SKILL.md` with a manager-');p.write_text(s)
