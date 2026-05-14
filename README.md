# SRE AssistaBot

SRE AssistaBot is a Slack-style Site Reliability Engineering assistant built with
Google's Agent Development Kit (ADK). It provides an SRE-oriented chat interface
for incident triage, reliability reviews, AWS operations, AWS cost analysis, and
Kubernetes operations.

The project started as an MVP Slack bot and has been extended into a more
complete local operations assistant with multiple model providers, a background
service runner, ADK Web UI testing, health checks, and read-only infrastructure
tooling.

![SRE AssistaBot demo](assets/SRE_Assista_Bot_Demo.gif)

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

5. **Natural Language Understanding**
   Users can ask questions in normal SRE language, such as "create an incident
   brief" or "review this system design," and the bot maps that request into
   structured SRE output.

6. **Prompt Engineering**
   The project uses system prompts to shape the bot's behavior, tone, safety
   rules, response format, delegation rules, and SRE-specific reasoning style.

7. **Retrieval of Live Operational Context**
   When tools are enabled, the bot can retrieve live or configured
   infrastructure data from AWS or Kubernetes instead of only relying on static
   model knowledge.

8. **Session Memory / Conversational Context**
   ADK sessions let the bot maintain conversation context across messages,
   especially inside Slack threads.

9. **Reasoning and Decision Support**
   The bot helps with incident triage, root-cause hypotheses, rollback
   criteria, risk assessment, SLO thinking, and reliability reviews.

10. **Human-in-the-Loop Safety**
    The prompts and tool design emphasize read-only checks first and ask for
    confirmation before risky or production-impacting actions.

In short: this project combines **LLMs, agentic AI, multi-agent delegation, tool
use, prompt engineering, and conversational memory** to create an SRE-focused
operational assistant.

## Current Status

Implemented and tested:

- Slack bot integration using Slack Socket Mode.
- ADK API server for programmatic sessions and `/run` calls.
- ADK Web UI for local browser-based testing.
- Root SRE orchestrator agent.
- AWS Cost sub-agent.
- AWS Core operations sub-agent.
- Kubernetes operations sub-agent.
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
65 passed, 1 skipped
All checks passed
```

## Evaluation And Benchmarking

The project includes a lightweight SRE eval harness in `evals/`.

It calls the running local ADK API and measures:

- non-streaming `/run` response latency
- p50 and p95 latency
- deterministic SRE quality score
- pass rate across canned SRE scenarios
- missing required SRE concepts per answer
- unsupported live-claim rate, such as claiming logs or metrics were checked
  when no tool result was provided

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

Current limitation: this harness measures full non-streaming API response
latency, not token-level TTFT. It also does not yet measure RAG metrics such as
Hit@K, MRR, citation accuracy, or retrieval groundedness because this project
does not currently include a runbook/past-incident retrieval corpus.

Latest local smoke benchmark:

```text
Cases: 3
Successful API calls: 3
Pass rate: 100.0%
Average quality score: 0.926
Average latency: 28.790s
P50 latency: 23.837s
P95 latency: 42.588s
Unsupported live-claim rate: 0.0%
```

This benchmark was run against the currently reachable local API. To benchmark a
specific provider, restart the bot with that provider first, then run the eval:

```powershell
.\start-assistabot.ps1 -Provider bedrock -Restart
.\.venv\Scripts\python.exe -m evals.run_sre_eval --limit 3
```

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

Main directories:

```text
agents/sre_agent/
  agent.py                         Root ADK SRE agent and delegation logic
  serve.py                         FastAPI ADK API server with health checks
  settings.py                      Session DB configuration
  utils.py                         Model selection and shared helpers
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

Incident command:

```text
@sre-assista-bot Act as the incident commander. We have a 5xx spike on checkout,
payment failures, and customer complaints from NA. Give me an incident brief,
first 15-minute plan, risks, rollback criteria, and customer comms draft.
```

Technical triage:

```text
@sre-assista-bot Based on that incident brief, create a technical triage
checklist for the on-call engineer. Include the exact metrics, logs, dashboards,
database checks, dependency checks, and rollback validation steps we should run
in the next 30 minutes. Prioritize read-only checks first.
```

Reliability review:

```text
@sre-assista-bot Review this production checkout design from an SRE perspective:
frontend -> API gateway -> payments service -> Postgres. Target availability is
99.9%, peak traffic is 500 requests/minute, and the main concerns are payment
failures, duplicate charges, DB saturation, and slow checkout. Give me risks,
SLIs/SLOs, alerts, observability gaps, and highest-priority improvements.
```

Kubernetes operations:

```text
@sre-assista-bot How many pods are running in the default namespace, and are any
pods crash looping?
```

AWS cost analysis:

```text
@sre-assista-bot Show me the top AWS cost drivers this month and compare them
against last month. Exclude Support and Tax.
```

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

## License

MIT License. See `LICENSE`.
