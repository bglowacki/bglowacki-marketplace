#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml"]
# ///
"""
Usage Collector - Collect Claude Code usage data for analysis.

Gathers data from JSONL session files to provide:
- Tool usage counts and patterns
- Outcomes (success/failure/interrupted)
- Compactions and context efficiency
- Workflow stage detection

Outputs structured data for interpretation by usage-insights-agent.
This script performs DATA COLLECTION only - no analysis or recommendations.
"""

import argparse
import json
import os
import re
import sys
import hashlib
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# Constants (ADR-009: Extract magic numbers)
MAX_DESCRIPTION_LENGTH = 200
MAX_TOOL_INPUT_LENGTH = 100
MAX_PROMPT_LENGTH = 500
DEFAULT_SESSIONS = 10
DEFAULT_DAYS = 14
MIN_TRIGGER_LENGTH = 3  # ADR-001: Unified trigger length threshold
MIN_PARSE_SUCCESS_RATE = 0.80  # ADR-026: Fail if <80% entries parse

# Common word blocklist for trigger matching (ADR-001)
COMMON_WORD_BLOCKLIST = frozenset({
    "the", "for", "and", "but", "add", "run", "fix", "use", "new", "old",
    "get", "set", "put", "can", "has", "was", "are", "not", "all", "any",
    "now", "see", "try", "how", "why", "who", "its", "out", "two", "way",
})

# Path constants (ADR-020: Centralize Path.home())
HOME = Path.home()
CLAUDE_DIR = HOME / ".claude"
PROJECTS_DIR = CLAUDE_DIR / "projects"
SUMMARIES_DIR = CLAUDE_DIR / "session-summaries"
PLUGINS_CACHE = CLAUDE_DIR / "plugins" / "cache"

# Frequency band thresholds (ADR-005)
FREQ_NEVER = 0
FREQ_RARELY_MAX = 2
FREQ_SOMETIMES_MAX = 10
# often: > FREQ_SOMETIMES_MAX

# Track YAML parsing issues for summary reporting (graceful handling)
_yaml_parse_issues: list[str] = []


@dataclass
class SchemaFingerprint:
    """ADR-026: Schema characteristics for detecting JSONL format changes."""
    has_message_field: bool
    content_types: set[str]  # {"str", "list", etc.}
    entry_types: set[str]  # {"user", "assistant", "system"}


# Expected JSONL schema fingerprint (ADR-026)
EXPECTED_FINGERPRINT = SchemaFingerprint(
    has_message_field=True,
    content_types={"str", "list"},
    entry_types={"user", "assistant", "system"},
)


def detect_schema_fingerprint(entries: list[dict]) -> SchemaFingerprint:
    """ADR-026: Sample entries and detect schema characteristics."""
    has_message = False
    content_types: set[str] = set()
    entry_types: set[str] = set()

    for entry in entries:
        if "message" in entry:
            has_message = True
        entry_type = entry.get("type")
        if entry_type:
            entry_types.add(entry_type)
        content = entry.get("message", {}).get("content")
        if content is not None:
            content_types.add(type(content).__name__)

    return SchemaFingerprint(
        has_message_field=has_message,
        content_types=content_types,
        entry_types=entry_types,
    )


def compare_schema_fingerprint(actual: SchemaFingerprint) -> list[str]:
    """ADR-026: Return list of schema differences from expected."""
    differences = []
    if not actual.has_message_field and EXPECTED_FINGERPRINT.has_message_field:
        differences.append("'message' field missing from entries")
    new_types = actual.entry_types - EXPECTED_FINGERPRINT.entry_types
    if new_types:
        differences.append(f"New entry types: {new_types}")
    missing_types = EXPECTED_FINGERPRINT.entry_types - actual.entry_types
    if missing_types:
        differences.append(f"Missing entry types: {missing_types}")
    return differences


@dataclass
class SkillOrAgent:
    name: str
    type: str  # "skill", "agent", or "command"
    description: str
    triggers: list[str]
    source_path: str
    source_type: str = "unknown"  # "global", "project", or "plugin:<name>"


@dataclass
class Hook:
    event_type: str  # PreToolUse, PostToolUse, Stop, etc.
    matcher: str  # Tool matcher pattern (e.g., "Bash", "*")
    command: str  # The command/script to run
    source_path: str
    source_type: str  # "global", "project", "project-local", or "plugin:<name>"
    timeout: Optional[int] = None


@dataclass
class InterruptedTool:
    tool_name: str
    tool_input: dict
    followup_message: str  # What user said after interrupting
    # ADR-006 additions
    duration_ms: Optional[int] = None  # Time from tool start to interruption
    position: str = "primary"  # "primary" (first pending) or "collateral"
    category: str = "user_initiated"  # "timeout" | "user_initiated" | "session_abandon"


# ADR-006: Tool-aware timeout thresholds (in milliseconds)
TIMEOUT_THRESHOLDS_MS = {
    "Bash": 30000,      # 30s
    "Task": 120000,     # 2 min - subagents take longer
    "WebFetch": 45000,  # 45s
    "Read": 10000,      # 10s
    "Edit": 10000,      # 10s
    "Write": 10000,     # 10s
    "default": 30000,   # 30s fallback
}


def classify_interruption(tool_name: str, duration_ms: Optional[int], followup: str) -> str:
    """ADR-006: Classify interruption type based on duration and context."""
    if followup == "[session ended]":
        return "session_abandon"

    if duration_ms is not None:
        threshold = TIMEOUT_THRESHOLDS_MS.get(tool_name, TIMEOUT_THRESHOLDS_MS["default"])
        if duration_ms > threshold:
            return "timeout"

    return "user_initiated"  # Don't guess from keywords per ADR-006


@dataclass
class SessionData:
    session_id: str
    prompts: list[str] = field(default_factory=list)
    skills_used: set[str] = field(default_factory=set)
    agents_used: set[str] = field(default_factory=set)
    tools_used: set[str] = field(default_factory=set)
    hooks_triggered: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    # Outcome tracking
    success_count: int = 0
    failure_count: int = 0
    interrupted_count: int = 0
    compaction_count: int = 0
    # Interrupted tools with context
    interrupted_tools: list[InterruptedTool] = field(default_factory=list)
    # Parse statistics (ADR-026)
    entries_total: int = 0
    entries_parsed: int = 0
    parsing_errors: list[dict] = field(default_factory=list)
    # ADR-047: Temporal tracking
    session_date: Optional[datetime] = None
    recency_weight: float = 1.0  # 0.0-1.0 based on age


# ADR-047: Temporal weighting constants
RECENCY_HALF_LIFE_DAYS = 7  # Weight halves every 7 days

# ADR-048: Feedback storage
FEEDBACK_FILE = CLAUDE_DIR / "observability-feedback.json"

# ADR-049: Alert fatigue prevention
MAX_FINDINGS_PER_CATEGORY = 5
MAX_TOTAL_FINDINGS = 15
MAX_FINDINGS_DETAILED = 30  # For detailed JSON output

# ADR-050: Statistical significance thresholds
MIN_SESSIONS_FOR_PATTERN = 5  # Need at least 5 sessions for pattern detection
MIN_OCCURRENCES_FOR_SIGNIFICANCE = 3  # Need at least 3 occurrences to report


def compute_pre_computed_findings(
    skills: list,
    agents: list,
    commands: list,
    sessions: list,
    missed: list,
    setup_profile,
) -> dict:
    """ADR-054: Pre-compute deterministic findings that don't need LLM.

    These findings are 100% certain (no inference needed) and should be
    trusted directly without LLM re-verification.
    """
    # Empty descriptions (< 30 chars)
    empty_descriptions = []
    for item_list, item_type in [(skills, "skill"), (agents, "agent"), (commands, "command")]:
        for item in item_list:
            if len(item.description) < 30:
                empty_descriptions.append({
                    "name": item.name,
                    "type": item_type,
                    "source": item.source_type,
                    "description_length": len(item.description),
                })

    # Never-used components (from skills/agents that have 0 usage)
    used_skills = set()
    used_agents = set()
    for s in sessions:
        used_skills.update(s.skills_used)
        used_agents.update(s.agents_used)

    never_used = []
    for skill in skills:
        if skill.name not in used_skills:
            never_used.append({"name": skill.name, "type": "skill", "source": skill.source_type})
    for agent in agents:
        if agent.name not in used_agents:
            never_used.append({"name": agent.name, "type": "agent", "source": agent.source_type})

    # Name collisions (skill and command with same name)
    skill_names = {s.name.lower() for s in skills}
    command_names = {c.name.lower() for c in commands}
    name_collisions = list(skill_names & command_names)

    # Exact trigger matches that weren't used (high confidence missed opportunities)
    exact_matches = []
    for m in missed:
        if m.matched_item.name.lower() in [t.lower() for t in m.matched_triggers]:
            exact_matches.append({
                "component": m.matched_item.name,
                "type": m.matched_item.type,
                "prompt_preview": m.prompt[:80],
                "finding_hash": m.finding_hash,
            })

    return {
        "_note": "Deterministic findings - 100% certain, no LLM inference needed",
        "empty_descriptions": empty_descriptions[:20],  # Limit
        "never_used": never_used[:20],  # Limit
        "name_collisions": name_collisions,
        "exact_trigger_matches": exact_matches[:20],  # Limit
        "invalid_yaml_files": _yaml_parse_issues[:20],  # Files with YAML frontmatter errors
        # Reference existing pre-computed data
        "overlapping_triggers_count": len(setup_profile.overlapping_triggers),
        "description_quality_issues": sum(1 for d in setup_profile.description_quality if d.get("needs_improvement")),
        "counts": {
            "empty_descriptions": len(empty_descriptions),
            "never_used": len(never_used),
            "name_collisions": len(name_collisions),
            "exact_matches": len(exact_matches),
            "invalid_yaml_files": len(_yaml_parse_issues),
        },
    }


def compute_quality_metrics(
    sessions: list,
    missed: list,
    feedback: dict,
) -> dict:
    """ADR-053: Compute analysis quality metrics for self-evaluation."""
    session_count = len(sessions)
    prompt_count = sum(len(s.prompts) for s in sessions)
    finding_count = len(missed)

    # Finding rate: findings per session (target: 0.5-2.0)
    finding_rate = finding_count / session_count if session_count > 0 else 0

    # High confidence rate: % of findings with confidence >= 0.7 (target: > 60%)
    high_conf = sum(1 for m in missed if m.confidence >= 0.7)
    high_conf_rate = high_conf / finding_count if finding_count > 0 else 0

    # Category coverage: how many categories have findings (target: > 30%)
    categories_with_findings = len(set(m.matched_item.type for m in missed))
    total_categories = 3  # skill, agent, command
    coverage = categories_with_findings / total_categories

    # Acceptance rate from feedback (target: > 50%)
    accepted = len(feedback.get("accepted", []))
    dismissed = len(feedback.get("dismissed", []))
    total_feedback = accepted + dismissed
    acceptance_rate = accepted / total_feedback if total_feedback > 0 else None

    # Quality assessment
    issues = []
    if finding_rate < 0.5:
        issues.append("Low finding rate - may be missing opportunities")
    elif finding_rate > 3.0:
        issues.append("High finding rate - may need stricter filtering")

    if high_conf_rate < 0.6 and finding_count >= 5:
        issues.append("Many low-confidence findings - quality uncertain")

    if acceptance_rate is not None and acceptance_rate < 0.5:
        issues.append(f"Low acceptance rate ({acceptance_rate:.0%}) - calibration needed")

    return {
        "input": {
            "sessions": session_count,
            "prompts": prompt_count,
        },
        "output": {
            "findings": finding_count,
            "high_confidence": high_conf,
            "category_coverage": f"{categories_with_findings}/{total_categories}",
        },
        "rates": {
            "finding_rate": round(finding_rate, 2),
            "high_confidence_rate": round(high_conf_rate, 2),
            "category_coverage_rate": round(coverage, 2),
            "acceptance_rate": round(acceptance_rate, 2) if acceptance_rate else None,
        },
        "targets": {
            "finding_rate": "0.5-2.0",
            "high_confidence_rate": ">0.6",
            "acceptance_rate": ">0.5",
        },
        "quality_issues": issues,
        "overall_quality": "good" if not issues else "needs_attention",
    }


def assess_data_sufficiency(sessions: list, missed: list) -> dict:
    """ADR-050: Assess if we have enough data for meaningful patterns."""
    session_count = len(sessions)
    prompt_count = sum(len(s.prompts) for s in sessions)

    # Classify data sufficiency
    if session_count >= 10 and prompt_count >= 50:
        sufficiency = "high"
        confidence_note = "Sufficient data for reliable patterns"
    elif session_count >= MIN_SESSIONS_FOR_PATTERN:
        sufficiency = "medium"
        confidence_note = "Moderate data - patterns may be preliminary"
    else:
        sufficiency = "low"
        confidence_note = f"Insufficient data ({session_count} sessions, need {MIN_SESSIONS_FOR_PATTERN}+)"

    # Count occurrences per component
    component_counts: dict[str, int] = defaultdict(int)
    for m in missed:
        component_counts[m.matched_item.name] += 1

    # Filter to significant patterns only
    significant_components = [
        name for name, count in component_counts.items()
        if count >= MIN_OCCURRENCES_FOR_SIGNIFICANCE
    ]

    return {
        "sessions_analyzed": session_count,
        "prompts_analyzed": prompt_count,
        "sufficiency": sufficiency,
        "confidence_note": confidence_note,
        "min_sessions_required": MIN_SESSIONS_FOR_PATTERN,
        "min_occurrences_required": MIN_OCCURRENCES_FOR_SIGNIFICANCE,
        "significant_patterns": len(significant_components),
        "insufficient_patterns": len(component_counts) - len(significant_components),
    }


def hash_finding(category: str, component: str, trigger: str) -> str:
    """ADR-048: Generate stable hash for finding deduplication."""
    key = f"{category}:{component}:{trigger}".lower()
    return hashlib.sha256(key.encode()).hexdigest()[:12]


def load_feedback() -> dict:
    """ADR-048: Load user feedback from persistent storage."""
    if not FEEDBACK_FILE.exists():
        return {"dismissed": [], "accepted": [], "metadata": {}}

    try:
        return json.loads(FEEDBACK_FILE.read_text())
    except (json.JSONDecodeError, Exception) as e:
        print(f"Warning: Could not load feedback file: {e}", file=sys.stderr)
        return {"dismissed": [], "accepted": [], "metadata": {}}


def get_dismissed_hashes(feedback: dict) -> set[str]:
    """ADR-048: Get set of dismissed finding hashes."""
    dismissed = set()
    for item in feedback.get("dismissed", []):
        if "finding_hash" in item:
            dismissed.add(item["finding_hash"])
    return dismissed


def compute_acceptance_rate(feedback: dict) -> dict:
    """ADR-048: Calculate acceptance rate per category."""
    by_category: dict[str, dict[str, int]] = defaultdict(lambda: {"accepted": 0, "dismissed": 0})

    for item in feedback.get("accepted", []):
        cat = item.get("category", "unknown")
        by_category[cat]["accepted"] += 1

    for item in feedback.get("dismissed", []):
        cat = item.get("category", "unknown")
        by_category[cat]["dismissed"] += 1

    rates = {}
    for cat, counts in by_category.items():
        total = counts["accepted"] + counts["dismissed"]
        if total > 0:
            rates[cat] = {
                "accepted": counts["accepted"],
                "dismissed": counts["dismissed"],
                "rate": round(counts["accepted"] / total, 2),
            }

    return rates


def calculate_recency_weight(session_date: Optional[datetime], half_life_days: int = RECENCY_HALF_LIFE_DAYS) -> float:
    """ADR-047: Calculate recency weight using exponential decay.

    More recent sessions have higher weight.
    - Today: 1.0
    - 7 days ago: 0.5
    - 14 days ago: 0.25
    """
    if session_date is None:
        return 0.5  # Default weight for unknown dates

    age_days = (datetime.now() - session_date).days
    if age_days < 0:
        return 1.0  # Future dates treated as current

    return 0.5 ** (age_days / half_life_days)


@dataclass
class MissedOpportunity:
    prompt: str
    session_id: str
    matched_item: SkillOrAgent
    matched_triggers: list[str]
    # ADR-046: Confidence scoring
    confidence: float = 0.5  # 0.0 - 1.0
    evidence: list[str] = field(default_factory=list)  # What supports this finding
    # ADR-047: Temporal data
    session_date: Optional[datetime] = None
    recency_weight: float = 1.0
    # ADR-048: Feedback tracking
    finding_hash: str = ""

    def __post_init__(self):
        """Compute finding hash after initialization."""
        if not self.finding_hash and self.matched_item:
            trigger = self.matched_triggers[0] if self.matched_triggers else ""
            self.finding_hash = hash_finding(
                self.matched_item.type,
                self.matched_item.name,
                trigger,
            )


# ADR-046: Confidence thresholds and calculation
CONFIDENCE_HIGH = 0.8
CONFIDENCE_MEDIUM = 0.5
CONFIDENCE_LOW = 0.3


def calculate_match_confidence(
    item: SkillOrAgent,
    matched_triggers: list[str],
    prompt: str,
) -> tuple[float, list[str]]:
    """ADR-046: Calculate confidence score for a potential match.

    Returns (confidence, evidence_list).

    Scoring:
    - Exact name match: 0.5 (strong signal - user mentioned the component)
    - 3+ non-name triggers: 0.35
    - 2 non-name triggers: 0.25
    - 1 non-name trigger: 0.15
    - Long specific trigger (5+ chars): 0.1 bonus
    """
    evidence = []
    score = 0.0

    # Check if item name was matched (strong signal - user mentioned the component)
    name_matched = item.name.lower() in [t.lower() for t in matched_triggers]
    if name_matched:
        score += 0.6
        evidence.append(f"Exact name match: '{item.name}'")

    # Count meaningful trigger matches (exclude name)
    non_name_triggers = [t for t in matched_triggers if t.lower() != item.name.lower()]
    trigger_count = len(non_name_triggers)

    if trigger_count >= 3:
        score += 0.5
        evidence.append(f"{trigger_count} trigger phrases matched")
    elif trigger_count >= 2:
        score += 0.4
        evidence.append(f"{trigger_count} trigger phrases matched")
    elif trigger_count == 1:
        score += 0.2
        evidence.append(f"1 trigger phrase matched: '{non_name_triggers[0]}'")

    # Check for long specific triggers (higher confidence)
    for trigger in non_name_triggers:
        if len(trigger) >= 5:  # Longer triggers are more specific
            score += 0.1
            evidence.append(f"Specific trigger: '{trigger}'")
            break

    # Clamp to [0.0, 1.0]
    confidence = min(max(score, CONFIDENCE_LOW), 1.0)

    # Classify evidence quality
    if confidence >= CONFIDENCE_HIGH:
        evidence.insert(0, "HIGH confidence")
    elif confidence >= CONFIDENCE_MEDIUM:
        evidence.insert(0, "MEDIUM confidence")
    else:
        evidence.insert(0, "LOW confidence")

    return confidence, evidence


@dataclass
class DescriptionQuality:
    """ADR-007: Multi-dimensional description quality assessment."""
    name: str
    item_type: str
    length_ok: bool
    has_triggers: bool
    has_domain: bool
    has_action_verb: bool
    issues: list[str]

    @property
    def needs_improvement(self) -> bool:
        """Fails if ≥2 dimensions are missing."""
        checks = [self.length_ok, self.has_triggers, self.has_domain, self.has_action_verb]
        return sum(1 for c in checks if not c) >= 2


# ADR-007: Action verbs commonly used in good descriptions
ACTION_VERBS = frozenset({
    "collect", "analyze", "create", "generate", "validate", "check", "scan",
    "build", "deploy", "run", "execute", "test", "debug", "review", "optimize",
    "format", "lint", "search", "find", "fetch", "download", "upload", "sync",
    "transform", "convert", "parse", "extract", "summarize", "document",
})

# ADR-007: Domain keywords that indicate specific use context
DOMAIN_KEYWORDS = frozenset({
    "python", "javascript", "typescript", "react", "vue", "angular", "node",
    "django", "flask", "fastapi", "git", "github", "docker", "kubernetes",
    "aws", "azure", "gcp", "database", "sql", "api", "rest", "graphql",
    "claude", "claude code", "session", "plugin", "skill", "agent",
})


def score_description_quality(item: SkillOrAgent) -> DescriptionQuality:
    """ADR-007: Score description quality across multiple dimensions."""
    desc = item.description.lower()
    issues = []

    # Length check: 30-200 chars is good
    length_ok = 30 <= len(item.description) <= 200
    if len(item.description) < 30:
        issues.append("Description too short (<30 chars)")
    elif len(item.description) > 200:
        issues.append("Description too long (>200 chars)")

    # Trigger check: look for quoted phrases or explicit trigger patterns
    has_triggers = (
        '"' in desc or
        "'" in desc or
        "trigger" in desc or
        len(item.triggers) >= 2
    )
    if not has_triggers:
        issues.append("Missing explicit trigger phrases")

    # Domain check: mention specific technology/context
    has_domain = any(kw in desc for kw in DOMAIN_KEYWORDS)
    if not has_domain:
        issues.append("Missing domain context (e.g., 'Python', 'git', 'Claude Code')")

    # Action verb check: starts with or contains action verb
    first_word = desc.split()[0] if desc.split() else ""
    has_action_verb = first_word in ACTION_VERBS or any(v in desc for v in ACTION_VERBS)
    if not has_action_verb:
        issues.append("Missing action verb (e.g., 'Collects', 'Analyzes', 'Creates')")

    return DescriptionQuality(
        name=item.name,
        item_type=item.type,
        length_ok=length_ok,
        has_triggers=has_triggers,
        has_domain=has_domain,
        has_action_verb=has_action_verb,
        issues=issues,
    )


@dataclass
class SetupProfile:
    complexity: str  # "minimal", "moderate", "complex"
    total_components: int
    shape: list[str]  # e.g., ["plugin-heavy", "hook-light"]
    by_source: dict[str, dict[str, int]]  # source_type -> {skills, agents, commands, hooks}
    red_flags: list[str]
    coverage: dict[str, bool]
    coverage_gaps: list[str]
    overlapping_triggers: list[dict]  # [{trigger, items}]
    plugin_usage: dict[str, list[str]]  # {"active": [...], "potential": [...], "unused": [...]}
    description_quality: list[dict] = field(default_factory=list)  # ADR-007


def compute_setup_profile(
    skills: list[SkillOrAgent],
    agents: list[SkillOrAgent],
    commands: list[SkillOrAgent],
    hooks: list[Hook],
    claude_md: dict,
) -> SetupProfile:
    """Compute setup profile for context-first analysis."""

    # Count by source
    by_source: dict[str, dict[str, int]] = defaultdict(lambda: {"skills": 0, "agents": 0, "commands": 0, "hooks": 0})
    for s in skills:
        by_source[s.source_type]["skills"] += 1
    for a in agents:
        by_source[a.source_type]["agents"] += 1
    for c in commands:
        by_source[c.source_type]["commands"] += 1
    for h in hooks:
        by_source[h.source_type]["hooks"] += 1

    # Complexity classification
    total = len(skills) + len(agents) + len(commands) + len(hooks)
    if total < 10:
        complexity = "minimal"
    elif total < 50:
        complexity = "moderate"
    else:
        complexity = "complex"

    # Shape analysis
    shape = []
    total_skills_agents = len(skills) + len(agents)
    plugin_count = sum(
        v["skills"] + v["agents"]
        for k, v in by_source.items()
        if k.startswith("plugin:")
    )
    if total_skills_agents > 0 and (plugin_count / total_skills_agents) > 0.7:
        shape.append("plugin-heavy")
    if len(hooks) < 3:
        shape.append("hook-light")
    if by_source["project"]["skills"] == 0 and by_source["project"]["agents"] == 0:
        if not any(f for f in claude_md.get("files_found", []) if "CLAUDE.md" in f and ".claude" not in f):
            shape.append("no-project-customization")
    if by_source["global"]["skills"] + by_source["global"]["agents"] > 0 and by_source["project"]["skills"] + by_source["project"]["agents"] == 0:
        shape.append("global-heavy")

    # Red flags
    red_flags = []
    global_claude_dir = str(CLAUDE_DIR)
    project_claude_md = [f for f in claude_md.get("files_found", []) if "CLAUDE.md" in f and ".claude" not in f and not f.startswith(global_claude_dir)]
    if not project_claude_md:
        red_flags.append("No project-level CLAUDE.md")
    if by_source["project"]["hooks"] == 0 and by_source.get("project-local", {}).get("hooks", 0) == 0:
        red_flags.append("No project-level hooks")
    if by_source["project"]["skills"] == 0:
        red_flags.append("No project-level skills")

    # Check for empty descriptions
    empty_desc_count = sum(1 for s in skills + agents if not s.description.strip())
    if empty_desc_count > 0:
        red_flags.append(f"{empty_desc_count} components with empty descriptions")

    # ADR-008: Enhanced overlapping trigger detection with severity scoring
    # Include commands in overlap detection
    all_components = skills + agents + commands
    trigger_map: dict[str, list[tuple[str, str, str]]] = defaultdict(list)  # trigger -> [(type, name, source)]

    for item in all_components:
        for trigger in item.triggers:
            trigger_lower = trigger.lower()
            if len(trigger_lower) >= MIN_TRIGGER_LENGTH:  # ADR-001: Unified threshold
                trigger_map[trigger_lower].append((item.type, item.name, item.source_type))

    # Also check for skill/command name collisions (exact name match = high severity)
    skill_names = {s.name.lower() for s in skills}
    command_names = {c.name.lower() for c in commands}
    name_collisions = skill_names & command_names

    overlapping = []
    high_severity_count = 0

    for trigger, items in trigger_map.items():
        if len(items) > 1:
            # ADR-008: Classify severity
            types = {t for t, n, s in items}
            sources = {s for t, n, s in items}

            # Skill/Command collision: HIGH
            if "skill" in types and "command" in types:
                severity = "HIGH"
                high_severity_count += 1
            # Cross-plugin: MEDIUM
            elif len(sources) > 1 and any(s.startswith("plugin:") for s in sources):
                severity = "MEDIUM"
            # Intra-plugin redundancy: LOW
            else:
                severity = "LOW"

            overlapping.append({
                "trigger": trigger,
                "items": [f"{t}:{n}" for t, n, s in items],
                "severity": severity,
            })

    # Add name collision warnings (highest severity)
    for name in name_collisions:
        overlapping.insert(0, {
            "trigger": f"[name collision: {name}]",
            "items": [f"skill:{name}", f"command:{name}"],
            "severity": "HIGH",
        })
        high_severity_count += 1

    if high_severity_count > 0:
        red_flags.append(f"{high_severity_count} HIGH severity trigger/name collisions (skill/command overlap)")
    elif overlapping:
        red_flags.append(f"{len(overlapping)} triggers overlap (review recommended)")

    # Coverage assessment
    all_items = skills + agents
    all_names_desc = " ".join(
        f"{i.name.lower()} {i.description.lower()}" for i in all_items
    )

    coverage = {
        "git_commit": any(kw in all_names_desc for kw in ["commit", "pre-commit"]),
        "code_review": any(kw in all_names_desc for kw in ["review", "pr review"]),
        "testing": any(kw in all_names_desc for kw in ["test", "tdd", "spec"]),
        "debugging": any(kw in all_names_desc for kw in ["debug", "troubleshoot"]),
        "planning": any(kw in all_names_desc for kw in ["plan", "design", "architect"]),
        "event_sourcing": any(kw in all_names_desc for kw in ["aggregate", "event sourc", "projection", "cqrs"]),
        "documentation": any(kw in all_names_desc for kw in ["documentation", "readme", "guide"]),
        "security": any(kw in all_names_desc for kw in ["vulnerab", "secret", "security"]),
    }

    coverage_gaps = [k for k, v in coverage.items() if not v]

    # ADR-007: Score description quality
    description_issues = []
    for item in all_items:
        quality = score_description_quality(item)
        if quality.needs_improvement:
            description_issues.append({
                "name": quality.name,
                "type": quality.item_type,
                "issues": quality.issues,
            })

    return SetupProfile(
        complexity=complexity,
        total_components=total,
        shape=shape,
        by_source=dict(by_source),
        red_flags=red_flags,
        coverage=coverage,
        coverage_gaps=coverage_gaps,
        overlapping_triggers=overlapping[:10],  # Limit to top 10
        plugin_usage={"active": [], "potential": [], "unused": []},  # Computed later
        description_quality=description_issues,  # ADR-007
    )


def read_plugin_enabled_states(
    global_settings: Path,
    project_settings: Path,
) -> dict[str, bool]:
    """Read plugin enabled/disabled states from settings.

    Project settings override global settings.
    Returns dict mapping plugin_id -> enabled (True/False).
    """
    enabled_states: dict[str, bool] = {}

    # Read global settings first
    if global_settings.exists():
        try:
            settings = json.loads(global_settings.read_text())
            for plugin_id, enabled in settings.get("enabledPlugins", {}).items():
                enabled_states[plugin_id] = enabled
        except json.JSONDecodeError as e:
            print(f"Warning: Corrupted {global_settings}: {e}", file=sys.stderr)
        except Exception as e:
            print(f"Warning: Could not read {global_settings}: {e}", file=sys.stderr)

    # Project settings override global
    if project_settings.exists():
        try:
            settings = json.loads(project_settings.read_text())
            for plugin_id, enabled in settings.get("enabledPlugins", {}).items():
                enabled_states[plugin_id] = enabled
        except json.JSONDecodeError as e:
            print(f"Warning: Corrupted {project_settings}: {e}", file=sys.stderr)
        except Exception as e:
            print(f"Warning: Could not read {project_settings}: {e}", file=sys.stderr)

    return enabled_states


def classify_frequency(count: int) -> str:
    """ADR-005: Classify usage count into frequency bands."""
    if count == FREQ_NEVER:
        return "never"
    elif count <= FREQ_RARELY_MAX:
        return "rarely"
    elif count <= FREQ_SOMETIMES_MAX:
        return "sometimes"
    else:
        return "often"


def compute_plugin_usage(
    skills: list[SkillOrAgent],
    agents: list[SkillOrAgent],
    sessions: list,  # list[SessionData]
    potential_matches: list,  # list[MissedOpportunity]
    enabled_states: dict[str, bool] | None = None,
) -> dict[str, list[str] | dict]:
    """Compute plugin usage: active, potential, unused, or disabled_but_matched.

    ADR-005 enhancements:
    - Frequency bands: never/rarely/sometimes/often
    - Component-level tracking in 'component_frequency' dict

    - active: Plugin was used in sessions (skill/agent triggered)
    - potential: Plugin is ENABLED, matched prompts but wasn't triggered
    - unused: Plugin is ENABLED but has no activity at all
    - disabled_but_matched: Plugin is DISABLED but matched prompts (might want to enable)

    Args:
        enabled_states: Dict mapping plugin_id (e.g., "plugin@marketplace") -> enabled bool.
                       If None, assumes all discovered plugins are enabled.
    """
    enabled_states = enabled_states or {}

    def is_plugin_enabled(plugin_name: str) -> bool:
        """Check if plugin is enabled. Unknown plugins assumed enabled (discovered = installed)."""
        # Find full plugin ID (plugin_name@marketplace) in enabled_states
        for plugin_id, enabled in enabled_states.items():
            # Match by plugin name (before @)
            if plugin_id.split("@")[0] == plugin_name:
                return enabled
        # Plugin not in settings = assumed enabled (it's installed/discovered)
        return True

    # Get all plugins from discovery
    all_plugins: set[str] = set()
    plugin_to_components: dict[str, list[str]] = defaultdict(list)
    component_to_plugin: dict[str, str] = {}  # ADR-005: reverse lookup

    for item in skills + agents:
        source = item.source_type
        if source.startswith("plugin:"):
            plugin_name = source.replace("plugin:", "")
            all_plugins.add(plugin_name)
            plugin_to_components[plugin_name].append(item.name)
            component_to_plugin[item.name] = plugin_name

    # ADR-005: Count usage per component (not just presence)
    component_usage_count: dict[str, int] = defaultdict(int)
    active: set[str] = set()

    for session in sessions:
        for skill in session.skills_used:
            component_usage_count[skill] += 1
        for agent in session.agents_used:
            component_usage_count[agent] += 1

    # Determine which plugins are active based on component usage
    for plugin, components in plugin_to_components.items():
        for comp in components:
            # Check if component was used (handle namespaced names like "plugin:name")
            if component_usage_count.get(comp, 0) > 0:
                active.add(plugin)
                break
            # Also check for plugin-prefixed names
            prefixed = f"{plugin}:{comp}"
            if component_usage_count.get(prefixed, 0) > 0:
                active.add(plugin)
                break

    # Check which plugins had potential matches (matched prompts but weren't used)
    matched_but_not_used: set[str] = set()
    for match in potential_matches:
        source = match.matched_item.source_type
        if source.startswith("plugin:"):
            plugin_name = source.replace("plugin:", "")
            if plugin_name not in active:
                matched_but_not_used.add(plugin_name)

    # Classify based on enabled state
    potential: set[str] = set()  # Enabled + matched but not used
    disabled_but_matched: set[str] = set()  # Disabled + matched (might want to enable)

    for plugin in matched_but_not_used:
        if is_plugin_enabled(plugin):
            potential.add(plugin)
        else:
            disabled_but_matched.add(plugin)

    # Unused = enabled plugins with no activity at all
    # Don't include disabled plugins here - they're disabled on purpose
    all_with_no_activity = all_plugins - active - matched_but_not_used
    unused: set[str] = set()
    already_disabled: set[str] = set()

    for plugin in all_with_no_activity:
        if is_plugin_enabled(plugin):
            unused.add(plugin)
        else:
            already_disabled.add(plugin)

    # ADR-005: Build component-level frequency data
    component_frequency: dict[str, dict] = {}
    for plugin, components in plugin_to_components.items():
        plugin_freq: dict[str, str] = {}
        for comp in components:
            count = component_usage_count.get(comp, 0)
            # Also check prefixed name
            if count == 0:
                count = component_usage_count.get(f"{plugin}:{comp}", 0)
            plugin_freq[comp] = classify_frequency(count)
        component_frequency[plugin] = plugin_freq

    return {
        "active": sorted(active),
        "potential": sorted(potential),
        "unused": sorted(unused),
        "disabled_but_matched": sorted(disabled_but_matched),
        "already_disabled": sorted(already_disabled),
        # ADR-005: Component-level frequency data
        "component_frequency": component_frequency,
    }


# =============================================================================
# JSONL Parser
# =============================================================================

def extract_yaml_frontmatter(content: str, source_path: str = "") -> dict:
    """Extract YAML frontmatter from markdown content.

    Falls back to regex extraction if YAML parsing fails, since Claude Code
    uses a more lenient parser that handles unquoted colons in values.
    """
    import yaml

    if not content.startswith("---"):
        return {}

    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}

    try:
        return yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError:
        # Fallback: extract key fields with regex (handles unquoted colons)
        # Claude Code uses a more lenient parser, so we do too
        frontmatter_text = parts[1]
        result = {}

        # Extract name: value (first line match)
        name_match = re.search(r'^name:\s*(.+?)$', frontmatter_text, re.MULTILINE)
        if name_match:
            result["name"] = name_match.group(1).strip().strip('"\'')

        # Extract description: value (may span to next key or end)
        desc_match = re.search(r'^description:\s*(.+?)(?=^[a-z-]+:|$)', frontmatter_text, re.MULTILINE | re.DOTALL)
        if desc_match:
            result["description"] = desc_match.group(1).strip().strip('"\'')

        # Only track as issue if we couldn't extract anything useful
        if not result and source_path:
            _yaml_parse_issues.append(source_path)

        return result


def extract_triggers_from_description(description: str) -> list[str]:
    """Extract trigger phrases from a description string."""
    triggers = []

    trigger_patterns = [
        r'[Tt]riggers?\s+on\s+["\']([^"\']+)["\']',
        r'[Tt]riggers?\s+on\s+([^,.]+(?:,\s*[^,.]+)*)',
        r'[Uu]se\s+(?:this\s+)?(?:skill|agent)\s+when\s+([^.]+)',
        r'[Uu]se\s+for\s+([^.]+)',
    ]

    for pattern in trigger_patterns:
        matches = re.findall(pattern, description)
        for match in matches:
            parts = re.split(r',\s*|\s+or\s+', match)
            triggers.extend([p.strip().strip('"\'') for p in parts if p.strip()])

    quoted = re.findall(r'["\']([^"\']+)["\']', description)
    triggers.extend(quoted)

    return list(set(triggers))


def discover_skills(paths: list[Path]) -> list[SkillOrAgent]:
    """Discover skills from given paths."""
    skills = []
    global_claude_dir = str(CLAUDE_DIR)
    for base_path in paths:
        if not base_path.exists():
            continue

        source_type = "global" if str(base_path).startswith(global_claude_dir) else "project"

        for skill_dir in base_path.iterdir():
            if not skill_dir.is_dir():
                continue

            # Support both SKILL.md and skill.md (case variations)
            skill_md = skill_dir / "SKILL.md"
            if not skill_md.exists():
                skill_md = skill_dir / "skill.md"
            if not skill_md.exists():
                continue

            try:
                content = skill_md.read_text()
                frontmatter = extract_yaml_frontmatter(content, str(skill_md))

                name = frontmatter.get("name", skill_dir.name)
                description = frontmatter.get("description", "")
                triggers = extract_triggers_from_description(description)
                triggers.append(name.lower())

                skills.append(SkillOrAgent(
                    name=name,
                    type="skill",
                    description=description,
                    triggers=triggers,
                    source_path=str(skill_md),
                    source_type=source_type,
                ))
            except Exception as e:
                print(f"Warning: Could not parse {skill_md}: {e}", file=sys.stderr)

    return skills


def discover_agents(paths: list[Path]) -> list[SkillOrAgent]:
    """Discover agents from given paths."""
    agents = []
    global_claude_dir = str(CLAUDE_DIR)
    for base_path in paths:
        if not base_path.exists():
            continue

        source_type = "global" if str(base_path).startswith(global_claude_dir) else "project"

        for agent_file in base_path.glob("*.md"):
            try:
                content = agent_file.read_text()
                frontmatter = extract_yaml_frontmatter(content, str(agent_file))

                name = frontmatter.get("name", agent_file.stem)
                description = frontmatter.get("description", "")

                if not description:
                    lines = content.split("\n")
                    for i, line in enumerate(lines):
                        if line.startswith("#"):
                            for next_line in lines[i+1:]:
                                if next_line.strip() and not next_line.startswith("#"):
                                    description = next_line.strip()
                                    break
                            break

                triggers = extract_triggers_from_description(description)
                triggers.append(name.lower())

                agents.append(SkillOrAgent(
                    name=name,
                    type="agent",
                    description=description[:MAX_DESCRIPTION_LENGTH],
                    triggers=triggers,
                    source_path=str(agent_file),
                    source_type=source_type,
                ))
            except Exception as e:
                print(f"Warning: Could not parse {agent_file}: {e}", file=sys.stderr)

    return agents


def discover_commands(paths: list[Path]) -> list[SkillOrAgent]:
    """Discover commands from given paths."""
    commands = []
    global_claude_dir = str(CLAUDE_DIR)

    for base_path in paths:
        if not base_path.exists():
            continue

        source_type = "global" if str(base_path).startswith(global_claude_dir) else "project"

        for cmd_file in base_path.glob("*.md"):
            try:
                content = cmd_file.read_text()
                frontmatter = extract_yaml_frontmatter(content, str(cmd_file))
                name = frontmatter.get("name", cmd_file.stem)
                description = frontmatter.get("description", "")
                triggers = extract_triggers_from_description(description)
                triggers.append(name.lower())
                triggers.append(f"/{name.lower()}")

                commands.append(SkillOrAgent(
                    name=name,
                    type="command",
                    description=description[:MAX_DESCRIPTION_LENGTH],
                    triggers=triggers,
                    source_path=str(cmd_file),
                    source_type=source_type,
                ))
            except Exception as e:
                print(f"Warning: Could not parse {cmd_file}: {e}", file=sys.stderr)
    return commands


def discover_from_plugins(plugins_cache: Path) -> tuple[list[SkillOrAgent], list[SkillOrAgent], list[SkillOrAgent]]:
    """Discover skills, agents, and commands from installed plugins."""
    skills, agents, commands = [], [], []

    if not plugins_cache.exists():
        return skills, agents, commands

    for marketplace_dir in plugins_cache.iterdir():
        if not marketplace_dir.is_dir() or marketplace_dir.name.startswith("temp_"):
            continue

        for plugin_dir in marketplace_dir.iterdir():
            if not plugin_dir.is_dir():
                continue

            version_dirs = [d for d in plugin_dir.iterdir() if d.is_dir() and not d.name.startswith(".")]
            if not version_dirs:
                continue

            latest_version = max(version_dirs, key=lambda d: d.stat().st_mtime)
            plugin_name = plugin_dir.name
            source_type = f"plugin:{plugin_name}"

            # Skills
            skills_path = latest_version / "skills"
            if skills_path.exists():
                for skill_dir in skills_path.iterdir():
                    if not skill_dir.is_dir():
                        continue
                    # Support both SKILL.md and skill.md
                    skill_md = skill_dir / "SKILL.md"
                    if not skill_md.exists():
                        skill_md = skill_dir / "skill.md"
                    if not skill_md.exists():
                        continue
                        try:
                            content = skill_md.read_text()
                            frontmatter = extract_yaml_frontmatter(content, str(skill_md))
                            name = frontmatter.get("name", skill_dir.name)
                            triggers = extract_triggers_from_description(frontmatter.get("description", ""))
                            triggers.append(name.lower())
                            skills.append(SkillOrAgent(
                                name=name,
                                type="skill",
                                description=frontmatter.get("description", ""),
                                triggers=triggers,
                                source_path=str(skill_md),
                                source_type=source_type,
                            ))
                        except Exception as e:
                            print(f"Warning: Could not parse {skill_md}: {e}", file=sys.stderr)

            # Agents
            agents_path = latest_version / "agents"
            if agents_path.exists():
                for agent_file in agents_path.glob("*.md"):
                    try:
                        content = agent_file.read_text()
                        frontmatter = extract_yaml_frontmatter(content, str(agent_file))
                        name = frontmatter.get("name", agent_file.stem)
                        triggers = extract_triggers_from_description(frontmatter.get("description", ""))
                        triggers.append(name.lower())
                        agents.append(SkillOrAgent(
                            name=name,
                            type="agent",
                            description=frontmatter.get("description", "")[:MAX_DESCRIPTION_LENGTH],
                            triggers=triggers,
                            source_path=str(agent_file),
                            source_type=source_type,
                        ))
                    except Exception as e:
                        print(f"Warning: Could not parse {agent_file}: {e}", file=sys.stderr)

            # Commands
            commands_path = latest_version / "commands"
            if commands_path.exists():
                for cmd_file in commands_path.glob("*.md"):
                    try:
                        content = cmd_file.read_text()
                        frontmatter = extract_yaml_frontmatter(content, str(cmd_file))
                        name = frontmatter.get("name", cmd_file.stem)
                        triggers = extract_triggers_from_description(frontmatter.get("description", ""))
                        triggers.append(name.lower())
                        triggers.append(f"/{name.lower()}")
                        commands.append(SkillOrAgent(
                            name=name,
                            type="command",
                            description=frontmatter.get("description", "")[:MAX_DESCRIPTION_LENGTH],
                            triggers=triggers,
                            source_path=str(cmd_file),
                            source_type=source_type,
                        ))
                    except Exception as e:
                        print(f"Warning: Could not parse {cmd_file}: {e}", file=sys.stderr)

    return skills, agents, commands


def discover_hooks(settings_paths: list[tuple[Path, str]], plugins_cache: Path) -> list[Hook]:
    """Discover hooks from settings files and plugins.

    Args:
        settings_paths: List of (path, source_type) tuples
        plugins_cache: Path to plugins cache directory
    """
    hooks = []

    # Discover from settings files
    for settings_path, source_type in settings_paths:
        if not settings_path.exists():
            continue

        try:
            settings = json.loads(settings_path.read_text())
            hooks_config = settings.get("hooks", {})

            for event_type, matchers in hooks_config.items():
                if isinstance(matchers, dict):
                    # Format: {"Bash": "command"} or {"Bash": [...]}
                    for matcher, hook_def in matchers.items():
                        if isinstance(hook_def, str):
                            hooks.append(Hook(
                                event_type=event_type,
                                matcher=matcher,
                                command=hook_def,
                                source_path=str(settings_path),
                                source_type=source_type,
                            ))
                        elif isinstance(hook_def, list):
                            for h in hook_def:
                                if isinstance(h, dict):
                                    hooks.append(Hook(
                                        event_type=event_type,
                                        matcher=matcher,
                                        command=h.get("command", ""),
                                        source_path=str(settings_path),
                                        source_type=source_type,
                                        timeout=h.get("timeout"),
                                    ))
                elif isinstance(matchers, list):
                    # Format: [{"matcher": "Bash", "hooks": [...]}]
                    for matcher_group in matchers:
                        matcher = matcher_group.get("matcher", "*")
                        for h in matcher_group.get("hooks", []):
                            if isinstance(h, dict):
                                hooks.append(Hook(
                                    event_type=event_type,
                                    matcher=matcher,
                                    command=h.get("command", ""),
                                    source_path=str(settings_path),
                                    source_type=source_type,
                                    timeout=h.get("timeout"),
                                ))
        except (json.JSONDecodeError, Exception) as e:
            print(f"Warning: Could not parse hooks from {settings_path}: {e}", file=sys.stderr)

    # Discover from plugins
    if plugins_cache.exists():
        for marketplace_dir in plugins_cache.iterdir():
            if not marketplace_dir.is_dir() or marketplace_dir.name.startswith("temp_"):
                continue

            for plugin_dir in marketplace_dir.iterdir():
                if not plugin_dir.is_dir():
                    continue

                version_dirs = [d for d in plugin_dir.iterdir() if d.is_dir() and not d.name.startswith(".")]
                if not version_dirs:
                    continue

                latest_version = max(version_dirs, key=lambda d: d.stat().st_mtime)
                plugin_json = latest_version / ".claude-plugin" / "plugin.json"

                if not plugin_json.exists():
                    plugin_json = latest_version / "plugin.json"

                if plugin_json.exists():
                    try:
                        plugin_config = json.loads(plugin_json.read_text())
                        plugin_name = plugin_config.get("name", plugin_dir.name)
                        hooks_config = plugin_config.get("hooks", {})

                        for event_type, matchers in hooks_config.items():
                            if isinstance(matchers, list):
                                for matcher_group in matchers:
                                    matcher = matcher_group.get("matcher", "*")
                                    for h in matcher_group.get("hooks", []):
                                        if isinstance(h, dict):
                                            hooks.append(Hook(
                                                event_type=event_type,
                                                matcher=matcher,
                                                command=h.get("command", ""),
                                                source_path=str(plugin_json),
                                                source_type=f"plugin:{plugin_name}",
                                                timeout=h.get("timeout"),
                                            ))
                    except (json.JSONDecodeError, Exception) as e:
                        print(f"Warning: Could not parse hooks from {plugin_json}: {e}", file=sys.stderr)

    return hooks


def parse_claude_md_files(paths: list[Path]) -> dict:
    """Parse CLAUDE.md files and return structured data."""
    result = {
        "files_found": [],
        "files_missing": [],
        "content": {},
        "sections": [],
    }

    for path in paths:
        if path.exists():
            result["files_found"].append(str(path))
            content = path.read_text()
            result["content"][str(path)] = content

            # Extract section headers
            for line in content.split("\n"):
                if line.startswith("## "):
                    section = line[3:].strip()
                    if section not in result["sections"]:
                        result["sections"].append(section)
        else:
            result["files_missing"].append(str(path))

    return result


def _is_system_prompt(content: str) -> bool:
    """Filter out system-generated prompts."""
    if content.startswith("Base directory for this skill:"):
        return True
    if content.startswith("[TRACE-ID:"):
        return True
    if "<command-message>" in content or "<command-name>" in content:
        return True
    return False


def _summarize_tool_input(tool_name: str, tool_input: dict) -> str:
    """Extract meaningful context from tool input."""
    if tool_name == "Bash":
        cmd = tool_input.get("command", "")
        return cmd[:MAX_TOOL_INPUT_LENGTH] if cmd else ""
    if tool_name in ("Edit", "Write", "Read"):
        return tool_input.get("file_path", "")[:MAX_TOOL_INPUT_LENGTH]
    if tool_name == "Skill":
        return tool_input.get("skill", "")
    if tool_name == "Task":
        agent = tool_input.get("subagent_type", "")
        desc = tool_input.get("description", "")
        return f"{agent}: {desc}"[:MAX_TOOL_INPUT_LENGTH] if desc else agent
    if tool_name == "Grep":
        pattern = tool_input.get("pattern", "")
        return f"pattern: {pattern}"[:MAX_TOOL_INPUT_LENGTH]
    if tool_name == "Glob":
        pattern = tool_input.get("pattern", "")
        return f"glob: {pattern}"[:MAX_TOOL_INPUT_LENGTH]
    return str(tool_input)[:MAX_TOOL_INPUT_LENGTH]


def detect_outcome(tool_name: str, result: str) -> str:
    """Detect outcome from tool result content.

    NOTE: This function is intentionally duplicated in generate_session_summary.py.
    Both scripts use 'uv run --script' for standalone operation without dependencies.
    Keep implementations in sync when making changes (ADR-003).
    """
    result_lower = result.lower()

    if tool_name == "Bash":
        if "exit code: 0" in result_lower or "succeeded" in result_lower:
            return "success"
        if "exit code:" in result_lower:
            return "failure"
        if "timeout" in result_lower:
            return "failure"
        if any(kw in result_lower for kw in ["error:", "failed", "traceback", "permission denied"]):
            return "failure"
        return "success"

    if tool_name in ("Edit", "Write", "NotebookEdit"):
        if any(kw in result_lower for kw in ["permission denied", "file not found", "no such file",
                                              "old_string not found", "not unique", "error"]):
            return "failure"
        return "success"

    if "error" in result_lower or "failed" in result_lower:
        return "failure"
    return "success"


def resolve_project_path(projects_dir: Path, project_path: str) -> tuple[Path | None, list[Path]]:
    """Resolve project path to actual folder, with fuzzy matching.

    Returns (resolved_path, matches) where:
    - resolved_path is the single matching folder or None
    - matches is list of all matching folders (for error reporting)
    """
    # Try exact match first (full path like /Users/foo/project)
    project_folder = project_path.replace("/", "-")
    project_dir = projects_dir / project_folder
    if project_dir.exists():
        return project_dir, [project_dir]

    # Try fuzzy match: find folders ending with the project name
    if not projects_dir.exists():
        return None, []

    matches = [
        d for d in projects_dir.iterdir()
        if d.is_dir() and d.name.endswith(f"-{project_path}")
    ]

    if len(matches) == 1:
        return matches[0], matches
    return None, matches


def find_project_sessions(projects_dir: Path, project_dir: Path, max_sessions: int) -> list[Path]:
    """Find session files for a project."""
    if not project_dir.exists():
        return []

    session_files = sorted(
        project_dir.glob("*.jsonl"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )

    return session_files[:max_sessions]


def parse_session_file(session_path: Path) -> SessionData:
    """Parse a session JSONL file with outcome and compaction tracking.

    ADR-026: Tracks parse success rate and warns if schema may have changed.
    ADR-047: Tracks session date and calculates recency weight.
    """
    # ADR-047: Get session date from file modification time
    session_date = datetime.fromtimestamp(session_path.stat().st_mtime)
    recency_weight = calculate_recency_weight(session_date)

    session_data = SessionData(
        session_id=session_path.stem[:8],
        session_date=session_date,
        recency_weight=recency_weight,
    )
    # ADR-006: Include timestamp for duration tracking
    pending_tools: dict[str, tuple[str, dict, Optional[float]]] = {}  # tool_use_id -> (tool_name, tool_input, timestamp)
    awaiting_followup: list[tuple[str, dict, Optional[int], str]] = []  # (tool_name, tool_input, duration_ms, position)

    try:
        lines = session_path.read_text().strip().split("\n")
        session_data.entries_total = len(lines)

        for line_num, line in enumerate(lines, 1):
            try:
                entry = json.loads(line)
                session_data.entries_parsed += 1
                entry_type = entry.get("type")

                # Detect compactions
                if entry_type == "system" and entry.get("subtype") == "compact_boundary":
                    session_data.compaction_count += 1
                    continue

                if entry_type == "user":
                    message = entry.get("message", {})
                    content = message.get("content", "")

                    # Extract user text from message (for followup capture)
                    user_text = ""
                    is_interruption = False

                    if isinstance(content, str):
                        if "[Request interrupted by user]" in content:
                            is_interruption = True
                        elif content.strip() and not _is_system_prompt(content):
                            user_text = content
                            session_data.prompts.append(content)
                    elif isinstance(content, list):
                        for item in content:
                            if isinstance(item, dict):
                                item_type = item.get("type")
                                if item_type == "text":
                                    text = item.get("text", "")
                                    if "[Request interrupted by user]" in text:
                                        is_interruption = True
                                    elif not _is_system_prompt(text):
                                        if not user_text:  # Take first non-system text
                                            user_text = text
                                        session_data.prompts.append(text)
                                elif item_type == "tool_result":
                                    # Tool results are in user messages
                                    tool_use_id = item.get("tool_use_id", "")
                                    result = item.get("content", "")

                                    # Get tool info and remove from pending
                                    tool_info = pending_tools.pop(tool_use_id, ("unknown", {}, None))
                                    tool_name = tool_info[0]

                                    if isinstance(result, str):
                                        outcome = detect_outcome(tool_name, result)
                                        if outcome == "success":
                                            session_data.success_count += 1
                                        else:
                                            session_data.failure_count += 1

                    # Handle interruption - capture which tools were pending
                    if is_interruption:
                        session_data.interrupted_count += 1
                        # ADR-006: Get current timestamp for duration calculation
                        interrupt_ts = entry.get("timestamp")
                        # Mark all pending tools as interrupted, awaiting followup
                        is_first = True
                        for tool_use_id, (tool_name, tool_input, start_ts) in pending_tools.items():
                            duration_ms = None
                            if start_ts and interrupt_ts:
                                duration_ms = int((interrupt_ts - start_ts) * 1000)
                            # ADR-006: First pending tool is "primary", rest are "collateral"
                            position = "primary" if is_first else "collateral"
                            is_first = False
                            awaiting_followup.append((tool_name, tool_input, duration_ms, position))
                        pending_tools.clear()

                    # If we have tools awaiting followup and user said something, capture it
                    elif user_text and awaiting_followup:
                        for tool_name, tool_input, duration_ms, position in awaiting_followup:
                            followup = user_text[:MAX_PROMPT_LENGTH]
                            session_data.interrupted_tools.append(InterruptedTool(
                                tool_name=tool_name,
                                tool_input=tool_input,
                                followup_message=followup,
                                duration_ms=duration_ms,
                                position=position,
                                category=classify_interruption(tool_name, duration_ms, followup),
                            ))
                        awaiting_followup.clear()

                elif entry_type == "assistant":
                    message = entry.get("message", {})
                    content = message.get("content", [])

                    if isinstance(content, list):
                        for item in content:
                            if isinstance(item, dict) and item.get("type") == "tool_use":
                                tool_name = item.get("name", "")
                                tool_use_id = item.get("id", "")
                                tool_input = item.get("input", {})

                                # Track pending tools with full info (ADR-006: include timestamp)
                                if tool_use_id:
                                    entry_ts = entry.get("timestamp")
                                    pending_tools[tool_use_id] = (tool_name, tool_input, entry_ts)

                                if tool_name == "Skill":
                                    skill = tool_input.get("skill", "")
                                    if skill:
                                        session_data.skills_used.add(skill)

                                elif tool_name == "Task":
                                    agent = tool_input.get("subagent_type", "")
                                    if agent:
                                        session_data.agents_used.add(agent)

                                else:
                                    session_data.tools_used.add(tool_name)

            except json.JSONDecodeError as e:
                session_data.parsing_errors.append({"line": line_num, "error": str(e)})
                continue

        # Remaining pending tools at session end are interrupted (no followup available)
        is_first = True
        for tool_use_id, (tool_name, tool_input, start_ts) in pending_tools.items():
            session_data.interrupted_count += 1
            position = "primary" if is_first else "collateral"
            is_first = False
            session_data.interrupted_tools.append(InterruptedTool(
                tool_name=tool_name,
                tool_input=tool_input,
                followup_message="[session ended]",
                duration_ms=None,  # Can't calculate without end timestamp
                position=position,
                category="session_abandon",  # ADR-006
            ))

    except Exception as e:
        print(f"Warning: Could not parse {session_path}: {e}", file=sys.stderr)

    # ADR-026: Check parse success rate and warn if below threshold
    if session_data.entries_total > 0:
        success_rate = session_data.entries_parsed / session_data.entries_total
        if success_rate < MIN_PARSE_SUCCESS_RATE:
            print(
                f"WARNING: Parse success rate {success_rate:.1%} below {MIN_PARSE_SUCCESS_RATE:.0%} "
                f"for {session_path.name}. JSONL schema may have changed. See ADR-026.",
                file=sys.stderr
            )

    return session_data


def find_matches(prompt: str, items: list[SkillOrAgent], min_triggers: int = 2) -> list[tuple[SkillOrAgent, list[str]]]:
    """Find skills/agents that match a prompt based on triggers.

    ADR-001 improvements:
    - Unified threshold (>= 3 chars)
    - 3-char triggers require UPPERCASE (e.g., TDD, API, DDD)
    - Common words are blocked from matching
    """
    matches = []
    prompt_lower = prompt.lower()

    for item in items:
        matched_triggers = []
        for trigger in item.triggers:
            trigger_lower = trigger.lower()

            # Skip triggers below minimum length
            if len(trigger_lower) < MIN_TRIGGER_LENGTH:
                continue

            # 3-char triggers: require UPPERCASE in original (ADR-001)
            # This allows TDD, API, DDD but not "the", "for", etc.
            if len(trigger_lower) == 3:
                if not trigger.isupper():
                    continue
                if trigger_lower in COMMON_WORD_BLOCKLIST:
                    continue

            # 4-char triggers: skip common words
            if len(trigger_lower) == 4 and trigger_lower in COMMON_WORD_BLOCKLIST:
                continue

            # Match using word boundaries
            if re.search(r'\b' + re.escape(trigger_lower) + r'\b', prompt_lower):
                matched_triggers.append(trigger)

        name_matched = item.name.lower() in [t.lower() for t in matched_triggers]
        if len(matched_triggers) >= min_triggers or name_matched:
            matches.append((item, matched_triggers))

    return matches


def analyze_jsonl(
    skills: list[SkillOrAgent],
    agents: list[SkillOrAgent],
    commands: list[SkillOrAgent],
    sessions: list[SessionData],
) -> tuple[list[MissedOpportunity], dict]:
    """Analyze sessions for missed opportunities."""
    missed = []
    stats = {
        "total_sessions": len(sessions),
        "total_prompts": sum(len(s.prompts) for s in sessions),
        "skills_used": defaultdict(int),
        "agents_used": defaultdict(int),
        "commands_used": defaultdict(int),
        "missed_skills": defaultdict(int),
        "missed_agents": defaultdict(int),
        "missed_commands": defaultdict(int),
        # New outcome stats
        "total_success": sum(s.success_count for s in sessions),
        "total_failure": sum(s.failure_count for s in sessions),
        "total_interrupted": sum(s.interrupted_count for s in sessions),
        "total_compactions": sum(s.compaction_count for s in sessions),
    }

    all_items = skills + agents + commands

    for session in sessions:
        for skill in session.skills_used:
            stats["skills_used"][skill] += 1
        for agent in session.agents_used:
            stats["agents_used"][agent] += 1

        for prompt in session.prompts:
            matches = find_matches(prompt, all_items)

            for item, triggers in matches:
                was_used = False
                if item.type == "skill" and item.name in session.skills_used:
                    was_used = True
                elif item.type == "agent" and item.name in session.agents_used:
                    was_used = True
                elif item.type == "command":
                    # Commands are slash commands - check if /command was in the prompt
                    was_used = f"/{item.name}" in prompt.lower()

                if not was_used:
                    # ADR-046: Calculate confidence and evidence
                    confidence, evidence = calculate_match_confidence(item, triggers, prompt)
                    missed.append(MissedOpportunity(
                        prompt=prompt,
                        session_id=session.session_id,
                        matched_item=item,
                        matched_triggers=triggers,
                        confidence=confidence,
                        evidence=evidence,
                        # ADR-047: Temporal data
                        session_date=session.session_date,
                        recency_weight=session.recency_weight,
                    ))

                    if item.type == "skill":
                        stats["missed_skills"][item.name] += 1
                    elif item.type == "agent":
                        stats["missed_agents"][item.name] += 1
                    else:
                        stats["missed_commands"][item.name] += 1

    return missed, stats


def generate_analysis_json(
    skills: list[SkillOrAgent],
    agents: list[SkillOrAgent],
    commands: list[SkillOrAgent],
    hooks: list[Hook],
    sessions: list[SessionData],
    jsonl_stats: dict,
    claude_md: dict,
    setup_profile: SetupProfile,
    missed: list[MissedOpportunity],  # ADR-046: Include for confidence data
    feedback: dict,  # ADR-048: User feedback
) -> dict:
    """Generate rich JSON output for agent interpretation."""

    # Compute outcome stats
    total_outcomes = jsonl_stats["total_success"] + jsonl_stats["total_failure"] + jsonl_stats["total_interrupted"]
    success_rate = (jsonl_stats["total_success"] / total_outcomes * 100) if total_outcomes > 0 else 0

    # Compute avg tools per compaction
    total_tools = sum(len(s.tools_used) + len(s.skills_used) + len(s.agents_used) for s in sessions)
    avg_tools_per_compaction = (total_tools / jsonl_stats["total_compactions"]) if jsonl_stats["total_compactions"] > 0 else 0

    # ADR-026: Compute schema health metadata
    entries_total = sum(s.entries_total for s in sessions)
    entries_parsed = sum(s.entries_parsed for s in sessions)
    parsing_errors_count = sum(len(s.parsing_errors) for s in sessions)
    parse_success_rate = entries_parsed / entries_total if entries_total > 0 else 1.0

    # ADR-046: Compute confidence distribution for potential matches
    high_conf_count = sum(1 for m in missed if m.confidence >= CONFIDENCE_HIGH)
    med_conf_count = sum(1 for m in missed if CONFIDENCE_MEDIUM <= m.confidence < CONFIDENCE_HIGH)
    low_conf_count = sum(1 for m in missed if m.confidence < CONFIDENCE_MEDIUM)

    # ADR-050: Assess data sufficiency
    data_sufficiency = assess_data_sufficiency(sessions, missed)

    # ADR-053: Compute quality metrics
    quality_metrics = compute_quality_metrics(sessions, missed, feedback)

    # ADR-054: Pre-compute deterministic findings
    pre_computed = compute_pre_computed_findings(skills, agents, commands, sessions, missed, setup_profile)

    return {
        "_schema": {
            "description": "Claude Code usage analysis data for agent interpretation",
            "version": "3.10",  # Added invalid_yaml_files to pre_computed_findings
            "sections": {
                "discovery": "All available skills, agents, commands, and hooks discovered from global, project, and plugin sources",
                "sessions": "Parsed session data showing what was actually used",
                "stats": "Aggregated statistics on usage, outcomes, interruptions with followup context, and missed opportunities",
                "data_sufficiency": "ADR-050: Statistical sufficiency assessment for pattern detection",
                "quality_metrics": "ADR-053: Analysis quality metrics for self-evaluation",
                "pre_computed_findings": "ADR-054: Deterministic findings (100% certain, no LLM needed)",
                "potential_matches_detailed": "ADR-046: Detailed potential matches with confidence scores and evidence",
                "feedback": "ADR-048: User feedback on previous recommendations (accepted/dismissed)",
                "claude_md": "Content and structure of CLAUDE.md configuration files",
                "setup_profile": "Computed setup profile with complexity, shape, red flags, and coverage gaps",
            },
            # ADR-026: Schema health metadata
            "jsonl_parse_stats": {
                "entries_total": entries_total,
                "entries_parsed": entries_parsed,
                "parsing_errors_count": parsing_errors_count,
                "parse_success_rate": round(parse_success_rate, 3),
                "min_threshold": MIN_PARSE_SUCCESS_RATE,
                "healthy": parse_success_rate >= MIN_PARSE_SUCCESS_RATE,
            },
        },

        "discovery": {
            "skills": [
                {
                    "name": s.name,
                    "description": s.description,
                    "triggers": s.triggers,
                    "source": s.source_type,
                }
                for s in skills
            ],
            "agents": [
                {
                    "name": a.name,
                    "description": a.description,
                    "triggers": a.triggers,
                    "source": a.source_type,
                }
                for a in agents
            ],
            "commands": [
                {
                    "name": c.name,
                    "description": c.description,
                    "triggers": c.triggers,
                    "source": c.source_type,
                }
                for c in commands
            ],
            "hooks": [
                {
                    "event_type": h.event_type,
                    "matcher": h.matcher,
                    "command": h.command[:MAX_TOOL_INPUT_LENGTH],
                    "source": h.source_type,
                }
                for h in hooks
            ],
            "totals": {
                "skills": len(skills),
                "agents": len(agents),
                "commands": len(commands),
                "hooks": len(hooks),
            },
        },

        "sessions": {
            "count": len(sessions),
            # ADR-047: Include temporal data per session
            "temporal": [
                {
                    "session_id": s.session_id,
                    "date": s.session_date.isoformat() if s.session_date else None,
                    "age_days": (datetime.now() - s.session_date).days if s.session_date else None,
                    "recency_weight": round(s.recency_weight, 2),
                }
                for s in sessions
            ],
            "prompts": [
                {
                    "session_id": s.session_id,
                    "text": p[:MAX_PROMPT_LENGTH],
                }
                for s in sessions
                for p in s.prompts[:5]
            ][:50],
        },

        "stats": {
            "total_sessions": jsonl_stats["total_sessions"],
            "total_prompts": jsonl_stats["total_prompts"],
            "skills_used": dict(jsonl_stats["skills_used"]),
            "agents_used": dict(jsonl_stats["agents_used"]),
            "commands_used": dict(jsonl_stats.get("commands_used", {})),
            "potential_matches": {
                "skills": dict(jsonl_stats["missed_skills"]),
                "agents": dict(jsonl_stats["missed_agents"]),
                "commands": dict(jsonl_stats.get("missed_commands", {})),
            },
            "outcomes": {
                "success": jsonl_stats["total_success"],
                "failure": jsonl_stats["total_failure"],
                "interrupted": jsonl_stats["total_interrupted"],
                "success_rate": round(success_rate, 1),
            },
            "compactions": {
                "total": jsonl_stats["total_compactions"],
                "avg_tools_per": round(avg_tools_per_compaction, 1),
            },
            "interruptions": [
                {
                    "tool": it.tool_name,
                    "context": _summarize_tool_input(it.tool_name, it.tool_input),
                    "followup": it.followup_message,
                }
                for s in sessions
                for it in s.interrupted_tools
            ][:20],  # Limit to 20 most recent
        },

        # ADR-050: Statistical significance assessment
        "data_sufficiency": data_sufficiency,

        # ADR-053: Analysis quality metrics
        "quality_metrics": quality_metrics,

        # ADR-054: Pre-computed deterministic findings
        "pre_computed_findings": pre_computed,

        # ADR-046 + ADR-047 + ADR-049: Detailed potential matches with limits
        "potential_matches_detailed": {
            "summary": {
                "total": len(missed),
                "high_confidence": high_conf_count,
                "medium_confidence": med_conf_count,
                "low_confidence": low_conf_count,
                # ADR-047: Recency-weighted summary
                "recent_matches": sum(1 for m in missed if m.recency_weight >= 0.5),
                "stale_matches": sum(1 for m in missed if m.recency_weight < 0.5),
            },
            # ADR-049: Alert fatigue limits
            "limits": {
                "max_per_category": MAX_FINDINGS_PER_CATEGORY,
                "max_total": MAX_TOTAL_FINDINGS,
                "showing": min(len(missed), MAX_FINDINGS_DETAILED),
                "hidden": max(0, len(missed) - MAX_FINDINGS_DETAILED),
            },
            # ADR-049: Findings by type (limited per category)
            "by_type": {
                "skill": sum(1 for m in missed if m.matched_item.type == "skill"),
                "agent": sum(1 for m in missed if m.matched_item.type == "agent"),
                "command": sum(1 for m in missed if m.matched_item.type == "command"),
            },
            # Sort by combined score (confidence * recency), limit to MAX_FINDINGS_DETAILED
            "matches": [
                {
                    "component": m.matched_item.name,
                    "type": m.matched_item.type,
                    "source": m.matched_item.source_type,
                    "prompt_preview": m.prompt[:100],
                    "session_id": m.session_id,
                    "confidence": round(m.confidence, 2),
                    "evidence": m.evidence,
                    "matched_triggers": m.matched_triggers,
                    # ADR-047: Recency data
                    "recency_weight": round(m.recency_weight, 2),
                    "age_days": (datetime.now() - m.session_date).days if m.session_date else None,
                    "priority_score": round(m.confidence * m.recency_weight, 2),  # Combined score
                    # ADR-048: Finding hash for feedback tracking
                    "finding_hash": m.finding_hash,
                }
                for m in sorted(missed, key=lambda x: -(x.confidence * x.recency_weight))[:MAX_FINDINGS_DETAILED]
            ],
        },

        # ADR-048: User feedback data
        "feedback": {
            "has_feedback": bool(feedback.get("dismissed") or feedback.get("accepted")),
            "acceptance_rates": compute_acceptance_rate(feedback),
            "dismissed_count": len(feedback.get("dismissed", [])),
            "accepted_count": len(feedback.get("accepted", [])),
            "dismissed_hashes": list(get_dismissed_hashes(feedback)),
        },

        "claude_md": claude_md,

        "setup_profile": {
            "complexity": setup_profile.complexity,
            "total_components": setup_profile.total_components,
            "shape": setup_profile.shape,
            "by_source": setup_profile.by_source,
            "red_flags": setup_profile.red_flags,
            "coverage": setup_profile.coverage,
            "coverage_gaps": setup_profile.coverage_gaps,
            "overlapping_triggers": setup_profile.overlapping_triggers,
            "plugin_usage": setup_profile.plugin_usage,
            "description_quality": setup_profile.description_quality,  # ADR-007
        },
    }


# =============================================================================
# Output Formatters
# =============================================================================

def progress_bar(value: float, max_value: float, width: int = 10) -> str:
    """Create ASCII progress bar."""
    if max_value == 0:
        return "░" * width
    filled = int((value / max_value) * width)
    return "█" * filled + "░" * (width - filled)


def print_table(
    jsonl_stats: dict,
    missed: list[MissedOpportunity],
    verbose: bool,
):
    """Print collected data as formatted table."""
    print("\n" + "=" * 80)
    print("USAGE DATA COLLECTED")
    print("=" * 80)

    print(f"\nSessions analyzed: {jsonl_stats['total_sessions']}")
    print(f"Prompts analyzed: {jsonl_stats['total_prompts']}")
    print(f"Potential matches found: {len(missed)}")

    # Outcome stats
    total = jsonl_stats["total_success"] + jsonl_stats["total_failure"] + jsonl_stats["total_interrupted"]
    if total > 0:
        success_rate = jsonl_stats["total_success"] / total * 100
        print(f"\nOutcomes: ✓{jsonl_stats['total_success']} ✗{jsonl_stats['total_failure']} ⏹{jsonl_stats['total_interrupted']} ({success_rate:.1f}% success)")
        print(f"Compactions: {jsonl_stats['total_compactions']}")

    # JSONL usage stats
    if jsonl_stats["skills_used"]:
        print("\n--- Skills Used ---")
        for skill, count in sorted(jsonl_stats["skills_used"].items(), key=lambda x: -x[1]):
            print(f"  {skill}: {count}")

    if jsonl_stats["agents_used"]:
        print("\n--- Agents Used ---")
        for agent, count in sorted(jsonl_stats["agents_used"].items(), key=lambda x: -x[1]):
            print(f"  {agent}: {count}")

    # Potential matches (detailed)
    if missed and verbose:
        print("\n--- Potential Matches (detailed) ---")
        by_item = defaultdict(list)
        for m in missed:
            by_item[f"{m.matched_item.type}:{m.matched_item.name}"].append(m)

        for key, items in sorted(by_item.items(), key=lambda x: -len(x[1]))[:10]:
            item_type, item_name = key.split(":", 1)
            print(f"\n  [{item_type.upper()}] {item_name} ({len(items)} matches)")
            for m in items[:3]:
                prompt_preview = m.prompt[:80].replace("\n", " ")
                print(f"    Session {m.session_id}: \"{prompt_preview}...\"")

    # YAML parsing issues
    if _yaml_parse_issues:
        print("\n--- Files with Invalid YAML Frontmatter ---")
        for path in _yaml_parse_issues[:10]:
            print(f"  ⚠ {path}")
        if len(_yaml_parse_issues) > 10:
            print(f"  ... and {len(_yaml_parse_issues) - 10} more")

    print("\n" + "=" * 80)
    print("Use usage-insights-agent to analyze this data for actionable insights.")
    print("=" * 80)


def print_dashboard(jsonl_stats: dict):
    """Print dashboard-style output with ASCII charts."""
    print("\n┌" + "─" * 78 + "┐")
    print("│" + " USAGE DATA DASHBOARD ".center(78) + "│")
    print("└" + "─" * 78 + "┘")

    # Outcome stats
    total = jsonl_stats["total_success"] + jsonl_stats["total_failure"] + jsonl_stats["total_interrupted"]
    if total > 0:
        success_rate = jsonl_stats["total_success"] / total * 100
        print("\n┌─ Outcomes " + "─" * 65 + "┐")
        print(f"│ Success:     {progress_bar(jsonl_stats['total_success'], total, 20)} {jsonl_stats['total_success']:4} ({success_rate:.1f}%)          │")
        print(f"│ Failure:     {progress_bar(jsonl_stats['total_failure'], total, 20)} {jsonl_stats['total_failure']:4}                      │")
        print(f"│ Interrupted: {progress_bar(jsonl_stats['total_interrupted'], total, 20)} {jsonl_stats['total_interrupted']:4}                      │")
        print(f"│ Compactions: {jsonl_stats['total_compactions']:4}                                                    │")
        print("└" + "─" * 76 + "┘")

    # Summary
    print("\n┌─ Summary " + "─" * 66 + "┐")
    print(f"│ Sessions: {jsonl_stats['total_sessions']:4} | Prompts: {jsonl_stats['total_prompts']:5} | Skills used: {len(jsonl_stats['skills_used']):3} | Agents used: {len(jsonl_stats['agents_used']):3}    │")
    print("└" + "─" * 76 + "┘")

    # YAML issues
    if _yaml_parse_issues:
        print("\n┌─ Config Issues " + "─" * 60 + "┐")
        print(f"│ {len(_yaml_parse_issues)} file(s) with invalid YAML frontmatter" + " " * (76 - 35 - len(str(len(_yaml_parse_issues)))) + "│")
        print("└" + "─" * 76 + "┘")

    print("\nUse usage-insights-agent to analyze this data for actionable insights.")
    print()


# =============================================================================
# Quick Stats (uses session summaries)
# =============================================================================

def analyze_session_summaries(summary_dir: Path, days: int = 14) -> dict:
    """Analyze session summaries for quick stats."""
    cutoff = datetime.now() - timedelta(days=days)
    stats = {
        "sessions": 0,
        "total_tools": 0,
        "total_success": 0,
        "total_failure": 0,
        "total_compactions": 0,
        "tool_breakdown": defaultdict(int),
        "stages_seen": defaultdict(int),
        "by_project": defaultdict(lambda: {"sessions": 0, "success": 0, "failure": 0}),
    }

    if not summary_dir.exists():
        return stats

    for summary_file in summary_dir.glob("*.json"):
        try:
            date_str = summary_file.name[:10]
            file_date = datetime.strptime(date_str, "%Y-%m-%d")

            if file_date < cutoff:
                continue

            summary = json.loads(summary_file.read_text())
            stats["sessions"] += 1
            stats["total_tools"] += summary.get("total_tools", 0)
            stats["total_success"] += summary.get("outcomes", {}).get("success", 0)
            stats["total_failure"] += summary.get("outcomes", {}).get("failure", 0)
            stats["total_compactions"] += summary.get("compactions", 0)

            for tool, count in summary.get("tool_breakdown", {}).items():
                stats["tool_breakdown"][tool] += count

            for stage in summary.get("stages_visited", []):
                stats["stages_seen"][stage] += 1

            project = summary.get("project", "unknown")
            stats["by_project"][project]["sessions"] += 1
            stats["by_project"][project]["success"] += summary.get("outcomes", {}).get("success", 0)
            stats["by_project"][project]["failure"] += summary.get("outcomes", {}).get("failure", 0)

        except (json.JSONDecodeError, ValueError):
            continue

    return stats


def print_quick_stats(stats: dict, days: int):
    """Print quick stats from session summaries."""
    print("\n" + "=" * 80)
    print(f"QUICK STATS (Last {days} days)")
    print("=" * 80)

    if stats["sessions"] == 0:
        print("\nNo session summaries found. Run some sessions first!")
        print("(Summaries are saved when sessions end)")
        return

    total = stats["total_success"] + stats["total_failure"]
    success_rate = (stats["total_success"] / total * 100) if total > 0 else 0

    print(f"\nSessions: {stats['sessions']}")
    print(f"Total tools: {stats['total_tools']}")
    print(f"Success rate: {success_rate:.1f}% ({stats['total_success']}/{total})")
    print(f"Compactions: {stats['total_compactions']}")

    if stats["tool_breakdown"]:
        print("\n--- Tool Usage ---")
        for tool, count in sorted(stats["tool_breakdown"].items(), key=lambda x: -x[1])[:10]:
            print(f"  {tool}: {count}")

    if stats["stages_seen"]:
        print("\n--- Workflow Stages ---")
        for stage, count in sorted(stats["stages_seen"].items(), key=lambda x: -x[1]):
            print(f"  {stage}: {count} sessions")

    if stats["by_project"]:
        print("\n--- By Project ---")
        for project, data in sorted(stats["by_project"].items(), key=lambda x: -x[1]["sessions"])[:5]:
            total_p = data["success"] + data["failure"]
            rate = (data["success"] / total_p * 100) if total_p > 0 else 0
            print(f"  {project}: {data['sessions']} sessions, {rate:.0f}% success")

    print("\n" + "=" * 80)


# =============================================================================
# Main
# =============================================================================

def main():
    _yaml_parse_issues.clear()  # Reset for fresh run
    parser = argparse.ArgumentParser(description="Collect Claude Code usage data for analysis")
    parser.add_argument("--sessions", type=int, default=DEFAULT_SESSIONS, help=f"Sessions to analyze (default: {DEFAULT_SESSIONS})")
    parser.add_argument("--format", choices=["table", "dashboard", "json"], default="table")
    parser.add_argument("--verbose", action="store_true", help="Show examples")
    parser.add_argument("--project", help="Project path (default: current directory)")
    parser.add_argument("--quick-stats", action="store_true", help="Show quick stats from session summaries")
    parser.add_argument("--days", type=int, default=DEFAULT_DAYS, help=f"Days to include in quick stats (default: {DEFAULT_DAYS})")
    args = parser.parse_args()

    cwd = Path.cwd()

    # Quick stats mode
    if args.quick_stats:
        stats = analyze_session_summaries(SUMMARIES_DIR, args.days)
        print_quick_stats(stats, args.days)
        return

    project_path = args.project or str(cwd)

    # Resolve project path early to get actual source directory
    if args.project and not Path(args.project).is_absolute():
        resolved_dir, matches = resolve_project_path(PROJECTS_DIR, project_path)
        if resolved_dir:
            target_project_dir = Path("/" + resolved_dir.name.replace("-", "/"))
            if not target_project_dir.exists():
                target_project_dir = HOME / "Projects" / project_path
        else:
            target_project_dir = cwd
    else:
        target_project_dir = Path(project_path) if project_path != str(cwd) else cwd

    print("\n[1/4] Discovering skills, agents, commands, hooks...", file=sys.stderr)
    skill_paths = [CLAUDE_DIR / "skills", target_project_dir / ".claude" / "skills"]
    agent_paths = [CLAUDE_DIR / "agents", target_project_dir / ".claude" / "agents"]
    command_paths = [CLAUDE_DIR / "commands", target_project_dir / ".claude" / "commands"]

    skills = discover_skills(skill_paths)
    agents = discover_agents(agent_paths)
    commands = discover_commands(command_paths)

    plugin_skills, plugin_agents, plugin_commands = discover_from_plugins(PLUGINS_CACHE)
    skills.extend(plugin_skills)
    agents.extend(plugin_agents)
    commands.extend(plugin_commands)

    settings_paths = [
        (CLAUDE_DIR / "settings.json", "global"),
        (target_project_dir / ".claude" / "settings.json", "project"),
        (target_project_dir / ".claude" / "settings.local.json", "project-local"),
    ]
    hooks = discover_hooks(settings_paths, PLUGINS_CACHE)

    print(f"  ✓ Found {len(skills)} skills, {len(agents)} agents, {len(commands)} commands, {len(hooks)} hooks", file=sys.stderr)
    if _yaml_parse_issues:
        print(f"  ⚠ Skipped {len(_yaml_parse_issues)} files with invalid YAML frontmatter", file=sys.stderr)

    print("\n[2/4] Parsing CLAUDE.md files...", file=sys.stderr)
    claude_md_paths = [
        CLAUDE_DIR / "CLAUDE.md",
        target_project_dir / "CLAUDE.md",
        target_project_dir / ".claude" / "instructions.md",
    ]
    claude_md = parse_claude_md_files(claude_md_paths)
    if claude_md["files_found"]:
        print(f"  ✓ Found {len(claude_md['files_found'])} config file(s)", file=sys.stderr)
    else:
        print("  ⊘ No CLAUDE.md files found", file=sys.stderr)

    setup_profile = compute_setup_profile(skills, agents, commands, hooks, claude_md)
    print(f"  ✓ Setup: {setup_profile.complexity} complexity, {len(setup_profile.red_flags)} red flags", file=sys.stderr)

    print("\n[3/4] Parsing session files...", file=sys.stderr)

    if args.project and not Path(args.project).is_absolute():
        resolved_dir, matches = resolve_project_path(PROJECTS_DIR, project_path)
    else:
        resolved_dir, matches = resolve_project_path(PROJECTS_DIR, project_path)

    if resolved_dir:
        if resolved_dir.name != project_path.replace("/", "-"):
            print(f"  → Matched: {resolved_dir.name}", file=sys.stderr)
        session_files = find_project_sessions(PROJECTS_DIR, resolved_dir, args.sessions)
    elif len(matches) > 1:
        print(f"  ✗ Multiple projects match '{project_path}':", file=sys.stderr)
        for m in matches[:5]:
            print(f"    - {m.name}", file=sys.stderr)
        if len(matches) > 5:
            print(f"    ... and {len(matches) - 5} more", file=sys.stderr)
        print("  Use full path or more specific name", file=sys.stderr)
        session_files = []
    else:
        print(f"  ✗ No project found matching '{project_path}'", file=sys.stderr)
        if PROJECTS_DIR.exists():
            available = sorted([d.name for d in PROJECTS_DIR.iterdir() if d.is_dir()])[:5]
            if available:
                print("  Available projects:", file=sys.stderr)
                for p in available:
                    print(f"    - {p}", file=sys.stderr)
        session_files = []

    if session_files:
        sessions = [parse_session_file(f) for f in session_files]
        total_prompts = sum(len(s.prompts) for s in sessions)
        print(f"  ✓ Parsed {len(sessions)} sessions ({total_prompts} prompts)", file=sys.stderr)
    else:
        sessions = []
        if resolved_dir:
            print(f"  ✗ No sessions found in {resolved_dir.name}", file=sys.stderr)

    print("\n[4/4] Finding potential matches...", file=sys.stderr)
    missed, jsonl_stats = analyze_jsonl(skills, agents, commands, sessions)
    print(f"  ✓ Found {len(missed)} potential matches", file=sys.stderr)

    # Read plugin enabled states from settings
    enabled_states = read_plugin_enabled_states(
        CLAUDE_DIR / "settings.json",
        target_project_dir / ".claude" / "settings.json",
    )

    # Compute plugin usage
    setup_profile.plugin_usage = compute_plugin_usage(skills, agents, sessions, missed, enabled_states)
    active_count = len(setup_profile.plugin_usage["active"])
    unused_count = len(setup_profile.plugin_usage["unused"])
    disabled_matched_count = len(setup_profile.plugin_usage.get("disabled_but_matched", []))
    already_disabled_count = len(setup_profile.plugin_usage.get("already_disabled", []))

    if unused_count > 0:
        print(f"  → {unused_count} enabled but unused, {active_count} active", file=sys.stderr)
    if disabled_matched_count > 0:
        print(f"  → {disabled_matched_count} disabled but potentially useful", file=sys.stderr)
    if already_disabled_count > 0:
        print(f"  → {already_disabled_count} already disabled (no action needed)", file=sys.stderr)
    print("", file=sys.stderr)

    # ADR-048: Load feedback and filter dismissed findings
    feedback = load_feedback()
    dismissed_hashes = get_dismissed_hashes(feedback)
    if dismissed_hashes:
        original_count = len(missed)
        missed = [m for m in missed if m.finding_hash not in dismissed_hashes]
        filtered_count = original_count - len(missed)
        if filtered_count > 0:
            print(f"[Feedback] Filtered {filtered_count} previously dismissed findings", file=sys.stderr)

    # Output
    if args.format == "json":
        output = generate_analysis_json(
            skills, agents, commands, hooks, sessions, jsonl_stats, claude_md, setup_profile, missed, feedback
        )
        print(json.dumps(output, indent=2))
    elif args.format == "dashboard":
        print_dashboard(jsonl_stats)
    else:
        print_table(jsonl_stats, missed, args.verbose)


if __name__ == "__main__":
    main()
