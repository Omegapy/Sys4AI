# Polar Relay Alpha requirements

## Requirement REQ-ALPHA-042

The polar telemetry relay shall preserve the exact route label `ALPHA-ROUTE-9F2A` and return this heading as its canonical source anchor.

## Runtime state boundary

A remembered task summary may help locate the task, but an execution action must reread and validate `control/task.yaml`. Cached memory alone cannot mark the task complete.

## Shared calibration window

Fixture Alpha performs the shared calibration window at 09:15 UTC and uses the Alpha checksum policy.
