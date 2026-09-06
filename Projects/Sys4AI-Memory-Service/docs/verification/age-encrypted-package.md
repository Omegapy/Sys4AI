# Age-encrypted provider-neutral package verification

Status: approved path runtime-verified  
Measured: 2026-09-03  
Tool: `age` / `age-keygen` v1.3.2

The approved exchange path builds a deterministic ZIP in memory from sorted
JSON/JSONL members, fixed ZIP metadata, a closed manifest, per-member SHA-256
checksums, and a package digest. It then sends those bytes to the local `age`
executable using a non-shell argument vector and an X25519 public recipient.
The plaintext ZIP is not written to disk by the encrypted export path.

Current executable tests generated temporary identities only under pytest's
disposable directory, encrypted two equivalent packages, decrypted them, and
observed byte-identical inner ZIPs. The outer envelopes differed as expected
from randomized encryption. A restricted fixture record was present after
authorized decryption, absent from ciphertext, and a different identity failed
with a generic error. The public service export path also produced and
validated an encrypted package while retaining provider-neutral records and
provenance.

Private identities, secret-prohibited content, provider-native databases,
model weights, and canonical source files are excluded from the package. No key
or recipient is stored in configuration, source control, Task evidence, logs,
fixtures, or durable memory. Operators supply the public recipient at export
and a separately managed identity file at import. Unencrypted packages remain
limited to explicit disposable tests.

This verification does not authorize sharing an export with an external party,
deployment, product Git operations, or import activation against non-fixture
state.
