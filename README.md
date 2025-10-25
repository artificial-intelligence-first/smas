# SSOT Manager

[![CI Status](https://github.com/artificial-intelligence-first/ssot-manager/workflows/CI/badge.svg)](https://github.com/artificial-intelligence-first/ssot-manager/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)

AI agent system for managing the [SSOT (Single Source of Truth)](https://github.com/artificial-intelligence-first/ssot) repository using the [AGDD framework](https://github.com/artificial-intelligence-first/agdd).

## Overview

SSOT Manager automates SSOT repository management through intelligent agents:
- **Query**: Search and retrieve information via A2A protocol
- **Validate**: Markdown linting, link checking, quality assurance
- **Analyze**: Cross-reference analysis, orphan detection, terminology usage
- **Update**: Content modification with Git operations and PR creation

## Architecture

SSOTManagerMAG (Main Orchestrator) ├── ContentRetrieverSAG (Information retrieval) ├── ContentValidatorSAG (Quality validation) ├── TaxonomyManagerSAG (Terminology management) ├── CrossRefAnalyzerSAG (Reference analysis) └── ContentUpdaterSAG (Content updates)

## Quick Start

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager
- Git

### Installation

```bash
# Clone repository
git clone https://github.com/artificial-intelligence-first/ssot-manager.git
cd ssot-manager

# Install dependencies
uv sync --extra dev

# Clone SSOT repository
git clone https://github.com/artificial-intelligence-first/ssot.git external/ssot

# Configure environment
cp .env.example .env
# Edit .env and set SSOT_REPO_PATH=external/ssot
```

### Basic Usage

```bash
# Query SSOT repository
echo '{
  "request_type": "query",
  "query": {
    "category": "files",
    "topic": "AGENTS",
    "question": "What are AGENTS best practices?"
  }
}' | SSOT_REPO_PATH=external/ssot uv run python -m catalog.agents.main.ssot_manager_mag.code.orchestrator

# Validate repository
echo '{
  "request_type": "validate",
  "validation_scope": "all"
}' | SSOT_REPO_PATH=external/ssot uv run python -m catalog.agents.main.ssot_manager_mag.code.orchestrator

# Analyze cross-references
echo '{
  "request_type": "analyze",
  "analysis_type": "crossref"
}' | SSOT_REPO_PATH=external/ssot uv run python -m catalog.agents.main.ssot_manager_mag.code.orchestrator
```

## Documentation

- [Contributing Guide](./CONTRIBUTING.md)
- [Code of Conduct](./CODE_OF_CONDUCT.md)
- [Changelog](./CHANGELOG.md)
- [Agent Documentation](./docs)

## Project Structure

```
ssot-manager/
├── catalog/
│   ├── agents/
│   │   ├── main/
│   │   │   └── ssot-manager-mag/      # Main orchestrator
│   │   └── sub/
│   │       ├── content-retriever-sag/  # Information retrieval
│   │       ├── content-validator-sag/  # Quality validation
│   │       ├── taxonomy-manager-sag/   # Terminology management
│   │       ├── crossref-analyzer-sag/  # Reference analysis
│   │       └── content-updater-sag/    # Content updates
│   ├── contracts/                      # JSON Schema contracts
│   └── registry/                       # Agent registry
├── tests/                              # Test suite
├── docs/                               # Documentation
└── examples/                           # Usage examples
```

## Features

### Query System

- Keyword-based search across SSOT categories
- Relevance scoring and source ranking
- Confidence estimation
- Section extraction

### Validation System

- Markdown linting (heading levels, trailing whitespace)
- Internal link verification
- Configurable scope (all, category, file)
- Detailed error reporting

### Analysis System

- Cross-reference graph construction
- Orphan document detection
- Circular reference detection
- Terminology usage statistics

### Update System

- Content add/update/delete operations
- Automated Git branching and committing
- Pull request creation (GitHub CLI required)
- Pre-update validation

## Development

### Running Tests

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/agents/test_ssot_manager_mag.py

# Run with coverage
uv run pytest --cov=catalog --cov-report=html
```

### Code Quality

```bash
# Format code
uv run ruff format .

# Lint code
uv run ruff check .

# Type check
uv run mypy catalog/ --ignore-missing-imports
```

## Roadmap

- Semantic search with vector embeddings (FAISS/Redis)
- GitHub Webhook integration for automated validation
- HTTP API server for A2A communication
- Advanced taxonomy analysis with NLP
- Bulk content operations
- AGDD official package integration (when published)

## License

MIT License - see [LICENSE](./LICENSE) for details.

## Acknowledgments

- Built with AGDD Framework
- Manages SSOT Repository
