from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.audit import write_audit
from app.core.database import get_db
from app.core.security import verify_password, create_access_token
from app.deps import get_current_user
from app.models import User
from app.schemas import LoginRequest, TokenResponse, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse, summary="Log in and receive a JWT")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == payload.username).first()

    if not user or not user.is_active or not verify_password(payload.password, user.password_hash):
        # Deliberately vague message — don't reveal whether the username exists
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    user.last_login_at = func.now()
    write_audit(db, user.user_id, "auth", user.user_id, "login",
                {"username": user.username, "role": user.role.role_name})
    db.commit()

    token = create_access_token(subject=user.username, role=user.role.role_name)
    return TokenResponse(access_token=token, role=user.role.role_name)


@router.get("/me", response_model=UserOut, summary="Get the currently authenticated user")
def read_me(current_user: User = Depends(get_current_user)):
    return current_user