# Development Rules

## Test-Driven Development (MANDATORY)
1. Write unit and integration tests FIRST
2. Tests must fail initially (red)
3. Commit tests before implementation
4. Write minimal code to pass tests (green) - DO NOT MODIFY THE TESTS!
5. Refactor while keeping tests green, commit

## TDD Workflow Commands (using uv)
```bash
# Install dependencies and sync environment
uv sync --dev            # Install all dependencies including dev tools

# Run tests
uv run pytest                    # All tests
uv run pytest -m unit           # Unit tests only
uv run pytest -m integration    # Integration tests only
uv run pytest --cov             # With coverage

# Code quality (run before committing!)
uv run black src/ tests/        # Format code
uv run ruff check --fix src/ tests/   # Lint and auto-fix
uv run mypy src/                # Type checking

# Pre-commit hooks (recommended)
uv run pre-commit install       # Install git hooks
uv run pre-commit run --all-files   # Run on all files

# Add new dependencies
uv add requests              # Add runtime dependency
uv add --dev pytest         # Add development dependency

# Environment management
uv sync                      # Sync dependencies (production only)
uv sync --dev               # Sync with development dependencies
```

## Code Quality Strategy
- **Pre-commit hooks**: Auto-run black/ruff/mypy before each commit
- **Local checks**: Always run `black` and `ruff --fix` before pushing
- **GitHub Actions**: Runs same checks on PRs - should never fail if run locally
- **IDE integration**: Configure your editor to run formatters on save

## Environment Configuration
- **ALWAYS use dotenv**: Use `from dotenv import load_dotenv; load_dotenv()` for environment variables, never use `os.getenv()` directly
- **Never hardcode secrets**: All API keys, emails, and sensitive data must come from .env files
- **Environment precedence**: Constructor params > environment variables > sensible defaults

## FORBIDDEN Patterns
- Mock data generation for integration tests
- Simulated API responses
- Dummy database connections
- Placeholder implementations
- Tests that pass without real integration
- Skipping failing tests with pytest.mark.skip

## Required Test Structure
- Unit tests: tests/unit/ (fast, isolated, no external deps)
- Integration tests: tests/integration/ (real DB/API connections)
- Fixtures with real connection setup/teardown
- Coverage minimum: 80%
- All tests must use pytest markers (@pytest.mark.unit or @pytest.mark.integration)

## Documentation Requirements
- Google-style docstrings for all public functions/classes
- Auto-generated API docs via Sphinx
- Manual docs in docs/ using MyST markdown
- Build docs: `sphinx-build docs docs/_build`

## MVP Definition
For each feature:
1. Clear, testable goal (e.g., "successfully extract DOI from EuroPMC response")
2. Integration test demonstrating real API connection
3. Error handling for actual failure modes (network, malformed data, rate limits)
4. No feature complete until real integration test passes

# Project Aim

**Reference Extraction from Deepsearch Results**

Analyse Deepsearch results to extract references in various formats and intelligently resolve reference identifiers.

## Reference Types
- Conventional academic references
- Plain URLs
- Bibliography with numbered citations ([1], [2])
- Author-year citations (Osumi et al., 2025)
- Miniref style citations

## Core Functionality
- Generate key-value pairs linking references to citations in text
- Intelligent extraction of reference identifiers
- URL resolution and page scraping for reference validation
- Handle multiple citation formats in academic literature

## Implementation Notes
- URL resolution and scraping provides the safest approach for identifier extraction
- Focus on robust parsing of different citation styles
- Real integration testing with actual Deepsearch data required

