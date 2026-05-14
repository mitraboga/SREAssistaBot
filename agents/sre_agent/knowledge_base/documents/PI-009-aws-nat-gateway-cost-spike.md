---
id: PI-009
title: Past Incident - AWS NAT Gateway Data Transfer Cost Spike
type: past_incident
tags: aws, cost, nat-gateway, data-transfer, account, service, usage-type
---

# Past Incident - AWS NAT Gateway Data Transfer Cost Spike

AWS spend increased after a private workload began routing large cross-AZ data
transfers through NAT Gateway.

## What Helped

- Cost Explorer grouped by service and usage type identified NAT Gateway data
  processing.
- Linked account and tag breakdowns identified the workload owner.
- Moving traffic to a private endpoint reduced recurring cost.

## Follow-Up Actions

- Alert on daily NAT Gateway spend.
- Add owner tags to networking resources.
- Review cross-AZ traffic during architecture reviews.

