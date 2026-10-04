"""Read-only endpoints exposing existing SRE tools to the React workspace."""

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, field_validator

from .tools.alert_intelligence import classify_alert_for_escalation
from .tools.knowledge_base import load_knowledge_documents, search_knowledge_base

router = APIRouter(prefix="/workspace", tags=["workspace"])


class AlertRequest(BaseModel):
    """Validated alert input; all classification remains server-side."""

    alert_text: str = Field(min_length=1, max_length=10000)
    service: str = Field(default="", max_length=120)
    current_severity: str = Field(default="", max_length=20)

    @field_validator("alert_text")
    @classmethod
    def reject_blank_alert(cls, value: str) -> str:
        """Reject whitespace-only alert descriptions.

        Args:
            value: Submitted alert text.

        Returns:
            Trimmed alert text.
        """
        if not value.strip():
            raise ValueError("Alert text must contain a description.")
        return value.strip()


@router.get("/knowledge")
def list_knowledge() -> dict[str, Any]:
    """List the configured corpus without exposing filesystem paths.

    Returns:
        Source IDs, titles, types and tags for the local corpus.
    """
    documents = load_knowledge_documents()
    return {
        "documents": [
            {
                "source_id": document.source_id,
                "title": document.title,
                "type": document.document_type,
                "tags": list(document.tags),
            }
            for document in documents
        ]
    }


@router.get("/knowledge/search")
def search_knowledge(
    query: str = Query(min_length=1, max_length=2000),
    top_k: int = Query(default=5, ge=1, le=10),
) -> dict[str, Any]:
    """Search with the same deterministic retriever used by the agent.

    Args:
        query: Operational symptoms or topic.
        top_k: Maximum results.

    Returns:
        Ranked citations, snippets and retrieval confidence scores.
    """
    if not query.strip():
        raise HTTPException(status_code=422, detail="Enter a search query.")
    result = search_knowledge_base(query.strip(), top_k)
    for item in result["results"]:
        item.pop("path", None)
    return result


@router.get("/knowledge/{source_id}")
def get_knowledge(source_id: str) -> dict[str, Any]:
    """Read a corpus document by its known ID, never an arbitrary path.

    Args:
        source_id: Corpus citation ID such as RB-001.

    Returns:
        Metadata and Markdown body of the matching document.
    """
    for document in load_knowledge_documents():
        if document.source_id == source_id:
            return {
                "source_id": document.source_id,
                "title": document.title,
                "type": document.document_type,
                "tags": list(document.tags),
                "body": document.body,
            }
    raise HTTPException(status_code=404, detail="Knowledge source not found.")


@router.post("/alerts/classify")
def classify_alert(payload: AlertRequest) -> dict[str, Any]:
    """Return a routing recommendation without dispatching an actual page.

    Args:
        payload: Validated alert text and optional service/severity.

    Returns:
        Existing deterministic classification, reasoning and known-issue context.
    """
    result = classify_alert_for_escalation(**payload.model_dump())
    if result["known_issue"]:
        result["known_issue"].pop("path", None)
    return result
