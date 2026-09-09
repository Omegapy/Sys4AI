---
{
  "applicability": [
    "The isolated Learning-Lab intent-routing fixture only; recheck current requirements before reuse."
  ],
  "claim": {
    "level": "accepted_design",
    "summary": "The authorized fixture design requires clarification for missing material intent while preserving the already-clear draft path."
  },
  "confidence": "high",
  "created": "2026-09-09T05:48:35.811551+00:00",
  "id": "MEM-20260909-A1B2C3D4",
  "lifecycle": {
    "reason": null,
    "superseded_by": null,
    "supersedes": []
  },
  "limitations": [
    "Controlled accepted fixture design, not production behavior or a long-term reliability measurement."
  ],
  "modified": "2026-09-09T05:48:35.811551+00:00",
  "origin": {
    "execution_id": null,
    "generation": null,
    "role": null,
    "task_id": null,
    "task_path": null
  },
  "project_id": "wdyl-lab",
  "publication": {
    "actor_id": "/root",
    "actor_kind": "director",
    "approved_at": "2026-09-09T05:48:35.811551+00:00",
    "operation_id": "MEMOP-wdyl-native-intent-001"
  },
  "schema_version": 1,
  "sources": [
    {
      "kind": "design",
      "locator": "document",
      "path": "context/intent-requirements.md",
      "sha256": "d2e26ced37c1f6e56d37daafce39b66d06b32ca05f6ce2d57b0531179da3b3da"
    }
  ],
  "state": "active",
  "title": "Clarify missing material intent and preserve the clear fast path",
  "type": "lesson"
}
---
## Observation

The controlled design settles that missing purpose or acceptance criteria need clarification. The real baseline check fails the ambiguous case and passes the clear case.

## Evidence

context/intent-requirements.md defines the accepted boundary. evidence/intent-before-results.json records the actual failing check and the preserved clear fast path. The native manual review is retained separately by the Director.

## Lesson and applicability

Before drafting in this fixture, check material intent fields. Clarify the missing fields; preserve the already-clear draft path. Reassess current sources when this lesson is retrieved.

## Limitations

This is an accepted fixture design and measured baseline, not an implemented fix. It does not diagnose the production to-trd skill or establish a timeout cause.

## Improvement disposition

Targeted improvement authorized by PLAN-20260909-2AB7D4CC TASK-022: a separate later native work unit may change only fixture/intent_router.py to implement the two specified paths. Preserve all governance, memory, requirements and existing to-trd sources. This review performs no code change.

## Validation and follow-up

Later work must retrieve this canonical lesson, recheck current requirements and run fixture/check_intent.py. Publication, implementation and later observed behavior require distinct evidence. No long-term benefit has been measured.
