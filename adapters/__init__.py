"""Adapters for feeding reviewed cases into the local controller.

There is intentionally no model or network adapter in this package.
"""

from .local import replay_case

__all__ = ["replay_case"]
