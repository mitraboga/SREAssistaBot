"""Contract tests for React's deterministic tool endpoints (no model/DB required)."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from agents.sre_agent.web_api import router


@pytest.fixture
def client():
    """Create an isolated API using the same router mounted in serve.py.

    Returns:
        Synchronous test client with the real knowledge and classification tools.
    """
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_corpus_metadata_and_document_body(client):
    """List the corpus and read a known runbook by citation ID."""
    response = client.get("/workspace/knowledge")
    assert response.status_code == 200
    documents = response.json()["documents"]
    assert len(documents) == 24
    assert all("path" not in document for document in documents)
    response = client.get("/workspace/knowledge/RB-001")
    assert response.status_code == 200
    assert "checkout" in response.json()["body"].lower()
    assert "path" not in response.json()


def test_search_matches_agent_retrieval_and_hides_paths(client):
    """Return ranked citation matches from the real retriever."""
    response = client.get(
        "/workspace/knowledge/search",
        params={"query": "checkout 5xx payment failures in NA", "top_k": 3},
    )
    assert response.status_code == 200
    results = response.json()["results"]
    assert len(results) == 3
    assert results[0]["source_id"] in {"RB-001", "PI-001"}
    assert all("path" not in result for result in results)


@pytest.mark.parametrize("query", ["", "  ", "x" * 2001])
def test_rejects_invalid_search_input(client, query):
    """Reject empty or oversized queries."""
    assert client.get("/workspace/knowledge/search", params={"query": query}).status_code == 422


def test_empty_retrieval_and_missing_document(client):
    """Handle unmatched text and unknown document IDs."""
    response = client.get("/workspace/knowledge/search", params={"query": "zzzxxyy"})
    assert response.json()["results"] == []
    assert client.get("/workspace/knowledge/NOT-A-SOURCE").status_code == 404
    assert client.get("/workspace/knowledge/%2E%2E%2Fsettings.py").status_code == 404


def test_alert_classification_uses_real_tool(client):
    """Recommend a page for impact and a quiet route for nightly noise."""
    response = client.post(
        "/workspace/alerts/classify",
        json={
            "alert_text": "Checkout 5xx payment failures and customer complaints in NA",
            "service": "checkout-api",
        },
    )
    assert response.status_code == 200
    result = response.json()
    assert result["should_page"] is True
    assert result["recommended_route"] == "page_oncall"
    assert "path" not in result["known_issue"]
    response = client.post(
        "/workspace/alerts/classify",
        json={"alert_text": "Nightly checkout latency is self-resolving with no customer impact"},
    )
    assert response.json()["should_page"] is False


@pytest.mark.parametrize("text", ["", "  ", "x" * 10001])
def test_rejects_invalid_alert_input(client, text):
    """Prevent malformed alert requests from reaching the classifier."""
    assert client.post("/workspace/alerts/classify", json={"alert_text": text}).status_code == 422


def test_rejects_oversized_fields_and_top_k(client):
    """Bound optional form fields and retrieval limits."""
    assert (
        client.post(
            "/workspace/alerts/classify", json={"alert_text": "signal", "service": "x" * 121}
        ).status_code
        == 422
    )
    assert (
        client.get(
            "/workspace/knowledge/search", params={"query": "checkout", "top_k": 11}
        ).status_code
        == 422
    )
