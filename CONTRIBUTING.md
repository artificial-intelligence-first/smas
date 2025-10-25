# Contributing to SSOT Manager

Thank you for your interest in contributing to SSOT Manager!

## Development Setup

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager
- Git

### Setup

```bash
# Clone repository
git clone https://github.com/artificial-intelligence-first/ssot-manager.git
cd ssot-manager

# Install dependencies
uv sync --extra dev

# Clone SSOT repository for testing
git clone https://github.com/artificial-intelligence-first/ssot.git external/ssot

# Configure environment
cp .env.example .env
# Edit .env and set SSOT_REPO_PATH to external/ssot
```

## Development Workflow

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. **Make Changes**
   - Follow existing code structure
   - Write tests for new functionality
   - Update documentation as needed
   - Ensure all code is in English (comments, docstrings, variable names)
3. **Run Tests**
   ```bash
   # Run all tests
   uv run pytest

   # Run specific test
   uv run pytest tests/agents/test_ssot_manager_mag.py

   # Run with coverage
   uv run pytest --cov=catalog --cov-report=html
   ```
4. **Code Quality**
   ```bash
   # Format code
   uv run ruff format .

   # Lint code
   uv run ruff check .

   # Type check
   uv run mypy catalog/
   ```
5. **Commit Changes**
   Follow conventional commit format:

   ```
   <type>(<scope>): <subject>

   <body>

   <footer>
   ```

   Types:

   - feat: New feature
   - fix: Bug fix
   - docs: Documentation changes
   - test: Test additions/changes
   - refactor: Code refactoring
   - chore: Build/tooling changes

   Example:

   ```bash
   git commit -m "feat(retriever): add semantic search capability

   Integrate FAISS-based vector search for improved query matching.
   Falls back to keyword search if embeddings unavailable."
   ```
6. **Push & Create PR**
   ```bash
   git push origin feature/your-feature-name
   ```
   Then create a Pull Request on GitHub.

## Code Style Guidelines

### Python

- Follow PEP 8
- Use type hints for all function signatures
- Maximum line length: 100 characters
- Use descriptive variable names
- Write docstrings for all public functions/classes

Example:

```python
def search_files(
    repo_path: str,
    category: str,
    keywords: List[str]
) -> List[Dict[str, Any]]:
    """
    Search files in repository by keywords.

    Args:
        repo_path: Absolute path to repository root
        category: Category to filter (files, engineering, tools, platforms, _meta)
        keywords: List of keywords for matching

    Returns:
        List of matching files with relevance scores
    """
    # Implementation
```

### YAML

- Use 2-space indentation
- Quote strings with special characters
- Keep files under 200 lines when possible

### JSON Schema

- Use descriptive titles and descriptions
- Provide examples where helpful
- Follow JSON Schema Draft 07 specification

## Agent Development Guidelines

### Adding New SAG

1. Create directory: `catalog/agents/sub/your-sag-name/`
2. Create `agent.yaml` with full specification
3. Create `code/your_sag.py` with `run()` function
4. Create `README.md` documenting purpose, inputs, outputs
5. Define input/output contracts in `catalog/contracts/`
6. Add to registry: `catalog/registry/agents.yaml`
7. Write tests: `tests/agents/test_your_sag.py`

### Modifying Existing Agent

- Update code in `catalog/agents/{main|sub}/agent-name/code/`
- Update contracts if input/output schema changes
- Update README.md with changes
- Update or add tests
- Update version in `agent.yaml` if breaking change

## Testing Guidelines

### Test Structure

```python
import pytest
from catalog.agents.sub.your_sag.code.your_sag import run


def test_your_sag_success():
    """Test successful execution."""
    payload = {"key": "value"}
    context = {"run_id": "test-123"}

    result = run(payload, context)

    assert result["status"] == "success"
    assert "data" in result


def test_your_sag_validation_error():
    """Test validation error handling."""
    payload = {}  # Invalid
    context = {"run_id": "test-456"}

    with pytest.raises(ValueError):
        run(payload, context)
```

### Test Coverage

- Aim for 80%+ coverage
- Test happy path and error cases
- Mock external dependencies (file I/O, subprocess calls)
- Use fixtures for common test data

## Documentation Guidelines

### README.md Updates

When adding features, update main README.md:

- Features section
- Usage examples
- Configuration options

### Agent README.md

Each agent should have a comprehensive README covering:

- Purpose and responsibilities
- Dependencies (sub-agents, skills)
- Input/output contracts with examples
- Execution flow
- Configuration options
- Usage examples
- Error handling
- Observability artifacts

## Questions?

- Open an issue for bugs or feature requests
- Start a discussion for general questions
- Check existing issues/PRs before creating new ones
- Thank you for contributing to SSOT Manager!
