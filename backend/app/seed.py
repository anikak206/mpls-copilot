"""Idempotent development seed: roles, demo users (passwords from .env), sites, devices, telemetry,
predictions, incidents, actions. Run directly with: python -m app.seed (from backend/)."""
from datetime import timedelta

import numpy as np
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal, engine
from app.models import (Alert, Device, EngineerAction, Incident, Outcome, Prediction, Role, Site, Telemetry, User)
from app.prediction_service import run_prediction
from app.security import ADMIN, AUDITOR, ENGINEER, hash_password, verify_password
from ml.data.generator import inject, normal_samples

ROLES = [(ADMIN, "Manages users, roles, devices and all operational records"),
         (ENGINEER, "Operates assigned devices: telemetry, predictions, actions and outcomes"),
         (AUDITOR, "Read-only access to operational records, reports and audit logs")]
SITES = [("Core POP North", "North", None), ("Core POP South", "South", None),
         ("Metro Edge East", "East", None), ("Metro Edge West", "West", None)]
DEVICES = [  # hostname, type, vendor, model, site index, engineer slot (0=eng1, 1=eng2, None)
    ("rr1-core-n", "RR", "Cisco", "ASR 9901", 0, 0), ("p1-core-n", "P", "Juniper", "MX480", 0, 0),
    ("p2-core-s", "P", "Juniper", "MX480", 1, 0), ("pe1-edge-e", "PE", "Nokia", "7750 SR-1", 2, 0),
    ("pe2-edge-e", "PE", "Nokia", "7750 SR-1", 2, 0), ("pe3-edge-w", "PE", "Cisco", "ASR 9903", 3, 0),
    ("pe4-edge-w", "PE", "Cisco", "ASR 9903", 3, 0), ("ce1-cust-e", "CE", "Cisco", "ISR 4451", 2, 0),
    ("ce2-cust-w", "CE", "Juniper", "SRX1500", 3, 1), ("pe5-edge-s", "PE", "Juniper", "MX204", 1, 1),
    ("p3-core-s", "P", "Nokia", "7750 SR-7", 1, None), ("ce3-cust-n", "CE", "Cisco", "ISR 4331", 0, None),
]
ANOMALIES = {"p2-core-s": ("congestion", 6), "pe1-edge-e": ("control_plane_instability", 5),
             "ce2-cust-w": ("link_degradation", 3)}
HOURS = 48


def sync_users(db: Session):
    roles = {r.name: r for r in db.scalars(select(Role))}
    users = list(settings.demo_users) + [(ENGINEER, "engineer2@mpls.local", settings.demo_users[1][2],
                                          "Network Engineer (Shift B)")]
    for role, email, password, name in users:
        if not email or not password:
            continue
        user = db.scalar(select(User).where(User.email == email.lower()))
        if user is None:
            db.add(User(email=email.lower(), full_name=name, password_hash=hash_password(password),
                        role_id=roles[role].role_id))
        elif not verify_password(password, user.password_hash):
            user.password_hash = hash_password(password)
    db.commit()


def seed_operational(db: Session):
    rng = np.random.default_rng(7)
    admin = db.scalar(select(User).where(User.email == settings.demo_users[0][1].lower()))
    engineers = db.scalars(select(User).join(Role).where(Role.name == ENGINEER).order_by(User.user_id)).all()
    sites = [Site(name=n, region=r, address=a) for n, r, a in SITES]
    db.add_all(sites)
    db.flush()
    now = db.scalar(text("SELECT NOW()")).replace(minute=0, second=0, microsecond=0)
    devices = []
    for i, (host, dtype, vendor, model, site_idx, eng) in enumerate(DEVICES):
        device = Device(hostname=host, mgmt_ip=f"10.20.{site_idx}.{10 + i}", device_type=dtype, vendor=vendor,
                        model=model, site_id=sites[site_idx].site_id,
                        assigned_engineer_id=engineers[eng].user_id if eng is not None and eng < len(engineers) else None,
                        status="degraded" if host in ANOMALIES else ("maintenance" if host == "ce3-cust-n" else "up"))
        db.add(device)
        devices.append(device)
    db.flush()
    for device in devices:
        frame = normal_samples(HOURS, rng, load=rng.uniform(0.7, 1.2))
        kind = ANOMALIES.get(device.hostname)
        if kind:
            tail = frame.iloc[-kind[1]:]
            frame.iloc[-kind[1]:] = inject(tail, kind[0], rng, np.linspace(0.5, 1.0, kind[1])).to_numpy()
        for h, row in enumerate(frame.itertuples(index=False)):
            values = row._asdict()
            for c in ("crc_errors", "lsp_flaps", "bgp_flaps"):
                values[c] = int(values[c])
            db.add(Telemetry(device_id=device.device_id, recorded_at=now - timedelta(hours=HOURS - 1 - h),
                             source="seed", **{k: (round(v, 3) if isinstance(v, float) else v) for k, v in values.items()}))
    db.flush()
    for device in devices:
        latest = db.scalars(select(Telemetry).where(Telemetry.device_id == device.device_id)
                            .order_by(Telemetry.recorded_at.desc()).limit(3)).all()
        for sample in reversed(latest):
            run_prediction(db, sample, admin.user_id)
    db.commit()

    eng1 = engineers[0]
    p2 = next(d for d in devices if d.hostname == "p2-core-s")
    incident = Incident(device_id=p2.device_id, title="Congestion on core path p2-core-s",
                        description="Latency, jitter and loss rising on LSPs transiting p2-core-s.",
                        severity="major", status="investigating", opened_by=admin.user_id, assigned_to=eng1.user_id)
    db.add(incident)
    db.flush()
    rec = db.scalars(select(Prediction).join(Telemetry).where(Telemetry.device_id == p2.device_id)
                     .order_by(Prediction.risk_score.desc())).first().recommendation
    action = EngineerAction(device_id=p2.device_id, recommendation_id=rec.recommendation_id,
                            incident_id=incident.incident_id, engineer_id=eng1.user_id, action_type="traffic_reroute",
                            description="Re-optimised RSVP-TE LSPs to shift traffic away from the congested link.")
    db.add(action)
    db.flush()
    db.add(Outcome(action_id=action.action_id, result="improved", recorded_by=eng1.user_id,
                   notes="Latency reduced; loss still above baseline. Monitoring continues."))
    for alert in db.scalars(select(Alert).where(Alert.device_id == p2.device_id).limit(2)):
        alert.incident_id, alert.status = incident.incident_id, "acknowledged"
    pe1 = next(d for d in devices if d.hostname == "pe1-edge-e")
    db.add(EngineerAction(device_id=pe1.device_id, engineer_id=eng1.user_id, action_type="monitoring",
                          description="Enabled detailed RSVP/LDP logging to investigate LSP flaps."))
    db.commit()


def run_seed():
    with SessionLocal() as db:
        if not db.scalar(select(Role).limit(1)):
            db.add_all([Role(name=n, description=d) for n, d in ROLES])
            db.commit()
        sync_users(db)
        if not db.scalar(select(Device).limit(1)):
            seed_operational(db)


if __name__ == "__main__":
    run_seed()
    print("Seed complete on", engine.url.database)
