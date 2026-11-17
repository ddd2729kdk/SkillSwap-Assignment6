import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from app.models import Base
from app.database import SessionLocal, engine as default_engine
from app.main import app

@pytest.fixture(autouse=True)
def clean_db(monkeypatch):
    url=os.getenv("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set TEST_DATABASE_URL to a dedicated PostgreSQL test database")
    test_engine=create_engine(url,pool_pre_ping=True)
    Base.metadata.drop_all(test_engine)
    Base.metadata.create_all(test_engine)
    SessionLocal.configure(bind=test_engine)
    monkeypatch.setenv("SKILLSWAP_SEED","0")
    yield
    Base.metadata.drop_all(test_engine)
    SessionLocal.configure(bind=default_engine)
    test_engine.dispose()

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c
