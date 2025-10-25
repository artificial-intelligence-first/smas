"""Content Retriever SAG - Search information from the SSOT repository."""

from __future__ import annotations

import os
from typing import Any, Dict, List

from agdd.observability.logger import ObservabilityLogger


def _sanitize_category(category: str) -> str:
    """Ensure category inputs do not escape the repository boundaries."""
    if not category:
        raise ValueError("category must be provided")
    if os.path.isabs(category):
        raise ValueError("category must be relative")

    normalized = os.path.normpath(category)
    if (
        normalized in ("", ".")
        or normalized.startswith("..")
        or os.path.sep in normalized
    ):
        raise ValueError("category escapes repository scope")

    return normalized


def run(payload: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Search relevant information from the SSOT repository."""
    run_id = context.get("run_id", "sag-unknown")
    logger = ObservabilityLogger(run_id, agent_name="ContentRetrieverSAG")

    logger.log("start", {"query": payload})

    ssot_repo_path = os.getenv("SSOT_REPO_PATH", "/path/to/ssot")

    category = payload.get("category", "all")
    topic = payload.get("topic", "")
    question = payload.get("question", "")

    sources = _search_files(ssot_repo_path, category, topic, question, logger)
    answer = _generate_answer(sources, question, logger)
    confidence = _calculate_confidence(sources, question)

    logger.log(
        "end",
        {
            "sources_found": len(sources),
            "confidence": confidence,
        },
    )

    return {
        "question": question,
        "answer": answer,
        "sources": sources,
        "confidence": confidence,
    }


def _search_files(
    repo_path: str,
    category: str,
    topic: str,
    question: str,
    logger: ObservabilityLogger,
) -> List[Dict[str, Any]]:
    """Search Markdown files in the repository."""
    sources: List[Dict[str, Any]] = []

    if category == "all":
        search_dirs = ["files", "engineering", "tools", "platforms", "_meta"]
    else:
        search_dirs = [_sanitize_category(category)]

    keywords = [topic.lower()] if topic else []
    keywords.extend(question.lower().split())

    for dir_name in search_dirs:
        dir_path = os.path.join(repo_path, dir_name)
        if not os.path.exists(dir_path):
            continue

        for root, _, files in os.walk(dir_path):
            for filename in files:
                if not filename.endswith(".md"):
                    continue

                file_path = os.path.join(root, filename)
                rel_path = os.path.relpath(file_path, repo_path)

                with open(file_path, "r", encoding="utf-8") as file:
                    content = file.read()

                relevance = _calculate_relevance(content, keywords)
                if relevance > 0.1:
                    sources.append(
                        {
                            "file": rel_path,
                            "section": _extract_relevant_section(content, keywords),
                            "content": content[:500],
                            "relevance": relevance,
                        }
                    )

    sources.sort(key=lambda item: item["relevance"], reverse=True)
    logger.log("search_complete", {"total_sources": len(sources)})

    return sources[:5]


def _calculate_relevance(content: str, keywords: List[str]) -> float:
    """Calculate content relevance score based on keyword hits."""
    if not keywords:
        return 0.0

    content_lower = content.lower()
    matches = sum(1 for keyword in keywords if keyword in content_lower)
    return matches / len(keywords)


def _extract_relevant_section(content: str, keywords: List[str]) -> str:
    """Extract the heading closest to the first keyword occurrence."""
    lines = content.split("\n")

    for index, line in enumerate(lines):
        if any(keyword in line.lower() for keyword in keywords):
            for heading_index in range(index, -1, -1):
                if lines[heading_index].startswith("#"):
                    return lines[heading_index].strip()
            break

    return "Introduction"


def _generate_answer(
    sources: List[Dict[str, Any]], question: str, logger: ObservabilityLogger
) -> str:
    """Generate an answer using the highest ranked source."""
    if not sources:
        return "No relevant information found."

    top_source = sources[0]
    answer = (
        f"Relevant information found in {top_source['file']}, "
        f"{top_source['section']} section.\n\n"
    )
    answer += top_source["content"]

    logger.log("answer_generated", {"source_file": top_source["file"]})
    return answer


def _calculate_confidence(sources: List[Dict[str, Any]], question: str) -> float:
    """Use the top source relevance score as a proxy for confidence."""
    if not sources:
        return 0.0

    return min(sources[0]["relevance"], 1.0)
