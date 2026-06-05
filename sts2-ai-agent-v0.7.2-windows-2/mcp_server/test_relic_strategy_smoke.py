from __future__ import annotations

import autoplay_ironclad as ai
from autoplay_relic_strategy import (
    current_relics,
    current_relic_ids,
    relic_card_reward_modifier,
    relic_profile,
)


def sample_state() -> dict:
    return {
        "screen": "COMBAT_REWARD",
        "run": {
            "character_id": "SILENT",
            "floor": 8,
            "current_hp": 48,
            "max_hp": 70,
            "gold": 170,
            "deck": [
                {"id": "STRIKE_SILENT", "name": "Strike", "type": "Attack", "cost": 1},
                {"id": "DEFEND_SILENT", "name": "Defend", "type": "Skill", "cost": 1},
                {"id": "NEUTRALIZE", "name": "Neutralize", "type": "Attack", "cost": 0},
            ],
            "relics": [
                {"id": "RING_OF_THE_SNAKE", "name": "Ring of the Snake"},
                {"id": "PRECARIOUS_SHEARS", "name": "Precarious Shears"},
                {"id": "BAG_OF_MARBLES", "name": "Bag of Marbles"},
                {"id": "SHURIKEN", "name": "Shuriken"},
            ],
        },
        "reward": {
            "rewards": [
                {"reward_type": "Card", "index": 0, "name": "Card Reward"},
                {"reward_type": "Relic", "index": 1, "name": "Unknown Relic"},
            ]
        },
    }


def main() -> int:
    state = sample_state()
    ids = current_relic_ids(state)
    profile = relic_profile(state)
    assert "RING_OF_THE_SNAKE" in ids
    assert "draw" in profile.tags
    assert "removal" in profile.tags
    assert "attack" in profile.tags
    assert "card_quality" in profile.tags
    assert ai.choose_claim_reward_index(state) == 1

    string_relic_state = {"run": {"relics": ["Ring of the Snake"], "deck": []}}
    assert current_relics(string_relic_state)[0]["id"] == "RING_OF_THE_SNAKE"
    assert "RING_OF_THE_SNAKE" in current_relic_ids(string_relic_state)

    vajra_state = {
        "combat": {"energy": 3, "enemies": [{"hp": 20, "intent": "Attack 0"}]},
        "run": {"deck": [], "relics": [{"id": "VAJRA", "name": "Vajra"}]},
    }
    strike = {"id": "STRIKE_SILENT", "name": "Strike", "type": "Attack", "cost": 1}
    assert ai.combat_card_damage(strike, {"combat": vajra_state["combat"], "run": {"deck": [], "relics": []}}) == 6
    assert ai.combat_card_damage(strike, vajra_state) == 7

    current_relic_state = {
        "run": {
            "character_id": "NECROBINDER",
            "current_hp": 40,
            "max_hp": 60,
            "deck": [],
            "relics": [
                {"id": "BOUND_PHYLACTERY", "name": "Bound Phylactery"},
                {"id": "DIVINE_RIGHT", "name": "Divine Right"},
                {"id": "PRECISE_SCISSORS", "name": "Precise Scissors"},
            ],
        }
    }
    current_profile = relic_profile(current_relic_state)
    assert "summon" in current_profile.tags
    assert "starter_resource" in current_profile.tags
    assert "card_quality" in current_profile.tags
    assert current_profile.combat_strength >= 14

    attack = {"id": "NEUTRALIZE", "name": "Neutralize", "type": "Attack", "cost": 0}
    skill = {"id": "DEFEND_SILENT", "name": "Defend", "type": "Skill", "cost": 1}
    attack_score, attack_reasons = relic_card_reward_modifier(attack, state)
    skill_score, _ = relic_card_reward_modifier(skill, state)
    assert attack_score > skill_score
    assert "relic-attack-chain" in attack_reasons

    x_card = {"id": "TEST_X", "name": "X Strike", "type": "Attack", "cost": 0, "is_x_cost": True, "damage": 9}
    x_card["description"] = "Deal 9 damage X times."
    combat_state = {
        "combat": {"energy": 3, "hand": [x_card], "enemies": [{"hp": 20, "intent": "Attack 0"}]},
        "run": {"deck": [], "relics": []},
    }
    assert ai.card_cost(x_card) == 99
    assert ai.combat_card_energy_cost(x_card, combat_state) == 3
    assert ai.combat_card_damage(x_card, combat_state) == 27
    zero_x_state = {
        "combat": {"energy": 0, "hand": [x_card], "enemies": [{"hp": 20, "intent": "Attack 0"}]},
        "run": {"deck": [], "relics": []},
    }
    assert ai.combat_card_energy_cost(x_card, zero_x_state) == 0
    assert ai.combat_card_damage(x_card, zero_x_state) == 0
    chemical_x_state = {
        "combat": {"energy": 0, "hand": [x_card], "enemies": [{"hp": 20, "intent": "Attack 0"}]},
        "run": {"deck": [], "relics": [{"id": "CHEMICAL_X", "name": "Chemical X"}]},
    }
    assert ai.combat_card_damage(x_card, chemical_x_state) == 18

    cascade_card = {
        "id": "CASCADE",
        "name": "Cascade",
        "type": "Skill",
        "cost": -1,
        "is_x_cost": True,
        "description": "Play the top X cards of your Draw Pile.",
    }
    assert ai.card_costs_x(cascade_card) is True
    assert ai.card_cost(cascade_card) == 99

    reduced_card = {
        "id": "DYNAMIC_COST",
        "name": "Dynamic Cost",
        "type": "Attack",
        "cost": 2,
        "cost_for_turn": 0,
        "damage": 8,
    }
    assert ai.card_cost(reduced_card) == 0
    assert ai.combat_card_energy_cost(reduced_card, combat_state) == 0

    fixed_cost_flagged = {
        "id": "SCRAPE",
        "name": "Scrape",
        "type": "Attack",
        "cost": 1,
        "is_x_cost": True,
        "description": "Deal 7 damage. Draw 4 cards. Discard all cards drawn this way that do not cost 0 [energy:1].",
    }
    assert ai.card_costs_x(fixed_cost_flagged) is False
    assert ai.card_cost(fixed_cost_flagged) == 1

    bullet_time_card = {
        "id": "BULLET_TIME",
        "name": "Bullet Time",
        "type": "Skill",
        "cost": 3,
        "is_x_cost": True,
        "description": "You cannot draw additional cards this turn. ALL cards in your Hand are free to play this turn.",
    }
    assert ai.card_costs_x(bullet_time_card) is False
    assert ai.card_cost(bullet_time_card) == 3

    star_x = {
        "id": "STARDUST",
        "name": "Stardust",
        "type": "Attack",
        "cost": 0,
        "is_x_star_cost": True,
        "description": "Deal 5 damage to a random enemy X times.",
    }
    star_state = {"combat": {"energy": 3, "stars": 4}, "run": {"deck": [], "relics": []}}
    assert ai.card_cost(star_x) == 0
    assert ai.combat_card_energy_cost(star_x, star_state) == 0
    assert ai.combat_card_star_cost(star_x, star_state) == 4
    assert ai.combat_card_damage(star_x, star_state) == 20

    double_energy_state = {
        "screen": "COMBAT",
        "available_actions": ["play_card", "end_turn"],
        "combat": {
            "energy": 3,
            "player": {"block": 0},
            "hand": [
                {
                    "index": 0,
                    "id": "DOUBLE_ENERGY",
                    "name": "Double Energy",
                    "type": "Skill",
                    "cost": 1,
                    "description": "Double your Energy.",
                    "playable": True,
                    "requires_target": False,
                },
                {
                    "index": 1,
                    "id": "GLACIER",
                    "name": "Glacier",
                    "type": "Skill",
                    "cost": 2,
                    "block": 7,
                    "description": "Gain 7 Block. Channel 2 Frost.",
                    "playable": True,
                    "requires_target": False,
                },
                {
                    "index": 2,
                    "id": "DEFEND_DEFECT",
                    "name": "Defend",
                    "type": "Skill",
                    "cost": 1,
                    "block": 5,
                    "playable": True,
                    "requires_target": False,
                },
                {
                    "index": 3,
                    "id": "DEFEND_DEFECT",
                    "name": "Defend",
                    "type": "Skill",
                    "cost": 1,
                    "block": 5,
                    "playable": True,
                    "requires_target": False,
                },
            ],
            "enemies": [{"index": 0, "id": "TEST_ENEMY", "hp": 40, "intent": "Attack 17"}],
        },
        "run": {"character_id": "DEFECT", "current_hp": 30, "max_hp": 75, "deck": [], "relics": []},
    }
    assert ai.card_energy_gain(double_energy_state["combat"]["hand"][0], double_energy_state) == 2
    combat_action, kwargs, reason = ai.choose_combat_action(double_energy_state)
    assert combat_action == "play_card", reason
    assert kwargs["card_index"] == 0

    minimal_cold_snap = {"id": "COLD_SNAP", "name": "Cold Snap", "cost": 1, "playable": True, "requires_target": True}
    minimal_sweeping_beam = {"id": "SWEEPING_BEAM", "name": "Sweeping Beam", "cost": 1}
    minimal_leap = {"id": "LEAP", "name": "Leap", "cost": 1}
    assert ai.estimate_card_damage(minimal_cold_snap) == 6
    assert ai.combat_card_damage(minimal_cold_snap, {"combat": {}, "run": {"deck": [], "relics": []}}) == 6
    assert ai.estimate_card_damage(minimal_sweeping_beam) == 6
    assert ai.card_draws_cards(minimal_sweeping_beam) is True
    assert ai.estimate_card_block(minimal_leap) == 9

    minimal_zap_state = {
        "screen": "COMBAT",
        "available_actions": ["play_card", "end_turn"],
        "combat": {
            "energy": 3,
            "player": {"block": 0},
            "hand": [{"index": 0, "id": "ZAP", "name": "Zap+", "cost": 0, "playable": True, "requires_target": False}],
            "enemies": [{"index": 0, "id": "TEST_ENEMY", "hp": 40, "intent": "Attack 0"}],
        },
        "run": {"character_id": "DEFECT", "current_hp": 60, "max_hp": 75, "deck": [], "relics": [{"id": "CRACKED_CORE"}]},
    }
    combat_action, _, reason = ai.choose_combat_action(minimal_zap_state)
    assert combat_action == "play_card", reason
    minimal_zap_state["combat"]["enemies"][0]["intent"] = "Attack 12"
    combat_action, _, reason = ai.choose_combat_action(minimal_zap_state)
    assert combat_action == "play_card", reason

    assert ai.enemy_pressure_damage({"id": "FOGMOG", "hp": 40, "intent": "SWIPE_MOVE"}) >= 9
    assert ai.enemy_pressure_damage({"id": "NIBBIT", "hp": 42, "intent": "BUTT_MOVE"}) >= 13
    assert ai.enemy_threat_score({"id": "EYE_WITH_TEETH", "hp": 6, "intent": "DISTRACT_MOVE"}) >= 28

    class FreshCombatClient:
        def __init__(self, state: dict) -> None:
            self.state = state

        def get_state(self) -> dict:
            return self.state

    class RecordingClient(FreshCombatClient):
        def __init__(self, state: dict) -> None:
            super().__init__(state)
            self.executed: list[tuple[str, dict]] = []

        def execute_action(self, action: str, **kwargs) -> dict:
            self.executed.append((action, kwargs))
            return {"ok": True}

    fresh_combat_state = {
        "screen": "COMBAT",
        "available_actions": ["play_card", "end_turn"],
        "combat": {
            "energy": 1,
            "player": {"block": 0},
            "hand": [
                {"index": 0, "id": "DEFEND_SILENT", "name": "Defend", "type": "Skill", "cost": 1, "block": 5, "playable": True},
                {
                    "index": 3,
                    "id": "NEUTRALIZE",
                    "name": "Neutralize",
                    "type": "Attack",
                    "cost": 0,
                    "damage": 3,
                    "playable": True,
                    "requires_target": True,
                },
            ],
            "enemies": [{"index": 0, "id": "FOGMOG", "hp": 3, "intent": "SWIPE_MOVE"}],
        },
        "run": {"character_id": "SILENT", "current_hp": 40, "max_hp": 70, "deck": [], "relics": []},
    }
    autoplayer = ai.Autoplayer(FreshCombatClient(fresh_combat_state), 0, 0, None, 1, 1, set(), {}, 0)
    fresh_action, fresh_kwargs, fresh_reason = autoplayer.combat_action_from_fresh_state(
        "play_card",
        {"card_index": 4, "target_index": 0},
        "stale combat action",
    )
    assert fresh_action == "play_card", fresh_reason
    assert fresh_kwargs["card_index"] == 3, fresh_reason

    fresh_selection_state = {
        "screen": "CARD_SELECTION",
        "available_actions": ["select_deck_card"],
        "selection": {"prompt": "Draw pile", "max": 0, "min": 0, "cards": []},
        "run": {"character_id": "SILENT", "current_hp": 40, "max_hp": 70, "deck": [], "relics": []},
    }
    autoplayer = ai.Autoplayer(FreshCombatClient(fresh_selection_state), 0, 0, None, 1, 1, set(), {}, 0)
    fresh_action, fresh_kwargs, fresh_reason = autoplayer.combat_action_from_fresh_state(
        "play_card",
        {"card_index": 1, "target_index": 0},
        "stale combat action",
    )
    assert fresh_action == "wait", fresh_reason
    assert fresh_kwargs == {}, fresh_reason

    cards_view_state = {
        "screen": "CARDS_VIEW",
        "available_actions": ["close_cards_view"],
        "in_combat": True,
        "combat": {"hand": [], "enemies": []},
        "run": {"character_id": "SILENT", "deck": [], "relics": []},
    }
    close_client = RecordingClient(cards_view_state)
    autoplayer = ai.Autoplayer(close_client, 0, 0, None, 1, 1, set(), {}, 0)
    autoplayer.step(cards_view_state, ai.as_actions(cards_view_state))
    assert close_client.executed[0][0] == "close_cards_view"

    original_close_readonly = ai.close_readonly_card_selection_fallback
    try:
        fallback_calls = []

        def fake_close_readonly() -> bool:
            fallback_calls.append(True)
            return True

        ai.close_readonly_card_selection_fallback = fake_close_readonly
        readonly_client = RecordingClient(fresh_selection_state)
        autoplayer = ai.Autoplayer(readonly_client, 0, 0, None, 1, 1, set(), {}, 0)
        autoplayer.readonly_selection_waits = 8
        autoplayer.step(fresh_selection_state, ai.as_actions(fresh_selection_state))
        assert fallback_calls
        assert readonly_client.executed == []
    finally:
        ai.close_readonly_card_selection_fallback = original_close_readonly

    cold_snap_priority_state = {
        **minimal_zap_state,
        "combat": {
            **minimal_zap_state["combat"],
            "energy": 1,
            "hand": [
                {"index": 0, "id": "STRIKE_DEFECT", "name": "Strike", "cost": 1, "playable": True, "requires_target": True},
                {"index": 1, "id": "COLD_SNAP", "name": "Cold Snap", "cost": 1, "playable": True, "requires_target": True},
            ],
        },
    }
    combat_action, kwargs, reason = ai.choose_combat_action(cold_snap_priority_state)
    assert combat_action == "play_card", reason
    assert kwargs["card_index"] == 1, reason

    vajra_kill_state = {
        "combat": {"energy": 3, "enemies": [{"hp": 7, "intent": "Attack 14"}]},
        "run": {"deck": [], "relics": [{"id": "VAJRA", "name": "Vajra"}]},
    }
    six_damage_attack = {"id": "STRIKE_SILENT", "name": "Strike", "type": "Attack", "cost": 1}
    assert ai.enemy_damage_after_card(six_damage_attack, 0, vajra_kill_state["combat"]["enemies"]) == 14
    assert ai.enemy_damage_after_card(six_damage_attack, 0, vajra_kill_state["combat"]["enemies"], vajra_kill_state) == 0

    free_attack = {
        "id": "FREE_NEXT_ATTACK",
        "name": "Free Next Attack",
        "type": "Attack",
        "cost": 1,
        "description": "Deal 1 damage. The next Attack you play costs 0 [energy:1].",
    }
    heavy_attack = {"id": "HEAVY_ATTACK", "name": "Heavy", "type": "Attack", "cost": 3, "damage": 18}
    combo_state = {
        "combat": {
            "energy": 1,
            "hand": [free_attack, heavy_attack],
            "enemies": [{"hp": 40, "intent": "Attack 0"}],
        },
        "run": {"deck": [], "relics": []},
    }
    combo, reasons = ai.followup_combo_value(
        free_attack,
        combo_state,
        [free_attack, heavy_attack],
        0,
        incoming=0,
        current_block=0,
        energy=1,
        stars=0,
    )
    assert combo > 0
    assert reasons

    full_potion_reward_state = {
        "screen": "REWARD",
        "available_actions": ["claim_reward", "resolve_rewards"],
        "run": {
            "deck": [],
            "relics": [],
            "potions": [
                {"index": 0, "potion_id": "FYSH_OIL", "occupied": True},
                {"index": 1, "potion_id": "HEART_OF_IRON", "occupied": True},
                {"index": 2, "potion_id": "FLEX_POTION", "occupied": True},
            ],
        },
        "reward": {"rewards": [{"index": 0, "reward_type": "Potion", "description": "Energy Potion"}]},
    }
    assert ai.potion_slots_full(full_potion_reward_state) is True
    assert ai.choose_claim_reward_index(full_potion_reward_state) is None

    high_hp_explosive_state = {
        "screen": "COMBAT",
        "available_actions": ["use_potion", "play_card", "end_turn"],
        "combat": {
            "player": {"block": 0},
            "enemies": [{"index": 0, "id": "TEST_ENEMY", "hp": 45, "block": 0, "intent": "Attack 12"}],
        },
        "run": {
            "current_hp": 64,
            "max_hp": 70,
            "deck": [],
            "relics": [],
            "potions": [{"index": 0, "id": "EXPLOSIVE_AMPOULE", "occupied": True, "requires_target": True}],
        },
    }
    assert ai.choose_potion_action(high_hp_explosive_state, {"use_potion"}) is None

    boss_prep_fire_potion_state = {
        **high_hp_explosive_state,
        "combat": {
            **high_hp_explosive_state["combat"],
            "enemies": [{"index": 0, "id": "LEAF_SLIME_M", "hp": 22, "block": 0, "intent": "Attack 5"}],
        },
        "run": {
            **high_hp_explosive_state["run"],
            "character_id": "SILENT",
            "floor": 15,
            "current_hp": 54,
            "max_hp": 75,
            "relics": [{"id": "LIZARD_TAIL", "name": "Lizard Tail"}],
            "potions": [{"index": 0, "id": "FIRE_POTION", "occupied": True, "requires_target": True}],
        },
    }
    assert ai.choose_potion_action(boss_prep_fire_potion_state, {"use_potion"}) is None

    silent_chip_speed_potion_state = {
        "screen": "COMBAT",
        "available_actions": ["use_potion", "play_card", "end_turn"],
        "combat": {
            "energy": 3,
            "player": {"block": 0},
            "hand": [
                {"index": 0, "id": "SURVIVOR", "name": "Survivor", "type": "Skill", "cost": 1, "block": 8, "playable": True},
                {"index": 1, "id": "NEUTRALIZE", "name": "Neutralize", "type": "Attack", "cost": 0, "damage": 3, "playable": True, "requires_target": True},
                {"index": 2, "id": "DEFEND_SILENT", "name": "Defend", "type": "Skill", "cost": 1, "block": 5, "playable": True},
                {"index": 3, "id": "STRIKE_SILENT", "name": "Strike", "type": "Attack", "cost": 1, "damage": 6, "playable": True, "requires_target": True},
                {"index": 4, "id": "DEFEND_SILENT", "name": "Defend", "type": "Skill", "cost": 1, "block": 5, "playable": True},
                {"index": 5, "id": "ACCURACY", "name": "Accuracy", "type": "Power", "cost": 1, "playable": True},
                {"index": 6, "id": "PIERCING_WAIL", "name": "Piercing Wail", "type": "Skill", "cost": 1, "description": "ALL enemies lose 6 Strength this turn. Exhaust.", "playable": True},
            ],
            "enemies": [
                {"index": 0, "id": "TOADPOLE", "hp": 25, "block": 0, "intent": "Attack 0"},
                {"index": 1, "id": "TOADPOLE", "hp": 24, "block": 0, "intent": "Attack 7"},
            ],
        },
        "run": {
            "character_id": "SILENT",
            "floor": 5,
            "current_hp": 37,
            "max_hp": 70,
            "deck": [],
            "relics": [{"id": "RING_OF_THE_SNAKE", "name": "Ring of the Snake"}],
            "potions": [{"index": 0, "id": "SPEED_POTION", "occupied": True}],
        },
    }
    assert ai.choose_potion_action(silent_chip_speed_potion_state, {"use_potion"}) is None

    crisis_explosive_state = {
        **high_hp_explosive_state,
        "combat": {
            **high_hp_explosive_state["combat"],
            "enemies": [{"index": 0, "id": "TEST_ENEMY", "hp": 45, "block": 0, "intent": "Attack 22"}],
        },
    }
    potion_action = ai.choose_potion_action(crisis_explosive_state, {"use_potion"})
    assert potion_action is not None and potion_action[0] == "use_potion"

    rest_state = {
        "screen": "REST",
        "available_actions": ["choose_rest_option"],
        "run": {
            "character_id": "REGENT",
            "floor": 14,
            "current_hp": 47,
            "max_hp": 78,
            "deck": [
                {"id": "STRIKE_REGENT", "name": "Strike", "type": "Attack", "rarity": "Basic", "cost": 1},
                {"id": "DEFEND_REGENT", "name": "Defend", "type": "Skill", "rarity": "Basic", "cost": 1},
                {"id": "FALLING_STAR", "name": "Falling Star", "type": "Attack", "rarity": "Common", "cost": 1},
            ],
            "relics": [
                {"id": "DIVINE_RIGHT", "name": "Divine Right"},
                {"id": "CHOSEN_CHEESE", "name": "The Chosen Cheese"},
                {"id": "PRECISE_SCISSORS", "name": "Precise Scissors"},
            ],
        },
        "rest": {
            "options": [
                {"index": 0, "option_id": "HEAL", "title": "Rest"},
                {"index": 1, "option_id": "SMITH", "title": "Smith"},
            ]
        },
    }
    rest_idx, _ = ai.choose_rest_index(rest_state)
    assert rest_idx == 0

    silent_campfire_state = {
        "screen": "REST",
        "available_actions": ["choose_rest_option"],
        "run": {
            "character_id": "SILENT",
            "floor": 9,
            "current_hp": 51,
            "max_hp": 70,
            "deck": (
                [{"id": "STRIKE_SILENT", "name": "Strike", "type": "Attack", "rarity": "Basic", "cost": 1} for _ in range(5)]
                + [{"id": "DEFEND_SILENT", "name": "Defend", "type": "Skill", "rarity": "Basic", "cost": 1} for _ in range(5)]
                + [
                    {"id": "NEUTRALIZE", "name": "Neutralize", "type": "Attack", "rarity": "Basic", "cost": 0, "damage": 3},
                    {"id": "SURVIVOR", "name": "Survivor", "type": "Skill", "rarity": "Basic", "cost": 1, "block": 8},
                    {"id": "DAGGER_THROW", "name": "Dagger Throw", "type": "Attack", "rarity": "Common", "cost": 1, "damage": 9},
                    {"id": "CLOAK_AND_DAGGER", "name": "Cloak and Dagger", "type": "Skill", "rarity": "Common", "cost": 1, "block": 6},
                ]
            ),
            "relics": [
                {"id": "RING_OF_THE_SNAKE", "name": "Ring of the Snake"},
                {"id": "HAPPY_FLOWER", "name": "Happy Flower"},
            ],
        },
        "rest": {
            "options": [
                {"index": 0, "option_id": "HEAL", "title": "Rest"},
                {"index": 1, "option_id": "SMITH", "title": "Smith"},
            ]
        },
    }
    smith_idx, smith_target = ai.choose_rest_index(silent_campfire_state)
    assert smith_idx == 1
    assert smith_target is not None

    low_hp_campfire_state = {
        **silent_campfire_state,
        "run": {
            **silent_campfire_state["run"],
            "current_hp": 36,
        },
    }
    low_hp_rest_idx, _ = ai.choose_rest_index(low_hp_campfire_state)
    assert low_hp_rest_idx == 0

    whisper_state = {
        "screen": "EVENT",
        "available_actions": ["choose_event_option"],
        "event": {
            "id": "WHISPERING_HOLLOW",
            "options": [
                {
                    "index": 0,
                    "text_key": "WHISPERING_HOLLOW.pages.INITIAL.options.GOLD",
                    "text": "交换金币",
                },
                {
                    "index": 1,
                    "text_key": "WHISPERING_HOLLOW.pages.INITIAL.options.HUG",
                    "text": "拥抱树木",
                },
            ],
        },
        "run": {
            "character_id": "SILENT",
            "floor": 9,
            "current_hp": 8,
            "max_hp": 77,
            "gold": 259,
            "deck": [
                {"id": "STRIKE_SILENT", "name": "Strike", "type": "Attack", "rarity": "Basic", "cost": 1},
                {"id": "DEFEND_SILENT", "name": "Defend", "type": "Skill", "rarity": "Basic", "cost": 1},
                {"id": "POOR_SLEEP", "name": "Poor Sleep", "type": "Curse", "rarity": "Curse", "cost": 0},
            ],
            "relics": [
                {"id": "RING_OF_THE_SNAKE", "name": "Ring of the Snake"},
                {"id": "NUNCHAKU", "name": "Nunchaku"},
            ],
        },
    }
    assert ai.event_option_hp_loss(ai.event_option_blob(whisper_state["event"]["options"][1], whisper_state)) == 9
    assert ai.choose_event_index(whisper_state) == 0

    dense_vegetation_risky_state = {
        "screen": "EVENT",
        "available_actions": ["choose_event_option"],
        "event": {
            "id": "DENSE_VEGETATION",
            "options": [
                {
                    "index": 0,
                    "id": "TRUDGE_ON",
                    "text_key": "DENSE_VEGETATION.pages.INITIAL.options.TRUDGE_ON",
                    "title": "Trudge On",
                },
                {
                    "index": 1,
                    "id": "REST",
                    "text_key": "DENSE_VEGETATION.pages.INITIAL.options.REST",
                    "title": "Rest",
                },
            ],
        },
        "run": {
            "character_id": "IRONCLAD",
            "floor": 7,
            "current_hp": 67,
            "max_hp": 80,
            "gold": 83,
            "deck": [
                *[
                    {"id": "STRIKE_IRONCLAD", "name": "Strike", "type": "Attack", "rarity": "Basic", "cost": 1}
                    for _ in range(4)
                ],
                *[
                    {"id": "DEFEND_IRONCLAD", "name": "Defend", "type": "Skill", "rarity": "Basic", "cost": 1}
                    for _ in range(4)
                ],
                {"id": "BASH", "name": "Bash", "type": "Attack", "rarity": "Basic", "cost": 2},
                {"id": "SHRUG_IT_OFF", "name": "Shrug It Off", "type": "Skill", "rarity": "Common", "cost": 1},
                {"id": "BODY_SLAM", "name": "Body Slam", "type": "Attack", "rarity": "Common", "cost": 1},
                {"id": "COLOSSUS", "name": "Colossus", "type": "Skill", "rarity": "Uncommon", "cost": 1},
                {"id": "HOWL_FROM_BEYOND", "name": "Howl from Beyond", "type": "Attack", "rarity": "Uncommon", "cost": 3},
                {"id": "FEED", "name": "Feed", "type": "Attack", "rarity": "Rare", "cost": 1},
                {"id": "THUNDERCLAP", "name": "Thunderclap", "type": "Attack", "rarity": "Common", "cost": 1},
            ],
            "relics": [
                {"id": "BURNING_BLOOD", "name": "Burning Blood"},
                {"id": "GOLDEN_PEARL", "name": "Golden Pearl"},
            ],
        },
    }
    assert ai.event_option_hp_loss(
        ai.event_option_blob(dense_vegetation_risky_state["event"]["options"][0], dense_vegetation_risky_state)
    ) == 11
    assert ai.choose_event_index(dense_vegetation_risky_state) == 1

    map_potion_state = {
        "screen": "MAP",
        "available_actions": ["discard_potion"],
        "run": {
            "potions": [{"index": 0, "potion_id": "DUPLICATOR", "occupied": True}],
            "deck": [],
            "relics": [{"id": "RING_OF_THE_SNAKE", "name": "Ring of the Snake"}],
        },
    }
    assert ai.choose_discard_potion_action(map_potion_state, {"discard_potion"}) is None
    assert ai.choose_potion_only_window_action(map_potion_state, {"discard_potion"}) is None

    def map_node(index: int, row: int, col: int, node_type: str, *children: tuple[int, int]) -> dict:
        return {
            "index": index,
            "row": row,
            "col": col,
            "node_type": node_type,
            "state": "Travelable",
            "children": [{"row": child_row, "col": child_col} for child_row, child_col in children],
        }

    late_elite_nodes = [
        map_node(0, 3, 3, "Monster", (4, 3)),
        map_node(1, 3, 5, "Unknown", (4, 5)),
        map_node(2, 4, 3, "Shop", (5, 3)),
        map_node(3, 5, 3, "Unknown", (6, 4)),
        map_node(4, 6, 4, "Unknown", (7, 4)),
        map_node(5, 7, 4, "Monster", (8, 3)),
        map_node(6, 8, 3, "Treasure", (9, 2)),
        map_node(7, 9, 2, "Elite"),
        map_node(8, 4, 5, "Unknown", (5, 5)),
        map_node(9, 5, 5, "Unknown", (6, 5)),
        map_node(10, 6, 5, "RestSite", (7, 5)),
        map_node(11, 7, 5, "Monster"),
    ]
    late_elite_state = {
        "screen": "MAP",
        "available_actions": ["choose_map_node"],
        "run": {
            "character_id": "REGENT",
            "floor": 20,
            "current_hp": 59,
            "max_hp": 80,
            "gold": 353,
            "potions": [
                {"index": 0, "occupied": False},
                {"index": 1, "occupied": False},
                {"index": 2, "occupied": False},
            ],
            "deck": [
                *[
                    {"id": "STRIKE_REGENT", "name": "Strike", "type": "Attack", "rarity": "Basic", "cost": 1}
                    for _ in range(3)
                ],
                *[
                    {"id": "DEFEND_REGENT", "name": "Defend", "type": "Skill", "rarity": "Basic", "cost": 1}
                    for _ in range(4)
                ],
                {"id": "FALLING_STAR", "name": "Falling Star", "type": "Attack", "rarity": "Basic", "cost": 0},
                {"id": "VENERATE", "name": "Venerate", "type": "Skill", "rarity": "Basic", "cost": 1},
                {"id": "REFLECT", "name": "Reflect", "type": "Skill", "rarity": "Uncommon", "cost": 1},
                {"id": "GLOW", "name": "Glow", "type": "Skill", "rarity": "Common", "cost": 1},
                {"id": "SHINING_STRIKE", "name": "Shining Strike", "type": "Attack", "rarity": "Uncommon", "cost": 1},
                {"id": "GAMMA_BLAST", "name": "Gamma Blast", "type": "Attack", "rarity": "Uncommon", "cost": 0},
                {"id": "KNOCKOUT_BLOW", "name": "Knockout Blow", "type": "Attack", "rarity": "Uncommon", "cost": 3},
                {"id": "GUIDING_STAR", "name": "Guiding Star", "type": "Attack", "rarity": "Common", "cost": 1},
            ],
            "relics": [{"id": "DIVINE_RIGHT"}, {"id": "NUNCHAKU"}],
        },
        "map": {"options": [late_elite_nodes[0], late_elite_nodes[1]], "nodes": late_elite_nodes},
    }
    assert ai.late_elite_route_penalty(late_elite_nodes[7], late_elite_state) > 0
    assert ai.map_risk_score(late_elite_nodes[0], late_elite_state) < ai.map_risk_score(
        late_elite_nodes[1], late_elite_state
    )
    assert ai.choose_map_index(late_elite_state) == 1

    early_unsafe_elite_state = {
        "screen": "MAP",
        "available_actions": ["choose_map_node"],
        "run": {
            "character_id": "SILENT",
            "floor": 6,
            "current_hp": 37,
            "max_hp": 70,
            "gold": 116,
            "potions": [
                {"index": 0, "occupied": False},
                {"index": 1, "occupied": False},
                {"index": 2, "occupied": False},
            ],
            "deck": [
                *[
                    {"id": "STRIKE_SILENT", "name": "Strike", "type": "Attack", "rarity": "Basic", "cost": 1}
                    for _ in range(5)
                ],
                *[
                    {"id": "DEFEND_SILENT", "name": "Defend", "type": "Skill", "rarity": "Basic", "cost": 1}
                    for _ in range(5)
                ],
                {"id": "NEUTRALIZE", "name": "Neutralize", "type": "Attack", "rarity": "Basic", "cost": 0},
                {"id": "SURVIVOR", "name": "Survivor", "type": "Skill", "rarity": "Basic", "cost": 1},
                {"id": "DAGGER_THROW", "name": "Dagger Throw", "type": "Attack", "rarity": "Common", "cost": 1},
                {"id": "PREDATOR", "name": "Predator", "type": "Attack", "rarity": "Uncommon", "cost": 2},
                {"id": "BACKFLIP", "name": "Backflip", "type": "Skill", "rarity": "Common", "cost": 1},
            ],
            "relics": [
                {"id": "RING_OF_THE_SNAKE", "name": "Ring of the Snake"},
                {"id": "PRECARIOUS_SHEARS", "name": "Precarious Shears"},
                {"id": "BAG_OF_MARBLES", "name": "Bag of Marbles"},
                {"id": "SHURIKEN", "name": "Shuriken"},
            ],
        },
        "map": {
            "options": [
                map_node(0, 6, 4, "Elite"),
                map_node(1, 6, 5, "Shop"),
            ],
            "nodes": [
                map_node(0, 6, 4, "Elite"),
                map_node(1, 6, 5, "Shop"),
            ],
        },
    }
    assert ai.early_elite_route_penalty(early_unsafe_elite_state["map"]["options"][0], early_unsafe_elite_state) > 0
    assert ai.choose_map_index(early_unsafe_elite_state) == 1

    early_removal_shop_state = {
        "screen": "MAP",
        "available_actions": ["choose_map_node"],
        "run": {
            "character_id": "SILENT",
            "floor": 2,
            "current_hp": 67,
            "max_hp": 70,
            "gold": 116,
            "deck": [
                *[
                    {"id": "STRIKE_SILENT", "name": "Strike", "type": "Attack", "rarity": "Basic", "cost": 1}
                    for _ in range(5)
                ],
                *[
                    {"id": "DEFEND_SILENT", "name": "Defend", "type": "Skill", "rarity": "Basic", "cost": 1}
                    for _ in range(5)
                ],
                {"id": "NEUTRALIZE", "name": "Neutralize", "type": "Attack", "rarity": "Basic", "cost": 0},
                {"id": "SURVIVOR", "name": "Survivor", "type": "Skill", "rarity": "Basic", "cost": 1},
                {"id": "DODGE_AND_ROLL", "name": "Dodge and Roll", "type": "Skill", "rarity": "Common", "cost": 1},
                {"id": "SPOILS_MAP", "name": "Spoils Map", "type": "Quest", "rarity": "Quest", "cost": -1},
            ],
            "relics": [{"id": "RING_OF_THE_SNAKE", "name": "Ring of the Snake"}],
        },
        "map": {
            "options": [
                map_node(0, 2, 5, "Unknown"),
                map_node(1, 2, 6, "Shop"),
            ],
            "nodes": [
                map_node(0, 2, 5, "Unknown"),
                map_node(1, 2, 6, "Shop"),
            ],
        },
    }
    assert ai.choose_map_index(early_removal_shop_state) == 1

    thick_reward_state = {
        "screen": "REWARD",
        "available_actions": ["claim_reward", "resolve_rewards"],
        "run": {
            "character_id": "SILENT",
            "current_hp": 60,
            "max_hp": 70,
            "gold": 110,
            "deck": [
                *[
                    {"id": "STRIKE_SILENT", "name": "Strike", "type": "Attack", "rarity": "Basic", "cost": 1}
                    for _ in range(5)
                ],
                *[
                    {"id": "DEFEND_SILENT", "name": "Defend", "type": "Skill", "rarity": "Basic", "cost": 1}
                    for _ in range(5)
                ],
                {"id": "NEUTRALIZE", "name": "Neutralize", "type": "Attack", "rarity": "Basic", "cost": 0},
                {"id": "SURVIVOR", "name": "Survivor", "type": "Skill", "rarity": "Basic", "cost": 1},
                {"id": "POISONED_STAB", "name": "Poisoned Stab", "type": "Attack", "rarity": "Common", "cost": 1},
                {"id": "BACKFLIP", "name": "Backflip", "type": "Skill", "rarity": "Common", "cost": 1},
                {"id": "PREPARED", "name": "Prepared", "type": "Skill", "rarity": "Common", "cost": 0},
                {"id": "PREPARED", "name": "Prepared", "type": "Skill", "rarity": "Common", "cost": 0},
                {"id": "SUCKER_PUNCH", "name": "Sucker Punch", "type": "Attack", "rarity": "Common", "cost": 1},
                {"id": "RICOCHET", "name": "Ricochet", "type": "Attack", "rarity": "Common", "cost": 2},
                {"id": "CLOAK_AND_DAGGER", "name": "Cloak and Dagger", "type": "Skill", "rarity": "Common", "cost": 1},
                {"id": "FOOTWORK", "name": "Footwork", "type": "Power", "rarity": "Uncommon", "cost": 1},
                {"id": "MIRAGE", "name": "Mirage", "type": "Skill", "rarity": "Uncommon", "cost": 1},
                {"id": "CLOAK_AND_DAGGER", "name": "Cloak and Dagger", "type": "Skill", "rarity": "Common", "cost": 1},
            ],
            "relics": [
                {"id": "RING_OF_THE_SNAKE", "name": "Ring of the Snake"},
                {"id": "VAJRA", "name": "Vajra"},
            ],
        },
        "reward": {
            "rewards": [
                {"index": 0, "reward_type": "Gold", "description": "18 Gold"},
                {"index": 1, "reward_type": "Card", "description": "Add a card to your deck."},
            ]
        },
    }
    assert ai.claim_card_reward_score(thick_reward_state)[0] < 18
    assert ai.choose_claim_reward_index(thick_reward_state) == 0

    defect_needs_draw_state = {
        "screen": "CARD_SELECTION",
        "available_actions": ["select_deck_card"],
        "run": {
            "character_id": "DEFECT",
            "current_hp": 69,
            "max_hp": 75,
            "deck": [
                *[
                    {"id": "STRIKE_DEFECT", "name": "Strike", "type": "Attack", "rarity": "Basic", "cost": 1}
                    for _ in range(4)
                ],
                *[
                    {"id": "DEFEND_DEFECT", "name": "Defend", "type": "Skill", "rarity": "Basic", "cost": 1}
                    for _ in range(4)
                ],
                {"id": "ZAP", "name": "Zap", "type": "Skill", "rarity": "Basic", "cost": 1},
                {"id": "DUALCAST", "name": "Dualcast", "type": "Skill", "rarity": "Basic", "cost": 1},
                {"id": "LIGHTNING_ROD", "name": "Lightning Rod", "type": "Skill", "rarity": "Common", "cost": 1},
                {"id": "STORM", "name": "Storm", "type": "Power", "rarity": "Uncommon", "cost": 1},
            ],
            "relics": [{"id": "CRACKED_CORE", "name": "Cracked Core"}],
        },
    }
    sweeping_beam = {
        "id": "SWEEPING_BEAM",
        "name": "Sweeping Beam",
        "type": "Attack",
        "rarity": "Common",
        "cost": 1,
        "damage": 6,
        "cards_draw": 1,
        "description": "Deal 6 damage to ALL enemies. Draw 1 card.",
    }
    capacitor = {
        "id": "CAPACITOR",
        "name": "Capacitor",
        "type": "Power",
        "rarity": "Uncommon",
        "cost": 1,
        "description": "Gain 2 Orb Slots.",
    }
    sweep_score = ai.score_reward_card(sweeping_beam, defect_needs_draw_state)
    capacitor_score = ai.score_reward_card(capacitor, defect_needs_draw_state)
    assert sweep_score > capacitor_score, (sweep_score, capacitor_score, capacitor.get("_knowledge_reasons"))
    assert any("slow-engine-density" in reason for reason in capacitor.get("_knowledge_reasons", []))

    reward_selection_state = {
        "screen": "CARD_SELECTION",
        "available_actions": ["select_deck_card"],
        "selection": {
            "prompt": "Choose a card to add to your deck. The unpicked cards are discarded.",
            "cards": [
                {
                    "index": 0,
                    "id": "ANGER",
                    "name": "Anger",
                    "type": "Attack",
                    "rarity": "Common",
                    "cost": 0,
                    "damage": 6,
                    "description": "Deal 6 damage. Add a copy of this card to your discard pile.",
                },
                {
                    "index": 1,
                    "id": "SHRUG_IT_OFF",
                    "name": "Shrug It Off",
                    "type": "Skill",
                    "rarity": "Common",
                    "cost": 1,
                    "block": 8,
                    "description": "Gain 8 Block. Draw 1 card.",
                },
                {
                    "index": 2,
                    "id": "WOUND",
                    "name": "Wound",
                    "type": "Status",
                    "rarity": "Status",
                    "cost": -1,
                    "description": "Unplayable. Discard this card.",
                },
            ],
        },
        "run": {
            "character_id": "IRONCLAD",
            "current_hp": 72,
            "max_hp": 80,
            "deck": [
                {"id": "STRIKE_IRONCLAD", "name": "Strike", "type": "Attack", "rarity": "Basic", "cost": 1},
                {"id": "DEFEND_IRONCLAD", "name": "Defend", "type": "Skill", "rarity": "Basic", "cost": 1},
                {"id": "BASH", "name": "Bash", "type": "Attack", "rarity": "Basic", "cost": 2},
            ],
            "relics": [{"id": "BURNING_BLOOD", "name": "Burning Blood"}],
        },
    }
    assert "discarded" in ai.selection_context_blob(reward_selection_state["selection"], {})
    assert ai.choose_deck_selection_index(reward_selection_state) == 1

    discard_selection_state = {
        **reward_selection_state,
        "selection": {
            "cards": [
                {"index": 0, "id": "STRIKE_IRONCLAD", "name": "Strike", "type": "Attack", "rarity": "Basic", "cost": 1},
                {"index": 1, "id": "DEFEND_IRONCLAD", "name": "Defend", "type": "Skill", "rarity": "Basic", "cost": 1},
                {"index": 2, "id": "WOUND", "name": "Wound", "type": "Status", "rarity": "Status", "cost": -1},
            ],
            "prompt": "Choose a card to discard.",
        },
        "run": {
            **reward_selection_state["run"],
            "deck": [
                {"id": "STRIKE_IRONCLAD", "name": "Strike", "type": "Attack", "rarity": "Basic", "cost": 1},
                {"id": "DEFEND_IRONCLAD", "name": "Defend", "type": "Skill", "rarity": "Basic", "cost": 1},
                {"id": "WOUND", "name": "Wound", "type": "Status", "rarity": "Status", "cost": -1},
            ],
        },
    }
    assert ai.choose_deck_selection_index(discard_selection_state) == 2

    silent_low_block_discard_state = {
        "screen": "CARD_SELECTION",
        "available_actions": ["select_deck_card"],
        "selection": {
            "cards": [
                {
                    "index": 0,
                    "id": "SURVIVOR",
                    "name": "Survivor",
                    "type": "Skill",
                    "rarity": "Basic",
                    "cost": 1,
                    "block": 8,
                    "description": "Gain 8 Block. Discard 1 card.",
                    "playable": True,
                    "requires_target": False,
                },
                {
                    "index": 1,
                    "id": "DEFEND_SILENT",
                    "name": "Defend",
                    "type": "Skill",
                    "rarity": "Basic",
                    "cost": 1,
                    "block": 5,
                    "playable": True,
                    "requires_target": False,
                },
                {
                    "index": 2,
                    "id": "STRIKE_SILENT",
                    "name": "Strike",
                    "type": "Attack",
                    "rarity": "Basic",
                    "cost": 1,
                    "damage": 6,
                    "playable": True,
                    "requires_target": True,
                },
            ],
            "prompt": "Choose a card to discard.",
        },
        "combat": {
            "energy": 1,
            "player": {"block": 0},
            "hand": [],
            "enemies": [{"index": 0, "id": "TEST_ENEMY", "hp": 60, "intent": "Attack 11"}],
        },
        "run": {
            "character_id": "SILENT",
            "current_hp": 34,
            "max_hp": 70,
            "deck": [],
            "relics": [{"id": "RING_OF_THE_SNAKE", "name": "Ring of the Snake"}],
        },
    }
    assert ai.choose_deck_selection_index(silent_low_block_discard_state) == 1

    silent_no_pressure_discard_state = {
        **silent_low_block_discard_state,
        "selection": {
            **silent_low_block_discard_state["selection"],
            "cards": [
                silent_low_block_discard_state["selection"]["cards"][1],
                silent_low_block_discard_state["selection"]["cards"][2],
            ],
        },
        "combat": {
            **silent_low_block_discard_state["combat"],
            "enemies": [{"index": 0, "id": "TEST_ENEMY", "hp": 60, "intent": "Attack 0"}],
        },
    }
    assert ai.choose_deck_selection_index(silent_no_pressure_discard_state) == 1

    critical_survival_discard_state = {
        **silent_low_block_discard_state,
        "selection": {
            **silent_low_block_discard_state["selection"],
            "cards": [
                {
                    "index": 0,
                    "id": "DEFEND_SILENT",
                    "name": "Defend",
                    "type": "Skill",
                    "rarity": "Basic",
                    "cost": 1,
                    "block": 5,
                    "playable": True,
                    "requires_target": False,
                },
                {
                    "index": 1,
                    "id": "SHADOWMELD",
                    "name": "Shadowmeld",
                    "type": "Skill",
                    "rarity": "Common",
                    "cost": 1,
                    "block": 3,
                    "playable": True,
                    "requires_target": False,
                },
                {
                    "index": 2,
                    "id": "SURVIVOR",
                    "name": "Survivor",
                    "type": "Skill",
                    "rarity": "Basic",
                    "cost": 1,
                    "block": 8,
                    "description": "Gain 8 Block. Discard 1 card.",
                    "playable": True,
                    "requires_target": False,
                },
                {
                    "index": 3,
                    "id": "SUCKER_PUNCH",
                    "name": "Sucker Punch",
                    "type": "Attack",
                    "rarity": "Common",
                    "cost": 1,
                    "damage": 8,
                    "playable": True,
                    "requires_target": True,
                },
                {
                    "index": 4,
                    "id": "PREDATOR",
                    "name": "Predator",
                    "type": "Attack",
                    "rarity": "Uncommon",
                    "cost": 2,
                    "damage": 15,
                    "playable": True,
                    "requires_target": True,
                },
                {
                    "index": 5,
                    "id": "PIERCING_WAIL",
                    "name": "Piercing Wail+",
                    "type": "Skill",
                    "rarity": "Common",
                    "cost": 1,
                    "description": "ALL enemies lose 8 Strength this turn. Exhaust.",
                    "playable": True,
                    "requires_target": False,
                },
            ],
        },
        "combat": {
            "energy": 3,
            "player": {"block": 0},
            "hand": [],
            "enemies": [
                {
                    "index": 0,
                    "id": "MAWLER",
                    "hp": 37,
                    "intent": "RIP_AND_TEAR_MOVE",
                }
            ],
        },
        "run": {
            "character_id": "SILENT",
            "current_hp": 3,
            "max_hp": 70,
            "deck": [],
            "relics": [{"id": "RING_OF_THE_SNAKE", "name": "Ring of the Snake"}],
        },
    }
    assert ai.enemy_pressure_damage(critical_survival_discard_state["combat"]["enemies"][0]) >= 18
    assert ai.discard_selection_score(
        critical_survival_discard_state["selection"]["cards"][4],
        critical_survival_discard_state,
    ) > ai.discard_selection_score(
        critical_survival_discard_state["selection"]["cards"][0],
        critical_survival_discard_state,
    )
    assert ai.discard_selection_score(
        critical_survival_discard_state["selection"]["cards"][4],
        critical_survival_discard_state,
    ) > ai.discard_selection_score(
        critical_survival_discard_state["selection"]["cards"][5],
        critical_survival_discard_state,
    )
    assert ai.choose_deck_selection_index(critical_survival_discard_state) == 4

    waterfall_ram_enemy = {"index": 0, "id": "WATERFALL_GIANT", "hp": 74, "intent": "RAM_MOVE"}
    waterfall_pressure_enemy = {"index": 0, "id": "WATERFALL_GIANT", "hp": 73, "intent": "PRESSURE_GUN_MOVE"}
    assert ai.enemy_pressure_damage(waterfall_ram_enemy) >= 10
    assert ai.enemy_pressure_damage(waterfall_pressure_enemy) >= 25

    ram_keep_free_weak_state = {
        "screen": "CARD_SELECTION",
        "available_actions": ["select_deck_card"],
        "selection": {
            "prompt": "Choose a card to discard.",
            "cards": [
                {
                    "index": 0,
                    "id": "DEFEND_SILENT",
                    "name": "Defend",
                    "type": "Skill",
                    "rarity": "Basic",
                    "cost": 1,
                    "block": 5,
                    "playable": True,
                    "requires_target": False,
                },
                {
                    "index": 1,
                    "id": "NEUTRALIZE",
                    "name": "Neutralize",
                    "type": "Attack",
                    "rarity": "Basic",
                    "cost": 0,
                    "playable": True,
                    "requires_target": True,
                },
            ],
        },
        "combat": {
            "energy": 1,
            "player": {"block": 8},
            "hand": [],
            "enemies": [waterfall_ram_enemy],
        },
        "run": {
            "character_id": "SILENT",
            "current_hp": 8,
            "max_hp": 70,
            "deck": [],
            "relics": [{"id": "RING_OF_THE_SNAKE", "name": "Ring of the Snake"}],
        },
    }
    assert ai.discard_selection_score(
        ram_keep_free_weak_state["selection"]["cards"][0],
        ram_keep_free_weak_state,
    ) > ai.discard_selection_score(
        ram_keep_free_weak_state["selection"]["cards"][1],
        ram_keep_free_weak_state,
    )
    assert ai.choose_deck_selection_index(ram_keep_free_weak_state) == 0

    readonly_pile_selection_state = {
        "screen": "CARD_SELECTION",
        "in_combat": True,
        "available_actions": ["select_deck_card", "discard_potion"],
        "selection": {},
        "agent_view": {
            "selection": {
                "kind": "deck_card_select",
                "prompt": "When the draw pile is empty, these cards will be shuffled into the draw pile.",
                "min": 0,
                "max": 0,
                "selected": 0,
                "confirm": False,
                "cards": [
                    {"i": 0, "line": "Strike [1]: Deal 6 damage."},
                    {"i": 1, "line": "Defend [1]: Gain 5 Block."},
                ],
            }
        },
        "combat": {
            "hand": [],
            "enemies": [{"index": 0, "id": "TEST_ENEMY", "hp": 30, "intent": "Attack 6"}],
        },
        "run": {"character_id": "SILENT", "current_hp": 42, "max_hp": 70, "deck": []},
    }
    assert ai.readonly_card_selection_reason(readonly_pile_selection_state) == "read-only card pile view"

    real_optional_selection_state = {
        **readonly_pile_selection_state,
        "available_actions": ["select_deck_card", "confirm_selection"],
        "agent_view": {
            "selection": {
                **readonly_pile_selection_state["agent_view"]["selection"],
                "prompt": "Choose cards to discard.",
                "max": 1,
            }
        },
    }
    assert ai.readonly_card_selection_reason(real_optional_selection_state) is None

    silent_discard_resource_state = {
        **silent_low_block_discard_state,
        "selection": {
            **silent_low_block_discard_state["selection"],
            "cards": [
                {
                    "index": 0,
                    "id": "REFLEX",
                    "name": "Reflex",
                    "type": "Skill",
                    "rarity": "Uncommon",
                    "cost": -1,
                    "playable": False,
                    "requires_target": False,
                },
                silent_low_block_discard_state["selection"]["cards"][1],
                silent_low_block_discard_state["selection"]["cards"][2],
            ],
        },
    }
    assert ai.choose_deck_selection_index(silent_discard_resource_state) == 0

    removal_preserve_shop_state = {
        "screen": "SHOP",
        "available_actions": ["buy_card", "remove_card_at_shop", "close_shop_inventory"],
        "run": {
            "character_id": "NECROBINDER",
            "current_hp": 65,
            "max_hp": 66,
            "gold": 148,
            "deck": [
                {"id": "STRIKE_NECROBINDER", "name": "Strike", "type": "Attack", "rarity": "Basic", "cost": 1},
                {"id": "STRIKE_NECROBINDER", "name": "Strike", "type": "Attack", "rarity": "Basic", "cost": 1},
                {"id": "DEFEND_NECROBINDER", "name": "Defend", "type": "Skill", "rarity": "Basic", "cost": 1},
                {"id": "DEFEND_NECROBINDER", "name": "Defend", "type": "Skill", "rarity": "Basic", "cost": 1},
                {"id": "DEFEND_NECROBINDER", "name": "Defend", "type": "Skill", "rarity": "Basic", "cost": 1},
                {"id": "DEFEND_NECROBINDER", "name": "Defend", "type": "Skill", "rarity": "Basic", "cost": 1},
                {"id": "BODYGUARD", "name": "Bodyguard", "type": "Skill", "rarity": "Basic", "cost": 1},
                {"id": "UNLEASH", "name": "Unleash", "type": "Attack", "rarity": "Basic", "cost": 1},
                {"id": "SPOILS_MAP", "name": "Spoils Map", "type": "Quest", "rarity": "Quest", "cost": -1},
            ],
            "relics": [{"id": "BOUND_PHYLACTERY", "name": "Bound Phylactery"}],
        },
        "shop": {
            "remove_cost": 75,
            "cards": [
                {
                    "index": 4,
                    "price": 76,
                    "card": {
                        "id": "DANSE_MACABRE",
                        "name": "Danse Macabre",
                        "type": "Power",
                        "rarity": "Uncommon",
                        "cost": 1,
                    },
                }
            ],
        },
    }
    shop_action, _, _ = ai.choose_shop_action(removal_preserve_shop_state)
    assert shop_action == "remove_card_at_shop"

    silent_boss_prep_remove_over_fire_potion_state = {
        "screen": "SHOP",
        "available_actions": ["buy_potion", "remove_card_at_shop", "close_shop_inventory"],
        "run": {
            "character_id": "SILENT",
            "floor": 14,
            "current_hp": 54,
            "max_hp": 75,
            "gold": 118,
            "deck": [
                {"id": "STRIKE_SILENT", "name": "Strike", "type": "Attack", "rarity": "Basic", "cost": 1},
                {"id": "STRIKE_SILENT", "name": "Strike", "type": "Attack", "rarity": "Basic", "cost": 1},
                {"id": "STRIKE_SILENT", "name": "Strike", "type": "Attack", "rarity": "Basic", "cost": 1},
                {"id": "STRIKE_SILENT", "name": "Strike", "type": "Attack", "rarity": "Basic", "cost": 1},
                {"id": "STRIKE_SILENT", "name": "Strike", "type": "Attack", "rarity": "Basic", "cost": 1},
                {"id": "DEFEND_SILENT", "name": "Defend", "type": "Skill", "rarity": "Basic", "cost": 1},
                {"id": "DEFEND_SILENT", "name": "Defend", "type": "Skill", "rarity": "Basic", "cost": 1},
                {"id": "DEFEND_SILENT", "name": "Defend", "type": "Skill", "rarity": "Basic", "cost": 1},
                {"id": "DEFEND_SILENT", "name": "Defend", "type": "Skill", "rarity": "Basic", "cost": 1},
                {"id": "DEFEND_SILENT", "name": "Defend", "type": "Skill", "rarity": "Basic", "cost": 1},
                {"id": "NEUTRALIZE", "name": "Neutralize", "type": "Attack", "rarity": "Basic", "cost": 0},
                {"id": "SURVIVOR", "name": "Survivor", "type": "Skill", "rarity": "Basic", "cost": 1},
                {"id": "ENVENOM", "name": "Envenom", "type": "Power", "rarity": "Rare", "cost": 2},
                {"id": "DAGGER_SPRAY", "name": "Dagger Spray", "type": "Attack", "rarity": "Common", "cost": 1, "damage": 4},
                {"id": "SKEWER", "name": "Skewer", "type": "Attack", "rarity": "Uncommon", "cost": -1, "damage": 7},
            ],
            "relics": [
                {"id": "RING_OF_THE_SNAKE", "name": "Ring of the Snake"},
                {"id": "LIZARD_TAIL", "name": "Lizard Tail"},
            ],
            "potions": [
                {"id": None, "name": None, "occupied": False},
                {"id": None, "name": None, "occupied": False},
                {"id": None, "name": None, "occupied": False},
            ],
        },
        "shop": {
            "remove_cost": 75,
            "items": [
                {
                    "index": 3,
                    "price": 48,
                    "potion": {"id": "FIRE_POTION", "name": "Fire Potion"},
                    "name": "Fire Potion",
                    "type": "Potion",
                }
            ],
        },
    }
    shop_action, _, reason = ai.choose_shop_action(silent_boss_prep_remove_over_fire_potion_state)
    assert shop_action == "remove_card_at_shop", reason

    silent_boss_dirty_shop_preserve_removal_state = {
        "screen": "SHOP",
        "available_actions": ["buy_card", "remove_card_at_shop", "close_shop_inventory"],
        "run": {
            "character_id": "SILENT",
            "floor": 13,
            "current_hp": 32,
            "max_hp": 70,
            "gold": 83,
            "deck": (
                [{"id": "STRIKE_SILENT", "name": "Strike", "type": "Attack", "rarity": "Basic", "cost": 1} for _ in range(5)]
                + [{"id": "DEFEND_SILENT", "name": "Defend", "type": "Skill", "rarity": "Basic", "cost": 1, "block": 5} for _ in range(4)]
                + [
                    {"id": "NEUTRALIZE", "name": "Neutralize+", "type": "Attack", "rarity": "Basic", "cost": 0, "upgraded": True},
                    {"id": "SURVIVOR", "name": "Survivor", "type": "Skill", "rarity": "Basic", "cost": 1, "block": 8},
                    {"id": "SUCKER_PUNCH", "name": "Sucker Punch", "type": "Attack", "rarity": "Common", "cost": 1, "damage": 8},
                    {"id": "FLECHETTES", "name": "Flechettes", "type": "Attack", "rarity": "Uncommon", "cost": 1, "damage": 5},
                    {"id": "SUCKER_PUNCH", "name": "Sucker Punch", "type": "Attack", "rarity": "Common", "cost": 1, "damage": 8},
                    {"id": "SPOILS_MAP", "name": "Spoils Map", "type": "Quest", "rarity": "Quest", "cost": -1},
                    {"id": "POISONED_STAB", "name": "Poisoned Stab", "type": "Attack", "rarity": "Common", "cost": 1, "damage": 6},
                    {"id": "SKEWER", "name": "Skewer", "type": "Attack", "rarity": "Uncommon", "cost": 0, "damage": 7},
                    {"id": "BLUR", "name": "Blur", "type": "Skill", "rarity": "Uncommon", "cost": 1, "block": 5},
                ]
            ),
            "relics": [
                {"id": "RING_OF_THE_SNAKE", "name": "Ring of the Snake"},
                {"id": "LOST_COFFER", "name": "Lost Coffer"},
                {"id": "SWORD_OF_STONE", "name": "Sword of Stone"},
                {"id": "CANDELABRA", "name": "Candelabra"},
            ],
            "potions": [
                {"id": "VULNERABLE_POTION", "name": "Vulnerable Potion", "occupied": True},
                {"id": "DROPLET_OF_PRECOGNITION", "name": "Droplet of Precognition", "occupied": True},
                {"id": "ATTACK_POTION", "name": "Attack Potion", "occupied": True},
            ],
        },
        "shop": {
            "remove_cost": 75,
            "items": [
                {
                    "index": 2,
                    "price": 26,
                    "card": {
                        "id": "DODGE_AND_ROLL",
                        "name": "Dodge and Roll",
                        "type": "Skill",
                        "rarity": "Common",
                        "cost": 1,
                        "block": 4,
                    },
                    "name": "Dodge and Roll",
                    "type": "Card",
                },
                {
                    "index": 1,
                    "price": 49,
                    "card": {
                        "id": "FLICK_FLACK",
                        "name": "Flick Flack",
                        "type": "Attack",
                        "rarity": "Common",
                        "cost": 1,
                        "damage": 6,
                    },
                    "name": "Flick Flack",
                    "type": "Card",
                },
            ],
        },
    }
    shop_action, _, reason = ai.choose_shop_action(silent_boss_dirty_shop_preserve_removal_state)
    assert shop_action == "remove_card_at_shop", reason

    silent_post_remove_cheap_block_shop_state = {
        "screen": "SHOP",
        "available_actions": ["buy_card", "close_shop_inventory"],
        "run": {
            "character_id": "SILENT",
            "floor": 3,
            "current_hp": 58,
            "max_hp": 70,
            "gold": 37,
            "deck": (
                [{"id": "STRIKE_SILENT", "name": "Strike", "type": "Attack", "rarity": "Basic", "cost": 1} for _ in range(5)]
                + [{"id": "DEFEND_SILENT", "name": "Defend", "type": "Skill", "rarity": "Basic", "cost": 1, "block": 5} for _ in range(3)]
                + [
                    {"id": "NEUTRALIZE", "name": "Neutralize", "type": "Attack", "rarity": "Basic", "cost": 0},
                    {"id": "SURVIVOR", "name": "Survivor", "type": "Skill", "rarity": "Basic", "cost": 1, "block": 8},
                    {"id": "EXPOSE", "name": "Expose", "type": "Skill", "rarity": "Uncommon", "cost": 0},
                    {"id": "MEMENTO_MORI", "name": "Memento Mori", "type": "Attack", "rarity": "Uncommon", "cost": 1, "damage": 9},
                ]
            ),
            "relics": [
                {"id": "RING_OF_THE_SNAKE", "name": "Ring of the Snake"},
                {"id": "NEW_LEAF", "name": "New Leaf"},
            ],
            "potions": [{"id": "POWER_POTION", "name": "Power Potion", "occupied": True}],
        },
        "shop": {
            "remove_cost": 75,
            "items": [
                {
                    "index": 3,
                    "price": 24,
                    "card": {
                        "id": "DODGE_AND_ROLL",
                        "name": "Dodge and Roll",
                        "type": "Skill",
                        "rarity": "Common",
                        "cost": 1,
                        "block": 4,
                    },
                    "name": "Dodge and Roll",
                    "type": "Card",
                }
            ],
        },
    }
    shop_action, kwargs, reason = ai.choose_shop_action(silent_post_remove_cheap_block_shop_state)
    assert shop_action == "buy_card", reason
    assert kwargs["option_index"] == 3

    silent_remove_low_block_state = {
        "screen": "CARD_SELECTION",
        "selection": {
            "type": "remove",
            "cards": [
                {"index": 0, "id": "STRIKE_SILENT", "name": "Strike", "type": "Attack", "rarity": "Basic", "cost": 1, "damage": 6},
                {"index": 1, "id": "DEFEND_SILENT", "name": "Defend", "type": "Skill", "rarity": "Basic", "cost": 1, "block": 5},
                {"index": 2, "id": "NEUTRALIZE", "name": "Neutralize", "type": "Attack", "rarity": "Basic", "cost": 0},
                {"index": 3, "id": "SURVIVOR", "name": "Survivor", "type": "Skill", "rarity": "Basic", "cost": 1, "block": 8},
            ],
        },
        "run": {
            "character_id": "SILENT",
            "floor": 7,
            "current_hp": 54,
            "max_hp": 70,
            "deck": (
                [{"id": "STRIKE_SILENT", "name": "Strike", "type": "Attack", "rarity": "Basic", "cost": 1, "damage": 6} for _ in range(3)]
                + [{"id": "DEFEND_SILENT", "name": "Defend", "type": "Skill", "rarity": "Basic", "cost": 1, "block": 5} for _ in range(5)]
                + [
                    {"id": "NEUTRALIZE", "name": "Neutralize", "type": "Attack", "rarity": "Basic", "cost": 0},
                    {"id": "SURVIVOR", "name": "Survivor", "type": "Skill", "rarity": "Basic", "cost": 1, "block": 8},
                    {"id": "DAGGER_THROW", "name": "Dagger Throw", "type": "Attack", "rarity": "Common", "cost": 1, "damage": 9},
                    {"id": "DASH", "name": "Dash", "type": "Attack", "rarity": "Uncommon", "cost": 2, "damage": 10, "block": 10},
                    {"id": "POISONED_STAB", "name": "Poisoned Stab", "type": "Attack", "rarity": "Common", "cost": 1, "damage": 6},
                    {"id": "BACKFLIP", "name": "Backflip", "type": "Skill", "rarity": "Common", "cost": 1, "block": 5, "description": "Gain 5 Block. Draw 2 cards."},
                ]
            ),
            "relics": [{"id": "RING_OF_THE_SNAKE", "name": "Ring of the Snake"}],
        },
    }
    assert ai.choose_deck_selection_index(silent_remove_low_block_state) == 1
    assert ai.remove_selection_score(
        silent_remove_low_block_state["selection"]["cards"][1],
        silent_remove_low_block_state,
    ) > ai.remove_selection_score(
        silent_remove_low_block_state["selection"]["cards"][0],
        silent_remove_low_block_state,
    )

    silent_alias_remove_state = {
        "screen": "CARD_SELECTION",
        "selection": {
            "context": "transform/remove a card",
            "cards": [
                {"index": 0, "id": "STRIKE_G", "name": "Strike", "type": "Attack", "rarity": "Basic", "cost": 1, "damage": 6},
                {"index": 1, "id": "DEFEND_G", "name": "Defend", "type": "Skill", "rarity": "Basic", "cost": 1, "block": 5},
            ],
        },
        "run": {
            "character_id": "SILENT",
            "floor": 1,
            "current_hp": 70,
            "max_hp": 70,
            "deck": (
                [{"id": "STRIKE_G", "name": "Strike", "type": "Attack", "rarity": "Basic", "cost": 1, "damage": 6} for _ in range(5)]
                + [{"id": "DEFEND_G", "name": "Defend", "type": "Skill", "rarity": "Basic", "cost": 1, "block": 5} for _ in range(5)]
                + [
                    {"id": "NEUTRALIZE", "name": "Neutralize", "type": "Attack", "rarity": "Basic", "cost": 0},
                    {"id": "SURVIVOR", "name": "Survivor", "type": "Skill", "rarity": "Basic", "cost": 1, "block": 8},
                ]
            ),
        },
    }
    assert ai.deck_plan(silent_alias_remove_state).character_id == "SILENT"
    assert ai.deck_plan(silent_alias_remove_state).ids["STRIKE_SILENT"] == 5
    assert ai.choose_deck_selection_index(silent_alias_remove_state) == 1
    assert ai.remove_selection_score(
        silent_alias_remove_state["selection"]["cards"][1],
        silent_alias_remove_state,
    ) > ai.remove_selection_score(
        silent_alias_remove_state["selection"]["cards"][0],
        silent_alias_remove_state,
    )

    silent_block_starved_remove_state = {
        **silent_remove_low_block_state,
        "run": {
            **silent_remove_low_block_state["run"],
            "floor": 8,
            "deck": (
                [{"id": "STRIKE_SILENT", "name": "Strike", "type": "Attack", "rarity": "Basic", "cost": 1, "damage": 6} for _ in range(5)]
                + [{"id": "DEFEND_SILENT", "name": "Defend", "type": "Skill", "rarity": "Basic", "cost": 1, "block": 5} for _ in range(2)]
                + [
                    {"id": "NEUTRALIZE", "name": "Neutralize", "type": "Attack", "rarity": "Basic", "cost": 0},
                    {"id": "SURVIVOR", "name": "Survivor", "type": "Skill", "rarity": "Basic", "cost": 1, "block": 8},
                    {"id": "DAGGER_THROW", "name": "Dagger Throw", "type": "Attack", "rarity": "Common", "cost": 1, "damage": 9},
                    {"id": "DAGGER_SPRAY", "name": "Dagger Spray", "type": "Attack", "rarity": "Common", "cost": 1, "damage": 4},
                    {"id": "POISONED_STAB", "name": "Poisoned Stab", "type": "Attack", "rarity": "Common", "cost": 1, "damage": 6},
                ]
            ),
        },
    }
    assert ai.deck_plan(silent_block_starved_remove_state).needs_block
    assert ai.choose_deck_selection_index(silent_block_starved_remove_state) == 0

    low_hp_survival_potion_shop_state = {
        "screen": "SHOP",
        "available_actions": ["buy_card", "buy_potion", "close_shop_inventory"],
        "run": {
            "character_id": "IRONCLAD",
            "current_hp": 27,
            "max_hp": 80,
            "gold": 110,
            "deck": [
                {"id": "STRIKE_IRONCLAD", "name": "Strike", "type": "Attack", "rarity": "Basic", "cost": 1},
                {"id": "DEFEND_IRONCLAD", "name": "Defend", "type": "Skill", "rarity": "Basic", "cost": 1},
                {"id": "BASH", "name": "Bash", "type": "Attack", "rarity": "Basic", "cost": 2},
            ],
            "relics": [{"id": "BURNING_BLOOD", "name": "Burning Blood"}],
            "potions": [
                {"id": None, "name": None, "occupied": False},
                {"id": None, "name": None, "occupied": False},
                {"id": None, "name": None, "occupied": False},
            ],
        },
        "shop": {
            "items": [
                {
                    "index": 0,
                    "price": 50,
                    "potion": {"id": "WEAK_POTION", "name": "Weak Potion"},
                    "name": "Weak Potion",
                    "type": "Potion",
                },
                {
                    "index": 1,
                    "price": 48,
                    "card": {"id": "BODY_SLAM", "name": "Body Slam", "type": "Attack", "rarity": "Common", "cost": 1},
                    "name": "Body Slam",
                    "type": "Card",
                },
            ],
        },
    }
    shop_action, kwargs, reason = ai.choose_shop_action(low_hp_survival_potion_shop_state)
    assert shop_action == "buy_potion", reason
    assert kwargs["option_index"] == 0

    high_hp_survival_potion_shop_state = {
        **low_hp_survival_potion_shop_state,
        "available_actions": ["buy_potion", "close_shop_inventory"],
        "run": {
            **low_hp_survival_potion_shop_state["run"],
            "current_hp": 75,
        },
        "shop": {
            "items": [
                low_hp_survival_potion_shop_state["shop"]["items"][0],
            ],
        },
    }
    shop_action, _, _ = ai.choose_shop_action(high_hp_survival_potion_shop_state)
    assert shop_action == "close_shop_inventory"

    critical_hp_generic_potion_shop_state = {
        "screen": "SHOP",
        "available_actions": ["buy_potion", "close_shop_inventory"],
        "run": {
            "character_id": "SILENT",
            "current_hp": 8,
            "max_hp": 70,
            "gold": 58,
            "deck": [
                {"id": "STRIKE_SILENT", "name": "Strike", "type": "Attack", "rarity": "Basic", "cost": 1},
                {"id": "DEFEND_SILENT", "name": "Defend", "type": "Skill", "rarity": "Basic", "cost": 1},
            ],
            "relics": [{"id": "RING_OF_THE_SNAKE", "name": "Ring of the Snake"}],
            "potions": [
                {"id": None, "name": None, "occupied": False},
                {"id": None, "name": None, "occupied": False},
                {"id": None, "name": None, "occupied": False},
            ],
        },
        "shop": {
            "items": [
                {
                    "index": 1,
                    "price": 52,
                    "potion": {"id": "ENERGY_POTION", "name": "Energy Potion"},
                    "name": "Energy Potion",
                    "type": "Potion",
                },
                {
                    "index": 2,
                    "price": 49,
                    "potion": {"id": "SKILL_POTION", "name": "Skill Potion"},
                    "name": "Skill Potion",
                    "type": "Potion",
                },
            ],
        },
    }
    shop_action, kwargs, reason = ai.choose_shop_action(critical_hp_generic_potion_shop_state)
    assert shop_action == "buy_potion", reason
    assert kwargs["option_index"] == 2

    high_hp_generic_potion_shop_state = {
        **critical_hp_generic_potion_shop_state,
        "run": {
            **critical_hp_generic_potion_shop_state["run"],
            "current_hp": 64,
        },
    }
    shop_action, _, _ = ai.choose_shop_action(high_hp_generic_potion_shop_state)
    assert shop_action == "close_shop_inventory"

    threshold_ordering_shop_state = {
        **low_hp_survival_potion_shop_state,
        "run": {
            **low_hp_survival_potion_shop_state["run"],
            "current_hp": 39,
        },
        "shop": {
            "items": [
                low_hp_survival_potion_shop_state["shop"]["items"][0],
                {
                    "index": 1,
                    "price": 48,
                    "card": {
                        "id": "THRESHOLD_TEST_CARD",
                        "name": "Threshold Test Card",
                        "type": "Attack",
                        "rarity": "Common",
                        "cost": 1,
                    },
                    "name": "Threshold Test Card",
                    "type": "Card",
                },
            ],
        },
    }
    original_score_reward_card = ai.score_reward_card
    try:
        ai.score_reward_card = (
            lambda card, state: 83.0
            if card.get("id") == "THRESHOLD_TEST_CARD"
            else original_score_reward_card(card, state)
        )
        shop_action, kwargs, reason = ai.choose_shop_action(threshold_ordering_shop_state)
        assert shop_action == "buy_potion", reason
        assert kwargs["option_index"] == 0

        ai.score_reward_card = (
            lambda card, state: 112.0
            if card.get("id") == "THRESHOLD_TEST_CARD"
            else original_score_reward_card(card, state)
        )
        shop_action, kwargs, reason = ai.choose_shop_action(threshold_ordering_shop_state)
        assert shop_action == "buy_card", reason
        assert kwargs["option_index"] == 1
    finally:
        ai.score_reward_card = original_score_reward_card

    orichalcum_state = {
        "screen": "COMBAT",
        "available_actions": ["play_card", "end_turn"],
        "combat": {
            "energy": 3,
            "player": {"block": 0},
            "hand": [
                {
                    "index": 0,
                    "id": "DEFEND_DEFECT",
                    "name": "Defend",
                    "type": "Skill",
                    "cost": 1,
                    "block": 5,
                    "playable": True,
                    "requires_target": False,
                }
            ],
            "enemies": [{"index": 0, "id": "TEST_ENEMY", "hp": 40, "intent": "Attack 5"}],
        },
        "run": {
            "character_id": "DEFECT",
            "current_hp": 60,
            "max_hp": 75,
            "deck": [],
            "relics": [{"id": "ORICHALCUM", "name": "Orichalcum"}],
        },
    }
    combat_action, _, reason = ai.choose_combat_action(orichalcum_state)
    assert ai.passive_end_turn_block(orichalcum_state, 0) == 6
    assert combat_action == "end_turn", reason

    orichalcum_partial_pressure_state = {
        **orichalcum_state,
        "combat": {
            **orichalcum_state["combat"],
            "energy": 1,
            "hand": [
                {
                    "index": 0,
                    "id": "BLUR",
                    "name": "Blur",
                    "type": "Skill",
                    "cost": 1,
                    "block": 3,
                    "description": "Gain 3 Block. Block is not removed at the start of your next turn.",
                    "playable": True,
                    "requires_target": False,
                }
            ],
            "enemies": [{"index": 0, "id": "TEST_ENEMY", "hp": 40, "intent": "Attack 11"}],
        },
        "run": {**orichalcum_state["run"], "character_id": "SILENT"},
    }
    combat_action, _, reason = ai.choose_combat_action(orichalcum_partial_pressure_state)
    assert combat_action == "end_turn", reason

    no_pressure_block_state = {
        **orichalcum_state,
        "combat": {
            **orichalcum_state["combat"],
            "hand": [
                {
                    "index": 0,
                    "id": "DEFEND_DEFECT",
                    "name": "Defend",
                    "type": "Skill",
                    "cost": 1,
                    "block": 5,
                    "playable": True,
                    "requires_target": False,
                }
            ],
            "enemies": [{"index": 0, "id": "TEST_ENEMY", "hp": 40, "intent": "Attack 0"}],
        },
        "run": {**orichalcum_state["run"], "relics": []},
    }
    combat_action, _, reason = ai.choose_combat_action(no_pressure_block_state)
    assert combat_action == "end_turn", reason

    covered_block_state = {
        **orichalcum_state,
        "combat": {
            **orichalcum_state["combat"],
            "player": {"block": 8},
            "hand": [
                {
                    "index": 0,
                    "id": "DEFEND_SILENT",
                    "name": "Defend",
                    "type": "Skill",
                    "cost": 1,
                    "block": 5,
                    "playable": True,
                    "requires_target": False,
                }
            ],
            "enemies": [{"index": 0, "id": "TEST_ENEMY", "hp": 40, "intent": "Attack 4"}],
        },
        "run": {**orichalcum_state["run"], "character_id": "SILENT", "relics": []},
    }
    combat_action, _, reason = ai.choose_combat_action(covered_block_state)
    assert combat_action == "end_turn", reason

    covered_functional_block_state = {
        **covered_block_state,
        "combat": {
            **covered_block_state["combat"],
            "hand": [
                {
                    "index": 0,
                    "id": "BACKFLIP",
                    "name": "Backflip",
                    "type": "Skill",
                    "cost": 1,
                    "block": 5,
                    "draw": 2,
                    "description": "Gain 5 Block. Draw 2 cards.",
                    "playable": True,
                    "requires_target": False,
                }
            ],
        },
    }
    combat_action, _, reason = ai.choose_combat_action(covered_functional_block_state)
    assert combat_action == "play_card", reason

    no_pressure_survivor_state = {
        "screen": "COMBAT",
        "available_actions": ["play_card", "end_turn"],
        "combat": {
            "energy": 1,
            "player": {"block": 0},
            "hand": [
                {
                    "index": 0,
                    "id": "SURVIVOR",
                    "name": "Survivor",
                    "type": "Skill",
                    "cost": 1,
                    "block": 8,
                    "description": "Gain 8 Block. Discard 1 card.",
                    "playable": True,
                    "requires_target": False,
                }
            ],
            "enemies": [{"index": 0, "id": "TEST_ENEMY", "hp": 40, "intent": "Attack 0"}],
        },
        "run": {
            "character_id": "SILENT",
            "current_hp": 60,
            "max_hp": 70,
            "deck": [],
            "relics": [],
        },
    }
    combat_action, _, reason = ai.choose_combat_action(no_pressure_survivor_state)
    assert combat_action == "end_turn", reason

    survivor_cleans_status_state = {
        **no_pressure_survivor_state,
        "combat": {
            **no_pressure_survivor_state["combat"],
            "hand": [
                no_pressure_survivor_state["combat"]["hand"][0],
                {
                    "index": 1,
                    "id": "WOUND",
                    "name": "Wound",
                    "type": "Status",
                    "rarity": "Status",
                    "cost": -1,
                    "playable": False,
                    "requires_target": False,
                },
            ],
        },
    }
    combat_action, kwargs, reason = ai.choose_combat_action(survivor_cleans_status_state)
    assert combat_action == "play_card", reason
    assert kwargs["card_index"] == 0

    survivor_discards_resource_state = {
        **no_pressure_survivor_state,
        "combat": {
            **no_pressure_survivor_state["combat"],
            "hand": [
                no_pressure_survivor_state["combat"]["hand"][0],
                {
                    "index": 1,
                    "id": "REFLEX",
                    "name": "Reflex",
                    "type": "Skill",
                    "rarity": "Uncommon",
                    "cost": -1,
                    "playable": False,
                    "requires_target": False,
                },
            ],
        },
    }
    combat_action, kwargs, reason = ai.choose_combat_action(survivor_discards_resource_state)
    assert combat_action == "play_card", reason
    assert kwargs["card_index"] == 0

    avoidable_chip_state = {
        "screen": "COMBAT",
        "available_actions": ["play_card", "end_turn"],
        "combat": {
            "energy": 1,
            "player": {"block": 0},
            "hand": [
                {
                    "index": 0,
                    "id": "DEFEND_SILENT",
                    "name": "Defend",
                    "type": "Skill",
                    "cost": 1,
                    "block": 5,
                    "playable": True,
                    "requires_target": False,
                },
                {
                    "index": 1,
                    "id": "STRIKE_SILENT",
                    "name": "Strike",
                    "type": "Attack",
                    "cost": 1,
                    "damage": 6,
                    "playable": True,
                    "requires_target": True,
                },
                {
                    "index": 2,
                    "id": "SURVIVOR",
                    "name": "Survivor",
                    "type": "Skill",
                    "cost": 1,
                    "block": 8,
                    "description": "Gain 8 Block. Discard 1 card.",
                    "playable": True,
                    "requires_target": False,
                },
            ],
            "enemies": [{"index": 0, "id": "TUNNELER", "hp": 78, "intent": "Attack 9"}],
        },
        "run": {
            "character_id": "SILENT",
            "current_hp": 75,
            "max_hp": 75,
            "deck": [],
            "relics": [{"id": "RING_OF_THE_SNAKE", "name": "Ring of the Snake"}],
        },
    }
    combat_action, kwargs, reason = ai.choose_combat_action(avoidable_chip_state)
    assert combat_action == "play_card", reason
    assert kwargs["card_index"] == 2

    large_avoidable_chip_state = {
        "screen": "COMBAT",
        "available_actions": ["play_card", "end_turn"],
        "combat": {
            "energy": 1,
            "player": {"block": 0},
            "hand": [
                {
                    "index": 0,
                    "id": "SURVIVOR",
                    "name": "Survivor",
                    "type": "Skill",
                    "cost": 1,
                    "block": 8,
                    "description": "Gain 8 Block. Discard 1 card.",
                    "playable": True,
                    "requires_target": False,
                },
                {
                    "index": 1,
                    "id": "HEAVY_TEST_ATTACK",
                    "name": "Heavy Test Attack",
                    "type": "Attack",
                    "cost": 1,
                    "damage": 16,
                    "playable": True,
                    "requires_target": True,
                },
                {
                    "index": 2,
                    "id": "DEFEND_SILENT",
                    "name": "Defend",
                    "type": "Skill",
                    "cost": 1,
                    "block": 5,
                    "playable": True,
                    "requires_target": False,
                },
            ],
            "enemies": [{"index": 0, "id": "TEST_ENEMY", "hp": 80, "intent": "Attack 11"}],
        },
        "run": {
            "character_id": "SILENT",
            "current_hp": 41,
            "max_hp": 70,
            "deck": [],
            "relics": [{"id": "RING_OF_THE_SNAKE", "name": "Ring of the Snake"}],
        },
    }
    combat_action, kwargs, reason = ai.choose_combat_action(large_avoidable_chip_state)
    assert combat_action == "play_card", reason
    assert kwargs["card_index"] == 0

    desperation_damage_state = {
        "screen": "COMBAT",
        "available_actions": ["play_card", "end_turn"],
        "combat": {
            "energy": 1,
            "player": {"block": 0},
            "hand": [
                {
                    "index": 0,
                    "id": "STRIKE_IRONCLAD",
                    "name": "Strike",
                    "type": "Attack",
                    "cost": 1,
                    "damage": 6,
                    "playable": True,
                    "requires_target": True,
                }
            ],
            "enemies": [{"index": 0, "id": "BOSS", "hp": 200, "intent": "Attack 30"}],
        },
        "run": {
            "character_id": "IRONCLAD",
            "current_hp": 30,
            "max_hp": 80,
            "deck": [],
            "relics": [],
        },
    }
    combat_action, kwargs, reason = ai.choose_combat_action(desperation_damage_state)
    assert combat_action == "end_turn", reason

    lizard_tail_spend_damage_state = {
        **desperation_damage_state,
        "combat": {
            **desperation_damage_state["combat"],
            "energy": 1,
            "hand": [
                {
                    "index": 0,
                    "id": "MEMENTO_MORI",
                    "name": "Memento Mori",
                    "type": "Attack",
                    "cost": 1,
                    "damage": 12,
                    "playable": True,
                    "requires_target": True,
                }
            ],
        },
        "run": {
            **desperation_damage_state["run"],
            "character_id": "SILENT",
            "current_hp": 10,
            "max_hp": 75,
            "relics": [{"id": "LIZARD_TAIL", "name": "Lizard Tail"}],
        },
    }
    combat_action, kwargs, reason = ai.choose_combat_action(lizard_tail_spend_damage_state)
    assert combat_action == "play_card", reason
    assert kwargs["card_index"] == 0

    critical_low_hp_chip_state = {
        "screen": "COMBAT",
        "available_actions": ["play_card", "end_turn"],
        "combat": {
            "energy": 1,
            "player": {"block": 5},
            "hand": [
                {
                    "index": 0,
                    "id": "DEFEND_SILENT",
                    "name": "Defend",
                    "type": "Skill",
                    "cost": 1,
                    "block": 5,
                    "playable": True,
                    "requires_target": False,
                },
                {
                    "index": 1,
                    "id": "STRIKE_SILENT",
                    "name": "Strike",
                    "type": "Attack",
                    "cost": 1,
                    "damage": 6,
                    "playable": True,
                    "requires_target": True,
                },
            ],
            "enemies": [{"index": 0, "id": "FOGMOG", "hp": 28, "intent": "Attack 11"}],
        },
        "run": {
            "character_id": "SILENT",
            "current_hp": 19,
            "max_hp": 75,
            "deck": [],
            "relics": [{"id": "RING_OF_THE_SNAKE", "name": "Ring of the Snake"}],
        },
    }
    combat_action, kwargs, reason = ai.choose_combat_action(critical_low_hp_chip_state)
    assert combat_action == "play_card", reason
    assert kwargs["card_index"] == 0

    partial_chip_state = {
        "screen": "COMBAT",
        "available_actions": ["play_card", "end_turn"],
        "combat": {
            "energy": 1,
            "player": {"block": 0},
            "hand": [
                {
                    "index": 0,
                    "id": "RATTLE",
                    "name": "Rattle",
                    "type": "Attack",
                    "cost": 1,
                    "damage": 7,
                    "playable": True,
                    "requires_target": True,
                },
                {
                    "index": 1,
                    "id": "DEFEND_NECROBINDER",
                    "name": "Defend",
                    "type": "Skill",
                    "cost": 1,
                    "block": 5,
                    "playable": True,
                    "requires_target": False,
                },
                {
                    "index": 2,
                    "id": "UNLEASH",
                    "name": "Unleash",
                    "type": "Attack",
                    "cost": 1,
                    "damage": 8,
                    "playable": True,
                    "requires_target": True,
                },
            ],
            "enemies": [{"index": 0, "id": "FLYCONID", "hp": 30, "intent": "Attack 11"}],
        },
        "run": {
            "character_id": "NECROBINDER",
            "current_hp": 60,
            "max_hp": 66,
            "deck": [],
            "relics": [{"id": "BOUND_PHYLACTERY", "name": "Bound Phylactery"}],
        },
    }
    combat_action, kwargs, reason = ai.choose_combat_action(partial_chip_state)
    assert combat_action == "play_card", reason
    assert kwargs["card_index"] == 1

    lethal_chip_state = {
        **avoidable_chip_state,
        "combat": {
            **avoidable_chip_state["combat"],
            "enemies": [{"index": 0, "id": "TUNNELER", "hp": 6, "intent": "Attack 9"}],
        },
    }
    combat_action, kwargs, reason = ai.choose_combat_action(lethal_chip_state)
    assert combat_action == "play_card", reason
    assert kwargs["card_index"] == 1

    lethal_sequence_before_death_state = {
        "screen": "COMBAT",
        "available_actions": ["play_card", "end_turn"],
        "combat": {
            "energy": 3,
            "player": {"block": 0},
            "hand": [
                {
                    "index": 0,
                    "id": "DAGGER_SPRAY",
                    "name": "Dagger Spray",
                    "type": "Attack",
                    "cost": 1,
                    "damage": 6,
                    "playable": True,
                    "requires_target": False,
                    "description": "Deal 4 damage to ALL enemies.",
                    "target": "AllEnemies",
                },
                {
                    "index": 1,
                    "id": "STRIKE_SILENT",
                    "name": "Strike",
                    "type": "Attack",
                    "cost": 1,
                    "damage": 8,
                    "playable": True,
                    "requires_target": True,
                },
            ],
            "enemies": [{"index": 0, "id": "BYGONE_EFFIGY", "hp": 12, "intent": "Attack 17"}],
        },
        "run": {
            "character_id": "SILENT",
            "floor": 14,
            "current_hp": 5,
            "max_hp": 70,
            "deck": [],
            "relics": [{"id": "RING_OF_THE_SNAKE", "name": "Ring of the Snake"}],
        },
    }
    assert ai.hand_has_affordable_lethal_sequence(
        ai.playable_cards(lethal_sequence_before_death_state),
        lethal_sequence_before_death_state,
        energy=3,
    )
    combat_action, kwargs, reason = ai.choose_combat_action(lethal_sequence_before_death_state)
    assert combat_action == "play_card", reason
    assert kwargs["card_index"] in {0, 1}, reason

    reindexed_enemy_target_state = {
        "screen": "COMBAT",
        "available_actions": ["play_card", "end_turn"],
        "combat": {
            "energy": 2,
            "player": {"block": 0},
            "hand": [
                {
                    "index": 0,
                    "id": "DASH",
                    "name": "Dash",
                    "type": "Attack",
                    "cost": 2,
                    "damage": 10,
                    "block": 10,
                    "playable": True,
                    "requires_target": True,
                }
            ],
            "enemies": [
                {"index": 0, "id": "KIN_FOLLOWER", "hp": 40, "intent": "Attack 0"},
                {"index": 2, "id": "KIN_FOLLOWER", "hp": 40, "intent": "Attack 0"},
                {"index": 3, "id": "KIN_PRIEST", "hp": 10, "intent": "Attack 0"},
            ],
        },
        "run": {
            "character_id": "SILENT",
            "current_hp": 44,
            "max_hp": 70,
            "deck": [],
            "relics": [{"id": "RING_OF_THE_SNAKE", "name": "Ring of the Snake"}],
        },
    }
    assert ai.valid_targets(
        reindexed_enemy_target_state["combat"]["hand"][0],
        reindexed_enemy_target_state["combat"]["enemies"],
    ) == [0, 1, 2]
    combat_action, kwargs, reason = ai.choose_combat_action(reindexed_enemy_target_state)
    assert combat_action == "play_card", reason
    assert kwargs["target_index"] == 2, reason

    dangerous_kin_target_state = {
        "screen": "COMBAT",
        "available_actions": ["play_card", "end_turn"],
        "combat": {
            "energy": 1,
            "player": {"block": 0},
            "hand": [
                {
                    "index": 0,
                    "id": "STRIKE_SILENT",
                    "name": "Strike",
                    "type": "Attack",
                    "cost": 1,
                    "damage": 6,
                    "playable": True,
                    "requires_target": True,
                }
            ],
            "enemies": [
                {"index": 0, "id": "KIN_FOLLOWER", "hp": 28, "intent": "QUICK_SLASH_MOVE"},
                {"index": 1, "id": "KIN_PRIEST", "hp": 155, "intent": "RITUAL_MOVE"},
            ],
        },
        "run": {
            "character_id": "SILENT",
            "current_hp": 34,
            "max_hp": 70,
            "deck": [],
            "relics": [{"id": "RING_OF_THE_SNAKE", "name": "Ring of the Snake"}],
        },
    }
    assert ai.choose_enemy_for_damage(dangerous_kin_target_state["combat"]["enemies"], 6) == 0
    combat_action, kwargs, reason = ai.choose_combat_action(dangerous_kin_target_state)
    assert combat_action == "play_card", reason
    assert kwargs["target_index"] == 0, reason

    regent_no_pressure_block_state = {
        "screen": "COMBAT",
        "available_actions": ["play_card", "end_turn"],
        "combat": {
            "energy": 2,
            "player": {"block": 0},
            "hand": [
                {
                    "index": 0,
                    "id": "DEFEND_REGENT",
                    "name": "Defend",
                    "cost": 1,
                    "playable": True,
                    "requires_target": False,
                }
            ],
            "enemies": [{"index": 0, "id": "TEST_ENEMY", "hp": 40, "intent": "Attack 0"}],
        },
        "run": {
            "character_id": "REGENT",
            "current_hp": 60,
            "max_hp": 75,
            "deck": [],
            "relics": [],
        },
    }
    combat_action, _, reason = ai.choose_combat_action(regent_no_pressure_block_state)
    assert combat_action == "end_turn", reason

    untouchable_no_pressure_state = {
        **regent_no_pressure_block_state,
        "combat": {
            **regent_no_pressure_block_state["combat"],
            "energy": 2,
            "hand": [
                {
                    "index": 0,
                    "id": "UNTOUCHABLE",
                    "name": "Untouchable",
                    "type": "Skill",
                    "cost": 2,
                    "block": 9,
                    "playable": True,
                    "requires_target": False,
                    "keywords": ["Sly"],
                }
            ],
        },
        "run": {
            **regent_no_pressure_block_state["run"],
            "character_id": "SILENT",
            "current_hp": 44,
            "max_hp": 70,
            "relics": [{"id": "RING_OF_THE_SNAKE", "name": "Ring of the Snake"}],
        },
    }
    combat_action, _, reason = ai.choose_combat_action(untouchable_no_pressure_state)
    assert combat_action == "end_turn", reason

    low_hp_block_miss_state = {
        "screen": "COMBAT",
        "available_actions": ["play_card", "end_turn"],
        "combat": {
            "energy": 1,
            "player": {"block": 5},
            "hand": [
                {
                    "index": 0,
                    "id": "STRIKE_SILENT",
                    "name": "Strike",
                    "type": "Attack",
                    "cost": 1,
                    "damage": 6,
                    "playable": True,
                    "requires_target": True,
                },
                {
                    "index": 1,
                    "id": "DEFEND_SILENT",
                    "name": "Defend",
                    "type": "Skill",
                    "cost": 1,
                    "block": 5,
                    "playable": True,
                    "requires_target": False,
                },
            ],
            "enemies": [{"index": 0, "id": "FOGMOG", "hp": 34, "intent": "Attack 11"}],
        },
        "run": {
            "character_id": "SILENT",
            "current_hp": 33,
            "max_hp": 70,
            "deck": [],
            "relics": [{"id": "RING_OF_THE_SNAKE", "name": "Ring of the Snake"}],
        },
    }
    combat_action, kwargs, reason = ai.choose_combat_action(low_hp_block_miss_state)
    assert combat_action == "play_card", reason
    assert kwargs["card_index"] == 1

    doomed_weak_block_state = {
        "screen": "COMBAT",
        "available_actions": ["play_card", "end_turn"],
        "combat": {
            "energy": 1,
            "player": {"block": 0},
            "hand": [
                {
                    "index": 0,
                    "id": "DEFLECT",
                    "name": "Deflect",
                    "type": "Skill",
                    "cost": 0,
                    "block": 1,
                    "playable": True,
                    "requires_target": False,
                }
            ],
            "enemies": [{"index": 0, "id": "BOSS", "hp": 151, "intent": "Attack 25"}],
        },
        "run": {
            "character_id": "SILENT",
            "current_hp": 8,
            "max_hp": 70,
            "deck": [],
            "relics": [{"id": "RING_OF_THE_SNAKE", "name": "Ring of the Snake"}],
        },
    }
    combat_action, _, reason = ai.choose_combat_action(doomed_weak_block_state)
    assert combat_action == "end_turn", reason

    doomed_generated_block_state = {
        "screen": "COMBAT",
        "available_actions": ["play_card", "end_turn"],
        "combat": {
            "energy": 3,
            "player": {"block": 0},
            "hand": [
                {
                    "index": 0,
                    "id": "CLOAK_AND_DAGGER",
                    "name": "Cloak and Dagger",
                    "type": "Skill",
                    "cost": 1,
                    "block": 6,
                    "description": "Gain 6 Block. Add 1 Shiv to your hand.",
                    "playable": True,
                    "requires_target": False,
                }
            ],
            "enemies": [{"index": 0, "id": "CEREMONIAL_BEAST", "hp": 162, "intent": "Attack 24"}],
        },
        "run": {
            "character_id": "SILENT",
            "current_hp": 13,
            "max_hp": 70,
            "deck": [],
            "relics": [{"id": "RING_OF_THE_SNAKE", "name": "Ring of the Snake"}],
        },
    }
    combat_action, _, reason = ai.choose_combat_action(doomed_generated_block_state)
    assert combat_action == "end_turn", reason
    assert "doomed" in reason, reason

    block_chain_survives_state = {
        "screen": "COMBAT",
        "available_actions": ["play_card", "end_turn"],
        "combat": {
            "energy": 2,
            "player": {"block": 0},
            "hand": [
                {
                    "index": 0,
                    "id": "DEFEND_SILENT",
                    "name": "Defend",
                    "type": "Skill",
                    "cost": 1,
                    "block": 5,
                    "playable": True,
                    "requires_target": False,
                },
                {
                    "index": 1,
                    "id": "DEFEND_SILENT",
                    "name": "Defend",
                    "type": "Skill",
                    "cost": 1,
                    "block": 5,
                    "playable": True,
                    "requires_target": False,
                },
            ],
            "enemies": [{"index": 0, "id": "BOSS", "hp": 151, "intent": "Attack 17"}],
        },
        "run": {
            "character_id": "SILENT",
            "current_hp": 8,
            "max_hp": 70,
            "deck": [],
            "relics": [{"id": "RING_OF_THE_SNAKE", "name": "Ring of the Snake"}],
        },
    }
    combat_action, kwargs, reason = ai.choose_combat_action(block_chain_survives_state)
    assert combat_action == "play_card", reason
    assert kwargs["card_index"] in {0, 1}, reason

    doomed_wail_state = {
        "screen": "COMBAT",
        "available_actions": ["play_card", "end_turn"],
        "combat": {
            "energy": 1,
            "player": {"block": 0},
            "hand": [
                {
                    "index": 0,
                    "id": "PIERCING_WAIL",
                    "name": "Piercing Wail",
                    "type": "Skill",
                    "cost": 1,
                    "description": "ALL enemies lose 6 Strength this turn. Exhaust.",
                    "playable": True,
                    "requires_target": False,
                }
            ],
            "enemies": [{"index": 0, "id": "BOSS", "hp": 151, "intent": "Attack 25"}],
        },
        "run": {
            "character_id": "SILENT",
            "current_hp": 5,
            "max_hp": 70,
            "deck": [],
            "relics": [{"id": "RING_OF_THE_SNAKE", "name": "Ring of the Snake"}],
        },
    }
    combat_action, _, reason = ai.choose_combat_action(doomed_wail_state)
    assert combat_action == "end_turn", reason

    doomed_block_mitigation_state = {
        "screen": "COMBAT",
        "available_actions": ["play_card", "end_turn"],
        "combat": {
            "energy": 1,
            "player": {"block": 0},
            "hand": [
                {
                    "index": 0,
                    "id": "DEFEND_SILENT",
                    "name": "Defend",
                    "type": "Skill",
                    "rarity": "Basic",
                    "cost": 1,
                    "block": 5,
                    "playable": True,
                    "requires_target": False,
                }
            ],
            "enemies": [{"index": 0, "id": "TERROR_EEL", "hp": 26, "intent": "ThrashMove"}],
        },
        "run": {
            "character_id": "SILENT",
            "floor": 7,
            "current_hp": 5,
            "max_hp": 70,
            "deck": [],
            "relics": [{"id": "RING_OF_THE_SNAKE", "name": "Ring of the Snake"}],
        },
    }
    combat_action, kwargs, reason = ai.choose_combat_action(doomed_block_mitigation_state)
    assert combat_action == "play_card", reason
    assert kwargs["card_index"] == 0, reason

    zero_energy_x_setup_state = {
        "screen": "COMBAT",
        "available_actions": ["play_card", "end_turn"],
        "combat": {
            "energy": 0,
            "player": {"block": 0},
            "hand": [
                {
                    "index": 0,
                    "id": "MALAISE",
                    "name": "Malaise",
                    "type": "Skill",
                    "cost": 0,
                    "is_x_cost": True,
                    "playable": True,
                    "requires_target": True,
                    "keywords": ["Exhaust"],
                    "description": "Enemy loses X Strength. Apply X Weak. Exhaust.",
                }
            ],
            "enemies": [{"index": 0, "id": "TEST_ENEMY", "hp": 60, "intent": "Attack 0"}],
        },
        "run": {
            "character_id": "SILENT",
            "current_hp": 55,
            "max_hp": 70,
            "deck": [],
            "relics": [{"id": "RING_OF_THE_SNAKE", "name": "Ring of the Snake"}],
        },
    }
    combat_action, _, reason = ai.choose_combat_action(zero_energy_x_setup_state)
    assert combat_action == "end_turn", reason

    parrying_shield_state = {
        **regent_no_pressure_block_state,
        "combat": {
            **regent_no_pressure_block_state["combat"],
            "player": {"block": 5},
        },
        "run": {
            **regent_no_pressure_block_state["run"],
            "relics": [{"id": "PARRYING_SHIELD", "name": "Parrying Shield"}],
        },
    }
    combat_action, _, reason = ai.choose_combat_action(parrying_shield_state)
    assert combat_action == "play_card", reason

    silent_stalled_boss_state = {
        "run": {
            "character_id": "SILENT",
            "floor": 16,
            "current_hp": 50,
            "max_hp": 76,
            "deck": (
                [{"id": "STRIKE_SILENT", "name": "Strike", "type": "Attack", "rarity": "Basic", "cost": 1} for _ in range(5)]
                + [{"id": "DEFEND_SILENT", "name": "Defend", "type": "Skill", "rarity": "Basic", "cost": 1} for _ in range(5)]
                + [
                    {"id": "NEUTRALIZE", "name": "Neutralize", "type": "Attack", "rarity": "Basic", "cost": 0},
                    {"id": "SURVIVOR", "name": "Survivor", "type": "Skill", "rarity": "Basic", "cost": 1},
                    {"id": "POISONED_STAB", "name": "Poisoned Stab", "type": "Attack", "rarity": "Common", "cost": 1},
                    {"id": "FOOTWORK", "name": "Footwork", "type": "Power", "rarity": "Uncommon", "cost": 1},
                    {"id": "BACKFLIP", "name": "Backflip", "type": "Skill", "rarity": "Common", "cost": 1},
                    {"id": "CLOAK_AND_DAGGER", "name": "Cloak and Dagger", "type": "Skill", "rarity": "Common", "cost": 1},
                    {"id": "UNTOUCHABLE", "name": "Untouchable", "type": "Skill", "rarity": "Common", "cost": 2},
                    {"id": "ANTICIPATE", "name": "Anticipate", "type": "Skill", "rarity": "Common", "cost": 0},
                    {"id": "DODGE_AND_ROLL", "name": "Dodge and Roll", "type": "Skill", "rarity": "Common", "cost": 1},
                    {"id": "BACKFLIP", "name": "Backflip", "type": "Skill", "rarity": "Common", "cost": 1},
                    {"id": "SPOILS_MAP", "name": "Spoils Map", "type": "Quest", "rarity": "Quest", "cost": -1},
                ]
            ),
            "relics": [{"id": "RING_OF_THE_SNAKE", "name": "Ring of the Snake"}],
        }
    }
    silent_plan = ai.deck_plan(silent_stalled_boss_state)
    assert silent_plan.needs_damage, silent_plan.summary()
    boss_damage_reward = {
        "id": "BLADE_DANCE",
        "name": "Blade Dance",
        "type": "Skill",
        "rarity": "Common",
        "cost": 1,
        "description": "Add 3 Shivs into your Hand.",
        "spawns_cards": ["SHIV"],
    }
    boss_draw_block_reward = {
        "id": "BACKFLIP",
        "name": "Backflip",
        "type": "Skill",
        "rarity": "Common",
        "cost": 1,
        "block": 5,
        "description": "Gain 5 Block. Draw 2 cards.",
    }
    assert ai.generated_card_damage(boss_damage_reward) == 12
    assert ai.score_reward_card(boss_damage_reward, silent_stalled_boss_state) > ai.score_reward_card(
        boss_draw_block_reward,
        silent_stalled_boss_state,
    )

    silent_boss_damage_starved_state = {
        "run": {
            "character_id": "SILENT",
            "floor": 16,
            "current_hp": 46,
            "max_hp": 70,
            "deck": (
                [{"id": "STRIKE_SILENT", "name": "Strike", "type": "Attack", "rarity": "Basic", "cost": 1} for _ in range(2)]
                + [{"id": "DEFEND_SILENT", "name": "Defend", "type": "Skill", "rarity": "Basic", "cost": 1} for _ in range(5)]
                + [
                    {"id": "NEUTRALIZE", "name": "Neutralize", "type": "Attack", "rarity": "Basic", "cost": 0},
                    {"id": "SURVIVOR", "name": "Survivor", "type": "Skill", "rarity": "Basic", "cost": 1},
                    {"id": "ACCURACY", "name": "Accuracy", "type": "Power", "rarity": "Uncommon", "cost": 1},
                    {"id": "PIERCING_WAIL", "name": "Piercing Wail", "type": "Skill", "rarity": "Common", "cost": 1},
                    {"id": "CLOAK_AND_DAGGER", "name": "Cloak and Dagger", "type": "Skill", "rarity": "Common", "cost": 1},
                    {"id": "MALAISE", "name": "Malaise", "type": "Skill", "rarity": "Uncommon", "cost": -1},
                    {"id": "DAGGER_THROW", "name": "Dagger Throw", "type": "Attack", "rarity": "Common", "cost": 1},
                    {"id": "CLOAK_AND_DAGGER", "name": "Cloak and Dagger", "type": "Skill", "rarity": "Common", "cost": 1},
                    {"id": "ANTICIPATE", "name": "Anticipate", "type": "Skill", "rarity": "Common", "cost": 0},
                    {"id": "PREPARED", "name": "Prepared", "type": "Skill", "rarity": "Common", "cost": 0},
                    {"id": "DAGGER_THROW", "name": "Dagger Throw", "type": "Attack", "rarity": "Common", "cost": 1},
                ]
            ),
            "relics": [
                {"id": "RING_OF_THE_SNAKE", "name": "Ring of the Snake"},
                {"id": "PRECARIOUS_SHEARS", "name": "Precarious Shears"},
                {"id": "HAPPY_FLOWER", "name": "Happy Flower"},
            ],
        }
    }
    damage_starved_plan = ai.deck_plan(silent_boss_damage_starved_state)
    assert damage_starved_plan.needs_damage, damage_starved_plan.summary()
    poison_stab_reward = {
        "id": "POISONED_STAB",
        "name": "Poisoned Stab",
        "type": "Attack",
        "rarity": "Common",
        "cost": 1,
        "damage": 6,
        "description": "Deal 6 damage. Apply 3 Poison.",
    }
    dodge_reward = {
        "id": "DODGE_AND_ROLL",
        "name": "Dodge and Roll",
        "type": "Skill",
        "rarity": "Common",
        "cost": 1,
        "block": 4,
        "description": "Gain 4 Block. Next turn, gain 4 Block.",
    }
    backflip_reward = {
        "id": "BACKFLIP",
        "name": "Backflip",
        "type": "Skill",
        "rarity": "Common",
        "cost": 1,
        "block": 5,
        "description": "Gain 5 Block. Draw 2 cards.",
    }
    assert ai.score_reward_card(poison_stab_reward, silent_boss_damage_starved_state) > ai.score_reward_card(
        dodge_reward,
        silent_boss_damage_starved_state,
    )
    assert ai.score_reward_card(boss_damage_reward, silent_boss_damage_starved_state) > ai.score_reward_card(
        backflip_reward,
        silent_boss_damage_starved_state,
    )

    silent_needs_cycle_state = {
        "run": {
            "character_id": "SILENT",
            "floor": 15,
            "current_hp": 31,
            "max_hp": 70,
            "deck": (
                [{"id": "STRIKE_SILENT", "name": "Strike", "type": "Attack", "rarity": "Basic", "cost": 1} for _ in range(4)]
                + [{"id": "DEFEND_SILENT", "name": "Defend", "type": "Skill", "rarity": "Basic", "cost": 1} for _ in range(3)]
                + [
                    {"id": "NEUTRALIZE", "name": "Neutralize", "type": "Attack", "rarity": "Basic", "cost": 0, "upgraded": True},
                    {"id": "SURVIVOR", "name": "Survivor", "type": "Skill", "rarity": "Basic", "cost": 1, "upgraded": True},
                    {"id": "CLOAK_AND_DAGGER", "name": "Cloak and Dagger", "type": "Skill", "rarity": "Common", "cost": 1},
                    {"id": "EXPOSE", "name": "Expose", "type": "Skill", "rarity": "Uncommon", "cost": 0},
                    {"id": "BLUR", "name": "Blur", "type": "Skill", "rarity": "Common", "cost": 1},
                    {"id": "PREDATOR", "name": "Predator", "type": "Attack", "rarity": "Uncommon", "cost": 2},
                    {"id": "MEMENTO_MORI", "name": "Memento Mori", "type": "Attack", "rarity": "Rare", "cost": 1},
                    {"id": "POISONED_STAB", "name": "Poisoned Stab", "type": "Attack", "rarity": "Common", "cost": 1},
                    {"id": "SUCKER_PUNCH", "name": "Sucker Punch", "type": "Attack", "rarity": "Common", "cost": 1},
                ]
            ),
            "relics": [
                {"id": "RING_OF_THE_SNAKE", "name": "Ring of the Snake"},
                {"id": "ORICHALCUM", "name": "Orichalcum"},
            ],
        }
    }
    cycle_plan = ai.deck_plan(silent_needs_cycle_state)
    assert cycle_plan.needs_draw, cycle_plan.summary()
    calculated_gamble_reward = {
        "id": "CALCULATED_GAMBLE",
        "name": "Calculated Gamble",
        "type": "Skill",
        "rarity": "Uncommon",
        "cost": 0,
        "description": "Discard your hand, then draw that many cards.",
    }
    duplicate_expose_reward = {
        "id": "EXPOSE",
        "name": "Expose",
        "type": "Skill",
        "rarity": "Uncommon",
        "cost": 0,
        "description": "Remove all Artifact and Block from the enemy. Apply 2 Vulnerable.",
    }
    assert "draw" in ai.known_card_roles(calculated_gamble_reward)
    assert ai.score_reward_card(calculated_gamble_reward, silent_needs_cycle_state) > ai.score_reward_card(
        duplicate_expose_reward,
        silent_needs_cycle_state,
    )

    silent_dirty_repeat_attack_reward_state = {
        "screen": "CARD_SELECTION",
        "available_actions": ["choose_reward_card", "skip_reward_cards", "select_deck_card"],
        "selection": {
            "cards": [
                {
                    "index": 0,
                    "id": "PREDATOR",
                    "name": "Predator",
                    "type": "Attack",
                    "rarity": "Uncommon",
                    "cost": 2,
                    "damage": 15,
                    "description": "Deal 15 damage. Draw 2 more cards next turn.",
                },
                {
                    "index": 1,
                    "id": "FLICK_FLACK",
                    "name": "Flick Flack",
                    "type": "Attack",
                    "rarity": "Common",
                    "cost": 1,
                    "damage": 6,
                },
                {
                    "index": 2,
                    "id": "STRIKE_SILENT",
                    "name": "Strike",
                    "type": "Attack",
                    "rarity": "Basic",
                    "cost": 1,
                    "damage": 6,
                },
            ]
        },
        "run": {
            "character_id": "SILENT",
            "floor": 16,
            "current_hp": 34,
            "max_hp": 77,
            "deck": (
                [{"id": "STRIKE_SILENT", "name": "Strike", "type": "Attack", "rarity": "Basic", "cost": 1} for _ in range(5)]
                + [{"id": "DEFEND_SILENT", "name": "Defend", "type": "Skill", "rarity": "Basic", "cost": 1} for _ in range(4)]
                + [
                    {"id": "NEUTRALIZE", "name": "Neutralize+", "type": "Attack", "rarity": "Basic", "cost": 0, "upgraded": True},
                    {"id": "SURVIVOR", "name": "Survivor+", "type": "Skill", "rarity": "Basic", "cost": 1, "upgraded": True},
                    {"id": "SEEKER_STRIKE", "name": "Seeker Strike", "type": "Attack", "rarity": "Uncommon", "cost": 1, "damage": 9},
                    {"id": "FLICK_FLACK", "name": "Flick Flack", "type": "Attack", "rarity": "Common", "cost": 1, "damage": 6},
                    {"id": "CLOAK_AND_DAGGER", "name": "Cloak and Dagger", "type": "Skill", "rarity": "Common", "cost": 1, "block": 6},
                    {"id": "DODGE_AND_ROLL", "name": "Dodge and Roll", "type": "Skill", "rarity": "Common", "cost": 1, "block": 4},
                    {"id": "PREDATOR", "name": "Predator", "type": "Attack", "rarity": "Uncommon", "cost": 2, "damage": 15},
                    {"id": "FLICK_FLACK", "name": "Flick Flack", "type": "Attack", "rarity": "Common", "cost": 1, "damage": 6},
                    {"id": "HAND_TRICK", "name": "Hand Trick", "type": "Skill", "rarity": "Uncommon", "cost": 1, "block": 7},
                    {"id": "FLICK_FLACK", "name": "Flick Flack", "type": "Attack", "rarity": "Common", "cost": 1, "damage": 6},
                    {"id": "ENVENOM", "name": "Envenom", "type": "Power", "rarity": "Rare", "cost": 2},
                ]
            ),
            "relics": [
                {"id": "RING_OF_THE_SNAKE", "name": "Ring of the Snake"},
                {"id": "LEAD_PAPERWEIGHT", "name": "Lead Paperweight"},
                {"id": "STRAWBERRY", "name": "Strawberry"},
            ],
        },
    }
    dirty_plan = ai.deck_plan(silent_dirty_repeat_attack_reward_state)
    assert dirty_plan.needs_draw and dirty_plan.wants_removal, dirty_plan.summary()
    dirty_predator = silent_dirty_repeat_attack_reward_state["selection"]["cards"][0]
    dirty_predator_score = ai.score_reward_card(dirty_predator, silent_dirty_repeat_attack_reward_state)
    assert dirty_predator_score < ai.reward_take_threshold(
        silent_dirty_repeat_attack_reward_state,
        dirty_predator,
        dirty_predator_score,
    )
    assert ai.choose_reward_index(silent_dirty_repeat_attack_reward_state) is None

    class RewardRecorder:
        def __init__(self) -> None:
            self.deck_selection_attempts = {}
            self.opened_shop_floors = set()
            self.calls = []

        def act(self, action, reason, **kwargs):
            self.calls.append((action, reason, kwargs))

    reward_recorder = RewardRecorder()
    ai.Autoplayer.step(
        reward_recorder,
        silent_dirty_repeat_attack_reward_state,
        set(silent_dirty_repeat_attack_reward_state["available_actions"]),
    )
    assert reward_recorder.calls[0][0] == "skip_reward_cards", reward_recorder.calls

    low_value_card_claim_state = {
        "screen": "REWARD",
        "available_actions": ["claim_reward", "resolve_rewards", "collect_rewards_and_proceed"],
        "reward": {
            "pending_card_choice": False,
            "can_proceed": True,
            "rewards": [
                {"index": 0, "reward_type": "Gold", "description": "18 Gold", "claimable": True},
                {
                    "index": 1,
                    "reward_type": "Card",
                    "description": "Add a card to your deck.",
                    "claimable": True,
                },
            ],
        },
        "run": {
            "character_id": "SILENT",
            "floor": 4,
            "current_hp": 45,
            "max_hp": 70,
            "deck": (
                [{"id": "STRIKE_SILENT", "name": "Strike", "type": "Attack", "rarity": "Basic", "cost": 1} for _ in range(5)]
                + [{"id": "DEFEND_SILENT", "name": "Defend", "type": "Skill", "rarity": "Basic", "cost": 1} for _ in range(3)]
                + [
                    {"id": "NEUTRALIZE", "name": "Neutralize", "type": "Attack", "rarity": "Basic", "cost": 0},
                    {"id": "SURVIVOR", "name": "Survivor", "type": "Skill", "rarity": "Basic", "cost": 1},
                    {"id": "LEADING_STRIKE", "name": "Leading Strike", "type": "Attack", "rarity": "Common", "cost": 1},
                    {"id": "DAGGER_THROW", "name": "Dagger Throw", "type": "Attack", "rarity": "Common", "cost": 1},
                    {"id": "BACKFLIP", "name": "Backflip", "type": "Skill", "rarity": "Common", "cost": 1},
                ]
            ),
            "relics": [
                {"id": "RING_OF_THE_SNAKE", "name": "Ring of the Snake"},
                {"id": "PRECARIOUS_SHEARS", "name": "Precarious Shears"},
            ],
        },
    }
    assert ai.claim_card_reward_score(low_value_card_claim_state)[0] < ai.claim_card_reward_threshold(
        low_value_card_claim_state
    )
    assert ai.choose_claim_reward_index(low_value_card_claim_state) == 0
    only_low_value_card_claim_state = {
        **low_value_card_claim_state,
        "reward": {
            **low_value_card_claim_state["reward"],
            "rewards": [low_value_card_claim_state["reward"]["rewards"][1]],
        },
    }
    assert ai.choose_claim_reward_index(only_low_value_card_claim_state) is None

    covered_calculated_gamble_state = {
        "screen": "COMBAT",
        "available_actions": ["play_card", "end_turn"],
        "combat": {
            "energy": 0,
            "player": {"block": 13},
            "hand": [
                {
                    "index": 0,
                    "id": "CALCULATED_GAMBLE",
                    "name": "Calculated Gamble",
                    "type": "Skill",
                    "rarity": "Uncommon",
                    "cost": 0,
                    "description": "Discard your hand, then draw that many cards. Exhaust.",
                    "playable": True,
                    "requires_target": False,
                }
            ],
            "enemies": [{"index": 0, "id": "TEST_ENEMY", "hp": 80, "intent": "Attack 13"}],
        },
        "run": {
            "character_id": "SILENT",
            "current_hp": 45,
            "max_hp": 70,
            "deck": silent_needs_cycle_state["run"]["deck"],
            "relics": [{"id": "RING_OF_THE_SNAKE", "name": "Ring of the Snake"}],
        },
    }
    combat_action, _, reason = ai.choose_combat_action(covered_calculated_gamble_state)
    assert combat_action == "end_turn", reason

    empty_cycle_calculated_gamble_state = {
        **covered_calculated_gamble_state,
        "combat": {
            **covered_calculated_gamble_state["combat"],
            "player": {"block": 0},
            "enemies": [{"index": 0, "id": "TEST_ENEMY", "hp": 80, "intent": "Attack 12"}],
        },
    }
    combat_action, _, reason = ai.choose_combat_action(empty_cycle_calculated_gamble_state)
    assert combat_action == "end_turn", reason

    pressure_anticipate_state = {
        "screen": "COMBAT",
        "available_actions": ["play_card", "end_turn"],
        "combat": {
            "energy": 0,
            "player": {"block": 8},
            "hand": [
                {
                    "index": 0,
                    "id": "ANTICIPATE",
                    "name": "Anticipate",
                    "type": "Skill",
                    "rarity": "Common",
                    "cost": 0,
                    "description": "Gain 2 Dexterity this turn.",
                    "playable": True,
                    "requires_target": False,
                }
            ],
            "enemies": [{"index": 0, "id": "WATERFALL_GIANT", "hp": 220, "intent": "Attack 30"}],
        },
        "run": {
            "character_id": "SILENT",
            "floor": 17,
            "current_hp": 20,
            "max_hp": 76,
            "deck": silent_stalled_boss_state["run"]["deck"],
            "relics": [{"id": "RING_OF_THE_SNAKE", "name": "Ring of the Snake"}],
        },
    }
    combat_action, _, reason = ai.choose_combat_action(pressure_anticipate_state)
    assert combat_action == "end_turn", reason

    no_attack_wail_state = {
        "screen": "COMBAT",
        "available_actions": ["play_card", "end_turn"],
        "combat": {
            "energy": 1,
            "player": {"block": 0},
            "hand": [
                {
                    "index": 0,
                    "id": "PIERCING_WAIL",
                    "name": "Piercing Wail",
                    "type": "Skill",
                    "rarity": "Common",
                    "cost": 1,
                    "description": "ALL enemies lose 6 Strength this turn. Exhaust.",
                    "playable": True,
                    "requires_target": False,
                }
            ],
            "enemies": [{"index": 0, "id": "TEST_ENEMY", "hp": 60, "intent": "Attack 0"}],
        },
        "run": {
            "character_id": "SILENT",
            "floor": 6,
            "current_hp": 55,
            "max_hp": 70,
            "deck": [],
            "relics": [{"id": "RING_OF_THE_SNAKE", "name": "Ring of the Snake"}],
        },
    }
    combat_action, _, reason = ai.choose_combat_action(no_attack_wail_state)
    assert combat_action == "end_turn", reason

    high_attack_wail_state = {
        **no_attack_wail_state,
        "combat": {
            **no_attack_wail_state["combat"],
            "enemies": [{"index": 0, "id": "TEST_ENEMY", "hp": 60, "intent": "Attack 24"}],
        },
    }
    combat_action, _, reason = ai.choose_combat_action(high_attack_wail_state)
    assert combat_action == "play_card", reason

    small_attack_wail_state = {
        **no_attack_wail_state,
        "combat": {
            **no_attack_wail_state["combat"],
            "enemies": [{"index": 0, "id": "TEST_ENEMY", "hp": 60, "intent": "Attack 4"}],
        },
        "run": {
            **no_attack_wail_state["run"],
            "current_hp": 22,
        },
    }
    combat_action, _, reason = ai.choose_combat_action(small_attack_wail_state)
    assert combat_action == "end_turn", reason

    small_attack_wail_with_block_state = {
        **small_attack_wail_state,
        "combat": {
            **small_attack_wail_state["combat"],
            "energy": 2,
            "hand": [
                small_attack_wail_state["combat"]["hand"][0],
                {
                    "index": 1,
                    "id": "DEFEND_SILENT",
                    "name": "Defend",
                    "type": "Skill",
                    "rarity": "Basic",
                    "cost": 1,
                    "block": 5,
                    "playable": True,
                    "requires_target": False,
                },
            ],
            "enemies": [{"index": 0, "id": "TEST_ENEMY", "hp": 60, "intent": "Attack 7"}],
        },
    }
    combat_action, kwargs, reason = ai.choose_combat_action(small_attack_wail_with_block_state)
    assert combat_action == "play_card", reason
    assert kwargs["card_index"] == 1, reason

    print("relic strategy smoke test passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
