# ADR-043: Prompt Data Sanitization for Privacy

**Status:** ACCEPTED
**Date:** 2026-01-27
**Category:** Security / Privacy
**Source:** Code exploration finding

## Context

User prompt text is captured in analysis output:

```python
"prompts": [
    {
        "session_id": s.session_id,
        "text": p[:MAX_PROMPT_LENGTH],  # Full prompt text
    }
]
```

Also `followup_message` in interrupted tools tracking.

## Problem Statement

Privacy risks:
- API keys or credentials mentioned in prompts are captured
- Customer data, passwords, confidential context leaked
- No data retention policy or sanitization option
- Compliance issues (GDPR, CCPA) if PII retained

## Proposed Solution

1. Add `--no-prompts` flag to exclude user prompt text
2. Add sanitization function to redact sensitive patterns:

```python
def sanitize_prompt(prompt: str) -> str:
    sanitized = re.sub(r'sk-[a-zA-Z0-9]{20,}', '[REDACTED_KEY]', prompt)
    sanitized = re.sub(r'["\']?([a-z0-9_-]{32,})["\']?', '[REDACTED_TOKEN]', sanitized)
    return sanitized
```

3. Document privacy implications in README
4. Add data retention policy (auto-delete after 30 days)

## Related ADRs

- ADR-028: Multi-Project Analysis (privacy mitigation)

## Review Summary

### Backend Architect
- **Verdict:** ACCEPT (High Priority)
- **Complexity:** Medium
- **Priority:** HIGH for privacy compliance

### System Architect
- **Verdict:** ACCEPT with modifications
- **Decision:** Sanitization should be OPT-OUT (default ON)
- **Decision:** Use established patterns: AWS `AKIA`, GitHub `ghp_/gho_`, `password=`, `secret=`

## Implementation Notes

- --no-prompts as immediate mitigation (opt-in to include prompts)
- --sanitize-prompts default ON with comprehensive patterns
- Allow project-level custom regex via config
- Log when sanitization occurs (without logging what)
