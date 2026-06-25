from __future__ import annotations
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from utils.constants import RANKS, GOALS, TIER_NAMES


# ── Main menu ─────────────────────────────────────────────────────────────────
def kb_main(has_profile: bool, is_active: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if has_profile:
        builder.button(text="🔍 Найти тиммейта", callback_data="browse")
        status_text = "🟢 Я в поиске" if is_active else "🔴 Не ищу тиммейта"
        toggle_text = "⏸ Пауза поиска" if is_active else "▶️ Возобновить поиск"
        builder.button(text=toggle_text, callback_data="toggle_status")
        builder.button(text="🗂 Моя анкета", callback_data="my_profile")
        builder.button(text="✏️ Редактировать анкету", callback_data="edit_profile")
    else:
        builder.button(text="📝 Создать анкету", callback_data="create_profile")
    builder.adjust(1)
    return builder.as_markup()


# ── Profile creation / editing steps ─────────────────────────────────────────
def kb_cancel() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Отмена", callback_data="cancel")
    return builder.as_markup()


def kb_skip_cancel() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="➡️ Пропустить", callback_data="skip_extra")
    builder.button(text="❌ Отмена", callback_data="cancel")
    builder.adjust(2)
    return builder.as_markup()


# ── Rank picker (paginated, 12 per page) ─────────────────────────────────────
RANKS_PER_PAGE = 12


def kb_rank_picker(page: int = 0) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    start = page * RANKS_PER_PAGE
    end = min(start + RANKS_PER_PAGE, len(RANKS))
    for i in range(start, end):
        builder.button(text=RANKS[i], callback_data=f"rank:{i}")
    builder.adjust(3)
    # navigation
    nav: list[InlineKeyboardButton] = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="◀️ Назад", callback_data=f"rank_page:{page - 1}"))
    total_pages = (len(RANKS) + RANKS_PER_PAGE - 1) // RANKS_PER_PAGE
    nav.append(InlineKeyboardButton(text=f"{page + 1}/{total_pages}", callback_data="noop"))
    if end < len(RANKS):
        nav.append(InlineKeyboardButton(text="Вперёд ▶️", callback_data=f"rank_page:{page + 1}"))
    nav.append(InlineKeyboardButton(text="❌ Отмена", callback_data="cancel"))
    builder.row(*nav)
    return builder.as_markup()


# ── Goal picker ───────────────────────────────────────────────────────────────
def kb_goal() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for key, label in GOALS.items():
        builder.button(text=label, callback_data=f"goal:{key}")
    builder.button(text="❌ Отмена", callback_data="cancel")
    builder.adjust(2, 1)
    return builder.as_markup()


# ── Browse actions ────────────────────────────────────────────────────────────
def kb_browse() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="❤️", callback_data="vote:like")
    builder.button(text="👎", callback_data="vote:dislike")
    builder.button(text="🏠 Меню", callback_data="menu")
    builder.adjust(2, 1)
    return builder.as_markup()


# ── Match confirmation ────────────────────────────────────────────────────────
def kb_match_confirm(partner_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Начать диалог", callback_data=f"match_accept:{partner_id}")
    builder.button(text="❌ Нет, спасибо", callback_data="match_decline")
    builder.adjust(1)
    return builder.as_markup()


# ── My profile actions ────────────────────────────────────────────────────────
def kb_my_profile_actions(is_active: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    toggle_text = "⏸ Пауза поиска" if is_active else "▶️ Возобновить поиск"
    builder.button(text="✏️ Редактировать", callback_data="edit_profile")
    builder.button(text=toggle_text, callback_data="toggle_status")
    builder.button(text="🏠 Меню", callback_data="menu")
    builder.adjust(1)
    return builder.as_markup()
