from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

import models
from auth import CurrentUser, get_current_user
from db import get_user_db
from schemas import ExpenseIn, ExpenseOut

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
