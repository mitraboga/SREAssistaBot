import { createContext, useContext, useEffect, useState } from "react";
import type { ReactNode } from "react";
import { seedIncidents } from "./demo";
import { incidentReducer } from "./incidents";
import type { IncidentAction } from "./incidents";
import {
  readStored,
  saveStored,
  validIncidents,
  workspaceKey,
} from "./storage";
import type { Incident, Mode } from "./types";

interface Workspace {
  mode: Mode;
  setMode: (mode: Mode) => void;
  incidents: Incident[];
  dispatch: (action: IncidentAction) => void;
  storageError: boolean;
}
const WorkspaceContext = createContext<Workspace | null>(null);

export function WorkspaceProvider({ children }: { children: ReactNode }) {
  const [mode, updateMode] = useState<Mode>(() =>
    readStored(
      "incidentiq:mode",
      "demo",
      (value): value is Mode => value === "demo" || value === "live",
    ),
  );
  const [records, setRecords] = useState<Record<Mode, Incident[]>>(() => ({
    demo: readStored(
      workspaceKey("demo", "incidents"),
      seedIncidents(),
      validIncidents,
    ),
    live: readStored(workspaceKey("live", "incidents"), [], validIncidents),
  }));
  const [storageError, setStorageError] = useState(false);
  useEffect(() => {
    const demoSaved = saveStored(
      workspaceKey("demo", "incidents"),
      records.demo,
    );
    const liveSaved = saveStored(
      workspaceKey("live", "incidents"),
      records.live,
    );
    setStorageError(!demoSaved || !liveSaved);
  }, [records]);
  const setMode = (next: Mode) => {
    updateMode(next);
    if (!saveStored("incidentiq:mode", next)) setStorageError(true);
  };
  const dispatch = (action: IncidentAction) =>
    setRecords((current) => ({
      ...current,
      [mode]: incidentReducer(current[mode], action),
    }));
  return (
    <WorkspaceContext.Provider
      value={{
        mode,
        setMode,
        incidents: records[mode],
        dispatch,
        storageError,
      }}
    >
      {children}
    </WorkspaceContext.Provider>
  );
}

export function useWorkspace(): Workspace {
  const context = useContext(WorkspaceContext);
  if (!context) throw new Error("WorkspaceProvider is required.");
  return context;
}
