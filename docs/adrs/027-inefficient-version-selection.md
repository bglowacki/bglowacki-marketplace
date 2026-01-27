# ADR-027: Inefficient Version Directory Selection

## Status
PROPOSED

## Context
Finding the "latest version" of a plugin performs a `stat()` system call for every version directory.

## Finding
**File**: `collect_usage.py:520-524, 665-669`

```python
latest_version = max(version_dirs, key=lambda d: d.stat().st_mtime)
```

This performs O(n) stat calls where n = number of version directories.

## Impact
- Slow startup when many plugins/versions installed
- Called twice per plugin (once for discovery, once for hooks)
- Could become noticeable with 50+ plugin versions

## Recommendation
Cache stat results or use simpler version comparison:

```python
# Option A: Cache stats
version_stats = [(d, d.stat().st_mtime) for d in version_dirs]
latest_version = max(version_stats, key=lambda x: x[1])[0]

# Option B: Use semver comparison (if versions follow semver)
from packaging.version import Version
latest_version = max(version_dirs, key=lambda d: Version(d.name))
```

Option A is preferred as it doesn't require the versions to follow any format.

## Review Notes
- Severity: Medium (performance)
- Effort: Low
- Risk: None
