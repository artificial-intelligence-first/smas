"""Agent runner stub for AGDD."""

from __future__ import annotations

import importlib.util
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

_AGENT_MODULES = {
    "content-retriever-sag": ("sub", "retriever"),
    "content-validator-sag": ("sub", "validator"),
    "taxonomy-manager-sag": ("sub", "taxonomy"),
    "crossref-analyzer-sag": ("sub", "analyzer"),
    "content-updater-sag": ("sub", "updater"),
}


def _discover_repo_root() -> Path:
    """Locate the SSOT Manager repository root."""
    repo_root = Path(__file__).resolve().parents[2]
    candidates = [
        Path.cwd(),
        repo_root,
        repo_root.parent,
    ]
    for candidate in candidates:
        if (candidate / "catalog" / "agents").exists():
            return candidate
    raise RuntimeError("Unable to locate SSOT Manager repository root for AGDD stub.")


@lru_cache(maxsize=None)
def _load_agent_module(agent_slug: str):
    """Load the Python module for a given agent slug."""
    if agent_slug not in _AGENT_MODULES:
        raise ValueError(f"Unknown agent slug: {agent_slug}")

    group, module_name = _AGENT_MODULES[agent_slug]
    repo_root = _discover_repo_root()
    module_path = (
        repo_root
        / "catalog"
        / "agents"
        / group
        / agent_slug
        / "code"
        / f"{module_name}.py"
    )

    if not module_path.exists():
        raise FileNotFoundError(f"Agent module not found at {module_path}")

    spec = importlib.util.spec_from_file_location(
        f"{agent_slug}.{module_name}", module_path
    )
    if not spec or not spec.loader:
        raise ImportError(f"Unable to load module for agent '{agent_slug}'")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def invoke_sag(
    agent_slug: str,
    payload: Dict[str, Any],
    parent_context: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Invoke a Sub Agent by loading its run() function."""
    module = _load_agent_module(agent_slug)
    if not hasattr(module, "run"):
        raise AttributeError(f"Agent '{agent_slug}' does not define a run() function")

    context = parent_context if parent_context is not None else {}
    return module.run(payload, context)
