from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
from sqlalchemy.orm import Session
from database.database import get_session
from models.services.balance import get_by_user_id as get_balance, create as create_balance, update_balance
from models.services.transaction import create as create_transaction
from models.services.user import get_by_email
from auth.auth import authenticate_cookie
from fastapi.templating import Jinja2Templates
from logger.logging import get_logger

logger = get_logger(logger_name=__name__)

router = APIRouter()
templates = Jinja2Templates(directory="view")


@router.get("/")
async def read_balance(request: Request, user: str = Depends(authenticate_cookie), session: Session = Depends(get_session)) -> dict:
    """
    Возвращает текущий баланс пользователя по его user_id.
    """
    user_id = get_by_email(session, user).id
    balance = get_balance(session, user_id)
    logger.info("Запрос баланса")
    if not balance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Balance not found for the given user_id"
        )
        # 3) Рендерим шаблон
    return templates.TemplateResponse("balance.html", {"request": request, "user": user, "balance": balance.amount})


@router.post("/")
async def deposit_balance(
    request: Request, user: str = Depends(authenticate_cookie),
    amount: float = Form(...),              # сумма приходит из HTML‑формы
    session: Session = Depends(get_session)
) -> dict:
    """
    Пополнение баланса пользователя.
    Если баланс отсутствует, создаёт новый с начальным значением 0.0.
    После пополнения автоматически создаётся транзакция с типом 'deposit'.
    """

    user_id = get_by_email(session, user).id
    balance = get_balance(session, user_id)
    if not balance:
        balance = create_balance(session, user_id, initial_amount=0.0)

    try:
        balance.deposit(amount)
        balance = update_balance(session, balance)
        logger.info("Баланс пополнен")
    except Exception as e:
        logger.error("Баланс не пополнен")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    # Записываем транзакцию пополнения
    create_transaction(session, user_id, "deposit", amount)

    session.commit()
    session.refresh(balance)
    context = {"request": request, "user": user, "balance": balance.amount}
    return templates.TemplateResponse("balance.html", context)