from evals.run_rag_eval import reciprocal_rank, score_query, summarize


def test_reciprocal_rank_scores_first_relevant_match():
    assert reciprocal_rank(["X", "RB-001", "PI-001"], {"RB-001"}) == 0.5
    assert reciprocal_rank(["X", "Y"], {"RB-001"}) == 0.0


def test_score_query_reports_hit_and_citations():
    result = score_query(
        {
            "id": "checkout",
            "query": "checkout 5xx payment failures customer complaints",
            "relevant_ids": ["RB-001"],
        },
        top_k=5,
    )

    assert result["hit_at_3"] is True
    assert "[RB-001]" in result["citations"]


def test_rag_summarize_computes_metrics():
    summary = summarize(
        [
            {
                "hit_at_1": True,
                "hit_at_3": True,
                "hit_at_5": True,
                "reciprocal_rank": 1.0,
                "citation_precision_at_3": 0.333,
                "citation_precision_at_5": 0.2,
                "top_relevant_confidence": 0.9,
            }
        ]
    )

    assert summary["hit_at_1"] == 1.0
    assert summary["mrr"] == 1.0

