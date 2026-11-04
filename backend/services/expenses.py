"""Expense logic. Used by the REST API now and by the AI agent's tools later."""
import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

import models
from schemas import ExpenseIn


def create_expense(db: Session, user_id: uuid.UUID, data: ExpenseIn) -> models.Expense:
    expense = models.Expense(
        user_id=user_id,                                        # from the verified token
        **data.model_dump(exclude={"items"}),
        items=[models.ExpenseItem(**item.model_dump()) for item in data.items],
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense


def list_expenses(db: Session, user_id: uuid.UUID, category: str | None = None) -> list[models.Expense]:
    stmt = (
        select(models.Expense)
        .where(models.Expense.user_id == user_id)              # guard 1: our code
        .order_by(models.Expense.expense_date.desc())          # guard 2: RLS in the database
    )
    if category:
        stmt = stmt.where(func.lower(models.Expense.category) == category.lower())
    return list(db.scalars(stmt).all())


def get_own_expense(db: Session, user_id: uuid.UUID, expense_id: int) -> models.Expense | None:
    """Returns the expense only if it belongs to this user, otherwise None."""
    return db.scalar(
        select(models.Expense).where(
            models.Expense.id == expense_id,
            models.Expense.user_id == user_id,
        )
    )


def delete_expense(db: Session, expense: models.Expense) -> None:
    db.delete(expense)
    db.commit()
