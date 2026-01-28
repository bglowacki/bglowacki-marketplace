"""Tests for code synchronization between duplicated files (ADR-013).

Verifies that intentionally duplicated code remains in sync.
"""

import ast
from pathlib import Path

import pytest


def extract_function_ast(file_path: Path, func_name: str) -> str:
    """Extract a function's AST representation from a file."""
    tree = ast.parse(file_path.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == func_name:
            # Remove docstring for comparison (may differ)
            if (node.body and isinstance(node.body[0], ast.Expr) and
                isinstance(node.body[0].value, ast.Constant) and
                isinstance(node.body[0].value.value, str)):
                node.body = node.body[1:]
            return ast.unparse(node)
    raise ValueError(f"Function {func_name} not found in {file_path}")


def get_project_root() -> Path:
    """Get the observability project root."""
    return Path(__file__).parent.parent


class TestCodeSync:
    """Verify duplicated code implementations remain synchronized."""

    def test_detect_outcome_sync(self):
        """Verify detect_outcome implementations are identical (ADR-013).

        Both hooks/generate_session_summary.py and collect_usage.py contain
        detect_outcome() for standalone operation. This test ensures they
        don't diverge.
        """
        root = get_project_root()

        hook_file = root / "hooks" / "generate_session_summary.py"
        collector_file = root / "skills" / "observability-usage-collector" / "scripts" / "collect_usage.py"

        assert hook_file.exists(), f"Hook file not found: {hook_file}"
        assert collector_file.exists(), f"Collector file not found: {collector_file}"

        hook_impl = extract_function_ast(hook_file, "detect_outcome")
        collector_impl = extract_function_ast(collector_file, "detect_outcome")

        assert hook_impl == collector_impl, (
            "detect_outcome() implementations have diverged!\n"
            "Both hooks/generate_session_summary.py and collect_usage.py must have "
            "identical implementations. See ADR-013 for rationale.\n\n"
            f"Hook version:\n{hook_impl}\n\n"
            f"Collector version:\n{collector_impl}"
        )

    def test_infer_workflow_stage_sync(self):
        """Verify infer_workflow_stage implementations are identical.

        If this function exists in both files, ensure they're in sync.
        """
        root = get_project_root()

        hook_file = root / "hooks" / "generate_session_summary.py"
        collector_file = root / "skills" / "observability-usage-collector" / "scripts" / "collect_usage.py"

        try:
            hook_impl = extract_function_ast(hook_file, "infer_workflow_stage")
        except ValueError:
            pytest.skip("infer_workflow_stage not in hook file")
            return

        try:
            collector_impl = extract_function_ast(collector_file, "infer_workflow_stage")
        except ValueError:
            pytest.skip("infer_workflow_stage not in collector file")
            return

        assert hook_impl == collector_impl, (
            "infer_workflow_stage() implementations have diverged!"
        )
