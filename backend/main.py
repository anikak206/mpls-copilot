import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.main import app  # noqa: E402,F401


@app.get("/", tags=["health"], include_in_schema=False)
def root():
    return {
        "name": "MPLS Predictive Copilot API",
        "status": "ok",
        "docs": "/docs",
        "health": "/health",
    }
