from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_error

    username = payload.get("sub")
    user = db.query(User).filter(User.username == username).first()

    if user is None or not user.is_active:
        raise credentials_error

    return user


def require_role(*allowed_roles: str):
    """
    Usage:
    @router.post(..., dependencies=[Depends(require_role("admin"))])

    or:
    current_user: User = Depends(
        require_role("admin", "network_engineer")
    )
    """

    def checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role.role_name not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of roles: {', '.join(allowed_roles)}",
            )
        return current_user

    return checker