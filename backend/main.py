"""WEBANKI backend v2: login, earmarked budgeting, reports, reminders.
Money is stored as integer cents to avoid rounding bugs."""
import os, hmac, hashlib, secrets, sqlite3, calendar, datetime as dt
from typing import Literal, Optional
import jwt
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from pydantic import BaseModel, Field

# Vercel's serverless filesystem is read-only except for /tmp.
# Set WEBANKI_DB env var in the Vercel dashboard to a persistent store path,
# or leave it as /tmp/webanki.db for ephemeral (resets on cold start).
DB = os.environ.get("WEBANKI_DB", "/tmp/webanki.db")
SECRET = os.environ.get("WEBANKI_SECRET", "dev-secret-change-me")  # set a real one when deployed
app = FastAPI(title="WEBANKI API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
bearer = HTTPBearer()

def db():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

with db() as c:
    c.executescript("""
    CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, name TEXT, email TEXT UNIQUE, password_hash TEXT,
        balance INT, salary INT, weekly_limit INT, savings_pct INT);
    CREATE TABLE IF NOT EXISTS buckets(id INTEGER PRIMARY KEY, user_id INT, kind TEXT, name TEXT,
        amount_due INT, saved INT DEFAULT 0, due_date TEXT);
    CREATE TABLE IF NOT EXISTS transactions(id INTEGER PRIMARY KEY, user_id INT, amount INT,
        category TEXT, note TEXT, created_at TEXT);
    """)

# ---------- auth ----------
def hash_pw(pw, salt=None):
    salt = salt or secrets.token_hex(16)
    return f"{salt}${hashlib.pbkdf2_hmac('sha256', pw.encode(), salt.encode(), 200_000).hex()}"

def check_pw(pw, stored):
    return hmac.compare_digest(hash_pw(pw, stored.split("$")[0]), stored)

def make_token(uid):
    exp = dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=12)
    return jwt.encode({"sub": str(uid), "exp": exp}, SECRET, algorithm="HS256")

def current_uid(cred=Depends(bearer)):
    try:
        return int(jwt.decode(cred.credentials, SECRET, algorithms=["HS256"])["sub"])
    except Exception:
        raise HTTPException(401, "Invalid or expired token")

# ---------- models ----------
class RegisterIn(BaseModel):
    name: str
    email: str = Field(..., min_length=5)
    password: str = Field(..., min_length=8)
    balance: int = Field(0, ge=0, description="cents")
    salary: int = Field(..., gt=0, description="cents per month")
    weekly_limit: int = Field(0, ge=0, description="cents")
    savings_pct: int = Field(20, ge=0, le=100)

class LoginIn(BaseModel):
    email: str
    password: str

class BucketIn(BaseModel):
    kind: Literal["bills", "rent", "tuition", "savings"]
    name: str
    amount_due: int = Field(0, ge=0, description="cents (savings: goal amount)")
    due_date: Optional[str] = Field(None, description="YYYY-MM-DD; moves forward a month when paid")

class ExpenseIn(BaseModel):
    amount: int = Field(..., gt=0, description="cents")
    category: str
    note: str = ""
    round_up: bool = True

# ---------- helpers ----------
def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()

def add_month(date_str):
    d = dt.date.fromisoformat(date_str)
    y, m = d.year + (d.month == 12), d.month % 12 + 1
    return dt.date(y, m, min(d.day, calendar.monthrange(y, m)[1])).isoformat()

def get_user(c, uid):
    u = c.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
    if not u:
        raise HTTPException(404, "User not found")
    return u

def buckets_of(c, uid):
    return [dict(b) for b in c.execute("SELECT * FROM buckets WHERE user_id=?", (uid,))]

def week_spent(c, uid):
    monday = (dt.date.today() - dt.timedelta(days=dt.date.today().weekday())).isoformat()
    return c.execute("SELECT COALESCE(SUM(amount),0) s FROM transactions WHERE user_id=? AND category='weekly' "
                     "AND created_at>=?", (uid, monday)).fetchone()["s"]

def due_soon(buckets, days_ahead):
    out, today = [], dt.date.today()
    for b in sorted([x for x in buckets if x["due_date"] and x["kind"] != "savings"], key=lambda x: x["due_date"]):
        days = (dt.date.fromisoformat(b["due_date"]) - today).days
        short = b["amount_due"] - b["saved"]
        if days <= days_ahead and short > 0:
            out.append({"bucket_id": b["id"], "name": b["name"], "days_left": days, "still_needed": short})
    return out

def wewe_tip(buckets, safe, weekly_left):
    soon = due_soon(buckets, 7)
    if soon:
        s = soon[0]
        return f"{s['name']} is due in {s['days_left']} days and still needs {s['still_needed']/100:.2f}. Move it now?"
    if weekly_left is not None and weekly_left < 0:
        return "You went over your weekly limit. Want me to adjust next week?"
    return f"You can safely spend {safe/100:.2f} this month."

# ---------- auth routes ----------
@app.post("/auth/register")
def register(b: RegisterIn):
    try:
        with db() as c:
            cur = c.execute("INSERT INTO users(name,email,password_hash,balance,salary,weekly_limit,savings_pct) "
                            "VALUES(?,?,?,?,?,?,?)", (b.name, b.email.lower(), hash_pw(b.password), b.balance,
                                                      b.salary, b.weekly_limit, b.savings_pct))
            return {"token": make_token(cur.lastrowid)}
    except sqlite3.IntegrityError:
        raise HTTPException(409, "Email already registered")

@app.post("/auth/login")
def login(b: LoginIn):
    with db() as c:
        u = c.execute("SELECT * FROM users WHERE email=?", (b.email.lower(),)).fetchone()
    if not u or not check_pw(b.password, u["password_hash"]):
        raise HTTPException(401, "Wrong email or password")
    return {"token": make_token(u["id"])}

# ---------- app routes (all need a token) ----------
@app.post("/me/buckets")
def add_bucket(b: BucketIn, uid: int = Depends(current_uid)):
    with db() as c:
        cur = c.execute("INSERT INTO buckets(user_id,kind,name,amount_due,due_date) VALUES(?,?,?,?,?)",
                        (uid, b.kind, b.name, b.amount_due, b.due_date))
        return {"id": cur.lastrowid}

@app.post("/me/payday")
def payday(uid: int = Depends(current_uid)):
    """Add salary, then earmark money for rent -> bills -> tuition -> savings."""
    with db() as c:
        u = get_user(c, uid)
        c.execute("UPDATE users SET balance=balance+? WHERE id=?", (u["salary"], uid))
        available, plan = u["salary"], []
        for kind in ("rent", "bills", "tuition"):
            for b in c.execute("SELECT * FROM buckets WHERE user_id=? AND kind=?", (uid, kind)).fetchall():
                amt = min(max(b["amount_due"] - b["saved"], 0), available)
                c.execute("UPDATE buckets SET saved=saved+? WHERE id=?", (amt, b["id"]))
                available -= amt
                plan.append({"bucket": b["name"], "set_aside": amt})
        share = min(u["salary"] * u["savings_pct"] // 100, available)
        for b in c.execute("SELECT * FROM buckets WHERE user_id=? AND kind='savings' LIMIT 1", (uid,)):
            c.execute("UPDATE buckets SET saved=saved+? WHERE id=?", (share, b["id"]))
            plan.append({"bucket": b["name"], "set_aside": share})
        return {"salary_added": u["salary"], "plan": plan}

@app.post("/me/expenses")
def add_expense(e: ExpenseIn, uid: int = Depends(current_uid)):
    with db() as c:
        u = get_user(c, uid)
        if e.amount > u["balance"]:
            raise HTTPException(400, "Insufficient balance")
        c.execute("UPDATE users SET balance=balance-? WHERE id=?", (e.amount, uid))
        c.execute("INSERT INTO transactions(user_id,amount,category,note,created_at) VALUES(?,?,?,?,?)",
                  (uid, e.amount, e.category, e.note, now()))
        reserved = sum(b["saved"] for b in buckets_of(c, uid))
        free = u["balance"] - e.amount - reserved
        spare = (-e.amount) % 100 if e.round_up else 0
        if spare and free >= spare:  # only round up from truly free money
            c.execute("UPDATE buckets SET saved=saved+? WHERE user_id=? AND kind='savings'", (spare, uid))
        else:
            spare = 0
        warn = "This used money set aside for your commitments." if free < 0 else None
        return {"spent": e.amount, "round_up_saved": spare, "warning": warn}

@app.post("/me/buckets/{bid}/pay")
def pay_bucket(bid: int, uid: int = Depends(current_uid)):
    """Pay a bill/rent/tuition. Money leaves the balance; the due date moves forward one month."""
    with db() as c:
        u = get_user(c, uid)
        b = c.execute("SELECT * FROM buckets WHERE id=? AND user_id=?", (bid, uid)).fetchone()
        if not b or b["kind"] == "savings":
            raise HTTPException(404, "Payable bucket not found")
        if b["amount_due"] > u["balance"]:
            raise HTTPException(400, "Insufficient balance")
        nxt = add_month(b["due_date"]) if b["due_date"] else None
        c.execute("UPDATE users SET balance=balance-? WHERE id=?", (b["amount_due"], uid))
        c.execute("UPDATE buckets SET saved=0, due_date=? WHERE id=?", (nxt, bid))
        c.execute("INSERT INTO transactions(user_id,amount,category,note,created_at) VALUES(?,?,?,?,?)",
                  (uid, b["amount_due"], b["kind"], b["name"], now()))
        return {"paid": b["name"], "amount": b["amount_due"], "next_due": nxt}

@app.get("/me/dashboard")
def dashboard(uid: int = Depends(current_uid)):
    with db() as c:
        u, buckets, spent = get_user(c, uid), buckets_of(c, uid), week_spent(c, uid)
        safe = u["balance"] - sum(b["saved"] for b in buckets)
        left = (u["weekly_limit"] - spent) if u["weekly_limit"] else None
        return {"name": u["name"], "balance": u["balance"], "salary": u["salary"],
                "reserved": u["balance"] - safe, "safe_to_spend": safe,
                "weekly": {"limit": u["weekly_limit"], "spent": spent, "left": left},
                "buckets": buckets, "wewe_tip": wewe_tip(buckets, safe, left)}

@app.get("/me/afford")
def afford(amount: int, uid: int = Depends(current_uid)):
    """WEWE: can I afford this?"""
    with db() as c:
        u, buckets, spent = get_user(c, uid), buckets_of(c, uid), week_spent(c, uid)
        safe = u["balance"] - sum(b["saved"] for b in buckets)
        left = (u["weekly_limit"] - spent) if u["weekly_limit"] else None
        if amount > safe:
            return {"ok": False, "message": "That would dip into money set aside for your bills, rent or tuition."}
        if left is not None and amount > left:
            return {"ok": False, "message": "You can pay for it, but it goes over your weekly limit."}
        return {"ok": True, "message": "Yes, you can afford it without touching your commitments."}

@app.get("/me/reminders")
def reminders(uid: int = Depends(current_uid)):
    """Bills due within 3 days (or overdue) that are not fully set aside."""
    with db() as c:
        return {"reminders": due_soon(buckets_of(c, uid), 3)}

@app.get("/me/report")
def report(uid: int = Depends(current_uid)):
    """Spending this month by category."""
    with db() as c:
        since = dt.date.today().replace(day=1).isoformat()
        rows = c.execute("SELECT category, SUM(amount) t FROM transactions WHERE user_id=? AND created_at>=? "
                         "GROUP BY category", (uid, since)).fetchall()
        return {"since": since, "by_category": {r["category"]: r["t"] for r in rows},
                "total": sum(r["t"] for r in rows), "week_spent": week_spent(c, uid)}