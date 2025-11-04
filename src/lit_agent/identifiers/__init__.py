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

# Validator implementations
from .validators import (
    CompositeValidator,
    FormatValidator,
    NCBIAPIValidator,
    MetapubValidator,
)

# High-level API functions
from .api import (
    extract_identifiers_from_bibliography,
    extract_identifiers_from_url,
    validate_identifier,
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
    # Validators
    "CompositeValidator",
    "FormatValidator",
    "NCBIAPIValidator",
    "MetapubValidator",
    # API functions
    "extract_identifiers_from_bibliography",
    "extract_identifiers_from_url",
    "validate_identifier",
    # Demo
    "demo_extraction",
]
