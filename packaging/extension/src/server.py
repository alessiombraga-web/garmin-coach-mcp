"""Garmin Coach — Claude Desktop extension entry point (MCP over stdio)."""
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

logging.basicConfig(level=logging.INFO, stream=sys.stderr,
                    format="%(asctime)s %(levelname)s %(name)s: %(message)s")

from app.server import serve_stdio  # noqa: E402

if __name__ == "__main__":
    serve_stdio()
