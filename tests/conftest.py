from pathlib import Path
import sys

# Ensure tests/testproject is importable as a top-level package
sys.path.insert(0, str(Path(__file__).parent))
