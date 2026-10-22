# Telegram Shorts — production Mini App

Telegram Shorts is a Telegram Mini App and aiogram bot with a vertical short-video feed. Railway serves the production UI directly from `dist/index.html`; this is intentionally not replaced by a separate React/Vite build.

## Architecture

- `bot.py`: FastAPI API, aiogram bot, PostgreSQL operations, Supabase Storage integration.
- `telegram_auth.py`: independently testable Telegram WebApp `initData` verification.
- `dist/index.html`: production HTML/CSS/JavaScript.
- `database/schema.sql`: PostgreSQL schema.
- `database/migrations/002_comment_social.sql`: additive migration for threaded comments, comment editing/pinning and comment likes.\n- `database/migrations/003_storage_cleanup_queue.sql`: durable retry queue for failed Storage cleanup.
- `tests/`: offline unit tests.
- `scripts/quality_check.py`: one-command offline quality checks.
- `docs/PROJECT_GUIDE.md`: architecture and operational guide.
- `docs/QUALITY_CHECKLIST.md`: release checklist.
- `.github/workflows/quality.yml`: offline checks on push and pull request.

## Local setup

Use Python 3.11+ and Node.js 22+ for the full offline quality command.

```bash
python -m venv .venv
# Activate the environment, then:
pip install -r requirements.txt
cp .env.example .env
python bot.py
```

The app does not automatically load `.env`; export its values in your shell/IDE or configure them in the runtime. Use only a dedicated development bot and non-production database/storage. Never commit `.env` or production credentials.

Required environment variables: `BOT_TOKEN`, `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`. `WEB_APP_URL` defaults to the existing Railway domain. `ADMIN_TELEGRAM_IDS` is an optional comma-separated list of Telegram numeric IDs.

## Quality checks

```bash
python scripts/quality_check.py
```

This runs Python syntax parsing, JavaScript syntax checks for inline production scripts, real unit tests for Telegram `initData` signature/freshness validation, and required-file checks. It reports backend integration availability separately. It does not claim to test a live Telegram client, Railway, Supabase, or a production database.

## Deploy to Railway

Keep the start command `python bot.py` and preserve the existing Railway variables. Before deploying the updated backend, run `database/migrations/002_comment_social.sql` and then `database/migrations/003_storage_cleanup_queue.sql` in the Supabase SQL Editor. Both are additive and idempotent. The app also applies compatible `CREATE/ALTER ... IF NOT EXISTS` schema initialization at startup. Failed Supabase Storage deletions are placed in `storage_cleanup_jobs` and retried by a background worker.

After deployment, check Railway logs, `https://telegram-shorts-production.up.railway.app/health`, `/health/db`, then open the Mini App through the Telegram bot and smoke-test authentication, feed playback, likes, comments, profile and upload.

See `docs/PROJECT_GUIDE.md` and `docs/QUALITY_CHECKLIST.md` for details.
