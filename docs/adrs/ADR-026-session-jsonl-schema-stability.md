# ADR-026: Session JSONL Schema Stability

**Status:** IMPLEMENTED
**Date:** 2026-01-27
**Revised:** 2026-01-27
**Category:** Risk
**Decision:** Defensive parsing + schema fingerprinting + degradation thresholds + output metadata

## Context

The analysis relies on parsing Claude Code's session JSONL files:
- Entry types: user, assistant, system
- Content structures vary by entry type
- Subtype field for system events (e.g., "compact_boundary")
- Tool use structures in assistant messages

## Risk Identified

**The JSONL format is an internal Claude Code implementation detail, not a stable API.**

If Claude Code changes the JSONL format:
1. Parsing may silently fail or produce wrong results
2. New fields may be missed
3. Removed fields may cause exceptions
4. Format changes have no deprecation notice

## Deep Research Findings (2026-01-27)

Critical issues with original proposal:

### 1. DEFENSIVE PARSING IS NECESSARY BUT INSUFFICIENT

**Problem:** try/except catches exceptions but not semantic errors.

| Change Type | Impact | try/except Helps? |
|-------------|--------|-------------------|
| New entry type added | Silently ignored | NO |
| Field renamed | KeyError or empty value | Partial |
| Field removed | Empty defaults, wrong logic | NO |
| Structure changed | Iteration fails | Partial |
| New tool added | Missed tracking | NO |

If `message.content` silently becomes `None` instead of raising, the code continues with empty data. This is **worse** than crashing because users don't know data is incomplete.

### 2. "MONITOR CLAUDE CODE RELEASES" IS TOO VAGUE

Original proposal had no mechanism for:
- Who monitors?
- How? (RSS? GitHub releases? Manual?)
- When? (Before or after upgrading?)
- What action?

### 3. NO DEGRADATION MODEL

Original proposal: "Continue analysis even with partial failures"

But how much failure is acceptable?
- 10% parse failures: Probably sampling noise
- 50% parse failures: Data unreliable
- 90% parse failures: Analysis is random

Without thresholds, users can't assess data quality.

### 4. DUPLICATE PARSING LOGIC

Both `collect_usage.py` (lines 855-969) and `generate_session_summary.py` (lines 162-231) have identical schema assumptions. Changes require updating both files.

## Revised Decision

**ACCEPTED with significant strengthening:**

1. **KEEP defensive parsing** - wrap each entry in try/except
2. **ADD schema fingerprinting** - detect schema changes proactively
3. **ADD degradation thresholds** - fail loudly when parse success rate is too low
4. **ADD output metadata** - include parse_success_rate in JSON output
5. **CONSOLIDATE parsing** - extract to shared module (long-term)

## Revised Implementation Plan

### 1. Schema Fingerprinting

Detect schema characteristics on startup:

```python
@dataclass
class SchemaFingerprint:
    has_message_field: bool
    content_types: set[str]  # {"str", "list", etc.}
    tool_field_path: str | None
    entry_types: set[str]  # {"user", "assistant", "system"}

EXPECTED_FINGERPRINT = SchemaFingerprint(
    has_message_field=True,
    content_types={"str", "list"},
    tool_field_path="message.content[].type=tool_use",
    entry_types={"user", "assistant", "system"},
)

def detect_schema_fingerprint(entries: list[dict]) -> SchemaFingerprint:
    """Sample entries and detect schema characteristics."""
    ...

def compare_to_expected(actual: SchemaFingerprint) -> list[str]:
    """Return list of schema differences."""
    differences = []
    if not actual.has_message_field:
        differences.append("'message' field missing")
    if actual.entry_types - EXPECTED_FINGERPRINT.entry_types:
        differences.append(f"New entry types: {actual.entry_types - EXPECTED_FINGERPRINT.entry_types}")
    return differences
```

### 2. Degradation Thresholds

Fail loudly when data quality is unacceptable:

```python
MIN_PARSE_SUCCESS_RATE = 0.80  # Fail if <80% entries parse

def parse_session_file(path: Path) -> SessionData:
    entries_total = 0
    entries_parsed = 0
    parsing_errors = []

    for line in file:
        entries_total += 1
        try:
            entry = json.loads(line)
            # ... parse entry ...
            entries_parsed += 1
        except Exception as e:
            parsing_errors.append({"line": entries_total, "error": str(e)})

    success_rate = entries_parsed / entries_total if entries_total > 0 else 1.0

    if success_rate < MIN_PARSE_SUCCESS_RATE:
        raise SchemaChangeError(
            f"Parse success rate {success_rate:.1%} below threshold {MIN_PARSE_SUCCESS_RATE:.0%}. "
            f"JSONL schema may have changed."
        )

    return SessionData(..., parse_success_rate=success_rate, parsing_errors=parsing_errors)
```

### 3. Output Metadata

Include schema health in JSON output:

```json
{
  "_schema": {
    "version": "3.1",
    "jsonl_format_detected": "2026-01",
    "schema_fingerprint_match": true,
    "parse_success_rate": 0.98,
    "entries_total": 150,
    "entries_parsed": 147,
    "parsing_errors_count": 3
  },
  "stats": { ... },
  "discovery": { ... }
}
```

### 4. Automated Schema Change Detection

On first run after potential Claude Code upgrade:

```python
def check_schema_compatibility():
    """Run at startup to detect schema changes."""
    sample_entries = load_sample_entries()
    actual_fingerprint = detect_schema_fingerprint(sample_entries)
    differences = compare_to_expected(actual_fingerprint)

    if differences:
        print("WARNING: JSONL schema may have changed", file=sys.stderr)
        for diff in differences:
            print(f"  - {diff}", file=sys.stderr)
        print("Analysis may be unreliable. See ADR-026.", file=sys.stderr)
```

### 5. Long-term: Consolidated Parser Module

Extract JSONL parsing to shared module:

```
observability/
  lib/
    jsonl_parser.py     # Shared parsing logic
    schema.py           # Expected schema definitions
  skills/.../collect_usage.py   # Uses lib/jsonl_parser
  hooks/generate_session_summary.py  # Uses lib/jsonl_parser
```

## Dependencies

- None for immediate implementation
- ADR-013 (code sync) helps with consolidation

## Review Summary

### Backend Architect Review (Original)
- **Verdict:** ACCEPT
- **Assessment:** Correctly identifies a real fragility. Pragmatic for internal API dependency.

### Deep Research Review (2026-01-27)
- **Finding:** Defensive parsing alone is insufficient
- **Added:** Schema fingerprinting for proactive detection
- **Added:** Degradation thresholds (80% minimum)
- **Added:** Output metadata for data quality visibility
- **Added:** Automated schema change warnings
- **Long-term:** Consolidated parser module

## Consequences

- More robust against minor JSONL changes (defensive parsing)
- **Proactive detection** of schema changes (fingerprinting)
- **User visibility** into data quality (metadata)
- **Fail loudly** when data is unreliable (thresholds)
- Accepted tech debt: no official API stability guarantee
- Better than silent degradation
