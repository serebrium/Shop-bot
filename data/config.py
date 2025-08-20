import os
from pathlib import Path

from dotenv import load_dotenv

# Проверяем существование .env файла
env_path = Path(".env")
if env_path.exists():
    load_dotenv()
else:
    print("⚠️  Файл .env не найден! Создайте его с необходимыми переменными окружения.")

BOT_TOKEN = os.getenv("BOT_TOKEN")

# Проверяем валидность токена
if not BOT_TOKEN or BOT_TOKEN == "your_bot_token_here" or len(BOT_TOKEN) < 10:
    print("❌ BOT_TOKEN не установлен в .env файле или имеет неверный формат")
    BOT_TOKEN = None

PROJECT_NAME = os.getenv("PROJECT_NAME")

# Heroku webhook
# WEBHOOK_HOST = f"https://{PROJECT_NAME}.herokuapp.com"
# WEBHOOK_PATH = '/webhook/' + BOT_TOKEN

# Railway webhook
RAILWAY_HOST = os.getenv("RAILWAY_PUBLIC_DOMAIN")
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH")

if RAILWAY_HOST and WEBHOOK_PATH:
    WEBHOOK_URL = f"{RAILWAY_HOST}{WEBHOOK_PATH}"
else:
    WEBHOOK_URL = None

# Redis для FSM storage (опционально)
REDIS_URL = os.getenv("REDIS_URL")

# Безопасная обработка ADMINS
admins_str = os.getenv("ADMINS", "")
if admins_str and admins_str.strip():
    try:
        ADMINS = list(map(int, admins_str.split(",")))
        print(f"✅ Загружено {len(ADMINS)} администраторов")
    except ValueError as e:
        print(f"❌ Ошибка при парсинге ADMINS: {e}")
        ADMINS = []
else:
    print("⚠️  ADMINS не установлены в .env файле")
    ADMINS = []

# Настройки логирования
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "bot.log")

# Настройки базы данных
DB_PATH = os.getenv("DB_PATH", "data/database.db")

# Настройки webhook
WEBHOOK_HOST: str = str(os.getenv("WEBHOOK_HOST", "0.0.0.0"))
WEBHOOK_PORT: int = int(os.getenv("WEBHOOK_PORT", "5000"))
