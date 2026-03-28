"""WSGI entry point for cloud deployment (Render, Railway, Heroku, etc.)."""
import sys
from pathlib import Path

# __file__ lives in deploy/; go up one level to reach the project root.
ROOT = Path(__file__).resolve().parent.parent
# Add project root so `scripts.api_prototype` is importable.
sys.path.insert(0, str(ROOT))
# Add src/ so `llm_provider` and other src modules are importable.
sys.path.insert(0, str(ROOT / "src"))

from scripts.api_prototype import app  # noqa: E402

if __name__ == "__main__":
    app.run()
