from aiogram.types import Message
from aiogram.filters import BaseFilter
from data.config import ADMINS


class IsUser(BaseFilter):
    """Фильтр для проверки обычного пользователя"""

    async def __call__(self, message: Message) -> bool:
        """Проверяет, является ли пользователь обычным пользователем (не администратором)"""
        if message.from_user is None:
            return False
        return message.from_user.id not in ADMINS
