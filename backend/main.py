from datetime import date
from decimal import Decimal

from fastapi import Depends, FastAPI, HTTPException

from sqlalchemy import func, select
from sqlalchemy.orm import Session

import models
from auth import CurrentUser, get_current_user
from db import get_user_db
from schemas import BudgetIn, BudgetOut, BudgetStatus, ExpenseIn, ExpenseOut


app = FastAPI(title="AI Expense Tracker")


@app.get("/")
def home():
    return {"message": "Hello, Expense Tracker!"}


@app.get("/me")
def who_am_i(user: CurrentUser = Depends(get_current_user)):
    return {"id": user.id, "email": user.claims.get("email")}


@app.post("/expenses", response_model=ExpenseOut, status_code=201)
def add_expense(
    data: ExpenseIn,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_user_db),
):
    expense = models.Expense(
        user_id=user.id,                                        # from the verified token
        **data.model_dump(exclude={"items"}),
        items=[models.ExpenseItem(**item.model_dump()) for item in data.items],
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense


@app.get("/expenses", response_model=list[ExpenseOut])
def list_expenses(
    category: str | None = None,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_user_db),
):
    stmt = (
        select(models.Expense)
        .where(models.Expense.user_id == user.id)              # guard 1: our code
        .order_by(models.Expense.expense_date.desc())          # guard 2: RLS in the database
    )
    if category:
        stmt = stmt.where(func.lower(models.Expense.category) == category.lower())
    return db.scalars(stmt).all()


def _get_own_expense(db: Session, expense_id: int, user_id) -> models.Expense:
    expense = db.scalar(
        select(models.Expense).where(
            models.Expense.id == expense_id,
            models.Expense.user_id == user_id,
        )
    )
    if expense is None:
        raise HTTPException(status_code=404, detail="Expense not found")
    return expense


@app.get("/expenses/{expense_id}", response_model=ExpenseOut)
def get_expense(
    expense_id: int,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_user_db),
):
    return _get_own_expense(db, expense_id, user.id)


@app.delete("/expenses/{expense_id}", status_code=204)
def delete_expense(
    expense_id: int,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_user_db),
):
    db.delete(_get_own_expense(db, expense_id, user.id))
    db.commit()


#for budgets
#create a new budget if previous one doesnt exist,else update the limit of previous one

@app.put("/budgets", response_model=BudgetOut)
def set_budget(
    data: BudgetIn,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_user_db),
):
    # Does this user already have a budget for this category?
    budget = db.scalar(
        select(models.Budget).where(
            models.Budget.user_id == user.id,
            func.lower(models.Budget.category) == data.category.lower(),
        )
    )
    if budget is None:                      # no -> create a new one
        budget = models.Budget(user_id=user.id, **data.model_dump())
        db.add(budget)
    else:                                   # yes -> just change the limit
        budget.monthly_limit = data.monthly_limit
    db.commit()
    db.refresh(budget)
    return budget


#list budgets
@app.get("/budgets", response_model=list[BudgetOut])
def list_budgets(
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_user_db),
):
    stmt = select(models.Budget).where(models.Budget.user_id == user.id)
    return db.scalars(stmt).all()



#budget status: how much spent this month vs the limit
@app.get("/budgets/status", response_model=list[BudgetStatus])
def budget_status(
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_user_db),
):
    # Step 1: work out this month's date range
    month_start = date.today().replace(day=1)              # e.g. 2026-11-01
    if month_start.month == 12:                             # December -> next month is January of next year
        next_month = month_start.replace(year=month_start.year + 1, month=1)
    else:
        next_month = month_start.replace(month=month_start.month + 1)

    # Step 2: total spent per category this month (SUM ... GROUP BY)
    category = func.lower(models.Expense.category)
    spent_stmt = (
        select(category, func.sum(models.Expense.total))
        .where(
            models.Expense.user_id == user.id,
            models.Expense.expense_date >= month_start,
            models.Expense.expense_date < next_month,
        )
        .group_by(category)
    )
    spent_by_category = dict(db.execute(spent_stmt).all())  # e.g. {"food": 1200.00, "travel": 300.00}

    # Step 3: compare each budget with what was spent
    budgets = db.scalars(select(models.Budget).where(models.Budget.user_id == user.id)).all()
    result = []
    for budget in budgets:
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


#find a budget that belongs to this user, or give 404
def _get_own_budget(db: Session, budget_id: int, user_id) -> models.Budget:
    budget = db.scalar(
        select(models.Budget).where(
            models.Budget.id == budget_id,
            models.Budget.user_id == user_id,
        )
    )
    if budget is None:
        raise HTTPException(status_code=404, detail="Budget not found")
    return budget


#delete a budget
@app.delete("/budgets/{budget_id}", status_code=204)
def delete_budget(
    budget_id: int,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_user_db),
):
    db.delete(_get_own_budget(db, budget_id, user.id))
    db.commit()
