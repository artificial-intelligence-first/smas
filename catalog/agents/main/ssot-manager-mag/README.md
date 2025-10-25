# SSOTManagerMAG

SSOTManagerMAG orchestrates SSOT Manager workflows by routing SSOT requests to specialized Sub Agents. It validates payloads via contract schemas and records observability metadata for every request.

## Responsibilities

- Route query, update, validation, and analysis requests
- Coordinate ContentRetrieverSAG, ContentValidatorSAG, TaxonomyManagerSAG, CrossRefAnalyzerSAG, and ContentUpdaterSAG
- Aggregate metadata for traceability and downstream reporting

## Entrypoint

```
catalog/agents/main/ssot-manager-mag/code/orchestrator.py:run
```
