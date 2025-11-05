"""Unit tests for web scraping extractors."""

import pytest
from unittest.mock import Mock, patch
import json

from lit_agent.identifiers.web_scrapers import WebScrapingExtractor, PDFExtractor
from lit_agent.identifiers.base import IdentifierType, ExtractionMethod


@pytest.mark.unit
class TestWebScrapingExtractor:
    """Test web scraping functionality."""

    @pytest.fixture
    def extractor(self):
        """Create a WebScrapingExtractor instance."""
        return WebScrapingExtractor(rate_limit=0.1)

    def test_extract_from_meta_tags(self, extractor):
        """Test extraction from HTML meta tags."""
        html = """
        <html>
        <head>
            <meta name="citation_doi" content="10.1234/example">
            <meta name="citation_pmid" content="12345678">
            <meta property="citation_pmc" content="PMC1234567">
        </head>
        </html>
        """

        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.content = html.encode()
            mock_get.return_value = mock_response

            identifiers = extractor.extract_from_url("https://example.com/article")

            assert len(identifiers) == 3

            # Check DOI
            doi_ids = [id for id in identifiers if id.type == IdentifierType.DOI]
            assert len(doi_ids) == 1
            assert doi_ids[0].value == "10.1234/example"
            assert doi_ids[0].confidence == 0.9

            # Check PMID
            pmid_ids = [id for id in identifiers if id.type == IdentifierType.PMID]
            assert len(pmid_ids) == 1
            assert pmid_ids[0].value == "12345678"

            # Check PMC
            pmc_ids = [id for id in identifiers if id.type == IdentifierType.PMC]
            assert len(pmc_ids) == 1
            assert pmc_ids[0].value == "PMC1234567"

    def test_extract_from_json_ld(self, extractor):
        """Test extraction from JSON-LD structured data."""
        html = """
        <html>
        <head>
            <script type="application/ld+json">
            {
                "@type": "ScholarlyArticle",
                "identifier": "10.1234/json-ld-example",
                "name": "Test Article"
            }
            </script>
        </head>
        </html>
        """

        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.content = html.encode()
            mock_get.return_value = mock_response

            identifiers = extractor.extract_from_url("https://example.com/article")

            assert len(identifiers) == 1
            assert identifiers[0].type == IdentifierType.DOI
            assert identifiers[0].value == "10.1234/json-ld-example"
            assert identifiers[0].confidence == 0.85

    def test_extract_from_content(self, extractor):
        """Test extraction from page content."""
        html = """
        <html>
        <body>
            <p>This article has DOI: 10.1234/content-example</p>
            <p>PMID: 87654321</p>
            <p>See also PMC9876543</p>
        </body>
        </html>
        """

        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.content = html.encode()
            mock_get.return_value = mock_response

            identifiers = extractor.extract_from_url("https://example.com/article")

            assert len(identifiers) >= 3

            # Should find DOI, PMID, and PMC in content
            types_found = {id.type for id in identifiers}
            assert IdentifierType.DOI in types_found
            assert IdentifierType.PMID in types_found
            assert IdentifierType.PMC in types_found

    def test_http_error_handling(self, extractor):
        """Test handling of HTTP errors."""
        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_get.return_value = mock_response

            identifiers = extractor.extract_from_url("https://example.com/notfound")
            assert identifiers == []

    def test_request_exception_handling(self, extractor):
        """Test handling of request exceptions."""
        with patch("requests.get") as mock_get:
            mock_get.side_effect = Exception("Network error")

            identifiers = extractor.extract_from_url("https://example.com/error")
            assert identifiers == []

    def test_invalid_url_handling(self, extractor):
        """Test handling of invalid URLs."""
        assert extractor.extract_from_url("") == []
        assert extractor.extract_from_url(None) == []
        assert extractor.extract_from_url(123) == []

    def test_rate_limiting(self, extractor):
        """Test that rate limiting works."""
        html = "<html><head><meta name='citation_doi' content='10.1234/test'></head></html>"

        with patch("requests.get") as mock_get, patch("time.sleep") as mock_sleep:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.content = html.encode()
            mock_get.return_value = mock_response

            # Make two quick requests
            extractor.extract_from_url("https://example.com/1")
            extractor.extract_from_url("https://example.com/2")

            # Should have called sleep for rate limiting
            mock_sleep.assert_called()


@pytest.mark.unit
class TestPDFExtractor:
    """Test PDF extraction functionality."""

    @pytest.fixture
    def extractor(self):
        """Create a PDFExtractor instance."""
        return PDFExtractor(rate_limit=0.1)

    def test_is_pdf_url(self, extractor):
        """Test PDF URL detection."""
        assert extractor.is_pdf_url("https://example.com/paper.pdf")
        assert extractor.is_pdf_url("https://example.com/paper.pdf?download=1")
        assert not extractor.is_pdf_url("https://example.com/paper.html")
        assert not extractor.is_pdf_url("https://example.com/paper")

    def test_non_pdf_url_skipped(self, extractor):
        """Test that non-PDF URLs are skipped."""
        identifiers = extractor.extract_from_url("https://example.com/article.html")
        assert identifiers == []

    @patch("litellm.completion")
    @patch("requests.get")
    def test_llm_extraction(self, mock_get, mock_llm, extractor):
        """Test LLM-based identifier extraction from PDF."""
        # Mock PDF download
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"fake pdf content"
        mock_get.return_value = mock_response

        # Mock PDF text extraction
        with patch.object(extractor, "_extract_pdf_text") as mock_extract:
            mock_extract.return_value = "This is a paper with DOI: 10.1234/test"

            # Mock LLM response
            mock_choice = Mock()
            mock_choice.message.content = json.dumps(
                {"doi": "10.1234/test", "pmid": "12345678"}
            )
            mock_llm_response = Mock()
            mock_llm_response.choices = [mock_choice]
            mock_llm.return_value = mock_llm_response

            identifiers = extractor.extract_from_url("https://example.com/paper.pdf")

            assert len(identifiers) == 2

            # Check DOI
            doi_ids = [id for id in identifiers if id.type == IdentifierType.DOI]
            assert len(doi_ids) == 1
            assert doi_ids[0].value == "10.1234/test"
            assert doi_ids[0].extraction_method == ExtractionMethod.API_LOOKUP

            # Check PMID
            pmid_ids = [id for id in identifiers if id.type == IdentifierType.PMID]
            assert len(pmid_ids) == 1
            assert pmid_ids[0].value == "12345678"

    def test_pdf_text_extraction_failure(self, extractor):
        """Test handling when PDF text extraction fails."""
        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.content = b"fake pdf content"
            mock_get.return_value = mock_response

            with patch.object(extractor, "_extract_pdf_text") as mock_extract:
                mock_extract.return_value = ""  # Empty text

                identifiers = extractor.extract_from_url(
                    "https://example.com/paper.pdf"
                )
                assert identifiers == []

    def test_llm_failure_handling(self, extractor):
        """Test handling when LLM extraction fails."""
        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.content = b"fake pdf content"
            mock_get.return_value = mock_response

            with patch.object(extractor, "_extract_pdf_text") as mock_extract:
                mock_extract.return_value = "Some PDF text"

                with patch.object(extractor, "_extract_with_llm") as mock_llm:
                    mock_llm.side_effect = Exception("LLM failed")

                    identifiers = extractor.extract_from_url(
                        "https://example.com/paper.pdf"
                    )
                    assert identifiers == []

    def test_invalid_identifier_filtering(self, extractor):
        """Test that invalid identifiers are filtered out."""
        # Test validation method directly
        assert extractor._validate_identifier_format(
            IdentifierType.DOI, "10.1234/valid"
        )
        assert not extractor._validate_identifier_format(
            IdentifierType.DOI, "invalid-doi"
        )

        assert extractor._validate_identifier_format(IdentifierType.PMID, "12345678")
        assert not extractor._validate_identifier_format(
            IdentifierType.PMID, "01234567"
        )  # Leading zero

        assert extractor._validate_identifier_format(IdentifierType.PMC, "PMC1234567")
        assert not extractor._validate_identifier_format(
            IdentifierType.PMC, "1234567"
        )  # Missing PMC prefix


@pytest.mark.unit
class TestIdentifierValidation:
    """Test identifier format validation."""

    def test_doi_validation(self):
        """Test DOI format validation."""
        extractor = WebScrapingExtractor()

        # Valid DOIs
        assert extractor._validate_identifier_format(
            IdentifierType.DOI, "10.1234/example"
        )
        assert extractor._validate_identifier_format(
            IdentifierType.DOI, "10.12345/long.example.2023"
        )

        # Invalid DOIs
        assert not extractor._validate_identifier_format(
            IdentifierType.DOI, "10.123/too-short"
        )  # Registrant too short
        assert not extractor._validate_identifier_format(
            IdentifierType.DOI, "doi:10.1234/prefixed"
        )  # Has prefix
        assert not extractor._validate_identifier_format(IdentifierType.DOI, "")
        assert not extractor._validate_identifier_format(IdentifierType.DOI, None)

    def test_pmid_validation(self):
        """Test PMID format validation."""
        extractor = WebScrapingExtractor()

        # Valid PMIDs
        assert extractor._validate_identifier_format(IdentifierType.PMID, "1")
        assert extractor._validate_identifier_format(IdentifierType.PMID, "12345678")
        assert extractor._validate_identifier_format(IdentifierType.PMID, "987654")

        # Invalid PMIDs
        assert not extractor._validate_identifier_format(
            IdentifierType.PMID, "0"
        )  # Zero
        assert not extractor._validate_identifier_format(
            IdentifierType.PMID, "01234567"
        )  # Leading zero
        assert not extractor._validate_identifier_format(
            IdentifierType.PMID, "123456789"
        )  # Too long
        assert not extractor._validate_identifier_format(
            IdentifierType.PMID, "abc123"
        )  # Non-numeric
        assert not extractor._validate_identifier_format(IdentifierType.PMID, "")

    def test_pmc_validation(self):
        """Test PMC format validation."""
        extractor = WebScrapingExtractor()

        # Valid PMC IDs
        assert extractor._validate_identifier_format(IdentifierType.PMC, "PMC1")
        assert extractor._validate_identifier_format(IdentifierType.PMC, "PMC1234567")
        assert extractor._validate_identifier_format(IdentifierType.PMC, "PMC999999999")

        # Invalid PMC IDs
        assert not extractor._validate_identifier_format(
            IdentifierType.PMC, "PMC"
        )  # No number
        assert not extractor._validate_identifier_format(
            IdentifierType.PMC, "pmc123"
        )  # Lowercase
        assert not extractor._validate_identifier_format(
            IdentifierType.PMC, "123456"
        )  # Missing prefix
        assert not extractor._validate_identifier_format(
            IdentifierType.PMC, "PMCABC"
        )  # Non-numeric
        assert not extractor._validate_identifier_format(IdentifierType.PMC, "")
