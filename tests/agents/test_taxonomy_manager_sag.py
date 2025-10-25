"""
Tests for TaxonomyManagerSAG
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from catalog.agents.sub.taxonomy_manager_sag.code.taxonomy import (
    run,
    _extract_taxonomy_candidates,
)


class TestTaxonomyManagerSAG:
    """Test suite for TaxonomyManagerSAG"""

    def test_validate_passes_with_known_terms(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Validation should pass when all tags exist in taxonomy"""
        repo_root = tmp_path / "repo"
        taxonomy_file = repo_root / "_meta" / "TAXONOMY.md"
        taxonomy_file.parent.mkdir(parents=True)
        taxonomy_file.write_text("- **agents**: Description\n", encoding="utf-8")

        monkeypatch.setenv("SSOT_REPO_PATH", str(repo_root))

        payload = {
            "operation": "validate",
            "content": """---
tags: ['agents']
---""",
        }
        context = {"run_id": "taxonomy-001"}

        result = run(payload, context)

        assert result["passed"] is True
        assert result["issues"] == []

    def test_validate_reports_unknown_terms(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Unknown tags should yield issues with suggestions"""
        repo_root = tmp_path / "repo"
        taxonomy_file = repo_root / "_meta" / "TAXONOMY.md"
        taxonomy_file.parent.mkdir(parents=True)
        taxonomy_file.write_text("- **agents**: Description\n", encoding="utf-8")

        monkeypatch.setenv("SSOT_REPO_PATH", str(repo_root))

        payload = {
            "operation": "validate",
            "content": """---
tags: ['agentz']
---""",
        }
        context = {"run_id": "taxonomy-002"}

        result = run(payload, context)

        assert result["passed"] is False
        assert result["issues"]
        assert result["issues"][0]["suggestions"]

    def test_analyze_counts_term_usage(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Analyze operation should count taxonomy term occurrences"""
        repo_root = tmp_path / "repo"
        taxonomy_file = repo_root / "_meta" / "TAXONOMY.md"
        taxonomy_file.parent.mkdir(parents=True)
        taxonomy_file.write_text("- **agents**: Description\n", encoding="utf-8")

        docs_dir = repo_root / "files"
        docs_dir.mkdir(parents=True)
        (docs_dir / "doc.md").write_text("Agents are important.\nagents improve docs.", encoding="utf-8")

        monkeypatch.setenv("SSOT_REPO_PATH", str(repo_root))

        payload = {"operation": "analyze"}
        context = {"run_id": "taxonomy-003"}

        result = run(payload, context)

        assert result["term_usage"]["agents"] >= 2
        assert result["recommendations"]

    def test_unknown_operation_raises(self) -> None:
        """Unsupported operation should raise ValueError"""
        with pytest.raises(ValueError):
            run({"operation": "delete"}, {"run_id": "taxonomy-004"})

    def test_extract_taxonomy_candidates(self) -> None:
        """Parsing front matter should capture tag values"""
        content = """---
tags:
  - agents
  - best-practices
---

# Body
"""
        candidates = _extract_taxonomy_candidates(content)

        assert "agents" in candidates
        assert "best-practices" in candidates
