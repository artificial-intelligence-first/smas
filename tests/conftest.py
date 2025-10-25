"""Shared test fixtures and stubs."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import types
from typing import Any, Dict

_BASE_DIR = Path(__file__).resolve().parents[1]


class _TestObservabilityLogger:
    """Lightweight stub used to satisfy AGDD imports in unit tests."""

    def __init__(self, run_id: str, agent_name: str | None = None) -> None:
        self.run_id = run_id
        self.agent_name = agent_name or ""
        self.records: list[tuple[str, Dict[str, Any]]] = []

    def log(self, event: str, payload: Dict[str, Any] | None = None) -> None:
        self.records.append((event, payload or {}))


def _ensure_package(name: str) -> types.ModuleType:
    """Ensure a package-like module exists for the given dotted name."""
    module = sys.modules.get(name)
    if module is None:
        module = types.ModuleType(name)
        module.__path__ = []  # type: ignore[attr-defined]
        sys.modules[name] = module
        if "." in name:
            parent_name, child_name = name.rsplit(".", 1)
            parent_module = _ensure_package(parent_name)
            setattr(parent_module, child_name, module)
    return module


def _register_alias(alias: str, relative_path: str) -> None:
    """Register an import alias that maps to a hyphenated agent directory."""
    module_path = _BASE_DIR / relative_path
    spec = importlib.util.spec_from_file_location(alias, module_path)
    if not spec or not spec.loader:
        raise ImportError(f"Cannot load module at {module_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]

    parts = alias.split(".")
    for i in range(1, len(parts)):
        parent_name = ".".join(parts[:i])
        parent_module = _ensure_package(parent_name)
        child_name = parts[i]
        if not hasattr(parent_module, child_name):
            setattr(parent_module, child_name, None)

    sys.modules[alias] = module
    if len(parts) > 1:
        parent_module = _ensure_package(".".join(parts[:-1]))
        setattr(parent_module, parts[-1], module)


def _install_agdd_stubs() -> None:
    """Install stub modules for agdd imports."""
    _ensure_package("agdd")

    observability_pkg = _ensure_package("agdd.observability")
    logger_module = types.ModuleType("agdd.observability.logger")
    logger_module.ObservabilityLogger = _TestObservabilityLogger
    observability_pkg.logger = logger_module
    sys.modules["agdd.observability.logger"] = logger_module

    runners_pkg = _ensure_package("agdd.runners")
    agent_runner_module = types.ModuleType("agdd.runners.agent_runner")

    def _default_invoke_sag(*args: Any, **kwargs: Any) -> Dict[str, Any]:
        raise NotImplementedError("invoke_sag stub must be patched in tests.")

    agent_runner_module.invoke_sag = _default_invoke_sag  # type: ignore[attr-defined]
    runners_pkg.agent_runner = agent_runner_module
    sys.modules["agdd.runners.agent_runner"] = agent_runner_module


def _register_agent_module_aliases() -> None:
    """Expose agent modules via underscore-based import paths for tests."""
    _ensure_package("catalog")
    _ensure_package("catalog.agents")
    _ensure_package("catalog.agents.main")
    _ensure_package("catalog.agents.sub")

    _register_alias(
        "catalog.agents.main.ssot_manager_mag.code.orchestrator",
        "catalog/agents/main/ssot-manager-mag/code/orchestrator.py",
    )
    _register_alias(
        "catalog.agents.sub.content_retriever_sag.code.retriever",
        "catalog/agents/sub/content-retriever-sag/code/retriever.py",
    )
    _register_alias(
        "catalog.agents.sub.content_validator_sag.code.validator",
        "catalog/agents/sub/content-validator-sag/code/validator.py",
    )
    _register_alias(
        "catalog.agents.sub.taxonomy_manager_sag.code.taxonomy",
        "catalog/agents/sub/taxonomy-manager-sag/code/taxonomy.py",
    )
    _register_alias(
        "catalog.agents.sub.crossref_analyzer_sag.code.analyzer",
        "catalog/agents/sub/crossref-analyzer-sag/code/analyzer.py",
    )
    _register_alias(
        "catalog.agents.sub.content_updater_sag.code.updater",
        "catalog/agents/sub/content-updater-sag/code/updater.py",
    )


_install_agdd_stubs()
_register_agent_module_aliases()
