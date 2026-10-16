# Project context

## Подтверждённая структура
- `bot.py`: единый Python entry point; FastAPI API и Telegram bot на aiogram.
- `dist/index.html`: фактический production frontend; HTML, CSS и JavaScript встроены в один файл.
- `src/main.jsx` и `src/style.css`: присутствуют, но минимальны и не являются текущим источником production UI.
- `database/schema.sql`: PostgreSQL/Supabase схема.
- `requirements.txt`: aiogram, FastAPI, uvicorn, asyncpg, httpx, python-multipart.
- `package.json`: `build` печатает, что production build уже находится в `dist/index.html`; полноценной frontend-сборки нет.

## Backend / storage
- PostgreSQL доступен через `asyncpg`; pool настроен с `statement_cache_size=0` для совместимости с pooler.
- В `bot.py` обязательны `BOT_TOKEN`, `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`; `WEB_APP_URL` имеет default; `ADMIN_TELEGRAM_IDS` опционален.
- Видео хранится через Supabase Storage; точный статус реального bucket и credentials не проверяется локальным аудитом.
- Telegram initData validation и API authorization реализованы в `bot.py`; нужно тестировать и негативные сценарии.

## Текущие ограничения
- Frontend — большой single-file UI; любые замены должны проверять все повторные CSS overrides и динамические template strings.
- Нет полноценного frontend bundler/test runner в `package.json`.
- Локальный синтаксис не подтверждает работу в Telegram WebView или на Railway.
- `video_watch_history` и endpoint истории есть в схеме/backend; продуктово UI истории не должен отображаться. Не удалять таблицу без отдельной миграции/согласования.
