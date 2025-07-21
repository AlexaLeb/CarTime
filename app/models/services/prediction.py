from models.Balance import Balance
from logger.logging import get_logger
from typing import Optional, List
from decimal import Decimal
from sqlmodel import select
from models.Prediction import Prediction
from models import User, Balance, Transactions
from models.services.balance import get_by_user_id as get_balance
from models.services.transaction import create

import bcrypt
from datetime import datetime


logger = get_logger(logger_name=__name__)


def create_prediction(session, user_id: int, predicted_value, cost) -> Prediction:
    logger.debug(f"Creating prediction for user_id={user_id}, cost={cost}")
    # Создаем транзакцию дебет автоматически
    create(session, user_id, tx_type='withdraw', amount=cost, description=f'Prediction cost for region')
    # Создаем прогноз
    pred = Prediction(
        user_id=user_id,
        requested_at=datetime.utcnow(),
        predicted_values=predicted_value,
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