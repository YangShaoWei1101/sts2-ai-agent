# uncompyle6 version 3.9.2
# Python bytecode version base 3.7.0 (3394)
# Decompiled from: Python 3.7.7 (tags/v3.7.7:d7c567b08f, Mar 10 2020, 09:44:33) [MSC v.1900 32 bit (Intel)]
# Embedded file name: .\autoplay_ironclad.py
# Compiled at: 2026-06-01 04:04:31
# Size of source mod 2**32: 143799 bytes
from __future__ import annotations
import argparse, ctypes, ctypes.wintypes, hashlib, json, math, os, re, sys, time
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any
from sts2_mcp.client import Sts2ApiError, Sts2Client
from autoplay_strategy import CARD_KNOWLEDGE, card_id_from_payload
from autoplay_relic_strategy import (
    current_relic_ids,
    current_relics,
    relic_card_reward_modifier,
    relic_combat_modifier,
    relic_damage_bonus,
    relic_event_option_modifier,
    relic_pickup_score,
    relic_profile,
    relic_remove_card_modifier,
    relic_rest_option_modifier,
    relic_reward_threshold_delta,
    relic_route_modifier,
    relic_shop_item_modifier,
    relic_shop_removal_modifier,
    relic_summary,
)
LOG_PATH = Path(__file__).with_name("autoplay_ironclad.log")
SUMMARY_PATH = Path(__file__).with_name("autoplay_ironclad_summary.json")
JOURNAL_PATH = Path(__file__).with_name("autoplay_decision_journal.jsonl")
POLICY_PATH = Path(os.getenv("STS2_AUTOPLAY_POLICY", str(Path(__file__).with_name("autoplay_policy.json"))))
EVENTS_PATH = Path(__file__).with_name("data") / "eng" / "events.json"
CARDS_PATH = Path(__file__).with_name("data") / "eng" / "cards.json"
TARGET_CHARACTER_ID = os.getenv("STS2_AUTOPLAY_CHARACTER", "RANDOM_CHARACTER").strip().upper()


class ReadOnlyCardSelection(RuntimeError):
    pass


def configure_stdio() -> None:
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    for stream in (getattr(sys, "stdout", None), getattr(sys, "stderr", None)):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    if os.name == "nt":
        try:
            ctypes.windll.kernel32.SetConsoleOutputCP(65001)
            ctypes.windll.kernel32.SetConsoleCP(65001)
        except Exception:
            pass


configure_stdio()

DEFAULT_POLICY: "dict[str, Any]" = {'version':1, 
 'reward':{'card_bonus':{},  'archetype_bonus':{},  'role_bonus':{},  'plan_match_bonus':0, 
  'focused_off_plan_penalty':0, 
  'take_threshold':{
   'early': 22, 
   'needs_core': 38, 
   'needs_support': 45, 
   'stable': 55, 
   'focused_bonus': 10, 
   'combat_ready_bonus': 8, 
   'large_deck_bonus': 8, 
   'very_large_deck_bonus': 12, 
   'huge_deck_bonus': 12, 
   'plan_match_discount': 12, 
   'utility_discount': 8, 
   'need_discount': 8, 
   'off_plan_focused_bonus': 12}, 
  'density_penalty':{
   'focused_off_plan': 16, 
   'combat_ready_off_plan': 12, 
   'large_generic': 10, 
   'very_large_generic': 12, 
   'generic_attack': 14, 
   'generic_block': 8}, 
  'need_bonus':{
   'damage_attack': 0, 
   'block_block': 0, 
   'draw_draw': 0, 
   'scaling_power': 0, 
   'aoe_aoe': 0}}, 
 'map':{'node_bonus':{},  'removal_shop_bonus':0, 
  'low_hp_rest_bonus':0, 
  'early_shop_penalty':0, 
  'combat_ready_elite_bonus':0, 
  'low_hp_elite_penalty':80, 
  'critical_hp_elite_penalty':120, 
  'low_hp_combat_penalty':18, 
  'critical_hp_combat_penalty':35, 
  'low_hp_unknown_penalty':10, 
  'critical_hp_unknown_penalty':24, 
  'critical_hp_rest_bonus':34, 
  'critical_hp_shop_bonus':14, 
  'risk_start_hp_ratio':0.72, 
  'mid_hp_penalty_scale':0.45, 
  'mid_hp_combat_node_penalty':8, 
  'mid_hp_unknown_node_penalty':4, 
  'low_hp_immediate_rest_floor':42, 
  'critical_hp_immediate_rest_floor':92, 
  'mid_hp_immediate_rest_floor':18, 
  'low_hp_immediate_shop_floor':16, 
  'critical_hp_immediate_shop_floor':34, 
  'mid_hp_immediate_shop_floor':8, 
  'lookahead_weight':0.45, 
  'center_tie_bonus':0.2, 
  'tie_jitter':0.12}, 
 'rest':{
  'heal_bonus': 0, 
  'smith_bonus': 0, 
  'smith_with_target_bonus': 0, 
  'heal_when_hp_below': 0.55, 
  'force_heal_below': 0.38}, 
 'shop':{
  'buy_threshold': 4, 
  'card_bonus': 0, 
  'relic_bonus': 0, 
  'potion_bonus': 0, 
  'removal_bias': 0, 
  'removal_gold_reserve': 180, 
  'removal_first_below_gold': 150, 
  'removal_first_buy_score': 75}, 
 'combat':{'damage_floor':-20, 
  'play_any_damage':True}}
_POLICY_CACHE: "dict[str, Any] | None" = None
_POLICY_MTIME: "float | None" = None
SILENT_DISCARD_NOW_IDS = {
 'ACROBATICS', 
 'CALCULATED_GAMBLE', 
 'DAGGER_THROW', 
 'HIDDEN_DAGGERS', 
 'PREPARED', 
 'SHADOW_STEP', 
 'STORM_OF_STEEL', 
 'SURVIVOR'}
SILENT_DISCARD_ENGINE_IDS = {
 "MASTER_PLANNER",
 "TOOLS_OF_THE_TRADE"}
SILENT_DISCARD_SCALING_IDS = {
 "MEMENTO_MORI"}
SILENT_SLY_KEYWORD_IDS = {
 'ABRASIVE', 
 'FLICK_FLACK', 
 'HAZE', 
 'HELIX_DRILL', 
 'REFLEX', 
 'RICOCHET', 
 'SNEAKY', 
 'TACTICIAN', 
 'UNTOUCHABLE'}
SILENT_SLY_RESOURCE_IDS = {
 "REFLEX",
 "TACTICIAN"}
SILENT_WHOLE_HAND_DISCARD_IDS = {
 "CALCULATED_GAMBLE",
 "SHADOW_STEP",
 "STORM_OF_STEEL"}
SILENT_LOW_DAMAGE_DEFENSE_REWARD_IDS = {
 "ANTICIPATE",
 "BACKFLIP",
 "DEFLECT",
 "DODGE_AND_ROLL",
 "PREPARED",
 "UNTOUCHABLE"}
SILENT_PSEUDO_DRAW_ATTACK_REWARD_IDS = {
 "PREDATOR"}
SILENT_PREMIUM_SURVIVAL_REWARD_IDS = {
 "BLUR",
 "FOOTWORK",
 "LEG_SWEEP",
 "MALAISE",
 "PIERCING_WAIL",
 "WRAITH_FORM"}
STATUS_BAGGAGE_IDS = {
 'BURN', 
 'CLUMSY', 
 'DAZED', 
 'DECAY', 
 'DOUBT', 
 'NORMALITY', 
 'PAIN', 
 'PARASITE', 
 'REGRET', 
 'SHAME', 
 'SLIMED', 
 'VOID', 
 'WOUND'}
BASIC_STRIKE_IDS = frozenset({
    "STRIKE",
    "STRIKE_R",
    "STRIKE_G",
    "STRIKE_B",
    "STRIKE_IRONCLAD",
    "STRIKE_SILENT",
    "STRIKE_DEFECT",
    "STRIKE_NECROBINDER",
    "STRIKE_REGENT",
})
BASIC_DEFEND_IDS = frozenset({
    "DEFEND",
    "DEFEND_R",
    "DEFEND_G",
    "DEFEND_B",
    "DEFEND_IRONCLAD",
    "DEFEND_SILENT",
    "DEFEND_DEFECT",
    "DEFEND_NECROBINDER",
    "DEFEND_REGENT",
})
REWARD_UTILITY_ROLES = {
 'draw', 
 'energy', 
 'star_resource', 
 'power_scaling', 
 'debuff', 
 'weak', 
 'vulnerable', 
 'aoe', 
 'status_cleanup', 
 'deck_manipulation', 
 'exhaust', 
 'block_retention', 
 'card_generation'}

def log(message: "str", payload: "Any | None"=None) -> "None":
    line = f'{time.strftime("%Y-%m-%d %H:%M:%S")} {message}'
    try:
        print(line, flush=True)
    except OSError:
        pass

    with LOG_PATH.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")
        if payload is not None:
            fh.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def deep_merge_policy(base: "dict[str, Any]", override: "dict[str, Any]") -> "dict[str, Any]":
    merged = {}
    for key, value in base.items():
        if isinstance(value, dict):
            merged[key] = deep_merge_policy(value, {})
        else:
            merged[key] = value

    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge_policy(merged[key], value)
        else:
            merged[key] = value

    return merged


def policy() -> "dict[str, Any]":
    global _POLICY_CACHE
    global _POLICY_MTIME
    try:
        mtime = POLICY_PATH.stat().st_mtime
    except FileNotFoundError:
        if _POLICY_CACHE is None:
            _POLICY_CACHE = deep_merge_policy(DEFAULT_POLICY, {})
        return _POLICY_CACHE
    except OSError:
        return _POLICY_CACHE or DEFAULT_POLICY
    else:
        if _POLICY_CACHE is None or _POLICY_MTIME != mtime:
            try:
                override = json.loads(POLICY_PATH.read_text(encoding="utf-8-sig"))
                if not isinstance(override, dict):
                    override = {}
                _POLICY_CACHE = deep_merge_policy(DEFAULT_POLICY, override)
                _POLICY_MTIME = mtime
                log(f'policy loaded path={POLICY_PATH} version={_POLICY_CACHE.get("version")}')
            except Exception as exc:
                try:
                    log(f"policy load failed {type(exc).__name__}: {exc}")
                    _POLICY_CACHE = _POLICY_CACHE or deep_merge_policy(DEFAULT_POLICY, {})
                finally:
                    exc = None
                    del exc

        return _POLICY_CACHE


def policy_number(path: "str", default: "float"=0.0) -> "float":
    cur = policy()
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]

    if isinstance(cur, bool):
        return default
    if isinstance(cur, (int, float)):
        return float(cur)
    return default


def policy_bool(path: "str", default: "bool"=False) -> "bool":
    cur = policy()
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]

    if isinstance(cur, bool):
        return bool(cur)
    return default


def policy_table(path: "str") -> "dict[str, Any]":
    cur = policy()
    for part in path.split("."):
        if not isinstance(cur, dict):
            return {}
        cur = cur.get(part)

    if isinstance(cur, dict):
        return cur
    return {}


def table_bonus(path: "str", key: "str | None") -> "float":
    if not key:
        return 0.0
    table = policy_table(path)
    value = table.get(key) or table.get(str(key).upper()) or table.get(str(key).lower())
    if isinstance(value, (int, float)):
        if not isinstance(value, bool):
            return float(value)
    return 0.0


def as_actions(state: "dict[str, Any]") -> "set[str]":
    actions = set()
    for raw_action in state.get("available_actions") or []:
        name = None
        if isinstance(raw_action, str):
            actions.add(raw_action)
        elif isinstance(raw_action, dict):
            name = raw_action.get("name") or raw_action.get("action") or raw_action.get("action_type") or raw_action.get("type") or raw_action.get("id")
        if name:
            actions.add(str(name))

    return actions


def action_specs(actions_payload: "Any") -> "list[dict[str, Any]]":
    if not isinstance(actions_payload, list):
        return []
    specs = []
    for raw_action in actions_payload:
        if isinstance(raw_action, dict):
            specs.append(raw_action)

    return specs


def compact_state(state: "dict[str, Any]") -> "dict[str, Any]":
    run = state.get("run") or {}
    combat = state.get("combat") or {}
    return {'screen':(state.get)("screen"), 
     'phase':((state.get("session") or {}).get)("phase"), 
     'actions':(state.get)("available_actions"), 
     'floor':run.get("floor") or run.get("current_floor"), 
     'hp':player_hp(state), 
     'gold':run.get("gold") or run.get("player_gold"), 
     'enemies':[{'i':(e.get)("index", i),  'id':e.get("enemy_id") or e.get("id"),  'name':(e.get)("name"),  'hp':e.get("hp") or e.get("current_hp"),  'block':(e.get)("block"),  'intent':e.get("intent") or e.get("intent_name") or e.get("move")} for i, e in enumerate(combat.get("enemies") or [])], 
     'hand':[{'i':(c.get)("index", i),  'id':c.get("card_id") or c.get("id"),  'name':(c.get)("name"),  'cost':(c.get)("energy_cost", c.get("cost")),  'playable':(c.get)("playable"),  'target':(c.get)("requires_target")} for i, c in enumerate(combat.get("hand") or [])], 
     'reward':(state.get)("reward"), 
     'agent_reward':((state.get("agent_view") or {}).get)("reward")}


def compact_card(card: "dict[str, Any] | None") -> "dict[str, Any]":
    if not isinstance(card, dict):
        return {}
    return {'id':card.get("card_id") or card.get("id"), 
     'name':(card.get)("name"), 
     'upgraded':card.get("upgraded") or card.get("is_upgraded"), 
     'rarity':(card.get)("rarity"), 
     'type':card.get("card_type") or card.get("type"), 
     'cost':(card.get)("energy_cost", card.get("cost"))}


def item_card_payload(item: "dict[str, Any] | None") -> "dict[str, Any] | None":
    if not isinstance(item, dict):
        return None
    item_type = str(item.get("item_type") or item.get("type") or "").lower()
    if item.get("relic") or item.get("relic_id") or item.get("potion") or item.get("potion_id"):
        return None
    nested = item.get("card")
    if isinstance(nested, dict):
        merged = dict(nested)
        for key in ("index", "price", "gold_cost"):
            if key in item and key not in merged:
                merged[key] = item[key]
        return merged
    if item.get("card_id") or item_type == "card":
        return item
    if item.get("id") and (item.get("card_type") or item_type in {"attack", "skill", "power", "curse", "status"}):
        return item
    return None


def compact_relic(relic: "dict[str, Any] | None") -> "dict[str, Any]":
    if not isinstance(relic, dict):
        return {}
    return {'id':relic.get("relic_id") or relic.get("id"), 
     'name':(relic.get)("name"), 
     'tier':relic.get("tier") or relic.get("rarity"), 
     'stack':(relic.get)("stack"), 
     'description':(relic.get)("description")}


def compact_potion(potion: "dict[str, Any] | None") -> "dict[str, Any]":
    if not isinstance(potion, dict):
        return {}
    return {'id':potion.get("potion_id") or potion.get("id"), 
     'name':(potion.get)("name"), 
     'occupied':(potion.get)("occupied")}


def compact_shop_item(item: "dict[str, Any] | None") -> "dict[str, Any]":
    if not isinstance(item, dict):
        return {}
    card = item_card_payload(item)
    nested_relic = item.get("relic") if isinstance(item.get("relic"), dict) else None
    nested_potion = item.get("potion") if isinstance(item.get("potion"), dict) else None
    return {'index':(item.get)("index"), 
     'price':item.get("price") or item.get("cost") or item.get("gold_cost"), 
     'card':compact_card(card) if card else None, 
     'relic':compact_relic(nested_relic or item) if (nested_relic or item.get("relic_id")) else None, 
     'potion':compact_potion(nested_potion or item) if (nested_potion or item.get("potion_id")) else None, 
     'name':item.get("name") or item.get("label") or item.get("title"), 
     'type':item.get("item_type") or item.get("type")}


DEFENSIVE_POTION_IDS = {
    "BLOCK_POTION",
    "DEXTERITY_POTION",
    "FORTIFIER",
    "GHOST_IN_A_JAR",
    "HEART_OF_IRON",
    "REGEN_POTION",
    "SPEED_POTION",
    "WEAK_POTION",
}
BOSS_PREP_POTION_IDS = DEFENSIVE_POTION_IDS | {
    "DUPLICATION_POTION",
    "ENERGY_POTION",
    "EXPLOSIVE_AMPOULE",
    "FIRE_POTION",
    "GAMBLER_BREW",
    "POWER_POTION",
    "SKILL_POTION",
    "SWIFT_POTION",
}
ACT2_SURVIVAL_POTION_IDS = DEFENSIVE_POTION_IDS | {
    "ENERGY_POTION",
    "GAMBLER_BREW",
    "SKILL_POTION",
    "SWIFT_POTION",
}
BOSS_PREP_FLOORS = {12, 13, 14, 15, 16, 30, 31, 32, 46, 47, 48}
OFFENSIVE_DAMAGE_POTION_IDS = {"FIRE_POTION", "EXPLOSIVE_AMPOULE"}


def shop_potion_id(item: "dict[str, Any] | None") -> "str":
    if not isinstance(item, dict):
        return ""
    nested = item.get("potion") if isinstance(item.get("potion"), dict) else {}
    return str(
        item.get("potion_id")
        or nested.get("potion_id")
        or nested.get("id")
        or item.get("id")
        or item.get("name")
        or nested.get("name")
        or ""
    ).strip().upper().replace(" ", "_")


def journal_decision(kind, state, decision=None, payload=None):
    try:
        run = state.get("run") or {}
        hp, max_hp = player_hp(state)
        deck = run.get("deck") or run.get("cards") or []
        entry = {'ts':(time.strftime)("%Y-%m-%d %H:%M:%S"), 
         'kind':kind, 
         'run_id':run.get("run_id") or run.get("id"), 
         'character_id':(run.get)("character_id"), 
         'floor':run.get("floor") or run.get("current_floor"), 
         'screen':(state.get)("screen"), 
         'hp':hp, 
         'max_hp':max_hp, 
         'gold':run.get("gold") or run.get("player_gold"), 
         'plan':plan_summary(state), 
         'plan_detail':(deck_plan(state)).__dict__, 
         'relic_plan':relic_summary(state), 
         'decision':decision or {}, 
         'deck':[compact_card(card) for card in deck[:60] if isinstance(card, dict)], 
         'deck_count':len(deck) if (isinstance(deck, list)) else None, 
         'relics':[compact_relic(relic) for relic in relics(state) if isinstance(relic, dict)], 
         'potions':[compact_potion(potion) for potion in (run.get("potions") or run.get("player_potions") or []) if isinstance(potion, dict)]}
        if payload is not None:
            entry["payload"] = payload
        with JOURNAL_PATH.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False, separators=(',', ':')) + "\n")
    except Exception as exc:
        try:
            log(f"journal write failed {type(exc).__name__}: {exc}")
        finally:
            exc = None
            del exc


def first_number(value: "Any") -> "int | None":
    if isinstance(value, bool) or value is None:
        return
    if isinstance(value, (int, float)):
        return int(value)
    match = re.search("-?\\d+", str(value))
    if match:
        return int(match.group(0))


def text_blob(obj: "Any") -> "str":
    try:
        return json.dumps(obj, ensure_ascii=False).lower()
    except Exception:
        return str(obj).lower()


@lru_cache(maxsize=1)
def card_catalog() -> "dict[str, dict[str, Any]]":
    if not CARDS_PATH.exists():
        return {}
    try:
        raw_cards = json.loads(CARDS_PATH.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}
    catalog = {}
    for card in raw_cards if isinstance(raw_cards, list) else []:
        if not isinstance(card, dict):
            continue
        card_id = card_id_from_payload(card)
        if card_id:
            catalog[card_id] = card
    return catalog


def card_catalog_entry(card: "dict[str, Any] | None") -> "dict[str, Any]":
    if not card:
        return {}
    return card_catalog().get(card_id_from_payload(card), {})


def catalog_card_number(card: "dict[str, Any]", field: "str", var_name: "str | None" = None) -> "int | None":
    entry = card_catalog_entry(card)
    if not entry:
        return None
    amount = first_number(entry.get(field))
    vars_blob = entry.get("vars")
    if amount is None and var_name and isinstance(vars_blob, dict):
        amount = first_number(vars_blob.get(var_name))
    if amount is None:
        return None
    if card.get("upgraded") or card.get("is_upgraded"):
        upgrade = entry.get("upgrade")
        if isinstance(upgrade, dict):
            keys = [field, field.lower()]
            if var_name:
                keys.extend([var_name, var_name.lower()])
            for key in keys:
                delta = first_number(upgrade.get(key))
                if delta:
                    amount += delta
                    break
    return amount


@lru_cache(maxsize=1)
def event_catalog() -> "dict[str, dict[str, Any]]":
    if not EVENTS_PATH.exists():
        return {}
    try:
        raw = json.loads(EVENTS_PATH.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}
    catalog = {}
    for event in raw if isinstance(raw, list) else []:
        if not isinstance(event, dict):
            continue
        event_id = str(event.get("id") or "").upper()
        if event_id:
            catalog[event_id] = event
    return catalog


def _event_option_id_from_key(text_key: "str") -> "str":
    key = str(text_key or "")
    lowered = key.lower()
    marker = ".options."
    if marker in lowered:
        return key[lowered.rfind(marker) + len(marker):].split(".")[0].upper()
    return ""


def _event_id_from_key(text_key: "str") -> "str":
    key = str(text_key or "")
    lowered = key.lower()
    for marker in (".pages.", ".options."):
        if marker in lowered:
            return key[:lowered.find(marker)].upper()
    return ""


def _catalog_event_options(event: "dict[str, Any]") -> "list[dict[str, Any]]":
    options = []
    top_options = event.get("options")
    if isinstance(top_options, list):
        options.extend([opt for opt in top_options if isinstance(opt, dict)])
    pages = event.get("pages")
    if isinstance(pages, list):
        for page in pages:
            if not isinstance(page, dict):
                continue
            page_options = page.get("options")
            if isinstance(page_options, list):
                options.extend([opt for opt in page_options if isinstance(opt, dict)])
    return options


def event_option_catalog_entry(state: "dict[str, Any]", option: "dict[str, Any]") -> "dict[str, Any]":
    event = state.get("event") or {}
    text_key = str(option.get("text_key") or "")
    event_id = str(event.get("id") or event.get("event_id") or "").upper() or _event_id_from_key(text_key)
    option_id = str(option.get("id") or option.get("option_id") or "").upper() or _event_option_id_from_key(text_key)
    catalog_event = event_catalog().get(event_id)
    if not catalog_event:
        return {}
    title = str(option.get("title") or option.get("label") or option.get("text") or "").strip().lower()
    for catalog_option in _catalog_event_options(catalog_event):
        catalog_id = str(catalog_option.get("id") or catalog_option.get("option_id") or "").upper()
        if option_id and catalog_id == option_id:
            return catalog_option
    if title:
        for catalog_option in _catalog_event_options(catalog_event):
            catalog_title = str(catalog_option.get("title") or catalog_option.get("label") or "").strip().lower()
            if catalog_title and catalog_title == title:
                return catalog_option
    return {}


def event_option_blob(option: "dict[str, Any]", state: "dict[str, Any]") -> "str":
    entry = event_option_catalog_entry(state, option)
    if entry:
        return f"{text_blob(option)} {text_blob(entry)}"
    return text_blob(option)


def _plain_event_text(blob: "str") -> "str":
    text = re.sub(r"\[[^\]]+\]", " ", str(blob or "").lower())
    text = re.sub(r"\s+", " ", text)
    return text


def event_option_hp_loss(blob: "str") -> "int | None":
    text = _plain_event_text(blob)
    patterns = (
        r"lose\s+(\d+)\s+hp",
        r"take\s+(\d+)\s+damage",
        r"lose\s+(\d+)\s+health",
        r"失去\s*(\d+)\s*点?生命",
        r"受到\s*(\d+)\s*点?伤害",
    )
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return int(match.group(1))
    return None


def event_option_max_hp_loss(blob: "str") -> "int | None":
    text = _plain_event_text(blob)
    patterns = (
        r"lose\s+(\d+)\s+max hp",
        r"失去\s*(\d+)\s*点?最大生命",
    )
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return int(match.group(1))
    return None


def event_option_gold_loss(blob: "str") -> "int | None":
    text = _plain_event_text(blob)
    patterns = (
        r"lose\s+(\d+)\s+gold",
        r"pay\s+(\d+)\s+gold",
        r"失去\s*(\d+)\s*金币",
        r"支付\s*(\d+)\s*金币",
    )
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return int(match.group(1))
    return None


def card_text_blob(card: "dict[str, Any]") -> "str":
    parts = []
    for key in ('card_id', 'id', 'name', 'rules_text', 'resolved_rules_text', 'description',
                'description_raw'):
        value = card.get(key)
        if value:
            parts.append(str(value))

    catalog = card_catalog_entry(card)
    for key in ('id', 'name', 'description', 'description_raw', 'type', 'target'):
        value = catalog.get(key)
        if value:
            parts.append(str(value))

    for key in ('keywords', 'keyword_ids', 'keywordIds', 'tags', 'mods'):
        value = card.get(key)
        if isinstance(value, list):
            parts.extend((str(item) for item in value if item))
        elif value:
            parts.append(str(value))

    return " ".join(parts).lower()


def card_rules_blob(card: "dict[str, Any]") -> "str":
    parts = []
    for key in ('rules_text', 'resolved_rules_text', 'description', 'description_raw'):
        value = card.get(key)
        if value:
            parts.append(str(value))

    catalog = card_catalog_entry(card)
    for key in ('description', 'description_raw'):
        value = catalog.get(key)
        if value:
            parts.append(str(value))

    return " ".join(parts).lower()


def dynamic_value_amount(card: "dict[str, Any]", *names: "str") -> "int | None":
    wanted = {name.lower() for name in names}
    for value in card.get("dynamic_values") or []:
        name = str(value.get("name") or "").lower()
        if name not in wanted:
            continue
        amount = first_number(value.get("current_value"))
        if amount is not None:
            return amount


def card_grants_combat_resource(card: "dict[str, Any]") -> "bool":
    cid = normalized_card_id(card)
    if cid in frozenset({'VENERATE'}):
        return True
    if dynamic_value_amount(card, "Energy", "Stars", "Star", "star_resource") is not None:
        return True
    if card_doubles_energy(card):
        return True
    blob = card_text_blob(card)
    return any((token in blob for token in ('gain energy', 'gain [e]', 'gain star',
                                            'gain stars', '获得能量', '获得{stars', '获得 res://images/packed/sprite_fonts/star_icon')))


def card_resource_gain(card: "dict[str, Any]", state: "dict[str, Any] | None"=None) -> "int":
    amount = dynamic_value_amount(card, "Energy", "Stars", "Star", "star_resource")
    if amount is not None:
        return max(0, amount)
    if card_doubles_energy(card):
        return card_energy_gain(card, state)
    if card_grants_combat_resource(card):
        return 1
    return 0


def card_is_turn_only_dexterity_setup(card: "dict[str, Any]") -> "bool":
    cid = normalized_card_id(card)
    if cid == "ANTICIPATE":
        return True
    blob = card_rules_blob(card)
    return "dexterity" in blob and ("this turn" in blob or "until end of turn" in blob)


def card_doubles_energy(card: "dict[str, Any]") -> "bool":
    cid = normalized_card_id(card)
    if cid == "DOUBLE_ENERGY":
        return True
    blob = card_rules_blob(card)
    return "double your energy" in blob or "double energy" in blob


def card_energy_gain(card: "dict[str, Any]", state: "dict[str, Any] | None"=None) -> "int":
    amount = dynamic_value_amount(card, "Energy")
    if amount is not None:
        return max(0, amount)
    if card_doubles_energy(card):
        if state is None:
            return 1
        energy_after_cost = max(0, player_energy(state) - combat_card_energy_cost(card, state))
        return energy_after_cost
    blob = card_rules_blob(card)
    if "gain energy" in blob or "gain [e]" in blob or "获得能量" in blob:
        return first_number(blob) or 1
    return 0


def card_star_gain(card: "dict[str, Any]") -> "int":
    amount = dynamic_value_amount(card, "Stars", "Star", "star_resource")
    if amount is not None:
        return max(0, amount)
    blob = card_rules_blob(card)
    if "gain star" in blob or "获得{stars" in blob or "star_icon" in blob:
        return first_number(blob) or 1
    return 0


def card_effective_energy_cost_value(card: "dict[str, Any]") -> "Any":
    for key in ("cost_for_turn", "current_cost", "energy_cost", "display_cost", "cost"):
        if key not in card:
            continue
        value = card.get(key)
        if value is None or value == "":
            continue
        return value
    return ""


def card_costs_x(card: "dict[str, Any]") -> "bool":
    if normalized_card_id(card) == "BULLET_TIME":
        return False
    raw_value = card_effective_energy_cost_value(card)
    raw = str(raw_value).strip().upper()
    if raw == "X":
        return True
    for key in ("cost_for_turn", "current_cost", "energy_cost", "display_cost", "cost"):
        if str(card.get(key, "")).strip().upper() == "X":
            return True
    rules = card_rules_blob(card)
    has_x_variable = bool(re.search(r"(?<![a-z])x(?![a-z])", rules))
    if card.get("costs_x") and has_x_variable:
        return True
    if card.get("is_x_cost"):
        cost_number = first_number(raw_value)
        if cost_number is not None and cost_number < 0:
            return True
        if has_x_variable:
            return cost_number is None or cost_number <= 0
    if "cost x" in rules or "cost [blue]x" in rules:
        return True
    return False


def card_star_costs_x(card: "dict[str, Any]") -> "bool":
    raw_value = card.get("star_cost", card.get("stars_cost", ""))
    raw = str(raw_value).strip().upper()
    if raw == "X":
        return True
    rules = card_rules_blob(card)
    if (card.get("is_x_star_cost") or card.get("star_costs_x")) and re.search(r"(?<![a-z])x(?![a-z])", rules):
        return True
    return "star cost x" in rules


def draw_pile_count(state: "dict[str, Any]") -> "int | None":
    for source in (state.get("combat") or {}, state.get("run") or {}, state):
        for key in (
            "draw_pile_count",
            "drawPileCount",
            "draw_pile_size",
            "drawPileSize",
            "draw_count",
            "drawCount",
        ):
            amount = first_number(source.get(key))
            if amount is not None:
                return max(0, amount)
    combat = state.get("combat") or {}
    for key in ("draw_pile", "drawPile", "draw_deck", "drawDeck"):
        pile = combat.get(key)
        if isinstance(pile, list):
            return len(pile)
    return None


def card_has_unmet_play_condition(card: "dict[str, Any]", state: "dict[str, Any]") -> "bool":
    cid = normalized_card_id(card)
    blob = card_rules_blob(card)
    if cid == "GRAND_FINALE" or (
        "can only be played" in blob and "draw pile" in blob and "no cards" in blob
    ):
        count = draw_pile_count(state)
        return count is None or count > 0
    return False


def card_has_hand_end_damage(card: "dict[str, Any]") -> "bool":
    cid = normalized_card_id(card)
    if cid == "TOXIC":
        return True
    blob = card_rules_blob(card)
    return (
        "end of your turn" in blob
        and "hand" in blob
        and ("take" in blob or "damage" in blob)
    )


def card_hand_end_damage_amount(card: "dict[str, Any]") -> int:
    if not card_has_hand_end_damage(card):
        return 0
    amount = dynamic_value_amount(card, "Damage")
    if amount is None:
        amount = first_number(card_rules_blob(card))
    return max(1, amount or 5)


def card_is_currently_free(card: "dict[str, Any]") -> "bool":
    for key in ("free_to_play", "free_to_play_once", "is_free", "free"):
        if card.get(key) is True:
            return True
    for key in ("energy_cost", "current_cost", "cost_for_turn"):
        value = card.get(key)
        if value is None:
            continue
        if str(value).strip().lower() in {"free", "none"}:
            return True
    return False


def card_has_cost_reduction_text(card: "dict[str, Any]") -> "bool":
    blob = card_text_blob(card)
    return any((token in blob for token in (
        "free to play",
        "costs 0",
        "cost 0",
        "cost by 1",
        "costs 1 less",
        "reduce this card's cost",
        "lower the cost",
        "费用降低",
        "费用减少",
        "减少费用",
        "降低费用",
        "免费",
    )))


def free_followup_kinds(card: "dict[str, Any]") -> "set[str]":
    blob = card_text_blob(card)
    if not card_has_cost_reduction_text(card):
        return set()
    kinds: set[str] = set()
    if re.search(r"all .{0,24}cards.{0,24}hand.{0,24}free", blob) or re.search(r"所有.{0,12}手牌.{0,12}免费", blob):
        kinds.add("any")
    if "next attack" in blob or re.search(r"(下一张|下张|下一个|下个).{0,8}攻击", blob):
        kinds.add("attack")
    if "next skill" in blob or re.search(r"(下一张|下张|下一个|下个).{0,8}技能", blob):
        kinds.add("skill")
    if "next power" in blob or re.search(r"(下一张|下张|下一个|下个).{0,8}能力", blob):
        kinds.add("power")
    if "ethereal" in blob:
        kinds.add("ethereal")
    if "random card in your hand is free" in blob or "first" in blob and "cards you play" in blob and "free" in blob:
        kinds.add("any")
    if "free to play" in blob and not kinds:
        kinds.add("generated")
    return kinds


def free_followup_applies(card: "dict[str, Any]", other: "dict[str, Any]") -> "bool":
    kinds = free_followup_kinds(card)
    if not kinds:
        return False
    if "any" in kinds:
        return True
    other_type = known_card_type(other)
    other_blob = card_text_blob(other)
    if "attack" in kinds and is_attack(other):
        return True
    if "skill" in kinds and is_skill(other):
        return True
    if "power" in kinds and (other_type == "power" or "power" in other_blob or "能力" in other_blob):
        return True
    if "ethereal" in kinds and ("ethereal" in other_blob or "虚无" in other_blob):
        return True
    return False


def combat_card_energy_cost(card: "dict[str, Any]", state: "dict[str, Any]") -> "int":
    if card_is_currently_free(card):
        return 0
    if card_costs_x(card):
        return max(0, player_energy(state))
    return card_cost(card)


def combat_card_star_cost(card: "dict[str, Any]", state: "dict[str, Any]") -> "int":
    if card_star_costs_x(card):
        return max(0, player_stars(state))
    return card_star_cost(card)


def followup_card_energy_cost(trigger: "dict[str, Any]", other: "dict[str, Any]", state: "dict[str, Any]", remaining_energy: "int") -> "int":
    if free_followup_applies(trigger, other):
        return 0
    if card_is_currently_free(other):
        return 0
    if card_costs_x(other):
        return max(0, remaining_energy)
    return card_cost(other)


def relics(state: "dict[str, Any]") -> "list[dict[str, Any]]":
    return current_relics(state)


def has_relic(state: "dict[str, Any]", *ids: "str") -> "bool":
    wanted = {relic_id.upper() for relic_id in ids}
    return bool(current_relic_ids(state) & wanted)


def relic_attack_damage_bonus(state: "dict[str, Any]") -> "int":
    bonus = 0
    if has_relic(state, "VAJRA"):
        bonus += 1
    return bonus


def attack_relic_block(card: "dict[str, Any]", state: "dict[str, Any]") -> "int":
    if not is_attack(card):
        return 0
    block = 0
    if has_relic(state, "DAUGHTER_OF_THE_WIND"):
        block += 1
    return block


def attack_relic_combo_value(card: "dict[str, Any]", state: "dict[str, Any]") -> "tuple[float, list[str]]":
    if not is_attack(card):
        return (
         0.0, [])
    combat = state.get("combat") or {}
    attacks_played = played_this_turn(state, "attacks_played_this_turn")
    reasons = []
    score = 0.0
    if has_relic(state, "SHURIKEN"):
        if (attacks_played + 1) % 3 == 0:
            score += 16
            reasons.append("relic-shuriken")
    if has_relic(state, "KUNAI"):
        if (attacks_played + 1) % 3 == 0:
            score += 14
            reasons.append("relic-kunai")
    if has_relic(state, "ORNAMENTAL_FAN"):
        if (attacks_played + 1) % 3 == 0:
            incoming = sum((intent_damage(enemy) for enemy in combat.get("enemies") or [] if enemy_alive(enemy)))
            current_block = first_number(current_player(state).get("block")) or first_number(combat.get("block")) or 0
            score += 16 if incoming > current_block else 8
            reasons.append("relic-fan")
    if has_relic(state, "DAUGHTER_OF_THE_WIND"):
        incoming = sum((intent_damage(enemy) for enemy in combat.get("enemies") or [] if enemy_alive(enemy)))
        current_block = first_number(current_player(state).get("block")) or first_number(combat.get("block")) or 0
        if incoming > current_block:
            score += 4
            reasons.append("relic-attack-block")
    return (
     score, reasons)


def card_draws_cards(card: "dict[str, Any]") -> "bool":
    cid = normalized_card_id(card)
    if cid in frozenset({'CLOAK_AND_DAGGER', 'HIDDEN_DAGGERS', 'UP_MY_SLEEVE'}):
        return False
    for key in ('cards_draw', 'cards_drawn', 'draw', 'draw_cards'):
        amount = first_number(card.get(key))
        if amount is not None and amount > 0:
            return True

    amount = catalog_card_number(card, "cards_draw", "Cards")
    if amount is not None and amount > 0:
        return True

    for value in card.get("dynamic_values") or []:
        name = str(value.get("name") or "").lower()
        if name in frozenset({'cardsdrawn', 'drawcards', 'draw', 'carddraw'}):
            amount = first_number(value.get("current_value"))
            if amount is None or amount > 0:
                return True

    blob = card_text_blob(card)
    if re.search("\\bdraw\\s+(?:\\{[^}]+\\}|\\d+|a|one|two|three)\\s+cards?\\b", blob):
        return True
    if re.search("\\bdraw\\s+cards?\\b", blob):
        return True
    if re.search("\\u62bd(?!\\u724c\\u5806)(?:\\{[^}]+\\}|\\d+)?\\s*\\u5f20?\\u724c(?!\\u5806)", blob):
        return True
    return "抽牌" in blob and "抽牌堆" not in blob


def card_generates_combat_cards(card: "dict[str, Any]") -> "bool":
    roles = known_card_roles(card)
    if roles & {"card_generation", "shiv", "summon_osty"}:
        return True
    cid = normalized_card_id(card)
    if cid in frozenset({'DAGGER_THROW', 'POISONED_STAB'}):
        return False
    blob = card_rules_blob(card)
    return any((token in blob for token in ('add a ', 'add an ', 'add ', 'create ',
                                            'generate ', 'shiv', '加入你的手牌', '添加到你的手牌',
                                            '小刀')))


def generated_card_damage(card: "dict[str, Any]") -> "int":
    blob = card_text_blob(card)
    amount = dynamic_value_amount(card, "Cards")
    if amount is None:
        amount = catalog_card_number(card, "cards_draw", "Cards")
    count = max(1, amount or 1)
    cid = normalized_card_id(card)
    roles = known_card_roles(card)
    if "shiv" in roles:
        return count * 4
    if "shiv" in blob or "knife" in blob or "小刀" in blob:
        return count * 4
    if cid == "UP_MY_SLEEVE":
        return count * 4
    return 0


def orb_channel_value(card: "dict[str, Any]", state: "dict[str, Any]", *, incoming: "int", current_block: "int") -> "tuple[float, list[str]]":
    roles = known_card_roles(card)
    blob = card_text_blob(card)
    cid = normalized_card_id(card)
    if "orb" not in roles and "channel" not in blob and "evoke" not in blob:
        return 0.0, []

    score = 0.0
    reasons = []
    pressure = incoming > current_block
    if "frost" in blob or cid in frozenset({"COLD_SNAP", "COOLHEADED", "GLACIER", "CHILL"}):
        score += 9 if pressure else 5
        reasons.append("orb-frost")
    if "lightning" in blob or cid in frozenset({"ZAP", "BALL_LIGHTNING", "LIGHTNING_ROD"}):
        score += 10
        reasons.append("orb-lightning")
    if "dark" in blob or cid in frozenset({"DARKNESS", "DOOM_AND_GLOOM"}):
        score += 8
        reasons.append("orb-dark")
    if "evoke" in blob or cid == "DUALCAST":
        score += 12
        reasons.append("orb-evoke")
    if combat_card_energy_cost(card, state) == 0:
        score += 6
        reasons.append("orb-free")
    if relic_profile(state).has("CRACKED_CORE", "DATA_DISK", "RUNIC_CAPACITOR", "SYMBIOTIC_VIRUS"):
        score += 4
        reasons.append("orb-shell")
    return min(30.0, score), reasons


def card_star_cost(card: "dict[str, Any]") -> "int":
    if card_star_costs_x(card):
        return 99
    return max(0, first_number(card.get("star_cost") or card.get("stars_cost")) or 0)


def player_stars(state: "dict[str, Any]") -> "int":
    combat = state.get("combat") or {}
    player = current_player(state)
    for source in (player, combat):
        for key in ('stars', 'current_stars', 'star', 'star_resource'):
            amount = first_number(source.get(key))
            if amount is not None:
                return max(0, amount)

    return 0


def card_hits_all_enemies(card: "dict[str, Any]") -> "bool":
    catalog = card_catalog_entry(card)
    targets = " ".join(
        str(value or "")
        for value in (
            card.get("target"),
            card.get("target_type"),
            card.get("targetType"),
            catalog.get("target"),
            catalog.get("target_type"),
        )
    ).lower()
    compact_targets = targets.replace("_", "").replace(" ", "")
    blob = card_rules_blob(card)
    return (
        "aoe" in known_card_roles(card)
        or "allenemies" in compact_targets
        or "all enemies" in blob
        or "all enemies" in text_blob(card)
        or "所有敌人" in blob
    )


TURN_STRENGTH_DEBUFF_IDS = frozenset({"PIERCING_WAIL"})


def card_is_turn_strength_debuff(card: "dict[str, Any]") -> "bool":
    cid = normalized_card_id(card)
    if cid in TURN_STRENGTH_DEBUFF_IDS:
        return True
    roles = known_card_roles(card)
    blob = card_rules_blob(card)
    return (
        "strength" in roles
        and "debuff" in roles
        and ("lose" in blob or "loss" in blob)
        and ("this turn" in blob or "until end of turn" in blob)
        and ("all enemies" in blob or card_hits_all_enemies(card))
    )


def turn_strength_debuff_amount(card: "dict[str, Any]") -> "int":
    cid = normalized_card_id(card)
    if cid == "PIERCING_WAIL":
        return 8 if (card.get("upgraded") or card.get("is_upgraded")) else 6
    blob = card_rules_blob(card)
    numbers = [int(value) for value in re.findall(r"\d+", blob)]
    return max(0, min(max(numbers) if numbers else 0, 12))


def enemy_attack_hit_count(enemy: "dict[str, Any]") -> "int":
    intents = enemy.get("intents")
    if isinstance(intents, list):
        hits_total = 0
        for intent in intents:
            has_damage = first_number(intent.get("total_damage")) is not None or first_number(intent.get("damage")) is not None
            if has_damage:
                hits_total += max(1, first_number(intent.get("hits")) or 1)
        return max(1, hits_total)
    return max(1, first_number(enemy.get("intent_hits") or enemy.get("hits") or enemy.get("attack_count")) or 1)


def enemy_damage_after_card(card, target, enemies, state=None):
    total = 0
    weakens = "weak" in known_card_roles(card) or "虚弱" in card_text_blob(card).lower()
    strength_loss = turn_strength_debuff_amount(card) if card_is_turn_strength_debuff(card) else 0
    damage_state = state if state is not None else {"combat": {"enemies": enemies}}
    attack_damage = combat_card_damage(card, damage_state)
    hits_all = bool(attack_damage and card_hits_all_enemies(card))
    for idx, enemy in enumerate(enemies):
        if not enemy_alive(enemy):
            continue
        if hits_all and attack_damage >= enemy_hp(enemy):
            continue
        elif target is not None:
            if idx == target:
                if attack_damage >= enemy_hp(enemy):
                    continue
        damage = enemy_pressure_damage(enemy)
        if weakens:
            if target is not None:
                if idx == target and damage:
                    damage = int(damage * 0.75)
        if strength_loss and damage:
            damage = max(0, damage - strength_loss * enemy_attack_hit_count(enemy))
        total += damage

    return total


def affordable_non_potion_card_value(cards: "list[dict[str, Any]]", state: "dict[str, Any]", *, energy: int) -> "tuple[int, int, int]":
    spendable = 0
    block_value = 0
    damage_value = 0
    for card in cards:
        if card.get("playable") is False:
            continue
        cost = combat_card_energy_cost(card, state)
        if cost <= 0 or cost > energy:
            continue
        if card_has_consuming_or_harmful_cost(card, state):
            continue
        spendable += cost
        block_value += estimate_card_block(card) + attack_relic_block(card, state)
        damage_value += combat_card_damage(card, state) + generated_card_damage(card)
    return spendable, block_value, damage_value


def immediate_dex_potion_block_gain(cards: "list[dict[str, Any]]", state: "dict[str, Any]", *, energy: int, dex_gain: int) -> "int":
    block_cards = []
    for card in cards:
        if card.get("playable") is False:
            continue
        if estimate_card_block(card) + attack_relic_block(card, state) <= 0:
            continue
        if card_has_consuming_or_harmful_cost(card, state):
            continue
        cost = combat_card_energy_cost(card, state)
        if cost < 0 or cost > energy:
            continue
        block_cards.append((max(0, cost), dex_gain))

    block_cards.sort(key=(lambda p: (p[1] / max(1, p[0]), p[1])), reverse=True)
    total = 0
    energy_left = energy
    free_picks = 0
    for cost, gain in block_cards:
        if cost == 0:
            if free_picks >= 4:
                continue
            free_picks += 1
        elif cost > energy_left:
            continue
        else:
            energy_left -= cost
        total += gain

    return total


def remaining_affordable_block(cards, card=None, *, remaining_energy, state=None):
    block_cards = []
    for other in cards:
        if card is not None and same_card_instance(other, card):
            continue
        block = estimate_card_block(other)
        if state is not None:
            block += attack_relic_block(other, state)
        if block <= 0:
            continue
        cost = combat_card_energy_cost(other, state) if state is not None else card_cost(other)
        if cost <= remaining_energy:
            block_cards.append((block, cost))

    block_cards.sort(key=(lambda p: (p[0] / max(1, p[1]), p[0])), reverse=True)
    total = 0
    energy_left = remaining_energy
    for block, cost in block_cards:
        if cost > energy_left:
            continue
        total += block
        energy_left -= cost

    return total


def passive_end_turn_block(state: "dict[str, Any]", current_block: int) -> "int":
    if current_block <= 0 and has_relic(state, "ORICHALCUM"):
        return 6
    return 0


def current_player(state: "dict[str, Any]") -> "dict[str, Any]":
    combat = state.get("combat") or {}
    resource_player = {}
    for key in ('player', 'local_player', 'self'):
        if isinstance(combat.get(key), dict):
            resource_player = combat[key]
            break

    run = state.get("run") or {}
    local_player = {}
    players = combat.get("players") or run.get("players") or []
    for player in players:
        if player.get("is_local") or player.get("player_id") in ('1', 1):
            local_player = player
            break

    if not local_player:
        for key in ('player', 'local_player', 'current_player'):
            if isinstance(run.get(key), dict):
                local_player = run[key]
                break

    if not local_player:
        if players:
            local_player = players[0]
    if resource_player:
        if local_player:
            merged = dict(resource_player)
            for key, value in local_player.items():
                if value is not None:
                    merged[key] = value

            return merged
    return resource_player or local_player or {}


def player_hp(state: "dict[str, Any]") -> "tuple[int | None, int | None]":
    combat = state.get("combat") or {}
    run = state.get("run") or {}
    players = combat.get("players") or run.get("players") or []
    hp = max_hp = None
    for player in players:
        if player.get("is_local") or player.get("player_id") in ('1', 1):
            hp = first_number(player.get("hp") or player.get("current_hp") or player.get("health"))
            max_hp = first_number(player.get("max_hp") or player.get("max_health"))
            break

    if hp is None:
        hp = first_number(run.get("hp") or run.get("current_hp") or run.get("player_hp"))
    if max_hp is None:
        max_hp = first_number(run.get("max_hp") or run.get("player_max_hp"))
    if hp is None or max_hp is None:
        player = current_player(state)
        hp = hp if hp is not None else first_number(player.get("hp") or player.get("current_hp") or player.get("health"))
        max_hp = max_hp if max_hp is not None else first_number(player.get("max_hp") or player.get("max_health"))
    return (
     hp, max_hp)


def enemy_hp(enemy: "dict[str, Any]") -> "int":
    hp = first_number(enemy.get("current_hp") or enemy.get("hp") or enemy.get("health")) or 0
    block = first_number(enemy.get("block")) or 0
    return max(0, hp + block)


def enemy_alive(enemy: "dict[str, Any]") -> "bool":
    if enemy.get("is_dead") or enemy.get("dead") or enemy.get("escaped"):
        return False
    return enemy_hp(enemy) > 0


def intent_damage(enemy: "dict[str, Any]") -> "int":
    intents = enemy.get("intents")
    if isinstance(intents, list):
        total = 0
        for intent in intents:
            total_damage = first_number(intent.get("total_damage"))
            if total_damage is not None:
                total += max(0, total_damage)
                continue
            damage = first_number(intent.get("damage"))
            hits = first_number(intent.get("hits")) or 1
            if damage is not None:
                total += max(0, damage * max(1, hits))

        if total:
            return total
        return 0
    else:
        candidates = [
         enemy.get("total_damage"),
         enemy.get("intent_damage"),
         enemy.get("damage"),
         enemy.get("move_damage"),
         enemy.get("attack_damage")]
        hits = first_number(enemy.get("intent_hits") or enemy.get("hits") or enemy.get("attack_count")) or 1
        for candidate in candidates:
            val = first_number(candidate)
            if val is not None:
                return max(0, val * max(1, hits))

        blob = text_blob(enemy.get("intent") or enemy.get("intent_name") or enemy)
        nums = [int(x) for x in re.findall("\\d+", blob)]
        if not nums:
            return 0
    if "x" in blob:
        if len(nums) >= 2:
            return nums[0] * nums[1]
    if "attack" in blob or "damage" in blob or "攻击" in blob:
        return max(nums)
    return 0


def enemy_power_amount(enemy: "dict[str, Any]", *power_ids: "str") -> "int":
    wanted = {power_id.upper() for power_id in power_ids}
    total = 0
    for power in enemy.get("powers") or []:
        power_id = str(power.get("power_id") or power.get("id") or "").upper()
        name = str(power.get("name") or "").upper()
        if power_id in wanted or name in wanted:
            total += first_number(power.get("amount")) or 0

    return total


def enemy_is_minion(enemy: "dict[str, Any]") -> "bool":
    return bool(enemy_power_amount(enemy, "MINION_POWER", "MINION") or "MINION" in text_blob(enemy))


def enemy_status_pressure(enemy: "dict[str, Any]") -> "int":
    pressure = 0
    enemy_id = str(enemy.get("enemy_id") or enemy.get("id") or "").upper()
    blob = text_blob(enemy)
    for intent in enemy.get("intents") or []:
        pressure += first_number(intent.get("status_card_count")) or 0
        intent_type = str(intent.get("intent_type") or "").lower()
        if "debuff" in intent_type or "status" in intent_type:
            pressure += 2

    if any((token in enemy_id for token in ('ENTOMANCER', 'SLIME', 'SENTRY', 'CHOSEN',
                                            'VANTOM', 'INK', 'BOOK'))):
        pressure += 2
    if any((token in blob for token in ('dazed', 'slimed', 'wound', 'status_card',
                                        'statuscard', '晕眩', '黏液'))):
        pressure += 3
    if any((token in blob for token in ('burn', 'void', '晕眩', '黏液', '伤口', '灼伤', '状态牌'))):
        pressure += 4
    return pressure


def enemy_summon_pressure(enemy: "dict[str, Any]") -> "int":
    blob = text_blob({'enemy_id':enemy.get("enemy_id") or enemy.get("id"), 
     'intent':(enemy.get)("intent"), 
     'move_id':(enemy.get)("move_id"), 
     'raw':enemy})
    if any((token in blob for token in ('summon', 'spawn', 'minion', 'call'))):
        return 1
    return 0


def enemy_move_pressure(enemy: "dict[str, Any]") -> "tuple[int, float]":
    enemy_id = str(enemy.get("enemy_id") or enemy.get("id") or "").lower()
    blob = text_blob(
        {
            "enemy_id": enemy.get("enemy_id") or enemy.get("id"),
            "intent": enemy.get("intent"),
            "intent_name": enemy.get("intent_name"),
            "move_id": enemy.get("move_id"),
            "raw": enemy,
        }
    )
    damage_hint = 0
    utility = 0.0
    if "quick_slash" in blob:
        damage_hint = max(damage_hint, 14)
        utility += 4
    if "boomerang" in blob:
        damage_hint = max(damage_hint, 16)
        utility += 4
    if "claw_move" in blob:
        damage_hint = max(damage_hint, 12)
    if "rip_and_tear" in blob:
        damage_hint = max(damage_hint, 18)
    if "waterfall_giant" in enemy_id:
        if "ram_move" in blob:
            damage_hint = max(damage_hint, 10)
        if "pressure_gun_move" in blob:
            damage_hint = max(damage_hint, 25)
        if "siphon_move" in blob:
            utility += 10
    if "terror_eel" in enemy_id:
        if "thrashmove" in blob or "thrash" in blob:
            damage_hint = max(damage_hint, 12)
        if "crash" in blob:
            damage_hint = max(damage_hint, 24)
        if "terror" in blob or "stun" in blob:
            utility += 12
    if "power_dance" in blob:
        utility += 20
    if "ritual" in blob:
        utility += 18
    if "orb_of_frailty" in blob or "frailty" in blob:
        utility += 14
    if any(token in blob for token in ("debuff", "vulnerable", "weak", "frail")):
        utility += 8
    if any(token in blob for token in ("buff", "strength", "power")):
        utility += 8
    if any(token in blob for token in ("heal", "regenerate")):
        utility += 10
    if enemy_summon_pressure(enemy):
        utility += 18
    if "kin_follower" in enemy_id and not damage_hint:
        utility += 8
    return damage_hint, utility


def enemy_pressure_damage(enemy: "dict[str, Any]") -> "int":
    move_damage, _ = enemy_move_pressure(enemy)
    return max(intent_damage(enemy), move_damage)


def enemy_threat_score(enemy: "dict[str, Any]") -> "float":
    enemy_id = str(enemy.get("enemy_id") or enemy.get("id") or "").upper()
    blob = text_blob(enemy)
    _, move_utility = enemy_move_pressure(enemy)
    score = float(enemy_pressure_damage(enemy) * 2)
    score += move_utility
    score += enemy_power_amount(enemy, "STRENGTH_POWER", "STRENGTH") * 3.0
    score += enemy_status_pressure(enemy) * 5.0
    if any((token in enemy_id for token in ('KIN_FOLLOWER', 'CULTIST', 'HEALER', 'PRIEST'))):
        score += 14
    elif any((token in enemy_id for token in ('STRANGLER', 'SENTRY', 'JAXFRUIT'))):
        score += 8
    if any((token in blob for token in ('buff', 'debuff', 'heal', 'summon'))):
        score += 6
    if enemy_summon_pressure(enemy):
        score += 18
    hp = enemy_hp(enemy)
    if hp <= 12:
        score += 10
    else:
        if hp <= 25:
            score += 5
    return score


def enemy_target_score(enemy, enemies, *, damage, lethal):
    score = enemy_threat_score(enemy)
    alive = [candidate for candidate in enemies if enemy_alive(candidate)]
    minion_count = sum((1 for candidate in alive if enemy_is_minion(candidate)))
    has_real_enemy = any((not enemy_is_minion(candidate) for candidate in alive))
    is_minion = enemy_is_minion(enemy)
    status_pressure = enemy_status_pressure(enemy)
    _, move_utility = enemy_move_pressure(enemy)
    damage_pressure = enemy_pressure_damage(enemy)
    if is_minion and has_real_enemy:
        score -= max(0, 18 - min(16, damage_pressure + int(move_utility // 2)))
        if lethal:
            if damage_pressure + status_pressure * 3 + int(move_utility) >= 8:
                score += 28
        if damage_pressure >= 8:
            score += 12
        if move_utility >= 10:
            score += 8
        if damage >= max(1, enemy_hp(enemy) // 2) and (damage_pressure or move_utility):
            score += 6
    else:
        if status_pressure >= 3:
            score += 8
        else:
            if minion_count and enemy_summon_pressure(enemy):
                score += 12 + minion_count * 4
                if enemy_summon_pressure(enemy):
                    score += 20
        hp = enemy_hp(enemy)
        if lethal:
            score += max(0, 30 - hp)
        else:
            if damage >= max(1, hp // 2):
                score += 6
    return score


def estimate_card_damage(card: "dict[str, Any]") -> "int":
    blob = text_blob(card)
    cid = str(card.get("card_id") or card.get("id") or "").lower()
    name = str(card.get("name") or "").lower()
    catalog = card_catalog_entry(card)
    card_type = str(card.get("card_type") or card.get("type") or catalog.get("type") or "").lower()
    if card_type != "attack" and "deal" not in blob and "deals" not in blob and "造成" not in blob:
        return 0
    for value in card.get("dynamic_values") or []:
        if str(value.get("name") or "").lower() == "damage":
            amount = first_number(value.get("current_value"))
            if amount is not None:
                return max(0, amount)

    candidates = [
        card.get("damage"),
        card.get("base_damage"),
        card.get("attack_damage"),
        card.get("value"),
    ]
    for candidate in candidates:
        val = first_number(candidate)
        if val is not None:
            return max(0, val)

    catalog_damage = catalog_card_number(card, "damage", "Damage")
    if catalog_damage is not None:
        return max(0, catalog_damage)

    if card_type != "attack" and "deal" not in blob and "deals" not in blob:
        return 0
    if "bash" in cid or "bash" in name or "重锤" in name:
        return 8
    if "strike" in cid or "strike" in name or "打击" in name:
        return 6
    if "attack" in blob or "damage" in blob or "造成" in blob or "伤害" in blob:
        nums = [int(x) for x in re.findall("\\d+", blob)]
        if nums:
            return max(nums)
    return 0


def card_x_multiplier(card: "dict[str, Any]", state: "dict[str, Any]") -> "int":
    rules = card_rules_blob(card)
    if not re.search(r"(?<![a-z])x(?![a-z]).{0,18}(times|次)", rules):
        return 1
    if card_star_costs_x(card):
        amount = combat_card_star_cost(card, state)
    elif card_costs_x(card):
        amount = combat_card_energy_cost(card, state)
    else:
        amount = max(player_energy(state), player_stars(state))
    if relic_profile(state).has("CHEMICAL_X") and card_costs_x(card):
        amount += 2
    return max(0, amount)


def combat_card_damage(card: "dict[str, Any]", state: "dict[str, Any]") -> "int":
    cid = str(card.get("card_id") or card.get("id") or "").lower()
    if "body_slam" in cid:
        player = current_player(state)
        combat = state.get("combat") or {}
        return first_number(player.get("block")) or first_number(combat.get("block")) or 0
    base = estimate_card_damage(card)
    bonus, _ = relic_damage_bonus(card, state, base_damage=base)
    if is_attack(card) and base:
        bonus += relic_attack_damage_bonus(state)
    damage = max(0, base + bonus)
    return max(0, damage * card_x_multiplier(card, state))


def estimate_card_block(card: "dict[str, Any]") -> "int":
    blob = text_blob(card)
    cid = str(card.get("card_id") or card.get("id") or "").lower()
    name = str(card.get("name") or "").lower()
    catalog = card_catalog_entry(card)
    card_type = str(card.get("card_type") or card.get("type") or catalog.get("type") or "").lower()
    if "body_slam" in cid:
        return 0
    rules_blob = card_rules_blob(card)
    explicit_block = any(first_number(card.get(key)) is not None for key in ("block", "base_block"))
    explicit_block = explicit_block or catalog_card_number(card, "block", "Block") is not None
    if not explicit_block and "block" not in rules_blob and "格挡" not in rules_blob:
        return 0
    for value in card.get("dynamic_values") or []:
        if str(value.get("name") or "").lower() == "block":
            amount = first_number(value.get("current_value"))
            if amount is not None:
                return max(0, amount)

    candidates = [
     card.get("block"), card.get("base_block")]
    for candidate in candidates:
        val = first_number(candidate)
        if val is not None:
            return max(0, val)

    catalog_block = catalog_card_number(card, "block", "Block")
    if catalog_block is not None:
        return max(0, catalog_block)

    if card_type == "attack":
        return 0
    if "defend" in cid or "defend" in name or "防御" in name:
        return 5
    if "block" in blob or "格挡" in blob:
        nums = [int(x) for x in re.findall("\\d+", blob)]
        if nums:
            return max(nums)
    return 0


def card_cost(card: "dict[str, Any]") -> "int":
    if card_costs_x(card):
        return 99
    raw_cost = card_effective_energy_cost_value(card)
    if str(raw_cost).strip().lower() in {"free", "none"}:
        return 0
    cost = first_number(raw_cost)
    return max(0, cost if cost is not None else 1)


def playable_cards(state: "dict[str, Any]") -> "list[dict[str, Any]]":
    hand = (state.get("combat") or {}).get("hand") or []
    cards = []
    for i, card in enumerate(hand):
        if card.get("playable") is False:
            continue
        index = first_number(card.get("index"))
        card = dict(card)
        card["_index"] = i if index is None else index
        cards.append(card)

    return cards


def valid_targets(card: "dict[str, Any]", enemies: "list[dict[str, Any]]") -> "list[int]":
    explicit = card.get("valid_target_indices")
    if isinstance(explicit, list):
        valid = []
        for raw in explicit:
            idx = first_number(raw)
            if idx is not None and 0 <= idx < len(enemies) and enemy_alive(enemies[idx]):
                valid.append(int(idx))
        if valid:
            return valid
    return [i for i, enemy in enumerate(enemies) if enemy_alive(enemy)]


def safe_card_target(card: "dict[str, Any]", target: "int | None", enemies: "list[dict[str, Any]]", damage: "int"=0) -> "int | None":
    valid = valid_targets(card, enemies)
    if not valid:
        return None
    if target is not None and target in valid:
        return int(target)
    fallback = choose_enemy_for_damage(enemies, damage)
    if fallback is not None and fallback in valid:
        return int(fallback)
    return int(valid[0])


def choose_enemy_for_damage(enemies: "list[dict[str, Any]]", damage: "int") -> "int | None":
    alive = [(i, enemy) for i, enemy in enumerate(enemies) if enemy_alive(enemy)]
    if not alive:
        return
    return max(alive,
      key=(lambda p: (
     enemy_target_score((p[1]),
       enemies,
       damage=damage,
       lethal=(damage >= enemy_hp(p[1]))),
     -enemy_hp(p[1]))))[0]


def hand_has_affordable_lethal_sequence(cards: "list[dict[str, Any]]", state: "dict[str, Any]", *, energy: int) -> "bool":
    enemies = [(i, enemy_hp(enemy)) for i, enemy in enumerate((state.get("combat") or {}).get("enemies") or []) if enemy_alive(enemy)]
    if not enemies:
        return False
    attacks = []
    for card in cards:
        if card.get("playable") is False:
            continue
        if card_has_unmet_play_condition(card, state):
            continue
        if enemy_punishes_extra_card_play(state, card):
            continue
        if card_has_consuming_or_harmful_cost(card, state):
            continue
        damage = combat_card_damage(card, state)
        if damage <= 0:
            continue
        cost = combat_card_energy_cost(card, state)
        if cost < 0 or cost > energy:
            continue
        attacks.append((max(0, cost), damage, card_hits_all_enemies(card)))

    if not attacks:
        return False
    attacks.sort(key=(lambda item: (item[2], item[1] / max(1, item[0]), item[1])), reverse=True)

    def search(enemy_hps: "tuple[int, ...]", energy_left: int, remaining: "tuple[tuple[int, int, bool], ...]") -> bool:
        if all(hp <= 0 for hp in enemy_hps):
            return True
        if not remaining:
            return False
        if sum(damage for cost, damage, _ in remaining if cost <= energy_left) < max(0, sum(hp for hp in enemy_hps if hp > 0)):
            return False
        for idx, (cost, damage, hits_all) in enumerate(remaining):
            if cost > energy_left:
                continue
            rest = remaining[:idx] + remaining[idx + 1:]
            if hits_all:
                next_hps = tuple(max(0, hp - damage) for hp in enemy_hps)
                if search(next_hps, energy_left - cost, rest):
                    return True
            else:
                for enemy_idx, hp in enumerate(enemy_hps):
                    if hp <= 0:
                        continue
                    next_hps = list(enemy_hps)
                    next_hps[enemy_idx] = max(0, hp - damage)
                    if search(tuple(next_hps), energy_left - cost, rest):
                        return True
        return False

    return search(tuple(hp for _, hp in enemies), energy, tuple(attacks[:8]))


def is_attack(card: "dict[str, Any]") -> "bool":
    blob = text_blob(card)
    return estimate_card_damage(card) > 0 or "attack" in blob or "攻击" in blob


def is_bloodletting(card: "dict[str, Any]") -> "bool":
    cid = str(card.get("card_id") or card.get("id") or "").lower()
    return "bloodletting" in cid


def is_low_impact_play(card, damage, block):
    if damage or block:
        return False
    if card_draws_cards(card) or card_grants_combat_resource(card):
        return False
    blob = card_text_blob(card)
    return not any((k in blob for k in ('vulnerable', 'weak', 'strength', 'exhaust',
                                        'summon', 'osty', 'doom', 'channel', 'discard',
                                        'retain', '易伤', '虚弱', '力量', '消耗', '召唤', '丢弃',
                                        '保留')))


def is_skill(card: "dict[str, Any]") -> "bool":
    blob = text_blob(card)
    return estimate_card_block(card) > 0 or "skill" in blob or "技能" in blob


def normalized_card_id(card: "dict[str, Any] | None") -> "str":
    return card_id_from_payload(card)


def known_card_roles(card: "dict[str, Any]") -> "frozenset[str]":
    known = CARD_KNOWLEDGE.lookup(card)
    if known:
        return known.roles
    return frozenset()


def known_card_type(card: "dict[str, Any]") -> "str":
    known = CARD_KNOWLEDGE.lookup(card)
    return (known.type if known else str(card.get("card_type") or card.get("type") or "")).lower()


PURE_BLOCK_UTILITY_ROLES = frozenset({
    "draw",
    "energy",
    "power_scaling",
    "debuff",
    "weak",
    "vulnerable",
    "exhaust",
    "discard",
    "orb",
    "focus",
    "card_generation",
    "shiv",
    "deck_manipulation",
    "block_retention",
    "status_cleanup",
    "summon_osty",
    "doom",
    "strength",
    "dexterity",
    "poison",
    "upgrade_forge",
})

PURE_BLOCK_UTILITY_TEXT = (
    "draw",
    "energy",
    "discard",
    "exhaust",
    "vulnerable",
    "weak",
    "strength",
    "dexterity",
    "channel",
    "focus",
    "orb",
    "retain",
    "add ",
    "create",
    "generate",
    "shiv",
    "poison",
    "doom",
    "summon",
    "upgrade",
)


def discard_play_has_tactical_value(card: "dict[str, Any]", state: "dict[str, Any] | None") -> "bool":
    if state is None:
        return True
    combat = state.get("combat") or {}
    hand = combat.get("hand") or []
    if not hand:
        return True
    discard_like = card_is_discard_now(card) or card_discards_count(card) or card_cleans_baggage(card)
    if not discard_like:
        return False
    other_cards = [other for other in hand if not same_card_instance(other, card)]
    if not other_cards:
        return False
    if card_cleans_baggage(card) and any(card_is_generated_baggage(other) for other in other_cards):
        return True
    if any(normalized_card_id(other) in SILENT_SLY_RESOURCE_IDS for other in other_cards):
        return True
    discard_engines = SILENT_DISCARD_SCALING_IDS | SILENT_DISCARD_ENGINE_IDS
    if any(normalized_card_id(other) in discard_engines and other.get("playable") is not False for other in other_cards):
        return True
    best_target = max((discard_selection_score(other, state) for other in other_cards), default=-999.0)
    return best_target >= 140.0


def is_pure_block_play(
    card: "dict[str, Any]",
    *,
    damage: "int",
    block: "int",
    setup_score: "float",
    state: "dict[str, Any] | None" = None,
    current_block: "int" = 0,
) -> "bool":
    if block <= 0 or damage > 0 or setup_score > 0:
        return False
    if generated_card_damage(card) > 0:
        return False
    if card_draws_cards(card) or card_energy_gain(card) or card_star_gain(card) or card_grants_combat_resource(card):
        return False
    if card_generates_combat_cards(card) or card_has_cost_reduction_text(card):
        return False
    discard_like = card_is_discard_now(card) or card_discards_count(card) or card_cleans_baggage(card)
    discard_has_value = discard_like and discard_play_has_tactical_value(card, state)
    if discard_has_value:
        return False
    if state is not None and has_relic(state, "PARRYING_SHIELD") and current_block < 10 <= current_block + block:
        return False
    roles = known_card_roles(card)
    if discard_like and not discard_has_value:
        roles = roles - {"discard", "status_cleanup", "deck_manipulation"}
    if roles & PURE_BLOCK_UTILITY_ROLES:
        return False
    if known_card_type(card) == "power":
        return False
    blob = card_text_blob(card)
    utility_text = PURE_BLOCK_UTILITY_TEXT
    if discard_like and not discard_has_value:
        utility_text = tuple(token for token in PURE_BLOCK_UTILITY_TEXT if token != "discard")
    return not any((token in blob for token in utility_text))


def enemy_punishes_extra_card_play(state: "dict[str, Any]", card: "dict[str, Any]") -> "bool":
    combat = state.get("combat") or {}
    enemies = combat.get("enemies") or []
    card_is_skill = is_skill(card)
    cards_played = played_this_turn(state)
    for enemy in enemies:
        if not enemy_alive(enemy):
            continue
        enemy_blob = text_blob(enemy)
        enemy_id = str(enemy.get("enemy_id") or enemy.get("id") or enemy.get("name") or "").upper()
        power_blob = " ".join(text_blob(power) for power in enemy.get("powers") or [])
        combined = f"{enemy_id} {enemy_blob} {power_blob}"
        if any(token in combined for token in ("BEAT_OF_DEATH", "beat of death", "whenever you play", "每当你打出")):
            return True
        if any(token in combined for token in ("TIME_EATER", "TIME_WARP", "time warp", "12 cards")):
            if cards_played >= 10:
                return True
        if card_is_skill and any(token in combined for token in ("GREMLIN_NOB", "ANGER", "ENRAGE", "enrage", "技能牌")):
            return True
    return False


def card_has_consuming_or_harmful_cost(card: "dict[str, Any]", state: "dict[str, Any]") -> "bool":
    roles = known_card_roles(card)
    card_type = known_card_type(card)
    blob = card_rules_blob(card)
    if card_has_unmet_play_condition(card, state):
        return True
    if card_has_hand_end_damage(card):
        return False
    if is_bloodletting(card) or card_is_turn_strength_debuff(card):
        return True
    if normalized_card_id(card) in SILENT_SLY_RESOURCE_IDS:
        return True
    if card_costs_x(card) or card_star_costs_x(card):
        return True
    if card_has_sly(card):
        return True
    if roles & {"self_damage", "status_pollution"}:
        return True
    if "not_for_drafting" in roles and not card_cleans_baggage(card):
        return True
    if card_type in {"curse", "status"} and not card_cleans_baggage(card):
        return True
    discard_like = card_is_discard_now(card) or card_discards_count(card) or card_cleans_baggage(card)
    if discard_like and not discard_play_has_tactical_value(card, state):
        hand = (state.get("combat") or {}).get("hand") or []
        if any(not same_card_instance(other, card) for other in hand):
            return True
    if any(token in blob for token in ("lose hp", "self damage", "自伤", "失去生命")):
        return True
    if "exhaust" in blob or "消耗" in blob:
        if not (card_cleans_baggage(card) or card_is_generated_baggage(card)):
            return True
    return False


def card_is_safe_current_turn_spend(
    card: "dict[str, Any]",
    state: "dict[str, Any]",
    *,
    damage: int,
    block: int,
    generated_damage: int,
    setup_score: float,
    reduces_incoming: bool,
) -> "bool":
    if card.get("playable") is False:
        return False
    if enemy_punishes_extra_card_play(state, card):
        return False
    if card_has_consuming_or_harmful_cost(card, state):
        return False
    return bool(
        damage > 0
        or block > 0
        or generated_damage > 0
        or reduces_incoming
        or setup_score > 0
        or card_draws_cards(card)
        or card_energy_gain(card, state)
        or card_star_gain(card)
        or card_generates_combat_cards(card)
        or card_grants_combat_resource(card)
        or card_has_hand_end_damage(card)
    )


def player_energy(state: "dict[str, Any]") -> "int":
    combat = state.get("combat") or {}
    player = current_player(state)
    run = state.get("run") or {}
    for source in (player, combat, run):
        for key in ('energy', 'current_energy', 'player_energy'):
            amount = first_number(source.get(key))
            if amount is not None:
                return max(0, amount)

    return 3


def played_this_turn(state: "dict[str, Any]", key: "str"='cards_played_this_turn') -> "int":
    combat = state.get("combat") or {}
    player = current_player(state)
    for source in (player, combat):
        amount = first_number(source.get(key))
        if amount is not None:
            return max(0, amount)

    return 0


def hand_has_role(cards: "list[dict[str, Any]]", *roles: "str") -> "bool":
    wanted = set(roles)
    return any((known_card_roles(card) & wanted for card in cards))


def card_setup_value(card: "dict[str, Any]", state: "dict[str, Any]", cards: "list[dict[str, Any]]") -> "tuple[float, list[str]]":
    roles = set(known_card_roles(card))
    cid = normalized_card_id(card)
    blob = card_text_blob(card)
    cost = combat_card_energy_cost(card, state)
    damage = combat_card_damage(card, state)
    block = estimate_card_block(card) + attack_relic_block(card, state)
    combat = state.get("combat") or {}
    enemies = combat.get("enemies") or []
    incoming = sum((enemy_pressure_damage(enemy) for enemy in enemies if enemy_alive(enemy)))
    current_block = first_number(current_player(state).get("block")) or first_number(combat.get("block")) or 0
    energy_after_card = max(0, player_energy(state) - cost + card_energy_gain(card, state))
    stars = player_stars(state)
    cards_played = played_this_turn(state)
    plan = deck_plan(state)
    reasons = []
    score = 0.0
    baggage = hand_baggage_count(cards)
    payload_count = hand_playable_payload_count(cards, state)
    has_followup_attack = any((not same_card_instance(other, card) and combat_card_damage(other, state) > 0 and followup_card_energy_cost(card, other, state, energy_after_card) <= energy_after_card for other in cards))
    has_followup_block = any((not same_card_instance(other, card) and estimate_card_block(other) > 0 and followup_card_energy_cost(card, other, state, energy_after_card) <= energy_after_card for other in cards))
    affordable_missing_star = any((not same_card_instance(other, card) and combat_card_star_cost(other, state) > stars and combat_card_star_cost(other, state) <= stars + card_star_gain(card) for other in cards))
    draws_cards = card_draws_cards(card)
    grants_resource = card_grants_combat_resource(card)
    generates_cards = card_generates_combat_cards(card)
    is_power_setup = "power_scaling" in roles or known_card_type(card) == "power" or "power" in blob or "能力" in blob
    is_debuff_setup = any((token in roles for token in ('vulnerable', 'weak', 'debuff', 'doom'))) or any((token in blob for token in ('vulnerable', 'weak', 'doom', '易伤', '虚弱', '灾厄')))
    is_summon_setup = cid in frozenset({'BODYGUARD', 'SUMMON_FORTH', 'NECRO_MASTERY'}) or any((token in blob for token in ('summon', '召唤')))

    if damage or block:
        return (
         0.0, reasons)

    if card_is_turn_only_dexterity_setup(card):
        if incoming <= current_block or not has_followup_block:
            score -= 34
            reasons.append("skip-low-value-turn-dex")
        elif incoming <= current_block + 4 and not plan.needs_block:
            score -= 18
            reasons.append("small-turn-dex-window")

    if draws_cards:
        draw_bonus = 22 if cards_played == 0 else 12
        if baggage >= 3 and not card_cleans_baggage(card):
            draw_bonus -= min(18, baggage * 4)
            reasons.append("clogged-draw")
        if card_cleans_baggage(card):
            draw_bonus += min(14, baggage * 3)
            if baggage:
                reasons.append(f"draw-cleans-baggage={baggage}")
        if payload_count <= 2:
            draw_bonus += 8
            reasons.append("unclog-hand")
        score += draw_bonus
        reasons.append("setup-draw")

    if generates_cards:
        gen_bonus = 10 + min(16, generated_card_damage(card) * 1.2)
        if "shiv" in roles or "小刀" in blob:
            gen_bonus += 6
        score += gen_bonus
        reasons.append("setup-generate")

    if grants_resource:
        resource_bonus = 18 if has_followup_attack or has_followup_block else 8
        if affordable_missing_star:
            resource_bonus += 12
            reasons.append("enables-star-card")
        resource_gain = card_resource_gain(card, state)
        if resource_gain:
            resource_bonus += min(10, resource_gain * 4)
        score += resource_bonus
        reasons.append("setup-energy")

    free_kinds = free_followup_kinds(card)
    if free_kinds:
        best_unlock = 0.0
        for other in cards:
            if same_card_instance(other, card) or other.get("playable") is False:
                continue
            if not free_followup_applies(card, other):
                continue
            other_cost = card_cost(other)
            if other_cost <= 0:
                continue
            other_value = combat_card_damage(other, state) * 1.2 + (estimate_card_block(other) + attack_relic_block(other, state)) * 1.5
            if card_draws_cards(other) or card_generates_combat_cards(other):
                other_value += 6
            best_unlock = max(best_unlock, min(26.0, other_value + other_cost * 4.0))
        if best_unlock:
            score += best_unlock
            reasons.append("free-followup")

    if card_has_cost_reduction_text(card) and not free_kinds:
        score += 5
        reasons.append("cost-reduction")

    if is_power_setup:
        score += 30 if plan.needs_scaling or incoming <= current_block + 4 else 10
        reasons.append("setup-power")
        if incoming > current_block + 10 and not block:
            score -= 20
            reasons.append("risky-power")

    if is_debuff_setup:
        debuff_bonus = 20
        if any((enemy_alive(enemy) and enemy_hp(enemy) >= 18 for enemy in enemies)):
            debuff_bonus += 8
        if "weak" in roles or "虚弱" in blob:
            debuff_bonus += 6 if incoming > current_block else 2
        if "doom" in roles or "灾厄" in blob:
            debuff_bonus += 8
        score += debuff_bonus
        reasons.append("setup-debuff")

    if is_summon_setup:
        summon_bonus = 26
        if cid == "BODYGUARD" and incoming > current_block:
            summon_bonus += 10
        if any((combat_card_damage(other, state) > 0 for other in cards if not same_card_instance(other, card))):
            summon_bonus += 6
        if cid == "UNLEASH":
            summon_bonus += 8
        score += summon_bonus
        reasons.append("setup-summon")
        if cid == "BODYGUARD" and not incoming:
            score -= 14
            reasons.append("wait-bodyguard")

    if "exhaust" in roles or "exhaust" in blob or "消耗" in blob:
        score += 8
        reasons.append("setup-exhaust")
    if "deck_manipulation" in roles:
        score += 8
        reasons.append("setup-manip")
    if has_followup_attack and any((token in roles for token in ('vulnerable', '易伤'))):
        score += 8
    if incoming > current_block and cost >= 2 and not block and not has_followup_block:
        score -= 14
        reasons.append("save-energy-for-block")
    return (
     score, reasons)


def card_keywords(card: "dict[str, Any]") -> "set[str]":
    raw_keywords = card.get("keywords") or card.get("keyword_ids") or card.get("keywordIds") or []
    if isinstance(raw_keywords, str):
        raw_keywords = [
         raw_keywords]
    return {str(keyword).strip().lower() for keyword in raw_keywords if keyword}


def card_has_sly(card: "dict[str, Any]") -> "bool":
    cid = normalized_card_id(card)
    blob = text_blob(card)
    return cid in SILENT_SLY_KEYWORD_IDS or "sly" in card_keywords(card) or "奇巧" in card_keywords(card) or '"sly"' in blob


def card_is_discard_now(card: "dict[str, Any]") -> "bool":
    cid = normalized_card_id(card)
    roles = known_card_roles(card)
    if cid in SILENT_DISCARD_NOW_IDS:
        return True
    if "discard" not in roles:
        return False
    blob = text_blob(card)
    if "discarded this turn" in blob:
        return False
    return "draw" in roles or "discard your hand" in blob or "discard 1" in blob


def card_is_generated_baggage(card: "dict[str, Any]") -> "bool":
    cid = normalized_card_id(card)
    card_type = known_card_type(card)
    rarity = str(card.get("rarity") or "").lower()
    roles = known_card_roles(card)
    blob = text_blob(card)
    return cid in STATUS_BAGGAGE_IDS or cid.endswith("_STATUS") or cid.endswith("_CURSE") or cid.endswith("_WOUND") or card_type in frozenset({'quest', 'status', 'curse'}) or "curse" in rarity or "not_for_drafting" in roles or "status" in blob or "curse" in blob


def hand_baggage_count(cards: "list[dict[str, Any]]") -> "int":
    return sum((1 for card in cards if card_is_generated_baggage(card)))


def hand_playable_payload_count(cards: "list[dict[str, Any]]", state: "dict[str, Any]") -> "int":
    count = 0
    for card in cards:
        if card.get("playable") is False or card_is_generated_baggage(card):
            continue
        if combat_card_damage(card, state) or estimate_card_block(card) or card_draws_cards(card):
            count += 1

    return count


def card_discards_count(card: "dict[str, Any]") -> "int":
    cid = normalized_card_id(card)
    if cid in frozenset({'STORM_OF_STEEL', 'SHADOW_STEP', 'CALCULATED_GAMBLE'}):
        return 99
    if cid == "HIDDEN_DAGGERS":
        return 2
    blob = card_rules_blob(card)
    if "discard your hand" in blob or "丢弃你的手牌" in blob:
        return 99
    if "discard" in blob or "丢弃" in blob or "弃" in blob:
        nums = [int(x) for x in re.findall("\\d+", blob)]
        return max(1, nums[0] if nums else 1)
    if card_is_discard_now(card):
        return 1
    return 0


def card_cleans_baggage(card: "dict[str, Any]") -> "bool":
    cid = normalized_card_id(card)
    roles = known_card_roles(card)
    blob = card_rules_blob(card)
    if card_is_generated_baggage(card):
        if card_draws_cards(card) or "exhaust" in blob or "消耗" in blob:
            return True
    return cid in frozenset({'SECOND_WIND', 'HIDDEN_DAGGERS', 'ACROBATICS', 'RECYCLE', 'CALCULATED_GAMBLE', 'TRUE_GRIT', 'SEVER_SOUL', 'STORM_OF_STEEL', 'DAGGER_THROW', 'PREPARED', 'SURVIVOR'}) or "discard" in roles or "discard" in blob or "exhaust a " in blob or "exhaust all" in blob or "exhaust 1" in blob or "丢弃" in blob or "弃" in blob or "消耗1" in blob or "消耗一" in blob or "消耗所有" in blob


def discarded_this_turn(state: "dict[str, Any]") -> "int":
    combat = state.get("combat") or {}
    player = current_player(state)
    for source in (combat, player):
        for key in ('cards_discarded_this_turn', 'discarded_this_turn', 'discard_count_this_turn',
                    'turn_discard_count'):
            amount = first_number(source.get(key))
            if amount is not None:
                return max(0, amount)

    return 0


def same_card_instance(left: "dict[str, Any]", right: "dict[str, Any]") -> "bool":
    left_index = first_number(left.get("_index", left.get("index")))
    right_index = first_number(right.get("_index", right.get("index")))
    if left_index is not None:
        if right_index is not None:
            return left_index == right_index
    return left is right


def discard_candidate_pool(state: "dict[str, Any]") -> "list[dict[str, Any]]":
    combat = state.get("combat") or {}
    hand = combat.get("hand") or []
    if hand:
        return hand
    selection = state.get("selection") or {}
    cards = selection.get("cards")
    if isinstance(cards, list):
        return cards
    agent_selection = (state.get("agent_view") or {}).get("selection") or {}
    cards = agent_selection.get("cards")
    if isinstance(cards, list):
        return cards
    return []


def remaining_turn_value_after_discard(cards: "list[dict[str, Any]]", state: "dict[str, Any]") -> "float":
    combat = state.get("combat") or {}
    enemies = combat.get("enemies") or []
    incoming = sum((enemy_pressure_damage(enemy) for enemy in enemies if enemy_alive(enemy)))
    current_block = first_number(current_player(state).get("block")) or first_number(combat.get("block")) or 0
    need = max(0, incoming - current_block)
    hp, max_hp = player_hp(state)
    hp_ratio = hp / max_hp if (hp and max_hp) else 1.0
    energy = player_energy(state)
    playable = []
    for card in cards[:10]:
        if not isinstance(card, dict) or card.get("playable") is False:
            continue
        cost = combat_card_energy_cost(card, state)
        if cost > energy or card_has_unmet_play_condition(card, state):
            continue
        playable.append((card, cost))

    block_weight = 0.35
    damage_weight = 2.0
    chip_penalty = 0.6
    if need > 0:
        block_weight = 4.8 if hp_ratio < 0.55 else 3.0
        damage_weight = 1.7 if hp_ratio < 0.55 else 2.05
        chip_penalty = 4.8 if hp_ratio < 0.55 else 2.2

    best = 0.0
    count = len(playable)
    for mask in range(1 << count):
        spent = 0
        block = 0
        damage = 0
        reduction = 0
        utility = 0.0
        lethal = False
        for bit, (card, cost) in enumerate(playable):
            if not (mask & (1 << bit)):
                continue
            spent += cost
            if spent > energy:
                break
            card_damage = combat_card_damage(card, state)
            damage += card_damage + generated_card_damage(card)
            block += estimate_card_block(card) + attack_relic_block(card, state)
            target = choose_enemy_for_damage(enemies, card_damage) if card.get("requires_target") else None
            if card_damage and any(enemy_alive(enemy) and card_damage >= enemy_hp(enemy) for enemy in enemies):
                lethal = True
            post_incoming = enemy_damage_after_card(card, target, enemies, state)
            reduction += max(0, incoming - post_incoming)
            if card_draws_cards(card):
                utility += 6.0
            if card_energy_gain(card, state) or card_star_gain(card):
                utility += 8.0
            if card_generates_combat_cards(card) or card_grants_combat_resource(card):
                utility += 4.0
            roles = known_card_roles(card)
            if roles & {"weak", "debuff", "strength", "block_retention", "intangible"}:
                utility += 6.0
        else:
            reduced_incoming = max(0, incoming - reduction)
            remaining_need = max(0, reduced_incoming - current_block)
            covered = min(block, remaining_need)
            gap = max(0, remaining_need - covered)
            value = (
                damage * damage_weight
                + covered * block_weight
                + min(reduction, incoming) * (block_weight + 0.8)
                + utility
                - gap * chip_penalty
            )
            if lethal:
                value += 35 + min(30, incoming)
            if value > best:
                best = value

    return best


def discard_selection_score(card: "dict[str, Any]", state: "dict[str, Any]") -> "float":
    cid = normalized_card_id(card)
    roles = known_card_roles(card)
    card_type = known_card_type(card)
    rarity = str(card.get("rarity") or "").lower()
    combat = state.get("combat") or {}
    hand = combat.get("hand") or []
    enemies = combat.get("enemies") or []
    incoming = sum((enemy_pressure_damage(enemy) for enemy in enemies if enemy_alive(enemy)))
    current_block = first_number(current_player(state).get("block")) or first_number(combat.get("block")) or 0
    energy = player_energy(state)
    hp, max_hp = player_hp(state)
    hp_ratio = hp / max_hp if (hp and max_hp) else 1.0
    cost = combat_card_energy_cost(card, state)
    dmg = combat_card_damage(card, state)
    block = estimate_card_block(card) + attack_relic_block(card, state)
    need = max(0, incoming - current_block)
    text = text_blob(card)
    starter_attack = cid in {
        "STRIKE",
        "STRIKE_IRONCLAD",
        "STRIKE_SILENT",
        "STRIKE_DEFECT",
        "STRIKE_NECROBINDER",
        "STRIKE_REGENT",
    } or "strike" in text
    starter_block = cid in {
        "DEFEND",
        "DEFEND_IRONCLAD",
        "DEFEND_SILENT",
        "DEFEND_DEFECT",
        "DEFEND_NECROBINDER",
        "DEFEND_REGENT",
    } or "defend" in text
    current_turn_playable = (
        card.get("playable") is not False
        and cost <= energy
        and not card_has_unmet_play_condition(card, state)
    )
    pool = discard_candidate_pool(state) or hand
    remaining_cards = [other for other in pool if isinstance(other, dict) and not same_card_instance(other, card)]
    score = remaining_turn_value_after_discard(remaining_cards, state)
    if card_is_generated_baggage(card):
        score += 220
    if card_has_hand_end_damage(card):
        score += 200
    if cid in SILENT_SLY_RESOURCE_IDS:
        score += 170
    elif card_has_sly(card):
        score += 60 if not current_turn_playable else 25
    if current_turn_playable and cid in SILENT_DISCARD_SCALING_IDS | SILENT_DISCARD_ENGINE_IDS:
        score -= 100
    if "not_for_drafting" in roles or card_type in frozenset({'status', 'curse', 'quest'}) or "curse" in rarity:
        score += 240
    if not current_turn_playable:
        score += 28
    critical_pressure = bool(
        need > 0
        and (
            hp_ratio < 0.30
            or hp is not None and need >= max(1, hp)
            or need >= 20
        )
    )
    survival_roles = {"block_retention", "weak", "debuff", "strength", "dexterity"}
    if current_turn_playable and roles & survival_roles:
        score -= 10
        if incoming > current_block:
            score -= min(26, 6 + (incoming - current_block) * 1.0)
        if critical_pressure:
            score -= 90
    if current_turn_playable and incoming > current_block and roles & {"weak", "debuff", "strength"}:
        reduction_target = None
        if card.get("requires_target") or dmg > 0:
            reduction_target = choose_enemy_for_damage(enemies, max(1, dmg))
            valid = valid_targets(card, enemies)
            if reduction_target is None and valid:
                reduction_target = valid[0]
            elif reduction_target is not None and valid and reduction_target not in valid:
                reduction_target = valid[0]
        incoming_reduced_by = max(0, incoming - enemy_damage_after_card(card, reduction_target, enemies, state))
        if incoming_reduced_by:
            reduction_protection = 18.0 + incoming_reduced_by * (8.0 if critical_pressure else 4.0)
            if cost <= 0:
                reduction_protection += 28.0
            if hp_ratio < 0.35:
                reduction_protection += 24.0
            if incoming_reduced_by >= max(1, need):
                reduction_protection += 24.0
            score -= min(150.0, reduction_protection)
    if current_turn_playable and block > 0 and critical_pressure:
        score -= min(220, 80 + block * 8 + need * (3.0 if hp_ratio < 0.45 else 1.5))
    if starter_attack:
        score += 10 if incoming <= current_block else 4
    if starter_block:
        if need <= 0:
            score += 14
        elif block <= 5:
            score += 6
    if cost >= 3 and cid not in SILENT_DISCARD_SCALING_IDS | SILENT_DISCARD_ENGINE_IDS and not current_turn_playable:
        score += 12
    if current_turn_playable and cost == 0 and not card_has_sly(card) and not card_is_generated_baggage(card):
        score -= 4
    return score


def starter_card_counts(plan: "Any") -> "tuple[int, int]":
    strikes = sum(int(plan.ids.get(card_id, 0) or 0) for card_id in BASIC_STRIKE_IDS)
    defends = sum(int(plan.ids.get(card_id, 0) or 0) for card_id in BASIC_DEFEND_IDS)
    return strikes, defends


def low_value_block_remove_candidate(card: "dict[str, Any]", plan: "Any") -> "bool":
    roles = known_card_roles(card)
    cid = normalized_card_id(card)
    block = estimate_card_block(card)
    if cid in BASIC_DEFEND_IDS:
        return block <= 6
    if block <= 0 or block > 6:
        return False
    if roles & {"draw", "energy", "star_resource", "power_scaling", "debuff", "weak", "vulnerable", "dexterity", "block_retention"}:
        return False
    known = CARD_KNOWLEDGE.lookup(card)
    if known is not None and plan.wants_archetype(known):
        return False
    rarity = str(card.get("rarity") or "").lower()
    return rarity in {"", "basic", "common"}


def remove_selection_score(card: "dict[str, Any]", state: "dict[str, Any]") -> "float":
    cid = normalized_card_id(card)
    roles = known_card_roles(card)
    card_type = known_card_type(card)
    rarity = str(card.get("rarity") or "").lower()
    plan = deck_plan(state)
    strike_count, defend_count = starter_card_counts(plan)
    starter_strike = cid in BASIC_STRIKE_IDS
    starter_defend = cid in BASIC_DEFEND_IDS
    low_value_block = low_value_block_remove_candidate(card, plan)
    score = 0.0
    if card.get("selected") or card.get("is_selected") or card.get("chosen") or card.get("disabled"):
        return -999.0
    if card_type in frozenset({'curse', 'status', 'quest'}) or "curse" in rarity or "not_for_drafting" in roles:
        score += 260
    if starter_strike:
        score += 120
        if plan.needs_damage:
            score -= 52
        if strike_count <= 2 and plan.needs_damage:
            score -= 24
        if not plan.needs_damage and strike_count >= 4:
            score += 10
    if starter_defend:
        score += 112
        if plan.needs_block:
            score -= 54
        if not plan.needs_block and defend_count >= 4:
            score += 30
        if defend_count >= strike_count and not plan.needs_block:
            score += 12
    elif low_value_block:
        score += 78
        if plan.needs_block:
            score -= 36
        elif plan.block_count >= 7:
            score += 20
    if low_value_block and not plan.needs_block:
        score += 10
        if plan.character_id == "SILENT" and (plan.attack_count >= 6 or not plan.needs_damage):
            score += 18
    if starter_strike and plan.character_id == "SILENT" and not plan.needs_damage and plan.needs_block:
        score += 14
    if card.get("playable") is False:
        score += 70
    if plan.wants_removal:
        score += 12
    known = CARD_KNOWLEDGE.lookup(card)
    if known is not None and plan.wants_archetype(known):
        score -= 55
    if roles & {'draw', 'energy', 'star_resource', 'power_scaling', 'debuff'}:
        score -= 25
    if card.get("upgraded") or card.get("is_upgraded"):
        score -= 35
    if str(card.get("rarity") or "").lower() in frozenset({'rare', 'uncommon'}):
        score -= 18
    score += relic_remove_card_modifier(card, state)
    return score


def best_discard_target_score(cards, state, *, exclude=None):
    scores = []
    for card in cards:
        if exclude is not None and same_card_instance(card, exclude):
            continue
        scores.append(discard_selection_score(card, state))
    if scores:
        return max(scores)
    return -999.0


def discard_combat_modifier(card, state, playable, *, incoming, current_block):
    cid = normalized_card_id(card)
    combat = state.get("combat") or {}
    hand = combat.get("hand") or []
    baggage = hand_baggage_count(hand)
    payload_count = hand_playable_payload_count(hand, state)
    best_target = best_discard_target_score(hand, state, exclude=card)
    has_playable_discard = any((not same_card_instance(other, card) and card_is_discard_now(other) for other in playable))
    has_memento = any((normalized_card_id(other) == "MEMENTO_MORI" for other in hand))
    discarded = discarded_this_turn(state)
    score = 0.0
    reasons = []
    if cid in SILENT_SLY_RESOURCE_IDS:
        score -= 85
        reasons.append("discard-sly-resource")
    else:
        if card_has_sly(card):
            if card_cost(card) >= 2:
                if best_target >= 45:
                    score -= 15
                    reasons.append("prefer-discard-sly")
                elif card_is_discard_now(card):
                    if baggage:
                        clean_bonus = min(42, baggage * 9 + card_discards_count(card) * 4)
                        score += clean_bonus
                        reasons.append(f"clear-baggage={baggage}")
                    elif payload_count <= 2:
                        if baggage:
                            score += 14
                            reasons.append("recover-clogged-hand")
                    if best_target >= 140:
                        score += 32
                        reasons.append("discard-sly-target")
                    else:
                        if best_target >= 55:
                            score += 14
                            reasons.append("discard-fodder")
                        else:
                            if cid in SILENT_WHOLE_HAND_DISCARD_IDS:
                                score -= 24
                                reasons.append("weak-whole-hand-discard")
                            elif has_memento:
                                score += 12
                                reasons.append("feeds-memento")
                            if cid == "PREPARED":
                                score += 10
                            else:
                                if cid == "ACROBATICS":
                                    score += 8 if best_target >= 45 else 2
                                else:
                                    if cid == "DAGGER_THROW":
                                        score += 7
                                    else:
                                        if cid == "HIDDEN_DAGGERS":
                                            score += 10 if best_target >= 45 else -4
                                        else:
                                            if cid == "SURVIVOR":
                                                if incoming > current_block:
                                                    score += 10
                if cid in SILENT_DISCARD_ENGINE_IDS:
                    covered = incoming <= current_block + estimate_card_block(card)
                    if covered or incoming <= current_block + 4:
                        score += 16
                        reasons.append("discard-engine")
            else:
                score -= 8
                reasons.append("unsafe-discard-engine")
            if cid == "MEMENTO_MORI":
                if discarded:
                    bonus = min(36, discarded * 8)
                    score += bonus
                    reasons.append(f"discarded={discarded}")
                else:
                    if has_playable_discard:
                        score -= 24
                        reasons.append("wait-for-discard")
        elif cid in SILENT_WHOLE_HAND_DISCARD_IDS:
            valuable_cards = 0
            playable_memento = False
            for other in hand:
                if same_card_instance(other, card):
                    continue
                other_id = normalized_card_id(other)
                other_value = combat_card_damage(other, state) + estimate_card_block(other)
                if not other_id in SILENT_DISCARD_ENGINE_IDS | SILENT_DISCARD_SCALING_IDS:
                    if other_value >= 12:
                        valuable_cards += 1
                    if other_id == "MEMENTO_MORI" and other.get("playable") is not False:
                        playable_memento = True

            if playable_memento:
                score -= 35
                reasons.append("save-memento")
            if valuable_cards >= 2:
                if best_target < 140:
                    score -= 18
                    reasons.append("protect-hand-value")
    return (
     score, reasons)


def followup_combo_value(card, state, cards, target, *, incoming, current_block, energy, stars):
    combat = state.get("combat") or {}
    enemies = combat.get("enemies") or []
    first_cost = combat_card_energy_cost(card, state)
    remaining_energy = max(0, energy - first_cost + card_energy_gain(card, state))
    remaining_stars = stars + card_star_gain(card)
    first_block = estimate_card_block(card) + attack_relic_block(card, state)
    post_incoming = enemy_damage_after_card(card, target, enemies, state)
    block_after = current_block + first_block
    baggage = hand_baggage_count(cards)
    reasons = []
    choices = []
    for other in cards:
        if same_card_instance(other, card) or other.get("playable") is False:
            continue
        if card_is_generated_baggage(other):
            if not card_cleans_baggage(other):
                continue
        if combat_card_star_cost(other, state) > remaining_stars:
            continue
        other_cost = followup_card_energy_cost(card, other, state, remaining_energy)
        if other_cost > remaining_energy:
            continue
        other_damage = combat_card_damage(other, state)
        other_block = estimate_card_block(other) + attack_relic_block(other, state)
        other_target = choose_enemy_for_damage(enemies, other_damage) if other_damage else None
        value = 0.0
        if other_damage:
            value += other_damage * 1.05
            if other_target is not None:
                if 0 <= other_target < len(enemies):
                    enemy = enemies[other_target]
                    if other_damage >= enemy_hp(enemy):
                        value += 28 + min(20, intent_damage(enemy) * 1.4)
        if other_block:
            need = max(0, post_incoming - block_after)
            value += min(other_block, need) * 2.0 + max(0, other_block - need) * 0.15
        if card_draws_cards(other):
            value += 4
        if card_generates_combat_cards(other):
            value += min(20, 6 + generated_card_damage(other) * 1.0)
        if card_is_discard_now(other):
            if baggage:
                value += min(18, baggage * 5)
            if known_card_roles(other) & {"debuff", "weak", "vulnerable"}:
                value += 5
        if free_followup_applies(card, other) and card_cost(other) > 0:
            value += min(14, card_cost(other) * 4)
        if value > 0:
            choices.append((value, other_cost, normalized_card_id(other) or str(other.get("name") or "followup")))

    if not choices:
        return (
         0.0, reasons)
    choices.sort(key=(lambda item: (item[0] / max(0.5, item[1]), item[0])), reverse=True)
    total = 0.0
    spent = 0
    picked = []
    free_picks = 0
    for value, cost, card_id in choices:
        if cost == 0:
            if free_picks >= 4:
                continue
            free_picks += 1
            total += value
            picked.append(card_id)
        else:
            if spent + cost > remaining_energy:
                continue
            spent += cost
            total += value
            picked.append(card_id)
        if len(picked) >= 3:
            break

    if total <= 0:
        return (
         0.0, reasons)
    score = min(46.0, total * 0.55)
    if card_energy_gain(card, state) or card_star_gain(card):
        reasons.append("unlocks-resource-chain")
    else:
        if card_draws_cards(card) or card_is_discard_now(card):
            reasons.append("unlocks-card-flow")
        else:
            if card_generates_combat_cards(card):
                reasons.append("unlocks-generated-chain")
            else:
                reasons.append("keeps-combo-line")
    return (
     score, reasons)


def choose_combat_action(state: "dict[str, Any]") -> "tuple[str, dict[str, int | None], str]":
    combat = state.get("combat") or {}
    enemies = combat.get("enemies") or []
    cards = playable_cards(state)
    if not cards:
        return (
         "end_turn", {}, "no playable cards")
    else:
        incoming = sum((intent_damage(e) for e in enemies if enemy_alive(e)))
        player = current_player(state)
        current_block = first_number(player.get("block")) or first_number(combat.get("block")) or 0
        hp, max_hp = player_hp(state)
        hp_ratio = hp / max_hp if (hp and max_hp) else 1.0
        energy = player_energy(state)
        cards_played = played_this_turn(state)
        total_attack_damage = sum((combat_card_damage(c, state) for c in cards if is_attack(c) or combat_card_damage(c, state) > 0))
        alive_hp = sum((enemy_hp(e) for e in enemies if enemy_alive(e)))
        can_sweep_lethal = bool(alive_hp and total_attack_damage >= alive_hp)
        damage_gap = max(0, incoming - current_block)
        hand_block = sum((estimate_card_block(c) + attack_relic_block(c, state) for c in cards))
        can_cover_with_hand = current_block + hand_block >= incoming
        baggage = hand_baggage_count(cards)
        payload_count = hand_playable_payload_count(cards, state)
        survival_pressure = damage_gap >= 18 or hp is not None and damage_gap >= max(10, int(hp * 0.35)) or hp_ratio < 0.45 and damage_gap >= 8
        candidates = []
        for card in cards:
            dmg = combat_card_damage(card, state)
            block = estimate_card_block(card)
            cost = card_cost(card)
            generated_damage = generated_card_damage(card)
            cid = str(card.get("card_id") or card.get("id") or card.get("name") or "").lower()
            blob = text_blob(card)
            target = None
            if card.get("requires_target"):
                target = choose_enemy_for_damage(enemies, dmg)
                valid = valid_targets(card, enemies)
                if target is not None and valid:
                    if target not in valid:
                        target = valid[0]
            score = 0.0
            relic_score, relic_reasons = attack_relic_combo_value(card, state)
            score += relic_score
            if dmg:
                score += dmg * 2.0
                if target is not None:
                    ehp = enemy_hp(enemies[target])
                    target_score = enemy_target_score((enemies[target]),
                      enemies,
                      damage=dmg,
                      lethal=(dmg >= ehp))
                    score += target_score * 0.45
                    if dmg >= ehp:
                        score += 80 + max(0, incoming) + target_score
                    score += intent_damage(enemies[target]) * 0.8
            effective_block = block + attack_relic_block(card, state)
            if generated_damage:
                score += generated_damage * (2.2 if incoming < current_block + block + 8 else 1.4)
            if effective_block:
                needed = max(0, incoming - current_block)
                block_weight = 4.8 if survival_pressure and not can_sweep_lethal else 2.4
                score += min(effective_block, needed) * block_weight + max(0, effective_block - needed) * (0.25 if incoming else 0.05)
            if "bash" in cid or "vulnerable" in blob or "易伤" in blob:
                score += 30
            if card_draws_cards(card):
                score += 5
            face_blob = card_text_blob(card)
            if "strength" in face_blob or "力量" in face_blob or "能力" in face_blob:
                score += 22
            score -= cost * 3.2
            setup_score, setup_reasons = card_setup_value(card, state, cards)
            score += setup_score
            combo_score, combo_reasons = followup_combo_value(card,
              state,
              cards,
              target,
              incoming=incoming,
              current_block=current_block,
              energy=energy,
              stars=(player_stars(state)))
            score += combo_score
            is_setup_only = setup_score > 0 and not effective_block and dmg <= 0 and generated_damage <= 0
            if damage_gap and not can_cover_with_hand:
                if is_setup_only:
                    pressure_penalty = 12 + min(60, damage_gap * (2.0 if hp_ratio < 0.55 else 1.0))
                    score -= pressure_penalty
                    setup_reasons.append("defer-setup-under-pressure")
                if setup_score > 0:
                    if cards_played == 0:
                        score += 10
            if survival_pressure:
                if not can_sweep_lethal:
                    if effective_block:
                        score += 10
                    else:
                        if setup_score > 0 and can_cover_with_hand and cost < energy:
                            score -= 4
                        else:
                            if target is not None and dmg >= enemy_hp(enemies[target]):
                                score += 8
                            else:
                                score -= 12
            remaining_energy = max(0, energy - cost + card_energy_gain(card, state))
            post_incoming = enemy_damage_after_card(card, target, enemies, state)
            post_block = current_block + effective_block
            post_extra_block = remaining_affordable_block(cards, card, remaining_energy=remaining_energy, state=state)
            if generated_damage:
                if remaining_energy > 0:
                    post_extra_block += 0
            post_gap = max(0, post_incoming - post_block)
            preventable_gap = max(0, post_incoming - post_block - post_extra_block)
            hp_after = (hp if hp is not None else 999) - preventable_gap
            if preventable_gap and not can_sweep_lethal:
                if hp_after <= 0:
                    score -= 300
                    setup_reasons.append("would-die")
                else:
                    if not survival_pressure:
                        if hp_ratio < 0.55 or preventable_gap >= 12:
                            score -= min(90, preventable_gap * 3.0)
                            setup_reasons.append(f"unsafe-gap={preventable_gap}")
                        if post_gap:
                            if effective_block:
                                score += min(18, (damage_gap - post_gap) * 1.3)
                        elif target is not None and dmg >= enemy_hp(enemies[target]):
                            if post_incoming < incoming:
                                score += min(30, (incoming - post_incoming) * 2.0)
                                setup_reasons.append("kill-reduces-damage")
                        elif target is not None:
                            target_hp = enemy_hp(enemies[target]) if (0 <= target < len(enemies)) else None
                            knowledge_score, knowledge_reasons = CARD_KNOWLEDGE.combat_modifier(card,
                              state,
                              damage=dmg,
                              block=block,
                              cost=cost,
                              incoming=incoming,
                              current_block=current_block,
                              hp_ratio=hp_ratio,
                              target_hp=target_hp)
                            score += knowledge_score
                            discard_score, discard_reasons = discard_combat_modifier(card,
                              state,
                              cards,
                              incoming=incoming,
                              current_block=current_block)
                            score += discard_score
                            if baggage and card_cleans_baggage(card):
                                score += min(30, baggage * 6)
                                all_baggage = payload_count == 0 or baggage >= max(2, len(cards) - 1)
                                if all_baggage:
                                    score += 18
                                    combo_reasons.append("escape-clog")
                        elif baggage >= 3 and card_draws_cards(card):
                            if not card_cleans_baggage(card) and not effective_block:
                                score -= min(24, baggage * 5)
                                combo_reasons.append("draw-into-clog")
                        if incoming >= 12:
                            if effective_block:
                                score += 8 if survival_pressure else 4
                        if incoming >= 20:
                            if hp_ratio < 0.65:
                                if effective_block:
                                    score += 12
                        if effective_block:
                            if damage_gap:
                                score += min(effective_block, damage_gap) * (4.0 if hp_ratio < 0.35 else 2.2)
                        if incoming >= 24:
                            if hp_ratio < 0.5 and not effective_block:
                                if dmg < 20:
                                    score -= 18
                        if incoming == 0 and effective_block and dmg == 0:
                            if setup_score <= 0:
                                score -= 25
                    elif cost >= 3:
                        if target is not None:
                            if dmg < enemy_hp(enemies[target]):
                                score -= 8
                    if is_bloodletting(card):
                        score += 4
                        if hp_ratio < 0.65 or incoming > current_block:
                            score -= 120
                    if is_low_impact_play(card, dmg, block):
                        score -= 20 if incoming else 4
                    all_reasons = setup_reasons + combo_reasons + relic_reasons + knowledge_reasons + discard_reasons
                    knowledge_note = f' knowledge={",".join(all_reasons[:3])}' if all_reasons else ""
                    candidates.append((
                     score,
                     card,
                     target,
                     f"dmg={dmg} block={block} incoming={incoming} gap={damage_gap} energy={energy}{knowledge_note}"))

        return candidates or (
         "end_turn", {}, "no candidate")
    best_score, card, target, reason = max(candidates, key=(lambda x: x[0]))
    damage_floor = policy_number("combat.damage_floor", -20.0)
    play_any_damage = policy_bool("combat.play_any_damage", True)
    best_damage = combat_card_damage(card, state)
    best_block = estimate_card_block(card)
    if not (best_score <= damage_floor):
        if not (play_any_damage and best_damage):
            return (
             "end_turn", {}, f"best card not worth playing score={best_score:.1f}")
        kwargs = {"card_index": (int(card["_index"]))}
        if card.get("requires_target"):
            target = safe_card_target(card, target, enemies, best_damage)
            if target is None:
                return (
                 "end_turn", {}, "no valid target for best card")
            kwargs["target_index"] = target
    return (
     "play_card", kwargs, f'{card.get("name") or card.get("card_id")} {reason}')


def score_reward_card(card: "dict[str, Any]", state: "dict[str, Any]") -> "float":
    blob = text_blob(card)
    cid = str(card.get("card_id") or card.get("id") or card.get("name") or "").lower()
    name = str(card.get("name") or "").lower()
    dmg = estimate_card_damage(card)
    block = estimate_card_block(card)
    score = 0.0
    score += dmg * 1.6 + block * 1.1
    if "body_slam" in cid:
        score -= 18
    if any((k in blob for k in ('draw', '抽牌', '抽', 'energy', '能量', 'strength', '力量',
                                'vulnerable', '易伤'))):
        score += 12
    if any((k in blob for k in ('exhaust', '消耗'))):
        score += 2
    if any((k in cid + name for k in ('strike', 'defend', '打击', '防御'))):
        score -= 10
    if any((k in blob for k in ('power', '能力'))):
        score += 8
    if any((k in blob for k in ('rare', '稀有'))):
        score += 6
    cost = card_cost(card)
    if cost >= 3:
        score -= 4
    else:
        if cost == 0:
            score += 3
        else:
            knowledge_score, knowledge_reasons = CARD_KNOWLEDGE.reward_modifier(card,
              state,
              damage=dmg,
              block=block,
              cost=cost)
            if knowledge_reasons:
                card["_knowledge_reasons"] = knowledge_reasons[:5]
            score += knowledge_score
            relic_score, relic_reasons = relic_card_reward_modifier(card, state, damage=dmg, block=block, cost=cost)
            score += relic_score
            if relic_reasons:
                current_reasons = card.get("_knowledge_reasons") or []
                card["_knowledge_reasons"] = (current_reasons + relic_reasons)[:8]
            known = CARD_KNOWLEDGE.lookup(card)
            plan = deck_plan(state)
            if known is not None:
                score += table_bonus("reward.card_bonus", known.id)
                for role in known.roles:
                    score += table_bonus("reward.role_bonus", role)

                for archetype in known.archetypes:
                    score += table_bonus("reward.archetype_bonus", archetype)

                if plan.wants_archetype(known):
                    score += policy_number("reward.plan_match_bonus", 0.0)
                else:
                    if plan.focused:
                        if known.archetypes:
                            score -= policy_number("reward.focused_off_plan_penalty", 0.0)
                        else:
                            need_bonus = policy_table("reward.need_bonus")
                            if plan.needs_damage:
                                if "attack" in known.roles:
                                    score += float(need_bonus.get("damage_attack", 0) or 0)
                            if plan.needs_block:
                                if "block" in known.roles:
                                    score += float(need_bonus.get("block_block", 0) or 0)
                            if plan.needs_draw:
                                if "draw" in known.roles:
                                    score += float(need_bonus.get("draw_draw", 0) or 0)
                            if plan.needs_scaling:
                                if "power_scaling" in known.roles:
                                    score += float(need_bonus.get("scaling_power", 0) or 0)
                            if plan.needs_aoe:
                                if "aoe" in known.roles:
                                    score += float(need_bonus.get("aoe_aoe", 0) or 0)
                            roles = known.roles
                            utility = bool(roles & REWARD_UTILITY_ROLES)
                            matching_plan = plan.wants_archetype(known)
                            fills_need = plan.needs_damage and "attack" in roles or plan.needs_block and "block" in roles or plan.needs_draw and "draw" in roles or plan.needs_scaling and "power_scaling" in roles or plan.needs_aoe and "aoe" in roles
                            density_policy = policy_table("reward.density_penalty")
                            if plan.focused:
                                if known.archetypes and not matching_plan:
                                    if not utility:
                                        if not fills_need:
                                            score -= float(density_policy.get("focused_off_plan", 16) or 0)
                            if plan.combat_ready:
                                if plan.card_count >= 18 and not matching_plan:
                                    if not utility:
                                        if not fills_need:
                                            score -= float(density_policy.get("combat_ready_off_plan", 12) or 0)
                            if plan.card_count >= 22:
                                if not matching_plan:
                                    if not utility:
                                        if not fills_need:
                                            score -= float(density_policy.get("large_generic", 10) or 0)
                        if plan.card_count >= 26 and not matching_plan:
                            if not utility:
                                if not fills_need:
                                    score -= float(density_policy.get("very_large_generic", 12) or 0)
                    elif plan.card_count >= 18:
                        if roles <= {"attack"}:
                            if not plan.needs_damage:
                                score -= float(density_policy.get("generic_attack", 14) or 0)
                if plan.card_count >= 20 and roles <= {"block"}:
                    if not plan.needs_block:
                        score -= float(density_policy.get("generic_block", 8) or 0)
        return score


def deck_plan(state: "dict[str, Any]"):
    return CARD_KNOWLEDGE.deck_plan(state)


def silent_discard_outlet_count(plan: "Any") -> int:
    outlet_ids = SILENT_DISCARD_NOW_IDS | SILENT_WHOLE_HAND_DISCARD_IDS | {
        "ACROBATICS",
        "CALCULATED_GAMBLE",
        "DAGGER_THROW",
        "HIDDEN_DAGGERS",
        "PREPARED",
        "SURVIVOR",
        "TOOLS_OF_THE_TRADE",
    }
    return sum(int(plan.ids.get(card_id, 0) or 0) for card_id in outlet_ids)


def deck_skill_count(state: "dict[str, Any]") -> int:
    run = state.get("run") or {}
    deck = run.get("deck") or run.get("cards") or []
    if not isinstance(deck, list):
        return 0
    return sum(1 for card in deck if isinstance(card, dict) and is_skill(card))


def plan_summary(state: "dict[str, Any]") -> "str":
    return deck_plan(state).summary()


def reward_need_filled(known: "Any", plan: "Any") -> "bool":
    roles = known.roles
    return bool(plan.needs_damage and "attack" in roles or plan.needs_block and "block" in roles or plan.needs_draw and "draw" in roles or plan.needs_scaling and "power_scaling" in roles or plan.needs_aoe and "aoe" in roles)


def silent_attack_reward_density_penalty(
    card: "dict[str, Any]",
    plan: "Any",
    roles: "frozenset[str]",
    cid_norm: str,
    cost: int,
    generated_damage: int=0,
) -> "tuple[float, list[str]]":
    if str(getattr(plan, "character_id", "") or "").upper() != "SILENT":
        return 0.0, []
    if plan.card_count < 16 or plan.needs_damage:
        return 0.0, []
    if "attack" not in roles and not is_attack(card):
        return 0.0, []

    density_policy = policy_table("reward.density_penalty")
    penalty = 0.0
    reasons: list[str] = []
    duplicate_count = int(plan.ids.get(cid_norm, 0) or 0)
    strategic_roles = roles & {
        "aoe",
        "card_generation",
        "debuff",
        "poison",
        "shiv",
        "strength",
        "vulnerable",
        "weak",
    }
    real_cycle = bool(roles & {"discard", "energy"}) and cid_norm not in SILENT_PSEUDO_DRAW_ATTACK_REWARD_IDS
    pseudo_draw_attack = bool(
        cid_norm in SILENT_PSEUDO_DRAW_ATTACK_REWARD_IDS
        or ("draw" in roles and is_attack(card) and cost >= 2)
    )

    if plan.attack_count >= plan.block_count + 2:
        value = float(density_policy.get("attack_heavy_ratio", 12) or 12)
        penalty += value
        reasons.append(f"attack-heavy={value:.0f}")
    if plan.needs_draw and not real_cycle:
        value = float(density_policy.get("attack_when_needs_engine", 14) or 14)
        penalty += value
        reasons.append(f"needs-engine={value:.0f}")
    if duplicate_count:
        value = float(density_policy.get("duplicate_attack_plan_card", 12) or 12)
        value += min(18.0, max(0, duplicate_count - 1) * 6.0)
        penalty += value
        reasons.append(f"duplicate-attack={value:.0f}")
    if cost >= 2:
        value = float(density_policy.get("expensive_attack_surplus", 16) or 16)
        penalty += value
        reasons.append(f"expensive-attack={value:.0f}")
    if pseudo_draw_attack:
        value = float(density_policy.get("pseudo_draw_attack", 18) or 18)
        value += float(density_policy.get("slow_engine_attack", 24) or 24)
        penalty += value
        reasons.append(f"pseudo-draw-attack={value:.0f}")
    if not strategic_roles and generated_damage <= 0 and not real_cycle:
        value = float(density_policy.get("attack_surplus", 18) or 18)
        penalty += value
        reasons.append(f"attack-surplus={value:.0f}")
    if plan.wants_removal and plan.removable_count >= 8:
        value = min(18.0, max(0, plan.removable_count - 6) * 4.0)
        if value:
            penalty += value
            reasons.append(f"dirty-deck={value:.0f}")
    return penalty, reasons


def reward_take_threshold(state, card, score):
    plan = deck_plan(state)
    table = policy_table("reward.take_threshold")
    if plan.card_count <= 12:
        threshold = float(table.get("early", 22) or 22)
    else:
        if plan.needs_damage or plan.needs_block:
            threshold = float(table.get("needs_core", 38) or 38)
        else:
            if not plan.needs_draw:
                if plan.needs_scaling or plan.needs_aoe:
                    threshold = float(table.get("needs_support", 45) or 45)
            else:
                threshold = float(table.get("stable", 55) or 55)
    if plan.focused:
        threshold += float(table.get("focused_bonus", 10) or 0)
    if plan.combat_ready:
        if plan.card_count >= 18:
            threshold += float(table.get("combat_ready_bonus", 8) or 0)
    if plan.card_count >= 20:
        threshold += float(table.get("large_deck_bonus", 8) or 0)
    if plan.card_count >= 24:
        threshold += float(table.get("very_large_deck_bonus", 12) or 0)
    if plan.card_count >= 30:
        threshold += float(table.get("huge_deck_bonus", 12) or 0)
    known = CARD_KNOWLEDGE.lookup(card) if card else None
    if known is not None:
        if plan.wants_archetype(known):
            threshold -= float(table.get("plan_match_discount", 12) or 0)
        if known.roles & REWARD_UTILITY_ROLES:
            threshold -= float(table.get("utility_discount", 8) or 0)
        if reward_need_filled(known, plan):
            threshold -= float(table.get("need_discount", 8) or 0)
        if plan.focused:
            if known.archetypes and not plan.wants_archetype(known):
                if not known.roles & REWARD_UTILITY_ROLES:
                    threshold += float(table.get("off_plan_focused_bonus", 12) or 0)
    if score <= -500:
        return 999.0
    threshold += relic_reward_threshold_delta(card, state, score)
    return max(8.0, threshold)


def reward_options(state: "dict[str, Any]") -> "list[dict[str, Any]]":
    reward = state.get("reward") or {}
    for key in ('cards', 'card_options', 'options'):
        val = reward.get(key)
        if isinstance(val, list) and any((item.get("card_id") or item.get("id") for item in val if isinstance(item, dict))):
            return val

    agent_reward = (state.get("agent_view") or {}).get("reward") or {}
    for key in ('cards', 'card_options', 'options'):
        val = agent_reward.get(key)
        if isinstance(val, list) and any((item.get("card_id") or item.get("id") for item in val if isinstance(item, dict))):
            return val

    selection = state.get("selection") or {}
    for key in ('cards', 'options', 'items'):
        val = selection.get(key)
        if isinstance(val, list) and any((item.get("card_id") or item.get("id") for item in val if isinstance(item, dict))):
            return val

    return []


def claimable_reward_options(state: "dict[str, Any]") -> "list[dict[str, Any]]":
    reward = state.get("reward") or {}
    for key in ('rewards', 'items', 'options'):
        val = reward.get(key)
        if isinstance(val, list) and val:
            return val

    agent_reward = (state.get("agent_view") or {}).get("reward") or {}
    for key in ('rewards', 'items', 'options'):
        val = agent_reward.get(key)
        if isinstance(val, list) and val:
            return val

    return []


def reward_is_potion(reward: "dict[str, Any]") -> "bool":
    reward_type = str(reward.get("reward_type") or reward.get("type") or "").lower()
    blob = text_blob(reward)
    return reward_type == "potion" or bool(reward.get("potion_id")) or "potion" in blob or "药水" in blob


def potion_slots_full(state: "dict[str, Any]") -> "bool":
    potions = (state.get("run") or {}).get("potions") or []
    if not isinstance(potions, list) or not potions:
        return False
    seen_slot = False
    for potion in potions:
        if not isinstance(potion, dict):
            continue
        seen_slot = True
        if not bool(potion.get("occupied") or potion.get("potion_id") or potion.get("id")):
            return False
    return seen_slot


def reward_blocked_by_inventory(reward: "dict[str, Any]", state: "dict[str, Any]") -> "bool":
    return reward_is_potion(reward) and potion_slots_full(state)


def choose_claim_reward_index(state: "dict[str, Any]") -> "int | None":
    rewards = claimable_reward_options(state)
    best = (-999.0, None, None)
    scored_options = []
    for i, reward in enumerate(rewards):
        if reward.get("claimed") or reward.get("disabled") or reward.get("is_locked") or reward.get("claimable") is False:
            continue
        idx = first_number(reward.get("index") or reward.get("i"))
        effective_idx = i if idx is None else idx
        blob = text_blob(reward)
        score = 0.0
        if "card" in blob or "鍗＄墝" in blob:
            score += 45
        if "relic" in blob or "閬楃墿" in blob:
            score += 42
        if "potion" in blob or "鑽\ue21b按" in blob:
            score += 15
        if not "gold" in blob:
            if "閲戝竵" in blob:
                score += 18
            if score > best[0]:
                best = (
                 score, int(effective_idx), reward)

    if best[1] is not None:
        log(f"claim reward idx={best[1]} score={best[0]:.1f}", best[2])
    return best[1]


def choose_reward_index(state: "dict[str, Any]") -> "int | None":
    options = reward_options(state)
    card_like = []
    for i, option in enumerate(options):
        blob = text_blob(option)
        if "skip" in blob or "跳过" in blob:
            continue
        if "card" in blob or option.get("card_id") or option.get("id"):
            idx = first_number(option.get("index"))
            card_like.append((i if idx is None else idx, option))

    if card_like:
        scored = [(score_reward_card(card, state), idx, card) for idx, card in card_like]
        scored.sort(reverse=True, key=(lambda x: x[0]))
        best_score, best_idx, best = scored[0]
        if best_score < 1:
            if "skip_reward_cards" in as_actions(state):
                return
        log(f'reward pick candidate idx={best_idx} score={best_score:.1f} card={best.get("name") or best.get("card_id") or best.get("id")} plan={plan_summary(state)} knowledge={best.get("_knowledge_reasons") or []}')
        return int(best_idx)
    indexed = []
    for i, option in enumerate(options):
        if not option.get("claimed"):
            if option.get("disabled") or option.get("is_locked"):
                continue
            idx = first_number(option.get("index"))
            indexed.append(i if idx is None else idx)

    if indexed:
        return int(indexed[0])


def choose_claim_reward_index(state: "dict[str, Any]") -> "int | None":
    rewards = claimable_reward_options(state)
    best = (-999.0, None, None)
    scored_options = []
    for i, reward in enumerate(rewards):
        if reward.get("claimed") or reward.get("disabled") or reward.get("is_locked") or reward.get("claimable") is False:
            continue
        idx = first_number(reward.get("index") or reward.get("i"))
        effective_idx = i if idx is None else idx
        blob = text_blob(reward)
        score = 0.0
        if "card" in blob or reward.get("card_id") or reward.get("id"):
            score += 45
        if "relic" in blob or reward.get("relic_id"):
            score += 42
        if not "potion" in blob:
            if reward.get("potion_id"):
                score += 15
            if "gold" in blob:
                score += 18
            scored_options.append({'idx':int(effective_idx), 
             'score':round(score, 1), 
             'reward_type':reward.get("reward_type") or reward.get("type"), 
             'card':compact_card(reward) if (reward.get("card_id") or reward.get("id")) else None, 
             'text':reward.get("text") or reward.get("name") or reward.get("label")})
            if score > best[0]:
                best = (
                 score, int(effective_idx), reward)

    if best[1] is not None:
        log(f"claim reward idx={best[1]} score={best[0]:.1f}", best[2])
        journal_decision("claim_reward", state, {'idx':best[1], 
         'score':round(best[0], 1)}, {"options": scored_options})
    return best[1]


def choose_reward_index(state: "dict[str, Any]") -> "int | None":
    options = reward_options(state)
    card_like = []
    for i, option in enumerate(options):
        blob = text_blob(option)
        if "skip" in blob:
            continue
        if "card" in blob or option.get("card_id") or option.get("id"):
            idx = first_number(option.get("index"))
            card_like.append((i if idx is None else idx, option))

    if card_like:
        scored = []
        for idx, card in card_like:
            score = score_reward_card(card, state)
            threshold = reward_take_threshold(state, card, score)
            scored.append((score, threshold, idx, card))

        scored.sort(reverse=True, key=(lambda x: x[0]))
        best_score, best_threshold, best_idx, best = scored[0]
        scored_payload = [{'idx':int(idx),  'score':round(score, 1),  'threshold':round(threshold, 1),  'card':compact_card(card),  'knowledge':card.get("_knowledge_reasons") or []} for score, threshold, idx, card in scored]
        if best_score < best_threshold:
            if "skip_reward_cards" in as_actions(state):
                log(f'reward skip best_idx={best_idx} score={best_score:.1f} threshold={best_threshold:.1f} card={best.get("name") or best.get("card_id") or best.get("id")} plan={plan_summary(state)} knowledge={best.get("_knowledge_reasons") or []}', scored_payload)
                journal_decision("reward_skip_card", state, {'best_idx':int(best_idx), 
                 'best_score':round(best_score, 1), 
                 'threshold':round(best_threshold, 1), 
                 'card':compact_card(best)}, {"options": scored_payload})
                return
        log(f'reward pick candidate idx={best_idx} score={best_score:.1f} threshold={best_threshold:.1f} card={best.get("name") or best.get("card_id") or best.get("id")} plan={plan_summary(state)} knowledge={best.get("_knowledge_reasons") or []}', scored_payload)
        journal_decision("reward_take_card", state, {'idx':int(best_idx), 
         'score':round(best_score, 1), 
         'threshold':round(best_threshold, 1), 
         'card':compact_card(best)}, {"options": scored_payload})
        return int(best_idx)
    indexed = []
    for i, option in enumerate(options):
        if not option.get("claimed"):
            if option.get("disabled") or option.get("is_locked"):
                continue
            idx = first_number(option.get("index"))
            indexed.append(i if idx is None else idx)

    choice = int(indexed[0]) if indexed else None
    journal_decision("reward_fallback", state, {"idx": choice}, {"options": (options[:6])})
    return choice


def character_options(state: "dict[str, Any]") -> "list[dict[str, Any]]":
    character_select = state.get("character_select") or {}
    for key in ('characters', 'options', 'choices'):
        val = character_select.get(key)
        if isinstance(val, list):
            return val

    agent_character_select = (state.get("agent_view") or {}).get("character_select") or {}
    for key in ('characters', 'options', 'choices'):
        val = agent_character_select.get(key)
        if isinstance(val, list):
            return val

    return []


def choose_character_index(state: "dict[str, Any]", target_character_id: "str | None"=None) -> "int":
    global TARGET_CHARACTER_ID
    target = (target_character_id or TARGET_CHARACTER_ID).upper()
    options = character_options(state)
    if target in frozenset({'RANDOM', 'RANDOM_CHARACTER', '随机'}):
        if options:
            indexed = []
            for i, option in enumerate(options):
                idx = first_number(option.get("index"))
                indexed.append(i if idx is None else idx)

            return int(max(indexed))
        return 0
    for i, option in enumerate(options):
        blob = text_blob(option).upper()
        option_id = str(option.get("character_id") or option.get("id") or "").upper()
        if option_id == target or target in blob:
            idx = first_number(option.get("index"))
            return int(i if idx is None else idx)

    return 0


def target_character_selected(state: "dict[str, Any]", target_character_id: "str"=TARGET_CHARACTER_ID) -> "bool":
    target = target_character_id.upper()
    character_select = state.get("character_select") or {}
    selected = str(character_select.get("selected_character_id") or "").upper()
    characters = character_options(state)
    if target in frozenset({'RANDOM', 'RANDOM_CHARACTER', '随机'}):
        if selected == "RANDOM_CHARACTER":
            return True
        return any((bool(option.get("is_random")) and bool(option.get("is_selected")) for option in characters))
    return bool(selected and selected == target)


def map_options(state: "dict[str, Any]") -> "list[dict[str, Any]]":
    map_state = state.get("map") or {}

    def usable(nodes: "list[dict[str, Any]]") -> "list[dict[str, Any]]":
        return [x for x in nodes if not x.get("is_unavailable") if not x.get("locked") if not x.get("disabled") if str(x.get("state") or "").lower() not in frozenset({'untravelable', 'visited', 'traveled'}) if not x.get("visited") if x.get("is_available", True) is not False]

    for key in ('available_nodes', 'options', 'choices', 'nodes'):
        val = map_state.get(key)
        if isinstance(val, list):
            options = usable(val)
            if options:
                return options

    agent_map = (state.get("agent_view") or {}).get("map") or {}
    for key in ('options', 'nodes'):
        val = agent_map.get(key)
        if isinstance(val, list):
            options = usable(val)
            if options:
                return options

    return []


def all_map_nodes(state: "dict[str, Any]") -> "list[dict[str, Any]]":
    map_state = state.get("map") or {}
    val = map_state.get("nodes")
    if isinstance(val, list):
        return [x for x in val if isinstance(x, dict)]
    agent_map = (state.get("agent_view") or {}).get("map") or {}
    val = agent_map.get("nodes")
    if isinstance(val, list):
        return [x for x in val if isinstance(x, dict)]
    return []


def first_present(*values: "Any") -> "Any":
    for value in values:
        if value is not None:
            return value


def map_coord(node: "dict[str, Any]") -> "tuple[int | None, int | None]":
    row = first_number(first_present(node.get("row"), node.get("y"), node.get("floor")))
    col = first_number(first_present(node.get("col"), node.get("x")))
    return (int(row) if row is not None else None, int(col) if col is not None else None)


def map_node_key(node: "dict[str, Any]") -> "tuple[int | None, int | None]":
    return map_coord(node)


def map_children(node: "dict[str, Any]") -> "list[tuple[int | None, int | None]]":
    children = node.get("children")
    if not isinstance(children, list):
        return []
    coords = []
    for child in children:
        if isinstance(child, dict):
            coords.append(map_coord(child))

    return coords


def map_lookahead_score(node, state, depth=7):
    nodes = all_map_nodes(state)
    if not nodes or depth <= 0:
        return 0.0
    by_key = {map_node_key(candidate): candidate for candidate in nodes}
    start = by_key.get(map_node_key(node), node)
    seen = set()

    def best_from(current, remaining):
        if remaining <= 0:
            return 0.0
        child_scores = []
        for child_key in map_children(current):
            child = by_key.get(child_key)
            if child:
                if child_key in seen:
                    continue
                seen.add(child_key)
                child_scores.append(node_score(child, state) + 0.65 * best_from(child, remaining - 1))
                seen.discard(child_key)

        if child_scores:
            return max(child_scores)
        return 0.0

    return best_from(start, depth)


def map_risk_score(node, state, depth=7):
    hp, max_hp = player_hp(state)
    ratio = hp / max_hp if (hp and max_hp) else 1.0
    if ratio >= 0.55:
        return 0.0
        nodes = all_map_nodes(state)
        by_key = {map_node_key(candidate): candidate for candidate in nodes}
        start = by_key.get(map_node_key(node), node)

        def kind_blob(candidate: "dict[str, Any]") -> "str":
            kind = str(candidate.get("node_type") or candidate.get("type") or candidate.get("symbol") or candidate.get("name") or candidate.get("label") or "").lower()
            return f"{kind} {text_blob(candidate)}"

        def penalty_for(candidate, distance):
            blob = kind_blob(candidate)
            factor = 1.0 / max(1, distance)
            penalty = 0.0
            if "elite" in blob:
                penalty += policy_number("map.low_hp_elite_penalty", 80.0)
                if ratio < 0.35:
                    penalty += policy_number("map.critical_hp_elite_penalty", 120.0)
            if any((k in blob for k in ('monster', 'combat', 'enemy', 'fight', 'normal'))):
                penalty += policy_number("map.low_hp_combat_penalty", 18.0)
                if ratio < 0.35:
                    penalty += policy_number("map.critical_hp_combat_penalty", 35.0)
                else:
                    if ratio >= 0.55:
                        penalty += policy_number("map.mid_hp_combat_node_penalty", 8.0)
            elif any((k in blob for k in ('event', 'unknown', '?'))):
                penalty += policy_number("map.low_hp_unknown_penalty", 10.0)
                if ratio < 0.35:
                    penalty += policy_number("map.critical_hp_unknown_penalty", 24.0)
                else:
                    if ratio >= 0.55:
                        penalty += policy_number("map.mid_hp_unknown_node_penalty", 4.0)
            if any((k in blob for k in ('rest', 'campfire'))):
                penalty -= 18.0
                if ratio < 0.35:
                    penalty -= policy_number("map.critical_hp_rest_bonus", 34.0)
            if "shop" in blob:
                penalty -= 6.0
                if ratio < 0.35:
                    penalty -= policy_number("map.critical_hp_shop_bonus", 14.0)
            if ratio >= 0.55:
                penalty *= policy_number("map.mid_hp_penalty_scale", 0.45)
            return penalty * factor

        total_penalty = penalty_for(start, 1)
        frontier = [(start, 1)]
        seen = {map_node_key(start)}
        while frontier:
            current, distance = frontier.pop(0)
            if distance >= depth:
                continue
            for child_key in map_children(current):
                if child_key in seen:
                    continue
                child = by_key.get(child_key)
                if not child:
                    continue
                seen.add(child_key)
                total_penalty += penalty_for(child, distance + 1)
                frontier.append((child, distance + 1))

        risk = -total_penalty
        start_blob = kind_blob(start)
        if any((k in start_blob for k in ('rest', 'campfire'))):
            if ratio < 0.35:
                risk = max(risk, policy_number("map.critical_hp_immediate_rest_floor", 92.0))
        elif ratio >= 0.55:
            risk = max(risk, policy_number("map.mid_hp_immediate_rest_floor", 18.0))
        else:
            risk = max(risk, policy_number("map.low_hp_immediate_rest_floor", 42.0))
    else:
        if "shop" in start_blob:
            if ratio < 0.35:
                risk = max(risk, policy_number("map.critical_hp_immediate_shop_floor", 34.0))
            else:
                if ratio >= 0.55:
                    risk = max(risk, policy_number("map.mid_hp_immediate_shop_floor", 8.0))
                else:
                    risk = max(risk, policy_number("map.low_hp_immediate_shop_floor", 16.0))
        return risk


def map_tiebreak_score(node: "dict[str, Any]", state: "dict[str, Any]") -> "float":
    nodes = all_map_nodes(state)
    row, col = map_coord(node)
    score = 0.0
    if col is not None:
        if nodes:
            cols = [map_coord(candidate)[1] for candidate in nodes if map_coord(candidate)[1] is not None]
            if cols:
                center = (min(cols) + max(cols)) / 2
                span = max(1.0, float(max(cols) - min(cols)))
                score += max(0.0, 1.0 - abs(col - center) / span) * policy_number("map.center_tie_bonus", 0.2)
    run_id = str((state.get("run") or {}).get("run_id") or state.get("run_id") or "")
    seed = f'{run_id}:{row}:{col}:{node.get("node_type") or node.get("type")}'
    digest = hashlib.sha1(seed.encode("utf-8", errors="ignore")).hexdigest()
    score += int(digest[:6], 16) / 16777215 * policy_number("map.tie_jitter", 0.12)
    return score


def node_score(node: "dict[str, Any]", state: "dict[str, Any]") -> "float":
    blob = text_blob(node)
    hp, max_hp = player_hp(state)
    ratio = hp / max_hp if (hp and max_hp) else 1.0
    run = state.get("run") or {}
    deck = run.get("deck") or []
    non_basic = sum((1 for card in deck if str(card.get("rarity") or "").lower() not in frozenset({'', 'basic'})))
    plan = deck_plan(state)
    gold = first_number(run.get("gold") or run.get("player_gold")) or 0
    floor = first_number(run.get("floor") or run.get("current_floor")) or 0
    score = 0.0
    if any((k in blob for k in ('elite', '精英'))):
        elite_ready = ratio > 0.78 and non_basic >= 4 and plan.combat_ready
        if plan.needs_scaling:
            if ratio > 0.86:
                if non_basic >= 5:
                    elite_ready = True
        score += 26 if elite_ready else -42
        if elite_ready:
            score += policy_number("map.combat_ready_elite_bonus", 0.0)
        if any((k in blob for k in ('monster', 'combat', 'enemy', '普通', '敌'))):
            if plan.needs_damage or plan.needs_block or plan.needs_draw:
                score += 10 if ratio > 0.48 else -6
    else:
        score += 3 if ratio > 0.55 else -4
    if any((k in blob for k in ('rest', 'campfire', '篝火', '休息'))):
        score += 26 if ratio < 0.65 else 12
        if ratio < 0.35:
            score += policy_number("map.critical_hp_rest_bonus", 34.0)
    elif ratio < 0.55:
        score += policy_number("map.low_hp_rest_bonus", 0.0)
    elif plan.combat_ready:
        if ratio > 0.72:
            score += 8
        if any((k in blob for k in ('treasure', 'chest', '宝箱'))):
            score += 18
        if any((k in blob for k in ('shop', '商店'))):
            if gold >= 220:
                score += 30
    elif gold >= 120:
        score += 20
    else:
        score += 5
    if plan.wants_removal:
        if gold >= 90:
            score += 12 + policy_number("map.removal_shop_bonus", 0.0)
    if floor <= 4:
        if gold < 120:
            score -= 8 + policy_number("map.early_shop_penalty", 0.0)
    if any((k in blob for k in ('event', 'unknown', '?', '未知', '事件'))):
        score += 16 if ratio > 0.35 else 20
        if plan.needs_damage:
            if floor <= 6:
                score -= 5
        if plan.wants_removal or ratio < 0.55:
            score += 6
    if ratio < 0.55:
        if any((k in blob for k in ('rest', 'campfire', '篝火', '休息'))):
            score += policy_number("map.low_hp_rest_bonus", 0.0)
    for node_key, bonus in policy_table("map.node_bonus").items():
        if str(node_key).lower() in blob and isinstance(bonus, (int, float)):
            if not isinstance(bonus, bool):
                score += float(bonus)

    y = first_number(node.get("y") or node.get("row") or node.get("floor"))
    if y:
        score += y * 0.05
    return score


def compact_map_node(node: "dict[str, Any]") -> "dict[str, Any]":
    row, col = map_coord(node)
    return {'index':(node.get)("index"), 
     'row':row, 
     'col':col, 
     'node_type':node.get("node_type") or node.get("type") or node.get("symbol"), 
     'state':(node.get)("state"), 
     'text':node.get("text") or node.get("name") or node.get("label")}


def choose_map_index(state: "dict[str, Any]") -> "int":
    opts = map_options(state)
    if not opts:
        return 0
    scored = []
    hp, max_hp = player_hp(state)
    ratio = hp / max_hp if (hp and max_hp) else 1.0
    lookahead_weight = policy_number("map.lookahead_weight", 0.45)
    risk_start = policy_number("map.risk_start_hp_ratio", 0.72)
    if ratio < 0.35:
        lookahead_weight *= policy_number("map.critical_hp_lookahead_scale", 0.05)
    elif ratio < 0.55:
        lookahead_weight *= policy_number("map.low_hp_lookahead_scale", 0.25)
    elif ratio < risk_start:
        lookahead_weight *= policy_number("map.mid_hp_lookahead_scale", 0.6)
    for i, node in enumerate(opts):
        idx = first_number(node.get("index"))
        base = node_score(node, state)
        lookahead = map_lookahead_score(node, state)
        risk = map_risk_score(node, state)
        tie = map_tiebreak_score(node, state)
        total = base + lookahead_weight * lookahead + risk + tie
        scored.append((total, i if idx is None else idx, node, base, lookahead, risk, tie))

    scored.sort(reverse=True, key=(lambda x: x[0]))
    score, idx, node, base, lookahead, risk, tie = scored[0]
    log(f"map candidates plan={plan_summary(state)} chosen={idx}", [{**{'score':round(option_score, 1),  'base':round(option_base, 1),  'lookahead':round(option_lookahead, 1),  'risk':round(option_risk, 1),  'tie':round(option_tie, 2),  'choice_index':option_idx}, **(compact_map_node(option_node))} for option_score, option_idx, option_node, option_base, option_lookahead, option_risk, option_tie in scored])
    log(f"map pick idx={idx} score={score:.1f} base={base:.1f} lookahead={lookahead:.1f} risk={risk:.1f} tie={tie:.2f} plan={plan_summary(state)}", node)
    journal_decision("map_route", state, {'idx':int(idx), 
     'score':round(score, 1), 
     'base':round(base, 1), 
     'lookahead':round(lookahead, 1), 
     'risk':round(risk, 1), 
     'tie':round(tie, 2), 
     'node':compact_map_node(node)}, {"options": [{'score':round(option_score, 1),  'base':round(option_base, 1),  'lookahead':round(option_lookahead, 1),  'risk':round(option_risk, 1),  'tie':round(option_tie, 2),  'idx':int(option_idx),  'node':compact_map_node(option_node)} for option_score, option_idx, option_node, option_base, option_lookahead, option_risk, option_tie in scored]})
    return int(idx)


def event_options(state: "dict[str, Any]") -> "list[dict[str, Any]]":
    event = state.get("event") or {}
    for key in ('options', 'choices'):
        val = event.get(key)
        if isinstance(val, list):
            return val

    return []


def choose_event_index(state: "dict[str, Any]") -> "int":
    opts = event_options(state)
    hp, max_hp = player_hp(state)
    ratio = hp / max_hp if (hp and max_hp) else 1.0
    plan = deck_plan(state)
    event = state.get("event") or {}
    event_id = str(event.get("id") or event.get("event_id") or "").upper()
    current_hp = hp if hp is not None else max_hp
    current_max_hp = max_hp if max_hp is not None else hp
    scored = []
    for i, opt in enumerate(opts):
        idx = first_number(opt.get("index"))
        blob = text_blob(opt)
        text_key = str(opt.get("text_key") or "").lower()
        option_id = str(opt.get("id") or opt.get("option_id") or "").upper()
        if opt.get("is_locked") or opt.get("locked") or opt.get("disabled"):
            continue
        score = 0.0
        if "rest" in text_key:
            score += 20 if ratio < 0.55 else 8 if ratio < 0.8 else -6
        if any((k in blob for k in ('leave', 'proceed', '离开', '继续'))):
            score += 12
        if any((k in blob for k in ('heal', '恢复', '治疗'))):
            score += 20 if ratio < 0.55 else 8 if ratio < 0.8 else -6
        if not any((k in blob for k in ('fight', 'combat', 'battle', 'enter combat'))):
            if any((k in text_key for k in ('fight', 'combat', 'battle'))):
                score += 8 if (ratio > 0.72 and plan.combat_ready) else (-34 if ratio > 0.7 else -8)
            if any((k in blob for k in ('relic', '遗物', 'card', '卡牌', 'upgrade', '升级',
                                        'max hp', '最大生命'))):
                score += 10
            if any((k in blob for k in ('upgrade', '升级', 'smith', '锻造'))):
                score += 10 if choose_upgrade_target(state) is not None else -4
            if any((k in blob for k in ('remove', '移除', 'forget', '遗忘', 'purge', '删除'))):
                score += 18 if plan.wants_removal else 3
            if any((k in blob for k in ('transform', '变化', '变换'))):
                score += 10 if plan.wants_removal else 1
            if any((k in blob for k in ('card', '卡牌', 'choose', '选择'))):
                if not plan.needs_damage:
                    if plan.needs_block or plan.needs_draw:
                        score += 6
                elif plan.combat_ready:
                    if plan.focused:
                        score -= 4
            if any((k in blob for k in ('lose hp', '失去', 'damage', '受伤', '诅咒', 'curse'))):
                penalty = 22 if ratio < 0.6 else 8
                if any((k in blob for k in ('relic', '遗物', 'remove', '移除', 'upgrade',
                                            '升级'))):
                    if ratio > 0.72:
                        penalty -= 5
                score -= penalty
            if any((k in blob for k in ('curse', '诅咒'))):
                score -= 20
            if any((k in blob for k in ('gold', '金币'))):
                score += 8 if plan.wants_removal else 5
            if event_id == "TABLET_OF_TRUTH":
                is_decipher = option_id.startswith("DECIPHER") or "decipher" in text_key
                is_give_up = option_id in frozenset({'GIVE_UP', 'SMASH'}) or any((k in text_key for k in ('give_up',
                                                                                                          'smash')))
                if is_decipher:
                    score += 14 if ("initial" in text_key or text_key.endswith("decipher_1")) else (-48)
                    if current_max_hp is not None:
                        if current_max_hp <= 72:
                            score -= 34
                    if ratio < 0.82:
                        score -= 30
                if is_give_up:
                    score += 28
                    if not ratio < 0.9:
                        if current_max_hp is not None:
                            if current_max_hp <= 72:
                                score += 32
            if event_id == "DENSE_VEGETATION":
                is_rest = option_id == "REST" or "rest" in text_key
                is_trudge = option_id == "TRUDGE_ON" or "trudge_on" in text_key
                if is_rest:
                    score -= 28
                    if ratio < 0.35:
                        score += 18
                    if plan.combat_ready:
                        score += 10
                if is_trudge:
                    if current_hp is not None and current_hp <= 11:
                        score -= 120
                    else:
                        if ratio < 0.35:
                            score -= 48
                        else:
                            if plan.wants_removal:
                                score += 8
            scored.append((score, i if idx is None else idx, opt))

    if not scored:
        return 0
    scored.sort(reverse=True, key=(lambda x: x[0]))
    log(f"event pick idx={scored[0][1]} score={scored[0][0]:.1f} plan={plan.summary()}", scored[0][2])
    journal_decision("event_option", state, {'idx':int(scored[0][1]), 
     'score':round(scored[0][0], 1)}, {"options": [{'idx':int(idx),  'score':round(score, 1),  'text_key':(opt.get)("text_key"),  'text':opt.get("text") or opt.get("label") or opt.get("title"),  'option_id':opt.get("option_id") or opt.get("id")} for score, idx, opt in scored]})
    return int(scored[0][1])


def rest_options(state: "dict[str, Any]") -> "list[dict[str, Any]]":
    rest = state.get("rest") or {}
    for key in ('options', 'choices'):
        val = rest.get(key)
        if isinstance(val, list):
            return val

    return []


def choose_rest_index(state: "dict[str, Any]") -> "tuple[int, int | None]":
    hp, max_hp = player_hp(state)
    ratio = hp / max_hp if (hp and max_hp) else 1.0
    opts = rest_options(state)
    plan = deck_plan(state)
    best = (0.0, 0, None, {})
    scored = []
    for i, opt in enumerate(opts):
        idx = first_number(opt.get("index"))
        blob = text_blob(opt)
        score = 0.0
        target = None
        if any((k in blob for k in ('rest', 'heal', '休息', '治疗'))):
            score += 30 if ratio < 0.55 else 4
            score += policy_number("rest.heal_bonus", 0.0)
            force_heal_below = policy_number("rest.force_heal_below", 0.38)
            if ratio < force_heal_below:
                score += 100
        if any((k in blob for k in ('smith', 'upgrade', '升级', '锻造'))):
            score += 20 if ratio >= 0.55 else -6
            if plan.needs_scaling or plan.focused:
                score += 6
            target = choose_upgrade_target(state)
            score += policy_number("rest.smith_bonus", 0.0)
            if target is not None:
                score += policy_number("rest.smith_with_target_bonus", 0.0)
            if any((k in blob for k in ('dig', 'relic', '遗物'))):
                score += 14 if ratio >= 0.65 else -2
            scored.append((score, i if idx is None else int(idx), target, opt))
            if score > best[0]:
                best = (
                 score, i if idx is None else int(idx), target, opt)

    log(f'rest pick idx={best[1]} target={best[2]} score={best[0]:.1f} hp_ratio={ratio:.2f} plan={plan.summary()} options={[(round(score, 1), idx, target, opt.get("option_id") or opt.get("title")) for score, idx, target, opt in scored]}')
    journal_decision("rest_option", state, {'idx':int(best[1]), 
     'target':best[2], 
     'score':round(best[0], 1), 
     'hp_ratio':round(ratio, 2)}, {"options": [{'idx':int(idx),  'target':target,  'score':round(score, 1),  'option_id':opt.get("option_id") or opt.get("id"),  'title':opt.get("title") or opt.get("name")} for score, idx, target, opt in scored]})
    return (
     best[1], best[2])


def choose_upgrade_target(state: "dict[str, Any]") -> "int | None":
    run = state.get("run") or {}
    deck = run.get("deck") or run.get("cards") or []
    plan = deck_plan(state)
    priorities = ('bash', 'neutralize', 'survivor', 'zap', 'dualcast', 'bodyguard',
                  'unleash', 'falling_star', 'venerate', 'immolate', 'uppercut',
                  'shockwave', 'inflame', 'strike')
    best = None
    best_score = -999
    for i, card in enumerate(deck):
        blob = text_blob(card)
        if card.get("upgraded") or card.get("is_upgraded"):
            continue
        score = 0
        for rank, key in enumerate(priorities):
            if key in blob:
                score += 100 - rank * 10

        dmg = estimate_card_damage(card)
        block = estimate_card_block(card)
        score += dmg + block
        score += CARD_KNOWLEDGE.upgrade_modifier(card, state, damage=dmg, block=block)
        known = CARD_KNOWLEDGE.lookup(card)
        if known is not None:
            if plan.wants_archetype(known):
                score += 14
            elif plan.needs_damage:
                if "attack" in known.roles:
                    score += 6
            if plan.needs_block:
                if "block" in known.roles:
                    score += 6
            if not plan.needs_draw or "draw" in known.roles or "energy" in known.roles:
                score += 5
            if plan.needs_scaling:
                if "power_scaling" in known.roles:
                    score += 8
            idx = first_number(card.get("index"))
            if score > best_score:
                best = i if idx is None else idx
                best_score = score

    if best is not None:
        return int(best)


def choose_deck_selection_index(state: "dict[str, Any]", avoid: "set[int] | None"=None) -> "int":
    selection = state.get("selection") or {}
    agent_selection = (state.get("agent_view") or {}).get("selection") or {}
    blob = text_blob(selection) + text_blob(agent_selection)
    run = state.get("run") or {}
    deck = run.get("deck") or []
    selection_cards = selection.get("cards") if isinstance(selection.get("cards"), list) else []
    if not selection_cards:
        if isinstance(agent_selection.get("cards"), list):
            selection_cards = agent_selection.get("cards") or []
    else:
        combat_hand = (state.get("combat") or {}).get("hand") or []
        source_cards = selection_cards or (combat_hand if state.get("screen") == "CARD_SELECTION" else deck)
        avoid = avoid or set()
        return source_cards or 0
    discard_like = any((k in blob for k in ('discard', '弃牌', '丢弃')))
    if discard_like:
        best = None
        best_score = -999.0
        for i, card in enumerate(source_cards):
            idx = first_number(card.get("index"))
            effective_idx = i if idx is None else idx
            if effective_idx in avoid:
                continue
            score = discard_selection_score(card, state)
            if score > best_score:
                best = effective_idx
                best_score = score

        return int(best if best is not None else 0)
    remove_like = any((k in blob for k in ('remove', 'transform', 'lose', 'exhaust',
                                           '移除', '变化', '失去', '遗忘', '消耗')))
    if remove_like:
        best = None
        best_score = -999.0
        for i, card in enumerate(source_cards):
            idx = first_number(card.get("index"))
            effective_idx = i if idx is None else idx
            if effective_idx in avoid:
                continue
            score = remove_selection_score(card, state)
            if score > best_score:
                best = effective_idx
                best_score = score

        return int(best if best is not None else 0)
    if selection_cards:
        combat = state.get("combat") or {}
        incoming = sum((intent_damage(e) for e in combat.get("enemies") or [] if enemy_alive(e)))
        best = None
        best_score = -999.0
        for i, card in enumerate(source_cards):
            idx = first_number(card.get("index"))
            effective_idx = i if idx is None else idx
            if effective_idx in avoid:
                continue
            dmg = combat_card_damage(card, state)
            block = estimate_card_block(card)
            blob_card = text_blob(card)
            score = dmg * (2.0 if incoming == 0 else 1.2) + block * (2.0 if incoming else 0.8)
            if any((k in blob_card for k in ('draw', 'energy', 'vulnerable', 'weak',
                                             'power', 'strength'))):
                score += 8
            cost = card_cost(card)
            knowledge_score, _ = CARD_KNOWLEDGE.combat_modifier(card,
              state,
              damage=dmg,
              block=block,
              cost=cost,
              incoming=incoming,
              current_block=0,
              hp_ratio=player_hp(state)[0] / player_hp(state)[1] if (player_hp(state)[0] and player_hp(state)[1]) else 1.0,
              target_hp=None)
            score += knowledge_score
            score -= cost * 0.2
            if score > best_score:
                best = effective_idx
                best_score = score

        return int(best if best is not None else 0)
    upgrade_target = choose_upgrade_target(state)
    if upgrade_target is not None:
        return upgrade_target
    return 0


def choose_potion_action(state: "dict[str, Any]", actions: "set[str]") -> "tuple[str, dict[str, int | None], str] | None":
    if "use_potion" not in actions:
        return
    hp, max_hp = player_hp(state)
    ratio = hp / max_hp if (hp and max_hp) else 1.0
    combat = state.get("combat") or {}
    incoming = sum((enemy_pressure_damage(e) for e in combat.get("enemies") or [] if enemy_alive(e)))
    current_block = first_number(current_player(state).get("block")) or first_number(combat.get("block")) or 0
    damage_gap = max(0, incoming - current_block)
    projected_hp = (hp or 999) - incoming
    projected_ratio = projected_hp / max_hp if max_hp else 1.0
    enemies = combat.get("enemies") or []
    run = state.get("run") or {}
    floor = first_number(run.get("floor") or run.get("current_floor")) or 0
    boss_prep = floor in BOSS_PREP_FLOORS or floor >= 30
    live_enemies = [enemy for enemy in enemies if enemy_alive(enemy)]
    boss_like_combat = bool(
        floor in {17, 33, 49}
        or any("boss" in str(enemy.get("enemy_id") or enemy.get("id") or "").lower() for enemy in live_enemies)
        or any((first_number(enemy.get("max_hp") or enemy.get("maxHealth")) or 0) >= 150 for enemy in live_enemies)
    )
    boss_pressure = boss_like_combat and (incoming >= 12 or damage_gap >= 8 or ratio <= 0.75)
    playable = playable_cards(state)
    hand_block = sum((estimate_card_block(card) + attack_relic_block(card, state) for card in playable))
    energy_now = player_energy(state)
    spendable_now, playable_block_now, playable_damage_now = affordable_non_potion_card_value(playable, state, energy=energy_now)
    spendable_plus_two, playable_block_plus_two, playable_damage_plus_two = affordable_non_potion_card_value(playable, state, energy=energy_now + 2)
    extra_energy_spend = max(0, spendable_plus_two - spendable_now)
    extra_energy_value = max(0, playable_block_plus_two - playable_block_now) + max(0, playable_damage_plus_two - playable_damage_now) * 0.7
    playable_block_cards = sum(1 for card in playable if estimate_card_block(card) + attack_relic_block(card, state) > 0 and card.get("playable") is not False)
    post_hand_gap = max(0, damage_gap - playable_block_now)
    projected_after_hand = (hp or 999) - post_hand_gap
    projected_after_hand_ratio = projected_after_hand / max_hp if max_hp else 1.0
    danger = (
        damage_gap >= 18
        or post_hand_gap >= 12 and projected_after_hand_ratio <= 0.65
        or projected_after_hand_ratio <= 0.5
        or ratio <= 0.45
    )
    potions = (state.get("run") or {}).get("potions") or []
    best = (-999.0, None, '')
    for i, potion in enumerate(potions):
        if potion.get("occupied"):
            if potion.get("can_use") is False:
                continue
            else:
                idx = first_number(potion.get("index"))
                pidx = i if idx is None else idx
                potion_id = str(potion.get("potion_id") or potion.get("id") or "").upper()
                blob = text_blob(potion)
                score = 10.0
                kill_score = 0.0
                speed_like_potion = "SPEED" in potion_id or "speed potion" in blob
                dex_like_potion = "DEXTERITY" in potion_id or "dexterity" in blob
                persistent_defensive_potion = any((k in potion_id for k in ('BLOCK', 'FORTIFIER',
                                                                            'GHOST', 'INTANGIBLE',
                                                                            'HEART_OF_IRON', 'PLATING'))) or any((k in blob for k in ('block',
                                                                                                                                      'intangible',
                                                                                                                                      'plating')))
                defensive_potion = speed_like_potion or dex_like_potion or persistent_defensive_potion
                offensive_potion = any((k in potion_id for k in ('FIRE', 'EXPLOSIVE', 'ATTACK')))
                direct_damage_potion = potion_id in OFFENSIVE_DAMAGE_POTION_IDS or any((k in potion_id for k in ('FIRE', 'EXPLOSIVE')))
                if defensive_potion:
                    score += 45 + damage_gap
                    if speed_like_potion or dex_like_potion:
                        dex_gain = 5 if speed_like_potion else 2
                        dex_block_gain = immediate_dex_potion_block_gain(playable, state, energy=energy_now, dex_gain=dex_gain)
                        base_block_prevented = min(damage_gap, playable_block_now)
                        immediate_damage_prevented = max(0, min(damage_gap, playable_block_now + dex_block_gain) - base_block_prevented)
                        if hand_block > 0:
                            score += min(36, dex_block_gain + hand_block * 0.7)
                        else:
                            score -= 42
                        if playable_block_cards <= 1 and not danger and not boss_pressure:
                            score -= 38
                        if dex_block_gain < max(4, min(10, damage_gap)) and not danger and not boss_pressure:
                            score -= 28
                        if boss_pressure:
                            score += 28 + min(30, damage_gap * 2)
                        elif not danger and ratio >= 0.6 and damage_gap < 16:
                            score -= 42
                            if not boss_like_combat:
                                score -= 34
                        if not danger and not boss_pressure:
                            min_prevented = policy_number("potion.dex_noncrisis_min_prevented", 6.0)
                            if immediate_damage_prevented <= 0:
                                score -= policy_number("potion.dex_noncrisis_no_prevented_penalty", 70.0)
                            elif damage_gap < 10 and immediate_damage_prevented < damage_gap:
                                score -= policy_number("potion.dex_noncrisis_partial_chip_penalty", 46.0)
                            elif immediate_damage_prevented < min_prevented:
                                score -= policy_number("potion.dex_noncrisis_low_prevented_penalty", 34.0)
                    elif boss_pressure:
                        score += 16
                    if boss_like_combat and not speed_like_potion and incoming <= 0 and ratio <= 0.85:
                        score += 32
                    if not danger and not boss_pressure:
                        min_gap = policy_number("potion.defensive_noncrisis_min_gap", 12.0)
                        if damage_gap < min_gap and ratio >= policy_number("potion.high_hp_noncrisis_ratio", 0.7):
                            score -= policy_number("potion.defensive_noncrisis_small_gap_penalty", 46.0)
                        elif damage_gap < max(8.0, min_gap - 4.0):
                            score -= policy_number("potion.defensive_noncrisis_chip_penalty", 28.0)
                    if not danger:
                        if incoming <= 0:
                            score -= 35
                if not any((k in potion_id for k in ('HEAL', 'BLOOD'))):
                    if "heal" in blob:
                        score += 30 if ratio < 0.45 else 5
                    if any((k in potion_id for k in ('DUPLICATOR', 'ENERGY', 'STRENGTH',
                                                     'FIRE', 'EXPLOSIVE'))):
                        score += 22 if (projected_ratio < 0.55 or incoming >= 18) else 8
                    if "ENERGY" in potion_id:
                        if extra_energy_spend <= 0 or extra_energy_value < max(6.0, min(14.0, damage_gap * 0.8)):
                            score -= 46 if not danger else 22
                        elif not danger and not boss_pressure and damage_gap < 16:
                            score -= 24
                        else:
                            score += min(32.0, extra_energy_value * 1.4)
                    if any((k in potion_id for k in ('FIRE', 'EXPLOSIVE'))):
                        target = choose_enemy_for_damage(enemies, 20)
                        kill_score = 0.0
                        lethal_target = False
                        lethal_reduces_incoming = 0
                        if target is not None:
                            if 0 <= target < len(enemies):
                                target_hp = enemy_hp(enemies[target])
                                lethal_target = target_hp <= 20
                                lethal_reduces_incoming = intent_damage(enemies[target]) if lethal_target else 0
                                kill_score = enemy_target_score((enemies[target]),
                                  enemies,
                                  damage=20,
                                  lethal=lethal_target) * 0.6
                                score += kill_score
                                if lethal_target:
                                    score += 70
                        if (
                            direct_damage_potion
                            and boss_prep
                            and not boss_like_combat
                            and not danger
                            and ratio >= policy_number("potion.boss_prep_reserve_hp_ratio", 0.6)
                            and incoming < policy_number("potion.boss_prep_reserve_incoming", 16.0)
                            and kill_score < policy_number("potion.boss_prep_offensive_min_kill_score", 75.0)
                            and lethal_reduces_incoming < policy_number("potion.boss_prep_offensive_min_damage_saved", 8.0)
                        ):
                            score -= policy_number("potion.boss_prep_offensive_reserve_penalty", 95.0)
                    if offensive_potion and not danger:
                        if kill_score < policy_number("potion.offensive_noncrisis_min_kill_score", 45.0):
                            score -= policy_number("potion.offensive_noncrisis_extra_penalty", 40.0)
                        if ratio >= policy_number("potion.high_hp_noncrisis_ratio", 0.7) and projected_ratio > 0.55:
                            score -= policy_number("potion.high_hp_noncrisis_penalty", 18.0)
                elif danger:
                    score += 18
                if not danger and incoming <= 0:
                    if kill_score < 36:
                        score -= 45
            if any((k in potion_id for k in ('WEAK', 'VULNERABLE', 'SHACKLING'))):
                score += 28 if incoming >= 18 else 10
            if projected_ratio <= 0.25:
                score += 35
            kwargs = {"option_index": (int(pidx))}
            if potion.get("requires_target"):
                kwargs["target_index"] = choose_enemy_for_damage(enemies, 20 if "FIRE" in potion_id else 999)
            if score > best[0]:
                best = (
                 score, kwargs, potion_id or str(potion.get("name") or "potion"))

    threshold = policy_number("potion.danger_threshold", 30.0) if danger else policy_number("potion.normal_threshold", 55.0)
    if best[1] is None or best[0] < threshold:
        return
    return (
     "use_potion", best[1],
     f"use potion {best[2]} score={best[0]:.1f} hp_ratio={ratio:.2f} incoming={incoming} block={current_block}")


def potion_discard_score(potion: "dict[str, Any]") -> "float":
    potion_id = str(potion.get("potion_id") or potion.get("id") or "").upper()
    blob = text_blob(potion)
    score = 50.0
    if any((k in potion_id for k in ('FAIRY', 'GHOST', 'INTANGIBLE'))) or any((k in blob for k in ('revive',
                                                                                                   'intangible'))):
        score -= 80
    if any((k in potion_id for k in ('HEAL', 'BLOOD'))) or "heal" in blob:
        score -= 45
    if any((k in potion_id for k in ('CURE', 'CLEANS', 'PANACEA', 'BRONZE', 'THORNS',
                                     'SPEED', 'DEXTERITY'))):
        score -= 25
    if any((k in potion_id for k in ('DUPLICATOR', 'ENERGY', 'STRENGTH', 'FIRE', 'EXPLOSIVE',
                                     'WEAK', 'VULNERABLE'))):
        score -= 18
    if any((k in potion_id for k in ('ATTACK', 'SKILL', 'POWER', 'COLORLESS'))):
        score += 8
    if not potion_id:
        score += 20
    return score


def choose_discard_potion_action(state: "dict[str, Any]", actions: "set[str]") -> "tuple[str, dict[str, int], str] | None":
    if "discard_potion" not in actions:
        return
    if state.get("in_combat") or state.get("screen") == "COMBAT":
        return
    potions = (state.get("run") or {}).get("potions") or []
    best = None
    for i, potion in enumerate(potions):
        if not potion.get("occupied"):
            if not potion.get("can_discard"):
                continue
        idx = first_number(potion.get("index"))
        pidx = i if idx is None else idx
        score = potion_discard_score(potion)
        label = str(potion.get("potion_id") or potion.get("name") or "empty")
        if best is None or score > best[0]:
            best = (
             score, int(pidx), label)

    if best is None:
        return (
         "discard_potion", {"option_index": 0}, "discard potion fallback")
    return (
     "discard_potion", {"option_index": (best[1])}, f"discard weakest potion {best[2]} score={best[0]:.1f}")


def choose_discard_potion_action(state: "dict[str, Any]", actions: "set[str]") -> "tuple[str, dict[str, int], str] | None":
    if "discard_potion" not in actions:
        return None
    if state.get("in_combat") or state.get("screen") == "COMBAT":
        return None
    screen = str(state.get("screen") or "").upper()
    if screen not in {"REWARD", "COMBAT_REWARD", "SHOP"}:
        return None
    potions = (state.get("run") or {}).get("potions") or []
    if not isinstance(potions, list):
        potions = []
    best = None
    for i, potion in enumerate(potions):
        if not isinstance(potion, dict):
            continue
        occupied = bool(potion.get("occupied") or potion.get("potion_id") or potion.get("id"))
        can_discard = potion.get("can_discard")
        if not occupied and can_discard is False:
            continue
        if occupied and can_discard is False:
            continue
        idx = first_number(potion.get("index") or potion.get("i"))
        pidx = i if idx is None else idx
        score = potion_discard_score(potion)
        label = str(potion.get("potion_id") or potion.get("name") or "empty")
        if best is None or score > best[0]:
            best = (score, int(pidx), label)
    if best is None:
        return ("discard_potion", {"option_index": 0}, "discard potion fallback")
    return ("discard_potion", {"option_index": best[1]}, f"discard weakest potion {best[2]} score={best[0]:.1f}")


def shop_items(state: "dict[str, Any]") -> "list[dict[str, Any]]":
    shop = state.get("shop") or {}
    for key in ('cards', 'relics', 'potions', 'items', 'inventory'):
        val = shop.get(key)
        if isinstance(val, list):
            return val

    return []


def shop_item_price(item: "dict[str, Any]") -> "int":
    return first_number(item.get("price") or item.get("cost") or item.get("gold_cost")) or 0


def shop_synergy_buy_score(best: "tuple[float, Any, Any, dict[str, Any]]", state: "dict[str, Any]") -> "float":
    score, action, _, item = best
    return action != "buy_card" or isinstance(item, dict) or 0.0
    plan = deck_plan(state)
    known = CARD_KNOWLEDGE.lookup(item)
    if known is None:
        return 0.0
    bonus = score
    if plan.wants_archetype(known):
        bonus += 25
    if known.roles & {'zero_cost', 'draw', 'energy', 'debuff', 'weak', 'vulnerable'}:
        bonus += 14
    if reward_need_filled(known, plan):
        bonus += 12
    return bonus


def choose_shop_action(state: "dict[str, Any]") -> "tuple[str, dict[str, int], str]":
    actions = as_actions(state)
    if "open_shop_inventory" in actions:
        return (
         "open_shop_inventory", {}, "open shop inventory")
    run = state.get("run") or {}
    gold = first_number(run.get("gold") or run.get("player_gold")) or 0
    items = shop_items(state)
    plan = deck_plan(state)
    removal_cost = first_number((state.get("shop") or {}).get("remove_cost") or (state.get("shop") or {}).get("card_remove_cost") or (state.get("shop") or {}).get("removal_cost")) or 75
    wants_shop_removal = "remove_card_at_shop" in actions and plan.wants_removal and gold >= removal_cost
    reserve_for_removal = wants_shop_removal and gold < policy_number("shop.removal_gold_reserve", 180.0) and plan.removable_count >= 5
    removal_first = wants_shop_removal and gold < policy_number("shop.removal_first_below_gold", 150.0)
    best = (-999.0, None, None, {})
    scored_items = []
    for i, item in enumerate(items):
        price = shop_item_price(item)
        if price:
            if price > gold:
                continue
        blob = text_blob(item)
        score = 0.0
        action = None
        if item.get("card_id") or "card" in blob:
            score = score_reward_card(item, state) - price / 35
            score += policy_number("shop.card_bonus", 0.0)
            known = CARD_KNOWLEDGE.lookup(item)
            if known is not None:
                if plan.wants_archetype(known):
                    score += 8
                if plan.combat_ready and not plan.wants_archetype(known):
                    if not known.roles & {"draw", "energy", "power_scaling", "aoe"}:
                        score -= 7
            if reserve_for_removal and price:
                if gold - price < removal_cost:
                    if not known is None:
                        if not plan.wants_archetype(known):
                            score -= 40
                    else:
                        score -= 28
                action = "buy_card"
            else:
                pass
        if item.get("relic_id") or "relic" in blob or "遗物" in blob:
            score = 28 - price / 40
            score += policy_number("shop.relic_bonus", 0.0)
            if plan.combat_ready or plan.focused:
                score += 8
            if plan.needs_damage or plan.needs_block:
                score -= 4
            if reserve_for_removal and price:
                if gold - price < removal_cost:
                    score -= 18
                action = "buy_relic"
            else:
                if item.get("potion_id") or "potion" in blob or "药水" in blob:
                    score = 8 - price / 50
                    score += policy_number("shop.potion_bonus", 0.0)
                    if plan.needs_damage or plan.needs_block:
                        score += 5
                    if reserve_for_removal:
                        if price:
                            if gold - price < removal_cost:
                                score -= 16
                    action = "buy_potion"
                idx = first_number(item.get("index"))
                if action:
                    scored_items.append({'idx':int(i if idx is None else idx), 
                     'score':round(score, 1), 
                     'action':action, 
                     'price':price, 
                     'item':compact_shop_item(item)})
            if action and action in actions and score > best[0]:
                best = (
                 score, action, i if idx is None else idx, item)

    if "remove_card_at_shop" in actions:
        if gold >= removal_cost:
            removal_score = 12 + plan.removable_count * 2 + plan.curse_status_count * 16 + policy_number("shop.removal_bias", 0.0)
            reserve = policy_number("shop.removal_gold_reserve", 180.0)
            best_price = shop_item_price(best[3]) if isinstance(best[3], dict) else 0
            can_buy_then_remove = bool(best[1] and best_price and gold - best_price >= removal_cost)
            synergy_buy_score = shop_synergy_buy_score(best, state)
            if plan.wants_removal:
                if can_buy_then_remove:
                    if synergy_buy_score >= max(35.0, removal_score):
                        if best[1] in actions:
                            log(f"shop buy-before-remove action={best[1]} idx={best[2]} score={best[0]:.1f} synergy={synergy_buy_score:.1f} plan={plan.summary()}", best[3])
                            journal_decision("shop_buy", state, {'action':best[1], 
                             'idx':int(best[2]), 
                             'score':round(best[0], 1), 
                             'synergy_buy_score':round(synergy_buy_score, 1), 
                             'reason':"buy_then_remove", 
                             'item':compact_shop_item(best[3])}, {'items':scored_items, 
                             'gold':gold,  'removal_cost':removal_cost})
                            return (
                             str(best[1]), {"option_index": (int(best[2]))}, "buy synergistic item before removal")
            if plan.wants_removal and removal_first:
                if best[0] < policy_number("shop.removal_first_buy_score", 150.0):
                    journal_decision("shop_remove", state, {'action':"remove_card_at_shop", 
                     'reason':"removal_first",  'removal_score':round(removal_score, 1),  'best_buy':round(best[0], 1)}, {'items':scored_items, 
                     'gold':gold,  'removal_cost':removal_cost})
                    return (
                     "remove_card_at_shop", {}, f"remove before buying plan={plan.summary()} best_buy={best[0]:.1f}")
    if best[1]:
        if best[0] > policy_number("shop.buy_threshold", 4.0):
            log(f"shop buy action={best[1]} idx={best[2]} score={best[0]:.1f} plan={plan.summary()}", best[3])
            journal_decision("shop_buy", state, {'action':best[1], 
             'idx':int(best[2]),  'score':round(best[0], 1),  'item':compact_shop_item(best[3])}, {'items':scored_items, 
             'gold':gold,  'removal_cost':removal_cost})
            return (
             str(best[1]), {"option_index": (int(best[2]))}, "buy useful shop item")
    if "remove_card_at_shop" in actions and gold >= removal_cost and plan.wants_removal and not best[0] < removal_score:
        if gold < reserve:
            journal_decision("shop_remove", state, {'action':"remove_card_at_shop", 
             'reason':"better_than_buy",  'removal_score':round(removal_score, 1),  'best_buy':round(best[0], 1)}, {'items':scored_items, 
             'gold':gold,  'removal_cost':removal_cost})
            return (
             "remove_card_at_shop", {}, f"remove weak card plan={plan.summary()}")
    if "close_shop_inventory" in actions:
        journal_decision("shop_close", state, {'action':"close_shop_inventory", 
         'best_buy':round(best[0], 1)}, {'items':scored_items, 
         'gold':gold,  'removal_cost':removal_cost})
        return (
         "close_shop_inventory", {}, "close shop")
    journal_decision("shop_leave", state, {'action':"proceed", 
     'best_buy':round(best[0], 1)}, {'items':scored_items, 
     'gold':gold,  'removal_cost':removal_cost})
    return (
     "proceed", {}, "leave shop")


def choose_combat_action(state: "dict[str, Any]") -> "tuple[str, dict[str, int | None], str]":
    combat = state.get("combat") or {}
    enemies = combat.get("enemies") or []
    cards = playable_cards(state)
    if not cards:
        return (
         "end_turn", {}, "no playable cards")

    incoming = sum((enemy_pressure_damage(e) for e in enemies if enemy_alive(e)))
    player = current_player(state)
    current_block = first_number(player.get("block")) or first_number(combat.get("block")) or 0
    hp, max_hp = player_hp(state)
    hp_ratio = hp / max_hp if (hp and max_hp) else 1.0
    energy = player_energy(state)
    total_attack_damage = sum((combat_card_damage(c, state) for c in cards if is_attack(c) or combat_card_damage(c, state) > 0))
    alive_hp = sum((enemy_hp(e) for e in enemies if enemy_alive(e)))
    can_sweep_lethal = hand_has_affordable_lethal_sequence(cards, state, energy=energy)
    passive_block = passive_end_turn_block(state, current_block)
    baseline_block = current_block + passive_block
    damage_gap = max(0, incoming - baseline_block)
    hand_block = sum((estimate_card_block(c) + attack_relic_block(c, state) for c in cards))
    can_cover_with_hand = max(baseline_block, current_block + hand_block) >= incoming
    affordable_block_now = remaining_affordable_block(cards, remaining_energy=energy, state=state)
    critical_survival_ratio = policy_number("combat.critical_survival_pressure_ratio", 0.35)
    critical_survival_gap = policy_number("combat.critical_survival_pressure_gap", 4.0)
    survival_pressure = (
        damage_gap >= 18
        or hp is not None and damage_gap >= max(10, int(hp * 0.35))
        or hp_ratio < critical_survival_ratio and damage_gap >= critical_survival_gap
        or hp_ratio < 0.45 and damage_gap >= 8
    )
    run = state.get("run") or {}
    floor = first_number(run.get("floor") or run.get("current_floor")) or 0
    live_enemies = [enemy for enemy in enemies if enemy_alive(enemy)]
    boss_like_combat = bool(
        floor in {17, 33, 49}
        or any("boss" in str(enemy.get("enemy_id") or enemy.get("id") or "").lower() for enemy in live_enemies)
        or any((first_number(enemy.get("max_hp") or enemy.get("maxHealth")) or 0) >= 150 for enemy in live_enemies)
    )
    boss_block_pressure = (
        boss_like_combat
        and incoming >= policy_number("combat.boss_block_pressure_incoming", 12.0)
        and damage_gap >= policy_number("combat.boss_block_pressure_gap", 6.0)
        and affordable_block_now > 0
    )
    baggage = hand_baggage_count(cards)
    payload_count = hand_playable_payload_count(cards, state)
    hand_end_damage = sum(card_hand_end_damage_amount(c) for c in cards)
    candidates = []

    for card in cards:
        dmg = combat_card_damage(card, state)
        raw_block = estimate_card_block(card)
        effective_block = raw_block + attack_relic_block(card, state)
        cost = combat_card_energy_cost(card, state)
        generated_damage = generated_card_damage(card)
        cid = str(card.get("card_id") or card.get("id") or card.get("name") or "").lower()
        blob = text_blob(card)
        target = None
        target_hp = None
        if card.get("requires_target"):
            target = choose_enemy_for_damage(enemies, dmg)
            valid = valid_targets(card, enemies)
            if target is None and valid:
                target = valid[0]
            elif target is not None and valid and target not in valid:
                target = valid[0]
            if target is not None and 0 <= target < len(enemies):
                target_hp = enemy_hp(enemies[target])

        score = 0.0
        reasons = []
        turn_strength_debuff = card_is_turn_strength_debuff(card)
        relic_score, relic_reasons = attack_relic_combo_value(card, state)
        score += relic_score
        reasons.extend(relic_reasons)
        combat_relic_score, combat_relic_reasons = relic_combat_modifier(card,
          state,
          damage=dmg,
          block=raw_block,
          cost=cost,
          incoming=incoming,
          current_block=current_block,
          target_hp=target_hp)
        score += combat_relic_score
        reasons.extend(combat_relic_reasons)

        if dmg:
            score += dmg * 2.0
            if target is None and card_hits_all_enemies(card):
                live_enemies = [enemy for enemy in enemies if enemy_alive(enemy)]
                if len(live_enemies) > 1:
                    score += dmg * min(3, len(live_enemies) - 1) * 1.2
                    reasons.append("aoe")
                aoe_kills = 0
                for enemy in live_enemies:
                    if dmg >= enemy_hp(enemy):
                        aoe_kills += 1
                        target_score = enemy_target_score(enemy, enemies, damage=dmg, lethal=True)
                        score += 30 + target_score * 0.65 + enemy_pressure_damage(enemy) * 2.0
                if aoe_kills:
                    reasons.append(f"aoe-lethal={aoe_kills}")
            if target is not None and 0 <= target < len(enemies):
                ehp = enemy_hp(enemies[target])
                target_score = enemy_target_score(enemies[target], enemies, damage=dmg, lethal=(dmg >= ehp))
                score += target_score * 0.45
                if dmg >= ehp:
                    score += 80 + max(0, incoming) + target_score
                    reasons.append("lethal")
                score += intent_damage(enemies[target]) * 0.8
        if generated_damage:
            score += generated_damage * (2.2 if incoming < current_block + effective_block + 8 else 1.4)
            reasons.append("generated-damage")
        if card_has_unmet_play_condition(card, state):
            score -= 220
            reasons.append("unmet-play-condition")
        if card_has_hand_end_damage(card):
            cleanup_bonus = 48
            if incoming <= current_block + affordable_block_now:
                cleanup_bonus += 24
            if hp_ratio < 0.45:
                cleanup_bonus += 18
            score += cleanup_bonus
            reasons.append("clear-hand-end-damage")
        orb_score, orb_reasons = orb_channel_value(card, state, incoming=incoming, current_block=current_block)
        score += orb_score
        reasons.extend(orb_reasons)
        if effective_block:
            net_block = max(0, current_block + effective_block - baseline_block)
            needed = max(0, incoming - baseline_block)
            block_weight = 4.8 if survival_pressure and not can_sweep_lethal else 2.4
            score += min(net_block, needed) * block_weight + max(0, net_block - needed) * (0.25 if incoming else 0.05)
            if needed:
                reasons.append("covers-damage")
            if boss_block_pressure and needed:
                boss_block_bonus = policy_number("combat.boss_block_priority_base", 24.0)
                boss_block_bonus += min(net_block, needed) * policy_number("combat.boss_block_priority_scale", 4.5)
                score += min(policy_number("combat.boss_block_priority_cap", 80.0), boss_block_bonus)
                reasons.append("boss-block-priority")
            if passive_block and effective_block <= passive_block:
                score -= (passive_block - effective_block + 1) * (3.0 if incoming else 1.2)
                reasons.append("orichalcum-passive-better")
        if "bash" in cid or "vulnerable" in blob or "易伤" in blob or "鏄撲激" in blob:
            score += 30
            reasons.append("vulnerable")
        if card_draws_cards(card):
            score += 5
            reasons.append("draw")
        face_blob = card_text_blob(card)
        if "strength" in face_blob or "力量" in face_blob or "鍔涢噺" in face_blob or "能力" in face_blob or "鑳藉姏" in face_blob:
            if turn_strength_debuff:
                score += 4
                reasons.append("strength-debuff")
            else:
                score += 22
                reasons.append("scaling")
        if card_costs_x(card):
            if energy <= 0:
                zero_x_penalty = 45 if (card.get("upgraded") or card.get("is_upgraded")) else 90
                if has_relic(state, "CHEMICAL_X"):
                    zero_x_penalty = 10
                score -= zero_x_penalty
                reasons.append("x-no-energy")
            elif dmg or effective_block or generated_damage:
                score += min(24, energy * 5)
                reasons.append(f"x-cost={energy}")
        if card_has_cost_reduction_text(card):
            if free_followup_kinds(card):
                score += 6
            else:
                score += 2
        score -= cost * 3.2

        setup_score, setup_reasons = card_setup_value(card, state, cards)
        score += setup_score
        reasons.extend(setup_reasons)
        combo_score, combo_reasons = followup_combo_value(card,
          state,
          cards,
          target,
          incoming=incoming,
          current_block=current_block,
          energy=energy,
          stars=(player_stars(state)))
        score += combo_score
        reasons.extend(combo_reasons)
        is_setup_only = setup_score > 0 and not effective_block and dmg <= 0 and generated_damage <= 0

        remaining_energy = max(0, energy - cost + card_energy_gain(card, state))
        post_incoming = enemy_damage_after_card(card, target, enemies, state)
        post_block = max(baseline_block if not effective_block else 0, current_block + effective_block)
        post_extra_block = remaining_affordable_block(cards, card, remaining_energy=remaining_energy, state=state)
        remaining_hand_end_damage = max(0, hand_end_damage - card_hand_end_damage_amount(card))
        enemy_gap = max(0, post_incoming - post_block - post_extra_block)
        preventable_gap = enemy_gap + remaining_hand_end_damage
        mitigated_after_card = min(max(0, post_incoming - post_block), post_extra_block)
        missed_affordable_block = max(0, min(damage_gap, affordable_block_now) - mitigated_after_card)
        hp_after = (hp if hp is not None else 999) - preventable_gap
        is_lethal = target is not None and target_hp is not None and dmg >= target_hp
        reduces_incoming = post_incoming < incoming
        incoming_reduced_by = max(0, incoming - post_incoming)
        has_resource_followup = bool(card_draws_cards(card) or card_energy_gain(card, state) or card_star_gain(card) or generated_damage or orb_score >= 8 or combo_score >= 12)
        has_tactical_followup = bool(has_resource_followup or setup_score > 0)
        if card_has_hand_end_damage(card):
            avoided_end_damage = card_hand_end_damage_amount(card)
            clear_bonus = 38 + avoided_end_damage * (8.0 if hp_ratio < 0.55 else 5.5)
            if enemy_gap > 0 and effective_block <= 0:
                clear_bonus -= min(50.0, enemy_gap * 5.0)
            if hp_after <= 0:
                clear_bonus -= 120.0
            score += clear_bonus
            reasons.append(f"avoid-hand-end-damage={avoided_end_damage}")
        pure_setup_under_gap = (
            damage_gap > 0
            and effective_block <= 0
            and dmg <= 0
            and generated_damage <= 0
            and setup_score > 0
            and not has_resource_followup
            and not reduces_incoming
        )
        low_pressure_attack = (
            survival_pressure
            and not can_sweep_lethal
            and dmg > 0
            and effective_block <= 0
            and not is_lethal
            and not reduces_incoming
            and not has_tactical_followup
        )

        if turn_strength_debuff:
            high_value_window = bool(
                incoming >= 18
                or damage_gap >= 12
                or survival_pressure
                or hp_ratio < 0.65 and damage_gap >= 6
            )
            if boss_like_combat:
                if high_value_window and incoming_reduced_by >= 6:
                    debuff_bonus = 36 + incoming_reduced_by * (5.0 if survival_pressure else 3.4)
                    score += min(150, debuff_bonus)
                    reasons.append(f"boss-strength-window={incoming_reduced_by}")
                else:
                    save_penalty = 58 + max(0, 16 - incoming) * 3.0
                    if damage_gap < 8:
                        save_penalty += 18
                    if hp_ratio > 0.75 and incoming < 18:
                        save_penalty += 12
                    score -= min(130, save_penalty)
                    reasons.append("save-boss-strength-debuff")
            elif incoming >= 18 and incoming_reduced_by >= 6:
                debuff_bonus = 20 + incoming_reduced_by * (2.8 if survival_pressure else 1.8)
                score += min(80, debuff_bonus)
                reasons.append(f"strength-window={incoming_reduced_by}")
            elif incoming <= current_block + 6 and not survival_pressure:
                score -= 24
                reasons.append("save-strength-debuff")

        if damage_gap and not can_cover_with_hand and is_setup_only:
            pressure_penalty = 12 + min(60, damage_gap * (2.0 if hp_ratio < 0.55 else 1.0))
            score -= pressure_penalty
            reasons.append("defer-setup-under-pressure")
        if pure_setup_under_gap and not can_sweep_lethal:
            setup_penalty = 10 + min(70, damage_gap * (2.0 if survival_pressure else 1.0) + preventable_gap * 1.5)
            if can_cover_with_hand:
                setup_penalty += 10
            score -= setup_penalty
            reasons.append("pressure-setup-low")
        if low_pressure_attack:
            pressure_penalty = 18 + min(55, damage_gap * 1.6 + preventable_gap * 2.0)
            if can_cover_with_hand:
                pressure_penalty += 8
            score -= pressure_penalty
            reasons.append("low-hp-nonlethal")
        if (
            boss_block_pressure
            and dmg > 0
            and effective_block <= 0
            and not is_lethal
            and not reduces_incoming
            and not can_sweep_lethal
            and remaining_energy < energy
        ):
            reserved_before = min(damage_gap, affordable_block_now)
            reserved_after = min(damage_gap, post_extra_block)
            block_lost = max(0, reserved_before - reserved_after)
            if block_lost > 0:
                boss_penalty = policy_number("combat.boss_attack_block_reserve_base", 18.0)
                boss_penalty += block_lost * policy_number("combat.boss_attack_block_reserve_scale", 5.0)
                if hp_ratio < policy_number("combat.boss_attack_low_hp_ratio", 0.75):
                    boss_penalty *= policy_number("combat.boss_attack_low_hp_mult", 1.35)
                score -= min(policy_number("combat.boss_attack_block_reserve_cap", 110.0), boss_penalty)
                reasons.append(f"boss-block-reserve={block_lost}")
            else:
                best_chip = max(0, min(preventable_gap, damage_gap))
            if block_lost <= 0 and best_chip:
                boss_penalty = policy_number("combat.boss_attack_chip_base", 10.0)
                boss_penalty += best_chip * policy_number("combat.boss_attack_chip_scale", 3.2)
                score -= min(policy_number("combat.boss_attack_chip_cap", 60.0), boss_penalty)
                reasons.append(f"boss-chip-first={best_chip}")
            elif block_lost <= 0 and not has_tactical_followup:
                score -= policy_number("combat.boss_attack_block_order_penalty", 14.0)
                reasons.append("boss-block-first")
        if survival_pressure and not can_sweep_lethal and not effective_block:
            if is_lethal:
                score += 8
            else:
                score -= 12
                reasons.append("survival-pressure")
        if preventable_gap and not can_sweep_lethal:
            if hp_after <= 0:
                score -= 300
                reasons.append("would-die")
                if effective_block:
                    score += min(160, effective_block * 9 + max(0, incoming - current_block) * 2)
                    reasons.append("desperate-block")
                elif card_draws_cards(card) or card_energy_gain(card, state) or generated_damage or setup_score > 0:
                    score += 35
                    reasons.append("desperate-dig")
                elif dmg and not (target is not None and target_hp is not None and dmg >= target_hp and post_incoming < incoming):
                    score -= 80
                    reasons.append("desperate-no-defense")
            elif hp_ratio < 0.55 or preventable_gap >= 12:
                incoming_reduced_by = max(0, incoming - post_incoming)
                weak_lethal_block_gap = max(0, missed_affordable_block - incoming_reduced_by)
                if (
                    survival_pressure
                    and is_lethal
                    and reduces_incoming
                    and weak_lethal_block_gap >= 5
                    and remaining_energy < energy
                    and dmg > 0
                    and effective_block <= 0
                ):
                    weak_lethal_penalty = 40 + weak_lethal_block_gap * 9.0 + max(0, preventable_gap - incoming_reduced_by) * 3.0
                    if cost >= 3:
                        weak_lethal_penalty += 25
                    if hp_ratio < 0.55:
                        weak_lethal_penalty += 20
                    score -= min(220, weak_lethal_penalty)
                    reasons.append(f"weak-lethal-block-miss={weak_lethal_block_gap}")
                score -= min(90, preventable_gap * 3.0)
                reasons.append(f"unsafe-gap={preventable_gap}")
                if (
                    missed_affordable_block >= 5
                    and remaining_energy < energy
                    and dmg > 0
                    and effective_block <= 0
                    and not is_lethal
                    and not reduces_incoming
                    and not has_tactical_followup
                ):
                    block_miss_penalty = min(72, 18 + missed_affordable_block * (6.0 if hp_ratio < 0.55 else 4.0))
                    if can_cover_with_hand:
                        block_miss_penalty = min(84, block_miss_penalty + 8)
                    score -= block_miss_penalty
                    reasons.append(f"block-miss={missed_affordable_block}")
            elif (
                can_cover_with_hand
                and preventable_gap >= 6
                and dmg > 0
                and effective_block <= 0
                and not is_lethal
                and not reduces_incoming
                and not has_tactical_followup
            ):
                chip_penalty = min(36, 8 + preventable_gap * 1.6)
                if hp_ratio < 0.7 or preventable_gap >= 10:
                    chip_penalty = max(chip_penalty, min(64, 14 + preventable_gap * 3.0))
                score -= chip_penalty
                reasons.append(f"avoidable-chip={preventable_gap}")
            elif (
                not can_cover_with_hand
                and incoming >= 8
                and missed_affordable_block >= 5
                and remaining_energy < energy
                and dmg > 0
                and effective_block <= 0
                and not is_lethal
                and not reduces_incoming
                and not has_tactical_followup
            ):
                chip_penalty = min(44, 14 + missed_affordable_block * 4.8)
                score -= chip_penalty
                reasons.append(f"partial-chip={missed_affordable_block}")
        elif target is not None and target_hp is not None and dmg >= target_hp and post_incoming < incoming:
            score += min(30, (incoming - post_incoming) * 2.0)
            reasons.append("kill-reduces-damage")

        knowledge_score, knowledge_reasons = CARD_KNOWLEDGE.combat_modifier(card,
          state,
          damage=dmg,
          block=raw_block,
          cost=cost,
          incoming=incoming,
          current_block=current_block,
          hp_ratio=hp_ratio,
          target_hp=target_hp)
        score += knowledge_score
        reasons.extend(knowledge_reasons)
        if card_has_hand_end_damage(card) and "bad-generated-card" in knowledge_reasons:
            score += 200.0
            reasons.append("playable-status-cleanup")
        discard_score, discard_reasons = discard_combat_modifier(card,
          state,
          cards,
          incoming=incoming,
          current_block=current_block)
        score += discard_score
        reasons.extend(discard_reasons)

        if baggage and card_cleans_baggage(card):
            score += min(30, baggage * 6)
            if payload_count == 0 or baggage >= max(2, len(cards) - 1):
                score += 18
                reasons.append("escape-clog")
        elif baggage >= 3 and card_draws_cards(card) and not card_cleans_baggage(card) and not effective_block:
            score -= min(24, baggage * 5)
            reasons.append("draw-into-clog")
        if incoming >= 12 and effective_block:
            score += 8 if survival_pressure else 4
        if incoming >= 20 and hp_ratio < 0.65 and effective_block:
            score += 12
        if incoming <= current_block and is_pure_block_play(
            card,
            damage=dmg,
            block=effective_block,
            setup_score=setup_score,
            state=state,
            current_block=current_block,
        ):
            score -= 18 if not enemy_punishes_extra_card_play(state, card) else 35
            reasons.append("skip-covered-pure-block")
        if cost >= 3 and target is not None and target_hp is not None and dmg < target_hp:
            score -= 8
        if is_bloodletting(card):
            score += 4
            if hp_ratio < 0.65 or incoming > current_block:
                score -= 120
        if is_low_impact_play(card, dmg, raw_block):
            score -= 20 if incoming else 4

        knowledge_note = f' knowledge={",".join(reasons[:5])}' if reasons else ""
        candidates.append((
         score,
         card,
         target,
         f"dmg={dmg} block={raw_block} incoming={incoming} gap={damage_gap} energy={energy}{knowledge_note}"))

    if not candidates:
        return (
         "end_turn", {}, "no candidate")
    best_score, card, target, reason = max(candidates, key=(lambda x: x[0]))
    damage_floor = policy_number("combat.damage_floor", -20.0)
    play_any_damage = policy_bool("combat.play_any_damage", True)
    best_damage = combat_card_damage(card, state)
    best_block = estimate_card_block(card) + attack_relic_block(card, state)
    best_post_incoming = enemy_damage_after_card(card, target, enemies, state)
    best_reduces_damage = best_post_incoming < incoming
    lethal_allowed_damage = best_damage and (not survival_pressure or can_sweep_lethal or best_reduces_damage)
    best_blob = card_text_blob(card)
    best_self_harm = is_bloodletting(card) or any(token in best_blob for token in ("lose hp", "失去", "自伤"))
    best_setup_score, _ = card_setup_value(card, state, cards)
    best_generated_damage = generated_card_damage(card)
    best_resource_followup = bool(
        card_draws_cards(card)
        or card_energy_gain(card, state)
        or card_star_gain(card)
        or best_generated_damage
        or best_setup_score >= 12
    )
    best_cost = combat_card_energy_cost(card, state)
    best_remaining_energy = max(0, energy - best_cost + card_energy_gain(card, state))
    best_post_block = max(baseline_block if not best_block else 0, current_block + best_block)
    best_remaining_block = remaining_affordable_block(cards, card, remaining_energy=best_remaining_energy, state=state)
    best_preventable_gap = max(0, best_post_incoming - best_post_block - best_remaining_block)
    best_would_die = hp is not None and hp - best_preventable_gap <= 0
    best_doomed_followup_out = bool(
        best_score > 0
        and (
            card_draws_cards(card)
            or card_energy_gain(card, state)
            or card_star_gain(card)
            or card_grants_combat_resource(card)
            or best_generated_damage > 0 and best_remaining_energy > 0
            or card_generates_combat_cards(card) and best_remaining_energy > 0
        )
    )
    best_incoming_reduced_by = max(0, incoming - best_post_incoming)
    best_is_turn_strength_debuff = card_is_turn_strength_debuff(card)
    best_id = normalized_card_id(card)
    best_tactical_discard = discard_play_has_tactical_value(card, state)
    best_other_hand_cards = [other for other in cards if not same_card_instance(other, card)]
    best_nonblock_immediate_value = bool(
        best_damage > 0
        or best_generated_damage > 0
        or best_reduces_damage
        or best_setup_score > 0
        or card_draws_cards(card)
        or card_energy_gain(card, state)
        or card_star_gain(card)
        or card_generates_combat_cards(card)
        or card_grants_combat_resource(card)
        or card_has_hand_end_damage(card)
    )
    no_more_defense_to_buy = bool(
        best_damage > 0
        and best_block <= 0
        and best_remaining_block <= 0
        and not best_self_harm
        and not best_is_turn_strength_debuff
        and not enemy_punishes_extra_card_play(state, card)
        and not card_has_consuming_or_harmful_cost(card, state)
    )
    current_turn_damage_spend = no_more_defense_to_buy and (not best_would_die or has_revive_safety(state))
    turn_strength_min_saved = policy_number("combat.turn_strength_debuff_min_saved", 6.0)
    turn_strength_min_incoming = policy_number("combat.turn_strength_debuff_min_incoming", 10.0)
    turn_strength_min_gap = policy_number("combat.turn_strength_debuff_min_gap", 8.0)
    turn_strength_prevents_death = bool(
        best_is_turn_strength_debuff
        and best_reduces_damage
        and hp is not None
        and hp - damage_gap <= 0
        and hp - best_preventable_gap > 0
    )
    turn_strength_meaningful_save = bool(
        best_is_turn_strength_debuff
        and best_reduces_damage
        and not best_would_die
        and best_incoming_reduced_by >= turn_strength_min_saved
        and (
            incoming >= turn_strength_min_incoming
            or damage_gap >= turn_strength_min_gap
            or boss_like_combat
        )
    )
    turn_strength_debuff_window = bool(
        best_is_turn_strength_debuff
        and best_reduces_damage
        and (
            turn_strength_prevents_death
            or turn_strength_meaningful_save
            and (survival_pressure or incoming >= 18 or damage_gap >= 12 or boss_like_combat)
        )
        and best_score > damage_floor - policy_number("combat.turn_strength_debuff_floor_slack", 24.0)
    )
    desperation_damage = bool(
        best_damage
        and play_any_damage
        and survival_pressure
        and hp_ratio < 0.55
        and incoming > current_block
        and not best_self_harm
        and not best_would_die
        and best_score > damage_floor - policy_number("combat.desperation_damage_floor_slack", 20.0)
        and (
            can_sweep_lethal
            or best_reduces_damage
            or (affordable_block_now <= 0 and best_resource_followup)
            or current_turn_damage_spend
        )
    )
    best_is_pure_block = is_pure_block_play(
        card,
        damage=best_damage,
        block=best_block,
        setup_score=best_setup_score,
        state=state,
        current_block=current_block,
    )
    best_safe_spend = card_is_safe_current_turn_spend(
        card,
        state,
        damage=best_damage,
        block=best_block,
        generated_damage=best_generated_damage,
        setup_score=best_setup_score,
        reduces_incoming=best_reduces_damage,
    )
    best_setup_only_spend = (
        best_setup_score > 0
        and best_damage <= 0
        and best_block <= 0
        and best_generated_damage <= 0
        and not best_reduces_damage
        and not card_draws_cards(card)
        and not card_energy_gain(card, state)
        and not card_star_gain(card)
        and not card_generates_combat_cards(card)
        and not card_grants_combat_resource(card)
        and not card_has_hand_end_damage(card)
    )
    best_last_ditch_mitigation = bool(
        not best_self_harm
        and not card_has_consuming_or_harmful_cost(card, state)
        and not enemy_punishes_extra_card_play(state, card)
        and (
            (
                best_block >= policy_number("combat.last_ditch_block_min", 4.0)
                and best_is_pure_block
            )
            or best_incoming_reduced_by >= policy_number("combat.last_ditch_damage_reduce_min", 4.0)
            or (
                best_is_turn_strength_debuff
                and best_incoming_reduced_by >= policy_number("combat.last_ditch_damage_reduce_min", 4.0)
            )
        )
    )
    if (
        best_would_die
        and not can_sweep_lethal
        and not has_revive_safety(state)
        and not best_doomed_followup_out
        and not current_turn_damage_spend
        and not best_last_ditch_mitigation
    ):
        return (
         "end_turn", {}, f"avoid doomed survival line score={best_score:.1f}")
    if incoming <= current_block and best_is_pure_block and not best_safe_spend:
        return (
         "end_turn", {}, f"incoming already blocked; skip unsafe pure block score={best_score:.1f}")
    if incoming <= current_block and best_is_pure_block:
        return (
         "end_turn", {}, f"incoming already blocked; skip pure block score={best_score:.1f}")
    if passive_block and incoming <= baseline_block and best_is_pure_block and best_block <= passive_block:
        return (
         "end_turn", {}, f"orichalcum covers damage; skip weak block score={best_score:.1f}")
    if passive_block and best_block > 0 and best_block <= passive_block and not best_nonblock_immediate_value:
        return (
         "end_turn", {}, f"orichalcum better than weak block score={best_score:.1f}")
    if (
        best_id == "CALCULATED_GAMBLE"
        and energy <= 0
        and not best_tactical_discard
        and (
            not best_other_hand_cards
            or incoming <= baseline_block
            or best_score <= 0
        )
    ):
        return (
         "end_turn", {}, f"save hand cycle for useful window score={best_score:.1f}")
    if (
        best_setup_only_spend
        and best_score <= damage_floor
        and (damage_gap > 0 or survival_pressure or boss_like_combat)
        and not best_resource_followup
    ):
        return (
         "end_turn", {}, f"skip pressure setup with no immediate value score={best_score:.1f}")
    if (
        best_score <= damage_floor
        and not best_safe_spend
        and not (play_any_damage and lethal_allowed_damage)
        and not (survival_pressure and best_block)
        and not desperation_damage
        and not current_turn_damage_spend
        and not turn_strength_debuff_window
    ):
        return (
         "end_turn", {}, f"best card not worth playing score={best_score:.1f}")
    if (
        best_is_turn_strength_debuff
        and not best_reduces_damage
        and not survival_pressure
        and not best_would_die
        and incoming <= current_block + 6
        and not can_sweep_lethal
    ):
        return (
         "end_turn", {}, f"save turn strength debuff for attack window score={best_score:.1f}")
    if (
        best_is_turn_strength_debuff
        and best_reduces_damage
        and not turn_strength_prevents_death
        and not turn_strength_meaningful_save
        and not best_would_die
        and not can_sweep_lethal
        and best_remaining_block <= 0
    ):
        return (
         "end_turn", {}, f"save turn strength debuff for larger attack saved={best_incoming_reduced_by} score={best_score:.1f}")
    kwargs = {"card_index": (int(card["_index"]))}
    if card.get("requires_target"):
        target = safe_card_target(card, target, enemies, best_damage)
        if target is None:
            return (
             "end_turn", {}, "no valid target for best card")
        kwargs["target_index"] = target
    return (
     "play_card", kwargs, f'{card.get("name") or card.get("card_id")} {reason} score={best_score:.1f}')


def score_reward_card(card: "dict[str, Any]", state: "dict[str, Any]") -> "float":
    blob = text_blob(card)
    cid_raw = str(card.get("card_id") or card.get("id") or card.get("name") or "")
    cid = cid_raw.lower()
    cid_norm = cid_raw.strip().upper().replace(" ", "_")
    name = str(card.get("name") or "").lower()
    dmg = estimate_card_damage(card)
    block = estimate_card_block(card)
    cost = card_cost(card)
    known = CARD_KNOWLEDGE.lookup(card)
    plan = deck_plan(state)
    roles = frozenset(known.roles if known is not None else ())
    hp, max_hp = player_hp(state)
    hp_ratio = hp / max_hp if (hp and max_hp) else 1.0
    run = state.get("run") or {}
    floor = first_number(run.get("floor") or run.get("current_floor")) or 0
    character_id = str(run.get("character_id") or run.get("character") or "").upper()
    boss_prep = floor >= 28 or floor in {12, 13, 14, 15, 16, 30, 31, 32, 46, 47, 48}
    silent_damage_starved = bool(
        character_id == "SILENT"
        and plan.needs_damage
        and plan.card_count >= 15
        and not plan.needs_block
        and not plan.needs_draw
    )
    score = 0.0
    score += dmg * 1.6 + block * 1.1
    if "body_slam" in cid:
        score -= 18
    if any((k in blob for k in ('draw', '抽牌', 'energy', '能量', 'strength', '力量', 'vulnerable', '易伤'))):
        score += 12
    if any((k in blob for k in ('exhaust', '消耗'))):
        score += 2
    if any((k in cid + name for k in ('strike', 'defend', '打击', '防御'))):
        score -= 10
    if any((k in blob for k in ('power', '能力'))):
        score += 8
    if any((k in blob for k in ('rare', '稀有'))):
        score += 6
    if cost >= 3:
        score -= 4
    elif cost == 0:
        score += 3
    reasons = []
    generated_damage = generated_card_damage(card)
    silent_damage_roles = roles & {"poison", "shiv", "strength", "vulnerable"}
    silent_damage_card = character_id == "SILENT" and (
        cid_norm in {
            "ACCURACY",
            "ACCELERANT",
            "BLADE_DANCE",
            "CATALYST",
            "DAGGER_SPRAY",
            "DAGGER_THROW",
            "DEADLY_POISON",
            "ECHOING_SLASH",
            "ENVENOM",
            "FINISHER",
            "FLECHETTES",
            "FLICK_FLACK",
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
        or bool(silent_damage_roles)
        or generated_damage >= 8
    )
    if generated_damage:
        score += min(30.0, generated_damage * (2.0 if plan.needs_damage else 1.1))
        reasons.append(f"generated-damage={generated_damage}")
    if plan.needs_damage and silent_damage_card:
        bonus = 18.0
        if generated_damage >= 8:
            bonus += 10.0
        if "poison" in roles:
            bonus += 8.0
        if roles & {"power_scaling", "vulnerable", "strength"}:
            bonus += 6.0
        if cost <= 1:
            bonus += 4.0
        score += min(48.0, bonus)
        reasons.append("silent-real-damage-need")
        if plan.block_count >= 9 and plan.card_count >= 16:
            balance_bonus = 12.0 + min(24.0, max(0, plan.block_count - 8) * 4.0)
            if plan.primary_archetype == "si_defense_control":
                balance_bonus += 8.0
            score += balance_bonus
            reasons.append(f"silent-block-heavy-damage={balance_bonus:.0f}")
    if (
        character_id == "SILENT"
        and plan.needs_damage
        and plan.block_count >= 8
        and plan.card_count >= 16
        and not silent_damage_card
        and roles & {"block", "draw"}
        and not (roles & {"weak", "vulnerable", "debuff", "block_retention", "intangible"})
    ):
        duplicate_count = int(plan.ids.get(cid_norm, 0) or 0)
        penalty = 24.0 + min(24.0, max(0, plan.block_count - 7) * 4.0)
        if duplicate_count:
            penalty += min(24.0, duplicate_count * 8.0)
        if plan.primary_archetype == "si_defense_control":
            penalty += 12.0
        if not plan.needs_block:
            penalty += 14.0
        if not plan.needs_draw and "draw" in roles:
            penalty += 10.0
        if cid_norm in SILENT_LOW_DAMAGE_DEFENSE_REWARD_IDS:
            penalty += 18.0
        score -= penalty
        reasons.append(f"silent-damage-before-more-defense={penalty:.0f}")
    if card_costs_x(card):
        x_bonus = 8 if (dmg or block or "x_cost" in roles) else 2
        if relic_profile(state).has("CHEMICAL_X"):
            x_bonus += 18
        if plan.needs_damage and dmg:
            x_bonus += 5
        score += x_bonus
        reasons.append("x-cost")
    if card_has_cost_reduction_text(card):
        score += 8 if free_followup_kinds(card) else 4
        reasons.append("cost-flex")
    if cid_norm == "GRAND_FINALE":
        count = draw_pile_count(state)
        if count is None or count > 0:
            penalty = 70.0
            if plan.card_count >= 15 and plan.draw_count < 4:
                penalty += 24.0
            score -= penalty
            reasons.append(f"unreliable-grand-finale={penalty:.0f}")
    if character_id == "SILENT" and cid_norm in SILENT_SLY_RESOURCE_IDS:
        outlet_count = silent_discard_outlet_count(plan)
        premium_outlets = sum(int(plan.ids.get(card_id, 0) or 0) for card_id in {
            "ACROBATICS",
            "CALCULATED_GAMBLE",
            "DAGGER_THROW",
            "PREPARED",
            "TOOLS_OF_THE_TRADE",
        })
        if outlet_count < 2 or premium_outlets <= 0:
            penalty = 36.0 + (12.0 if plan.card_count >= 16 else 0.0)
            score -= penalty
            reasons.append(f"unsupported-discard-resource={penalty:.0f}")
        elif outlet_count < 3:
            score -= 14.0
            reasons.append("thin-discard-resource-support")
        else:
            score += min(18.0, outlet_count * 3.0 + premium_outlets * 4.0)
            reasons.append("supported-discard-resource")
    if character_id == "SILENT" and cid_norm == "CALCULATED_GAMBLE":
        cycle_bonus = 16.0
        if plan.needs_draw:
            cycle_bonus += 32.0
        if plan.card_count >= 15:
            cycle_bonus += 12.0
        if plan.basic_count >= 8 or plan.wants_removal:
            cycle_bonus += 14.0
        if boss_prep:
            cycle_bonus += 8.0
        if plan.ids.get("CALCULATED_GAMBLE", 0):
            cycle_bonus -= 22.0
        score += max(8.0, cycle_bonus)
        reasons.append(f"silent-discard-cycle={cycle_bonus:.0f}")
    if character_id == "SILENT" and cid_norm == "EXPOSE" and plan.ids.get("EXPOSE", 0):
        expose_penalty = 18.0 + min(28.0, int(plan.ids.get("EXPOSE", 0) or 0) * 14.0)
        if plan.needs_draw:
            expose_penalty += 14.0
        if not plan.needs_damage:
            expose_penalty += 8.0
        score -= expose_penalty
        reasons.append(f"duplicate-expose={expose_penalty:.0f}")
    boss_survival_pressure = boss_prep and (
        hp_ratio < 0.78
        or plan.block_count < 8
        or plan.scaling_count == 0
        or (plan.attack_count >= plan.block_count + 2 and plan.card_count >= 16)
    )
    if boss_survival_pressure:
        survival_bonus = 0.0
        if cid_norm == "BUFFER":
            survival_bonus += 44.0
            reasons.append("boss-prep-buffer")
        if cid_norm in {"BOOT_SEQUENCE", "CHARGE_BATTERY", "GLASSWORK", "GLACIER", "LEAP", "REINFORCED_BODY", "STACK"}:
            survival_bonus += 12.0 + min(18.0, max(block, 0) * 1.4)
            reasons.append("boss-prep-block")
        if character_id == "SILENT":
            silent_block_ids = {
                "BACKFLIP",
                "BLUR",
                "CLOAK_AND_DAGGER",
                "DODGE_AND_ROLL",
                "LEG_SWEEP",
                "PIERCING_WAIL",
                "WRAITH_FORM",
            }
            low_damage_survival = cid_norm in SILENT_LOW_DAMAGE_DEFENSE_REWARD_IDS and not (
                roles & {"weak", "vulnerable", "debuff", "block_retention", "intangible"}
            )
            if (cid_norm in silent_block_ids or roles & {"block_retention", "weak", "debuff", "strength"}) and not (
                silent_damage_starved and low_damage_survival
            ):
                survival_bonus += 16.0
                reasons.append("silent-boss-survival")
            if cid_norm == "BLUR":
                survival_bonus += 34.0
                reasons.append("silent-boss-blur")
            if cid_norm == "DODGE_AND_ROLL":
                if silent_damage_starved:
                    dodge_penalty = 28.0 + (12.0 if plan.primary_archetype == "si_defense_control" else 0.0)
                    score -= dodge_penalty
                    reasons.append(f"silent-damage-before-dodge={dodge_penalty:.0f}")
                else:
                    survival_bonus += 26.0
                    reasons.append("silent-boss-next-turn-block")
            if cid_norm in {"PIERCING_WAIL", "LEG_SWEEP", "MALAISE"}:
                survival_bonus += 36.0
                reasons.append("silent-boss-debuff")
            if cid_norm == "FOOTWORK":
                survival_bonus += 38.0 + min(18.0, plan.block_count * 2.0)
                reasons.append("silent-boss-dex")
            if cid_norm == "UNTOUCHABLE":
                survival_bonus += 10.0
                reasons.append("silent-boss-big-block")
        if "block_retention" in roles:
            survival_bonus += 12.0
            reasons.append("boss-prep-prevent-hp-loss")
        if roles & {"block", "weak"} and plan.needs_block:
            survival_bonus += 8.0
            reasons.append("boss-prep-needs-block")
        if roles & {"block", "weak", "debuff", "strength"} and plan.attack_count >= plan.block_count + 2:
            survival_bonus += 12.0
            reasons.append("boss-prep-attack-heavy")
        if (
            character_id == "SILENT"
            and roles <= {"attack", "draw", "discard"}
            and plan.card_count >= 16
            and not plan.needs_damage
        ):
            penalty = 18.0 + min(24.0, max(0, plan.attack_count - plan.block_count + 1) * 4.0)
            if plan.ids.get(cid_norm, 0) >= 1:
                penalty += 12.0 + min(18.0, plan.ids.get(cid_norm, 0) * 6.0)
            score -= penalty
            reasons.append(f"boss-prep-attack-density={penalty:.0f}")
        if roles & {"status_pollution"} and hp_ratio < 0.55:
            penalty = 12.0
            score -= penalty
            reasons.append(f"boss-prep-junk-risk={penalty:.0f}")
        if (
            "power_scaling" in roles
            and block <= 0
            and cid_norm not in {"BUFFER", "BOOT_SEQUENCE"}
            and not (roles & {"draw", "energy", "block_retention"})
            and hp_ratio < 0.65
        ):
            penalty = 18.0
            score -= penalty
            reasons.append(f"boss-prep-slow-power={penalty:.0f}")
        score += survival_bonus

    density_penalty, density_reasons = silent_attack_reward_density_penalty(
        card,
        plan,
        roles,
        cid_norm,
        cost,
        generated_damage,
    )
    if density_penalty:
        score -= density_penalty
        reasons.extend(density_reasons)

    knowledge_score, knowledge_reasons = CARD_KNOWLEDGE.reward_modifier(card,
      state,
      damage=dmg,
      block=block,
      cost=cost)
    score += knowledge_score
    reasons.extend(knowledge_reasons)
    relic_score, relic_reasons = relic_card_reward_modifier(card, state, damage=dmg, block=block, cost=cost)
    score += relic_score
    reasons.extend(relic_reasons)
    if reasons:
        card["_knowledge_reasons"] = reasons[:8]

    if known is not None:
        score += table_bonus("reward.card_bonus", known.id)
        for role in known.roles:
            score += table_bonus("reward.role_bonus", role)
        for archetype in known.archetypes:
            score += table_bonus("reward.archetype_bonus", archetype)
        if plan.wants_archetype(known):
            score += policy_number("reward.plan_match_bonus", 0.0)
        elif plan.focused and known.archetypes:
            score -= policy_number("reward.focused_off_plan_penalty", 0.0)

        need_bonus = policy_table("reward.need_bonus")
        if plan.needs_damage and "attack" in roles:
            score += float(need_bonus.get("damage_attack", 0) or 0)
        if plan.needs_block and "block" in roles:
            score += float(need_bonus.get("block_block", 0) or 0)
        if plan.needs_draw and "draw" in roles:
            score += float(need_bonus.get("draw_draw", 0) or 0)
        if plan.needs_scaling and "power_scaling" in roles:
            score += float(need_bonus.get("scaling_power", 0) or 0)
        if plan.needs_aoe and "aoe" in roles:
            score += float(need_bonus.get("aoe_aoe", 0) or 0)
        profile = CARD_KNOWLEDGE.deck_profile(state)
        if (
            "power_scaling" in roles
            and dmg == 0
            and block == 0
            and not (roles & {"draw", "energy", "star_resource", "debuff"})
            and plan.needs_draw
            and profile.role("power_scaling") >= 1
            and plan.card_count >= 12
        ):
            penalty = 26.0 + min(18.0, max(0, plan.card_count - 12) * 2.0)
            score -= penalty
            reasons.append(f"slow-engine-density={penalty:.0f}")

        utility = bool(roles & REWARD_UTILITY_ROLES)
        matching_plan = plan.wants_archetype(known)
        fills_need = reward_need_filled(known, plan)
        density_policy = policy_table("reward.density_penalty")
        if plan.focused and known.archetypes and not matching_plan and not utility and not fills_need:
            score -= float(density_policy.get("focused_off_plan", 16) or 0)
        if plan.combat_ready and plan.card_count >= 18 and not matching_plan and not utility and not fills_need:
            score -= float(density_policy.get("combat_ready_off_plan", 12) or 0)
        if plan.card_count >= 22 and not matching_plan and not utility and not fills_need:
            score -= float(density_policy.get("large_generic", 10) or 0)
        if plan.card_count >= 26 and not matching_plan and not utility and not fills_need:
            score -= float(density_policy.get("very_large_generic", 12) or 0)
        if plan.card_count >= 18 and roles <= {"attack"} and not plan.needs_damage:
            score -= float(density_policy.get("generic_attack", 14) or 0)
        if plan.card_count >= 20 and roles <= {"block"} and not plan.needs_block:
            score -= float(density_policy.get("generic_block", 8) or 0)
    if reasons:
        card["_knowledge_reasons"] = reasons[:8]
    return score


def reward_take_threshold(state, card, score):
    plan = deck_plan(state)
    table = policy_table("reward.take_threshold")
    profile = relic_profile(state)
    if plan.card_count <= 12:
        threshold = float(table.get("early", 22) or 22)
    elif plan.needs_damage or plan.needs_block:
        threshold = float(table.get("needs_core", 38) or 38)
    elif plan.needs_draw or plan.needs_scaling or plan.needs_aoe:
        threshold = float(table.get("needs_support", 45) or 45)
    else:
        threshold = float(table.get("stable", 55) or 55)
    if plan.focused:
        threshold += float(table.get("focused_bonus", 10) or 0)
    if plan.combat_ready and plan.card_count >= 18:
        threshold += float(table.get("combat_ready_bonus", 8) or 0)
    if plan.card_count >= 20:
        threshold += float(table.get("large_deck_bonus", 8) or 0)
    if plan.card_count >= 24:
        threshold += float(table.get("very_large_deck_bonus", 12) or 0)
    if plan.card_count >= 30:
        threshold += float(table.get("huge_deck_bonus", 12) or 0)
    known = CARD_KNOWLEDGE.lookup(card) if card else None
    utility = False
    fills_need = False
    matching_plan = False
    if known is not None:
        matching_plan = plan.wants_archetype(known)
        utility = bool(known.roles & REWARD_UTILITY_ROLES)
        fills_need = reward_need_filled(known, plan)
        if matching_plan:
            threshold -= float(table.get("plan_match_discount", 12) or 0)
        if utility:
            threshold -= float(table.get("utility_discount", 8) or 0)
        if fills_need:
            threshold -= float(table.get("need_discount", 8) or 0)
        if plan.focused and known.archetypes and not plan.wants_archetype(known):
            if not known.roles & REWARD_UTILITY_ROLES:
                threshold += float(table.get("off_plan_focused_bonus", 12) or 0)
        cid_norm = normalized_card_id(card)
        if (
            str(getattr(plan, "character_id", "") or "").upper() == "SILENT"
            and plan.card_count >= 18
            and not plan.needs_damage
            and "attack" in known.roles
        ):
            duplicate_count = int(plan.ids.get(cid_norm, 0) or 0)
            density_policy = policy_table("reward.density_penalty")
            if duplicate_count:
                threshold += min(18.0, 6.0 + duplicate_count * 4.0)
            if plan.needs_draw and cid_norm in SILENT_PSEUDO_DRAW_ATTACK_REWARD_IDS:
                threshold += float(density_policy.get("pseudo_draw_attack", 18) or 18)
            if plan.wants_removal and plan.removable_count >= 8:
                threshold += min(12.0, max(0, plan.removable_count - 6) * 3.0)
    removal_debt = plan.curse_status_count * 2 + max(0, plan.removable_count - 5)
    if removal_debt and not (matching_plan or utility or fills_need):
        threshold += min(18.0, 3.0 * removal_debt)
    if profile.reward_selectivity and plan.card_count >= 18 and not (matching_plan or utility or fills_need):
        threshold += min(10.0, profile.reward_selectivity * 0.5)
    if profile.has("SILVER_CRUCIBLE") and score >= threshold + 6 and (matching_plan or utility or fills_need):
        threshold -= 4.0
    if score <= -500:
        return 999.0
    threshold += relic_reward_threshold_delta(card, state, score)
    return max(8.0, threshold)


def claim_card_reward_score(state: "dict[str, Any]") -> "tuple[float, list[str]]":
    plan = deck_plan(state)
    profile = relic_profile(state)
    score = 42.0
    reasons: list[str] = []
    if plan.needs_damage or plan.needs_block:
        score += 12.0
        reasons.append("needs-core")
    if plan.needs_draw or plan.needs_scaling or plan.needs_aoe:
        score += 7.0
        reasons.append("needs-support")
    if profile.has("SILVER_CRUCIBLE"):
        score += 8.0
        reasons.append("upgraded-card-reward")
    if profile.has("PRAYER_WHEEL", "WHITE_STAR", "WING_CHARM"):
        score += 7.0
        reasons.append("better-card-reward")
    if profile.draw_support and plan.card_count <= 20:
        score += min(5.0, profile.draw_support * 2.5)
        reasons.append("draw-support")
    if plan.combat_ready and plan.focused:
        score -= 8.0
        reasons.append("focused-deck")
    if plan.card_count >= 20:
        score -= 6.0 + min(14.0, (plan.card_count - 20) * 2.0)
        reasons.append("large-deck")
    if plan.removable_count >= 8:
        score -= 9.0
        reasons.append("many-basics")
    if plan.curse_status_count:
        score -= 12.0 + plan.curse_status_count * 5.0
        reasons.append("cleanse-first")
    if profile.reward_selectivity and plan.card_count >= 18:
        score -= min(10.0, profile.reward_selectivity * 0.5)
        reasons.append("relic-selective")
    return score, reasons


def claim_card_reward_threshold(state: "dict[str, Any]") -> "float":
    plan = deck_plan(state)
    threshold = 28.0 if plan.card_count <= 12 else 36.0
    if plan.needs_damage or plan.needs_block:
        threshold -= 6.0
    elif plan.needs_draw or plan.needs_scaling or plan.needs_aoe:
        threshold -= 2.0
    else:
        threshold += 8.0
    if plan.combat_ready and plan.focused:
        threshold += 6.0
    if plan.wants_removal and plan.removable_count >= 8:
        threshold += 8.0
    if plan.card_count >= 18:
        threshold += 6.0
    if plan.curse_status_count:
        threshold += 10.0 + min(10.0, plan.curse_status_count * 4.0)
    if relic_profile(state).reward_selectivity and plan.card_count >= 16:
        threshold += min(8.0, relic_profile(state).reward_selectivity * 0.4)
    return max(18.0, threshold)


def potion_slot_counts(state: "dict[str, Any]") -> "tuple[int, int]":
    run = state.get("run") or {}
    potions = run.get("potions") or run.get("player_potions") or []
    if not isinstance(potions, list):
        return (0, 0)
    occupied = 0
    for potion in potions:
        if not isinstance(potion, dict):
            continue
        if potion.get("occupied") is True:
            occupied += 1
            continue
        if potion.get("id") or potion.get("potion_id") or potion.get("name"):
            occupied += 1
    return (occupied, len(potions))


def late_elite_route_penalty(node: "dict[str, Any]", state: "dict[str, Any]") -> "float":
    blob = text_blob(node)
    if not any((k in blob for k in ('elite', '绮捐嫳'))):
        return 0.0
    hp, max_hp = player_hp(state)
    ratio = hp / max_hp if (hp and max_hp) else 1.0
    run = state.get("run") or {}
    floor = first_number(run.get("floor") or run.get("current_floor")) or 0
    if floor < policy_number("map.late_elite_floor", 10.0):
        return 0.0
    gate = policy_number("map.late_elite_hp_gate", 0.9)
    if ratio >= gate:
        return 0.0
    plan = deck_plan(state)
    gold = first_number(run.get("gold") or run.get("player_gold")) or 0
    occupied_potions, potion_slots = potion_slot_counts(state)
    empty_potions = max(0, potion_slots - occupied_potions)
    penalty = policy_number("map.late_elite_boss_prep_penalty", 26.0)
    if getattr(plan, "needs_aoe", False) or getattr(plan, "aoe_count", 0) <= 0:
        penalty += policy_number("map.late_elite_no_aoe_penalty", 14.0)
    basic_threshold = policy_number("map.elite_basic_count_threshold", 8.0)
    basic_count = getattr(plan, "basic_count", 0)
    if basic_count >= basic_threshold:
        penalty += policy_number("map.late_elite_basic_penalty", 10.0) * (1.0 + min(1.0, (basic_count - basic_threshold) * 0.15))
    if getattr(plan, "wants_removal", False) and gold >= 90:
        penalty += policy_number("map.late_elite_removal_gold_penalty", 12.0)
    if empty_potions:
        penalty += min(2, empty_potions) * policy_number("map.late_elite_empty_potion_penalty", 12.0)
    if ratio < 0.55:
        penalty += policy_number("map.low_hp_elite_penalty", 80.0) * 0.35
    if ratio < 0.35:
        penalty += policy_number("map.critical_hp_elite_penalty", 120.0) * 0.35
    return penalty


def early_elite_route_penalty(node: "dict[str, Any]", state: "dict[str, Any]") -> "float":
    blob = text_blob(node)
    if "elite" not in blob:
        return 0.0
    hp, max_hp = player_hp(state)
    ratio = hp / max_hp if (hp and max_hp) else 1.0
    run = state.get("run") or {}
    floor = first_number(run.get("floor") or run.get("current_floor")) or 0
    if floor >= policy_number("map.late_elite_floor", 10.0):
        return 0.0
    plan = deck_plan(state)
    occupied_potions, potion_slots = potion_slot_counts(state)
    has_potion = occupied_potions > 0 or potion_slots <= 0
    if ratio >= 0.82 and has_potion and getattr(plan, "combat_ready", False):
        return 0.0
    penalty = 0.0
    if ratio < 0.72:
        penalty += policy_number("map.early_elite_mid_hp_penalty", 22.0)
    if ratio < 0.60:
        penalty += policy_number("map.early_elite_low_hp_penalty", 30.0)
    if ratio < 0.50:
        penalty += policy_number("map.early_elite_critical_hp_penalty", 40.0)
    if not has_potion:
        penalty += policy_number("map.early_elite_empty_potion_penalty", 18.0)
    basic_count = getattr(plan, "basic_count", 0)
    if basic_count >= policy_number("map.elite_basic_count_threshold", 8.0):
        penalty += policy_number("map.early_elite_basic_penalty", 14.0)
    gold = first_number(run.get("gold") or run.get("player_gold")) or 0
    if getattr(plan, "wants_removal", False) and gold >= 75:
        penalty += policy_number("map.early_elite_removal_penalty", 12.0)
    return penalty


def map_risk_score(node, state, depth=7):
    hp, max_hp = player_hp(state)
    ratio = hp / max_hp if (hp and max_hp) else 1.0
    risk_start = policy_number("map.risk_start_hp_ratio", 0.72)
    run = state.get("run") or {}
    floor = first_number(run.get("floor") or run.get("current_floor")) or 0
    late_floor = policy_number("map.late_elite_floor", 10.0)
    late_gate = policy_number("map.late_elite_hp_gate", 0.9)
    if ratio >= risk_start and not (floor >= late_floor and ratio < late_gate):
        return 0.0
    nodes = all_map_nodes(state)
    by_key = {map_node_key(candidate): candidate for candidate in nodes}
    start = by_key.get(map_node_key(node), node)

    def kind_blob(candidate: "dict[str, Any]") -> "str":
        kind = str(candidate.get("node_type") or candidate.get("type") or candidate.get("symbol") or candidate.get("name") or candidate.get("label") or "").lower()
        return f"{kind} {text_blob(candidate)}"

    def penalty_for(candidate, distance):
        blob = kind_blob(candidate)
        factor = 1.0 / max(1, distance)
        mid_factor = 0.0
        if ratio >= 0.55:
            mid_factor = policy_number("map.mid_hp_penalty_scale", 0.45)
        penalty = 0.0
        if "elite" in blob:
            penalty += policy_number("map.low_hp_elite_penalty", 80.0)
            if ratio < 0.35:
                penalty += policy_number("map.critical_hp_elite_penalty", 120.0)
            penalty += early_elite_route_penalty(candidate, state)
            penalty += late_elite_route_penalty(candidate, state)
        if any((k in blob for k in ('monster', 'combat', 'enemy', 'fight', 'normal', '普通', '敌'))):
            penalty += policy_number("map.low_hp_combat_penalty", 18.0)
            if ratio < 0.35:
                penalty += policy_number("map.critical_hp_combat_penalty", 35.0)
        elif any((k in blob for k in ('event', 'unknown', '?', '事件'))):
            penalty += policy_number("map.low_hp_unknown_penalty", 10.0)
            if ratio < 0.35:
                penalty += policy_number("map.critical_hp_unknown_penalty", 24.0)
        if mid_factor:
            if any((k in blob for k in ('monster', 'combat', 'enemy', 'fight', 'normal', '普通', '敌'))):
                penalty += policy_number("map.mid_hp_combat_node_penalty", 8.0)
            elif any((k in blob for k in ('event', 'unknown', '?', '事件'))):
                penalty += policy_number("map.mid_hp_unknown_node_penalty", 4.0)
            penalty *= mid_factor
        if any((k in blob for k in ('rest', 'campfire', '篝火', '休息'))):
            penalty -= 18.0
            if ratio < 0.35:
                penalty -= policy_number("map.critical_hp_rest_bonus", 34.0)
            elif ratio < 0.55:
                penalty -= policy_number("map.low_hp_rest_bonus", 0.0)
            else:
                penalty -= policy_number("map.mid_hp_immediate_rest_floor", 18.0) * 0.35
        if "shop" in blob or "商店" in blob:
            penalty -= 6.0
            if ratio < 0.35:
                penalty -= policy_number("map.critical_hp_shop_bonus", 14.0)
            elif ratio < 0.55:
                penalty -= policy_number("map.low_hp_immediate_shop_floor", 16.0) * 0.5
            else:
                penalty -= policy_number("map.mid_hp_immediate_shop_floor", 8.0) * 0.35
        return penalty * factor

    total_penalty = penalty_for(start, 1)
    frontier = [(start, 1)]
    seen = {map_node_key(start)}
    while frontier:
        current, distance = frontier.pop(0)
        if distance >= depth:
            continue
        for child_key in map_children(current):
            if child_key in seen:
                continue
            child = by_key.get(child_key)
            if not child:
                continue
            seen.add(child_key)
            total_penalty += penalty_for(child, distance + 1)
            frontier.append((child, distance + 1))

    risk = -total_penalty
    start_blob = kind_blob(start)
    if any((k in start_blob for k in ('rest', 'campfire', '篝火', '休息'))):
        if ratio < 0.35:
            risk = max(risk, policy_number("map.critical_hp_immediate_rest_floor", 92.0))
        elif ratio < 0.55:
            risk = max(risk, policy_number("map.low_hp_immediate_rest_floor", 42.0))
        else:
            risk = max(risk, policy_number("map.mid_hp_immediate_rest_floor", 18.0))
    if "shop" in start_blob or "商店" in start_blob:
        if ratio < 0.35:
            risk = max(risk, policy_number("map.critical_hp_immediate_shop_floor", 34.0))
        elif ratio < 0.55:
            risk = max(risk, policy_number("map.low_hp_immediate_shop_floor", 16.0))
        else:
            risk = max(risk, policy_number("map.mid_hp_immediate_shop_floor", 8.0))
    return risk


def node_score(node: "dict[str, Any]", state: "dict[str, Any]") -> "float":
    blob = text_blob(node)
    hp, max_hp = player_hp(state)
    ratio = hp / max_hp if (hp and max_hp) else 1.0
    run = state.get("run") or {}
    deck = run.get("deck") or []
    non_basic = sum((1 for card in deck if str(card.get("rarity") or "").lower() not in frozenset({'', 'basic'})))
    plan = deck_plan(state)
    gold = first_number(run.get("gold") or run.get("player_gold")) or 0
    floor = first_number(run.get("floor") or run.get("current_floor")) or 0
    profile = relic_profile(state)
    removal_pressure = getattr(plan, "removable_count", 0) + getattr(plan, "curse_status_count", 0) * 2
    score = 0.0
    is_elite = any((k in blob for k in ('elite', '精英')))
    is_combat = any((k in blob for k in ('monster', 'combat', 'enemy', 'fight', 'normal', '普通', '敌')))
    is_rest = any((k in blob for k in ('rest', 'campfire', '篝火', '休息')))
    is_shop = any((k in blob for k in ('shop', '商店')))
    is_chest = any((k in blob for k in ('treasure', 'chest', '宝箱')))
    is_event = any((k in blob for k in ('event', 'unknown', '?', '未知', '事件')))

    if is_elite:
        elite_ready = ratio > 0.78 and non_basic >= 4 and plan.combat_ready
        early_elite_penalty = early_elite_route_penalty(node, state)
        if profile.route_aggression >= 12 and ratio > 0.66 and early_elite_penalty <= 0:
            elite_ready = True
        score += 26 if elite_ready else -42
        if elite_ready:
            score += policy_number("map.combat_ready_elite_bonus", 0.0)
        score -= early_elite_penalty
        score -= late_elite_route_penalty(node, state)
    elif is_combat:
        score += 10 if ratio > 0.48 else -6
        if plan.needs_damage or plan.needs_block or plan.needs_draw:
            score += 5
        if ratio < policy_number("map.risk_start_hp_ratio", 0.72):
            score -= policy_number("map.mid_hp_combat_node_penalty", 8.0)
        if ratio < 0.55:
            score -= policy_number("map.low_hp_combat_penalty", 18.0) * 0.35
        if ratio < 0.35:
            score -= policy_number("map.critical_hp_combat_penalty", 35.0) * 0.45
    else:
        score += 3 if ratio > 0.55 else -4

    if is_rest:
        score += 26 if ratio < 0.65 else 12
        if ratio < 0.35:
            score += policy_number("map.critical_hp_rest_bonus", 34.0)
    elif ratio < 0.55:
        score += policy_number("map.low_hp_rest_bonus", 0.0)
    elif plan.combat_ready and ratio > 0.72:
        score += 8

    if is_chest:
        score += 18
    if is_shop:
        score += 30 if gold >= 220 else (20 if gold >= 120 else 5)
        if plan.wants_removal and gold >= 90:
            score += 12 + policy_number("map.removal_shop_bonus", 0.0)
        if plan.wants_removal and gold >= 75 and removal_pressure >= 8:
            score += policy_number("map.early_removal_shop_bonus", 22.0) + min(18.0, (removal_pressure - 7) * 2.5)
        if ratio < 0.55 and (plan.needs_block or plan.needs_draw or gold >= 120):
            score += policy_number("map.low_hp_immediate_shop_floor", 16.0) * 0.6
    early_removal_shop = plan.wants_removal and gold >= 75 and removal_pressure >= 8
    if floor <= 4 and is_shop and gold < 120 and not early_removal_shop:
        score -= 8 + policy_number("map.early_shop_penalty", 0.0)
    if is_event:
        score += 16 if ratio > 0.35 else 20
        if plan.needs_damage and floor <= 6:
            score -= 5
        if plan.wants_removal or ratio < 0.55:
            score += 6
    for node_key, bonus in policy_table("map.node_bonus").items():
        if str(node_key).lower() in blob and isinstance(bonus, (int, float)) and not isinstance(bonus, bool):
            score += float(bonus)
    score += relic_route_modifier(node, state)
    y = first_number(node.get("y") or node.get("row") or node.get("floor"))
    if y:
        score += y * 0.05
    return score


def choose_event_index(state: "dict[str, Any]") -> "int":
    opts = event_options(state)
    hp, max_hp = player_hp(state)
    ratio = hp / max_hp if (hp and max_hp) else 1.0
    plan = deck_plan(state)
    event = state.get("event") or {}
    event_id = str(event.get("id") or event.get("event_id") or "").upper()
    current_hp = hp if hp is not None else max_hp
    current_max_hp = max_hp if max_hp is not None else hp
    scored = []
    for i, opt in enumerate(opts):
        idx = first_number(opt.get("index"))
        blob = event_option_blob(opt, state)
        text_key = str(opt.get("text_key") or "").lower()
        option_id = str(opt.get("id") or opt.get("option_id") or "").upper()
        if opt.get("is_locked") or opt.get("locked") or opt.get("disabled"):
            continue
        score = 0.0
        reasons = []
        if "rest" in text_key:
            score += 20 if ratio < 0.55 else 8 if ratio < 0.8 else -6
        if any((k in blob for k in ('leave', 'proceed', '离开', '继续'))):
            score += 12
        if any((k in blob for k in ('heal', '恢复', '治疗'))):
            score += 20 if ratio < 0.55 else 8 if ratio < 0.8 else -6
        if any((k in text_key for k in ('fight', 'combat', 'battle'))):
            score += 8 if (ratio > 0.72 and plan.combat_ready) else (-34 if ratio > 0.7 else -8)
        if any((k in blob for k in ('relic', '遗物', 'card', '卡牌', 'upgrade', '升级', 'max hp'))):
            score += 10
        if any((k in blob for k in ('upgrade', '升级', 'smith', '锻造'))):
            score += 10 if choose_upgrade_target(state) is not None else -4
        if any((k in blob for k in ('remove', '移除', 'forget', '遗忘', 'purge', '删除'))):
            score += 18 if plan.wants_removal else 3
        if any((k in blob for k in ('transform', '变化', '变换'))):
            score += 10 if plan.wants_removal else 1
        if any((k in blob for k in ('card', '卡牌', 'choose', '选择'))) and plan.combat_ready and plan.focused:
            score -= 4
        if any((k in blob for k in ('lose hp', '失去', 'damage', '受伤', 'curse', '诅咒'))):
            penalty = 22 if ratio < 0.6 else 8
            if ratio > 0.72 and any((k in blob for k in ('relic', '遗物', 'remove', '移除', 'upgrade', '升级'))):
                penalty -= 5
            score -= penalty
        if any((k in blob for k in ('curse', '诅咒'))):
            score -= 20
        if any((k in blob for k in ('gold', '金币'))):
            score += 8 if plan.wants_removal else 5
        hp_loss = event_option_hp_loss(blob)
        if hp_loss is not None:
            if current_hp is not None and hp_loss >= current_hp:
                score -= 1000
                reasons.append(f"lethal-hp-cost={hp_loss}")
            else:
                hp_penalty = hp_loss * (6.0 if ratio < 0.35 else 3.5 if ratio < 0.6 else 1.4)
                if ratio < 0.45:
                    hp_penalty += 35
                score -= min(180.0, hp_penalty)
                reasons.append(f"hp-cost={hp_loss}")
        max_hp_loss = event_option_max_hp_loss(blob)
        if max_hp_loss is not None:
            score -= 12 + max_hp_loss * (2.0 if ratio < 0.7 else 1.0)
            reasons.append(f"max-hp-cost={max_hp_loss}")
        gold_loss = event_option_gold_loss(blob)
        if gold_loss is not None:
            gold = first_number((state.get("run") or {}).get("gold") or (state.get("run") or {}).get("player_gold")) or 0
            if gold_loss > gold:
                score -= 200
                reasons.append(f"unaffordable-gold={gold_loss}")
            else:
                score -= min(45.0, gold_loss / (5.0 if plan.wants_removal else 8.0))
                reasons.append(f"gold-cost={gold_loss}")
        relic_event_score, relic_event_reasons = relic_event_option_modifier(opt, state)
        score += relic_event_score
        reasons.extend(relic_event_reasons)

        if event_id == "TABLET_OF_TRUTH":
            is_decipher = option_id.startswith("DECIPHER") or "decipher" in text_key
            is_give_up = option_id in frozenset({'GIVE_UP', 'SMASH'}) or any((k in text_key for k in ('give_up', 'smash')))
            if is_decipher:
                score += 14 if ("initial" in text_key or text_key.endswith("decipher_1")) else -48
                if current_max_hp is not None and current_max_hp <= 72:
                    score -= 34
                if ratio < 0.82:
                    score -= 30
            if is_give_up:
                score += 28
                if ratio >= 0.9 and current_max_hp is not None and current_max_hp <= 72:
                    score += 32
        if event_id == "DENSE_VEGETATION":
            is_rest = option_id == "REST" or "rest" in text_key
            is_trudge = option_id == "TRUDGE_ON" or "trudge_on" in text_key
            if is_rest:
                score -= 28
                if ratio < 0.35:
                    score += 18
                if plan.combat_ready:
                    score += 10
            if is_trudge:
                if current_hp is not None and current_hp <= 11:
                    score -= 120
                elif ratio < 0.35:
                    score -= 48
                elif plan.wants_removal:
                    score += 8
        scored.append((score, i if idx is None else idx, opt, reasons))

    if not scored:
        return 0
    scored.sort(reverse=True, key=(lambda x: x[0]))
    log(f"event pick idx={scored[0][1]} score={scored[0][0]:.1f} plan={plan.summary()} relic={relic_summary(state)}", scored[0][2])
    journal_decision("event_option", state, {'idx':int(scored[0][1]), 
     'score':round(scored[0][0], 1)}, {"options": [{'idx':int(idx),  'score':round(score, 1),  'text_key':(opt.get)("text_key"),  'text':opt.get("text") or opt.get("label") or opt.get("title"),  'option_id':opt.get("option_id") or opt.get("id"),  'relic':reasons} for score, idx, opt, reasons in scored]})
    return int(scored[0][1])


SILENT_CAMPFIRE_KEY_UPGRADE_IDS = {
    "ACCURACY",
    "BACKFLIP",
    "BLADE_DANCE",
    "CLOAK_AND_DAGGER",
    "DAGGER_SPRAY",
    "DAGGER_THROW",
    "FOOTWORK",
    "LEG_SWEEP",
    "MALAISE",
    "NEUTRALIZE",
    "NOXIOUS_FUMES",
    "PIERCING_WAIL",
    "POISONED_STAB",
    "SURVIVOR",
    "TERROR",
}


def deck_card_for_effective_index(state: "dict[str, Any]", target: "int | None") -> "dict[str, Any] | None":
    if target is None:
        return None
    run = state.get("run") or {}
    deck = run.get("deck") or run.get("cards") or []
    if not isinstance(deck, list):
        return None
    for i, card in enumerate(deck):
        if not isinstance(card, dict):
            continue
        idx = first_number(card.get("index") or card.get("i"))
        if int(target) == int(i if idx is None else idx):
            return card
    if 0 <= int(target) < len(deck) and isinstance(deck[int(target)], dict):
        return deck[int(target)]
    return None


def campfire_upgrade_value(state: "dict[str, Any]", target: "int | None") -> "tuple[float, str]":
    card = deck_card_for_effective_index(state, target)
    if card is None:
        return 0.0, ""
    value = max(0.0, upgrade_selection_score(card, state))
    cid = normalized_card_id(card)
    run = state.get("run") or {}
    character_id = str(run.get("character_id") or run.get("character") or "").upper()
    if character_id == "SILENT" and cid in SILENT_CAMPFIRE_KEY_UPGRADE_IDS:
        value += 10.0
    return value, cid


def choose_rest_index(state: "dict[str, Any]") -> "tuple[int, int | None]":
    hp, max_hp = player_hp(state)
    ratio = hp / max_hp if (hp and max_hp) else 1.0
    opts = rest_options(state)
    plan = deck_plan(state)
    profile = relic_profile(state)
    run = state.get("run") or {}
    character_id = str(run.get("character_id") or run.get("character") or "").upper()
    floor = first_number(run.get("floor") or run.get("current_floor")) or 0
    deck_ids = {
        normalized_card_id(card)
        for card in (run.get("deck") or run.get("cards") or [])
        if isinstance(card, dict)
    }
    has_byrdonis_egg = "BYRDONIS_EGG" in deck_ids
    upgrade_target = choose_upgrade_target(state)
    upgrade_value, upgrade_card_id = campfire_upgrade_value(state, upgrade_target)
    strong_upgrade = upgrade_value >= (42.0 if character_id == "SILENT" else 50.0)
    solid_upgrade = upgrade_value >= (28.0 if character_id == "SILENT" else 36.0)
    safe_smith_ratio = 0.72
    if profile.combat_strength >= 18 and plan.combat_ready:
        safe_smith_ratio -= 0.04
    if "sustain" in profile.tags or profile.has("BURNING_BLOOD", "BLOOD_VIAL", "REGAL_PILLOW"):
        safe_smith_ratio -= 0.03
    if not plan.combat_ready or plan.needs_block or plan.needs_draw:
        safe_smith_ratio += 0.03
    if floor >= 12 and ratio < 0.72:
        safe_smith_ratio += 0.03
    if strong_upgrade:
        safe_smith_ratio -= 0.08 if character_id == "SILENT" else 0.04
    elif solid_upgrade and (character_id == "SILENT" or plan.combat_ready):
        safe_smith_ratio -= 0.04 if character_id == "SILENT" else 0.02
    safe_smith_ratio = max(0.58, min(0.82, safe_smith_ratio))
    best = (-999.0, 0, None, {})
    scored = []
    for i, opt in enumerate(opts):
        idx = first_number(opt.get("index"))
        blob = text_blob(opt)
        option_label = str(opt.get("option_id") or opt.get("id") or opt.get("title") or opt.get("name") or "").upper()
        score = 0.0
        target = None
        reasons = []
        if any((k in blob for k in ('rest', 'heal', '休息', '治疗'))):
            score += 30 if ratio < 0.55 else 4
            score += policy_number("rest.heal_bonus", 0.0)
            if ratio < policy_number("rest.force_heal_below", 0.38):
                score += 100
                reasons.append("force-low-hp")
            elif ratio < 0.48:
                score += 52
                reasons.append("critical-heal")
            elif ratio < 0.58:
                score += 34
                reasons.append("low-heal")
            elif ratio < safe_smith_ratio:
                if strong_upgrade and ratio >= 0.65:
                    score += 10
                    reasons.append("mid-hp-key-upgrade")
                else:
                    score += 28
                    reasons.append("mid-hp-heal")
            elif ratio < 0.78 and not plan.combat_ready:
                score += 12
                reasons.append("deck-not-ready-heal")
            if "sustain" in profile.tags and ratio >= 0.62 and plan.combat_ready:
                score -= 4
                reasons.append("relic-sustain-buffer")
        if any((k in blob for k in ('smith', 'upgrade', '升级', '锻造'))):
            score += 20 if ratio >= 0.55 else -6
            if plan.needs_scaling or plan.focused:
                score += 6
            target = upgrade_target
            score += policy_number("rest.smith_bonus", 0.0)
            if target is not None:
                score += policy_number("rest.smith_with_target_bonus", 0.0)
                score += min(24.0, max(4.0, upgrade_value * 0.35))
                if strong_upgrade:
                    reasons.append(f"key-upgrade:{upgrade_card_id}")
                elif solid_upgrade:
                    reasons.append(f"solid-upgrade:{upgrade_card_id}")
            else:
                score -= 8
                reasons.append("no-upgrade-target")
            if ratio < 0.55:
                score -= 70
                reasons.append("too-low-smith")
            elif ratio < safe_smith_ratio:
                penalty = 34 + (14 if not plan.combat_ready else 0)
                if plan.needs_block or plan.needs_draw:
                    penalty += 10
                if solid_upgrade and ratio >= 0.62:
                    penalty -= 22 if character_id == "SILENT" and strong_upgrade else 12
                    reasons.append("upgrade-risk-credit")
                score -= max(12, penalty)
                reasons.append("unsafe-mid-hp-smith")
            elif ratio < safe_smith_ratio + 0.06 and not plan.combat_ready:
                if solid_upgrade and ratio >= 0.68:
                    score -= 4
                    reasons.append("borderline-key-smith")
                else:
                    score -= 12
                    reasons.append("borderline-smith")
        if any((k in blob for k in ('dig', 'relic', '遗物'))):
            score += 14 if ratio >= 0.65 else -2
        if "HATCH" in option_label or any((k in blob for k in ('hatch', '孵化'))):
            if has_byrdonis_egg:
                score += 72
                reasons.append("hatch-byrdonis-egg")
                if ratio < policy_number("rest.force_heal_below", 0.38):
                    score -= 180
                    reasons.append("too-low-hatch")
                elif ratio < 0.55:
                    score -= 52
                    reasons.append("low-hp-delay-hatch")
                elif floor >= 15 and ratio < 0.72:
                    score -= 24
                    reasons.append("boss-prep-hatch-risk")
            else:
                score -= 12
                reasons.append("no-egg-to-hatch")
        relic_rest_score, relic_rest_reasons = relic_rest_option_modifier(opt, state, hp_ratio=ratio)
        score += relic_rest_score
        reasons.extend(relic_rest_reasons)
        scored.append((score, i if idx is None else int(idx), target, opt, reasons))
        if score > best[0]:
            best = (score, i if idx is None else int(idx), target, opt)

    log(f'rest pick idx={best[1]} target={best[2]} upgrade={upgrade_card_id}:{upgrade_value:.1f} score={best[0]:.1f} hp_ratio={ratio:.2f} plan={plan.summary()} relic={relic_summary(state)} options={[(round(score, 1), idx, target, opt.get("option_id") or opt.get("title"), reasons) for score, idx, target, opt, reasons in scored]}')
    journal_decision("rest_option", state, {'idx':int(best[1]), 
     'target':best[2], 
     'score':round(best[0], 1), 
     'hp_ratio':round(ratio, 2)}, {"options": [{'idx':int(idx),  'target':target,  'score':round(score, 1),  'option_id':opt.get("option_id") or opt.get("id"),  'title':opt.get("title") or opt.get("name"),  'relic':reasons} for score, idx, target, opt, reasons in scored]})
    return (
     best[1], best[2])


def shop_items(state: "dict[str, Any]") -> "list[dict[str, Any]]":
    shop = state.get("shop") or {}
    items = []
    for key in ('cards', 'relics', 'potions', 'items', 'inventory'):
        val = shop.get(key)
        if isinstance(val, list):
            items.extend([item for item in val if isinstance(item, dict)])
    return items


def shop_synergy_buy_score(best: "tuple[float, Any, Any, dict[str, Any]]", state: "dict[str, Any]") -> "float":
    score, action, _, item = best
    if not action or not isinstance(item, dict):
        return 0.0
    bonus = score
    plan = deck_plan(state)
    if action == "buy_card":
        card = item_card_payload(item) or item
        known = CARD_KNOWLEDGE.lookup(card)
        if known is not None:
            if plan.wants_archetype(known):
                bonus += 25
            if known.roles & {'zero_cost', 'draw', 'energy', 'debuff', 'weak', 'vulnerable'}:
                bonus += 14
            if reward_need_filled(known, plan):
                bonus += 12
        if card_costs_x(card):
            bonus += 12
            if relic_profile(state).has("CHEMICAL_X"):
                bonus += 20
        if card_has_cost_reduction_text(card):
            bonus += 10 if free_followup_kinds(card) else 5
    elif action == "buy_relic":
        relic_score, _ = relic_pickup_score(item, state)
        bonus += relic_score * 0.35
    return bonus


def shop_core_buy_reasons(best: "tuple[float, Any, Any, dict[str, Any]]", state: "dict[str, Any]") -> "list[str]":
    score, action, _, item = best
    if not action or not isinstance(item, dict):
        return []
    plan = deck_plan(state)
    run = state.get("run") or {}
    floor = first_number(run.get("floor") or run.get("current_floor")) or 0
    character_id = str(run.get("character_id") or run.get("character") or "").upper()
    hp, max_hp = player_hp(state)
    hp_ratio = hp / max_hp if (hp and max_hp) else 1.0
    boss_prep = floor >= 28 or floor in {12, 13, 14, 15, 16, 30, 31, 32, 46, 47, 48}
    reasons = []
    if action == "buy_card":
        card = item_card_payload(item) or item
        known = CARD_KNOWLEDGE.lookup(card)
        roles = frozenset(known.roles if known is not None else known_card_roles(card))
        cid = normalized_card_id(card)
        block = estimate_card_block(card)
        damage = estimate_card_damage(card)
        if plan.needs_block and (block >= 7 or "block" in roles or "weak" in roles):
            reasons.append("fills-block")
        if plan.needs_draw and (card_draws_cards(card) or "draw" in roles):
            reasons.append("fills-draw")
        if plan.needs_scaling and ("power_scaling" in roles or known_card_type(card) == "power"):
            reasons.append("fills-scaling")
        if plan.needs_aoe and "aoe" in roles:
            reasons.append("fills-aoe")
        if plan.needs_damage and (damage >= 10 or "vulnerable" in roles or card_costs_x(card)):
            reasons.append("fills-damage")
        if hp_ratio < 0.55 and (block >= 8 or "weak" in roles or "intangible" in roles):
            reasons.append("survival-card")
        if boss_prep and character_id == "SILENT" and (
            cid in {
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
            or roles & {"block_retention", "weak", "debuff", "strength", "dexterity"}
            or block >= 8
        ):
            reasons.append("boss-survival-card")
        if plan.wants_archetype(known) if known is not None else False:
            reasons.append("archetype-core")
        if card_has_cost_reduction_text(card) and free_followup_kinds(card):
            reasons.append("cost-engine")
        if card_costs_x(card) and damage:
            reasons.append("x-burst")
    elif action == "buy_relic":
        relic_score, relic_reasons = relic_pickup_score(item, state)
        relic_id = str(item.get("relic_id") or item.get("id") or item.get("name") or "").strip().upper().replace(" ", "_")
        if relic_score >= 45:
            reasons.append("high-impact-relic")
        if character_id == "SILENT" and relic_id == "LETTER_OPENER" and deck_skill_count(state) >= 7:
            reasons.append("skill-chain-relic")
        if relic_reasons:
            reasons.extend(relic_reasons[:2])
    elif action == "buy_potion":
        potion_id = shop_potion_id(item)
        if boss_prep and potion_id in BOSS_PREP_POTION_IDS:
            reasons.append("boss-survival-potion")
        elif floor >= 18 and character_id == "SILENT" and potion_id in ACT2_SURVIVAL_POTION_IDS and not potion_slots_full(state):
            reasons.append("act2-survival-potion")
        elif hp_ratio < 0.55 and potion_id in DEFENSIVE_POTION_IDS:
            reasons.append("survival-potion")
    return reasons


def shop_purchase_preserves_removal(best: "tuple[float, Any, Any, dict[str, Any]]", gold: int, removal_cost: int) -> "bool":
    price = shop_item_price(best[3]) if isinstance(best[3], dict) else 0
    return bool(best[1] and price and gold - price >= removal_cost)


def shop_buy_before_removal_gate(best: "tuple[float, Any, Any, dict[str, Any]]", state: "dict[str, Any]", gold: int, removal_cost: int, removal_score: float) -> "tuple[bool, list[str], float]":
    if not shop_purchase_preserves_removal(best, gold, removal_cost):
        return False, [], 0.0
    core_reasons = shop_core_buy_reasons(best, state)
    synergy_score = shop_synergy_buy_score(best, state)
    if not core_reasons:
        return False, core_reasons, synergy_score
    plan = deck_plan(state)
    threshold = max(removal_score + 18.0, 92.0)
    if plan.curse_status_count:
        threshold += 14.0
    if plan.removable_count >= 7:
        threshold += 10.0
    if any(reason in core_reasons for reason in ("survival-card", "boss-survival-card", "boss-survival-potion", "act2-survival-potion", "survival-potion", "archetype-core", "high-impact-relic", "skill-chain-relic")):
        threshold -= 12.0
    return synergy_score >= threshold, core_reasons, synergy_score


def shop_buy_threshold_for_action(action: Any) -> float:
    buy_threshold = policy_number("shop.buy_threshold", 4.0)
    if action == "buy_potion":
        return policy_number("shop.potion_buy_threshold", buy_threshold)
    return buy_threshold


def shop_buy_threshold_for_item(action: Any, item: "dict[str, Any]", state: "dict[str, Any]", price: int) -> float:
    threshold = shop_buy_threshold_for_action(action)
    if action != "buy_card" or not isinstance(item, dict):
        return threshold
    card = item_card_payload(item) or item
    known = CARD_KNOWLEDGE.lookup(card)
    roles = frozenset(known.roles if known is not None else known_card_roles(card))
    plan = deck_plan(state)
    cheap = bool(price and price <= policy_number("shop.cheap_card_price", 55.0))
    fills_need = bool(known is not None and reward_need_filled(known, plan))
    archetype_card = bool(known is not None and plan.wants_archetype(known))
    survival_card = bool(
        estimate_card_block(card) >= 5
        or roles & {"block", "block_retention", "weak", "debuff", "strength", "dexterity", "intangible"}
        or normalized_card_id(card) in {
            "BACKFLIP",
            "BLUR",
            "CLOAK_AND_DAGGER",
            "DODGE_AND_ROLL",
            "LEG_SWEEP",
            "PIERCING_WAIL",
            "WRAITH_FORM",
        }
    )
    if fills_need:
        threshold = min(threshold, policy_number("shop.need_card_buy_threshold", 18.0))
    if cheap and (survival_card or archetype_card):
        threshold = min(threshold, policy_number("shop.synergy_card_buy_threshold", 30.0))
    if cheap and survival_card:
        threshold = min(threshold, policy_number("shop.core_card_buy_threshold", 24.0) + 20.0)
    if "remove_card_at_shop" not in as_actions(state) and (survival_card or fills_need):
        threshold = min(threshold, policy_number("shop.no_removal_fallback_threshold", 22.0) + 20.0)
    return threshold


def has_revive_safety(state: "dict[str, Any]") -> "bool":
    if has_relic(state, "LIZARD_TAIL"):
        return True
    potions = (state.get("run") or {}).get("potions") or []
    for potion in potions:
        if not isinstance(potion, dict):
            continue
        potion_id = str(potion.get("potion_id") or potion.get("id") or potion.get("name") or "").upper()
        if "FAIRY" in potion_id:
            return True
    return False


def shop_boss_survival_can_block_removal(
    best: "tuple[float, Any, Any, dict[str, Any]]",
    state: "dict[str, Any]",
    removal_score: float,
    core_buy_reasons: "list[str] | None" = None,
) -> "bool":
    if not best[1]:
        return False
    core_buy_reasons = core_buy_reasons if core_buy_reasons is not None else shop_core_buy_reasons(best, state)
    if not core_buy_reasons:
        return False
    hp, max_hp = player_hp(state)
    hp_ratio = hp / max_hp if (hp and max_hp) else 1.0
    urgent_ratio = policy_number("shop.boss_survival_before_remove_hp_ratio", 0.55)
    critical_ratio = policy_number("shop.boss_survival_before_remove_critical_hp_ratio", 0.38)
    score_margin = float(best[0]) - float(removal_score)
    protected = has_revive_safety(state)
    if hp_ratio <= critical_ratio:
        return True
    action = best[1]
    if action == "buy_potion":
        potion_id = shop_potion_id(best[3])
        defensive = potion_id in DEFENSIVE_POTION_IDS or any(
            token in potion_id
            for token in ("GHOST", "INTANGIBLE", "BLOCK", "DEXTERITY", "WEAK", "SHACKLING", "REGEN", "HEAL", "BLOOD")
        )
        flexible = potion_id in {"ENERGY_POTION", "GAMBLER_BREW", "SKILL_POTION", "SWIFT_POTION"}
        if hp_ratio <= urgent_ratio and (defensive or flexible):
            return True
        if (
            defensive
            and not protected
            and hp_ratio <= policy_number("shop.boss_survival_before_remove_unprotected_hp_ratio", 0.62)
            and score_margin >= policy_number("shop.boss_survival_before_remove_min_margin", 16.0)
        ):
            return True
        return False
    if protected and hp_ratio >= policy_number("shop.boss_survival_before_remove_protected_skip_ratio", 0.62):
        return False
    if action == "buy_card":
        survival_card = any(reason in core_buy_reasons for reason in ("survival-card", "boss-survival-card"))
        fills_need = any(reason in core_buy_reasons for reason in ("fills-block", "fills-damage", "fills-draw", "fills-scaling"))
        if hp_ratio <= urgent_ratio and survival_card:
            return True
        return fills_need and score_margin >= policy_number("shop.boss_survival_card_block_removal_margin", 46.0)
    if action == "buy_relic":
        if "high-impact-relic" in core_buy_reasons and score_margin >= policy_number("shop.boss_survival_relic_block_removal_margin", 42.0):
            return True
    return False


def shop_boss_survival_block_removal_threshold(state: "dict[str, Any]", removal_score: float) -> "float":
    plan = deck_plan(state)
    threshold = max(145.0, removal_score + 70.0)
    if plan.curse_status_count or plan.removable_count >= 9:
        threshold = max(threshold, 190.0)
    if plan.needs_draw and plan.draw_count == 0:
        threshold += 20.0
    return threshold


def choose_shop_action(state: "dict[str, Any]") -> "tuple[str, dict[str, int], str]":
    actions = as_actions(state)
    if "open_shop_inventory" in actions:
        return (
         "open_shop_inventory", {}, "open shop inventory")
    run = state.get("run") or {}
    gold = first_number(run.get("gold") or run.get("player_gold")) or 0
    items = shop_items(state)
    plan = deck_plan(state)
    profile = relic_profile(state)
    floor = first_number(run.get("floor") or run.get("current_floor")) or 0
    character_id = str(run.get("character_id") or run.get("character") or "").upper()
    boss_prep = floor >= 28 or floor in {12, 13, 14, 15, 16, 30, 31, 32, 46, 47, 48}
    hp, max_hp = player_hp(state)
    hp_ratio = hp / max_hp if (hp and max_hp) else 1.0
    removal_cost = first_number((state.get("shop") or {}).get("remove_cost") or (state.get("shop") or {}).get("card_remove_cost") or (state.get("shop") or {}).get("removal_cost")) or 75
    removal_score = 12 + plan.removable_count * 2 + plan.curse_status_count * 16 + policy_number("shop.removal_bias", 0.0) + relic_shop_removal_modifier(state)
    wants_shop_removal = "remove_card_at_shop" in actions and plan.wants_removal and gold >= removal_cost
    reserve_for_removal = wants_shop_removal and gold < policy_number("shop.removal_gold_reserve", 180.0) and plan.removable_count >= 5
    removal_first = wants_shop_removal and gold < policy_number("shop.removal_first_below_gold", 150.0)
    removal_priority = wants_shop_removal and (
        plan.removable_count >= 5
        or plan.curse_status_count > 0
        or ("card_quality" in profile.tags and plan.removable_count >= 3)
    )
    best = (-999.0, None, None, {})
    qualified_best = (-999.0, None, None, {})
    scored_items = []
    for i, item in enumerate(items):
        price = shop_item_price(item)
        if price and price > gold:
            continue
        blob = text_blob(item)
        score = 0.0
        action = None
        critical_potion_buy = False
        card_item = item_card_payload(item)
        if card_item is not None or "card" in blob or "卡牌" in blob:
            card_for_score = card_item or item
            score = score_reward_card(card_for_score, state) - price / 35
            score += policy_number("shop.card_bonus", 0.0)
            known = CARD_KNOWLEDGE.lookup(card_for_score)
            roles = frozenset(known.roles if known is not None else known_card_roles(card_for_score))
            cid = normalized_card_id(card_for_score)
            if known is not None:
                if plan.wants_archetype(known):
                    score += 8
                if plan.combat_ready and not plan.wants_archetype(known) and not known.roles & {"draw", "energy", "power_scaling", "aoe"}:
                    score -= 7
            if boss_prep and character_id == "SILENT":
                if cid in {
                    "BACKFLIP",
                    "BLUR",
                    "CLOAK_AND_DAGGER",
                    "DODGE_AND_ROLL",
                    "FOOTWORK",
                    "LEG_SWEEP",
                    "MALAISE",
                    "PIERCING_WAIL",
                    "WRAITH_FORM",
                }:
                    score += 18.0
                if roles & {"block_retention", "weak", "debuff", "strength", "dexterity"}:
                    score += 10.0
                if hp_ratio < 0.75 and (estimate_card_block(card_for_score) >= 8 or roles & {"block", "weak", "debuff", "strength", "dexterity"}):
                    score += 14.0
            action = "buy_card"
        elif item.get("relic_id") or "relic" in blob or "遗物" in blob:
            relic_score, relic_reasons = relic_pickup_score(item, state)
            score = 28 + relic_score - price / 40 + policy_number("shop.relic_bonus", 0.0)
            if plan.needs_damage or plan.needs_block:
                score -= 2
            if boss_prep and hp_ratio < 0.78 and relic_score >= 35:
                score += 14.0
            relic_id = str(item.get("relic_id") or item.get("id") or item.get("name") or "").strip().upper().replace(" ", "_")
            if character_id == "SILENT" and relic_id == "LETTER_OPENER":
                skill_count = deck_skill_count(state)
                if skill_count >= 7:
                    score += 34.0 + min(18.0, (skill_count - 7) * 3.0)
                if floor >= 18:
                    score += 10.0
            action = "buy_relic"
        elif item.get("potion_id") or "potion" in blob or "药水" in blob:
            score = 8 - price / 50 + policy_number("shop.potion_bonus", 0.0)
            if plan.needs_damage or plan.needs_block:
                score += 5
            nested_potion = item.get("potion") if isinstance(item.get("potion"), dict) else {}
            potion_id = str(
                item.get("potion_id")
                or nested_potion.get("potion_id")
                or nested_potion.get("id")
                or item.get("id")
                or item.get("name")
                or nested_potion.get("name")
                or ""
            ).upper()
            potion_blob = f"{blob} {text_blob(nested_potion)}"
            survival_potion = any(
                token in potion_id
                for token in (
                    "WEAK",
                    "SHACKLING",
                    "BLOCK",
                    "DEXTERITY",
                    "GHOST",
                    "INTANGIBLE",
                    "HEART_OF_IRON",
                    "HEAL",
                    "BLOOD",
                    "SPEED",
                    "FORTIFIER",
                    "REGEN",
                )
            ) or any(token in potion_blob for token in ("weak", "block", "dexterity", "intangible", "heal", "虚弱", "格挡", "治疗", "敏捷"))
            emergency_potion = survival_potion or any(
                token in potion_id
                for token in (
                    "ENERGY",
                    "SKILL",
                    "ATTACK",
                    "POWER",
                    "COLORLESS",
                    "DUPLICATOR",
                    "GAMBLER",
                    "SWIFT",
                    "STRENGTH",
                    "FIRE",
                    "EXPLOSIVE",
                )
            )
            if not potion_slots_full(state):
                score += policy_number("shop.empty_potion_slot_bonus", 8.0)
            if survival_potion and hp_ratio < 0.55:
                score += policy_number("shop.low_hp_survival_potion_bonus", 34.0)
                if hp_ratio < 0.38:
                    score += policy_number("shop.critical_hp_survival_potion_bonus", 18.0)
            if boss_prep and potion_id in BOSS_PREP_POTION_IDS and not potion_slots_full(state):
                score += policy_number("shop.boss_prep_potion_bonus", 36.0)
                if hp_ratio < 0.75:
                    score += 10.0
                critical_potion_buy = True
            elif floor >= 18 and character_id == "SILENT" and potion_id in ACT2_SURVIVAL_POTION_IDS and not potion_slots_full(state):
                score += 30.0
                if hp_ratio < 0.9:
                    score += 10.0
                if potion_id in DEFENSIVE_POTION_IDS:
                    score += 8.0
                critical_potion_buy = True
            elif emergency_potion and hp_ratio < policy_number("shop.critical_hp_generic_potion_ratio", 0.25) and not potion_slots_full(state):
                score += policy_number("shop.critical_hp_generic_potion_bonus", 52.0)
                critical_potion_buy = True
            action = "buy_potion"

        relic_item_score, relic_item_reasons = relic_shop_item_modifier(item, state)
        score += relic_item_score
        if action == "buy_card":
            card_for_score = item_card_payload(item) or item
            known = CARD_KNOWLEDGE.lookup(card_for_score)
            roles = frozenset(known.roles if known is not None else known_card_roles(card_for_score))
            generic_attack = roles <= {"attack"} and not card_draws_cards(card_for_score) and not card_costs_x(card_for_score)
            generic_block = roles <= {"block"} and not (plan.needs_block or hp_ratio < 0.55)
            if removal_priority and (generic_attack or generic_block):
                score -= 18
            if known is not None and "card_quality" in profile.tags and plan.card_count >= 16 and not reward_need_filled(known, plan):
                score -= 8
        if action == "buy_potion" and "potion" in profile.tags:
            score -= 4
        if reserve_for_removal and price and gold - price < removal_cost:
            if action == "buy_relic":
                score -= 18
            elif action == "buy_card":
                card_for_score = item_card_payload(item) or item
                known = CARD_KNOWLEDGE.lookup(card_for_score)
                score -= 40 if known is not None and not plan.wants_archetype(known) else 28
            elif action == "buy_potion":
                score -= 4 if critical_potion_buy else 16
        idx = first_number(item.get("index"))
        effective_idx = i if idx is None else idx
        if action:
            scored_items.append({'idx':int(effective_idx), 
             'score':round(score, 1), 
             'action':action, 
             'price':price, 
             'relic_reasons':relic_item_reasons, 
             'item':compact_shop_item(item)})
        if action and action in actions and score > best[0]:
            best = (score, action, effective_idx, item)
        if action and action in actions:
            buy_threshold = shop_buy_threshold_for_item(action, item, state, price)
            if score >= buy_threshold and score > qualified_best[0]:
                qualified_best = (score, action, effective_idx, item)

    if wants_shop_removal:
        can_buy_then_remove, core_buy_reasons, synergy_buy_score = shop_buy_before_removal_gate(best, state, gold, removal_cost, removal_score)
        core_buy_score = max(48.0, removal_score + (0.0 if (plan.needs_block or plan.needs_draw or plan.needs_damage) else 8.0))
        buy_then_remove_threshold = max(35.0, removal_score)
        if removal_priority and not core_buy_reasons:
            buy_then_remove_threshold += 18.0
        boss_survival_buy = bool(
            boss_prep
            and best[1]
            and best[1] in actions
            and core_buy_reasons
            and best[0] >= max(42.0, removal_score - 4.0)
            and shop_boss_survival_can_block_removal(best, state, removal_score, core_buy_reasons)
            and (
                shop_purchase_preserves_removal(best, gold, removal_cost)
                or best[0] >= shop_boss_survival_block_removal_threshold(state, removal_score)
            )
        )
        if boss_survival_buy and not shop_purchase_preserves_removal(best, gold, removal_cost):
            log(f"shop boss-survival-before-remove action={best[1]} idx={best[2]} score={best[0]:.1f} reasons={','.join(core_buy_reasons[:4])} plan={plan.summary()} relic={relic_summary(state)}", best[3])
            journal_decision("shop_buy", state, {'action':best[1],
             'idx':int(best[2]),  'score':round(best[0], 1),  'reason':"boss_survival_before_remove",  'core_reasons':core_buy_reasons[:6],  'item':compact_shop_item(best[3])}, {'items':scored_items,
             'gold':gold,  'removal_cost':removal_cost})
            return (
             str(best[1]), {"option_index": (int(best[2]))}, f"buy boss survival item before removal {','.join(core_buy_reasons[:3])}")
        if can_buy_then_remove and synergy_buy_score >= buy_then_remove_threshold:
            log(f"shop buy-before-remove action={best[1]} idx={best[2]} score={best[0]:.1f} synergy={synergy_buy_score:.1f} plan={plan.summary()} relic={relic_summary(state)}", best[3])
            journal_decision("shop_buy", state, {'action':best[1], 
             'idx':int(best[2]),  'score':round(best[0], 1),  'synergy_buy_score':round(synergy_buy_score, 1),  'reason':"buy_then_remove",  'item':compact_shop_item(best[3])}, {'items':scored_items, 
             'gold':gold,  'removal_cost':removal_cost})
            return (
             str(best[1]), {"option_index": (int(best[2]))}, "buy synergistic item before removal")
        if can_buy_then_remove and best[1] and best[1] in actions and core_buy_reasons and best[0] >= core_buy_score:
            log(f"shop core-buy action={best[1]} idx={best[2]} score={best[0]:.1f} reasons={','.join(core_buy_reasons[:4])} plan={plan.summary()} relic={relic_summary(state)}", best[3])
            journal_decision("shop_buy", state, {'action':best[1],
             'idx':int(best[2]),  'score':round(best[0], 1),  'reason':"core_before_remove",  'core_reasons':core_buy_reasons[:6],  'item':compact_shop_item(best[3])}, {'items':scored_items,
             'gold':gold,  'removal_cost':removal_cost})
            return (
             str(best[1]), {"option_index": (int(best[2]))}, f"buy core item before removal {','.join(core_buy_reasons[:3])}")
        if removal_first and best[0] < policy_number("shop.removal_first_buy_score", 150.0):
            journal_decision("shop_remove", state, {'action':"remove_card_at_shop", 
             'reason':"removal_first",  'removal_score':round(removal_score, 1),  'best_buy':round(best[0], 1)}, {'items':scored_items, 
             'gold':gold,  'removal_cost':removal_cost})
            return (
             "remove_card_at_shop", {}, f"remove before buying plan={plan.summary()} best_buy={best[0]:.1f}")
    if removal_priority and "remove_card_at_shop" in actions and gold >= removal_cost:
        core_buy_reasons = shop_core_buy_reasons(best, state)
        would_block_removal = best[1] and not shop_purchase_preserves_removal(best, gold, removal_cost)
        preserves_removal = shop_purchase_preserves_removal(best, gold, removal_cost)
        blocks_removal_as_core = bool(
            not preserves_removal
            and shop_boss_survival_can_block_removal(best, state, removal_score, core_buy_reasons)
            and best[0] >= shop_boss_survival_block_removal_threshold(state, removal_score)
        )
        boss_core_buy = bool(
            boss_prep
            and best[1]
            and core_buy_reasons
            and best[0] >= max(42.0, removal_score - 4.0)
            and (preserves_removal or blocks_removal_as_core)
        )
        if (would_block_removal or not core_buy_reasons or best[0] < max(removal_score + 10.0, 42.0)) and not boss_core_buy:
            journal_decision("shop_remove", state, {'action':"remove_card_at_shop",
             'reason':"preserve_removal_gold" if would_block_removal else "relic_quality_removal_priority",  'removal_score':round(removal_score, 1),  'best_buy':round(best[0], 1)}, {'items':scored_items,
             'gold':gold,  'removal_cost':removal_cost})
            return (
             "remove_card_at_shop", {}, f"remove weak card before marginal buy plan={plan.summary()}")
    if qualified_best[1]:
        log(f"shop buy action={qualified_best[1]} idx={qualified_best[2]} score={qualified_best[0]:.1f} plan={plan.summary()} relic={relic_summary(state)}", qualified_best[3])
        journal_decision("shop_buy", state, {'action':qualified_best[1], 
         'idx':int(qualified_best[2]),  'score':round(qualified_best[0], 1),  'threshold':round(shop_buy_threshold_for_item(qualified_best[1], qualified_best[3], state, shop_item_price(qualified_best[3])), 1),  'item':compact_shop_item(qualified_best[3])}, {'items':scored_items, 
         'gold':gold,  'removal_cost':removal_cost})
        return (
         str(qualified_best[1]), {"option_index": (int(qualified_best[2]))}, "buy useful shop item")
    if wants_shop_removal and best[0] < removal_score:
        journal_decision("shop_remove", state, {'action':"remove_card_at_shop", 
         'reason':"better_than_buy",  'removal_score':round(removal_score, 1),  'best_buy':round(best[0], 1)}, {'items':scored_items, 
         'gold':gold,  'removal_cost':removal_cost})
        return (
         "remove_card_at_shop", {}, f"remove weak card plan={plan.summary()}")
    if "close_shop_inventory" in actions:
        journal_decision("shop_close", state, {'action':"close_shop_inventory", 
         'best_buy':round(best[0], 1)}, {'items':scored_items, 
         'gold':gold,  'removal_cost':removal_cost})
        return (
         "close_shop_inventory", {}, "close shop")
    journal_decision("shop_leave", state, {'action':"proceed", 
     'best_buy':round(best[0], 1)}, {'items':scored_items, 
     'gold':gold,  'removal_cost':removal_cost})
    return (
     "proceed", {}, "leave shop")


def choose_relic_reward_index(state: "dict[str, Any]") -> "int | None":
    candidates = []
    sources = []
    for container_key in ('reward', 'treasure', 'selection', 'agent_view'):
        container = state.get(container_key) or {}
        if container_key == 'agent_view':
            container = container.get("reward") or {}
        if not isinstance(container, dict):
            continue
        for key in ('relics', 'rewards', 'items', 'options'):
            value = container.get(key)
            if isinstance(value, list):
                sources.extend(value)
    for i, item in enumerate(sources):
        if not isinstance(item, dict):
            continue
        if item.get("claimed") or item.get("disabled") or item.get("is_locked") or item.get("claimable") is False:
            continue
        blob = text_blob(item)
        if not (item.get("relic_id") or "relic" in blob or "遗物" in blob):
            continue
        idx = first_number(item.get("index") or item.get("i"))
        effective_idx = i if idx is None else idx
        score, reasons = relic_pickup_score(item, state)
        candidates.append((score, int(effective_idx), item, reasons))
    if not candidates:
        return None
    candidates.sort(reverse=True, key=(lambda x: x[0]))
    best_score, best_idx, best_item, best_reasons = candidates[0]
    log(f"relic reward pick idx={best_idx} score={best_score:.1f} relic={relic_summary(state)} reasons={best_reasons}", best_item)
    journal_decision("relic_reward", state, {'idx':best_idx, 
     'score':round(best_score, 1), 
     'reasons':best_reasons, 
     'item':compact_relic(best_item)}, {"options": [{'idx':idx,  'score':round(score, 1),  'reasons':reasons,  'item':compact_relic(item)} for score, idx, item, reasons in candidates]})
    return best_idx


def choose_potion_only_window_action(state: "dict[str, Any]", actions: "set[str]") -> "tuple[str, dict[str, int], str] | None":
    if "use_potion" in actions:
        action = choose_potion_action(state, actions)
        if action is not None:
            return action
    if state.get("in_combat") or state.get("screen") == "COMBAT":
        return None
    if "discard_potion" in actions:
        action = choose_discard_potion_action(state, actions)
        if action is not None:
            return action
    return None


def choose_deck_selection_index(state: "dict[str, Any]", avoid: "set[int] | None"=None) -> "int":
    selection = state.get("selection") or {}
    agent_selection = (state.get("agent_view") or {}).get("selection") or {}
    blob = text_blob(selection) + text_blob(agent_selection)
    selection_cards = selection.get("cards") if isinstance(selection.get("cards"), list) else []
    if not selection_cards and isinstance(agent_selection.get("cards"), list):
        selection_cards = agent_selection.get("cards") or []
    run = state.get("run") or {}
    deck = run.get("deck") or run.get("cards") or []
    combat_hand = (state.get("combat") or {}).get("hand") or []
    source_cards = selection_cards or (combat_hand if state.get("screen") == "CARD_SELECTION" else deck)
    if not isinstance(source_cards, list) or not source_cards:
        upgrade_target = choose_upgrade_target(state)
        return int(upgrade_target if upgrade_target is not None else 0)

    avoid = avoid or set()
    discard_like = any((k in blob for k in ('discard', '弃牌')))
    remove_like = any((k in blob for k in ('remove', 'transform', 'lose', 'exhaust', '移除', '删除', '变换')))
    combat = state.get("combat") or {}
    incoming = sum((enemy_pressure_damage(e) for e in combat.get("enemies") or [] if enemy_alive(e)))
    current_block = first_number(current_player(state).get("block")) or first_number(combat.get("block")) or 0
    hp, max_hp = player_hp(state)
    hp_ratio = hp / max_hp if (hp and max_hp) else 1.0

    best = None
    best_score = -9999.0
    scored = []
    for i, card in enumerate(source_cards):
        if not isinstance(card, dict):
            continue
        idx = first_number(card.get("index") or card.get("i"))
        effective_idx = i if idx is None else idx
        if effective_idx in avoid:
            continue
        if discard_like:
            score = discard_selection_score(card, state)
        elif remove_like:
            score = remove_selection_score(card, state)
        else:
            dmg = combat_card_damage(card, state)
            block = estimate_card_block(card)
            cost = card_cost(card)
            score = dmg * (2.0 if incoming <= current_block else 1.2) + block * (1.6 if incoming > current_block else 0.45)
            knowledge_score, knowledge_reasons = CARD_KNOWLEDGE.combat_modifier(
                card,
                state,
                damage=dmg,
                block=block,
                cost=cost,
                incoming=incoming,
                current_block=current_block,
                hp_ratio=hp_ratio,
                target_hp=None,
            )
            score += knowledge_score
            score -= cost * 0.25
            blob_card = text_blob(card)
            if any((k in blob_card for k in ('draw', '抽', 'energy', '能量', 'vulnerable', '易伤', 'weak', '虚弱', 'focus', '集中'))):
                score += 8
            if any((k in blob_card for k in ('exhaust', '消耗'))) and incoming > current_block:
                score -= 3
        scored.append({'idx':int(effective_idx), 'score':round(score, 1), 'card':compact_card(card)})
        if score > best_score:
            best = int(effective_idx)
            best_score = score

    chosen = int(best if best is not None else 0)
    journal_decision("deck_selection", state, {'idx':chosen, 'score':round(best_score, 1), 'mode':"discard" if discard_like else "remove" if remove_like else "pick"}, {"options": scored})
    return chosen


def selection_context_blob(selection: "dict[str, Any]", agent_selection: "dict[str, Any]") -> "str":
    parts = []
    for source in (selection, agent_selection):
        if not isinstance(source, dict):
            continue
        for key in (
            "prompt",
            "title",
            "header",
            "label",
            "text",
            "description",
            "context",
            "context_text",
            "mode",
            "selection_mode",
            "selection_type",
            "type",
            "action",
            "reason",
        ):
            value = source.get(key)
            if isinstance(value, str) and value:
                parts.append(value)
        for key in ("actions", "available_actions", "tags"):
            value = source.get(key)
            if isinstance(value, list):
                parts.extend(str(item) for item in value if isinstance(item, (str, int, float)))
    return " ".join(parts).lower()


def selection_number(selection: "dict[str, Any]", agent_selection: "dict[str, Any]", key: "str") -> "int | None":
    for source in (selection, agent_selection):
        if not isinstance(source, dict):
            continue
        number = first_number(source.get(key))
        if number is not None:
            return number
    return None


def readonly_card_selection_reason(state: "dict[str, Any]") -> "str | None":
    if state.get("screen") != "CARD_SELECTION":
        return None
    selection = state.get("selection") or {}
    agent_selection = (state.get("agent_view") or {}).get("selection") or {}
    max_pick = selection_number(selection, agent_selection, "max")
    min_pick = selection_number(selection, agent_selection, "min")
    if max_pick != 0 or min_pick not in (None, 0):
        return None
    if "confirm_selection" in as_actions(state):
        return None
    context_blob = selection_context_blob(selection, agent_selection)
    readonly_prompt = any(token in context_blob for token in (
        "draw pile",
        "discard pile",
        "will be shuffled",
        "shuffled into",
        "抽牌堆耗尽",
        "洗入抽牌堆",
        "抽牌堆",
        "弃牌堆",
    ))
    if readonly_prompt:
        return "read-only card pile view"
    return None


def selection_cards_match_deck(selection_cards: "list[dict[str, Any]]", deck: "list[dict[str, Any]]") -> "bool":
    if not selection_cards or not deck:
        return False
    deck_counts: dict[str, int] = {}
    for card in deck:
        if not isinstance(card, dict):
            continue
        cid = normalized_card_id(card)
        if cid:
            deck_counts[cid] = deck_counts.get(cid, 0) + 1
    matches = 0
    for card in selection_cards:
        if not isinstance(card, dict):
            continue
        cid = normalized_card_id(card)
        if cid and deck_counts.get(cid, 0) > 0:
            matches += 1
            deck_counts[cid] -= 1
    return matches >= max(3, min(len(selection_cards), int(len(selection_cards) * 0.6)))


def upgrade_selection_score(card: "dict[str, Any]", state: "dict[str, Any]") -> "float":
    if card.get("selected") or card.get("is_selected") or card.get("chosen") or card.get("disabled"):
        return -999.0
    if card.get("upgraded") or card.get("is_upgraded"):
        return -150.0
    dmg = estimate_card_damage(card)
    block = estimate_card_block(card)
    score = dmg + block + CARD_KNOWLEDGE.upgrade_modifier(card, state, damage=dmg, block=block)
    cid = normalized_card_id(card)
    if cid in {"BASH", "NEUTRALIZE", "SURVIVOR", "ZAP", "DUALCAST", "FALLING_STAR", "VENERATE"}:
        score += 35
    known = CARD_KNOWLEDGE.lookup(card)
    plan = deck_plan(state)
    if known is not None:
        if plan.wants_archetype(known):
            score += 14
        if plan.needs_damage and "attack" in known.roles:
            score += 6
        if plan.needs_block and "block" in known.roles:
            score += 6
        if plan.needs_draw and "draw" in known.roles:
            score += 8
        if plan.needs_scaling and "power_scaling" in known.roles:
            score += 8
        if known.roles & {"draw", "energy", "star_resource", "debuff"}:
            score += 5
    return score


def choose_deck_selection_index(state: "dict[str, Any]", avoid: "set[int] | None"=None) -> "int":
    selection = state.get("selection") or {}
    agent_selection = (state.get("agent_view") or {}).get("selection") or {}
    context_blob = selection_context_blob(selection, agent_selection)
    selection_cards = selection.get("cards") if isinstance(selection.get("cards"), list) else []
    if not selection_cards and isinstance(agent_selection.get("cards"), list):
        selection_cards = agent_selection.get("cards") or []
    run = state.get("run") or {}
    deck = run.get("deck") or run.get("cards") or []
    combat = state.get("combat") or {}
    combat_hand = combat.get("hand") or []
    source_cards = selection_cards or (combat_hand if state.get("screen") == "CARD_SELECTION" else deck)
    if not isinstance(source_cards, list) or not source_cards:
        upgrade_target = choose_upgrade_target(state)
        return int(upgrade_target if upgrade_target is not None else 0)

    avoid = avoid or set()
    discard_like = any(token in context_blob for token in ("discard", "弃牌", "丢弃"))
    remove_like = any(token in context_blob for token in ("remove", "transform", "lose", "exhaust", "purge", "forget", "移除", "删除", "变换", "变化"))
    upgrade_like = any(token in context_blob for token in ("upgrade", "smith", "升级", "锻造"))
    in_combat_selection = bool(state.get("in_combat") or state.get("screen") == "COMBAT" or combat.get("enemies"))
    deck_like_selection = selection_cards_match_deck(selection_cards, deck if isinstance(deck, list) else [])
    reward_pick_like = bool(selection_cards) and not in_combat_selection and not remove_like and not upgrade_like and not deck_like_selection
    if reward_pick_like:
        discard_like = False

    incoming = sum((intent_damage(e) for e in combat.get("enemies") or [] if enemy_alive(e)))
    current_block = first_number((combat.get("player") or {}).get("block")) or 0
    hp, max_hp = player_hp(state)
    hp_ratio = hp / max_hp if (hp and max_hp) else 1.0

    best = None
    best_score = -9999.0
    scored = []
    for i, card in enumerate(source_cards):
        if not isinstance(card, dict):
            continue
        idx = first_number(card.get("index") or card.get("i"))
        effective_idx = i if idx is None else idx
        if effective_idx in avoid:
            continue
        if discard_like:
            score = discard_selection_score(card, state)
        elif remove_like:
            score = remove_selection_score(card, state)
        elif upgrade_like:
            score = upgrade_selection_score(card, state)
        elif reward_pick_like:
            score = score_reward_card(card, state)
        else:
            dmg = combat_card_damage(card, state)
            block = estimate_card_block(card)
            cost = card_cost(card)
            score = dmg * (2.0 if incoming <= current_block else 1.2) + block * (1.6 if incoming > current_block else 0.45)
            gap = max(0, incoming - current_block)
            survival_pick = (
                gap >= 18
                or hp is not None and gap >= max(10, int(hp * 0.35))
                or hp_ratio < 0.45 and gap >= 8
            )
            if survival_pick:
                if block > 0:
                    score += 12 + min(block, gap) * (2.8 if hp_ratio < 0.55 else 1.8)
                elif dmg > 0:
                    score -= 12 + min(70, gap * (1.5 if hp_ratio < 0.55 else 1.0))
            knowledge_score, _ = CARD_KNOWLEDGE.combat_modifier(
                card,
                state,
                damage=dmg,
                block=block,
                cost=cost,
                incoming=incoming,
                current_block=current_block,
                hp_ratio=hp_ratio,
                target_hp=None,
            )
            score += knowledge_score
            score -= cost * 0.25
            blob_card = text_blob(card)
            if any(token in blob_card for token in ("draw", "energy", "vulnerable", "weak", "focus", "抽牌", "能量", "易伤", "虚弱", "集中")):
                score += 8
            if "exhaust" in blob_card and incoming > current_block:
                score -= 3
            if card_has_unmet_play_condition(card, state):
                score -= 220
            if card_has_hand_end_damage(card):
                score += 70
        scored.append({"idx": int(effective_idx), "score": round(score, 1), "card": compact_card(card)})
        if score > best_score:
            best = int(effective_idx)
            best_score = score

    chosen = int(best if best is not None else 0)
    mode = "discard" if discard_like else "remove" if remove_like else "upgrade" if upgrade_like else "reward_pick" if reward_pick_like else "pick"
    journal_decision("deck_selection", state, {"idx": chosen, "score": round(best_score, 1), "mode": mode}, {"options": scored})
    return chosen


def choose_claim_reward_index(state: "dict[str, Any]") -> "int | None":
    rewards = claimable_reward_options(state)
    best = (-999.0, None, None, [])
    scored_options = []
    for i, reward in enumerate(rewards):
        if reward.get("claimed") or reward.get("disabled") or reward.get("is_locked") or reward.get("claimable") is False:
            continue
        if reward_blocked_by_inventory(reward, state):
            idx = first_number(reward.get("index") or reward.get("i"))
            effective_idx = i if idx is None else idx
            scored_options.append({'idx':int(effective_idx),
             'score':-120.0,
             'reward_type':reward.get("reward_type") or reward.get("type"),
             'card':None,
             'relic':None,
             'reasons':["potion-slots-full"],
             'text':reward.get("text") or reward.get("name") or reward.get("label") or reward.get("description")})
            continue
        idx = first_number(reward.get("index") or reward.get("i"))
        effective_idx = i if idx is None else idx
        blob = text_blob(reward)
        score = 0.0
        reasons = []
        if "relic" in blob or reward.get("relic_id") or "遗物" in blob:
            relic_score, relic_reasons = relic_pickup_score(reward, state)
            score += 70 + relic_score
            reasons.extend(relic_reasons)
        elif "card" in blob or reward.get("card_id") or reward.get("id"):
            card_score, card_reasons = claim_card_reward_score(state)
            score += card_score
            reasons.extend(card_reasons)
            card_threshold = claim_card_reward_threshold(state)
            if score < card_threshold and (
                "resolve_rewards" in as_actions(state)
                or "collect_rewards_and_proceed" in as_actions(state)
                or "skip_reward_cards" in as_actions(state)
            ):
                reasons.append(f"below-card-claim-threshold:{card_threshold:.0f}")
                scored_options.append({'idx':int(effective_idx),
                 'score':round(score, 1),
                 'reward_type':reward.get("reward_type") or reward.get("type"),
                 'card':compact_card(reward) if (reward.get("card_id") or reward.get("id")) else None,
                 'relic':None,
                 'reasons':reasons,
                 'text':reward.get("text") or reward.get("name") or reward.get("label") or reward.get("description")})
                continue
        elif "potion" in blob or reward.get("potion_id"):
            relic_item_score, relic_item_reasons = relic_shop_item_modifier(reward, state)
            score += 15 + relic_item_score
            reasons.extend(relic_item_reasons)
        elif "gold" in blob:
            score += 18
            if relic_profile(state).shop_strength or relic_profile(state).removal_pressure:
                score += 5
                reasons.append("relic-gold-useful")
        scored_options.append({'idx':int(effective_idx), 
         'score':round(score, 1), 
         'reward_type':reward.get("reward_type") or reward.get("type"), 
         'card':compact_card(reward) if (reward.get("card_id") or reward.get("id")) else None, 
         'relic':compact_relic(reward) if (reward.get("relic_id") or "relic" in blob or "遗物" in blob) else None, 
         'reasons':reasons, 
         'text':reward.get("text") or reward.get("name") or reward.get("label") or reward.get("description")})
        if score > best[0]:
            best = (score, int(effective_idx), reward, reasons)

    if best[1] is not None:
        log(f"claim reward idx={best[1]} score={best[0]:.1f} relic={relic_summary(state)}", best[2])
        journal_decision("claim_reward", state, {'idx':best[1], 
         'score':round(best[0], 1), 
         'reasons':best[3]}, {"options": scored_options})
    return best[1]


def click_divine_unknown_fallback() -> "bool":
    if os.name != "nt":
        return False
    try:
        user32 = ctypes.windll.user32
    except AttributeError:
        return False
    else:
        try:
            hwnd = None
            for title in ('Slay the Spire 2', '127.0.0.1'):
                hwnd = user32.FindWindowW(None, title)
                if hwnd:
                    break

            if not hwnd:
                return False
            user32.ShowWindow(hwnd, 9)
            user32.SetForegroundWindow(hwnd)
            time.sleep(0.2)
            rect = ctypes.wintypes.RECT()
            if not user32.GetClientRect(hwnd, ctypes.byref(rect)):
                return False
            origin = ctypes.wintypes.POINT(0, 0)
            user32.ClientToScreen(hwnd, ctypes.byref(origin))
            width = max(1, rect.right - rect.left)
            height = max(1, rect.bottom - rect.top)
            points = [
             (0.64, 0.78), 
             (0.7, 0.82), 
             (0.76, 0.82), 
             (0.84, 0.88), 
             (0.92, 0.88)]
            for x_ratio, y_ratio in points:
                x = int(origin.x + width * x_ratio)
                y = int(origin.y + height * y_ratio)
                user32.SetCursorPos(x, y)
                time.sleep(0.45)
                user32.mouse_event(2, 0, 0, 0, 0)
                time.sleep(0.08)
                user32.mouse_event(4, 0, 0, 0, 0)
                time.sleep(0.4)

            return True
        except Exception as exc:
            try:
                log(f"divine fallback failed {type(exc).__name__}: {exc}")
                return False
            finally:
                exc = None
                del exc


@dataclass
class Autoplayer:
    client: "Sts2Client"
    steps = 0
    steps: "int"
    combats_won = 0
    combats_won: "int"
    last_screen = None
    last_screen: "str | None"
    attempts = 1
    attempts: "int"
    max_attempts = 1
    max_attempts: "int"
    opened_shop_floors = None
    opened_shop_floors: "set[int] | None"
    deck_selection_attempts = None
    deck_selection_attempts: "dict[str, set[int]] | None"
    unknown_waits = 0
    unknown_waits: "int"

    def act(self, action, reason, **kwargs):
        kwargs = {k: v for k, v in kwargs.items() if v is not None}
        log(f"step={self.steps} act={action} kwargs={kwargs} reason={reason}")
        return (self.client.execute_action)(
 action, **kwargs, **{"client_context": {'source':"codex-autoplayer", 
                            'reason':reason}})

    def run(self, max_steps: "int"=1200) -> "dict[str, Any]":
        if self.opened_shop_floors is None:
            self.opened_shop_floors = set()
        if self.deck_selection_attempts is None:
            self.deck_selection_attempts = {}
        while self.steps < max_steps:
            state = self.client.get_state()
            self.steps += 1
            screen = state.get("screen")
            if screen != self.last_screen:
                log(f"screen={screen}", compact_state(state))
                self.last_screen = screen
                if screen != "CARD_SELECTION":
                    if self.deck_selection_attempts is not None:
                        self.deck_selection_attempts.clear()
            if state.get("game_over") or screen == "GAME_OVER":
                game_over = state.get("game_over") or {}
                log("game over reached", compact_state(state))
                journal_decision("game_over", state, {'is_victory':bool(game_over.get("is_victory")), 
                 'attempt':self.attempts, 
                 'steps':self.steps}, {"game_over": game_over})
                if "return_to_main_menu" in as_actions(state):
                    if self.steps <= 2:
                        self.act("return_to_main_menu", "clear previous game over before starting")
                        self.last_screen = None
                        time.sleep(1)
                        continue
                if game_over.get("is_victory"):
                    return {'status':"victory", 
                     'steps':self.steps,  'attempts':self.attempts,  'state':state}
                if "return_to_main_menu" in as_actions(state):
                    if self.attempts < self.max_attempts:
                        self.act("return_to_main_menu", "restart after failed attempt")
                        self.attempts += 1
                        self.last_screen = None
                        time.sleep(1)
                        continue
                return {'status':"game_over", 
                 'steps':self.steps,  'attempts':self.attempts,  'state':state}
            actions = as_actions(state)
            if not actions:
                self.unknown_waits += 1
                if screen == "UNKNOWN":
                    if (state.get("in_combat") or self.unknown_waits) >= 2:
                        if click_divine_unknown_fallback():
                            log("clicked divine unknown fallback", compact_state(state))
                            time.sleep(1.5)
                            continue
                try:
                    waited = self.client.wait_for_event(event_names=[
                     'player_action_window_opened', 
                     'route_decision_required', 
                     'reward_decision_required', 
                     'available_actions_changed', 
                     'screen_changed'],
                      timeout=5)
                    log("waited for action", waited)
                except Exception:
                    time.sleep(1)
                else:
                    continue

            self.unknown_waits = 0
            try:
                self.step(state, actions)
            except ReadOnlyCardSelection as exc:
                log(f"readonly card selection blocked: {exc}", compact_state(state))
                return {'status':"readonly_card_selection",  'steps':self.steps,  'state':state}
            except Sts2ApiError as exc:
                try:
                    log(f"api error {exc}", compact_state(state))
                    time.sleep(1)
                finally:
                    exc = None
                    del exc

            except Exception as exc:
                try:
                    log(f"unexpected error {type(exc).__name__}: {exc}", state)
                    raise
                finally:
                    exc = None
                    del exc

            time.sleep(0.35)

        state = self.client.get_state()
        return {'status':"max_steps",  'steps':self.steps,  'state':state}

    def step(self, state: "dict[str, Any]", actions: "set[str]") -> "None":
        screen = state.get("screen")
        if "confirm_modal" in actions:
            modal = state.get("modal") or {}
            modal_type = str(modal.get("type_name") or modal.get("type") or "")
            if "Tutorial" in modal_type or "Ftue" in modal_type:
                self.act("dismiss_modal", "skip tutorial")
            else:
                self.act("confirm_modal", "confirm modal")
            return
        if "open_character_select" in actions:
            self.act("open_character_select", f"start {TARGET_CHARACTER_ID} run")
            return
        if "select_character" in actions:
            if not target_character_selected(state, TARGET_CHARACTER_ID):
                self.act("select_character",
                  f"select {TARGET_CHARACTER_ID}",
                  option_index=(choose_character_index(state, TARGET_CHARACTER_ID)))
                return
        if "embark" in actions:
            self.act("embark", f"embark {TARGET_CHARACTER_ID}")
            return
        if "continue_run" in actions:
            if screen == "MAIN_MENU":
                self.act("continue_run", "continue active run")
                return
        if "confirm_selection" in actions:
            self.act("confirm_selection", "confirm completed selection")
            return
        if "choose_reward_card" in actions:
            idx = choose_reward_index(state)
            if idx is None and "skip_reward_cards" in actions:
                self.act("skip_reward_cards", "skip weak rewards")
            else:
                self.act("choose_reward_card", "pick best reward card", option_index=(idx or 0))
            return
        if "select_deck_card" in actions:
            readonly_reason = readonly_card_selection_reason(state)
            if readonly_reason:
                raise ReadOnlyCardSelection(readonly_reason)
            selection = state.get("selection") or {}
            run = state.get("run") or {}
            cards = selection.get("cards") if isinstance(selection.get("cards"), list) else []
            fingerprint = ",".join((str(c.get("card_id") or c.get("id") or c.get("name") or "") for c in cards[:8]))
            key = f'{run.get("run_id")}:{run.get("floor")}:{selection.get("prompt")}:{fingerprint}'
            attempts = self.deck_selection_attempts.setdefault(key, set()) if self.deck_selection_attempts is not None else set()
            idx = choose_deck_selection_index(state, attempts)
            attempts.add(idx)
            self.act("select_deck_card",
              "select deck card for current screen",
              option_index=idx)
            return
        potion_action = choose_potion_action(state, actions)
        if potion_action is not None:
            action, kwargs, reason = potion_action
            (self.act)(action, reason, **kwargs)
            return
        discard_potion_action = choose_discard_potion_action(state, actions)
        if discard_potion_action is not None:
            if len(actions) == 1:
                action, kwargs, reason = discard_potion_action
                (self.act)(action, reason, **kwargs)
                return
        if "play_card" in actions or state.get("in_combat"):
            action, kwargs, reason = choose_combat_action(state)
            if action in actions:
                (self.act)(action, reason, **kwargs)
            else:
                if "end_turn" in actions:
                    self.act("end_turn", "combat fallback end turn")
                return
        if "choose_reward_card" in actions:
            idx = choose_reward_index(state)
            if idx is None and "skip_reward_cards" in actions:
                self.act("skip_reward_cards", "skip weak rewards")
            else:
                self.act("choose_reward_card", "pick best reward card", option_index=(idx or 0))
            return
        if "claim_reward" in actions:
            idx = choose_claim_reward_index(state)
            self.act("claim_reward", "claim useful reward", option_index=(idx or 0))
            return
            if "resolve_rewards" in actions:
                idx = choose_reward_index(state)
                if idx is None:
                    self.act("resolve_rewards", "resolve rewards without card")
                else:
                    self.act("resolve_rewards", "resolve best reward", option_index=idx)
                return
            if "collect_rewards_and_proceed" in actions:
                self.act("collect_rewards_and_proceed", "collect rewards and proceed")
                return
            if "skip_reward_cards" in actions:
                self.act("skip_reward_cards", "skip reward fallback")
                return
            if "choose_map_node" in actions:
                self.act("choose_map_node", "choose best route", option_index=(choose_map_index(state)))
                return
            if "open_chest" in actions:
                self.act("open_chest", "open chest")
                return
            if "choose_treasure_relic" in actions:
                self.act("choose_treasure_relic", "take relic", option_index=0)
                return
            if "choose_event_option" in actions:
                self.act("choose_event_option", "choose event option", option_index=(choose_event_index(state)))
                return
            if "choose_rest_option" in actions:
                idx, target = choose_rest_index(state)
                self.act("choose_rest_option", "choose rest option", option_index=idx, target_index=target)
                return
        else:
            for action in ('choose_capstone_option', 'choose_bundle'):
                if action in actions:
                    self.act(action, "choose first progression option", option_index=0)
                    return

            if "confirm_bundle" in actions:
                self.act("confirm_bundle", "confirm bundle")
                return
                if any((a in actions for a in ('open_shop_inventory', 'buy_card', 'buy_relic',
                                               'buy_potion', 'remove_card_at_shop',
                                               'close_shop_inventory'))):
                    floor = first_number((state.get("run") or {}).get("floor")) or -1
                    if "open_shop_inventory" in actions and "proceed" in actions:
                        if self.opened_shop_floors is not None and floor in self.opened_shop_floors:
                            self.act("proceed", "leave shop after browsing")
            elif self.opened_shop_floors is not None:
                self.opened_shop_floors.add(floor)
            self.act("open_shop_inventory", "open shop inventory")
            return
        action, kwargs, reason = choose_shop_action(state)
        if action in actions:
            (self.act)(action, reason, **kwargs)
        else:
            if "proceed" in actions:
                self.act("proceed", "leave shop fallback")
            else:
                return
                if "proceed" in actions:
                    self.act("proceed", "proceed")
                    return
                if "close_main_menu_submenu" in actions:
                    self.act("close_main_menu_submenu", "close submenu fallback")
                    return
                if "dismiss_modal" in actions:
                    self.act("dismiss_modal", "dismiss modal fallback")
                    return
                safe_fallback_actions = [a for a in sorted(actions) if a != "discard_potion"]
                discard_potion_action = safe_fallback_actions or choose_discard_potion_action(state, actions)
                if discard_potion_action is not None:
                    action, kwargs, reason = discard_potion_action
                    (self.act)(action, reason, **kwargs)
                return
            action = safe_fallback_actions[0]
            kwargs = {}
            spec = next((a for a in action_specs(self.client.get_available_actions()) if a.get("name") == action), {})
            if spec.get("requires_index"):
                kwargs["option_index"] = 0
            (self.act)(action, "last-resort available action", **kwargs)


def _autoplayer_step(self: "Autoplayer", state: "dict[str, Any]", actions: "set[str]") -> "None":
    screen = state.get("screen")
    if screen == "MAIN_MENU" and "close_main_menu_submenu" in actions and "open_character_select" not in actions:
        self.act("close_main_menu_submenu", "close submenu before starting")
        return
    if "confirm_modal" in actions:
        modal = state.get("modal") or {}
        modal_type = str(modal.get("type_name") or modal.get("type") or "")
        if "Tutorial" in modal_type or "Ftue" in modal_type:
            self.act("dismiss_modal", "skip tutorial")
        else:
            self.act("confirm_modal", "confirm modal")
        return
    if "open_character_select" in actions:
        self.act("open_character_select", f"start {TARGET_CHARACTER_ID} run")
        return
    if "select_character" in actions:
        if not target_character_selected(state, TARGET_CHARACTER_ID):
            self.act("select_character",
              f"select {TARGET_CHARACTER_ID}",
              option_index=(choose_character_index(state, TARGET_CHARACTER_ID)))
            return
    if "embark" in actions:
        self.act("embark", f"embark {TARGET_CHARACTER_ID}")
        return
    if "continue_run" in actions and screen == "MAIN_MENU":
        self.act("continue_run", "continue active run")
        return
    if "confirm_selection" in actions:
        self.act("confirm_selection", "confirm completed selection")
        return
    if "choose_reward_card" in actions:
        idx = choose_reward_index(state)
        if idx is None and "skip_reward_cards" in actions:
            self.act("skip_reward_cards", "skip weak rewards")
        else:
            self.act("choose_reward_card", "pick best reward card", option_index=(idx or 0))
        return
    if "select_deck_card" in actions:
        readonly_reason = readonly_card_selection_reason(state)
        if readonly_reason:
            raise ReadOnlyCardSelection(readonly_reason)
        selection = state.get("selection") or {}
        run = state.get("run") or {}
        cards = selection.get("cards") if isinstance(selection.get("cards"), list) else []
        fingerprint = ",".join((str(c.get("card_id") or c.get("id") or c.get("name") or "") for c in cards[:8]))
        key = f'{run.get("run_id")}:{run.get("floor")}:{selection.get("prompt")}:{fingerprint}'
        attempts = self.deck_selection_attempts.setdefault(key, set()) if self.deck_selection_attempts is not None else set()
        idx = choose_deck_selection_index(state, attempts)
        attempts.add(idx)
        self.act("select_deck_card", "select deck card for current screen", option_index=idx)
        return

    if actions and actions.issubset({"use_potion", "discard_potion"}):
        potion_only_action = choose_potion_only_window_action(state, actions)
        if potion_only_action is not None:
            action, kwargs, reason = potion_only_action
            self.act(action, reason, **kwargs)
        return

    potion_action = choose_potion_action(state, actions)
    if potion_action is not None:
        action, kwargs, reason = potion_action
        self.act(action, reason, **kwargs)
        return
    if "discard_potion" in actions and len(actions) == 1:
        discard_potion_action = choose_discard_potion_action(state, actions)
        if discard_potion_action is not None:
            action, kwargs, reason = discard_potion_action
            self.act(action, reason, **kwargs)
        return

    if "play_card" in actions or state.get("in_combat"):
        action, kwargs, reason = choose_combat_action(state)
        if action in actions:
            self.act(action, reason, **kwargs)
        elif "end_turn" in actions:
            self.act("end_turn", "combat fallback end turn")
        else:
            log("combat action unavailable; waiting", {"wanted": action, "actions": sorted(actions)})
        return

    if "claim_reward" in actions:
        idx = choose_claim_reward_index(state)
        if idx is None:
            if "resolve_rewards" in actions:
                self.act("resolve_rewards", "resolve rewards and skip blocked reward", option_index=-1)
                return
            if "collect_rewards_and_proceed" in actions:
                self.act("collect_rewards_and_proceed", "collect rewards and proceed")
                return
            log("claim reward unavailable; waiting", compact_state(state))
            return
        self.act("claim_reward", "claim useful reward", option_index=(idx or 0))
        return
    if "resolve_rewards" in actions:
        idx = choose_reward_index(state)
        if idx is None:
            self.act("resolve_rewards", "resolve rewards and skip weak card", option_index=-1)
        else:
            self.act("resolve_rewards", "resolve best reward", option_index=idx)
        return
    if "collect_rewards_and_proceed" in actions:
        self.act("collect_rewards_and_proceed", "collect rewards and proceed")
        return
    if "skip_reward_cards" in actions:
        self.act("skip_reward_cards", "skip reward fallback")
        return
    if "choose_map_node" in actions:
        self.act("choose_map_node", "choose best route", option_index=(choose_map_index(state)))
        return
    if "open_chest" in actions:
        self.act("open_chest", "open chest")
        return
    if "choose_treasure_relic" in actions:
        idx = choose_relic_reward_index(state)
        self.act("choose_treasure_relic", "take best relic", option_index=(idx or 0))
        return
    if "choose_event_option" in actions:
        self.act("choose_event_option", "choose event option", option_index=(choose_event_index(state)))
        return
    if "choose_rest_option" in actions:
        idx, target = choose_rest_index(state)
        self.act("choose_rest_option", "choose rest option", option_index=idx, target_index=target)
        return
    for action in ("choose_capstone_option", "choose_bundle"):
        if action in actions:
            self.act(action, "choose first progression option", option_index=0)
            return
    if "confirm_bundle" in actions:
        self.act("confirm_bundle", "confirm bundle")
        return

    shop_actions = {
        "open_shop_inventory",
        "buy_card",
        "buy_relic",
        "buy_potion",
        "remove_card_at_shop",
        "close_shop_inventory",
    }
    if any((a in actions for a in shop_actions)):
        floor = first_number((state.get("run") or {}).get("floor") or (state.get("run") or {}).get("current_floor")) or -1
        if "open_shop_inventory" in actions:
            if "proceed" in actions and self.opened_shop_floors is not None and floor in self.opened_shop_floors:
                self.act("proceed", "leave shop after browsing")
                return
            if self.opened_shop_floors is not None:
                self.opened_shop_floors.add(floor)
            self.act("open_shop_inventory", "open shop inventory")
            return
        action, kwargs, reason = choose_shop_action(state)
        if action in actions:
            self.act(action, reason, **kwargs)
            return
        if "close_shop_inventory" in actions:
            self.act("close_shop_inventory", "close shop inventory fallback")
            return
        if "proceed" in actions:
            self.act("proceed", "leave shop fallback")
            return
        log("shop action unavailable; waiting", {"wanted": action, "actions": sorted(actions)})
        return

    if "proceed" in actions:
        self.act("proceed", "proceed")
        return
    if "close_main_menu_submenu" in actions:
        self.act("close_main_menu_submenu", "close submenu fallback")
        return
    if "dismiss_modal" in actions:
        self.act("dismiss_modal", "dismiss modal fallback")
        return

    potion_only_action = choose_potion_only_window_action(state, actions)
    if potion_only_action is not None:
        action, kwargs, reason = potion_only_action
        self.act(action, reason, **kwargs)
        return

    risky_actions = {
        "play_card",
        "buy_card",
        "buy_relic",
        "buy_potion",
        "remove_card_at_shop",
        "discard_potion",
        "use_potion",
        "select_deck_card",
        "choose_reward_card",
        "claim_reward",
        "choose_event_option",
        "choose_rest_option",
        "choose_map_node",
        "choose_treasure_relic",
    }
    safe_fallback_actions = [a for a in sorted(actions) if a not in risky_actions]
    if not safe_fallback_actions:
        log("no safe fallback action; waiting", compact_state(state))
        return
    action = safe_fallback_actions[0]
    kwargs = {}
    spec = next((a for a in action_specs(state.get("available_actions")) if a.get("name") == action or a.get("action") == action), {})
    if spec.get("requires_index"):
        kwargs["option_index"] = 0
    self.act(action, "last-resort available action", **kwargs)


Autoplayer.step = _autoplayer_step


def parse_args(argv: "list[str] | None"=None) -> "argparse.Namespace":
    parser = argparse.ArgumentParser(description="Run the STS2 local autoplay agent.")
    parser.add_argument("--character",
      default=TARGET_CHARACTER_ID,
      help="Target character id for new runs. Default is RANDOM_CHARACTER to use the game's random-character option.")
    parser.add_argument("--max-steps",
      type=int,
      default=(int(os.getenv("STS2_AUTOPLAY_MAX_STEPS", "1200"))),
      help="Maximum number of action loop iterations before stopping.")
    parser.add_argument("--attempts",
      type=int,
      default=(int(os.getenv("STS2_AUTOPLAY_ATTEMPTS", "1"))),
      help="Maximum failed-run attempts before stopping. Default is 1 to avoid runaway restarts.")
    return parser.parse_args(argv)


def main(argv: "list[str] | None"=None) -> "int":
    global TARGET_CHARACTER_ID
    args = parse_args(argv)
    TARGET_CHARACTER_ID = str(args.character or TARGET_CHARACTER_ID).strip().upper()
    LOG_PATH.write_text("", encoding="utf-8")
    client = Sts2Client()
    player = Autoplayer(client, max_attempts=(max(1, int(args.attempts))))
    result = player.run(max_steps=(max(1, int(args.max_steps))))
    SUMMARY_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    log("finished", {'status':(result.get)("status"),  'steps':(result.get)("steps")})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
