from agents.sre_agent.tools.alert_intelligence import classify_alert_for_escalation


def test_checkout_customer_impact_pages_oncall():
    result = classify_alert_for_escalation(
        "Checkout 5xx spike in NA with payment failures and customer complaints",
        service="checkout",
        current_severity="P2",
    )

    assert result["should_page"] is True
    assert result["recommended_severity"] == "P2"
    assert result["recommended_route"] == "page_oncall"
    assert result["known_issue"]


def test_nightly_self_resolving_alert_is_deflected():
    result = classify_alert_for_escalation(
        "Nightly checkout latency warning pages every night and resolves without action; no customer impact",
        service="checkout",
        current_severity="warning",
    )

    assert result["should_page"] is False
    assert result["recommended_severity"] == "P4"
    assert result["recommended_route"] in {"dedupe_known_issue", "ticket"}
    assert result["known_issue"]

