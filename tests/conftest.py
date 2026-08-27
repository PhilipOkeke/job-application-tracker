import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel

TEST_DB = Path("test_applications.db")
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB}"

from app.database import create_db_and_tables, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def clean_database():
    SQLModel.metadata.drop_all(engine)
    create_db_and_tables()
    yield
    SQLModel.metadata.drop_all(engine)


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client
