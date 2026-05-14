"""Local runbook and past-incident retrieval for SRE answers."""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any


DEFAULT_DOCUMENT_DIR = Path(__file__).resolve().parents[1] / "knowledge_base" / "documents"
TOKEN_PATTERN = re.compile(r"[a-z0-9][a-z0-9-]{1,}")
STOP_WORDS = {
    "about",
    "after",
    "again",
    "against",
    "and",
    "any",
    "are",
    "before",
    "but",
    "can",
    "for",
    "from",
    "give",
    "has",
    "have",
    "how",
    "into",
    "not",
    "now",
    "our",
    "out",
    "the",
    "then",
    "this",
    "that",
    "what",
    "when",
    "where",
    "with",
    "without",
    "would",
    "you",
}


@dataclass(frozen=True)
class KnowledgeDocument:
    """Parsed local knowledge-base document."""

    source_id: str
    title: str
    document_type: str
    tags: tuple[str, ...]
    path: Path
    body: str
    tokens: tuple[str, ...]
    term_counts: Counter[str]

    @property
    def citation(self) -> str:
        return f"[{self.source_id}]"


def tokenize(text: str) -> list[str]:
    """Tokenize text for deterministic lexical retrieval."""
    return [
        token
        for token in TOKEN_PATTERN.findall(text.lower())
        if token not in STOP_WORDS and len(token) > 1
    ]


def _split_metadata(raw_text: str) -> tuple[dict[str, str], str]:
    if not raw_text.startswith("---"):
        return {}, raw_text

    parts = raw_text.split("---", 2)
    if len(parts) < 3:
        return {}, raw_text

    metadata: dict[str, str] = {}
    for line in parts[1].splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip().lower()] = value.strip()

    return metadata, parts[2].strip()


def _parse_document(path: Path) -> KnowledgeDocument:
    raw_text = path.read_text(encoding="utf-8")
    metadata, body = _split_metadata(raw_text)
    source_id = metadata.get("id") or path.stem.upper()
    title = metadata.get("title") or path.stem.replace("-", " ").title()
    document_type = metadata.get("type") or "document"
    tags = tuple(tag.strip().lower() for tag in metadata.get("tags", "").split(",") if tag.strip())

    token_source = " ".join([source_id, title, " ".join(tags), body])
    tokens = tuple(tokenize(token_source))
    return KnowledgeDocument(
        source_id=source_id,
        title=title,
        document_type=document_type,
        tags=tags,
        path=path,
        body=body,
        tokens=tokens,
        term_counts=Counter(tokens),
    )


@lru_cache(maxsize=1)
def load_knowledge_documents(document_dir: str | None = None) -> tuple[KnowledgeDocument, ...]:
    """Load local runbook and past-incident documents."""
    base_dir = Path(document_dir) if document_dir else DEFAULT_DOCUMENT_DIR
    if not base_dir.exists():
        return ()

    documents = [_parse_document(path) for path in sorted(base_dir.glob("*.md"))]
    return tuple(documents)


def _idf_by_token(documents: tuple[KnowledgeDocument, ...]) -> dict[str, float]:
    doc_count = len(documents)
    document_frequency: Counter[str] = Counter()
    for document in documents:
        document_frequency.update(set(document.tokens))

    return {
        token: math.log((doc_count + 1) / (frequency + 0.5)) + 1.0
        for token, frequency in document_frequency.items()
    }


def _score_document(query_tokens: list[str], document: KnowledgeDocument, idf: dict[str, float]) -> float:
    if not query_tokens:
        return 0.0

    query_counts = Counter(query_tokens)
    score = 0.0
    for token, query_count in query_counts.items():
        term_count = document.term_counts.get(token, 0)
        if not term_count:
            continue
        term_weight = 1.0 + math.log(term_count)
        score += query_count * term_weight * idf.get(token, 1.0)

        if token in document.title.lower():
            score += 1.5
        if token in document.tags:
            score += 2.0

    coverage = len(set(query_tokens) & set(document.tokens)) / max(len(set(query_tokens)), 1)
    return score * (0.75 + coverage)


def _make_snippet(document: KnowledgeDocument, query_tokens: list[str], max_chars: int = 420) -> str:
    paragraphs = [paragraph.strip() for paragraph in document.body.split("\n\n") if paragraph.strip()]
    if not paragraphs:
        return ""

    query_set = set(query_tokens)
    best = max(paragraphs, key=lambda paragraph: len(query_set & set(tokenize(paragraph))))
    best = re.sub(r"\s+", " ", best)
    if len(best) <= max_chars:
        return best
    return best[: max_chars - 3].rstrip() + "..."


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(Path.cwd()))
    except ValueError:
        return str(path)


def retrieve_documents(query: str, top_k: int = 5) -> list[dict[str, Any]]:
    """Retrieve local documents for evals and tools."""
    documents = load_knowledge_documents()
    query_tokens = tokenize(query)
    if not documents or not query_tokens:
        return []

    idf = _idf_by_token(documents)
    scored = [
        (_score_document(query_tokens, document, idf), document)
        for document in documents
    ]
    scored = [(score, document) for score, document in scored if score > 0]
    scored.sort(key=lambda item: item[0], reverse=True)

    if not scored:
        return []

    max_score = scored[0][0]
    results: list[dict[str, Any]] = []
    for rank, (score, document) in enumerate(scored[: max(1, min(top_k, 10))], start=1):
        normalized = score / max(max_score, 0.001)
        confidence = max(0.10, min(0.99, normalized))
        results.append(
            {
                "rank": rank,
                "source_id": document.source_id,
                "citation": document.citation,
                "title": document.title,
                "type": document.document_type,
                "tags": list(document.tags),
                "path": _display_path(document.path),
                "score": round(score, 3),
                "confidence": round(confidence, 3),
                "snippet": _make_snippet(document, query_tokens),
            }
        )

    return results


def search_knowledge_base(query: str, top_k: int = 5) -> dict[str, Any]:
    """Search local SRE runbooks and past incidents.

    Args:
        query: Operational question, incident symptom, alert text, or design topic.
        top_k: Maximum number of documents to return.

    Returns:
        A structured retrieval result with source citations and confidence scores.
    """
    results = retrieve_documents(query=query, top_k=top_k)
    if not results:
        return {
            "status": "empty",
            "query": query,
            "message": "No local runbook or past-incident match found.",
            "results": [],
        }

    return {
        "status": "success",
        "query": query,
        "result_count": len(results),
        "results": results,
        "citation_instructions": (
            "When using these results, cite source_id values inline, for example [RB-001]."
        ),
    }
