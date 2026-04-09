# Taskme

Production-grade task management app for small teams (5–10 employees).

## Tech stack

- **Frontend**: Reflex (Python)
- **Backend**: FastAPI (separate REST service)
- **DB**: PostgreSQL (SQLAlchemy ORM + Alembic migrations)
- **Auth**: JWT access + refresh tokens
- **Deploy**: Docker Compose

## Quick start (Docker)

1. Create a `.env` file from the template:

```bash
copy .env.example .env
```

2. Start everything:

```bash
docker compose up --build
```

3. Open the app:
- Frontend: `http://localhost:3000`
- Backend docs: `http://localhost:8000/docs`
- Health: `http://localhost:8000/api/health`

## Seed data

After the stack is up (DB reachable), run:

```bash
docker compose exec backend python seed.py
```

This seeds:
- CEO: `ceo / ceo123`
- Employees: `emp1/emp123`, `emp2/emp123`, `emp3/emp123`
- Sample tasks with varied statuses/deadlines

## Environment variables

See `.env.example` for all supported settings.
