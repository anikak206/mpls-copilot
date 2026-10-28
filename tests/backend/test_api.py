"""Authentication, RBAC, validation, CRUD, ML workflow persistence, reports and audit logging."""
from app.config import settings

FEATURES = {"cpu_util": 35, "mem_util": 55, "latency_ms": 12, "jitter_ms": 1.2, "packet_loss_pct": 0.02,
            "throughput_mbps": 4200, "crc_errors": 0, "lsp_flaps": 0, "bgp_flaps": 0}


def test_login_invalid_and_me(client, admin):
    assert client.post("/api/auth/login", json={"email": settings.demo_users[0][1], "password": "wrong"}).status_code == 401
    assert client.post("/api/auth/login", json={"email": "not-an-email", "password": "x"}).status_code == 422
    me = client.get("/api/auth/me", headers=admin).json()
    assert me["role"] == "Administrator" and "password_hash" not in me
    assert client.get("/api/auth/me").status_code == 401
    assert client.get("/api/auth/me", headers={"Authorization": "Bearer garbage"}).status_code == 401


def test_password_is_bcrypt_hashed(client, db):
    from sqlalchemy import text
    hashes = [r[0] for r in db.execute(text("SELECT password_hash FROM users"))]
    assert hashes and all(h.startswith("$2b$") for h in hashes)


def test_logout_revokes_token(client):
    r = client.post("/api/auth/login", json={"email": settings.demo_users[2][1], "password": settings.demo_users[2][2]})
    headers = {"Authorization": f"Bearer {r.json()['access_token']}"}
    assert client.post("/api/auth/logout", headers=headers).status_code == 200
    assert client.get("/api/auth/me", headers=headers).status_code == 401


def test_bruteforce_lockout(client):
    for _ in range(5):
        client.post("/api/auth/login", json={"email": "nobody@lockout.test", "password": "bad"})
    assert client.post("/api/auth/login", json={"email": "nobody@lockout.test", "password": "bad"}).status_code == 429


def test_rbac_forbidden_actions(client, engineer, auditor):
    device = {"hostname": "rbac-test", "mgmt_ip": "192.0.2.10", "device_type": "PE", "vendor": "Test",
              "model": "M1", "site_id": 1}
    assert client.post("/api/devices", json=device, headers=auditor).status_code == 403
    assert client.post("/api/devices", json=device, headers=engineer).status_code == 403
    assert client.get("/api/users", headers=engineer).status_code == 403
    assert client.get("/api/users", headers=auditor).status_code == 403
    assert client.get("/api/audit-logs", headers=engineer).status_code == 403
    assert client.get("/api/audit-logs", headers=auditor).status_code == 200
    assert client.post("/api/telemetry", json={"device_id": 1, **FEATURES}, headers=auditor).status_code == 403
    assert client.post("/api/predictions/run", json={"telemetry_id": 1}, headers=auditor).status_code == 403


def test_engineer_sees_only_assigned_devices(client, engineer, admin):
    mine = client.get("/api/devices?page_size=100", headers=engineer).json()
    everything = client.get("/api/devices?page_size=100", headers=admin).json()
    assert 0 < mine["total"] < everything["total"]
    me = client.get("/api/auth/me", headers=engineer).json()
    assert all(d["assigned_engineer_id"] == me["user_id"] for d in mine["items"])
    other = next(d for d in everything["items"] if d["assigned_engineer_id"] != me["user_id"])
    assert client.get(f"/api/devices/{other['device_id']}", headers=engineer).status_code == 403


def test_device_crud_and_validation(client, admin):
    body = {"hostname": "pe9-test", "mgmt_ip": "192.0.2.99", "device_type": "PE", "vendor": "Test", "model": "M1",
            "site_id": 1}
    assert client.post("/api/devices", json={**body, "mgmt_ip": "999.1.1.1"}, headers=admin).status_code == 422
    assert client.post("/api/devices", json={**body, "device_type": "XX"}, headers=admin).status_code == 422
    created = client.post("/api/devices", json=body, headers=admin)
    assert created.status_code == 201
    device_id = created.json()["device_id"]
    assert client.post("/api/devices", json=body, headers=admin).status_code == 409
    assert client.get(f"/api/devices?q=pe9-test", headers=admin).json()["total"] == 1
    updated = client.patch(f"/api/devices/{device_id}", json={"status": "maintenance"}, headers=admin).json()
    assert updated["status"] == "maintenance"
    assert client.delete(f"/api/devices/{device_id}", headers=admin).status_code == 200
    assert client.get(f"/api/devices/{device_id}", headers=admin).status_code == 404


def test_pagination(client, admin):
    page1 = client.get("/api/telemetry?page=1&page_size=10", headers=admin).json()
    page2 = client.get("/api/telemetry?page=2&page_size=10", headers=admin).json()
    assert len(page1["items"]) == 10 and page1["total"] >= 576
    assert {i["telemetry_id"] for i in page1["items"]}.isdisjoint({i["telemetry_id"] for i in page2["items"]})
    assert client.get("/api/telemetry?page_size=500", headers=admin).status_code == 422


def test_telemetry_validation_and_trigger_alert(client, engineer):
    devices = client.get("/api/devices", headers=engineer).json()["items"]
    assert client.post("/api/telemetry", json={"device_id": devices[0]["device_id"], **FEATURES, "cpu_util": 120},
                       headers=engineer).status_code == 422
    r = client.post("/api/telemetry", json={"device_id": devices[0]["device_id"], **FEATURES, "packet_loss_pct": 6},
                    headers=engineer)
    assert r.status_code == 201 and r.json()["trigger_alerts"][0]["severity"] == "critical"


def test_prediction_workflow_persists(client, engineer, admin):
    device_id = client.get("/api/devices", headers=engineer).json()["items"][0]["device_id"]
    normal = client.post("/api/predictions/run", json={"device_id": device_id, "features": FEATURES}, headers=engineer)
    assert normal.status_code == 201, normal.text
    p = normal.json()
    assert p["label"] == "normal" and p["mode"] == "model" and p["recommendation"]["action_code"] == "CONTINUE_MONITORING"
    bad = {**FEATURES, "packet_loss_pct": 8, "latency_ms": 140, "jitter_ms": 25, "crc_errors": 600}
    anomalous = client.post("/api/predictions/run", json={"device_id": device_id, "features": bad}, headers=engineer).json()
    assert anomalous["label"] == "anomalous" and anomalous["risk_score"] >= 60
    assert "Advisory only" in anomalous["recommendation"]["rationale"]
    fetched = client.get(f"/api/predictions/{anomalous['prediction_id']}", headers=admin).json()
    assert fetched["recommendation"]["recommendation_id"] == anomalous["recommendation"]["recommendation_id"]
    ml_alerts = client.get("/api/alerts?source=ml&page_size=100", headers=admin).json()["items"]
    assert any(a["prediction_id"] == anomalous["prediction_id"] for a in ml_alerts)
    assert client.post("/api/predictions/run", json={}, headers=engineer).status_code == 422


def test_engineer_action_and_outcome(client, engineer):
    rec = client.get("/api/recommendations", headers=engineer).json()["items"][0]
    r = client.post("/api/actions", headers=engineer, json={
        "device_id": rec["device_id"], "recommendation_id": rec["recommendation_id"], "action_type": "interface_reset",
        "description": "Bounced interface after optics check"})
    assert r.status_code == 201 and r.json()["outcome"] is None
    action_id = r.json()["action_id"]
    o = client.post(f"/api/actions/{action_id}/outcome", json={"result": "resolved", "notes": "Loss cleared"}, headers=engineer)
    assert o.status_code == 201 and o.json()["outcome"]["result"] == "resolved"
    assert client.post(f"/api/actions/{action_id}/outcome", json={"result": "resolved", "notes": "dup"},
                       headers=engineer).status_code == 409


def test_incident_update_audited_by_trigger(client, engineer):
    incident = client.get("/api/incidents", headers=engineer).json()["items"][0]
    new_status = "mitigated" if incident["status"] != "mitigated" else "investigating"
    assert client.patch(f"/api/incidents/{incident['incident_id']}", json={"status": new_status},
                        headers=engineer).status_code == 200
    history = client.get(f"/api/incidents/{incident['incident_id']}", headers=engineer).json()["history"]
    assert history[-1]["action"] == "incident_status_changed" and history[-1]["user_id"] is not None


def test_reports_and_exports(client, auditor):
    for name in ("device-health", "predictions", "risk-summary", "alerts"):
        r = client.get(f"/api/reports/{name}", headers=auditor)
        assert r.status_code == 200 and r.json()["count"] >= 1, name
    csv = client.get("/api/reports/alerts/export?format=csv&severity=critical", headers=auditor)
    assert csv.status_code == 200 and csv.text.startswith("alert_id")
    pdf = client.get("/api/reports/device-health/export?format=pdf", headers=auditor)
    assert pdf.status_code == 200 and pdf.content[:4] == b"%PDF"
    assert client.get("/api/reports/risk-summary?days=0", headers=auditor).status_code == 422


def test_audit_logging_of_sensitive_operations(client, admin):
    actions = client.get("/api/audit-logs/actions", headers=admin).json()
    assert {"login_success", "login_failed", "logout", "prediction_run", "device_created"} <= set(actions)


def test_user_management(client, admin):
    r = client.post("/api/users", headers=admin, json={"email": "new.engineer@mpls.local", "full_name": "Test Engineer",
                                                        "password": "short", "role": "Network Engineer"})
    assert r.status_code == 422
    r = client.post("/api/users", headers=admin, json={"email": "new.engineer@mpls.local", "full_name": "Test Engineer",
                                                        "password": "LongEnough123", "role": "Network Engineer"})
    assert r.status_code == 201
    uid = r.json()["user_id"]
    assert client.patch(f"/api/users/{uid}", json={"role": "Auditor"}, headers=admin).json()["role"] == "Auditor"
    assert client.delete(f"/api/users/{uid}", headers=admin).status_code == 200
    assert client.post("/api/auth/login", json={"email": "new.engineer@mpls.local",
                                                "password": "LongEnough123"}).status_code == 401
