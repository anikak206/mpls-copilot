from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Role, User
from app.schemas import UserCreate, UserUpdate
from app.security import ADMIN, ENGINEER, hash_password, require_roles
from app.serializers import user_out
from app.utils import PageParams, log_audit, paginate

router = APIRouter(prefix="/api", tags=["Users & Roles"])
admin_only = require_roles(ADMIN)


def _role(db: Session, name: str) -> Role:
    return db.scalar(select(Role).where(Role.name == name))


@router.get("/roles")
def list_roles(db: Session = Depends(get_db), _=Depends(admin_only)):
    return [{"role_id": r.role_id, "name": r.name, "description": r.description}
            for r in db.scalars(select(Role).order_by(Role.role_id))]


@router.get("/users")
def list_users(q: Optional[str] = None, role: Optional[str] = None, is_active: Optional[bool] = None,
               params: PageParams = Depends(), db: Session = Depends(get_db), _=Depends(admin_only)):
    stmt = select(User).join(Role).order_by(User.user_id)
    if q:
        stmt = stmt.where(or_(User.email.contains(q), User.full_name.contains(q)))
    if role:
        stmt = stmt.where(Role.name == role)
    if is_active is not None:
        stmt = stmt.where(User.is_active == is_active)
    return paginate(db, stmt, params, user_out)


@router.get("/users/engineers")
def list_engineers(db: Session = Depends(get_db), _=Depends(require_roles(ADMIN, ENGINEER))):
    stmt = select(User).join(Role).where(Role.name == ENGINEER, User.is_active.is_(True)).order_by(User.full_name)
    return [{"user_id": u.user_id, "full_name": u.full_name} for u in db.scalars(stmt)]


@router.post("/users", status_code=201)
def create_user(body: UserCreate, request: Request, db: Session = Depends(get_db), admin: User = Depends(admin_only)):
    if db.scalar(select(User).where(User.email == body.email)):
        raise HTTPException(409, "A user with this email already exists")
    user = User(email=body.email, full_name=body.full_name, password_hash=hash_password(body.password),
                role_id=_role(db, body.role).role_id)
    db.add(user)
    db.flush()
    log_audit(db, admin.user_id, "user_created", "user", user.user_id, {"email": user.email, "role": body.role}, request)
    db.commit()
    db.refresh(user)
    return user_out(user)


@router.patch("/users/{user_id}")
def update_user(user_id: int, body: UserUpdate, request: Request, db: Session = Depends(get_db),
                admin: User = Depends(admin_only)):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(404, "User not found")
    if user.user_id == admin.user_id and (body.is_active is False or (body.role and body.role != ADMIN)):
        raise HTTPException(400, "You cannot deactivate or demote your own account")
    changes = body.model_dump(exclude_unset=True)
    if "full_name" in changes:
        user.full_name = body.full_name
    if "password" in changes:
        user.password_hash = hash_password(body.password)
    if "role" in changes:
        user.role_id = _role(db, body.role).role_id
    if "is_active" in changes:
        user.is_active = body.is_active
    if "password" in changes:
        changes["password"] = "changed"
    log_audit(db, admin.user_id, "user_updated", "user", user_id, changes, request)
    db.commit()
    db.refresh(user)
    return user_out(user)


@router.delete("/users/{user_id}")
def deactivate_user(user_id: int, request: Request, db: Session = Depends(get_db), admin: User = Depends(admin_only)):
    """Users are soft-deleted (deactivated) so audit history and FK references stay intact."""
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(404, "User not found")
    if user.user_id == admin.user_id:
        raise HTTPException(400, "You cannot deactivate your own account")
    user.is_active = False
    log_audit(db, admin.user_id, "user_deactivated", "user", user_id, request=request)
    db.commit()
    return {"detail": "User deactivated"}
