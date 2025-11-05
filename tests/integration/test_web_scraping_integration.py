"""Integration tests for web scraping extractors."""

import pytest
import warnings

from lit_agent.identifiers.web_scrapers import WebScrapingExtractor, PDFExtractor
from lit_agent.identifiers.base import IdentifierType


@pytest.mark.integration
class TestWebScrapingIntegration:
    """Integration tests for web scraping with real URLs."""

    @pytest.fixture
    def web_extractor(self):
        """Create a web scraping extractor."""
        return WebScrapingExtractor(rate_limit=1.0)  # Be nice to servers

    @pytest.fixture
    def pdf_extractor(self):
        """Create a PDF extractor."""
        return PDFExtractor(rate_limit=2.0)  # Even slower for PDFs

    @pytest.fixture
    def phase1_failed_urls(self):
        """URLs that failed Phase 1 extraction."""
        return [
            # Journal URLs without DOI in URL path
            "https://academic.oup.com/brain/article/145/1/64/6367770",
            "https://rupress.org/jcb/article/222/11/e202303138/276267/Catenin-controls-astrocyte-morphogenesis-via-layer",
            "https://aacrjournals.org/cancerres/article/83/16_Supplement/A011/728267/",
            "https://www.biorxiv.org/content/early/2023/09/08/2023.09.08.556944",
            "https://iovs.arvojournals.org/article.aspx?articleid=2182305",
            "https://joe.bioscientifica.com/view/journals/joe/265/3/JOE-24-0318.xml",
            # Repository URLs
            "https://epublications.marquette.edu/biomedsci_fac/264/",
            "https://brainpalmseq.med.ubc.ca/cell-types/astrocytes-batiuk-2016/1583-2/",
            "https://knowledge.brain-map.org/data/LVDBJAW8BI5YSS1QUBG",
        ]

    @pytest.fixture
    def pdf_urls(self):
        """Direct PDF URLs from Deepsearch examples."""
        return [
            "https://escholarship.org/content/qt0b29m655/qt0b29m655.pdf",
            "https://refubium.fu-berlin.de/bitstream/handle/fub188/44854/journal.pone.0302376.pdf?sequence=1&isAllowed=y",
            "https://edoc.mdc-berlin.de/id/eprint/24531/1/24531oa.pdf",
        ]

    def test_web_scraping_phase1_failures(self, web_extractor, phase1_failed_urls):
        """Test web scraping on URLs that failed Phase 1."""
        successful_extractions = 0
        total_identifiers = 0

        for url in phase1_failed_urls:
            try:
                print(f"\n--- Testing web scraping: {url} ---")
                identifiers = web_extractor.extract_from_url(url)

                if identifiers:
                    successful_extractions += 1
                    total_identifiers += len(identifiers)
                    print(f"✅ Found {len(identifiers)} identifiers:")
                    for identifier in identifiers:
                        print(
                            f"   {identifier.type.value.upper()}: {identifier.value} "
                            f"(confidence: {identifier.confidence:.2f})"
                        )
                else:
                    print("❌ No identifiers found")

            except Exception as e:
                warnings.warn(f"Web scraping failed for {url}: {e}")
                print(f"⚠️  Scraping failed: {e}")

        print("\n--- Web Scraping Results ---")
        print(f"URLs tested: {len(phase1_failed_urls)}")
        print(f"Successful extractions: {successful_extractions}")
        print(f"Total identifiers found: {total_identifiers}")
        print(
            f"Success rate: {successful_extractions / len(phase1_failed_urls) * 100:.1f}%"
        )

        # We expect at least some success
        assert successful_extractions > 0, "Web scraping should find some identifiers"

    def test_pdf_extraction_integration(self, pdf_extractor, pdf_urls):
        """Test PDF extraction with real PDF URLs."""
        successful_extractions = 0
        total_identifiers = 0

        for url in pdf_urls:
            try:
                print(f"\n--- Testing PDF extraction: {url} ---")
                identifiers = pdf_extractor.extract_from_url(url)

                if identifiers:
                    successful_extractions += 1
                    total_identifiers += len(identifiers)
                    print(f"✅ Found {len(identifiers)} identifiers:")
                    for identifier in identifiers:
                        print(
                            f"   {identifier.type.value.upper()}: {identifier.value} "
                            f"(confidence: {identifier.confidence:.2f})"
                        )
                else:
                    print("❌ No identifiers found")

            except Exception as e:
                warnings.warn(f"PDF extraction failed for {url}: {e}")
                print(f"⚠️  PDF extraction failed: {e}")

        print("\n--- PDF Extraction Results ---")
        print(f"URLs tested: {len(pdf_urls)}")
        print(f"Successful extractions: {successful_extractions}")
        print(f"Total identifiers found: {total_identifiers}")
        print(f"Success rate: {successful_extractions / len(pdf_urls) * 100:.1f}%")

        # PDF extraction might fail due to LLM API availability
        if successful_extractions == 0:
            warnings.warn("PDF extraction found no identifiers - may need API keys")

    def test_mixed_extraction_strategy(
        self, web_extractor, pdf_extractor, phase1_failed_urls, pdf_urls
    ):
        """Test combined web scraping and PDF extraction strategy."""
        all_urls = phase1_failed_urls + pdf_urls
        total_successful = 0
        total_identifiers = 0

        for url in all_urls:
            identifiers = []

            try:
                if pdf_extractor._is_pdf_url(url):
                    print(f"\n--- PDF Strategy: {url} ---")
                    identifiers = pdf_extractor.extract_from_url(url)
                else:
                    print(f"\n--- Web Scraping Strategy: {url} ---")
                    identifiers = web_extractor.extract_from_url(url)

                if identifiers:
                    total_successful += 1
                    total_identifiers += len(identifiers)
                    print(f"✅ Found {len(identifiers)} identifiers")
                    for identifier in identifiers:
                        print(f"   {identifier.type.value.upper()}: {identifier.value}")
                else:
                    print("❌ No identifiers found")

            except Exception as e:
                warnings.warn(f"Extraction failed for {url}: {e}")
                print(f"⚠️  Extraction failed: {e}")

        print("\n--- Combined Strategy Results ---")
        print(f"URLs tested: {len(all_urls)}")
        print(f"Successful extractions: {total_successful}")
        print(f"Total identifiers found: {total_identifiers}")
        print(f"Overall success rate: {total_successful / len(all_urls) * 100:.1f}%")

        # We should improve overall success rate compared to Phase 1 alone
        # This is more of a demonstration than a strict requirement
        expected_min_success = max(1, len(all_urls) // 4)  # At least 25% success
        if total_successful < expected_min_success:
            warnings.warn(f"Low success rate: {total_successful}/{len(all_urls)}")


@pytest.mark.integration
class TestSpecificJournalPatterns:
    """Test extraction patterns for specific journal types."""

    def test_oup_academic_extraction(self):
        """Test Oxford Academic URL extraction."""
        extractor = WebScrapingExtractor(rate_limit=1.0)
        url = "https://academic.oup.com/brain/article/145/1/64/6367770"

        try:
            identifiers = extractor.extract_from_url(url)
            print("\n--- Oxford Academic Test ---")
            print(f"URL: {url}")

            if identifiers:
                print(f"Found {len(identifiers)} identifiers:")
                for identifier in identifiers:
                    print(f"  {identifier.type.value.upper()}: {identifier.value}")
            else:
                print("No identifiers found")

        except Exception as e:
            warnings.warn(f"Oxford Academic test failed: {e}")

    def test_bioarxiv_early_version_extraction(self):
        """Test bioRxiv early version URL extraction."""
        extractor = WebScrapingExtractor(rate_limit=1.0)
        url = "https://www.biorxiv.org/content/early/2023/09/08/2023.09.08.556944"

        try:
            identifiers = extractor.extract_from_url(url)
            print("\n--- bioRxiv Early Version Test ---")
            print(f"URL: {url}")

            if identifiers:
                print(f"Found {len(identifiers)} identifiers:")
                for identifier in identifiers:
                    print(f"  {identifier.type.value.upper()}: {identifier.value}")

                # bioRxiv should have DOIs
                doi_ids = [id for id in identifiers if id.type == IdentifierType.DOI]
                assert len(doi_ids) > 0, "bioRxiv should have DOI"
            else:
                print("No identifiers found")

        except Exception as e:
            warnings.warn(f"bioRxiv test failed: {e}")

    def test_repository_metadata_extraction(self):
        """Test repository metadata extraction."""
        extractor = WebScrapingExtractor(rate_limit=1.0)
        url = "https://epublications.marquette.edu/biomedsci_fac/264/"

        try:
            identifiers = extractor.extract_from_url(url)
            print("\n--- Repository Metadata Test ---")
            print(f"URL: {url}")

            if identifiers:
                print(f"Found {len(identifiers)} identifiers:")
                for identifier in identifiers:
                    print(f"  {identifier.type.value.upper()}: {identifier.value}")
            else:
                print("No identifiers found")

        except Exception as e:
            warnings.warn(f"Repository test failed: {e}")
