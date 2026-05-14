from agents.sre_agent.tools.knowledge_base import retrieve_documents, search_knowledge_base, tokenize


def test_tokenize_removes_common_stop_words():
    assert "checkout" in tokenize("What should we do for checkout 5xx?")
    assert "what" not in tokenize("What should we do for checkout 5xx?")


def test_search_knowledge_base_returns_citations_for_checkout_incident():
    result = search_knowledge_base(
        "checkout 5xx payment failures in NA with customer complaints",
        top_k=3,
    )

    assert result["status"] == "success"
    assert result["results"]
    assert result["results"][0]["source_id"] in {"RB-001", "PI-001"}
    assert result["results"][0]["citation"].startswith("[")
    assert result["results"][0]["confidence"] > 0


def test_retrieve_documents_matches_pager_noise_docs():
    results = retrieve_documents(
        "nightly checkout latency alert resolves without action reduce pager noise",
        top_k=3,
    )

    source_ids = {result["source_id"] for result in results}
    assert {"RB-004", "PI-002"} & source_ids

