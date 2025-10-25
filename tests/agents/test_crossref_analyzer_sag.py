"""
Tests for CrossRefAnalyzerSAG
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock

import pytest

from catalog.agents.sub.crossref_analyzer_sag.code.analyzer import (
    run,
    _extract_references,
    _detect_cycles,
)


class TestCrossRefAnalyzerSAG:
    """Test suite for CrossRefAnalyzerSAG"""

    def test_run_builds_reference_graph(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Run should analyze repository and produce statistics"""
        repo_root = tmp_path / "repo"
        files_dir = repo_root / "files"
        files_dir.mkdir(parents=True)

        (files_dir / "a.md").write_text("[Link](b.md)\n", encoding="utf-8")
        (files_dir / "b.md").write_text("# Heading\n", encoding="utf-8")

        monkeypatch.setenv("SSOT_REPO_PATH", str(repo_root))

        result = run({}, {"run_id": "crossref-001"})

        assert result["statistics"]["total_files"] == 2
        assert "files/a.md" in result["reference_graph"]
        assert result["orphans"]

    def test_extract_references_resolves_relative_paths(self) -> None:
        """Ensure helper normalizes markdown links"""
        content = "[Doc](./docs/guide.md) and [Absolute](/files/intro.md)"

        refs = _extract_references(content, "files/source.md")

        assert "files/docs/guide.md" in refs
        assert "files/intro.md" in refs

    def test_detect_cycles_identifies_loop(self) -> None:
        """Detect simple reference cycle"""
        graph = {
            "files/a.md": {"files/b.md"},
            "files/b.md": {"files/a.md"},
        }

        cycles = _detect_cycles(graph, logger=Mock())

        assert cycles
        assert cycles[0][0] == "files/a.md"
