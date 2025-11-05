"""Web scraping extractors for academic identifier extraction."""

import logging
import re
import time
from typing import List, Optional, Dict, Any

import requests
from bs4 import BeautifulSoup
import json

from .base import (
    AcademicIdentifier,
    IdentifierType,
    ExtractionMethod,
    IdentifierExtractorBase,
)

logger = logging.getLogger(__name__)


class WebScrapingExtractor(IdentifierExtractorBase):
    """Extract identifiers by scraping web pages."""

    def __init__(self, timeout: int = 10, rate_limit: float = 1.0):
        """Initialize web scraping extractor.

        Args:
            timeout: Request timeout in seconds
            rate_limit: Minimum time between requests in seconds
        """
        self.timeout = timeout
        self.rate_limit = rate_limit
        self.last_request_time = 0.0

        # User agent to avoid basic bot detection
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }

    def extract_from_url(self, url: str) -> List[AcademicIdentifier]:
        """Extract identifiers by scraping a web page.

        Args:
            url: URL to scrape

        Returns:
            List of extracted identifiers
        """
        if not url or not isinstance(url, str):
            return []

        try:
            # Rate limiting
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            if time_since_last < self.rate_limit:
                time.sleep(self.rate_limit - time_since_last)

            # Fetch page
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            self.last_request_time = time.time()

            if response.status_code != 200:
                logger.warning(f"HTTP {response.status_code} for {url}")
                return []

            # Parse HTML
            soup = BeautifulSoup(response.content, "html.parser")
            identifiers = []

            # Extract from meta tags
            identifiers.extend(self._extract_from_meta_tags(soup, url))

            # Extract from JSON-LD structured data
            identifiers.extend(self._extract_from_json_ld(soup, url))

            # Extract from page content
            identifiers.extend(self._extract_from_content(soup, url))

            return identifiers

        except requests.RequestException as e:
            logger.warning(f"Request failed for {url}: {e}")
            return []
        except Exception as e:
            logger.warning(f"Scraping failed for {url}: {e}")
            return []

    def _extract_from_meta_tags(
        self, soup: BeautifulSoup, source_url: str
    ) -> List[AcademicIdentifier]:
        """Extract identifiers from HTML meta tags."""
        identifiers = []

        # Common meta tag patterns for academic papers
        meta_patterns = {
            IdentifierType.DOI: [
                "citation_doi",
                "dc.identifier.doi",
                "prism.doi",
                "DOI",
            ],
            IdentifierType.PMID: [
                "citation_pmid",
                "citation_pubmed_id",
                "dc.identifier.pmid",
            ],
            IdentifierType.PMC: [
                "citation_pmc",
                "citation_pmcid",
                "dc.identifier.pmc",
            ],
        }

        for identifier_type, patterns in meta_patterns.items():
            for pattern in patterns:
                # Try name attribute
                meta = soup.find("meta", {"name": pattern})
                if not meta:
                    # Try property attribute
                    meta = soup.find("meta", {"property": pattern})

                if meta:
                    content = meta.get("content")
                    if content and isinstance(content, str):
                        value = content.strip()
                        if self._validate_identifier_format(identifier_type, value):
                            identifiers.append(
                                AcademicIdentifier(
                                    type=identifier_type,
                                    value=value,
                                    confidence=0.9,  # High confidence for meta tags
                                    source_url=source_url,
                                    extraction_method=ExtractionMethod.WEB_SCRAPING,
                                )
                            )

        return identifiers

    def _extract_from_json_ld(
        self, soup: BeautifulSoup, source_url: str
    ) -> List[AcademicIdentifier]:
        """Extract identifiers from JSON-LD structured data."""
        identifiers = []

        # Find JSON-LD script tags
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                if not script.string:
                    continue
                data = json.loads(script.string)
                if isinstance(data, list):
                    data = data[0]  # Take first item if it's a list

                # Look for ScholarlyArticle or similar
                if data.get("@type") in ["ScholarlyArticle", "Article"]:
                    # Extract DOI
                    doi = self._extract_doi_from_json_ld(data)
                    if doi:
                        identifiers.append(
                            AcademicIdentifier(
                                type=IdentifierType.DOI,
                                value=doi,
                                confidence=0.85,
                                source_url=source_url,
                                extraction_method=ExtractionMethod.WEB_SCRAPING,
                            )
                        )

            except (json.JSONDecodeError, KeyError, TypeError) as e:
                logger.debug(f"Failed to parse JSON-LD: {e}")

        return identifiers

    def _extract_doi_from_json_ld(self, data: Dict[str, Any]) -> Optional[str]:
        """Extract DOI from JSON-LD data."""
        # Check identifier field
        if "identifier" in data:
            identifier = data["identifier"]
            if isinstance(identifier, str) and identifier.startswith("10."):
                return identifier
            elif isinstance(identifier, list):
                for item in identifier:
                    if isinstance(item, str) and item.startswith("10."):
                        return item
                    elif isinstance(item, dict):
                        if (
                            item.get("@type") == "PropertyValue"
                            and item.get("name") == "DOI"
                        ):
                            return item.get("value")

        # Check url field for DOI patterns
        if "url" in data:
            url = data["url"]
            if isinstance(url, str):
                doi_match = re.search(r"10\.\d{4,}/[^\s]+", url)
                if doi_match:
                    return doi_match.group()

        return None

    def _extract_from_content(
        self, soup: BeautifulSoup, source_url: str
    ) -> List[AcademicIdentifier]:
        """Extract identifiers from page content."""
        identifiers = []

        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        # Get text content
        text = soup.get_text()

        # Look for DOI patterns
        doi_pattern = r"\b(10\.\d{4,}/[^\s]+)\b"
        for match in re.finditer(doi_pattern, text):
            doi = match.group(1)
            # Clean up common trailing characters
            doi = re.sub(r"[.,;)]+$", "", doi)
            if self._validate_identifier_format(IdentifierType.DOI, doi):
                identifiers.append(
                    AcademicIdentifier(
                        type=IdentifierType.DOI,
                        value=doi,
                        confidence=0.7,  # Lower confidence for content extraction
                        source_url=source_url,
                        extraction_method=ExtractionMethod.WEB_SCRAPING,
                    )
                )

        # Look for PMID patterns
        pmid_pattern = r"\bPMID:?\s*(\d{1,8})\b"
        for match in re.finditer(pmid_pattern, text, re.IGNORECASE):
            pmid = match.group(1)
            if self._validate_identifier_format(IdentifierType.PMID, pmid):
                identifiers.append(
                    AcademicIdentifier(
                        type=IdentifierType.PMID,
                        value=pmid,
                        confidence=0.8,
                        source_url=source_url,
                        extraction_method=ExtractionMethod.WEB_SCRAPING,
                    )
                )

        # Look for PMC patterns
        pmc_pattern = r"\b(PMC\d+)\b"
        for match in re.finditer(pmc_pattern, text):
            pmc = match.group(1)
            if self._validate_identifier_format(IdentifierType.PMC, pmc):
                identifiers.append(
                    AcademicIdentifier(
                        type=IdentifierType.PMC,
                        value=pmc,
                        confidence=0.8,
                        source_url=source_url,
                        extraction_method=ExtractionMethod.WEB_SCRAPING,
                    )
                )

        return identifiers

    def _validate_identifier_format(
        self, identifier_type: IdentifierType, value: str
    ) -> bool:
        """Basic format validation for identifiers."""
        if not value or not isinstance(value, str):
            return False

        value = value.strip()

        if identifier_type == IdentifierType.DOI:
            return bool(re.match(r"^10\.\d{4,}/[^\s]+$", value))
        elif identifier_type == IdentifierType.PMID:
            return bool(re.match(r"^\d{1,8}$", value) and not value.startswith("0"))
        elif identifier_type == IdentifierType.PMC:
            return bool(re.match(r"^PMC\d+$", value))

        return False


class PDFExtractor(IdentifierExtractorBase):
    """Extract identifiers from PDF documents using LLM analysis."""

    def __init__(self, timeout: int = 10, rate_limit: float = 2.0, max_pages: int = 3):
        """Initialize PDF extractor.

        Args:
            timeout: Request timeout in seconds
            rate_limit: Minimum time between requests in seconds
            max_pages: Maximum number of pages to extract from PDF
        """
        self.timeout = timeout
        self.rate_limit = rate_limit
        self.max_pages = max_pages
        self.last_request_time = 0.0

        # Headers for PDF requests
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Accept": "application/pdf,*/*",
        }

    def extract_from_url(self, url: str) -> List[AcademicIdentifier]:
        """Extract identifiers from a PDF URL using LLM analysis.

        Args:
            url: URL pointing to a PDF

        Returns:
            List of extracted identifiers
        """
        if not url or not isinstance(url, str):
            return []

        # Only process PDF URLs
        if not self.is_pdf_url(url):
            return []

        try:
            # Rate limiting
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            if time_since_last < self.rate_limit:
                time.sleep(self.rate_limit - time_since_last)

            # Download PDF
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            self.last_request_time = time.time()

            if response.status_code != 200:
                logger.warning(f"HTTP {response.status_code} for PDF {url}")
                return []

            # Extract text from PDF
            pdf_text = self._extract_pdf_text(response.content)
            if not pdf_text:
                logger.warning(f"No text extracted from PDF {url}")
                return []

            # Use LLM to extract identifiers
            identifiers = self._extract_with_llm(pdf_text, url)
            return identifiers

        except requests.RequestException as e:
            logger.warning(f"Failed to download PDF {url}: {e}")
            return []
        except Exception as e:
            logger.warning(f"PDF extraction failed for {url}: {e}")
            return []

    def is_pdf_url(self, url: str) -> bool:
        """Check if URL likely points to a PDF."""
        return url.lower().endswith(".pdf") or ".pdf?" in url.lower()

    def _extract_pdf_text(self, pdf_content: bytes) -> str:
        """Extract text from PDF bytes."""
        try:
            from pypdf import PdfReader
            from io import BytesIO

            reader = PdfReader(BytesIO(pdf_content))

            # Extract text from first few pages (title page + references likely)
            text_parts = []
            for i, page in enumerate(reader.pages[: self.max_pages]):
                text_parts.append(page.extract_text())

            return "\n".join(text_parts)

        except Exception as e:
            logger.warning(f"PDF text extraction failed: {e}")
            return ""

    def _extract_with_llm(
        self, pdf_text: str, source_url: str
    ) -> List[AcademicIdentifier]:
        """Extract identifiers from PDF text using LLM."""
        try:
            import litellm

            # Prepare prompt
            prompt = f"""
            Extract academic identifiers from this PDF text. Look for:
            - DOI (format: 10.xxxx/yyyy...)
            - PMID (PubMed ID: 1-8 digits, often labeled as "PMID:")
            - PMC ID (format: PMCxxxxxxx)

            Return only valid identifiers in JSON format:
            {{"doi": "10.xxxx/yyyy", "pmid": "12345678", "pmc": "PMC1234567"}}

            If an identifier type is not found, omit it from the response.

            PDF Text:
            {pdf_text[:4000]}  # Limit text to avoid token limits
            """

            # Call LLM
            response = litellm.completion(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0,
            )

            # Parse response
            content = response.choices[0].message.content
            identifiers_data = json.loads(content)

            # Convert to AcademicIdentifier objects
            identifiers = []
            for id_type_str, value in identifiers_data.items():
                if id_type_str == "doi":
                    identifier_type = IdentifierType.DOI
                elif id_type_str == "pmid":
                    identifier_type = IdentifierType.PMID
                elif id_type_str == "pmc":
                    identifier_type = IdentifierType.PMC
                else:
                    continue

                if self._validate_identifier_format(identifier_type, value):
                    identifiers.append(
                        AcademicIdentifier(
                            type=identifier_type,
                            value=value,
                            confidence=0.8,  # Good confidence for LLM extraction
                            source_url=source_url,
                            extraction_method=ExtractionMethod.API_LOOKUP,  # Using LLM API
                        )
                    )

            return identifiers

        except Exception as e:
            logger.warning(f"LLM extraction failed: {e}")
            return []

    def _validate_identifier_format(
        self, identifier_type: IdentifierType, value: str
    ) -> bool:
        """Basic format validation for identifiers."""
        if not value or not isinstance(value, str):
            return False

        value = value.strip()

        if identifier_type == IdentifierType.DOI:
            return bool(re.match(r"^10\.\d{4,}/[^\s]+$", value))
        elif identifier_type == IdentifierType.PMID:
            return bool(re.match(r"^\d{1,8}$", value) and not value.startswith("0"))
        elif identifier_type == IdentifierType.PMC:
            return bool(re.match(r"^PMC\d+$", value))

        return False
