"""
Kubernetes Operations Agent.

Provides read-only cluster inspection for SRE workflows using kubectl.
"""

from __future__ import annotations

import os
from contextlib import AsyncExitStack

from google.adk.agents import Agent

from ...utils import get_configured_model, get_logger, load_instruction_from_file

logger = get_logger(__name__)


def _extra_instruction_layer() -> str:
    enabled = os.getenv("SRE_APPEND_PROMPT_LAYER", "true").lower() == "true"
    if not enabled:
        return ""

    brand = os.getenv("SRE_ASSISTANT_BRAND", "IncidentIQ")
    return f"""

--- Additional Operating Rules ({brand}) ---
When you use Kubernetes tools, summarize findings in an Evidence section.
Always state namespace and context when available.
Prefer status/list/log checks before proposing rollout or scaling actions.
If kubectl is unavailable, provide the exact local setup step the user needs next.
"""


def create_kubernetes_agent():
    """Create the Kubernetes Operations agent."""
    try:
        from .tools.kubernetes_tools import (
            get_cluster_summary,
            get_current_context,
            get_pod_logs,
            list_contexts,
            list_deployments,
            list_nodes,
            list_pods,
            list_services,
        )

        current_dir = os.path.dirname(os.path.abspath(__file__))
        base_prompt = load_instruction_from_file(
            os.path.join(current_dir, "prompts", "kubernetes_agent_system_prompt.md")
        )
        instruction = base_prompt + _extra_instruction_layer()

        tools = [
            get_current_context,
            list_contexts,
            list_nodes,
            list_pods,
            list_deployments,
            list_services,
            get_pod_logs,
            get_cluster_summary,
        ]

        agent = Agent(
            name="kubernetes_agent",
            model=get_configured_model(),
            description=(
                "Specialized read-only Kubernetes operations agent. Handles cluster summaries, "
                "pod/deployment/service/node status, and recent pod logs."
            ),
            instruction=instruction,
            tools=tools,
        )

        logger.info(f"Kubernetes agent created (tools={len(tools)})")
        return agent
    except Exception as e:
        logger.warning(f"Failed to create Kubernetes agent: {e}", exc_info=True)
        return None


async def get_kubernetes_agent():
    """Create Kubernetes Operations agent with an exit stack for compatibility."""
    exit_stack = AsyncExitStack()
    try:
        agent = create_kubernetes_agent()
        if agent is None:
            raise Exception("Failed to create Kubernetes agent")
        return agent, exit_stack
    except Exception as e:
        await exit_stack.aclose()
        raise Exception(f"Failed to create Kubernetes agent: {e}")
