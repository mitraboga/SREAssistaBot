---
id: RB-006
title: Deploy Rollback And Feature Flag Runbook
type: runbook
tags: deploy, rollback, canary, feature-flag, release, error-rate, latency
---

# Deploy Rollback And Feature Flag Runbook

Use this runbook when an incident may be connected to a recent deploy, canary,
configuration change, or feature flag.

## Read-Only Checks

1. Compare error rate, latency, saturation, and business metrics before and
   after the deploy timestamp.
2. Check whether the impact is limited to the new version, canary cohort, region,
   or feature-flag audience.
3. Confirm database migrations, schema compatibility, config changes, and
   dependency version changes.
4. Validate whether rollback is safe for data compatibility and idempotency.

## Rollback Criteria

Rollback, disable the feature flag, or halt rollout when the new version is in
the incident window and error rate, latency, or customer impact remains elevated
after low-risk mitigations.

## Evidence To Cite

- Deploy timeline and version split.
- Canary versus stable metrics.
- Feature flag exposure.
- Rollback validation checklist.

