from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth import CurrentUser, get_current_user
from db import get_user_db
from schemas import BudgetIn, BudgetOut, BudgetStatus
from services import budgets as budget_service

router = APIRouter(prefix="/budgets", tags=["Budgets"])


@router.put("", response_model=BudgetOut)
def set_budget(
    data: BudgetIn,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_user_db),
):
    return budget_service.set_budget(db, user.id, data)


@router.get("", response_model=list[BudgetOut])
def list_budgets(
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_user_db),
):
    return budget_service.list_budgets(db, user.id)


# fixed path, so it stays ABOVE any route with {budget_id}
@router.get("/status", response_model=list[BudgetStatus])
def budget_status(
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_user_db),
):
    return budget_service.budget_status(db, user.id)


@router.delete("/{budget_id}", status_code=204)
def delete_budget(
    budget_id: int,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_user_db),
):
    budget = budget_service.get_own_budget(db, user.id, budget_id)
    if budget is None:
        raise HTTPException(status_code=404, detail="Budget not found")
    budget_service.delete_budget(db, budget)
