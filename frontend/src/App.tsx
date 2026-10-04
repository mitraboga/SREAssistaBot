import { Component } from "react";
import type { ErrorInfo, ReactNode } from "react";
import { BrowserRouter, Link, Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { WorkspaceProvider } from "./lib/workspace";
import { IncidentBoard } from "./pages/IncidentBoard";
import { Assistant } from "./pages/Assistant";
import { Knowledge } from "./pages/Knowledge";
import { Triage } from "./pages/Triage";

class ErrorBoundary extends Component<
  { children: ReactNode },
  { failed: boolean }
> {
  state = { failed: false };
  static getDerivedStateFromError() {
    return { failed: true };
  }
  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("Workspace rendering failed", error, info.componentStack);
  }
  render() {
    return this.state.failed ? (
      <main className="fatal-error">
        <h1>The workspace could not load</h1>
        <p>
          Reload the page to try again. Your saved incidents remain in browser
          storage.
        </p>
        <button onClick={() => window.location.reload()}>
          Reload workspace
        </button>
      </main>
    ) : (
      this.props.children
    );
  }
}

export function App() {
  return (
    <ErrorBoundary>
      <WorkspaceProvider>
        <BrowserRouter>
          <Routes>
            <Route element={<Layout />}>
              <Route index element={<Navigate to="/incidents" replace />} />
              <Route path="incidents" element={<IncidentBoard />} />
              <Route path="assistant" element={<Assistant />} />
              <Route path="knowledge" element={<Knowledge />} />
              <Route path="triage" element={<Triage />} />
              <Route
                path="*"
                element={
                  <div className="empty-state">
                    <h1>Page not found</h1>
                    <Link to="/incidents">Return to the incident board</Link>
                  </div>
                }
              />
            </Route>
          </Routes>
        </BrowserRouter>
      </WorkspaceProvider>
    </ErrorBoundary>
  );
}
