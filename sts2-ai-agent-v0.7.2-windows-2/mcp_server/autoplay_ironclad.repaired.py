# uncompyle6 version 3.9.2
# Python bytecode version base 3.7.0 (3394)
# Decompiled from: Python 3.7.7 (tags/v3.7.7:d7c567b08f, Mar 10 2020, 09:44:33) [MSC v.1900 32 bit (Intel)]
# Embedded file name: .\autoplay_ironclad.py
# Compiled at: 2026-06-01 04:04:31
# Size of source mod 2**32: 143799 bytes
from __future__ import annotations
import argparse, ctypes, ctypes.wintypes, hashlib, json, math, os, re, sys, time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from sts2_mcp.client import Sts2ApiError, Sts2Client
from autoplay_strategy import CARD_KNOWLEDGE, card_id_from_payload
LOG_PATH = Path(__file__).with_name("autoplay_ironclad.log")
SUMMARY_PATH = Path(__file__).with_name("autoplay_ironclad_summary.json")
JOURNAL_PATH = Path(__file__).with_name("autoplay_decision_journal.jsonl")
POLICY_PATH = Path(os.getenv("STS2_AUTOPLAY_POLICY", str(Path(__file__).with_name("autoplay_policy.json"))))
TARGET_CHARACTER_ID = os.getenv("STS2_AUTOPLAY_CHARACTER", "RANDOM_CHARACTER").strip().upper()
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

    return isinstance(cur, bool) or isinstance(cur, (int, float)) or default
    return float(cur)


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
        if isinstance(raw_action, str):
            actions.add(raw_action)
        elif isinstance(raw_action, dict):
            name = raw_action.get("name") or raw_action.get("action")
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


def compact_relic(relic: "dict[str, Any] | None") -> "dict[str, Any]":
    if not isinstance(relic, dict):
        return {}
    return {'id':relic.get("relic_id") or relic.get("id"), 
     'name':(relic.get)("name"), 
     'tier':relic.get("tier") or relic.get("rarity")}


def compact_potion(potion: "dict[str, Any] | None") -> "dict[str, Any]":
    if not isinstance(potion, dict):
        return {}
    return {'id':potion.get("potion_id") or potion.get("id"), 
     'name':(potion.get)("name"), 
     'occupied':(potion.get)("occupied")}


def compact_shop_item(item: "dict[str, Any] | None") -> "dict[str, Any]":
    if not isinstance(item, dict):
        return {}
    return {'index':(item.get)("index"), 
     'price':item.get("price") or item.get("cost") or item.get("gold_cost"), 
     'card':compact_card(item) if (item.get("card_id") or item.get("id")) else None, 
     'relic':compact_relic(item) if (item.get("relic_id")) else None, 
     'potion':compact_potion(item) if (item.get("potion_id")) else None, 
     'name':item.get("name") or item.get("label") or item.get("title"), 
     'type':item.get("item_type") or item.get("type")}


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


def card_text_blob(card: "dict[str, Any]") -> "str":
    parts = []
    for key in ('card_id', 'id', 'name', 'rules_text', 'resolved_rules_text', 'description',
                'description_raw'):
        value = card.get(key)
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
    blob = card_text_blob(card)
    return any((token in blob for token in ('gain energy', 'gain [e]', 'gain star',
                                            'gain stars', '获得能量', '获得{stars', '获得 res://images/packed/sprite_fonts/star_icon')))


def card_resource_gain(card: "dict[str, Any]") -> "int":
    amount = dynamic_value_amount(card, "Energy", "Stars", "Star", "star_resource")
    if amount is not None:
        return max(0, amount)
    if card_grants_combat_resource(card):
        return 1
    return 0


def card_energy_gain(card: "dict[str, Any]") -> "int":
    amount = dynamic_value_amount(card, "Energy")
    if amount is not None:
        return max(0, amount)
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


def relics(state: "dict[str, Any]") -> "list[dict[str, Any]]":
    run = state.get("run") or {}
    raw_relics = run.get("relics") or run.get("player_relics") or []
    if isinstance(raw_relics, list):
        return raw_relics
    return []


def has_relic(state: "dict[str, Any]", *ids: "str") -> "bool":
    wanted = {relic_id.upper() for relic_id in ids}
    for relic in relics(state):
        relic_id = str(relic.get("relic_id") or relic.get("id") or relic.get("name") or "").upper()
        if relic_id in wanted:
            return True

    return False


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


def card_star_cost(card: "dict[str, Any]") -> "int":
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


def enemy_damage_after_card(card, target, enemies):
    total = 0
    weakens = "weak" in known_card_roles(card) or "虚弱" in card_text_blob(card).lower()
    for idx, enemy in enumerate(enemies):
        if not enemy_alive(enemy):
            continue
        elif target is not None:
            if idx == target:
                if combat_card_damage(card, {"combat": {"enemies": enemies}}) >= enemy_hp(enemy):
                    continue
        damage = intent_damage(enemy)
        if weakens:
            if target is not None:
                if idx == target and damage:
                    damage = int(damage * 0.75)
        total += damage

    return total


def remaining_affordable_block(cards, card, *, remaining_energy, state=None):
    block_cards = []
    for other in cards:
        if same_card_instance(other, card):
            continue
        block = estimate_card_block(other)
        if state is not None:
            block += attack_relic_block(other, state)
        if block <= 0:
            continue
        cost = card_cost(other)
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
        return nums or 0
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


def enemy_threat_score(enemy: "dict[str, Any]") -> "float":
    enemy_id = str(enemy.get("enemy_id") or enemy.get("id") or "").upper()
    blob = text_blob(enemy)
    score = float(intent_damage(enemy) * 2)
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
    damage_pressure = intent_damage(enemy)
    if is_minion and has_real_enemy:
        score -= 24
        if lethal:
            if damage_pressure + status_pressure * 3 >= 10:
                score += 18
        if damage_pressure >= 12:
            score += 12
    else:
        if status_pressure >= 3:
            score += 8
        else:
            if minion_count:
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
    card_type = str(card.get("card_type") or card.get("type") or "").lower()
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


def combat_card_damage(card: "dict[str, Any]", state: "dict[str, Any]") -> "int":
    cid = str(card.get("card_id") or card.get("id") or "").lower()
    if "body_slam" in cid:
        player = current_player(state)
        combat = state.get("combat") or {}
        return first_number(player.get("block")) or first_number(combat.get("block")) or 0
    return estimate_card_damage(card)


def estimate_card_block(card: "dict[str, Any]") -> "int":
    blob = text_blob(card)
    cid = str(card.get("card_id") or card.get("id") or "").lower()
    name = str(card.get("name") or "").lower()
    card_type = str(card.get("card_type") or "").lower()
    if "body_slam" in cid:
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
    if card.get("costs_x") or card.get("star_costs_x"):
        return 99
    cost = first_number(card.get("energy_cost", card.get("cost")))
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
        if explicit:
            return [int(i) for i in explicit if isinstance(i, int) or str(i).isdigit()]
    return [int(enemy.get("index", i)) for i, enemy in enumerate(enemies) if enemy_alive(enemy)]


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
    cost = card_cost(card)
    damage = combat_card_damage(card, state)
    block = estimate_card_block(card) + attack_relic_block(card, state)
    combat = state.get("combat") or {}
    enemies = combat.get("enemies") or []
    incoming = sum((intent_damage(enemy) for enemy in enemies if enemy_alive(enemy)))
    current_block = first_number(current_player(state).get("block")) or first_number(combat.get("block")) or 0
    energy_after_card = max(0, player_energy(state) - cost + card_energy_gain(card))
    stars = player_stars(state)
    cards_played = played_this_turn(state)
    plan = deck_plan(state)
    reasons = []
    score = 0.0
    baggage = hand_baggage_count(cards)
    payload_count = hand_playable_payload_count(cards, state)
    has_followup_attack = any((not same_card_instance(other, card) and combat_card_damage(other, state) > 0 and card_cost(other) <= energy_after_card for other in cards))
    has_followup_block = any((not same_card_instance(other, card) and estimate_card_block(other) > 0 and card_cost(other) <= energy_after_card for other in cards))
    affordable_missing_star = any((not same_card_instance(other, card) and card_star_cost(other) > stars and card_star_cost(other) <= stars + card_star_gain(card) for other in cards))
    draws_cards = card_draws_cards(card)
    grants_resource = card_grants_combat_resource(card)
    generates_cards = card_generates_combat_cards(card)
    is_power_setup = "power_scaling" in roles or known_card_type(card) == "power" or "power" in blob or "能力" in blob
    is_debuff_setup = any((token in roles for token in ('vulnerable', 'weak', 'debuff', 'doom'))) or any((token in blob for token in ('vulnerable', 'weak', 'doom', '易伤', '虚弱', '灾厄')))
    is_summon_setup = cid in frozenset({'BODYGUARD', 'SUMMON_FORTH', 'NECRO_MASTERY'}) or any((token in blob for token in ('summon', '召唤')))

    if damage or block:
        return (
         0.0, reasons)

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
        if card_resource_gain(card):
            resource_bonus += min(10, card_resource_gain(card) * 4)
        score += resource_bonus
        reasons.append("setup-energy")

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


def discard_selection_score(card: "dict[str, Any]", state: "dict[str, Any]") -> "float":
    cid = normalized_card_id(card)
    roles = known_card_roles(card)
    card_type = known_card_type(card)
    rarity = str(card.get("rarity") or "").lower()
    cost = card_cost(card)
    dmg = combat_card_damage(card, state)
    block = estimate_card_block(card)
    combat = state.get("combat") or {}
    incoming = sum((intent_damage(enemy) for enemy in combat.get("enemies") or [] if enemy_alive(enemy)))
    current_block = first_number(current_player(state).get("block")) or first_number(combat.get("block")) or 0
    score = 0.0
    if card_is_generated_baggage(card):
        score += 180
    if cid in SILENT_SLY_RESOURCE_IDS:
        score -= 160
    if card_has_sly(card):
        score -= 95
    if cid in SILENT_DISCARD_SCALING_IDS | SILENT_DISCARD_ENGINE_IDS:
        score -= 85
    if "not_for_drafting" in roles or card_type in frozenset({'status', 'curse', 'quest'}) or "curse" in rarity:
        score += 220
    if dmg:
        score -= min(dmg, 24) * 1.2
        if any((enemy_alive(enemy) and dmg >= enemy_hp(enemy) for enemy in combat.get("enemies") or [])):
            score -= 45
    if block:
        need = max(0, incoming - current_block)
        score -= min(block, need) * 2.2 + max(0, block - need) * 0.4
    if any((key in text_blob(card) for key in ('strike', 'defend', 'strike_silent', 'defend_silent'))):
        score += 48 if "strike" in text_blob(card) else 36
    if card_type == "attack" and incoming > current_block:
        score += 8
    if cost >= 3 and cid not in SILENT_DISCARD_SCALING_IDS | SILENT_DISCARD_ENGINE_IDS:
        score += 18
    if cost == 0 and not card_has_sly(card) and not card_is_generated_baggage(card):
        score -= 8
    if card.get("upgraded") or card.get("is_upgraded"):
        score -= 18
    if rarity == "rare" and not card_is_generated_baggage(card):
        score -= 12
    return score


def remove_selection_score(card: "dict[str, Any]", state: "dict[str, Any]") -> "float":
    cid = normalized_card_id(card)
    roles = known_card_roles(card)
    card_type = known_card_type(card)
    rarity = str(card.get("rarity") or "").lower()
    plan = deck_plan(state)
    score = 0.0
    if card.get("selected") or card.get("is_selected") or card.get("chosen") or card.get("disabled"):
        return -999.0
    if card_type in frozenset({'curse', 'status', 'quest'}) or "curse" in rarity or "not_for_drafting" in roles:
        score += 260
    if cid in frozenset({'STRIKE', 'STRIKE_IRONCLAD', 'STRIKE_SILENT', 'STRIKE_DEFECT', 'STRIKE_NECROBINDER', 'STRIKE_REGENT'}):
        score += 130
        if plan.needs_damage:
            score -= 25
    if cid in frozenset({'DEFEND', 'DEFEND_IRONCLAD', 'DEFEND_SILENT', 'DEFEND_DEFECT', 'DEFEND_NECROBINDER', 'DEFEND_REGENT'}):
        score += 115
        if plan.needs_block:
            score -= 30
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
    return score


def best_discard_target_score(cards, state, *, exclude=None):
    scores = [same_card_instance(card, exclude) or discard_selection_score(card, state) for card in cards if not exclude is None]
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
    remaining_energy = max(0, energy - card_cost(card) + card_energy_gain(card))
    remaining_stars = stars + card_star_gain(card)
    first_block = estimate_card_block(card) + attack_relic_block(card, state)
    post_incoming = enemy_damage_after_card(card, target, enemies)
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
        if card_star_cost(other) > remaining_stars:
            continue
        other_cost = card_cost(other)
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
    if card_energy_gain(card) or card_star_gain(card):
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
            remaining_energy = max(0, energy - cost + card_energy_gain(card))
            post_incoming = enemy_damage_after_card(card, target, enemies)
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


def plan_summary(state: "dict[str, Any]") -> "str":
    return deck_plan(state).summary()


def reward_need_filled(known: "Any", plan: "Any") -> "bool":
    roles = known.roles
    return bool(plan.needs_damage and "attack" in roles or plan.needs_block and "block" in roles or plan.needs_draw and "draw" in roles or plan.needs_scaling and "power_scaling" in roles or plan.needs_aoe and "aoe" in roles)


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


def map_lookahead_score(node, state, depth=4):
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


def map_risk_score(node, state, depth=4):
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
    for i, node in enumerate(opts):
        idx = first_number(node.get("index"))
        base = node_score(node, state)
        lookahead = map_lookahead_score(node, state)
        risk = map_risk_score(node, state)
        tie = map_tiebreak_score(node, state)
        total = base + policy_number("map.lookahead_weight", 0.45) * lookahead + risk + tie
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
    incoming = sum((intent_damage(e) for e in combat.get("enemies") or [] if enemy_alive(e)))
    current_block = first_number((combat.get("player") or {}).get("block")) or 0
    damage_gap = max(0, incoming - current_block)
    projected_hp = (hp or 999) - incoming
    projected_ratio = projected_hp / max_hp if max_hp else 1.0
    enemies = combat.get("enemies") or []
    danger = damage_gap >= 12 or projected_ratio <= 0.5 or ratio <= 0.45
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
                defensive_potion = any((k in potion_id for k in ('BLOCK', 'FORTIFIER',
                                                                 'GHOST', 'DEXTERITY'))) or any((k in blob for k in ('block',
                                                                                                                     'intangible')))
                if defensive_potion:
                    score += 45 + damage_gap
                    if not danger:
                        if incoming <= 0:
                            score -= 35
                if not any((k in potion_id for k in ('HEAL', 'BLOOD'))):
                    if "heal" in blob:
                        score += 30 if ratio < 0.45 else 5
                    if any((k in potion_id for k in ('DUPLICATOR', 'ENERGY', 'STRENGTH',
                                                     'FIRE', 'EXPLOSIVE'))):
                        score += 22 if (projected_ratio < 0.55 or incoming >= 18) else 8
                    if any((k in potion_id for k in ('FIRE', 'EXPLOSIVE'))):
                        target = choose_enemy_for_damage(enemies, 20)
                        kill_score = 0.0
                        if target is not None:
                            if 0 <= target < len(enemies):
                                target_hp = enemy_hp(enemies[target])
                                kill_score = enemy_target_score((enemies[target]),
                                  enemies,
                                  damage=20,
                                  lethal=(target_hp <= 20)) * 0.6
                                score += kill_score
                                if target_hp <= 20:
                                    score += 70
                elif danger:
                    score += 18
                if (danger or incoming) <= 0:
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

    threshold = 30 if danger else 55
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
