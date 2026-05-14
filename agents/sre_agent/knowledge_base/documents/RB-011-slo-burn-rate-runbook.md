---
id: RB-011
title: SLO Burn Rate And Error Budget Runbook
type: runbook
tags: slo, burn-rate, error-budget, alerting, availability, latency, paging
---

# SLO Burn Rate And Error Budget Runbook

Use this runbook to review whether an alert should page based on customer impact,
SLO burn, and error budget consumption.

## Review Steps

1. Define the user-visible SLI: availability, latency, correctness, durability,
   or freshness.
2. Calculate short-window and long-window burn rate before paging.
3. Separate symptoms that affect users from internal-only saturation or noisy
   warning thresholds.
4. Page when fast burn threatens the objective; create tickets for slow burn or
   non-customer-impacting issues.
5. Track false escalations, missed pages, alert fatigue, and time to
   acknowledgment.

## Evidence To Cite

- SLI numerator and denominator.
- Error budget consumed.
- Short-window and long-window burn rate.
- Customer impact and false escalation count.

