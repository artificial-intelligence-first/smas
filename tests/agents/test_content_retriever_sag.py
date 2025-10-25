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

MODULE_PATH = Path(__file__).resolve().parents[2] / "catalog/agents/sub/content-retriever-sag/code/retriever.py"
spec = importlib.util.spec_from_file_location("content_retriever", MODULE_PATH)
assert spec and spec.loader
retriever = importlib.util.module_from_spec(spec)
spec.loader.exec_module(retriever)  # type: ignore[union-attr]


@pytest.mark.skip(reason="Content retriever logic requires SSOT repository fixture.")
def test_content_retriever_placeholder() -> None:
  assert True


def test_sanitize_category_blocks_traversal() -> None:
  with pytest.raises(ValueError):
    retriever._sanitize_category("../outside")


def test_search_files_rejects_escape(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
  repo_root = tmp_path / "repo"
  (repo_root / "files").mkdir(parents=True)
  monkeypatch.setenv("SSOT_REPO_PATH", str(repo_root))

  with pytest.raises(ValueError):
    retriever._search_files(str(repo_root), "../../etc", "", "", _StubObservabilityLogger("run", {}))
