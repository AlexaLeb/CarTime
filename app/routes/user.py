from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from database.database import get_session
from services.loginform import LoginForm
from models.services.user import create_user, get_by_email, get_all_users
from models.User import User
from typing import List
from models.services.user import get_by_email
from auth.auth import authenticate_cookie
from fastapi.templating import Jinja2Templates
from models.services.balance import get_by_user_id as get_balance, create as create_balance
from logger.logging import get_logger

logger = get_logger(logger_name=__name__)
router = APIRouter()
templates = Jinja2Templates(directory="view")


@router.get("/signup", response_class=HTMLResponse)
async def signup_get(request: Request):
    """
    Показывает форму регистрации.
    """
    return templates.TemplateResponse(
        "users.html",
        {"request": request, "errors": [], "username": ""}
    )


@router.post("/signup", response_class=HTMLResponse)
async def signup_post(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    session: Session = Depends(get_session)
):
    """
    Обрабатывает форму регистрации: создаёт нового пользователя или
    рендерит форму снова с ошибкой.
    """
    errors = []

    # Проверяем, не занят ли логин
    if get_by_email(session, username):
        errors.append("Пользователь с таким email уже существует")

    if errors:
        # вернём форму обратно с текстом ошибки и введённым username
        return templates.TemplateResponse(
            "users.html",
            {"request": request, "errors": errors, "username": username}
        )

    # создаём реально
    create_user(session, username, password)
    user_id = get_by_email(session, username).id
    create_balance(session, user_id, initial_amount=0.0)
    logger.info('Запрос на создание пользователя')
    # после успешной регистрации делаем редирект на страницу входа
    return RedirectResponse(url="/login/login", status_code=status.HTTP_302_FOUND)


@router.post("/signin")
async def signin(username: str, password: str, session: Session = Depends(get_session)) -> dict:
    """
    Авторизует пользователя по username и password.
    """
    user = get_by_email(session, username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User does not exist"
        )
    # Проверяем пароль
    if not user.check_password(password):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Wrong credentials passed"
        )
    return {"message": "User signed in successfully"}


@router.get("/users", response_model=List[User])
async def get_users(session: Session = Depends(get_session)):
    """
    Возвращает список всех пользователей.
    """
    return get_all_users(session)
