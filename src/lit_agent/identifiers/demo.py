"""Demo functionality for academic identifier extraction."""

from typing import List, Optional

from .api import extract_identifiers_from_bibliography


def demo_extraction(sample_urls: Optional[List[str]] = None) -> None:
    """Demonstrate identifier extraction with sample URLs.

    Args:
        sample_urls: Optional list of URLs to test. Uses defaults if None.
    """
    if sample_urls is None:
        sample_urls = [
            "https://pubmed.ncbi.nlm.nih.gov/37674083/",
            "https://pmc.ncbi.nlm.nih.gov/articles/PMC11239014/",
            "https://www.science.org/doi/10.1126/science.abm5224",
            "https://www.nature.com/articles/s41586-023-06502-w",
            "https://doi.org/10.1038/ncomms3230",
        ]

    print("🧬 Academic Identifier Extraction Demo")
    print("=" * 50)

    result = extract_identifiers_from_bibliography(sample_urls)

    print("📊 Extraction Statistics:")
    print(f"   Total URLs processed: {result.extraction_stats['total_urls']}")
    print(
        f"   Successful extractions: {result.extraction_stats['successful_extractions']}"
    )
    print(f"   Failed extractions: {result.extraction_stats['failed_extractions']}")
    print(f"   Success rate: {result.success_rate:.2%}")
    print(f"   Processing time: {result.processing_time:.2f} seconds")
    print()

    print(f"🎯 Extracted Identifiers ({len(result.identifiers)} total):")
    for identifier in result.identifiers:
        confidence_emoji = (
            "🟢"
            if identifier.confidence >= 0.9
            else "🟡" if identifier.confidence >= 0.7 else "🔴"
        )
        print(
            f"   {confidence_emoji} {identifier.type.value.upper()}: {identifier.value}"
        )
        print(f"      Confidence: {identifier.confidence:.2f}")
        print(f"      Source: {identifier.source_url}")
        print()

    if result.failed_urls:
        print(f"❌ Failed URLs ({len(result.failed_urls)}):")
        for url in result.failed_urls:
            print(f"   • {url}")


if __name__ == "__main__":
    # Run demo when module is executed directly
    demo_extraction()
