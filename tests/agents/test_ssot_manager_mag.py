from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import types

import pytest

agdd_pkg = sys.modules.setdefault("agdd", types.ModuleType("agdd"))
observability_pkg = sys.modules.setdefault("agdd.observability", types.ModuleType("agdd.observability"))


class _StubObservabilityLogger:
  records: list[tuple[str, dict]] = []

  def __init__(self, *args, **kwargs) -> None:
    self.records = _StubObservabilityLogger.records

  def log(self, *args, **kwargs) -> None:
    event = args[0] if args else ""
    payload = args[1] if len(args) > 1 else kwargs
    self.records.append((event, payload))


logger_module = types.ModuleType("agdd.observability.logger")
logger_module.ObservabilityLogger = _StubObservabilityLogger
observability_pkg.logger = logger_module
sys.modules["agdd.observability.logger"] = logger_module

runners_pkg = sys.modules.setdefault("agdd.runners", types.ModuleType("agdd.runners"))
agent_runner_module = types.ModuleType("agdd.runners.agent_runner")
agent_runner_module.invoke_sag = lambda *args, **kwargs: None
runners_pkg.agent_runner = agent_runner_module
sys.modules["agdd.runners.agent_runner"] = agent_runner_module

MODULE_PATH = Path(__file__).resolve().parents[2] / "catalog/agents/main/ssot-manager-mag/code/orchestrator.py"
spec = importlib.util.spec_from_file_location("ssot_manager_orchestrator", MODULE_PATH)
assert spec and spec.loader  # basic sanity check for module loading
orchestrator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(orchestrator)  # type: ignore[union-attr]


class DummyLogger:
  def log(self, *args, **kwargs) -> None:
    return None


@pytest.mark.skip(reason="Integration tests for AGDD runners are not implemented yet.")
def test_ssot_manager_mag_placeholder() -> None:
  assert True


def test_handle_update_validation_failure(monkeypatch: pytest.MonkeyPatch) -> None:
  """Validation failures should return contract-compliant update_result payloads."""
  def fake_invoke(name: str, payload: dict, parent_context: dict) -> dict:
    assert name == "content-validator-sag"
    return {"passed": False, "errors": ["missing field"]}

  monkeypatch.setattr(orchestrator, "invoke_sag", fake_invoke)

  payload = {"update": {"content": "value", "target_file": "docs/file.md"}}
  context: dict = {}

  response = orchestrator._handle_update(payload, context, DummyLogger())

  assert response["response_type"] == "update_result"
  assert response["status"] == "failure"
  assert response["update_result"]["validation_passed"] is False
  assert response["update_result"]["files_modified"] == ["docs/file.md"]
  assert response["update_result"]["commit_sha"] == ""
  assert response["update_result"]["branch"] == ""
  assert "validation_errors" in response["data"]
  assert context["sags_invoked"] == ["content-validator-sag"]


def test_handle_update_taxonomy_failure(monkeypatch: pytest.MonkeyPatch) -> None:
  """Taxonomy failures should preserve validation state and contract fields."""
  def fake_invoke(name: str, payload: dict, parent_context: dict) -> dict:
    if name == "content-validator-sag":
      return {"passed": True}
    if name == "taxonomy-manager-sag":
      return {"passed": False, "issues": ["taxonomy mismatch"]}
    raise AssertionError(f"Unexpected SAG: {name}")

  monkeypatch.setattr(orchestrator, "invoke_sag", fake_invoke)

  payload = {"update": {"content": "value", "target_file": "docs/file.md"}}
  context: dict = {}

  response = orchestrator._handle_update(payload, context, DummyLogger())

  assert response["response_type"] == "update_result"
  assert response["status"] == "failure"
  assert response["update_result"]["validation_passed"] is True
  assert response["update_result"]["files_modified"] == ["docs/file.md"]
  assert response["update_result"]["commit_sha"] == ""
  assert response["update_result"]["branch"] == ""
  assert "taxonomy_issues" in response["data"]
  assert context["sags_invoked"] == ["content-validator-sag", "taxonomy-manager-sag"]


def test_handle_analyze_orphans(monkeypatch: pytest.MonkeyPatch) -> None:
  """Orphan analysis requests should invoke crossref analyzer and surface findings."""
  def fake_invoke(name: str, payload: dict, parent_context: dict) -> dict:
    if name == "crossref-analyzer-sag":
      return {"orphans": ["doc/a.md", "doc/b.md"], "cycles": [["x", "y", "x"]]}
    raise AssertionError(f"Unexpected SAG: {name}")

  monkeypatch.setattr(orchestrator, "invoke_sag", fake_invoke)

  context: dict = {}
  response = orchestrator._handle_analyze({"analysis_type": "orphans"}, context, DummyLogger())

  assert response["response_type"] == "analysis_report"
  assert response["status"] == "success"
  assert response["analysis_report"]["type"] == "orphans"
  findings = response["analysis_report"]["findings"]
  assert findings and findings[0]["orphan_count"] == 2
  assert context["sags_invoked"] == ["crossref-analyzer-sag"]
  recommendations = response["analysis_report"]["recommendations"]
  assert any("orphan" in rec for rec in recommendations)


def test_handle_update_delete_skips_validator(monkeypatch: pytest.MonkeyPatch) -> None:
  """Delete operations should bypass validator to avoid repo-wide lint failures."""
  invocations: list[str] = []

  def fake_invoke(name: str, payload: dict, parent_context: dict) -> dict:
    invocations.append(name)
    if name == "taxonomy-manager-sag":
      return {"passed": True}
    if name == "content-updater-sag":
      assert payload["operation"] == "delete"
      return {
        "files_modified": ["docs/file.md"],
        "commit_sha": "abc123",
        "branch": "smas-update-delete",
        "validation_passed": True,
      }
    raise AssertionError(f"Unexpected SAG: {name}")

  monkeypatch.setattr(orchestrator, "invoke_sag", fake_invoke)

  context: dict = {}
  response = orchestrator._handle_update(
    {"update": {"operation": "delete", "target_file": "docs/file.md"}},
    context,
    DummyLogger(),
  )

  assert response["status"] == "success"
  assert response["update_result"]["files_modified"] == ["docs/file.md"]
  assert "content-validator-sag" not in invocations
  assert invocations == ["taxonomy-manager-sag", "content-updater-sag"]
  assert context["sags_invoked"] == ["taxonomy-manager-sag", "content-updater-sag"]


def test_run_logs_failure_status(monkeypatch: pytest.MonkeyPatch) -> None:
  """High-level run() should log actual handler status for failures."""
  _StubObservabilityLogger.records.clear()

  def fake_invoke(name: str, payload: dict, parent_context: dict) -> dict:
    assert name == "content-validator-sag"
    return {"passed": False, "errors": ["bad"]}

  monkeypatch.setattr(orchestrator, "invoke_sag", fake_invoke)

  payload = {
    "request_type": "update",
    "update": {"operation": "update", "content": "value", "target_file": "docs/file.md"},
  }
  context: dict = {"run_id": "run-1"}

  result = orchestrator.run(payload, context)

  assert result["status"] == "failure"
  assert _StubObservabilityLogger.records[-1][0] == "end"
  assert _StubObservabilityLogger.records[-1][1]["status"] == "failure"
