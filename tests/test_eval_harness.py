from evals.run_sre_eval import extract_response_text, score_response, summarize


def test_extract_response_text_from_adk_event_list():
    data = [
        {"content": {"parts": [{"text": "draft"}]}},
        {"content": {"parts": [{"text": "final answer"}]}},
    ]

    assert extract_response_text(data) == "final answer"


def test_score_response_passes_structured_incident_answer():
    scenario = {
        "required_terms": ["incident brief", "summary", "evidence", "rollback"],
        "expected_sections": ["summary", "evidence", "next actions"],
        "action_terms": ["check", "verify", "rollback"],
        "forbidden_terms": ["logs confirm"],
        "min_score": 0.7,
    }
    response = """
    INCIDENT BRIEF
    Summary: checkout has elevated 5xx errors.
    Evidence: check API gateway 5xx, payment error logs, and database saturation.
    Next Actions: verify deploy status and rollback if error rate remains high.
    """

    score = score_response(scenario, response)

    assert score["passed"] is True
    assert score["quality_score"] >= 0.7
    assert score["required_missing"] == []


def test_score_response_flags_unsupported_live_claims():
    scenario = {
        "required_terms": ["incident brief", "summary"],
        "expected_sections": ["summary"],
        "action_terms": ["check"],
        "forbidden_terms": [],
        "min_score": 0.7,
    }
    response = "Incident brief. Summary: logs confirm the database caused it. Check dashboards."

    score = score_response(scenario, response)

    assert "logs confirm" in score["unsupported_live_claims"]
    assert score["quality_score"] < 1.0


def test_summarize_computes_rates_and_latency():
    results = [
        {"ok": True, "latency_seconds": 2.0, "score": {"quality_score": 0.8, "passed": True}},
        {"ok": True, "latency_seconds": 4.0, "score": {"quality_score": 0.6, "passed": False}},
    ]

    summary = summarize(results)

    assert summary["case_count"] == 2
    assert summary["successful_api_calls"] == 2
    assert summary["pass_rate"] == 0.5
    assert summary["average_latency_seconds"] == 3.0
    assert summary["hallucination_proxy_rate"] == summary["unsupported_live_claim_rate"]
