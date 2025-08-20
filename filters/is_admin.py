from aiogram.types import Message
from aiogram.filters import BaseFilter
from data.config import ADMINS


class IsAdmin(BaseFilter):
    """Фильтр для проверки администратора"""

    async def __call__(self, message: Message) -> bool:
        """Проверяет, является ли пользователь администратором"""
        if message.from_user is None:
            return False
        return message.from_user.id in ADMINS
