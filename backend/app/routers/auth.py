from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_access_token, verify_password
from app.models import User


router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"]
)


@router.post("/login")
def login(
    username: str,
    password: str,
    db: Session = Depends(get_db)
):
    user = (
        db.query(User)
        .filter(
            User.username == username,
            User.is_active == True
        )
        .first()
    )

    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    access_token = create_access_token(
        subject=user.username,
        role=user.role.role_name
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role.role_name
    }