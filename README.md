<div align="center">

# 🚨 SRE Assista Bot 🤖

### IncidentIQ — Slack-Native SRE Assistant for Incident Triage, RAG & Alert Intelligence

<p align="center">
  <!-- Existing -->
  <img src="https://img.shields.io/badge/Python-3.11%2B-blue?logo=python">
  <img src="https://img.shields.io/badge/Slack-Bot-4A154B?logo=slack">
  <img src="https://img.shields.io/badge/Google%20ADK-Agent_Dev_Kit-4285F4?logo=google">
  <img src="https://img.shields.io/badge/FastAPI-API-009688?logo=fastapi">
  <img src="https://img.shields.io/badge/Postgres-Session_DB-336791?logo=postgresql">
  <img src="https://img.shields.io/badge/RAG-Runbooks%20%26%20Incidents-6A5ACD">
  <img src="https://img.shields.io/badge/CI%2FCD-GitHub_Actions-2088FF?logo=githubactions&logoColor=white">
  <img src="https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white">

  <!-- New: Concepts -->
  <img src="https://img.shields.io/badge/LLM-Enabled-2ea44f">
  <img src="https://img.shields.io/badge/Multi--Agent-Architecture-6f42c1">
  <img src="https://img.shields.io/badge/Site_Reliability-Engineering-8A2BE2">
  <img src="https://img.shields.io/badge/Incident-Response-ff6f00">
  <img src="https://img.shields.io/badge/Observability-Enabled-0aa6a6">
  <img src="https://img.shields.io/badge/Alert-Triage-ff4d4d">
  <img src="https://img.shields.io/badge/PagerNoise-Reduction-7f8c8d">
  <img src="https://img.shields.io/badge/TTFT-Measured-1f6feb">
  <img src="https://img.shields.io/badge/Evaluation-Harness-9b59b6">

  <!-- New: Providers -->
  <img src="https://img.shields.io/badge/Ollama-Local_Model-111111">
  <img src="https://img.shields.io/badge/Amazon_Bedrock-LLM-232F3E?logo=amazonaws&logoColor=white">
  <img src="https://img.shields.io/badge/Gemini-Google_AI-4285F4?logo=google&logoColor=white">
  <img src="https://img.shields.io/badge/Claude-Anthropic-000000">

  <!-- New: Infra / Platforms -->
  <img src="https://img.shields.io/badge/Kubernetes-Read--Only-326CE5?logo=kubernetes&logoColor=white">
  <img src="https://img.shields.io/badge/AWS-Operations-232F3E?logo=amazonaws&logoColor=white">
  <img src="https://img.shields.io/badge/Cost_Explorer-AWS-232F3E?logo=amazonaws&logoColor=white">
</p>

<img src="assets/SRE_Assista_Bot_Demo.gif" alt="SRE AssistaBot demo" width="900">

</div>

IncidentIQ is an SRE Assistant Chatbot, a Slack-style Site Reliability Engineering assistant built with
Google's Agent Development Kit (ADK). It provides an SRE-oriented chat interface
for incident triage, reliability reviews, AWS operations, AWS cost analysis, and
Kubernetes operations.

The project started as an MVP Slack bot and has been extended into a more
complete local operations assistant with multiple model providers, a background
service runner, ADK Web UI testing, health checks, and read-only infrastructure
tooling.

---

## What This Project Does

SRE AssistaBot lets an engineer ask operational questions in Slack threads or
through the ADK Web UI. The root SRE agent can answer general reliability
questions directly and, when full model mode is enabled, delegate specialized
requests to sub-agents.

Primary workflows:

- Create incident briefs from messy incident reports.
- Generate first 15-minute incident response plans.
- Review system designs from an SRE perspective.
- Recommend SLIs, SLOs, alerts, dashboards, and runbook steps.
- Analyze AWS cost and usage patterns when AWS credentials are configured.
- Inspect AWS infrastructure when AWS credentials are configured.
- Inspect Kubernetes cluster state through read-only `kubectl` tools.
- Search local runbooks and past incidents for citation-backed guidance.
- Classify alerts for page, ticket, or dedupe routing.
- Keep Slack thread context through ADK sessions.

## AI Concepts

This project uses several AI concepts, not just a basic chatbot wrapper.

Main AI Concepts Used:

1. **Large Language Models**
   The bot uses LLMs to understand natural-language SRE questions and generate
   structured operational responses. Supported providers include Ollama, Amazon
   Bedrock, Google Gemini, and Anthropic Claude.

2. **Agentic AI**
   The system is built with Google ADK, so the bot is modeled as an agent that
   can reason about a user request, decide whether to answer directly, or
   delegate to a specialized sub-agent.

3. **Multi-Agent Architecture**
   The root SRE agent can delegate to specialized agents:
   - AWS Cost agent
   - AWS Core operations agent
   - Kubernetes operations agent

4. **Tool Use / Function Calling**
   The agents can use tools such as AWS Cost Explorer helpers, AWS
   infrastructure checks, and read-only Kubernetes `kubectl` tools to gather
   operational evidence.

5. **Retrieval-Augmented Generation**
   The full-model path can search a local runbook and past-incident knowledge
   base before answering reliability, incident, and alerting questions. Retrieved
   sources include citation IDs such as `[RB-001]` and confidence scores.

6. **Natural Language Understanding**
   Users can ask questions in normal SRE language, such as "create an incident
   brief" or "review this system design," and the bot maps that request into
   structured SRE output.

7. **Prompt Engineering**
   The project uses system prompts to shape the bot's behavior, tone, safety
   rules, response format, delegation rules, and SRE-specific reasoning style.

8. **Retrieval of Live Operational Context**
   When tools are enabled, the bot can retrieve live or configured
   infrastructure data from AWS or Kubernetes instead of only relying on static
   model knowledge.

9. **Session Memory / Conversational Context**
   ADK sessions let the bot maintain conversation context across messages,
   especially inside Slack threads.

10. **Reasoning and Decision Support**
   The bot helps with incident triage, root-cause hypotheses, rollback
   criteria, risk assessment, SLO thinking, and reliability reviews.

11. **Human-in-the-Loop Safety**
    The prompts and tool design emphasize read-only checks first and ask for
    confirmation before risky or production-impacting actions.

12. **Alert Classification And Deflection**
    A deterministic alert-intelligence helper classifies alert severity,
    recommends page/ticket/dedupe routing, matches known issues, and measures
    pager-noise reduction in evals.

In short: this project combines **LLMs, agentic AI, multi-agent delegation, tool
use, RAG, prompt engineering, alert classification, and conversational memory**
to create an SRE-focused operational assistant.

## Current Status

Implemented and tested:

- Slack bot integration using Slack Socket Mode.
- ADK API server for programmatic sessions and `/run` calls.
- ADK Web UI for local browser-based testing.
- Root SRE orchestrator agent.
- AWS Cost sub-agent.
- AWS Core operations sub-agent.
- Kubernetes operations sub-agent.
- Local runbook and past-incident RAG tool with citations and confidence.
- Alert escalation, known-issue matching, and pager-noise deflection helper.
- Multiple model providers:
  - Ollama local demo mode.
  - Amazon Bedrock.
  - Google Gemini.
  - Anthropic Claude.
- Local background process manager for day-to-day use.
- Optional Windows login task for auto-start.
- Docker Compose stack for containerized local development.
- Health checks, request logging, response chunking, Slack event de-dupe, and
  safer environment handling.
- Tests and linting.

Validation at completion:

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
.\.venv\Scripts\python.exe -m ruff check .
```

Latest local result:

```text
77 passed, 1 skipped
All checks passed
```

## Scope And Mode Boundaries

The original MVP scope remains intact:

- Slack bot -> ADK API -> SRE agent flow still works.
- ADK Web UI and API testing are still available.
- AWS Cost, AWS Core, and Kubernetes sub-agents are still present.
- Docker Compose support, health checks, environment files, and dev tooling are
  still supported.

The newer resume-metric additions are additive:

- RAG over local runbooks and past incidents.
- Citation and confidence scoring.
- Alert severity classification, dedupe keys, known-issue matching, and
  deflection scoring.
- TTFT and benchmark probes.
- Expanded eval sets for SRE response quality, RAG retrieval, and alert routing.

Provider behavior matters:

- **Ollama demo mode** keeps the bot stable by answering directly with the root
  SRE prompt and avoiding sub-agent/tool delegation.
- **Bedrock, Gemini, and Claude full-model modes** enable richer ADK behavior,
  including sub-agent delegation and root-agent tools such as RAG and alert
  classification.

## Evaluation And Benchmarking

The project includes lightweight eval and benchmark harnesses in `evals/`.

### SRE Quality, Latency, And Hallucination Proxy

This harness calls the running local ADK API and measures:

- non-streaming `/run` response latency
- p50 and p95 latency
- deterministic SRE quality score
- pass rate across canned SRE scenarios
- missing required SRE concepts per answer
- unsupported live-claim rate, such as claiming logs or metrics were checked
  when no tool result was provided
- hallucination proxy rate, currently equal to unsupported live-claim rate

Run the full benchmark:

```powershell
.\.venv\Scripts\python.exe -m evals.run_sre_eval --api-url http://localhost:8001
```

Run a smaller smoke benchmark:

```powershell
.\.venv\Scripts\python.exe -m evals.run_sre_eval --limit 3
```

Results are written to:

```text
evals/results/
```

Those generated result files are ignored by Git.

Latest local smoke benchmark:

```text
Cases: 3
Successful API calls: 3
Pass rate: 100.0%
Average quality score: 0.885
Average latency: 24.236s
P50 latency: 24.745s
P95 latency: 28.339s
Unsupported live-claim rate: 0.0%
Hallucination proxy rate: 0.0%
```

This benchmark was run against the currently reachable local API. To benchmark a
specific provider, restart the bot with that provider first, then run the eval:

```powershell
.\start-assistabot.ps1 -Provider bedrock -Restart
.\.venv\Scripts\python.exe -m evals.run_sre_eval --limit 3
```

### TTFT Probe

Token-level time-to-first-token is measured through ADK's streaming `/run_sse`
endpoint:

```powershell
.\.venv\Scripts\python.exe -m evals.run_ttft_probe --api-url http://localhost:8001
```

Latest local TTFT probe:

```text
Status: success
First streamed text / TTFT: 15.031s
Total response time: 24.497s
Events observed: 253
```

TTFT depends heavily on the active provider, model size, local machine, and
whether Ollama/Bedrock/Gemini/Claude is being used.

### RAG Retrieval, Citations, And Confidence

The repository includes an expanded local knowledge base under
`agents/sre_agent/knowledge_base/documents/` with 14 runbooks and 10
past-incident notes. The root agent can use `search_knowledge_base` in full
model mode to cite retrieved sources such as `[RB-001]` and `[PI-001]`.

Run the RAG benchmark:

```powershell
.\.venv\Scripts\python.exe -m evals.run_rag_eval
```

Latest local RAG benchmark:

```text
Cases: 30
Hit@1: 96.7%
Hit@3: 100.0%
Hit@5: 100.0%
MRR: 0.983
Citation precision@3: 0.544
Citation precision@5: 0.333
Average top relevant confidence: 0.986
```

These are real measurements over the included demo/anonymized corpus. They
should not be presented as production RAG metrics until the corpus is replaced
or augmented with actual sanitized team runbooks and incident records.

### Alert Deflection And PagerNoise

The alert eval calls the deterministic alert classification helper and measures
page/ticket/dedupe routing quality.

```powershell
.\.venv\Scripts\python.exe -m evals.run_alert_eval
```

Latest local alert benchmark:

```text
Cases: 30
Page decision accuracy: 100.0%
Severity accuracy: 100.0%
Known-issue hit rate: 100.0%
Alert deflection rate: 60.0%
False escalation rate: 0.0%
Missed page rate: 0.0%
PagerNoise reduction: 60.0%
```

This is a controlled benchmark over 30 representative alert scenarios, not a
claim from live PagerDuty production traffic.

### Current Resume-Metric Coverage

Implemented and measured locally:

- Slack-based SRE assistant.
- Structured incident briefs and first-response plans.
- RAG over local runbooks and past incidents.
- Citations and confidence scores.
- Eval harnesses for SRE quality, RAG, alert routing, and TTFT.
- Hallucination proxy based on unsupported live-data claims.
- Guardrails for read-only-first investigation and risky-action confirmation.
- Severity classification, dedupe keys, known-issue detection, and alert
  deflection metrics.

Not claimed as production evidence yet:

- Real production PagerDuty alert deflection.
- Real production PagerNoise reduction.
- Real team/user time saved per incident.
- A 250-scenario benchmark.
- Production RAG quality over actual company runbooks and incident records.

### Expanding To Production-Grade Claims

The repo now has the structure needed for larger resume claims, but the wording
must match the evidence:

- Current evidence: 30 RAG queries, 30 alert scenarios, 20 SRE quality prompts,
  14 runbooks, and 10 past-incident notes.
- To claim "250 incident scenarios", add at least 250 JSONL cases across
  `sre_eval_scenarios.jsonl`, `rag_eval_queries.jsonl`, and
  `alert_eval_scenarios.jsonl`, then run the evals and cite the measured output.
- To claim production RAG quality, replace or augment the demo corpus with
  sanitized real runbooks and real past incidents.
- To claim real alert deflection or PagerNoise reduction, compare the classifier
  against historical alert/page data, not only synthetic benchmark scenarios.

## Architecture

```text
Slack / ADK Web UI / API clients
        |
        v
FastAPI ADK server: agents/sre_agent/serve.py
        |
        v
Root SRE agent: agents/sre_agent/agent.py
        |
        +-- local knowledge-base tools
        |   +-- runbook / past-incident retrieval with citations
        |   +-- alert severity, known-issue, and deflection scoring
        |
        +-- aws_cost_agent
        |   +-- Cost Explorer tools
        |   +-- service, account, tag, monthly, trend, and optimization analysis
        |
        +-- aws_core_agent
        |   +-- AWS account, EC2, S3, RDS, region, and connectivity checks
        |
        +-- kubernetes_agent
            +-- read-only kubectl tools for contexts, nodes, pods,
                deployments, services, pod logs, and cluster summary
```

### RAG And Alert Intelligence Internals

The local knowledge base is stored as Markdown documents with lightweight
metadata:

```text
agents/sre_agent/knowledge_base/documents/
  RB-001...RB-014       Runbooks
  PI-001...PI-010       Past incident notes
```

Root-agent tools:

```text
agents/sre_agent/tools/knowledge_base.py       Lexical retrieval, citations, confidence
agents/sre_agent/tools/alert_intelligence.py   Severity, route, dedupe, known issue scoring
```

The retriever is deterministic and local. It does not call an external vector
database. That keeps the project easy to run for a class/demo environment while
still making RAG behavior measurable through Hit@K, MRR, citation precision, and
confidence.

Main directories:

```text
agents/sre_agent/
  agent.py                         Root ADK SRE agent and delegation logic
  serve.py                         FastAPI ADK API server with health checks
  settings.py                      Session DB configuration
  utils.py                         Model selection and shared helpers
  tools/                           Root-agent RAG and alert-intelligence tools
  knowledge_base/documents/        Local runbooks and past incidents
  aws_auth/                        Optional role-based AWS auth layer
  sub_agents/
    aws_cost/                      AWS cost analysis sub-agent
    aws_core/                      AWS infrastructure operations sub-agent
    kubernetes/                    Kubernetes operations sub-agent

slack_bot/
  main.py                          Slack Socket Mode and Events API integration
  modules/health.py                Slack listener health check

tests/                             Unit tests for auth, tools, providers, and k8s
```

## Model Modes

The project supports four provider paths. Provider selection can be automatic,
but local scripts let you force the provider explicitly.

### Ollama Demo Mode

Ollama mode is the free local demo path.

Use it when:

- You do not want paid API usage.
- You want to demo Slack integration locally.
- You want basic SRE guidance without cloud billing.

Important behavior:

- Uses a local model through Ollama.
- Defaults to `qwen2.5:1.5b`.
- Enables `SRE_OLLAMA_SIMPLE_MODE=true`.
- Disables active sub-agent handoffs for stability with small local models.
- Still answers as an SRE assistant, but does not actively query AWS or
  Kubernetes tools in simple mode.

Start Ollama mode:

```powershell
.\start-assistabot.ps1 -Provider ollama -Restart
```

### Amazon Bedrock Mode

Bedrock mode is the AWS-native paid model path used for stronger responses and
full ADK delegation.

Use it when:

- You want better model quality than local Ollama.
- You want sub-agent delegation enabled.
- You are comfortable with AWS Bedrock usage charges.

Recommended smoke-test model:

```env
BEDROCK_MODEL_ID=amazon.nova-micro-v1:0
BEDROCK_REGION=us-east-1
```

Authentication options:

```env
# Option A: Bedrock API key
BEDROCK_API_KEY=your_bedrock_api_key_here

# Option B: official AWS bearer-token env var
AWS_BEARER_TOKEN_BEDROCK=your_bedrock_api_key_here

# Option C: normal AWS credentials/profile
AWS_PROFILE=your_aws_profile
AWS_REGION=us-east-1
```

Start Bedrock mode:

```powershell
.\start-assistabot.ps1 -Provider bedrock -Restart
```

Bedrock calls are billable AWS usage. Use short prompts while testing.

### Google Gemini Mode

Gemini is supported through Google AI Studio API keys.

```env
GOOGLE_API_KEY=your_google_api_key_here
GOOGLE_AI_MODEL=gemini-2.0-flash
```

Start Gemini mode:

```powershell
.\start-assistabot.ps1 -Provider google -Restart
```

### Anthropic Claude Mode

Claude is supported through LiteLLM.

```env
ANTHROPIC_API_KEY=your_anthropic_api_key_here
ANTHROPIC_MODEL=claude-3-5-sonnet-20240620
```

Start Claude mode:

```powershell
.\start-assistabot.ps1 -Provider anthropic -Restart
```

### Automatic Provider Priority

If `MODEL_PROVIDER` is not forced, the code checks providers in this order:

1. Google Gemini
2. Anthropic Claude
3. Amazon Bedrock

The local scripts are preferred because they make the selected provider
explicit and avoid confusion when multiple keys exist in `agents/.env`.

### Model Selection Guide

| Scenario | Recommended Provider | Suggested Model | Why |
| --- | --- | --- | --- |
| Free local demo, no cloud spend | Ollama | `qwen2.5:1.5b` | Runs locally and is enough to prove Slack integration, background services, and basic SRE response behavior. |
| Best low-cost AWS smoke test | Amazon Bedrock | `amazon.nova-micro-v1:0` | Confirms Bedrock auth, billing, and ADK provider wiring without starting with a larger model. |
| AWS-native project demo | Amazon Bedrock | Nova or Claude model available in Bedrock | Keeps the model path inside AWS and enables full sub-agent delegation for a stronger demo. |
| Fast general SRE assistance | Google Gemini | `gemini-2.0-flash` | Good default for quick operational guidance and lower-latency interactions. |
| Strong incident/reliability reasoning | Anthropic Claude | `claude-3-5-sonnet-20240620` or newer available model | Best fit for detailed incident command, tradeoff analysis, and design reviews. |
| Full production-style behavior | Bedrock, Gemini, or Claude | Stronger hosted model | Hosted models handle ADK delegation more reliably than the small local Ollama demo model. |

## Recommended Local Setup

### 1. Create a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r agents\sre_agent\requirements.txt
.\.venv\Scripts\python.exe -m pip install -r slack_bot\requirements.txt
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

### 2. Create environment files

```powershell
Copy-Item agents\env.example agents\.env
Copy-Item slack_bot\env.example slack_bot\.env
```

Edit:

- `agents/.env` for model provider, AWS, and Kubernetes settings.
- `slack_bot/.env` for Slack tokens.

Do not commit `.env` files.

### 3. Configure Slack

Create a Slack app at:

```text
https://api.slack.com/apps
```

Required bot scopes:

```text
app_mentions:read
channels:history
channels:join
chat:write
chat:write.public
im:history
im:read
im:write
```

Enable Socket Mode and create an app-level token with:

```text
connections:write
```

Set these values in `slack_bot/.env`:

```env
SLACK_BOT_TOKEN=xoxb-your-token
SLACK_SIGNING_SECRET=your-signing-secret
SLACK_APP_TOKEN=xapp-your-app-token
```

The local Slack runner forces:

```env
SLACK_SOCKET_MODE=true
SRE_AGENT_API_URL=http://localhost:8001
```

Socket Mode avoids needing ngrok or a public Events API URL for local testing.

## Daily Local Operation

Start the Slack bot and ADK API in the background:

```powershell
.\start-assistabot.ps1 -Provider bedrock -Restart
```

or:

```powershell
.\start-assistabot.ps1 -Provider ollama -Restart
```

Check status:

```powershell
.\status-assistabot.ps1
```

Stop all background services:

```powershell
.\stop-assistabot.ps1
```

Tail logs:

```powershell
Get-Content .runtime\logs\agent.out.log -Wait
Get-Content .runtime\logs\slack.out.log -Wait
```

### Start With ADK Web UI

The ADK Web UI is optional. It lets you test the agent directly in the browser
without Slack.

```powershell
.\start-assistabot.ps1 -Provider bedrock -WithWeb -Restart
```

Then open:

```text
http://localhost:8000/dev-ui/
```

### Auto-Start At Windows Login

Install the Windows scheduled task:

```powershell
.\install-assistabot-login-task.ps1 -Provider bedrock -WithWeb
```

If Windows returns `Access is denied`, run PowerShell as Administrator and retry.

Remove the login task:

```powershell
.\uninstall-assistabot-login-task.ps1
```

## Example Slack Prompts

<img src="assets/IncidentIQ.png" alt="IncidentIQ — Slack prompt examples" width="900">

<details>
  <summary><b>i) Incident Response</b></summary>
  <br/>
  <ol>
    <li>
      <img src="assets/IncidentResponse1.png" alt="Incident Response 1" width="900">
    </li>
    <li>
      <img src="assets/IncidentResponse2.png" alt="Incident Response 2" width="900">
    </li>
    <li>
      <img src="assets/IncidentResponse3.png" alt="Incident Response 3" width="900">
    </li>
    <li>
      <img src="assets/IncidentResponse4.png" alt="Incident Response 4" width="900">
    </li>
  </ol>
</details>

<details>
  <summary><b>ii) Debugging / Triage</b></summary>
  <br/>
  <ol>
    <li>
      <img src="assets/DebuggingTriage1.png" alt="Debugging / Triage 1" width="900">
    </li>
    <li>
      <img src="assets/DebuggingTriage2.png" alt="Debugging / Triage 2" width="900">
    </li>
    <li>
      <img src="assets/DebuggingTriage3.png" alt="Debugging / Triage 3" width="900">
    </li>
    <li>
      <img src="assets/DebuggingTriage4.png" alt="Debugging / Triage 4" width="900">
    </li>
  </ol>
</details>

<details>
  <summary><b>iii) Reliability Engineering</b></summary>
  <br/>
  <ol>
    <li>
      <img src="assets/ReliabilityEngineering1.png" alt="Reliability Engineering 1" width="900">
    </li>
    <li>
      <img src="assets/ReliabilityEngineering1.5.png" alt="Reliability Engineering 1.5" width="900">
    </li>
    <li>
      <img src="assets/ReliabilityEngineering2.png" alt="Reliability Engineering 2" width="900">
    </li>
    <li>
      <img src="assets/ReliabilityEngineering3.png" alt="Reliability Engineering 3" width="900">
    </li>
    <li>
      <img src="assets/ReliabilityEngineering4.png" alt="Reliability Engineering 4" width="900">
    </li>
  </ol>
</details>

<details>
  <summary><b>iv) AWS Cost / Style</b></summary>
  <br/>
  <ol>
    <li>
      <img src="assets/AWSCostStyle1.png" alt="AWS Cost / Style 1" width="900">
    </li>
    <li>
      <img src="assets/AWSCostStyle2.png" alt="AWS Cost / Style 2" width="900">
    </li>
    <li>
      <img src="assets/AWSCostStyle3.png" alt="AWS Cost / Style 3" width="900">
    </li>
  </ol>
</details>

<details>
  <summary><b>v) Real World Implementation</b></summary>
  <br/>
  <ol>
    <li>
      <img src="assets/RealWorldApplication1.png" alt="Real World Application 1" width="900">
    </li>
    <li>
      <img src="assets/RealWorldApplication1.5.png" alt="Real World Application 1.5" width="900">
    </li>
    <li>
      <img src="assets/RealWorldApplication2.png" alt="Real World Application 2" width="900">
    </li>
    <li>
      <img src="assets/RealWorldApplication2.33.png" alt="Real World Application 2.33" width="900">
    </li>
    <li>
      <img src="assets/RealWorldApplication2.66.png" alt="Real World Application 2.66" width="900">
    </li>
  </ol>
</details>

## API Usage

Create a session:

```bash
curl -X POST http://localhost:8001/apps/sre_agent/users/u_123/sessions/s_123 \
  -H "Content-Type: application/json" \
  -d '{"state": {"source": "manual-test"}}'
```

Send a message:

```bash
curl -X POST http://localhost:8001/run \
  -H "Content-Type: application/json" \
  -d '{
    "app_name": "sre_agent",
    "user_id": "u_123",
    "session_id": "s_123",
    "new_message": {
      "role": "user",
      "parts": [{"text": "Create an incident brief for checkout 5xx errors."}]
    }
  }'
```

Health checks:

```text
http://localhost:8001/health
http://localhost:8001/health/readiness
http://localhost:8001/health/liveness
```

## Docker Compose

Docker Compose remains available for containerized local development.

Services:

- `sre-bot-web`: ADK Web UI on port `8000`.
- `sre-bot-api`: ADK API server on port `8001`.
- `slack-bot`: Slack integration service on port `8002`.
- `postgres`: session database.

Start the stack:

```bash
docker compose up --build
```

Start selected services:

```bash
docker compose up sre-bot-web
docker compose up sre-bot-api slack-bot
```

View logs:

```bash
docker compose logs -f sre-bot-api slack-bot
```

The Windows PowerShell scripts are the recommended path for the current local
demo because they support provider switching, background execution, and local
SQLite sessions without requiring Docker Desktop.

## Kubernetes Operations

The Kubernetes sub-agent is read-only. It shells out to `kubectl` with structured
arguments and never runs mutating commands.

Tools include:

- current context
- available contexts
- nodes and readiness
- pods by namespace or label selector
- deployments and replica health
- services
- pod logs with tail limits
- cluster summary

Configuration:

```env
KUBE_CONTEXT=your_kube_context
# Optional:
KUBE_NAMESPACE=default
KUBECTL_PATH=C:\path\to\kubectl.exe
```

If `kubectl` is missing, the tools return an actionable error instead of
crashing the agent.

## AWS Operations And Cost Analysis

The AWS sub-agents are available when full model mode is enabled and AWS
credentials are configured.

AWS Core can help with:

- caller identity
- AWS connectivity checks
- region discovery
- EC2, S3, and RDS summaries
- account-level operational review

AWS Cost can help with:

- monthly totals
- current month-to-date cost
- previous month cost
- last N months trend
- spend by service
- spend by tag
- spend by linked account
- most expensive linked account
- daily averages
- step-change and trend summaries
- cost optimization recommendations

Configuration:

```env
AWS_PROFILE=your_aws_profile
AWS_REGION=us-east-1
```

Optional role-based auth:

```env
AWS_AUTH_ENABLE_CACHING=true
AWS_AUTH_DEFAULT_REGION=us-east-1
AWS_AUTH_DEFAULT_ROLE_ARN=arn:aws:iam::123456789012:role/SRERole
AWS_AUTH_DEFAULT_ACCOUNT_ID=123456789012
AWS_AUTH_DEFAULT_SESSION_NAME=SREBotSession
```

## Environment Files

```text
agents/env.example       template for agent model/AWS/Kubernetes settings
agents/.env              local agent secrets and settings, not committed

slack_bot/env.example    template for Slack settings
slack_bot/.env           local Slack secrets, not committed
```

Important `.gitignore` protections:

- `.env`
- `**/.env`
- `.venv/`
- `.runtime/`
- `*.log`
- `*.db`
- `postgres_data/`

## Development

Run tests:

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
```

Run lint:

```powershell
.\.venv\Scripts\python.exe -m ruff check .
```

Format:

```powershell
.\.venv\Scripts\python.exe -m ruff format .
```

Pre-commit:

```powershell
.\.venv\Scripts\pre-commit.exe run --all-files
```

CI is configured in:

```text
.github/workflows/ci.yml
```

## Troubleshooting

Check local service status:

```powershell
.\status-assistabot.ps1
```

Restart with a specific provider:

```powershell
.\start-assistabot.ps1 -Provider bedrock -Restart
.\start-assistabot.ps1 -Provider ollama -Restart
```

Common issues:

- Slack does not reply:
  - Run `.\status-assistabot.ps1`.
  - Check `.runtime\logs\slack.out.log`.
  - Verify `SLACK_BOT_TOKEN` and `SLACK_APP_TOKEN`.

- API returns 500:
  - Check `.runtime\logs\agent.out.log`.
  - Verify the selected model provider credentials.
  - If using Ollama, confirm Ollama is running on `localhost:11434`.

- Bedrock fails:
  - Verify `BEDROCK_API_KEY` or AWS credentials.
  - Verify `BEDROCK_MODEL_ID` and `BEDROCK_REGION`.
  - Remember that Bedrock usage is billable.

- Kubernetes tools fail:
  - Run `kubectl config current-context`.
  - Verify `KUBE_CONTEXT`.
  - Set `KUBECTL_PATH` if `kubectl` is not on PATH.

## Security Notes

- Never commit `.env` files.
- Rotate any key that was accidentally exposed during development.
- Use least-privilege AWS and Kubernetes credentials.
- Prefer read-only AWS/IAM/Kubernetes permissions for demos.
- Bedrock, Gemini, and Claude API calls may incur provider charges.
- Review logs before sharing them; application logs may contain operational
  details.

---

## 👤 Author

<p align="center">
  <b>Mitra Boga</b><br>
  <a href="https://www.linkedin.com/in/bogamitra/">
    <img src="https://img.shields.io/badge/LinkedIn-bogamitra-blue?logo=linkedin">
  </a>
  <a href="https://x.com/techtraboga">
    <img src="https://img.shields.io/badge/X-techtraboga-black?logo=x">
  </a>
</p>

---

## License

MIT License. See `LICENSE`.
