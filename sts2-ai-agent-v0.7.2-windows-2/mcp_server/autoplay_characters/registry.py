from __future__ import annotations

from typing import Callable

from .base import CHARACTER_COLOR, STARTER_UPGRADE_HINTS, CharacterStrategy, character_strategy, normalize_id, register_strategy
from .defect import defect_narrow_card_adjustment
from .ironclad import ironclad_narrow_card_adjustment
from .necrobinder import necrobinder_narrow_card_adjustment
from .silent import silent_narrow_card_adjustment


ARCHETYPE_PRIORITIES = {
    "IRONCLAD": (
        "ic_exhaust_engine",
        "ic_vulnerable_burst",
        "ic_block_body_slam",
        "ic_self_damage_strength",
        "ic_attack_chain",
    ),
    "SILENT": (
        "si_discard_sly",
        "si_draw_skill_chain",
        "si_shiv",
        "si_poison",
        "si_defense_control",
    ),
    "DEFECT": (
        "de_orb_focus",
        "de_frost_defense",
        "de_power_engine",
        "de_zero_claw",
        "de_status_engine",
    ),
    "NECROBINDER": (
        "nb_osty_summon",
        "nb_ethereal_soul",
        "nb_doom",
        "nb_debuff_control",
    ),
    "REGENT": (
        "rg_star_resource",
        "rg_forge_blade",
        "rg_created_cards",
        "rg_skill_chain",
        "rg_strength_control",
    ),
}


def generic_narrow_card_adjustment(
    card_id: object,
    roles: set[str] | frozenset[str],
    cost: int | None,
    archetype_count: Callable[[str], int],
    role_count: Callable[[str], int],
    reasons: list[str],
) -> float:
    cid = normalize_id(card_id)
    score = 0.0

    if cid == "BODY_SLAM" and archetype_count("ic_block_body_slam") < 3:
        score -= 16
        reasons.append("body-slam-needs-block")
    if cid in {"TIMES_UP", "END_OF_DAYS"} and archetype_count("nb_doom") < 3:
        score -= 16
        reasons.append("doom-payoff-too-early")
    if cid in {"SEEKING_EDGE", "SWORD_SAGE", "PARRY"} and archetype_count("rg_forge_blade") < 3:
        score -= 10
        reasons.append("blade-payoff-too-early")
    if "star_resource" in roles and cost is not None and cost >= 2 and archetype_count("rg_star_resource") < 3:
        score -= 8
        reasons.append("star-spender-needs-economy")
    return score


def _combined_adjuster(character_adjuster: Callable[..., float] | None = None) -> Callable[..., float]:
    def adjust(
        card_id: object,
        roles: set[str] | frozenset[str],
        cost: int | None,
        archetype_count: Callable[[str], int],
        role_count: Callable[[str], int],
        reasons: list[str],
    ) -> float:
        score = generic_narrow_card_adjustment(card_id, roles, cost, archetype_count, role_count, reasons)
        if character_adjuster is not None:
            score += character_adjuster(card_id, roles, cost, archetype_count, role_count, reasons)
        return score

    return adjust


for _character_id, _color in CHARACTER_COLOR.items():
    _adjuster = None
    if _character_id == "IRONCLAD":
        _adjuster = ironclad_narrow_card_adjustment
    elif _character_id == "SILENT":
        _adjuster = silent_narrow_card_adjustment
    elif _character_id == "DEFECT":
        _adjuster = defect_narrow_card_adjustment
    elif _character_id == "NECROBINDER":
        _adjuster = necrobinder_narrow_card_adjustment
    register_strategy(
        CharacterStrategy(
            character_id=_character_id,
            color=_color,
            archetype_priorities=ARCHETYPE_PRIORITIES.get(_character_id, ()),
            starter_upgrade_hints=STARTER_UPGRADE_HINTS,
            narrow_adjuster=_combined_adjuster(_adjuster),
        )
    )


def archetype_priority(character_id: object) -> tuple[str, ...]:
    return character_strategy(character_id).archetype_priority()


def narrow_card_adjustment(
    card_id: object,
    roles: set[str] | frozenset[str],
    cost: int | None,
    character_id: object,
    archetype_count: Callable[[str], int],
    role_count: Callable[[str], int],
    reasons: list[str],
) -> float:
    return character_strategy(character_id).narrow_card_adjustment(
        card_id,
        roles,
        cost,
        archetype_count,
        role_count,
        reasons,
    )
