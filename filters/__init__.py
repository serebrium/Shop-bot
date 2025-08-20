from aiogram import Dispatcher
from .is_admin import IsAdmin
from .is_user import IsUser

def setup(dp: Dispatcher):
    """Настраивает фильтры для диспетчера"""
    # В aiogram 3.x фильтры регистрируются автоматически через роутеры
    # Здесь можно добавить глобальные фильтры если потребуется
    pass
