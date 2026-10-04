import type { ReactNode } from "react";
import { AlertCircle, ArrowUpRight } from "lucide-react";
import ReactMarkdown from "react-markdown";
import { Link } from "react-router-dom";

export function Badge({
  children,
  tone = "",
}: {
  children: ReactNode;
  tone?: string;
}) {
  return <span className={`badge ${tone}`}>{children}</span>;
}
export function ErrorNotice({ message }: { message: string }) {
  return (
    <div className="notice error" role="alert">
      <AlertCircle size={17} />
      <span>{message}</span>
    </div>
  );
}
export function Markdown({ text }: { text: string }) {
  return (
    <div className="markdown">
      <ReactMarkdown
        components={{
          a: ({ href, children }) => (
            <a href={href} target="_blank" rel="noopener noreferrer">
              {children}
            </a>
          ),
        }}
      >
        {text}
      </ReactMarkdown>
    </div>
  );
}
export function SourceLink({
  id,
  children,
}: {
  id: string;
  children?: ReactNode;
}) {
  return (
    <Link
      className="source-link"
      to={`/knowledge?source=${encodeURIComponent(id)}`}
    >
      {children || id}
      <ArrowUpRight size={13} />
    </Link>
  );
}
export function formatTime(at: string): string {
  const date = new Date(at);
  return Number.isNaN(date.getTime())
    ? at
    : date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}
