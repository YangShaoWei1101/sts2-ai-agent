from __future__ import annotations

from typing import Callable

from .base import normalize_id


IRONCLAD_RELIABLE_DAMAGE_IDS = {
    "ANGER",
    "BLOOD_FOR_BLOOD",
    "CARNAGE",
    "CLEAVE",
    "FEED",
    "HEAVY_BLADE",
    "POMMEL_STRIKE",
    "REAPER",
    "SWORD_BOOMERANG",
    "TWIN_STRIKE",
    "UPPERCUT",
    "WHIRLWIND",
}

IRONCLAD_SLOW_ATTACK_IDS = {
    "PERFECTED_STRIKE",
}

IRONCLAD_BLOCK_CORE_IDS = {
    "FLAME_BARRIER",
    "GHOSTLY_ARMOR",
    "IMPERVIOUS",
    "POWER_THROUGH",
    "RAGE",
    "SHRUG_IT_OFF",
    "TRUE_GRIT",
}

IRONCLAD_EXHAUST_CORE_IDS = {
    "BURNING_PACT",
    "CORRUPTION",
    "DARK_EMBRACE",
    "FEEL_NO_PAIN",
    "FIEND_FIRE",
    "SECOND_WIND",
    "SEVER_SOUL",
    "TRUE_GRIT",
}

IRONCLAD_SLOW_ENGINE_IDS = {
    "BARRICADE",
    "CORRUPTION",
    "DARK_EMBRACE",
    "DEMON_FORM",
}


def ironclad_narrow_card_adjustment(
    card_id: object,
    roles: set[str] | frozenset[str],
    cost: int | None,
    archetype_count: Callable[[str], int],
    role_count: Callable[[str], int],
    reasons: list[str],
) -> float:
    cid = normalize_id(card_id)
    score = 0.0
    real_damage_shell = (
        archetype_count("ic_vulnerable_burst")
        + archetype_count("ic_attack_chain")
        + role_count("strength")
    )
    exhaust_shell = archetype_count("ic_exhaust_engine") + role_count("exhaust")
    block_shell = archetype_count("ic_block_body_slam") + role_count("block")

    if cid in IRONCLAD_RELIABLE_DAMAGE_IDS and real_damage_shell < 3:
        score += 12
        reasons.append("ironclad-needs-real-damage")
    if cid in {"POMMEL_STRIKE", "UPPERCUT"}:
        score += 6
        reasons.append("ironclad-tempo-core")
    if cid in IRONCLAD_SLOW_ATTACK_IDS:
        score -= 28
        reasons.append("ironclad-slow-strike-package")
    if cid in IRONCLAD_BLOCK_CORE_IDS and block_shell < 6:
        score += 8
        reasons.append("ironclad-stabilize-block")
    if cid in {"FEEL_NO_PAIN", "DARK_EMBRACE", "CORRUPTION"} and exhaust_shell >= 3:
        score += 10
        reasons.append("ironclad-exhaust-engine")
    if cid in IRONCLAD_SLOW_ENGINE_IDS and exhaust_shell < 2 and real_damage_shell < 2:
        score -= 28
        reasons.append("ironclad-slow-engine-too-early")
    if cid == "BARRICADE" and block_shell < 5:
        score -= 14
        reasons.append("barricade-needs-block-density")
    if cid == "ENTRENCH" and block_shell < 5:
        score -= 12
        reasons.append("entrench-needs-block-density")
    if cost is not None and cost >= 3 and real_damage_shell < 2 and cid not in {"CARNAGE", "WHIRLWIND"}:
        score -= 6
        reasons.append("ironclad-expensive-before-core")
    return score
