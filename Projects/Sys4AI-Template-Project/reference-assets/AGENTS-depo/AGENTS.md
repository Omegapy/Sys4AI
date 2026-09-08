# AGENTS.md

Root project guidance for agents working in this project.

## Required First Reads

1. Read `./SOUL.md` before performing any work. It defines the required reasoning, engineering, and communication behavior for the agent.
2. Read `./ROLE.md` before performing any work. It defines the agent's active role.

3. Read `./SPECS.md` and the owning project's current requirements and constraints.

## Explicit Task execution

Use the installed `.agents/skills/task/SKILL.md` only under its activation
contract. The host performs bounded bootstrap to one real native manager;
canonical writer authority transfers only after the actual receipt and
activation handoff. The confirmed manager owns that Task execution, while
ordinary children return bounded evidence. Reading this file does not promote
a child to manager. Keep Task, TRD, plan, conversation and native goal state
separate. Status and other read-only routes do not start execution.

Use `.agents/skills/manage-subagent-roles/SKILL.md` before every assignment.
Active roles use paired `roles/<name>/AGENTS.md` and `ROLE.md`; their generated
index is navigation only. Preserve exact manager model and reasoning settings,
independent solver contexts and non-overlapping authorized write ownership.
