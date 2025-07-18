from models.User import User
from logger.logging import get_logger

logger = get_logger(logger_name=__name__)


def create_user(session, email: str, password: str, is_admin: bool = False):
    """
    Создаёт нового пользователя с заданным email, паролем и флагом администратора.
    Пароль хэшируется внутри модели.
    """
    user = User(email=email, hashed_password="")
    user.set_password(password)
    user.is_admin = is_admin
    session.add(user)
    session.commit()
    logger.info('Создан пользователь')
    return user


def get_all_users(session):
    """
    Возвращает список всех пользователей из базы данных.
    """
    return session.query(User).all()


def get_by_email(session, email: str):
    """
    Возвращает пользователя по email, или None, если пользователь не найден.
    """
    return session.query(User).filter_by(email=email).first()