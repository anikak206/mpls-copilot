"""Pytest fixtures: a disposable MySQL database (<MYSQL_DATABASE>_test) rebuilt for every run."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / "backend" / ".env")
os.environ["MYSQL_DATABASE"] = os.environ["MYSQL_DATABASE"] + "_test"  # never touch the real database

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app.config import settings  # noqa: E402
from app.database import engine  # noqa: E402

assert settings.mysql_database.endswith("_test")


def _reset_database():
    with engine.begin() as conn:
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
        for (name, kind) in conn.execute(text(
                "SELECT TABLE_NAME, TABLE_TYPE FROM information_schema.TABLES WHERE TABLE_SCHEMA = DATABASE()")).all():
            conn.execute(text(f"DROP {'VIEW' if kind == 'VIEW' else 'TABLE'} IF EXISTS `{name}`"))
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))


@pytest.fixture(scope="session")
def client():
    _reset_database()
    from server import app
    with TestClient(app) as test_client:  # lifespan runs Alembic migrations + seed on the test DB
        yield test_client


def _login(client, email, password):
    r = client.post("/api/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture(scope="session")
def admin(client):
    return _login(client, settings.demo_users[0][1], settings.demo_users[0][2])


@pytest.fixture(scope="session")
def engineer(client):
    return _login(client, settings.demo_users[1][1], settings.demo_users[1][2])


@pytest.fixture(scope="session")
def auditor(client):
    return _login(client, settings.demo_users[2][1], settings.demo_users[2][2])


@pytest.fixture()
def db():
    with engine.connect() as conn:
        yield conn
