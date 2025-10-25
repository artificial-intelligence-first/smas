"""
Tests for ContentRetrieverSAG
"""

from __future__ import annotations

from pathlib import Path

import pytest

from catalog.agents.sub.content_retriever_sag.code.retriever import (
    run,
    _calculate_relevance,
    _extract_relevant_section,
)


class TestContentRetrieverSAG:
    """Test suite for ContentRetrieverSAG"""

    def test_run_success(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test successful retrieval"""
        ssot_dir = tmp_path / "ssot"
        ssot_dir.mkdir(parents=True, exist_ok=True)
        files_dir = ssot_dir / "files"
        files_dir.mkdir(parents=True)

        agents_file = files_dir / "AGENTS.md"
        agents_file.write_text("# AGENTS\n\nThis is about agents.", encoding="utf-8")

        payload = {
            "category": "files",
            "topic": "AGENTS",
            "question": "What is AGENTS?",
        }
        context = {"run_id": "test-retriever-001"}

        monkeypatch.setenv("SSOT_REPO_PATH", str(ssot_dir))

        result = run(payload, context)

        assert "answer" in result
        assert "sources" in result
        assert "confidence" in result
        assert result["question"] == "What is AGENTS?"

    def test_calculate_relevance(self) -> None:
        """Test relevance calculation"""
        content = "This document is about AGENTS and best practices."
        keywords = ["agents", "practices"]

        relevance = _calculate_relevance(content, keywords)

        assert relevance == 1.0

    def test_calculate_relevance_partial(self) -> None:
        """Test partial keyword match"""
        content = "This document is about AGENTS only."
        keywords = ["agents", "missing"]

        relevance = _calculate_relevance(content, keywords)

        assert relevance == 0.5

    def test_extract_relevant_section(self) -> None:
        """Test section extraction"""
        content = """# Introduction
This is intro.

# Best Practices
This section has agents information.

# Conclusion
End."""
        keywords = ["agents"]

        section = _extract_relevant_section(content, keywords)

        assert "Best Practices" in section

    def test_no_results_found(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test when no relevant files found"""
        ssot_dir = tmp_path / "ssot-empty"
        ssot_dir.mkdir(parents=True, exist_ok=True)

        payload = {
            "category": "files",
            "topic": "NonExistent",
            "question": "Where is it?",
        }
        context = {"run_id": "test-retriever-002"}

        monkeypatch.setenv("SSOT_REPO_PATH", str(ssot_dir))

        result = run(payload, context)

        assert "No relevant information found" in result["answer"]
        assert result["confidence"] == 0.0
