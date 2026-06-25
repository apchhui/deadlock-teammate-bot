from __future__ import annotations
import asyncio
import os
from dotenv import load_dotenv
from loguru import logger
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from database import create_pool
from utils import create_cache
from bot import menu_router, profile_router, browse_router
from bot.middleware import DepsMiddleware

load_dotenv()

# ── Logging ───────────────────────────────────────────────────────────────────
logger.remove()
logger.add(sys.stdout, level="INFO", colorize=True,
           format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | {message}")
logger.add("logs/bot.log", level="DEBUG", rotation="10 MB", retention="7 days")


async def main() -> None:
    token = os.environ["BOT_TOKEN"]
    pg_dsn = (
        f"postgresql://{os.getenv('POSTGRES_USER', 'deadlock')}"
        f":{os.getenv('POSTGRES_PASSWORD', 'deadlock')}"
        f"@{os.getenv('POSTGRES_HOST', 'postgres')}"
        f":{os.getenv('POSTGRES_PORT', '5432')}"
        f"/{os.getenv('POSTGRES_DB', 'deadlock')}"
    )
    redis_host = os.getenv("REDIS_HOST", "redis")
    redis_port = int(os.getenv("REDIS_PORT", 6379))
    redis_db   = int(os.getenv("REDIS_DB", 0))

    pool  = await create_pool(pg_dsn)
    cache = await create_cache(redis_host, redis_port, redis_db)
    bot   = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    dp = Dispatcher()

    # Register middleware on all updates
    middleware = DepsMiddleware(pool, cache, bot)
    dp.message.middleware(middleware)
    dp.callback_query.middleware(middleware)

    # Register routers (order matters — menu last as catch-all text)
    dp.include_router(menu_router)
    dp.include_router(profile_router)
    dp.include_router(browse_router)

    logger.info("Bot starting...")
    await dp.start_polling(bot, allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    asyncio.run(main())
