import os
import asyncio

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message
from fastapi import FastAPI
import uvicorn


BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не найден")


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
app = FastAPI()


@dp.message(CommandStart())
async def start_handler(message: Message):
    await message.answer(
        "👋 Добро пожаловать в Telegram Shorts!\n\n"
        "🎬 Скоро здесь появится новая платформа коротких видео."
    )


@app.get("/")
async def health_check():
    return {"status": "ok", "service": "Telegram Shorts"}


async def run_bot():
    print("Telegram Shorts bot запущен!")
    await dp.start_polling(bot)


async def run_web_server():
    port = int(os.getenv("PORT", "8080"))
    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info",
    )
    server = uvicorn.Server(config)
    await server.serve()


async def main():
    await asyncio.gather(
        run_bot(),
        run_web_server(),
    )


if __name__ == "__main__":
    asyncio.run(main())
