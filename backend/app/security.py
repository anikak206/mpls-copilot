"""Password hashing (bcrypt), JWT issuing/validation, revocation and role/scope guards."""
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Device, RevokedToken, User

ADMIN, ENGINEER, AUDITOR = "Administrator", "Network Engineer", "Auditor"
ALL_ROLES = (ADMIN, ENGINEER, AUDITOR)
OPERATORS = (ADMIN, ENGINEER)
ALGORITHM = "HS256"
bearer = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(user: User):
    now = datetime.now(timezone.utc)
    expires = now + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": str(user.user_id), "role": user.role.name, "jti": str(uuid.uuid4()),
               "iat": now, "exp": expires, "type": "access"}
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM), expires


def _unauthorized(detail: str):
    return HTTPException(status.HTTP_401_UNAUTHORIZED, detail, headers={"WWW-Authenticate": "Bearer"})


def get_current_user(request: Request, creds: HTTPAuthorizationCredentials = Depends(bearer),
                     db: Session = Depends(get_db)) -> User:
    if creds is None:
        raise _unauthorized("Not authenticated")
    try:
        payload = jwt.decode(creds.credentials, settings.jwt_secret, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise _unauthorized("Session expired, please sign in again")
    except jwt.InvalidTokenError:
        raise _unauthorized("Invalid token")
    if payload.get("type") != "access" or db.get(RevokedToken, payload.get("jti", "")):
        raise _unauthorized("Token is no longer valid")
    user = db.get(User, int(payload["sub"]))
    if user is None or not user.is_active:
        raise _unauthorized("Account not found or disabled")
    request.state.token_payload = payload
    return user


def require_roles(*roles: str):
    def guard(user: User = Depends(get_current_user)) -> User:
        if user.role.name not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Your role is not permitted to perform this action")
        return user
    return guard


def is_engineer(user: User) -> bool:
    return user.role.name == ENGINEER


def scope_to_assigned(stmt, user: User, device_col):
    """Network Engineers only see operational data for devices assigned to them."""
    if is_engineer(user):
        assigned = select(Device.device_id).where(Device.assigned_engineer_id == user.user_id)
        return stmt.where(device_col.in_(assigned))
    return stmt


def get_accessible_device(db: Session, user: User, device_id: int) -> Device:
    device = db.get(Device, device_id)
    if device is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Device not found")
    if is_engineer(user) and device.assigned_engineer_id != user.user_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Device is not assigned to you")
    return device
