from typing import Optional, List
from decimal import Decimal
from sqlmodel import Session, select
from models import User, Balance, Transactions, Prediction

import bcrypt
from datetime import datetime
from models.Balance import Balance
from logger.logging import get_logger

logger = get_logger(logger_name=__name__)


def create(session, user_id: int, initial_amount: float = 0.0):
    balance = Balance(user_id=user_id, amount=initial_amount)
    logger.info('Создан баланс')
    session.add(balance)
    session.commit()
    return balance


def update_balance(session, balance: Balance) -> Balance:
    """
    Принимает уже модифицированный объект Balance,
    сохраняет его в БД и возвращает обновлённый экземпляр.
    """
    session.add(balance)
    session.commit()
    session.refresh(balance)
    return balance


def get_all(session):
    return session.query(Balance).all()


def get_by_user_id(session, user_id: int):
    return session.query(Balance).filter_by(user_id=user_id).first()