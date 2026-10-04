import { useEffect, useState } from "react";
import { ArrowUpRight, BookOpen, FileText, Search, X } from "lucide-react";
import { useSearchParams } from "react-router-dom";
import { Badge, ErrorNotice, Markdown } from "../components/ui";
import { demoDocuments, demoSearch } from "../lib/demo";
import { liveApi } from "../lib/api";
import { useWorkspace } from "../lib/workspace";
import type {
  DocumentSummary,
  KnowledgeDocument,
  SearchResult,
} from "../lib/types";

export function Knowledge() {
  const { mode } = useWorkspace();
  const [params, setParams] = useSearchParams();
  const sourceId = params.get("source");
  const [documents, setDocuments] = useState<DocumentSummary[]>(
    mode === "demo" ? demoDocuments : [],
  );
  const [query, setQuery] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [results, setResults] = useState<SearchResult[] | null>(null);
  const [type, setType] = useState("all");
  const [detail, setDetail] = useState<KnowledgeDocument | null>(null);
  const [error, setError] = useState("");
  const [detailError, setDetailError] = useState("");
  const [loading, setLoading] = useState(mode === "live");
  const [detailLoading, setDetailLoading] = useState(false);
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    setError("");
    setLoading(true);
    if (!searchQuery) {
      setResults(null);
      const load =
        mode === "demo"
          ? Promise.resolve({ documents: demoDocuments })
          : liveApi.documents();
      void load
        .then((data) => {
          if (!controller.signal.aborted) setDocuments(data.documents);
        })
        .catch((failure) => {
          if (!controller.signal.aborted) setError(failure.message);
        })
        .finally(() => {
          if (!controller.signal.aborted) setLoading(false);
        });
    } else {
      const load =
        mode === "demo"
          ? Promise.resolve({ results: demoSearch(searchQuery) })
          : liveApi.search(searchQuery, controller.signal);
      void load
        .then((data) => {
          if (!controller.signal.aborted) setResults(data.results);
        })
        .catch((failure) => {
          if (!controller.signal.aborted) setError(failure.message);
        })
        .finally(() => {
          if (!controller.signal.aborted) setLoading(false);
        });
    }
    return () => controller.abort();
  }, [mode, searchQuery, retry]);
  useEffect(() => {
    const controller = new AbortController();
    setDetail(null);
    setDetailError("");
    setDetailLoading(Boolean(sourceId));
    if (sourceId) {
      const load =
        mode === "demo"
          ? Promise.resolve(
              demoDocuments.find((item) => item.source_id === sourceId),
            )
          : liveApi.document(sourceId, controller.signal);
      void load
        .then((data) => {
          if (!controller.signal.aborted) {
            if (!data) throw new Error("Knowledge source not found.");
            setDetail(data);
          }
        })
        .catch((failure) => {
          if (!controller.signal.aborted) setDetailError(failure.message);
        })
        .finally(() => {
          if (!controller.signal.aborted) setDetailLoading(false);
        });
    }
    return () => controller.abort();
  }, [mode, sourceId, retry]);
  const shown = (results || documents).filter(
    (item) => type === "all" || item.type === type,
  );
  return (
    <>
      <div className="page-heading">
        <div>
          <p className="eyebrow">EVIDENCE BEFORE ASSUMPTIONS</p>
          <h1>Knowledge base</h1>
          <p>
            Find the runbook. Learn from the last incident. Keep the source
            close.
          </p>
        </div>
        <Badge tone="neutral">
          {mode === "demo" ? "Repository snapshot" : "Backend corpus"}
        </Badge>
      </div>
      <section className="knowledge-search panel">
        <BookOpen size={23} />
        <div>
          <h2>Your operational memory</h2>
          <p>
            Runbooks and past incidents from the project’s anonymized corpus.
          </p>
        </div>
        <form
          onSubmit={(event) => {
            event.preventDefault();
            setSearchQuery(query.trim());
          }}
          className="knowledge-search-form"
        >
          <label className="search-field">
            <Search size={17} />
            <input
              aria-label="Search knowledge base"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Try ‘checkout 5xx’ or ‘Postgres saturation’"
              maxLength={2000}
            />
          </label>
          <button type="submit" className="primary">
            Search
          </button>
        </form>
      </section>
      <div className="knowledge-grid">
        <section>
          <div className="knowledge-toolbar">
            <div className="tab-buttons" aria-label="Document type">
              {[
                ["all", "All sources"],
                ["runbook", "Runbooks"],
                ["past_incident", "Past incidents"],
              ].map(([value, label]) => (
                <button
                  key={value}
                  aria-pressed={type === value}
                  className={type === value ? "active" : ""}
                  onClick={() => setType(value)}
                >
                  {label}
                </button>
              ))}
            </div>
            {searchQuery && (
              <button
                className="text-button"
                onClick={() => {
                  setQuery("");
                  setSearchQuery("");
                }}
              >
                <X size={13} />
                Clear search
              </button>
            )}
          </div>
          {error && (
            <>
              <ErrorNotice message={error} />
              <button
                className="secondary"
                onClick={() => setRetry((value) => value + 1)}
              >
                Retry
              </button>
            </>
          )}
          {loading ? (
            <div className="panel empty-state" role="status">
              <span className="spinner" />
              <p>Loading knowledge sources…</p>
            </div>
          ) : (
            <>
              <p className="result-count">
                {shown.length} sources
                {searchQuery ? ` for “${searchQuery}”` : ""}
              </p>
              <div className="document-grid">
                {shown.map((item) => {
                  const result = item as SearchResult;
                  return (
                    <button
                      key={item.source_id}
                      className={`document-card panel ${sourceId === item.source_id ? "active" : ""}`}
                      onClick={() => setParams({ source: item.source_id })}
                    >
                      <div className="document-card-top">
                        <span className="document-icon">
                          {item.type === "runbook" ? (
                            <BookOpen size={20} />
                          ) : (
                            <FileText size={20} />
                          )}
                        </span>
                        <span className="mono muted">{item.source_id}</span>
                        <ArrowUpRight size={16} />
                      </div>
                      <h3>{item.title}</h3>
                      <div className="tags">
                        {item.tags.slice(0, 3).map((tag) => (
                          <Badge key={tag} tone="neutral">
                            {tag}
                          </Badge>
                        ))}
                      </div>
                      {result.snippet && <p>{result.snippet}</p>}
                      {typeof result.confidence === "number" && (
                        <small>
                          Retrieval score: {Math.round(result.confidence * 100)}
                          %{" "}
                          {mode === "demo"
                            ? "(demo keyword overlap)"
                            : "(relative match)"}
                        </small>
                      )}
                    </button>
                  );
                })}
              </div>
              {!shown.length && (
                <div className="panel empty-state">
                  <Search size={24} />
                  <h3>No matching sources</h3>
                  <p>Try a service name, symptom, or broader search.</p>
                </div>
              )}
            </>
          )}
        </section>
        <aside
          className="panel knowledge-detail"
          aria-label="Knowledge source details"
        >
          <div className="panel-heading">
            <h2>{detail?.source_id || "Source preview"}</h2>
            {detail && (
              <Badge tone="green">
                {detail.type === "runbook" ? "Runbook" : "Past incident"}
              </Badge>
            )}
          </div>
          {detailError ? (
            <>
              <ErrorNotice message={detailError} />
              <button
                className="secondary"
                onClick={() => setRetry((value) => value + 1)}
              >
                Retry source
              </button>
            </>
          ) : detailLoading ? (
            <div className="empty-state" role="status">
              <span className="spinner" />
              <p>Loading source…</p>
            </div>
          ) : detail ? (
            <div className="source-body">
              {!detail.body.trimStart().startsWith("# ") && (
                <h2>{detail.title}</h2>
              )}
              <Markdown text={detail.body} />
            </div>
          ) : (
            <div className="empty-state">
              <BookOpen size={30} />
              <h3>Open the evidence</h3>
              <p>Select a source to read its full runbook or incident notes.</p>
            </div>
          )}
        </aside>
      </div>
      <p className="footnote">
        Retrieval scores rank document matches; they are not probabilities that
        an operational diagnosis is correct.
      </p>
    </>
  );
}
