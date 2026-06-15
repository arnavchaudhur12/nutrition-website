# Lagads Nutrition

Monorepo for the Lagads Nutrition ecommerce website.

## Stack

- Frontend: React + TypeScript + Vite
- Backend: FastAPI + SQLAlchemy
- Database: SQLite for local development, PostgreSQL-ready for production
- Payments: provider abstraction with Razorpay-ready placeholder configuration
- Email: SMTP configuration for transactional emails

## Structure

- `frontend/`: customer storefront and admin UI shell
- `backend/`: FastAPI APIs, data models, services, and metrics
- `docs/`: architecture and deployment notes

## Branch Strategy

- `dev`: active feature development
- `stage`: pre-production validation
- `prod`: production release branch

## Local Setup

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Notes

- Payment gateway credentials are intentionally environment-driven and not committed.
- Admin credentials should be seeded through environment variables and rotated before launch.
- Production deployment for a FastAPI app with background email and payment callbacks is best hosted on a VPS rather than shared hosting.
- Google Sheets sync can be run with `python backend/scripts/sync_orders_to_google_sheet.py` after setting `GOOGLE_SHEET_ID`, `GOOGLE_SHEET_WORKSHEET`, and `GOOGLE_SERVICE_ACCOUNT_FILE`.
