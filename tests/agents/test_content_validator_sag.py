from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import types
from typing import Any

import pytest

agdd_pkg = sys.modules.setdefault("agdd", types.ModuleType("agdd"))
observability_pkg = sys.modules.setdefault("agdd.observability", types.ModuleType("agdd.observability"))


class _StubObservabilityLogger:
  def __init__(self, *args, **kwargs) -> None:
    return None

  def log(self, *args, **kwargs) -> None:
    return None


logger_module = types.ModuleType("agdd.observability.logger")
logger_module.ObservabilityLogger = _StubObservabilityLogger
observability_pkg.logger = logger_module
sys.modules["agdd.observability.logger"] = logger_module

MODULE_PATH = Path(__file__).resolve().parents[2] / "catalog/agents/sub/content-validator-sag/code/validator.py"
spec = importlib.util.spec_from_file_location("content_validator", MODULE_PATH)
assert spec and spec.loader
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)  # type: ignore[union-attr]


@pytest.mark.skip(reason="Validator tests depend on Markdown sample corpus.")
def test_content_validator_placeholder() -> None:
  assert True


def test_validate_markdown_trailing_spaces_warning() -> None:
  errors, warnings = validator._validate_markdown("Line  \nNext", "doc.md")

  assert errors == []
  assert warnings and warnings[0]["severity"] == "warning"


def test_run_marks_trailing_space_as_pass(monkeypatch: pytest.MonkeyPatch) -> None:
  def fake_count_files(path: str, scope: str, **kwargs: Any) -> int:
    return 1

  monkeypatch.setattr(validator, "_count_files", fake_count_files)

  result = validator.run({"content": "Example  ", "scope": "all"}, {"run_id": "test"})

  assert result["passed"] is True
  assert result["warnings"]


def test_run_category_scope_honors_category(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
  repo_root = tmp_path / "repo"
  (repo_root / "files").mkdir(parents=True)
  (repo_root / "files" / "doc.md").write_text("####### Too deep", encoding="utf-8")
  (repo_root / "engineering").mkdir(parents=True)
  (repo_root / "engineering" / "ok.md").write_text("# Fine\n", encoding="utf-8")

  monkeypatch.setenv("SSOT_REPO_PATH", str(repo_root))

  result = validator.run({"scope": "category", "category": "files"}, {"run_id": "test"})

  assert result["total_files"] == 1
  assert any(err["file"] == "files/doc.md" for err in result["errors"])
  assert all("engineering" not in err["file"] for err in result["errors"])


def test_run_file_scope_honors_target(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
  repo_root = tmp_path / "repo"
  (repo_root / "files").mkdir(parents=True)
  (repo_root / "files" / "doc.md").write_text("Line  \nNext", encoding="utf-8")
  (repo_root / "files" / "other.md").write_text("####### Too deep", encoding="utf-8")

  monkeypatch.setenv("SSOT_REPO_PATH", str(repo_root))

  result = validator.run(
    {"scope": "file", "target_file": "files/doc.md"},
    {"run_id": "test"},
  )

  assert result["total_files"] == 1
  assert result["errors"] == []
  assert any(warn["file"] == "files/doc.md" for warn in result["warnings"])


def test_run_file_scope_rejects_escape(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
  repo_root = tmp_path / "repo"
  repo_root.mkdir()
  monkeypatch.setenv("SSOT_REPO_PATH", str(repo_root))

  with pytest.raises(ValueError):
    validator.run(
      {"scope": "file", "target_file": "../../etc/passwd"},
      {"run_id": "test"},
    )
