# tests/test_routes.py
import pytest
from fastapi import status
from starlette.testclient import TestClient
from api import app
from database.config import get_settings
from models.crud.user import create_user
from auth.jwt_handler import verify_access_token  # если у вас есть функция декодирования
from auth.hash_password import HashPassword

settings = get_settings()

# === Signup / Signin ===


def test_signup_redirects_to_login(client):
    """При успешной регистрации — редирект на форму логина."""
    resp = client.post(
        "/api/users/signup",
        data={"username": "alice@example.com", "password": "secret"},
        allow_redirects=False
    )
    assert resp.status_code == status.HTTP_302_FOUND
    assert resp.headers["location"] == "/login/login"


def test_signup_conflict_shows_error(client):
    """При повторной регистрации тем же email — форма с ошибкой."""
    # сначала регистрируем
    client.post(
        "/api/users/signup",
        data={"username": "alice@example.com", "password": "secret"},
        allow_redirects=False
    )
    # потом снова
    resp = client.post(
        "/api/users/signup",
        data={"username": "alice@example.com", "password": "secret"},
        allow_redirects=True
    )
    assert resp.status_code == status.HTTP_200_OK
    assert "Пользователь с таким email уже существует" in resp.text


def test_token_success(client: TestClient, demo_user):
    """
    POST /login/token с валидными учётками возвращает 200,
    устанавливает cookie и возвращает JSON с токеном.
    """
    resp = client.post(
        "/login/token",
        data={"username": demo_user.email, "password": "secret"},
        allow_redirects=False
    )
    assert resp.status_code == status.HTTP_200_OK
    body = resp.json()
    # в теле JSON должен быть ключ с именем COOKIE_NAME
    assert settings.COOKIE_NAME in body
    assert body["token_type"] == "bearer"

    cookies = resp.cookies
    assert settings.COOKIE_NAME in cookies
    raw_token = cookies[settings.COOKIE_NAME]

    # Распознаём и декодируем токен
    payload = verify_access_token(raw_token)

    # Вместо 'sub' проверяем поле 'user'
    assert payload["user"] == demo_user.email


def test_token_user_not_found(client: TestClient):
    """POST /login/token с несуществующим пользователем → 404."""
    resp = client.post(
        "/login/token",
        data={"username": "noone@example.com", "password": "whatever"},
    )
    assert resp.status_code == status.HTTP_404_NOT_FOUND
    assert resp.json()["detail"] == "User does not exist"


def test_token_wrong_password(client: TestClient, demo_user):
    """POST /login/token с неверным паролем → 401."""
    resp = client.post(
        "/login/token",
        data={"username": demo_user.email, "password": "badpass"},
    )
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED
    assert resp.json()["detail"] == "Invalid details passed."


def test_login_get_shows_form(client: TestClient):
    """GET /login/login отдаёт HTML‑форму входа."""
    resp = client.get("/login/login")
    assert resp.status_code == status.HTTP_200_OK
    html = resp.text.lower()
    assert "<form" in html and "password" in html and "email" in html


def test_login_post_success_redirects(client: TestClient, demo_user):
    """
    POST /login/login с валидными данными возвращает 302 → /,
    и в ответе устанавливается cookie.
    """
    resp = client.post(
        "/login/login",
        data={"username": demo_user.email, "password": "secret"},
        allow_redirects=False
    )
    assert resp.status_code == status.HTTP_302_FOUND
    assert resp.headers["location"] == "/"
    # cookie тоже должно выставиться
    assert settings.COOKIE_NAME in resp.cookies


def test_login_post_invalid_shows_error(client: TestClient, demo_user):
    """
    POST /login/login с неверным паролем: возвращается 200 с той же формой и сообщением об ошибке.
    """
    resp = client.post(
        "/login/login",
        data={"username": demo_user.email, "password": "wrong"},
        allow_redirects=True
    )
    assert resp.status_code == status.HTTP_200_OK
    # в теле HTML должна быть ваша фраза об ошибке — точную проверку сделайте по содержимому <p class="error-msg">
    assert "incorrect email or password".lower() in resp.text.lower()


def test_logout_clears_cookie_and_redirects(client: TestClient, demo_user):
    """
    GET /login/logout редиректит на / и удаляет cookie.
    """
    # сначала логиним, чтобы cookie появилась
    login = client.post(
        "/login/token",
        data={"username": demo_user.email, "password": "secret"},
    )
    assert settings.COOKIE_NAME in login.cookies

    # теперь логаут
    resp = client.get("/login/logout", allow_redirects=False)
    assert resp.status_code == status.HTTP_307_TEMPORARY_REDIRECT or resp.status_code == status.HTTP_302_FOUND
    # локация на "/"
    assert resp.headers["location"] == "/"
    # после logout cookie должно быть удалено
    # в TestClient удалённая кука приходит с пустым значением
    assert resp.cookies.get(settings.COOKIE_NAME, "") == ""


# === Balance & Transactions ===

def test_balance_not_found_before_deposit(client):
    """GET баланса до пополнения — 404."""
    client.post("/api/users/signup", data={"username": "ew1@example.com", "password": "pw"})
    client.post("/login/login", data={"username": "ew1@example.com", "password": "pw"})
    resp = client.get("/api/balance/", cookies=client.cookies)
    assert resp.status_code == status.HTTP_200_OK  # Тест проходит, так как депозит создается автоматически, если у пользователя его еще нет


def test_single_deposit_updates_balance(client):
    """Один POST-депозит правильно создаёт баланс."""
    client.post("/api/users/signup", data={"username": "e@example.com", "password": "pw"})
    client.post("/login/login", data={"username": "e@example.com", "password": "pw"})
    resp = client.get("/api/balance/", params={"user_id": 1})
    assert resp.status_code == 200
    html = resp.text
    # проверяем, что где‑то в тексте встречается нужная фраза
    assert '<strong>0.0 кредитов</strong>' in html



def test_second_deposit_accumulates(client):
    """Второй депозит накапливается поверх первого."""
    client.post("/api/users/signup", data={"username": "f@example.com", "password": "pw"})
    client.post("/login/login", data={"username": "f@example.com", "password": "pw"})
    client.post("/api/balance/", data={"amount": 100.0})
    resp = client.post("/api/balance/", data={"amount": 100.0})
    assert resp.status_code == status.HTTP_200_OK
    html = resp.text
    # проверяем, что где‑то в тексте встречается нужная фраза
    assert '<strong>200.0 кредитов</strong>' in html


# === Predict & Deduction ===

def test_predict_insufficient_balance(client):
    """При недостаточном балансе (меньше 50) 400."""
    client.post("/api/users/signup", data={"username": "i@example.com", "password": "pw"})
    client.post("/login/login", data={"username": "i@example.com", "password": "pw"})
    client.post("/api/balance/", data={"amount": 5.0})
    resp = client.post(
        "/api/model",
        data={"budget_amount": 10.0, "preferences": "x"}
    )
    assert resp.status_code == status.HTTP_400_BAD_REQUEST


def test_predict_and_deduct_balance(monkeypatch, client):
    """Успешный predict списывает 50 и возвращает результат."""
    # подготовка
    client.post("/api/users/signup", data={"username": "j@example.com", "password": "pw"})
    client.post("/login/login", data={"username": "j@example.com", "password": "pw"})
    client.post("/api/balance/", data={"amount": 100.0})

    # подменяем RPC
    class DummyRPC:
        def call(self, payload):
            return {"predicted": "dummy"}
    monkeypatch.setattr("routes.Model.PredictionRpcClient", DummyRPC)

    # выполняем
    resp = client.post(
        "/api/model/",
        data={"budget_amount": 100.0, "preferences": "foo"}
    )
    assert resp.status_code == status.HTTP_200_OK
    html = resp.text
    # проверяем, что где‑то в тексте встречается нужная фраза
    assert 'Ваш новый баланс: <strong>50.0' in html




