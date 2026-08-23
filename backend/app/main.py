from fastapi import FastAPI

from app.routers import (
    auth, devices, telemetry, alerts, incidents,
    predictions, recommendations, actions, outcomes, reports,
)

app = FastAPI(
    title="MPLS Predictive Copilot API",
    description="Backend for the Air-Gapped Predictive Copilot for Secure MPLS Operations.",
    version="0.1.0",
)

app.include_router(auth.router)
app.include_router(devices.router)
app.include_router(telemetry.router)
app.include_router(alerts.router)
app.include_router(incidents.router)
app.include_router(predictions.router)
app.include_router(recommendations.router)
app.include_router(actions.router)
app.include_router(outcomes.router)
app.include_router(reports.router)


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}
