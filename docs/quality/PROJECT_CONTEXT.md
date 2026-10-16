# Project context

## Confirmed structure and entry points
- `bot.py`: Python entry point containing FastAPI routes and an aiogram Telegram bot.
- `dist/index.html`: production frontend source, with inline CSS and JavaScript.
- `src/main.jsx` and `src/style.css`: minimal files; they are not the current production UI entry point.
- `database/schema.sql`: PostgreSQL schema; some schema initialization also exists in `bot.py`.
- `requirements.txt`: pinned Python dependencies.
- `package.json`: no real frontend bundling pipeline; `build` is informational.
- `tests/test_quality_regressions.py`: static regression assertions.

## Stack and data
- FastAPI + asyncpg + PostgreSQL/Supabase database.
- aiogram Telegram bot in the same process.
- Supabase Storage for uploaded video files.
- Telegram WebApp `initData` is sent in `X-Telegram-Init-Data` and must be verified by backend.
- Required env names: `BOT_TOKEN`, `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`; `WEB_APP_URL` has a default; `ADMIN_TELEGRAM_IDS` is optional.
- asyncpg pool sets `statement_cache_size=0` for transaction pooler compatibility.

## Version provenance warning
The ZIP attached for the 2026-10-16 audit does not match current GitHub `main` for the main files. Compare file/blob hashes before uploading this archive; changes in this archive were made against the supplied ZIP, not committed to GitHub.

## Constraints and unknowns
- Production credentials, actual Storage bucket, BotFather Main Mini App settings, Railway deployment and live database were not accessed or changed.
- No real Telegram Android test was performed.
- `video_watch_history` and its API may remain for backward compatibility, but the history UI is removed by product decision.
- Comments currently support plain comments only, not threaded replies.
- Thumbnail display depends on an actual `thumbnail_url`; no thumbnail generation job is included.
