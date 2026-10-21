# WEBANKI — Security Self-Assessment Report

**Project:** WEBANKI  
**Stack:** FastAPI + SQLite (backend), Vanilla JS SPA (frontend)  
**Deployment:** Vercel  
**Date:** July 2025

---

## Overall Rating: C+

**Adequate for a prototype / student project.** Core authentication is correctly implemented (PBKDF2 password hashing, JWT tokens, per-user data isolation). Several issues need to be addressed before this is suitable for real financial data or public users. The most critical items are the wildcard CORS policy, the fallback `SECRET` in source, and the use of `eval()` in the rule-based fallback.

---

## Finding Summary

| # | Finding | Area | Severity | Status |
|---|---|---|---|---|
| F-01 | Hardcoded fallback JWT secret in source | Backend | 🔴 HIGH | Open |
| F-02 | Wildcard CORS — all origins accepted | Backend | 🔴 HIGH | Open |
| F-03 | `eval()` used on user-supplied arithmetic | Backend | 🔴 HIGH | Open |
| F-04 | No HTTPS enforcement or HSTS header | Infra | 🟡 MEDIUM | Delegated to Vercel |
| F-05 | JWT stored in `sessionStorage` (XSS-accessible) | Frontend | 🟡 MEDIUM | Open |
| F-06 | No rate limiting on authentication endpoints | Backend | 🟡 MEDIUM | Open |
| F-07 | SQLite on ephemeral Vercel filesystem | Infra | 🟡 MEDIUM | By design (noted in code) |
| F-08 | No `Content-Security-Policy` header | Frontend | 🟡 MEDIUM | Open |
| F-09 | QR tokens never expire by time | Backend | 🔵 LOW | Open |
| F-10 | Integer arithmetic — no overflow guard on large cent values | Backend | 🔵 LOW | Open |
| F-11 | External CDN script (`qrcodejs`) loaded without SRI | Frontend | 🔵 LOW | Open |
| F-12 | Password hashing: PBKDF2-SHA256 200k iterations | Backend | ✅ PASS | Good |
| F-13 | Timing-safe password comparison (`hmac.compare_digest`) | Backend | ✅ PASS | Good |
| F-14 | Per-user data isolation — all queries scoped to `user_id` | Backend | ✅ PASS | Good |
| F-15 | WEWE rate limit (20 calls/user/hour) | Backend | ✅ PASS | Good |
| F-16 | HTML output escaped with `escapeHTML()` | Frontend | ✅ PASS | Good |
| F-17 | `.env` excluded from git via `.gitignore` | Infra | ✅ PASS | Good |

---

## High Severity

### F-01 — Hardcoded fallback JWT secret in source code

**Location:** `backend/main.py` line 17

**Detail:** `SECRET = os.environ.get("WEBANKI_SECRET", "dev-secret-change-me")` — if the environment variable is ever absent (e.g. a misconfigured Vercel deployment), every JWT ever issued can be forged by anyone who reads the source code on GitHub.

**Recommendation:** Replace the default with an exception:
```python
SECRET = os.environ.get("WEBANKI_SECRET")
if not SECRET:
    raise RuntimeError("WEBANKI_SECRET env var must be set")
```
Rotate the secret immediately if the app has ever run without the env var set.

---

### F-02 — Wildcard CORS policy (`allow_origins=["*"]`)

**Location:** `backend/main.py` line 19

**Detail:** Any website on the internet can make authenticated cross-origin requests to the API using a victim's browser credentials (CSRF-style attack). For a financial app this is a significant risk.

**Recommendation:** Restrict origins to the known Vercel frontend URL:
```python
allow_origins=["https://webanki.vercel.app"]
```
Maintain a separate list for local development via an environment variable.

---

### F-03 — `eval()` on user-supplied text in rule-based fallback

**Location:** `backend/main.py` ~line 593

**Detail:** The `_rule_based_reply` function calls `eval(compile(arith, ...))` on input derived from the user's chat message. Although `__builtins__` is emptied, using `eval()` on any user-supplied data is a dangerous pattern. A regex bypass or future code change could lead to remote code execution.

**Recommendation:** Replace `eval()` with a safe arithmetic parser (e.g. `ast.literal_eval` on numeric literals, or a dedicated expression parser). The regex guard is insufficient on its own.

---

## Medium Severity

### F-05 — JWT stored in `sessionStorage`

**Location:** `frontend/index.html`

**Detail:** Tokens in `sessionStorage` are accessible to any JavaScript running on the page. A single XSS gadget (e.g. via an injected third-party script) would steal the token immediately.

**Recommendation:** For production, consider HttpOnly cookies with the `SameSite=Strict` attribute so tokens are never reachable from JS. As a minimum, add a strong CSP header (see F-08).

---

### F-06 — No rate limiting on `/auth/login` or `/auth/register`

**Detail:** An attacker can make unlimited login attempts against any email address (credential stuffing / brute-force). The existing rate limiter only covers `/me/wewe/chat`.

**Recommendation:** Add a per-IP or per-email rate limiter (e.g. `slowapi` for FastAPI, or Vercel Edge middleware). Alternatively, add a short `time.sleep(0.3)` on failed logins as a basic deterrent.

---

### F-07 — SQLite on ephemeral Vercel filesystem

**Detail:** The database lives in `/tmp/webanki.db` on Vercel serverless functions. Every cold start wipes all user data. This is already acknowledged in code comments but means the app cannot be used for real money.

**Recommendation:** Migrate to a persistent database (Supabase Postgres, PlanetScale, Turso, etc.) before any production use.

---

### F-08 — No `Content-Security-Policy` header

**Detail:** Without a CSP, any injected or third-party script runs with full page privileges, making XSS exploitation trivial. The `qrcodejs` CDN dependency amplifies this risk.

**Recommendation:** Add a `vercel.json` with appropriate headers:
```
default-src 'self';
script-src 'self' cdnjs.cloudflare.com;
style-src 'self' fonts.googleapis.com 'unsafe-inline'
```

---

## Low Severity

### F-09 — QR tokens never expire by time

**Detail:** A generated QR token remains valid indefinitely until used. If a token is leaked (e.g. screenshot shared) it can be paid by anyone at any point in the future.

**Recommendation:** Add an `expires_at` column to `qr_tokens` and reject tokens older than 15–30 minutes in `qr_pay`.

---

### F-10 — No integer overflow guard on balance/amount fields

**Detail:** Amounts are stored as 32-bit SQLite integers (max ~$21M). A user could register with a very large salary value and trigger arithmetic issues.

**Recommendation:** Add `le=2_000_000_000` (or similar) to Pydantic `Field` validators on all cent-valued fields.

---

### F-11 — External CDN script loaded without Subresource Integrity (SRI)

**Location:** `frontend/index.html` line 143 — `cdnjs.cloudflare.com/…/qrcode.min.js`

**Detail:** If the CDN is compromised or the file is replaced, the malicious script runs in full page context and can steal the JWT token.

**Recommendation:** Add `integrity="sha384-…"` and `crossorigin="anonymous"` attributes. Generate the hash with:
```bash
openssl dgst -sha384 -binary qrcode.min.js | openssl base64 -A
```

---

## What Is Done Well

| # | Finding | Notes |
|---|---|---|
| F-12 | **Password hashing** | PBKDF2-SHA256 with 200,000 iterations and a per-user random salt. Correct and modern. |
| F-13 | **Timing-safe comparison** | `hmac.compare_digest` prevents timing side-channel attacks on login. |
| F-14 | **Per-user data isolation** | Every database query is scoped to the authenticated `user_id`. Automated tests verify cross-user access is rejected. |
| F-15 | **JWT expiry** | Tokens expire after 12 hours; expiry is checked on every request. |
| F-16 | **WEWE rate limiting** | 20 calls/user/hour prevents OpenAI API abuse. |
| F-17 | **HTML output escaping** | `escapeHTML()` is applied to all user-controlled data before it is inserted into the DOM, preventing stored XSS. |
| — | **Secrets excluded from git** | `.env*` is in `.gitignore`; no credentials found in committed files. |
| — | **QR self-pay prevention** | `qr_pay` rejects tokens owned by the payer. |
| — | **Parameterised SQL** | All database calls use `sqlite3` parameterised statements (`?`), no string concatenation. SQL injection risk is low. |
| — | **Pydantic input validation** | Request bodies are validated with type constraints and field-level minimums/maximums before any business logic runs. |

---

## Priority Action Plan

| Priority | Action | Effort |
|---|---|---|
| 1 — Immediate | Remove hardcoded default JWT secret; raise exception if env var missing (F-01) | 1 line |
| 2 — Before sharing publicly | Replace `eval()` with a safe arithmetic evaluator (F-03) | ~10 lines |
| 3 — Before sharing publicly | Restrict CORS to `https://webanki.vercel.app` (F-02) | 1 line |
| 4 — Before real users | Add login rate limiting (F-06) | ~15 lines |
| 5 — Before real users | Add CSP header via `vercel.json` (F-08) | ~10 lines |
| 6 — Before real users | Add QR token expiry (F-09) | ~5 lines |
| 7 — Before real users | Add SRI to the CDN script tag (F-11) | 1 attribute |
| 8 — Long term | Migrate from SQLite/tmp to a persistent database (F-07) | Medium refactor |
