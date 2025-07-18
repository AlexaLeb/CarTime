from sqlmodel import SQLModel, Session, create_engine

from .config import get_settings
from models.services import balance, transaction, user
from logger.logging import get_logger

logger = get_logger(logger_name=__name__)


# Создаем движок на основе URL, полученного из настроек
engine = create_engine(
    url=get_settings().DATABASE_URL_psycopg,
    echo=True,
    pool_size=5,
    max_overflow=10
)
logger.info("Создан движок")


# Функция-генератор для получения сессии. Используем with-контекст, чтобы автоматически закрыть сессию.
def get_session():
    with Session(engine) as session:
        yield session


# Инициализация базы данных: дропаем существующие таблицы и создаём заново
def init_db():
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)

    session = next(get_session())
    alex = user.create_user(session, 'Demo@mail.ru', '11', False)
    user.create_user(session, 'Admin@demo.ru', '13', True)

    dmb = balance.create(session, user_id=alex.id, initial_amount=1000)
    balance.create(session, user_id=user.get_by_email(session, 'Admin@demo.ru').id, initial_amount=800)
    alex.balance = dmb


    session.commit()
    session.close()
    logger.info("База данных собрана с начальными значениями")
