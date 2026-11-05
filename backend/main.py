from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from auth import CurrentUser, get_current_user
from routers import budgets, chat,expenses,receipts

app = FastAPI(title="AI Expense Tracker")
# Let the React app (a different "origin") call this API from the browser
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# plug in the routes from the routers/ folder
app.include_router(expenses.router)
app.include_router(budgets.router)
app.include_router(receipts.router)
app.include_router(chat.router)



@app.get("/")
def home():
    return {"message": "Hello, Expense Tracker!"}


@app.get("/me")
def who_am_i(user: CurrentUser = Depends(get_current_user)):
    return {"id": user.id, "email": user.claims.get("email")}
