"""Stub observability logger for AGDD."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple


class ObservabilityLogger:
    """Minimal logger that records events for inspection."""

    def __init__(self, run_id: str, agent_name: str | None = None) -> None:
        self.run_id = run_id
        self.agent_name = agent_name or ""
        self.events: List[Tuple[str, Dict[str, Any]]] = []

    def log(self, event: str, payload: Dict[str, Any] | None = None) -> None:
        """Record an event for debugging."""
        self.events.append((event, payload or {}))
