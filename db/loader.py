"""
Database Loader shim delegating to src.etl.loader.ETLLoader.
"""

import sys
import os

# Ensure the project root (parent of this db/ directory) is on sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.etl.loader import ETLLoader

if __name__ == "__main__":
    loader = ETLLoader()
    loader.run()
