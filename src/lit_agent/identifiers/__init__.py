"""Academic identifier extraction module.

This module provides functionality to extract DOI, PMID, and PMC identifiers
from URLs found in academic bibliographies, particularly from Deepsearch results.
"""

# Core data structures and base classes
from .base import (
    AcademicIdentifier,
    IdentifierType,
    ExtractionMethod,
    IdentifierExtractionResult,
    IdentifierExtractorBase,
    IdentifierValidatorBase,
)

# Extractor implementations
from .extractors import URLPatternExtractor, JournalURLExtractor
from .web_scrapers import WebScrapingExtractor, PDFExtractor

# Validator implementations
from .validators import (
    CompositeValidator,
    FormatValidator,
    NCBIAPIValidator,
    MetapubValidator,
)
from .topic_validator import TopicValidator
from .reporting import ValidationReporter
from .visualizations import ValidationVisualizer

# High-level API functions
from .api import (
    extract_identifiers_from_bibliography,
    extract_identifiers_from_url,
    validate_identifier,
    resolve_bibliography,
    CitationResolutionResult,
)

# Demo functionality
from .demo import demo_extraction

__version__ = "0.1.0"
__all__ = [
    # Core types
    "AcademicIdentifier",
    "IdentifierType",
    "ExtractionMethod",
    "IdentifierExtractionResult",
    "IdentifierExtractorBase",
    "IdentifierValidatorBase",
    # Extractors
    "URLPatternExtractor",
    "JournalURLExtractor",
    "WebScrapingExtractor",
    "PDFExtractor",
    # Validators
    "CompositeValidator",
    "FormatValidator",
    "NCBIAPIValidator",
    "MetapubValidator",
    "TopicValidator",
    # Reporting
    "ValidationReporter",
    "ValidationVisualizer",
    # API functions
    "extract_identifiers_from_bibliography",
    "extract_identifiers_from_url",
    "validate_identifier",
    "resolve_bibliography",
    "CitationResolutionResult",
    # Demo
    "demo_extraction",
]
