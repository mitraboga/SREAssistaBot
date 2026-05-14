---
id: PI-007
title: Past Incident - Notification Queue Backlog From Worker Saturation
type: past_incident
tags: queue, backlog, workers, sqs, retries, dead-letter, notifications
---

# Past Incident - Notification Queue Backlog From Worker Saturation

Notification delivery was delayed after a downstream provider slowed down.
Workers retried aggressively and oldest message age increased.

## What Helped

- Oldest message age showed user-visible delay more clearly than queue depth.
- Dead-letter volume identified poison messages.
- Rate-limiting producers stopped retries from overwhelming the provider.

## Follow-Up Actions

- Add retry budget and jitter.
- Alert on oldest message age.
- Add dead-letter owner and replay procedure.

