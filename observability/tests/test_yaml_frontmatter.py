"""Tests for YAML frontmatter extraction and error handling.

Tests the extract_yaml_frontmatter function and graceful error handling
when skill/agent/command files have invalid YAML.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "observability-usage-collector" / "scripts"))
import collect_usage


class TestExtractYamlFrontmatter:
    """Tests for extract_yaml_frontmatter function."""

    def setup_method(self):
        """Clear the issues list before each test."""
        collect_usage._yaml_parse_issues.clear()

    def test_valid_frontmatter(self):
        """Valid YAML frontmatter should be extracted."""
        content = """---
name: Test Skill
description: A test skill for testing
---

# Content here
"""
        result = collect_usage.extract_yaml_frontmatter(content)
        assert result["name"] == "Test Skill"
        assert result["description"] == "A test skill for testing"
        assert len(collect_usage._yaml_parse_issues) == 0

    def test_no_frontmatter(self):
        """Content without frontmatter should return empty dict."""
        content = "# Just a heading\n\nSome content"
        result = collect_usage.extract_yaml_frontmatter(content)
        assert result == {}
        assert len(collect_usage._yaml_parse_issues) == 0

    def test_incomplete_frontmatter(self):
        """Frontmatter without closing delimiter should return empty dict."""
        content = """---
name: Test
description: No closing delimiter
"""
        result = collect_usage.extract_yaml_frontmatter(content)
        assert result == {}
        assert len(collect_usage._yaml_parse_issues) == 0

    def test_invalid_yaml_frontmatter(self):
        """Invalid YAML should return empty dict and record the issue."""
        content = """---
name: Test Skill
description: This has a colon: in the middle without quotes
---

# Content
"""
        result = collect_usage.extract_yaml_frontmatter(content, "/test/path/SKILL.md")
        assert result == {}
        assert len(collect_usage._yaml_parse_issues) == 1
        assert collect_usage._yaml_parse_issues[0] == "/test/path/SKILL.md"

    def test_invalid_yaml_without_path(self):
        """Invalid YAML without source_path should not record issue."""
        content = """---
name: Test
bad: yaml: here
---
"""
        result = collect_usage.extract_yaml_frontmatter(content)
        assert result == {}
        assert len(collect_usage._yaml_parse_issues) == 0

    def test_empty_frontmatter(self):
        """Empty frontmatter should return empty dict."""
        content = """---
---

# Content
"""
        result = collect_usage.extract_yaml_frontmatter(content)
        assert result == {}
        assert len(collect_usage._yaml_parse_issues) == 0

    def test_frontmatter_with_lists(self):
        """Frontmatter with list values should work."""
        content = """---
name: Test
allowed-tools: [Read, Write, Edit]
---
"""
        result = collect_usage.extract_yaml_frontmatter(content)
        assert result["name"] == "Test"
        assert result["allowed-tools"] == ["Read", "Write", "Edit"]

    def test_multiple_invalid_files_tracked(self):
        """Multiple invalid files should all be tracked."""
        invalid_content = """---
bad: yaml: here
---
"""
        collect_usage.extract_yaml_frontmatter(invalid_content, "/path/one.md")
        collect_usage.extract_yaml_frontmatter(invalid_content, "/path/two.md")
        collect_usage.extract_yaml_frontmatter(invalid_content, "/path/three.md")

        assert len(collect_usage._yaml_parse_issues) == 3
        assert "/path/one.md" in collect_usage._yaml_parse_issues
        assert "/path/two.md" in collect_usage._yaml_parse_issues
        assert "/path/three.md" in collect_usage._yaml_parse_issues


class TestPreComputedFindings:
    """Tests for YAML issues in pre_computed_findings."""

    def setup_method(self):
        """Clear the issues list before each test."""
        collect_usage._yaml_parse_issues.clear()

    def test_yaml_issues_in_findings(self):
        """Invalid YAML files should appear in pre_computed_findings."""
        collect_usage._yaml_parse_issues.extend([
            "/path/skill1.md",
            "/path/skill2.md",
        ])

        # Create minimal inputs for compute_pre_computed_findings
        class MockSetupProfile:
            overlapping_triggers = []
            description_quality = []

        findings = collect_usage.compute_pre_computed_findings(
            skills=[],
            agents=[],
            commands=[],
            sessions=[],
            missed=[],
            setup_profile=MockSetupProfile(),
        )

        assert "invalid_yaml_files" in findings
        assert len(findings["invalid_yaml_files"]) == 2
        assert "/path/skill1.md" in findings["invalid_yaml_files"]
        assert findings["counts"]["invalid_yaml_files"] == 2

    def test_no_yaml_issues_empty_list(self):
        """No YAML issues should result in empty list."""
        class MockSetupProfile:
            overlapping_triggers = []
            description_quality = []

        findings = collect_usage.compute_pre_computed_findings(
            skills=[],
            agents=[],
            commands=[],
            sessions=[],
            missed=[],
            setup_profile=MockSetupProfile(),
        )

        assert findings["invalid_yaml_files"] == []
        assert findings["counts"]["invalid_yaml_files"] == 0

    def test_yaml_issues_limited_to_20(self):
        """Findings should limit to 20 files max."""
        collect_usage._yaml_parse_issues.extend([f"/path/file{i}.md" for i in range(30)])

        class MockSetupProfile:
            overlapping_triggers = []
            description_quality = []

        findings = collect_usage.compute_pre_computed_findings(
            skills=[],
            agents=[],
            commands=[],
            sessions=[],
            missed=[],
            setup_profile=MockSetupProfile(),
        )

        assert len(findings["invalid_yaml_files"]) == 20
        assert findings["counts"]["invalid_yaml_files"] == 30  # Full count preserved
