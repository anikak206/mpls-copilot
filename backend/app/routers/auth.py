from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from jose import jwt
from passlib.context import CryptContext

from backend.app.db.database import get_db_connection


router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"]
)


SECRET_KEY = "change-this-secret-key-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


class LoginRequest(BaseModel):
    username: str
    password: str


def create_access_token(data: dict):
    payload = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload.update({
        "exp": expire
    })

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )


@router.post("/login")
def login(request: LoginRequest):

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                user_id,
                username,
                password_hash,
                full_name,
                email,
                role_id
            FROM users
            WHERE username = %s
              AND is_active = 1
        """, (request.username,))

        user = cursor.fetchone()

        if not user:
            raise HTTPException(
                status_code=401,
                detail="Invalid username or password"
            )

        if not pwd_context.verify(
            request.password,
            user["password_hash"]
        ):
            raise HTTPException(
                status_code=401,
                detail="Invalid username or password"
            )

        access_token = create_access_token({
            "sub": str(user["user_id"]),
            "username": user["username"],
            "role_id": user["role_id"]
        })

        return {
            "message": "Login successful",
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "user_id": user["user_id"],
                "username": user["username"],
                "full_name": user["full_name"],
                "email": user["email"],
                "role_id": user["role_id"]
            }
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    finally:
        if cursor:
            cursor.close()

        if connection:
            connection.close()