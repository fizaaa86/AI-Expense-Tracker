from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ItemIn(BaseModel):
    name: str = Field(min_length=1)
    price: Decimal = Field(max_digits=12, decimal_places=2)


class ItemOut(ItemIn):
    model_config = ConfigDict(from_attributes=True)   # allow building from SQLAlchemy objects
    id: int


class ExpenseIn(BaseModel):
    merchant: str = Field(min_length=1)
    expense_date: date
    total: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    tax: Decimal = Field(default=Decimal("0"), ge=0, max_digits=12, decimal_places=2)
    category: str = "Other"
    items: list[ItemIn] = []


class ExpenseOut(ExpenseIn):
    model_config = ConfigDict(from_attributes=True)
    id: int
    image_url: str | None
    created_at: datetime
    items: list[ItemOut]
