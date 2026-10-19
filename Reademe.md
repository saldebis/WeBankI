# WEBANKI

## Deploy to Vercel

### One-time setup
1. Install the Vercel CLI: `npm i -g vercel`
2. Log in: `vercel login`

### Deploy
```bash
cd backend
vercel
```
On the first deploy Vercel will ask a few questions:
- **Set up and deploy?** → Yes
- **Which scope?** → your account
- **Link to existing project?** → No (create new)
- **Project name** → `webanki` (or anything you like)
- **Directory** → `.` (you are already inside `backend/`)
- **Override settings?** → No

After it finishes, Vercel prints your URL, e.g. `https://webanki-xyz.vercel.app`.

### Environment variables (set in the Vercel dashboard)
| Variable | Purpose | Example |
|---|---|---|
| `WEBANKI_SECRET` | JWT signing secret — **change this!** | `some-long-random-string` |
| `WEBANKI_DB` | SQLite path (optional — see note below) | `/tmp/webanki.db` |

> **SQLite on Vercel is ephemeral.** `/tmp` is writable but resets on every cold start, so registered users and data are lost between deploys/restarts. For a production-grade persistent store, swap SQLite for a hosted DB (e.g. Vercel Postgres, PlanetScale, or Turso) and update `main.py` accordingly.

### Subsequent deploys
```bash
cd backend
vercel --prod
```

---


Budgeting app with WEWE, a green robot that helps you plan your money.
Built for the Shenzhen FinTech Competition.

## Project structure
- `main.py`, `requirements.txt`, `test_api.py`: backend (FastAPI + SQLite)
- `frontend/`: the app screens (teammate adds this folder)
- `index.html`: small working example of calling the API (delete or replace)

## Run the backend
    pip install -r requirements.txt
    python -m uvicorn main:app --reload
Then open http://127.0.0.1:8000/docs to try every endpoint.

## API for the frontend
Base URL: `http://127.0.0.1:8000`. All money values are **integer cents** (1550 = $15.50).
Send the token as the header `Authorization: Bearer <token>` on every `/me/...` route.

| Route | Purpose |
|---|---|
| `POST /auth/register` | Create account, returns `{token}` |
| `POST /auth/login` | Log in, returns `{token}` |
| `GET /me/dashboard` | Balance, salary, safe_to_spend, buckets, weekly, wewe_tip |
| `POST /me/buckets` | Add rent / bills / tuition / savings bucket |
| `POST /me/payday` | Add salary and split it into buckets |
| `POST /me/expenses` | Add an expense (round-up goes to savings) |
| `POST /me/buckets/{id}/pay` | Pay a bill, rent or tuition |
| `GET /me/afford?amount=` | WEWE: can I afford this? |
| `GET /me/reminders` | Bills due within 3 days that are not fully funded |
| `GET /me/report` | This month's spending by category |

## Tests
    python test_api.py

## Team workflow
1. Never work directly on `main`. Make a branch: `git checkout -b my-feature`
2. Commit, then `git push -u origin my-feature` and open a Pull Request on GitHub.
3. Before starting work each day: `git pull`