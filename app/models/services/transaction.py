from models.Balance import Balance
from logger.logging import get_logger
from typing import Optional, List
from decimal import Decimal
from sqlmodel import select
from models.Transactions import Transaction
# from models import User, Balance, Prediction
from models.services.balance import get_by_user_id as get_balance

import bcrypt
from datetime import datetime


logger = get_logger(logger_name=__name__)


def create(session, user_id: int, tx_type: str, amount, description: Optional[str] = None) -> Transaction:
    logger.debug(f"Creating transaction: user_id={user_id}, tx_type={tx_type}, amount={amount}")
    # Получаем и обновляем баланс
    balance = get_balance(session, user_id)
    if tx_type == 'withdraw':
        if balance.amount < amount:
            logger.error(f"Transaction failed: insufficient funds for user_id={user_id}")
            raise ValueError("Insufficient funds")
        balance.amount -= amount
    elif tx_type == 'deposit':
        balance.amount += amount
    else:
        logger.error(f"Transaction failed: invalid tx_type={tx_type}")
        raise ValueError("Invalid transaction type")
    balance.updated_at = datetime.utcnow()
    # Создаем запись транзакции
    tx = Transaction(
        user_id=user_id,
        tx_type=tx_type,
        amount=amount,
        timestamp=datetime.utcnow(),
        description=description
    )
    session.add(tx)
    session.add(balance)
    session.commit()
    session.refresh(tx)
    logger.info(f"Transaction created: tx_id={tx.id}, user_id={user_id}, type={tx_type}, amount={amount}")
    return tx


def list_transactions(session, user_id: int) -> List[Transaction]:
    logger.debug(f"Listing transactions for user_id={user_id}")
    stmt = select(Transaction).where(Transaction.user_id == user_id).order_by(Transaction.timestamp.desc())
    transactions = session.exec(stmt).all()
    logger.info(f"Retrieved {len(transactions)} transactions for user_id={user_id}")
    return transactions

