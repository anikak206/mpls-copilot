from fastapi import FastAPI

from app.routers import (
    auth, users, devices, telemetry, alerts, incidents,
    predictions, recommendations, actions, outcomes, audit, reports,
)

tags_metadata = [
    {"name": "auth", "description": "Login (issues a JWT) and current-user info."},
    {"name": "users", "description": "User management. Admin only."},
    {"name": "devices", "description": "Device inventory plus the per-device telemetry feed used by the AI module."},
    {"name": "telemetry", "description": "Telemetry ingestion and query."},
    {"name": "alerts", "description": "Alerts raised on devices."},
    {"name": "incidents", "description": "Incident tracking."},
    {"name": "predictions", "description": "AI failure predictions: ingestion, risk score/level and contributing factors."},
    {"name": "recommendations", "description": "Preventive recommendations linked to predictions."},
    {"name": "actions", "description": "Engineer actions taken against predictions/recommendations."},
    {"name": "outcomes", "description": "Actual outcome recorded per prediction (one per prediction)."},
    {"name": "audit", "description": "Audit trail. Admin only."},
    {"name": "reports", "description": "Aggregated device-health and incident-summary reports."},
]

app = FastAPI(
    title="MPLS Predictive Copilot API",
    description=(
        "Backend for the Air-Gapped Predictive Copilot for Secure MPLS Operations.\n\n"
        "Authenticate via `POST /auth/login` and send the returned token as "
        "`Authorization: Bearer <token>`. Roles: **viewer** (read-only), "
        "**network_engineer** (operational read/write), **admin** (full access)."
    ),
    version="0.2.0",
    openapi_tags=tags_metadata,
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(devices.router)
app.include_router(telemetry.router)
app.include_router(alerts.router)
app.include_router(incidents.router)
app.include_router(predictions.router)
app.include_router(recommendations.router)
app.include_router(actions.router)
app.include_router(outcomes.router)
app.include_router(audit.router)
app.include_router(reports.router)


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "healthy"}