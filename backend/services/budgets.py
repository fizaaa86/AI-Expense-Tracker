"""Budget logic. Used by the REST API now and by the AI agent's tools later."""
import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

import models
from schemas import BudgetIn, BudgetStatus


def set_budget(db: Session, user_id: uuid.UUID, data: BudgetIn) -> models.Budget:
    """Create a budget for this category, or update the limit if one already exists."""
    budget = db.scalar(
        select(models.Budget).where(
            models.Budget.user_id == user_id,
            func.lower(models.Budget.category) == data.category.lower(),
        )
    )
    if budget is None:                      # no -> create a new one
        budget = models.Budget(user_id=user_id, **data.model_dump())
        db.add(budget)
    else:                                   # yes -> just change the limit
        budget.monthly_limit = data.monthly_limit
    db.commit()
    db.refresh(budget)
    return budget


def list_budgets(db: Session, user_id: uuid.UUID) -> list[models.Budget]:
    stmt = select(models.Budget).where(models.Budget.user_id == user_id)
    return list(db.scalars(stmt).all())


def get_own_budget(db: Session, user_id: uuid.UUID, budget_id: int) -> models.Budget | None:
    """Returns the budget only if it belongs to this user, otherwise None."""
    return db.scalar(
        select(models.Budget).where(
            models.Budget.id == budget_id,
            models.Budget.user_id == user_id,
        )
    )


def delete_budget(db: Session, budget: models.Budget) -> None:
    db.delete(budget)
    db.commit()


def month_range(day: date) -> tuple[date, date]:
    """First day of this month and first day of next month, e.g. (2026-11-01, 2026-12-01)."""
    start = day.replace(day=1)
    if start.month == 12:                   # December -> next month is January of next year
        return start, start.replace(year=start.year + 1, month=1)
    return start, start.replace(month=start.month + 1)


def budget_status(db: Session, user_id: uuid.UUID) -> list[BudgetStatus]:
    """How much was spent this month in each budgeted category, compared with the limit."""
    month_start, next_month = month_range(date.today())

    # Total spent per category this month (SUM ... GROUP BY)
    category = func.lower(models.Expense.category)
    spent_stmt = (
        select(category, func.sum(models.Expense.total))
        .where(
            models.Expense.user_id == user_id,
            models.Expense.expense_date >= month_start,
            models.Expense.expense_date < next_month,
        )
        .group_by(category)
    )
    spent_by_category = dict(db.execute(spent_stmt).all())  # e.g. {"food": 1200.00}

    result = []
    for budget in list_budgets(db, user_id):
        spent = spent_by_category.get(budget.category.lower(), Decimal("0"))  # no spending -> 0
        result.append(
            BudgetStatus(
                category=budget.category,
                monthly_limit=budget.monthly_limit,
                spent=spent,
                remaining=budget.monthly_limit - spent,
                over_budget=spent > budget.monthly_limit,
            )
        )
    return result
