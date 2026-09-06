"""
Root entry point so the app can be started from the project root:

    uvicorn backend.main:app --reload

Puts backend/ on sys.path so the `app` package (app/routers/*, app/core/*)
imports cleanly, then re-exports the FastAPI app defined in app/main.py,
which already includes all Phase 3 routers.
"""

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