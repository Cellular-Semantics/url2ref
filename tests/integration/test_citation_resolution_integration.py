"""Integration test for bibliography resolution hitting real services."""

import pytest

from lit_agent.identifiers import resolve_bibliography


@pytest.mark.integration
def test_resolve_bibliography_live_ncbi_lookup():
    """Ensure resolve_bibliography works against live PubMed/PMC entries."""

    bibliography = [
        {
            "source_id": "pubmed",
            "url": "https://pubmed.ncbi.nlm.nih.gov/37674083/",
        },
        {
            "source_id": "pmc",
            "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC11239014/",
        },
    ]

    result = resolve_bibliography(
        bibliography,
        validate=True,
        scrape=False,
        pdf=False,
        topic_validation=False,
    )

    assert set(result.citations.keys()) == {"pubmed", "pmc"}
    assert result.stats["resolved"] == 2
    assert not result.failures

    pubmed_citation = result.citations["pubmed"]
    assert pubmed_citation["PMID"] == "37674083"
    assert pubmed_citation["resolution"]["confidence"] > 0.8
    assert "url_pattern" in pubmed_citation["resolution"]["methods"]
    assert pubmed_citation["resolution"]["validation"]["ncbi"] in {"passed", "unknown", "failed"}

    pmc_citation = result.citations["pmc"]
    assert pmc_citation["PMCID"] == "PMC11239014"
    assert pmc_citation["resolution"]["confidence"] > 0.8
    assert "url_pattern" in pmc_citation["resolution"]["methods"]
