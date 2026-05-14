__all__ = ["create_kubernetes_agent", "get_kubernetes_agent"]


def __getattr__(name):
    if name in __all__:
        from .agent import create_kubernetes_agent, get_kubernetes_agent

        return {
            "create_kubernetes_agent": create_kubernetes_agent,
            "get_kubernetes_agent": get_kubernetes_agent,
        }[name]
    raise AttributeError(name)
