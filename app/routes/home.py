from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from database.database import get_session
from models.services.balance import get_by_user_id as get_balance, create as create_balance
from models.services.transaction import create as create_transaction

from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from auth.auth import authenticate_cookie, authenticate
from auth.jwt_handler import create_access_token
from database.database import get_session
from services.loginform import LoginForm
from models.services import user as UsersService
from database.config import get_settings
from typing import Dict
from logger.logging import get_logger

logger = get_logger(logger_name=__name__)
router = APIRouter()
settings = get_settings()
templates = Jinja2Templates(directory="view")


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    token = request.cookies.get(settings.COOKIE_NAME)
    if token:
        user = await authenticate_cookie(token)
    else:
        user = None
    context = {
        "user": user,
        "request": request
    }
    logger.info('Запрос на сайт')
    return templates.TemplateResponse("index.html", context)


@router.get("/private", response_class=HTMLResponse)
async def index_private(request: Request, user: str = Depends(authenticate_cookie)):
    context = {
        "user": user,
        "request": request
    }
    return templates.TemplateResponse("private.html", context)


@router.get(
    "/health",
    response_model=Dict[str, str],
    summary="Health check endpoint",
    description="Returns service health status"
)
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint for monitoring.

    Returns:
        Dict[str, str]: Health status message

    Raises:
        HTTPException: If service is unhealthy
    """
    try:
        # Add actual health checks here
        return {"status": "healthy"}
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail="Service unavailable"
        )
