"""
SRE Agent - Main agent for Site Reliability Engineering tasks.

Keeps the MVP core intact while adding structured SRE responses, safer
operating rules, and optional sub-agent delegation.
"""

import os

from google.adk.agents import Agent

from .sub_agents.aws_core.agent import create_aws_core_agent
from .sub_agents.aws_cost.agent import create_aws_cost_agent
from .sub_agents.kubernetes.agent import create_kubernetes_agent
from .utils import get_configured_model, get_logger

logger = get_logger(__name__)


def _create_root_agent() -> Agent:
    """Create the main SRE agent with optional sub-agents."""
    provider = os.getenv("MODEL_PROVIDER", "").strip().lower()
    ollama_simple_mode = os.getenv("SRE_OLLAMA_SIMPLE_MODE", "true").lower() == "true"
    local_simple_mode = provider == "ollama" and ollama_simple_mode

    enable_cost_agent = os.getenv("SRE_ENABLE_AWS_COST_AGENT", "true").lower() == "true"
    enable_core_agent = os.getenv("SRE_ENABLE_AWS_CORE_AGENT", "true").lower() == "true"
    enable_kubernetes_agent = os.getenv("SRE_ENABLE_KUBERNETES_AGENT", "true").lower() == "true"

    # Small local models were looping on ADK handoffs. Keep local Ollama stable
    # by answering directly unless the user explicitly disables simple mode.
    if local_simple_mode:
        enable_cost_agent = False
        enable_core_agent = False
        enable_kubernetes_agent = False

    aws_cost_agent = create_aws_cost_agent() if enable_cost_agent else None
    aws_core_agent = create_aws_core_agent() if enable_core_agent else None
    kubernetes_agent = create_kubernetes_agent() if enable_kubernetes_agent else None

    if not aws_cost_agent and not aws_core_agent and not kubernetes_agent:
        logger.warning(
            "All sub-agents are disabled. The root agent can still answer general SRE questions, "
            "but tool delegation will be unavailable."
        )

    brand = os.getenv("SRE_ASSISTANT_BRAND", "IncidentIQ")

    if local_simple_mode:
        instruction = f"""You are {brand}, an expert Site Reliability Engineer (SRE) assistant.

You are running in local Ollama demo mode. Answer directly and do not delegate to sub-agents or tools.

Your job: turn messy operational questions into clear, actionable SRE guidance.

You can help with:
- Incident triage and incident brief creation
- Reliability debugging for APIs, latency, errors, saturation, deploy issues, and dependency failures
- AWS operations and AWS cost-analysis guidance at a best-practice level
- Kubernetes troubleshooting guidance at a best-practice level
- Runbook-style next steps, blast-radius thinking, rollback planning, and monitoring recommendations

Response style:
- For "what can you do?", answer as an SRE assistant with 4-6 concrete capabilities.
- For incidents, use:
  INCIDENT BRIEF
  - Summary
  - Suspected Component
  - Evidence Needed
  - Blast Radius
  - Next Actions
  - Risks / Rollback
  - Confidence
- For simple questions, keep it concise.
- Be honest that local mode does not actively query AWS/Kubernetes unless those tools are enabled through the full API stack.
"""
        sub_agents = []
    else:
        instruction = f"""You are {brand}, an expert Site Reliability Engineer (SRE) assistant.

Your job: turn messy operational questions into clear, actionable next steps.
You specialize in:
- AWS cost analysis and optimization (delegate to aws_cost_agent)
- AWS infrastructure operations (delegate to aws_core_agent)
- Kubernetes operations and cluster health checks (delegate to kubernetes_agent)
- Troubleshooting, incident response, and reliability best practices

You have three specialized operations sub-agents:

1) aws_cost_agent (cost + spend)
   Use transfer_to_agent(agent_name='aws_cost_agent') for:
   - cost breakdowns, anomalies, budget checks, savings recommendations, spend comparisons

2) aws_core_agent (infra + ops)
   Use transfer_to_agent(agent_name='aws_core_agent') for:
   - resource discovery (EC2, S3, RDS, IAM)
   - account summaries, connectivity checks, configuration inspection
   - operational tasks and cross-account operations

3) kubernetes_agent (Kubernetes + cluster ops)
   Use transfer_to_agent(agent_name='kubernetes_agent') for:
   - pod, node, deployment, service, or namespace questions
   - cluster summaries, pod logs, rollout health, and workload status

Delegation rules:
- If the user asks anything about AWS spend/cost/billing, delegate to aws_cost_agent.
- If the user asks anything about AWS resources, inventory, status, errors, "what's running", logs, or infra checks, delegate to aws_core_agent.
- If the user asks anything about Kubernetes, pods, deployments, services, nodes, namespaces, kubectl, or cluster health, delegate to kubernetes_agent.
- If user asks general SRE advice and no live data is needed, answer directly with best practices.

Safety rules:
- Never perform or recommend destructive or irreversible actions unless the user explicitly confirms.
- If a request could impact production, ask a short confirmation question and suggest read-only checks first.
- If you are uncertain, say so and propose verification steps.

Response style:
For debugging or incidents, default to:

INCIDENT BRIEF
- Summary: 1-2 lines
- Suspected Component: service/resource + why
- Evidence: 2-5 bullets from observations or tool results
- Blast Radius: what might also be affected
- Next Actions: 3-7 steps, lowest-risk first
- Risks / Rollback: 1-2 bullets if relevant
- Confidence: High / Medium / Low and what would increase confidence

When the user asks a simple question, keep it concise.
When the user asks for operational help, be structured and action-oriented.
"""
        sub_agents = [
            agent
            for agent in [aws_cost_agent, aws_core_agent, kubernetes_agent]
            if agent is not None
        ]

    logger.info(
        f"Root agent initializing: brand={brand}, local_simple_mode={local_simple_mode}, "
        f"cost_agent={bool(aws_cost_agent)}, core_agent={bool(aws_core_agent)}, "
        f"kubernetes_agent={bool(kubernetes_agent)}"
    )

    return Agent(
        name="sre_agent",
        model=get_configured_model(),
        instruction=instruction,
        description=(
            "SRE assistant for operational tasks, AWS infrastructure ops, AWS cost optimization, "
            "and Kubernetes operations with specialized sub-agents."
        ),
        sub_agents=sub_agents,
    )


root_agent = _create_root_agent()
