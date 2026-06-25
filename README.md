# 👾 Deadlock Teammate Finder Bot

Telegram-бот для поиска тиммейтов в игре **Deadlock** в формате свайп-дайтинга.

## 🚀 Быстрый старт

### 1. Клонируй репозиторий
```bash
git clone <repo_url>
cd deadlock_bot
```

### 2. Создай `.env` файл
```bash
cp .env.example .env
```
Заполни `BOT_TOKEN` (получить у [@BotFather](https://t.me/BotFather)).

### 3. Запусти через Docker Compose
```bash
docker compose up -d --build
```

### 4. Логи
```bash
docker compose logs -f bot
```

---

## 🏗 Архитектура

```
deadlock_bot/
├── bot/
│   ├── __init__.py
│   ├── main.py              # Entry point, Dispatcher
│   ├── middleware.py        # DepsMiddleware (pool, cache, bot)
│   ├── keyboards.py         # Все клавиатуры
│   ├── handlers_menu.py     # /start, главное меню, статус
│   ├── handlers_profile.py  # Создание и редактирование анкеты
│   └── handlers_browse.py   # Просмотр анкет, лайки, матчи
├── database/
│   ├── __init__.py
│   ├── db.py                # Пул соединений + DDL
│   └── queries.py           # Все SQL-запросы
├── utils/
│   ├── __init__.py
│   ├── constants.py         # Ранги, цели, герои
│   ├── cache.py             # Redis-хелперы (FSM, draft, target)
│   └── formatters.py        # Форматирование анкет
├── logs/                    # Логи (монтируется из контейнера)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

---

## ⚙️ Стек

| Компонент | Технология |
|-----------|-----------|
| Бот       | [aiogram 3](https://docs.aiogram.dev/) |
| БД        | PostgreSQL 16 + asyncpg |
| Кэш / FSM | Redis 7 + redis[asyncio] |
| Контейнеры| Docker Compose |
| Логи      | Loguru |

---

## 🎮 Функциональность

- **Анкета**: Steam ID, ранг (все 66 рангов Deadlock), часовой пояс, пул героев, цель, доп. инфо
- **Поиск**: диапазон ±1 тир от твоего ранга (например Oracle 4 → Archon + Oracle + Phantom)
- **Свайп**: ❤️ / 👎, при взаимной симпатии — уведомление обоих и предложение написать
- **Статус**: можно поставить поиск на паузу и возобновить
- **FSM в Redis**: черновики анкеты хранятся 1 час, состояния — 24 часа
- **Rate-limit**: защита от флуда (1 голос/сек)

---

## 🔧 Масштабирование

Бот использует **aiogram 3 polling** (легко переключается на webhook):

```python
# В main.py замени start_polling на:
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

app = web.Application()
SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path="/webhook")
setup_application(app, dp, bot=bot)
web.run_app(app, host="0.0.0.0", port=8080)
```

Для горизонтального масштабирования (несколько реплик бота):
- Переключись на **webhook** (polling несовместим с несколькими репликами)
- Добавь `replicas: N` в `docker-compose.yml` для сервиса `bot`
- Используй **nginx** или **Traefik** как reverse proxy

---

## 📋 Переменные окружения

| Переменная | По умолчанию | Описание |
|------------|-------------|----------|
| `BOT_TOKEN` | — | Токен Telegram-бота (обязательно) |
| `POSTGRES_HOST` | `postgres` | Хост PostgreSQL |
| `POSTGRES_PORT` | `5432` | Порт PostgreSQL |
| `POSTGRES_DB` | `deadlock` | Имя базы данных |
| `POSTGRES_USER` | `deadlock` | Пользователь БД |
| `POSTGRES_PASSWORD` | `deadlock` | Пароль БД |
| `REDIS_HOST` | `redis` | Хост Redis |
| `REDIS_PORT` | `6379` | Порт Redis |
| `REDIS_DB` | `0` | Номер БД Redis |
| `ADMINS` | — | Telegram ID админов (через запятую) |

---

## 🛠 Разработка без Docker

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Убедись, что PostgreSQL и Redis запущены локально,
# и укажи их в .env (POSTGRES_HOST=localhost, REDIS_HOST=localhost)

python -m bot.main
```
