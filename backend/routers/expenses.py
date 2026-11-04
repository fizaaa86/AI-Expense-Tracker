import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
from auth import CurrentUser, get_current_user
from db import get_user_db
from schemas import ExpenseIn, ExpenseOut
from services import expenses as expense_service
from services import storage
# prefix: every route below starts with /expenses. tags: groups them in /docs
router = APIRouter(prefix="/expenses", tags=["Expenses"])


def _own_expense_or_404(db: Session, user_id, expense_id: int) -> models.Expense:
    expense = expense_service.get_own_expense(db, user_id, expense_id)
    if expense is None:
        raise HTTPException(status_code=404, detail="Expense not found")
    return expense


@router.post("", response_model=ExpenseOut, status_code=201)
def add_expense(
    data: ExpenseIn,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_user_db),
):
    if data.image_url and not data.image_url.startswith(f"{user.id}/"):
        raise HTTPException(status_code=400, detail="image_url must be one of your own receipt images")
    return expense_service.create_expense(db, user.id, data)


@router.get("", response_model=list[ExpenseOut])
def list_expenses(
    category: str | None = None,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_user_db),
):
    return expense_service.list_expenses(db, user.id, category)


@router.get("/{expense_id}", response_model=ExpenseOut)
def get_expense(
    expense_id: int,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_user_db),
):
    return _own_expense_or_404(db, user.id, expense_id)


@router.delete("/{expense_id}", status_code=204)
def delete_expense(
    expense_id: int,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_user_db),
):
    expense_service.delete_expense(db, _own_expense_or_404(db, user.id, expense_id))


@router.get("/{expense_id}/image")
def get_expense_image(
    expense_id: int,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_user_db),
):
    """A temporary link (valid 1 hour) to this expense's receipt photo."""
    expense = _own_expense_or_404(db, user.id, expense_id)
    if not expense.image_url:
        raise HTTPException(status_code=404, detail="This expense has no receipt image")
    try:
        return {"url": storage.signed_url(user.token, expense.image_url)}
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Could not create the image link: {e}")
