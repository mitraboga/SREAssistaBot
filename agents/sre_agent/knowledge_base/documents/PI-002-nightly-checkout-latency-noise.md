---
id: PI-002
title: Past Incident - Nightly Checkout Latency False Pages
type: past_incident
tags: checkout, latency, pager-noise, false-escalation, scheduled-job
---

# Past Incident - Nightly Checkout Latency False Pages

A nightly checkout latency alert paged the on-call team for several days, then
resolved without action. The alert fired during a scheduled batch job and did not
correlate with customer-visible errors or SLO burn.

## What Helped

- The alert was converted from a page to a ticket unless SLO burn or 5xx errors
  appeared at the same time.
- Dedupe grouped repeated alerts by service, region, and scheduled-job window.
- The runbook was updated with the known batch-job window and escalation
  criteria.

## Follow-Up Actions

- Track false escalation count weekly.
- Review alert thresholds after seasonal traffic changes.
- Keep customer-impact checks in the alert description.

