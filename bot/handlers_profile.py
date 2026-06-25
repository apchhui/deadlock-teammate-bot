from __future__ import annotations
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from database import upsert_profile, get_profile
from bot.keyboards import (
    kb_rank_picker, kb_goal, kb_cancel, kb_skip_cancel, kb_main,
)
from utils import RANKS, HEROES_HINT, EXAMPLE_PROFILE, format_profile
from bot.handlers_menu import send_main_menu

router = Router()

# ── FSM states (stored in Redis) ──────────────────────────────────────────────
S_GAME_ID   = "profile:game_id"
S_RANK      = "profile:rank"
S_TIMEZONE  = "profile:timezone"
S_HEROES    = "profile:heroes"
S_GOAL      = "profile:goal"
S_EXTRA     = "profile:extra"


async def _ask_game_id(target: Message | CallbackQuery, cache, tg_id: int, editing: bool = False):
    await cache.set_state(tg_id, S_GAME_ID)
    if editing:
        await cache.update_draft(tg_id, editing=True)
    text = (
        f"{EXAMPLE_PROFILE}\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "📝 <b>Шаг 1/5 — Steam ID</b>\n\n"
        "Введи свой <b>Steam ID</b> (число)\n\n"
        "<i>Пример:</i>  <code>76561198012345678</code>"
    )
    if isinstance(target, CallbackQuery):
        await target.message.edit_text(text, reply_markup=kb_cancel(), parse_mode="HTML")
        await target.answer()
    else:
        await target.answer(text, reply_markup=kb_cancel(), parse_mode="HTML")


@router.callback_query(F.data == "create_profile")
async def cb_create_profile(call: CallbackQuery, pool, cache):
    tg_id = call.from_user.id
    await cache.del_draft(tg_id)
    await _ask_game_id(call, cache, tg_id, editing=False)


@router.callback_query(F.data == "edit_profile")
async def cb_edit_profile(call: CallbackQuery, pool, cache):
    tg_id = call.from_user.id
    p = await get_profile(pool, tg_id)
    if p:
        # Pre-fill draft with existing values
        await cache.set_draft(tg_id, {
            "game_id": p["game_id"],
            "rank_index": p["rank_index"],
            "timezone": p["timezone"],
            "heroes": p["heroes"],
            "goal": p["goal"],
            "extra": p["extra"] or "",
            "editing": True,
        })
    await _ask_game_id(call, cache, tg_id, editing=True)


@router.callback_query(F.data == "cancel")
async def cb_cancel(call: CallbackQuery, pool, cache):
    tg_id = call.from_user.id
    await cache.del_state(tg_id)
    await cache.del_draft(tg_id)
    await send_main_menu(call, pool, tg_id)


# ── Step 1: Game ID ───────────────────────────────────────────────────────────
@router.message(F.text)
async def handle_text_input(message: Message, pool, cache):
    tg_id = message.from_user.id
    state = await cache.get_state(tg_id)

    if state == S_GAME_ID:
        game_id = message.text.strip()
        if len(game_id) < 3 or len(game_id) > 64:
            await message.answer(
                "⚠️ Ник должен быть от 3 до 64 символов. Попробуй ещё раз.",
                reply_markup=kb_cancel(),
                parse_mode="HTML",
            )
            return
        await cache.update_draft(tg_id, game_id=game_id)
        await cache.set_state(tg_id, S_RANK)
        await message.answer(
            "🏆 <b>Шаг 2/5 — Ранг</b>\n\nВыбери свой текущий ранг:",
            reply_markup=kb_rank_picker(0),
            parse_mode="HTML",
        )

    elif state == S_TIMEZONE:
        tz = message.text.strip()
        if len(tz) > 20:
            await message.answer("⚠️ Слишком длинно. Напиши в формате МСК+0 или UTC+3.")
            return
        await cache.update_draft(tg_id, timezone=tz)
        await cache.set_state(tg_id, S_HEROES)
        await message.answer(
            f"🦸 <b>Шаг 4/5 — Пул героев</b>\n\n"
            f"Перечисли героев через запятую.\n\n"
            f"<i>Пример:</i>  <code>Haze, Seven, Wraith</code>\n\n"
            f"<b>Популярные герои:</b>\n<i>{HEROES_HINT}</i>",
            reply_markup=kb_cancel(),
            parse_mode="HTML",
        )

    elif state == S_HEROES:
        heroes = message.text.strip()
        if len(heroes) < 2 or len(heroes) > 200:
            await message.answer("⚠️ Пул героев должен быть от 2 до 200 символов.")
            return
        await cache.update_draft(tg_id, heroes=heroes)
        await cache.set_state(tg_id, S_GOAL)
        await message.answer(
            "🎯 <b>Шаг 5/5 — Цель</b>\n\nЧего ты хочешь от игры?",
            reply_markup=kb_goal(),
            parse_mode="HTML",
        )

    elif state == S_EXTRA:
        extra = message.text.strip()
        if len(extra) > 300:
            await message.answer("⚠️ Слишком длинно (макс. 300 символов).")
            return
        await cache.update_draft(tg_id, extra=extra)
        await _save_profile(message, pool, cache, tg_id)


# ── Step 2: Rank (paginated picker) ──────────────────────────────────────────
@router.callback_query(F.data.startswith("rank_page:"))
async def cb_rank_page(call: CallbackQuery, cache):
    state = await cache.get_state(call.from_user.id)
    if state != S_RANK:
        await call.answer()
        return
    page = int(call.data.split(":")[1])
    await call.message.edit_reply_markup(reply_markup=kb_rank_picker(page))
    await call.answer()


@router.callback_query(F.data.startswith("rank:"))
async def cb_rank_select(call: CallbackQuery, cache):
    state = await cache.get_state(call.from_user.id)
    if state != S_RANK:
        await call.answer()
        return
    tg_id = call.from_user.id
    rank_index = int(call.data.split(":")[1])
    await cache.update_draft(tg_id, rank_index=rank_index)
    await cache.set_state(tg_id, S_TIMEZONE)
    await call.message.edit_text(
        f"✅ Ранг: <b>{RANKS[rank_index]}</b>\n\n"
        "🕐 <b>Шаг 3/5 — Часовой пояс</b>\n\n"
        "Напиши свой часовой пояс.\n\n"
        "<i>Примеры:</i>  <code>МСК+0</code>   <code>МСК+3</code>   <code>UTC+5</code>   <code>GMT+2</code>",
        reply_markup=kb_cancel(),
        parse_mode="HTML",
    )
    await call.answer()


# ── Step 5: Goal ──────────────────────────────────────────────────────────────
@router.callback_query(F.data.startswith("goal:"))
async def cb_goal_select(call: CallbackQuery, cache):
    state = await cache.get_state(call.from_user.id)
    if state != S_GOAL:
        await call.answer()
        return
    tg_id = call.from_user.id
    goal = call.data.split(":")[1]
    await cache.update_draft(tg_id, goal=goal)
    await cache.set_state(tg_id, S_EXTRA)
    await call.message.edit_text(
        "💬 <b>Дополнительно (необязательно)</b>\n\n"
        "Расскажи о себе пару слов — стиль игры, предпочтения, время онлайна.\n\n"
        "<i>Пример:</i>  <code>Играю вечерами, общаюсь в войс, токс — мимо</code>",
        reply_markup=kb_skip_cancel(),
        parse_mode="HTML",
    )
    await call.answer()


@router.callback_query(F.data == "skip_extra")
async def cb_skip_extra(call: CallbackQuery, pool, cache):
    tg_id = call.from_user.id
    state = await cache.get_state(tg_id)
    if state != S_EXTRA:
        await call.answer()
        return
    await cache.update_draft(tg_id, extra="")
    await _save_profile(call.message, pool, cache, tg_id, edit_msg=call.message)
    await call.answer()


async def _save_profile(
    message: Message,
    pool,
    cache,
    tg_id: int,
    edit_msg=None,
) -> None:
    draft = await cache.get_draft(tg_id)
    required = ["game_id", "rank_index", "timezone", "heroes", "goal"]
    if not all(k in draft for k in required):
        await message.answer("⚠️ Что-то пошло не так. Начни заново через /start.")
        return

    await upsert_profile(
        pool,
        tg_id=tg_id,
        game_id=draft["game_id"],
        rank_index=draft["rank_index"],
        timezone=draft["timezone"],
        heroes=draft["heroes"],
        goal=draft["goal"],
        extra=draft.get("extra") or None,
    )
    await cache.del_state(tg_id)
    await cache.del_draft(tg_id)

    preview = format_profile(
        game_id=draft["game_id"],
        rank_index=draft["rank_index"],
        timezone=draft["timezone"],
        heroes=draft["heroes"],
        goal=draft["goal"],
        extra=draft.get("extra") or None,
        is_own=True,
    )
    success_text = "✅ <b>Анкета сохранена!</b>\n\n" + preview
    markup = kb_main(has_profile=True, is_active=True)

    if edit_msg:
        await edit_msg.edit_text(success_text, reply_markup=markup, parse_mode="HTML")
    else:
        await message.answer(success_text, reply_markup=markup, parse_mode="HTML")
