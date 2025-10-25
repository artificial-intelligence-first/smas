"""Cross Reference Analyzer SAG - Analyze inter-document references."""

from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Set

from agdd.observability.logger import ObservabilityLogger


def run(payload: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze inter-document references across the SSOT repository."""
    run_id = context.get("run_id", "sag-unknown")
    logger = ObservabilityLogger(run_id, agent_name="CrossRefAnalyzerSAG")

    logger.log("start", {})

    ssot_repo_path = os.getenv("SSOT_REPO_PATH", "/path/to/ssot")

    ref_graph = _build_reference_graph(ssot_repo_path, logger)
    orphans = _detect_orphans(ref_graph, logger)
    cycles = _detect_cycles(ref_graph, logger)

    logger.log(
        "end",
        {
            "total_files": len(ref_graph),
            "orphans": len(orphans),
            "cycles": len(cycles),
        },
    )

    return {
        "reference_graph": {file: sorted(refs) for file, refs in ref_graph.items()},
        "orphans": sorted(orphans),
        "cycles": cycles,
        "statistics": {
            "total_files": len(ref_graph),
            "total_references": sum(len(refs) for refs in ref_graph.values()),
            "orphan_count": len(orphans),
        },
    }


def _build_reference_graph(
    repo_path: str, logger: ObservabilityLogger
) -> Dict[str, Set[str]]:
    """Build a graph of Markdown cross references."""
    graph: Dict[str, Set[str]] = {}

    for root, _, files in os.walk(repo_path):
        for filename in files:
            if not filename.endswith(".md"):
                continue

            file_path = os.path.join(root, filename)
            rel_path = os.path.relpath(file_path, repo_path)

            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()

            refs = _extract_references(content, rel_path)
            graph[rel_path] = refs

    logger.log("graph_built", {"nodes": len(graph)})
    return graph


def _extract_references(content: str, source_file: str) -> Set[str]:
    """Extract Markdown link targets as repository-relative paths."""
    refs: Set[str] = set()
    link_pattern = r"\[([^\]]+)\]\(([^\)]+)\)"

    for match in re.finditer(link_pattern, content):
        link_url = match.group(2)

        if link_url.startswith("http"):
            continue

        if link_url.startswith("/"):
            target_path = os.path.normpath(link_url.lstrip("/"))
        else:
            source_dir = os.path.dirname(source_file)
            target_path = os.path.normpath(os.path.join(source_dir, link_url))

        target_path = target_path.split("#")[0]

        if target_path.endswith(".md"):
            refs.add(target_path)

    return refs


def _detect_orphans(
    graph: Dict[str, Set[str]], logger: ObservabilityLogger
) -> List[str]:
    """Detect Markdown files that are never referenced by others."""
    referenced: Set[str] = set()
    for refs in graph.values():
        referenced.update(refs)

    all_files = set(graph.keys())
    orphans = [
        path for path in all_files - referenced if not path.endswith("README.md")
    ]

    logger.log("orphans_detected", {"count": len(orphans)})
    return orphans


def _detect_cycles(
    graph: Dict[str, Set[str]], logger: ObservabilityLogger
) -> List[List[str]]:
    """Detect circular references using DFS recursion."""
    cycles: List[List[str]] = []
    visited: Set[str] = set()
    recursion_stack: Set[str] = set()

    def dfs(node: str, path: List[str]) -> None:
        visited.add(node)
        recursion_stack.add(node)
        path.append(node)

        for neighbor in graph.get(node, set()):
            if neighbor not in visited:
                dfs(neighbor, path[:])
            elif neighbor in recursion_stack:
                cycle_start = path.index(neighbor)
                cycle = path[cycle_start:] + [neighbor]
                cycles.append(cycle)

        recursion_stack.remove(node)

    for node in graph:
        if node not in visited:
            dfs(node, [])

    logger.log("cycles_detected", {"count": len(cycles)})
    return cycles
