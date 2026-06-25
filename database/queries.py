from __future__ import annotations
import asyncpg
from typing import Optional


# ── users ────────────────────────────────────────────────────────────────────

async def upsert_user(pool: asyncpg.Pool, tg_id: int, username: Optional[str]) -> None:
    await pool.execute(
        """
        INSERT INTO users (tg_id, username)
        VALUES ($1, $2)
        ON CONFLICT (tg_id) DO UPDATE SET username = EXCLUDED.username
        """,
        tg_id, username,
    )


async def get_user(pool: asyncpg.Pool, tg_id: int) -> Optional[asyncpg.Record]:
    return await pool.fetchrow("SELECT * FROM users WHERE tg_id = $1", tg_id)


# ── profiles ─────────────────────────────────────────────────────────────────

async def get_profile(pool: asyncpg.Pool, tg_id: int) -> Optional[asyncpg.Record]:
    return await pool.fetchrow("SELECT * FROM profiles WHERE tg_id = $1", tg_id)


async def upsert_profile(
    pool: asyncpg.Pool,
    tg_id: int,
    game_id: str,
    rank_index: int,
    timezone: str,
    heroes: str,
    goal: str,
    extra: Optional[str],
) -> None:
    await pool.execute(
        """
        INSERT INTO profiles (tg_id, game_id, rank_index, timezone, heroes, goal, extra)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        ON CONFLICT (tg_id) DO UPDATE
          SET game_id = EXCLUDED.game_id,
              rank_index = EXCLUDED.rank_index,
              timezone = EXCLUDED.timezone,
              heroes = EXCLUDED.heroes,
              goal = EXCLUDED.goal,
              extra = EXCLUDED.extra,
              is_active = TRUE,
              updated_at = NOW()
        """,
        tg_id, game_id, rank_index, timezone, heroes, goal, extra,
    )


async def set_profile_active(pool: asyncpg.Pool, tg_id: int, active: bool) -> None:
    await pool.execute(
        "UPDATE profiles SET is_active = $1 WHERE tg_id = $2",
        active, tg_id,
    )


# ── browse ────────────────────────────────────────────────────────────────────

async def get_next_candidate(
    pool: asyncpg.Pool,
    viewer_id: int,
    rank_min: int,
    rank_max: int,
) -> Optional[asyncpg.Record]:
    """Return a profile not yet voted on by viewer, within rank range."""
    return await pool.fetchrow(
        """
        SELECT p.tg_id, p.game_id, p.rank_index, p.timezone,
               p.heroes, p.goal, p.extra, u.username
        FROM profiles p
        JOIN users u ON u.tg_id = p.tg_id
        WHERE p.is_active = TRUE
          AND p.tg_id <> $1
          AND p.rank_index BETWEEN $2 AND $3
          AND NOT EXISTS (
              SELECT 1 FROM likes l
              WHERE l.from_id = $1 AND l.to_id = p.tg_id
          )
        ORDER BY RANDOM()
        LIMIT 1
        """,
        viewer_id, rank_min, rank_max,
    )


# ── likes / matches ───────────────────────────────────────────────────────────

async def record_vote(
    pool: asyncpg.Pool,
    from_id: int,
    to_id: int,
    is_like: bool,
) -> bool:
    """Save vote. Returns True if mutual like (match) detected."""
    await pool.execute(
        """
        INSERT INTO likes (from_id, to_id, is_like)
        VALUES ($1, $2, $3)
        ON CONFLICT (from_id, to_id) DO UPDATE SET is_like = EXCLUDED.is_like
        """,
        from_id, to_id, is_like,
    )
    if not is_like:
        return False
    # check reverse like
    mutual = await pool.fetchval(
        "SELECT is_like FROM likes WHERE from_id = $1 AND to_id = $2",
        to_id, from_id,
    )
    if mutual:
        # store match (smaller id first for uniqueness)
        u1, u2 = sorted([from_id, to_id])
        await pool.execute(
            """
            INSERT INTO matches (user1_id, user2_id)
            VALUES ($1, $2)
            ON CONFLICT DO NOTHING
            """,
            u1, u2,
        )
        return True
    return False


async def already_voted(pool: asyncpg.Pool, from_id: int, to_id: int) -> bool:
    row = await pool.fetchval(
        "SELECT 1 FROM likes WHERE from_id = $1 AND to_id = $2",
        from_id, to_id,
    )
    return bool(row)
