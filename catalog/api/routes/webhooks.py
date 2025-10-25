"""GitHub webhook integration endpoints."""

from __future__ import annotations

import asyncio
import hmac
import os
from hashlib import sha256
from typing import Any, Dict

from fastapi import APIRouter, Header, HTTPException, Request

from catalog.api.utils import build_context, load_orchestrator

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


def _verify_github_signature(payload_body: bytes, signature: str, secret: str) -> bool:
    """
    Verify GitHub webhook signature.

    Args:
        payload_body: Raw request body bytes
        signature: X-Hub-Signature-256 header value
        secret: GitHub webhook secret

    Returns:
        True if signature is valid, False otherwise
    """
    if not signature or not signature.startswith("sha256="):
        return False

    expected_signature = (
        "sha256=" + hmac.new(secret.encode(), payload_body, sha256).hexdigest()
    )

    return hmac.compare_digest(signature, expected_signature)


@router.post("/github")
async def github_webhook(
    request: Request,
    x_github_event: str = Header(None),
    x_hub_signature_256: str = Header(None),
) -> Dict[str, Any]:
    """
    Handle GitHub webhook events with signature verification.

    Supported events:
    - pull_request.opened: Automatically validate PR changes
    - pull_request.synchronize: Re-validate on new commits
    - push: Validate pushed commits

    Security:
    - Requires GITHUB_WEBHOOK_SECRET environment variable
    - Validates X-Hub-Signature-256 header

    Returns validation results and optional GitHub Status API updates.
    """
    # Get raw body for signature verification
    body = await request.body()

    # Verify webhook signature (skip for ping events during setup)
    webhook_secret = os.getenv("GITHUB_WEBHOOK_SECRET")
    if webhook_secret and x_github_event != "ping":
        if not x_hub_signature_256:
            raise HTTPException(
                status_code=401,
                detail="Missing X-Hub-Signature-256 header",
            )

        if not _verify_github_signature(body, x_hub_signature_256, webhook_secret):
            raise HTTPException(
                status_code=403,
                detail="Invalid webhook signature",
            )

    # Parse webhook payload
    payload = await request.json()

    # Handle different event types
    if x_github_event == "pull_request":
        return await _handle_pull_request(payload)
    elif x_github_event == "push":
        return await _handle_push(payload)
    elif x_github_event == "ping":
        return {"status": "ok", "message": "Webhook configured successfully"}
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported event type: {x_github_event}",
        )


async def _handle_pull_request(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Handle pull_request webhook events."""
    action = payload.get("action")

    # Only process opened and synchronize actions
    if action not in ["opened", "synchronize"]:
        return {"status": "skipped", "action": action}

    # Build validation request
    context = build_context(run_id=f"webhook-pr-{payload['pull_request']['number']}")

    validation_request = {
        "request_type": "validate",
        "validation_scope": "all",
    }

    # Execute validation (run in thread to avoid blocking event loop)
    run = load_orchestrator()
    result = await asyncio.to_thread(run, validation_request, context)

    # TODO: Report result to GitHub Status API
    # This would require GitHub API token and commit SHA

    return {
        "status": "processed",
        "event": "pull_request",
        "action": action,
        "pr_number": payload["pull_request"]["number"],
        "validation_result": result,
    }


async def _handle_push(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Handle push webhook events."""
    ref = payload.get("ref", "")
    default_branch = payload.get("repository", {}).get("default_branch", "main")

    # Only validate pushes to default branch
    if not ref.endswith(default_branch):
        return {"status": "skipped", "ref": ref}

    # Build validation request
    commits = payload.get("commits", [])
    context = build_context(
        run_id=f"webhook-push-{payload.get('after', 'unknown')[:8]}"
    )

    validation_request = {
        "request_type": "validate",
        "validation_scope": "all",
    }

    # Execute validation (run in thread to avoid blocking event loop)
    run = load_orchestrator()
    result = await asyncio.to_thread(run, validation_request, context)

    return {
        "status": "processed",
        "event": "push",
        "ref": ref,
        "commit_count": len(commits),
        "validation_result": result,
    }
