"""Reporting SQL: JOIN/aggregate queries over views and the stored procedure (parameterized)."""
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models import User
from app.security import is_engineer

REPORTS = {
    "device-health": "Device health (view v_device_health)",
    "predictions": "Prediction report (view v_prediction_report)",
    "risk-summary": "Device risk summary (procedure sp_device_risk_summary)",
    "alerts": "Alert report (JOIN alerts, devices, sites)",
}


def _scope(user: User, alias: str, params: dict) -> str:
    if is_engineer(user):
        params["uid"] = user.user_id
        return f" AND {alias}.device_id IN (SELECT device_id FROM devices WHERE assigned_engineer_id = :uid)"
    return ""


def _rows(db: Session, sql: str, params: dict):
    result = db.execute(text(sql), params)
    columns = list(result.keys())
    return columns, [dict(zip(columns, row)) for row in result.fetchall()]


def fetch_report(db: Session, user: User, name: str, f: dict):
    params, where = {}, ""
    if name == "device-health":
        for key in ("status", "latest_risk_level", "site_name"):
            if f.get(key):
                where += f" AND v.{key} = :{key}"
                params[key] = f[key]
        if f.get("device_id"):
            where += " AND v.device_id = :device_id"
            params["device_id"] = f["device_id"]
        where += _scope(user, "v", params)
        return _rows(db, f"SELECT * FROM v_device_health v WHERE 1=1{where} ORDER BY v.latest_risk_score DESC", params)
    if name == "predictions":
        for key, col in (("risk_level", "risk_level"), ("label", "label"), ("device_id", "device_id")):
            if f.get(key):
                where += f" AND v.{col} = :{key}"
                params[key] = f[key]
        if f.get("date_from"):
            where += " AND v.created_at >= :date_from"
            params["date_from"] = f["date_from"]
        if f.get("date_to"):
            where += " AND v.created_at <= :date_to"
            params["date_to"] = f["date_to"]
        where += _scope(user, "v", params)
        return _rows(db, f"SELECT * FROM v_prediction_report v WHERE 1=1{where} "
                         "ORDER BY v.created_at DESC, v.prediction_id DESC LIMIT 1000", params)
    if name == "risk-summary":
        days = 7 if f.get("days") is None else int(f["days"])
        if not 1 <= days <= 365:
            raise ValueError("days must be between 1 and 365")
        columns, rows = _rows(db, "CALL sp_device_risk_summary(:days)", {"days": days})
        if is_engineer(user):
            allowed = {r[0] for r in db.execute(text("SELECT device_id FROM devices WHERE assigned_engineer_id=:u"),
                                                {"u": user.user_id})}
            rows = [r for r in rows if r["device_id"] in allowed]
        return columns, rows
    if name == "alerts":
        for key in ("status", "severity", "device_id"):
            if f.get(key):
                where += f" AND a.{key} = :{key}"
                params[key] = f[key]
        if f.get("date_from"):
            where += " AND a.created_at >= :date_from"
            params["date_from"] = f["date_from"]
        if f.get("date_to"):
            where += " AND a.created_at <= :date_to"
            params["date_to"] = f["date_to"]
        where += _scope(user, "a", params)
        return _rows(db, "SELECT a.alert_id, a.created_at, d.hostname, s.name AS site_name, a.severity, a.source, "
                         "a.status, a.message, a.incident_id FROM alerts a JOIN devices d ON d.device_id = a.device_id "
                         f"JOIN sites s ON s.site_id = d.site_id WHERE 1=1{where} ORDER BY a.created_at DESC LIMIT 1000",
                     params)
    raise KeyError(name)
