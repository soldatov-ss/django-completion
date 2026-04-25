import sys
from pathlib import Path

# Ensure tests/testproject is importable as a top-level package
sys.path.insert(0, str(Path(__file__).parent))
