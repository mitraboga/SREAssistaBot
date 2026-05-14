---
id: RB-013
title: AWS Core Infrastructure Triage Runbook
type: runbook
tags: aws, ec2, rds, s3, iam, connectivity, region, load-balancer, security-group
---

# AWS Core Infrastructure Triage Runbook

Use this runbook when AWS infrastructure may be contributing to an incident.

## Read-Only Checks

1. Confirm caller identity, account, region, and assumed role before checking
   resources.
2. Review load balancer target health, security group changes, route tables, and
   DNS records.
3. Check EC2 instance health, autoscaling events, and recent deployment activity.
4. Check RDS status, failover events, connection count, and storage saturation.
5. Check S3 4xx/5xx, bucket policy changes, and access denied errors.

## Safety Notes

Prefer describe/list/status calls first. Do not change IAM, networking, or
database configuration without explicit confirmation and rollback plan.

## Evidence To Cite

- Account and region.
- Load balancer target health.
- EC2/RDS/S3 status.
- Recent IAM, security group, or route changes.

