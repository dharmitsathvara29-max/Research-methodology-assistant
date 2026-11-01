"""Root runner for automated test suite."""

import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from tests.run_tests import run_all_tests

if __name__ == "__main__":
    run_all_tests()

