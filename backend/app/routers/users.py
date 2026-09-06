"""User management — admin only. password_hash is never returned by any endpoint."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.audit import write_audit
from app.core.database import get_db
from app.core.security import hash_password
from app.deps import require_role
from app.models import Role, User
from app.schemas import UserCreate, UserOut, UserUpdate


router = APIRouter(prefix="/users", tags=["users"])


def _get_user_or_404(db: Session, user_id: int) -> User:
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


def _check_role_exists(db: Session, role_id: int) -> None:
    if not db.query(Role).filter(Role.role_id == role_id).first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )


@router.get("", response_model=list[UserOut], summary="List users (admin only)")
def list_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _user=Depends(require_role("admin")),
):
    return db.query(User).offset(skip).limit(limit).all()


@router.get("/{user_id}", response_model=UserOut, summary="Get one user (admin only)")
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    _user=Depends(require_role("admin")),
):
    return _get_user_or_404(db, user_id)


@router.post(
    "",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a user (admin only)",
)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists",
        )

    _check_role_exists(db, payload.role_id)

    user = User(
        username=payload.username,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
        email=payload.email,
        role_id=payload.role_id,
    )

    db.add(user)
    db.flush()

    write_audit(
        db,
        current_user.user_id,
        "user",
        user.user_id,
        "create",
        {
            "username": user.username,
            "role_id": user.role_id,
        },
    )

    db.commit()
    db.refresh(user)

    return user


@router.put(
    "/{user_id}",
    response_model=UserOut,
    summary="Update a user (admin only)",
)
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    user = _get_user_or_404(db, user_id)
    data = payload.model_dump(exclude_unset=True)

    new_password = data.pop("password", None)

    if "role_id" in data:
        _check_role_exists(db, data["role_id"])

    for field, value in data.items():
        setattr(user, field, value)

    if new_password:
        user.password_hash = hash_password(new_password)

    write_audit(
        db,
        current_user.user_id,
        "user",
        user.user_id,
        "update",
        {
            "fields": sorted(data.keys())
            + (["password"] if new_password else [])
        },
    )

    db.commit()
    db.refresh(user)

    return user


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a user (admin only)",
)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    user = _get_user_or_404(db, user_id)

    if user.user_id == current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account",
        )

    write_audit(
        db,
        current_user.user_id,
        "user",
        user.user_id,
        "delete",
        {"username": user.username},
    )

    db.delete(user)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User has related records and cannot be deleted",
        )