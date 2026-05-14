"""
AWS Core Agent - General AWS operations sub-agent.

Provides general AWS infrastructure management and monitoring capabilities
using role-based authentication for cross-account access.

Enhancements (backwards-compatible):
- Appends a small "Mitra/IncidentIQ" operating style layer to the existing system prompt
- Adds optional env flags (safe defaults) without changing behavior
- Improves logging without leaking secrets
"""

from __future__ import annotations

import os
from contextlib import AsyncExitStack
from google.adk.agents import Agent

from ...utils import load_instruction_from_file, get_logger, get_configured_model

logger = get_logger(__name__)


def _extra_instruction_layer() -> str:
    """
    Small additive instruction layer to make the assistant's behavior more
    enterprise/incident-focused, WITHOUT changing tool behavior.

    Controlled by env:
      - SRE_APPEND_PROMPT_LAYER=true|false  (default true)
      - SRE_ASSISTANT_BRAND=IncidentIQ      (default IncidentIQ)
    """
    enabled = os.getenv("SRE_APPEND_PROMPT_LAYER", "true").lower() == "true"
    if not enabled:
        return ""

    brand = os.getenv("SRE_ASSISTANT_BRAND", "IncidentIQ")

    return f"""

--- Additional Operating Rules ({brand}) ---
When you use tools, summarize findings in an "Evidence" section.
Prefer read-only investigation first (describe/list/status), then propose lowest-risk next actions.
If an action might be disruptive, ask for explicit confirmation before recommending it.

Default output for operational help:
- Summary (1–2 lines)
- Evidence (2–6 bullets from tool results)
- Likely Cause (short, if applicable)
- Next Actions (3–7 steps, lowest-risk first)
- Confidence (High/Medium/Low + what would increase confidence)
"""


def create_aws_core_agent():
    """
    Create AWS Core Operations agent (sync version for ADK).

    Returns:
        Agent: Configured AWS core agent or None if creation fails
    """
    try:
        from .tools.aws_core_tools import (
            get_caller_identity,
            list_s3_buckets,
            list_ec2_instances,
            list_rds_instances,
            get_aws_regions,
            get_account_summary,
            test_aws_connectivity,
        )

        current_dir = os.path.dirname(os.path.abspath(__file__))

        base_prompt = load_instruction_from_file(
            os.path.join(current_dir, "prompts", "aws_core_agent_system_prompt.md")
        )
        instruction = base_prompt + _extra_instruction_layer()

        tools = [
            get_caller_identity,
            list_s3_buckets,
            list_ec2_instances,
            list_rds_instances,
            get_aws_regions,
            get_account_summary,
            test_aws_connectivity,
        ]

        agent = Agent(
            name="aws_core_agent",
            model=get_configured_model(),
            description=(
                "Specialized agent for general AWS infrastructure operations and cross-account management. "
                "Handles EC2, S3, RDS discovery, account summaries, and connectivity testing."
            ),
            instruction=instruction,
            tools=tools,
        )

        logger.info(f"AWS core agent created (tools={len(tools)})")
        return agent

    except Exception as e:
        # Keep prior behavior (return None), but improve debugging
        logger.warning(f"Failed to create AWS core agent: {e}", exc_info=True)
        return None


async def get_aws_core_agent():
    """
    Create AWS Core Operations agent (async version for backward compatibility).

    Returns:
        Agent: Configured AWS core agent
        AsyncExitStack: Exit stack for cleanup
    """
    exit_stack = AsyncExitStack()

    try:
        agent = create_aws_core_agent()
        if agent is None:
            raise Exception("Failed to create AWS core agent")

        return agent, exit_stack

    except Exception as e:
        await exit_stack.aclose()
        raise Exception(f"Failed to create AWS core agent: {e}")
