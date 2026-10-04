import { useEffect, useState } from "react";
import {
  Activity,
  Bot,
  BookOpen,
  ChevronRight,
  CircleHelp,
  Command,
  LayoutDashboard,
  Radio,
  ShieldCheck,
} from "lucide-react";
import { NavLink, Outlet } from "react-router-dom";
import { liveApi } from "../lib/api";
import { useWorkspace } from "../lib/workspace";
import { ErrorNotice } from "./ui";

const navigation = [
  { path: "/incidents", label: "Incident board", icon: LayoutDashboard },
  { path: "/assistant", label: "SRE assistant", icon: Bot },
  { path: "/knowledge", label: "Knowledge base", icon: BookOpen },
  { path: "/triage", label: "Alert triage", icon: Radio },
];

export function Layout() {
  const { mode, setMode, storageError } = useWorkspace();
  const [health, setHealth] = useState("Checking API");
  useEffect(() => {
    if (mode !== "live") return;
    let active = true;
    const check = () =>
      liveApi
        .health()
        .then((result) => {
          if (active)
            setHealth(
              result.status === "healthy" ? "API reachable" : "API degraded",
            );
        })
        .catch(() => {
          if (active) setHealth("API offline");
        });
    void check();
    const interval = setInterval(() => {
      void check();
    }, 30000);
    return () => {
      active = false;
      clearInterval(interval);
    };
  }, [mode]);
  return (
    <div className="app-shell">
      <a className="skip-link" href="#main">
        Skip to content
      </a>
      <aside className="sidebar">
        <LinkBrand />
        <div className="workspace-label">
          <span className="workspace-avatar">IQ</span>
          <div>
            Engineering workspace<small>Reliability & response</small>
          </div>
          <ChevronRight size={15} />
        </div>
        <p className="nav-caption">WORKSPACE</p>
        <nav aria-label="Main navigation">
          {navigation.map(({ path, label, icon: Icon }) => (
            <NavLink key={path} to={path}>
              <Icon size={18} />
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="safety-card">
            <ShieldCheck size={19} />
            <strong>Investigate with confidence</strong>
            <p>Read-only guidance. Human-reviewed actions.</p>
          </div>
          <a
            className="repo-link"
            href="https://github.com/mitraboga/SREAssistaBot"
            target="_blank"
            rel="noopener noreferrer"
          >
            <CircleHelp size={16} />
            Project & documentation
          </a>
          <div className="profile">
            <span className="avatar">MB</span>
            <div>
              Mitra Boga<small>IncidentIQ workspace</small>
            </div>
          </div>
        </div>
      </aside>
      <div className="main-shell">
        <header className="topbar">
          <div className="breadcrumb">
            Workspace <ChevronRight size={13} />
            <span>Operations</span>
          </div>
          <div className="topbar-actions">
            <span
              className={`health ${mode === "demo" || health === "API reachable" ? "" : "offline"}`}
            >
              <span />
              {mode === "demo" ? "Demo environment" : health}
            </span>
            <label className="mode-control">
              <span className="sr-only">Environment</span>
              <select
                aria-label="Environment"
                value={mode}
                onChange={(event) =>
                  setMode(event.target.value as "demo" | "live")
                }
              >
                <option value="demo">Demo</option>
                <option value="live">Live API</option>
              </select>
            </label>
          </div>
        </header>
        <div className={`mode-banner ${mode}`}>
          <Activity size={14} />
          <span>
            {mode === "demo" ? "DEMO WORKSPACE" : "LIVE API WORKSPACE"}
          </span>
          <p>
            {mode === "demo"
              ? "Sample incidents and canned responses. Explore the workflow without credentials."
              : "Assistant and tools use your backend. Incident coordination is saved in this browser."}
          </p>
        </div>
        {storageError && (
          <ErrorNotice message="Browser storage is unavailable. Changes last only for this session; export important handoffs." />
        )}
        <main id="main" tabIndex={-1}>
          <Outlet key={mode} />
        </main>
        <footer className="app-footer">
          IncidentIQ <span>Built for the moments that matter.</span>
          <span>React workspace · v1.0</span>
        </footer>
      </div>
    </div>
  );
}

function LinkBrand() {
  return (
    <div className="brand">
      <span className="brand-mark">
        <Command size={23} />
      </span>
      <span>
        Incident<span className="brand-iq">IQ</span>
      </span>
      <span className="brand-tag">OPS</span>
    </div>
  );
}
