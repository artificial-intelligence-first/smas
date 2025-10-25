"""SSOT Manager MAG - Main orchestrator for SSOT repository management."""

from __future__ import annotations

import time
from datetime import datetime
from typing import Any, Dict, List

from agdd.observability.logger import ObservabilityLogger
from agdd.runners.agent_runner import invoke_sag


def _build_update_failure_response(
    update_payload: Dict[str, Any],
    validation_passed: bool,
    data: Dict[str, Any],
) -> Dict[str, Any]:
    """Assemble a contract-compliant failure response for update requests."""
    target_file = update_payload.get("target_file")
    files_modified = [target_file] if target_file else []

    return {
        "response_type": "update_result",
        "status": "failure",
        "update_result": {
            "files_modified": files_modified,
            "commit_sha": "",
            "branch": update_payload.get("branch", ""),
            "validation_passed": validation_passed,
        },
        "data": data,
    }


def run(payload: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Main entry point for SSOTManagerMAG."""
    run_id = context.get("run_id", "mag-unknown")
    logger = ObservabilityLogger(run_id, agent_name="SSOTManagerMAG")

    start_time = time.time()
    logger.log("start", {"request_type": payload.get("request_type")})

    try:
        request_type = payload["request_type"]

        if request_type == "query":
            result = _handle_query(payload, context, logger)
        elif request_type == "update":
            result = _handle_update(payload, context, logger)
        elif request_type == "validate":
            result = _handle_validate(payload, context, logger)
        elif request_type == "analyze":
            result = _handle_analyze(payload, context, logger)
        else:
            raise ValueError(f"Unknown request_type: {request_type}")

        duration_ms = (time.time() - start_time) * 1000
        result_status = result.get("status", "success")
        logger.log(
            "end",
            {
                "status": result_status,
                "duration_ms": duration_ms,
                "response_type": result["response_type"],
            },
        )

        timestamp = datetime.utcnow().isoformat(timespec="milliseconds") + "Z"
        result["metadata"] = {
            "run_id": run_id,
            "timestamp": timestamp,
            "sags_invoked": context.get("sags_invoked", []),
            "duration_ms": duration_ms,
        }

        return result

    except Exception as exc:  # pragma: no cover - defensive logging
        duration_ms = (time.time() - start_time) * 1000
        logger.log(
            "error",
            {
                "error_type": type(exc).__name__,
                "error_message": str(exc),
                "duration_ms": duration_ms,
            },
        )
        raise


def _handle_query(
    payload: Dict[str, Any], context: Dict[str, Any], logger: ObservabilityLogger
) -> Dict[str, Any]:
    """Handle query request by delegating to ContentRetrieverSAG."""
    logger.log(
        "delegation_start",
        {
            "task": "query",
            "sag": "content-retriever-sag",
        },
    )

    result = invoke_sag(
        "content-retriever-sag",
        payload.get("query", {}),
        parent_context=context,
    )

    logger.log(
        "delegation_complete",
        {
            "task": "query",
            "sag": "content-retriever-sag",
            "status": "success",
        },
    )

    context["sags_invoked"] = ["content-retriever-sag"]

    return {
        "response_type": "answer",
        "status": "success",
        "answer": result,
    }


def _handle_update(
    payload: Dict[str, Any], context: Dict[str, Any], logger: ObservabilityLogger
) -> Dict[str, Any]:
    """Handle update request with validation, terminology checks, and Git updates."""
    sags_invoked: List[str] = []
    update_payload = payload["update"]
    operation = update_payload.get("operation")
    is_delete = operation == "delete"

    logger.log(
        "delegation_start",
        {
            "task": "validate_update",
            "sag": "content-validator-sag",
        },
    )

    if not is_delete:
        validation_result = invoke_sag(
            "content-validator-sag",
            {
                "content": update_payload.get("content"),
                "target_file": update_payload.get("target_file"),
            },
            parent_context=context,
        )
        sags_invoked.append("content-validator-sag")

        if not validation_result.get("passed", False):
            context["sags_invoked"] = sags_invoked
            return _build_update_failure_response(
                update_payload,
                validation_passed=False,
                data={"validation_errors": validation_result.get("errors", [])},
            )

    logger.log(
        "delegation_start",
        {
            "task": "check_taxonomy",
            "sag": "taxonomy-manager-sag",
        },
    )

    taxonomy_result = invoke_sag(
        "taxonomy-manager-sag",
        {"operation": "validate", "content": update_payload.get("content", "")},
        parent_context=context,
    )
    sags_invoked.append("taxonomy-manager-sag")

    if not taxonomy_result.get("passed", False):
        context["sags_invoked"] = sags_invoked
        return _build_update_failure_response(
            update_payload,
            validation_passed=True,
            data={"taxonomy_issues": taxonomy_result.get("issues", [])},
        )

    logger.log(
        "delegation_start",
        {
            "task": "update_content",
            "sag": "content-updater-sag",
        },
    )

    update_result = invoke_sag(
        "content-updater-sag",
        update_payload,
        parent_context=context,
    )
    sags_invoked.append("content-updater-sag")

    context["sags_invoked"] = sags_invoked

    return {
        "response_type": "update_result",
        "status": "success",
        "update_result": update_result,
    }


def _handle_validate(
    payload: Dict[str, Any], context: Dict[str, Any], logger: ObservabilityLogger
) -> Dict[str, Any]:
    """Handle validation request."""
    logger.log(
        "delegation_start",
        {
            "task": "validate_repo",
            "sag": "content-validator-sag",
        },
    )

    validator_payload = {}
    if "scope" in payload:
        validator_payload["scope"] = payload["scope"]
    else:
        validator_payload["scope"] = payload.get("validation_scope", "all")
    if "content" in payload:
        validator_payload["content"] = payload["content"]
    if "target_file" in payload:
        validator_payload["target_file"] = payload["target_file"]
    if "category" in payload:
        validator_payload["category"] = payload["category"]

    result = invoke_sag(
        "content-validator-sag",
        validator_payload,
        parent_context=context,
    )

    context["sags_invoked"] = ["content-validator-sag"]

    return {
        "response_type": "validation_report",
        "status": "success" if result.get("passed", False) else "failure",
        "validation_report": result,
    }


def _handle_analyze(
    payload: Dict[str, Any], context: Dict[str, Any], logger: ObservabilityLogger
) -> Dict[str, Any]:
    """Handle analysis request across taxonomy and cross-reference checks."""
    analysis_type = payload.get("analysis_type", "full")
    sags_invoked: List[str] = []
    findings: List[Dict[str, Any]] = []
    recommendations: List[str] = []

    crossref_result: Dict[str, Any] | None = None
    taxonomy_result: Dict[str, Any] | None = None

    crossref_requested = analysis_type in ("crossref", "full", "orphans")
    taxonomy_requested = analysis_type in ("taxonomy", "full")

    if crossref_requested:
        logger.log(
            "delegation_start",
            {
                "task": "analyze_crossref",
                "sag": "crossref-analyzer-sag",
            },
        )

        crossref_result = invoke_sag(
            "crossref-analyzer-sag",
            {},
            parent_context=context,
        )
        sags_invoked.append("crossref-analyzer-sag")

        orphans = crossref_result.get("orphans", [])
        cycles = crossref_result.get("cycles", [])
        findings.append(
            {
                "agent": "crossref-analyzer-sag",
                "orphan_count": len(orphans),
                "sample_orphans": orphans[:5],
                "cycle_count": len(cycles),
                "sample_cycles": cycles[:3],
            }
        )
        if orphans:
            recommendations.append(
                f"Review {len(orphans)} orphan documents (e.g. {', '.join(orphans[:3])})."
            )
        if cycles and analysis_type != "orphans":
            recommendations.append(
                f"Resolve {len(cycles)} circular reference chains (first cycle starts at {cycles[0][0]})."
            )

    if taxonomy_requested:
        logger.log(
            "delegation_start",
            {
                "task": "analyze_taxonomy",
                "sag": "taxonomy-manager-sag",
            },
        )

        taxonomy_result = invoke_sag(
            "taxonomy-manager-sag",
            {"operation": "analyze"},
            parent_context=context,
        )
        sags_invoked.append("taxonomy-manager-sag")

        term_usage = taxonomy_result.get("term_usage", {})
        unused_terms = [term for term, count in term_usage.items() if count == 0]
        top_terms = sorted(term_usage.items(), key=lambda item: item[1], reverse=True)[
            :5
        ]
        findings.append(
            {
                "agent": "taxonomy-manager-sag",
                "unused_terms": unused_terms[:5],
                "frequent_terms": top_terms,
            }
        )
        recommendations.extend(taxonomy_result.get("recommendations", []))

    context["sags_invoked"] = sags_invoked

    return {
        "response_type": "analysis_report",
        "status": "success",
        "analysis_report": {
            "type": analysis_type,
            "findings": findings,
            "recommendations": recommendations,
        },
    }
