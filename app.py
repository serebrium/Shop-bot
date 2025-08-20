
import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram import F
from data import config
from loader import get_dispatcher, get_bot, db, register_routers
import filters
import asyncio

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL, "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOG_FILE if hasattr(config, 'LOG_FILE') else 'bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Инициализируем компоненты только при необходимости
dp = get_dispatcher()
bot = get_bot()

# Настраиваем фильтры
filters.setup(dp)

# Регистрируем роутеры
register_routers()

WEBAPP_HOST = getattr(config, 'WEBHOOK_HOST', "0.0.0.0")
WEBAPP_PORT = getattr(config, 'WEBHOOK_PORT', 5000)
user_message = 'Пользователь'
admin_message = 'Админ'


@dp.message(commands='start')
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
        
        markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.row(f"👤 {user_message}", f"⚙️ {admin_message}")

        await message.answer('''Привет! 👋

🤖 Я бот-магазин по продаже товаров любой категории.
    
🛍️ Чтобы перейти в каталог и выбрать приглянувшиеся товары, воспользуйтесь командой /menu.

💰 Пополнить счет можно через Яндекс.Кассу, Сбербанк или Qiwi.

❓ Возникли вопросы? Не проблема! Команда /sos поможет связаться с администраторами, которые постараются как можно быстрее откликнуться.

🤝 Заказать похожего бота? Свяжитесь с разработчиком <a href="https://t.me/NikolaySimakov">Nikolay Simakov</a>, он не кусается! 😄
        ''', reply_markup=markup)
    except Exception as e:
        logger.error(f"Ошибка в команде start: {e}")
        await message.answer("Произошла ошибка при запуске бота. Попробуйте позже.")


@dp.message(F.text == user_message)
async def user_mode(message: types.Message):
    try:
        # Валидация входных данных
        if not message.from_user:
            logger.warning("Получено сообщение без информации о пользователе")
            return
            
        cid = message.chat.id
        if not cid or cid <= 0:
            logger.warning(f"Некорректный ID чата: {cid}")
            return
            
        logger.info(f"Пользователь {cid} переключился в пользовательский режим")
        
        # Проверяем, является ли пользователь администратором
        if cid in config.ADMINS:
            # Убираем из списка администраторов для пользовательского режима
            config.ADMINS.remove(cid)
            await message.answer('Включен пользовательский режим.', reply_markup=ReplyKeyboardRemove())
        else:
            await message.answer('Вы уже в пользовательском режиме.', reply_markup=ReplyKeyboardRemove())
    except Exception as e:
        logger.error(f"Ошибка при переключении в пользовательский режим: {e}")
        await message.answer("Произошла ошибка. Попробуйте позже.")


@dp.message(F.text == admin_message)
async def admin_mode(message: types.Message):
    try:
        # Валидация входных данных
        if not message.from_user:
            logger.warning("Получено сообщение без информации о пользователе")
            return
            
        cid = message.chat.id
        if not cid or cid <= 0:
            logger.warning(f"Некорректный ID чата: {cid}")
            return
            
        logger.info(f"Пользователь {cid} переключился в админский режим")
        
        # Проверяем, не является ли пользователь уже администратором
        if cid not in config.ADMINS:
            # Добавляем в список администраторов
            config.ADMINS.append(cid)
            await message.answer('Включен админский режим.', reply_markup=ReplyKeyboardRemove())
        else:
            await message.answer('Вы уже в админском режиме.', reply_markup=ReplyKeyboardRemove())
    except Exception as e:
        logger.error(f"Ошибка при переключении в админский режим: {e}")
        await message.answer("Произошла ошибка. Попробуйте позже.")


async def on_startup(dp):
    logger.info("🚀 Бот запускается...")
    db.create_tables()
    logger.info("✅ База данных инициализирована")

    await bot.delete_webhook()
    if hasattr(config, 'WEBHOOK_URL') and config.WEBHOOK_URL:
        await bot.set_webhook(config.WEBHOOK_URL)
        logger.info(f"✅ Webhook установлен: {config.WEBHOOK_URL}")
    else:
        logger.info("✅ Запуск в режиме polling")
    
    logger.info("🎉 Бот успешно запущен!")


async def on_shutdown():
    logger.warning("🛑 Бот выключается...")
    await bot.delete_webhook()
    await dp.storage.close()
    logger.warning("✅ Бот выключен")


async def main():
    """Главная функция запуска бота"""
    logger.info("🚀 Запуск бота...")
    
    # Инициализируем компоненты
    dp = get_dispatcher()
    bot = get_bot()
    
    # Настраиваем фильтры
    filters.setup(dp)
    
    # Регистрируем роутеры
    register_routers()
    
    # Запускаем бота
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == '__main__':

    # Проверяем наличие переменных для webhook
    has_webhook_vars = (("HEROKU_APP_NAME" in list(os.environ.keys())) or
                        ("RAILWAY_PUBLIC_DOMAIN" in list(os.environ.keys())))

    if has_webhook_vars and hasattr(config, 'WEBHOOK_URL') and config.WEBHOOK_URL:
        logger.info("🚀 Запуск в режиме webhook...")
        # TODO: Реализовать webhook для aiogram 3.x
        logger.warning("Webhook режим пока не реализован для aiogram 3.x")
        asyncio.run(main())
    else:
        logger.info("🚀 Запуск в режиме polling...")
        asyncio.run(main())
