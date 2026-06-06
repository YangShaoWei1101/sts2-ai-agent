from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from autoplay_strategy import CARD_KNOWLEDGE


RELICS_PATH = Path(__file__).resolve().with_name("data") / "eng" / "relics.json"

START_DRAW_RELICS = {
    "BAG_OF_PREPARATION",
    "RING_OF_THE_SNAKE",
    "RING_OF_THE_DRAKE",
    "SNECKO_EYE",
}
THIN_DECK_RELICS = {
    "BIIIG_HUG",
    "EMPTY_CAGE",
    "PAELS_TOOTH",
    "PRECARIOUS_SHEARS",
    "PRECISE_SCISSORS",
    "PRESERVED_FOG",
}
ON_PICKUP_REMOVE_RELICS = set(THIN_DECK_RELICS)
ATTACK_CHAIN_RELICS = {
    "AKABEKO",
    "BAG_OF_MARBLES",
    "BOOK_OF_FIVE_RINGS",
    "DAUGHTER_OF_THE_WIND",
    "KUNAI",
    "NINJA_SCROLL",
    "NUNCHAKU",
    "ORNAMENTAL_FAN",
    "PEN_NIB",
    "SHURIKEN",
    "STRIKE_DUMMY",
}
SKILL_CHAIN_RELICS = {"LETTER_OPENER", "BURNING_STICKS"}
DISCARD_RELICS = {"GAMBLING_CHIP", "TINGSHA", "TOUGH_BANDAGES"}
ORB_RELICS = {"CRACKED_CORE", "DATA_DISK", "RUNIC_CAPACITOR", "SYMBIOTIC_VIRUS"}
ENERGY_RELICS = {
    "BLESSED_ANTLER",
    "BREAD",
    "ECTOPLASM",
    "HAPPY_FLOWER",
    "ICE_CREAM",
    "LANTERN",
    "PHILOSOPHERS_STONE",
    "PRISMATIC_GEM",
    "SOZU",
    "VELVET_CHOKER",
    "VENERABLE_TEA_SET",
    "VERY_HOT_COCOA",
}
SHOP_VALUE_RELICS = {"THE_COURIER", "MEMBERSHIP_CARD", "MEAL_TICKET", "MAW_BANK"}
REST_VALUE_RELICS = {
    "ETERNAL_FEATHER",
    "GIRYA",
    "MEAT_CLEAVER",
    "MINIATURE_TENT",
    "REGAL_PILLOW",
    "SHOVEL",
    "STONE_HUMIDIFIER",
    "TINY_MAILBOX",
    "VENERABLE_TEA_SET",
}
ELITE_VALUE_RELICS = {"BLACK_STAR", "SLING_OF_COURAGE", "SWORD_OF_STONE", "WHITE_STAR"}
CARD_REWARD_RELICS = {
    "DINGY_RUG",
    "DRIFTWOOD",
    "GLITTER",
    "LAVA_LAMP",
    "PRAYER_WHEEL",
    "PRISMATIC_GEM",
    "SILVER_CRUCIBLE",
    "WHITE_STAR",
    "WING_CHARM",
}
CARD_DUPLICATING_RELICS = {"BING_BONG"}
POTION_RELICS = {"ALCHEMICAL_COFFER", "CAULDRON", "DELICATE_FROND", "POTION_BELT", "WHITE_BEAST_STATUE"}
START_BLOCK_RELICS = {"ANCHOR"}
START_RESOURCE_RELICS = {"DIVINE_RIGHT", "LANTERN", "VENERABLE_TEA_SET"}
START_SCALING_RELICS = {"SPARKLING_ROUGE", "DATA_DISK"}
SUMMON_RELICS = {"BOUND_PHYLACTERY", "VITRUVIAN_MINION"}
CARD_QUALITY_RELICS = THIN_DECK_RELICS | {
    "ARCANE_SCROLL",
    "ARCHAIC_TOOTH",
    "ASTROLABE",
    "EMPTY_CAGE",
    "LEAFY_POULTICE",
    "PANDORAS_BOX",
}
SUSTAIN_RELICS = {"BLOOD_VIAL", "BURNING_BLOOD", "CHOSEN_CHEESE", "MEAL_TICKET", "REGAL_PILLOW"}
HP_COST_RELICS = {"LEAFY_POULTICE", "PRECARIOUS_SHEARS"}


@dataclass(frozen=True)
class RelicProfile:
    ids: frozenset[str]
    tags: frozenset[str]
    combat_strength: float
    route_aggression: float
    shop_strength: float
    rest_strength: float
    removal_pressure: float
    reward_selectivity: float
    draw_support: int
    energy_support: int
    discard_support: int
    reasons: tuple[str, ...]

    def has(self, *ids: str) -> bool:
        return any(normalize_relic_id(relic_id) in self.ids for relic_id in ids)

    def summary(self) -> str:
        tags = ",".join(sorted(self.tags)[:8]) or "none"
        ids = ",".join(sorted(self.ids)[:8]) or "none"
        return f"ids={ids} tags={tags} combat={self.combat_strength:.1f} select={self.reward_selectivity:.1f}"


def normalize_relic_id(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    raw = raw.replace("-", "_").replace(" ", "_")
    if raw.upper() == raw:
        return raw.upper()
    raw = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", raw)
    raw = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", raw)
    return raw.upper()


def _first_number(value: Any) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return int(value)
    match = re.search(r"-?\d+", str(value))
    return int(match.group(0)) if match else None


def _text_blob(obj: Any) -> str:
    try:
        return json.dumps(obj, ensure_ascii=False).lower()
    except Exception:
        return str(obj).lower()


def _card_text(card: dict[str, Any] | None) -> str:
    if not isinstance(card, dict):
        return ""
    parts: list[str] = []
    for key in (
        "card_id",
        "id",
        "name",
        "rules_text",
        "resolved_rules_text",
        "description",
        "description_raw",
        "type",
        "card_type",
        "rarity",
    ):
        if card.get(key):
            parts.append(str(card.get(key)))
    for key in ("keywords", "keyword_ids", "tags", "mods"):
        value = card.get(key)
        if isinstance(value, list):
            parts.extend(str(item) for item in value if item)
        elif value:
            parts.append(str(value))
    return " ".join(parts).lower()


@lru_cache(maxsize=1)
def relic_catalog() -> dict[str, dict[str, Any]]:
    if not RELICS_PATH.exists():
        return {}
    raw = json.loads(RELICS_PATH.read_text(encoding="utf-8-sig"))
    catalog: dict[str, dict[str, Any]] = {}
    for relic in raw:
        if not isinstance(relic, dict):
            continue
        relic_id = normalize_relic_id(relic.get("id"))
        if relic_id:
            catalog[relic_id] = relic
    return catalog


@lru_cache(maxsize=1)
def _name_index() -> dict[str, str]:
    return {str(relic.get("name") or "").lower(): relic_id for relic_id, relic in relic_catalog().items()}


def current_relics(state: dict[str, Any]) -> list[dict[str, Any]]:
    run = state.get("run") or {}
    raw_relics = run.get("relics") or run.get("player_relics") or []
    if not isinstance(raw_relics, list):
        return []
    relics: list[dict[str, Any]] = []
    for relic in raw_relics:
        if isinstance(relic, dict):
            relics.append(relic)
        elif isinstance(relic, str):
            relic_id = _name_index().get(relic.lower(), "")
            relics.append({"id": relic_id, "name": relic})
    return relics


def current_relic_ids(state: dict[str, Any]) -> frozenset[str]:
    ids: set[str] = set()
    for relic in current_relics(state):
        if not isinstance(relic, dict):
            continue
        relic_id = normalize_relic_id(relic.get("relic_id") or relic.get("id"))
        if not relic_id:
            relic_id = _name_index().get(str(relic.get("name") or "").lower(), "")
        if relic_id:
            ids.add(relic_id)
    return frozenset(ids)


def relic_entry_for_item(item: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(item, dict):
        return None
    relic_id = normalize_relic_id(item.get("relic_id") or item.get("id") or item.get("internal_id"))
    if relic_id and relic_id in relic_catalog():
        return relic_catalog()[relic_id]
    name_id = _name_index().get(str(item.get("name") or "").lower())
    if name_id:
        return relic_catalog().get(name_id)
    return None


def _tags_for_relic(relic_id: str, entry: dict[str, Any] | None = None) -> set[str]:
    entry = entry or relic_catalog().get(relic_id) or {}
    text = " ".join(
        str(entry.get(key) or "") for key in ("id", "name", "description", "description_raw", "rarity", "pool")
    ).lower()
    tags: set[str] = set()
    if relic_id in START_DRAW_RELICS or "draw" in text:
        tags.add("draw")
    if relic_id in ENERGY_RELICS or "energy:" in text or "gain [energy" in text:
        tags.add("energy")
    if relic_id in START_RESOURCE_RELICS or "[star:" in text or "gain [star" in text:
        tags.add("energy")
        tags.add("starter_resource")
    if relic_id in DISCARD_RELICS or "discard" in text:
        tags.add("discard")
    if relic_id in ORB_RELICS or "channel" in text or "focus" in text or "orb" in text:
        tags.add("orb")
    if relic_id in ATTACK_CHAIN_RELICS or "attack" in text or "strength" in text or "vulnerable" in text:
        tags.add("attack")
    if relic_id in SKILL_CHAIN_RELICS or "skill" in text:
        tags.add("skill")
    if "block" in text or "dexterity" in text or "plating" in text:
        tags.add("block")
    if relic_id in START_BLOCK_RELICS or ("start" in text and "combat" in text and "block" in text):
        tags.add("block")
        tags.add("combat_start")
    if "damage to all enemies" in text or "deal" in text:
        tags.add("damage")
    if relic_id in START_SCALING_RELICS or "strength" in text or "dexterity" in text:
        tags.add("scaling")
    if relic_id in SUMMON_RELICS or "summon" in text:
        tags.add("summon")
    if relic_id in CARD_QUALITY_RELICS or ("upon pickup" in text and ("remove" in text or "transform" in text)):
        tags.add("card_quality")
    if relic_id in THIN_DECK_RELICS or "remove" in text:
        tags.add("removal")
    if "transform" in text:
        tags.add("transform")
    if relic_id in SHOP_VALUE_RELICS or "merchant" in text or "shop" in text or "shop relic" in text:
        tags.add("shop")
    if relic_id in REST_VALUE_RELICS or "rest site" in text or "rest]" in text:
        tags.add("rest")
    if relic_id in ELITE_VALUE_RELICS or "elite" in text:
        tags.add("elite")
    if relic_id in CARD_REWARD_RELICS or "card reward" in text:
        tags.add("card_reward")
    if relic_id in POTION_RELICS or "potion" in text:
        tags.add("potion")
    if "gold" in text or "drop" in text:
        tags.add("gold")
    if "boss" in text:
        tags.add("boss")
    if "x]" in text or " cost [blue]x" in text:
        tags.add("x_cost")
    if "start of each combat" in text or "start each combat" in text or "at the start of combat" in text:
        tags.add("combat_start")
    if relic_id in SUSTAIN_RELICS or ("end of combat" in text and "max hp" in text):
        tags.add("sustain")
    if "max hp" in text:
        tags.add("max_hp")
        if "lose" in text:
            tags.add("max_hp_loss")
    if relic_id in HP_COST_RELICS or ("take" in text and "damage" in text):
        tags.add("hp_cost")
    if "confused" in text:
        tags.add("random_cost")
    return tags


def relic_profile(state: dict[str, Any]) -> RelicProfile:
    ids = current_relic_ids(state)
    tags: set[str] = set()
    reasons: list[str] = []
    combat_strength = 0.0
    route_aggression = 0.0
    shop_strength = 0.0
    rest_strength = 0.0
    removal_pressure = 0.0
    reward_selectivity = 0.0
    draw_support = 0
    energy_support = 0
    discard_support = 0

    for relic_id in ids:
        relic_tags = _tags_for_relic(relic_id)
        tags.update(relic_tags)
        if "draw" in relic_tags:
            draw_support += 1
            combat_strength += 4.0
        if "energy" in relic_tags:
            energy_support += 1
            combat_strength += 5.0
        if "discard" in relic_tags:
            discard_support += 1
            combat_strength += 3.0
        if "attack" in relic_tags:
            combat_strength += 4.0
        if "block" in relic_tags:
            combat_strength += 3.0
        if "damage" in relic_tags:
            combat_strength += 3.0
        if "orb" in relic_tags:
            combat_strength += 4.0
        if "starter_resource" in relic_tags:
            combat_strength += 2.0
        if "combat_start" in relic_tags:
            combat_strength += 2.0
        if "summon" in relic_tags:
            combat_strength += 7.0
            route_aggression += 2.0
        if "scaling" in relic_tags:
            combat_strength += 4.0
            route_aggression += 2.0
        if "card_quality" in relic_tags:
            combat_strength += 2.0
            route_aggression += 3.0
            reward_selectivity += 4.0
            if relic_id not in ON_PICKUP_REMOVE_RELICS:
                removal_pressure += 5.0
        if "sustain" in relic_tags:
            route_aggression += 5.0
            rest_strength += 3.0
        if "shop" in relic_tags:
            shop_strength += 8.0
        if "rest" in relic_tags:
            rest_strength += 8.0
        if "elite" in relic_tags:
            route_aggression += 10.0
        if "removal" in relic_tags:
            if relic_id not in ON_PICKUP_REMOVE_RELICS:
                removal_pressure += 10.0
            reward_selectivity += 8.0
        if "card_reward" in relic_tags:
            reward_selectivity += 3.0

    if ids & START_DRAW_RELICS:
        reasons.append("opening-draw")
    if ids & THIN_DECK_RELICS:
        reasons.append("thin-deck")
    if ids & ATTACK_CHAIN_RELICS:
        reasons.append("attack-chain")
    if ids & DISCARD_RELICS:
        reasons.append("discard-payoff")
    if ids & ORB_RELICS:
        reasons.append("orb-payoff")
    if ids & SHOP_VALUE_RELICS:
        reasons.append("shop-payoff")
    if ids & REST_VALUE_RELICS:
        reasons.append("rest-payoff")
    if any("starter_resource" in _tags_for_relic(relic_id) for relic_id in ids):
        reasons.append("opening-resource")
    if any("summon" in _tags_for_relic(relic_id) for relic_id in ids):
        reasons.append("summon-engine")
    if any("card_quality" in _tags_for_relic(relic_id) for relic_id in ids):
        reasons.append("deck-quality")
    if any("sustain" in _tags_for_relic(relic_id) for relic_id in ids):
        reasons.append("combat-sustain")
    if "AMETHYST_AUBERGINE" in ids:
        route_aggression += 7.0
        shop_strength += 5.0
        reasons.append("combat-gold")
    if "STONE_CALENDAR" in ids:
        combat_strength += 8.0
        route_aggression += 3.0
        reasons.append("stall-payoff")
    if "BURNING_BLOOD" in ids or "BLOOD_VIAL" in ids:
        route_aggression += 3.0

    route_aggression += combat_strength * 0.25
    return RelicProfile(
        ids=ids,
        tags=frozenset(tags),
        combat_strength=combat_strength,
        route_aggression=route_aggression,
        shop_strength=shop_strength,
        rest_strength=rest_strength,
        removal_pressure=removal_pressure,
        reward_selectivity=reward_selectivity,
        draw_support=draw_support,
        energy_support=energy_support,
        discard_support=discard_support,
        reasons=tuple(reasons),
    )


def relic_summary(state: dict[str, Any]) -> str:
    return relic_profile(state).summary()


def _card_roles(card: dict[str, Any]) -> set[str]:
    known = CARD_KNOWLEDGE.lookup(card)
    roles = set(known.roles if known is not None else ())
    text = _card_text(card)
    card_type = str(card.get("card_type") or card.get("type") or "").lower()
    if card_type == "attack" or "attack" in text:
        roles.add("attack")
    if card_type == "skill" or "skill" in text:
        roles.add("skill")
    if card_type == "power" or "power" in text:
        roles.add("power_scaling")
    for role, tokens in {
        "draw": ("draw", "抽牌"),
        "energy": ("energy", "[e]", "能量"),
        "discard": ("discard", "丢弃", "弃牌"),
        "exhaust": ("exhaust", "消耗"),
        "block": ("block", "格挡"),
        "vulnerable": ("vulnerable", "易伤"),
        "weak": ("weak", "虚弱"),
        "shiv": ("shiv", "小刀"),
        "orb": ("channel", "orb", "lightning", "frost", "dark"),
        "focus": ("focus", "集中"),
        "doom": ("doom", "灾厄"),
        "summon_osty": ("summon", "召唤", "minion"),
    }.items():
        if any(token in text for token in tokens):
            roles.add(role)
    if card_costs_x(card):
        roles.add("x_cost")
    return roles


def card_costs_x(card: dict[str, Any]) -> bool:
    raw_cost = str(card.get("cost") or card.get("energy_cost") or card.get("display_cost") or "").strip().upper()
    return bool(card.get("is_x_cost") or card.get("costs_x") or raw_cost == "X" or "cost x" in _card_text(card))


def _card_cost(card: dict[str, Any]) -> int:
    amount = _first_number(card.get("energy_cost", card.get("cost")))
    return max(0, amount if amount is not None else 1)


def _deck_count(state: dict[str, Any], predicate) -> int:
    run = state.get("run") or {}
    deck = run.get("deck") or run.get("cards") or []
    count = 0
    for card in deck if isinstance(deck, list) else []:
        if isinstance(card, dict) and predicate(card):
            count += 1
    return count


def _deck_role_count(state: dict[str, Any], *roles: str) -> int:
    wanted = set(roles)
    return _deck_count(state, lambda card: bool(_card_roles(card) & wanted))


def _card_id(card: dict[str, Any]) -> str:
    known = CARD_KNOWLEDGE.lookup(card)
    if known is not None:
        return str(known.id or "").upper()
    for key in ("card_id", "id", "internal_id", "name"):
        raw = str(card.get(key) or "").strip()
        if raw:
            return raw.replace("-", "_").replace(" ", "_").upper()
    return ""


def relic_card_copy_penalty(
    card: dict[str, Any],
    state: dict[str, Any],
    roles: set[str],
    *,
    damage: int,
    block: int,
) -> tuple[float, list[str]]:
    profile = relic_profile(state)
    if not profile.has(*CARD_DUPLICATING_RELICS):
        return 0.0, []
    plan = CARD_KNOWLEDGE.deck_plan(state)
    if plan.card_count < 14:
        return 0.0, []
    cid = _card_id(card)
    duplicate_count = int(plan.ids.get(cid, 0) or 0)
    utility_roles = {
        "aoe",
        "block_retention",
        "debuff",
        "discard",
        "draw",
        "energy",
        "exhaust",
        "focus",
        "orb",
        "power_scaling",
        "status_cleanup",
        "vulnerable",
        "weak",
    }
    fills_need = bool(
        (plan.needs_damage and ("attack" in roles) and (damage >= 12 or "vulnerable" in roles or "aoe" in roles or card_costs_x(card)))
        or (plan.needs_block and ("block" in roles or "weak" in roles or block >= 8))
        or (plan.needs_draw and "draw" in roles)
        or (plan.needs_aoe and "aoe" in roles)
        or (plan.needs_scaling and "power_scaling" in roles)
    )
    low_impact = not bool(roles & utility_roles)
    penalty = 0.0
    if duplicate_count:
        penalty += 22.0 + min(30.0, duplicate_count * 10.0)
    if plan.card_count >= 18:
        penalty += 10.0
    if plan.card_count >= 22:
        penalty += 10.0
    if low_impact and not fills_need:
        penalty += 18.0
    if "attack" in roles and not plan.needs_damage and not (roles & {"aoe", "draw", "energy", "debuff", "vulnerable", "weak"}):
        penalty += 12.0
    if "block" in roles and not plan.needs_block and not (roles & {"draw", "weak", "block_retention"}):
        penalty += 8.0
    if fills_need:
        penalty -= 14.0
    if plan.needs_draw and "draw" in roles:
        penalty -= 18.0
    penalty = max(0.0, min(84.0, penalty))
    if not penalty:
        return 0.0, []
    return penalty, [f"relic-bing-bong-copy-risk={penalty:.0f}"]


def relic_damage_bonus(card: dict[str, Any], state: dict[str, Any], base_damage: int = 0) -> tuple[int, list[str]]:
    profile = relic_profile(state)
    roles = _card_roles(card)
    text = _card_text(card)
    bonus = 0
    reasons: list[str] = []
    if profile.has("STRIKE_DUMMY") and "strike" in text:
        bonus += 3
        reasons.append("relic-strike-dummy")
    if profile.has("VITRUVIAN_MINION") and ("minion" in text or "summon_osty" in roles):
        bonus += max(0, base_damage)
        reasons.append("relic-minion-double")
    if profile.has("MYSTIC_LIGHTER") and "attack" in roles and ("enchanted" in text or "enchant" in text):
        bonus += 9
        reasons.append("relic-enchanted-attack")
    for relic in current_relics(state):
        rid = normalize_relic_id(relic.get("relic_id") or relic.get("id"))
        if rid == "PEN_NIB":
            counter = _first_number(relic.get("counter") or relic.get("stack") or relic.get("value"))
            if counter is not None and counter >= 9 and "attack" in roles:
                bonus += max(0, base_damage)
                reasons.append("relic-pen-nib-ready")
    return bonus, reasons


def relic_combat_modifier(
    card: dict[str, Any],
    state: dict[str, Any],
    *,
    damage: int,
    block: int,
    cost: int,
    incoming: int,
    current_block: int,
    target_hp: int | None = None,
) -> tuple[float, list[str]]:
    profile = relic_profile(state)
    roles = _card_roles(card)
    text = _card_text(card)
    score = 0.0
    reasons: list[str] = []
    combat = state.get("combat") or {}
    turn = _first_number(combat.get("turn") or combat.get("turn_number") or combat.get("combat_turn")) or 1

    if "attack" in roles:
        if profile.has("BAG_OF_MARBLES") and turn <= 1:
            score += 7 if target_hp is None or target_hp > damage else 3
            reasons.append("relic-opening-vulnerable")
        if profile.has("AKABEKO") and turn <= 1:
            score += 8
            reasons.append("relic-opening-vigor")
        if profile.has("DAUGHTER_OF_THE_WIND") and incoming > current_block:
            score += 4
            reasons.append("relic-attack-block")
        if profile.has("SHURIKEN", "KUNAI", "ORNAMENTAL_FAN", "NUNCHAKU", "PEN_NIB"):
            score += 2.5 if cost <= 1 else 1.0
            reasons.append("relic-attack-chain")

    if turn <= 1 and "combat_start" in profile.tags and (damage or block):
        score += min(6.0, max(2.0, profile.combat_strength * 0.18))
        reasons.append("relic-opening-tempo")
    if "starter_resource" in profile.tags and (cost >= 2 or card_costs_x(card)):
        score += min(8.0, 3.0 + profile.energy_support * 2.0)
        reasons.append("relic-resource-support")
    if "summon" in profile.tags and (roles & {"summon_osty", "power_scaling"} or "summon" in text or "minion" in text):
        score += 8
        reasons.append("relic-summon-engine")
    if "scaling" in profile.tags and turn >= 3 and (damage or block):
        score += 2
        reasons.append("relic-delayed-scaling")

    if "skill" in roles and profile.has("LETTER_OPENER"):
        skills_played = _first_number(combat.get("skills_played_this_turn") or combat.get("skills_played")) or 0
        if (skills_played + 1) % 3 == 0:
            score += 18
            reasons.append("relic-letter-opener")
        elif cost <= 1:
            score += 3

    if "discard" in roles and profile.has("TOUGH_BANDAGES", "TINGSHA"):
        score += 14 if incoming > current_block else 8
        reasons.append("relic-discard-payoff")
    if card_costs_x(card) and profile.has("CHEMICAL_X"):
        score += 22
        reasons.append("relic-chemical-x")
    if profile.has("STONE_CALENDAR") and turn >= 6 and block and incoming > current_block:
        score += 10
        reasons.append("relic-stall-calendar")
    if profile.has("INTIMIDATING_HELMET") and cost >= 2:
        score += 5 if incoming > current_block else 2
        reasons.append("relic-expensive-block")
    if profile.has("IVORY_TILE") and cost >= 3:
        score += 5
        reasons.append("relic-expensive-energy")
    if profile.has("VELVET_CHOKER") and cost == 0:
        score -= 4
        reasons.append("relic-choker-card-count")
    return score, reasons


def relic_card_reward_modifier(card: dict[str, Any], state: dict[str, Any], *, damage: int = 0, block: int = 0, cost: int | None = None) -> tuple[float, list[str]]:
    profile = relic_profile(state)
    roles = _card_roles(card)
    cost = _card_cost(card) if cost is None else cost
    text = _card_text(card)
    plan = CARD_KNOWLEDGE.deck_plan(state)
    score = 0.0
    reasons: list[str] = []

    if profile.has(*START_DRAW_RELICS):
        if cost <= 1 or roles & {"draw", "energy", "discard"}:
            score += 4
            reasons.append("relic-opening-draw")
        elif cost >= 3 and profile.energy_support == 0 and not profile.has("SNECKO_EYE"):
            score -= 3
    if profile.has("SNECKO_EYE"):
        if cost >= 2:
            score += 8
            reasons.append("relic-snecko-expensive")
        elif cost == 0:
            score -= 3
    if profile.has("CHEMICAL_X") and card_costs_x(card):
        score += 24
        reasons.append("relic-chemical-x")
    if "starter_resource" in profile.tags and (cost >= 2 or "x_cost" in roles):
        score += 5
        reasons.append("relic-resource-support")
    if "summon" in profile.tags and (roles & {"summon_osty", "power_scaling"} or "summon" in text or "minion" in text):
        score += 8
        reasons.append("relic-summon-engine")

    if profile.has("SHURIKEN", "KUNAI", "ORNAMENTAL_FAN", "NUNCHAKU", "PEN_NIB", "NINJA_SCROLL"):
        if "attack" in roles:
            score += 6 if cost <= 1 else 3
            reasons.append("relic-attack-chain")
        if "shiv" in roles:
            score += 8
            reasons.append("relic-shiv-chain")
    if profile.has("STRIKE_DUMMY") and "strike" in text:
        score += 7
        reasons.append("relic-strike-dummy")
    if profile.has("BAG_OF_MARBLES", "AKABEKO") and "attack" in roles:
        score += 4
    if profile.has("DAUGHTER_OF_THE_WIND") and "attack" in roles:
        score += 3 if plan.needs_block else 1
    if profile.has("LETTER_OPENER") and "skill" in roles:
        score += 5 if cost <= 1 or "draw" in roles else 2
        reasons.append("relic-skill-chain")
    if profile.has("TOUGH_BANDAGES", "TINGSHA", "GAMBLING_CHIP") and "discard" in roles:
        score += 10
        reasons.append("relic-discard-payoff")
    if profile.has("DATA_DISK", "CRACKED_CORE", "RUNIC_CAPACITOR", "SYMBIOTIC_VIRUS") and roles & {"orb", "focus"}:
        score += 10
        reasons.append("relic-orb-payoff")
    if profile.energy_support and (cost >= 2 or "x_cost" in roles):
        score += min(6, profile.energy_support * 3)
    if profile.has("ETERNAL_FEATHER") and plan.card_count >= 20 and roles <= {"attack"}:
        score -= 3

    copy_penalty, copy_reasons = relic_card_copy_penalty(card, state, roles, damage=damage, block=block)
    if copy_penalty:
        score -= copy_penalty
        reasons.extend(copy_reasons)

    generic_low_impact = roles <= {"attack"} or roles <= {"block"} or not (roles & {"draw", "energy", "power_scaling", "discard", "orb", "focus", "aoe", "debuff"})
    if profile.reward_selectivity:
        selective_count = 14 if "card_quality" in profile.tags else 16
        if generic_low_impact and plan.card_count >= selective_count and not plan.needs_damage and not plan.needs_block:
            score -= min(12.0, profile.reward_selectivity)
            reasons.append("relic-thin-deck-selective")
        elif roles & {"draw", "energy", "power_scaling", "discard", "orb", "focus"}:
            score += 4
    return score, reasons


def relic_reward_threshold_delta(card: dict[str, Any], state: dict[str, Any], score: float) -> float:
    profile = relic_profile(state)
    if not profile.reward_selectivity:
        return 0.0
    modifier, _ = relic_card_reward_modifier(card, state)
    delta = min(10.0, profile.reward_selectivity * 0.55)
    if modifier >= 8:
        delta -= 6
    elif modifier <= -4:
        delta += 5
    return max(-6.0, delta)


def relic_pickup_score(item: dict[str, Any], state: dict[str, Any]) -> tuple[float, list[str]]:
    entry = relic_entry_for_item(item)
    relic_id = normalize_relic_id((entry or {}).get("id") or item.get("relic_id") or item.get("id"))
    tags = _tags_for_relic(relic_id, entry)
    profile = relic_profile(state)
    plan = CARD_KNOWLEDGE.deck_plan(state)
    run = state.get("run") or {}
    gold = _first_number(run.get("gold") or run.get("player_gold")) or 0
    hp = _first_number(run.get("current_hp"))
    max_hp = _first_number(run.get("max_hp"))
    hp_ratio = hp / max_hp if hp and max_hp else 1.0
    score = 0.0
    reasons: list[str] = []

    rarity = str((entry or item).get("rarity") or "").lower()
    if "shop" in rarity:
        score += 10
    elif "rare" in rarity:
        score += 12
    elif "uncommon" in rarity:
        score += 8
    elif "common" in rarity:
        score += 5

    if tags & {"attack", "skill", "block", "damage", "draw", "energy", "orb"}:
        score += 14
        reasons.append("relic-combat")
    if "card_reward" in tags:
        score += 8
        reasons.append("relic-reward")
    if "shop" in tags:
        score += 8 + (6 if gold >= 150 else 0)
        reasons.append("relic-shop")
    if "rest" in tags:
        score += 7
        reasons.append("relic-rest")
    if "removal" in tags:
        score += 18 + (18 if plan.wants_removal else 0)
        reasons.append("relic-remove")
    if "card_quality" in tags:
        score += 12 + (8 if plan.removable_count >= 4 else 0)
        reasons.append("relic-card-quality")
    if "transform" in tags:
        score += 8 + (8 if plan.wants_removal else 0)
        reasons.append("relic-transform")
    if "summon" in tags:
        score += 16
        reasons.append("relic-summon")
    if "starter_resource" in tags:
        score += 14
        reasons.append("relic-resource")
    if "sustain" in tags:
        score += 10
        reasons.append("relic-sustain")
    if "potion" in tags and not profile.has("SOZU"):
        score += 4
    if relic_id == "CHEMICAL_X":
        x_count = _deck_role_count(state, "x_cost")
        score += 35 if x_count else 10
        reasons.append("relic-x-cost")
    if relic_id in {"TOUGH_BANDAGES", "TINGSHA", "GAMBLING_CHIP"}:
        discard_count = _deck_role_count(state, "discard")
        score += 12 + discard_count * 6
        reasons.append("relic-discard")
    if relic_id in {"SHURIKEN", "KUNAI", "ORNAMENTAL_FAN", "NUNCHAKU", "NINJA_SCROLL"}:
        attack_count = _deck_role_count(state, "attack", "shiv")
        score += min(28, attack_count * 3)
        reasons.append("relic-attack-chain")
    if relic_id in {"DATA_DISK", "RUNIC_CAPACITOR", "SYMBIOTIC_VIRUS"}:
        orb_count = _deck_role_count(state, "orb", "focus")
        score += 12 + orb_count * 4
        reasons.append("relic-orb")
    if relic_id == "PRECARIOUS_SHEARS" and hp_ratio < 0.55:
        score -= 35
        reasons.append("low-hp-shears")
    if "hp_cost" in tags and hp_ratio < 0.65:
        score -= 18
        reasons.append("low-hp-pickup-cost")
    if "max_hp_loss" in tags:
        score -= 10
        if hp_ratio < 0.75:
            score -= 8
        reasons.append("max-hp-cost")
    if relic_id in {"MEMBERSHIP_CARD", "THE_COURIER"}:
        score += 28 if gold >= 120 else 16
        reasons.append("future-shop")
    if relic_id == "MEAL_TICKET" and hp_ratio < 0.75:
        score += 14
    if relic_id in {"SHOVEL", "GIRYA", "MINIATURE_TENT"} and hp_ratio >= 0.65:
        score += 12
    if relic_id == "SOZU":
        score += 18
        if current_potion_count(state) <= 1:
            score -= 8
    return score, reasons


def relic_shop_item_modifier(item: dict[str, Any], state: dict[str, Any]) -> tuple[float, list[str]]:
    if not isinstance(item, dict):
        return 0.0, []
    text = _text_blob(item)
    profile = relic_profile(state)
    if item.get("relic_id") or "relic" in text or "遗物" in text:
        return relic_pickup_score(item, state)
    if item.get("potion_id") or "potion" in text or "药水" in text:
        score = 0.0
        reasons: list[str] = []
        if profile.has("SOZU"):
            score -= 100
            reasons.append("relic-sozu-no-potions")
        if profile.has("WHITE_BEAST_STATUE", "POTION_BELT", "ALCHEMICAL_COFFER"):
            score -= 3
        if profile.has("BELT_BUCKLE") and current_potion_count(state) == 0:
            score -= 14
            reasons.append("relic-empty-belt")
        return score, reasons
    modifier, reasons = relic_card_reward_modifier(item, state)
    return modifier, reasons


def current_potion_count(state: dict[str, Any]) -> int:
    run = state.get("run") or {}
    potions = run.get("potions") or run.get("player_potions") or []
    if not isinstance(potions, list):
        return 0
    return sum(1 for potion in potions if isinstance(potion, dict) and (potion.get("potion_id") or potion.get("id") or potion.get("occupied")))


def relic_shop_removal_modifier(state: dict[str, Any]) -> float:
    profile = relic_profile(state)
    plan = CARD_KNOWLEDGE.deck_plan(state)
    bonus = 0.0
    if profile.reward_selectivity and plan.removable_count:
        bonus += min(18.0, profile.reward_selectivity)
    if "card_quality" in profile.tags and plan.removable_count:
        bonus += 6.0
    if profile.has("STRIKE_DUMMY"):
        bonus -= 4.0
    if profile.has("MEMBERSHIP_CARD", "THE_COURIER") and plan.removable_count <= 3:
        bonus -= 4.0
    return bonus


def relic_remove_card_modifier(card: dict[str, Any], state: dict[str, Any]) -> float:
    profile = relic_profile(state)
    roles = _card_roles(card)
    text = _card_text(card)
    score = 0.0
    if profile.has("STRIKE_DUMMY") and "strike" in text:
        score -= 22
    if profile.has("SHURIKEN", "KUNAI", "ORNAMENTAL_FAN") and "attack" in roles and "strike" not in text:
        score -= 8
    if profile.has("TOUGH_BANDAGES", "TINGSHA") and "discard" in roles:
        score -= 18
    if profile.has("DATA_DISK", "CRACKED_CORE", "RUNIC_CAPACITOR") and roles & {"orb", "focus"}:
        score -= 20
    if profile.has(*THIN_DECK_RELICS) and ("strike" in text or "defend" in text):
        score += 6
    return score


def relic_route_modifier(node: dict[str, Any], state: dict[str, Any]) -> float:
    profile = relic_profile(state)
    text = _text_blob(node)
    hp, max_hp = _first_number((state.get("run") or {}).get("current_hp")), _first_number((state.get("run") or {}).get("max_hp"))
    ratio = hp / max_hp if hp and max_hp else 1.0
    plan = CARD_KNOWLEDGE.deck_plan(state)
    score = 0.0
    is_elite = "elite" in text or "精英" in text
    is_combat = any(token in text for token in ("monster", "combat", "enemy", "fight", "normal", "普通", "敌"))
    is_shop = "shop" in text or "商店" in text
    is_rest = "rest" in text or "campfire" in text or "篝火" in text or "休息" in text
    is_chest = "treasure" in text or "chest" in text or "宝箱" in text
    is_event = "event" in text or "unknown" in text or "?" in text or "事件" in text
    if is_elite:
        score += profile.route_aggression
        if profile.has("BLACK_STAR", "WHITE_STAR", "SWORD_OF_STONE", "SLING_OF_COURAGE"):
            score += 16 if ratio >= 0.65 else 4
    elif is_combat:
        score += profile.combat_strength * 0.35
        if profile.has("AMETHYST_AUBERGINE"):
            score += 6
        if "sustain" in profile.tags:
            score += 8 if ratio >= 0.45 else 2
        if "card_quality" in profile.tags and plan.combat_ready:
            score += 3
    if is_shop:
        score += profile.shop_strength
        if profile.removal_pressure and plan.wants_removal:
            score += 6
        if profile.has("MEAL_TICKET") and ratio < 0.9:
            score += 10
        if profile.has("THE_COURIER", "MEMBERSHIP_CARD"):
            score += 8
    if is_rest:
        score += profile.rest_strength
        if profile.has("SHOVEL") and ratio >= 0.6:
            score += 12
        if profile.has("ETERNAL_FEATHER", "REGAL_PILLOW") and ratio < 0.7:
            score += 8
    if is_chest:
        score += 8
        if profile.has("SILVER_CRUCIBLE"):
            score -= 10
    if is_event and profile.has("MAW_BANK"):
        score += 3
    return score


def relic_event_option_modifier(option: dict[str, Any], state: dict[str, Any]) -> tuple[float, list[str]]:
    profile = relic_profile(state)
    text = _text_blob(option)
    run = state.get("run") or {}
    hp = _first_number(run.get("current_hp"))
    max_hp = _first_number(run.get("max_hp"))
    ratio = hp / max_hp if hp and max_hp else 1.0
    score = 0.0
    reasons: list[str] = []
    if "relic" in text or "遗物" in text:
        score += 12
        reasons.append("event-relic")
        if "lose" in text or "damage" in text or "失去" in text or "受伤" in text:
            score += 8 if ratio > 0.72 else -18
            reasons.append("event-hp-for-relic")
    if "remove" in text or "移除" in text:
        score += min(12.0, profile.removal_pressure)
    if "curse" in text or "诅咒" in text:
        score -= 10 + min(10.0, profile.reward_selectivity)
    if "shop" in text and profile.shop_strength:
        score += 5
    return score, reasons


def relic_rest_option_modifier(option: dict[str, Any], state: dict[str, Any], *, hp_ratio: float) -> tuple[float, list[str]]:
    profile = relic_profile(state)
    text = _text_blob(option)
    score = 0.0
    reasons: list[str] = []
    if "dig" in text or "relic" in text or "遗物" in text:
        if profile.has("SHOVEL"):
            score += 28 if hp_ratio >= 0.6 else -8
            reasons.append("relic-shovel-dig")
    if "rest" in text or "heal" in text or "休息" in text:
        if profile.has("REGAL_PILLOW", "STONE_HUMIDIFIER"):
            score += 10 if hp_ratio < 0.72 else -2
            reasons.append("relic-rest-heal")
    if "smith" in text or "upgrade" in text or "升级" in text:
        if profile.has("ETERNAL_FEATHER", "BURNING_BLOOD", "BLOOD_VIAL") and hp_ratio >= 0.5:
            score += 5
            reasons.append("relic-heal-allows-smith")
    if "strength" in text and profile.has("GIRYA") and hp_ratio >= 0.6:
        score += 14
        reasons.append("relic-girya")
    return score, reasons
