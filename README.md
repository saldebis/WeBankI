# 💚 WEBANKI: Your Money, Your Goals, Your Future

*Shenzhen FinTech Competition submission*

**Your balance shows what you have. WEBANKI shows what you can safely spend.**

🔗 [Live demo](https://frontend-lake-xi-76.vercel.app) · 🎥 [Demo video](https://drive.google.com/file/d/1PVrVcCOYVzBgbY7oTEPJ4SImcIxVh_Rk/view?usp=sharing) · 📊 [Slides](https://drive.google.com/file/d/1VnlIfgagM38XqRZpJdzIg5WE7HckYYbh/view?usp=sharing) · 💻 [GitHub](https://github.com/saldebis/WeBankI)

## The problem
A bank balance is misleading. Money for rent, bills and savings is already spoken for, yet it still looks spendable. Most budgeting apps only review spending after it has happened.

## Our solution
WEBANKI earmarks income into buckets (rent, bills, tuition, savings) **before** it is spent, then calculates a **Safe-to-Spend** amount. Bills due within 14 days are counted against it.

| Total balance | Rent | Upcoming bills | Savings | **Safe to spend** |
|---:|---:|---:|---:|---:|
| $2,000 | −$700 | −$200 | −$300 | **$800** |

*Illustrative example.*

**WEWE**, a friendly green robot assistant, helps users ask: *Can I afford this? How much can I spend this week?*

## Key features
- Salary allocation into buckets
- Safe-to-Spend calculation
- Savings goals and round-up savings
- Weekly spending limit
- Bill reminders (due within 3 days) and recurring bills
- Monthly spending report
- Secure accounts (PBKDF2 password hashing, JWT auth)

## Built with
Python · FastAPI · SQLite · JWT · Web frontend on Vercel. Money is stored as integer cents to avoid rounding errors.

## Honest scope
A working prototype with simulated data: no real bank connections or transactions. Free-form AI chat with WEWE is in development. Next steps: smarter WEWE, a persistent cloud database, personalized insights and security hardening.

## Team
**Salma:** backend and financial logic · **Fathima:** frontend
