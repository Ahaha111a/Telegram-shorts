import os
import asyncio
from pathlib import Path

import asyncpg
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
WEB_APP_URL = os.getenv("WEB_APP_URL", "https://telegram-shorts-production.up.railway.app")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не найден")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL не найден")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
app = FastAPI()
db_pool = None

async def get_db_pool():
    global db_pool
    if db_pool is None:
        db_pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=5)
    return db_pool

async def save_user(message: Message):
    user = message.from_user
    pool = await get_db_pool()
    async with pool.acquire() as connection:
        await connection.execute(
            """
            insert into users (id, username, first_name, last_name)
            values ($1, $2, $3, $4)
            on conflict (id) do update set
                username = excluded.username,
                first_name = excluded.first_name,
                last_name = excluded.last_name
            """,
            user.id, user.username, user.first_name, user.last_name
        )

@dp.message(CommandStart())
async def start_handler(message: Message):
    await save_user(message)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="🎬 Открыть Telegram Shorts",
                web_app=WebAppInfo(url=WEB_APP_URL)
            )]
        ]
    )
    await message.answer(
        "👋 Добро пожаловать в Telegram Shorts!\n\n"
        "🎬 Смотри короткие видео и открывай новые возможности.",
        reply_markup=keyboard
    )

DIST_DIR = Path("dist")

if (DIST_DIR / "assets").exists():
    app.mount("/assets", StaticFiles(directory=DIST_DIR / "assets"), name="assets")

@app.get("/")
async def home():
    index_file = DIST_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return JSONResponse({"status": "ok", "service": "Telegram Shorts"})

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "Telegram Shorts"}

async def run_bot():
    print("Telegram Shorts bot запущен!")
    await dp.start_polling(bot)

async def run_web_server():
    port = int(os.getenv("PORT", "8080"))
    config = uvicorn.Config(app, host="0.0.0.0", port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

async def main():
    await asyncio.gather(run_bot(), run_web_server())

if __name__ == "__main__":
    asyncio.run(main())
