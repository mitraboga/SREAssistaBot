"""
AWS Cost Agent - Self-contained AWS cost analysis sub-agent.

Enhancements (backwards-compatible):
- Appends a small "Mitra/IncidentIQ" reporting style layer to the existing system prompt
- Keeps the same tool list + agent name + function names
- Improves logging for easier debugging
"""

from __future__ import annotations

import os
from contextlib import AsyncExitStack
from google.adk.agents import Agent

from ...utils import load_instruction_from_file, get_logger, get_configured_model

logger = get_logger(__name__)


def _extra_instruction_layer() -> str:
    """
    Additive layer for consistent, recruiter-grade cost outputs.

    Controlled by env:
      - SRE_APPEND_PROMPT_LAYER=true|false (default true)
      - SRE_ASSISTANT_BRAND=IncidentIQ     (default IncidentIQ)
    """
    enabled = os.getenv("SRE_APPEND_PROMPT_LAYER", "true").lower() == "true"
    if not enabled:
        return ""

    brand = os.getenv("SRE_ASSISTANT_BRAND", "IncidentIQ")

    return f"""

--- Additional Operating Rules ({brand}) ---
When you answer cost questions, always include:
- Time window (what period you used)
- Key numbers (total, deltas, biggest drivers)
- Recommended actions (ranked by impact and effort)
- Confidence (High/Medium/Low + what data would improve it)

If the user asks "why did cost spike?", prefer:
1) service-level breakdown
2) account-level (if multi-account)
3) tag-level (if tags exist)
4) day-by-day trend
"""


def create_aws_cost_agent():
    """
    Create AWS Cost Analysis agent (sync version for ADK).

    Returns:
        Agent: Configured AWS cost agent or None if creation fails
    """
    try:
        from .tools.aws_cost_tools import (
            get_cost_for_period,
            get_monthly_cost,
            get_cost_excluding_services,
            get_cost_trend,
            get_current_month_cost_excluding_days,
            get_average_daily_cost,
            get_weekend_daily_cost,
            get_weekday_daily_cost,
            get_most_expensive_account,
            get_cost_by_service,
            get_cost_by_tag,
            get_digital_cost_for_month,
            get_current_date_info,
            get_current_month_cost,
            get_previous_month_cost,
            get_last_n_months_trend,
        )

        current_dir = os.path.dirname(os.path.abspath(__file__))

        base_prompt = load_instruction_from_file(
            os.path.join(current_dir, "prompts", "aws_cost_agent_system_prompt.md")
        )
        instruction = base_prompt + _extra_instruction_layer()

        tools = [
            get_cost_for_period,
            get_monthly_cost,
            get_cost_excluding_services,
            get_cost_trend,
            get_current_month_cost_excluding_days,
            get_average_daily_cost,
            get_weekend_daily_cost,
            get_weekday_daily_cost,
            get_most_expensive_account,
            get_cost_by_service,
            get_cost_by_tag,
            get_digital_cost_for_month,
            get_current_date_info,
            get_current_month_cost,
            get_previous_month_cost,
            get_last_n_months_trend,
        ]

        agent = Agent(
            name="aws_cost_agent",
            model=get_configured_model(),
            description=(
                "Specialized agent for AWS cost analysis and optimization. "
                "Handles cost queries, trends, and budget optimization recommendations."
            ),
            instruction=instruction,
            tools=tools,
        )

        logger.info(f"AWS cost agent created (tools={len(tools)})")
        return agent

    except Exception as e:
        logger.warning(f"Failed to create AWS cost agent: {e}", exc_info=True)
        return None


async def get_aws_cost_agent():
    """
    Create AWS Cost Analysis agent (async version for backward compatibility).

    Returns:
        Agent: Configured AWS cost agent
        AsyncExitStack: Exit stack for cleanup
    """
    exit_stack = AsyncExitStack()

    try:
        agent = create_aws_cost_agent()
        if agent is None:
            raise Exception("Failed to create AWS cost agent")

        return agent, exit_stack

    except Exception as e:
        await exit_stack.aclose()
        raise Exception(f"Failed to create AWS cost agent: {e}")
