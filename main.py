import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from aiogram.types import Update
from telegram.bot import create_bot, create_dispatcher
from telegram.handlers import router
from telegram.callbacks import router as callback_router
from modules.database import create_tables, init_db
from modules.seed.products import init_products

init_db()
create_tables()
init_products()

load_dotenv()

bot = create_bot()
dp = create_dispatcher()

dp.include_router(router)
dp.include_router(callback_router)


@asynccontextmanager
async def lifespan(app: FastAPI):
    webhook_url = os.getenv("TELEGRAM_WEBHOOK_URL")
    webhook_secret = os.getenv("TELEGRAM_WEBHOOK_SECRET")

    if not webhook_url:
        raise RuntimeError("TELEGRAM_WEBHOOK_URL is not configured")
    if not webhook_secret:
        raise RuntimeError("TELEGRAM_WEBHOOK_SECRET is not configured")
    await bot.set_webhook(
        url=f"{webhook_url}/telegram/webhook",
        secret_token=webhook_secret,
    )

    print(f"Telegram webhook configured: {webhook_url}/telegram/webhook")

    yield

    await bot.session.close()


app = FastAPI(title="Pizza AI Assistant", lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/telegram/webhook")
async def telegram_webhook(request: Request):
    # 1. Проверка секрета ДО разбора JSON
    expected = os.getenv("TELEGRAM_WEBHOOK_SECRET")
    received = request.headers.get("X-Telegram-Bot-Api-Secret-Token")

    if not received or received != expected:
        raise HTTPException(status_code=403, detail="Invalid secret token")

    # 2. Только теперь парсим и обрабатываем
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    update = Update.model_validate(data, context={"bot": bot})
    await dp.feed_update(bot, update)

    return {"ok": True}