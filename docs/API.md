# SSOT Manager API Documentation

SSOT Manager provides three types of API endpoints:

1. **Basic Execution API** - Execute query, update, validate, and analyze operations
2. **GitHub Webhook Integration** - Automated validation on PR events
3. **A2A Protocol** - Agent-to-Agent communication protocol

## Starting the Server

```bash
# Development server with auto-reload
uvicorn catalog.api.server:app --reload

# Production server
uvicorn catalog.api.server:app --host 0.0.0.0 --port 8000

# With workers
uvicorn catalog.api.server:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Documentation

Interactive API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 1. Basic Execution API

### Health Check

```bash
curl http://localhost:8000/api/v1/health
```

**Response**:
```json
{
  "status": "healthy",
  "service": "ssot-manager",
  "version": "0.1.0"
}
```

### Execute Query

```bash
curl -X POST http://localhost:8000/api/v1/execute \
  -H "Content-Type: application/json" \
  -d '{
    "request_type": "query",
    "query": {
      "category": "files",
      "topic": "AGENTS",
      "question": "What are AGENTS best practices?"
    }
  }'
```

**Response**:
```json
{
  "response_type": "answer",
  "status": "success",
  "answer": {
    "question": "What are AGENTS best practices?",
    "answer": "Based on the SSOT repository...",
    "sources": [
      {
        "file": "files/AGENTS.md",
        "section": "## Best Practices",
        "relevance": 0.92
      }
    ],
    "confidence": 0.85
  },
  "metadata": {
    "run_id": "api-1234567890-abcd1234",
    "timestamp": "2025-10-25T10:30:00.000Z",
    "sags_invoked": ["content-retriever-sag"],
    "duration_ms": 234.5
  }
}
```

### Execute Validation

```bash
curl -X POST http://localhost:8000/api/v1/execute \
  -H "Content-Type: application/json" \
  -d '{
    "request_type": "validate",
    "validation_scope": "all"
  }'
```

**Response**:
```json
{
  "response_type": "validation_report",
  "status": "success",
  "validation_report": {
    "passed": true,
    "total_files": 42,
    "errors": [],
    "warnings": []
  },
  "metadata": {
    "run_id": "api-1234567890-abcd1234",
    "timestamp": "2025-10-25T10:31:00.000Z",
    "sags_invoked": ["content-validator-sag"],
    "duration_ms": 1234.5
  }
}
```

### Execute Analysis

```bash
curl -X POST http://localhost:8000/api/v1/execute \
  -H "Content-Type": application/json" \
  -d '{
    "request_type": "analyze",
    "analysis_type": "crossref"
  }'
```

### Execute Update

```bash
curl -X POST http://localhost:8000/api/v1/execute \
  -H "Content-Type: application/json" \
  -d '{
    "request_type": "update",
    "update": {
      "target_file": "files/EXAMPLE.md",
      "operation": "add",
      "content": "# Example\n\nThis is an example file.\n",
      "reason": "Add example documentation"
    }
  }'
```

## 2. GitHub Webhook Integration

### Setup

1. Go to your GitHub repository settings
2. Navigate to **Webhooks** → **Add webhook**
3. Set **Payload URL** to: `https://your-domain.com/webhooks/github`
4. Set **Content type** to: `application/json`
5. Select events: `Pull requests` and `Pushes`

### Webhook Endpoint

```
POST /webhooks/github
```

**Supported Events**:
- `pull_request.opened` - Automatically validate PR changes
- `pull_request.synchronize` - Re-validate on new commits
- `push` - Validate pushed commits to default branch
- `ping` - Webhook configuration test

**Example Response** (for pull_request event):
```json
{
  "status": "processed",
  "event": "pull_request",
  "action": "opened",
  "pr_number": 42,
  "validation_result": {
    "response_type": "validation_report",
    "status": "success",
    "validation_report": {
      "passed": true,
      "total_files": 15,
      "errors": [],
      "warnings": []
    }
  }
}
```

## 3. A2A Protocol

### List Available Agents

```bash
curl http://localhost:8000/agdd/registry
```

**Response**:
```json
{
  "agents": [
    {
      "slug": "ssot-manager-mag",
      "version": "0.1.0",
      "role": "main",
      "uri": "agdd://main.ssot-manager-mag@0.1.0"
    },
    {
      "slug": "content-retriever-sag",
      "version": "0.1.0",
      "role": "sub",
      "uri": "agdd://sub.content-retriever-sag@0.1.0"
    }
  ],
  "count": 6
}
```

### Invoke Agent

```bash
curl -X POST http://localhost:8000/agdd/invoke/content-retriever-sag \
  -H "Content-Type: application/json" \
  -d '{
    "agent_slug": "content-retriever-sag",
    "payload": {
      "category": "files",
      "topic": "AGENTS",
      "question": "What are AGENTS best practices?"
    }
  }'
```

**Response**:
```json
{
  "agent_slug": "content-retriever-sag",
  "result": {
    "sources": [...],
    "answer": "...",
    "confidence": 0.85
  },
  "execution_time_ms": 156.7
}
```

### Invoke Main Orchestrator

```bash
curl -X POST http://localhost:8000/agdd/invoke/ssot-manager-mag \
  -H "Content-Type: application/json" \
  -d '{
    "agent_slug": "ssot-manager-mag",
    "payload": {
      "request_type": "query",
      "query": {
        "category": "files",
        "topic": "AGENTS",
        "question": "What are AGENTS best practices?"
      }
    }
  }'
```

## Environment Variables

```bash
# Required
export SSOT_REPO_PATH=/path/to/ssot

# Optional
export AGDD_API_KEY=your-api-key  # For future AGDD integration
export GITHUB_TOKEN=ghp_...       # For PR creation in updates
```

## Error Handling

All endpoints return standard HTTP status codes:

- **200 OK** - Successful execution
- **400 Bad Request** - Invalid payload or parameters
- **404 Not Found** - Agent not found (A2A protocol)
- **500 Internal Server Error** - Agent execution failed

**Error Response Format**:
```json
{
  "detail": "Error message describing what went wrong"
}
```

## Rate Limiting

Currently no rate limiting is implemented. For production use, consider:
- Adding rate limiting middleware
- Implementing request queuing for long-running operations
- Setting up monitoring and alerting

## Security Considerations

⚠️ **Important for Production**:

1. **CORS**: Update `allow_origins` in `catalog/api/server.py` to restrict origins
2. **Authentication**: Implement API key or OAuth for webhook endpoints
3. **HTTPS**: Always use HTTPS in production
4. **Webhook Signatures**: Verify `X-Hub-Signature-256` for GitHub webhooks
5. **Input Validation**: All inputs are validated via Pydantic models

## Example: Python Client

```python
import requests

# Execute query
response = requests.post(
    "http://localhost:8000/api/v1/execute",
    json={
        "request_type": "query",
        "query": {
            "category": "files",
            "topic": "AGENTS",
            "question": "What are AGENTS best practices?"
        }
    }
)

result = response.json()
print(f"Answer: {result['answer']['answer']}")
print(f"Confidence: {result['answer']['confidence']}")
```

## Example: JavaScript Client

```javascript
// Execute query
const response = await fetch('http://localhost:8000/api/v1/execute', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    request_type: 'query',
    query: {
      category: 'files',
      topic: 'AGENTS',
      question: 'What are AGENTS best practices?'
    }
  })
});

const result = await response.json();
console.log('Answer:', result.answer.answer);
console.log('Confidence:', result.answer.confidence);
```
