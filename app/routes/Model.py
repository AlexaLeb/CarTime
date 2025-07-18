from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
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

logger = get_logger(logger_name=__name__)
router = APIRouter()
templates = Jinja2Templates(directory="view")


@router.post("/")
async def predict(request: Request, budget_amount: float = Form(...), preferences:  str = Form(...), session: Session = Depends(get_session),
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
    # Списываем 50 баллов с баланса
    try:
        balance.withdraw(50)
        balance = update_balance(session, balance)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Формируем payload для RPC-запроса
    payload = {
        "user_id": user_id,
        "budget_amount": budget_amount,
        "preferences": preferences
    }
    logger.info("Вызов RPC клиента")
    rpc_client = PredictionRpcClient()
    result = rpc_client.call(payload)
    logger.info('RPC клиент отработал')
    return templates.TemplateResponse("model.html", {"request": request, "user": user, "result": result, "new_balance": balance.amount})


@router.get("/")
async def prediction_history(request: Request, session: Session = Depends(get_session), user: str = Depends(authenticate_cookie)) -> dict:
    """
    Возвращает историю предсказаний для указанного пользователя.
    """
    user_id = get_by_email(session, user).id
    tasks = list_transactions(session, user_id)
    return templates.TemplateResponse("model.html", {"request": request, "user": user, "prediction_history": tasks})
