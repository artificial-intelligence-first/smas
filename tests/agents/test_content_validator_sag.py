"""
Tests for ContentValidatorSAG
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from catalog.agents.sub.content_validator_sag.code.validator import (
    run,
    _validate_markdown,
    _check_links,
    _resolve_repo_relative_path,
)


class TestContentValidatorSAG:
    """Test suite for ContentValidatorSAG"""

    def test_run_inline_content_success(self) -> None:
        """Validate inline content without errors"""
        payload = {
            "scope": "file",
            "content": "# Title\n\nValid content.",
            "target_file": "docs/overview.md",
        }
        context = {"run_id": "validator-001"}

        result = run(payload, context)

        assert result["passed"] is True
        assert result["errors"] == []
        assert result["total_files"] == 1

    def test_run_category_scope_filters(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Category scope should only scan requested directory"""
        repo_root = tmp_path / "repo"
        (repo_root / "files").mkdir(parents=True)
        (repo_root / "files" / "bad.md").write_text("####### Too deep", encoding="utf-8")
        (repo_root / "engineering").mkdir(parents=True)
        (repo_root / "engineering" / "ok.md").write_text("# Fine\n", encoding="utf-8")

        monkeypatch.setenv("SSOT_REPO_PATH", str(repo_root))

        payload = {"scope": "category", "category": "files"}
        context = {"run_id": "validator-002"}

        result = run(payload, context)

        assert result["total_files"] == 1
        assert any(err["file"] == "files/bad.md" for err in result["errors"])
        assert all("engineering" not in err.get("file", "") for err in result["errors"])

    def test_run_file_scope_invalid_path(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Reject attempts to escape repository via target_file"""
        repo_root = tmp_path / "repo"
        repo_root.mkdir()
        monkeypatch.setenv("SSOT_REPO_PATH", str(repo_root))

        payload = {"scope": "file", "target_file": "../../etc/passwd"}
        context = {"run_id": "validator-003"}

        with pytest.raises(ValueError):
            run(payload, context)

    def test_validate_markdown_detects_heading_error(self) -> None:
        """Ensure helper flags overly deep heading levels"""
        errors, warnings = _validate_markdown("####### Too deep", "doc.md")

        assert any(err["severity"] == "error" for err in errors)
        assert warnings == []

    def test_check_links_flags_relative(self) -> None:
        """Relative links should trigger informational warnings"""
        warnings = _check_links(
            "Refer to [docs](../docs/readme.md) for details.",
            "doc.md",
        )

        assert warnings
        assert warnings[0]["severity"] == "info"

    def test_resolve_repo_relative_path_success(self, tmp_path: Path) -> None:
        """Helper should return sanitized repo-relative path"""
        repo_root = tmp_path / "repo"
        repo_root.mkdir()
        (repo_root / "docs").mkdir()
        target = repo_root / "docs" / "file.md"
        target.write_text("# Sample", encoding="utf-8")

        relative, absolute = _resolve_repo_relative_path(str(repo_root), "docs/file.md")

        assert relative == "docs/file.md"
        assert absolute.endswith("docs/file.md")
