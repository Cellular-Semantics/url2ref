#!/usr/bin/env python3
"""Test citation formatting for different URL types."""

from lit_agent.identifiers.api import resolve_bibliography
from dotenv import load_dotenv

load_dotenv()

urls = [
    'https://www.nature.com/articles/s41467-025-67223-4_reference.pdf',
    'https://www.nature.com/articles/s41597-025-06145-8',
    'https://www.ncbi.nlm.nih.gov/gene/26291',
    'https://www.proteinatlas.org/ENSG00000137962-ARHGAP29/cancer/glioma',
]

print('Citation Formatting Analysis\n')
print('=' * 80)

result = resolve_bibliography(urls)

print(f'\n{len(result.citations)} citations resolved\n')

for source_id, citation in result.citations.items():
    url = citation.get('URL', 'N/A')
    doi = citation.get('DOI', 'N/A')
    pmid = citation.get('PMID', 'N/A')
    title = citation.get('title', 'N/A')
    has_metadata = title != 'N/A'

    print(f'[{source_id}] {url}')
    print(f'     DOI: {doi}, PMID: {pmid}')
    print(f'     Title: {title[:70] + "..." if has_metadata and len(title) > 70 else title}')
    print(f'     Has metadata: {has_metadata}')
    print()
