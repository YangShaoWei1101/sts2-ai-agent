from __future__ import annotations

from typing import Callable

from .base import normalize_id


NECROBINDER_OSTY_CORE_IDS = {
    "AFTERLIFE",
    "BODYGUARD",
    "BONE_SHARDS",
    "CALCIFY",
    "CLEANSE",
    "DIRGE",
    "FETCH",
    "FLATTEN",
    "GRAVE_WARDEN",
    "HIGH_FIVE",
    "INVOKE",
    "NECRO_MASTERY",
    "POKE",
    "PULL_AGGRO",
    "RATTLE",
    "REAVE",
    "RIGHT_HAND_HAND",
    "SACRIFICE",
    "SIC_EM",
    "SNAP",
    "SPUR",
    "UNLEASH",
}
NECROBINDER_DOOM_CORE_IDS = {
    "BLIGHT_STRIKE",
    "COUNTDOWN",
    "DEATHBRINGER",
    "DEATHS_DOOR",
    "END_OF_DAYS",
    "NEGATIVE_PULSE",
    "NEUROSURGE",
    "NO_ESCAPE",
    "OBLIVION",
    "REAPER_FORM",
    "SCOURGE",
    "SHROUD",
    "TIMES_UP",
}
NECROBINDER_ETHEREAL_CORE_IDS = {
    "BANSHEES_CRY",
    "CALL_OF_THE_VOID",
    "DEFILE",
    "DEFY",
    "DEMESNE",
    "ENFEEBLING_TOUCH",
    "FEAR",
    "LETHALITY",
    "PAGESTORM",
    "PARSE",
    "PULL_FROM_BELOW",
    "SCULPTING_STRIKE",
    "SPIRIT_OF_ASH",
    "VEILPIERCER",
}


def necrobinder_narrow_card_adjustment(
    card_id: object,
    roles: set[str] | frozenset[str],
    cost: int | None,
    archetype_count: Callable[[str], int],
    role_count: Callable[[str], int],
    reasons: list[str],
) -> float:
    cid = normalize_id(card_id)
    osty_count = archetype_count("nb_osty_summon") + role_count("summon_osty")
    doom_count = archetype_count("nb_doom") + role_count("doom")
    ethereal_count = archetype_count("nb_ethereal_soul") + role_count("ethereal")
    block_count = role_count("block")
    draw_count = role_count("draw")
    score = 0.0

    if cid == "GRAVE_WARDEN":
        score += 16
        reasons.append("necrobinder-osty-block-draw")
        if block_count < 6 or draw_count < 2:
            score += 8
            reasons.append("necrobinder-fills-core-gap")
    elif cid in {"AFTERLIFE", "PULL_AGGRO", "CLEANSE", "SPUR"}:
        score += 8 if osty_count >= 2 else 3
        reasons.append("necrobinder-osty-support")
    elif cid in {"FETCH", "REAVE", "SNAP", "POKE"}:
        score += 8 if osty_count >= 2 else 2
        reasons.append("necrobinder-osty-tempo")
    elif cid in {"BONE_SHARDS", "HIGH_FIVE", "RATTLE", "SIC_EM"}:
        score += 10 if osty_count >= 2 else 1
        reasons.append("necrobinder-osty-payoff")

    if cid in {"SCOURGE", "NEGATIVE_PULSE", "DEATHS_DOOR", "SHROUD"}:
        if doom_count >= 2:
            score += 10
            reasons.append("necrobinder-doom-shell")
        elif osty_count >= 2 and doom_count == 0:
            score -= 36
            reasons.append("necrobinder-doom-off-opener")
    if cid in {"COUNTDOWN", "DEATHBRINGER", "REAPER_FORM"} and doom_count < 2:
        score -= 8
        reasons.append("necrobinder-doom-engine-too-early")

    if cid in {"DEFY", "PARSE", "PAGESTORM", "SPIRIT_OF_ASH"}:
        score += 8 if ethereal_count >= 2 else 2
        reasons.append("necrobinder-ethereal-shell")
    if cid in {"ENFEEBLING_TOUCH", "FEAR", "VEILPIERCER"} and ethereal_count == 0 and osty_count >= 2:
        score -= 6
        reasons.append("necrobinder-ethereal-off-opener")
    return score
