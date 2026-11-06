# AI Expense Tracker

A personal expense tracker where you can **photograph a receipt** and have AI fill in the expense, set **monthly budgets**, see **spending charts**, and **ask questions in plain English** ("Am I spending more on food than last month?").

Built with a **FastAPI** backend, a **React** frontend, **Supabase** (auth, Postgres, storage), **Google Gemini**, and an **MCP** tool server, all packaged with **Docker**.

## Features

- 📸 **AI receipt scanning.** Gemini reads the merchant, date, items, discount, tax and total. Plain-maths checks catch misreadings, Gemini gets one retry with feedback, and you review everything before saving.
- 🔁 **Duplicate detection.** Warns if the same merchant, date and total is already saved.
- 🤖 **AI chat agent.** Ask about your spending. Gemini plans which tools to call, and every answer shows the steps it took.
- 🧰 **MCP tool server.** 7 tools (extract, validate, check duplicate, save, query, set budget, check budget), shared by the agent and usable from any MCP client.
- 📊 **Dashboard.** Headline numbers, spending per month, and this month by category.
- 💰 **Monthly budgets.** Per-category limits with progress bars that turn red when you go over.
- 🧾 **Expenses.** Line items, filters by category, date and merchant, and private receipt photos.
- 🔐 **Security in layers.** Verified Supabase JWTs, Row Level Security in Postgres and Storage, and the user's identity kept outside the AI.
- 🐳 **One-command start** with Docker Compose.

## Tech Stack

| Layer      | Technology                                         |
|------------|----------------------------------------------------|
| Frontend   | React 19, Vite, Tailwind CSS, Recharts             |
| API        | FastAPI, Pydantic                                  |
| Database   | PostgreSQL (Supabase), SQLAlchemy 2, RLS           |
| Auth       | Supabase Auth, PyJWT (ES256 via JWKS)              |
| Storage    | Supabase Storage (private bucket)                  |
| AI         | Google Gemini (`google-genai`)                     |
| Tools      | MCP (FastMCP, stdio)                               |
| Deployment | Docker, Docker Compose, nginx                      |

## How it works

```
 Browser (React)  ──login──▶  Supabase Auth ──▶ token (JWT)
       │
       │  every request: "Authorization: Bearer <token>"
       ▼
 FastAPI backend ── verifies the token, then talks to Postgres AS that user (RLS)
       │
       ├── /receipts/scan ──▶ Gemini reads the photo ──▶ maths checks ──▶ duplicate check
       │
       └── /chat ──▶ starts the MCP server with the user's token
                        │
                ┌──▶ Gemini: question + tool list + results so far
                │          ├── "call tool X" ──▶ MCP server runs it (as the user) ──┐
                └──────────┼────────────────────────────────────────────────────────┘
                           └── final answer + list of steps
```

### Security design
- **Two locks on every row.** The API filters by the logged-in user, and Postgres **Row Level Security** enforces the same rule again, in case the code ever has a bug.
- **Receipt photos** live in a **private** bucket. Users can only reach their own `<user_id>/` folder, and images are viewed through 1-hour signed links.
- **The AI never chooses whose data it sees.** The MCP server gets the user's verified token from its environment. `user_id` is never a tool input, so a prompt like "show me everyone's expenses" cannot work.
- **Human in the loop.** Scanned receipts are never saved automatically, and the agent is told not to save without a clear request.
- **Secrets** stay in `backend/.env`. They're never committed, and never copied into a Docker image.

## Project Structure

```
Expense/
├── docker-compose.yml       # Starts backend + frontend together
├── backend/
│   ├── main.py              # Creates the app, CORS, plugs in the routers
│   ├── routers/             # Web layer: expenses, budgets, receipts, chat
│   ├── services/            # Business logic, shared by the REST API and MCP
│   │   ├── expenses.py, budgets.py
│   │   ├── receipts.py      # Gemini receipt reading + maths checks
│   │   ├── storage.py       # Supabase Storage upload / signed links
│   │   └── agent.py         # The AI agent loop
│   ├── mcp_server.py        # MCP tool server (7 tools)
│   ├── auth.py, db.py       # Token verification; per-user DB session (RLS)
│   ├── models.py, schemas.py
│   ├── sql/schema.sql       # Tables, indexes, RLS + storage policies
│   ├── test_mcp.py, get_token.py, check_db.py   # Dev helpers
│   ├── Dockerfile
│   └── .env.example
└── frontend/
    ├── src/
    │   ├── App.jsx          # Login check + tabs
    │   ├── pages/           # Login, Dashboard, Expenses, Scan, Budgets, Chat
    │   ├── components/      # ExpenseForm (shared by Expenses and Scan)
    │   └── lib/             # Supabase client, API helper, formatting
    ├── Dockerfile           # Build with Node, serve with nginx
    └── .env.example
```

## Getting Started

### 1. Set up Supabase
1. Create a project at [supabase.com](https://supabase.com).
2. In the **SQL Editor**, run the contents of `backend/sql/schema.sql`. This creates the tables, the security policies and the private `receipts` storage bucket.

### 2. Add your settings
```bash
git clone https://github.com/fizaaa86/AI-Expense-Tracker.git
cd AI-Expense-Tracker
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
```
Fill in **`backend/.env`** (secret, never share it):
```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
DATABASE_URL=postgresql://user:password@host:5432/postgres
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-3.6-flash
```
and **`frontend/.env.local`** (public values only):
```
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
VITE_API_URL=http://localhost:8000
```
Get a free Gemini API key at [aistudio.google.com](https://aistudio.google.com).

### 3a. Run with Docker (easiest)
```bash
docker compose up --build
```
Open **http://localhost:8080**. Stop it with **Ctrl+C**, then `docker compose down`.

### 3b. Or run for development (auto-reload)
**Backend:**
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
fastapi dev main.py          # API docs at http://127.0.0.1:8000/docs
```
**Frontend** (in a second terminal):
```bash
cd frontend
npm install
npm run dev                  # http://localhost:5173
```

## API Endpoints

All endpoints except `/` require `Authorization: Bearer <token>`. Interactive docs are at `/docs`.

| Method | Endpoint               | Description                              |
|--------|------------------------|------------------------------------------|
| GET    | `/`                    | Health check                             |
| GET    | `/me`                  | The logged-in user's id and email        |
| POST   | `/expenses`            | Add an expense (with optional items and receipt image) |
| GET    | `/expenses`            | List expenses (`category`, `start`, `end`, `merchant` filters) |
| GET    | `/expenses/{id}`       | Get one expense                          |
| GET    | `/expenses/{id}/image` | A 1-hour link to the receipt photo       |
| DELETE | `/expenses/{id}`       | Delete an expense and its items          |
| PUT    | `/budgets`             | Set a monthly limit for a category (creates or updates) |
| GET    | `/budgets`             | List budgets                             |
| GET    | `/budgets/status`      | This month's spending vs each budget     |
| DELETE | `/budgets/{id}`        | Delete a budget                          |
| POST   | `/receipts/scan`       | Upload a receipt photo: AI reading, checks, duplicates (not saved yet) |
| POST   | `/chat`                | Ask the AI agent; returns the answer and the tools it used |

## Design notes

- **ES256 tokens via JWKS.** Supabase signs tokens with an asymmetric key, so the backend verifies them with Supabase's **public** keys. No shared secret is stored, which is safer than the HS256 approach first planned.
- **One set of business logic, two front doors.** The REST API and the MCP server both call the same `services/` functions.
- **The AI is never trusted to check itself.** Receipt totals are verified with plain arithmetic (₹1 tolerance for round-off). Duplicates are found by a database query.
- **Clear error handling.** Gemini errors, usage limits and timeouts become readable messages instead of crashes.

## Known limitations

- **Gemini free tier:** about 20 requests per day per model, and 5 per minute. One chat question uses 2–5 requests. The model can be changed with `GEMINI_MODEL`.
- **Unsaved scans leave their photo in storage.** A clean-up job would remove photos that no expense uses.
- **Chat history lives only in the browser tab.** It's gone after a refresh.
- **Rupees only**, one photo per receipt, max 5 MB.
- **Docker setup is for running locally.** Hosting it online would need HTTPS and the real website address in `FRONTEND_ORIGINS`.

## Future ideas
- Recurring expenses and reminders
- Export to CSV / PDF
- Automated tests and a CI pipeline
- Clean-up of unused receipt photos

## Author

**Fathima Fiza** · [@fizaaa86](https://github.com/fizaaa86)
