# Outdated Plugin & Stale Cache Checks

## Goal

Add two new pre-computed finding types to the observability collector that detect outdated installed plugins and stale cache artifacts.

## Finding Types

### 1. `outdated_plugins`

Compares installed plugin versions against what's available in the remote marketplace GitHub repo.

**Output per finding:**
```json
{
    "plugin": "superpowers",
    "marketplace": "superpowers-marketplace",
    "installed_version": "4.0.3",
    "latest_version": "4.1.1",
    "source_repo": "obra/superpowers-marketplace"
}
```

**Data flow:**
1. Read `~/.claude/settings.json` -> `extraKnownMarketplaces` for repo URLs
2. Read local `marketplace.json` from each cached marketplace to get plugin source paths
3. Fetch `{source}/.claude-plugin/plugin.json` from GitHub API: `GET /repos/{owner}/{repo}/contents/{path}/.claude-plugin/plugin.json`
4. Parse remote `version` field, compare against locally installed latest version using semantic version comparison

**Edge cases:**
- Marketplaces without a repo entry in settings -> skip remote check, not flagged
- Plugins without a `version` field in plugin.json (e.g., `atlassian`, `slack`) -> skip
- GitHub API errors / rate limits -> graceful skip, don't fail the collector
- Commit-hash version dirs (e.g., `claude-plugins-official`) -> skip version comparison
- No network available -> skip all remote checks, produce empty list

### 2. `stale_cache`

Three sub-checks, all local (no network):

**a) Temp directory leftovers** - `temp_git_*` dirs in plugin cache
```json
{"type": "temp_leftover", "path": "temp_git_1770021977469_jt1fll"}
```

**b) Old version accumulation** - Plugins with >1 old version directory
```json
{
    "type": "old_versions",
    "plugin": "observability",
    "marketplace": "bglowacki-marketplace",
    "active_version": "2.7.1",
    "old_versions": ["2.4.0", "2.5.0", "2.6.0", "2.7.0"],
    "old_count": 4
}
```
Threshold: flag if >1 old version exists (latest always kept).

**c) Orphaned marketplaces** - Cache dirs not in `settings.json`
```json
{"type": "orphaned_marketplace", "name": "cc-handbook"}
```

## Implementation

### New functions in `collect_usage.py`

**`check_outdated_plugins(plugins_cache, settings_path)`**
- Reads settings.json for marketplace repo mappings
- For each marketplace with a known repo, reads local marketplace.json for plugin list
- Fetches remote plugin.json via GitHub API (`urllib.request`, no auth needed for public repos)
- Compares versions using `packaging.version.Version` or manual semver parse
- Returns list of outdated findings
- Timeout: 5s per request, total cap of 30s for all remote checks

**`check_stale_cache(plugins_cache, settings_path)`**
- Scans for `temp_git_*` dirs
- For each plugin, finds version dirs and identifies old ones (all except latest by semver)
- Cross-references marketplace dirs against settings.json entries
- Returns list of stale cache findings

### Integration into `compute_pre_computed_findings()`

Add `plugins_cache` and `settings_path` parameters. Call both new functions and add results:

```python
result = {
    # ... existing findings ...
    "outdated_plugins": outdated_plugins[:20],
    "stale_cache": stale_cache[:20],
    "counts": {
        # ... existing counts ...
        "outdated_plugins": len(outdated_plugins),
        "stale_cache_temp": len([s for s in stale_cache if s["type"] == "temp_leftover"]),
        "stale_cache_old_versions": len([s for s in stale_cache if s["type"] == "old_versions"]),
        "stale_cache_orphaned": len([s for s in stale_cache if s["type"] == "orphaned_marketplace"]),
    },
}
```

### No changes to

- `generate_session_summary.py` (hook)
- Agent/skill/command markdown files
- No new dependencies beyond stdlib (`urllib.request`, `json`, `base64`)

## Testing

- Mock GitHub API responses for remote version checks
- Temp fixture directories for stale cache detection
- Edge cases: missing settings.json, no version field, API failure, commit-hash versions, empty cache
- Verify graceful degradation when network unavailable

## Version

PATCH bump (e.g., 2.7.1 -> 2.8.0 since it's a new feature, MINOR bump).
