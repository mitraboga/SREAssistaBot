---
id: PI-010
title: Past Incident - Fast SLO Burn From API 5xx Spike
type: past_incident
tags: slo, burn-rate, api, 5xx, error-budget, paging
---

# Past Incident - Fast SLO Burn From API 5xx Spike

An API 5xx spike consumed error budget quickly. The old threshold alert fired
late, while the burn-rate dashboard showed user impact earlier.

## What Helped

- Short-window and long-window burn-rate alerts identified severity.
- Error budget consumed made the escalation decision clear.
- A rollback reduced 5xx before the next customer update.

## Follow-Up Actions

- Replace static 5xx threshold pages with multi-window burn-rate alerts.
- Include SLO burn in incident severity guidance.
- Track missed page and false escalation rates.

