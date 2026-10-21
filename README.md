# WEBANKI — Your Money, Your Goals, Your Future

> **Your balance shows what you have. WEBANKI shows what you can safely spend.**

🔗 [Live demo](https://frontend-lake-xi-76.vercel.app/) · 🎥 [Demo video](https://drive.google.com/file/d/1PVrVcCOYVzBgbY7oTEPJ4SImcIxVh_Rk/view?usp=sharing) · 🔒 [Security report](SECURITY_REPORT.md) · 📊 [Slides](https://drive.google.com/file/d/1VnlIfgagM38XqRZpJdzIg5WE7HckYYbh/view?usp=sharing) · 💻 [GitHub](https://github.com/saldebis/WeBankI)

---

## Table of Contents

1. [What is WEBANKI?](#what-is-webanki)
2. [Features](#features)
3. [Architecture](#architecture)
4. [Local Development](#local-development)
5. [Environment Variables](#environment-variables)
6. [Deployment](#deployment)
7. [API Reference](#api-reference)
8. [Test Cases](#test-cases)
9. [Team](#team)

---

## What is WEBANKI?

A bank balance is misleading. Money already committed to rent, bills, and savings still shows up as spendable. Most budgeting apps only review spending *after* it has happened.

WEBANKI earmarks your income into **buckets** (rent, bills, tuition, savings) *before* you spend it, then exposes a single **Safe-to-Spend** number — the money you can actually use without touching your commitments.

| Total balance | Rent | Bills | Savings | **Safe to spend** |
|---:|---:|---:|---:|---:|
| $2,000 | −$700 | −$200 | −$300 | **$800** |

**WEWE** is a built-in AI money assistant (powered by GPT-4o-mini with a rule-based fallback) that answers questions like *"Can I afford $60 this week?"* or *"How long until I save $1,500?"* using your live financial snapshot.

---

## Features

| Feature | Description |
|---|---|
| **Earmarked budgeting** | Salary is split into buckets (rent, bills, tuition, savings) on payday |
| **Safe-to-Spend** | Real-time figure: balance minus all reserved money |
| **Savings goals** | Track progress toward named goals; round-up savings from every expense |
| **Weekly spending limit** | Set a weekly cap; WEWE warns when you're close |
| **Bill reminders** | Alerts for bills due within 3 days that aren't fully funded |
| **Recurring bills** | Due date auto-advances one month after payment |
| **Monthly report** | Spending breakdown by category |
| **Send money** | Transfer to any registered user by email |
| **QR payments** | Generate a one-time token; anyone can pay it by pasting the token |
| **Split bills** | Split a total equally across multiple users; settle with one tap |
| **WEWE AI chat** | GPT-4o-mini with live financial context; rule-based fallback if no key |
| **Dark / light theme** | System, light, or dark mode persisted in `localStorage` |
| **Secure accounts** | PBKDF2-SHA256 passwords, JWT auth (12-hour expiry), per-user data isolation |

---

## Architecture

```
┌─────────────────────┐        HTTPS        ┌──────────────────────────┐
│  frontend/          │  ──────────────────▶ │  backend/                │
│  index.html         │                      │  main.py  (FastAPI)      │
│  (Vanilla JS SPA)   │ ◀────────────────── │  api/index.py (Vercel EP)│
│  Hosted on Vercel   │       JSON           │  SQLite  (/tmp or local) │
└─────────────────────┘                      └──────────────────────────┘
```

- **Frontend:** Single HTML file, no build step, deployed as a static site on Vercel.
- **Backend:** FastAPI app; `backend/api/index.py` is the Vercel serverless entry point.
- **Database:** SQLite via Python's built-in `sqlite3`. Money is stored as **integer cents** to eliminate floating-point rounding bugs.
- **Auth:** JWT (HS256) via `PyJWT`. Passwords hashed with PBKDF2-SHA256 (200,000 iterations, random salt per user).

---

## Local Development

### Prerequisites

- Python 3.10+
- A terminal (PowerShell, bash, zsh)

### 1 — Clone the repo

```bash
git clone https://github.com/saldebis/WeBankI.git
cd WeBankI
```

### 2 — Install Python dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 3 — Configure environment variables

```bash
# Copy the example file and fill in your values
cp .env.example .env
```

Edit `backend/.env` — at minimum set `WEBANKI_SECRET` to a long random string. `OPENAI_API_KEY` is optional; WEWE falls back to rule-based replies without it.

### 4 — Run the backend

```bash
cd backend
uvicorn main:app --reload --port 8000
```

The API is now available at `http://localhost:8000`. Interactive docs: `http://localhost:8000/docs`.

### 5 — Open the frontend

Open `frontend/index.html` directly in your browser, **or** start a local server:

```bash
# from the repo root
python -m http.server 5500 --directory frontend
```

Then visit `http://localhost:5500`.

> **Note:** The frontend's `API` constant in `index.html` points to `https://webanki.vercel.app` by default. For local testing change it to `http://localhost:8000` on line 440 of `frontend/index.html`.

---

## Environment Variables

All variables are read at startup from the process environment or `backend/.env` (via `python-dotenv`).

| Variable | Required | Default | Description |
|---|---|---|---|
| `WEBANKI_SECRET` | **Yes** (prod) | `dev-secret-change-me` | Secret key used to sign JWT tokens. Use a long random string in production. |
| `OPENAI_API_KEY` | No | *(not set)* | OpenAI key for WEWE AI chat. Falls back to rule-based replies if absent. |
| `OPENAI_MODEL` | No | `gpt-4o-mini` | OpenAI model name to use for WEWE. |
| `WEBANKI_DB` | No | `/tmp/webanki.db` (Linux) or `backend/webanki.db` (Windows) | Path to the SQLite database file. |

> ⚠️ On Vercel's Hobby plan `/tmp` is **ephemeral** — data is lost on cold starts. For persistence, host the backend on Railway, Render, or Fly.io, or replace SQLite with a cloud database (Neon, Supabase, PlanetScale).

---

## Deployment

### Backend — Vercel (Serverless)

The backend is a Vercel Python serverless function.

#### First-time setup

1. Install the Vercel CLI:
   ```bash
   npm i -g vercel
   ```

2. Link the project (run from `backend/`):
   ```bash
   cd backend
   vercel link
   ```

3. Set production environment variables in the Vercel dashboard or via CLI:
   ```bash
   vercel env add WEBANKI_SECRET production
   vercel env add OPENAI_API_KEY production   # optional
   ```

4. Deploy:
   ```bash
   vercel --prod
   ```

#### Subsequent deploys

```bash
cd backend
vercel --prod
```

Or simply push to the `main` branch if you have Vercel's GitHub integration enabled — Vercel will deploy automatically.

#### Key files

| File | Purpose |
|---|---|
| `backend/vercel.json` | Tells Vercel to build `api/index.py` with `@vercel/python` and route all traffic to it |
| `backend/api/index.py` | Thin entry point that adds `backend/` to `sys.path` and imports `app` from `main.py` |
| `backend/requirements.txt` | Python dependencies installed by Vercel at build time |

---

### Frontend — Vercel (Static)

The frontend is a single `frontend/index.html` file with no build step.

1. In the Vercel dashboard, create a new project pointed at the repo root.
2. Set **Framework Preset** to `Other` and **Output Directory** to `frontend`.
3. No build command is needed.
4. Deploy. Vercel serves `index.html` at the root URL.

> Make sure the `API` constant at the top of the `<script>` block in `index.html` points to your deployed backend URL.

---

### Self-hosted (non-Vercel)

```bash
cd backend
pip install -r requirements.txt
export WEBANKI_SECRET="your-long-random-secret"
export OPENAI_API_KEY="sk-..."   # optional
uvicorn main:app --host 0.0.0.0 --port 8000
```

Serve `frontend/index.html` with any static file server (Nginx, Caddy, `python -m http.server`). Update the `API` constant in `index.html` to point to your backend host.

---

## API Reference

All authenticated endpoints require an `Authorization: Bearer <token>` header.

### Auth

| Method | Path | Body | Description |
|---|---|---|---|
| `POST` | `/auth/register` | `{name, email, password, salary, balance?, weekly_limit?, savings_pct?}` | Create account, returns `{token}` |
| `POST` | `/auth/login` | `{email, password}` | Returns `{token}` |

### Dashboard & Reports

| Method | Path | Description |
|---|---|---|
| `GET` | `/me/dashboard` | Balance, safe-to-spend, buckets, WEWE tip |
| `GET` | `/me/report` | Spending this month by category |
| `GET` | `/me/reminders` | Bills due within 3 days, not fully funded |
| `GET` | `/me/analyse-bills` | Bill funding status, total still needed |
| `GET` | `/me/afford?amount=<cents>` | WEWE affordability check |

### Buckets & Budget

| Method | Path | Body | Description |
|---|---|---|---|
| `GET` | `/me/buckets` | — | List all buckets |
| `POST` | `/me/buckets` | `{kind, name, amount_due, due_date?}` | Create bucket |
| `PATCH` | `/me/buckets/{id}` | `{name?, amount_due?, due_date?}` | Update bucket |
| `PUT` | `/me/budget/{kind}` | `{kind, amount_due, due_date?}` | Upsert primary bucket for a kind (`bills`, `rent`, `tuition`, `savings`, `weekly`) |
| `POST` | `/me/buckets/{id}/pay` | — | Pay a bill bucket; due date advances one month |
| `POST` | `/me/payday` | — | Add salary; earmark rent → bills → tuition → savings |

### Transactions & Balance

| Method | Path | Body | Description |
|---|---|---|---|
| `POST` | `/me/expenses` | `{amount, category, note?, round_up?}` | Record an expense |
| `PATCH` | `/me/balance` | `{balance}` | Directly set balance (top-up / correction) |
| `PATCH` | `/me/weekly-limit` | `{weekly_limit}` | Update weekly spending limit |
| `POST` | `/me/plan-savings` | `{goal_bucket_id, months}` | Monthly saving needed to reach a goal |

### Payments

| Method | Path | Body | Description |
|---|---|---|---|
| `POST` | `/me/send` | `{to_email, amount, note?}` | Transfer money to another user |
| `POST` | `/me/qr/generate?amount=&note=` | — | Generate one-time QR token |
| `POST` | `/me/qr/pay?token=` | — | Pay a QR token |
| `POST` | `/me/split` | `{amount, participants, note?}` | Split a bill equally |
| `GET` | `/me/splits` | — | List splits owed to you and you owe |
| `POST` | `/me/splits/{id}/settle` | — | Payer settles a split |

### WEWE

| Method | Path | Body | Description |
|---|---|---|---|
| `POST` | `/me/wewe/chat` | `{message, history?}` | AI chat (GPT-4o-mini or rule-based fallback) |

> All amounts are in **integer cents** (e.g. `$12.50` → `1250`).

---

## Test Cases

The test suite lives in [`backend/test_api.py`](backend/test_api.py). It uses FastAPI's built-in `TestClient` and runs against a fresh temporary SQLite database — no server or network required.

### Running the tests

```bash
cd backend
pip install -r requirements.txt
python test_api.py
```

Expected output on success:
```
all checks passed
```

---

### Test case catalogue

#### Authentication

| # | Test | Expected |
|---|---|---|
| A-01 | Register user A with valid data | `200` + JWT token |
| A-02 | Register user B with valid data | `200` + JWT token |
| A-03 | Register with duplicate email | `409 Conflict` |
| A-04 | Login with wrong password | `401 Unauthorized` |
| A-05 | Login with correct credentials | `200` + JWT token |
| A-06 | Access `/me/dashboard` with no token | `401` or `403` |

#### Bucket CRUD

| # | Test | Expected |
|---|---|---|
| B-01 | Create rent bucket for user A | `200`, returns `id` |
| B-02 | Create bills and savings buckets for user A | `200` each |
| B-03 | List buckets for user A | `200`, 3 buckets returned |
| B-04 | PATCH rent bucket — update `amount_due` | `200`, field updated to new value |
| B-05 | User B cannot PATCH user A's bucket | `404` (A's bucket not visible to B) |

#### Budget Upsert (`PUT /me/budget/{kind}`)

| # | Test | Expected |
|---|---|---|
| U-01 | Upsert `bills` with no existing bucket → creates | `200`, `created: true`, `amount_due` matches |
| U-02 | Upsert `bills` again → updates existing, no duplicate | `200`, `created: false`, `amount_due` updated |
| U-03 | Dashboard reflects upserted bills value | bucket with updated `amount_due` present |
| U-04 | Upsert `rent` (bucket already exists) → updates | `200`, `created: false`, `amount_due` updated |
| U-05 | Upsert `tuition` (no bucket yet) → creates | `200`, `created: true` |
| U-06 | Upsert `weekly` → updates `weekly_limit` on user | `200`, dashboard `weekly.limit` matches |
| U-07 | User B upsert does not affect user A's buckets | A's bills bucket unchanged after B's upsert |
| U-08 | Upsert with invalid kind | `400` or `422` |

#### Core Financial Workflow

| # | Test | Expected |
|---|---|---|
| W-01 | Payday — salary added and plan returned | balance increases by salary |
| W-02 | Add expense — balance decreases | `200`, `spent` matches amount |
| W-03 | Dashboard `safe_to_spend` = balance − reserved | value is consistent |
| W-04 | Afford check within safe-to-spend | `{ok: true}` |
| W-05 | Monthly report after expenses | totals by category correct |
| W-06 | Reminders — add bill due in 2 days with large shortfall | reminder appears |
| W-07 | Pay a bucket — balance decreases, due date advances | `200`, `next_due` is one month later |
| W-08 | User B cannot pay user A's bucket | `404` |
| W-09 | User B dashboard balance starts at 0 | `balance === 0` |

### Manual / browser test cases

The following require the frontend and a running backend:

| # | Scenario | Steps | Expected |
|---|---|---|---|
| M-01 | Register new account | Fill name, email, salary → Create account | Redirects to dashboard, name shown |
| M-02 | Login with existing account | Enter email + password → Login | Dashboard loads with correct balance |
| M-03 | Invalid login | Enter wrong password | Error message shown, no redirect |
| M-04 | Edit Bills budget card | Tap Bills card → set amount → Save | Card updates, dashboard reloads |
| M-05 | Split salary (Payday) | Bills & Budgets → Split my salary | Toast shows salary added and split |
| M-06 | Add expense with round-up | Insights → enter $12.40 → Add expense | Toast shows round-up saved to goal |
| M-07 | Send money | Home → Send → enter recipient email + amount | Toast confirms, sender balance reduced |
| M-08 | Generate QR token | Home → Scan to pay → Generate → enter amount | Token + QR code displayed |
| M-09 | Pay QR token | Paste token → Pay this code | Toast confirms payment |
| M-10 | Split bill | Home → Split a payment → emails + amount | Toast shows share per person |
| M-11 | WEWE chat — affordability | WEWE tab → "Can I afford $200?" | Relevant yes/no with safe-to-spend figure |
| M-12 | WEWE chat — rule-based fallback | Same as above with no API key set | Rule-based answer with correct figure |
| M-13 | Dark mode | Header → Dark button | Theme switches, persists on reload |
| M-14 | Update balance | Home → Edit (balance card) → enter value | Balance card animates to new value |

---

## Team

| Name | Role |
|---|---|
| **Salma** | Backend, financial logic, API design, deployment |
| **Fathima** | Frontend, UI/UX, WEWE interface |

---

*WEBANKI is a prototype built for the Shenzhen FinTech Competition. It uses simulated data — no real bank connections or transactions are made.*
