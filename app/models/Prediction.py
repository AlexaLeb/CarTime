from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from sqlmodel import SQLModel
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from models.User import User


class Prediction(SQLModel, table=True):
    __tablename__ = 'predictions'

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", nullable=False)
    requested_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    region: str = Field(nullable=False)
    predicted_value: int = Field(nullable=False)
    cost: Decimal = Field(nullable=False)

    user: Optional[User] = Relationship(back_populates="predictions")