#!/usr/bin/env python3
"""Test problematic URLs from original error messages."""

from lit_agent.identifiers.api import resolve_bibliography
from dotenv import load_dotenv

load_dotenv()

# URLs from user's original error messages
problematic_urls = [
    'https://www.nature.com/articles/s41467-025-67223-4_reference.pdf',
    'https://www.nature.com/articles/s41597-025-06145-8',
    'https://www.nature.com/articles/s41467-025-65309-7',
    'https://www.nature.com/articles/s41392-025-02486-3',
    'https://www.nature.com/articles/s41467-025-66245-2',
    'https://www.ncbi.nlm.nih.gov/gene/26291',
    'https://www.ncbi.nlm.nih.gov/gene/6285',
    'https://www.ncbi.nlm.nih.gov/gene/80212',
    'https://www.nature.com/articles/s41467-025-66109-9_reference.pdf',
]

print('Testing problematic URLs from original error messages\n')
print('=' * 80)

issues_found = []

for url in problematic_urls:
    print(f'\nURL: {url}')
    result = resolve_bibliography([url])
    if result.citations:
        cit = list(result.citations.values())[0]
        doi = cit.get('DOI', 'N/A')
        pmid = cit.get('PMID', 'N/A')
        pmc = cit.get('PMCID', 'N/A')
        title = cit.get('title', 'N/A')
        if title != 'N/A' and len(title) > 60:
            title = title[:60] + '...'

        print(f'  DOI:   {doi}')
        print(f'  PMID:  {pmid}')
        print(f'  PMC:   {pmc}')
        print(f'  Title: {title}')

        # Check for issues
        if doi != 'N/A' and any(ext in doi for ext in ['.pdf', '.html', '_reference']):
            print(f'  ⚠️  ISSUE: DOI contains file extension!')
            issues_found.append((url, doi))
    else:
        print('  ❌ No identifiers extracted')

print('\n' + '=' * 80)
print(f'\nSUMMARY:')
print(f'Total URLs tested: {len(problematic_urls)}')
print(f'Issues found: {len(issues_found)}')

if issues_found:
    print(f'\nPROBLEMS DETECTED:')
    for url, doi in issues_found:
        print(f'  URL:  {url}')
        print(f'  DOI:  {doi}')
        print()
