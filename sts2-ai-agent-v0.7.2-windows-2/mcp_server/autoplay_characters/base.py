from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


def normalize_id(value: object) -> str:
    return str(value or "").strip().upper().replace(" ", "_")


MAJOR_ARCHETYPE_PREFIXES = {
    "IRONCLAD": "ic_",
    "SILENT": "si_",
    "DEFECT": "de_",
    "NECROBINDER": "nb_",
    "REGENT": "rg_",
}

CHARACTER_COLOR = {
    "IRONCLAD": "ironclad",
    "SILENT": "silent",
    "DEFECT": "defect",
    "NECROBINDER": "necrobinder",
    "REGENT": "regent",
}

ARCHETYPE_STRENGTH_BONUS = {
    "ic_exhaust_engine": 6,
    "ic_vulnerable_burst": 4,
    "ic_block_body_slam": 3,
    "si_discard_sly": 7,
    "si_draw_skill_chain": 5,
    "si_shiv": 4,
    "si_poison": 2,
    "de_orb_focus": 7,
    "de_frost_defense": 6,
    "de_power_engine": 5,
    "de_zero_claw": 2,
    "nb_osty_summon": 6,
    "nb_ethereal_soul": 5,
    "nb_doom": 3,
    "rg_star_resource": 6,
    "rg_forge_blade": 4,
    "rg_skill_chain": 4,
}

STARTER_UPGRADE_HINTS = {
    "BASH": 34,
    "NEUTRALIZE": 26,
    "SURVIVOR": 16,
    "ZAP": 22,
    "DUALCAST": 18,
    "BODYGUARD": 18,
    "UNLEASH": 18,
    "FALLING_STAR": 24,
    "VENERATE": 20,
}

BASIC_STRIKE_IDS = {
    "STRIKE",
    "STRIKE_IRONCLAD",
    "STRIKE_SILENT",
    "STRIKE_DEFECT",
    "STRIKE_NECROBINDER",
    "STRIKE_REGENT",
}
BASIC_DEFEND_IDS = {
    "DEFEND",
    "DEFEND_IRONCLAD",
    "DEFEND_SILENT",
    "DEFEND_DEFECT",
    "DEFEND_NECROBINDER",
    "DEFEND_REGENT",
}


@dataclass(frozen=True)
class CharacterStrategy:
    character_id: str
    color: str | None = None
    archetype_priorities: tuple[str, ...] = ()
    starter_upgrade_hints: dict[str, int] | None = None
    narrow_adjuster: Callable[..., float] | None = None

    def archetype_priority(self) -> tuple[str, ...]:
        return self.archetype_priorities

    def starter_upgrade_hint(self, card_id: object) -> int:
        hints = self.starter_upgrade_hints or {}
        return hints.get(normalize_id(card_id), 0)

    def narrow_card_adjustment(
        self,
        card_id: object,
        roles: set[str] | frozenset[str],
        cost: int | None,
        archetype_count: Callable[[str], int],
        role_count: Callable[[str], int],
        reasons: list[str],
    ) -> float:
        if self.narrow_adjuster is None:
            return 0.0
        return self.narrow_adjuster(card_id, roles, cost, archetype_count, role_count, reasons)


CHARACTER_STRATEGIES: dict[str, CharacterStrategy] = {}


def register_strategy(strategy: CharacterStrategy) -> CharacterStrategy:
    CHARACTER_STRATEGIES[normalize_id(strategy.character_id)] = strategy
    return strategy


def character_strategy(character_id: object) -> CharacterStrategy:
    normalized = normalize_id(character_id)
    return CHARACTER_STRATEGIES.get(normalized) or CharacterStrategy(character_id=normalized or "UNKNOWN")


def character_color(character_id: object) -> str | None:
    return character_strategy(character_id).color


def archetype_strength_bonus(archetype: object) -> int:
    return ARCHETYPE_STRENGTH_BONUS.get(str(archetype or ""), 0)


def starter_upgrade_hint(card_id: object) -> int:
    return STARTER_UPGRADE_HINTS.get(normalize_id(card_id), 0)


def is_basic_strike_id(card_id: object) -> bool:
    return normalize_id(card_id) in BASIC_STRIKE_IDS


def is_basic_defend_id(card_id: object) -> bool:
    return normalize_id(card_id) in BASIC_DEFEND_IDS


def is_basic_card_id(card_id: object) -> bool:
    card_id = normalize_id(card_id)
    return card_id in BASIC_STRIKE_IDS or card_id in BASIC_DEFEND_IDS
