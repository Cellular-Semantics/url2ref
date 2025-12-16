# Targeted Implementation Plan - Citation Processing Fixes

## Executive Summary

Based on empirical testing of 67 real-world URLs:
- **System Success Rate**: 98.3% on standard URLs
- **Critical Issue Identified**: DOI extraction includes file extensions (`_reference.pdf`)
- **Impact**: Causes cascading failures (no metadata, validation errors, formatting inconsistency)
- **Fix Scope**: Single method modification + comprehensive tests

---

## Issue #1: File Extensions in DOIs (HIGH PRIORITY)

### Problem

**URLs like**:
- `https://www.nature.com/articles/s41467-025-67223-4_reference.pdf`

**Extract DOI as**:
- `10.1038/s41467-025-67223-4_reference.pdf` ❌

**Should extract**:
- `10.1038/s41467-025-67223-4` ✅

### Impact Analysis

This single bug causes THREE reported issues:

1. **Malformed DOIs**: CrossRef API rejects with 404
2. **Validation Warnings**: Log spam from metapub validation failures
3. **Formatting Inconsistency**: No metadata → bare URL rendering instead of formatted citation

### Implementation (TDD)

#### Step 1: Write Failing Tests ✍️ (RED)

**File**: `tests/unit/test_identifiers.py`

**Add test method**:
```python
def test_extract_doi_from_nature_urls_with_file_extensions(self):
    """Test that file extensions are stripped from Nature article IDs."""
    extractor = JournalURLExtractor()

    test_cases = [
        # (input_url, expected_doi)
        ("https://www.nature.com/articles/s41467-025-67223-4_reference.pdf",
         "10.1038/s41467-025-67223-4"),
        ("https://www.nature.com/articles/s41467-025-66109-9_reference.pdf",
         "10.1038/s41467-025-66109-9"),
        ("https://www.nature.com/articles/s41586-023-06502-w.pdf",
         "10.1038/s41586-023-06502-w"),
        ("https://www.nature.com/articles/s41586-023-06502-w.html",
         "10.1038/s41586-023-06502-w"),
        # Ensure we don't break existing functionality
        ("https://www.nature.com/articles/s41586-023-06502-w",
         "10.1038/s41586-023-06502-w"),
    ]

    for url, expected_doi in test_cases:
        identifiers = extractor.extract_from_url(url)

        # Should extract exactly one DOI
        doi_identifiers = [id for id in identifiers if id.type == IdentifierType.DOI]
        assert len(doi_identifiers) == 1, f"Expected 1 DOI for {url}, got {len(doi_identifiers)}"

        # Check DOI value
        actual_doi = doi_identifiers[0].value
        assert actual_doi == expected_doi, f"URL: {url}\nExpected: {expected_doi}\nGot: {actual_doi}"
```

**Run tests** (should fail):
```bash
uv run pytest tests/unit/test_identifiers.py::TestIdentifierExtraction::test_extract_doi_from_nature_urls_with_file_extensions -v
```

**Commit failing tests**:
```bash
git add tests/unit/test_identifiers.py
git commit -m "test: add failing tests for Nature URL file extension stripping

Tests verify that DOI extraction strips file extensions like:
- _reference.pdf
- .pdf
- .html

Expected to fail until extractor is fixed."
```

---

#### Step 2: Implement Fix 🔧 (GREEN)

**File**: `src/lit_agent/identifiers/extractors.py`

**Location**: Lines 246-264 in `_extract_journal_doi()` method

**Add helper method** (after `_is_valid_doi_format`, around line 179):
```python
def _strip_file_extensions(self, article_id: str) -> str:
    """Remove common file extensions from article IDs.

    Args:
        article_id: Article identifier that may include file extensions

    Returns:
        Article ID with file extensions removed

    Examples:
        >>> self._strip_file_extensions("s41467-025-67223-4_reference.pdf")
        "s41467-025-67223-4"
        >>> self._strip_file_extensions("s41586-023-06502-w.html")
        "s41586-023-06502-w"
        >>> self._strip_file_extensions("s41586-023-06502-w")
        "s41586-023-06502-w"
    """
    # Common file extensions found in journal URLs
    # Order matters: strip longer patterns first
    extensions = [
        '_reference.pdf',
        '_reference.html',
        '_reference.htm',
        '.pdf',
        '.html',
        '.htm',
    ]

    for ext in extensions:
        if article_id.endswith(ext):
            article_id = article_id[:-len(ext)]
            break  # Only strip one extension

    return article_id
```

**Modify `_extract_journal_doi()` method** (line 260-262):
```python
# For some journals, we need to construct the DOI
if domain == "nature.com":
    # Strip file extensions before constructing DOI
    article_id = self._strip_file_extensions(potential_doi)
    return f"10.1038/{article_id}"
```

**Run tests** (should pass):
```bash
uv run pytest tests/unit/test_identifiers.py::TestIdentifierExtraction::test_extract_doi_from_nature_urls_with_file_extensions -v
```

**Run full test suite** (ensure no regressions):
```bash
uv run pytest tests/unit/test_identifiers.py -v
```

**Commit fix**:
```bash
git add src/lit_agent/identifiers/extractors.py
git commit -m "fix: strip file extensions from Nature article IDs before DOI construction

Fixes issue where URLs like:
  https://www.nature.com/articles/s41467-025-67223-4_reference.pdf

Were extracting DOI as:
  10.1038/s41467-025-67223-4_reference.pdf (invalid)

Now correctly extract:
  10.1038/s41467-025-67223-4

This fix also resolves cascading issues:
- CrossRef API 404 errors on malformed DOIs
- metapub validation warnings
- Missing metadata due to failed API lookups
- Inconsistent citation formatting

See: extractors.py:_strip_file_extensions() and _extract_journal_doi()"
```

---

#### Step 3: Verify Cascading Fixes ✅

**Re-run empirical tests**:
```bash
uv run python test_problematic_urls.py
```

**Expected results**:
- ✅ No DOIs with file extensions
- ✅ No metapub validation warnings for malformed DOIs
- ✅ Metadata successfully retrieved for all valid Nature URLs
- ✅ Consistent citation formatting

**Success criteria**:
- All 9 problematic URLs process correctly
- Issues found: 0

---

## Issue #2 & #3: Validation Warnings & Formatting (AUTO-RESOLVED)

These are **secondary effects** of Issue #1. Once file extensions are stripped:

- **Issue #2 (metapub warnings)**: Validation succeeds because DOIs are valid
- **Issue #3 (formatting inconsistency)**: Metadata lookups succeed, consistent formatting

**Verification**: Re-run empirical tests after fixing Issue #1.

**No additional code changes needed**.

---

## Issue #4: Non-Journal URL Handling (USER DECISION REQUIRED)

### Current Behavior

**NCBI Gene URLs**:
- Input: `https://www.ncbi.nlm.nih.gov/gene/26291`
- Current: Extracts PMID from linked paper
- Question: Is this desired behavior?

**Protein Atlas URLs**:
- Input: `https://www.proteinatlas.org/ENSG00000137962-ARHGAP29/cancer/glioma`
- Current: No identifiers extracted (correct)

### Options

**Option A: Keep Current Behavior**
- Gene URLs extract PMID from related papers
- Database URLs remain as plain URLs
- **Effort**: None
- **Pros**: Provides some academic context
- **Cons**: PMID may not represent the gene itself

**Option B: Extract Gene IDs**
- Add new identifier type: `IdentifierType.GENE_ID`
- Extract gene IDs from NCBI gene URLs
- **Effort**: Medium (new extractor pattern, tests)
- **Pros**: More semantically correct
- **Cons**: Gene IDs are not citeable academic references

**Option C: Keep as Plain URLs**
- Don't extract identifiers from database URLs
- Render as simple hyperlinks in bibliography
- **Effort**: Small (update extractor patterns)
- **Pros**: Clearest representation
- **Cons**: Less metadata available

### Decision: Option C - Keep as Plain URLs ✅

**User Choice**: Keep database URLs (NCBI gene, Protein Atlas, etc.) as plain URLs without extracting identifiers.

**Rationale**:
- Gene IDs and database entries are not citeable academic references
- Clearest representation for non-article URLs
- Minimal implementation effort

**Implementation**: Ensure extractor patterns don't falsely match database URLs (current behavior appears correct)

---

## Testing Strategy

### Unit Tests
```bash
# Test specific fix
uv run pytest tests/unit/test_identifiers.py::TestIdentifierExtraction::test_extract_doi_from_nature_urls_with_file_extensions -v

# Full unit test suite
uv run pytest -m unit
```

### Integration Tests
```bash
# Full integration test suite
uv run pytest -m integration
```

### Empirical Validation
```bash
# Re-run all empirical tests
uv run python test_problematic_urls.py
uv run python test_real_citations.py

# Compare before/after results
diff citation_analysis_results_before.json citation_analysis_results.json
```

---

## Success Criteria

✅ All unit tests pass (existing + new)
✅ All integration tests pass
✅ No DOIs contain file extensions
✅ No metapub validation warnings for valid Nature URLs
✅ Metadata retrieved for all valid academic URLs
✅ Consistent citation formatting across all academic references
✅ Empirical test success rate: 100% (or 98.3% if proteinatlas is expected failure)

---

## Implementation Timeline

### Phase 1: Core Fix (Issue #1)
1. ✍️ Write failing tests (5 min)
2. 🔴 Commit failing tests (RED phase)
3. 🔧 Implement `_strip_file_extensions()` (10 min)
4. 🔧 Update `_extract_journal_doi()` (5 min)
5. ✅ Run tests until GREEN (5 min)
6. 🟢 Commit fix (GREEN phase)
7. 🧹 Refactor if needed (5 min)

**Total**: ~30 minutes

### Phase 2: Verification
1. Re-run empirical tests (10 min)
2. Verify Issues #2 and #3 auto-resolved (5 min)
3. Run full test suite (5 min)

**Total**: ~20 minutes

### Phase 3: Verify Issue #4 (Database URLs)
1. Verify NCBI gene URLs remain as plain URLs (no identifier extraction)
2. Verify proteinatlas URLs remain as plain URLs
3. Confirm this is acceptable behavior per user preference (Option C)

**Total**: ~5 minutes (verification only, no code changes needed)

---

## Risk Assessment

### Low Risk
- **Change scope**: Single method modification
- **Test coverage**: Comprehensive unit tests
- **Impact**: Localized to Nature URL extraction
- **Rollback**: Simple git revert if issues arise

### Validation
- Empirical tests with 67 real-world URLs
- Clear before/after comparison
- Known expected outputs for all test cases

---

## Files Modified

### Tests (RED Phase)
- `tests/unit/test_identifiers.py` - Add file extension stripping tests

### Implementation (GREEN Phase)
- `src/lit_agent/identifiers/extractors.py` - Add `_strip_file_extensions()` method and update `_extract_journal_doi()`

### Documentation
- `EMPIRICAL_ANALYSIS.md` - Analysis results (already created)
- `IMPLEMENTATION_PLAN.md` - This file

---

## Appendix: Test Cases

### Confirmed Failures (Before Fix)
1. `https://www.nature.com/articles/s41467-025-67223-4_reference.pdf` → `10.1038/s41467-025-67223-4_reference.pdf` ❌
2. `https://www.nature.com/articles/s41467-025-66109-9_reference.pdf` → `10.1038/s41467-025-66109-9_reference.pdf` ❌

### Expected Successes (After Fix)
1. `https://www.nature.com/articles/s41467-025-67223-4_reference.pdf` → `10.1038/s41467-025-67223-4` ✅
2. `https://www.nature.com/articles/s41467-025-66109-9_reference.pdf` → `10.1038/s41467-025-66109-9` ✅
3. `https://www.nature.com/articles/s41586-023-06502-w.pdf` → `10.1038/s41586-023-06502-w` ✅
4. `https://www.nature.com/articles/s41586-023-06502-w.html` → `10.1038/s41586-023-06502-w` ✅

### Regression Prevention
1. `https://www.nature.com/articles/s41586-023-06502-w` → `10.1038/s41586-023-06502-w` ✅ (no extension, should still work)
