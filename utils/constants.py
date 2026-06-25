from __future__ import annotations

# ── Deadlock rank ladder ──────────────────────────────────────────────────────
RANKS: list[str] = [
    "Initiate 1",  "Initiate 2",  "Initiate 3",
    "Initiate 4",  "Initiate 5",  "Initiate 6",
    "Seeker 1",    "Seeker 2",    "Seeker 3",
    "Seeker 4",    "Seeker 5",    "Seeker 6",
    "Alchemist 1", "Alchemist 2", "Alchemist 3",
    "Alchemist 4", "Alchemist 5", "Alchemist 6",
    "Arcanist 1",  "Arcanist 2",  "Arcanist 3",
    "Arcanist 4",  "Arcanist 5",  "Arcanist 6",
    "Ritualist 1", "Ritualist 2", "Ritualist 3",
    "Ritualist 4", "Ritualist 5", "Ritualist 6",
    "Emissary 1",  "Emissary 2",  "Emissary 3",
    "Emissary 4",  "Emissary 5",  "Emissary 6",
    "Archon 1",    "Archon 2",    "Archon 3",
    "Archon 4",    "Archon 5",    "Archon 6",
    "Oracle 1",    "Oracle 2",    "Oracle 3",
    "Oracle 4",    "Oracle 5",    "Oracle 6",
    "Phantom 1",   "Phantom 2",   "Phantom 3",
    "Phantom 4",   "Phantom 5",   "Phantom 6",
    "Ascendant 1", "Ascendant 2", "Ascendant 3",
    "Ascendant 4", "Ascendant 5", "Ascendant 6",
    "Eternus 1",   "Eternus 2",   "Eternus 3",
    "Eternus 4",   "Eternus 5",   "Eternus 6",
]

# Tier names only (without the digit suffix) – used for range calculation
TIER_NAMES: list[str] = [
    "Initiate", "Seeker", "Alchemist", "Arcanist",
    "Ritualist", "Emissary", "Archon", "Oracle",
    "Phantom", "Ascendant", "Eternus",
]

TIER_SIZE = 6  # ranks per tier


def rank_range(rank_index: int, spread: int = 1) -> tuple[int, int]:
    """Return (min_index, max_index) for ±spread tiers around rank_index."""
    tier = rank_index // TIER_SIZE
    lo = max(0, tier - spread) * TIER_SIZE
    hi = min(len(TIER_NAMES) - 1, tier + spread) * TIER_SIZE + (TIER_SIZE - 1)
    return lo, min(hi, len(RANKS) - 1)


# ── Goals ─────────────────────────────────────────────────────────────────────
GOALS: dict[str, str] = {
    "rank": "📈 Рейтинг",
    "fun":  "🎮 По фану",
}

# ── Popular heroes list (for hint in UI) ──────────────────────────────────────
HEROES_HINT = (
    "Haze, Abrams, Bebop, Dynamo, Grey Talon, Ivy, Kelvin, Lady Geist, "
    "Lash, McGinnis, Mo & Krill, Paradox, Pocket, Seven, Shiv, "
    "Vindicta, Viscous, Warden, Wraith, Yamato"
)
