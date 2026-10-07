# Personal Finance Tracker

A full-stack personal finance app for tracking accounts, transactions, budgets, savings goals and recurring payments, with monthly insights and reports.

- **Backend:** FastAPI + SQLAlchemy, PostgreSQL and Auth on Supabase
- **Frontend:** React + TypeScript + Vite + Tailwind CSS

---

## Features

| Area | What you can do |
|---|---|
| **Authentication** | Register, log in and out, forgot/reset password by email, silent session refresh |
| **Accounts** | Cash, bank and wallet accounts with live balances and a total balance |
| **Categories** | Built-in default categories plus your own (income, expense or both) |
| **Transactions** | Add, edit and delete; search; filter by type, account, category and date; pagination; transfers between accounts |
| **CSV import** | Upload bank statements, duplicate detection, per-row error report, import history, original file download |
| **Budgets** | Monthly limits per category with On track / Warning / Exceeded status |
| **Goals** | Savings goals with progress, monthly saving suggestion and contributions |
| **Recurring** | Automatic detection of subscriptions and regular payments, confirm or dismiss, estimated monthly cost |
| **Dashboard** | Income, expenses and savings, spending by category, 6-month trend, unusual spending, budget status |
| **Reports** | Monthly report, CSV download, print to PDF |
| **Alerts** | Budget warnings, unusual spending and upcoming recurring payments |
| **Settings** | Update name and currency, delete account (with a grace period to restore it) |

---

## Architecture

```
Browser (React app, :5173)
   │   /api/*  (Vite dev proxy, same origin, httpOnly cookies)
   ▼
FastAPI backend (:8000)
   ├── Supabase Auth      users, passwords, reset emails, JWTs
   ├── Supabase Postgres  application data (SQLAlchemy)
   └── Supabase Storage   uploaded CSV files
```

- **Cookie-based auth:** login sets `access_token` and `refresh_token` as `httpOnly` cookies. The backend refreshes an expired access token silently, so the frontend never handles tokens.
- **Money values** are returned as strings (for example `"1500.00"`) to avoid floating point errors.
- **Errors** always have the shape `{ "detail": "message" }`.
- **Scheduled cleanup:** a background job permanently deletes accounts whose deletion grace period has expired.

---

## Project structure

```
Personal_Finance_Tracker/
├── app/                      # FastAPI backend
│   ├── main.py               # app factory, routers, health checks
│   ├── core/                 # config, database, security, cookies, storage, errors
│   ├── models/               # SQLAlchemy models
│   ├── schemas/              # Pydantic request/response models
│   ├── routers/              # API routes (one file per feature)
│   └── services/             # business logic
└── frontend/                 # React app
    └── src/
        ├── api/              # API client and per-feature API modules
        ├── components/       # shared UI and feature components
        ├── hooks/            # data hooks (TanStack Query) and helpers
        ├── lib/              # formatting, validation, constants
        ├── pages/            # one file per screen
        └── types/            # TypeScript types matching the API
```

---

## Tech stack

**Backend:** Python, FastAPI, SQLAlchemy, psycopg, Pydantic and pydantic-settings, Supabase (Auth, Postgres, Storage), PyJWT, APScheduler.

**Frontend:** React, TypeScript, Vite, Tailwind CSS, React Router, TanStack Query, React Hook Form, Zod, Recharts, lucide-react.

---

## Getting started

### Prerequisites

- Python 3.11 or newer
- Node.js 20.19 or newer (or 22.12+)
- A [Supabase](https://supabase.com) project

### 1. Supabase setup

1. **Database:** create the application tables in your Supabase Postgres database and seed the default categories (the API returns *"Default categories are not seeded"* otherwise).
2. **Storage:** create a **private** bucket named `csv-imports` (or set `IMPORT_BUCKET_NAME`).
3. **Authentication, URL Configuration:**
   - Site URL: `http://localhost:5173`
   - Redirect URLs: add `http://localhost:5173/**`
4. **Authentication, Emails, SMTP Settings:** configure a custom SMTP provider (for example Resend). Supabase's built-in email sender is meant for testing and is heavily limited, so password reset emails to real users need your own SMTP.

### 2. Backend

From the project root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create a `.env` file in the project root (see [Environment variables](#environment-variables)), then start the server:

```powershell
uvicorn app.main:app --reload
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

Open `http://localhost:5173`. In development the Vite dev server proxies `/api` to `http://localhost:8000`, so cookies work without any CORS setup.

---

## Environment variables

Backend settings are read from `.env` in the project root.

| Variable | Required | Default | Description |
|---|---|---|---|
| `DATABASE_URL` | yes | | Postgres connection string |
| `SUPABASE_URL` | yes | | Supabase project URL |
| `SUPABASE_ANON_KEY` | yes | | Supabase anon (public) key |
| `SUPABASE_SERVICE_ROLE_KEY` | yes | | Supabase service role key. **Server only, never expose it** |
| `SUPABASE_JWT_SECRET` | no | | If set, tokens are verified with this secret; otherwise with the project's JWKS |
| `FRONTEND_URL` | no | `http://localhost:5173` | Used to build the password reset link |
| `CORS_ORIGINS` | no | `[]` | JSON list of allowed origins, for example `["https://app.example.com"]` |
| `COOKIE_SECURE` | no | `false` | Set to `true` in production (HTTPS) |
| `ACCESS_COOKIE_MAX_AGE` | no | `3600` | Access cookie lifetime in seconds |
| `REFRESH_COOKIE_MAX_AGE` | no | 30 days | Refresh cookie lifetime in seconds |
| `IMPORT_BUCKET_NAME` | no | `csv-imports` | Storage bucket for uploaded CSV files |
| `MAX_UPLOAD_SIZE_MB` | no | `5` | Maximum CSV upload size |
| `DEFAULT_CURRENCY` | no | `PKR` | Currency assigned to new users |
| `ACCOUNT_DELETION_GRACE_HOURS` | no | `2` | Time during which a deleted account can be restored by logging in |
| `PURGE_INTERVAL_MINUTES` | no | `10` | How often expired accounts are purged |

Example `.env` (use your own values, and never commit this file):

```env
DATABASE_URL=postgresql://USER:PASSWORD@HOST:5432/postgres
SUPABASE_URL=https://YOUR-PROJECT.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
FRONTEND_URL=http://localhost:5173
```

The frontend needs no environment variables in development.

---

## API overview

All routes are prefixed with `/api` and, except register, login and the password reset routes, require authentication.

| Group | Endpoints |
|---|---|
| **Auth** | `POST /auth/register`, `POST /auth/login`, `POST /auth/logout`, `POST /auth/forgot-password`, `POST /auth/reset-password` |
| **Users** | `GET /users`, `PATCH /users`, `DELETE /users` |
| **Accounts** | `GET /accounts`, `POST /accounts`, `GET /accounts/summary`, `GET /accounts/{id}/summary`, `PATCH /accounts/{id}`, `DELETE /accounts/{id}` |
| **Categories** | `GET /categories`, `POST /categories`, `PATCH /categories/{id}`, `DELETE /categories/{id}` |
| **Transactions** | `GET /transactions`, `POST /transactions`, `PATCH /transactions/{id}`, `DELETE /transactions/{id}`, `POST /transfers` |
| **Imports** | `POST /transactions/import`, `GET /imports`, `GET /imports/{id}/transactions`, `GET /imports/{id}/download` |
| **Budgets** | `GET /budgets`, `POST /budgets`, `PATCH /budgets/{id}`, `DELETE /budgets/{id}` |
| **Goals** | `GET /goals`, `POST /goals`, `PUT /goals/{id}`, `DELETE /goals/{id}`, `POST /goals/{id}/contribute` |
| **Recurring** | `GET /recurring`, `POST /recurring/detect`, `PATCH /recurring/{id}` |
| **Insights** | `GET /insights/summary`, `/insights/categories`, `/insights/trends`, `/insights/unusual` |
| **Reports** | `GET /reports/monthly` |
| **Alerts** | `GET /alerts` |

Full request and response schemas are available in the interactive docs at `/docs`.

---

## How some features work

**CSV import.** The backend recognises columns by name: `Date`, `Description`, and either `Amount` (negative = expense) or `Debit` / `Credit`. `Type` and `Balance` are optional. Rows that were already imported (same account, date, amount and description) are skipped. If the file has a `Balance` column, the account's opening balance is adjusted so the balance matches the statement.

**Recurring payments.** Detection looks for expenses from the same merchant that appear at least 3 times with a regular gap (weekly, every 2 weeks or monthly) and a similar amount (within 10%). Run detection again after adding new transactions.

**Password reset.** The user requests a reset email, follows the link in it, and sets a new password on the `/reset-password` page. The backend confirms the link with Supabase, updates the password and signs the user out of all other sessions. The same response is returned whether or not the email is registered.

**Account deletion.** Deleting an account only schedules it. Logging in again within the grace period restores it; afterwards all data is permanently removed.

---

## Production notes

- Serve the frontend and the API **from the same domain** (for example behind a reverse proxy that forwards `/api` to FastAPI). The `/api` proxy in `vite.config.ts` only exists in development.
- Set `COOKIE_SECURE=true` and serve over HTTPS.
- If the frontend and API are on different origins, set `CORS_ORIGINS`, and review the cookie `SameSite` settings.
- Update `FRONTEND_URL`, the Supabase **Site URL** and **Redirect URLs** to the production domain.
- Build the frontend with `npm run build` and serve the `frontend/dist` folder.
- Keep `SUPABASE_SERVICE_ROLE_KEY` and database credentials in server-side secrets only.

---

## Known limitations

- Only CSV files can be imported (no PDF import).
- Alerts are read-only: there is no mark-as-read endpoint yet.
- Reports can be downloaded as CSV (generated in the browser) or printed to PDF; there is no server-side export.
- A bank account that has transactions cannot be deleted through the API.
- Changing the profile currency changes the label only; amounts are not converted.