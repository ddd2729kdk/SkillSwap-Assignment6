# SkillSwap API — Assignment 6

FastAPI REST API upgraded from Assignment 5 in-memory storage to persistent PostgreSQL storage using SQLAlchemy 2.x, Alembic and Pydantic v2. Existing Assignment 5 endpoints and business rules are retained.

## Stack
- FastAPI + Pydantic validation
- PostgreSQL + SQLAlchemy ORM
- Alembic schema migrations
- psycopg 3 PostgreSQL driver

## Project structure
```text
app/
  main.py                 FastAPI application and startup
  database.py             SQLAlchemy engine and session factory
  models.py               ORM tables, keys, constraints and relationships
  exceptions.py           Consistent API error responses
  seed.py                 Optional demo data
  routers/                REST endpoints
  schemas/                Pydantic request/response models
  services/               Business logic and database CRUD
migrations/
  env.py
  versions/0001_initial_schema.py
tests/
  test_api.py
  conftest.py
.env.example
```

## 1. PostgreSQL setup (Windows / VS Code)

Create a PostgreSQL database named `skillswap` in pgAdmin (or psql). Example SQL:
```sql
CREATE DATABASE skillswap;
```

Open the project folder in VS Code. In its terminal:
```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
```
Copy `.env.example` to `.env` and replace `YOUR_PASSWORD` with your local PostgreSQL password:
```env
DATABASE_URL=postgresql+psycopg://postgres:YOUR_PASSWORD@localhost:5432/skillswap
SKILLSWAP_SEED=1
```
Do not commit `.env`; it is ignored by Git. Keep `.env.example` in the repository.

## 2. Apply database migration

Run from the project root (the folder containing `alembic.ini`):
```powershell
alembic upgrade head
```
This creates `users`, `skills`, `user_skills`, `swaps`, `reviews` and `alembic_version`. The migration can recreate the schema on a fresh database.

## 3. Start API
```powershell
uvicorn app.main:app --reload
```
Open http://127.0.0.1:8000/docs. Demo data is inserted once when the database is empty. Set `SKILLSWAP_SEED=0` for an empty database.

## Database design and relationships
- **User → UserSkill:** one-to-many. A user has multiple skill profile records; each profile record belongs to one user.
- **Skill → UserSkill:** one-to-many. A skill can appear in many user profiles.
- **User → Swap:** one-to-many in two roles (`requester` and `partner`).
- **Swap → Review:** one-to-many. Each review belongs to a swap.
- Foreign keys enforce references. `uq_user_skill` prevents a user adding the same skill twice; `uq_review_swap_author` prevents duplicate reviews by one author for one swap. Skill names and user emails are unique. User IDs and skill IDs are primary keys.

## Existing API
| Resource | Endpoints |
|---|---|
| Users | `POST/GET /users`, `GET/PATCH/DELETE /users/{id}`, `GET /users/{id}/matches` |
| User skills | `POST/GET /users/{id}/skills`, `PATCH/DELETE /users/{id}/skills/{record_id}` |
| Skills | `POST/GET /skills`, `GET/PATCH/DELETE /skills/{id}`, `GET /skills/{id}/teachers` |
| Swaps | `POST/GET /swaps`, `GET/PATCH/DELETE /swaps/{id}`, `PATCH /swaps/{id}/status` |
| Reviews | `POST/GET /reviews`, `GET/PATCH/DELETE /reviews/{id}` |

## Swagger testing checklist
1. `GET /users` and `GET /skills` — seeded data.
2. `POST /users` — create a user; `GET /users/{id}` — retrieve; `PATCH` — update; `DELETE` — delete when no active swaps.
3. `POST /users/{id}/skills` — add a profile skill; `GET` — verify its related skill name.
4. `POST /swaps` — create a future swap between valid users with correct offer relationships.
5. `PATCH /swaps/{id}/status` — accept and complete it.
6. `POST /reviews` — add a review for a completed swap.
7. Try invalid email/rating, missing foreign-key IDs, duplicate email/skill, and invalid business transitions. Expected responses include 422, 404, 409, 400 and 403.
8. Restart the server and repeat GET requests: records remain because PostgreSQL stores them persistently.

## Tests
Set `TEST_DATABASE_URL` to a dedicated test PostgreSQL database before running pytest:
```powershell
$env:TEST_DATABASE_URL="postgresql+psycopg://postgres:YOUR_PASSWORD@localhost:5432/skillswap_test"
python -m pip install -r requirements-dev.txt
pytest -q
```
The test fixture drops and recreates tables in that database. **Never point `TEST_DATABASE_URL` at a database containing important data.**

## GitHub submission
Commit the full project including `app/`, `migrations/`, `alembic.ini`, requirements, README and `.env.example`. Do not commit `.env`, virtual environments, passwords, or local database files. Submit the shared repository URL on Moodle.
