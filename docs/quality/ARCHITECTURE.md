# Architecture

## Request flow
Telegram WebApp → frontend `dist/index.html` → FastAPI routes in `bot.py` → asyncpg PostgreSQL; video files use Supabase Storage. Telegram bot is created with aiogram in the same Python process.

## Rules
- Keep auth validation at API boundary; never trust client-provided user IDs for ownership.
- SQL mutations that toggle user state must be atomic and safe under duplicate requests. Consider idempotent desired-state endpoints for retries rather than blind toggles.
- Frontend uses shared `api()` helper and Telegram auth headers. All UI state changes should reflect server response or roll back on error.
- Use stable video IDs when opening a shared link; validate payload before fetching.
- Add `thumbnail_url` to every video response that renders a tile/preview. Database schema already includes `videos.thumbnail_url`; check upload pipeline before assuming it is populated.
- Avoid loading every video metadata in large grids. Use IntersectionObserver and release `src`/playback on close where safe.
- Do not create production migrations that delete or rewrite user data without approval.
