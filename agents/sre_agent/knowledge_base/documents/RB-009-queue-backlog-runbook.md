---
id: RB-009
title: Queue Backlog And Worker Saturation Runbook
type: runbook
tags: queue, backlog, workers, kafka, sqs, consumer-lag, retries, dead-letter
---

# Queue Backlog And Worker Saturation Runbook

Use this runbook when asynchronous processing is delayed, consumer lag grows, or
dead-letter queues increase.

## Read-Only Checks

1. Check backlog depth, consumer lag, oldest message age, retry rate, and
   dead-letter queue volume.
2. Compare producer rate versus consumer throughput and worker saturation.
3. Identify poison messages, schema changes, downstream dependency failures, and
   retry storms.
4. Verify autoscaling limits, worker concurrency, and partition assignment.

## Mitigation Options

- Pause or rate-limit non-critical producers.
- Move poison messages to a quarantine path with owner approval.
- Scale workers only after checking downstream capacity.

## Evidence To Cite

- Backlog depth and oldest message age.
- Consumer lag and worker saturation.
- Dead-letter queue trend and retry reason.

