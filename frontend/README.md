# IncidentIQ React workspace

A React + TypeScript interface for SREAssistaBot, built with Vite. It adds a
browser-based incident coordination workflow and connects directly to the existing
FastAPI / Google ADK backend. Slack and the ADK developer UI remain available.

## Run the offline demo

Install Git and Node.js 24. Open a terminal in the folder where you want to
download the project. The commands below clone `main`, including the React
workspace in `frontend/`.

**Windows PowerShell:** run each command one at a time:

```powershell
git clone --branch main https://github.com/mitraboga/SREAssistaBot.git SREAssistaBot-React
cd .\SREAssistaBot-React\frontend
npm.cmd ci
npm.cmd run dev
```

**macOS/Linux:**

```bash
git clone --branch main https://github.com/mitraboga/SREAssistaBot.git SREAssistaBot-React
cd SREAssistaBot-React/frontend
npm ci
npm run dev
```

Already have an up-to-date local checkout of `main`? From that repository's root,
run `cd frontend`, then install/start with the npm commands for your operating
system above.

Open the exact URL printed beside **Local:**, normally <http://localhost:5173>.
Vite may choose another port if 5173 is occupied. Keep the terminal open while
using the app. The default **Demo** environment works without a Python backend,
model, Slack, AWS, Kubernetes, database credentials, or API keys.

**Restart later:** open a terminal in the downloaded project's `frontend/` folder
and run `npm.cmd run dev` on Windows or `npm run dev` on macOS/Linux. Stop the
server with **Ctrl+C**. Reinstall dependencies with `npm.cmd ci` / `npm ci` when
the dependency files change.

**Troubleshooting:**

- `not a git repository` or `Cannot find path ... frontend`: open the downloaded
  project folder first, or use the complete clone commands above.
- `ERR_CONNECTION_REFUSED`: check that the Vite terminal is still running and
  use its printed URL. Resolve any terminal startup error before opening Chrome.
- PowerShell blocks `npm.ps1`: use the documented `npm.cmd` commands.
- `node` or `npm` is not recognized: install Node.js 24 and reopen your terminal.

If a command fails, stop there and resolve its error before running the next one.

- Incident board: create incidents, assign owners, change status, check off
  response actions, add timeline notes, filter the queue, and export a Markdown handoff.
- SRE assistant: canned demo guidance, editable prompt suggestions, and citation links.
- Knowledge base: browse/search a snapshot of all 24 anonymized repository documents.
- Alert triage: a deliberately simple browser demo classifier with sample alerts.

Demo responses and scores are labeled. They are not live operational results, LLM
responses, or measured production outcomes. The demo classifier and browser search
are simplified examples; Live API uses the original Python tools.

## Let others try it

Visitors can run their own copy with the commands above. `localhost` refers to
the computer opening the URL, so sharing your local URL does not share your app.

A public demo requires deploying the frontend to a web host. No public React demo
deployment is included in this change. To create the production files, run
`npm run build` (`npm.cmd run build` in PowerShell) from `frontend/`; the output is
`frontend/dist/`. Configure the host to serve `index.html` for React route URLs
such as `/incidents` and `/knowledge`, since the app uses `BrowserRouter`.

Hosting only this frontend provides the labeled Demo experience. Live AI also
requires a deployed Python API, a working model provider, and the appropriate API
address/proxy configuration. Vite's development proxy is not included in `dist/`;
the provided nginx configuration demonstrates a production proxy. Read the
[state and scope](#state-and-scope) notes before sharing a live multi-user API.

## Connect to the backend

Start the existing API on port 8001 using your configured provider. On Windows,
run this from the repository root in a separate terminal:

```powershell
.\start-local-agent.ps1 -Provider ollama
```

For other supported providers, use `bedrock`, `google`, or `anthropic` with the
existing server-side credentials. Ollama requires a running local model. Paid
providers use their normal billing when you send a live assistant message.

On Linux/macOS, after installing the existing agent requirements in your virtual
environment, run from `agents/` with the repository's documented provider env vars:

```bash
PYTHONPATH="$PWD" SESSION_SERVICE_URI=sqlite:///./srebot_sessions.db PORT=8001 \
  ../venv_linux/bin/python -m sre_agent.serve
```

In the React app choose **Live API**. The Vite dev server proxies `/api` to
`http://127.0.0.1:8001`. To change the backend address, copy `.env.example` to `.env`
and set `API_PROXY_TARGET`, then restart Vite. Never put provider keys in `VITE_*`
variables; those variables are public browser configuration.

The existing health endpoint only reports API reachability. It does not prove
that a model, session database, AWS account, or Kubernetes cluster is healthy.

## Docker

After configuring the existing `agents/.env` file and credentials mounts, run
from the repository root:

```bash
docker compose --profile react up --build incidentiq-ui
```

This starts the UI and its API/Postgres dependencies. The UI is on port 5173;
nginx serves the production bundle, handles React route refreshes, and proxies
`/api/` to `sre-bot-api:8000`. The UI is opt-in through the `react` profile so the
existing default stack does not start an extra service.

## API contract

The app uses `sre_agent` as its ADK application name. A random, browser-local user
ID and per-conversation session ID keep unrelated browser conversations separate.

| Endpoint | Usage |
| --- | --- |
| `GET /health` | API reachability indicator |
| `GET /apps/sre_agent/users/{user}/sessions/{session}` | Check session / synchronize ADK history |
| `POST /apps/sre_agent/users/{user}/sessions/{session}` | Create a session only when GET returns 404 |
| `POST /run` | Send a message and read the final non-partial, non-thought answer |
| `GET /workspace/knowledge` | List the configured corpus |
| `GET /workspace/knowledge/search?query=...&top_k=5` | Search with the existing Python retriever |
| `GET /workspace/knowledge/{source_id}` | Read a known source by ID |
| `POST /workspace/alerts/classify` | Use the existing deterministic alert classifier |

The workspace routes are mounted in `agents/sre_agent/serve.py`, not in the stock
`adk web` command. Start the custom API server for React's live tool screens.
Document IDs are resolved against the loaded corpus, with no arbitrary path access.
Input lengths and retrieval limits are validated with Pydantic/FastAPI.

Chat uses the existing non-streaming `/run` route. The request can be cancelled
in the browser, but cancellation does not guarantee that the backend model run
stopped. Use **Sync ADK history** to reconcile after cancellation or an ambiguous
network failure before retrying. Timing shown in the UI is total browser response
time, not token-level TTFT. Only completed answers are persisted in the UI history.

## State and scope

- Incident records, owners, tasks, and timeline entries live in `localStorage`.
  They are personal browser coordination data, not a shared server incident database.
- Demo and Live API records and chat histories use separate, versioned storage keys.
- ADK live conversation history uses the backend's existing session service.
  **Sync ADK history** reloads completed text events from that service.
- Malformed browser storage falls back safely. Storage failures show an explicit notice.
- Client-generated IDs organize sessions; they are **not authentication**.
  The existing backend is intended for local development. Add authentication,
  authorization, and server-side incident storage before sharing a multi-user deployment.
- The UI never dispatches a page, creates an external ticket, or runs remediation.
- Retrieval and classifier confidence values are heuristic scores, not calibrated
  diagnosis probabilities. Users confirm customer impact before acting.
- Markdown is rendered without raw HTML, and external links use safe new-tab attributes.

## Architecture and SWE coverage

The routed app shares incident state through a React context. A reducer records
status, ownership, action, and note changes in the timeline. Components are split
by workflow, with a typed API client, abortable requests, explicit loading/error/empty
states, responsive CSS, accessible labels, keyboard navigation, and an error boundary.

```text
src/
  components/       Shared layout, incident details, Markdown and citation UI
  pages/            Incident board, assistant, knowledge explorer, alert triage
  lib/api.ts        Typed ADK and workspace API client
  lib/incidents.ts  Incident transitions and Markdown handoff export
  lib/storage.ts    Validation and versioned browser persistence
  lib/workspace.tsx Shared React incident context
  lib/demo.ts       Explicit offline demonstration logic
  test/             React Testing Library setup
e2e/                Desktop/mobile Playwright workflow checks
```

For internship discussions, this adds concrete experience in React, TypeScript,
client-side routing, forms and state, REST integration, testing, and containerized
frontend delivery to the existing Python/SRE project. Claims about authentication,
multi-user collaboration, production usage, or streaming should wait until those
features are implemented and measured.

## Verification

```bash
npm run build        # strict TypeScript validation + production bundle
npm test             # Vitest / React Testing Library
npx playwright install chromium
npm run test:e2e     # desktop + mobile flows; ADK responses are mocked
```

In environments that already provide Chromium, set
`PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH` to its executable path instead of downloading
Playwright's browser. Tests cover incident creation/ownership/status/tasks,
persistence, export, citations, triage, and ADK request/error/retry behavior. They
do not validate a paid provider or real infrastructure.

The backend contract tests use the real deterministic corpus/classifier, without
ADK initialization or a database:

```bash
venv_linux/bin/python -m pytest tests/test_workspace_api.py -q
```

The dedicated `React workspace` GitHub Actions workflow builds/tests the frontend,
runs Playwright in Chromium, and checks the new backend routes.
