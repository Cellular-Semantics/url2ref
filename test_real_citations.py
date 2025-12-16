#!/usr/bin/env python3
"""Test script to analyze real citation URL processing."""

import json
from dotenv import load_dotenv
from lit_agent.identifiers.api import resolve_bibliography

# Load environment variables
load_dotenv()

# Real citation URLs from user
test_citations = [
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC6896086/",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC6609345/",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC5692520/",
    "https://www.nature.com/articles/s41420-024-01886-8",
    "https://www.spandidos-publications.com/10.3892/or.2019.7204/abstract",
    "https://www.proteinatlas.org/ENSG00000137962-ARHGAP29/cancer/glioma",
    "https://www.nature.com/articles/s41392-024-01868-3",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC9233184/",
    "https://www.nature.com/articles/s41420-021-00661-3",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC12063100/",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC8021872/",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC8147444/",
    "https://pubmed.ncbi.nlm.nih.gov/33807899/",
    "https://www.nature.com/articles/s41467-023-40212-1",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC5984695/",
    "https://www.nature.com/articles/s41420-023-01524-9",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC10854665/",
    "https://www.nature.com/articles/s41392-024-02121-7",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC11696323/",
    "https://www.nature.com/articles/s43018-021-00201-z",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC7601979/",
    "https://www.nature.com/articles/s41388-020-1308-2",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC9206138/",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC6013650/",
    "https://www.nature.com/articles/s41419-019-1505-5",
    "https://pubmed.ncbi.nlm.nih.gov/30720218/",
    "https://www.nature.com/articles/s41420-022-01018-0",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC4767244/",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC3586846/",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC12418754/",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC6888274/",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC11668713/",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC5091648/",
    "https://www.nature.com/articles/s41388-024-03228-5",
    "https://www.jci.org/articles/view/147552",
    "https://www.oncotarget.com/article/9744/text/",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC4424499/",
    "https://pubmed.ncbi.nlm.nih.gov/34399888/",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC5993506/",
    "https://www.tandfonline.com/doi/full/10.4161/cc.20309",
    "https://elifesciences.org/articles/64846",
    "https://www.frontiersin.org/journals/immunology/articles/10.3389/fimmu.2023.1202098/full",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC3124067/",
    "https://pubmed.ncbi.nlm.nih.gov/32965165/",
    "https://www.tandfonline.com/doi/full/10.1080/14728222.2025.2589807?src=",
    "https://iubmb.onlinelibrary.wiley.com/doi/full/10.1002/biof.2060",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC8177779/",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC5562912/",
    "https://www.nature.com/articles/s41598-021-00691-y",
    "https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0078728",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC8582528/",
    "https://pubmed.ncbi.nlm.nih.gov/24244348/",
    "https://febs.onlinelibrary.wiley.com/doi/10.1002/1878-0261.12196",
    "https://pubmed.ncbi.nlm.nih.gov/12763682/",
    "https://www.nature.com/articles/srep21710",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC3596950/",
    "https://ashpublications.org/blood/article/107/1/151/21731/The-pattern-recognition-receptor-PTX3-is-recruited",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC5355046/",
]

def analyze_citation_processing():
    """Process citations and analyze the results."""

    print("=" * 80)
    print("CITATION PROCESSING ANALYSIS")
    print("=" * 80)
    print(f"\nProcessing {len(test_citations)} citations...\n")

    results = {
        "successful": [],
        "failed": [],
        "partial": [],
        "issues": []
    }

    for i, url in enumerate(test_citations, 1):
        print(f"\n[{i}/{len(test_citations)}] Processing: {url}")
        print("-" * 80)

        try:
            # Resolve the citation
            result = resolve_bibliography([url])

            if result.citations:
                # Citations is a dict keyed by source_id (e.g., "1")
                citation = list(result.citations.values())[0]

                # Extract key info
                doi = citation.get("DOI", "N/A")
                pmid = citation.get("PMID", "N/A")
                pmc = citation.get("PMCID", "N/A")
                title = citation.get("title", "N/A")

                # Check for issues
                issues_found = []

                # Check for file extensions in DOI
                if doi != "N/A" and any(ext in doi for ext in [".pdf", ".html", "_reference"]):
                    issues_found.append(f"DOI contains file extension: {doi}")

                # Check if we got at least one identifier
                has_identifier = doi != "N/A" or pmid != "N/A" or pmc != "N/A"

                print(f"  DOI:   {doi}")
                print(f"  PMID:  {pmid}")
                print(f"  PMC:   {pmc}")
                print(f"  Title: {title[:80] + '...' if len(title) > 80 else title}")

                if issues_found:
                    print(f"  ⚠️  ISSUES: {', '.join(issues_found)}")
                    results["issues"].extend([(url, issue) for issue in issues_found])
                    results["partial"].append((url, citation))
                elif has_identifier:
                    print("  ✅ Success")
                    results["successful"].append((url, citation))
                else:
                    print("  ❌ No identifiers extracted")
                    results["failed"].append((url, citation))

            else:
                print("  ❌ No citation returned")
                results["failed"].append((url, None))

        except Exception as e:
            print(f"  ❌ Error: {e}")
            results["failed"].append((url, str(e)))

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total citations: {len(test_citations)}")
    print(f"✅ Successful:   {len(results['successful'])} ({len(results['successful'])/len(test_citations)*100:.1f}%)")
    print(f"⚠️  Partial:      {len(results['partial'])} ({len(results['partial'])/len(test_citations)*100:.1f}%)")
    print(f"❌ Failed:       {len(results['failed'])} ({len(results['failed'])/len(test_citations)*100:.1f}%)")

    if results["issues"]:
        print(f"\n⚠️  ISSUES FOUND ({len(results['issues'])}):")
        for url, issue in results["issues"]:
            print(f"  - {issue}")
            print(f"    URL: {url}")

    # Save detailed results to file
    output = {
        "summary": {
            "total": len(test_citations),
            "successful": len(results["successful"]),
            "partial": len(results["partial"]),
            "failed": len(results["failed"]),
            "issues": len(results["issues"])
        },
        "issues": [{"url": url, "issue": issue} for url, issue in results["issues"]],
        "failed_urls": [url for url, _ in results["failed"]]
    }

    with open("citation_analysis_results.json", "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n📝 Detailed results saved to: citation_analysis_results.json")
    print("=" * 80)

if __name__ == "__main__":
    analyze_citation_processing()