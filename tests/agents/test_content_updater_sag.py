from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import types

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

MODULE_PATH = Path(__file__).resolve().parents[2] / "catalog/agents/sub/content-updater-sag/code/updater.py"
spec = importlib.util.spec_from_file_location("content_updater", MODULE_PATH)
assert spec and spec.loader
updater = importlib.util.module_from_spec(spec)
spec.loader.exec_module(updater)  # type: ignore[union-attr]


@pytest.mark.skip(reason="Content updater requires Git fixture and SSOT checkout.")
def test_content_updater_placeholder() -> None:
  assert True


def test_resolve_repo_path_blocks_escape(tmp_path: Path) -> None:
  repo_root = tmp_path / "repo"
  repo_root.mkdir()

  with pytest.raises(ValueError):
    updater._resolve_repo_path(str(repo_root), "../outside.md")


def test_run_rejects_path_traversal(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
  repo_root = tmp_path / "repo"
  repo_root.mkdir()

  monkeypatch.setenv("SSOT_REPO_PATH", str(repo_root))

  def fail_git_commit(*args, **kwargs):
    raise AssertionError("git commit should not be invoked")

  monkeypatch.setattr(updater, "_git_commit", fail_git_commit)

  with pytest.raises(ValueError):
    updater.run(
      {"target_file": "../../etc/passwd", "operation": "add", "content": "danger"},
      {"run_id": "test"},
    )
