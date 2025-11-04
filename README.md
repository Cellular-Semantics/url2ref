# lit-agent

[![Tests](https://github.com/dosumis/lit_agent/actions/workflows/test.yml/badge.svg)](https://github.com/dosumis/lit_agent/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/dosumis/lit_agent/branch/main/graph/badge.svg)](https://codecov.io/gh/dosumis/lit_agent)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)

Reference extraction agent for analyzing Deepsearch results with unified LLM API access.

## Features

- 🔍 **Reference Extraction**: Extract academic references from Deepsearch results in various formats
- 🤖 **Unified LLM API**: Support for OpenAI, Anthropic, and 100+ other providers via LiteLLM
- 📝 **Multiple Citation Formats**: Handle numbered citations ([1]), author-year (Smith et al., 2024), and plain URLs
- 🧪 **Test-Driven Development**: Comprehensive test suite with real API integration testing
- ⚡ **Modern Tooling**: Built with uv, black, ruff, and pre-commit hooks

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/dosumis/lit_agent.git
cd lit_agent

# Install with uv (recommended)
uv sync --dev

# Or with pip
pip install -e ".[dev]"
```

### API Keys Setup

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your API keys
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
```

### Basic Usage

```python
from lit_agent.agent_connection import create_agent_from_env, OpenAIAgent, AnthropicAgent

# Create agents from environment variables
openai_agent = create_agent_from_env("openai")
anthropic_agent = create_agent_from_env("anthropic")

# Or create directly with API keys
agent = OpenAIAgent("your-api-key")
response = agent.query("Write a hello world program in Python")

# Use any LiteLLM-supported model directly
from lit_agent.agent_connection import LiteLLMAgent
agent = LiteLLMAgent("gpt-4")  # Uses environment variables
```

## Development

### Setup

```bash
# Install development dependencies
uv sync --dev

# Install pre-commit hooks (recommended)
uv run pre-commit install
```

### Testing

```bash
# Run all tests
uv run pytest

# Run only unit tests (fast)
uv run pytest -m unit

# Run integration tests (requires API keys)
uv run pytest -m integration

# Run with coverage
uv run pytest --cov
```

### Code Quality

```bash
# Format code
uv run black src/ tests/

# Lint and fix issues
uv run ruff check --fix src/ tests/

# Type checking
uv run mypy src/

# Run all quality checks
uv run pre-commit run --all-files
```

## Testing Strategy

This project follows **strict Test-Driven Development** with real integration testing:

- **Unit Tests**: Fast, isolated tests with mocks
- **Integration Tests**: Real API calls when keys available, mock fallback with warnings
- **No Mocks for Integration**: Real API testing is prioritized, mocks only as fallback
- **Coverage Requirement**: Minimum 80% test coverage

### Integration Test Behavior

```bash
# With API keys: Real API calls
--- Anthropic Hello World Response (REAL API) ---
The first recorded use of "Hello, World!" to demonstrate a programming language...

# Without API keys: Mock fallback with warning
UserWarning: ANTHROPIC_API_KEY not found - falling back to mock test.
--- Anthropic Hello World Response (MOCK) ---
```

## Project Scope

**Current Focus**: Reference extraction from Deepsearch results

### Supported Reference Types
- Conventional academic references
- Plain URLs
- Numbered citations ([1], [2], etc.)
- Author-year citations (Osumi et al., 2025)
- Bibliography with miniref style citations

### Key Capabilities
- Generate key-value pairs linking references to citations in text
- Intelligent extraction of reference identifiers
- URL resolution and page scraping for reference validation
- Handle various citation formats found in academic literature

## Architecture

- **LiteLLM Integration**: Unified API for 100+ LLM providers
- **Environment-based Configuration**: API keys via dotenv
- **Modular Design**: Abstract base classes with concrete implementations
- **Error Handling**: Comprehensive error handling with meaningful messages

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Write tests first (TDD approach)
4. Implement the feature
5. Ensure all tests pass (`uv run pytest`)
6. Run code quality checks (`uv run pre-commit run --all-files`)
7. Commit your changes (`git commit -m 'Add amazing feature'`)
8. Push to the branch (`git push origin feature/amazing-feature`)
9. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [LiteLLM](https://github.com/BerriAI/litellm) for unified LLM API access
- Uses [uv](https://github.com/astral-sh/uv) for fast Python package management
- Code quality maintained with [black](https://github.com/psf/black) and [ruff](https://github.com/astral-sh/ruff)