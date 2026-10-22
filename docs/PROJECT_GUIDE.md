# Telegram Shorts — Project Guide

## Architecture

- `bot.py` is the Railway entry point. It starts aiogram polling and a FastAPI server in the same process.
- `dist/index.html` is the production Telegram Mini App. Its HTML, CSS, and JavaScript are embedded in that file and served at `/`.
- `telegram_auth.py` contains the pure standard-library Telegram WebApp `initData` signature and freshness validation used by the backend and unit-tested without production credentials.
- `src/main.jsx` and `src/style.css` are intentionally informational placeholders; they are not a second frontend and are not built over `dist/index.html`.
- `database/schema.sql` documents the PostgreSQL schema. `database/migrations/` contains additive, versioned migrations.
- PostgreSQL is accessed through `asyncpg`; video objects are stored in the Supabase Storage bucket `videos`.

## Entry points and API map

The bot handles `/start` and `/id`. FastAPI routes include authentication (`/api/auth`, `/api/me`), feed (`/api/feed`, `/api/feed/following`), video operations (`/api/videos/*`), comments (`/api/videos/{id}/comments`, `/api/comments/{id}`), profiles/follows (`/api/profile/{id}`, `/api/users/{id}/follow`), saved/history/search/notifications, reports/moderation, and `/health` and `/health/db`.

Use the route decorators in `bot.py` as the source of truth; this guide is an overview, not a complete API specification.

## Environment variables

Required: `BOT_TOKEN`, `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`. `WEB_APP_URL` defaults to the existing Railway domain; `ADMIN_TELEGRAM_IDS` is a comma-separated list of Telegram numeric IDs. Keep real secrets in Railway variables or a local ignored `.env`, never in Git.

Supabase's service-role key is server-only. Never send it to the browser or include it in a ZIP.

## Local run

1. Use Python 3.11 or newer.
2. Create a virtual environment and install `pip install -r requirements.txt`.
3. Copy `.env.example` to `.env` and populate it with a dedicated test bot, non-production database, and test Supabase project.
4. Run `python bot.py`. The bot and web server run concurrently; `PORT` is supplied by Railway.
5. For isolated checks, run `python scripts/quality_check.py`. The authentication unit tests do not require network access or production secrets.

Do not run the app against production data to test destructive actions.

## Database and migrations

`bot.py:init_db()` applies idempotent additive schema initialization on startup for compatibility with the current deployment. Keep it non-destructive. Versioned SQL migrations are also provided for operators who prefer an explicit pre-deploy step. Back up a database before applying any schema change, and never run destructive SQL from a test environment against production.

For this version, apply `database/migrations/002_comment_social.sql` and `database/migrations/003_storage_cleanup_queue.sql` in numeric order in the Supabase SQL Editor before deploying the updated backend, then deploy. Both migrations are additive, idempotent, and preserve existing data. Startup initialization also ensures these structures exist, but explicit migrations make the change auditable.

## Deployment

Railway start command remains `python bot.py`. Railway must provide `BOT_TOKEN`, `DATABASE_URL`, `WEB_APP_URL`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, and optionally `ADMIN_TELEGRAM_IDS`. Root `/` serves `dist/index.html`; `/health` is the lightweight process health endpoint and `/health/db` checks database connectivity.

## Safe-change rules

- Treat PostgreSQL as the source of truth for social state and counts.
- Use parameterized SQL; validate and authorize every protected action server-side.
- Preserve the deployed route and JSON contracts unless compatibility is explicitly reviewed.
- Add schema changes as additive, idempotent migrations; never drop tables/columns as part of startup.
- Keep the production UI in `dist/index.html`; source placeholders do not override it.
- Test on a non-production database before deployment, and report untested real-device behavior honestly.
