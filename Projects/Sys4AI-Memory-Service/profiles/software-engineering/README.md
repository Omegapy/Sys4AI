# Software-engineering memory profile

`software-engineering@1` is the first approved derived-agent profile. It extends
`base@1` without changing the public memory API, and adds Python AST-backed code,
test, build-target, and failure-pattern records plus software-specific relation
declarations.

The profile owns only deterministic classification and profile policy. Canonical
source files remain authoritative, a profile cannot grant itself permission, and
provider output cannot promote source authority. The caller must explicitly
supply `SoftwareEngineeringPythonAdapter`; no global adapter or provider state is
changed by loading the profile.
