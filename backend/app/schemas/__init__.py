"""
Pydantic schemas. `devices` and `auth` are fully built out as the pattern to follow.
TODO (Person 1): add matching schemas for telemetry, alerts, incidents, predictions,
recommendations, engineer_actions, and outcomes as you build each router —
one *Create, *Update (if needed), and *Out class per resource, same shape as below.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


# ---- Auth ----

class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str


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
