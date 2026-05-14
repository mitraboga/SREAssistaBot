__all__ = ["create_aws_cost_agent", "get_aws_cost_agent"]


def __getattr__(name):
    if name in __all__:
        from . import agent

        return getattr(agent, name)
    raise AttributeError(name)
