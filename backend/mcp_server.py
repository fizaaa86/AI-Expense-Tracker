"""MCP tool server: the expense tracker's abilities as tools that any MCP client
(our own agent, Claude Desktop, ...) can discover and call.

WHO the user is comes from the EXPENSE_USER_TOKEN environment variable, which the program
starting this server sets. It is checked on every call, exactly like the API checks tokens.
It is never a tool parameter, so the AI cannot choose whose data it reads or writes."""
import os
from datetime import date
from decimal import Decimal

import jwt
from mcp.server.fastmcp import FastMCP

from auth import CurrentUser, verify_token
from db import user_session
from schemas import BudgetIn, BudgetOut, ExpenseIn, ExpenseOut, ReceiptExtraction
from services import budgets as budget_service
from services import expenses as expense_service
from services import receipts as receipt_service
from services import storage

mcp = FastMCP("expense-tools")


def current_user() -> CurrentUser:
    """The logged-in user. Comes from the environment, never from the AI."""
    token = os.environ.get("EXPENSE_USER_TOKEN")
    if not token:
        raise RuntimeError("No user is logged in (EXPENSE_USER_TOKEN is not set).")
    try:
        return verify_token(token)
    except jwt.PyJWTError:
        raise RuntimeError("The login token is invalid or has expired. Please log in again.")


def _expense_json(expense) -> dict:
    return ExpenseOut.model_validate(expense).model_dump(mode="json")


# ---------------------------------------------------------------- receipts

@mcp.tool()
def extract_receipt(image_path: str, feedback: str | None = None) -> dict:
    """Read a stored receipt photo and return merchant, expense_date, items, discount, tax, total and category.
    image_path: the path the photo was saved under (from the upload).
    feedback: only when re-reading a receipt; describe what was wrong last time (e.g. the problems from validate_receipt).
    Always run validate_receipt on the result before showing it or saving it."""
    user = current_user()
    if not image_path.startswith(f"{user.id}/"):
        raise ValueError("That image does not belong to the current user.")
    image, mime_type = storage.download_receipt_image(user.token, image_path)
    return receipt_service.extract_receipt(image, mime_type, feedback).model_dump(mode="json")


@mcp.tool()
def validate_receipt(receipt: ReceiptExtraction) -> dict:
    """Check an extracted receipt with plain arithmetic: merchant, date and total present,
    and items - discount + tax equals the total (within 1 rupee of rounding).
    Returns ok (true/false) and a list of problems. If not ok, re-read once with extract_receipt
    using the problems as feedback; if still not ok, show the problems to the user."""
    return receipt_service.validate_receipt(receipt).model_dump(mode="json")


@mcp.tool()
def check_duplicate(merchant: str, expense_date: date, total: Decimal) -> dict:
    """Find saved expenses that look like the same bill (same merchant, date and total).
    Use before save_expense. If any are found, ask the user whether to save anyway."""
    user = current_user()
    with user_session(user) as db:
        found = expense_service.find_duplicates(db, user.id, merchant, expense_date, total)
        return {"duplicates": [_expense_json(e) for e in found]}


@mcp.tool()
def save_expense(expense: ExpenseIn) -> dict:
    """Save an expense with its line items. ONLY call this after the user has seen the details
    and clearly confirmed. image_url (optional) is the receipt photo's path."""
    user = current_user()
    if expense.image_url and not expense.image_url.startswith(f"{user.id}/"):
        raise ValueError("That image does not belong to the current user.")
    with user_session(user) as db:
        return _expense_json(expense_service.create_expense(db, user.id, expense))


# ---------------------------------------------------------------- spending questions

@mcp.tool()
def query_expenses(
    category: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    merchant: str | None = None,
) -> dict:
    """Look up the user's saved expenses. All filters are optional and can be combined.
    start_date / end_date: YYYY-MM-DD, both inclusive. merchant: any part of the shop name, any case.
    Returns count, total (sum of all matching expenses) and the expenses, newest first.
    Use this for every question about past spending; never estimate amounts yourself."""
    user = current_user()
    with user_session(user) as db:
        found = expense_service.list_expenses(db, user.id, category, start_date, end_date, merchant)
        total = sum((e.total for e in found), Decimal("0"))
        return {"count": len(found), "total": str(total), "expenses": [_expense_json(e) for e in found]}


@mcp.tool()
def set_budget(category: str, monthly_limit: Decimal) -> dict:
    """Create a monthly budget for a category, or change the limit if one already exists."""
    user = current_user()
    with user_session(user) as db:
        budget = budget_service.set_budget(db, user.id, BudgetIn(category=category, monthly_limit=monthly_limit))
        return BudgetOut.model_validate(budget).model_dump(mode="json")


@mcp.tool()
def check_budget(category: str | None = None) -> dict:
    """This month's spending against each monthly budget: monthly_limit, spent, remaining, over_budget.
    Give a category to check just that one."""
    user = current_user()
    with user_session(user) as db:
        statuses = budget_service.budget_status(db, user.id)
    if category:
        statuses = [s for s in statuses if s.category.lower() == category.lower()]
    return {"budgets": [s.model_dump(mode="json") for s in statuses]}


if __name__ == "__main__":
    mcp.run()   # talk over stdin/stdout ("stdio"), the standard way for local MCP servers


#mcp.run() uses stdio, meaning it talks through standard input and output, like a phone line between two programs on the same computer. The server is not on the internet, as your report says in section 7.