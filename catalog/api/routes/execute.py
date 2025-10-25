"""Basic execution endpoints for SSOT Manager."""

from __future__ import annotations

import asyncio
from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from catalog.api.models import ExecuteRequest, ExecuteResponse
from catalog.api.utils import build_context, load_orchestrator

router = APIRouter(prefix="/api/v1", tags=["execution"])


@router.post("/execute", response_model=ExecuteResponse)
async def execute(request: ExecuteRequest) -> Dict[str, Any]:
    """
    Execute a request to SSOT Manager.

    Supports four request types:
    - query: Search and retrieve information from SSOT
    - update: Modify content with validation and Git operations
    - validate: Lint and validate markdown files
    - analyze: Analyze cross-references and terminology

    Returns execution results with metadata.
    """
    try:
        # Build execution context
        context = build_context()

        # Convert Pydantic model to dict for orchestrator
        payload = request.model_dump(exclude_none=True)

        # Load and execute via orchestrator (run in thread to avoid blocking event loop)
        run = load_orchestrator()
        result = await asyncio.to_thread(run, payload, context)

        return result

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Internal error: {str(exc)}"
        ) from exc


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "ssot-manager",
        "version": "0.1.0",
    }
