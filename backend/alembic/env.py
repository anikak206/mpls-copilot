import sys
from pathlib import Path

from alembic import context

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(BACKEND_DIR.parent))

from app.database import Base, engine  # noqa: E402
import app.models  # noqa: E402,F401

target_metadata = Base.metadata


def run_migrations_offline():
    context.configure(url=engine.url.render_as_string(hide_password=False), target_metadata=target_metadata,
                      literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
