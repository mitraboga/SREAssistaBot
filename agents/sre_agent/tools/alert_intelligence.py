"""Deterministic alert classification and pager-noise scoring."""

from __future__ import annotations

import re
from typing import Any

from .knowledge_base import retrieve_documents


HIGH_IMPACT_TERMS = {
    "5xx",
    "payment",
    "payments",
    "customer impact",
    "customers affected",
    "complaint",
    "complaints",
    "outage",
    "failed",
    "failures",
    "failed orders",
    "revenue",
    "p1",
    "sev1",
    "critical",
}
LOW_IMPACT_TERMS = {
    "dev environment",
    "nightly",
    "non-production",
    "scheduled",
    "self-resolving",
    "self resolving",
    "no customer impact",
    "sandbox",
    "single user",
    "staging",
    "warning",
    "ticket",
    "noise",
    "flapping",
}
TRANSIENT_TERMS = {"resolved", "recovers", "recovered", "intermittent", "flap", "flapping"}


def _contains_any(text: str, terms: set[str]) -> bool:
    return any(term in text for term in terms)


def _normalize_severity(severity: str) -> str:
    normalized = severity.strip().lower().replace("sev", "p")
    if normalized in {"critical", "page", "urgent"}:
        return "p1"
    if normalized in {"warning", "warn"}:
        return "p3"
    return normalized


def _dedupe_key(alert_text: str, service: str) -> str:
    region_match = re.search(r"\b(na|eu|apac|us-east-1|us-west-2|global)\b", alert_text.lower())
    symptom = "latency"
    if "5xx" in alert_text.lower() or "error" in alert_text.lower():
        symptom = "5xx"
    if "payment" in alert_text.lower():
        symptom = "payment"
    region = region_match.group(1) if region_match else "unknown-region"
    return f"{service or 'unknown-service'}:{region}:{symptom}"


def classify_alert_for_escalation(
    alert_text: str,
    service: str = "",
    current_severity: str = "",
) -> dict[str, Any]:
    """Classify whether an operational alert should page, ticket, or dedupe.

    Args:
        alert_text: Alert title, page text, or incident symptom.
        service: Optional service name.
        current_severity: Optional incoming severity such as P1, P2, warning.

    Returns:
        Escalation decision, confidence, dedupe key, and known-issue context.
    """
    text_lower = alert_text.lower()
    severity = _normalize_severity(current_severity)
    no_customer_impact = (
        "no customer impact" in text_lower
        or "without customer impact" in text_lower
        or "not customer-impacting" in text_lower
    )
    non_production = bool(
        re.search(r"\b(dev|development|staging|sandbox|non-production)\b", text_lower)
    )
    has_high_impact = _contains_any(text_lower, HIGH_IMPACT_TERMS)
    has_low_impact = _contains_any(text_lower, LOW_IMPACT_TERMS)
    is_transient = _contains_any(text_lower, TRANSIENT_TERMS)

    known_matches = retrieve_documents(alert_text, top_k=3)
    known_issue = known_matches[0] if known_matches and known_matches[0]["confidence"] >= 0.35 else None

    if severity == "p1" or (has_high_impact and not (no_customer_impact or non_production)):
        recommended_severity = "P2"
        should_page = True
        route = "page_oncall"
        reason = "customer-impacting or revenue-sensitive signal"
    elif severity == "p2" and not (has_low_impact or no_customer_impact or non_production):
        recommended_severity = "P2"
        should_page = True
        route = "page_oncall"
        reason = "incoming severity requires paging until impact is ruled out"
    elif has_low_impact or is_transient or no_customer_impact or non_production:
        recommended_severity = "P4"
        should_page = False
        route = "dedupe_known_issue" if known_issue else "ticket"
        reason = "known, low-impact, or self-resolving alert pattern"
    elif known_issue:
        recommended_severity = "P3"
        should_page = False
        route = "dedupe_known_issue"
        reason = "known issue that should be tracked without paging"
    else:
        recommended_severity = "P3"
        should_page = False
        route = "watch"
        reason = "needs investigation but does not yet show customer impact"

    if (has_low_impact or no_customer_impact or non_production) and severity != "p1":
        should_page = False
        route = "dedupe_known_issue" if known_issue else "ticket"
        recommended_severity = "P4"

    confidence = 0.55
    if has_high_impact:
        confidence += 0.25
    if has_low_impact or is_transient:
        confidence += 0.15
    if known_issue:
        confidence += 0.10

    return {
        "status": "success",
        "alert_text": alert_text,
        "service": service,
        "incoming_severity": current_severity,
        "recommended_severity": recommended_severity,
        "should_page": should_page,
        "recommended_route": route,
        "dedupe_key": _dedupe_key(alert_text, service),
        "reason": reason,
        "confidence": round(min(confidence, 0.95), 3),
        "known_issue": known_issue,
        "next_checks": [
            "Confirm customer impact and SLO burn before changing route.",
            "Check whether the alert has a runbook and owner.",
            "Measure false escalation count before and after tuning.",
        ],
    }
