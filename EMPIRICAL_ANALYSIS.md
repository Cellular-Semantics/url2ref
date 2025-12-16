# Empirical Citation Processing Analysis

## Test Results Summary

### Test 1: User-Provided 58 URLs
- **Success Rate**: 98.3% (57/58)
- **Failures**: 1 URL (proteinatlas.org - expected, not an academic article)
- **Issues Found**: 0 (no file extension problems, no formatting issues)
- **Conclusion**: System handles standard academic URLs excellently

### Test 2: Problematic URLs from Error Messages
- **Total Tested**: 9 URLs
- **Issues Found**: 2 URLs with DOI file extension problems
- **Success Rate**: 77.8% (7/9 fully correct)

## Confirmed Issues

### Issue 1: DOI Extraction with File Extensions ⚠️ HIGH PRIORITY

**Examples**:
```
URL:  https://www.nature.com/articles/s41467-025-67223-4_reference.pdf
DOI:  10.1038/s41467-025-67223-4_reference.pdf  ❌ WRONG
Expected: 10.1038/s41467-025-67223-4

URL:  https://www.nature.com/articles/s41467-025-66109-9_reference.pdf
DOI:  10.1038/s41467-025-66109-9_reference.pdf  ❌ WRONG
Expected: 10.1038/s41467-025-66109-9
```

**Impact**:
- Malformed DOIs cause CrossRef API 404 errors
- No metadata retrieved (missing title, authors, etc.)
- Inconsistent bibliography formatting

**Root Cause**:
- `src/lit_agent/identifiers/extractors.py:210`
- Pattern: `r"nature\.com/articles/([^/?]+)"` captures everything including `_reference.pdf`
- Line 262 constructs DOI: `f"10.1038/{potential_doi}"` without stripping extensions

**Frequency**:
- Rare in standard workflows (0/58 in user's main URLs)
- But when it occurs, causes cascading failures

---

### Issue 2: metapub Validation Warnings ⚠️ MEDIUM PRIORITY

**Error Messages**:
```
metapub validation failed for doi 10.1038/s41467-025-67223-4_reference.pdf:
Client error '404 Not Found' for url 'https://api.crossref.org/works/10.1038/s41467-025-67223-4_reference.pdf'
```

**Impact**:
- Log spam (warnings for every malformed DOI)
- Validation attempts on invalid DOIs waste API calls

**Root Cause**:
- Secondary effect of Issue #1 (malformed DOIs)
- CrossRef API correctly rejects DOIs with file extensions
- Validator logs warnings but doesn't prevent the malformed DOI from being used

**Fix Strategy**:
- Primarily: Fix Issue #1 (prevent malformed DOIs)
- Secondarily: Improve error handling to reduce log spam

---

### Issue 3: Citation Formatting Inconsistency ⚠️ MEDIUM PRIORITY

**Observation**:
```
[1] https://www.nature.com/articles/s41467-025-67223-4_reference.pdf
    DOI: 10.1038/s41467-025-67223-4_reference.pdf
    Title: N/A
    Has metadata: False

[2] https://www.nature.com/articles/s41597-025-06145-8
    DOI: 10.1038/s41597-025-06145-8
    Title: The chromosome-level genome assembly...
    Has metadata: True
```

**Impact**:
- Citations with malformed DOIs render as bare URLs
- Citations with valid DOIs render as "Author et al. Title. DOI"
- Inconsistent bibliography appearance

**Root Cause**:
- Direct consequence of Issue #1
- Malformed DOIs fail CrossRef lookup → no metadata
- No metadata → fallback to URL-only rendering

**Fix Strategy**:
- Fix Issue #1, which will resolve this automatically

---

### Issue 4: Non-Journal URL Handling ⚠️ LOW PRIORITY

**Examples**:
```
https://www.proteinatlas.org/ENSG00000137962-ARHGAP29/cancer/glioma
→ No identifiers extracted (expected behavior)

https://www.ncbi.nlm.nih.gov/gene/26291
→ Extracts PMID from related paper, not gene ID
```

**Impact**:
- Database URLs don't extract meaningful identifiers
- Gene URLs extract PMIDs from linked papers (potentially confusing)

**Current Behavior**:
- proteinatlas.org: Correctly identified as non-academic, no extraction
- NCBI gene URLs: Extracts PMID from most recent related publication

**User Expectation**: Unclear - need to clarify:
- Option A: Keep gene URLs as-is (just the URL)
- Option B: Extract gene ID (e.g., "Gene: 26291")
- Option C: Extract linked paper PMID (current behavior)

---

## Priority Ranking

1. **HIGH**: Issue #1 - DOI file extension stripping (fixes Issues #2 and #3 as side effects)
2. **MEDIUM**: Verify Issue #2 and #3 are resolved after fixing Issue #1
3. **LOW**: Issue #4 - Decide on gene URL handling strategy with user

## Key Insights

1. **System is robust for standard use cases**: 98.3% success rate on real-world URLs
2. **Edge case impacts are severe**: File extension issue causes cascading failures
3. **Fix is localized**: Single method modification in extractors.py
4. **TDD is feasible**: Clear test cases exist with known expected outputs

## Next Steps

1. Write failing tests for Issue #1 (file extension stripping)
2. Implement fix in `extractors.py:_extract_journal_doi()`
3. Verify Issues #2 and #3 resolve automatically
4. Re-run empirical tests to confirm
5. Ask user about Issue #4 (gene URL handling)
