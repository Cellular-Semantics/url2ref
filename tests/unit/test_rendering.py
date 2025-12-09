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
