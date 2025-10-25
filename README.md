# SMAS (SSOT Management Agents System)

SMAS is an AGDD-based orchestration layer that manages the SSOT (Single Source of Truth) repository. It coordinates specialized agents to query, validate, analyze, and update the SSOT knowledge base.

## Features

- **SSOTManagerMAG** routes incoming requests to specialized Sub Agents.
- **ContentRetrieverSAG** surfaces relevant SSOT knowledge for A2A queries.
- **ContentValidatorSAG** enforces Markdown quality and link integrity.
- **TaxonomyManagerSAG** governs terminology consistency.
- **CrossRefAnalyzerSAG** inspects inter-document references and orphaned content.
- **ContentUpdaterSAG** applies repository updates with Git automation.

## Getting Started

1. Install dependencies:
   ```bash
   uv pip install -e .[dev]
   ```
2. Point SMAS to your local SSOT checkout:
   ```bash
   export SSOT_REPO_PATH=/path/to/ssot
   ```
3. Run an agent:
   ```bash
   uv run agdd agent run ssot-manager-mag --payload payload.json
   ```

## Project Layout

```
catalog/
  agents/
    main/ssot-manager-mag/
    sub/content-retriever-sag/
    sub/content-validator-sag/
    sub/taxonomy-manager-sag/
    sub/crossref-analyzer-sag/
    sub/content-updater-sag/
  contracts/
  registry/
docs/
examples/
tests/
```

## License

MIT
