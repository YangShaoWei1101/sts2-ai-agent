from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from autoplay_character_strategy import (
    archetype_priority,
    archetype_strength_bonus,
    character_color,
    is_basic_card_id,
    narrow_card_adjustment,
    starter_upgrade_hint,
)

CARD_MODEL_PATH = Path(__file__).resolve().parents[2] / "output" / "sts2-knowledge" / "card_model.json"
FALLBACK_CARDS_PATH = Path(__file__).resolve().with_name("data") / "eng" / "cards.json"

SCALING_ROLES = {
    "power_scaling",
    "strength",
    "dexterity",
    "focus",
    "poison",
    "shiv",
    "orb",
    "doom",
    "summon_osty",
    "star_resource",
    "upgrade_forge",
}

STATUS_BAGGAGE_IDS = {
    "BURN",
    "DAZED",
    "SLIMED",
    "VOID",
    "WOUND",
}

PERSISTENT_SELF_DAMAGE_POWER_IDS = {
    "BRUTALITY",
    "COMBUST",
    "CRIMSON_MANTLE",
}

BASIC_CARD_ID_ALIASES = {
    "STRIKE_R": "STRIKE_IRONCLAD",
    "DEFEND_R": "DEFEND_IRONCLAD",
    "STRIKE_G": "STRIKE_SILENT",
    "DEFEND_G": "DEFEND_SILENT",
    "STRIKE_B": "STRIKE_DEFECT",
    "DEFEND_B": "DEFEND_DEFECT",
}

SILENT_REAL_DAMAGE_IDS = {
    "ACCURACY",
    "ACCELERANT",
    "ALL_OUT_ATTACK",
    "BACKSTAB",
    "BLADE_DANCE",
    "BLADE_OF_INK",
    "CATALYST",
    "CHOKE",
    "CORPSE_EXPLOSION",
    "DAGGER_SPRAY",
    "DAGGER_THROW",
    "DASH",
    "DEADLY_POISON",
    "DIE_DIE_DIE",
    "ECHOING_SLASH",
    "ENDLESS_AGONY",
    "ENVENOM",
    "FINISHER",
    "FLECHETTES",
    "FLICK_FLACK",
    "GLASS_KNIFE",
    "HIDDEN_DAGGERS",
    "KNIFE_TRAP",
    "MEMENTO_MORI",
    "MIRAGE",
    "NOXIOUS_FUMES",
    "OUTBREAK",
    "PHANTOM_BLADES",
    "POISONED_STAB",
    "PREDATOR",
    "SKEWER",
    "STORM_OF_STEEL",
    "TERROR",
}

SILENT_REAL_DAMAGE_ROLES = {
    "poison",
    "shiv",
    "strength",
    "vulnerable",
}


@dataclass(frozen=True)
class KnownCard:
    id: str
    name: str
    color: str
    type: str
    rarity: str
    cost: int | None
    roles: frozenset[str]
    archetypes: frozenset[str]
    live_present: bool
    summary: str
    description: str

    @property
    def draftable(self) -> bool:
        return self.live_present and "not_for_drafting" not in self.roles and "token_or_generated" not in self.roles


@dataclass
class DeckProfile:
    character_id: str | None
    card_count: int
    ids: Counter[str]
    roles: Counter[str]
    archetypes: Counter[str]

    def role(self, name: str) -> int:
        return self.roles.get(name, 0)

    def archetype(self, name: str) -> int:
        return self.archetypes.get(name, 0)

    def matching_archetype_count(self, card: KnownCard) -> int:
        return sum(self.archetypes.get(tag, 0) for tag in card.archetypes)


@dataclass(frozen=True)
class DeckPlan:
    character_id: str | None
    card_count: int
    ids: Counter[str]
    primary_archetype: str | None
    primary_count: int
    attack_count: int
    block_count: int
    draw_count: int
    energy_count: int
    scaling_count: int
    aoe_count: int
    debuff_count: int
    basic_count: int
    removable_count: int
    curse_status_count: int
    needs_damage: bool
    needs_block: bool
    needs_draw: bool
    needs_scaling: bool
    needs_aoe: bool
    wants_removal: bool
    combat_ready: bool
    focused: bool

    def wants_archetype(self, known: KnownCard) -> bool:
        return bool(self.primary_archetype and self.primary_archetype in known.archetypes)

    def summary(self) -> str:
        primary = self.primary_archetype or "open"
        needs = [
            name
            for name, enabled in (
                ("damage", self.needs_damage),
                ("block", self.needs_block),
                ("draw", self.needs_draw),
                ("scaling", self.needs_scaling),
                ("aoe", self.needs_aoe),
                ("remove", self.wants_removal),
            )
            if enabled
        ]
        return f"{self.character_id or 'UNKNOWN'}:{primary}:{','.join(needs) or 'stable'}"


def normalize_card_id(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    raw = raw.replace("-", "_").replace(" ", "_")
    if raw.upper() == raw:
        normalized = raw.upper()
    else:
        raw = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", raw)
        raw = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", raw)
        normalized = raw.upper()
    return BASIC_CARD_ID_ALIASES.get(normalized, normalized)


def card_id_from_payload(card: dict[str, Any] | None) -> str:
    if not card:
        return ""
    for key in ("card_id", "id", "cardId", "internal_id"):
        if card.get(key):
            return normalize_card_id(card.get(key))
    return normalize_card_id(card.get("name"))


def _text_draws_cards(text: str) -> bool:
    text = text.lower()
    return bool(
        re.search(r"\bdraw\s+(?:\d+|a|one|two|three|four|all)?\s*cards?\b", text)
        or re.search(r"\bdraw\s+cards?\b", text)
        or "draw that many cards" in text
        or "抽牌" in text
        or re.search(r"抽(?:\d+)?\s*张?牌", text)
    )


def _spawns_status_baggage(card: dict[str, Any], text: str) -> bool:
    spawned = {normalize_card_id(card_id) for card_id in card.get("spawns_cards") or []}
    if spawned & STATUS_BAGGAGE_IDS:
        return True
    return bool(
        ("slimed" in text and ("discard" in text or "draw pile" in text))
        or ("wound" in text and ("discard" in text or "draw pile" in text))
        or ("burn" in text and ("discard" in text or "draw pile" in text))
        or ("dazed" in text and ("discard" in text or "draw pile" in text))
    )


def _is_persistent_self_damage_power(known: KnownCard) -> bool:
    if known.id in PERSISTENT_SELF_DAMAGE_POWER_IDS:
        return True
    description = known.description.lower()
    return bool(
        known.type.lower() == "power"
        and "self_damage" in known.roles
        and "lose" in description
        and "hp" in description
        and "whenever you lose hp" not in description
        and any(token in description for token in ("at the start of your turn", "end of your turn"))
    )


def _self_damage_payoff_count(profile: DeckProfile) -> int:
    return profile.ids.get("RUPTURE", 0) + profile.ids.get("BLOOD_FOR_BLOOD", 0)


def _build_fallback_model() -> list[dict[str, Any]]:
    if not FALLBACK_CARDS_PATH.exists():
        return []
    raw_cards = json.loads(FALLBACK_CARDS_PATH.read_text(encoding="utf-8-sig"))
    model = []
    for card in raw_cards:
        text = " ".join(
            str(card.get(key) or "")
            for key in ("id", "name", "description", "type", "rarity", "color", "target")
        ).lower()
        roles: set[str] = set()
        if card.get("type") == "Attack" or card.get("damage") is not None:
            roles.add("attack")
        if card.get("target") == "AllEnemies":
            roles.add("aoe")
        if card.get("block") is not None or "block" in text:
            roles.add("block")
        if _text_draws_cards(text):
            roles.add("draw")
        if card.get("energy_gain") is not None or "energy" in text:
            roles.add("energy")
        if card.get("type") == "Power":
            roles.add("power_scaling")
        if card.get("is_x_cost"):
            roles.add("x_cost")
        if card.get("is_x_star_cost"):
            roles.add("star_x_cost")
            roles.add("star_resource")
        for role, token in (
            ("exhaust", "exhaust"),
            ("poison", "poison"),
            ("shiv", "shiv"),
            ("discard", "discard"),
            ("vulnerable", "vulnerable"),
            ("weak", "weak"),
            ("orb", "channel"),
            ("focus", "focus"),
            ("doom", "doom"),
            ("summon_osty", "osty"),
            ("ethereal", "ethereal"),
            ("star_resource", "star"),
            ("upgrade_forge", "forge"),
        ):
            if token in text:
                roles.add(role)
        if card.get("type") in {"Status", "Curse", "Quest"} or card.get("color") in {"status", "curse", "quest"}:
            roles.add("not_for_drafting")
            roles.add("token_or_generated")
        if _spawns_status_baggage(card, text):
            roles.add("status_pollution")
        model.append(
            {
                "id": normalize_card_id(card.get("id")),
                "name": card.get("name") or card.get("id"),
                "color": card.get("color") or "",
                "type": card.get("type") or "",
                "rarity": card.get("rarity") or "",
                "cost": card.get("cost"),
                "roles": sorted(roles),
                "archetype_tags": [],
                "live_present": True,
                "use_summary": "",
                "description": card.get("description") or "",
            }
        )
    return model


@lru_cache(maxsize=1)
def load_card_model() -> dict[str, KnownCard]:
    if CARD_MODEL_PATH.exists():
        raw_cards = json.loads(CARD_MODEL_PATH.read_text(encoding="utf-8-sig"))
    else:
        raw_cards = _build_fallback_model()
    cards: dict[str, KnownCard] = {}
    for raw in raw_cards:
        card_id = normalize_card_id(raw.get("id"))
        if not card_id:
            continue
        roles = set(str(role) for role in raw.get("roles") or [])
        description = " ".join(
            str(raw.get(key) or "")
            for key in ("description", "upgrade_description")
        )
        description_l = description.lower()
        if card_id == "BUFFER" or "prevent the next time you would lose hp" in description_l:
            roles.discard("self_damage")
            roles.add("block_retention")
        if card_id == "PIERCING_WAIL":
            roles.discard("self_damage")
            roles.add("debuff")
            roles.add("strength")
        if card_id == "CALCULATED_GAMBLE":
            roles.add("draw")
            roles.add("discard")
            roles.add("deck_manipulation")
        if card_id == "FOOTWORK":
            roles.add("block")
            roles.add("dexterity")
        if "draw" in roles and not _text_draws_cards(description):
            roles.discard("draw")
        if "discard" in description_l:
            roles.add("discard")
        if raw.get("is_x_cost"):
            roles.add("x_cost")
        if raw.get("is_x_star_cost"):
            roles.add("star_x_cost")
            roles.add("star_resource")
            roles.discard("x_cost")
        fallback_card = {
            "spawns_cards": raw.get("spawns_cards") or raw.get("spawnsCards") or [],
        }
        if _spawns_status_baggage(fallback_card, " ".join((description, str(raw.get("use_summary") or ""))).lower()):
            roles.add("status_pollution")
        cards[card_id] = KnownCard(
            id=card_id,
            name=str(raw.get("name") or card_id),
            color=str(raw.get("color") or ""),
            type=str(raw.get("type") or ""),
            rarity=str(raw.get("rarity") or ""),
            cost=raw.get("cost") if isinstance(raw.get("cost"), int) else None,
            roles=frozenset(roles),
            archetypes=frozenset(str(tag) for tag in raw.get("archetype_tags") or []),
            live_present=bool(raw.get("live_present", True)),
            summary=str(raw.get("use_summary") or ""),
            description=str(raw.get("description") or ""),
        )
    return cards


class CardKnowledge:
    def __init__(self, cards: dict[str, KnownCard] | None = None) -> None:
        self.cards = cards if cards is not None else load_card_model()

    def lookup_id(self, card_id: str) -> KnownCard | None:
        return self.cards.get(normalize_card_id(card_id))

    def lookup(self, card: dict[str, Any] | None) -> KnownCard | None:
        return self.lookup_id(card_id_from_payload(card))

    def deck_profile(self, state: dict[str, Any]) -> DeckProfile:
        run = state.get("run") or {}
        character_id = run.get("character_id")
        if not character_id:
            players = run.get("players") or []
            for player in players:
                if player.get("is_local"):
                    character_id = player.get("character_id")
                    break
        character_id = str(character_id).upper() if character_id else None

        ids: Counter[str] = Counter()
        roles: Counter[str] = Counter()
        archetypes: Counter[str] = Counter()
        deck = run.get("deck") or run.get("cards") or []
        for raw_card in deck:
            card_id = card_id_from_payload(raw_card)
            if not card_id:
                continue
            ids[card_id] += 1
            known = self.lookup_id(card_id)
            if known is None:
                continue
            roles.update(known.roles)
            if known.rarity != "Basic" or not is_basic_card_id(card_id):
                archetypes.update(known.archetypes)
        return DeckProfile(
            character_id=character_id,
            card_count=sum(ids.values()),
            ids=ids,
            roles=roles,
            archetypes=archetypes,
        )

    def deck_plan(self, state: dict[str, Any]) -> DeckPlan:
        profile = self.deck_profile(state)
        run = state.get("run") or {}
        deck = run.get("deck") or run.get("cards") or []
        attack_count = 0
        block_count = 0
        draw_count = 0
        energy_count = 0
        scaling_count = 0
        aoe_count = 0
        debuff_count = 0
        basic_count = 0
        removable_count = 0
        curse_status_count = 0

        for raw_card in deck:
            card_id = card_id_from_payload(raw_card)
            known = self.lookup_id(card_id)
            roles = known.roles if known else frozenset()
            rarity = str(raw_card.get("rarity") or (known.rarity if known else "")).lower()
            card_type = str(raw_card.get("card_type") or raw_card.get("type") or (known.type if known else "")).lower()
            if "attack" in roles or card_type == "attack":
                attack_count += 1
            if "block" in roles:
                block_count += 1
            if "draw" in roles:
                draw_count += 1
            if "energy" in roles or "star_resource" in roles:
                energy_count += 1
            if roles & SCALING_ROLES:
                scaling_count += 1
            if "aoe" in roles:
                aoe_count += 1
            if "debuff" in roles or "weak" in roles or "vulnerable" in roles:
                debuff_count += 1
            if rarity == "basic":
                basic_count += 1
            if is_basic_card_id(card_id):
                removable_count += 1
            if card_type in {"curse", "status", "quest"} or "not_for_drafting" in roles:
                curse_status_count += 1
                removable_count += 2

        priority = archetype_priority(profile.character_id or "")
        primary_archetype = None
        primary_count = 0
        if profile.archetypes:
            candidates = [
                (profile.archetypes.get(tag, 0), -rank, tag)
                for rank, tag in enumerate(priority)
                if profile.archetypes.get(tag, 0) > 0
            ]
            if not candidates:
                candidates = [(count, 0, tag) for tag, count in profile.archetypes.items()]
            primary_count, _, primary_archetype = max(candidates)

        card_count = max(1, profile.card_count)
        needs_damage = attack_count < (5 if card_count <= 16 else 7)
        needs_block = block_count < (5 if card_count <= 16 else 7)
        needs_draw = draw_count < (1 if card_count <= 14 else 3)
        needs_scaling = scaling_count < (1 if card_count <= 14 else 2)
        needs_aoe = aoe_count == 0 and card_count >= 14
        wants_removal = removable_count >= 5 or curse_status_count > 0 or (card_count >= 18 and basic_count >= 8)

        if profile.character_id == "DEFECT":
            frost_ids = {"CHILL", "COLD_SNAP", "COOLHEADED", "GLACIER", "HAILSTORM", "LIGHTNING_ROD"}
            focus_ids = {"BIASED_COGNITION", "DEFRAGMENT", "FOCUS", "HOTFIX"}
            frost_count = sum(profile.ids.get(card_id, 0) for card_id in frost_ids) + profile.archetype("de_frost_defense")
            focus_count = sum(profile.ids.get(card_id, 0) for card_id in focus_ids) + profile.role("focus")
            orb_shell = profile.archetype("de_orb_focus") + profile.archetype("de_frost_defense")
            if card_count >= 12 and orb_shell >= 2 and focus_count == 0:
                needs_scaling = True
            if card_count >= 12 and (block_count < 6 or (attack_count >= block_count + 2 and frost_count < 2)):
                needs_block = True
            if card_count >= 16 and draw_count < 3:
                needs_draw = True

        if profile.character_id == "IRONCLAD":
            reliable_damage_ids = {
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
            real_damage_count = sum(profile.ids.get(card_id, 0) for card_id in reliable_damage_ids)
            real_damage_count += profile.role("strength")
            slow_engine_count = sum(
                profile.ids.get(card_id, 0)
                for card_id in {"BARRICADE", "CORRUPTION", "DARK_EMBRACE", "DEMON_FORM"}
            )
            exhaust_shell = profile.archetype("ic_exhaust_engine") + profile.role("exhaust")
            if card_count <= 14 and real_damage_count < 2:
                needs_damage = True
            if card_count >= 12 and real_damage_count < 3 and slow_engine_count:
                needs_damage = True
            if slow_engine_count and exhaust_shell < 3 and real_damage_count < 3:
                needs_scaling = False
            if card_count >= 14 and draw_count < 2 and not slow_engine_count:
                needs_draw = True

        if profile.character_id == "SILENT":
            strike_count = profile.ids.get("STRIKE_SILENT", 0)
            neutralize_count = profile.ids.get("NEUTRALIZE", 0)
            real_damage_count = sum(profile.ids.get(card_id, 0) for card_id in SILENT_REAL_DAMAGE_IDS)
            real_damage_count += profile.role("poison")
            real_damage_count += profile.role("shiv")
            real_damage_count += profile.role("strength")
            real_damage_count += max(0, profile.role("vulnerable") - neutralize_count)
            nonstarter_attack_count = max(0, attack_count - strike_count - neutralize_count)
            floor = _first_number(run.get("floor") or run.get("current_floor")) or 0
            boss_prep = floor in {12, 13, 14, 15, 16, 30, 31, 32, 46, 47, 48}
            if card_count <= 14 and real_damage_count < 2:
                needs_damage = True
            if card_count >= 15 and real_damage_count < 3:
                needs_damage = True
            if card_count >= 18 and real_damage_count < 4:
                needs_damage = True
            if boss_prep and real_damage_count < 4:
                needs_damage = True
            if card_count >= 16 and block_count >= 9 and nonstarter_attack_count < 2:
                needs_damage = True
            if primary_archetype == "si_defense_control" and card_count >= 16 and real_damage_count < 4:
                needs_damage = True

        focused = bool(primary_archetype and primary_count >= 3)
        combat_ready = not needs_damage and not needs_block and (card_count < 16 or not needs_draw)

        return DeckPlan(
            character_id=profile.character_id,
            card_count=profile.card_count,
            ids=profile.ids,
            primary_archetype=primary_archetype,
            primary_count=primary_count,
            attack_count=attack_count,
            block_count=block_count,
            draw_count=draw_count,
            energy_count=energy_count,
            scaling_count=scaling_count,
            aoe_count=aoe_count,
            debuff_count=debuff_count,
            basic_count=basic_count,
            removable_count=removable_count,
            curse_status_count=curse_status_count,
            needs_damage=needs_damage,
            needs_block=needs_block,
            needs_draw=needs_draw,
            needs_scaling=needs_scaling,
            needs_aoe=needs_aoe,
            wants_removal=wants_removal,
            combat_ready=combat_ready,
            focused=focused,
        )

    def target_color(self, state: dict[str, Any]) -> str | None:
        profile = self.deck_profile(state)
        if profile.character_id:
            return character_color(profile.character_id)
        return None

    def reward_modifier(
        self,
        card: dict[str, Any],
        state: dict[str, Any],
        *,
        damage: int,
        block: int,
        cost: int,
    ) -> tuple[float, list[str]]:
        known = self.lookup(card)
        if known is None:
            return 0.0, ["unknown-card"]

        profile = self.deck_profile(state)
        plan = self.deck_plan(state)
        roles = known.roles
        reasons: list[str] = []
        score = 0.0

        if not known.draftable:
            return -1000.0, ["not-draftable"]

        target_color = character_color(profile.character_id or "")
        if known.color not in {target_color, "colorless"} and target_color is not None:
            score -= 8
            reasons.append("off-color")

        if known.rarity == "Basic":
            score -= 20
        if known.rarity == "Rare":
            score += 4
        elif known.rarity == "Uncommon":
            score += 2

        if "attack" in roles:
            score += 8 if cost <= 1 else 4
            if profile.card_count <= 14:
                score += 7
            if plan.needs_damage:
                score += 8
                reasons.append("deck-needs-damage")
        if "aoe" in roles:
            score += 6
            if plan.needs_aoe:
                score += 10
                reasons.append("deck-needs-aoe")
        if "block" in roles:
            score += 6 if profile.role("block") < 5 else 2
            if plan.needs_block:
                score += 7
                reasons.append("deck-needs-block")
        if "draw" in roles:
            score += 9
            if plan.needs_draw:
                score += 8
                reasons.append("deck-needs-draw")
        if "energy" in roles or "star_resource" in roles:
            score += 7
        if "power_scaling" in roles:
            score += 5 if profile.card_count >= 12 else 2
            if plan.needs_scaling:
                score += 7
                reasons.append("deck-needs-scaling")
        if "debuff" in roles:
            score += 4
        if "deck_manipulation" in roles:
            score += 4
        if "discard" in roles and profile.character_id == "SILENT":
            score += 4

        matching = profile.matching_archetype_count(known)
        if matching:
            score += min(18, matching * 3.0)
            reasons.append(f"synergy={matching}")
        strength_bonus = max((archetype_strength_bonus(tag) for tag in known.archetypes), default=0)
        if strength_bonus:
            if profile.card_count <= 15 or matching or plan.wants_archetype(known):
                score += strength_bonus
                reasons.append(f"strong-archetype={strength_bonus}")
        if plan.wants_archetype(known):
            score += 8 + min(8, plan.primary_count * 2)
            reasons.append(f"plan={plan.primary_archetype}")
        elif known.archetypes and profile.card_count > 13:
            penalty = 9 if plan.focused else 4
            score -= penalty
            reasons.append("off-plan-archetype")

        score += self._narrow_card_adjustment(known, profile, reasons)

        if "self_damage" in roles:
            hp_ratio = _hp_ratio(state)
            penalty = 12 if hp_ratio < 0.55 else 4
            if _is_persistent_self_damage_power(known):
                payoff = _self_damage_payoff_count(profile)
                extra = 28 if hp_ratio < 0.55 else 10
                if payoff <= 0:
                    extra += 18
                if plan.needs_block and hp_ratio < 0.45:
                    extra += 14
                penalty += extra
            score -= penalty
            reasons.append(f"self-damage-penalty={penalty}")
        if "status_pollution" in roles and profile.role("status_cleanup") == 0 and profile.archetype("de_status_engine") < 2:
            penalty = 30
            if profile.card_count <= 14:
                penalty += 8
            if plan.needs_block or plan.needs_draw or plan.needs_scaling:
                penalty += 8
            score -= penalty
            reasons.append("junk-without-cleanup")
        if "coop_only_value" in roles:
            score -= 10
            reasons.append("coop-downrank")
        if cost >= 3 and profile.role("energy") + profile.role("star_resource") < 2:
            score -= 5
        if damage == 0 and block == 0 and not (roles & {"draw", "energy", "star_resource", "power_scaling", "debuff"}):
            score -= 8
        if (
            "power_scaling" in roles
            and damage == 0
            and block == 0
            and not (roles & {"draw", "energy", "star_resource", "debuff"})
            and plan.needs_draw
            and profile.role("power_scaling") >= 1
            and profile.card_count >= 12
        ):
            penalty = 26 + min(18, max(0, profile.card_count - 12) * 2)
            score -= penalty
            reasons.append(f"slow-engine-density={penalty}")
        if (
            plan.combat_ready
            and profile.card_count >= 18
            and not plan.wants_archetype(known)
            and not (roles & {"draw", "energy", "star_resource", "power_scaling", "aoe"})
        ):
            score -= 8
            reasons.append("deck-density")

        return score, reasons

    def combat_modifier(
        self,
        card: dict[str, Any],
        state: dict[str, Any],
        *,
        damage: int,
        block: int,
        cost: int,
        incoming: int,
        current_block: int,
        hp_ratio: float,
        target_hp: int | None,
    ) -> tuple[float, list[str]]:
        known = self.lookup(card)
        if known is None:
            return 0.0, ["unknown-card"]

        roles = known.roles
        reasons: list[str] = []
        score = 0.0
        covered = incoming <= current_block + block

        if "not_for_drafting" in roles and known.type in {"Status", "Curse", "Quest"}:
            return -200.0, ["bad-generated-card"]

        if "draw" in roles:
            score += 6 if cost <= 1 else 3
        if "energy" in roles or "star_resource" in roles:
            score += 6
        if "power_scaling" in roles:
            if covered or incoming <= current_block + 4 or hp_ratio > 0.75:
                score += 16
                reasons.append("safe-scaling")
            else:
                score -= 12
                reasons.append("unsafe-scaling")
        if "debuff" in roles:
            score += 8
        if "weak" in roles and incoming > current_block:
            score += 8
        if "vulnerable" in roles and target_hp and target_hp > max(10, damage):
            score += 8
        if "block_retention" in roles:
            score += 6
        if "self_damage" in roles:
            penalty = 35 if hp_ratio < 0.55 or incoming > current_block else 8
            score -= penalty
            reasons.append(f"self-damage-penalty={penalty}")
        if "status_pollution" in roles:
            profile = self.deck_profile(state)
            if profile.role("status_cleanup") == 0 and profile.archetype("de_status_engine") < 2:
                score -= 9
        if "x_cost" in roles and damage == 0 and block == 0:
            score -= 10
        if "coop_only_value" in roles:
            score -= 8

        return score, reasons

    def upgrade_modifier(self, card: dict[str, Any], state: dict[str, Any], *, damage: int, block: int) -> float:
        known = self.lookup(card)
        if known is None:
            return 0.0
        if "not_for_drafting" in known.roles:
            return -1000.0
        plan = self.deck_plan(state)
        score = starter_upgrade_hint(known.id)
        if "power_scaling" in known.roles:
            score += 18
            if plan.needs_scaling:
                score += 6
        if "draw" in known.roles or "energy" in known.roles or "star_resource" in known.roles:
            score += 12
            if plan.needs_draw:
                score += 5
        if "debuff" in known.roles:
            score += 10
        if "block" in known.roles:
            score += min(block, 12) * 0.8
            if plan.needs_block:
                score += 5
        if "attack" in known.roles:
            score += min(damage, 20) * 0.7
            if plan.needs_damage:
                score += 5
        profile = self.deck_profile(state)
        score += min(12, profile.matching_archetype_count(known) * 2)
        if plan.wants_archetype(known):
            score += 8
        if known.rarity == "Basic" and not starter_upgrade_hint(known.id):
            score -= 12
        return score

    def _narrow_card_adjustment(self, known: KnownCard, profile: DeckProfile, reasons: list[str]) -> float:
        return narrow_card_adjustment(
            known.id,
            known.roles,
            known.cost,
            profile.character_id,
            profile.archetype,
            profile.role,
            reasons,
        )


def _hp_ratio(state: dict[str, Any]) -> float:
    run = state.get("run") or {}
    hp = _first_number(run.get("current_hp") or run.get("hp") or run.get("player_hp"))
    max_hp = _first_number(run.get("max_hp") or run.get("player_max_hp"))
    if hp is None or max_hp in (None, 0):
        players = run.get("players") or []
        for player in players:
            if player.get("is_local"):
                hp = _first_number(player.get("current_hp") or player.get("hp"))
                max_hp = _first_number(player.get("max_hp"))
                break
    if hp is None or max_hp in (None, 0):
        return 1.0
    return max(0.0, min(1.0, hp / max_hp))


def _first_number(value: Any) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return int(value)
    match = re.search(r"-?\d+", str(value))
    return int(match.group(0)) if match else None


CARD_KNOWLEDGE = CardKnowledge()
