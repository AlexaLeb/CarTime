from datetime import datetime
from decimal import Decimal

from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from sqlmodel import SQLModel
from models.User import User

from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship


class Balance(SQLModel, table=True):
    __tablename__ = 'balances'

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", nullable=False)
    amount: float = Field(default=0.0)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    user: Optional[User] = Relationship(back_populates="balance")


    def deposit(self, amount: float):
        self.amount += amount
        print(self.amount)

    def withdraw(self, amount: float):
        if self.amount >= amount:
            self.amount -= amount
            print(f'баланс теперь - {self.amount}')
        else:
            raise Exception("Недостаточно средств для списания")

    def get_amount(self) -> float:
        return self.amount