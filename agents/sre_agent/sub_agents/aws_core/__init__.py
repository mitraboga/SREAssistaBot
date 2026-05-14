"""
AWS Core Sub-Agent - Export agent creation functions.
"""

__all__ = [
    "create_aws_core_agent",
    "get_aws_core_agent",
]


def __getattr__(name):
    if name in __all__:
        from . import agent

        return getattr(agent, name)
    raise AttributeError(name)
