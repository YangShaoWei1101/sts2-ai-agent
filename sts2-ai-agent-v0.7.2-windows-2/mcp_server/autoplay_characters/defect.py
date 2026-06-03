from __future__ import annotations

from typing import Callable

from .base import normalize_id


DEFECT_FROST_BLOCK_IDS = {
    "CHILL",
    "COLD_SNAP",
    "COOLHEADED",
    "GLACIER",
    "HAILSTORM",
    "LIGHTNING_ROD",
}
DEFECT_FOCUS_IDS = {
    "BIASED_COGNITION",
    "DEFRAGMENT",
    "FOCUS",
    "HOTFIX",
}
DEFECT_ORB_ENGINE_IDS = {
    "CAPACITOR",
    "ELECTRODYNAMICS",
    "HAILSTORM",
    "ITERATION",
    "LOOP",
    "STORM",
    "THUNDER",
}
DEFECT_ATTACK_PAYOFF_IDS = {
    "FOCUSED_STRIKE",
    "ROCKET_PUNCH",
    "SHATTER",
    "SUNDER",
    "SYNTHESIS",
}
DEFECT_ZERO_ATTACK_IDS = {
    "ALL_FOR_ONE",
    "CLAW",
    "SCRAPE",
}


def defect_narrow_card_adjustment(
    card_id: object,
    roles: set[str] | frozenset[str],
    cost: int | None,
    archetype_count: Callable[[str], int],
    role_count: Callable[[str], int],
    reasons: list[str],
) -> float:
    cid = normalize_id(card_id)
    score = 0.0
    orb_count = archetype_count("de_orb_focus") + archetype_count("de_frost_defense")
    frost_count = archetype_count("de_frost_defense")
    block_count = role_count("block")
    draw_count = role_count("draw")
    focus_count = role_count("focus") + archetype_count("de_power_engine")
    cleanup_count = role_count("status_cleanup") + archetype_count("de_status_engine")

    if cid == "BUFFER":
        score += 22
        reasons.append("defect-boss-survival")
        if block_count < 7:
            score += 8
            reasons.append("defect-buffer-covers-block-gap")
        if orb_count >= 2:
            score += 4
            reasons.append("defect-power-shell")
    if cid == "BOOT_SEQUENCE":
        score += 10
        reasons.append("defect-innate-boss-block")
    if cid == "CHARGE_BATTERY":
        score += 6
        reasons.append("defect-block-energy")
    if cid == "GLASSWORK":
        score += 8
        reasons.append("defect-orb-block-core")

    if cid == "COOLHEADED":
        score += 14
        reasons.append("defect-frost-draw")
        if draw_count < 3:
            score += 6
            reasons.append("defect-needs-cycle")
    elif cid in {"CHILL", "GLACIER"}:
        score += 12
        reasons.append("defect-frost-core")
    elif cid in {"COLD_SNAP", "LIGHTNING_ROD"}:
        score += 8
        reasons.append("defect-orb-block")
        if block_count < 6:
            score += 6
            reasons.append("defect-needs-block")

    if cid in DEFECT_FOCUS_IDS:
        score += 16 if orb_count else 8
        reasons.append("defect-focus-engine")
    if cid in DEFECT_ORB_ENGINE_IDS and orb_count >= 2:
        score += 8
        reasons.append("defect-orb-engine")

    if cid in {"BOOT_SEQUENCE", "CHARGE_BATTERY", "LEAP", "REINFORCED_BODY", "STACK"} and block_count < 7:
        score += 8
        reasons.append("defect-block-gap")

    if cid == "HAILSTORM" and block_count < 7:
        score -= 10
        reasons.append("defect-defense-before-damage-power")

    if cid in DEFECT_ATTACK_PAYOFF_IDS and orb_count >= 2 and block_count < 6:
        score -= 12
        reasons.append("defect-support-before-payoff")
    if cid in DEFECT_ZERO_ATTACK_IDS and archetype_count("de_zero_claw") < 3 and orb_count >= 2:
        score -= 10
        reasons.append("defect-zero-payoff-too-early")
    if cid == "SHATTER" and focus_count == 0 and frost_count < 2:
        score -= 10
        reasons.append("shatter-needs-orb-shell")
    if "status_pollution" in roles and cleanup_count < 2:
        penalty = 24
        if block_count < 6 or draw_count < 3 or focus_count == 0:
            penalty += 14
        score -= penalty
        reasons.append("defect-avoid-junk-without-cleanup")
    return score
