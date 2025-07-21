from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, status, Request, Form, Body
# from models.services.prediction_task import create as create_prediction_task, \
    # get_by_user_id as get_prediction_tasks_by_user
# from models.services.prediction_result import create as create_prediction_result
from models.services.balance import get_by_user_id as get_balance, create as create_balance, update_balance
from models.services.user import get_by_email
from auth.auth import authenticate_cookie
from fastapi.templating import Jinja2Templates
from database.database import get_session
from models.PredictionRpcClient import PredictionRpcClient
from logger.logging import get_logger
from models.services.transaction import list_transactions
import json
import datetime

logger = get_logger(logger_name=__name__)
router = APIRouter()
templates = Jinja2Templates(directory="view")


@router.post("/")
async def predict(request: Request,  exog: str = Form(..., description="Список словарей с ключами 'timestamp' (ISO) и экзогенными признаками"), session: Session = Depends(get_session),
                  user: str = Depends(authenticate_cookie)) -> dict:
    """
    Назначает задачу на предсказание для пользователя.
    За каждое предсказание списывается 50 баллов с баланса.
    Создает задачу и симулирует результат предсказания.
    """

    user_id = get_by_email(session, user).id
    # Получаем баланс пользователя; если баланс не существует, создаем его с начальным значением 0.0
    balance = get_balance(session, user_id)
    logger.info('Запрос предсказания')
    if not balance:
        balance = create_balance(session, user_id, 0.0)
    if balance.amount < 50:
        logger.warning("Недостаточно кредитов")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient balance for prediction (requires at least 50 points)"
        )

    try:
        exog_list = json.loads(exog)
        if not isinstance(exog_list, list):
            raise ValueError()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Поле exog должно быть валидным JSON-массивом"
        )
    # Формируем payload для RPC-запроса
    payload = {
        "user_id": user_id,
        "exog": exog_list
    }
    logger.info("Вызов RPC клиента")
    rpc_client = PredictionRpcClient()
    result = rpc_client.call(payload)
    logger.info('\nRPC клиент отработал')
    raw = result["predicted_result"]
    formatted = []
    for rec in raw:
        # 1) Парсим ISO-время и форматируем
        dt = datetime.datetime.fromisoformat(rec["timestamp"])
        ts_str = dt.strftime("%d %b %Y %H:%M")
        # 2) Округляем до целого и ставим разделитель тысяч
        count = round(rec["ride_count"])  # округляем
        # форматируем с запятыми: 10171 → "10,171"
        rc = f"{count:,}".replace(",", " ")
        formatted.append({
            "timestamp": ts_str,
            "ride_count": rc
        })
    logger.info(formatted)
    return templates.TemplateResponse("model.html", {"request": request, "user": user, "result": formatted, "new_balance": balance.amount, "message": "Прогноз готов"})


@router.get("/")
async def prediction_history(request: Request, session: Session = Depends(get_session), user: str = Depends(authenticate_cookie)) -> dict:
    """
    Возвращает историю предсказаний для указанного пользователя.
    """
    user_id = get_by_email(session, user).id
    tasks = list_transactions(session, user_id)
    return templates.TemplateResponse("model.html", {"request": request, "user": user, "prediction_history": tasks})
