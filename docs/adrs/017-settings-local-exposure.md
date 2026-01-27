# ADR-017: Review settings.local.json Exposure

## Status
PROPOSED

## Context
The `.claude/settings.local.json` file contains permission grants:
```json
{
  "permissions": {
    "allow": [
      "Bash(python3:*)",
      "Bash(chmod:*)",
      "Bash(stat:*)",
      "Bash(head:*)",
      "Bash(find:*)",
      "Bash(cat:*)",
      "Skill(superpowers:brainstorming)"
    ]
  }
}
```

This file is tracked in git and would be shared with anyone cloning the repository.

## Finding
**File**: `.claude/settings.local.json`

Issues:
1. `.local.json` files are typically meant for user-specific settings NOT committed to git
2. Granting broad permissions (`python3:*`, `chmod:*`) may not be appropriate for all users
3. The `superpowers:brainstorming` skill reference is user-specific

## Decision
TBD - Needs review

## Options

### Option A: Add to .gitignore
Remove from git and add `*.local.json` to `.gitignore`.

**Pros**: Standard practice, allows user-specific config
**Cons**: Loses the example configuration

### Option B: Rename to settings.example.json
Keep as example, users copy to settings.local.json.

**Pros**: Shows intended usage pattern
**Cons**: Extra step for users

### Option C: Move to settings.json
If these are intentional project settings, put in settings.json (non-local).

**Pros**: Clear intent that these are project defaults
**Cons**: May override user preferences

### Option D: Keep Current
These are intentional for the project development workflow.

**Pros**: No change needed
**Cons**: May confuse contributors

## Recommendation
Option A - The pattern for `.local.json` files is that they should NOT be committed. Add to `.gitignore`:
```
.claude/settings.local.json
```

If the permissions are needed for the project, document them in CLAUDE.md or move to settings.json.

## Impact
- Follows standard configuration patterns
- Prevents unintended permission sharing
- Users can customize without git conflicts

## Review Notes
- Severity: Low (configuration hygiene)
- Effort: Trivial
- Risk: Low
