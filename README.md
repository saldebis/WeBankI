# 💚 WEBANKI

**Your balance shows what you have. WEBANKI shows what you can safely spend.**

WEBANKI is an AI-assisted personal finance prototype built for the Shenzhen FinTech Competition. It sets money aside for rent, bills, tuition and savings *before* you spend it, then tells you how much is actually free, with help from **WEWE**, a friendly green robot assistant.

🔗 **[Live demo](https://frontend-lake-xi-76.vercel.app)** · 💻 **[GitHub](https://github.com/saldebis/WeBankI)** · 📊 **[Slides](https://drive.google.com/file/d/1VnlIfgagM38XqRZpJdzIg5WE7HckYYbh/view?usp=sharing)** · 🎥 **Demo video:** _coming soon_

> ⚠️ **Prototype notice:** WEBANKI uses simulated data, does not connect to real bank accounts, and never moves real money. Please don't enter real financial information.

---

## The idea: Safe-to-Spend

Most budgeting apps record what you've already spent. WEBANKI works the other way around: it earmarks money for commitments first, so a $2,000 balance doesn't look like $2,000 of free cash.

| | Amount |
|---|---:|
| Total balance | $2,000 |
| Rent reserved | −$700 |
| Upcoming bills | −$200 |
| Savings reserved | −$300 |
| **Safe to spend** | **$800** |

_Illustrative example. Real results depend on the user's recorded data and the app's rules._

Bills due within the next **14 days** are counted against Safe-to-Spend, so the number reflects what's coming, not just what's already committed.

## Meet WEWE

WEWE is the green robot assistant who answers everyday money questions:

- Can I afford this purchase?
- How much can I safely spend this week?
- How much should I set aside for upcoming bills?

> WEWE currently gives contextual tips and affordability answers. Free-form AI conversation is still in development.

## Features

- **Buckets and salary allocation:** split income into rent, bills, tuition, savings and more.
- **Safe-to-Spend:** available money after reserved funds and upcoming obligations.
- **Savings goals:** reserve money toward a target and track progress.
- **Weekly spending limit:** see how much of your limit remains as expenses are logged.
- **Round-up savings:** eligible expenses can contribute extra toward savings.
- **Bill reminders:** alerts for recorded bills due within 3 days.
- **Recurring bills:** marking a bill as paid advances its due date.
- **Monthly report:** spending broken down by category.
- **Accounts:** registration and login with PBKDF2-hashed passwords and JWT auth; each user's data is isolated.

## Who it's for

Students on tight budgets, employees allocating a salary, families planning household bills, freelancers with irregular income, and anyone saving toward a big purchase.

## Tech stack

| Layer | Technology |
|---|---|
| Backend | Python, FastAPI |
| Database | SQLite |
| Auth | JWT, PBKDF2 |
| Frontend | Web UI, deployed on Vercel |
| AI | WEWE assistant (conversational features in progress) |

**How it fits together:** the web frontend talks to an authenticated FastAPI backend, which handles budgets, buckets, expenses, savings allocation and affordability calculations against SQLite. Money is stored as **integer cents** to avoid floating-point rounding errors.

## Run the backend locally

**Requirements:** Python 3.10+ and pip.

```bash
git clone https://github.com/saldebis/WeBankI.git
cd WeBankI/backend
pip install -r requirements.txt
```

Set your environment variables:

```env
WEBANKI_SECRET=your_secret_key
WEBANKI_DB=webanki.db
```

Use a strong, private secret and never commit real secrets to GitHub.

Start the server:

```bash
python -m uvicorn main:app --reload
```

Then open the interactive API docs at <http://127.0.0.1:8000/docs>.

## API reference

All `/me/...` endpoints require a Bearer token.

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/auth/register` | Register an account |
| POST | `/auth/login` | Log in |
| GET | `/me/dashboard` | Get dashboard data |
| POST | `/me/buckets` | Create a budget bucket |
| POST | `/me/payday` | Allocate salary across buckets |
| POST | `/me/expenses` | Record an expense |
| POST | `/me/buckets/{id}/pay` | Mark a bucket's bill as paid |
| GET | `/me/afford?amount=` | Check whether you can afford an amount |
| GET | `/me/reminders` | Get bill reminders |
| GET | `/me/report` | Get the monthly spending report |

## Current limitations

- Financial data is simulated; there are no live bank connections.
- Free-form AI conversation with WEWE is still being improved.
- The current deployment may use temporary storage, so data can be lost when the environment resets.
- Security hardening and testing are needed before any production use.

## Roadmap

- Smarter WEWE: natural-language questions, conversational context, and explanations based on the user's own numbers
- Personalized insights from spending and savings data
- Persistent cloud database
- Long-term goal planning and better visualizations
- More testing and security hardening
- Possible integrations with external financial services, subject to security, privacy and regulatory requirements

## Team

| Name | Role |
|---|---|
| Salma | Backend development and financial logic |
|  Fathima | Frontend development |

## Disclaimer

WEBANKI is an educational, experimental prototype. It does not provide regulated financial advice, connect to real bank accounts, or execute real transactions. Results depend on the information entered.
