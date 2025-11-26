"""Unit tests for bibliography resolution to CSL-JSON."""

import pytest

from lit_agent.identifiers import resolve_bibliography


@pytest.mark.unit
def test_resolve_bibliography_preserves_source_ids():
    """URLs with explicit source_ids should be keyed by those IDs."""

    entries = [
        {
            "source_id": "10",
            "url": "https://pubmed.ncbi.nlm.nih.gov/12345678/",
        },
        {
            "source_id": "20",
            "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC7654321/",
        },
    ]

    result = resolve_bibliography(
        entries,
        validate=False,
        scrape=False,
        pdf=False,
        topic_validation=False,
    )

    assert set(result.citations.keys()) == {"10", "20"}

    pmid_citation = result.citations["10"]
    assert pmid_citation["id"] == "10"
    assert pmid_citation["URL"] == entries[0]["url"]
    assert pmid_citation["PMID"] == "12345678"
    assert "url_pattern" in pmid_citation["resolution"]["methods"]
    assert pmid_citation["resolution"]["source_url"] == entries[0]["url"]

    pmc_citation = result.citations["20"]
    assert pmc_citation["PMCID"] == "PMC7654321"
    assert result.stats["resolved"] == 2
    assert result.stats["unresolved"] == 0


@pytest.mark.unit
def test_resolve_bibliography_numbers_plain_url_lists():
    """Plain URL lists fall back to 1-based string source_ids."""

    urls = [
        "https://doi.org/10.1234/abc.def.001",
        "https://example.com/not-a-reference",
    ]

    result = resolve_bibliography(
        urls,
        validate=False,
        scrape=False,
        pdf=False,
        topic_validation=False,
    )

    assert list(result.citations.keys()) == ["1", "2"]
    assert result.citations["1"]["DOI"] == "10.1234/abc.def.001"

    assert result.stats["resolved"] == 1
    assert result.stats["unresolved"] == 1
    assert "2" in result.failures
    assert result.citations["2"]["resolution"]["errors"]


@pytest.mark.unit
def test_resolve_bibliography_enriches_metadata(monkeypatch):
    """Metadata lookup should populate CSL fields when provided."""

    url = "https://pubmed.ncbi.nlm.nih.gov/11111111/"

    def fake_metadata_lookup(identifier_type, value):
        return {
            "title": "Sample Article Title",
            "authors": ["Doe J", "Smith A"],
            "journal": "Journal of Examples",
            "pubdate": "2024 Jan 15",
            "pmid": value,
            "pmcid": "PMC9999999",
            "doi": "10.4321/example.doi",
            "volume": "12",
            "issue": "3",
            "pages": "101-110",
        }

    result = resolve_bibliography(
        [url],
        validate=False,
        scrape=False,
        pdf=False,
        topic_validation=False,
        metadata_lookup=fake_metadata_lookup,
    )

    citation = result.citations["1"]
    assert citation["title"] == "Sample Article Title"
    assert citation["container-title"] == "Journal of Examples"
    assert citation["issued"]["date-parts"][0][0] == 2024
    assert citation["author"][0]["family"] == "Doe"
    assert citation["PMID"] == "11111111"
    assert citation["PMCID"] == "PMC9999999"
    assert citation["DOI"] == "10.4321/example.doi"
