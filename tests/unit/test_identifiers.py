"""Unit tests for academic identifier extraction."""

import pytest

from lit_agent.identifiers import (
    AcademicIdentifier,
    IdentifierType,
    ExtractionMethod,
    IdentifierExtractionResult,
    extract_identifiers_from_bibliography,
    URLPatternExtractor,
    JournalURLExtractor,
    FormatValidator,
)


@pytest.mark.unit
class TestIdentifierExtractionFromDeepsearch:
    """Test identifier extraction using real URLs from Deepsearch examples."""

    @pytest.fixture
    def sample_deepsearch_urls(self):
        """Sample URLs extracted from Deepsearch examples."""
        return [
            # PMC URLs
            "https://pmc.ncbi.nlm.nih.gov/articles/PMC11239014/",
            "https://pmc.ncbi.nlm.nih.gov/articles/PMC7880286/",
            "https://pmc.ncbi.nlm.nih.gov/articles/PMC6187980/",
            "https://pmc.ncbi.nlm.nih.gov/articles/PMC3610681/",
            # PubMed URLs
            "https://pubmed.ncbi.nlm.nih.gov/37674083/",
            "https://pubmed.ncbi.nlm.nih.gov/32139688/",
            "https://pubmed.ncbi.nlm.nih.gov/32809228/",
            "https://pubmed.ncbi.nlm.nih.gov/35587512/",
            # DOI URLs - Science
            "https://www.science.org/doi/10.1126/science.abm5224",
            "https://www.science.org/doi/10.1126/science.adc9020",
            "https://www.science.org/doi/10.1126/sciadv.abe8978",
            # DOI URLs - Nature
            "https://www.nature.com/articles/s41586-023-06502-w",
            "https://www.nature.com/articles/s41593-023-01464-8",
            "https://www.nature.com/articles/s41467-019-14198-8",
            "https://www.nature.com/articles/s41591-024-03150-z",
            "https://www.nature.com/articles/s41593-024-01791-4",
            "https://www.nature.com/articles/s41467-025-61829-4",
            "https://www.nature.com/articles/s41398-025-03562-6",
            # DOI URLs - PNAS
            "https://www.pnas.org/doi/10.1073/pnas.2303809120",
            "https://www.pnas.org/doi/10.1073/pnas.1716032115",
            # Wiley URLs
            "https://onlinelibrary.wiley.com/doi/full/10.1002/glia.24621",
            "https://onlinelibrary.wiley.com/doi/10.1002/glia.24479",
            "https://onlinelibrary.wiley.com/doi/full/10.1002/glia.24016",
            "https://onlinelibrary.wiley.com/doi/10.1002/glia.24605",
            # Direct DOI URLs
            "https://doi.org/10.1371/journal.pone.0302376",
            # Other journal URLs
            "https://elifesciences.org/articles/65482",
            "https://www.biorxiv.org/content/10.1101/2024.03.27.586938v1.full",
        ]

    def test_extract_pmid_from_pubmed_urls(self, sample_deepsearch_urls):
        """Test PMID extraction from PubMed URLs."""
        extractor = URLPatternExtractor()

        pubmed_urls = [
            url for url in sample_deepsearch_urls if "pubmed.ncbi.nlm.nih.gov" in url
        ]

        for url in pubmed_urls:
            identifiers = extractor.extract_from_url(url)

            # Should extract exactly one PMID
            pmid_identifiers = [
                id for id in identifiers if id.type == IdentifierType.PMID
            ]
            assert len(pmid_identifiers) == 1

            pmid = pmid_identifiers[0]
            assert pmid.type == IdentifierType.PMID
            assert pmid.confidence >= 0.9  # High confidence for direct PubMed URLs
            assert pmid.extraction_method == ExtractionMethod.URL_PATTERN
            assert pmid.source_url == url

            # Validate PMID format
            assert pmid.value.isdigit()
            assert 1 <= len(pmid.value) <= 8

    def test_extract_pmc_from_pmc_urls(self, sample_deepsearch_urls):
        """Test PMC extraction from PMC URLs."""
        extractor = URLPatternExtractor()

        pmc_urls = [
            url for url in sample_deepsearch_urls if "pmc.ncbi.nlm.nih.gov" in url
        ]

        for url in pmc_urls:
            identifiers = extractor.extract_from_url(url)

            # Should extract exactly one PMC
            pmc_identifiers = [
                id for id in identifiers if id.type == IdentifierType.PMC
            ]
            assert len(pmc_identifiers) == 1

            pmc = pmc_identifiers[0]
            assert pmc.type == IdentifierType.PMC
            assert pmc.confidence >= 0.9  # High confidence for direct PMC URLs
            assert pmc.extraction_method == ExtractionMethod.URL_PATTERN
            assert pmc.source_url == url

            # Validate PMC format
            assert pmc.value.startswith("PMC")
            assert pmc.value[3:].isdigit()

    def test_extract_doi_from_journal_urls(self, sample_deepsearch_urls):
        """Test DOI extraction from various journal URLs."""
        extractor = JournalURLExtractor()  # Use journal-aware extractor

        # Expected DOI mappings for some URLs
        expected_dois = {
            "https://www.science.org/doi/10.1126/science.abm5224": "10.1126/science.abm5224",
            "https://www.nature.com/articles/s41586-023-06502-w": "10.1038/s41586-023-06502-w",
            "https://www.pnas.org/doi/10.1073/pnas.2303809120": "10.1073/pnas.2303809120",
            "https://onlinelibrary.wiley.com/doi/full/10.1002/glia.24621": "10.1002/glia.24621",
        }

        for url, expected_doi in expected_dois.items():
            identifiers = extractor.extract_from_url(url)

            # Should extract at least one DOI
            doi_identifiers = [
                id for id in identifiers if id.type == IdentifierType.DOI
            ]
            assert len(doi_identifiers) >= 1

            # Check if we got the expected DOI
            extracted_dois = [id.value for id in doi_identifiers]
            assert expected_doi in extracted_dois

            # Check properties of the extracted DOI
            doi_id = next(id for id in doi_identifiers if id.value == expected_doi)
            assert doi_id.confidence >= 0.8
            assert doi_id.extraction_method == ExtractionMethod.URL_PATTERN
            assert doi_id.source_url == url

    def test_batch_extraction_from_deepsearch_urls(self, sample_deepsearch_urls):
        """Test batch extraction from all Deepsearch URLs."""
        result = extract_identifiers_from_bibliography(
            sample_deepsearch_urls,
            use_api_validation=False,  # Skip API validation for unit tests
            use_metapub_validation=False,
        )

        # Should extract some identifiers
        assert len(result.identifiers) > 0

        # Success rate should be reasonable
        assert result.success_rate > 0.5

        # Should have good statistics
        assert result.extraction_stats["total_urls"] == len(sample_deepsearch_urls)
        assert result.extraction_stats["successful_extractions"] > 0

        # Should have extracted each type of identifier
        doi_count = len(result.get_identifiers_by_type(IdentifierType.DOI))
        pmid_count = len(result.get_identifiers_by_type(IdentifierType.PMID))
        pmc_count = len(result.get_identifiers_by_type(IdentifierType.PMC))

        assert doi_count > 0
        assert pmid_count > 0
        assert pmc_count > 0

        # Processing time should be reasonable
        assert result.processing_time < 30  # Should process quickly


@pytest.mark.unit
class TestURLPatternExtractor:
    """Test URL pattern extraction functionality."""

    def test_pmid_extraction_patterns(self):
        """Test various PMID URL patterns."""
        extractor = URLPatternExtractor()

        test_cases = [
            ("https://pubmed.ncbi.nlm.nih.gov/12345678/", "12345678"),
            ("https://www.ncbi.nlm.nih.gov/pubmed/87654321", "87654321"),
            ("https://pubmed.ncbi.nlm.nih.gov/1234567", "1234567"),
            ("https://pubmed.ncbi.nlm.nih.gov/123456", "123456"),
        ]

        for url, expected_pmid in test_cases:
            identifiers = extractor.extract_from_url(url)
            pmids = [id.value for id in identifiers if id.type == IdentifierType.PMID]
            assert expected_pmid in pmids

    def test_pmc_extraction_patterns(self):
        """Test various PMC URL patterns."""
        extractor = URLPatternExtractor()

        test_cases = [
            ("https://pmc.ncbi.nlm.nih.gov/articles/PMC1234567/", "PMC1234567"),
            ("https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7654321/", "PMC7654321"),
            ("https://pmc.ncbi.nlm.nih.gov/articles/PMC123456", "PMC123456"),
        ]

        for url, expected_pmc in test_cases:
            identifiers = extractor.extract_from_url(url)
            pmcs = [id.value for id in identifiers if id.type == IdentifierType.PMC]
            assert expected_pmc in pmcs

    def test_doi_extraction_patterns(self):
        """Test various DOI URL patterns."""
        extractor = URLPatternExtractor()

        test_cases = [
            ("https://doi.org/10.1126/science.abm5224", "10.1126/science.abm5224"),
            ("https://dx.doi.org/10.1038/nature12345", "10.1038/nature12345"),
            ("https://example.com/doi/10.1002/example.123", "10.1002/example.123"),
        ]

        for url, expected_doi in test_cases:
            identifiers = extractor.extract_from_url(url)
            dois = [id.value for id in identifiers if id.type == IdentifierType.DOI]
            assert expected_doi in dois

    def test_url_decoding(self):
        """Test that URL encoding is properly handled."""
        extractor = URLPatternExtractor()

        # URL with encoded characters
        encoded_url = "https://pubmed.ncbi.nlm.nih.gov/12345678%2F"
        identifiers = extractor.extract_from_url(encoded_url)

        pmids = [id.value for id in identifiers if id.type == IdentifierType.PMID]
        assert "12345678" in pmids

    def test_invalid_urls(self):
        """Test handling of invalid or malformed URLs."""
        extractor = URLPatternExtractor()

        invalid_urls = [
            "",
            None,
            "not-a-url",
            "https://example.com/no-identifiers",
            "https://pubmed.ncbi.nlm.nih.gov/invalid-pmid/",
        ]

        for url in invalid_urls:
            identifiers = extractor.extract_from_url(url)
            # Should not crash and return empty list for invalid URLs
            assert isinstance(identifiers, list)


@pytest.mark.unit
class TestFormatValidator:
    """Test identifier format validation."""

    def test_pmid_format_validation(self):
        """Test PMID format validation."""
        validator = FormatValidator()

        # Valid PMIDs
        valid_pmids = ["1", "123", "12345678", "37674083"]
        for pmid in valid_pmids:
            assert validator.validate_identifier(IdentifierType.PMID, pmid)

        # Invalid PMIDs
        invalid_pmids = ["", "0", "012345", "123456789", "abc123", "123.456"]
        for pmid in invalid_pmids:
            assert not validator.validate_identifier(IdentifierType.PMID, pmid)

    def test_pmc_format_validation(self):
        """Test PMC format validation."""
        validator = FormatValidator()

        # Valid PMCs
        valid_pmcs = ["PMC1", "PMC123", "PMC1234567", "PMC11239014"]
        for pmc in valid_pmcs:
            assert validator.validate_identifier(IdentifierType.PMC, pmc)

        # Invalid PMCs
        invalid_pmcs = ["", "PMC", "pmc123", "123", "PMC0", "PMCABC"]
        for pmc in invalid_pmcs:
            assert not validator.validate_identifier(IdentifierType.PMC, pmc)

    def test_doi_format_validation(self):
        """Test DOI format validation."""
        validator = FormatValidator()

        # Valid DOIs
        valid_dois = [
            "10.1126/science.abm5224",
            "10.1038/s41586-023-06502-w",
            "10.1002/glia.24621",
            "10.1073/pnas.2303809120",
        ]
        for doi in valid_dois:
            assert validator.validate_identifier(IdentifierType.DOI, doi)

        # Invalid DOIs
        invalid_dois = [
            "",
            "10.123",  # Registrant too short
            "10.1234/",  # Empty suffix
            "doi:10.1234/example",  # Has prefix
            "not-a-doi",
        ]
        for doi in invalid_dois:
            assert not validator.validate_identifier(IdentifierType.DOI, doi)


@pytest.mark.unit
class TestAcademicIdentifier:
    """Test AcademicIdentifier data structure."""

    def test_identifier_creation(self):
        """Test creating AcademicIdentifier objects."""
        identifier = AcademicIdentifier(
            type=IdentifierType.PMID,
            value="12345678",
            confidence=0.95,
            source_url="https://pubmed.ncbi.nlm.nih.gov/12345678/",
            extraction_method=ExtractionMethod.URL_PATTERN,
        )

        assert identifier.type == IdentifierType.PMID
        assert identifier.value == "12345678"
        assert identifier.confidence == 0.95
        assert identifier.is_high_confidence
        assert identifier.timestamp is not None

    def test_identifier_serialization(self):
        """Test converting identifier to dictionary."""
        identifier = AcademicIdentifier(
            type=IdentifierType.DOI,
            value="10.1126/science.abm5224",
            confidence=0.88,
            source_url="https://www.science.org/doi/10.1126/science.abm5224",
            extraction_method=ExtractionMethod.URL_PATTERN,
        )

        data = identifier.to_dict()

        assert data["type"] == "doi"
        assert data["value"] == "10.1126/science.abm5224"
        assert data["confidence"] == 0.88
        assert data["extraction_method"] == "url_pattern"
        assert "timestamp" in data

    def test_confidence_classification(self):
        """Test confidence level classification."""
        high_conf = AcademicIdentifier(
            type=IdentifierType.PMC,
            value="PMC123456",
            confidence=0.92,
            source_url="test",
            extraction_method=ExtractionMethod.URL_PATTERN,
        )

        low_conf = AcademicIdentifier(
            type=IdentifierType.PMC,
            value="PMC123456",
            confidence=0.65,
            source_url="test",
            extraction_method=ExtractionMethod.URL_PATTERN,
        )

        assert high_conf.is_high_confidence
        assert not low_conf.is_high_confidence


@pytest.mark.unit
class TestExtractionResult:
    """Test IdentifierExtractionResult functionality."""

    def test_result_statistics(self):
        """Test extraction result statistics."""
        identifiers = [
            AcademicIdentifier(
                IdentifierType.PMID, "123", 0.9, "url1", ExtractionMethod.URL_PATTERN
            ),
            AcademicIdentifier(
                IdentifierType.DOI,
                "10.1234/test",
                0.85,
                "url2",
                ExtractionMethod.URL_PATTERN,
            ),
            AcademicIdentifier(
                IdentifierType.PMC, "PMC123", 0.75, "url3", ExtractionMethod.URL_PATTERN
            ),
        ]

        result = IdentifierExtractionResult(
            identifiers=identifiers,
            failed_urls=["url4", "url5"],
            extraction_stats={"total_urls": 5, "successful_extractions": 3},
        )

        assert result.success_rate == 0.6  # 3 successes out of 5 total
        assert result.high_confidence_count == 2  # 2 with confidence >= 0.8

        # Test filtering by type
        pmid_ids = result.get_identifiers_by_type(IdentifierType.PMID)
        assert len(pmid_ids) == 1
        assert pmid_ids[0].value == "123"

    def test_result_serialization(self):
        """Test result serialization to dictionary."""
        identifiers = [
            AcademicIdentifier(
                IdentifierType.PMID, "123", 0.9, "url1", ExtractionMethod.URL_PATTERN
            )
        ]

        result = IdentifierExtractionResult(
            identifiers=identifiers,
            failed_urls=["url2"],
            extraction_stats={"total_urls": 2},
        )

        data = result.to_dict()

        assert len(data["identifiers"]) == 1
        assert data["failed_urls"] == ["url2"]
        assert data["extraction_stats"]["total_urls"] == 2
        assert "success_rate" in data
        assert "high_confidence_count" in data
