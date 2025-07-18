from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from sqlmodel import SQLModel

from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship


class User(SQLModel, table=True):
    __tablename__ = 'users'

    # Определяем поле id с типом Optional[int] и указываем, что оно является первичным ключом.
    id: Optional[int] = Field(default=None, primary_key=True)

    # Поле username с указанием дополнительных параметров через sa_column
    email: str = Field(sa_column_kwargs={"unique": True, "nullable": False})

    # Поле hashed_password, обязательное для заполнения
    hashed_password: str = Field(sa_column_kwargs={"nullable": False})

    # Флаг администратора, по умолчанию False
    is_admin: bool = Field(default=False, sa_column_kwargs={"default": False})

    # Определяем связь "один к одному" с балансом
    balance: Optional["Balance"] = Relationship(back_populates="user")

    # Определяем связь "один ко многим" с транзакциями, используем тип List для множественных записей
    transactions: List["Transaction"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

    # Новая связь "один ко многим" с задачами предсказаний
    predictions: List["Prediction"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

    def set_password(self, password: str):
        import bcrypt
        self.hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')