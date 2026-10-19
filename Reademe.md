# WEBANKI

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