"""Tests for outcome detection logic.

Tests the detect_outcome function that determines success/failure from tool results.
This function is duplicated in generate_session_summary.py and collect_usage.py.
"""

import pytest
import sys
from pathlib import Path

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "hooks"))
sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "observability-usage-collector" / "scripts"))

from generate_session_summary import detect_outcome as detect_outcome_hook
from collect_usage import detect_outcome as detect_outcome_collector


@pytest.fixture(params=["hook", "collector"])
def detect_outcome(request):
    """Test both implementations of detect_outcome."""
    if request.param == "hook":
        return detect_outcome_hook
    return detect_outcome_collector


class TestBashOutcomes:
    """Tests for Bash command outcome detection."""

    def test_exit_code_0_success(self, detect_outcome):
        result = "Command output\nExit code: 0"
        assert detect_outcome("Bash", result) == "success"

    def test_exit_code_nonzero_failure(self, detect_outcome):
        result = "Command failed\nExit code: 1"
        assert detect_outcome("Bash", result) == "failure"

    def test_exit_code_127_failure(self, detect_outcome):
        result = "Command not found\nExit code: 127"
        assert detect_outcome("Bash", result) == "failure"

    def test_succeeded_keyword(self, detect_outcome):
        result = "Build succeeded"
        assert detect_outcome("Bash", result) == "success"

    def test_timeout_failure(self, detect_outcome):
        result = "Command timed out after 30 seconds"
        assert detect_outcome("Bash", result) == "failure"

    def test_error_keyword_failure(self, detect_outcome):
        result = "error: Something went wrong"
        assert detect_outcome("Bash", result) == "failure"

    def test_failed_keyword_failure(self, detect_outcome):
        result = "Build failed with errors"
        assert detect_outcome("Bash", result) == "failure"

    def test_traceback_failure(self, detect_outcome):
        result = "Traceback (most recent call last):\n  File..."
        assert detect_outcome("Bash", result) == "failure"

    def test_permission_denied_failure(self, detect_outcome):
        result = "permission denied: /etc/passwd"
        assert detect_outcome("Bash", result) == "failure"

    def test_clean_output_success(self, detect_outcome):
        """Output without error indicators should be success."""
        result = "Hello World\nDone."
        assert detect_outcome("Bash", result) == "success"

    def test_empty_output_success(self, detect_outcome):
        result = ""
        assert detect_outcome("Bash", result) == "success"

    def test_case_insensitive_error(self, detect_outcome):
        result = "ERROR: Something happened"
        assert detect_outcome("Bash", result) == "failure"

    def test_case_insensitive_failed(self, detect_outcome):
        result = "FAILED to compile"
        assert detect_outcome("Bash", result) == "failure"


class TestEditWriteOutcomes:
    """Tests for Edit/Write tool outcome detection."""

    @pytest.mark.parametrize("tool", ["Edit", "Write", "NotebookEdit"])
    def test_success_on_clean_result(self, detect_outcome, tool):
        result = "File updated successfully"
        assert detect_outcome(tool, result) == "success"

    @pytest.mark.parametrize("tool", ["Edit", "Write", "NotebookEdit"])
    def test_permission_denied_failure(self, detect_outcome, tool):
        result = "Permission denied: cannot write to file"
        assert detect_outcome(tool, result) == "failure"

    @pytest.mark.parametrize("tool", ["Edit", "Write", "NotebookEdit"])
    def test_file_not_found_failure(self, detect_outcome, tool):
        result = "File not found: /path/to/file.txt"
        assert detect_outcome(tool, result) == "failure"

    @pytest.mark.parametrize("tool", ["Edit", "Write", "NotebookEdit"])
    def test_no_such_file_failure(self, detect_outcome, tool):
        result = "No such file or directory"
        assert detect_outcome(tool, result) == "failure"

    def test_edit_old_string_not_found(self, detect_outcome):
        result = "old_string not found in file"
        assert detect_outcome("Edit", result) == "failure"

    def test_edit_not_unique(self, detect_outcome):
        result = "The string is not unique in the file"
        assert detect_outcome("Edit", result) == "failure"

    def test_edit_generic_error(self, detect_outcome):
        result = "Error: Unable to edit file"
        assert detect_outcome("Edit", result) == "failure"


class TestOtherToolOutcomes:
    """Tests for other tools' outcome detection."""

    @pytest.mark.parametrize("tool", ["Read", "Glob", "Grep", "Task", "Skill"])
    def test_generic_success(self, detect_outcome, tool):
        result = "Some normal output"
        assert detect_outcome(tool, result) == "success"

    @pytest.mark.parametrize("tool", ["Read", "Glob", "Grep", "Task", "Skill"])
    def test_generic_error_failure(self, detect_outcome, tool):
        result = "Error occurred during operation"
        assert detect_outcome(tool, result) == "failure"

    @pytest.mark.parametrize("tool", ["Read", "Glob", "Grep", "Task", "Skill"])
    def test_generic_failed_failure(self, detect_outcome, tool):
        result = "Operation failed"
        assert detect_outcome(tool, result) == "failure"

    def test_read_file_contents_success(self, detect_outcome):
        result = "def hello():\n    print('world')"
        assert detect_outcome("Read", result) == "success"

    def test_glob_no_matches_success(self, detect_outcome):
        """No matches is not an error."""
        result = "No files found matching pattern"
        assert detect_outcome("Glob", result) == "success"

    def test_grep_no_matches_success(self, detect_outcome):
        """No matches is not an error."""
        result = ""
        assert detect_outcome("Grep", result) == "success"


class TestEdgeCases:
    """Tests for edge cases and tricky scenarios."""

    def test_error_in_output_not_keyword(self, detect_outcome):
        """Word 'error' as part of normal text shouldn't trigger failure."""
        # Note: Current implementation will mark this as failure
        # This documents the current behavior
        result = "The error handling code works correctly"
        # Current behavior: "error" substring matches, returns failure
        assert detect_outcome("Read", result) == "failure"

    def test_failed_in_output_not_keyword(self, detect_outcome):
        """Word 'failed' as part of normal text."""
        result = "The test that previously failed now passes"
        # Current behavior: "failed" substring matches, returns failure
        assert detect_outcome("Read", result) == "failure"

    def test_multiline_with_error_at_end(self, detect_outcome):
        result = "Line 1\nLine 2\nLine 3\nerror: something"
        assert detect_outcome("Bash", result) == "failure"

    def test_case_sensitivity_mixed(self, detect_outcome):
        result = "ErRoR: Mixed case"
        assert detect_outcome("Bash", result) == "failure"

    def test_exit_code_in_middle(self, detect_outcome):
        result = "Some output\nExit code: 0\nMore output"
        assert detect_outcome("Bash", result) == "success"

    def test_unknown_tool_success(self, detect_outcome):
        result = "Some result"
        assert detect_outcome("UnknownTool", result) == "success"

    def test_unknown_tool_with_error(self, detect_outcome):
        result = "Error in result"
        assert detect_outcome("UnknownTool", result) == "failure"


class TestImplementationParity:
    """Verify both implementations behave identically."""

    TEST_CASES = [
        ("Bash", "Exit code: 0", "success"),
        ("Bash", "Exit code: 1", "failure"),
        ("Bash", "error: something", "failure"),
        ("Edit", "File updated", "success"),
        ("Edit", "old_string not found", "failure"),
        ("Write", "Success", "success"),
        ("Read", "content", "success"),
        ("Task", "completed", "success"),
    ]

    @pytest.mark.parametrize("tool,result,expected", TEST_CASES)
    def test_implementations_match(self, tool, result, expected):
        """Both implementations should return the same result."""
        hook_result = detect_outcome_hook(tool, result)
        collector_result = detect_outcome_collector(tool, result)
        assert hook_result == collector_result == expected
