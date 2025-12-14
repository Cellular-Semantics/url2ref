"""High-level API functions for academic identifier extraction."""

from collections import Counter, defaultdict
from dataclasses import dataclass
import json
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional

from .base import IdentifierType, AcademicIdentifier, IdentifierExtractionResult
from .extractors import JournalURLExtractor
from .web_scrapers import WebScrapingExtractor, PDFExtractor
from .validators import CompositeValidator, NCBIAPIValidator
from .topic_validator import TopicValidator


@dataclass
class CitationResolutionResult:
    """Resolved bibliography output mapped to CSL-JSON entries."""

    citations: Dict[str, Dict[str, Any]]
    stats: Dict[str, Any]
    failures: List[str]

    def to_json(self) -> str:
        """Serialize the resolution result to JSON."""

        payload = {
            "citations": self.citations,
            "stats": self.stats,
            "failures": self.failures,
        }
        return json.dumps(payload, default=str)


def extract_identifiers_from_bibliography(
    urls: List[str],
    use_web_scraping: bool = False,
    use_api_validation: bool = True,
    use_metapub_validation: bool = True,
    use_topic_validation: bool = False,
    use_pdf_extraction: bool = True,
) -> IdentifierExtractionResult:
    """Extract academic identifiers from a list of bibliography URLs.

    This is the main entry point for identifier extraction from Deepsearch
    bibliography results.

    Args:
        urls: List of URLs to extract identifiers from
        use_web_scraping: Whether to use web scraping for failed extractions (Phase 2)
        use_api_validation: Whether to validate identifiers using NCBI API
        use_metapub_validation: Whether to validate identifiers using metapub
        use_topic_validation: Whether to validate topic relevance using LLM analysis
        use_pdf_extraction: Whether to allow PDF extraction in Phase 2

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

    # Phase 2 - Add web scraping for failed URLs
    if use_web_scraping and result.failed_urls:
        web_extractor = WebScrapingExtractor()
        pdf_extractor = PDFExtractor()

        # Track additional identifiers from Phase 2
        phase2_identifiers = []
        successful_urls = []  # Track URLs that succeeded in Phase 2

        # Create a copy of failed_urls to avoid modifying list while iterating
        for failed_url in result.failed_urls.copy():
            try:
                # Choose extractor based on URL type
                if pdf_extractor.is_pdf_url(failed_url):
                    if not use_pdf_extraction:
                        continue
                    identifiers = pdf_extractor.extract_from_url(failed_url)
                else:
                    identifiers = web_extractor.extract_from_url(failed_url)

                if identifiers:
                    phase2_identifiers.extend(identifiers)
                    successful_urls.append(failed_url)  # Track for removal later
                    # Update stats
                    result.extraction_stats["successful_extractions"] += 1
                    result.extraction_stats["failed_extractions"] -= 1
            except Exception:
                # Keep in failed URLs if Phase 2 also fails
                pass

        # Remove successful URLs from failed_urls after iteration completes
        for successful_url in successful_urls:
            if successful_url in result.failed_urls:
                result.failed_urls.remove(successful_url)

        # Add Phase 2 identifiers to result
        result.identifiers.extend(phase2_identifiers)

        # Update type counts
        for identifier in phase2_identifiers:
            if identifier.type == IdentifierType.DOI:
                result.extraction_stats["doi_count"] += 1
            elif identifier.type == IdentifierType.PMID:
                result.extraction_stats["pmid_count"] += 1
            elif identifier.type == IdentifierType.PMC:
                result.extraction_stats["pmc_count"] += 1

    # Phase 3 - Topic validation using LLM analysis
    if use_topic_validation and result.identifiers:
        metadata_validator = NCBIAPIValidator()
        topic_validator = TopicValidator()

        # Track topic validation statistics
        topic_validation_stats = {
            "total_validated": 0,
            "relevant_papers": 0,
            "irrelevant_papers": 0,
            "validation_errors": 0,
            "avg_confidence": 0.0,
        }

        confidence_scores = []

        for identifier in result.identifiers:
            try:
                # Get article metadata
                metadata = metadata_validator.get_article_metadata(
                    identifier.type, identifier.value
                )

                if metadata and ("title" in metadata or "abstract" in metadata):
                    title = metadata.get("title", "")
                    abstract = metadata.get("abstract", "")

                    # Validate topic relevance
                    topic_result = topic_validator.validate_topic_relevance(
                        title, abstract, metadata.get("pmid", "")
                    )

                    # Store topic validation results in identifier
                    identifier.topic_validation = {
                        "is_relevant": topic_result["is_relevant"],
                        "confidence": topic_result["confidence"],
                        "reasoning": topic_result["reasoning"],
                        "keywords_found": topic_result["keywords_found"],
                    }

                    # Update statistics
                    topic_validation_stats["total_validated"] += 1
                    confidence_scores.append(topic_result["confidence"])

                    if topic_result["is_relevant"]:
                        topic_validation_stats["relevant_papers"] += 1
                    else:
                        topic_validation_stats["irrelevant_papers"] += 1

                else:
                    # No metadata available for topic validation
                    identifier.topic_validation = {
                        "is_relevant": None,
                        "confidence": 0,
                        "reasoning": "No title or abstract available for topic validation",
                        "keywords_found": [],
                    }

            except Exception as e:
                topic_validation_stats["validation_errors"] += 1
                # Store error info
                identifier.topic_validation = {
                    "is_relevant": None,
                    "confidence": 0,
                    "reasoning": f"Topic validation failed: {str(e)}",
                    "keywords_found": [],
                }

        # Calculate average confidence
        if confidence_scores:
            topic_validation_stats["avg_confidence"] = sum(confidence_scores) / len(
                confidence_scores
            )

        # Add topic validation stats to result
        result.extraction_stats["topic_validation"] = topic_validation_stats

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


def resolve_bibliography(
    bibliography: Iterable[Any],
    *,
    validate: bool = True,
    scrape: bool = True,
    pdf: bool = True,
    topic_validation: bool = False,
    metadata_lookup: Optional[
        Callable[[IdentifierType, str], Optional[Dict[str, Any]]]
    ] = None,
) -> CitationResolutionResult:
    """Resolve a DeepSearch bibliography to CSL-JSON keyed by source_id.

    Args:
        bibliography: Iterable of URLs or mappings with ``source_id`` and ``url`` keys.
        validate: Whether to run API/metapub validation when extracting identifiers.
        scrape: Whether to enable web scraping for failed URLs.
        pdf: Whether to enable PDF extraction during scraping.
        topic_validation: Whether to run topic validation.
        metadata_lookup: Optional callable to enrich metadata (identifier_type, value) -> metadata dict.

    Returns:
        CitationResolutionResult with CSL-JSON citations keyed by source_id and resolution stats.
    """

    entries = _normalize_bibliography_entries(bibliography)
    urls = [entry["url"] for entry in entries]

    extraction_result = extract_identifiers_from_bibliography(
        urls,
        use_web_scraping=scrape,
        use_api_validation=validate,
        use_metapub_validation=validate,
        use_topic_validation=topic_validation,
        use_pdf_extraction=pdf,
    )

    grouped_identifiers: Dict[str, List[AcademicIdentifier]] = defaultdict(list)
    for identifier in extraction_result.identifiers:
        grouped_identifiers[identifier.source_url].append(identifier)

    citations: Dict[str, Dict[str, Any]] = {}
    failures: List[str] = []
    method_counter: Counter[str] = Counter()
    confidence_values: List[float] = []

    for entry in entries:
        source_id = entry["source_id"]
        url = entry["url"]
        identifiers = grouped_identifiers.get(url, [])

        citation = _build_csl_citation(
            source_id=source_id,
            url=url,
            identifiers=identifiers,
            metadata_lookup=metadata_lookup,
            validate=validate,
        )

        citations[source_id] = citation

        method_counter.update(citation["resolution"].get("methods", []))
        if identifiers:
            confidence_values.extend(
                [identifier.confidence for identifier in identifiers]
            )
        else:
            failures.append(source_id)

    stats = {
        "total": len(entries),
        "resolved": len(entries) - len(failures),
        "unresolved": len(failures),
        "methods": dict(method_counter),
        "average_confidence": (
            round(sum(confidence_values) / len(confidence_values), 2)
            if confidence_values
            else 0.0
        ),
    }

    return CitationResolutionResult(
        citations=citations,
        stats=stats,
        failures=failures,
    )


def _normalize_bibliography_entries(
    bibliography: Iterable[Any],
) -> List[Dict[str, str]]:
    """Normalize bibliography input to a list of ``{"source_id", "url"}`` dicts."""

    normalized_entries: List[Dict[str, str]] = []
    for index, entry in enumerate(bibliography, start=1):
        if isinstance(entry, Mapping):
            source_id = str(entry.get("source_id") or entry.get("id") or index)
            url = str(entry.get("url")) if entry.get("url") is not None else ""
        else:
            source_id = str(index)
            url = str(entry)

        normalized_entries.append({"source_id": source_id, "url": url})

    return normalized_entries


def _build_csl_citation(
    *,
    source_id: str,
    url: str,
    identifiers: List[AcademicIdentifier],
    metadata_lookup: Optional[
        Callable[[IdentifierType, str], Optional[Dict[str, Any]]]
    ],
    validate: bool,
) -> Dict[str, Any]:
    """Convert extracted identifiers into a CSL-JSON-like dict."""

    citation: Dict[str, Any] = {
        "id": source_id,
        "URL": url,
        "type": "article-journal",
        "resolution": {
            "confidence": max(
                (identifier.confidence for identifier in identifiers), default=0.0
            ),
            "methods": sorted(
                {identifier.extraction_method.value for identifier in identifiers}
            ),
            "validation": _build_validation_status(validate, bool(identifiers)),
            "errors": [],
            "source_url": url,
            "canonical_id": None,
        },
    }

    for identifier in identifiers:
        if identifier.type == IdentifierType.DOI:
            citation["DOI"] = identifier.value
        elif identifier.type == IdentifierType.PMID:
            citation["PMID"] = identifier.value
        elif identifier.type == IdentifierType.PMC:
            citation["PMCID"] = identifier.value

    if not identifiers:
        citation["resolution"]["errors"].append("no identifiers extracted")
        return citation

    preferred_identifier = _select_preferred_identifier(identifiers)

    metadata = None
    if metadata_lookup:
        try:
            metadata = metadata_lookup(
                preferred_identifier.type, preferred_identifier.value
            )
        except Exception as exc:  # pragma: no cover - defensive
            citation["resolution"]["errors"].append(f"metadata lookup failed: {exc}")
    elif validate:
        metadata_validator = NCBIAPIValidator()
        try:
            metadata = metadata_validator.get_article_metadata(
                preferred_identifier.type, preferred_identifier.value
            )
            citation["resolution"]["validation"]["ncbi"] = (
                "passed" if metadata else "failed"
            )
        except Exception as exc:  # pragma: no cover - defensive
            citation["resolution"]["errors"].append(f"metadata lookup failed: {exc}")
            citation["resolution"]["validation"]["ncbi"] = "failed"

    if metadata:
        _apply_metadata_to_citation(citation, metadata)
        if "metadata_lookup" not in citation["resolution"]["methods"]:
            citation["resolution"]["methods"].append("metadata_lookup")

    return citation


def _build_validation_status(validate: bool, has_identifiers: bool) -> Dict[str, str]:
    """Construct validation status map for ncbi/metapub."""

    if not validate:
        return {"ncbi": "skipped", "metapub": "skipped"}

    return {"ncbi": "unknown" if has_identifiers else "failed", "metapub": "unknown"}


def _select_preferred_identifier(
    identifiers: List[AcademicIdentifier],
) -> AcademicIdentifier:
    """Choose the best identifier for metadata lookup (PMID > PMC > DOI)."""

    priority = {IdentifierType.PMID: 0, IdentifierType.PMC: 1, IdentifierType.DOI: 2}
    return sorted(
        identifiers, key=lambda identifier: priority.get(identifier.type, 99)
    )[0]


def _apply_metadata_to_citation(
    citation: Dict[str, Any], metadata: Dict[str, Any]
) -> None:
    """Map metadata dictionary into CSL fields on the citation dict."""

    if title := metadata.get("title"):
        citation["title"] = title

    if journal := metadata.get("journal"):
        citation["container-title"] = journal

    if pubdate := metadata.get("pubdate"):
        date_parts = _parse_pubdate(pubdate)
        if date_parts:
            citation["issued"] = {"date-parts": [date_parts]}

    if authors := metadata.get("authors"):
        citation["author"] = _parse_authors(authors)

    for field in ["volume", "issue", "pages"]:
        if metadata.get(field):
            citation[field] = metadata[field]

    if metadata.get("doi"):
        citation.setdefault("DOI", metadata["doi"])
    if metadata.get("pmid"):
        citation.setdefault("PMID", metadata["pmid"])
    if metadata.get("pmcid"):
        citation.setdefault("PMCID", metadata["pmcid"])


def _parse_pubdate(pubdate: str) -> List[int]:
    """Parse NCBI-style pubdate strings into date-parts."""

    months = {
        "jan": 1,
        "feb": 2,
        "mar": 3,
        "apr": 4,
        "may": 5,
        "jun": 6,
        "jul": 7,
        "aug": 8,
        "sep": 9,
        "oct": 10,
        "nov": 11,
        "dec": 12,
    }

    tokens = pubdate.replace(",", " ").split()
    date_parts: List[int] = []

    for token in tokens:
        lower_token = token.lower()
        if lower_token in months:
            date_parts.append(months[lower_token])
        else:
            try:
                date_parts.append(int(token))
            except ValueError:
                continue

    if not date_parts and pubdate.isdigit():
        date_parts.append(int(pubdate))

    return date_parts[:3]


def _parse_authors(authors: Iterable[str]) -> List[Dict[str, str]]:
    """Convert a list of author strings into CSL author dicts."""

    parsed_authors: List[Dict[str, str]] = []

    for author in authors:
        if not author:
            continue

        tokens = author.replace(",", " ").split()
        if not tokens:
            continue

        family = tokens[0]
        given = " ".join(tokens[1:]) if len(tokens) > 1 else ""

        parsed_authors.append({"family": family, "given": given})

    return parsed_authors


def render_bibliography_to_strings(
    resolution_result: CitationResolutionResult,
    style: str = "vancouver",
    locale: str = "en-US",
) -> tuple[List[str], Dict[str, Any]]:
    """Render CSL-JSON citations to compact strings using citeproc if available.

    Falls back to a lightweight formatter when citeproc-py is not installed or fails.

    Args:
        resolution_result: Output of ``resolve_bibliography``.
        style: CSL style to use (e.g., ``vancouver``, ``ieee``, ``ama``).
        locale: Locale for the style (default: ``en-US``).

    Returns:
        Tuple of (rendered strings, metadata describing renderer and style).
    """

    try:
        (
            CitationStylesStyle,
            CitationStylesBibliography,
            Citation,
            CitationItem,
            formatter,
            CiteProcJSON,
        ) = _import_citeproc()
    except ImportError as exc:
        return _render_compact(resolution_result), {
            "renderer": "fallback",
            "style": style,
            "locale": locale,
            "error": str(exc),
        }

    try:
        entries = _prepare_citeproc_entries(resolution_result.citations.values())
        style_name = _resolve_csl_style(style)
        style_obj = CitationStylesStyle(style_name, validate=False, locale=locale)
        source = CiteProcJSON(entries)
        bibliography = CitationStylesBibliography(style_obj, source, formatter.plain)

        for item_id in source:
            citation = Citation([CitationItem(item_id)])
            bibliography.register(citation)

        rendered = [str(entry) for entry in bibliography.bibliography()]
        return rendered, {
            "renderer": "citeproc",
            "style": style,
            "locale": locale,
        }
    except Exception as exc:  # pragma: no cover - defensive
        return _render_compact(resolution_result), {
            "renderer": "fallback",
            "style": style,
            "locale": locale,
            "error": str(exc),
        }


def _render_compact(resolution_result: CitationResolutionResult) -> List[str]:
    """Minimal, dependency-free compact bibliography formatter."""

    rendered = []
    for citation in resolution_result.citations.values():
        parts = [f"[{citation.get('id', '?')}]"]

        authors = citation.get("author") or []
        if authors:
            first_author = authors[0]
            name = first_author.get("family") or first_author.get("literal") or ""
            if len(authors) > 1 and name:
                name = f"{name} et al."
            if name:
                parts.append(name)

        if citation.get("title"):
            parts.append(citation["title"])

        year = _extract_year(citation)
        if year:
            parts.append(str(year))

        id_field = citation.get("DOI") or citation.get("PMID") or citation.get("PMCID")
        if id_field:
            parts.append(id_field)
        elif citation.get("URL"):
            parts.append(citation["URL"])

        rendered.append(" ".join(parts))

    return rendered


def _extract_year(citation: Dict[str, Any]) -> Optional[int]:
    """Pull a year from a CSL citation if present."""

    issued = citation.get("issued", {})
    date_parts = issued.get("date-parts") if isinstance(issued, dict) else None
    if date_parts and isinstance(date_parts, list) and date_parts and date_parts[0]:
        try:
            return int(date_parts[0][0])
        except Exception:
            return None
    return None


def _prepare_citeproc_entries(
    citations: Iterable[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Normalize CSL entries to avoid citeproc parsing errors."""

    prepared: List[Dict[str, Any]] = []
    for index, citation in enumerate(citations, start=1):
        normalized = dict(citation)

        citation_id = normalized.get("id")
        normalized["id"] = (
            str(citation_id) if citation_id not in [None, ""] else str(index)
        )

        if not normalized.get("type"):
            normalized["type"] = "article-journal"

        # Remove internal fields citeproc does not understand
        normalized.pop("resolution", None)

        # Ensure author list exists
        if normalized.get("author") is None:
            normalized["author"] = []

        prepared.append(normalized)

    return prepared


def _resolve_csl_style(style: str) -> str:
    """Map friendly style aliases to canonical CSL identifiers."""

    aliases = {
        "chicago": "chicago-author-date",
    }
    normalized = style.lower()
    return aliases.get(normalized, normalized)


def _import_citeproc():
    """Import citeproc modules, isolated for easier testing."""

    import importlib

    citeproc = importlib.import_module("citeproc")
    citeproc_json = importlib.import_module("citeproc.source.json")

    return (
        citeproc.CitationStylesStyle,
        citeproc.CitationStylesBibliography,
        citeproc.Citation,
        citeproc.CitationItem,
        citeproc.formatter,
        citeproc_json.CiteProcJSON,
    )
