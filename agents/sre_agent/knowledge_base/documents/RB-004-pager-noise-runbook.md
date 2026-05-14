---
id: RB-004
title: Pager Noise And Alert Deflection Runbook
type: runbook
tags: pager-noise, alerts, dedupe, burn-rate, slo, runbook, alert-quality
---

# Pager Noise And Alert Deflection Runbook

Use this runbook when an alert repeatedly pages but resolves without action or
does not represent customer impact.

## Alert Review

1. Separate paging alerts from ticket-only or dashboard-only alerts.
2. Measure whether the alert correlates with SLO burn, customer impact, error
   budget consumption, or operator action.
3. Add dedupe keys for service, region, dependency, and symptom so one incident
   does not create many pages.
4. Use multi-window burn-rate alerts for availability and latency SLOs instead
   of single-sample threshold pages.
5. Route known recurring low-impact alerts to a ticket with runbook context,
   while preserving pages for high-severity customer impact.

## Deflection Criteria

An alert can be deflected from paging when it is known, self-resolving, has no
customer impact, and has a ticket/runbook owner.

## Evidence To Cite

- Page volume before and after tuning.
- False escalation count.
- SLO burn rate and customer impact.
- Dedupe key effectiveness.

