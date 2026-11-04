import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

#Our Base class inherits SQLAlchemy's ORM functionality by DeclarativeBase class
#We will use Base as the parent class for all our database models.


class Base(DeclarativeBase):
    pass

#Mapped tells SQLAlchemy what type of Python data a database column represents.
#mapped_column() lets us configure a database column.
#We use mapped_column()when we need additional configuration, such as primary keys, numeric precision, defaults, and foreign keys.


class Expense(Base):
    __tablename__ = "expenses"   # must match the table name in Supabase exactly

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[uuid.UUID]
    merchant: Mapped[str]
    expense_date: Mapped[date]
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    tax: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"))
    category: Mapped[str] = mapped_column(default="Other")
    image_url: Mapped[str | None]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # One expense -> many items. "delete-orphan": removing an item from this list deletes it in the DB.
    items: Mapped[list["ExpenseItem"]] = relationship(
        back_populates="expense", cascade="all, delete-orphan", lazy="selectin"
    )


class ExpenseItem(Base):
    __tablename__ = "expense_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    expense_id: Mapped[int] = mapped_column(ForeignKey("expenses.id", ondelete="CASCADE"))
    name: Mapped[str]
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2))

    expense: Mapped[Expense] = relationship(back_populates="items")


class Budget(Base):
    __tablename__ = "budgets"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[uuid.UUID]
    category: Mapped[str]
    monthly_limit: Mapped[Decimal] = mapped_column(Numeric(12, 2))
