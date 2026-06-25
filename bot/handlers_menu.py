from __future__ import annotations
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery

from database import upsert_user, get_profile, set_profile_active
from bot.keyboards import kb_main, kb_my_profile_actions
from utils import format_profile, RANKS

router = Router()


async def send_main_menu(
    target: Message | CallbackQuery,
    pool,
    tg_id: int,
    text: str = "🏠 <b>Главное меню</b>",
) -> None:
    profile = await get_profile(pool, tg_id)
    has_profile = profile is not None
    is_active = profile["is_active"] if has_profile else False
    markup = kb_main(has_profile, is_active)

    status_line = ""
    if has_profile:
        status_emoji = "🟢" if is_active else "🔴"
        status_text = "В поиске тиммейта" if is_active else "Поиск приостановлен"
        status_line = f"\nСтатус: {status_emoji} <i>{status_text}</i>"

    full_text = text + status_line

    if isinstance(target, CallbackQuery):
        await target.message.edit_text(full_text, reply_markup=markup, parse_mode="HTML")
        await target.answer()
    else:
        await target.answer(full_text, reply_markup=markup, parse_mode="HTML")


@router.message(CommandStart())
async def cmd_start(message: Message, pool, cache):
    await upsert_user(pool, message.from_user.id, message.from_user.username)
    await cache.del_state(message.from_user.id)
    await cache.del_draft(message.from_user.id)

    welcome = (
        "👾 <b>Deadlock Teammate Finder</b>\n\n"
        "Привет! Я помогу найти тиммейтов для игры в <b>Deadlock</b>.\n\n"
        "Создай анкету — и начни просматривать других игроков. "
        "При взаимной симпатии мы вас познакомим 🤝\n"
    )
    await send_main_menu(message, pool, message.from_user.id, text=welcome)


@router.callback_query(F.data == "menu")
async def cb_menu(call: CallbackQuery, pool, cache):
    await cache.del_state(call.from_user.id)
    await send_main_menu(call, pool, call.from_user.id)


@router.callback_query(F.data == "my_profile")
async def cb_my_profile(call: CallbackQuery, pool):
    tg_id = call.from_user.id
    p = await get_profile(pool, tg_id)
    if not p:
        await call.answer("У тебя ещё нет анкеты.", show_alert=True)
        return
    text = format_profile(
        game_id=p["game_id"],
        rank_index=p["rank_index"],
        timezone=p["timezone"],
        heroes=p["heroes"],
        goal=p["goal"],
        extra=p["extra"],
        is_own=True,
    )
    markup = kb_my_profile_actions(p["is_active"])
    await call.message.edit_text(text, reply_markup=markup, parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data == "toggle_status")
async def cb_toggle_status(call: CallbackQuery, pool):
    tg_id = call.from_user.id
    p = await get_profile(pool, tg_id)
    if not p:
        await call.answer("Сначала создай анкету.", show_alert=True)
        return
    new_status = not p["is_active"]
    await set_profile_active(pool, tg_id, new_status)
    status_text = "🟢 Ты снова в поиске!" if new_status else "🔴 Поиск приостановлен."
    await call.answer(status_text, show_alert=True)
    await send_main_menu(call, pool, tg_id)


@router.callback_query(F.data == "noop")
async def cb_noop(call: CallbackQuery):
    await call.answer()
