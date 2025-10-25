# SMAS Usage Examples

This directory contains example payloads for SMAS operations.

## Query Example

Search for information about AGENTS best practices:

```bash
cat examples/query_example.json | \
  SSOT_REPO_PATH=external/ssot \
  uv run python -m catalog.agents.main.ssot_manager_mag.code.orchestrator
```

## Validate Example

Validate all files in the "files" category:

```bash
cat examples/validate_example.json | \
  SSOT_REPO_PATH=external/ssot \
  uv run python -m catalog.agents.main.ssot_manager_mag.code.orchestrator
```

## Analyze Example

Run full analysis (cross-references + taxonomy):

```bash
cat examples/analyze_example.json | \
  SSOT_REPO_PATH=external/ssot \
  uv run python -m catalog.agents.main.ssot_manager_mag.code.orchestrator
```

## Update Example

Note: Update operations modify the SSOT repository. Use with caution.

```json
{
  "request_type": "update",
  "update": {
    "target_file": "files/EXAMPLE.md",
    "operation": "add",
    "content": "# Example\n\nThis is an example file.\n",
    "reason": "Add example documentation"
  }
}
```
