import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
import redis.asyncio as redis # <-- Убедись, что этот импорт есть
import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.handlers import basic, preorder, booking, menu
from app.config import settings
from app.scheduler import check_reminders

# --- Конфигурация ---
logging.basicConfig(level=logging.INFO)

# --- Переменные для вебхука ---
WEB_SERVER_HOST = "0.0.0.0"
WEB_SERVER_PORT = settings.PORT
BASE_WEBHOOK_URL = settings.BASE_WEBHOOK_URL
WEBHOOK_PATH = f"/bot/{settings.TELEGRAM_BOT_TOKEN}"

# --- Подключение к Redis ---
try:
    storage = RedisStorage.from_url(settings.REDIS_URL)
except Exception as e:
    logging.error(f"Could not connect to Redis: {e}")
    from aiogram.fsm.storage.memory import MemoryStorage
    storage = MemoryStorage()

# --- Инициализация ---
bot = Bot(token=settings.TELEGRAM_BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher(storage=storage)
scheduler = AsyncIOScheduler(timezone=pytz.UTC)

# --- Регистрация роутеров ---
dp.include_router(basic.router)
dp.include_router(preorder.router)
dp.include_router(booking.router)
dp.include_router(menu.router)

# --- Функции жизненного цикла ---
async def on_startup_webhook(bot: Bot):
    await bot.set_webhook(url=f"{BASE_WEBHOOK_URL}{WEBHOOK_PATH}")
    logging.info(f"Webhook has been set to: {BASE_WEBHOOK_URL}{WEBHOOK_PATH}")
    scheduler.add_job(check_reminders, 'interval', minutes=1, kwargs={'bot': bot})
    scheduler.start()
    logging.info("Scheduler started.")

async def on_shutdown_webhook(bot: Bot):
    logging.info("Stopping bot, scheduler and webhook...")
    scheduler.shutdown()
    await bot.delete_webhook()
    logging.info("Webhook has been deleted.")
    # Закрытие сессии Redis и бота теперь управляется через setup_application
    
# --- НОВАЯ ФУНКЦИЯ ДЛЯ KEEPALIVE ---
async def ping_handler(request):
    """
    Обработчик для UptimeRobot, который будет его "пинговать".
    """
    return web.Response(text="I'm alive!")

# --- Главная функция ---
def main():
    dp.startup.register(on_startup_webhook)
    dp.shutdown.register(on_shutdown_webhook)

    app = web.Application()
    
    # Регистрируем обработчик для Telegram
    webhook_requests_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)
    
    # ДОБАВЛЯЕМ РЕГИСТРАЦИЮ НАШЕГО ПИНГ-ОБРАБОТЧИКА
    app.router.add_get("/ping", ping_handler)
    
    setup_application(app, dp, bot=bot)
    
    logging.info("Starting web server...")
    web.run_app(app, host=WEB_SERVER_HOST, port=WEB_SERVER_PORT)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.info("Bot stopped by user (Ctrl+C)")