"""Content Validator SAG - Markdown linting and link validation."""

from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Optional, Tuple

from agdd.observability.logger import ObservabilityLogger


def _resolve_repo_relative_path(repo_root: str, target: str) -> Tuple[str, str]:
  """Return sanitized repo-relative and absolute paths for the given target."""
  if not target:
    raise ValueError("target_file is required")
  if os.path.isabs(target):
    raise ValueError("target_file must be relative")

  normalized = os.path.normpath(target)
  if normalized in ("", "."):
    raise ValueError("target_file must reference content within the repository")
  if normalized.startswith(".."):
    raise ValueError("target_file escapes repository")

  repo_root_real = os.path.realpath(repo_root)
  absolute_path = os.path.realpath(os.path.join(repo_root_real, normalized))
  if os.path.commonpath([repo_root_real, absolute_path]) != repo_root_real:
    raise ValueError("target_file escapes repository")

  return normalized, absolute_path


def _sanitize_category(category: str) -> str:
  """Ensure category inputs cannot traverse directories."""
  if not category:
    raise ValueError("category is required for category-scoped validation")
  if os.path.isabs(category):
    raise ValueError("category must be relative")
  normalized = os.path.normpath(category)
  if normalized in ("", ".") or normalized.startswith("..") or os.path.sep in normalized:
    raise ValueError("category escapes repository scope")
  return normalized


def run(payload: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
  """Validate Markdown quality and links for provided content or repository."""
  run_id = context.get("run_id", "sag-unknown")
  logger = ObservabilityLogger(run_id, agent_name="ContentValidatorSAG")

  logger.log("start", {"payload": payload})

  errors: List[Dict[str, Any]] = []
  warnings: List[Dict[str, Any]] = []

  scope = payload.get("scope", "all")
  content = payload.get("content")
  target_file = payload.get("target_file")

  if content:
    markdown_errors, markdown_warnings = _validate_markdown(
      content,
      target_file or "inline",
    )
    errors.extend(markdown_errors)
    warnings.extend(markdown_warnings)
    warnings.extend(_check_links(content, target_file or "inline"))
    total_files = 1
  else:
    ssot_repo_path = os.getenv("SSOT_REPO_PATH", "/path/to/ssot")
    repo_root = os.path.realpath(ssot_repo_path)
    safe_target: Optional[str] = None
    if target_file:
      safe_target, _ = _resolve_repo_relative_path(repo_root, target_file)
    safe_category = payload.get("category")
    if scope == "category":
      safe_category = _sanitize_category(safe_category or "")
    errors, repo_warnings = _validate_repository(
      repo_root,
      scope,
      logger,
      category=safe_category,
      target_file=safe_target,
    )
    warnings.extend(repo_warnings)
    total_files = _count_files(
      repo_root,
      scope,
      category=safe_category,
      target_file=safe_target,
    )

  passed = len(errors) == 0

  logger.log(
    "end",
    {
      "passed": passed,
      "errors": len(errors),
      "warnings": len(warnings),
    },
  )

  return {
    "passed": passed,
    "errors": errors,
    "warnings": warnings,
    "total_files": total_files,
  }


def _validate_markdown(content: str, file_name: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
  """Validate Markdown content for simple lint rules."""
  errors: List[Dict[str, Any]] = []
  warnings: List[Dict[str, Any]] = []
  lines = content.split("\n")

  for index, line in enumerate(lines, 1):
    if line.endswith(" "):
      warnings.append(
        {
          "file": file_name,
          "line": index,
          "message": "Trailing whitespace found",
          "severity": "warning",
        }
      )

    if line.startswith("#"):
      match = re.match(r"^#+", line)
      if match and len(match.group()) > 6:
        errors.append(
          {
            "file": file_name,
            "line": index,
            "message": f"Heading level too deep: {len(match.group())}",
            "severity": "error",
          }
        )

  return errors, warnings


def _check_links(content: str, file_name: str) -> List[Dict[str, Any]]:
  """Check Markdown links and flag relative references for review."""
  warnings: List[Dict[str, Any]] = []
  link_pattern = r"\[([^\]]+)\]\(([^\)]+)\)"

  for match in re.finditer(link_pattern, content):
    link_url = match.group(2)
    if link_url.startswith("./") or link_url.startswith("../"):
      warnings.append(
        {
          "file": file_name,
          "message": f"Internal link '{link_url}' needs verification",
          "severity": "info",
        }
      )

  return warnings


def _validate_repository(
  repo_path: str,
  scope: str,
  logger: ObservabilityLogger,
  *,
  category: Optional[str] = None,
  target_file: Optional[str] = None,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
  """Validate all Markdown files in the repository for the given scope."""
  all_errors: List[Dict[str, Any]] = []
  all_warnings: List[Dict[str, Any]] = []
  repo_root = os.path.realpath(repo_path)

  if scope == "file":
    if not target_file:
      raise ValueError("target_file is required when scope is 'file'")
    relative_path, file_path = _resolve_repo_relative_path(repo_root, target_file)
    if os.path.isfile(file_path):
      with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()
      file_errors, file_warnings = _validate_markdown(content, relative_path)
      all_errors.extend(file_errors)
      all_warnings.extend(file_warnings)
      all_warnings.extend(_check_links(content, relative_path))

    logger.log(
      "validation_complete",
      {
        "errors": len(all_errors),
        "warnings": len(all_warnings),
      },
    )
    return all_errors, all_warnings

  if scope == "category" and category:
    search_dirs = [category]
  elif scope == "all":
    search_dirs = ["files", "engineering", "tools", "platforms", "_meta"]
  else:
    search_dirs = []

  for dir_name in search_dirs:
    dir_path = os.path.join(repo_root, dir_name)
    if not os.path.exists(dir_path):
      continue

    for root, _, files in os.walk(dir_path):
      for filename in files:
        if not filename.endswith(".md"):
          continue

        file_path = os.path.join(root, filename)
        with open(file_path, "r", encoding="utf-8") as file:
          content = file.read()

        rel_path = os.path.relpath(file_path, repo_root)
        file_errors, file_warnings = _validate_markdown(content, rel_path)
        all_errors.extend(file_errors)
        all_warnings.extend(file_warnings)
        all_warnings.extend(_check_links(content, rel_path))

  logger.log(
    "validation_complete",
    {
      "errors": len(all_errors),
      "warnings": len(all_warnings),
    },
  )

  return all_errors, all_warnings


def _count_files(
  repo_path: str,
  scope: str,
  *,
  category: Optional[str] = None,
  target_file: Optional[str] = None,
) -> int:
  """Count Markdown files in scope."""
  repo_root = os.path.realpath(repo_path)
  if scope == "file":
    if not target_file:
      raise ValueError("target_file is required when scope is 'file'")
    _, file_path = _resolve_repo_relative_path(repo_root, target_file)
    return int(os.path.isfile(file_path))

  if scope == "category" and category:
    search_dirs = [category]
  elif scope == "all":
    search_dirs = ["files", "engineering", "tools", "platforms", "_meta"]
  else:
    return 0

  count = 0
  for dir_name in search_dirs:
    dir_path = os.path.join(repo_root, dir_name)
    if os.path.exists(dir_path):
      for _, _, files in os.walk(dir_path):
        count += sum(1 for filename in files if filename.endswith(".md"))

  return count
