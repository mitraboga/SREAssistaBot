__all__ = ["_create_root_agent"]


def __getattr__(name):
    if name == "_create_root_agent":
        from .agent import _create_root_agent

        return _create_root_agent
    raise AttributeError(name)
