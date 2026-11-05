from datetime import date, datetime
from decimal import Decimal
from typing import Any,Literal

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
    image_url: str | None = None     # path returned by /receipts/scan (optional)

class ExpenseOut(ExpenseIn):
    model_config = ConfigDict(from_attributes=True)
    id: int
    image_url: str | None
    created_at: datetime
    items: list[ItemOut]

#for the Budgets

class BudgetIn(BaseModel):
    category: str = Field(min_length=1)
    monthly_limit: Decimal = Field(gt=0, max_digits=12, decimal_places=2)


class BudgetOut(BudgetIn):
    model_config = ConfigDict(from_attributes=True)
    id: int


class BudgetStatus(BaseModel):
    category: str
    monthly_limit: Decimal
    spent: Decimal
    remaining: Decimal
    over_budget: bool



#for AI receipt scanning

Category = Literal[
    "Food", "Groceries", "Transport", "Shopping", "Bills", "Health", "Entertainment", "Other"
]


class ExtractedItem(BaseModel):
    name: str = Field(description="Item name as printed on the receipt.")
    price: float = Field(description="Final price for this line (quantity x unit price).")


class ReceiptExtraction(BaseModel):
    """What Gemini reads from a receipt photo. Anything unreadable is null."""
    merchant: str | None = Field(description="Shop or business name.")
    expense_date: str | None = Field(description="Purchase date in YYYY-MM-DD format.")
    items: list[ExtractedItem] = Field(description="Purchased items only. No subtotal, tax or total lines.")
    discount: float | None = Field(description="Total of all discounts as a positive number, 0 if none.")
    tax: float | None = Field(description="Total tax shown on the receipt, 0 if none.")
    total: float | None = Field(description="Final amount paid.")
    category: Category = Field(description="Best matching spending category.")


class ReceiptValidation(BaseModel):
    ok: bool
    problems: list[str]


class ScanResult(BaseModel):
    receipt: ReceiptExtraction
    validation: ReceiptValidation
    attempts: int          # 1 = first reading was fine, 2 = Gemini had to look again
    image_path: str                        # where the photo was saved; send it as image_url when saving
    possible_duplicates: list[ExpenseOut]  # bills that look the same; ask the user before saving

#Literal[...] means "only one of these exact words". Gemini must pick one of your categories, so you won't get "food", "FOOD" and "Meals" all meaning the same thing. That keeps your budgets working.
#description=: Gemini reads these descriptions. They're instructions to the AI as much as notes for humans. Your report says the same about tool descriptions in section 6.2.
#str | None means "text, or nothing". If the date is smudged, Gemini should return null rather than invent a date.
#We use float here instead of Decimal because it's the simplest number type for Gemini to produce. Your existing ExpenseIn converts it to an exact Decimal when saving.

#for the AI chat agent

class ChatTurn(BaseModel):
    role: Literal["user", "model"]     # who said it: the person, or the AI
    text: str


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    history: list[ChatTurn] = []       # earlier messages, so the AI remembers the conversation


class ToolStep(BaseModel):
    tool: str                          # which tool the agent called
    args: dict[str, Any]               # with which inputs
    ok: bool                           # did it work?


class ChatResponse(BaseModel):
    answer: str
    steps: list[ToolStep]              # what the agent did, in order

#history: the server doesn't remember past messages. The app sends earlier messages back each time, so follow-ups like "yes, save it" make sense.
#steps is the agent's "working out". It's great for checking what it did, and for your report and demo.
#Any means "any type of value", because different tools take different inputs.