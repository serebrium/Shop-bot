from aiogram import BaseMiddleware
from aiogram.types import Message
from typing import Dict, Any, Callable, Awaitable
import time


class AntiFloodMiddleware(BaseMiddleware):
    def __init__(self, rate_limit: float = 0.5):
        self.rate_limit = rate_limit
        self.user_last_message: Dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        if not event.from_user:
            return await handler(event, data)

        user_id = event.from_user.id
        current_time = time.time()

        last_time = self.user_last_message.get(user_id)
        if last_time is not None and current_time - last_time < self.rate_limit:
            await event.answer("Слишком много запросов. Подождите немного.")
            return

        self.user_last_message[user_id] = current_time
        return await handler(event, data)


