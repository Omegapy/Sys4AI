# Enforced advanced budgets

The companion `limits` object may select positive integer budgets. A request
override can lower a project budget. Zero, negative, Boolean, unknown, unlimited,
and excessive values are rejected. Core retrieval remains limited to 32,000
bytes; frozen Task packets retain 250,000 bytes and 200 references.

| Budget | Default | Release ceiling |
| --- | ---: | ---: |
| Selected IPC input bytes | 8 MiB | 32 MiB |
| Input RDF triples | 50,000 | 200,000 |
| Query seconds | 10 | 60 |
| Result rows / graph triples | 500 | 5,000 |
| Output bytes including context | 1 MiB | 8 MiB |
| Reasoning seconds | 30 | 120 |
| Derived triples | 100,000 | 400,000 |
| Rule rounds | 128 | 512 |
| Proof nodes | 10,000 | 40,000 |
| Concurrent workers | 2 | 2 |
| Resident memory per worker | 512 MiB | 1 GiB |
| Guard seconds | 5 | 5 |
| Parsed query depth | 64 | 64 |

The parent supervises a separate process group. Darwin `sandbox-exec` denies
network activity and all file data reads except selected runtime/code and
necessary OS loader resources. Selected project data arrives as bounded JSON
through a pipe; the worker cannot open the project corpus. Parser/plugin
registration is closed to the selected in-memory RDF stack. The process starts
with an isolated Python path, without user site initialization or `.pth` files.

The parent samples resident memory with Darwin `proc_pidinfo` while draining
bounded nonblocking output. It kills the whole worker group on excess, timeout,
or cancellation. RSS enforcement is supervised sampling, with measured
overshoot returned in every worker receipt; it is not an exact allocation cap.
Host certification records the actual observed limit and overshoot. Unsupported
confinement or memory observation makes the profile unavailable. File/network
denial is enforced independently by the operating system.

Explicit setup creates two empty runtime slot files. Callers take read-only
advisory locks, so queries do not create or modify persistent state and a host
process failure releases capacity. A single-worker request reserves both slots.
The returned states distinguish capacity exhaustion, resource limits, memory
termination, timeout, cancellation, invalid IPC, and backend failure. Truncated
rows or closure never receive complete-success status.
