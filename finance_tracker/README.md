# 💰 Personal Finance Tracker — FischerJordan Assignment

A full-featured personal finance tracking web application built with Django, DRF, and PostgreSQL.

## 🛠 Tech Stack
- **Backend**: Django 4.2, Django REST Framework
- **Database**: PostgreSQL
- **Auth**: Django Auth + Google OAuth (via django-allauth)
- **Templates**: Django Templating Language + Bootstrap 5
- **Charts**: Chart.js
- **Email**: SendGrid (console backend in dev)
- **Deployment**: Gunicorn + WhiteNoise

---

## 🚀 Getting Started (Local Setup)

### 1. Clone and set up Python environment
```bash
git clone https://github.com/yourusername/FJ-BE-R2-YourName-YourCollege
cd FJ-BE-R2-YourName-YourCollege

# Create virtual environment
python -m venv venv

# Activate it
# On Mac/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set up environment variables
```bash
# Copy the example file
cp .env.example .env

# Edit .env and fill in your values
# At minimum, set DB_NAME, DB_USER, DB_PASSWORD
```

### 4. Set up PostgreSQL database
```bash
# In your PostgreSQL shell (psql):
CREATE DATABASE finance_tracker;
CREATE USER postgres WITH PASSWORD 'yourpassword';
GRANT ALL PRIVILEGES ON DATABASE finance_tracker TO postgres;
```

### 5. Run Django setup commands
```bash
# Create all database tables
python manage.py makemigrations
python manage.py migrate

# Create an admin account
python manage.py createsuperuser

# Start the dev server
python manage.py runserver
```

### 6. Open the app
Go to **http://127.0.0.1:8000** in your browser.

---

## 📁 Project Structure

```
finance_tracker/
├── finance_tracker/          # Main Django project settings
│   ├── settings.py           # All config (DB, auth, email, etc.)
│   └── urls.py               # URL routing
│
├── accounts/                 # User authentication & profiles
│   ├── models.py             # UserProfile model
│   ├── views.py              # Register, login, logout, profile
│   ├── forms.py              # Registration & profile forms
│   └── signals.py            # Auto-create profile on user creation
│
├── transactions/             # Core financial data
│   ├── models.py             # Category & Transaction models
│   ├── views.py              # CRUD + filtering views
│   └── forms.py              # Transaction & Category forms
│
├── budgets/                  # Budget goals & tracking
│   ├── models.py             # Budget model with usage calculation
│   ├── views.py              # Budget CRUD
│   └── utils.py              # Email alert helper
│
├── dashboard/                # Overview dashboard
│   └── views.py              # Chart data + summary stats
│
├── reports/                  # Financial reports
│   └── views.py              # Monthly & yearly reports
│
└── templates/                # All HTML templates
    ├── base.html             # Shared sidebar layout
    ├── accounts/             # Login, register, profile
    ├── transactions/         # Transaction & category pages
    ├── budgets/              # Budget pages
    ├── dashboard/            # Dashboard with charts
    └── reports/              # Monthly & yearly reports
```

---

## ✅ Features Implemented

### Part A — Basic Task
- [x] **User Authentication** — Register, Login, Logout, Profile management
- [x] **Google OAuth** — Sign in with Google via django-allauth
- [x] **Database Models** — UserProfile, Category, Transaction, Budget
- [x] **Transaction CRUD** — Add, edit, delete income & expense transactions
- [x] **Edge Cases Handled**:
  - Refunds (negative expenses) via `is_refund` flag
  - Category deletion with existing transactions (SET_NULL)
  - Decimal precision via `DecimalField` (never `FloatField`)
- [x] **Dashboard** — Monthly stats + pie chart + bar chart
- [x] **Monthly Reports** — Income vs expense with category breakdown
- [x] **Yearly Reports** — 12-month overview with charts
- [x] **Budgets** — Set budget goals, track usage %, get alerts
- [x] **Budget Alerts** — In-app warnings + email notifications
- [x] **Receipt Uploads** — Upload images for transactions
- [x] **Multi-Currency** — USD, EUR, GBP, INR, JPY, CAD, AUD

### Part B — Extra Credit
- [ ] OpenAI integration (spending insights)
- [ ] Bank statement PDF/CSV import
- [ ] Anomaly detection

---

## 🔑 Key Design Decisions

### Why `DecimalField` for money?
`FloatField` has floating-point precision issues (`0.1 + 0.2 ≠ 0.3`).
`DecimalField` is exact — critical for financial calculations.

### Why `on_delete=SET_NULL` for Category?
When a user deletes a category, we don't want to lose their transaction history.
Transactions keep their data but lose the category reference.

### How refunds work
Instead of storing negative amounts (which violates the `MinValueValidator`),
we use an `is_refund` boolean flag. The `effective_amount` and `signed_amount`
properties handle the math correctly everywhere.

### Signals for UserProfile
We use Django signals to automatically create a `UserProfile` every time a
`User` is created — so you never have to remember to create one manually.

---

## 🌐 Deployment (Render)

1. Push your code to GitHub
2. Go to [render.com](https://render.com) → New Web Service → Connect GitHub
3. Set environment variables in Render dashboard
4. Set build command: `pip install -r requirements.txt`
5. Set start command: `gunicorn finance_tracker.wsgi:application`
6. Add a PostgreSQL database service on Render
7. Run migrations: `python manage.py migrate`

---

## 🧪 Running Tests
```bash
python manage.py test
```
