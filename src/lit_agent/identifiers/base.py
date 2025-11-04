"""Base classes and data structures for academic identifier extraction."""

from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Any, Optional
import time


class IdentifierType(Enum):
    """Supported academic identifier types."""

    DOI = "doi"
    PMID = "pmid"
    PMC = "pmc"


class ExtractionMethod(Enum):
    """Methods used to extract identifiers."""

    URL_PATTERN = "url_pattern"
    API_LOOKUP = "api_lookup"
    WEB_SCRAPING = "web_scraping"
    METADATA_PARSING = "metadata_parsing"


@dataclass
class AcademicIdentifier:
    """Represents an extracted academic identifier."""

    type: IdentifierType
    value: str
    confidence: float  # 0.0 to 1.0
    source_url: str
    extraction_method: ExtractionMethod
    timestamp: Optional[float] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()

    @property
    def is_high_confidence(self) -> bool:
        """Check if identifier has high confidence (>= 0.8)."""
        return self.confidence >= 0.8

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "type": self.type.value,
            "value": self.value,
            "confidence": self.confidence,
            "source_url": self.source_url,
            "extraction_method": self.extraction_method.value,
            "timestamp": self.timestamp,
        }


@dataclass
class IdentifierExtractionResult:
    """Result of identifier extraction from multiple URLs."""

    identifiers: List[AcademicIdentifier]
    failed_urls: List[str]
    extraction_stats: Dict[str, int]
    processing_time: float = 0.0

    @property
    def success_rate(self) -> float:
        """Calculate success rate of extraction."""
        total_urls = len(self.identifiers) + len(self.failed_urls)
        if total_urls == 0:
            return 0.0
        return len(self.identifiers) / total_urls

    @property
    def high_confidence_count(self) -> int:
        """Count of high confidence identifiers."""
        return len([id for id in self.identifiers if id.is_high_confidence])

    def get_identifiers_by_type(
        self, identifier_type: IdentifierType
    ) -> List[AcademicIdentifier]:
        """Get identifiers of a specific type."""
        return [id for id in self.identifiers if id.type == identifier_type]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "identifiers": [id.to_dict() for id in self.identifiers],
            "failed_urls": self.failed_urls,
            "extraction_stats": self.extraction_stats,
            "processing_time": self.processing_time,
            "success_rate": self.success_rate,
            "high_confidence_count": self.high_confidence_count,
        }


class IdentifierExtractorBase:
    """Abstract base class for identifier extractors."""

    def extract_from_url(self, url: str) -> List[AcademicIdentifier]:
        """Extract identifiers from a single URL.

        Args:
            url: URL to extract identifiers from

        Returns:
            List of extracted identifiers
        """
        raise NotImplementedError

    def extract_from_urls(self, urls: List[str]) -> IdentifierExtractionResult:
        """Extract identifiers from multiple URLs.

        Args:
            urls: List of URLs to process

        Returns:
            Extraction result with all identifiers and statistics
        """
        start_time = time.time()
        identifiers = []
        failed_urls = []
        stats = {
            "total_urls": len(urls),
            "successful_extractions": 0,
            "failed_extractions": 0,
            "doi_count": 0,
            "pmid_count": 0,
            "pmc_count": 0,
        }

        for url in urls:
            try:
                extracted = self.extract_from_url(url)
                if extracted:
                    identifiers.extend(extracted)
                    stats["successful_extractions"] += 1

                    # Count by type
                    for identifier in extracted:
                        if identifier.type == IdentifierType.DOI:
                            stats["doi_count"] += 1
                        elif identifier.type == IdentifierType.PMID:
                            stats["pmid_count"] += 1
                        elif identifier.type == IdentifierType.PMC:
                            stats["pmc_count"] += 1
                else:
                    failed_urls.append(url)
                    stats["failed_extractions"] += 1
            except Exception:
                failed_urls.append(url)
                stats["failed_extractions"] += 1

        processing_time = time.time() - start_time

        return IdentifierExtractionResult(
            identifiers=identifiers,
            failed_urls=failed_urls,
            extraction_stats=stats,
            processing_time=processing_time,
        )


class IdentifierValidatorBase:
    """Abstract base class for identifier validators."""

    def validate_identifier(self, identifier_type: IdentifierType, value: str) -> bool:
        """Validate an identifier.

        Args:
            identifier_type: Type of identifier to validate
            value: Identifier value to validate

        Returns:
            True if valid, False otherwise
        """
        raise NotImplementedError

    def get_confidence_score(
        self, identifier_type: IdentifierType, value: str
    ) -> float:
        """Get confidence score for an identifier.

        Args:
            identifier_type: Type of identifier
            value: Identifier value

        Returns:
            Confidence score between 0.0 and 1.0
        """
        if self.validate_identifier(identifier_type, value):
            return 1.0
        return 0.0
