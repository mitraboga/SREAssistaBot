---
id: PI-001
title: Past Incident - NA Checkout 5xx From Payment Provider Timeouts
type: past_incident
tags: checkout, payments, na, provider-timeout, 5xx, rollback
---

# Past Incident - NA Checkout 5xx From Payment Provider Timeouts

During a previous North America checkout incident, API gateway 5xx errors rose
with payment authorization timeouts. Customer complaints were concentrated in NA.

## What Helped

- Comparing gateway 5xx by region isolated impact to NA.
- Payment timeout errors increased before Postgres saturation symptoms.
- A temporary feature flag reduced calls to the affected provider path.
- Customer communications avoided naming a root cause until provider evidence
  was confirmed.

## Follow-Up Actions

- Add payment provider timeout dashboards.
- Keep idempotency checks in the rollback validation checklist.
- Include support macros for failed payment and duplicate-charge reports.

