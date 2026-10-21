import os, tempfile, datetime as dt
os.environ["WEBANKI_DB"] = tempfile.mktemp(suffix=".db")
from fastapi.testclient import TestClient
from main import app
c = TestClient(app)
soon = (dt.date.today() + dt.timedelta(days=2)).isoformat()

def reg(email):
    r = c.post("/auth/register", json={"name": "T", "email": email, "password": "password123",
                                        "salary": 300000, "weekly_limit": 20000})
    assert r.status_code == 200, f"register failed: {r.text}"
    return {"Authorization": "Bearer " + r.json()["token"]}

A, B = reg("a@x.com"), reg("b@x.com")

# ── auth ────────────────────────────────────────────────────────────────────
assert c.post("/auth/register", json={"name": "T", "email": "a@x.com", "password": "password123", "salary": 1}).status_code == 409
assert c.post("/auth/login", json={"email": "a@x.com", "password": "wrongpass1"}).status_code == 401
assert c.post("/auth/login", json={"email": "a@x.com", "password": "password123"}).status_code == 200
assert c.get("/me/dashboard").status_code in (401, 403)          # no token

# ── bucket CRUD ─────────────────────────────────────────────────────────────
rent_id = c.post("/me/buckets", headers=A, json={"kind": "rent", "name": "Rent", "amount_due": 120000, "due_date": soon}).json()["id"]
c.post("/me/buckets", headers=A, json={"kind": "bills", "name": "Bills", "amount_due": 30000})
c.post("/me/buckets", headers=A, json={"kind": "savings", "name": "Laptop", "amount_due": 500000})

# list buckets
buckets_r = c.get("/me/buckets", headers=A)
assert buckets_r.status_code == 200
assert len(buckets_r.json()["buckets"]) == 3, f"expected 3 buckets, got: {buckets_r.json()}"

# update a bucket via PATCH
patch_r = c.patch(f"/me/buckets/{rent_id}", headers=A, json={"amount_due": 150000})
assert patch_r.status_code == 200, f"PATCH bucket failed: {patch_r.text}"
assert patch_r.json()["amount_due"] == 150000

# B cannot update A's bucket
assert c.patch(f"/me/buckets/{rent_id}", headers=B, json={"amount_due": 1}).status_code == 404

# ── upsert budget (the main fix) ────────────────────────────────────────────
# 1. Upsert bills (no existing bills bucket for user A yet) → creates
upsert_bills = c.put("/me/budget/bills", headers=A, json={"kind": "bills", "amount_due": 50000, "due_date": soon})
assert upsert_bills.status_code == 200, f"upsert bills failed: {upsert_bills.text}"
data = upsert_bills.json()
assert data["amount_due"] == 50000

# 2. Upsert bills again → updates the existing bucket (NOT a new insert)
upsert_bills2 = c.put("/me/budget/bills", headers=A, json={"kind": "bills", "amount_due": 75000, "due_date": soon})
assert upsert_bills2.status_code == 200
data2 = upsert_bills2.json()
assert data2["amount_due"] == 75000
assert data2.get("created") is False, "second upsert should update, not create"

# 3. Verify dashboard reflects updated value (not the old one or zero)
dash = c.get("/me/dashboard", headers=A).json()
bills_buckets = [b for b in dash["buckets"] if b["kind"] == "bills"]
bills_total = sum(b["amount_due"] for b in bills_buckets)
# The initial 30000 bucket + updated 75000 (replaced from 50000) — but we only have
# the one bills bucket created via upsert (the earlier 30000 was separate via /me/buckets)
# We just verify the upserted bucket has the right value
upserted = next((b for b in bills_buckets if b["amount_due"] == 75000), None)
assert upserted is not None, f"Expected a bills bucket with amount_due=75000 in dashboard, got: {bills_buckets}"

# 4. Upsert rent → updates the existing rent bucket (rent_id created above, now 150000)
upsert_rent = c.put("/me/budget/rent", headers=A, json={"kind": "rent", "amount_due": 200000, "due_date": soon})
assert upsert_rent.status_code == 200
assert upsert_rent.json()["amount_due"] == 200000
assert upsert_rent.json().get("created") is False

# 5. Upsert tuition (no tuition bucket yet for user A) → creates
upsert_tuition = c.put("/me/budget/tuition", headers=A, json={"kind": "tuition", "amount_due": 300000})
assert upsert_tuition.status_code == 200
assert upsert_tuition.json()["amount_due"] == 300000
assert upsert_tuition.json().get("created") is True

# 6. Upsert weekly (Daily Life) → sets the user's weekly_limit
upsert_weekly = c.put("/me/budget/weekly", headers=A, json={"kind": "weekly", "amount_due": 50000})
assert upsert_weekly.status_code == 200
assert upsert_weekly.json()["amount_due"] == 50000

# Verify weekly_limit is reflected in the dashboard
dash2 = c.get("/me/dashboard", headers=A).json()
assert dash2["weekly"]["limit"] == 50000, f"weekly limit not updated: {dash2['weekly']}"

# 7. One user's data is not accessible or overwritten by another user's upsert
upsert_bills_B = c.put("/me/budget/bills", headers=B, json={"kind": "bills", "amount_due": 999999})
assert upsert_bills_B.status_code == 200
dash_B = c.get("/me/dashboard", headers=B).json()
dash_A_after = c.get("/me/dashboard", headers=A).json()
bills_A_after = [b for b in dash_A_after["buckets"] if b["kind"] == "bills"]
# A's bills bucket should still have 75000, not 999999
upserted_A = next((b for b in bills_A_after if b["amount_due"] == 75000), None)
assert upserted_A is not None, f"A's bills bucket was overwritten by B! A's bills: {bills_A_after}"

# 8. Invalid kind returns 400
bad = c.put("/me/budget/invalid_kind", headers=A, json={"kind": "invalid_kind", "amount_due": 100})
assert bad.status_code == 422 or bad.status_code == 400, f"Expected 400/422 for invalid kind, got: {bad.status_code}"

# ── existing workflow tests ──────────────────────────────────────────────────
print(c.post("/me/payday", headers=A).json())
c.post("/me/expenses", headers=A, json={"amount": 1550, "category": "weekly", "note": "lunch"})
d = c.get("/me/dashboard", headers=A).json()
print({k: d[k] for k in ("balance", "reserved", "safe_to_spend", "wewe_tip")})
print(c.get("/me/afford", headers=A, params={"amount": 10000}).json())
print(c.get("/me/report", headers=A).json())
print(c.get("/me/reminders", headers=A).json())
c.post("/me/buckets", headers=A, json={"kind": "bills", "name": "Phone", "amount_due": 999999, "due_date": soon})
rem = c.get("/me/reminders", headers=A).json()["reminders"]
assert rem and rem[0]["name"] == "Phone", rem
print("pay:", c.post(f"/me/buckets/{rent_id}/pay", headers=A).json())
assert c.post(f"/me/buckets/{rent_id}/pay", headers=B).status_code == 404   # B cannot touch A's data
assert c.get("/me/dashboard", headers=B).json()["balance"] == 0

print("all checks passed")
