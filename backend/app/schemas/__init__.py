"""
Pydantic schemas. `devices` and `auth` are fully built out as the pattern to follow.
All other resources follow the same shape: one *Create, *Update (partial), and *Out
class per resource.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


# ---- Auth ----

class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str


# ---- Enum types (mirror the MySQL enums in database/schema.sql) ----

class AlertSeverity(str, Enum):
    info = "info"
    warning = "warning"
    critical = "critical"


class AlertStatus(str, Enum):
    open = "open"
    acknowledged = "acknowledged"
    closed = "closed"


class IncidentStatus(str, Enum):
    open = "open"
    in_progress = "in_progress"
    resolved = "resolved"
    closed = "closed"


class RiskLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class RecPriority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class OutcomeResult(str, Enum):
    failure_occurred = "failure_occurred"
    no_failure = "no_failure"
    false_positive = "false_positive"
    unknown = "unknown"


# ---- Users ----

class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=120)
    email: Optional[str] = Field(default=None, max_length=120)
    role_id: int


class UserUpdate(BaseModel):
    password: Optional[str] = Field(default=None, min_length=8, max_length=128)
    full_name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    email: Optional[str] = Field(default=None, max_length=120)
    role_id: Optional[int] = None
    is_active: Optional[bool] = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    username: str
    full_name: str
    email: Optional[str] = None
    role_id: int
    is_active: bool
    created_at: datetime
    last_login_at: Optional[datetime] = None


# ---- Devices ----

class DeviceCreate(BaseModel):
    hostname: str
    vendor: str
    model: Optional[str] = None
    mgmt_ip: str
    device_role: Optional[str] = None
    site: Optional[str] = None


class DeviceUpdate(BaseModel):
    hostname: Optional[str] = None
    vendor: Optional[str] = None
    model: Optional[str] = None
    mgmt_ip: Optional[str] = None
    device_role: Optional[str] = None
    site: Optional[str] = None
    is_active: Optional[bool] = None


class DeviceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    device_id: int
    hostname: str
    vendor: str
    model: Optional[str] = None
    mgmt_ip: str
    device_role: Optional[str] = None
    site: Optional[str] = None
    is_active: bool
    created_at: datetime


# ---- Telemetry ----

class TelemetryCreate(BaseModel):
    device_id: int
    metric_type: str = Field(min_length=1, max_length=40)
    metric_value: Decimal
    unit: Optional[str] = Field(default=None, max_length=20)
    collected_at: datetime


class TelemetryUpdate(BaseModel):
    metric_type: Optional[str] = Field(default=None, min_length=1, max_length=40)
    metric_value: Optional[Decimal] = None
    unit: Optional[str] = Field(default=None, max_length=20)
    collected_at: Optional[datetime] = None


class TelemetryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    telemetry_id: int
    device_id: int
    metric_type: str
    metric_value: Decimal
    unit: Optional[str] = None
    collected_at: datetime


# ---- Alerts ----

class AlertCreate(BaseModel):
    device_id: int
    alert_type: str = Field(min_length=1, max_length=60)
    severity: AlertSeverity = AlertSeverity.warning
    message: str = Field(min_length=1, max_length=500)


class AlertUpdate(BaseModel):
    alert_type: Optional[str] = Field(default=None, min_length=1, max_length=60)
    severity: Optional[AlertSeverity] = None
    message: Optional[str] = Field(default=None, min_length=1, max_length=500)
    status: Optional[AlertStatus] = None


class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    alert_id: int
    device_id: int
    alert_type: str
    severity: AlertSeverity
    message: str
    status: AlertStatus
    triggered_at: datetime
    resolved_at: Optional[datetime] = None


# ---- Incidents ----

class IncidentCreate(BaseModel):
    device_id: int
    alert_id: Optional[int] = None
    title: str = Field(min_length=1, max_length=200)
    description: Optional[str] = None


class IncidentUpdate(BaseModel):
    alert_id: Optional[int] = None
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = None
    status: Optional[IncidentStatus] = None


class IncidentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    incident_id: int
    device_id: int
    alert_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    status: IncidentStatus
    opened_by: Optional[int] = None
    opened_at: datetime
    closed_at: Optional[datetime] = None


# ---- Predictions ----

class PredictionCreate(BaseModel):
    device_id: int
    incident_id: Optional[int] = None
    model_version: str = Field(min_length=1, max_length=40)
    risk_score: Decimal = Field(ge=Decimal("0"), le=Decimal("1"))
    risk_level: RiskLevel
    prediction_horizon: Optional[str] = Field(default=None, max_length=40)
    contributing_factors: Optional[Any] = None


class PredictionUpdate(BaseModel):
    incident_id: Optional[int] = None
    model_version: Optional[str] = Field(default=None, min_length=1, max_length=40)
    risk_score: Optional[Decimal] = Field(default=None, ge=Decimal("0"), le=Decimal("1"))
    risk_level: Optional[RiskLevel] = None
    prediction_horizon: Optional[str] = Field(default=None, max_length=40)
    contributing_factors: Optional[Any] = None


class PredictionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    prediction_id: int
    device_id: int
    incident_id: Optional[int] = None
    model_version: str
    risk_score: Decimal
    risk_level: RiskLevel
    prediction_horizon: Optional[str] = None
    contributing_factors: Optional[Any] = None
    predicted_at: datetime


# ---- Recommendations ----

class RecommendationCreate(BaseModel):
    prediction_id: int
    recommendation_text: str = Field(min_length=1, max_length=1000)
    priority: RecPriority = RecPriority.medium


class RecommendationUpdate(BaseModel):
    recommendation_text: Optional[str] = Field(default=None, min_length=1, max_length=1000)
    priority: Optional[RecPriority] = None


class RecommendationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    recommendation_id: int
    prediction_id: int
    recommendation_text: str
    priority: RecPriority
    created_at: datetime


# ---- Engineer Actions ----

class EngineerActionCreate(BaseModel):
    prediction_id: int
    recommendation_id: Optional[int] = None
    action_taken: str = Field(min_length=1, max_length=500)
    action_notes: Optional[str] = None


class EngineerActionUpdate(BaseModel):
    recommendation_id: Optional[int] = None
    action_taken: Optional[str] = Field(default=None, min_length=1, max_length=500)
    action_notes: Optional[str] = None


class EngineerActionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    action_id: int
    prediction_id: int
    recommendation_id: Optional[int] = None
    user_id: int
    action_taken: str
    action_notes: Optional[str] = None
    action_at: datetime


# ---- Outcomes ----

class OutcomeCreate(BaseModel):
    prediction_id: int
    actual_result: OutcomeResult
    outcome_notes: Optional[str] = None


class OutcomeUpdate(BaseModel):
    actual_result: Optional[OutcomeResult] = None
    outcome_notes: Optional[str] = None


class OutcomeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    outcome_id: int
    prediction_id: int
    actual_result: OutcomeResult
    outcome_notes: Optional[str] = None
    recorded_by: Optional[int] = None
    recorded_at: datetime


# ---- Audit ----

class AuditOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    audit_id: int
    user_id: Optional[int] = None
    entity_type: str
    entity_id: int
    action: str
    details: Optional[Any] = None
    created_at: datetime