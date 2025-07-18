# tests/conftest.py
import pytest
import fastapi
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine, Session, StaticPool
from sqlalchemy.orm import sessionmaker
from api import app                     # ваш FastAPI‑приложение
from database.database import get_session as get_session
from database.config import get_settings
from models.User import User
from models.crud.user import create_user
from auth.auth import authenticate
from models.Balance import Balance
from models.Prediction_task import PredictionTask
from models.Prediction_result import PredictionResult


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine("sqlite:///testing.db", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    app.dependency_overrides[authenticate] = lambda: "user@test.ru"

    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def cleanup_balances(session: Session):
    """
    Перед каждым тестом очищаем таблицу balances,
    чтобы тесты были детерминированы.
    """
    session.query(Balance).delete()
    session.commit()
    yield
    session.query(Balance).delete()
    session.commit()


@pytest.fixture  # фикстура для тестов
def client():
    return TestClient(app)



@pytest.fixture
def demo_user(session):
    """Создаём демо‑пользователя перед тестами."""
    # прямо сохраняем пользователя через CRUD
    user = create_user(session, email="alice@example.com", password="secret")
    return user



@pytest.fixture(autouse=True)
def cleanup_tasks(session: Session):
    """
    Очищаем таблицу prediction_tasks перед и после каждого теста.
    """
    session.query(PredictionTask).delete()
    session.commit()
    yield
    session.query(PredictionTask).delete()
    session.commit()

@pytest.fixture(autouse=True)
def cleanup_results(session: Session):
    # очищаем таблицу перед каждым тестом
    session.query(PredictionResult).delete()
    session.commit()
    yield
    session.query(PredictionResult).delete()
    session.commit()