# Deadlock Teammate Finder Bot

Telegram bot for finding Deadlock teammates using a swipe-based format.

## Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/apchhui/deadlock-teammate-bot.git
cd deadlock-teammate-bot
```

### 2. Create `.env` file
```bash
cp .env.example .env
```
Fill in `BOT_TOKEN` (get one from [@BotFather](https://t.me/BotFather)).

### 3. Run with Docker Compose
```bash
docker compose up -d --build
```

### 4. Logs
```bash
docker compose logs -f bot
```

---

## Architecture

```
deadlock-teammate-bot/
├── bot/
│   ├── __init__.py
│   ├── main.py              # Entry point, Dispatcher
│   ├── middleware.py        # DepsMiddleware (pool, cache, bot)
│   ├── keyboards.py         # All keyboards
│   ├── handlers_menu.py     # /start, main menu, status
│   ├── handlers_profile.py  # Profile creation and editing
│   └── handlers_browse.py   # Browsing profiles, likes, matches
├── database/
│   ├── __init__.py
│   ├── db.py                # Connection pool + DDL
│   └── queries.py           # All SQL queries
├── utils/
│   ├── __init__.py
│   ├── constants.py         # Ranks, goals, heroes
│   ├── cache.py             # Redis helpers (FSM, draft, target)
│   └── formatters.py        # Profile formatting
├── logs/                    # Logs (mounted from container)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

---

## Stack

| Component  | Technology |
|------------|------------|
| Bot        | [aiogram 3](https://docs.aiogram.dev/) |
| Database   | PostgreSQL 16 + asyncpg |
| Cache / FSM| Redis 7 + redis[asyncio] |
| Containers | Docker Compose |
| Logging    | Loguru |

---

## Features

- **Profile**: Steam ID, rank (all 66 Deadlock ranks), timezone, hero pool, goal, extra info
- **Matchmaking**: range of ±1 tier from your rank (e.g. Oracle 4 → Archon + Oracle + Phantom)
- **Swipe**: like / dislike, mutual match triggers a notification to both users
- **Status**: pause and resume search at any time
- **FSM in Redis**: profile drafts stored for 1 hour, states for 24 hours
- **Rate-limit**: flood protection (1 vote/sec)

---

## Scaling

The bot uses aiogram 3 polling (easily switchable to webhook):

```python
# In main.py replace start_polling with:
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

app = web.Application()
SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path="/webhook")
setup_application(app, dp, bot=bot)
web.run_app(app, host="0.0.0.0", port=8080)
```

For horizontal scaling (multiple bot replicas):
- Switch to webhook (polling is incompatible with multiple replicas)
- Add `replicas: N` to `docker-compose.yml` for the `bot` service
- Use nginx or Traefik as a reverse proxy

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `BOT_TOKEN` | — | Telegram bot token (required) |
| `POSTGRES_HOST` | `postgres` | PostgreSQL host |
| `POSTGRES_PORT` | `5432` | PostgreSQL port |
| `POSTGRES_DB` | `deadlock` | Database name |
| `POSTGRES_USER` | `deadlock` | Database user |
| `POSTGRES_PASSWORD` | `deadlock` | Database password |
| `REDIS_HOST` | `redis` | Redis host |
| `REDIS_PORT` | `6379` | Redis port |
| `REDIS_DB` | `0` | Redis database index |
| `ADMINS` | — | Telegram admin IDs (comma-separated) |

---

## Running Without Docker

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Make sure PostgreSQL and Redis are running locally
# and set POSTGRES_HOST=localhost, REDIS_HOST=localhost in .env

python -m bot.main
```
