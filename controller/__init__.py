"""Audited, local-only export controller for AstraCottle.

The package intentionally contains no model transport or network client.  The
public API is :func:`inspect_proposal` and :func:`execute`.
"""

from .core import ControllerError, execute, inspect_proposal

__all__ = ["ControllerError", "execute", "inspect_proposal"]
