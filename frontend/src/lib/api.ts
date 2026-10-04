import type {
  AlertInput,
  AlertResult,
  ChatMessage,
  DocumentSummary,
  KnowledgeDocument,
  SearchResult,
} from "./types";

const base = (import.meta.env.VITE_API_BASE_URL || "/api").replace(/\/$/, "");

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
  }
}

export async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const timeout = AbortSignal.timeout(180000);
  const signal = options.signal
    ? AbortSignal.any([options.signal, timeout])
    : timeout;
  let response: Response;
  try {
    response = await fetch(`${base}${path}`, {
      ...options,
      signal,
      headers: { "Content-Type": "application/json", ...options.headers },
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError")
      throw error;
    if (timeout.aborted)
      throw new ApiError(
        "The request timed out. Check the model provider and try again.",
        408,
      );
    throw new ApiError(
      "Cannot reach the API. Start the backend on port 8001 or use demo mode.",
      0,
    );
  }
  if (!response.ok) {
    throw new ApiError(
      `API returned ${response.status}. ${response.status === 404 ? "Check the backend version and session." : "Check backend logs and retry."}`,
      response.status,
    );
  }
  try {
    return (await response.json()) as T;
  } catch {
    throw new ApiError("The API returned an invalid JSON response.", 502);
  }
}

export const liveApi = {
  health: () => request<{ status: string }>("/health"),
  documents: () =>
    request<{ documents: DocumentSummary[] }>("/workspace/knowledge"),
  search: (query: string, signal?: AbortSignal) =>
    request<{ results: SearchResult[] }>(
      `/workspace/knowledge/search?query=${encodeURIComponent(query)}`,
      { signal },
    ),
  document: (id: string, signal?: AbortSignal) =>
    request<KnowledgeDocument>(
      `/workspace/knowledge/${encodeURIComponent(id)}`,
      { signal },
    ),
  classify: (input: AlertInput, signal?: AbortSignal) =>
    request<AlertResult>("/workspace/alerts/classify", {
      method: "POST",
      body: JSON.stringify(input),
      signal,
    }),
};

interface AdkPart {
  text?: string;
  thought?: boolean;
}
interface AdkEvent {
  author?: string;
  partial?: boolean;
  content?: { role?: string; parts?: AdkPart[] };
}

export function extractAssistantText(events: unknown): string {
  if (!Array.isArray(events))
    throw new ApiError("Unexpected ADK response format.", 502);
  const answers = (events as AdkEvent[])
    .filter(
      (event) =>
        event &&
        event.author !== "user" &&
        event.content?.role !== "user" &&
        !event.partial,
    )
    .map(
      (event) =>
        event.content?.parts
          ?.filter((part) => !part.thought && typeof part.text === "string")
          .map((part) => part.text)
          .join("\n") || "",
    )
    .filter((text) => text.trim());
  const answer = answers.at(-1);
  if (!answer)
    throw new ApiError(
      "The agent returned no answer text. Check the provider and backend logs.",
      502,
    );
  return answer;
}

function sessionPath(userId: string, sessionId: string): string {
  return `/apps/sre_agent/users/${encodeURIComponent(userId)}/sessions/${encodeURIComponent(sessionId)}`;
}

export async function sendLiveMessage(
  userId: string,
  sessionId: string,
  text: string,
  signal: AbortSignal,
): Promise<string> {
  const path = sessionPath(userId, sessionId);
  try {
    await request(path, { signal });
  } catch (error) {
    if (!(error instanceof ApiError) || error.status !== 404) throw error;
    await request(path, {
      method: "POST",
      body: JSON.stringify({ state: { source: "react_workspace" } }),
      signal,
    });
  }
  const events = await request<unknown>("/run", {
    method: "POST",
    signal,
    body: JSON.stringify({
      app_name: "sre_agent",
      user_id: userId,
      session_id: sessionId,
      new_message: { role: "user", parts: [{ text }] },
    }),
  });
  return extractAssistantText(events);
}

export async function loadSessionMessages(
  userId: string,
  sessionId: string,
  signal: AbortSignal,
): Promise<ChatMessage[]> {
  const session = await request<{ events?: AdkEvent[] }>(
    sessionPath(userId, sessionId),
    { signal },
  );
  return (session.events || []).flatMap((event, index) => {
    if (event.partial) return [];
    const text = event.content?.parts
      ?.filter((part) => !part.thought && typeof part.text === "string")
      .map((part) => part.text)
      .join("\n");
    return text
      ? [
          {
            id: `history-${index}`,
            role:
              event.author === "user" || event.content?.role === "user"
                ? ("user" as const)
                : ("assistant" as const),
            text,
          },
        ]
      : [];
  });
}
