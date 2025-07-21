from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from sqlmodel import SQLModel
from sqlalchemy.types import JSON
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from sqlmodel import SQLModel, Field, Relationship
from models.User import User


class Prediction(SQLModel, table=True):
    __tablename__ = 'predictions'

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", nullable=False)
    requested_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    predicted_values: List[Dict[str, Any]] = Field(
        sa_column=Column(JSON, nullable=False),
        description="JSON array of {\"timestamp\": ..., \"ride_count\": ...} dicts"
    )
    cost: Decimal = Field(nullable=False)

    user: Optional[User] = Relationship(back_populates="predictions")
