import asyncpg
from loguru import logger


CREATE_TABLES = """
CREATE TABLE IF NOT EXISTS users (
    tg_id        BIGINT PRIMARY KEY,
    username     TEXT,
    created_at   TIMESTAMPTZ DEFAULT NOW(),
    is_banned    BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS profiles (
    tg_id           BIGINT PRIMARY KEY REFERENCES users(tg_id) ON DELETE CASCADE,
    game_id         TEXT NOT NULL,
    rank_index      SMALLINT NOT NULL,   -- index in RANKS list
    timezone        TEXT NOT NULL,
    heroes          TEXT NOT NULL,       -- comma-separated
    goal            TEXT NOT NULL,       -- 'rank' | 'fun'
    extra           TEXT,
    is_active       BOOLEAN DEFAULT TRUE,
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS likes (
    from_id     BIGINT NOT NULL REFERENCES users(tg_id) ON DELETE CASCADE,
    to_id       BIGINT NOT NULL REFERENCES users(tg_id) ON DELETE CASCADE,
    is_like     BOOLEAN NOT NULL,        -- TRUE = like, FALSE = dislike
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (from_id, to_id)
);

CREATE TABLE IF NOT EXISTS matches (
    id          SERIAL PRIMARY KEY,
    user1_id    BIGINT NOT NULL REFERENCES users(tg_id) ON DELETE CASCADE,
    user2_id    BIGINT NOT NULL REFERENCES users(tg_id) ON DELETE CASCADE,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (user1_id, user2_id)
);

CREATE INDEX IF NOT EXISTS idx_profiles_rank_active ON profiles(rank_index, is_active);
CREATE INDEX IF NOT EXISTS idx_likes_to ON likes(to_id);
CREATE INDEX IF NOT EXISTS idx_likes_from ON likes(from_id);
"""


async def create_pool(dsn: str) -> asyncpg.Pool:
    pool = await asyncpg.create_pool(dsn=dsn, min_size=3, max_size=15)
    async with pool.acquire() as conn:
        await conn.execute(CREATE_TABLES)
    logger.info("PostgreSQL connected, tables ensured.")
    return pool
