export type Mode = "demo" | "live";
export type IncidentStatus = "Investigating" | "Mitigating" | "Resolved";
export type Severity = "P1" | "P2" | "P3" | "P4";
export interface ActionItem {
  id: string;
  text: string;
  done: boolean;
}
export interface TimelineEntry {
  id: string;
  text: string;
  at: string;
}
export interface Incident {
  id: string;
  title: string;
  service: string;
  severity: Severity;
  status: IncidentStatus;
  owner: string;
  summary: string;
  createdAt: string;
  tasks: ActionItem[];
  timeline: TimelineEntry[];
}
export interface DocumentSummary {
  source_id: string;
  title: string;
  type: string;
  tags: string[];
}
export interface KnowledgeDocument extends DocumentSummary {
  body: string;
}
export interface SearchResult extends DocumentSummary {
  citation: string;
  confidence: number;
  snippet: string;
  rank: number;
}
export interface AlertInput {
  alert_text: string;
  service: string;
  current_severity: string;
}
export interface AlertResult {
  recommended_severity: Severity;
  should_page: boolean;
  recommended_route: string;
  dedupe_key: string;
  reason: string;
  confidence: number;
  known_issue: SearchResult | null;
  next_checks: string[];
}
export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  text: string;
}
export interface Conversation {
  sessionId: string;
  messages: ChatMessage[];
}
