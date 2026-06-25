from __future__ import annotations
from typing import Any, Awaitable, Callable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject


class DepsMiddleware(BaseMiddleware):
    """Inject pool, cache, and bot into handler data."""

    def __init__(self, pool, cache, bot):
        self.pool = pool
        self.cache = cache
        self.bot = bot

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        data["pool"] = self.pool
        data["cache"] = self.cache
        data["bot"] = self.bot
        return await handler(event, data)
