from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from utils.db.storage import DatabaseManager
import logging

from data import config

logger = logging.getLogger(__name__)

# Инициализируем компоненты только при необходимости
def init_bot():
    """Инициализирует бота только при необходимости"""
    if not config.BOT_TOKEN or config.BOT_TOKEN == "your_bot_token_here" or len(config.BOT_TOKEN) < 10:
        raise ValueError("BOT_TOKEN не установлен в .env файле или имеет неверный формат")
    return Bot(
        token=config.BOT_TOKEN, 
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

def init_dispatcher():
    """Инициализирует диспетчер"""
    bot = init_bot()
    
    # Выбираем storage в зависимости от окружения
    if hasattr(config, 'REDIS_URL') and config.REDIS_URL:
        try:
            storage = RedisStorage.from_url(config.REDIS_URL)
            logger.info("Используется Redis storage")
        except Exception as e:
            logger.warning(f"Не удалось подключиться к Redis: {e}, используется Memory storage")
            storage = MemoryStorage()
    else:
        storage = MemoryStorage()
        logger.info("Используется Memory storage")
    
    return Dispatcher(storage=storage)

# Создаем экземпляры только при вызове функций
storage = MemoryStorage()
dp = None  # Будет инициализирован при необходимости
db = DatabaseManager('data/database.db')

# Функция для получения диспетчера
def get_dispatcher():
    global dp
    if dp is None:
        dp = init_dispatcher()
    return dp

# Функция для получения бота
def get_bot():
    return init_bot()

# Функция для получения базы данных
def get_db():
    return db

# Функция для регистрации роутеров
def register_routers():
    """Регистрирует все роутеры в диспетчере"""
    from handlers.admin import add, orders, questions
    from handlers.user import menu, catalog, cart, wallet, sos, delivery_status
    
    dp = get_dispatcher()
    
    # Регистрируем admin роутеры
    dp.include_router(add.router)
    dp.include_router(orders.router)
    dp.include_router(questions.router)
    
    # Регистрируем user роутеры
    dp.include_router(menu.router)
    dp.include_router(catalog.router)
    dp.include_router(cart.router)
    dp.include_router(wallet.router)
    dp.include_router(sos.router)
    dp.include_router(delivery_status.router)
    
    logger.info("Все роутеры зарегистрированы")