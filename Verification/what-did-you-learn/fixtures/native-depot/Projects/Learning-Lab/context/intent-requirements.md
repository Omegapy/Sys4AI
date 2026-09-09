# Authorized controlled fixture requirements

PLAN-20260909-2AB7D4CC TASK-022 authorizes this bounded intent-routing fixture.
This document is the Director's concrete fixture design, not a transcript of a
user correction or a diagnosis of the existing to-trd skill.

An intent with missing purpose or acceptance criteria must return `clarify` and
name its missing fields. An intent with both fields must return `draft` with no
missing fields. Preserve the clear fast path. Do not guess unresolved material
requirements. Apply an improvement only to fixture/intent_router.py after a
separate later work unit retrieves and rechecks the accepted lesson.

The first reviewed proposal was to draft for every input; this controlled design
settles the correction by requiring material clarification only when needed.
The cause of any unrelated timeout is unknown without diagnostic evidence.
