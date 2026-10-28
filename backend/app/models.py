"""ORM models. This metadata is the single source of truth for the MySQL schema (3NF)."""
from datetime import datetime
from typing import Optional

from sqlalchemy import (Boolean, CheckConstraint, DateTime, Float, ForeignKey, Index, Integer, String, Text,
                        UniqueConstraint, func)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

SEVERITIES = "('info','warning','major','critical')"


def created_col():
    return mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())


class Role(Base):
    __tablename__ = "roles"
    role_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(40), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(String(255), nullable=False)


class User(Base):
    __tablename__ = "users"
    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.role_id", ondelete="RESTRICT"), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="1")
    created_at: Mapped[datetime] = created_col()
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    role: Mapped[Role] = relationship(lazy="joined")
    __table_args__ = (CheckConstraint("email LIKE '%_@_%'", name="ck_users_email_format"),)


class RevokedToken(Base):
    __tablename__ = "revoked_tokens"
    jti: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    revoked_at: Mapped[datetime] = created_col()


class Site(Base):
    __tablename__ = "sites"
    site_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    region: Mapped[str] = mapped_column(String(80), nullable=False)
    address: Mapped[Optional[str]] = mapped_column(String(255))


class Device(Base):
    __tablename__ = "devices"
    device_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    hostname: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    mgmt_ip: Mapped[str] = mapped_column(String(45), nullable=False, unique=True)
    device_type: Mapped[str] = mapped_column(String(4), nullable=False)
    vendor: Mapped[str] = mapped_column(String(40), nullable=False)
    model: Mapped[str] = mapped_column(String(60), nullable=False)
    site_id: Mapped[int] = mapped_column(ForeignKey("sites.site_id", ondelete="RESTRICT"), nullable=False, index=True)
    assigned_engineer_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.user_id", ondelete="SET NULL"), index=True)
    status: Mapped[str] = mapped_column(String(12), nullable=False, server_default="up")
    created_at: Mapped[datetime] = created_col()
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp(),
                                                 onupdate=func.current_timestamp())
    site: Mapped[Site] = relationship(lazy="joined")
    engineer: Mapped[Optional[User]] = relationship(lazy="joined")
    __table_args__ = (
        CheckConstraint("device_type IN ('PE','P','CE','RR')", name="ck_devices_type"),
        CheckConstraint("status IN ('up','degraded','down','maintenance')", name="ck_devices_status"),
        Index("ix_devices_status", "status"),
    )


class Telemetry(Base):
    __tablename__ = "telemetry"
    telemetry_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.device_id", ondelete="CASCADE"), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())
    cpu_util: Mapped[float] = mapped_column(Float, nullable=False)
    mem_util: Mapped[float] = mapped_column(Float, nullable=False)
    latency_ms: Mapped[float] = mapped_column(Float, nullable=False)
    jitter_ms: Mapped[float] = mapped_column(Float, nullable=False)
    packet_loss_pct: Mapped[float] = mapped_column(Float, nullable=False)
    throughput_mbps: Mapped[float] = mapped_column(Float, nullable=False)
    crc_errors: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    lsp_flaps: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    bgp_flaps: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    source: Mapped[str] = mapped_column(String(10), nullable=False, server_default="collector")
    recorded_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.user_id", ondelete="SET NULL"))
    device: Mapped[Device] = relationship(lazy="joined")
    __table_args__ = (
        CheckConstraint("cpu_util BETWEEN 0 AND 100", name="ck_tel_cpu"),
        CheckConstraint("mem_util BETWEEN 0 AND 100", name="ck_tel_mem"),
        CheckConstraint("latency_ms >= 0 AND latency_ms <= 10000", name="ck_tel_latency"),
        CheckConstraint("jitter_ms >= 0 AND jitter_ms <= 5000", name="ck_tel_jitter"),
        CheckConstraint("packet_loss_pct BETWEEN 0 AND 100", name="ck_tel_loss"),
        CheckConstraint("throughput_mbps >= 0", name="ck_tel_throughput"),
        CheckConstraint("crc_errors >= 0 AND lsp_flaps >= 0 AND bgp_flaps >= 0", name="ck_tel_counters"),
        CheckConstraint("source IN ('manual','collector','seed')", name="ck_tel_source"),
        Index("ix_telemetry_device_time", "device_id", "recorded_at"),
        Index("ix_telemetry_time", "recorded_at"),
    )


class Prediction(Base):
    __tablename__ = "predictions"
    prediction_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telemetry_id: Mapped[int] = mapped_column(ForeignKey("telemetry.telemetry_id", ondelete="CASCADE"), nullable=False)
    model_version: Mapped[str] = mapped_column(String(40), nullable=False)
    mode: Mapped[str] = mapped_column(String(5), nullable=False)
    label: Mapped[str] = mapped_column(String(10), nullable=False)
    anomaly_score: Mapped[float] = mapped_column(Float, nullable=False)
    risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(8), nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    requested_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.user_id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = created_col()
    telemetry: Mapped[Telemetry] = relationship(lazy="joined")
    recommendation: Mapped[Optional["Recommendation"]] = relationship(back_populates="prediction", uselist=False,
                                                                      lazy="joined")
    __table_args__ = (
        CheckConstraint("mode IN ('model','demo')", name="ck_pred_mode"),
        CheckConstraint("label IN ('normal','anomalous','uncertain')", name="ck_pred_label"),
        CheckConstraint("risk_score BETWEEN 0 AND 100", name="ck_pred_risk"),
        CheckConstraint("risk_level IN ('low','medium','high','critical')", name="ck_pred_level"),
        Index("ix_predictions_telemetry", "telemetry_id"),
        Index("ix_predictions_created", "created_at"),
        Index("ix_predictions_level", "risk_level"),
    )


class Recommendation(Base):
    __tablename__ = "recommendations"
    recommendation_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    prediction_id: Mapped[int] = mapped_column(ForeignKey("predictions.prediction_id", ondelete="CASCADE"),
                                               nullable=False, unique=True)
    action_code: Mapped[str] = mapped_column(String(40), nullable=False)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(String(8), nullable=False)
    created_at: Mapped[datetime] = created_col()
    prediction: Mapped[Prediction] = relationship(back_populates="recommendation")
    __table_args__ = (CheckConstraint("priority IN ('low','medium','high','urgent')", name="ck_rec_priority"),)


class Incident(Base):
    __tablename__ = "incidents"
    incident_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.device_id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(8), nullable=False)
    status: Mapped[str] = mapped_column(String(13), nullable=False, server_default="open")
    opened_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.user_id", ondelete="SET NULL"))
    assigned_to: Mapped[Optional[int]] = mapped_column(ForeignKey("users.user_id", ondelete="SET NULL"))
    opened_at: Mapped[datetime] = created_col()
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    device: Mapped[Device] = relationship(lazy="joined")
    assignee: Mapped[Optional[User]] = relationship(foreign_keys=[assigned_to], lazy="joined")
    __table_args__ = (
        CheckConstraint(f"severity IN {SEVERITIES}", name="ck_inc_severity"),
        CheckConstraint("status IN ('open','investigating','mitigated','closed')", name="ck_inc_status"),
        Index("ix_incidents_status", "status"),
    )


class Alert(Base):
    __tablename__ = "alerts"
    alert_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.device_id", ondelete="CASCADE"), nullable=False)
    telemetry_id: Mapped[Optional[int]] = mapped_column(ForeignKey("telemetry.telemetry_id", ondelete="SET NULL"))
    prediction_id: Mapped[Optional[int]] = mapped_column(ForeignKey("predictions.prediction_id", ondelete="SET NULL"))
    incident_id: Mapped[Optional[int]] = mapped_column(ForeignKey("incidents.incident_id", ondelete="SET NULL"), index=True)
    severity: Mapped[str] = mapped_column(String(8), nullable=False)
    source: Mapped[str] = mapped_column(String(7), nullable=False)
    message: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(12), nullable=False, server_default="open")
    acknowledged_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.user_id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = created_col()
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    device: Mapped[Device] = relationship(lazy="joined")
    __table_args__ = (
        CheckConstraint(f"severity IN {SEVERITIES}", name="ck_alert_severity"),
        CheckConstraint("source IN ('trigger','ml','manual')", name="ck_alert_source"),
        CheckConstraint("status IN ('open','acknowledged','resolved')", name="ck_alert_status"),
        Index("ix_alerts_device_status", "device_id", "status"),
        Index("ix_alerts_created", "created_at"),
    )


class EngineerAction(Base):
    __tablename__ = "engineer_actions"
    action_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.device_id", ondelete="CASCADE"), nullable=False, index=True)
    recommendation_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("recommendations.recommendation_id", ondelete="SET NULL"), index=True)
    incident_id: Mapped[Optional[int]] = mapped_column(ForeignKey("incidents.incident_id", ondelete="SET NULL"), index=True)
    engineer_id: Mapped[int] = mapped_column(ForeignKey("users.user_id", ondelete="RESTRICT"), nullable=False)
    action_type: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    performed_at: Mapped[datetime] = created_col()
    device: Mapped[Device] = relationship(lazy="joined")
    engineer: Mapped[User] = relationship(lazy="joined")
    outcome: Mapped[Optional["Outcome"]] = relationship(uselist=False, lazy="joined", back_populates="action")
    __table_args__ = (CheckConstraint(
        "action_type IN ('config_change','interface_reset','traffic_reroute','hardware_check','escalation',"
        "'monitoring','other')", name="ck_action_type"),)


class Outcome(Base):
    __tablename__ = "outcomes"
    outcome_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    action_id: Mapped[int] = mapped_column(ForeignKey("engineer_actions.action_id", ondelete="CASCADE"),
                                           nullable=False, unique=True)
    result: Mapped[str] = mapped_column(String(10), nullable=False)
    notes: Mapped[str] = mapped_column(Text, nullable=False)
    recorded_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.user_id", ondelete="SET NULL"))
    recorded_at: Mapped[datetime] = created_col()
    action: Mapped[EngineerAction] = relationship(back_populates="outcome")
    __table_args__ = (CheckConstraint("result IN ('resolved','improved','no_change','worsened')",
                                      name="ck_outcome_result"),)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    audit_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.user_id", ondelete="SET NULL"), index=True)
    action: Mapped[str] = mapped_column(String(60), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(40), nullable=False)
    entity_id: Mapped[Optional[str]] = mapped_column(String(120))
    details: Mapped[Optional[str]] = mapped_column(Text)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    created_at: Mapped[datetime] = created_col()
    user: Mapped[Optional[User]] = relationship(lazy="joined")
    __table_args__ = (
        Index("ix_audit_created", "created_at"),
        Index("ix_audit_entity", "entity_type", "entity_id"),
        Index("ix_audit_action", "action"),
    )


__all__ = ["Role", "User", "RevokedToken", "Site", "Device", "Telemetry", "Prediction", "Recommendation",
           "Incident", "Alert", "EngineerAction", "Outcome", "AuditLog", "UniqueConstraint"]
