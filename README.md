# MovieWatch

A full-stack movie ticket availability tracker. Configure a movie, city, date,
platform, cinema, time window and seat count; MovieWatch polls in the
background and notifies you the moment matching tickets appear.

## Overview

- **Frontend**: Angular 20 + Angular Material, dark cinematic theme (with
  light mode), responsive, JWT-authenticated SPA.
- **Backend**: FastAPI + SQLAlchemy + PostgreSQL, JWT auth, APScheduler
  background worker, pluggable ticket-provider architecture.
- **Notifications**: email + Telegram abstraction that degrades gracefully
  (the app fully works with zero notification credentials configured — it
  just records in-app notifications and skips the external channels).

## Architecture

```
backend/app/
  main.py                    FastAPI app, CORS, scheduler lifecycle
  config.py                  Settings (env-driven)
  database.py                SQLAlchemy engine/session
  models/                    user, movie, tracker, show, notification
  schemas/                   Pydantic request/response models
  api/                       auth, movies, trackers, shows, notifications
  providers/
    base_provider.py         TicketProvider abstract interface
    mock_provider.py         Fully working simulated provider (see below)
    bookmyshow_provider.py   Documented stub — no public API exists
    district_provider.py     Documented stub — no public API exists
  services/
    tracker_service.py       Availability-checking + matching logic
    notification_service.py  Email / Telegram / in-app notification fan-out
    movie_service.py         Movie get-or-create helper
  workers/
    availability_worker.py   APScheduler: one job per active tracker
  tests/                     pytest suite (11 tests, all passing)

frontend/src/app/
  core/                      models, services, JWT interceptor, auth guard
  pages/
    login, register          Auth
    dashboard                Active trackers, start/stop/delete
    create-tracker           New tracker form
    tracker-details          Live shows table + Book Now links
    notifications            Notification history
    settings                 Notification channels + preferences
  shared/nav                 Top nav with dark/light toggle
```

### Provider architecture & why BookMyShow/District aren't "really" wired up

`TicketProvider` is the shared interface (`search_movies`, `get_showtimes`,
`check_availability`, `get_booking_url`). `MockTicketProvider` is a complete,
deterministic simulation used for all development and testing.

BookMyShow and District do not publish a public ticket-availability API.
Per the project's own rules (no CAPTCHA bypass, no scraping of private
endpoints, no evading rate limits or anti-bot systems), `bookmyshow_provider.py`
and `district_provider.py` are **documented stubs that raise
`NotImplementedError`** rather than unauthorized scrapers. Each file's
docstring explains exactly what an authorized integration would need and
where to plug it in (`tracker_service.py`'s provider registry). Selecting
those platforms in the UI works end-to-end except that the availability
check itself returns no results, which is clearly the honest behavior for
"we don't have a legitimate way to get this data yet."

## Mock provider — simulated states

`MockTicketProvider` simulates each (movie, city, date) combination moving
through:

```
MOVIE_NOT_AVAILABLE -> SHOW_AVAILABLE (0 seats) -> SEATS_AVAILABLE (N seats)
```

automatically over time (`MOCK_PROVIDER_AVAILABILITY_DELAY_SECONDS`), or you
can force any state instantly for demos/tests via:

```
POST /api/dev/mock/force-state
{ "movie_id": "mock-avatar", "city": "Visakhapatnam", "date": "2026-09-25", "state": "SEATS_AVAILABLE" }
```

Valid `state` values: `MOVIE_NOT_AVAILABLE`, `SHOW_NOT_AVAILABLE`,
`SHOW_AVAILABLE`, `SEATS_AVAILABLE`, `SEATS_SOLD_OUT`.

## Running locally with Docker (recommended)

```bash
cp backend/.env.example backend/.env   # already done for this delivered copy
docker compose up --build
```

- Frontend: http://localhost:4200
- Backend API: http://localhost:8000 (docs at http://localhost:8000/docs)
- Postgres: localhost:5432 (user/pass/db: `moviewatch`)

Register an account in the UI, create a tracker, hit Start, and use the
`/docs` Swagger UI to call `/api/dev/mock/force-state` to instantly flip a
tracker's showset to `SEATS_AVAILABLE` and watch the notification appear.

## Running locally without Docker

**Backend** (Python 3.11+):
```bash
cd backend
pip install -r requirements.txt --break-system-packages   # or use a venv
cp .env.example .env   # defaults to SQLite if DATABASE_URL is left as-is locally
uvicorn app.main:app --reload
```
By default `config.py` falls back to a local SQLite file if `DATABASE_URL`
isn't reachable/set, so you can run the backend with zero external services
for quick testing. Set `DATABASE_URL` to your Postgres instance to use it
for real.

**Frontend** (Node 20+):
```bash
cd frontend
npm install
npm start   # ng serve, http://localhost:4200
```
The frontend reads its API base URL from `public/config.js`
(`window.__MOVIEWATCH_API_BASE__`), defaulting to `http://localhost:8000`.

## Environment variables (`backend/.env`)

```
DATABASE_URL=postgresql://moviewatch:moviewatch@localhost:5432/moviewatch
JWT_SECRET=change-this-secret-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440
EMAIL_HOST=
EMAIL_PORT=587
EMAIL_USERNAME=
EMAIL_PASSWORD=
EMAIL_FROM=noreply@moviewatch.local
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
DEFAULT_CHECK_INTERVAL_MINUTES=5
MOCK_PROVIDER_AVAILABILITY_DELAY_SECONDS=60
CORS_ORIGINS=http://localhost:4200
```

Leave the email/Telegram fields blank to run with zero notification
credentials — the app still works and records in-app notifications with
status `skipped` for the unconfigured channels.

## API summary

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/auth/register` | Create account |
| POST | `/api/auth/login` | OAuth2 password login → JWT |
| GET | `/api/auth/me` | Current user |
| PUT | `/api/auth/me/settings` | Update notification email / Telegram chat id |
| GET | `/api/movies/search?q=&city=` | Search movies (mock) |
| POST | `/api/trackers` | Create tracker |
| GET | `/api/trackers` | List my trackers |
| GET/PUT/DELETE | `/api/trackers/{id}` | Get / update / delete |
| POST | `/api/trackers/{id}/start` | Start monitoring (schedules worker job) |
| POST | `/api/trackers/{id}/stop` | Stop monitoring |
| GET | `/api/trackers/{id}/shows` | Shows currently known for a tracker |
| GET | `/api/notifications` | My notification history |
| POST | `/api/notifications/test` | Send a test notification |
| POST | `/api/dev/mock/force-state` | Force the mock provider's simulated state |
| POST | `/api/dev/mock/reset` | Reset a showset's simulation |
| GET | `/health` | Health check |

Full interactive docs at `/docs` once the backend is running.

## Testing

```bash
cd backend
pytest -q
```

11 tests, covering: registration/login, protected routes, movie search,
tracker CRUD, ownership isolation (users can't see each other's trackers),
start/stop, and the full mock-provider availability → notification pipeline
(the workflow explicitly required by the spec):

```
Create tracker -> Start tracker -> Worker checks mock provider ->
initially unavailable -> forced available -> availability detected ->
notification generated -> visible via GET /api/notifications
```

All 11 pass as of this delivery.

The frontend was verified with `ng build --configuration production`
(clean build) and manually smoke-tested against the running backend.

## Deployment

- **Frontend → Vercel**: point Vercel at `frontend/`, build command
  `npm run build`, output directory `dist/frontend/browser`. Set the
  `API_BASE_URL` your deployed backend serves at by editing
  `public/config.js` (or scripting it into the build) since Vercel doesn't
  run the Docker entrypoint.
- **Backend → Render/Railway**: point at `backend/`, it already has a
  `Dockerfile`. Set `DATABASE_URL` to the platform's managed Postgres
  connection string, plus `JWT_SECRET`, `CORS_ORIGINS` (your Vercel URL),
  and optionally the email/Telegram variables.
- **Database**: any managed PostgreSQL 14+ works; the app creates its own
  tables on startup (no separate migration step is required for this
  version — see Limitations).

## Known limitations

- No real BookMyShow/District integration exists (see above) — this is a
  deliberate, documented boundary, not an oversight.
- Schema is created via `Base.metadata.create_all()` on startup rather than
  Alembic migrations; fine for this scope, but a real production rollout
  would want proper migrations before the schema needs to change.
- Browser push notifications are not implemented (email + Telegram +
  in-app are); the notification abstraction (`notification_service.py`)
  is structured so a push channel could be added the same way as
  Telegram.
- Adjacent-seat detection in the mock provider is a simplified heuristic
  (seats >= 2 implies adjacency); a real provider with true seat-map data
  would replace that logic in `tracker_service.py`.
- APScheduler jobs are in-process; for a multi-instance production
  deployment you'd want a shared job store (APScheduler supports this) or
  a dedicated worker process/queue instead of running the scheduler inside
  the API process.
