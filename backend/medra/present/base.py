"""Layer 3 interface. A presenter turns mining output into visual decisions
(which bubbles, how big, what to underline). It does no mining itself."""

from __future__ import annotations

from typing import Protocol

from medra.contracts import MiningUpdate, ViewUpdate


class Presenter(Protocol):
    def present(self, update: MiningUpdate) -> ViewUpdate | None:
        """Return the diff for the dashboard, or None if nothing visible changed."""
        ...
