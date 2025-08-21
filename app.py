import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
from aiogram.filters import Command
from aiogram import F
from data import config
from loader import get_dispatcher, get_bot, db, register_routers
from middlewares.antiflood import AntiFloodMiddleware
import filters
import asyncio

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL, "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(
            config.LOG_FILE if hasattr(config, "LOG_FILE") else "bot.log"
        ),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# Инициализация и регистрация роутеров происходит внутри main()

WEBAPP_HOST = getattr(config, "WEBHOOK_HOST", "0.0.0.0")
WEBAPP_PORT = getattr(config, "WEBHOOK_PORT", 5000)


async def cmd_start(message: types.Message):
    try:
        # Валидация входных данных
        if not message.from_user:
            logger.warning("Получено сообщение без информации о пользователе")
            return

        user_id = message.from_user.id
        if not user_id or user_id <= 0:
            logger.warning(f"Некорректный ID пользователя: {user_id}")
            return

        logger.info(f"Пользователь {user_id} запустил бота")

        await message.answer(
            """Привет! 👋

🤖 Я бот-магазин по продаже товаров любой категории.
    
🛍️ Чтобы перейти в каталог и выбрать приглянувшиеся товары, воспользуйтесь командой /menu.

💰 Пополнить счет можно через BLIK, BTC, ETH, USDT.

❓ Возникли вопросы? Не проблема! Команда /sos поможет связаться с администраторами, которые постараются как можно быстрее откликнуться.

🤝 Заказать похожего бота? Свяжитесь с разработчиком <a href="https://t.me/fastbillfor">Stay here</a>, по цене договоримся! 😄
        """
        )
    except Exception as e:
        logger.error(f"Ошибка в команде start: {e}")
        await message.answer("Произошла ошибка при запуске бота. Попробуйте позже.")


async def on_startup(dp):
    logger.info("🚀 Бот запускается...")
    db.create_tables()
    logger.info("✅ База данных инициализирована")

    current_bot = get_bot()
    await current_bot.delete_webhook()
    if hasattr(config, "WEBHOOK_URL") and config.WEBHOOK_URL:
        await current_bot.set_webhook(config.WEBHOOK_URL)
        logger.info(f"✅ Webhook установлен: {config.WEBHOOK_URL}")
    else:
        logger.info("✅ Запуск в режиме polling")

    logger.info("🎉 Бот успешно запущен!")


async def on_shutdown():
    logger.warning("🛑 Бот выключается...")
    try:
        await get_bot().delete_webhook()
    except Exception:
        pass
    # Закрываем storage, если доступен
    try:
        await get_dispatcher().storage.close()
    except Exception:
        pass
    logger.warning("✅ Бот выключен")


async def main():
    """Главная функция запуска бота"""
    logger.info("🚀 Запуск бота...")

    # Инициализируем компоненты
    dp = get_dispatcher()
    bot = get_bot()

    # Настраиваем фильтры
    filters.setup(dp)

    # Подключаем защиту от флуда
    dp.message.middleware(AntiFloodMiddleware(rate_limit=0.5))

    # Регистрируем роутеры
    register_routers()

    # Регистрируем локальные хендлеры
    dp.message.register(cmd_start, Command("start"))

    # Запускаем бота
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    # Проверяем наличие переменных для webhook
    has_webhook_vars = ("HEROKU_APP_NAME" in list(os.environ.keys())) or (
        "RAILWAY_PUBLIC_DOMAIN" in list(os.environ.keys())
    )

    if has_webhook_vars and hasattr(config, "WEBHOOK_URL") and config.WEBHOOK_URL:
        logger.info("🚀 Запуск в режиме webhook...")
        # TODO: Реализовать webhook для aiogram 3.x
        logger.warning("Webhook режим пока не реализован для aiogram 3.x")
        asyncio.run(main())
    else:
        logger.info("🚀 Запуск в режиме polling...")
        asyncio.run(main())
