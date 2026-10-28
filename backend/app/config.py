"""Environment-based configuration. All secrets come from backend/.env (never source code)."""
import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent
load_dotenv(BACKEND_DIR / ".env")


def _required(key: str) -> str:
    value = os.environ.get(key)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {key}")
    return value


class Settings:
    mysql_host = _required("MYSQL_HOST")
    mysql_port = int(_required("MYSQL_PORT"))
    mysql_user = _required("MYSQL_USER")
    mysql_password = _required("MYSQL_PASSWORD")
    mysql_database = _required("MYSQL_DATABASE")
    jwt_secret = _required("JWT_SECRET")
    jwt_expire_minutes = int(_required("JWT_EXPIRE_MINUTES"))
    cors_origins = [o.strip() for o in _required("CORS_ORIGINS").split(",")]
    demo_users = [
        ("Administrator", os.environ.get("ADMIN_EMAIL"), os.environ.get("ADMIN_PASSWORD"), "System Administrator"),
        ("Network Engineer", os.environ.get("ENGINEER_EMAIL"), os.environ.get("ENGINEER_PASSWORD"), "Network Engineer"),
        ("Auditor", os.environ.get("AUDITOR_EMAIL"), os.environ.get("AUDITOR_PASSWORD"), "Compliance Auditor"),
    ]
    database_dir = PROJECT_ROOT / "database"


settings = Settings()
