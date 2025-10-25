"""Pydantic models for API requests and responses."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


# Request Models
class QueryRequest(BaseModel):
    """Query request payload."""

    category: Literal["files", "engineering", "tools", "platforms", "_meta", "all"]
    topic: str = Field(..., description="Search topic (e.g., AGENTS, MCP)")
    question: str = Field(..., description="Specific question")


class UpdateRequest(BaseModel):
    """Update request payload."""

    target_file: str = Field(..., description="Target file path")
    operation: Literal["add", "update", "delete"]
    content: Optional[str] = Field(None, description="Content to add or update")
    reason: Optional[str] = Field(None, description="Reason for change")


class ExecuteRequest(BaseModel):
    """Main execution request."""

    request_type: Literal["query", "update", "validate", "analyze"]
    query: Optional[QueryRequest] = None
    update: Optional[UpdateRequest] = None
    validation_scope: Optional[Literal["all", "category", "file"]] = None
    analysis_type: Optional[Literal["crossref", "taxonomy", "orphans", "full"]] = None
    category: Optional[str] = None
    target_file: Optional[str] = None


# Response Models
class SourceInfo(BaseModel):
    """Source information for query results."""

    file: str
    section: str
    relevance: float = Field(..., ge=0, le=1)


class QueryAnswer(BaseModel):
    """Query answer payload."""

    question: str
    answer: str
    sources: List[SourceInfo]
    confidence: float = Field(..., ge=0, le=1)


class UpdateResult(BaseModel):
    """Update result payload."""

    files_modified: List[str]
    commit_sha: str
    branch: str
    pr_url: Optional[str] = None
    validation_passed: bool


class ValidationReport(BaseModel):
    """Validation report payload."""

    passed: bool
    total_files: int
    errors: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]


class AnalysisReport(BaseModel):
    """Analysis report payload."""

    type: str
    findings: List[Dict[str, Any]]
    recommendations: List[str]


class ResponseMetadata(BaseModel):
    """Response metadata."""

    run_id: str
    timestamp: str
    sags_invoked: List[str]
    duration_ms: float
    cost_estimate: Optional[float] = None


class ExecuteResponse(BaseModel):
    """Main execution response."""

    response_type: Literal[
        "answer", "update_result", "validation_report", "analysis_report"
    ]
    status: Literal["success", "partial_success", "failure"]
    answer: Optional[QueryAnswer] = None
    update_result: Optional[UpdateResult] = None
    validation_report: Optional[ValidationReport] = None
    analysis_report: Optional[AnalysisReport] = None
    data: Optional[Dict[str, Any]] = None
    metadata: ResponseMetadata


# GitHub Webhook Models
class GitHubRepository(BaseModel):
    """GitHub repository information."""

    full_name: str
    clone_url: str
    default_branch: str


class GitHubPullRequest(BaseModel):
    """GitHub pull request information."""

    number: int
    title: str
    head: Dict[str, Any]
    base: Dict[str, Any]


class GitHubWebhookPayload(BaseModel):
    """GitHub webhook payload."""

    action: str
    repository: GitHubRepository
    pull_request: Optional[GitHubPullRequest] = None


# A2A Protocol Models
class A2AInvokeRequest(BaseModel):
    """A2A protocol invoke request."""

    agent_slug: str
    payload: Dict[str, Any]
    parent_context: Optional[Dict[str, Any]] = None


class A2AInvokeResponse(BaseModel):
    """A2A protocol invoke response."""

    agent_slug: str
    result: Dict[str, Any]
    execution_time_ms: float
