# Telegram Shorts

Telegram Mini App for vertical short videos. The current frontend is served from `dist/index.html`; FastAPI and the aiogram bot are started from `bot.py`.

## Required environment
See `.env.example` for variable names. Keep real tokens and service-role keys in Railway variables, never in Git.

## Run
Install `requirements.txt`, set required environment variables, then run `python bot.py`. The current `npm run build` command is informational only; it does not compile the frontend.

## Quality rules
See [`docs/quality/README.md`](docs/quality/README.md) before changing code. Static checks do not replace Telegram Android and production integration tests.
