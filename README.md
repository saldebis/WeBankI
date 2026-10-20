# 💚 WEBANKI — Your Money, Your Goals, Your Future

### Your balance tells you what you have. WEBANKI helps you understand what you can safely spend.

WEBANKI is an AI-powered personal finance platform designed to help people manage their money, make informed financial decisions, and work toward their financial goals.

Combining intelligent budgeting tools with **WEWE**, a friendly green robot financial assistant, WEBANKI transforms financial management from simply tracking expenses into understanding money and making better decisions.

Whether you're a student managing a limited budget, a professional organizing your salary, a family planning household expenses, a freelancer managing irregular income, or someone saving for a major purchase, WEBANKI helps you take control of your finances.

---

## 🚀 Our Core Innovation: Safe-to-Spend Through Earmarking

**Your bank balance tells you how much money you have. WEBANKI helps you understand how much you can actually afford to spend.**

Traditional budgeting often focuses on recording expenses and reviewing spending after the money has already been spent.

WEBANKI takes a more proactive approach.

It organizes income into dedicated categories, or *buckets*, for financial commitments such as rent, bills, tuition, and savings. Instead of treating the entire account balance as available money, WEBANKI calculates a **Safe-to-Spend** amount that accounts for reserved funds and qualifying upcoming financial obligations.

### 💡 How It Works

Imagine a user has $2,000 in their account.

| Financial Summary | Amount |
|---|---:|
| Total Balance | $2,000 |
| Rent Reserved | $700 |
| Upcoming Bills | $200 |
| Savings Reserved | $300 |
| **Safe to Spend** | **$800** |

*This is an illustrative example. Actual calculations depend on the application's rules and the user's recorded financial information.*

Although the user has $2,000 in total, some of that money is already committed to important expenses and savings goals.

WEBANKI helps the user understand that distinction before making their next spending decision.

### 🤖 Meet WEWE

WEWE is WEBANKI's friendly green robot assistant, designed to make financial management more intuitive and approachable.

Rather than forcing users to navigate complicated financial reports, WEWE helps them interact with their financial information and explore questions about their spending and savings goals.

For example, users might want to know:

- Can I afford this purchase?
- How much money can I safely spend this week?
- How much should I reserve for upcoming bills?
- How can I organize my salary?
- How can I work toward my savings goal?

The goal is to make financial information easier to understand and turn it into practical decisions.

**WEBANKI doesn't just show people how much money they have. It helps them understand how much they can safely spend.**

---

## ✨ Key Features

### 💰 Smart Budgeting and Salary Allocation
- Organize income into categories such as rent, bills, tuition, and savings.
- Allocate salary toward planned expenses and financial goals.
- Keep committed funds visible instead of treating the entire balance as freely spendable.

### 🛡️ Safe-to-Spend Calculation
- Calculate available spending money based on recorded balances and financial commitments.
- Account for qualifying upcoming bills, including obligations due within the next 14 days.
- Help users make spending decisions with a clearer understanding of their remaining financial flexibility.

### 🎯 Savings Goals
- Set savings targets and reserve money toward them.
- Track progress toward financial goals.
- Use the available budgeting information to help plan for future purchases.

### 📅 Weekly Spending Limits
- Set a weekly spending limit.
- Track how much of the limit remains as expenses are recorded.
- Encourage more consistent spending habits.

### 🤖 WEWE Financial Assistant
- Interact with a friendly assistant designed to make financial information easier to understand.
- Receive contextual financial tips based on available information.
- Explore affordability and budgeting questions.

*AI-powered free-form conversations are still being developed, so the assistant's current capabilities may be more limited than the long-term vision.*

### 🔄 Round-Up Savings
- Support a round-up savings concept in which eligible expenses contribute additional amounts toward savings.

### 🔔 Bill Reminders
- Identify bills approaching their due dates.
- Provide reminders for recorded bills due within three days.

### 📊 Monthly Spending Reports
- Review recorded spending by category.
- Understand where money is going.
- Use spending patterns to make more informed budgeting decisions.

### 🔁 Recurring Bills
- Manage recurring bill records.
- Advance a recurring bill's due date when the bill is marked as paid.

### 🔐 User Accounts
- Register and log in securely.
- Hash passwords using PBKDF2.
- Use token-based authentication for protected API endpoints.
- Keep each user's financial records separated from those of other users.

---

## 🌍 Who Is WEBANKI For?

WEBANKI is designed to support people at different stages of life and with different financial priorities.

| Audience | How WEBANKI Can Help |
|---|---|
| Students | Organize limited budgets, tuition, and savings |
| Employees | Allocate salary and prepare for upcoming expenses |
| Families | Plan household expenses and recurring bills |
| Freelancers | Organize income and prepare for financial commitments |
| Savers | Track progress toward personal financial goals |
| Young professionals | Build healthier financial habits |
| Anyone planning a major purchase | Understand how spending may affect savings goals |

Our vision is to make practical financial planning more accessible, regardless of someone's income, occupation, or financial experience.

---

## 🧠 What Makes WEBANKI Different?

WEBANKI brings together three important ideas:

**1. Proactive budgeting**

Rather than focusing only on money already spent, WEBANKI helps users account for financial commitments before deciding what they can spend.

**2. Safe-to-Spend awareness**

A total balance does not necessarily represent freely available money. WEBANKI makes the distinction between money on hand and money available for discretionary spending more visible.

**3. Conversational financial assistance**

Through WEWE, we aim to make financial information easier to understand by allowing people to interact with their finances in a more natural way.

Together, these ideas support a shift from expense tracking toward more informed financial decision-making.

---

## 🛠️ Technology Stack

### Backend
- **Python** — Core application logic
- **FastAPI** — REST API framework
- **SQLite** — Database for application records
- **JWT** — Token-based authentication
- **PBKDF2** — Password hashing

### Frontend
- Web-based user interface
- Deployed using Vercel

### AI Integration
- WEWE is designed to provide conversational financial assistance.
- AI-powered free-form questions and contextual responses are a work in progress.

---

## 🏗️ System Architecture

WEBANKI separates the user interface from the backend services.

1. **Frontend:** Users interact with the application through its web interface.
2. **Authentication:** Users register or log in to access their accounts.
3. **Backend API:** FastAPI handles authenticated requests and financial calculations.
4. **Database:** SQLite stores application data.
5. **Financial logic:** The backend processes budgets, buckets, expenses, savings allocations, and affordability calculations.
6. **WEWE:** The assistant helps users interact with financial information, with more advanced AI capabilities under development.

This structure provides a foundation for expanding the application with more advanced AI features and a persistent production database.

---

## 🔗 Live Demo

**Try WEBANKI:**  
https://frontend-lake-xi-76.vercel.app

**GitHub Repository:**  
https://github.com/saldebis/WeBankI

---

## 🎥 Project Demonstration

**Demo Video:**  
[Add demo video link here]

The demonstration will showcase the user interface, account workflow, budgeting features, Safe-to-Spend calculation, and WEWE assistant.

---

## 📊 Project Presentation

**Presentation Slides:**  https://drive.google.com/file/d/1VnlIfgagM38XqRZpJdzIg5WE7HckYYbh/view?usp=sharing


---

## ⚙️ Running the Backend Locally

### Requirements
- Python 3.10 or a compatible version
- pip

### 1. Clone the repository

```bash
git clone https://github.com/saldebis/WeBankI.git
cd WeBankI
```

### 2. Navigate to the backend

```bash
cd backend
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Configure the following variables in your environment:

```env
WEBANKI_SECRET=your_secret_key
WEBANKI_DB=webanki.db
```

Use a strong, private secret key. Never commit real secrets or API keys to GitHub.

### 5. Start the backend server

```bash
python -m uvicorn main:app --reload
```

### 6. Explore the API

Once the server is running, open:

http://127.0.0.1:8000/docs

The interactive API documentation allows you to explore the available endpoints.

---

## 🔌 API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/auth/register` | Register an account |
| POST | `/auth/login` | Log in |
| GET | `/me/dashboard` | Retrieve dashboard information |
| POST | `/me/buckets` | Create a budget bucket |
| POST | `/me/payday` | Process salary allocation |
| POST | `/me/expenses` | Record an expense |
| POST | `/me/buckets/{id}/pay` | Mark a bucket-related payment |
| GET | `/me/afford?amount=` | Check affordability |
| GET | `/me/reminders` | Retrieve bill reminders |
| GET | `/me/report` | Retrieve the spending report |

Protected `/me/...` endpoints require a valid Bearer token.

Financial amounts are represented as integer cents in the backend to help avoid floating-point rounding errors.

---

## 🔒 Security and Privacy

WEBANKI incorporates foundational security practices, including:

- Password hashing using PBKDF2.
- Token-based authentication.
- Authentication requirements for protected endpoints.
- User-specific access to financial records.

**Important:** WEBANKI is currently a prototype and should not be used to store sensitive real-world financial information. It does not connect to real bank accounts or move real money.

Further security testing and hardening would be necessary before production use.

---

## ⚠️ Current Limitations

WEBANKI is an evolving prototype, and some capabilities are still under development.

- The application uses simulated financial data rather than live bank connections.
- No real money is transferred.
- Free-form AI conversations with WEWE are still being improved.
- The current deployment may use temporary storage, meaning data can be lost when the environment resets.
- A persistent production database and additional reliability improvements are future development goals.

These limitations define the current scope of the prototype and provide clear directions for future development.

---

## 🔮 Future Development

Our vision is to develop WEBANKI into a more intelligent and reliable personal finance companion.

Planned improvements include:

- **More capable AI assistance:** Improve WEWE's ability to understand natural-language questions, follow conversational context, and explain calculations using users' actual financial data.
- **Personalized financial insights:** Provide more relevant suggestions based on recorded spending and savings goals.
- **Persistent cloud database:** Preserve user data reliably between sessions and deployments.
- **Expanded financial planning:** Improve support for long-term goals and future expenses.
- **Enhanced visualization:** Make financial patterns and progress easier to understand.
- **Stronger testing and security:** Improve reliability, validation, and protection of user data.
- **Future integrations:** Explore appropriate integrations with external financial services, subject to security, privacy, and regulatory requirements.

---

## 👥 Team

| Team Member | Responsibility |
|---|---|
| Salma | Backend development and financial logic |
| [Teammate's Name] | Frontend development |

---

## 💚 Our Vision

We believe managing money should not require people to become financial experts.

Everyone deserves a clearer understanding of their finances, the ability to plan ahead, and the confidence to make informed decisions.

WEBANKI aims to make that possible by combining practical budgeting tools, proactive financial planning, and approachable AI assistance.

**Your money has a purpose. WEBANKI helps you plan for it.**

---

## 📌 Disclaimer

WEBANKI is an educational and experimental personal finance prototype. It does not provide regulated financial advice, connect to real bank accounts, or execute real financial transactions. Calculations and recommendations depend on the information entered into the application.
