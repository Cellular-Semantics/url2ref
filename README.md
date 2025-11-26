# lit-agent

[![Tests](https://github.com/dosumis/lit_agent/actions/workflows/test.yml/badge.svg?branch=main)](https://github.com/dosumis/lit_agent/actions/workflows/test.yml)
[![coverage](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/dosumis/lit_agent/main/.github/badges/coverage.json)](https://github.com/dosumis/lit_agent/actions/workflows/test.yml)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)

Advanced academic identifier extraction and validation system with comprehensive assessment capabilities.

## Features

- 🔍 **Reference Extraction**: Extract academic references from Deepsearch results in various formats
- 🔍 **Multi-Phase Identifier Extraction**: Extract DOI, PMID, and PMC identifiers from academic URLs using URL patterns, web scraping, and PDF text analysis
- 🎯 **AI-Powered Topic Validation**: LLM-based relevance assessment to ensure extracted papers match your research domain (e.g., astrocyte biology)
- 📊 **Comprehensive Validation Pipeline**: Multi-layered validation using format checking, NCBI API verification, and metapub integration
- 📈 **Detailed Reporting & Visualization**: Interactive HTML reports with charts, statistics, and actionable recommendations
- 🔬 **Manual Review Guidance**: Systematic sampling strategies and pause-point assessments for quality control
- 🤖 **Unified LLM API**: Support for OpenAI, Anthropic, and 100+ other providers via LiteLLM
- 📝 **Multiple Citation Formats**: Handle numbered citations ([1]), author-year (Smith et al., 2024), and plain URLs


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

# For academic identifier validation (required for validation features)
NCBI_EMAIL=your_email@domain.com  # Should be registered with NCBI
NCBI_API_KEY=your_ncbi_key        # Optional but recommended for higher rate limits
```

## Usage

### Bibliography → CSL-JSON mapping

Take a DeepSearch-style bibliography (URLs, optionally with `source_id`) and return CSL-JSON keyed by the original reference numbers:

```python
from lit_agent.identifiers import resolve_bibliography

bibliography = [
    {"source_id": "1", "url": "https://pubmed.ncbi.nlm.nih.gov/37674083/"},
    {"source_id": "2", "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC11239014/"},
    {"source_id": "3", "url": "https://doi.org/10.1038/s41586-023-06502-w"},
]

result = resolve_bibliography(
    bibliography,
    validate=True,     # NCBI/metapub validation + metadata fetch
    scrape=False,      # Enable if you want web/PDF scraping for failures
    pdf=False,
    topic_validation=False,
)

print(result.citations["1"]["PMID"])     # "37674083"
print(result.citations["2"]["PMCID"])    # "PMC11239014"
print(result.citations["3"]["DOI"])      # "10.1038/s41586-023-06502-w"
print(result.citations["1"]["resolution"])  # methods, confidence, validation, errors
```

Each citation is CSL-JSON–compatible with a custom `resolution` block:
- `id` is the original `source_id` (or 1-based string if absent)
- `URL`, identifiers (`DOI`/`PMID`/`PMCID`), optional metadata (`title`, `author`, `container-title`, `issued`, etc.)
- `resolution`: `confidence`, `methods`, `validation` statuses, `errors`, `source_url`, optional `canonical_id`

### Academic Identifier Extraction

Extract DOI, PMID, and PMC identifiers from academic URLs with comprehensive validation:

```python
from lit_agent.identifiers import extract_identifiers_from_bibliography

# Basic extraction from URLs
urls = [
    "https://pubmed.ncbi.nlm.nih.gov/37674083/",
    "https://www.nature.com/articles/s41586-023-06812-z",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC11239014/"
]

result = extract_identifiers_from_bibliography(
    urls=urls,
    use_web_scraping=True,      # Enable Phase 2 web scraping
    use_api_validation=True,    # Enable NCBI API validation
    use_topic_validation=True   # Enable LLM topic validation
)

print(f"Found {len(result.identifiers)} identifiers")
print(f"Success rate: {result.success_rate:.1%}")
```

### Comprehensive Validation Assessment

Run a complete validation assessment with detailed reporting and visualizations:

```python
from lit_agent.identifiers.validation_demo import run_validation_assessment_demo

# Run comprehensive validation assessment
report = run_validation_assessment_demo(
    urls=None,  # Uses default astrocyte biology test URLs
    use_topic_validation=True,
    output_dir="validation_reports",
    report_name="my_assessment"
)

# Check validation quality score
print(f"Validation Quality Score: {report['quality_score']}/100")
```

This generates:
- **JSON Report**: Complete validation statistics and metadata
- **Text Summary**: Human-readable assessment with recommendations
- **CSV Export**: Detailed paper information for spreadsheet analysis
- **Interactive HTML**: Visual dashboard with charts and insights
- **Visualizations**: 6 different chart types analyzing validation performance

### Topic Validation for Specific Research Domains

Validate that extracted papers are relevant to your research topic:

```python
from lit_agent.identifiers.topic_validator import TopicValidator

validator = TopicValidator()

# Validate a single identifier for astrocyte biology relevance
identifier = result.identifiers[0]
validation_result = validator.validate_identifier(identifier)

print(f"Relevant: {validation_result['is_relevant']}")
print(f"Confidence: {validation_result['confidence']}%")
print(f"Reasoning: {validation_result['reasoning']}")
```

### Manual Review Workflow

The system provides systematic guidance for manual review:

```python
# Generate paper classifications for manual review
from lit_agent.identifiers.reporting import ValidationReporter

reporter = ValidationReporter()
report = reporter.generate_validation_report(results, "manual_review")

# Papers needing manual review
classifications = report["paper_classifications"]
needs_review = classifications["needs_manual_review"]
low_confidence = classifications["low_confidence_relevant"]

print(f"Papers requiring manual review: {len(needs_review)}")
print(f"Low confidence papers: {len(low_confidence)}")
```

### LLM Integration

Use the unified LLM API for custom analyses:

```python
from lit_agent.agent_connection import create_agent_from_env

# Create agents from environment variables
agent = create_agent_from_env("anthropic")
response = agent.query("Analyze this paper abstract for astrocyte biology relevance...")
```

### Command Line Interface

Run validation assessments directly from the command line:

```bash
# Run demo with default astrocyte biology URLs
uv run python -m lit_agent.identifiers.validation_demo

# Or run with Python directly
python src/lit_agent/identifiers/validation_demo.py

# Check the generated reports
ls demo_reports/
# validation_demo_20241105_143022.json
# validation_demo_20241105_143022_summary.txt
# validation_demo_20241105_143022_papers.csv
# validation_demo_20241105_143022.html
```

The demo script provides:
- ✅ **Real-time Progress**: Live updates on extraction and validation progress
- 📊 **Immediate Results**: Success rates, identifier counts, and confidence distributions
- 🎯 **Topic Analysis**: Relevance assessment for astrocyte biology research
- 💡 **Actionable Recommendations**: Specific suggestions for quality improvement
- 🌐 **Interactive Reports**: HTML dashboard with embedded visualizations

## Troubleshooting

### Common Issues

**1. NCBI API Rate Limiting**
```bash
# Error: HTTPSConnectionPool... Read timed out
# Solution: Add NCBI API key and email to .env
NCBI_EMAIL=your_email@domain.com
NCBI_API_KEY=your_ncbi_key
```

**2. LLM API Errors**
```bash
# Error: No API key provided
# Solution: Verify your .env file has the correct keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

**3. Missing Dependencies**
```bash
# Error: No module named 'matplotlib'
# Solution: Install visualization dependencies
uv sync --dev
# or
pip install matplotlib beautifulsoup4 pypdf lxml
```

**4. Low Validation Quality Scores**
- **Check Topic Validation**: Ensure your research domain matches the built-in astrocyte biology validation
- **Review URLs**: Verify input URLs are from academic sources
- **API Connectivity**: Confirm NCBI API access is working
- **Manual Review**: Use the paper classifications to identify systematic issues

### Performance Optimization

**For Large URL Lists**:
- Enable caching for topic validation results
- Use batch processing for NCBI API calls
- Consider running validation in parallel chunks
- Monitor API rate limits and adjust delays

**For Custom Research Domains**:
- Modify the topic validation prompts in `topic_validator.py`
- Update keyword lists for your specific field
- Adjust confidence thresholds based on domain expertise

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

## Validation Assessment Features

### Multi-Phase Extraction Pipeline

1. **Phase 1 - URL Pattern Extraction**: Fast extraction using regex patterns for known journal URLs
2. **Phase 2 - Web Scraping**: BeautifulSoup-based scraping for meta tags and JSON-LD data
3. **Phase 3 - PDF Text Analysis**: LLM-powered extraction from PDF content when available

### Validation Methods

- **Format Validation**: Verify identifier formats (DOI, PMID, PMC patterns)
- **NCBI API Validation**: Real-time verification against PubMed database with metadata retrieval
- **Metapub Integration**: Cross-validation using metapub library
- **Topic Validation**: LLM-based assessment of paper relevance to research domains

### Reporting & Analytics

- **Comprehensive Statistics**: Success rates, processing times, confidence distributions
- **Interactive Visualizations**: 6 chart types including confidence histograms, method comparisons, and topic analysis
- **Quality Scoring**: Data-driven assessment with actionable recommendations
- **Manual Review Guidance**: Stratified sampling strategies based on confidence scores

### Pause-Point Assessment

The system provides systematic checkpoints for quality control:

- **Validation Quality Score**: 0-100 rating based on relevance, confidence, and success rates
- **Automated Recommendations**: Specific suggestions for improving extraction quality
- **Paper Classifications**: Systematic categorization for manual review prioritization
- **Statistical Robustness**: Confidence intervals and sample size recommendations

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
