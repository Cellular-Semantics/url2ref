"""High-level API functions for academic identifier extraction."""

from typing import List, Dict, Any

from .base import IdentifierType, AcademicIdentifier, IdentifierExtractionResult
from .extractors import JournalURLExtractor
from .validators import CompositeValidator


def extract_identifiers_from_bibliography(
    urls: List[str],
    use_web_scraping: bool = False,
    use_api_validation: bool = True,
    use_metapub_validation: bool = True,
) -> IdentifierExtractionResult:
    """Extract academic identifiers from a list of bibliography URLs.

    This is the main entry point for identifier extraction from Deepsearch
    bibliography results.

    Args:
        urls: List of URLs to extract identifiers from
        use_web_scraping: Whether to use web scraping for failed extractions (Phase 2)
        use_api_validation: Whether to validate identifiers using NCBI API
        use_metapub_validation: Whether to validate identifiers using metapub

    Returns:
        IdentifierExtractionResult containing all extracted identifiers and statistics

    Example:
        >>> from lit_agent.identifiers import extract_identifiers_from_bibliography
        >>> urls = [
        ...     "https://pubmed.ncbi.nlm.nih.gov/37674083/",
        ...     "https://pmc.ncbi.nlm.nih.gov/articles/PMC11239014/",
        ...     "https://www.science.org/doi/10.1126/science.abm5224"
        ... ]
        >>> result = extract_identifiers_from_bibliography(urls)
        >>> print(f"Extracted {len(result.identifiers)} identifiers")
        >>> print(f"Success rate: {result.success_rate:.2%}")
    """
    # Use journal-aware extractor for better DOI extraction
    extractor = JournalURLExtractor()

    # Extract identifiers from URLs
    result = extractor.extract_from_urls(urls)

    # Validate extracted identifiers if requested
    if use_api_validation or use_metapub_validation:
        validator = CompositeValidator(
            use_api=use_api_validation, use_metapub=use_metapub_validation
        )

        # Update confidence scores based on validation
        for identifier in result.identifiers:
            confidence = validator.get_confidence_score(
                identifier.type, identifier.value
            )
            # Use the higher of the extraction confidence or validation confidence
            identifier.confidence = max(identifier.confidence, confidence)

    # TODO: Phase 2 - Add web scraping for failed URLs
    if use_web_scraping and result.failed_urls:
        # Placeholder for Phase 2 implementation
        pass

    return result


def extract_identifiers_from_url(
    url: str, use_api_validation: bool = False, use_metapub_validation: bool = False
) -> List[AcademicIdentifier]:
    """Extract academic identifiers from a single URL.

    Args:
        url: URL to extract identifiers from
        use_api_validation: Whether to validate using NCBI API
        use_metapub_validation: Whether to validate using metapub

    Returns:
        List of extracted AcademicIdentifier objects

    Example:
        >>> from lit_agent.identifiers import extract_identifiers_from_url
        >>> url = "https://pubmed.ncbi.nlm.nih.gov/37674083/"
        >>> identifiers = extract_identifiers_from_url(url)
        >>> if identifiers:
        ...     print(f"Found {identifiers[0].type.value}: {identifiers[0].value}")
    """
    extractor = JournalURLExtractor()
    identifiers = extractor.extract_from_url(url)

    # Validate if requested
    if (use_api_validation or use_metapub_validation) and identifiers:
        validator = CompositeValidator(
            use_api=use_api_validation, use_metapub=use_metapub_validation
        )

        for identifier in identifiers:
            confidence = validator.get_confidence_score(
                identifier.type, identifier.value
            )
            identifier.confidence = max(identifier.confidence, confidence)

    return identifiers


def validate_identifier(
    identifier_type: IdentifierType,
    value: str,
    use_api: bool = True,
    use_metapub: bool = True,
) -> Dict[str, Any]:
    """Validate a single academic identifier.

    Args:
        identifier_type: Type of identifier (DOI, PMID, PMC)
        value: Identifier value to validate
        use_api: Whether to use NCBI API validation
        use_metapub: Whether to use metapub validation

    Returns:
        Dictionary with validation results including confidence score

    Example:
        >>> from lit_agent.identifiers import validate_identifier, IdentifierType
        >>> result = validate_identifier(IdentifierType.PMID, "37674083")
        >>> print(f"Valid: {result['valid']}, Confidence: {result['confidence']}")
    """
    validator = CompositeValidator(use_api=use_api, use_metapub=use_metapub)

    is_valid = validator.validate_identifier(identifier_type, value)
    confidence = validator.get_confidence_score(identifier_type, value)

    return {
        "valid": is_valid,
        "confidence": confidence,
        "identifier_type": identifier_type.value,
        "value": value,
    }
