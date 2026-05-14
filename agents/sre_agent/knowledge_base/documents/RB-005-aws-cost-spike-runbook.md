---
id: RB-005
title: AWS Cost Spike Triage Runbook
type: runbook
tags: aws, cost, cost-explorer, budget, service, account, tag, anomaly, nat-gateway
---

# AWS Cost Spike Triage Runbook

Use this runbook when AWS spend increases unexpectedly month over month, week
over week, or day over day.

## First Checks

1. Confirm the time window and compare current month-to-date spend against the
   same number of days in the prior month.
2. Break down cost by service, linked account, region, usage type, and tag.
3. Exclude Support, Tax, credits, Marketplace, and known fixed commitments when
   investigating usage-driven spikes.
4. Check daily trend for a step change after a deploy, migration, data transfer
   event, or workload schedule change.
5. Look for NAT Gateway data processing, inter-AZ transfer, CloudWatch log
   ingestion, S3 request volume, and idle compute.

## Recommendations

- Attach owner and environment tags to untagged cost drivers.
- Create budget alerts for abnormal daily spend and forecasted overrun.
- Prefer private endpoints or same-AZ traffic patterns when NAT cost spikes.
- Review retention on high-ingestion logs.

## Evidence To Cite

- Service, linked account, region, usage type, and tag breakdowns.
- Month-to-date versus previous month comparison.
- Day-by-day trend and step-change date.

