# Taskme

Production-grade task management app for small teams (5–10 employees).

## Tech stack

- **Frontend**: Reflex (Python)
- **Backend**: FastAPI (separate REST service)
- **DB**: PostgreSQL (SQLAlchemy ORM + Alembic migrations)
- **Auth**: JWT access + refresh tokens
- **Deploy**: Docker Compose

## Project layout

| Area | Path | Notes |
|------|------|--------|
| Frontend app | `frontend/taskme/` | Pages, state, components |
| Static assets (logos, etc.) | `frontend/assets/` | Served at `/filename` (e.g. `/taskme-logo-header.png`) |
| Backend API | `backend/` | Routers, models, Alembic |
| Compose | `docker-compose.yml` | `db`, `backend`, `frontend` |

## Quick start (Docker)

1. Create a `.env` file from the template:

```bash
cp .env.example .env
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

---

## Branding

- **Header logo (CEO + employee):** replace `frontend/assets/taskme-logo-header.png` to update the logo everywhere those headers are used.
- **Login** may use a separate asset (e.g. `/taskme-logo.png`) if configured in `taskme/pages/login.py`.

---

## CEO dashboard (`/dashboard`)

UI-focused enhancements (no API or schema changes required for the features below):

- **Header:** Sticky bar with logo, user initial + name, logout, greeting, status filter, **Add Task** (solid orange primary).
- **Task table:**
  - Taller rows, hover styling, workload table hover for analytics.
  - **Status pills:** Done (green), In Progress (yellow), others unchanged pattern.
  - **Priority** column: values from API when present; otherwise **Medium** (client-side default).
  - **Actions:** Icon group (edit, comments, submissions) in a compact bar; **Done**, **Reassign**, and **Attach** as outline/secondary actions; **Reassign** / attach flows use outline orange where applicable.
- **Dialogs:** **Create Task** and **Generate Now** use solid orange; **Upload** (attach) and **Reassign** confirmations use outline secondary styling.
- **EOD reports:** Card-style section with schedule/timezone, **Active/Inactive** switch (still persisted via **Save schedule**), **Last generated** timestamp from the newest report in the list, and improved past-report rows.
- **Visuals:** Cool neutral page background (`#ECEEF3`), 16px-style radii, soft shadows on main surfaces and analytics.

---

## Employee dashboard (`/tasks`)

- **Header:** Same visual pattern as the CEO header (logo, avatar, name, logout) plus greeting, pending summary, **My Tasks**, and **Refresh**.
- **Mini stats (from current task list only):**
  - **Completed today** — `done` tasks whose `updated_at` date is today (approximation; no separate “completed at” field).
  - **Pending tasks** — count with `status == pending`.
  - **Overdue** — not `done` and deadline date before today.
  - **Avg completion time** — for `done` tasks, mean days from `created_at` to `updated_at` (approximation of cycle time).
- **Task cards:**
  - **Priority** badge: High (red), Medium (yellow), Low (green); priority from API when sent, else Medium.
  - **Task type** label from API when present, else **General**.
  - Title, description, and a **deadline line** (“Due in X days”, “Due tomorrow”, “Overdue”, “Completed”, etc.) with green / amber / red styling; raw due date shown as secondary text.
  - **Progress:** Gradient bar with percentage label, width transition, and a light CSS animation on the gradient.
- **Submit work:** Outline **Submit Work** when there are no submissions; solid green **Submitted ✓** when `submission_count > 0` (both still open the submissions dialog).

---

## Frontend task model (client)

`TaskState` maps API tasks into a rich `TaskDict` used by both roles, including:

- Core: id, title, description, assignee, status, progress, deadline, attachments, comment/submission counts.
- **UI helpers:** `priority`, `task_type`, `created_at`, `updated_at`, `deadline_label`, `deadline_label_color` (labels/colors derived when tasks are loaded).

Backend responses do not need to include `priority` or `task_type` for the app to run; missing values fall back to Medium / General.

---

## Components (selected)

| Component | Role |
|-----------|------|
| `taskme/components/status_badge.py` | Shared status pills (e.g. In Progress → yellow). |
| `taskme/components/progress_bar.py` | Default bar (CEO table); `employee_progress_bar` for gradient + animation. |
| `taskme/components/task_card.py` | Employee task card layout only. |
| `taskme/pages/ceo_dashboard.py` | CEO route and dashboard UI. |
| `taskme/pages/employee_view.py` | Employee route, mini stats, header, submissions UI. |
| `taskme/state/task_state.py` | Shared state, API calls, `TaskDict` building, computed employee stats. |

---

## License / support

Internal or team use as configured for your deployment.
