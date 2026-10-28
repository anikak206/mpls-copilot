"""Startup: apply Alembic migrations, ensure the local ML artifact exists, seed development data."""
from alembic import command
from alembic.config import Config

from app.config import BACKEND_DIR


def migrate():
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    command.upgrade(cfg, "head")


def ensure_model():
    from ml.inference.predictor import MODEL_PATH
    if not MODEL_PATH.exists():
        from ml.training.train import train
        train()


def bootstrap(seed: bool = True):
    migrate()
    ensure_model()
    if seed:
        from app.seed import run_seed
        run_seed()
