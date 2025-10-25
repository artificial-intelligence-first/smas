"""A2A (Agent-to-Agent) protocol endpoints."""

from __future__ import annotations

import asyncio
import time
from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from agdd.runners.agent_runner import invoke_sag
from catalog.api.models import A2AInvokeRequest, A2AInvokeResponse
from catalog.api.utils import build_context, load_orchestrator

router = APIRouter(prefix="/agdd", tags=["a2a-protocol"])


@router.post("/invoke/{agent_slug}", response_model=A2AInvokeResponse)
async def invoke_agent(agent_slug: str, request: A2AInvokeRequest) -> Dict[str, Any]:
    """
    Invoke an agent via A2A protocol.

    Supports invoking both the main agent (ssot-manager-mag) and sub-agents.

    URI format: agdd://agent-slug@version
    Example: agdd://main.ssot-manager-mag@0.1.0

    Returns agent execution results with timing information.
    """
    start_time = time.time()

    try:
        # Build context
        context = request.parent_context or build_context()

        # Check if invoking main agent (run in thread to avoid blocking event loop)
        if agent_slug == "ssot-manager-mag":
            run = load_orchestrator()
            result = await asyncio.to_thread(run, request.payload, context)
        else:
            # Invoke sub-agent (run in thread to avoid blocking event loop)
            result = await asyncio.to_thread(
                invoke_sag, agent_slug, request.payload, parent_context=context
            )

        execution_time_ms = (time.time() - start_time) * 1000

        return {
            "agent_slug": agent_slug,
            "result": result,
            "execution_time_ms": execution_time_ms,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid agent or payload: {str(exc)}",
        ) from exc
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=f"Agent not found: {agent_slug}",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Agent execution failed: {str(exc)}",
        ) from exc


@router.get("/registry")
async def list_agents() -> Dict[str, Any]:
    """
    List available agents in the registry.

    Returns agent metadata including versions, paths, and capabilities.
    """
    # TODO: Parse catalog/registry/agents.yaml
    return {
        "agents": [
            {
                "slug": "ssot-manager-mag",
                "version": "0.1.0",
                "role": "main",
                "uri": "agdd://main.ssot-manager-mag@0.1.0",
            },
            {
                "slug": "content-retriever-sag",
                "version": "0.1.0",
                "role": "sub",
                "uri": "agdd://sub.content-retriever-sag@0.1.0",
            },
            {
                "slug": "content-validator-sag",
                "version": "0.1.0",
                "role": "sub",
                "uri": "agdd://sub.content-validator-sag@0.1.0",
            },
            {
                "slug": "taxonomy-manager-sag",
                "version": "0.1.0",
                "role": "sub",
                "uri": "agdd://sub.taxonomy-manager-sag@0.1.0",
            },
            {
                "slug": "crossref-analyzer-sag",
                "version": "0.1.0",
                "role": "sub",
                "uri": "agdd://sub.crossref-analyzer-sag@0.1.0",
            },
            {
                "slug": "content-updater-sag",
                "version": "0.1.0",
                "role": "sub",
                "uri": "agdd://sub.content-updater-sag@0.1.0",
            },
        ],
        "count": 6,
    }
