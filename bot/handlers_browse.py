from __future__ import annotations
from aiogram import Router, F
from aiogram.types import CallbackQuery

from database import get_profile, get_next_candidate, record_vote
from bot.keyboards import kb_browse, kb_match_confirm, kb_main
from bot.handlers_menu import send_main_menu
from utils import format_profile, rank_range

router = Router()


async def _show_candidate(call: CallbackQuery, pool, cache, tg_id: int) -> None:
    my_profile = await get_profile(pool, tg_id)
    if not my_profile:
        await call.answer("Сначала создай анкету.", show_alert=True)
        return
    if not my_profile["is_active"]:
        await call.answer("Твой поиск приостановлен. Возобнови его в меню.", show_alert=True)
        return

    rmin, rmax = rank_range(my_profile["rank_index"], spread=1)
    candidate = await get_next_candidate(pool, tg_id, rmin, rmax)

    if not candidate:
        text = (
            "😔 <b>Пока никого не найдено</b>\n\n"
            "Ты просмотрел всех доступных игроков в твоём диапазоне рангов.\n"
            "Загляни позже — база пополняется 🙏"
        )
        markup = kb_main(has_profile=True, is_active=True)
        await call.message.edit_text(text, reply_markup=markup, parse_mode="HTML")
        await call.answer()
        return

    await cache.set_current_target(tg_id, candidate["tg_id"])

    text = format_profile(
        game_id=candidate["game_id"],
        rank_index=candidate["rank_index"],
        timezone=candidate["timezone"],
        heroes=candidate["heroes"],
        goal=candidate["goal"],
        extra=candidate["extra"],
        tg_username=candidate["username"],
    )
    await call.message.edit_text(text, reply_markup=kb_browse(), parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data == "browse")
async def cb_browse(call: CallbackQuery, pool, cache):
    await _show_candidate(call, pool, cache, call.from_user.id)


@router.callback_query(F.data.startswith("vote:"))
async def cb_vote(call: CallbackQuery, pool, cache, bot):
    tg_id = call.from_user.id

    # rate-limit: 1 vote per second
    if await cache.is_rate_limited(tg_id, "vote", ttl=1):
        await call.answer("Полегче! 😄", show_alert=False)
        return

    is_like = call.data.split(":")[1] == "like"
    target_id = await cache.get_current_target(tg_id)
    if not target_id:
        await call.answer("Анкета устарела, загружаю новую...")
        await _show_candidate(call, pool, cache, tg_id)
        return

    mutual = await record_vote(pool, tg_id, target_id, is_like)

    if mutual:
        # Notify both users
        target_profile = await get_profile(pool, target_id)
        my_profile = await get_profile(pool, tg_id)

        match_text_for_viewer = (
            "🎉 <b>Взаимная симпатия!</b>\n\n"
            f"Игрок <b>{target_profile['game_id']}</b> тоже поставил тебе ❤️\n\n"
            "Хочешь начать диалог?"
        )
        await call.message.edit_text(
            match_text_for_viewer,
            reply_markup=kb_match_confirm(target_id),
            parse_mode="HTML",
        )
        await call.answer("❤️ Взаимная симпатия!")

        # Notify the other user
        match_text_for_target = (
            "🎉 <b>Взаимная симпатия!</b>\n\n"
            f"Игрок <b>{my_profile['game_id']}</b> поставил тебе ❤️, и это взаимно!\n\n"
            "Хочешь начать диалог?"
        )
        try:
            await bot.send_message(
                target_id,
                match_text_for_target,
                reply_markup=kb_match_confirm(tg_id),
                parse_mode="HTML",
            )
        except Exception:
            pass  # user may have blocked the bot

    else:
        emoji = "❤️" if is_like else "👎"
        await call.answer(emoji)
        await _show_candidate(call, pool, cache, tg_id)


@router.callback_query(F.data.startswith("match_accept:"))
async def cb_match_accept(call: CallbackQuery, pool, cache, bot):
    tg_id = call.from_user.id
    partner_id = int(call.data.split(":")[1])
    partner_profile = await get_profile(pool, partner_id)

    if partner_profile and partner_profile.get("username"):
        partner_link = f"@{partner_profile['username']}"
    else:
        partner_link = f"tg://user?id={partner_id}"

    text = (
        "✅ <b>Отлично!</b>\n\n"
        f"Напиши своему новому тиммейту: {partner_link}\n\n"
        f"<i>Ник в игре: <b>{partner_profile['game_id']}</b></i>"
    )
    markup = kb_main(has_profile=True, is_active=True)
    await call.message.edit_text(text, reply_markup=markup, parse_mode="HTML")
    await call.answer("🤝 Удачи в игре!")


@router.callback_query(F.data == "match_decline")
async def cb_match_decline(call: CallbackQuery, pool, cache):
    await call.answer("Окей, продолжаем поиск!")
    await send_main_menu(call, pool, call.from_user.id)
