"""Tests for Story 3.2: Summary Dashboard in usage-insights-agent.

Validates that the agent markdown contains required dashboard structure,
tier definitions, and category drill-down instructions.
"""

from pathlib import Path

import pytest


def get_agent_content() -> str:
    root = Path(__file__).parent.parent
    agent_file = root / "agents" / "usage-insights-agent.md"
    assert agent_file.exists(), f"Agent file not found: {agent_file}"
    return agent_file.read_text()


def get_dashboard_section() -> str:
    """Extract the Summary Dashboard section (up to Analysis Workflow)."""
    content = get_agent_content()
    start = content.find("## Summary Dashboard")
    assert start != -1, "Summary Dashboard section not found"
    end = content.find("## Analysis Workflow", start + 1)
    return content[start:end] if end != -1 else content[start:]


class TestDashboardStructure:
    """AC-1: Dashboard is presented FIRST before drill-down."""

    def test_dashboard_section_exists(self):
        content = get_agent_content()
        assert "## Summary Dashboard" in content

    def test_dashboard_before_analysis_workflow(self):
        content = get_agent_content()
        dashboard_pos = content.find("## Summary Dashboard")
        workflow_pos = content.find("## Analysis Workflow")
        assert dashboard_pos != -1, "Summary Dashboard section missing"
        assert workflow_pos != -1, "Analysis Workflow section missing"
        assert dashboard_pos < workflow_pos, "Dashboard must appear before Analysis Workflow"

    def test_analysis_workflow_references_dashboard(self):
        content = get_agent_content()
        workflow_start = content.find("## Analysis Workflow")
        workflow_section = content[workflow_start:]
        assert "Summary Dashboard" in workflow_section, (
            "Analysis Workflow must reference Summary Dashboard to ensure it renders first"
        )


class TestStatsTier:
    """AC-2: Stats tier shows sessions, skills, classification counts."""

    def test_stats_tier_in_dashboard(self):
        section = get_dashboard_section()
        assert "Quick Stats" in section or "Stats Tier" in section

    def test_stats_includes_sessions(self):
        section = get_dashboard_section()
        assert "total_sessions" in section

    def test_stats_includes_active_dormant_unused(self):
        section = get_dashboard_section()
        assert "active" in section.lower()
        assert "dormant" in section.lower()
        assert "unused" in section.lower()

    def test_stats_includes_percentages(self):
        section = get_dashboard_section()
        assert "%" in section, "Stats tier should show percentage calculations"


class TestTopThreeTier:
    """AC-2, AC-4: Top 3 highest impact missed opportunities sorted by impact_score."""

    def test_top3_in_dashboard(self):
        section = get_dashboard_section()
        assert "Top 3" in section

    def test_top3_sort_by_impact_score_descending(self):
        section = get_dashboard_section()
        assert "impact_score" in section
        assert "descending" in section.lower(), "Must specify descending sort order"

    def test_top3_emoji_indicators_in_dashboard(self):
        section = get_dashboard_section()
        for emoji in ["🔴", "🟡", "🟢"]:
            assert emoji in section, f"Missing emoji indicator in dashboard: {emoji}"

    def test_top3_handles_fewer_than_three(self):
        section = get_dashboard_section()
        assert "fewer than 3" in section, "Must handle case with < 3 missed opportunities"


class TestCategoriesTier:
    """AC-2: Categories tier shows grouped findings with counts."""

    def test_categories_in_dashboard(self):
        section = get_dashboard_section()
        assert "Categories" in section

    def test_categories_include_missed_opportunities(self):
        section = get_dashboard_section()
        assert "Missed Opportunities" in section

    def test_categories_include_dormant_skills(self):
        section = get_dashboard_section()
        assert "Dormant Skills" in section

    def test_categories_include_unused_skills(self):
        section = get_dashboard_section()
        assert "Unused Skills" in section

    def test_categories_are_selectable(self):
        section = get_dashboard_section()
        assert "[1]" in section and "[2]" in section and "[3]" in section, (
            "Categories must be presented as numbered selectable options"
        )

    def test_zero_count_categories_omitted(self):
        section = get_dashboard_section()
        assert "0 items" in section.lower() or "omit" in section.lower() or "1+" in section, (
            "Must specify handling for categories with zero items"
        )


class TestTierOrdering:
    """Verify the three tiers appear in correct order within the dashboard."""

    def test_stats_before_top3(self):
        section = get_dashboard_section()
        stats_pos = section.find("Quick Stats")
        top3_pos = section.find("Top 3")
        assert stats_pos != -1 and top3_pos != -1
        assert stats_pos < top3_pos, "Quick Stats must appear before Top 3"

    def test_top3_before_categories(self):
        section = get_dashboard_section()
        top3_pos = section.find("Top 3")
        cat_pos = section.find("Categories Tier")
        assert top3_pos != -1 and cat_pos != -1
        assert top3_pos < cat_pos, "Top 3 must appear before Categories"

    def test_drill_down_data_extraction_table(self):
        section = get_dashboard_section()
        assert "Category Drill-Down Data Extraction" in section, (
            "Must specify how to extract data for each dashboard category"
        )
        assert "missed_opportunities" in section
        assert "discovery.skills" in section


class TestCategoryDrillDown:
    """AC-3: Category selection presents findings one-by-one."""

    def test_drilldown_section_in_dashboard(self):
        section = get_dashboard_section()
        assert "Drill-Down" in section or "drill-down" in section.lower()

    def test_drilldown_offers_accept_skip_detail(self):
        section = get_dashboard_section()
        assert "[Accept]" in section
        assert "[Skip]" in section
        assert "[More Detail]" in section

    def test_drilldown_tracks_reviewed_items(self):
        section = get_dashboard_section()
        assert "reviewed" in section.lower(), "Must track which items have been reviewed"
