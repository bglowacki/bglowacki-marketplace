"""Tests for Story 3.3: Findings Walk-through in usage-insights-agent.

Validates that the agent markdown contains finding templates with
Problem-Evidence-Action format, copy-paste instructions, response handling,
progress tracking, and finding type templates.
"""

from pathlib import Path

import pytest


def get_agent_content() -> str:
    root = Path(__file__).parent.parent
    agent_file = root / "agents" / "usage-insights-agent.md"
    assert agent_file.exists(), f"Agent file not found: {agent_file}"
    return agent_file.read_text()


def get_findings_section() -> str:
    """Extract the Findings Walk-through section."""
    content = get_agent_content()
    start = content.find("## Findings Walk-through")
    assert start != -1, "Findings Walk-through section not found"
    # Find next h2 section
    end = content.find("\n## ", start + 1)
    return content[start:end] if end != -1 else content[start:]


class TestFindingTemplate:
    """AC-1: Problem-Evidence-Action format."""

    def test_findings_walkthrough_section_exists(self):
        content = get_agent_content()
        assert "## Findings Walk-through" in content

    def test_problem_section_format(self):
        section = get_findings_section()
        assert "**Problem:**" in section or "**Problem**" in section

    def test_evidence_section_format(self):
        section = get_findings_section()
        assert "**Evidence:**" in section or "**Evidence**" in section

    def test_evidence_includes_confidence(self):
        section = get_findings_section()
        assert "confidence" in section.lower()

    def test_evidence_includes_frequency(self):
        section = get_findings_section()
        assert "frequency" in section.lower() or "session" in section.lower()

    def test_action_section_format(self):
        section = get_findings_section()
        assert "**Recommended Action:**" in section or "**Action:**" in section or "**Recommended Action**" in section


class TestFindingTemplateOrdering:
    """Verify Problem-Evidence-Action appears in correct order."""

    def test_problem_before_evidence(self):
        section = get_findings_section()
        problem_pos = section.find("**Problem:**")
        evidence_pos = section.find("**Evidence:**")
        assert problem_pos != -1 and evidence_pos != -1
        assert problem_pos < evidence_pos, "Problem must appear before Evidence"

    def test_evidence_before_action(self):
        section = get_findings_section()
        evidence_pos = section.find("**Evidence:**")
        action_pos = section.find("**Recommended Action:**")
        assert evidence_pos != -1 and action_pos != -1
        assert evidence_pos < action_pos, "Evidence must appear before Recommended Action"


class TestCopyPasteActions:
    """AC-2: Copy-paste ready instructions."""

    def test_copy_paste_for_claude_md(self):
        section = get_findings_section()
        assert "CLAUDE.md" in section, "Must include CLAUDE.md copy-paste example"

    def test_copy_paste_for_skill_invocation(self):
        section = get_findings_section()
        assert "invocation" in section.lower() or "invoke" in section.lower() or "command" in section.lower()

    def test_copy_paste_for_config(self):
        section = get_findings_section()
        assert "config" in section.lower(), "Must include configuration copy-paste example"

    def test_copy_paste_has_code_blocks(self):
        section = get_findings_section()
        assert "```" in section, "Copy-paste actions must use code blocks"

    def test_evidence_based_explanation(self):
        section = get_findings_section()
        assert "why" in section.lower(), "Must explain WHY the recommendation is made"


class TestResponseHandling:
    """AC-3: Accept/Skip/More Detail response options."""

    def test_accept_option(self):
        section = get_findings_section()
        assert "Accept" in section

    def test_skip_option(self):
        section = get_findings_section()
        assert "Skip" in section

    def test_more_detail_option(self):
        section = get_findings_section()
        assert "More Detail" in section

    def test_accept_logs_action(self):
        section = get_findings_section()
        lower = section.lower()
        assert "actioned" in lower or "log" in lower or "record" in lower, (
            "Accept must log/record the action"
        )

    def test_more_detail_shows_additional_context(self):
        section = get_findings_section()
        lower = section.lower()
        assert "session" in lower or "prompt" in lower, (
            "More Detail must show additional context like sessions or prompts"
        )


class TestProgressIndicator:
    """AC-4: Progress tracking through findings."""

    def test_progress_counter_format(self):
        section = get_findings_section()
        assert "of" in section and "Finding" in section, (
            "Must show 'Finding X of Y' format"
        )

    def test_reviewed_items_tracked(self):
        section = get_findings_section()
        assert "track" in section.lower() or "reviewed" in section.lower()

    def test_completion_summary(self):
        section = get_findings_section()
        assert "summary" in section.lower() or "completion" in section.lower()


class TestFindingTypeTemplates:
    """AC-1, AC-2: Specific templates for different finding types."""

    def test_missed_opportunity_template(self):
        section = get_findings_section()
        assert "Missed Opportunity" in section or "missed_opportunity" in section

    def test_dormant_skill_template(self):
        section = get_findings_section()
        assert "Dormant Skill" in section or "dormant" in section.lower()

    def test_configuration_issue_template(self):
        section = get_findings_section()
        assert "Configuration" in section or "configuration" in section
