"""
Tests for SSOTManagerMAG
"""

from __future__ import annotations

import pytest
import pytest_mock

from catalog.agents.main.ssot_manager_mag.code.orchestrator import run


class TestSSOTManagerMAG:
    """Test suite for SSOTManagerMAG"""

    def test_handle_query_success(
        self, mocker: pytest_mock.plugin.MockerFixture
    ) -> None:
        """Test successful query handling"""
        mock_invoke_sag = mocker.patch(
            "catalog.agents.main.ssot_manager_mag.code.orchestrator.invoke_sag"
        )
        mock_invoke_sag.return_value = {
            "question": "What is AGENTS?",
            "answer": "AGENTS is a convention file.",
            "sources": [],
            "confidence": 0.8,
        }

        payload = {
            "request_type": "query",
            "query": {
                "category": "files",
                "topic": "AGENTS",
                "question": "What is AGENTS?",
            },
        }
        context = {"run_id": "test-mag-001"}

        result = run(payload, context)

        assert result["response_type"] == "answer"
        assert result["status"] == "success"
        assert "metadata" in result
        assert result["metadata"]["run_id"] == "test-mag-001"

    def test_handle_validate_success(
        self, mocker: pytest_mock.plugin.MockerFixture
    ) -> None:
        """Test successful validation handling"""
        mock_invoke_sag = mocker.patch(
            "catalog.agents.main.ssot_manager_mag.code.orchestrator.invoke_sag"
        )
        mock_invoke_sag.return_value = {
            "passed": True,
            "errors": [],
            "warnings": [],
            "total_files": 10,
        }

        payload = {"request_type": "validate", "validation_scope": "all"}
        context = {"run_id": "test-mag-002"}

        result = run(payload, context)

        assert result["response_type"] == "validation_report"
        assert result["status"] == "success"

    def test_handle_analyze_crossref(
        self, mocker: pytest_mock.plugin.MockerFixture
    ) -> None:
        """Test cross-reference analysis"""
        mock_invoke_sag = mocker.patch(
            "catalog.agents.main.ssot_manager_mag.code.orchestrator.invoke_sag"
        )
        mock_invoke_sag.return_value = {
            "reference_graph": {},
            "orphans": ["orphan.md"],
            "cycles": [],
            "statistics": {"total_files": 5, "orphan_count": 1},
        }

        payload = {"request_type": "analyze", "analysis_type": "crossref"}
        context = {"run_id": "test-mag-003"}

        result = run(payload, context)

        assert result["response_type"] == "analysis_report"
        assert result["status"] == "success"
        assert "crossref-analyzer-sag" in context.get("sags_invoked", [])

    def test_invalid_request_type(self) -> None:
        """Test error handling for invalid request type"""
        payload = {"request_type": "invalid"}
        context = {"run_id": "test-mag-004"}

        with pytest.raises(ValueError, match="Unknown request_type"):
            run(payload, context)

    def test_update_validation_failure(
        self, mocker: pytest_mock.plugin.MockerFixture
    ) -> None:
        """Test update request with validation failure"""
        mock_invoke_sag = mocker.patch(
            "catalog.agents.main.ssot_manager_mag.code.orchestrator.invoke_sag"
        )
        mock_invoke_sag.return_value = {
            "passed": False,
            "errors": [{"line": 1, "message": "Error"}],
        }

        payload = {
            "request_type": "update",
            "update": {
                "target_file": "files/TEST.md",
                "operation": "add",
                "content": "Invalid content",
                "reason": "Test",
            },
        }
        context = {"run_id": "test-mag-005"}

        result = run(payload, context)

        assert result["response_type"] == "update_result"
        assert result["status"] == "failure"
