"""Unit tests for bibliography rendering helpers."""

import pytest

from lit_agent.identifiers import (
    CitationResolutionResult,
    render_bibliography_to_strings,
)


@pytest.mark.unit
def test_render_bibliography_fallback(monkeypatch):
    """Render should fall back to compact mode when citeproc is unavailable."""

    def raise_import_error():
        raise ImportError("citeproc not installed")

    monkeypatch.setattr(
        "lit_agent.identifiers.api._import_citeproc",
        raise_import_error,
    )

    result = CitationResolutionResult(
        citations={
            "1": {
                "id": "1",
                "title": "Example Paper",
                "author": [{"family": "Doe"}],
                "issued": {"date-parts": [[2024]]},
                "DOI": "10.1234/example",
                "resolution": {},
                "URL": "https://example.com",
            },
        },
        stats={},
        failures=[],
    )

    rendered, meta = render_bibliography_to_strings(result, style="vancouver")

    assert rendered[0].startswith("[1] Doe Example Paper 2024 10.1234/example")
    assert meta["renderer"] == "fallback"
    assert meta["style"] == "vancouver"


@pytest.mark.unit
def test_render_bibliography_vancouver_style():
    """Test proper bibliography rendering with vancouver style."""
    result = CitationResolutionResult(
        citations={
            "1": {
                "id": "1",
                "title": "Example Paper on Glioblastoma",
                "author": [{"family": "Doe", "given": "John"}],
                "issued": {"date-parts": [[2024]]},
                "container-title": "Nature",
                "DOI": "10.1234/example",
                "resolution": {"method": "doi"},
                "URL": "https://example.com",
            },
        },
        stats={"total": 1, "resolved": 1},
        failures=[],
    )

    rendered, meta = render_bibliography_to_strings(result, style="vancouver")

    # Should use citeproc renderer with citeproc-py-styles installed
    assert meta["renderer"] == "citeproc", (
        "Expected citeproc renderer but got fallback. "
        "Ensure citeproc-py-styles is installed: pip install citeproc-py-styles"
    )
    assert meta["style"] == "vancouver"
    assert meta["locale"] == "en-US"

    # Bibliography should be properly formatted and non-empty
    assert len(rendered) == 1, "Should have one bibliography entry"
    assert rendered[0], "Bibliography entry should not be empty"
    assert "Doe" in rendered[0], "Author name should appear in citation"
    assert "2024" in rendered[0], "Publication year should appear"


@pytest.mark.unit
def test_render_bibliography_apa_style():
    """Test bibliography rendering with APA style."""
    result = CitationResolutionResult(
        citations={
            "1": {
                "id": "1",
                "title": "Machine Learning in Cancer Research",
                "author": [
                    {"family": "Smith", "given": "Jane"},
                    {"family": "Johnson", "given": "Bob"},
                ],
                "issued": {"date-parts": [[2023]]},
                "container-title": "Cell",
                "DOI": "10.5678/test",
                "resolution": {"method": "doi"},
            },
        },
        stats={"total": 1, "resolved": 1},
        failures=[],
    )

    rendered, meta = render_bibliography_to_strings(result, style="apa")

    assert meta["renderer"] == "citeproc", (
        "Expected citeproc renderer. Ensure citeproc-py-styles is installed."
    )
    assert meta["style"] == "apa"
    assert len(rendered) == 1
    assert "Smith" in rendered[0]
    assert "2023" in rendered[0]


@pytest.mark.unit
def test_render_bibliography_chicago_style():
    """Test bibliography rendering with Chicago style."""
    result = CitationResolutionResult(
        citations={
            "1": {
                "id": "1",
                "title": "The Role of Inflammation in Disease",
                "author": [{"family": "Brown", "given": "Alice"}],
                "issued": {"date-parts": [[2022]]},
                "container-title": "Science",
                "DOI": "10.9999/chicago-test",
                "resolution": {"method": "doi"},
            },
        },
        stats={"total": 1, "resolved": 1},
        failures=[],
    )

    rendered, meta = render_bibliography_to_strings(result, style="chicago")

    assert meta["renderer"] == "citeproc"
    assert meta["style"] == "chicago"
    assert len(rendered) == 1
    assert rendered[0]  # Non-empty


@pytest.mark.unit
def test_render_bibliography_multiple_citations():
    """Test rendering multiple citations in correct order."""
    result = CitationResolutionResult(
        citations={
            "1": {
                "id": "1",
                "title": "First Paper",
                "author": [{"family": "Alpha", "given": "A"}],
                "issued": {"date-parts": [[2021]]},
                "DOI": "10.1111/first",
            },
            "2": {
                "id": "2",
                "title": "Second Paper",
                "author": [{"family": "Beta", "given": "B"}],
                "issued": {"date-parts": [[2022]]},
                "DOI": "10.2222/second",
            },
            "3": {
                "id": "3",
                "title": "Third Paper",
                "author": [{"family": "Gamma", "given": "C"}],
                "issued": {"date-parts": [[2023]]},
                "DOI": "10.3333/third",
            },
        },
        stats={"total": 3, "resolved": 3},
        failures=[],
    )

    rendered, meta = render_bibliography_to_strings(result, style="vancouver")

    assert meta["renderer"] == "citeproc"
    assert len(rendered) == 3, "Should have three bibliography entries"

    # Check all entries are non-empty
    for entry in rendered:
        assert entry, "Each bibliography entry should be non-empty"

    # Check authors appear in their respective entries
    assert "Alpha" in rendered[0]
    assert "Beta" in rendered[1]
    assert "Gamma" in rendered[2]


@pytest.mark.unit
def test_render_bibliography_empty_citations():
    """Test rendering with no citations."""
    result = CitationResolutionResult(
        citations={},
        stats={"total": 0, "resolved": 0},
        failures=[],
    )

    rendered, meta = render_bibliography_to_strings(result, style="vancouver")

    # Even with no citations, should use citeproc if available
    assert meta["renderer"] in ["citeproc", "fallback"]
    assert meta["style"] == "vancouver"
    assert len(rendered) == 0, "Should have no bibliography entries"


@pytest.mark.unit
def test_render_bibliography_with_locale():
    """Test bibliography rendering with different locale."""
    result = CitationResolutionResult(
        citations={
            "1": {
                "id": "1",
                "title": "Example Paper",
                "author": [{"family": "Doe", "given": "John"}],
                "issued": {"date-parts": [[2024]]},
                "DOI": "10.1234/example",
            },
        },
        stats={"total": 1, "resolved": 1},
        failures=[],
    )

    rendered, meta = render_bibliography_to_strings(
        result, style="vancouver", locale="en-GB"
    )

    assert meta["renderer"] == "citeproc"
    assert meta["locale"] == "en-GB"
    assert len(rendered) == 1
