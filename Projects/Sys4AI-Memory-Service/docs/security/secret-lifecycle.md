# Secret and credential lifecycle

Status: binding security contract; no cloud/provider credential is required or
provisioned for the approved first profile

Pattern detection, structured rejection, exception/log redaction, source
exclusion, and package filtering are implemented and exercised with synthetic
fixtures. No credential lifecycle has been run against a live external
provider.

## Prohibited durable content

Passwords, tokens, API keys, cookies, private keys, recovery codes, seed phrases, client secrets, credential-bearing connection strings, and equivalent encoded or encrypted copies must not enter Git, canonical documents, Tasks, fixtures, logs, receipts, exports, provider databases, embeddings, graph properties, or durable memory. `secret-prohibited` is a rejection class, not an encryption request.

## Lifecycle

1. Prefer a no-credential local profile. Do not request a key for a capability that can run locally.
2. For a future credentialed profile, create the credential with the narrowest provider scope, environment, dataset, operation set, and lifetime available.
3. Store the value in an operator-owned OS keychain or managed secret store outside the repository. Tracked configuration may contain only a non-secret reference name after the profile is approved.
4. Resolve the reference at runtime after configuration and permission validation. Inject the value only into the provider process that needs it. Never pass it on a CLI command line.
5. Redact before serialization. Errors, debug output, traces, subprocess environments, crash reports, and support bundles must not copy the value.
6. Rotate on schedule, scope change, personnel/access change, provider recommendation, or suspected exposure. Validate the replacement before revoking the old credential; do not store either value in a receipt.
7. Revoke immediately on confirmed exposure or when the integration is retired. Disable the affected profile, invalidate sessions, and record non-sensitive identifiers, times, scope, and response status.
8. Scan canonical and derived locations after an incident. If prohibited content entered memory, use the privacy-erasure workflow across indexes, provider stores, caches, logs, staging, backups under project control, and exports.

## Discovery and write handling

Filename/path exclusions run before content access where possible. Streaming content detection then runs before normalization, model calls, embedding, logging, or provider ingestion. A detection returns a redacted rule ID, source registration ID, location class, and disposition. It does not echo the matching value.

False-positive review cannot place the candidate value in a Task or control record. Reviewers inspect it through an approved secure channel outside memory artifacts. An allow rule must be narrow, versioned, and must not reclassify an actual credential as safe content.

## Rotation, revocation, and incident evidence

A non-sensitive lifecycle receipt may include credential reference ID, provider, granted scope, creation/rotation/revocation timestamp, actor identity, policy revision, and success/failure. It must exclude the value, reversible encodings, full headers, query strings, and secret-derived low-entropy hashes.

The operator must verify provider-side revocation and local process restart. Deleting a local reference alone is not proof that the remote credential is invalid.

## Local Ollama identity note

The first local Ollama startup reported creating `~/.ollama/id_ed25519`. It is
outside this repository and was not inspected, copied, deleted, or placed in
memory. Treat it as sensitive runtime identity material. Do not register it as
a source, place it in `models/ollama/`, include it in a package, or paste it
into incident records. If rotation is required, stop Ollama and follow an
approved Ollama-specific procedure; a memory-service delete is not sufficient.

See [incident response](incident-response.md) for containment and recovery.
