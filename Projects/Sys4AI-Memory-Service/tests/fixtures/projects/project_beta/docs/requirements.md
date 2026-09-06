# Polar Relay Beta requirements

## Requirement REQ-BETA-042

The polar telemetry relay shall preserve the exact route label `BETA-ROUTE-7C4B` and return this heading as its canonical source anchor.

## Runtime state boundary

A remembered task summary may help locate the task, but an execution action must reread and validate `control/task.yaml`. Cached memory alone cannot mark the task complete.

## Shared calibration window

Fixture Beta performs the shared calibration window at 10:45 UTC and uses the Beta checksum policy.
