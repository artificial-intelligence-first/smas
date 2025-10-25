"""Utility functions for API server."""

from __future__ import annotations

import importlib.util
import secrets
import time
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable, Dict


def generate_run_id(prefix: str = "api") -> str:
    """Generate a unique run ID for tracking requests."""
    timestamp = int(time.time() * 1000)
    random_suffix = secrets.token_hex(4)
    return f"{prefix}-{timestamp}-{random_suffix}"


def build_context(run_id: str | None = None) -> Dict[str, Any]:
    """Build execution context for agent invocation."""
    if run_id is None:
        run_id = generate_run_id()

    return {
        "run_id": run_id,
        "sags_invoked": [],
    }


@lru_cache(maxsize=1)
def load_orchestrator() -> Callable:
    """Dynamically load the orchestrator run function."""
    # Find repository root
    current_file = Path(__file__)
    repo_root = current_file.parent.parent.parent

    # Load orchestrator module
    orchestrator_path = (
        repo_root
        / "catalog"
        / "agents"
        / "main"
        / "ssot-manager-mag"
        / "code"
        / "orchestrator.py"
    )

    spec = importlib.util.spec_from_file_location("orchestrator", orchestrator_path)
    if not spec or not spec.loader:
        raise ImportError(f"Cannot load orchestrator from {orchestrator_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]

    return module.run
