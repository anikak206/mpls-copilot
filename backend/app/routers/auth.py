from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AuditLog, RevokedToken, User
from app.schemas import LoginIn
from app.security import create_access_token, get_current_user, verify_password
from app.serializers import user_out
from app.utils import log_audit

router = APIRouter(prefix="/api/auth", tags=["Authentication"])
MAX_FAILED, LOCK_MINUTES = 5, 15


@router.post("/login")
def login(body: LoginIn, request: Request, db: Session = Depends(get_db)):
    since = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=LOCK_MINUTES)
    failures = db.scalar(select(func.count()).select_from(AuditLog).where(
        AuditLog.action == "login_failed", AuditLog.entity_id == body.email, AuditLog.created_at >= since))
    if failures >= MAX_FAILED:
        raise HTTPException(429, f"Too many failed attempts. Try again in {LOCK_MINUTES} minutes.")
    user = db.scalar(select(User).where(User.email == body.email))
    if user is None or not user.is_active or not verify_password(body.password, user.password_hash):
        log_audit(db, user.user_id if user else None, "login_failed", "user", body.email, request=request)
        db.commit()
        raise HTTPException(401, "Invalid email or password")
    token, expires = create_access_token(user)
    user.last_login_at = datetime.now(timezone.utc).replace(tzinfo=None)
    log_audit(db, user.user_id, "login_success", "user", user.user_id, request=request)
    db.commit()
    return {"access_token": token, "token_type": "bearer", "expires_at": expires.isoformat(), "user": user_out(user)}


@router.post("/logout")
def logout(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    payload = request.state.token_payload
    db.add(RevokedToken(jti=payload["jti"], user_id=user.user_id,
                        expires_at=datetime.fromtimestamp(payload["exp"], timezone.utc).replace(tzinfo=None)))
    log_audit(db, user.user_id, "logout", "user", user.user_id, request=request)
    db.commit()
    return {"detail": "Signed out; token revoked"}


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return user_out(user)
