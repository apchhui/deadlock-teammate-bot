from __future__ import annotations
from typing import Optional
from .constants import RANKS, GOALS


GOAL_EMOJI = {"rank": "📈", "fun": "🎮"}


def format_profile(
    game_id: str,
    rank_index: int,
    timezone: str,
    heroes: str,
    goal: str,
    extra: Optional[str],
    tg_username: Optional[str] = None,
    is_own: bool = False,
) -> str:
    rank_name = RANKS[rank_index]
    goal_label = GOALS.get(goal, goal)
    header = "🗂 <b>Твоя анкета</b>" if is_own else "🃏 <b>Анкета тиммейта</b>"

    lines = [
        header,
        "",
        f"🎮  <b>Steam ID / ник:</b>  <code>{game_id}</code>",
        f"🏆  <b>Ранг:</b>  {rank_name}",
        f"🕐  <b>Часовой пояс:</b>  {timezone}",
        f"🦸  <b>Пул героев:</b>  {heroes}",
        f"🎯  <b>Цель:</b>  {goal_label}",
    ]

    if extra:
        lines.append(f"💬  <b>О себе:</b>  {extra}")

    if tg_username and not is_own:
        lines.append(f"\n📎  <b>Telegram:</b>  @{tg_username}")

    return "\n".join(lines)


EXAMPLE_PROFILE = """
<b>📋 Пример анкеты:</b>

🎮  <b>Steam ID / ник:</b>  <code>76561198012345678</code>
🏆  <b>Ранг:</b>  Oracle 4
🕐  <b>Часовой пояс:</b>  МСК+0
🦸  <b>Пул героев:</b>  Haze, Seven, Wraith
🎯  <b>Цель:</b>  📈 Рейтинг
💬  <b>О себе:</b>  Играю вечерами, общаюсь в войс, токс — мимо

<i>Так будет выглядеть твоя анкета для других игроков.</i>
"""
