# ADR-028: No YAML Validation Context

## Status
PROPOSED

## Context
YAML parsing errors are silently caught without file context.

## Finding
**File**: `collect_usage.py:345-359`

```python
def extract_yaml_frontmatter(content: str) -> dict:
    # ...
    except yaml.YAMLError:
        return {}  # No context about which file failed
```

## Impact
- Skills/agents with broken frontmatter are silently skipped
- User won't know their configuration is invalid
- Debugging trigger/description issues becomes difficult

## Recommendation
Add file path parameter and log on error:

```python
def extract_yaml_frontmatter(content: str, source_path: str = "") -> dict:
    try:
        # ... existing logic
    except yaml.YAMLError as e:
        if source_path:
            print(f"Warning: Invalid YAML in {source_path}: {e}", file=sys.stderr)
        return {}
```

Update all call sites to pass the source path.

## Review Notes
- Severity: Medium (data integrity)
- Effort: Low
- Risk: None (logging only)
