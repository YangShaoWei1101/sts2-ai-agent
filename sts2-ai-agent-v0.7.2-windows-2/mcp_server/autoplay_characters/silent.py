from __future__ import annotations

from typing import Callable

from .base import normalize_id


SILENT_DISCARD_NOW_IDS = {
    "ACROBATICS",
    "CALCULATED_GAMBLE",
    "DAGGER_THROW",
    "HIDDEN_DAGGERS",
    "PREPARED",
    "SHADOW_STEP",
    "STORM_OF_STEEL",
    "SURVIVOR",
}
SILENT_DISCARD_ENGINE_IDS = {
    "MASTER_PLANNER",
    "TOOLS_OF_THE_TRADE",
}
SILENT_DISCARD_SCALING_IDS = {
    "MEMENTO_MORI",
}
SILENT_SLY_KEYWORD_IDS = {
    "ABRASIVE",
    "FLICK_FLACK",
    "HAZE",
    "HELIX_DRILL",
    "REFLEX",
    "RICOCHET",
    "SNEAKY",
    "TACTICIAN",
    "UNTOUCHABLE",
}
SILENT_SLY_RESOURCE_IDS = {
    "REFLEX",
    "TACTICIAN",
}
SILENT_WHOLE_HAND_DISCARD_IDS = {
    "CALCULATED_GAMBLE",
    "SHADOW_STEP",
    "STORM_OF_STEEL",
}
SILENT_BOSS_SURVIVAL_IDS = {
    "BACKFLIP",
    "BLUR",
    "CLOAK_AND_DAGGER",
    "DODGE_AND_ROLL",
    "FOOTWORK",
    "LEG_SWEEP",
    "MALAISE",
    "PIERCING_WAIL",
    "WRAITH_FORM",
}


def is_silent_sly_id(card_id: object) -> bool:
    return normalize_id(card_id) in SILENT_SLY_KEYWORD_IDS


def is_silent_sly_resource_id(card_id: object) -> bool:
    return normalize_id(card_id) in SILENT_SLY_RESOURCE_IDS


def is_silent_discard_now_id(card_id: object) -> bool:
    return normalize_id(card_id) in SILENT_DISCARD_NOW_IDS


def is_silent_whole_hand_discard_id(card_id: object) -> bool:
    return normalize_id(card_id) in SILENT_WHOLE_HAND_DISCARD_IDS


def silent_narrow_card_adjustment(
    card_id: object,
    roles: set[str] | frozenset[str],
    cost: int | None,
    archetype_count: Callable[[str], int],
    role_count: Callable[[str], int],
    reasons: list[str],
) -> float:
    cid = normalize_id(card_id)
    discard_count = archetype_count("si_discard_sly") + role_count("discard")
    score = 0.0

    if cid in {"ACCURACY"} and archetype_count("si_shiv") < 2:
        score -= 18
        reasons.append("accuracy-needs-shivs")
    if "poison" in roles and cid in {"ACCELERANT", "OUTBREAK", "MIRAGE"} and archetype_count("si_poison") < 2:
        score -= 12
        reasons.append("poison-payoff-too-early")
    if "shiv" in roles and cid in {"KNIFE_TRAP", "FAN_OF_KNIVES", "PHANTOM_BLADES"} and archetype_count("si_shiv") < 2:
        score -= 10
        reasons.append("shiv-payoff-too-early")

    if cid in {"PREPARED", "DAGGER_THROW", "ACROBATICS", "SURVIVOR", "TOOLS_OF_THE_TRADE"}:
        score += 8
        reasons.append("silent-discard-outlet")
        if cid == "DAGGER_THROW" and discard_count >= 5 and role_count("attack") >= role_count("block") + 2:
            score -= 10
            reasons.append("silent-attack-density")
    if cid in SILENT_BOSS_SURVIVAL_IDS:
        score += 10
        reasons.append("silent-boss-survival")
        if role_count("block") < 8 or role_count("power_scaling") == 0:
            score += 6
            reasons.append("silent-stabilize-defense")
    if cid in {"BLUR", "DODGE_AND_ROLL"} and role_count("block") < 9:
        score += 6
        reasons.append("silent-layered-block")
    if cid in {"PIERCING_WAIL", "LEG_SWEEP", "MALAISE"}:
        score += 8
        reasons.append("silent-boss-debuff")
    if cid == "FOOTWORK":
        score += 8 + min(8, role_count("block"))
        reasons.append("silent-dex-scaling")
    if cid in {"CALCULATED_GAMBLE", "HIDDEN_DAGGERS"}:
        score += 5 if discard_count >= 2 else 1
        reasons.append("silent-discard-cycle")
    if cid in {"TACTICIAN", "REFLEX"}:
        if discard_count >= 2:
            score += 18
            reasons.append("sly-resource-supported")
        elif discard_count >= 1:
            score += 6
            reasons.append("sly-resource-speculative")
        else:
            score -= 14
            reasons.append("sly-resource-needs-outlet")
    if cid in {"MEMENTO_MORI", "STORM_OF_STEEL", "SHADOW_STEP"}:
        if discard_count >= 2:
            score += 10
            reasons.append("discard-payoff-supported")
        else:
            score -= 8
            reasons.append("discard-payoff-too-early")
    if cid in {"MASTER_PLANNER", "HAND_TRICK"}:
        score += 7 if discard_count >= 1 else 1
        reasons.append("sly-enabler")
    return score
