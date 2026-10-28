"""Dict serializers for API responses (no raw ORM objects leave the API)."""
from app.utils import iso


def user_out(u):
    return {"user_id": u.user_id, "email": u.email, "full_name": u.full_name, "role": u.role.name,
            "is_active": u.is_active, "created_at": iso(u.created_at), "last_login_at": iso(u.last_login_at)}


def device_out(d):
    return {"device_id": d.device_id, "hostname": d.hostname, "mgmt_ip": d.mgmt_ip, "device_type": d.device_type,
            "vendor": d.vendor, "model": d.model, "site_id": d.site_id, "site_name": d.site.name,
            "region": d.site.region, "status": d.status, "assigned_engineer_id": d.assigned_engineer_id,
            "assigned_engineer": d.engineer.full_name if d.engineer else None,
            "created_at": iso(d.created_at), "updated_at": iso(d.updated_at)}


FEATURE_COLS = ["cpu_util", "mem_util", "latency_ms", "jitter_ms", "packet_loss_pct", "throughput_mbps",
                "crc_errors", "lsp_flaps", "bgp_flaps"]


def telemetry_out(t):
    data = {c: getattr(t, c) for c in FEATURE_COLS}
    data.update({"telemetry_id": t.telemetry_id, "device_id": t.device_id, "hostname": t.device.hostname,
                 "recorded_at": iso(t.recorded_at), "source": t.source, "recorded_by": t.recorded_by})
    return data


def recommendation_out(r):
    if r is None:
        return None
    return {"recommendation_id": r.recommendation_id, "prediction_id": r.prediction_id, "action_code": r.action_code,
            "title": r.title, "rationale": r.rationale, "priority": r.priority, "created_at": iso(r.created_at)}


def prediction_out(p):
    return {"prediction_id": p.prediction_id, "telemetry_id": p.telemetry_id, "device_id": p.telemetry.device_id,
            "hostname": p.telemetry.device.hostname, "model_version": p.model_version, "mode": p.mode,
            "label": p.label, "anomaly_score": p.anomaly_score, "risk_score": p.risk_score,
            "risk_level": p.risk_level, "explanation": p.explanation, "created_at": iso(p.created_at),
            "features": {c: getattr(p.telemetry, c) for c in FEATURE_COLS},
            "recommendation": recommendation_out(p.recommendation)}


def alert_out(a):
    return {"alert_id": a.alert_id, "device_id": a.device_id, "hostname": a.device.hostname,
            "telemetry_id": a.telemetry_id, "prediction_id": a.prediction_id, "incident_id": a.incident_id,
            "severity": a.severity, "source": a.source, "message": a.message, "status": a.status,
            "acknowledged_by": a.acknowledged_by, "created_at": iso(a.created_at), "resolved_at": iso(a.resolved_at)}


def incident_out(i):
    return {"incident_id": i.incident_id, "device_id": i.device_id, "hostname": i.device.hostname,
            "title": i.title, "description": i.description, "severity": i.severity, "status": i.status,
            "opened_by": i.opened_by, "assigned_to": i.assigned_to,
            "assignee": i.assignee.full_name if i.assignee else None,
            "opened_at": iso(i.opened_at), "closed_at": iso(i.closed_at)}


def outcome_out(o):
    if o is None:
        return None
    return {"outcome_id": o.outcome_id, "action_id": o.action_id, "result": o.result, "notes": o.notes,
            "recorded_by": o.recorded_by, "recorded_at": iso(o.recorded_at)}


def action_out(a):
    return {"action_id": a.action_id, "device_id": a.device_id, "hostname": a.device.hostname,
            "recommendation_id": a.recommendation_id, "incident_id": a.incident_id, "engineer_id": a.engineer_id,
            "engineer": a.engineer.full_name, "action_type": a.action_type, "description": a.description,
            "performed_at": iso(a.performed_at), "outcome": outcome_out(a.outcome)}


def audit_out(a):
    return {"audit_id": a.audit_id, "user_id": a.user_id, "user_email": a.user.email if a.user else None,
            "action": a.action, "entity_type": a.entity_type, "entity_id": a.entity_id, "details": a.details,
            "ip_address": a.ip_address, "created_at": iso(a.created_at)}
