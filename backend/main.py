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
# Use /tmp on Vercel (Linux); fall back to a local file on Windows dev machines
_default_db = "/tmp/webanki.db" if os.name != "nt" else os.path.join(os.path.dirname(__file__), "webanki.db")
DB = os.environ.get("WEBANKI_DB", _default_db)
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
    CREATE TABLE IF NOT EXISTS splits(id INTEGER PRIMARY KEY, owner_id INT, payer_id INT,
        amount INT, note TEXT, settled INT DEFAULT 0, created_at TEXT);
    CREATE TABLE IF NOT EXISTS qr_tokens(id INTEGER PRIMARY KEY, token TEXT UNIQUE, user_id INT,
        amount INT, note TEXT, used INT DEFAULT 0, created_at TEXT);
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
    return c.execute("SELECT COALESCE(SUM(amount),0) s FROM transactions WHERE user_id=? "
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

# ---------- send ----------
class SendIn(BaseModel):
    to_email: str
    amount: int = Field(..., gt=0, description="cents")
    note: str = ""

@app.post("/me/send")
def send_money(b: SendIn, uid: int = Depends(current_uid)):
    """Transfer money to another registered user."""
    with db() as c:
        sender = get_user(c, uid)
        recipient = c.execute("SELECT * FROM users WHERE email=?", (b.to_email.lower(),)).fetchone()
        if not recipient:
            raise HTTPException(404, "Recipient not found")
        if recipient["id"] == uid:
            raise HTTPException(400, "Cannot send money to yourself")
        if b.amount > sender["balance"]:
            raise HTTPException(400, "Insufficient balance")
        c.execute("UPDATE users SET balance=balance-? WHERE id=?", (b.amount, uid))
        c.execute("UPDATE users SET balance=balance+? WHERE id=?", (b.amount, recipient["id"]))
        c.execute("INSERT INTO transactions(user_id,amount,category,note,created_at) VALUES(?,?,?,?,?)",
                  (uid, b.amount, "send", f"To {recipient['name']}: {b.note}", now()))
        c.execute("INSERT INTO transactions(user_id,amount,category,note,created_at) VALUES(?,?,?,?,?)",
                  (recipient["id"], b.amount, "receive", f"From {sender['name']}: {b.note}", now()))
    return {"sent": b.amount, "to": recipient["name"], "to_email": b.to_email.lower()}

# ---------- qr ----------
@app.post("/me/qr/generate")
def qr_generate(amount: int, note: str = "", uid: int = Depends(current_uid)):
    """Generate a one-time QR token for receiving a payment."""
    token = secrets.token_urlsafe(24)
    with db() as c:
        c.execute("INSERT INTO qr_tokens(token,user_id,amount,note,created_at) VALUES(?,?,?,?,?)",
                  (token, uid, amount, note, now()))
    return {"token": token, "amount": amount, "note": note}

@app.post("/me/qr/pay")
def qr_pay(token: str, uid: int = Depends(current_uid)):
    """Pay a QR token — deducts from the scanner's balance, credits the token owner."""
    with db() as c:
        row = c.execute("SELECT * FROM qr_tokens WHERE token=?", (token,)).fetchone()
        if not row:
            raise HTTPException(404, "QR code not found")
        if row["used"]:
            raise HTTPException(400, "QR code already used")
        if row["user_id"] == uid:
            raise HTTPException(400, "Cannot pay your own QR code")
        payer = get_user(c, uid)
        if row["amount"] > payer["balance"]:
            raise HTTPException(400, "Insufficient balance")
        c.execute("UPDATE qr_tokens SET used=1 WHERE token=?", (token,))
        c.execute("UPDATE users SET balance=balance-? WHERE id=?", (row["amount"], uid))
        c.execute("UPDATE users SET balance=balance+? WHERE id=?", (row["amount"], row["user_id"]))
        owner = get_user(c, row["user_id"])
        c.execute("INSERT INTO transactions(user_id,amount,category,note,created_at) VALUES(?,?,?,?,?)",
                  (uid, row["amount"], "qr_pay", f"QR pay to {owner['name']}: {row['note']}", now()))
        c.execute("INSERT INTO transactions(user_id,amount,category,note,created_at) VALUES(?,?,?,?,?)",
                  (row["user_id"], row["amount"], "qr_receive", f"QR from {payer['name']}: {row['note']}", now()))
    return {"paid": row["amount"], "to": owner["name"], "note": row["note"]}

# ---------- split bill ----------
class SplitIn(BaseModel):
    amount: int = Field(..., gt=0, description="total cents to split")
    participants: list = Field(..., description="list of emails to split with")
    note: str = ""

@app.post("/me/split")
def create_split(b: SplitIn, uid: int = Depends(current_uid)):
    """Split a bill equally between yourself and a list of other users."""
    if not b.participants:
        raise HTTPException(400, "Provide at least one participant email")
    with db() as c:
        owner = get_user(c, uid)
        payers = []
        for email in b.participants:
            u = c.execute("SELECT * FROM users WHERE email=?", (email.lower(),)).fetchone()
            if not u:
                raise HTTPException(404, f"User not found: {email}")
            if u["id"] == uid:
                raise HTTPException(400, "Don't include yourself in participants")
            payers.append(u)
        share = b.amount // (len(payers) + 1)  # your share + each participant's share
        ids = []
        for p in payers:
            cur = c.execute(
                "INSERT INTO splits(owner_id,payer_id,amount,note,created_at) VALUES(?,?,?,?,?)",
                (uid, p["id"], share, b.note, now()))
            ids.append(cur.lastrowid)
    return {"total": b.amount, "share_each": share, "splits_created": ids,
            "participants": [p["name"] for p in payers]}

@app.get("/me/splits")
def list_splits(uid: int = Depends(current_uid)):
    """List splits you are owed (owner) and splits you owe (payer)."""
    with db() as c:
        owed = [dict(r) for r in c.execute(
            "SELECT s.*,u.name payer_name,u.email payer_email FROM splits s JOIN users u ON u.id=s.payer_id "
            "WHERE s.owner_id=? AND s.settled=0", (uid,))]
        owe = [dict(r) for r in c.execute(
            "SELECT s.*,u.name owner_name,u.email owner_email FROM splits s JOIN users u ON u.id=s.owner_id "
            "WHERE s.payer_id=? AND s.settled=0", (uid,))]
    return {"owed_to_you": owed, "you_owe": owe}

@app.post("/me/splits/{sid}/settle")
def settle_split(sid: int, uid: int = Depends(current_uid)):
    """Payer settles a split — money moves from payer to owner."""
    with db() as c:
        row = c.execute("SELECT * FROM splits WHERE id=?", (sid,)).fetchone()
        if not row:
            raise HTTPException(404, "Split not found")
        if row["payer_id"] != uid:
            raise HTTPException(403, "Only the payer can settle this split")
        if row["settled"]:
            raise HTTPException(400, "Already settled")
        payer = get_user(c, uid)
        if row["amount"] > payer["balance"]:
            raise HTTPException(400, "Insufficient balance")
        c.execute("UPDATE splits SET settled=1 WHERE id=?", (sid,))
        c.execute("UPDATE users SET balance=balance-? WHERE id=?", (row["amount"], uid))
        c.execute("UPDATE users SET balance=balance+? WHERE id=?", (row["amount"], row["owner_id"]))
        owner = get_user(c, row["owner_id"])
        c.execute("INSERT INTO transactions(user_id,amount,category,note,created_at) VALUES(?,?,?,?,?)",
                  (uid, row["amount"], "split_pay", f"Split settled to {owner['name']}: {row['note']}", now()))
        c.execute("INSERT INTO transactions(user_id,amount,category,note,created_at) VALUES(?,?,?,?,?)",
                  (row["owner_id"], row["amount"], "split_receive", f"Split from {payer['name']}: {row['note']}", now()))
    return {"settled": row["amount"], "to": owner["name"]}

# ---------- new routes ----------
class WeeklyLimitIn(BaseModel):
    weekly_limit: int = Field(..., ge=0, description="cents")

@app.patch("/me/weekly-limit")
def set_weekly_limit(b: WeeklyLimitIn, uid: int = Depends(current_uid)):
    """Update the user's weekly spending limit (cents)."""
    with db() as c:
        c.execute("UPDATE users SET weekly_limit=? WHERE id=?", (b.weekly_limit, uid))
    return {"weekly_limit": b.weekly_limit}

class BalanceIn(BaseModel):
    balance: int = Field(..., ge=0, description="new balance in cents")

@app.patch("/me/balance")
def update_balance(b: BalanceIn, uid: int = Depends(current_uid)):
    """Directly set the user's balance (e.g. after a top-up or correction)."""
    with db() as c:
        c.execute("UPDATE users SET balance=? WHERE id=?", (b.balance, uid))
    return {"balance": b.balance}

@app.get("/me/analyse-bills")
def analyse_bills(uid: int = Depends(current_uid)):
    """For every bill/rent/tuition bucket: what is due, what is funded, what is still needed."""
    with db() as c:
        u = get_user(c, uid)
        buckets = buckets_of(c, uid)
        safe = u["balance"] - sum(b["saved"] for b in buckets)
        due14 = due_soon(buckets, 14)
        result = []
        for b in [x for x in buckets if x["kind"] != "savings"]:
            still = max(b["amount_due"] - b["saved"], 0)
            result.append({
                "id": b["id"], "name": b["name"], "kind": b["kind"],
                "amount_due": b["amount_due"], "saved": b["saved"],
                "still_needed": still, "due_date": b["due_date"],
                "funded": still == 0,
                "days_left": (dt.date.fromisoformat(b["due_date"]) - dt.date.today()).days if b["due_date"] else None,
            })
        total_still_needed = sum(r["still_needed"] for r in result)
        return {
            "bills": result,
            "total_still_needed": total_still_needed,
            "safe_to_spend": safe,
            "can_cover_all": safe >= total_still_needed,
        }

class PlanSavingsIn(BaseModel):
    goal_bucket_id: int
    months: int = Field(..., gt=0)

@app.post("/me/plan-savings")
def plan_savings(b: PlanSavingsIn, uid: int = Depends(current_uid)):
    """How much per month to reach a savings goal, and whether it fits in safe_to_spend."""
    with db() as c:
        u = get_user(c, uid)
        bucket = c.execute("SELECT * FROM buckets WHERE id=? AND user_id=? AND kind='savings'",
                           (b.goal_bucket_id, uid)).fetchone()
        if not bucket:
            raise HTTPException(404, "Savings bucket not found")
        buckets = buckets_of(c, uid)
        safe = u["balance"] - sum(bk["saved"] for bk in buckets)
        remaining = max(bucket["amount_due"] - bucket["saved"], 0)
        monthly = (remaining + b.months - 1) // b.months  # ceiling integer division (cents)
        return {
            "goal": bucket["name"], "goal_amount": bucket["amount_due"],
            "already_saved": bucket["saved"], "remaining": remaining,
            "months": b.months, "monthly_needed": monthly,
            "fits_in_safe_to_spend": monthly <= safe,
        }

# ---------- WEWE LLM chat ----------
import collections, time as _time

# Simple in-memory rate limiter: max 20 calls per user per hour
_rate: dict[int, collections.deque] = {}
_RATE_MAX = 20
_RATE_WINDOW = 3600  # seconds

def _check_rate(uid: int):
    now_ts = _time.monotonic()
    q = _rate.setdefault(uid, collections.deque())
    while q and now_ts - q[0] > _RATE_WINDOW:
        q.popleft()
    if len(q) >= _RATE_MAX:
        raise HTTPException(429, "Rate limit: max 20 WEWE messages per hour")
    q.append(now_ts)

def _financial_snapshot(uid: int) -> str:
    """Build a dollar-formatted snapshot for the LLM. Never includes credentials."""
    with db() as c:
        u = get_user(c, uid)
        buckets = buckets_of(c, uid)
        spent = week_spent(c, uid)
        safe = u["balance"] - sum(b["saved"] for b in buckets)
        weekly_left = (u["weekly_limit"] - spent) if u["weekly_limit"] else None
        since = dt.date.today().replace(day=1).isoformat()
        rows = c.execute("SELECT category, SUM(amount) t FROM transactions WHERE user_id=? AND created_at>=? "
                         "GROUP BY category", (uid, since)).fetchall()
        reminders = due_soon(buckets, 14)

    lines = [
        f"User: {u['name']}",
        f"Balance: ${u['balance']/100:.2f}",
        f"Monthly salary: ${u['salary']/100:.2f}",
        f"Safe to spend (balance minus reserved): ${safe/100:.2f}",
        f"Weekly spending limit: {'${:.2f}'.format(u['weekly_limit']/100) if u['weekly_limit'] else 'not set'}",
        f"Spent this week: ${spent/100:.2f}",
        f"Weekly budget left: {'${:.2f}'.format(weekly_left/100) if weekly_left is not None else 'no limit set'}",
    ]
    if buckets:
        lines.append("Buckets:")
        for b in buckets:
            still = max(b["amount_due"] - b["saved"], 0)
            lines.append(f"  [{b['kind']}] {b['name']}: goal ${b['amount_due']/100:.2f}, saved ${b['saved']/100:.2f}, still needed ${still/100:.2f}"
                         + (f", due {b['due_date']}" if b["due_date"] else ""))
    if reminders:
        lines.append("Upcoming bills (due within 14 days, not fully funded):")
        for r in reminders:
            lines.append(f"  {r['name']}: ${r['still_needed']/100:.2f} still needed, due in {r['days_left']} days")
    if rows:
        lines.append("This month's spending by category:")
        for row in rows:
            lines.append(f"  {row['category']}: ${row['t']/100:.2f}")
    return "\n".join(lines)

_SYSTEM_PROMPT = """You are WEWE, a friendly green robot money assistant for the WEBANKI app.

Rules:
- You have access to the user's real financial snapshot. Use it to answer financial questions accurately. Never invent numbers.
- For arithmetic (e.g. "888-99", "what is 4400 minus 500"), compute the result and show it clearly.
- For savings timeline questions (e.g. "how many months to save for X?"):
    1. If the goal amount and monthly savings are known from the snapshot or conversation, calculate: months = ceil((goal - already_saved) / monthly_savings).
    2. If monthly savings capacity is unknown, ask the user for it. Do NOT assume it equals the salary.
    3. Use numbers from the snapshot or the conversation — never invent figures.
- For affordability questions, use the safe_to_spend figure from the snapshot.
- For ambiguous short inputs (e.g. a single letter), ask the user to clarify politely.
- Maintain context from the conversation history. If the user says "what if I save $1,500 instead?" refer back to the prior goal.
- Keep answers concise (under 120 words). If a calculation requires more steps, show the working briefly.
- Answer in the user's language (English or Arabic).
- You may answer brief general conversation, then guide back to budgeting.
- This is a simulated app. Never claim to move real money or give professional financial advice.
- For action requests (add expense, send money, set limit), tell the user to use the relevant button in the app — you cannot perform actions yourself."""

def _rule_based_reply(uid: int, text: str) -> str:
    """Fallback when LLM is unavailable. Returns a relevant answer based on the query."""
    import re as _re
    q = text.lower().strip()

    # Arithmetic: handle expressions like "4400-500", "8000 minus 99", "what is 120+30"
    arith = _re.sub(r'\b(plus|add)\b', '+', _re.sub(r'\b(minus|subtract)\b', '-',
             _re.sub(r'\b(times|multiplied by)\b', '*', _re.sub(r'\b(divided by)\b', '/', q))))
    m = _re.fullmatch(r'\s*[\d\s\+\-\*\/\.\(\)]+\s*', arith)
    if m:
        try:
            result = eval(compile(arith.strip(), '<string>', 'eval'),  # noqa: S307
                          {"__builtins__": {}}, {})
            return f"{arith.strip()} = {result:g}"
        except Exception:
            pass

    # Too short
    if len(q) <= 2:
        return "I didn't catch that 😊 Could you tell me more? For example: \"Can I afford $50?\" or \"Show my bills\"."

    with db() as c:
        u = get_user(c, uid)
        buckets = buckets_of(c, uid)
        spent = week_spent(c, uid)
        safe = u["balance"] - sum(b["saved"] for b in buckets)
        weekly_left = (u["weekly_limit"] - spent) if u["weekly_limit"] else None

    if "afford" in q or "buy" in q or "can i" in q:
        m2 = _re.search(r"(\d+(?:\.\d{1,2})?)", q)
        if m2:
            amt = round(float(m2.group(1)) * 100)
            if amt > safe:
                return f"That would dip into your reserved money. Your safe-to-spend is ${safe/100:.2f}."
            if weekly_left is not None and amt > weekly_left:
                return f"You can pay for it, but it goes over your weekly limit. You have ${weekly_left/100:.2f} left."
            return f"Yes, you can afford it! Your safe-to-spend is ${safe/100:.2f}."
        return f"Tell me the price and I'll check! Your safe-to-spend is ${safe/100:.2f}."
    if "bill" in q or "remind" in q:
        soon = due_soon(buckets, 14)
        if soon:
            s = soon[0]
            return f"{s['name']} is due in {s['days_left']} days and still needs ${s['still_needed']/100:.2f}."
        return "No unfunded bills due soon. You're all set!"
    if "saving" in q:
        sv = next((b for b in buckets if b["kind"] == "savings"), None)
        if sv:
            return f"You've saved ${sv['saved']/100:.2f} of ${sv['amount_due']/100:.2f} for {sv['name']}. Keep going!"
        return "You have no savings goal set yet."
    if "limit" in q or "weekly" in q:
        if u["weekly_limit"] and weekly_left is not None:
            return f"Your weekly limit is ${u['weekly_limit']/100:.2f} and you have ${weekly_left/100:.2f} left."
        return "You have no weekly limit set yet."
    tip = wewe_tip(buckets, safe, weekly_left)
    return f"{tip} Ask me anything about your money!"

class ChatIn(BaseModel):
    message: str
    history: Optional[list] = Field(default_factory=list)

@app.post("/me/wewe/chat")
def wewe_chat(b: ChatIn, uid: int = Depends(current_uid)):
    """OpenAI-powered WEWE chat. Falls back to rule-based reply if API key is not set."""
    _check_rate(uid)
    snapshot = _financial_snapshot(uid)

    # Read the standard OpenAI env var; also accept the legacy LLM_API_KEY for backwards compat
    api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("LLM_API_KEY", "")
    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

    if not api_key:
        return {"reply": _rule_based_reply(uid, b.message), "source": "fallback"}

    # Build conversation turns (history + current message), excluding system
    turns = []
    for h in (b.history or []):
        if isinstance(h, dict) and h.get("role") in ("user", "assistant"):
            turns.append({"role": h["role"], "content": str(h.get("content", ""))})
    turns.append({"role": "user", "content": b.message})

    # Cap history to last 20 turns to avoid hitting token limits
    if len(turns) > 21:
        turns = turns[-21:]

    system_content = _SYSTEM_PROMPT + "\n\nCurrent financial snapshot (today's live data):\n" + snapshot

    messages = [{"role": "system", "content": system_content}] + turns

    try:
        import urllib.request, json as _json, urllib.error as _ue
        payload = _json.dumps({
            "model": model,
            "messages": messages,
            "max_tokens": 400,
            "temperature": 0.4,
        }).encode()
        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = _json.loads(resp.read())
        reply = data["choices"][0]["message"]["content"].strip()
        return {"reply": reply, "source": "llm"}
    except _ue.HTTPError as e:
        err_detail = ""
        try:
            err_detail = _json.loads(e.read()).get("error", {}).get("message", "")
        except Exception:
            pass
        # Surface a user-friendly message without leaking API internals
        if e.code == 401:
            return {"reply": _rule_based_reply(uid, b.message), "source": "fallback"}
        if e.code == 429:
            return {"reply": "I'm getting a lot of questions right now — please wait a moment and try again.", "source": "error"}
        if err_detail:
            return {"reply": _rule_based_reply(uid, b.message), "source": "fallback"}
        return {"reply": _rule_based_reply(uid, b.message), "source": "fallback"}
    except Exception:
        return {"reply": _rule_based_reply(uid, b.message), "source": "fallback"}
