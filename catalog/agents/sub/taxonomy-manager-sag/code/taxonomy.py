"""Taxonomy Manager SAG - Manage `_meta/TAXONOMY.md` terminology."""

from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Set

from agdd.observability.logger import ObservabilityLogger


def run(payload: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
  """Execute terminology management operations against the SSOT taxonomy."""
  run_id = context.get("run_id", "sag-unknown")
  logger = ObservabilityLogger(run_id, agent_name="TaxonomyManagerSAG")

  logger.log("start", {"operation": payload.get("operation")})

  operation = payload.get("operation", "validate")
  ssot_repo_path = os.getenv("SSOT_REPO_PATH", "/path/to/ssot")
  taxonomy_path = os.path.join(ssot_repo_path, "_meta", "TAXONOMY.md")

  controlled_terms = _load_taxonomy(taxonomy_path, logger)

  if operation == "validate":
    content = payload.get("content", "")
    issues = _validate_terms(content, controlled_terms, logger)
    return {
      "operation": "validate",
      "passed": len(issues) == 0,
      "issues": issues,
    }

  if operation == "analyze":
    usage = _analyze_term_usage(ssot_repo_path, controlled_terms, logger)
    return {
      "operation": "analyze",
      "term_usage": usage,
      "recommendations": _generate_recommendations(usage, controlled_terms),
    }

  if operation == "add":
    new_term = payload.get("term")
    logger.log("add_term", {"term": new_term})
    return {
      "operation": "add",
      "success": True,
      "term": new_term,
    }

  raise ValueError(f"Unknown operation: {operation}")


def _load_taxonomy(taxonomy_path: str, logger: ObservabilityLogger) -> Set[str]:
  """Load controlled vocabulary terms from the taxonomy file."""
  if not os.path.exists(taxonomy_path):
    logger.log("warning", {"message": "TAXONOMY.md not found"})
    return set()

  with open(taxonomy_path, "r", encoding="utf-8") as file:
    content = file.read()

  terms: Set[str] = set()
  for line in content.split("\n"):
    match = re.match(r"^-\s+\*\*([^*]+)\*\*:", line)
    if match:
      terms.add(match.group(1).strip().lower())
      continue

    heading_match = re.match(r"^###\s+(.+)$", line.strip())
    if heading_match:
      heading_term = heading_match.group(1).strip().lower()
      # Normalize whitespace to hyphen for consistency with tag usage.
      heading_term = re.sub(r"\s+", "-", heading_term)
      if re.search(r"[a-z]", heading_term):
        terms.add(heading_term)

  logger.log("taxonomy_loaded", {"term_count": len(terms)})
  return terms


def _validate_terms(
  content: str, controlled_terms: Set[str], logger: ObservabilityLogger
) -> List[Dict[str, Any]]:
  """Validate terms used in content against the controlled vocabulary."""
  issues: List[Dict[str, Any]] = []

  candidates = _extract_taxonomy_candidates(content)

  for term in candidates:
    if term in controlled_terms:
      continue

    suggestions = _find_similar_terms(term, controlled_terms)
    issues.append(
      {
        "term": term,
        "message": f"'{term}' not in controlled vocabulary",
        "suggestions": suggestions,
      }
    )

  logger.log("validation_complete", {"issues_found": len(issues)})
  return issues


def _find_similar_terms(term: str, controlled_terms: Set[str]) -> List[str]:
  """Find similar controlled vocabulary terms by prefix comparison."""
  similar = [candidate for candidate in controlled_terms if candidate.startswith(term[:3])]
  return similar[:3]


def _analyze_term_usage(
  repo_path: str, controlled_terms: Set[str], logger: ObservabilityLogger
) -> Dict[str, int]:
  """Analyze how frequently each controlled term appears in the repository."""
  usage = {term: 0 for term in controlled_terms}

  for root, _, files in os.walk(repo_path):
    for filename in files:
      if not filename.endswith(".md"):
        continue

      file_path = os.path.join(root, filename)
      with open(file_path, "r", encoding="utf-8") as file:
        content = file.read().lower()

      for term in controlled_terms:
        usage[term] += content.count(term)

  logger.log("usage_analyzed", {"total_terms": len(usage)})
  return usage


def _generate_recommendations(usage: Dict[str, int], controlled_terms: Set[str]) -> List[str]:
  """Generate usage recommendations for taxonomy maintenance."""
  recommendations: List[str] = []

  unused = [term for term, count in usage.items() if count == 0]
  if unused:
    recommendations.append(f"{len(unused)} unused terms: {', '.join(unused[:5])}")

  frequent = sorted(usage.items(), key=lambda item: item[1], reverse=True)[:5]
  recommendations.append(
    "Frequent terms: "
    + ", ".join(f"{term}({count})" for term, count in frequent)
  )

  return recommendations


def _extract_taxonomy_candidates(content: str) -> List[str]:
  """Extract candidate taxonomy terms from document front matter."""
  lines = content.splitlines()
  if not lines or lines[0].strip() != "---":
    return []

  front_matter: List[str] = []
  for line in lines[1:]:
    if line.strip() == "---":
      break
    front_matter.append(line)

  candidates: List[str] = []
  in_tags_block = False
  for line in front_matter:
    stripped = line.strip()

    if stripped.startswith("tags:"):
      remainder = stripped[len("tags:") :].strip()

      if remainder.startswith("[") and remainder.endswith("]"):
        inside = remainder[1:-1]
        parts = [part.strip().strip("'\"") for part in inside.split(",")]
        candidates.extend(term.lower() for term in parts if term)
        in_tags_block = False
      elif remainder:
        token = remainder.strip("'\"")
        if token:
          candidates.append(token.lower())
        in_tags_block = False
      else:
        in_tags_block = True
      continue

    if in_tags_block:
      if stripped.startswith("-"):
        token = stripped[1:].strip().strip("'\"")
        if token:
          candidates.append(token.lower())
      elif stripped:
        in_tags_block = False

  return candidates
