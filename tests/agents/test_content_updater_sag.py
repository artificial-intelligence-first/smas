"""
Tests for ContentUpdaterSAG
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock

import pytest

from catalog.agents.sub.content_updater_sag.code.updater import (
    run,
    _resolve_repo_path,
    _sanitize_ref_component,
)


class TestContentUpdaterSAG:
    """Test suite for ContentUpdaterSAG"""

    def test_run_add_creates_file(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Add operation should write file and return commit info"""
        repo_root = tmp_path / "repo"
        repo_root.mkdir()
        monkeypatch.setenv("SSOT_REPO_PATH", str(repo_root))

        git_mock = Mock(return_value="abc123")
        monkeypatch.setattr(
            "catalog.agents.sub.content_updater_sag.code.updater._git_commit",
            git_mock,
        )
        monkeypatch.setattr(
            "catalog.agents.sub.content_updater_sag.code.updater._create_pull_request",
            Mock(return_value="https://example.com/pr"),
        )

        payload = {
            "operation": "add",
            "target_file": "docs/new.md",
            "content": "Hello World",
            "reason": "Add new doc",
        }
        context = {"run_id": "updater-001"}

        result = run(payload, context)

        created_file = repo_root / "docs" / "new.md"
        assert created_file.exists()
        assert created_file.read_text(encoding="utf-8") == "Hello World"
        git_mock.assert_called_once()
        assert result["commit_sha"] == "abc123"

    def test_run_delete_removes_file(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Delete operation should remove file if present"""
        repo_root = tmp_path / "repo"
        target = repo_root / "docs" / "obsolete.md"
        target.parent.mkdir(parents=True)
        target.write_text("Old content", encoding="utf-8")
        monkeypatch.setenv("SSOT_REPO_PATH", str(repo_root))

        monkeypatch.setattr(
            "catalog.agents.sub.content_updater_sag.code.updater._git_commit",
            Mock(return_value="deadbeef"),
        )

        payload = {
            "operation": "delete",
            "target_file": "docs/obsolete.md",
            "reason": "Cleanup",
        }
        context = {"run_id": "updater-002"}

        result = run(payload, context)

        assert not target.exists()
        assert result["files_modified"] == ["docs/obsolete.md"]

    def test_run_unknown_operation(self) -> None:
        """Invalid operations should raise ValueError"""
        with pytest.raises(ValueError):
            run(
                {"operation": "rename", "target_file": "docs/doc.md"},
                {"run_id": "updater-003"},
            )

    def test_resolve_repo_path_rejects_escape(self, tmp_path: Path) -> None:
        """Reject attempts to navigate outside repository"""
        repo_root = tmp_path / "repo"
        repo_root.mkdir()

        with pytest.raises(ValueError):
            _resolve_repo_path(str(repo_root), "../secrets.txt")

    def test_sanitize_ref_component(self) -> None:
        """Run IDs should be normalized for branch names"""
        sanitized = _sanitize_ref_component("run id with spaces & symbols!")

        assert sanitized == "run-id-with-spaces-symbols"
