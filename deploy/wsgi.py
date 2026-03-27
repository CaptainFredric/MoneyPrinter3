"""WSGI entry point for cloud deployment (Render, Railway, Heroku, etc.)."""
import sys
from pathlib import Path

# Ensure src/ is on the path so llm_provider can be imported
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from scripts.api_prototype import app  # noqa: E402

if __name__ == "__main__":
    app.run()
