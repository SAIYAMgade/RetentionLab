"""Pytest configuration and fixture imports."""
import sys
from pathlib import Path

# Add src and root to python path for all test runners
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "src"))
sys.path.insert(0, str(ROOT_DIR))

from tests.fixtures.synthetic_fixtures import sample_transactions_raw
