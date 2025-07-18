from models.Balance import Balance
from logger.logging import get_logger
from typing import Optional, List
from decimal import Decimal
from sqlmodel import select
from models import User, Balance, Transaction, Prediction
from balance import get_by_user_id as get_balance
from transaction import create_transaction

import bcrypt
from datetime import datetime


logger = get_logger(logger_name=__name__)


def create_prediction(session, user_id: int, predicted_value: int, cost) -> Prediction:
    logger.debug(f"Creating prediction for user_id={user_id}, cost={cost}")
    # Создаем транзакцию дебет автоматически
    create_transaction(session, user_id, get_balance(session, user_id).id,
                             tx_type='withdraw', amount=cost,
                             description=f'Prediction cost for region')
    # Создаем прогноз
    pred = Prediction(
        user_id=user_id,
        requested_at=datetime.utcnow(),
        predicted_value=predicted_value,
        cost=cost
    )
    session.add(pred)
    session.commit()
    session.refresh(pred)
    logger.info(f"Prediction created: id={pred.id}, user_id={user_id}, value={predicted_value}")
    return pred


def list_predictions(session, user_id: int) -> List[Prediction]:
    logger.debug(f"Listing predictions for user_id={user_id}")
    stmt = select(Prediction).where(Prediction.user_id == user_id).order_by(Prediction.requested_at.desc())
    predictions = session.exec(stmt).all()
    logger.info(f"Retrieved {len(predictions)} predictions for user_id={user_id}")
    return predictions