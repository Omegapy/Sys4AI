---
{
  "applicability": [
    "Native memory fixture only, at the exact source and helper versions cited in the observation."
  ],
  "claim": {
    "level": "verified_outcome",
    "summary": "The actual lexical memory CLI recalled the literal E=mc^2 source and eq:native-energy label with the current source digest; all 53 inspected filesystem entries preserved bytes and modification times."
  },
  "confidence": "high",
  "created": "2026-09-08T22:00:46.635855Z",
  "id": "MEM-20260908-31E9F7F5",
  "lifecycle": {
    "reason": null,
    "superseded_by": null,
    "supersedes": []
  },
  "limitations": [
    "This is one literal lexical fixture lookup; TeX macros and included files were not expanded or compiled.",
    "The preservation observation covers the 53 source, memory, role, config, baseline and canonical Task entries listed in search-observation.json.",
    "Backend retrieval, publication and Task completion were outside this worker observation."
  ],
  "modified": "2026-09-08T22:02:05.838622+00:00",
  "origin": {
    "execution_id": "native-memory-release-001",
    "generation": 1,
    "role": {
      "agents_path": "Roles/project-sub-agent/AGENTS.md",
      "agents_sha256": "7d064ae5d5954af65fc1a83b2ce1c69562d5c31f085e70ac92c3ad0bf2e7eec2",
      "name": "project-sub-agent",
      "role_path": "Roles/project-sub-agent/ROLE.md",
      "role_sha256": "4c3ac5415030ab770d9af7b73fc773da43d07b041889c77a8755974284c874e2"
    },
    "task_id": "TASK-20260908-300591ED",
    "task_path": "Tasks/Task-native-project-memory-release-verification-2026-09-08--300591ED/task.json"
  },
  "project_id": "native-memory-fixture",
  "publication": {
    "actor_id": "/root/memory_native_manager",
    "actor_kind": "manager",
    "approved_at": "2026-09-08T22:02:05.838622+00:00",
    "operation_id": "MEMOP-native-generic-001"
  },
  "schema_version": 1,
  "sources": [
    {
      "kind": "source",
      "locator": "label:eq:native-energy",
      "path": "research/fixture.tex",
      "sha256": "416f53b8a7b5697bb1522cd2066705af138f3ef921a6240247cab2603e4d3a73"
    },
    {
      "kind": "verification",
      "locator": "json:/details",
      "path": "output/generic/verification-receipt.json",
      "sha256": "62322c824035f922202a8bd0024355e2dc2c517e803d8f944252bd2754adaf67"
    }
  ],
  "state": "active",
  "title": "Labelled equation recalled without changing inspected fixture files",
  "type": "finding"
}
---
The lexical search for `eq:native-energy` returned `research/fixture.tex` with the source label and literal `E=mc^2` text. Direct inspection agreed with the returned current raw-byte digest.

The before and after observation found no byte or modification-time changes in the 53 inspected source, memory, role, configuration, baseline and canonical Task entries. The worker returned the observation in its assigned result; the confirmed manager reviewed the exact source and receipt before this publication.
