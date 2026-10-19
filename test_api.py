import os, tempfile, datetime as dt
os.environ["WEBANKI_DB"] = tempfile.mktemp(suffix=".db")
from fastapi.testclient import TestClient
from main import app
c = TestClient(app)
soon = (dt.date.today() + dt.timedelta(days=2)).isoformat()

def reg(email):
    r = c.post("/auth/register", json={"name": "T", "email": email, "password": "password123",
                                        "salary": 300000, "weekly_limit": 20000})
    return {"Authorization": "Bearer " + r.json()["token"]}

A, B = reg("a@x.com"), reg("b@x.com")
assert c.post("/auth/register", json={"name": "T", "email": "a@x.com", "password": "password123", "salary": 1}).status_code == 409
assert c.post("/auth/login", json={"email": "a@x.com", "password": "wrongpass1"}).status_code == 401
assert c.post("/auth/login", json={"email": "a@x.com", "password": "password123"}).status_code == 200
assert c.get("/me/dashboard").status_code in (401, 403)          # no token

rent = c.post("/me/buckets", headers=A, json={"kind": "rent", "name": "Rent", "amount_due": 120000, "due_date": soon}).json()["id"]
c.post("/me/buckets", headers=A, json={"kind": "bills", "name": "Bills", "amount_due": 30000})
c.post("/me/buckets", headers=A, json={"kind": "savings", "name": "Laptop", "amount_due": 500000})
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
print("pay:", c.post(f"/me/buckets/{rent}/pay", headers=A).json())
assert c.post(f"/me/buckets/{rent}/pay", headers=B).status_code == 404   # B cannot touch A's data
assert c.get("/me/dashboard", headers=B).json()["balance"] == 0
print("all checks passed")