# Preparing reviewed publication

Construct final record metadata and Markdown first, including its active state
and exact publication actor/operation/time. `render_record` produces portable
frontmatter; use the resulting exact bytes for review. The helper does not
silently stamp a different approval into reviewed content.

```python
from memory_core import json_bytes, render_record, sha256
from memory_publish import transaction_payload

content = render_record(reviewed_record)
payload = transaction_payload("MEMOP-example-0001", "publish", [
    {"path": "MEMORY/" + reviewed_record["metadata"]["id"] + ".md",
     "expected_sha256": None,
     "content": content,
     "reviewed_record_sha256": sha256(content)}
], "Record the observed project decision and its applicability.")
payload_sha256 = sha256(json_bytes(payload))
```

For an existing record, reopen it and use its actual prior SHA256 instead of
null. The grant's `reviewed_records` binds the same path, post-hash and
`expected_sha256`. Bind `config_sha256` to the actual `memory.yaml` bytes.
Save the actual current native roster receipt with a validity window of at
most five minutes. These fields record inspected authority; do not invent a
native receipt or treat this example as permission to publish.

The grant's `actor_kind` is `director` or `manager`. Director scope comes from
the reviewed project config binding and current governance hashes. Manager
scope comes from its actual canonical Task, current generation, active manager
assignment and `fit.writes`; the grant's Task reference must name those exact
versions. The helper rejects ordinary children as canonical publishers.

Invoke the selected operation with `--grant-file` and `--actor`. Record its
actual receipt through the Task's existing artifact/response mechanisms if
the current Task requires it. A receipt does not itself accept a Task or
change its state.

For supersession, include the successor and every predecessor in one payload.
The successor's `lifecycle.supersedes` and each predecessor's
`lifecycle.superseded_by` must agree. Preserve predecessor body bytes and
use the same explicit correction reason. A partial receipt reports actual
commit state; recover the exact journal with a current grant rather than
starting an unrelated replacement operation.

For a redaction, set `privacy_redaction: true` only under actual scoped
privacy authority. Include existing record versions and sanitized final bytes.
The reason and hash receipt survive; managed copies of selected content are
removed so recovery cannot restore it. Unrelated project history and external
copies remain outside this operation's boundary.
