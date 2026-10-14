# Personal Finance Tracker

![Personal Finance Tracker](docs/thumbnail.png)

A personal finance web app for tracking money across bank accounts and mobile wallets. Import your bank statements as CSV or PDF, and the app sorts transactions into categories, recognises money you moved between your own accounts, tracks budgets and goals, finds recurring bills and shows monthly insights and reports.

- **Backend:** FastAPI, SQLAlchemy, Alembic, PostgreSQL, deployed on Railway
- **Frontend:** React, TypeScript, Vite, Tailwind CSS, deployed on Vercel
- **Auth, database and file storage:** Supabase

---

## Features

| Area | What you can do |
|---|---|
| **Authentication** | Register, log in and out, forgot and reset password by email. Sessions renew automatically in the background. |
| **Accounts** | Cash, bank and wallet accounts with live balances and a total balance. |
| **Transactions** | Add, edit and delete. Search, filter by type, account, category and date, with pagination. Record transfers between accounts. |
| **Statement import** | Upload bank statements as CSV or PDF, including password-protected PDFs. Tested with statements from Meezan Bank, Bank AL Habib, NayaPay and OPay. Skips duplicates, reports bad rows and keeps an import history with the original file. |
| **Own transfers** | Money moved between your own accounts is found automatically and kept out of income and expenses, so totals stay correct. Any imported row can also be marked or unmarked as a transfer by hand. |
| **Categories** | Built-in default categories plus your own, with automatic categorisation on import. |
| **Budgets** | Monthly limits per category with On track, Warning and Exceeded status. |
| **Goals** | Saving goals with progress, a suggested monthly amount and contributions. |
| **Recurring** | Detects subscriptions and regular payments, lets you confirm or dismiss them and estimates the monthly cost. |
| **Dashboard** | Total balance, income, expenses, spending pace compared with last month, upcoming bills, spending by category, a 6-month trend, unusual spending and budget status. |
| **Reports** | Monthly report with categories, budgets and recurring bills. Download as CSV or print to PDF. |
| **Alerts** | Budget warnings, unusual spending and upcoming recurring payments, with mark as read. |
| **Settings** | Change name and currency. Delete your account, with a grace period to restore it by logging in again. |

---

## Architecture

```
Browser ──► Vercel (React app)
               │  /api/*  rewritten to Railway, so the app and API share one origin
               ▼
           Railway (FastAPI, Docker)
               ├── Supabase Auth      users, passwords, reset emails, JWTs
               ├── Supabase Postgres  application data (SQLAlchemy + Alembic)
               └── Supabase Storage   uploaded statement files
```

- **Cookie-based auth.** Login sets `access_token` and `refresh_token` as `httpOnly` cookies. When the access token expires, the backend renews the session on the next request, so the frontend never handles tokens.
- **Same origin.** In development the Vite dev server proxies `/api` to the backend. In production `frontend/vercel.json` rewrites `/api/*` to the Railway URL. No CORS setup is needed in either case.
- **Money values** are sent as strings (for example `"1500.00"`) to avoid floating point errors.
- **Errors** always have the shape `{ "detail": "message" }`.
- **Background job.** A scheduler permanently deletes accounts whose deletion grace period has ended.

---

## Project structure

```
Personal_Finance_Tracker/
├── app/                    FastAPI backend
│   ├── main.py             app factory, routers, health checks
│   ├── core/               config, database, security, cookies, storage, errors
│   ├── models/             SQLAlchemy models
│   ├── schemas/            Pydantic request and response models
│   ├── routers/            API routes, one file per feature
│   └── services/           business logic (CSV and PDF parsing, transfers, insights, ...)
├── alembic/                database migrations
├── scripts/                seed script for default categories
├── tests/                  pytest tests
├── frontend/               React app
│   ├── src/
│   │   ├── api/            API client and one module per feature
│   │   ├── components/     shared UI and feature components
│   │   ├── hooks/          data hooks (TanStack Query)
│   │   ├── lib/            formatting, validation, helpers
│   │   ├── pages/          one file per screen
│   │   └── types/          TypeScript types matching the API
│   └── vercel.json         production rewrite of /api to the backend
├── .github/workflows/      CI: backend tests, frontend lint and build
├── Dockerfile              backend image (used by Railway)
└── docker-compose.yml      run backend and frontend together locally
```

---

## Tech stack

**Backend:** Python 3.12, FastAPI, SQLAlchemy 2, Alembic, psycopg 3, Pydantic and pydantic-settings, Supabase (Auth, Postgres, Storage), PyJWT, pdfplumber, APScheduler, uv, pytest.

**Frontend:** React 19, TypeScript, Vite, Tailwind CSS 4, React Router, TanStack Query, React Hook Form, Zod, Recharts, lucide-react, oxlint.

---

## Getting started

### Prerequisites

- Python 3.12 or newer and [uv](https://docs.astral.sh/uv/)
- Node.js 22
- A [Supabase](https://supabase.com) project

### 1. Supabase setup

1. **Storage:** create a **private** bucket named `csv-imports`, or set `IMPORT_BUCKET_NAME` to another name.
2. **Authentication → URL Configuration:**
   - Site URL: `http://localhost:5173`
   - Redirect URLs: add `http://localhost:5173/**`
3. **Authentication → Emails → SMTP Settings:** add a custom SMTP provider (for example Resend). The built-in Supabase sender is only for testing and is heavily rate limited, so reset emails to real users need your own SMTP.

### 2. Backend

Create a `.env` file in the project root (see [Environment variables](#environment-variables)), then from the project root:

```powershell
uv sync
uv run alembic upgrade head
uv run python scripts/seed_default_categories.py
uv run uvicorn app.main:app --reload
```

- API: `http://localhost:8000`
- Interactive docs: `http://localhost:8000/docs`
- Health checks: `GET /health` and `GET /health/database`

### 3. Frontend

In a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

### Run with Docker (optional)

```powershell
docker compose up --build
```

The app is then available at `http://localhost:8080`.

---

## Environment variables

The backend reads its settings from `.env` in the project root.

| Variable | Required | Default | Description |
|---|---|---|---|
| `DATABASE_URL` | yes | | Postgres connection string |
| `SUPABASE_URL` | yes | | Supabase project URL |
| `SUPABASE_ANON_KEY` | yes | | Supabase anon (public) key |
| `SUPABASE_SERVICE_ROLE_KEY` | yes | | Supabase service role key. **Server only, never expose it.** |
| `SUPABASE_JWT_SECRET` | no | | If set, tokens are verified with this secret, otherwise with the project's JWKS |
| `FRONTEND_URL` | no | `http://localhost:5173` | Used to build the password reset link |
| `CORS_ORIGINS` | no | `[]` | JSON list of allowed origins, only needed if the app and API are on different origins |
| `COOKIE_SECURE` | no | `false` | Set to `true` in production (HTTPS) |
| `ACCESS_COOKIE_MAX_AGE` | no | `3600` | Access cookie lifetime in seconds |
| `REFRESH_COOKIE_MAX_AGE` | no | 30 days | Refresh cookie lifetime in seconds |
| `IMPORT_BUCKET_NAME` | no | `csv-imports` | Storage bucket for uploaded statements |
| `MAX_UPLOAD_SIZE_MB` | no | `5` | Maximum statement file size |
| `DEFAULT_CURRENCY` | no | `PKR` | Currency for new users |
| `ACCOUNT_DELETION_GRACE_HOURS` | no | `2` | Time in which a deleted account can be restored by logging in |
| `PURGE_INTERVAL_MINUTES` | no | `10` | How often expired accounts are purged |

Example `.env` (use your own values and never commit this file):

```env
DATABASE_URL=postgresql://USER:PASSWORD@HOST:5432/postgres
SUPABASE_URL=https://YOUR-PROJECT.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
FRONTEND_URL=http://localhost:5173
```

The frontend needs no environment variables.

---

## API overview

All routes start with `/api`. Everything except register, login, forgot password and reset password needs a logged-in user.

| Group | Endpoints |
|---|---|
| **Auth** | `POST /auth/register`, `POST /auth/login`, `POST /auth/logout`, `POST /auth/forgot-password`, `POST /auth/reset-password` |
| **Users** | `GET /users`, `PATCH /users`, `DELETE /users` |
| **Accounts** | `GET /accounts`, `POST /accounts`, `GET /accounts/summary`, `GET /accounts/{id}/summary`, `PATCH /accounts/{id}`, `DELETE /accounts/{id}` |
| **Categories** | `GET /categories`, `POST /categories`, `PATCH /categories/{id}`, `DELETE /categories/{id}` |
| **Transactions** | `GET /transactions`, `POST /transactions`, `PATCH /transactions/{id}`, `DELETE /transactions/{id}`, `POST /transfers` |
| **Own transfers** | `POST /transactions/own-transfers/detect`, `POST /transactions/{id}/mark-transfer`, `POST /transactions/{id}/not-transfer` |
| **Imports** | `POST /transactions/import`, `GET /imports`, `GET /imports/{id}/transactions`, `GET /imports/{id}/download` |
| **Budgets** | `GET /budgets`, `POST /budgets`, `PATCH /budgets/{id}`, `DELETE /budgets/{id}` |
| **Goals** | `GET /goals`, `POST /goals`, `PUT /goals/{id}`, `DELETE /goals/{id}`, `POST /goals/{id}/contribute` |
| **Recurring** | `GET /recurring`, `POST /recurring/detect`, `PATCH /recurring/{id}` |
| **Insights** | `GET /insights/summary`, `/insights/categories`, `/insights/trends`, `/insights/top`, `/insights/messages`, `/insights/unusual` |
| **Reports** | `GET /reports/monthly` |
| **Alerts** | `GET /alerts`, `POST /alerts/read-all`, `PATCH /alerts/{id}/read` |

Full request and response schemas are in the interactive docs at `/docs`.

---

## How some features work

**Statement import.** CSV columns are recognised by name, including common bank variants: a date, a description, and either one amount column (negative means expense) or separate debit and credit columns. Amounts like `Rs. 1,250`, `(500)`, `300-`, `1.234,56` and `500 CR` are understood. For PDFs, the parser finds the transaction table on each page, even when the statement has no description column or unusual headers, and converts it to the same format. Rows already imported (same account, date, amount and description) are skipped. On the first import into an account, its opening balance is set from the statement so the balance matches the bank.

**Transfers between your own accounts.** A move from one of your accounts to another shows up as an expense in one statement and as income in the other. Counted as spending and earning, it would distort every total. After each import the app marks a row as a transfer when:
- it has a transfer word (transfer, Raast, IBFT, funds, sent, received, ...) and your own name, compared without vowels or spaces so "Abdul Moeed" and "ABDUL MUEED" match, or
- it has a transfer word and matches a row in another of your accounts with the same amount going the other way within a day.

Both sides of a move are linked into one transfer. Transfers are shown in blue as "Meezan → NayaPay", leave balances correct and are left out of income, expenses, budgets and reports. You can mark any imported row as a transfer, or undo a match with "Not a transfer", which is remembered.

**Recurring payments.** Detection looks for expenses from the same merchant that appear at least 3 times with a regular gap (weekly, every 2 weeks or monthly) and a similar amount (within 10%).

**Password reset.** The user requests a reset email, opens the link and sets a new password on the `/reset-password` page. The backend checks the link with Supabase, updates the password and signs out all other sessions. The response is the same whether or not the email is registered.

**Account deletion.** Deleting an account only schedules it. Logging in again within the grace period restores it. After that, all data is permanently removed.

---

## Testing and CI

```powershell
uv run pytest -q
cd frontend
npm run lint
npm run build
```

GitHub Actions runs the backend tests and the frontend lint and build on every pull request and on pushes to `main`. The `main` branch is protected, so changes go through a pull request with passing checks.

---

## Deployment

- **Backend (Railway):** built from the `Dockerfile`. Set the environment variables above, with `COOKIE_SECURE=true` and `FRONTEND_URL` set to the Vercel domain. Run `alembic upgrade head` against the production database after adding a migration.
- **Frontend (Vercel):** root directory `frontend`, build command `npm run build`, output `dist`. Update the Railway URL in `frontend/vercel.json` if it changes.
- **Supabase:** set the **Site URL** and **Redirect URLs** to the Vercel domain, so password reset links open the live app.
- Keep `SUPABASE_SERVICE_ROLE_KEY` and database credentials in server-side secrets only.

---

## Known limitations

- PDF import needs a text-based PDF. Scanned or photographed statements are not supported.
- Reports are downloaded as CSV (made in the browser) or printed to PDF; there is no server-side export.
- Changing the profile currency changes the label only; amounts are not converted.
- Own-transfer detection by name needs your full name (first and last) in Settings.
