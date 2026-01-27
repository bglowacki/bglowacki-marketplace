"""Pytest configuration and fixtures for observability tests."""

import sys
from pathlib import Path

# Add source directories to path
_root = Path(__file__).parent.parent
sys.path.insert(0, str(_root / "hooks"))
sys.path.insert(0, str(_root / "skills" / "observability-usage-collector" / "scripts"))
