"""Legacy SyteLine 8 adapter (planned).

This package is intentionally lightweight for now: it provides the module boundary and
placeholder client/config types without wiring it into production connectors yet.
"""

from .client import SyteLine8Client, SyteLine8Config

__all__ = ["SyteLine8Client", "SyteLine8Config"]

