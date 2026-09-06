# Verification fixtures

This directory contains synthetic, non-production source material for adapter, lifecycle, security, and project-isolation tests. `projects/project_alpha` and `projects/project_beta` have the same format mix and similar language but different project and record identities. A correct implementation must retain those boundaries.

All instruction-like security content is explicitly labeled `untrusted` and is test data, never governance. No fixture contains a real or realistic credential. A secret-detection test that needs a pattern must create it only in an isolated runtime temporary directory and must not persist the value in logs, snapshots, receipts, or repository files.

Lifecycle snapshots preserve test copies of moved, changed, and deleted sources so expected reconciliation can be checked without deleting repository content.
