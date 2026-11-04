# AI Expense Tracker

A personal expense tracker with a **FastAPI** backend, **Supabase** authentication and a **PostgreSQL** database.
Each user signs in and can only see and manage their own expenses. This is enforced twice: once in the API code and again in the database with Row Level Security.

> 🚧 Work in progress. The REST API for expenses and budgets is working. AI receipt scanning, the AI agent and the frontend are planned.


## Features

- 🔐 **Secure login.** Supabase JWTs are verified against Supabase's public keys (JWKS).
- 🧾 **Expenses with line items.** Store the merchant, date, total, tax, category and individual items.
- 🔎 **Filter by category.** For example, `GET /expenses?category=food`.
- 💰 **Monthly budgets.** Set a limit per category and see how much you've spent and what's left this month.
- 🛡️ **Row Level Security.** Postgres policies make sure users can only touch their own rows.
- 📄 **Interactive API docs.** Generated automatically at `/docs`.

## Tech Stack

| Layer      | Technology                          |
|------------|-------------------------------------|
| API        | FastAPI, Pydantic                   |
| Database   | PostgreSQL (Supabase), SQLAlchemy 2 |
| Auth       | Supabase Auth, PyJWT                |
| Language   | Python 3                            |

## Project Structure

```
Expense/
├── backend/
│   ├── main.py           # Creates the app and plugs in the routers
│   ├── routers/          # Web layer: URLs, login check, HTTP errors
│   │   ├── expenses.py
│   │   └── budgets.py
│   ├── services/         # Business logic, shared with the AI agent later
│   │   ├── expenses.py
│   │   └── budgets.py
│   ├── auth.py           # JWT verification -> current user
│   ├── db.py             # Database connection + per-user session for RLS
│   ├── models.py         # SQLAlchemy tables (Expense, ExpenseItem, Budget)
│   ├── schemas.py        # Pydantic request/response models
│   ├── sql/schema.sql    # Tables, indexes and RLS policies
│   ├── check_db.py       # Quick database connection check
│   ├── get_token.py      # Log in and print a token for testing
│   ├── requirements.txt
│   └── .env.example      # Template for your secrets
└── frontend/             # (coming soon)

```

## Getting Started

### 1. Clone the repo
```bash
git clone https://github.com/fizaaa86/AI-Expense-Tracker.git
cd AI-Expense-Tracker/backend
```

### 2. Create a virtual environment and install dependencies
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Set up Supabase
1. Create a project at [supabase.com](https://supabase.com).
2. In the **SQL Editor**, run the contents of `sql/schema.sql`.
3. Copy the env template and fill in your project's values:
   ```bash
   cp .env.example .env
   ```
   ```
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_ANON_KEY=your-anon-key
   DATABASE_URL=postgresql://user:password@host:5432/postgres
   ```

### 4. Check the database connection
```bash
python check_db.py
```

### 5. Run the API
```bash
fastapi dev main.py
```
Open **http://127.0.0.1:8000/docs** to try the endpoints.

### 6. Get a token for testing
```bash
python get_token.py
```
Copy the printed token, click **Authorize** in `/docs`, and paste it in.

## API Endpoints

All endpoints except `/` require an `Authorization: Bearer <token>` header.

| Method | Endpoint               | Description                              |
|--------|------------------------|------------------------------------------|
| GET    | `/`                    | Health check                             |
| GET    | `/me`                  | Show the logged-in user's id and email   |
| POST   | `/expenses`            | Add an expense (with optional items)     |
| GET    | `/expenses`            | List your expenses (`?category=` filter) |
| GET    | `/expenses/{id}`       | Get one expense                          |
| DELETE | `/expenses/{id}`       | Delete an expense and its items          |
| PUT    | `/budgets`             | Set a monthly limit for a category (creates or updates) |
| GET    | `/budgets`             | List your budgets                        |
| GET    | `/budgets/status`      | This month's spending vs each budget     |
| DELETE | `/budgets/{id}`        | Delete a budget                          |

Example request body for `POST /expenses`:
```json
{
  "merchant": "Lulu Hypermarket",
  "expense_date": "2026-11-04",
  "total": 450.00,
  "tax": 22.50,
  "category": "Groceries",
  "items": [
    { "name": "Milk", "price": 60.00 },
    { "name": "Bread", "price": 45.00 }
  ]
}
```

## Roadmap

- [ ] AI receipt scanning (upload a photo and extract the merchant, items and total automatically)
- [x] Monthly budgets per category, with over-budget status
- [ ] Spending insights and charts
- [ ] Frontend

## Author

**Fathima Fiza** · [@fizaaa86](https://github.com/fizaaa86)
