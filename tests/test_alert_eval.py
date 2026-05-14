from evals.run_alert_eval import score_case, summarize


def test_alert_eval_score_case_matches_expected_page_decision():
    result = score_case(
        {
            "id": "nightly",
            "alert_text": "Nightly checkout latency warning resolves without action; no customer impact",
            "service": "checkout",
            "current_severity": "warning",
            "expected_should_page": False,
            "expected_severity": "P4",
            "expected_known_issue": True,
            "baseline_should_page": True,
        }
    )

    assert result["page_correct"] is True
    assert result["severity_correct"] is True


def test_alert_eval_summarize_reports_noise_reduction():
    summary = summarize(
        [
            {
                "baseline_should_page": True,
                "predicted_should_page": False,
                "expected_should_page": False,
                "page_correct": True,
                "severity_correct": True,
                "expected_known_issue": False,
                "known_issue_found": False,
            },
            {
                "baseline_should_page": True,
                "predicted_should_page": True,
                "expected_should_page": True,
                "page_correct": True,
                "severity_correct": True,
                "expected_known_issue": False,
                "known_issue_found": False,
            },
        ]
    )

    assert summary["page_decision_accuracy"] == 1.0
    assert summary["pager_noise_reduction"] == 0.5

