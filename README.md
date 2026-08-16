# Allied Tours & Travel

Production-ready **Tours & Travel Management** web application for **Allied Tours & Travel**.

**Tagline:** *Your one-stop travel shop.*

Clients browse tours and submit booking requests **without accounts**. Admins review bookings, generate invoices, and record external payments. Booking status and payment status are tracked separately.

---

## Features

### Public website
- Home, Tours, Destinations, Services, Partners, Gallery, Blog, About, FAQs, Contact, Terms, Privacy
- Tour search/filters, departure availability, booking request form
- Booking confirmation with reference (`ATT-YYYY-######`)
- Check Booking by reference + email/phone
- SEO: meta tags, Open Graph, `sitemap.xml`, `robots.txt`

### Admin portal (`/admin`)
- Secure staff login (no public customer accounts)
- Five RBAC roles with permission codes
- Tours, destinations, departures & capacity
- Bookings, customers, invoices (PDF), manual payments
- Content: blog, gallery, testimonials, FAQs, services, partners
- Dashboard, reports, settings, audit logs

### Core business workflow
```text
Browse → Book → Reference issued (UNPAID)
     → Admin reviews → Invoice → Client pays externally
     → Admin records/verifies payment → CONFIRMED
```

---

## Tech stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.12, Flask, SQLAlchemy, Flask-Migrate, Flask-Login, WTForms |
| Database | PostgreSQL |
| Frontend | Jinja2, Tailwind CSS (CLI build), Vanilla JS |
| Server | Gunicorn (Docker) |
| PDF | ReportLab |

---

## Requirements

- Python 3.12+
- Node.js 18+ (Tailwind build)
- PostgreSQL 14+ (or Docker)

---

## Quick start (Docker)

Required files:
- `Dockerfile`
- `docker-compose.yml`
- `deployment.sh`
- `mypsql.sh`

```bash
cp .env.example .env
# Set SECRET_KEY (>= 32 chars) and POSTGRES_PASSWORD

chmod +x deployment.sh mypsql.sh
./deployment.sh deploy
```

App: http://localhost:8000  
Admin: http://localhost:8000/admin/login

First-time Super Admin (optional seed):

```bash
# In .env set SEED_ADMIN_EMAIL / SEED_ADMIN_PASSWORD, then:
./deployment.sh seed
```

Database helpers:

```bash
./mypsql.sh status
./mypsql.sh shell
./mypsql.sh backup
./mypsql.sh restore backups/allied_allied_tours_YYYYMMDD_HHMMSS.dump
```

Other deploy commands: `./deployment.sh check|build|up|migrate|logs|status|down`
---

## Local installation

### 1. Clone / open project

```bash
cd Allied
```

### 2. Python environment

```bash
py -3.12 -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
# source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Node / Tailwind

```bash
npm install
npm run build:css
```

For CSS watch mode during development:

```bash
npm run watch:css
```

### 4. Environment

```bash
cp .env.example .env
```

Edit `.env`:

```env
FLASK_ENV=development
SECRET_KEY=generate-a-long-random-string
DATABASE_URL=postgresql+psycopg2://allied:allied_secret@localhost:5432/allied_tours
SEED_ADMIN_EMAIL=admin@alliedtours.example
SEED_ADMIN_PASSWORD=ChangeMeNow!123
```

### 5. PostgreSQL (recommended)

Create database and user (example):

```sql
CREATE USER allied WITH PASSWORD 'allied_secret';
CREATE DATABASE allied_tours OWNER allied;
```

Or start only the database via Docker:

```bash
docker compose up -d db
```

For local UI exploration without PostgreSQL, you may temporarily point `DATABASE_URL` at SQLite (see comments in `.env`). Production and Docker use PostgreSQL.

### 6. Migrations & seed

```bash
set FLASK_APP=run.py
flask db upgrade
flask seed
```

If migrations have not been initialized yet:

```bash
flask db init
flask db migrate -m "Initial schema"
flask db upgrade
flask seed
```

### 7. Run Flask

```bash
python run.py
```

Open http://127.0.0.1:5000

---

## Seed admin accounts (demo)

| Role | Email | Password |
|------|-------|----------|
| Super Admin | admin@alliedtours.example | `SEED_ADMIN_PASSWORD` / `ChangeMeNow!123` |
| Operations Manager | ops@alliedtours.example | OpsDemo!12345 |
| Booking Manager | bookings@alliedtours.example | BookDemo!12345 |
| Finance | finance@alliedtours.example | FinanceDemo!123 |
| Content Manager | content@alliedtours.example | ContentDemo!123 |

Sample tours/testimonials are **demo data**. Demo testimonials are flagged `is_demo=True` and should not be treated as real guest reviews in production.

---

## Tests

```bash
pytest
```

Coverage of critical paths:

- Admin authentication / logout / authorization
- Tour create/update/archive
- Booking create, capacity, duplicate submission token
- Invoice totals, PDF generation
- Partial/full payments and booking confirmation
- Role permission boundaries

---

## Production notes

- Set a strong `SECRET_KEY`
- Use `FLASK_ENV=production`
- Serve behind Nginx (TLS termination)
- Run with Gunicorn (see `Dockerfile`)
- Configure real SMTP for invoice/booking emails
- Keep `.env` out of version control
- Replace demo content before go-live
- Ensure `SESSION_COOKIE_SECURE=True` in production (enabled by ProductionConfig)

### Useful commands

```bash
flask db migrate -m "Describe change"
flask db upgrade
flask seed
gunicorn --bind 0.0.0.0:8000 --workers 3 run:app
```

---

## Project structure

```text
allied-tours/
├── app/
│   ├── admin/          # Admin portal + RBAC
│   ├── auth/           # Staff login
│   ├── public/         # Client website
│   ├── models/         # SQLAlchemy models
│   ├── services/       # Booking, invoice, payment, email
│   ├── templates/      # Jinja2
│   └── static/         # CSS, JS, brand assets, uploads
├── migrations/
├── scripts/seed.py
├── tests/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── package.json
├── tailwind.config.js
└── run.py
```

---

## Brand assets

Logo files live in:

```text
app/static/assets/brand/
  logo-primary.png
  logo-light.png
  logo-dark.png
  favicon.png
  favicon.ico
```

Do not stretch or redraw the official Allied Tours & Travel logo.

---

## License

Proprietary — Allied Tours & Travel. All rights reserved.
