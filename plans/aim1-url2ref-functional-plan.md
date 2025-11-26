# Aim 1 – url2ref functionality plan (standalone)

## Goal
Expand `url2ref` (lit_agent) so it can take a numbered bibliography (URLs) from upstream systems (e.g., DeepSearch) and return a citation map keyed by the original reference numbers. Each entry should be CSL-JSON–compatible, enriched with resolved identifiers and confidence/validation details.

## Chosen citation schema
- **CSL-JSON** as the citation payload: stable, widely supported, flexible for partial metadata.
- Fields we commit to populate when available: `id` (ref_id), `URL`, `type`, `title`, `author` (family/given), `issued` (`date-parts`), `container-title`, `publisher`, `page`, `volume`, `issue`, `DOI`, `PMID`, `PMCID`.
- Add a `resolution` object (custom) with: `confidence` (0–1), `methods` (ordered list of extraction methods), `validation` (e.g., `{"ncbi": "passed" | "failed" | "skipped", "metapub": ...}`), `errors` (optional list), and `source_url` for traceability.
- Numbering: preserve the **original ref number** (stringified) from the input order. Never renumber. If deduplication is applied, keep both the original `id` and a `canonical_id` for grouping.

## New/updated APIs
- High-level function: `resolve_bibliography(urls: list[str], *, validate=True, scrape=True, pdf=True, topic_validation=False) -> CitationResolutionResult`
  - Input: ordered list of URLs (implicitly numbered starting at 1).
  - Output: `CitationResolutionResult` with:
    - `citations: dict[str, CSLJSONCitation]` keyed by ref_id (`"1"`, `"2"`, ...).
    - `stats`: counts for resolved/unresolved, by method, average confidence, validation outcomes.
    - `failures`: list of ref_ids with reasons.
- Keep existing `extract_identifiers_from_bibliography` public but use it internally.

## Processing pipeline
1) **Identifier extraction (existing)**: reuse `JournalURLExtractor` → `CompositeValidator` (NCBI/metapub) with per-identifier confidence.
2) **Phase 2 (optional)**: web scraping/PDF extraction for failed URLs; track methods.
3) **Metadata enrichment**:
   - Primary: `NCBIAPIValidator.get_article_metadata` when PMID/PMCID present.
   - DOI metadata lookup (CrossRef or other) if available in codebase or add light DOI resolver (no network if policies forbid; allow graceful skip).
   - Map metadata to CSL-JSON fields; fill `issued` from year (or full date if present).
4) **Record assembly**:
   - For each URL (ref_id), create CSL-JSON object with `id = ref_id`, `URL = url`, identifiers (`DOI`, `PMID`, `PMCID`), and enriched metadata.
   - Attach `resolution` with method path and validation outcomes; if unresolved, include `errors` and leave identifiers blank.
5) **Stats/reporting**:
   - Aggregate success/failure, per-method success, confidence histograms, validation pass rates.
   - Optional: expose `to_json()` for container embedding.

## Edge cases & rules
- Preserve input order as authoritative numbering; never reshuffle.
- If multiple identifiers per URL, keep all (`DOI`, `PMID`, `PMCID`); prefer PMID/PMCID to fetch metadata, but do not drop DOI.
- If metadata fetch fails, still return identifiers and source URL with low confidence.
- If scraping/PDF disabled or not permitted, mark validation as `skipped` and return partial data.
- Keep network-dependent steps optional via flags; ensure graceful degradation without secrets.

## Testing
- Unit tests: fixture URLs → expected CSL-JSON snippets; confidence/method tracking; unresolved paths.
- Integration (if allowed): small curated URLs hitting NCBI (and DOI if available) with recorded responses; fallback to mocks when offline.
- Schema checks: validate produced citation map against CSL-JSON structure + custom `resolution` fragment.
