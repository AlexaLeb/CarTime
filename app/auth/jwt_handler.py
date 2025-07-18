import time
from datetime import datetime
from fastapi import HTTPException, status
from jose import jwt, JWTError
from database.config import get_settings
from logger.logging import get_logger

logger = get_logger(logger_name=__name__)
settings = get_settings()
SECRET_KEY = settings.SECRET_KEY


def create_access_token(user: str) -> str:
    payload = {
        "user": user,
        "expires": time.time() + 3600
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token


def verify_access_token(token: str) -> dict:
    # 1) убираем возможные кавычки вокруг
    if token.startswith('"') and token.endswith('"'):
        token = token[1:-1]
    # 2) убираем префикс Bearer
    if token.lower().startswith("bearer "):
        token = token.split(" ", 1)[1]
    try:
        data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        expire = data.get("expires")
        if expire is None:
            logger.error('Токен отсутствует')
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No access token supplied"
            )
        if datetime.utcnow() > datetime.utcfromtimestamp(expire):
            logger.error('Токен просрочен')
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Token expired!"
            )
        logger.info('Токен расшифрован успешно')
        return data
    except JWTError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token")
