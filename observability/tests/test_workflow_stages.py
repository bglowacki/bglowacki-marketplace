"""Tests for workflow stage inference logic.

Tests the infer_workflow_stage function that determines what stage
of the workflow the user is in based on tool usage.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "hooks"))
from generate_session_summary import infer_workflow_stage


class TestSkillBasedStages:
    """Tests for stage inference from Skill tool usage."""

    def test_brainstorm_skill(self):
        result = infer_workflow_stage("Skill", {"skill": "brainstorming"}, "unknown")
        assert result == "brainstorm"

    def test_brainstorm_skill_partial(self):
        result = infer_workflow_stage("Skill", {"skill": "superpowers:brainstorm"}, "unknown")
        assert result == "brainstorm"

    def test_plan_skill(self):
        result = infer_workflow_stage("Skill", {"skill": "writing-plans"}, "unknown")
        assert result == "plan"

    def test_plan_skill_alternate(self):
        result = infer_workflow_stage("Skill", {"skill": "my-plan-skill"}, "unknown")
        assert result == "plan"

    def test_review_skill(self):
        result = infer_workflow_stage("Skill", {"skill": "code-review"}, "unknown")
        assert result == "review"

    def test_review_skill_alternate(self):
        result = infer_workflow_stage("Skill", {"skill": "requesting-code-review"}, "unknown")
        assert result == "review"

    def test_tdd_skill(self):
        result = infer_workflow_stage("Skill", {"skill": "test-driven-development"}, "unknown")
        assert result == "test"

    def test_tdd_skill_short(self):
        result = infer_workflow_stage("Skill", {"skill": "tdd"}, "unknown")
        assert result == "test"

    def test_commit_skill(self):
        result = infer_workflow_stage("Skill", {"skill": "commit"}, "unknown")
        assert result == "commit"

    def test_unknown_skill_keeps_current(self):
        result = infer_workflow_stage("Skill", {"skill": "random-skill"}, "implement")
        assert result == "implement"


class TestEditWriteStages:
    """Tests for stage inference from Edit/Write tools."""

    def test_edit_is_implement(self):
        result = infer_workflow_stage("Edit", {}, "unknown")
        assert result == "implement"

    def test_write_is_implement(self):
        result = infer_workflow_stage("Write", {}, "unknown")
        assert result == "implement"

    def test_edit_overrides_previous(self):
        result = infer_workflow_stage("Edit", {}, "plan")
        assert result == "implement"


class TestBashStages:
    """Tests for stage inference from Bash commands."""

    def test_pytest_is_test(self):
        result = infer_workflow_stage("Bash", {"command": "pytest tests/"}, "implement")
        assert result == "test"

    def test_npm_test_is_test(self):
        result = infer_workflow_stage("Bash", {"command": "npm test"}, "implement")
        assert result == "test"

    def test_unittest_is_test(self):
        result = infer_workflow_stage("Bash", {"command": "python -m unittest"}, "implement")
        assert result == "test"

    def test_jest_is_test(self):
        result = infer_workflow_stage("Bash", {"command": "jest --watch"}, "implement")
        assert result == "test"

    def test_test_keyword_is_test(self):
        result = infer_workflow_stage("Bash", {"command": "./run_tests.sh"}, "implement")
        assert result == "test"

    def test_git_commit_is_commit(self):
        result = infer_workflow_stage("Bash", {"command": "git commit -m 'msg'"}, "test")
        assert result == "commit"

    def test_git_push_is_deploy(self):
        result = infer_workflow_stage("Bash", {"command": "git push origin main"}, "commit")
        assert result == "deploy"

    def test_other_bash_keeps_current(self):
        result = infer_workflow_stage("Bash", {"command": "ls -la"}, "implement")
        assert result == "implement"

    def test_empty_command_keeps_current(self):
        result = infer_workflow_stage("Bash", {"command": ""}, "implement")
        assert result == "implement"


class TestTaskStages:
    """Tests for stage inference from Task (agent) tool."""

    def test_review_agent_is_review(self):
        result = infer_workflow_stage("Task", {"subagent_type": "code-reviewer"}, "implement")
        assert result == "review"

    def test_test_agent_is_test(self):
        result = infer_workflow_stage("Task", {"subagent_type": "test-runner"}, "implement")
        assert result == "test"

    def test_other_agent_keeps_current(self):
        result = infer_workflow_stage("Task", {"subagent_type": "explorer"}, "implement")
        assert result == "implement"


class TestOtherTools:
    """Tests for other tools that don't change stage."""

    @pytest.mark.parametrize("tool", ["Read", "Glob", "Grep", "WebFetch", "WebSearch"])
    def test_read_tools_keep_current(self, tool):
        result = infer_workflow_stage(tool, {}, "implement")
        assert result == "implement"

    def test_unknown_tool_keeps_current(self):
        result = infer_workflow_stage("UnknownTool", {}, "plan")
        assert result == "plan"


class TestStageTransitions:
    """Tests for realistic stage transition sequences."""

    def test_typical_workflow(self):
        """Simulate a typical workflow progression."""
        stage = "unknown"

        # Start with brainstorming
        stage = infer_workflow_stage("Skill", {"skill": "brainstorming"}, stage)
        assert stage == "brainstorm"

        # Move to planning
        stage = infer_workflow_stage("Skill", {"skill": "writing-plans"}, stage)
        assert stage == "plan"

        # Read some files (stays in plan)
        stage = infer_workflow_stage("Read", {"file_path": "src/main.py"}, stage)
        assert stage == "plan"

        # Start implementing
        stage = infer_workflow_stage("Edit", {"file_path": "src/main.py"}, stage)
        assert stage == "implement"

        # Run tests
        stage = infer_workflow_stage("Bash", {"command": "pytest"}, stage)
        assert stage == "test"

        # Get review
        stage = infer_workflow_stage("Task", {"subagent_type": "code-reviewer"}, stage)
        assert stage == "review"

        # Commit
        stage = infer_workflow_stage("Bash", {"command": "git commit -m 'done'"}, stage)
        assert stage == "commit"

        # Deploy
        stage = infer_workflow_stage("Bash", {"command": "git push"}, stage)
        assert stage == "deploy"


class TestResearchStage:
    """Tests for research stage detection (ADR-011 implemented)."""

    def test_read_is_research_from_unknown(self):
        """Read tool triggers research stage from unknown."""
        result = infer_workflow_stage("Read", {"file_path": "doc.md"}, "unknown")
        assert result == "research"

    def test_glob_is_research_from_unknown(self):
        """Glob tool triggers research stage from unknown."""
        result = infer_workflow_stage("Glob", {"pattern": "**/*.py"}, "unknown")
        assert result == "research"

    def test_grep_is_research_from_unknown(self):
        """Grep tool triggers research stage from unknown."""
        result = infer_workflow_stage("Grep", {"pattern": "TODO"}, "unknown")
        assert result == "research"

    def test_webfetch_is_research_from_unknown(self):
        """WebFetch tool triggers research stage from unknown."""
        result = infer_workflow_stage("WebFetch", {"url": "https://example.com"}, "unknown")
        assert result == "research"

    def test_websearch_is_research_from_unknown(self):
        """WebSearch tool triggers research stage from unknown."""
        result = infer_workflow_stage("WebSearch", {"query": "python async"}, "unknown")
        assert result == "research"

    def test_read_is_research_from_plan(self):
        """Read during planning is still research."""
        result = infer_workflow_stage("Read", {"file_path": "doc.md"}, "plan")
        assert result == "research"

    def test_read_stays_implement_during_implement(self):
        """Read during implementation stays in implement stage."""
        result = infer_workflow_stage("Read", {"file_path": "doc.md"}, "implement")
        assert result == "implement"

    def test_read_stays_test_during_test(self):
        """Read during testing stays in test stage."""
        result = infer_workflow_stage("Read", {"file_path": "doc.md"}, "test")
        assert result == "test"

    def test_explore_agent_is_research(self):
        """Explore agent triggers research stage."""
        result = infer_workflow_stage("Task", {"subagent_type": "explore"}, "unknown")
        assert result == "research"


class TestDebugStage:
    """Tests for debug stage detection."""

    def test_debug_skill(self):
        """Debug skill triggers debug stage."""
        result = infer_workflow_stage("Skill", {"skill": "systematic-debugging"}, "implement")
        assert result == "debug"

    def test_debug_agent(self):
        """Debug agent triggers debug stage."""
        result = infer_workflow_stage("Task", {"subagent_type": "debugger"}, "implement")
        assert result == "debug"
