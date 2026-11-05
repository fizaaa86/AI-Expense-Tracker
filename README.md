# AI Expense Tracker

A personal expense tracker with a **FastAPI** backend, **Supabase** authentication, database and storage, and an **AI agent** powered by **Gemini** and an **MCP** tool server.
Each user signs in and can only see and manage their own data. This is enforced twice: once in the API code and again in the database with Row Level Security.

> 🚧 Work in progress. The backend (REST API, receipt scanning, MCP tools and AI chat agent) is working. The frontend and Docker setup are coming next.

## Features

- 🔐 **Secure login.** Supabase JWTs are verified against Supabase's public keys (JWKS).
- 🧾 **Expenses with line items.** Store the merchant, date, total, tax, category and individual items.
- 🔎 **Filters.** By category, date range and merchant.
- 💰 **Monthly budgets.** Set a limit per category and see how much you've spent and what's left this month.
- 📸 **AI receipt scanning.** Upload a photo and Gemini extracts the merchant, date, items, discount, tax and total. Plain-maths checks catch misreadings, and Gemini gets one retry with feedback.
- 🔁 **Duplicate detection.** Warns if an expense with the same merchant, date and total already exists.
- 🖼️ **Private receipt images.** Stored in a private Supabase Storage bucket, viewed through short-lived signed links.
- 🧰 **MCP tool server.** 7 tools (extract, validate, check duplicate, save, query, set budget, check budget). The user's identity comes from their verified token, never from the AI.
- 🤖 **AI chat agent.** Ask questions in plain English. Gemini decides which tools to call, and the response shows every step it took.
- 🛡️ **Row Level Security.** Postgres policies make sure users can only touch their own rows.
- 📄 **Interactive API docs.** Generated automatically at `/docs`.

## Tech Stack

| Layer      | Technology                              |
|------------|-----------------------------------------|
| API        | FastAPI, Pydantic                       |
| Database   | PostgreSQL (Supabase), SQLAlchemy 2     |
| Auth       | Supabase Auth, PyJWT                    |
| Storage    | Supabase Storage (private bucket)       |
| AI         | Google Gemini (`google-genai`)          |
| Tools      | MCP (FastMCP, stdio)                    |
| Language   | Python 3                                |

## Project Structure

```
Expense/
├── backend/
│   ├── main.py           # Creates the app and plugs in the routers
│   ├── routers/          # Web layer: URLs, login check, HTTP errors
│   │   ├── expenses.py
│   │   ├── budgets.py
│   │   ├── receipts.py
│   │   └── chat.py
│   ├── services/         # Business logic, shared by the REST API and the MCP server
│   │   ├── expenses.py
│   │   ├── budgets.py
│   │   ├── receipts.py   # Gemini receipt reading + maths checks
│   │   ├── storage.py    # Supabase Storage upload / signed links
│   │   └── agent.py      # The AI agent loop
│   ├── mcp_server.py     # MCP tool server (7 tools)
│   ├── test_mcp.py       # Quick test of the MCP server
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

## How the AI agent works

```
You ask a question ──▶ POST /chat
                         │
                         ▼
              ┌──▶ Gemini sees: question + tool list + results so far
              │          │
              │          ├── "call tool X"  ──▶ run it on the MCP server (as you) ──┐
              │          │                                                         │
              └──────────┼─────────────────────────────────────────────────────────┘
                         └── final answer ──▶ returned, with the list of steps
```
- Gemini only **asks** for tools; the backend runs them.
- The MCP server is started with the logged-in user's token, so the agent can only reach that user's data.
- At most 8 steps per question.

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
3. In **Storage**, create a private bucket called `receipts`, with policies that let users upload and read only files in their own `<user_id>/` folder.
4. Copy the env template and fill in your project's values:
   ```bash
   cp .env.example .env
   ```
   ```
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_ANON_KEY=your-anon-key
   DATABASE_URL=postgresql://user:password@host:5432/postgres
   GEMINI_API_KEY=your-gemini-api-key
   GEMINI_MODEL=gemini-3.5-flash
   ```
   Get a free Gemini API key at [aistudio.google.com](https://aistudio.google.com).

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
| POST   | `/expenses`            | Add an expense (with optional items and receipt image) |
| GET    | `/expenses`            | List your expenses (`?category=`, `start`, `end`, `merchant` filters) |
| GET    | `/expenses/{id}`       | Get one expense                          |
| GET    | `/expenses/{id}/image` | Get a 1-hour link to the receipt photo   |
| DELETE | `/expenses/{id}`       | Delete an expense and its items          |
| PUT    | `/budgets`             | Set a monthly limit for a category (creates or updates) |
| GET    | `/budgets`             | List your budgets                        |
| GET    | `/budgets/status`      | This month's spending vs each budget     |
| DELETE | `/budgets/{id}`        | Delete a budget                          |
| POST   | `/receipts/scan`       | Upload a receipt photo; AI reads and checks it, stores the image, and flags duplicates (the expense is not saved yet) |
| POST   | `/chat`                | Ask the AI agent a question; returns the answer and the tools it used |

Example request body for `POST /chat`:
```json
{ "message": "Am I spending more on food this month than last month, and am I over any budget?" }
```

## Roadmap

- [x] Monthly budgets per category, with over-budget status
- [x] AI receipt scanning with validation and duplicate detection
- [x] MCP tool server
- [x] AI chat agent
- [ ] Frontend (React) with spending charts
- [ ] Docker setup

## Author

**Fathima Fiza** · [@fizaaa86](https://github.com/fizaaa86)
