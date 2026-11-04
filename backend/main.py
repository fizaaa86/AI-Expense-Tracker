from fastapi import Depends, FastAPI

from auth import CurrentUser, get_current_user
from routers import budgets, expenses

app = FastAPI(title="AI Expense Tracker")

# plug in the routes from the routers/ folder
app.include_router(expenses.router)
app.include_router(budgets.router)


@app.get("/")
def home():
    return {"message": "Hello, Expense Tracker!"}


@app.get("/me")
def who_am_i(user: CurrentUser = Depends(get_current_user)):
    return {"id": user.id, "email": user.claims.get("email")}
