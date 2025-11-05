"""Identifier validation using format checking and API validation."""

import logging
import re
import time
from typing import Any, Dict, Optional

import requests  # type: ignore[import-untyped]

from .base import IdentifierType, IdentifierValidatorBase

logger = logging.getLogger(__name__)


class FormatValidator(IdentifierValidatorBase):
    """Validates identifiers based on format rules."""

    def __init__(self):
        """Initialize format patterns."""
        # PMID: 1-8 digits, no leading zeros
        self.pmid_pattern = re.compile(r"^\d{1,8}$")

        # PMC: PMC followed by digits
        self.pmc_pattern = re.compile(r"^PMC\d+$")

        # DOI: 10.{registrant}/{suffix}
        self.doi_pattern = re.compile(r"^10\.\d{4,}/[^\s]+$")

    def validate_identifier(self, identifier_type: IdentifierType, value: str) -> bool:
        """Validate identifier format.

        Args:
            identifier_type: Type of identifier
            value: Identifier value to validate

        Returns:
            True if format is valid, False otherwise
        """
        if not value or not isinstance(value, str):
            return False

        value = value.strip()

        if identifier_type == IdentifierType.PMID:
            return self._validate_pmid_format(value)
        elif identifier_type == IdentifierType.PMC:
            return self._validate_pmc_format(value)
        elif identifier_type == IdentifierType.DOI:
            return self._validate_doi_format(value)

        return False

    def _validate_pmid_format(self, pmid: str) -> bool:
        """Validate PMID format."""
        if not self.pmid_pattern.match(pmid):
            return False

        # Check for leading zeros (invalid)
        if len(pmid) > 1 and pmid.startswith("0"):
            return False

        # Check reasonable range (first PMID was 1)
        try:
            pmid_int = int(pmid)
            return 1 <= pmid_int <= 99999999  # Current max is around 39M
        except ValueError:
            return False

    def _validate_pmc_format(self, pmc: str) -> bool:
        """Validate PMC format."""
        if not self.pmc_pattern.match(pmc):
            return False

        # Extract numeric part and validate
        try:
            numeric_part = pmc[3:]  # Remove 'PMC'
            pmc_int = int(numeric_part)
            return 1 <= pmc_int <= 99999999  # Reasonable range
        except ValueError:
            return False

    def _validate_doi_format(self, doi: str) -> bool:
        """Validate DOI format."""
        if not self.doi_pattern.match(doi):
            return False

        # Additional checks
        parts = doi.split("/", 1)
        if len(parts) != 2:
            return False

        registrant, suffix = parts
        registrant_digits = registrant[3:]  # Remove '10.'

        # Registrant should be at least 4 digits
        if not registrant_digits.isdigit() or len(registrant_digits) < 4:
            return False

        # Suffix should not be empty and should contain valid characters
        if not suffix or len(suffix.strip()) == 0:
            return False

        return True


class NCBIAPIValidator(IdentifierValidatorBase):
    """Validates identifiers using NCBI API."""

    def __init__(
        self, timeout: int = 10, rate_limit: float = 0.5, email: Optional[str] = None
    ):
        """Initialize API validator.

        Args:
            timeout: Request timeout in seconds
            rate_limit: Minimum time between requests in seconds
            email: Email address for NCBI API (should be registered with NCBI)
        """
        self.timeout = timeout
        self.rate_limit = rate_limit
        self.last_request_time = 0.0

        # Use provided email or environment variable, with fallback
        # Note: For production use, email should be registered with NCBI
        from dotenv import load_dotenv
        import os

        load_dotenv()
        self.email = email or os.getenv("NCBI_EMAIL", "developer@localhost")

        # NCBI API URLs
        self.api_base_url = "https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/"
        self.efetch_base_url = (
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        )

        # Format validator for basic checks
        self.format_validator = FormatValidator()

    def validate_identifier(self, identifier_type: IdentifierType, value: str) -> bool:
        """Validate identifier using NCBI API.

        Args:
            identifier_type: Type of identifier
            value: Identifier value to validate

        Returns:
            True if valid according to API, False otherwise
        """
        # First check format
        if not self.format_validator.validate_identifier(identifier_type, value):
            return False

        try:
            result = self._query_ncbi_api(identifier_type, value)
            return result is not None
        except Exception as e:
            logger.warning(
                f"API validation failed for {identifier_type.value} {value}: {e}"
            )
            # Fall back to format validation
            return True  # Assume valid if API fails

    def get_confidence_score(
        self, identifier_type: IdentifierType, value: str
    ) -> float:
        """Get confidence score for identifier.

        Args:
            identifier_type: Type of identifier
            value: Identifier value

        Returns:
            Confidence score between 0.0 and 1.0
        """
        # Format validation
        if not self.format_validator.validate_identifier(identifier_type, value):
            return 0.0

        # Try API validation
        try:
            result = self._query_ncbi_api(identifier_type, value)
            if result:
                return 0.98  # High confidence for API-validated IDs
            else:
                return 0.2  # Low confidence if API says invalid
        except Exception:
            # If API fails, rely on format validation
            return 0.7  # Medium confidence for format-only validation

    def get_article_metadata(
        self, identifier_type: IdentifierType, value: str
    ) -> Optional[Dict[str, Any]]:
        """Fetch article metadata (title, abstract, authors) from NCBI.

        Args:
            identifier_type: Type of identifier (PMID, PMC, or DOI)
            value: Identifier value

        Returns:
            Dictionary with article metadata or None if not found
        """
        # First validate the identifier format
        if not self.format_validator.validate_identifier(identifier_type, value):
            return None

        try:
            # Convert identifier to PMID if needed (efetch works best with PMIDs)
            pmid = self._get_pmid_for_identifier(identifier_type, value)
            if not pmid:
                return None

            # Fetch article metadata using efetch
            return self._fetch_article_metadata(pmid)

        except Exception as e:
            logger.warning(
                f"Failed to fetch metadata for {identifier_type.value} {value}: {e}"
            )
            return None

    def _get_pmid_for_identifier(
        self, identifier_type: IdentifierType, value: str
    ) -> Optional[str]:
        """Get PMID for any identifier type using ID converter.

        Args:
            identifier_type: Type of identifier
            value: Identifier value

        Returns:
            PMID string or None if not found
        """
        if identifier_type == IdentifierType.PMID:
            return value

        # Use ID converter for PMC and DOI
        try:
            result = self._query_ncbi_api(identifier_type, value)
            if result and "pmid" in result:
                return result["pmid"]
            return None
        except Exception:
            return None

    def _fetch_article_metadata(self, pmid: str) -> Optional[Dict[str, Any]]:
        """Fetch article metadata using efetch API.

        Args:
            pmid: PubMed ID

        Returns:
            Dictionary with title, abstract, authors, etc.
        """
        # Rate limiting
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit:
            time.sleep(self.rate_limit - time_since_last)

        # Prepare efetch API request
        params = {
            "db": "pubmed",
            "id": pmid,
            "retmode": "xml",
            "rettype": "abstract",
            "tool": "lit-agent",
            "email": self.email,
        }

        try:
            response = requests.get(
                self.efetch_base_url, params=params, timeout=self.timeout
            )
            self.last_request_time = time.time()

            if response.status_code == 200:
                return self._parse_efetch_xml(response.text, pmid)
            else:
                logger.warning(
                    f"efetch API returned status {response.status_code} for PMID {pmid}"
                )
                return None

        except requests.RequestException as e:
            logger.warning(f"efetch API request failed for PMID {pmid}: {e}")
            return None

    def _parse_efetch_xml(
        self, xml_content: str, pmid: str
    ) -> Optional[Dict[str, Any]]:
        """Parse XML response from efetch to extract metadata.

        Args:
            xml_content: XML response from efetch
            pmid: PubMed ID for context

        Returns:
            Dictionary with parsed metadata
        """
        try:
            from xml.etree import ElementTree as ET

            root = ET.fromstring(xml_content)

            # Find the PubmedArticle element
            article = root.find(".//PubmedArticle")
            if article is None:
                return None

            metadata: Dict[str, Any] = {"pmid": pmid}

            # Extract title
            title_elem = article.find(".//ArticleTitle")
            if title_elem is not None:
                metadata["title"] = title_elem.text or ""

            # Extract abstract
            abstract_elem = article.find(".//AbstractText")
            if abstract_elem is not None:
                metadata["abstract"] = abstract_elem.text or ""

            # Extract authors
            authors = []
            for author in article.findall(".//Author"):
                last_name = author.find("LastName")
                fore_name = author.find("ForeName")
                if last_name is not None:
                    author_name = last_name.text or ""
                    if fore_name is not None and fore_name.text:
                        author_name = f"{fore_name.text} {author_name}"
                    authors.append(author_name)

            if authors:
                metadata["authors"] = authors

            # Extract journal information
            journal_elem = article.find(".//Journal/Title")
            if journal_elem is not None:
                metadata["journal"] = journal_elem.text or ""

            # Extract publication year
            year_elem = article.find(".//PubDate/Year")
            if year_elem is not None:
                metadata["year"] = year_elem.text or ""

            return metadata

        except ET.ParseError as e:
            logger.warning(f"Failed to parse XML for PMID {pmid}: {e}")
            return None
        except Exception as e:
            logger.warning(f"Unexpected error parsing metadata for PMID {pmid}: {e}")
            return None

    def _query_ncbi_api(
        self, identifier_type: IdentifierType, value: str
    ) -> Optional[Dict[str, Any]]:
        """Query NCBI ID Converter API.

        Args:
            identifier_type: Type of identifier
            value: Identifier value

        Returns:
            API response data or None if not found
        """
        # Rate limiting
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit:
            time.sleep(self.rate_limit - time_since_last)

        # Prepare API request
        params = {
            "tool": "lit-agent",
            "email": self.email,  # Required by NCBI
            "ids": value,
            "format": "json",
        }

        try:
            response = requests.get(
                self.api_base_url, params=params, timeout=self.timeout
            )
            self.last_request_time = time.time()

            if response.status_code == 200:
                data = response.json()
                # Check if the identifier was found
                if "records" in data and data["records"]:
                    return data["records"][0] if data["records"] else None
                return None
            else:
                logger.warning(f"NCBI API returned status {response.status_code}")
                return None

        except requests.RequestException as e:
            logger.warning(f"NCBI API request failed: {e}")
            raise


class MetapubValidator(IdentifierValidatorBase):
    """Validates identifiers using metapub library."""

    def __init__(self):
        """Initialize metapub validator."""
        self.format_validator = FormatValidator()

    def validate_identifier(self, identifier_type: IdentifierType, value: str) -> bool:
        """Validate identifier using metapub.

        Args:
            identifier_type: Type of identifier
            value: Identifier value to validate

        Returns:
            True if valid, False otherwise
        """
        # First check format
        if not self.format_validator.validate_identifier(identifier_type, value):
            return False

        try:
            import metapub  # type: ignore[import-untyped]

            if identifier_type == IdentifierType.PMID:
                # Try to fetch article by PMID
                article = metapub.PubMedFetcher().article_by_pmid(value)
                return article is not None

            elif identifier_type == IdentifierType.DOI:
                # Try to get PMID for DOI
                pmid = metapub.CrossRef().pmid_from_doi(value)
                return pmid is not None

            elif identifier_type == IdentifierType.PMC:
                # PMC validation through conversion
                pmc_fetcher = metapub.PubMedCentralFetcher()
                # Try to convert PMC to PMID
                pmid = pmc_fetcher.pmid_from_pmcid(value)
                return pmid is not None

        except ImportError:
            logger.warning("metapub not available, falling back to format validation")
            return True
        except Exception as e:
            logger.warning(
                f"metapub validation failed for {identifier_type.value} {value}: {e}"
            )
            return True  # Assume valid if validation fails

        return False

    def get_confidence_score(
        self, identifier_type: IdentifierType, value: str
    ) -> float:
        """Get confidence score using metapub validation."""
        if self.validate_identifier(identifier_type, value):
            return 0.95
        return 0.0


class CompositeValidator(IdentifierValidatorBase):
    """Composite validator that combines multiple validation methods."""

    def __init__(self, use_api: bool = True, use_metapub: bool = True):
        """Initialize composite validator.

        Args:
            use_api: Whether to use NCBI API validation
            use_metapub: Whether to use metapub validation
        """
        self.format_validator = FormatValidator()
        self.api_validator = NCBIAPIValidator() if use_api else None
        self.metapub_validator = MetapubValidator() if use_metapub else None

    def validate_identifier(self, identifier_type: IdentifierType, value: str) -> bool:
        """Validate using multiple methods.

        Args:
            identifier_type: Type of identifier
            value: Identifier value to validate

        Returns:
            True if valid according to any method, False otherwise
        """
        # Format validation (required)
        if not self.format_validator.validate_identifier(identifier_type, value):
            return False

        # Try additional validators
        validators = [
            v for v in [self.api_validator, self.metapub_validator] if v is not None
        ]

        if not validators:
            return True  # Only format validation available

        # If any validator confirms it's valid, consider it valid
        for validator in validators:
            try:
                if validator.validate_identifier(identifier_type, value):
                    return True
            except Exception as e:
                logger.warning(f"Validator {validator.__class__.__name__} failed: {e}")

        # If all validators fail but format is good, assume valid
        return True

    def get_confidence_score(
        self, identifier_type: IdentifierType, value: str
    ) -> float:
        """Get confidence score from multiple validators."""
        # Format validation
        if not self.format_validator.validate_identifier(identifier_type, value):
            return 0.0

        scores = []

        # Collect scores from available validators
        validators = [
            v for v in [self.api_validator, self.metapub_validator] if v is not None
        ]

        for validator in validators:
            try:
                score = validator.get_confidence_score(identifier_type, value)
                scores.append(score)
            except Exception as e:
                logger.warning(
                    f"Confidence scoring failed for {validator.__class__.__name__}: {e}"
                )

        if scores:
            # Return the maximum score (most optimistic)
            return max(scores)
        else:
            # Only format validation available
            return 0.7
