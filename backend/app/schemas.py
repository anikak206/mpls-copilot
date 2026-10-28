"""Pydantic request schemas (validation at the API boundary)."""
import ipaddress
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

RoleName = Literal["Administrator", "Network Engineer", "Auditor"]
Severity = Literal["info", "warning", "major", "critical"]
DeviceType = Literal["PE", "P", "CE", "RR"]
DeviceStatus = Literal["up", "degraded", "down", "maintenance"]
IncidentStatus = Literal["open", "investigating", "mitigated", "closed"]
ActionType = Literal["config_change", "interface_reset", "traffic_reroute", "hardware_check", "escalation",
                     "monitoring", "other"]
OutcomeResult = Literal["resolved", "improved", "no_change", "worsened"]


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


def _email(value: str) -> str:
    value = value.lower()
    local, _, domain = value.partition("@")
    if not local or "." not in domain or " " in value:
        raise ValueError("Enter a valid email address")
    return value


class LoginIn(Strict):
    email: str = Field(min_length=5, max_length=120)
    password: str = Field(min_length=1, max_length=128)
    _v = field_validator("email")(_email)


class UserCreate(Strict):
    email: str = Field(min_length=5, max_length=120)
    full_name: str = Field(min_length=2, max_length=100)
    password: str = Field(min_length=10, max_length=128)
    role: RoleName
    _v = field_validator("email")(_email)


class UserUpdate(Strict):
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    password: Optional[str] = Field(None, min_length=10, max_length=128)
    role: Optional[RoleName] = None
    is_active: Optional[bool] = None


class SiteIn(Strict):
    name: str = Field(min_length=2, max_length=80)
    region: str = Field(min_length=2, max_length=80)
    address: Optional[str] = Field(None, max_length=255)


class DeviceBase(Strict):
    hostname: str = Field(min_length=2, max_length=64, pattern=r"^[A-Za-z0-9][A-Za-z0-9.\-_]*$")
    mgmt_ip: str
    device_type: DeviceType
    vendor: str = Field(min_length=2, max_length=40)
    model: str = Field(min_length=1, max_length=60)
    site_id: int = Field(gt=0)
    status: DeviceStatus = "up"
    assigned_engineer_id: Optional[int] = Field(None, gt=0)

    @field_validator("mgmt_ip")
    @classmethod
    def _ip(cls, v):
        try:
            return str(ipaddress.ip_address(v))
        except ValueError:
            raise ValueError("mgmt_ip must be a valid IPv4/IPv6 address")


class DeviceUpdate(DeviceBase):
    hostname: Optional[str] = Field(None, min_length=2, max_length=64, pattern=r"^[A-Za-z0-9][A-Za-z0-9.\-_]*$")
    mgmt_ip: Optional[str] = None
    device_type: Optional[DeviceType] = None
    vendor: Optional[str] = Field(None, min_length=2, max_length=40)
    model: Optional[str] = Field(None, min_length=1, max_length=60)
    site_id: Optional[int] = Field(None, gt=0)
    status: Optional[DeviceStatus] = None


class Features(Strict):
    cpu_util: float = Field(ge=0, le=100)
    mem_util: float = Field(ge=0, le=100)
    latency_ms: float = Field(ge=0, le=10000)
    jitter_ms: float = Field(ge=0, le=5000)
    packet_loss_pct: float = Field(ge=0, le=100)
    throughput_mbps: float = Field(ge=0, le=400000)
    crc_errors: int = Field(0, ge=0, le=10_000_000)
    lsp_flaps: int = Field(0, ge=0, le=100000)
    bgp_flaps: int = Field(0, ge=0, le=100000)


class TelemetryIn(Features):
    device_id: int = Field(gt=0)
    recorded_at: Optional[datetime] = None


class AlertCreate(Strict):
    device_id: int = Field(gt=0)
    severity: Severity
    message: str = Field(min_length=3, max_length=255)


class AlertUpdate(Strict):
    status: Literal["open", "acknowledged", "resolved"]


class IncidentCreate(Strict):
    device_id: int = Field(gt=0)
    title: str = Field(min_length=3, max_length=160)
    description: str = Field(min_length=3, max_length=5000)
    severity: Severity
    assigned_to: Optional[int] = Field(None, gt=0)


class IncidentUpdate(Strict):
    status: Optional[IncidentStatus] = None
    severity: Optional[Severity] = None
    description: Optional[str] = Field(None, min_length=3, max_length=5000)
    assigned_to: Optional[int] = Field(None, gt=0)


class PredictRequest(Strict):
    telemetry_id: Optional[int] = Field(None, gt=0)
    device_id: Optional[int] = Field(None, gt=0)
    features: Optional[Features] = None


class OutcomeIn(Strict):
    result: OutcomeResult
    notes: str = Field(min_length=3, max_length=5000)


class ActionCreate(Strict):
    device_id: int = Field(gt=0)
    recommendation_id: Optional[int] = Field(None, gt=0)
    incident_id: Optional[int] = Field(None, gt=0)
    action_type: ActionType
    description: str = Field(min_length=3, max_length=5000)
    outcome: Optional[OutcomeIn] = None
