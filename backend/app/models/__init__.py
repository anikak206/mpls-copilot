"""
SQLAlchemy models — these must stay in sync with /database/schema.sql.
If you change a table here, change schema.sql (or add a migration) to match,
and vice versa. Person 1 (SQL owner) is the source of truth for this file.
"""

from sqlalchemy import (
    Column, Integer, BigInteger, String, Boolean, DECIMAL, Text, JSON,
    TIMESTAMP, Enum, ForeignKey, func
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class Role(Base):
    __tablename__ = "roles"

    role_id = Column(Integer, primary_key=True, autoincrement=True)
    role_name = Column(String(50), unique=True, nullable=False)
    description = Column(String(255))
    created_at = Column(TIMESTAMP, server_default=func.now())

    users = relationship("User", back_populates="role")


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(64), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(120), nullable=False)
    email = Column(String(120))
    role_id = Column(Integer, ForeignKey("roles.role_id"), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    last_login_at = Column(TIMESTAMP, nullable=True)

    role = relationship("Role", back_populates="users")


class Device(Base):
    __tablename__ = "devices"

    device_id = Column(Integer, primary_key=True, autoincrement=True)
    hostname = Column(String(120), unique=True, nullable=False)
    vendor = Column(String(60), nullable=False)
    model = Column(String(80))
    mgmt_ip = Column(String(45), nullable=False)
    device_role = Column(String(40))
    site = Column(String(120))
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())


class Telemetry(Base):
    __tablename__ = "telemetry"

    telemetry_id = Column(BigInteger, primary_key=True, autoincrement=True)
    device_id = Column(Integer, ForeignKey("devices.device_id"), nullable=False)
    metric_type = Column(String(40), nullable=False)
    metric_value = Column(DECIMAL(12, 4), nullable=False)
    unit = Column(String(20))
    collected_at = Column(TIMESTAMP, nullable=False)


class Alert(Base):
    __tablename__ = "alerts"

    alert_id = Column(BigInteger, primary_key=True, autoincrement=True)
    device_id = Column(Integer, ForeignKey("devices.device_id"), nullable=False)
    alert_type = Column(String(60), nullable=False)
    severity = Column(Enum("info", "warning", "critical", name="alert_severity"), default="warning")
    message = Column(String(500), nullable=False)
    status = Column(Enum("open", "acknowledged", "closed", name="alert_status"), default="open")
    triggered_at = Column(TIMESTAMP, server_default=func.now())
    resolved_at = Column(TIMESTAMP, nullable=True)


class Incident(Base):
    __tablename__ = "incidents"

    incident_id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(Integer, ForeignKey("devices.device_id"), nullable=False)
    alert_id = Column(BigInteger, ForeignKey("alerts.alert_id"), nullable=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    status = Column(
        Enum("open", "in_progress", "resolved", "closed", name="incident_status"),
        default="open",
    )
    opened_by = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    opened_at = Column(TIMESTAMP, server_default=func.now())
    closed_at = Column(TIMESTAMP, nullable=True)


class Prediction(Base):
    __tablename__ = "predictions"

    prediction_id = Column(BigInteger, primary_key=True, autoincrement=True)
    device_id = Column(Integer, ForeignKey("devices.device_id"), nullable=False)
    incident_id = Column(Integer, ForeignKey("incidents.incident_id"), nullable=True)
    model_version = Column(String(40), nullable=False)
    risk_score = Column(DECIMAL(5, 4), nullable=False)
    risk_level = Column(
        Enum("low", "medium", "high", "critical", name="risk_level"), nullable=False
    )
    prediction_horizon = Column(String(40))
    contributing_factors = Column(JSON)
    predicted_at = Column(TIMESTAMP, server_default=func.now())


class Recommendation(Base):
    __tablename__ = "recommendations"

    recommendation_id = Column(Integer, primary_key=True, autoincrement=True)
    prediction_id = Column(BigInteger, ForeignKey("predictions.prediction_id"), nullable=False)
    recommendation_text = Column(String(1000), nullable=False)
    priority = Column(Enum("low", "medium", "high", name="rec_priority"), default="medium")
    created_at = Column(TIMESTAMP, server_default=func.now())


class EngineerAction(Base):
    __tablename__ = "engineer_actions"

    action_id = Column(Integer, primary_key=True, autoincrement=True)
    prediction_id = Column(BigInteger, ForeignKey("predictions.prediction_id"), nullable=False)
    recommendation_id = Column(Integer, ForeignKey("recommendations.recommendation_id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    action_taken = Column(String(500), nullable=False)
    action_notes = Column(Text)
    action_at = Column(TIMESTAMP, server_default=func.now())


class Outcome(Base):
    __tablename__ = "outcomes"

    outcome_id = Column(Integer, primary_key=True, autoincrement=True)
    prediction_id = Column(BigInteger, ForeignKey("predictions.prediction_id"), nullable=False, unique=True)
    actual_result = Column(
        Enum("failure_occurred", "no_failure", "false_positive", "unknown", name="outcome_result"),
        nullable=False,
    )
    outcome_notes = Column(Text)
    recorded_by = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    recorded_at = Column(TIMESTAMP, server_default=func.now())


class AuditLog(Base):
    __tablename__ = "audit_log"

    audit_id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    entity_type = Column(String(60), nullable=False)
    entity_id = Column(BigInteger, nullable=False)
    action = Column(String(60), nullable=False)
    details = Column(JSON)
    created_at = Column(TIMESTAMP, server_default=func.now())