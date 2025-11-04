"""URL pattern-based identifier extractors for academic references."""

import re
import urllib.parse
from typing import List, Optional
from urllib.parse import urlparse

from .base import (
    AcademicIdentifier,
    IdentifierType,
    ExtractionMethod,
    IdentifierExtractorBase,
)


class URLPatternExtractor(IdentifierExtractorBase):
    """Extracts academic identifiers from URLs using pattern matching."""

    def __init__(self):
        """Initialize the extractor with URL patterns."""
        # PMID patterns
        self.pmid_patterns = [
            # PubMed URLs
            r"pubmed\.ncbi\.nlm\.nih\.gov/(\d{1,8})/?",
            r"ncbi\.nlm\.nih\.gov/pubmed/(\d{1,8})/?",
            r"ncbi\.nlm\.nih\.gov/entrez/query\.fcgi\?.*pmid[=:](\d{1,8})",
            # Alternative formats
            r"pmid[:\s=](\d{1,8})",
        ]

        # PMC patterns
        self.pmc_patterns = [
            # PMC URLs
            r"pmc\.ncbi\.nlm\.nih\.gov/articles/(PMC\d+)/?",
            r"ncbi\.nlm\.nih\.gov/pmc/articles/(PMC\d+)/?",
            # PMC in text
            r"pmc[:\s=](PMC\d+)",
        ]

        # DOI patterns
        self.doi_patterns = [
            # Standard DOI format in URLs
            r'doi\.org/(10\.\d+/[^\s\'"<>]+)',
            r'/doi/(10\.\d+/[^\s\'"<>]+)',
            # DOI in journal URLs
            r'10\.\d+/[^\s\'"<>/?]+',
            # DOI with prefix
            r'doi[:\s=](10\.\d+/[^\s\'"<>]+)',
        ]

        # Compile all patterns for efficiency
        self.compiled_pmid_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.pmid_patterns
        ]
        self.compiled_pmc_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.pmc_patterns
        ]
        self.compiled_doi_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.doi_patterns
        ]

    def extract_from_url(self, url: str) -> List[AcademicIdentifier]:
        """Extract identifiers from a single URL.

        Args:
            url: URL to extract identifiers from

        Returns:
            List of extracted identifiers
        """
        if not url or not isinstance(url, str):
            return []

        # URL decode to handle encoded characters
        decoded_url = urllib.parse.unquote(url)

        identifiers = []

        # Extract PMID
        pmid = self._extract_pmid(decoded_url)
        if pmid:
            identifiers.append(
                AcademicIdentifier(
                    type=IdentifierType.PMID,
                    value=pmid,
                    confidence=0.95,  # High confidence for direct URL patterns
                    source_url=url,
                    extraction_method=ExtractionMethod.URL_PATTERN,
                )
            )

        # Extract PMC
        pmc = self._extract_pmc(decoded_url)
        if pmc:
            identifiers.append(
                AcademicIdentifier(
                    type=IdentifierType.PMC,
                    value=pmc,
                    confidence=0.95,
                    source_url=url,
                    extraction_method=ExtractionMethod.URL_PATTERN,
                )
            )

        # Extract DOI
        doi = self._extract_doi(decoded_url)
        if doi:
            identifiers.append(
                AcademicIdentifier(
                    type=IdentifierType.DOI,
                    value=doi,
                    confidence=self._calculate_doi_confidence(doi, decoded_url),
                    source_url=url,
                    extraction_method=ExtractionMethod.URL_PATTERN,
                )
            )

        return identifiers

    def _extract_pmid(self, url: str) -> Optional[str]:
        """Extract PMID from URL."""
        for pattern in self.compiled_pmid_patterns:
            match = pattern.search(url)
            if match:
                pmid = match.group(1)
                # Validate PMID format (1-8 digits)
                if pmid.isdigit() and 1 <= len(pmid) <= 8:
                    return pmid
        return None

    def _extract_pmc(self, url: str) -> Optional[str]:
        """Extract PMC ID from URL."""
        for pattern in self.compiled_pmc_patterns:
            match = pattern.search(url)
            if match:
                pmc = match.group(1)
                # Validate PMC format (PMC followed by digits)
                if re.match(r"^PMC\d+$", pmc):
                    return pmc
        return None

    def _extract_doi(self, url: str) -> Optional[str]:
        """Extract DOI from URL."""
        for pattern in self.compiled_doi_patterns:
            match = pattern.search(url)
            if match:
                if len(match.groups()) > 0:
                    doi = match.group(1)
                else:
                    doi = match.group(0)

                # Clean DOI (remove trailing punctuation, etc.)
                doi = self._clean_doi(doi)

                # Validate DOI format
                if self._is_valid_doi_format(doi):
                    return doi
        return None

    def _clean_doi(self, doi: str) -> str:
        """Clean extracted DOI string."""
        # Remove common trailing characters that aren't part of DOI
        doi = re.sub(r'[.,;)\]}>"\'\s]+$', "", doi)
        # Remove leading characters that aren't part of DOI
        doi = re.sub(r"^[^\d]+", "", doi)
        # Ensure it starts with 10.
        if not doi.startswith("10."):
            if "10." in doi:
                doi = "10." + doi.split("10.", 1)[1]
            else:
                return doi
        return doi

    def _is_valid_doi_format(self, doi: str) -> bool:
        """Validate DOI format."""
        # Basic DOI format: 10.{registrant}/{suffix}
        doi_pattern = r"^10\.\d{4,}/[^\s]+$"
        return bool(re.match(doi_pattern, doi))

    def _calculate_doi_confidence(self, doi: str, url: str) -> float:
        """Calculate confidence score for extracted DOI."""
        confidence = 0.8  # Base confidence for DOI pattern matching

        # Higher confidence if from known DOI domains
        doi_domains = ["doi.org", "dx.doi.org"]
        parsed_url = urlparse(url)
        if any(domain in parsed_url.netloc for domain in doi_domains):
            confidence = 0.98

        # Higher confidence if DOI appears in a structured path
        if "/doi/" in url.lower():
            confidence = min(confidence + 0.1, 0.98)

        # Lower confidence if DOI is very short (might be incomplete)
        if len(doi) < 10:
            confidence *= 0.8

        return round(confidence, 2)


class JournalURLExtractor(URLPatternExtractor):
    """Specialized extractor for journal-specific URL patterns."""

    def __init__(self):
        """Initialize with journal-specific patterns."""
        super().__init__()

        # Journal-specific DOI extraction patterns
        self.journal_patterns = {
            "nature.com": r"nature\.com/articles/([^/?]+)",
            "science.org": r"science\.org/doi/(?:abs/|full/)?(10\.\d+/[^/?]+)",
            "wiley.com": r"onlinelibrary\.wiley\.com/doi/(?:abs/|full/)?(10\.\d+/[^/?]+)",
            "springer.com": r"link\.springer\.com/(?:article/)?(?:10\.\d+/)?([^/?]+)",
            "elsevier.com": r"sciencedirect\.com/science/article/[^/]+/([^/?]+)",
            "pnas.org": r"pnas\.org/doi/(?:abs/|full/)?(10\.\d+/[^/?]+)",
            "cell.com": r"cell\.com/[^/]+/(?:fulltext/)?([^/?]+)",
        }

        # Compile journal patterns
        self.compiled_journal_patterns = {
            domain: re.compile(pattern, re.IGNORECASE)
            for domain, pattern in self.journal_patterns.items()
        }

    def extract_from_url(self, url: str) -> List[AcademicIdentifier]:
        """Extract identifiers using both general and journal-specific patterns."""
        identifiers = super().extract_from_url(url)

        # Try journal-specific patterns if no DOI found yet
        has_doi = any(id.type == IdentifierType.DOI for id in identifiers)
        if not has_doi:
            journal_doi = self._extract_journal_doi(url)
            if journal_doi:
                identifiers.append(
                    AcademicIdentifier(
                        type=IdentifierType.DOI,
                        value=journal_doi,
                        confidence=0.85,  # Slightly lower confidence for journal-specific patterns
                        source_url=url,
                        extraction_method=ExtractionMethod.URL_PATTERN,
                    )
                )

        return identifiers

    def _extract_journal_doi(self, url: str) -> Optional[str]:
        """Extract DOI using journal-specific patterns."""
        parsed_url = urlparse(url)

        for domain, pattern in self.compiled_journal_patterns.items():
            if domain in parsed_url.netloc:
                match = pattern.search(url)
                if match:
                    potential_doi = match.group(1)

                    # If it looks like a DOI, return it
                    if self._is_valid_doi_format(potential_doi):
                        return potential_doi

                    # For some journals, we need to construct the DOI
                    if domain == "nature.com":
                        return f"10.1038/{potential_doi}"

        return None
