"""SSOT Manager HTTP API Server.

FastAPI-based server providing HTTP endpoints for:
- Basic execution (query, update, validate, analyze)
- GitHub webhook integration
- Agent-to-Agent (A2A) protocol

Usage:
    uvicorn catalog.api.server:app --reload
    uvicorn catalog.api.server:app --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from catalog.api.routes import agdd, execute, webhooks

# Create FastAPI application
app = FastAPI(
    title="SSOT Manager API",
    description="AI agent system for managing the SSOT repository",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(execute.router)
app.include_router(webhooks.router)
app.include_router(agdd.router)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "SSOT Manager",
        "version": "0.1.0",
        "docs": "/docs",
        "endpoints": {
            "execute": "/api/v1/execute",
            "health": "/api/v1/health",
            "github_webhook": "/webhooks/github",
            "a2a_invoke": "/agdd/invoke/{agent_slug}",
            "a2a_registry": "/agdd/registry",
        },
    }
