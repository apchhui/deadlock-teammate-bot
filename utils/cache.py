from __future__ import annotations
import json
from typing import Any, Optional
import redis.asyncio as aioredis


class Cache:
    def __init__(self, client: aioredis.Redis):
        self._r = client

    # ── FSM state stored in Redis (TTL 1 day) ────────────────────────────────
    async def set_state(self, tg_id: int, state: str) -> None:
        await self._r.setex(f"fsm:{tg_id}:state", 86400, state)

    async def get_state(self, tg_id: int) -> Optional[str]:
        val = await self._r.get(f"fsm:{tg_id}:state")
        return val.decode() if val else None

    async def del_state(self, tg_id: int) -> None:
        await self._r.delete(f"fsm:{tg_id}:state")

    # ── Temporary profile draft ───────────────────────────────────────────────
    async def set_draft(self, tg_id: int, data: dict[str, Any]) -> None:
        await self._r.setex(f"draft:{tg_id}", 3600, json.dumps(data, ensure_ascii=False))

    async def get_draft(self, tg_id: int) -> dict[str, Any]:
        val = await self._r.get(f"draft:{tg_id}")
        return json.loads(val) if val else {}

    async def update_draft(self, tg_id: int, **kwargs: Any) -> None:
        draft = await self.get_draft(tg_id)
        draft.update(kwargs)
        await self.set_draft(tg_id, draft)

    async def del_draft(self, tg_id: int) -> None:
        await self._r.delete(f"draft:{tg_id}")

    # ── Current browse target (for like/dislike) ──────────────────────────────
    async def set_current_target(self, viewer_id: int, target_id: int) -> None:
        await self._r.setex(f"target:{viewer_id}", 600, str(target_id))

    async def get_current_target(self, viewer_id: int) -> Optional[int]:
        val = await self._r.get(f"target:{viewer_id}")
        return int(val) if val else None

    # ── Cooldown / rate-limit ─────────────────────────────────────────────────
    async def is_rate_limited(self, tg_id: int, action: str, ttl: int = 1) -> bool:
        key = f"rl:{tg_id}:{action}"
        set_ok = await self._r.set(key, 1, ex=ttl, nx=True)
        return not set_ok


async def create_cache(host: str, port: int, db: int) -> Cache:
    client = aioredis.Redis(host=host, port=port, db=db)
    await client.ping()
    from loguru import logger
    logger.info("Redis connected.")
    return Cache(client)
