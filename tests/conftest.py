import os
from pathlib import Path

import pytest

TEST_DB = Path(__file__).resolve().parent / "_pytest.db"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB.as_posix()}"
os.environ["DEBUG"] = "true"
os.environ["API_KEY"] = "test-api-key"

API_KEY = os.environ["API_KEY"]


@pytest.fixture(autouse=True)
def reset_settings():
    from app.config import reset_settings_cache

    reset_settings_cache()
    yield
    reset_settings_cache()


@pytest.fixture
def client(reset_settings):
    from app.db import Base, SessionLocal, engine, init_db
    from app.models import Project
    from main import app

    Base.metadata.drop_all(bind=engine)
    init_db()

    db = SessionLocal()
    try:
        db.add(Project(project_key="demo", name="Demo", is_active=True))
        db.commit()
    finally:
        db.close()

    from fastapi.testclient import TestClient

    with TestClient(app) as test_client:
        yield test_client

    engine.dispose()
