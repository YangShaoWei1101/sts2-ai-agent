# STS2 Card Model

Generated from live game API plus Spire Codex English API. Use `card_model.json` for machine decisions and this file for human review.

## ironclad (87)

| Card | Cost | Type | Rarity | Roles | Use |
| --- | ---: | --- | --- | --- | --- |
| Break (BREAK) | 1 | Attack | Ancient | attack, debuff, vulnerable | single-target damage; enemy debuff setup; archetypes: ic_vulnerable_burst |
| Bash (BASH) | 2 | Attack | Basic | attack, debuff, expensive, vulnerable | single-target damage; enemy debuff setup; archetypes: ic_vulnerable_burst |
| Strike (STRIKE_IRONCLAD) | 1 | Attack | Basic | attack | single-target damage |
| Anger (ANGER) | 0 | Attack | Common | attack, card_generation, deck_manipulation, discard, zero_cost | single-target damage; card generation/deck manipulation; archetypes: ic_attack_chain |
| Body Slam (BODY_SLAM) | 1 | Attack | Common | attack, block | single-target damage; block/mitigation; archetypes: ic_block_body_slam |
| Breakthrough (BREAKTHROUGH) | 1 | Attack | Common | aoe, attack, self_damage | damage/AoE; self-damage payoff/enabler; needs HP discipline; archetypes: ic_self_damage_strength |
| Cinder (CINDER) | 2 | Attack | Common | attack, exhaust, expensive | single-target damage; archetypes: ic_exhaust_engine |
| Headbutt (HEADBUTT) | 1 | Attack | Common | attack, deck_manipulation, discard | single-target damage |
| Iron Wave (IRON_WAVE) | 1 | Attack | Common | attack, block | single-target damage; block/mitigation; archetypes: ic_block_body_slam |
| Molten Fist (MOLTEN_FIST) | 1 | Attack | Common | attack, debuff, exhaust, vulnerable | single-target damage; enemy debuff setup; archetypes: ic_exhaust_engine, ic_vulnerable_burst |
| Perfected Strike (PERFECTED_STRIKE) | 2 | Attack | Common | attack, expensive | single-target damage; archetypes: ic_attack_chain |
| Pommel Strike (POMMEL_STRIKE) | 1 | Attack | Common | attack, draw | single-target damage; draw/cycle |
| Setup Strike (SETUP_STRIKE) | 1 | Attack | Common | attack, strength | single-target damage |
| Sword Boomerang (SWORD_BOOMERANG) | 1 | Attack | Common | aoe, attack, multi_hit, random_target | damage/AoE; archetypes: ic_attack_chain |
| Thunderclap (THUNDERCLAP) | 1 | Attack | Common | aoe, attack, debuff, vulnerable | damage/AoE; enemy debuff setup; archetypes: ic_vulnerable_burst |
| Twin Strike (TWIN_STRIKE) | 1 | Attack | Common | attack, multi_hit | single-target damage; archetypes: ic_attack_chain |
| Conflagration (CONFLAGRATION) | 1 | Attack | Rare | aoe, attack, multi_hit | damage/AoE; archetypes: ic_attack_chain |
| Feed (FEED) | 1 | Attack | Rare | attack, exhaust, fatal_reward, max_hp | single-target damage; archetypes: ic_exhaust_engine |
| Fiend Fire (FIEND_FIRE) | 2 | Attack | Rare | attack, exhaust, expensive, multi_hit | single-target damage; archetypes: ic_exhaust_engine |
| Mangle (MANGLE) | 3 | Attack | Rare | attack, debuff, expensive, strength | single-target damage; enemy debuff setup |
| Pact's End (PACTS_END) | 0 | Attack | Rare | aoe, attack, draw, exhaust, zero_cost | damage/AoE; draw/cycle; archetypes: ic_exhaust_engine |
| Tear Asunder (TEAR_ASUNDER) | 2 | Attack | Rare | attack, expensive, multi_hit | single-target damage; archetypes: ic_self_damage_strength |
| Thrash (THRASH) | 1 | Attack | Rare | attack, card_generation, exhaust, multi_hit | single-target damage; card generation/deck manipulation; archetypes: ic_exhaust_engine |
| Ashen Strike (ASHEN_STRIKE) | 1 | Attack | Uncommon | attack, exhaust, multi_hit | single-target damage; archetypes: ic_exhaust_engine |
| Bludgeon (BLUDGEON) | 3 | Attack | Uncommon | attack, expensive | single-target damage |
| Bully (BULLY) | 0 | Attack | Uncommon | attack, debuff, multi_hit, vulnerable, zero_cost | single-target damage; enemy debuff setup; archetypes: ic_vulnerable_burst |
| Dismantle (DISMANTLE) | 1 | Attack | Uncommon | attack, debuff, multi_hit, vulnerable | single-target damage; enemy debuff setup; archetypes: ic_vulnerable_burst |
| Fight Me! (FIGHT_ME) | 2 | Attack | Uncommon | attack, expensive, multi_hit, strength | single-target damage |
| Hemokinesis (HEMOKINESIS) | 1 | Attack | Uncommon | attack, self_damage | single-target damage; self-damage payoff/enabler; needs HP discipline; archetypes: ic_self_damage_strength |
| Howl from Beyond (HOWL_FROM_BEYOND) | 3 | Attack | Uncommon | aoe, attack, exhaust, expensive | damage/AoE; archetypes: ic_exhaust_engine |
| Pillage (PILLAGE) | 1 | Attack | Uncommon | attack, draw | single-target damage; draw/cycle |
| Rampage (RAMPAGE) | 1 | Attack | Uncommon | attack | single-target damage |
| Spite (SPITE) | 0 | Attack | Uncommon | attack, multi_hit, zero_cost | single-target damage; archetypes: ic_self_damage_strength |
| Stomp (STOMP) | 3 | Attack | Uncommon | aoe, attack, expensive, multi_hit | damage/AoE; archetypes: ic_attack_chain |
| Unrelenting (UNRELENTING) | 2 | Attack | Uncommon | attack, energy, expensive | single-target damage; resource acceleration |
| Uppercut (UPPERCUT) | 2 | Attack | Uncommon | attack, debuff, expensive, vulnerable, weak | single-target damage; enemy debuff setup; archetypes: ic_vulnerable_burst |
| Whirlwind (WHIRLWIND) | 0 X | Attack | Uncommon | aoe, attack, multi_hit, x_cost, zero_cost | damage/AoE; archetypes: ic_attack_chain |
| Corruption (CORRUPTION) | 3 | Power | Ancient | exhaust, expensive, power_scaling | persistent scaling engine; archetypes: ic_exhaust_engine |
| Aggression (AGGRESSION) | 1 | Power | Rare | deck_manipulation, discard, power_scaling, upgrade_forge | persistent scaling engine |
| Barricade (BARRICADE) | 3 | Power | Rare | block, block_retention, expensive, power_scaling | block/mitigation; persistent scaling engine; archetypes: ic_block_body_slam |
| Crimson Mantle (CRIMSON_MANTLE) | 1 | Power | Rare | block, power_scaling, self_damage | block/mitigation; persistent scaling engine; self-damage payoff/enabler; needs HP discipline; archetypes: ic_block_body_slam, ic_self_damage_strength |
| Cruelty (CRUELTY) | 1 | Power | Rare | attack, debuff, power_scaling, vulnerable | single-target damage; persistent scaling engine; enemy debuff setup; archetypes: ic_vulnerable_burst |
| Dark Embrace (DARK_EMBRACE) | 2 | Power | Rare | draw, exhaust, expensive, power_scaling | draw/cycle; persistent scaling engine; archetypes: ic_exhaust_engine |
| Demon Form (DEMON_FORM) | 3 | Power | Rare | expensive, power_scaling, strength | persistent scaling engine |
| Hellraiser (HELLRAISER) | 2 | Power | Rare | aoe, expensive, power_scaling, random_target | persistent scaling engine; archetypes: ic_attack_chain |
| Juggernaut (JUGGERNAUT) | 2 | Power | Rare | aoe, attack, block, expensive, power_scaling, random_target | damage/AoE; block/mitigation; persistent scaling engine; archetypes: ic_block_body_slam |
| Pyre (PYRE) | 2 | Power | Rare | energy, expensive, power_scaling | resource acceleration; persistent scaling engine |
| Tank (TANK) | 1 | Power | Rare | attack, coop_only_value, power_scaling, self_damage | single-target damage; persistent scaling engine; self-damage payoff/enabler; needs HP discipline; archetypes: ic_self_damage_strength |
| Unmovable (UNMOVABLE) | 2 | Power | Rare | block, expensive, power_scaling | block/mitigation; persistent scaling engine; archetypes: ic_block_body_slam |
| Drum of Battle (DRUM_OF_BATTLE) | 0 | Power | Uncommon | deck_manipulation, draw, exhaust, power_scaling, zero_cost | draw/cycle; persistent scaling engine; archetypes: ic_exhaust_engine |
| Feel No Pain (FEEL_NO_PAIN) | 1 | Power | Uncommon | block, exhaust, power_scaling | block/mitigation; persistent scaling engine; archetypes: ic_block_body_slam, ic_exhaust_engine |
| Inferno (INFERNO) | 1 | Power | Uncommon | aoe, attack, power_scaling, self_damage | damage/AoE; persistent scaling engine; self-damage payoff/enabler; needs HP discipline; archetypes: ic_self_damage_strength |
| Inflame (INFLAME) | 1 | Power | Uncommon | power_scaling, strength | persistent scaling engine |
| Juggling (JUGGLING) | 1 | Power | Uncommon | card_generation, power_scaling | persistent scaling engine; card generation/deck manipulation; archetypes: ic_attack_chain |
| Rupture (RUPTURE) | 1 | Power | Uncommon | power_scaling, self_damage, strength | persistent scaling engine; self-damage payoff/enabler; needs HP discipline; archetypes: ic_self_damage_strength |
| Stampede (STAMPEDE) | 2 | Power | Uncommon | aoe, expensive, power_scaling, random_target | persistent scaling engine; archetypes: ic_attack_chain |
| Stone Armor (STONE_ARMOR) | 1 | Power | Uncommon | plating, power_scaling | persistent scaling engine |
| Vicious (VICIOUS) | 1 | Power | Uncommon | debuff, draw, power_scaling, vulnerable | draw/cycle; persistent scaling engine; enemy debuff setup; archetypes: ic_vulnerable_burst |
| Defend (DEFEND_IRONCLAD) | 1 | Skill | Basic | block | block/mitigation; archetypes: ic_block_body_slam |
| Armaments (ARMAMENTS) | 1 | Skill | Common | block, deck_manipulation, upgrade_forge | block/mitigation; archetypes: ic_block_body_slam |
| Blood Wall (BLOOD_WALL) | 2 | Skill | Common | block, expensive, self_damage | block/mitigation; self-damage payoff/enabler; needs HP discipline; archetypes: ic_block_body_slam, ic_self_damage_strength |
| Bloodletting (BLOODLETTING) | 0 | Skill | Common | energy, self_damage, zero_cost | resource acceleration; self-damage payoff/enabler; needs HP discipline; archetypes: ic_self_damage_strength |
| Havoc (HAVOC) | 1 | Skill | Common | deck_manipulation, exhaust | archetypes: ic_exhaust_engine |
| Shrug It Off (SHRUG_IT_OFF) | 1 | Skill | Common | block, draw | block/mitigation; draw/cycle; archetypes: ic_block_body_slam |
| Tremble (TREMBLE) | 1 | Skill | Common | debuff, exhaust, vulnerable | enemy debuff setup; archetypes: ic_exhaust_engine, ic_vulnerable_burst |
| True Grit (TRUE_GRIT) | 1 | Skill | Common | block, exhaust | block/mitigation; archetypes: ic_block_body_slam, ic_exhaust_engine |
| Brand (BRAND) | 0 | Skill | Rare | exhaust, self_damage, strength, zero_cost | self-damage payoff/enabler; needs HP discipline; archetypes: ic_exhaust_engine, ic_self_damage_strength |
| Cascade (CASCADE) | -1 X | Skill | Rare | deck_manipulation, x_cost | utility card; inspect exact text before drafting |
| Impervious (IMPERVIOUS) | 2 | Skill | Rare | block, exhaust, expensive | block/mitigation; archetypes: ic_block_body_slam, ic_exhaust_engine |
| Not Yet (NOT_YET) | 2 | Skill | Rare | exhaust, expensive, heal | archetypes: ic_exhaust_engine |
| Offering (OFFERING) | 0 | Skill | Rare | draw, energy, exhaust, self_damage, zero_cost | draw/cycle; resource acceleration; self-damage payoff/enabler; needs HP discipline; archetypes: ic_exhaust_engine, ic_self_damage_strength |
| One-Two Punch (ONE_TWO_PUNCH) | 1 | Skill | Rare |  | utility card; inspect exact text before drafting |
| Primal Force (PRIMAL_FORCE) | 0 | Skill | Rare | card_generation, deck_manipulation, zero_cost | card generation/deck manipulation |
| Stoke (STOKE) | 1 | Skill | Rare | card_generation, exhaust, upgrade_forge | card generation/deck manipulation; archetypes: ic_exhaust_engine |
| Battle Trance (BATTLE_TRANCE) | 0 | Skill | Uncommon | draw, zero_cost | draw/cycle |
| Burning Pact (BURNING_PACT) | 1 | Skill | Uncommon | draw, exhaust, status_pollution | draw/cycle; adds junk/status; draft only with payoff or cleanup; archetypes: ic_exhaust_engine |
| Colossus (COLOSSUS) | 1 | Skill | Uncommon | attack, block, debuff, vulnerable | single-target damage; block/mitigation; enemy debuff setup; archetypes: ic_block_body_slam, ic_vulnerable_burst |
| Demonic Shield (DEMONIC_SHIELD) | 0 | Skill | Uncommon | attack, block, coop_only_value, exhaust, self_damage, zero_cost | single-target damage; block/mitigation; self-damage payoff/enabler; needs HP discipline; archetypes: ic_block_body_slam, ic_exhaust_engine, ic_self_damage_strength |
| Dominate (DOMINATE) | 1 | Skill | Uncommon | debuff, exhaust, strength, vulnerable | enemy debuff setup; archetypes: ic_exhaust_engine, ic_vulnerable_burst |
| Evil Eye (EVIL_EYE) | 1 | Skill | Uncommon | block, exhaust | block/mitigation; archetypes: ic_block_body_slam, ic_exhaust_engine |
| Expect a Fight (EXPECT_A_FIGHT) | 2 | Skill | Uncommon | attack, energy, expensive | single-target damage; resource acceleration |
| Flame Barrier (FLAME_BARRIER) | 2 | Skill | Uncommon | attack, block, expensive | single-target damage; block/mitigation; archetypes: ic_block_body_slam |
| Forgotten Ritual (FORGOTTEN_RITUAL) | 1 | Skill | Uncommon | energy, exhaust | resource acceleration; archetypes: ic_exhaust_engine |
| Infernal Blade (INFERNAL_BLADE) | 1 | Skill | Uncommon | card_generation, energy, exhaust | resource acceleration; card generation/deck manipulation; archetypes: ic_exhaust_engine |
| Rage (RAGE) | 0 | Skill | Uncommon | block, zero_cost | block/mitigation; archetypes: ic_block_body_slam |
| Second Wind (SECOND_WIND) | 1 | Skill | Uncommon | block, exhaust | block/mitigation; archetypes: ic_block_body_slam, ic_exhaust_engine |
| Taunt (TAUNT) | 1 | Skill | Uncommon | block, debuff, vulnerable | block/mitigation; enemy debuff setup; archetypes: ic_block_body_slam, ic_vulnerable_burst |

## silent (88)

| Card | Cost | Type | Rarity | Roles | Use |
| --- | ---: | --- | --- | --- | --- |
| Suppress (SUPPRESS) | 0 | Attack | Ancient | attack, debuff, innate, weak, zero_cost | single-target damage; enemy debuff setup; archetypes: si_defense_control |
| Neutralize (NEUTRALIZE) | 0 | Attack | Basic | attack, debuff, weak, zero_cost | single-target damage; enemy debuff setup; archetypes: si_defense_control |
| Strike (STRIKE_SILENT) | 1 | Attack | Basic | attack | single-target damage |
| Dagger Spray (DAGGER_SPRAY) | 1 | Attack | Common | aoe, attack, multi_hit | damage/AoE |
| Dagger Throw (DAGGER_THROW) | 1 | Attack | Common | attack, discard, draw | single-target damage; draw/cycle; archetypes: si_discard_sly, si_draw_skill_chain |
| Flick-Flack (FLICK_FLACK) | 1 | Attack | Common | aoe, attack, sly | damage/AoE; archetypes: si_discard_sly |
| Follow Through (FOLLOW_THROUGH) | 1 | Attack | Common | attack, multi_hit | single-target damage |
| Leading Strike (LEADING_STRIKE) | 1 | Attack | Common | attack, card_generation, shiv | single-target damage; card generation/deck manipulation; archetypes: si_shiv |
| Poisoned Stab (POISONED_STAB) | 1 | Attack | Common | attack, debuff, poison | single-target damage; enemy debuff setup; archetypes: si_poison |
| Ricochet (RICOCHET) | 2 | Attack | Common | aoe, attack, expensive, multi_hit, random_target, sly | damage/AoE; archetypes: si_discard_sly |
| Slice (SLICE) | 0 | Attack | Common | attack, zero_cost | single-target damage |
| Sucker Punch (SUCKER_PUNCH) | 1 | Attack | Common | attack, debuff, weak | single-target damage; enemy debuff setup; archetypes: si_defense_control |
| Assassinate (ASSASSINATE) | 0 | Attack | Rare | attack, debuff, exhaust, innate, vulnerable, zero_cost | single-target damage; enemy debuff setup |
| Echoing Slash (ECHOING_SLASH) | 1 | Attack | Rare | aoe, attack, multi_hit | damage/AoE |
| Grand Finale (GRAND_FINALE) | 0 | Attack | Rare | aoe, attack, deck_manipulation, zero_cost | damage/AoE |
| Murder (MURDER) | 3 | Attack | Rare | attack, expensive, multi_hit | single-target damage; archetypes: si_draw_skill_chain |
| The Hunt (THE_HUNT) | 1 | Attack | Rare | attack, exhaust, fatal_reward | single-target damage |
| Backstab (BACKSTAB) | 0 | Attack | Uncommon | attack, exhaust, innate, zero_cost | single-target damage |
| Dash (DASH) | 2 | Attack | Uncommon | attack, block, expensive | single-target damage; block/mitigation; archetypes: si_defense_control |
| Finisher (FINISHER) | 1 | Attack | Uncommon | attack, multi_hit | single-target damage; archetypes: si_draw_skill_chain |
| Flechettes (FLECHETTES) | 1 | Attack | Uncommon | attack, multi_hit | single-target damage; archetypes: si_draw_skill_chain |
| Memento Mori (MEMENTO_MORI) | 1 | Attack | Uncommon | attack, discard, multi_hit | single-target damage; archetypes: si_discard_sly |
| Pinpoint (PINPOINT) | 3 | Attack | Uncommon | attack, expensive, multi_hit | single-target damage; archetypes: si_draw_skill_chain |
| Pounce (POUNCE) | 2 | Attack | Uncommon | attack, energy, expensive | single-target damage; resource acceleration |
| Precise Cut (PRECISE_CUT) | 0 | Attack | Uncommon | attack, multi_hit, zero_cost | single-target damage |
| Predator (PREDATOR) | 2 | Attack | Uncommon | attack, draw, expensive | single-target damage; draw/cycle; archetypes: si_draw_skill_chain |
| Skewer (SKEWER) | 0 X | Attack | Uncommon | attack, multi_hit, x_cost, zero_cost | single-target damage |
| Strangle (STRANGLE) | 1 | Attack | Uncommon | attack | single-target damage |
| Wraith Form (WRAITH_FORM) | 3 | Power | Ancient | dexterity, expensive, intangible, power_scaling | persistent scaling engine; archetypes: si_defense_control |
| Abrasive (ABRASIVE) | 3 | Power | Rare | dexterity, expensive, power_scaling, sly | persistent scaling engine; archetypes: si_defense_control, si_discard_sly |
| Accelerant (ACCELERANT) | 1 | Power | Rare | debuff, poison, power_scaling | persistent scaling engine; enemy debuff setup; archetypes: si_poison |
| Afterimage (AFTERIMAGE) | 1 | Power | Rare | block, power_scaling | block/mitigation; persistent scaling engine; archetypes: si_defense_control, si_draw_skill_chain |
| Envenom (ENVENOM) | 2 | Power | Rare | attack, block, debuff, expensive, poison, power_scaling | single-target damage; block/mitigation; persistent scaling engine; enemy debuff setup; archetypes: si_defense_control, si_poison |
| Fan of Knives (FAN_OF_KNIVES) | 2 | Power | Rare | aoe, card_generation, expensive, power_scaling, shiv | persistent scaling engine; card generation/deck manipulation; archetypes: si_shiv |
| Master Planner (MASTER_PLANNER) | 2 | Power | Rare | expensive, power_scaling, sly | persistent scaling engine; archetypes: si_discard_sly |
| Serpent Form (SERPENT_FORM) | 3 | Power | Rare | aoe, attack, card_generation, expensive, power_scaling, random_target | damage/AoE; persistent scaling engine; card generation/deck manipulation |
| Sneaky (SNEAKY) | 2 | Power | Rare | block, coop_only_value, expensive, power_scaling, sly | block/mitigation; persistent scaling engine; archetypes: si_defense_control, si_discard_sly |
| Tools of the Trade (TOOLS_OF_THE_TRADE) | 1 | Power | Rare | discard, draw, power_scaling | draw/cycle; persistent scaling engine; archetypes: si_discard_sly, si_draw_skill_chain |
| Tracking (TRACKING) | 2 | Power | Rare | attack, debuff, expensive, power_scaling, self_damage, weak | single-target damage; persistent scaling engine; enemy debuff setup; self-damage payoff/enabler; needs HP discipline; archetypes: si_defense_control |
| Accuracy (ACCURACY) | 1 | Power | Uncommon | attack, card_generation, power_scaling, shiv | single-target damage; persistent scaling engine; card generation/deck manipulation; archetypes: si_shiv |
| Footwork (FOOTWORK) | 1 | Power | Uncommon | dexterity, power_scaling | persistent scaling engine; archetypes: si_defense_control |
| Infinite Blades (INFINITE_BLADES) | 1 | Power | Uncommon | card_generation, power_scaling, shiv | persistent scaling engine; card generation/deck manipulation; archetypes: si_shiv |
| Noxious Fumes (NOXIOUS_FUMES) | 1 | Power | Uncommon | aoe, debuff, poison, power_scaling | persistent scaling engine; enemy debuff setup; archetypes: si_poison |
| Outbreak (OUTBREAK) | 1 | Power | Uncommon | aoe, attack, debuff, multi_hit, poison, power_scaling | damage/AoE; persistent scaling engine; enemy debuff setup; archetypes: si_poison |
| Phantom Blades (PHANTOM_BLADES) | 1 | Power | Uncommon | attack, card_generation, power_scaling, retain, shiv | single-target damage; persistent scaling engine; card generation/deck manipulation; archetypes: si_shiv |
| Speedster (SPEEDSTER) | 2 | Power | Uncommon | aoe, attack, expensive, power_scaling | damage/AoE; persistent scaling engine; archetypes: si_draw_skill_chain |
| Well-Laid Plans (WELL_LAID_PLANS) | 1 | Power | Uncommon | power_scaling, retain | persistent scaling engine |
| Defend (DEFEND_SILENT) | 1 | Skill | Basic | block | block/mitigation; archetypes: si_defense_control |
| Survivor (SURVIVOR) | 1 | Skill | Basic | block, discard | block/mitigation; archetypes: si_defense_control, si_discard_sly |
| Anticipate (ANTICIPATE) | 0 | Skill | Common | dexterity, zero_cost | archetypes: si_defense_control |
| Backflip (BACKFLIP) | 1 | Skill | Common | block, draw | block/mitigation; draw/cycle; archetypes: si_defense_control, si_draw_skill_chain |
| Blade Dance (BLADE_DANCE) | 1 | Skill | Common | card_generation, draw, exhaust, shiv | draw/cycle; card generation/deck manipulation; archetypes: si_draw_skill_chain, si_shiv |
| Cloak and Dagger (CLOAK_AND_DAGGER) | 1 | Skill | Common | block, card_generation, draw, shiv | block/mitigation; draw/cycle; card generation/deck manipulation; archetypes: si_defense_control, si_draw_skill_chain, si_shiv |
| Deadly Poison (DEADLY_POISON) | 1 | Skill | Common | debuff, poison | enemy debuff setup; archetypes: si_poison |
| Deflect (DEFLECT) | 0 | Skill | Common | block, zero_cost | block/mitigation; archetypes: si_defense_control |
| Dodge and Roll (DODGE_AND_ROLL) | 1 | Skill | Common | block, energy | block/mitigation; resource acceleration; archetypes: si_defense_control |
| Piercing Wail (PIERCING_WAIL) | 1 | Skill | Common | aoe, debuff, exhaust, self_damage, strength | enemy debuff setup; self-damage payoff/enabler; needs HP discipline |
| Prepared (PREPARED) | 0 | Skill | Common | discard, draw, zero_cost | draw/cycle; archetypes: si_discard_sly, si_draw_skill_chain |
| Snakebite (SNAKEBITE) | 2 | Skill | Common | debuff, expensive, poison, retain | enemy debuff setup; archetypes: si_poison |
| Untouchable (UNTOUCHABLE) | 2 | Skill | Common | block, expensive, sly | block/mitigation; archetypes: si_defense_control, si_discard_sly |
| Adrenaline (ADRENALINE) | 0 | Skill | Rare | draw, energy, exhaust, zero_cost | draw/cycle; resource acceleration; archetypes: si_draw_skill_chain |
| Blade of Ink (BLADE_OF_INK) | 1 | Skill | Rare | card_generation, draw, shiv | draw/cycle; card generation/deck manipulation; archetypes: si_draw_skill_chain, si_shiv |
| Bullet Time (BULLET_TIME) | 3 | Skill | Rare | draw, energy, expensive | draw/cycle; resource acceleration; archetypes: si_draw_skill_chain |
| Burst (BURST) | 1 | Skill | Rare |  | archetypes: si_draw_skill_chain |
| Corrosive Wave (CORROSIVE_WAVE) | 1 | Skill | Rare | aoe, debuff, poison | enemy debuff setup; archetypes: si_poison |
| Knife Trap (KNIFE_TRAP) | 2 | Skill | Rare | attack, card_generation, exhaust, expensive, shiv, upgrade_forge | single-target damage; card generation/deck manipulation; archetypes: si_shiv |
| Malaise (MALAISE) | 0 X | Skill | Rare | debuff, exhaust, strength, weak, x_cost, zero_cost | enemy debuff setup; archetypes: si_defense_control |
| Nightmare (NIGHTMARE) | 3 | Skill | Rare | card_generation, exhaust, expensive | card generation/deck manipulation |
| Shadow Step (SHADOW_STEP) | 1 | Skill | Rare | attack, discard, draw | single-target damage; draw/cycle; archetypes: si_discard_sly, si_draw_skill_chain |
| Shadowmeld (SHADOWMELD) | 1 | Skill | Rare | block | block/mitigation; archetypes: si_defense_control |
| Storm of Steel (STORM_OF_STEEL) | 1 | Skill | Rare | card_generation, discard, shiv | card generation/deck manipulation; archetypes: si_discard_sly, si_shiv |
| Acrobatics (ACROBATICS) | 1 | Skill | Uncommon | discard, draw | draw/cycle; archetypes: si_discard_sly, si_draw_skill_chain |
| Blur (BLUR) | 1 | Skill | Uncommon | block, block_retention | block/mitigation; archetypes: si_defense_control |
| Bouncing Flask (BOUNCING_FLASK) | 2 | Skill | Uncommon | aoe, debuff, expensive, poison, random_target | enemy debuff setup; archetypes: si_poison |
| Bubble Bubble (BUBBLE_BUBBLE) | 1 | Skill | Uncommon | debuff, poison | enemy debuff setup; archetypes: si_poison |
| Calculated Gamble (CALCULATED_GAMBLE) | 0 | Skill | Uncommon | discard, exhaust, zero_cost | archetypes: si_discard_sly |
| Escape Plan (ESCAPE_PLAN) | 0 | Skill | Uncommon | block, draw, zero_cost | block/mitigation; draw/cycle; archetypes: si_defense_control, si_draw_skill_chain |
| Expertise (EXPERTISE) | 1 | Skill | Uncommon | draw | draw/cycle; archetypes: si_draw_skill_chain |
| Expose (EXPOSE) | 0 | Skill | Uncommon | block, debuff, exhaust, vulnerable, zero_cost | block/mitigation; enemy debuff setup; archetypes: si_defense_control |
| Flanking (FLANKING) | 2 | Skill | Uncommon | attack, coop_only_value, expensive | single-target damage |
| Hand Trick (HAND_TRICK) | 1 | Skill | Uncommon | block, sly | block/mitigation; archetypes: si_defense_control, si_discard_sly |
| Haze (HAZE) | 3 | Skill | Uncommon | aoe, debuff, expensive, poison, sly | enemy debuff setup; archetypes: si_discard_sly, si_poison |
| Hidden Daggers (HIDDEN_DAGGERS) | 0 | Skill | Uncommon | card_generation, discard, draw, shiv, zero_cost | draw/cycle; card generation/deck manipulation; archetypes: si_discard_sly, si_draw_skill_chain, si_shiv |
| Leg Sweep (LEG_SWEEP) | 2 | Skill | Uncommon | block, debuff, expensive, weak | block/mitigation; enemy debuff setup; archetypes: si_defense_control |
| Mirage (MIRAGE) | 1 | Skill | Uncommon | aoe, attack, block, debuff, exhaust, poison | damage/AoE; block/mitigation; enemy debuff setup; archetypes: si_defense_control, si_poison |
| Reflex (REFLEX) | 3 | Skill | Uncommon | draw, expensive, sly | draw/cycle; archetypes: si_discard_sly, si_draw_skill_chain |
| Tactician (TACTICIAN) | 3 | Skill | Uncommon | energy, expensive, sly | resource acceleration; archetypes: si_discard_sly |
| Up My Sleeve (UP_MY_SLEEVE) | 2 | Skill | Uncommon | card_generation, draw, expensive, shiv | draw/cycle; card generation/deck manipulation; archetypes: si_draw_skill_chain, si_shiv |

## defect (88)

| Card | Cost | Type | Rarity | Roles | Use |
| --- | ---: | --- | --- | --- | --- |
| Strike (STRIKE_DEFECT) | 1 | Attack | Basic | attack | single-target damage |
| Ball Lightning (BALL_LIGHTNING) | 1 | Attack | Common | attack, orb | single-target damage; archetypes: de_orb_focus |
| Barrage (BARRAGE) | 1 | Attack | Common | attack, multi_hit, orb | single-target damage; archetypes: de_orb_focus |
| Beam Cell (BEAM_CELL) | 0 | Attack | Common | attack, debuff, vulnerable, zero_cost | single-target damage; enemy debuff setup; archetypes: de_zero_claw |
| Claw (CLAW) | 0 | Attack | Common | attack, zero_cost | single-target damage; archetypes: de_zero_claw |
| Cold Snap (COLD_SNAP) | 1 | Attack | Common | attack, orb | single-target damage; archetypes: de_frost_defense, de_orb_focus |
| Compile Driver (COMPILE_DRIVER) | 1 | Attack | Common | attack, draw, multi_hit, orb | single-target damage; draw/cycle; archetypes: de_orb_focus |
| Focused Strike (FOCUSED_STRIKE) | 1 | Attack | Common | attack, focus, orb | single-target damage; archetypes: de_orb_focus |
| Go for the Eyes (GO_FOR_THE_EYES) | 0 | Attack | Common | attack, debuff, weak, zero_cost | single-target damage; enemy debuff setup; archetypes: de_zero_claw |
| Gunk Up (GUNK_UP) | 1 | Attack | Common | attack, card_generation, deck_manipulation, discard, multi_hit, status_pollution | single-target damage; card generation/deck manipulation; adds junk/status; draft only with payoff or cleanup; archetypes: de_status_engine |
| Momentum Strike (MOMENTUM_STRIKE) | 1 | Attack | Common | attack | single-target damage; archetypes: de_zero_claw |
| Sweeping Beam (SWEEPING_BEAM) | 1 | Attack | Common | aoe, attack, draw | damage/AoE; draw/cycle |
| Uproar (UPROAR) | 2 | Attack | Common | attack, deck_manipulation, expensive, multi_hit | single-target damage |
| Adaptive Strike (ADAPTIVE_STRIKE) | 2 | Attack | Rare | attack, card_generation, deck_manipulation, discard, expensive | single-target damage; card generation/deck manipulation |
| All for One (ALL_FOR_ONE) | 2 | Attack | Rare | attack, deck_manipulation, discard, expensive | single-target damage; archetypes: de_zero_claw |
| Flak Cannon (FLAK_CANNON) | 2 | Attack | Rare | aoe, attack, card_generation, exhaust, expensive, multi_hit, random_target, status_cleanup | damage/AoE; card generation/deck manipulation; adds junk/status; draft only with payoff or cleanup; archetypes: de_status_engine |
| Helix Drill (HELIX_DRILL) | 0 | Attack | Rare | attack, multi_hit, sly, zero_cost | single-target damage; archetypes: de_zero_claw |
| Hyperbeam (HYPERBEAM) | 2 | Attack | Rare | aoe, attack, expensive, focus, orb | damage/AoE; archetypes: de_orb_focus |
| Ice Lance (ICE_LANCE) | 3 | Attack | Rare | attack, expensive, orb | single-target damage; archetypes: de_frost_defense, de_orb_focus |
| Meteor Strike (METEOR_STRIKE) | 5 | Attack | Rare | attack, expensive, orb | single-target damage; archetypes: de_orb_focus |
| Shatter (SHATTER) | 1 | Attack | Rare | aoe, attack, orb | damage/AoE; archetypes: de_orb_focus |
| FTL (FTL) | 0 | Attack | Uncommon | attack, draw, zero_cost | single-target damage; draw/cycle; archetypes: de_zero_claw |
| Null (NULL) | 2 | Attack | Uncommon | attack, debuff, expensive, orb, weak | single-target damage; enemy debuff setup; archetypes: de_orb_focus |
| Refract (REFRACT) | 3 | Attack | Uncommon | attack, expensive, multi_hit, orb | single-target damage; archetypes: de_orb_focus |
| Rocket Punch (ROCKET_PUNCH) | 2 | Attack | Uncommon | attack, draw, expensive | single-target damage; draw/cycle |
| Scrape (SCRAPE) | 1 | Attack | Uncommon | attack, discard, draw | single-target damage; draw/cycle |
| Sunder (SUNDER) | 3 | Attack | Uncommon | attack, energy, expensive, fatal_reward | single-target damage; resource acceleration |
| Synthesis (SYNTHESIS) | 2 | Attack | Uncommon | attack, energy, expensive | single-target damage; resource acceleration |
| Tesla Coil (TESLA_COIL) | 0 | Attack | Uncommon | attack, orb, zero_cost | single-target damage; archetypes: de_orb_focus, de_zero_claw |
| Biased Cognition (BIASED_COGNITION) | 1 | Power | Ancient | focus, orb, power_scaling | persistent scaling engine; archetypes: de_orb_focus, de_power_engine |
| Buffer (BUFFER) | 2 | Power | Rare | expensive, power_scaling, self_damage | persistent scaling engine; self-damage payoff/enabler; needs HP discipline; archetypes: de_power_engine |
| Consuming Shadow (CONSUMING_SHADOW) | 2 | Power | Rare | expensive, orb, power_scaling | persistent scaling engine; archetypes: de_orb_focus, de_power_engine |
| Coolant (COOLANT) | 1 | Power | Rare | block, orb, power_scaling | block/mitigation; persistent scaling engine; archetypes: de_frost_defense, de_orb_focus, de_power_engine |
| Creative AI (CREATIVE_AI) | 3 | Power | Rare | card_generation, expensive, power_scaling | persistent scaling engine; card generation/deck manipulation; archetypes: de_power_engine |
| Defragment (DEFRAGMENT) | 1 | Power | Rare | focus, orb, power_scaling | persistent scaling engine; archetypes: de_orb_focus, de_power_engine |
| Echo Form (ECHO_FORM) | 3 | Power | Rare | ethereal, expensive, power_scaling | persistent scaling engine; archetypes: de_power_engine |
| Machine Learning (MACHINE_LEARNING) | 1 | Power | Rare | draw, power_scaling | draw/cycle; persistent scaling engine; archetypes: de_power_engine |
| Spinner (SPINNER) | 1 | Power | Rare | orb, power_scaling | persistent scaling engine; archetypes: de_orb_focus, de_power_engine |
| Trash to Treasure (TRASH_TO_TREASURE) | 1 | Power | Rare | orb, power_scaling | persistent scaling engine; archetypes: de_orb_focus, de_power_engine |
| Bulk Up (BULK_UP) | 2 | Power | Uncommon | dexterity, expensive, orb, power_scaling, strength | persistent scaling engine; archetypes: de_orb_focus, de_power_engine |
| Capacitor (CAPACITOR) | 1 | Power | Uncommon | orb, power_scaling | persistent scaling engine; archetypes: de_orb_focus, de_power_engine |
| Feral (FERAL) | 2 | Power | Uncommon | expensive, power_scaling | persistent scaling engine; archetypes: de_power_engine, de_zero_claw |
| Hailstorm (HAILSTORM) | 1 | Power | Uncommon | aoe, attack, orb, power_scaling | damage/AoE; persistent scaling engine; archetypes: de_frost_defense, de_orb_focus, de_power_engine |
| Iteration (ITERATION) | 1 | Power | Uncommon | draw, power_scaling | draw/cycle; persistent scaling engine; archetypes: de_power_engine, de_status_engine |
| Loop (LOOP) | 1 | Power | Uncommon | orb, power_scaling | persistent scaling engine; archetypes: de_orb_focus, de_power_engine |
| Smokestack (SMOKESTACK) | 1 | Power | Uncommon | aoe, attack, power_scaling | damage/AoE; persistent scaling engine; archetypes: de_power_engine |
| Storm (STORM) | 1 | Power | Uncommon | orb, power_scaling | persistent scaling engine; archetypes: de_orb_focus, de_power_engine |
| Subroutine (SUBROUTINE) | 1 | Power | Uncommon | power_scaling | persistent scaling engine; archetypes: de_power_engine |
| Thunder (THUNDER) | 1 | Power | Uncommon | attack, orb, power_scaling | single-target damage; persistent scaling engine; archetypes: de_orb_focus, de_power_engine |
| Quadcast (QUADCAST) | 1 | Skill | Ancient | orb | archetypes: de_orb_focus |
| Defend (DEFEND_DEFECT) | 1 | Skill | Basic | block | block/mitigation |
| Dualcast (DUALCAST) | 1 | Skill | Basic | orb | archetypes: de_orb_focus |
| Zap (ZAP) | 1 | Skill | Basic | orb | archetypes: de_orb_focus |
| Boost Away (BOOST_AWAY) | 0 | Skill | Common | block, card_generation, deck_manipulation, discard, status_pollution, zero_cost | block/mitigation; card generation/deck manipulation; adds junk/status; draft only with payoff or cleanup; archetypes: de_status_engine, de_zero_claw |
| Charge Battery (CHARGE_BATTERY) | 1 | Skill | Common | block, energy | block/mitigation; resource acceleration |
| Coolheaded (COOLHEADED) | 1 | Skill | Common | draw, orb | draw/cycle; archetypes: de_frost_defense, de_orb_focus |
| Hologram (HOLOGRAM) | 1 | Skill | Common | block, deck_manipulation, discard, exhaust | block/mitigation |
| Hotfix (HOTFIX) | 0 | Skill | Common | exhaust, focus, orb, zero_cost | archetypes: de_orb_focus, de_zero_claw |
| Leap (LEAP) | 1 | Skill | Common | block | block/mitigation |
| Lightning Rod (LIGHTNING_ROD) | 1 | Skill | Common | block, orb | block/mitigation; archetypes: de_orb_focus |
| TURBO (TURBO) | 0 | Skill | Common | card_generation, deck_manipulation, discard, energy, zero_cost | resource acceleration; card generation/deck manipulation; archetypes: de_zero_claw |
| Genetic Algorithm (GENETIC_ALGORITHM) | 1 | Skill | Rare | block, exhaust | block/mitigation |
| Ignition (IGNITION) | 1 | Skill | Rare | coop_only_value, exhaust, orb | archetypes: de_orb_focus |
| Modded (MODDED) | 0 | Skill | Rare | draw, orb, zero_cost | draw/cycle; archetypes: de_orb_focus, de_zero_claw |
| Multi-Cast (MULTI_CAST) | 0 X | Skill | Rare | orb, x_cost, zero_cost | archetypes: de_orb_focus, de_zero_claw |
| Rainbow (RAINBOW) | 2 | Skill | Rare | exhaust, expensive, orb | archetypes: de_orb_focus |
| Reboot (REBOOT) | 0 | Skill | Rare | deck_manipulation, draw, exhaust, zero_cost | draw/cycle; archetypes: de_zero_claw |
| Signal Boost (SIGNAL_BOOST) | 1 | Skill | Rare | exhaust | utility card; inspect exact text before drafting |
| Supercritical (SUPERCRITICAL) | 0 | Skill | Rare | energy, exhaust, zero_cost | resource acceleration; archetypes: de_zero_claw |
| Voltaic (VOLTAIC) | 3 | Skill | Rare | attack, exhaust, expensive, orb | single-target damage; archetypes: de_orb_focus |
| Boot Sequence (BOOT_SEQUENCE) | 0 | Skill | Uncommon | block, exhaust, innate, zero_cost | block/mitigation; archetypes: de_zero_claw |
| Chaos (CHAOS) | 1 | Skill | Uncommon | orb | archetypes: de_orb_focus |
| Chill (CHILL) | 0 | Skill | Uncommon | exhaust, orb, zero_cost | archetypes: de_frost_defense, de_orb_focus, de_zero_claw |
| Compact (COMPACT) | 1 | Skill | Uncommon | block, card_generation, deck_manipulation, status_cleanup, status_pollution | block/mitigation; card generation/deck manipulation; adds junk/status; draft only with payoff or cleanup; archetypes: de_status_engine |
| Darkness (DARKNESS) | 1 | Skill | Uncommon | orb | archetypes: de_orb_focus |
| Double Energy (DOUBLE_ENERGY) | 1 | Skill | Uncommon | energy, exhaust | resource acceleration |
| Energy Surge (ENERGY_SURGE) | 1 | Skill | Uncommon | coop_only_value, energy, exhaust | resource acceleration |
| Fight Through (FIGHT_THROUGH) | 1 | Skill | Uncommon | block, card_generation, deck_manipulation, discard, status_pollution | block/mitigation; card generation/deck manipulation; adds junk/status; draft only with payoff or cleanup; archetypes: de_status_engine |
| Fusion (FUSION) | 2 | Skill | Uncommon | expensive, orb | archetypes: de_orb_focus |
| Glacier (GLACIER) | 2 | Skill | Uncommon | block, expensive, orb | block/mitigation; archetypes: de_frost_defense, de_orb_focus |
| Glasswork (GLASSWORK) | 1 | Skill | Uncommon | block, orb | block/mitigation; archetypes: de_frost_defense, de_orb_focus |
| Overclock (OVERCLOCK) | 0 | Skill | Uncommon | card_generation, deck_manipulation, discard, draw, status_pollution, zero_cost | draw/cycle; card generation/deck manipulation; adds junk/status; draft only with payoff or cleanup; archetypes: de_status_engine, de_zero_claw |
| Scavenge (SCAVENGE) | 1 | Skill | Uncommon | energy, exhaust | resource acceleration |
| Shadow Shield (SHADOW_SHIELD) | 2 | Skill | Uncommon | block, expensive, orb | block/mitigation; archetypes: de_orb_focus |
| Skim (SKIM) | 1 | Skill | Uncommon | draw | draw/cycle |
| Synchronize (SYNCHRONIZE) | 1 | Skill | Uncommon | attack, exhaust, focus, orb | single-target damage; archetypes: de_orb_focus |
| Tempest (TEMPEST) | 0 X | Skill | Uncommon | orb, x_cost, zero_cost | archetypes: de_orb_focus, de_zero_claw |
| White Noise (WHITE_NOISE) | 1 | Skill | Uncommon | card_generation, energy, exhaust | resource acceleration; card generation/deck manipulation |

## necrobinder (88)

| Card | Cost | Type | Rarity | Roles | Use |
| --- | ---: | --- | --- | --- | --- |
| Protector (PROTECTOR) | 1 | Attack | Ancient | attack, max_hp, summon_osty | single-target damage; archetypes: nb_osty_summon |
| Strike (STRIKE_NECROBINDER) | 1 | Attack | Basic | attack | single-target damage |
| Unleash (UNLEASH) | 1 | Attack | Basic | attack, summon_osty | single-target damage; archetypes: nb_osty_summon |
| Blight Strike (BLIGHT_STRIKE) | 1 | Attack | Common | attack, debuff, doom | single-target damage; enemy debuff setup; archetypes: nb_doom |
| Defile (DEFILE) | 1 | Attack | Common | attack, ethereal | single-target damage; archetypes: nb_ethereal_soul |
| Drain Power (DRAIN_POWER) | 1 | Attack | Common | attack, card_generation, deck_manipulation, discard, draw, upgrade_forge | single-target damage; draw/cycle; card generation/deck manipulation |
| Fear (FEAR) | 1 | Attack | Common | attack, debuff, ethereal, vulnerable | single-target damage; enemy debuff setup; archetypes: nb_debuff_control, nb_ethereal_soul |
| Flatten (FLATTEN) | 2 | Attack | Common | attack, energy, expensive, summon_osty | single-target damage; resource acceleration; archetypes: nb_osty_summon |
| Graveblast (GRAVEBLAST) | 1 | Attack | Common | attack, deck_manipulation, discard, exhaust | single-target damage |
| Poke (POKE) | 0 | Attack | Common | attack, summon_osty, zero_cost | single-target damage; archetypes: nb_osty_summon |
| Reap (REAP) | 3 | Attack | Common | attack, expensive, retain | single-target damage |
| Reave (REAVE) | 1 | Attack | Common | attack, card_generation, deck_manipulation, draw, summon_osty | single-target damage; draw/cycle; card generation/deck manipulation; archetypes: nb_osty_summon |
| Sculpting Strike (SCULPTING_STRIKE) | 1 | Attack | Common | attack, ethereal | single-target damage; archetypes: nb_ethereal_soul |
| Snap (SNAP) | 1 | Attack | Common | attack, retain, summon_osty | single-target damage; archetypes: nb_osty_summon |
| Sow (SOW) | 1 | Attack | Common | aoe, attack, retain | damage/AoE |
| Banshee's Cry (BANSHEES_CRY) | 9 | Attack | Rare | aoe, attack, energy, ethereal, expensive, multi_hit | damage/AoE; resource acceleration; archetypes: nb_ethereal_soul |
| Eradicate (ERADICATE) | 0 X | Attack | Rare | attack, multi_hit, retain, x_cost, zero_cost | single-target damage |
| Hang (HANG) | 1 | Attack | Rare | attack | single-target damage |
| Misery (MISERY) | 0 | Attack | Rare | attack, debuff, zero_cost | single-target damage; enemy debuff setup; archetypes: nb_debuff_control |
| Soul Storm (SOUL_STORM) | 1 | Attack | Rare | attack, card_generation, exhaust, multi_hit, summon_osty | single-target damage; card generation/deck manipulation; archetypes: nb_ethereal_soul, nb_osty_summon |
| Squeeze (SQUEEZE) | 3 | Attack | Rare | attack, expensive, summon_osty | single-target damage; archetypes: nb_osty_summon |
| The Scythe (THE_SCYTHE) | 2 | Attack | Rare | attack, exhaust, expensive | single-target damage |
| Time's Up (TIMES_UP) | 2 | Attack | Rare | attack, debuff, doom, exhaust, expensive | single-target damage; enemy debuff setup; archetypes: nb_doom |
| Bone Shards (BONE_SHARDS) | 1 | Attack | Uncommon | aoe, attack, block, summon_osty | damage/AoE; block/mitigation; archetypes: nb_osty_summon |
| Bury (BURY) | 4 | Attack | Uncommon | attack, expensive | single-target damage |
| Death March (DEATH_MARCH) | 1 | Attack | Uncommon | attack, multi_hit | single-target damage |
| Debilitate (DEBILITATE) | 1 | Attack | Uncommon | attack, debuff, multi_hit, vulnerable, weak | single-target damage; enemy debuff setup; archetypes: nb_debuff_control |
| Fetch (FETCH) | 0 | Attack | Uncommon | attack, draw, summon_osty, zero_cost | single-target damage; draw/cycle; archetypes: nb_osty_summon |
| High Five (HIGH_FIVE) | 2 | Attack | Uncommon | aoe, attack, debuff, expensive, summon_osty, vulnerable | damage/AoE; enemy debuff setup; archetypes: nb_debuff_control, nb_osty_summon |
| Pull from Below (PULL_FROM_BELOW) | 1 | Attack | Uncommon | attack, ethereal, multi_hit | single-target damage; archetypes: nb_ethereal_soul |
| Rattle (RATTLE) | 1 | Attack | Uncommon | attack, multi_hit, summon_osty | single-target damage; archetypes: nb_osty_summon |
| Right Hand Hand (RIGHT_HAND_HAND) | 0 | Attack | Uncommon | attack, deck_manipulation, discard, energy, summon_osty, zero_cost | single-target damage; resource acceleration; archetypes: nb_osty_summon |
| Severance (SEVERANCE) | 2 | Attack | Uncommon | attack, card_generation, deck_manipulation, discard, expensive, summon_osty | single-target damage; card generation/deck manipulation; archetypes: nb_osty_summon |
| Sic 'Em (SIC_EM) | 1 | Attack | Uncommon | attack, multi_hit, summon_osty | single-target damage; archetypes: nb_osty_summon |
| Veilpiercer (VEILPIERCER) | 1 | Attack | Uncommon | attack, energy, ethereal | single-target damage; resource acceleration; archetypes: nb_ethereal_soul |
| Forbidden Grimoire (FORBIDDEN_GRIMOIRE) | 2 | Power | Ancient | expensive, power_scaling | persistent scaling engine |
| Call of the Void (CALL_OF_THE_VOID) | 1 | Power | Rare | card_generation, draw, ethereal, power_scaling | draw/cycle; persistent scaling engine; card generation/deck manipulation; archetypes: nb_ethereal_soul |
| Demesne (DEMESNE) | 3 | Power | Rare | draw, energy, ethereal, expensive, power_scaling | draw/cycle; resource acceleration; persistent scaling engine; archetypes: nb_ethereal_soul |
| Devour Life (DEVOUR_LIFE) | 1 | Power | Rare | card_generation, power_scaling, summon_osty | persistent scaling engine; card generation/deck manipulation; archetypes: nb_osty_summon |
| Necro Mastery (NECRO_MASTERY) | 2 | Power | Rare | aoe, expensive, power_scaling, summon_osty | persistent scaling engine; archetypes: nb_osty_summon |
| Neurosurge (NEUROSURGE) | 0 | Power | Rare | debuff, doom, draw, energy, power_scaling, zero_cost | draw/cycle; resource acceleration; persistent scaling engine; enemy debuff setup; archetypes: nb_doom |
| Reaper Form (REAPER_FORM) | 3 | Power | Rare | attack, debuff, doom, expensive, power_scaling | single-target damage; persistent scaling engine; enemy debuff setup; archetypes: nb_doom |
| Sentry Mode (SENTRY_MODE) | 2 | Power | Rare | card_generation, expensive, power_scaling | persistent scaling engine; card generation/deck manipulation |
| Spirit of Ash (SPIRIT_OF_ASH) | 1 | Power | Rare | block, ethereal, power_scaling | block/mitigation; persistent scaling engine; archetypes: nb_ethereal_soul |
| Calcify (CALCIFY) | 1 | Power | Uncommon | attack, power_scaling, summon_osty | single-target damage; persistent scaling engine; archetypes: nb_osty_summon |
| Countdown (COUNTDOWN) | 1 | Power | Uncommon | aoe, debuff, doom, power_scaling, random_target | persistent scaling engine; enemy debuff setup; archetypes: nb_doom |
| Danse Macabre (DANSE_MACABRE) | 1 | Power | Uncommon | block, energy, power_scaling | block/mitigation; resource acceleration; persistent scaling engine |
| Friendship (FRIENDSHIP) | 1 | Power | Uncommon | debuff, energy, power_scaling, self_damage, strength | resource acceleration; persistent scaling engine; enemy debuff setup; self-damage payoff/enabler; needs HP discipline |
| Haunt (HAUNT) | 1 | Power | Uncommon | aoe, card_generation, power_scaling, random_target, self_damage, summon_osty | persistent scaling engine; card generation/deck manipulation; self-damage payoff/enabler; needs HP discipline; archetypes: nb_osty_summon |
| Lethality (LETHALITY) | 1 | Power | Uncommon | attack, ethereal, power_scaling | single-target damage; persistent scaling engine; archetypes: nb_ethereal_soul |
| Pagestorm (PAGESTORM) | 1 | Power | Uncommon | draw, ethereal, power_scaling | draw/cycle; persistent scaling engine; archetypes: nb_ethereal_soul |
| Shroud (SHROUD) | 1 | Power | Uncommon | block, debuff, doom, power_scaling | block/mitigation; persistent scaling engine; enemy debuff setup; archetypes: nb_doom |
| Sleight of Flesh (SLEIGHT_OF_FLESH) | 2 | Power | Uncommon | attack, debuff, expensive, power_scaling | single-target damage; persistent scaling engine; enemy debuff setup; archetypes: nb_debuff_control |
| Bodyguard (BODYGUARD) | 1 | Skill | Basic | summon_osty | archetypes: nb_osty_summon |
| Defend (DEFEND_NECROBINDER) | 1 | Skill | Basic | block | block/mitigation |
| Afterlife (AFTERLIFE) | 1 | Skill | Common | exhaust, summon_osty | archetypes: nb_osty_summon |
| Defy (DEFY) | 1 | Skill | Common | block, debuff, ethereal, weak | block/mitigation; enemy debuff setup; archetypes: nb_debuff_control, nb_ethereal_soul |
| Grave Warden (GRAVE_WARDEN) | 1 | Skill | Common | block, card_generation, deck_manipulation, draw, summon_osty | block/mitigation; draw/cycle; card generation/deck manipulation; archetypes: nb_osty_summon |
| Invoke (INVOKE) | 1 | Skill | Common | energy, summon_osty | resource acceleration; archetypes: nb_osty_summon |
| Negative Pulse (NEGATIVE_PULSE) | 1 | Skill | Common | aoe, block, debuff, doom | block/mitigation; enemy debuff setup; archetypes: nb_doom |
| Pull Aggro (PULL_AGGRO) | 2 | Skill | Common | block, expensive, summon_osty | block/mitigation; archetypes: nb_osty_summon |
| Scourge (SCOURGE) | 1 | Skill | Common | debuff, doom, draw | draw/cycle; enemy debuff setup; archetypes: nb_doom |
| Wisp (WISP) | 0 | Skill | Common | energy, exhaust, zero_cost | resource acceleration |
| Eidolon (EIDOLON) | 2 | Skill | Rare | exhaust, expensive, intangible | utility card; inspect exact text before drafting |
| End of Days (END_OF_DAYS) | 3 | Skill | Rare | aoe, debuff, doom, expensive | enemy debuff setup; archetypes: nb_doom |
| Glimpse Beyond (GLIMPSE_BEYOND) | 1 | Skill | Rare | card_generation, coop_only_value, deck_manipulation, draw, exhaust, summon_osty | draw/cycle; card generation/deck manipulation; archetypes: nb_ethereal_soul, nb_osty_summon |
| Oblivion (OBLIVION) | 0 | Skill | Rare | debuff, doom, zero_cost | enemy debuff setup; archetypes: nb_doom |
| Reanimate (REANIMATE) | 3 | Skill | Rare | exhaust, expensive, summon_osty | archetypes: nb_osty_summon |
| Sacrifice (SACRIFICE) | 1 | Skill | Rare | block, max_hp, retain, summon_osty | block/mitigation; archetypes: nb_osty_summon |
| Seance (SEANCE) | 1 | Skill | Rare | card_generation, deck_manipulation, draw, ethereal, summon_osty | draw/cycle; card generation/deck manipulation; archetypes: nb_ethereal_soul, nb_osty_summon |
| Shared Fate (SHARED_FATE) | 0 | Skill | Rare | debuff, exhaust, self_damage, strength, zero_cost | enemy debuff setup; self-damage payoff/enabler; needs HP discipline; archetypes: nb_debuff_control |
| Transfigure (TRANSFIGURE) | 1 | Skill | Rare | deck_manipulation, energy, exhaust | resource acceleration |
| Undeath (UNDEATH) | 0 | Skill | Rare | block, card_generation, deck_manipulation, discard, zero_cost | block/mitigation; card generation/deck manipulation |
| Borrowed Time (BORROWED_TIME) | 1 | Skill | Uncommon | energy | resource acceleration |
| Capture Spirit (CAPTURE_SPIRIT) | 1 | Skill | Uncommon | attack, card_generation, deck_manipulation, draw, summon_osty | single-target damage; draw/cycle; card generation/deck manipulation; archetypes: nb_osty_summon |
| Cleanse (CLEANSE) | 1 | Skill | Uncommon | deck_manipulation, exhaust, summon_osty | archetypes: nb_osty_summon |
| Death's Door (DEATHS_DOOR) | 1 | Skill | Uncommon | block, debuff, doom | block/mitigation; enemy debuff setup; archetypes: nb_doom |
| Deathbringer (DEATHBRINGER) | 2 | Skill | Uncommon | aoe, debuff, doom, expensive, weak | enemy debuff setup; archetypes: nb_debuff_control, nb_doom |
| Delay (DELAY) | 2 | Skill | Uncommon | block, energy, expensive | block/mitigation; resource acceleration |
| Dirge (DIRGE) | 0 X | Skill | Uncommon | card_generation, deck_manipulation, exhaust, summon_osty, x_cost, zero_cost | card generation/deck manipulation; archetypes: nb_osty_summon |
| Dredge (DREDGE) | 1 | Skill | Uncommon | deck_manipulation, discard, draw, exhaust | draw/cycle |
| Enfeebling Touch (ENFEEBLING_TOUCH) | 1 | Skill | Uncommon | debuff, ethereal, strength | enemy debuff setup; archetypes: nb_debuff_control, nb_ethereal_soul |
| Legion of Bone (LEGION_OF_BONE) | 2 | Skill | Uncommon | coop_only_value, exhaust, expensive, summon_osty | archetypes: nb_osty_summon |
| Melancholy (MELANCHOLY) | 3 | Skill | Uncommon | block, energy, expensive | block/mitigation; resource acceleration |
| No Escape (NO_ESCAPE) | 1 | Skill | Uncommon | attack, debuff, doom | single-target damage; enemy debuff setup; archetypes: nb_doom |
| Parse (PARSE) | 1 | Skill | Uncommon | draw, ethereal | draw/cycle; archetypes: nb_ethereal_soul |
| Putrefy (PUTREFY) | 1 | Skill | Uncommon | debuff, exhaust, vulnerable, weak | enemy debuff setup; archetypes: nb_debuff_control |
| Spur (SPUR) | 1 | Skill | Uncommon | heal, retain, summon_osty | archetypes: nb_osty_summon |

## regent (88)

| Card | Cost | Type | Rarity | Roles | Use |
| --- | ---: | --- | --- | --- | --- |
| Meteor Shower (METEOR_SHOWER) | 0/2* | Attack | Ancient | aoe, attack, debuff, star_resource, vulnerable, weak, zero_cost | damage/AoE; resource acceleration; enemy debuff setup; archetypes: rg_star_resource, rg_strength_control |
| Falling Star (FALLING_STAR) | 0/2* | Attack | Basic | attack, debuff, star_resource, vulnerable, weak, zero_cost | single-target damage; resource acceleration; enemy debuff setup; archetypes: rg_star_resource, rg_strength_control |
| Strike (STRIKE_REGENT) | 1 | Attack | Basic | attack | single-target damage |
| Astral Pulse (ASTRAL_PULSE) | 0/3* | Attack | Common | aoe, attack, expensive, star_resource, zero_cost | damage/AoE; resource acceleration; archetypes: rg_star_resource |
| Celestial Might (CELESTIAL_MIGHT) | 2 | Attack | Common | attack, expensive, multi_hit | single-target damage |
| Collision Course (COLLISION_COURSE) | 0 | Attack | Common | attack, card_generation, status_pollution, zero_cost | single-target damage; card generation/deck manipulation; adds junk/status; draft only with payoff or cleanup; archetypes: rg_created_cards |
| Crescent Spear (CRESCENT_SPEAR) | 1/1* | Attack | Common | attack, star_resource | single-target damage; resource acceleration; archetypes: rg_star_resource |
| Crush Under (CRUSH_UNDER) | 1 | Attack | Common | aoe, attack, debuff, self_damage, strength | damage/AoE; enemy debuff setup; self-damage payoff/enabler; needs HP discipline; archetypes: rg_strength_control |
| Guiding Star (GUIDING_STAR) | 1/2* | Attack | Common | attack, draw, star_resource | single-target damage; draw/cycle; resource acceleration; archetypes: rg_star_resource |
| Photon Cut (PHOTON_CUT) | 1 | Attack | Common | attack, deck_manipulation, draw | single-target damage; draw/cycle; archetypes: rg_skill_chain |
| Solar Strike (SOLAR_STRIKE) | 1 | Attack | Common | attack, star_resource | single-target damage; resource acceleration; archetypes: rg_star_resource |
| Wrought in War (WROUGHT_IN_WAR) | 1 | Attack | Common | attack, upgrade_forge | single-target damage; archetypes: rg_forge_blade |
| Beat into Shape (BEAT_INTO_SHAPE) | 1 | Attack | Rare | attack, upgrade_forge, x_cost | single-target damage; archetypes: rg_forge_blade |
| Bombardment (BOMBARDMENT) | 3 | Attack | Rare | attack, exhaust, expensive, star_resource | single-target damage; resource acceleration; archetypes: rg_star_resource |
| Comet (COMET) | 0/5* | Attack | Rare | attack, debuff, expensive, star_resource, vulnerable, weak, zero_cost | single-target damage; resource acceleration; enemy debuff setup; archetypes: rg_star_resource, rg_strength_control |
| Crash Landing (CRASH_LANDING) | 1 | Attack | Rare | aoe, attack, card_generation, status_pollution | damage/AoE; card generation/deck manipulation; adds junk/status; draft only with payoff or cleanup; archetypes: rg_created_cards |
| Dying Star (DYING_STAR) | 1/3* | Attack | Rare | aoe, attack, debuff, ethereal, expensive, self_damage, star_resource, strength | damage/AoE; resource acceleration; enemy debuff setup; self-damage payoff/enabler; needs HP discipline; archetypes: rg_star_resource, rg_strength_control |
| Heavenly Drill (HEAVENLY_DRILL) | 0 X | Attack | Rare | attack, energy, multi_hit, x_cost, zero_cost | single-target damage; resource acceleration |
| Heirloom Hammer (HEIRLOOM_HAMMER) | 2 | Attack | Rare | attack, card_generation, colorless_creation, expensive | single-target damage; card generation/deck manipulation; archetypes: rg_created_cards |
| Make It So (MAKE_IT_SO) | 0 | Attack | Rare | attack, deck_manipulation, draw, zero_cost | single-target damage; draw/cycle; archetypes: rg_skill_chain |
| Seven Stars (SEVEN_STARS) | 2/7* | Attack | Rare | aoe, attack, expensive, multi_hit, star_resource | damage/AoE; resource acceleration; archetypes: rg_star_resource |
| Devastate (DEVASTATE) | 1/4* | Attack | Uncommon | attack, expensive, star_resource | single-target damage; resource acceleration; archetypes: rg_star_resource |
| Gamma Blast (GAMMA_BLAST) | 0/3* | Attack | Uncommon | attack, debuff, expensive, star_resource, vulnerable, weak, zero_cost | single-target damage; resource acceleration; enemy debuff setup; archetypes: rg_star_resource, rg_strength_control |
| Hegemony (HEGEMONY) | 2 | Attack | Uncommon | attack, energy, expensive, star_resource | single-target damage; resource acceleration; archetypes: rg_star_resource |
| Kingly Kick (KINGLY_KICK) | 4 | Attack | Uncommon | attack, expensive | single-target damage |
| Kingly Punch (KINGLY_PUNCH) | 1 | Attack | Uncommon | attack | single-target damage |
| Knockout Blow (KNOCKOUT_BLOW) | 3 | Attack | Uncommon | attack, expensive, fatal_reward, star_resource | single-target damage; resource acceleration; archetypes: rg_star_resource |
| Lunar Blast (LUNAR_BLAST) | 0 | Attack | Uncommon | attack, multi_hit, zero_cost | single-target damage; archetypes: rg_skill_chain |
| Radiate (RADIATE) | 0 | Attack | Uncommon | aoe, attack, multi_hit, star_resource, zero_cost | damage/AoE; resource acceleration; archetypes: rg_star_resource |
| Shining Strike (SHINING_STRIKE) | 1 | Attack | Uncommon | attack, deck_manipulation, star_resource | single-target damage; resource acceleration; archetypes: rg_star_resource |
| Stardust (STARDUST) | 0 X* | Attack | Uncommon | aoe, attack, multi_hit, random_target, star_resource, x_cost, zero_cost | damage/AoE; resource acceleration; archetypes: rg_star_resource |
| Supermassive (SUPERMASSIVE) | 1 | Attack | Uncommon | attack, multi_hit | single-target damage; archetypes: rg_created_cards |
| The Sealed Throne (THE_SEALED_THRONE) | 1/3* | Power | Ancient | expensive, power_scaling, star_resource | resource acceleration; persistent scaling engine; archetypes: rg_star_resource |
| Arsenal (ARSENAL) | 1 | Power | Rare | card_generation, power_scaling, star_resource, strength | resource acceleration; persistent scaling engine; card generation/deck manipulation; archetypes: rg_created_cards, rg_star_resource, rg_strength_control |
| Genesis (GENESIS) | 2 | Power | Rare | expensive, power_scaling, star_resource | resource acceleration; persistent scaling engine; archetypes: rg_star_resource |
| Hammer Time (HAMMER_TIME) | 2 | Power | Rare | coop_only_value, expensive, power_scaling, upgrade_forge | persistent scaling engine; archetypes: rg_forge_blade |
| Monarch's Gaze (MONARCHS_GAZE) | 3 | Power | Rare | debuff, expensive, power_scaling, strength | persistent scaling engine; enemy debuff setup; archetypes: rg_strength_control |
| Neutron Aegis (NEUTRON_AEGIS) | 1/5* | Power | Rare | expensive, plating, power_scaling, star_resource | resource acceleration; persistent scaling engine; archetypes: rg_star_resource |
| Royalties (ROYALTIES) | 1 | Power | Rare | gold, power_scaling, star_resource | resource acceleration; persistent scaling engine; archetypes: rg_star_resource |
| Seeking Edge (SEEKING_EDGE) | 1 | Power | Rare | aoe, attack, power_scaling, sovereign_blade, upgrade_forge | damage/AoE; persistent scaling engine; archetypes: rg_forge_blade |
| Sword Sage (SWORD_SAGE) | 2 | Power | Rare | card_generation, expensive, power_scaling, sovereign_blade | persistent scaling engine; card generation/deck manipulation; archetypes: rg_created_cards, rg_forge_blade |
| Tyranny (TYRANNY) | 1 | Power | Rare | draw, exhaust, power_scaling, star_resource | draw/cycle; resource acceleration; persistent scaling engine; archetypes: rg_star_resource |
| Void Form (VOID_FORM) | 3 | Power | Rare | energy, ethereal, expensive, power_scaling | resource acceleration; persistent scaling engine |
| Black Hole (BLACK_HOLE) | 1 | Power | Uncommon | aoe, attack, power_scaling, star_resource | damage/AoE; resource acceleration; persistent scaling engine; archetypes: rg_star_resource |
| Child of the Stars (CHILD_OF_THE_STARS) | 1 | Power | Uncommon | block, power_scaling, star_resource | block/mitigation; resource acceleration; persistent scaling engine; archetypes: rg_star_resource |
| Furnace (FURNACE) | 1 | Power | Uncommon | power_scaling, star_resource, upgrade_forge | resource acceleration; persistent scaling engine; archetypes: rg_forge_blade, rg_star_resource |
| Orbit (ORBIT) | 2 | Power | Uncommon | energy, expensive, power_scaling, star_resource | resource acceleration; persistent scaling engine; archetypes: rg_star_resource |
| Pale Blue Dot (PALE_BLUE_DOT) | 1 | Power | Uncommon | draw, power_scaling, star_resource | draw/cycle; resource acceleration; persistent scaling engine; archetypes: rg_skill_chain, rg_star_resource |
| Parry (PARRY) | 1 | Power | Uncommon | block, card_generation, power_scaling, sovereign_blade, star_resource | block/mitigation; resource acceleration; persistent scaling engine; card generation/deck manipulation; archetypes: rg_created_cards, rg_forge_blade, rg_star_resource |
| Pillar of Creation (PILLAR_OF_CREATION) | 1 | Power | Uncommon | block, card_generation, power_scaling, star_resource | block/mitigation; resource acceleration; persistent scaling engine; card generation/deck manipulation; archetypes: rg_created_cards, rg_star_resource |
| Spectrum Shift (SPECTRUM_SHIFT) | 2 | Power | Uncommon | card_generation, colorless_creation, draw, expensive, power_scaling, star_resource | draw/cycle; resource acceleration; persistent scaling engine; card generation/deck manipulation; archetypes: rg_created_cards, rg_star_resource |
| Defend (DEFEND_REGENT) | 1 | Skill | Basic | block, star_resource | block/mitigation; resource acceleration; archetypes: rg_star_resource |
| Venerate (VENERATE) | 1 | Skill | Basic | star_resource | resource acceleration; archetypes: rg_star_resource |
| BEGONE! (BEGONE) | 1 | Skill | Common | card_generation, deck_manipulation | card generation/deck manipulation; archetypes: rg_created_cards |
| Cloak of Stars (CLOAK_OF_STARS) | 0/1* | Skill | Common | block, star_resource, zero_cost | block/mitigation; resource acceleration; archetypes: rg_star_resource |
| Cosmic Indifference (COSMIC_INDIFFERENCE) | 1 | Skill | Common | block, deck_manipulation, discard, star_resource | block/mitigation; resource acceleration; archetypes: rg_star_resource |
| Gather Light (GATHER_LIGHT) | 1 | Skill | Common | block, star_resource | block/mitigation; resource acceleration; archetypes: rg_star_resource |
| Glitterstream (GLITTERSTREAM) | 2 | Skill | Common | block, energy, expensive, star_resource | block/mitigation; resource acceleration; archetypes: rg_star_resource |
| Glow (GLOW) | 1 | Skill | Common | draw, star_resource | draw/cycle; resource acceleration; archetypes: rg_star_resource |
| Hidden Cache (HIDDEN_CACHE) | 1 | Skill | Common | energy, star_resource | resource acceleration; archetypes: rg_star_resource |
| Know Thy Place (KNOW_THY_PLACE) | 0 | Skill | Common | debuff, exhaust, vulnerable, weak, zero_cost | enemy debuff setup; archetypes: rg_strength_control |
| Patter (PATTER) | 1 | Skill | Common | block, star_resource | block/mitigation; resource acceleration; archetypes: rg_star_resource, rg_strength_control |
| Refine Blade (REFINE_BLADE) | 1 | Skill | Common | energy, star_resource, upgrade_forge | resource acceleration; archetypes: rg_forge_blade, rg_star_resource |
| Spoils of Battle (SPOILS_OF_BATTLE) | 1 | Skill | Common | draw, upgrade_forge | draw/cycle; archetypes: rg_forge_blade |
| Big Bang (BIG_BANG) | 0 | Skill | Rare | draw, energy, exhaust, star_resource, upgrade_forge, zero_cost | draw/cycle; resource acceleration; archetypes: rg_forge_blade, rg_star_resource |
| Bundle of Joy (BUNDLE_OF_JOY) | 1 | Skill | Rare | card_generation, colorless_creation, draw, exhaust | draw/cycle; card generation/deck manipulation; archetypes: rg_created_cards |
| Decisions, Decisions (DECISIONS_DECISIONS) | 0/6* | Skill | Rare | draw, exhaust, expensive, star_resource, zero_cost | draw/cycle; resource acceleration; archetypes: rg_skill_chain, rg_star_resource |
| Foregone Conclusion (FOREGONE_CONCLUSION) | 1 | Skill | Rare | deck_manipulation, draw | draw/cycle |
| GUARDS!!! (GUARDS) | 2 | Skill | Rare | card_generation, deck_manipulation, exhaust, expensive | card generation/deck manipulation; archetypes: rg_created_cards |
| I Am Invincible (I_AM_INVINCIBLE) | 1 | Skill | Rare | block, deck_manipulation, star_resource | block/mitigation; resource acceleration; archetypes: rg_star_resource |
| The Smith (THE_SMITH) | 1/4* | Skill | Rare | expensive, star_resource, upgrade_forge | resource acceleration; archetypes: rg_forge_blade, rg_star_resource |
| Alignment (ALIGNMENT) | 0/3* | Skill | Uncommon | energy, expensive, star_resource, zero_cost | resource acceleration; archetypes: rg_star_resource |
| Bulwark (BULWARK) | 2 | Skill | Uncommon | block, expensive, star_resource, upgrade_forge | block/mitigation; resource acceleration; archetypes: rg_forge_blade, rg_star_resource |
| CHARGE!! (CHARGE) | 1 | Skill | Uncommon | card_generation, deck_manipulation, draw | draw/cycle; card generation/deck manipulation; archetypes: rg_created_cards |
| Conqueror (CONQUEROR) | 1 | Skill | Uncommon | attack, sovereign_blade, upgrade_forge | single-target damage; archetypes: rg_forge_blade |
| Convergence (CONVERGENCE) | 1 | Skill | Uncommon | block_retention, deck_manipulation, energy, retain, star_resource | resource acceleration; archetypes: rg_star_resource |
| Glimmer (GLIMMER) | 1 | Skill | Uncommon | deck_manipulation, draw | draw/cycle; archetypes: rg_skill_chain |
| Largesse (LARGESSE) | 0 | Skill | Uncommon | card_generation, colorless_creation, coop_only_value, upgrade_forge, zero_cost | card generation/deck manipulation; archetypes: rg_created_cards, rg_forge_blade |
| Manifest Authority (MANIFEST_AUTHORITY) | 1 | Skill | Uncommon | block, card_generation, colorless_creation, star_resource, upgrade_forge | block/mitigation; resource acceleration; card generation/deck manipulation; archetypes: rg_created_cards, rg_forge_blade, rg_star_resource |
| Monologue (MONOLOGUE) | 0 | Skill | Uncommon | star_resource, strength, zero_cost | resource acceleration; archetypes: rg_skill_chain, rg_star_resource, rg_strength_control |
| Particle Wall (PARTICLE_WALL) | 0/2* | Skill | Uncommon | block, star_resource, zero_cost | block/mitigation; resource acceleration; archetypes: rg_star_resource |
| Prophesize (PROPHESIZE) | 2 | Skill | Uncommon | draw, expensive | draw/cycle; archetypes: rg_skill_chain |
| Quasar (QUASAR) | 0/2* | Skill | Uncommon | card_generation, colorless_creation, star_resource, upgrade_forge, zero_cost | resource acceleration; card generation/deck manipulation; archetypes: rg_created_cards, rg_forge_blade, rg_star_resource |
| Reflect (REFLECT) | 1/3* | Skill | Uncommon | attack, block, block_retention, expensive, star_resource | single-target damage; block/mitigation; resource acceleration; archetypes: rg_star_resource |
| Resonance (RESONANCE) | 1/3* | Skill | Uncommon | aoe, debuff, expensive, self_damage, star_resource, strength | resource acceleration; enemy debuff setup; self-damage payoff/enabler; needs HP discipline; archetypes: rg_star_resource, rg_strength_control |
| Royal Gamble (ROYAL_GAMBLE) | 0/5* | Skill | Uncommon | exhaust, expensive, star_resource, zero_cost | resource acceleration; archetypes: rg_star_resource |
| Summon Forth (SUMMON_FORTH) | 1 | Skill | Uncommon | card_generation, deck_manipulation, sovereign_blade, summon_osty, upgrade_forge | card generation/deck manipulation; archetypes: rg_created_cards, rg_forge_blade |
| Terraforming (TERRAFORMING) | 1 | Skill | Uncommon | star_resource | resource acceleration; archetypes: rg_star_resource, rg_strength_control |

## colorless (65)

| Card | Cost | Type | Rarity | Roles | Use |
| --- | ---: | --- | --- | --- | --- |
| Bolas (BOLAS) | 0 | Attack | Rare | attack, colorless_creation, zero_cost | single-target damage |
| Gold Axe (GOLD_AXE) | 1 | Attack | Rare | attack, colorless_creation, gold | single-target damage |
| Hand of Greed (HAND_OF_GREED) | 2 | Attack | Rare | attack, colorless_creation, expensive, fatal_reward, gold | single-target damage |
| Jackpot (JACKPOT) | 3 | Attack | Rare | attack, card_generation, colorless_creation, draw, expensive, upgrade_forge | single-target damage; draw/cycle; card generation/deck manipulation |
| Knockdown (KNOCKDOWN) | 3 | Attack | Rare | attack, colorless_creation, coop_only_value, expensive | single-target damage |
| Rend (REND) | 2 | Attack | Rare | attack, colorless_creation, debuff, expensive, multi_hit | single-target damage; enemy debuff setup |
| Salvo (SALVO) | 1 | Attack | Rare | attack, block_retention, colorless_creation, deck_manipulation, retain | single-target damage |
| Dramatic Entrance (DRAMATIC_ENTRANCE) | 0 | Attack | Uncommon | aoe, attack, colorless_creation, exhaust, innate, zero_cost | damage/AoE |
| Fisticuffs (FISTICUFFS) | 1 | Attack | Uncommon | attack, block, colorless_creation | single-target damage; block/mitigation |
| Flash of Steel (FLASH_OF_STEEL) | 0 | Attack | Uncommon | attack, colorless_creation, draw, zero_cost | single-target damage; draw/cycle |
| Gang Up (GANG_UP) | 1 | Attack | Uncommon | attack, colorless_creation, coop_only_value, multi_hit | single-target damage |
| Mind Blast (MIND_BLAST) | 1 | Attack | Uncommon | attack, colorless_creation, deck_manipulation, innate | single-target damage |
| Omnislice (OMNISLICE) | 0 | Attack | Uncommon | attack, colorless_creation, zero_cost | single-target damage |
| Seeker Strike (SEEKER_STRIKE) | 1 | Attack | Uncommon | attack, card_generation, colorless_creation, deck_manipulation, draw | single-target damage; draw/cycle; card generation/deck manipulation |
| Tag Team (TAG_TEAM) | 2 | Attack | Uncommon | attack, colorless_creation, coop_only_value, expensive | single-target damage |
| Thrumming Hatchet (THRUMMING_HATCHET) | 1 | Attack | Uncommon | attack, colorless_creation | single-target damage |
| Ultimate Strike (ULTIMATE_STRIKE) | 1 | Attack | Uncommon | attack, colorless_creation | single-target damage |
| Volley (VOLLEY) | 0 X | Attack | Uncommon | aoe, attack, colorless_creation, multi_hit, random_target, x_cost, zero_cost | damage/AoE |
| Beacon of Hope (BEACON_OF_HOPE) | 1 | Power | Rare | block, colorless_creation, coop_only_value, power_scaling | block/mitigation; persistent scaling engine |
| Calamity (CALAMITY) | 3 | Power | Rare | card_generation, colorless_creation, expensive, power_scaling | persistent scaling engine; card generation/deck manipulation |
| Entropy (ENTROPY) | 1 | Power | Rare | card_generation, colorless_creation, deck_manipulation, draw, power_scaling | draw/cycle; persistent scaling engine; card generation/deck manipulation |
| Eternal Armor (ETERNAL_ARMOR) | 3 | Power | Rare | colorless_creation, expensive, plating, power_scaling | persistent scaling engine |
| Mayhem (MAYHEM) | 2 | Power | Rare | colorless_creation, deck_manipulation, expensive, power_scaling | persistent scaling engine |
| Nostalgia (NOSTALGIA) | 1 | Power | Rare | colorless_creation, deck_manipulation, power_scaling | persistent scaling engine |
| Rolling Boulder (ROLLING_BOULDER) | 3 | Power | Rare | aoe, attack, colorless_creation, expensive, power_scaling | damage/AoE; persistent scaling engine |
| Automation (AUTOMATION) | 1 | Power | Uncommon | colorless_creation, energy, power_scaling | resource acceleration; persistent scaling engine |
| Fasten (FASTEN) | 1 | Power | Uncommon | block, colorless_creation, power_scaling | block/mitigation; persistent scaling engine |
| Panache (PANACHE) | 0 | Power | Uncommon | aoe, attack, colorless_creation, power_scaling, zero_cost | damage/AoE; persistent scaling engine |
| Prep Time (PREP_TIME) | 1 | Power | Uncommon | colorless_creation, power_scaling | persistent scaling engine |
| Prowess (PROWESS) | 1 | Power | Uncommon | colorless_creation, dexterity, power_scaling, strength | persistent scaling engine |
| Stratagem (STRATAGEM) | 1 | Power | Uncommon | colorless_creation, deck_manipulation, power_scaling | persistent scaling engine |
| Alchemize (ALCHEMIZE) | 1 | Skill | Rare | colorless_creation, exhaust | utility card; inspect exact text before drafting |
| Anointed (ANOINTED) | 1 | Skill | Rare | colorless_creation, deck_manipulation, draw, exhaust | draw/cycle |
| Beat Down (BEAT_DOWN) | 3 | Skill | Rare | colorless_creation, deck_manipulation, discard, draw, expensive | draw/cycle |
| Hidden Gem (HIDDEN_GEM) | 1 | Skill | Rare | card_generation, colorless_creation, deck_manipulation | card generation/deck manipulation |
| Master of Strategy (MASTER_OF_STRATEGY) | 0 | Skill | Rare | colorless_creation, draw, exhaust, zero_cost | draw/cycle |
| Mimic (MIMIC) | 1 | Skill | Rare | attack, block, colorless_creation, coop_only_value, exhaust | single-target damage; block/mitigation |
| Rally (RALLY) | 2 | Skill | Rare | block, colorless_creation, coop_only_value, expensive | block/mitigation |
| Scrawl (SCRAWL) | 1 | Skill | Rare | colorless_creation, draw, exhaust | draw/cycle |
| Secret Technique (SECRET_TECHNIQUE) | 0 | Skill | Rare | colorless_creation, deck_manipulation, draw, exhaust, zero_cost | draw/cycle |
| Secret Weapon (SECRET_WEAPON) | 0 | Skill | Rare | colorless_creation, deck_manipulation, draw, exhaust, zero_cost | draw/cycle |
| The Gambit (THE_GAMBIT) | 0 | Skill | Rare | attack, block, colorless_creation, zero_cost | single-target damage; block/mitigation |
| Believe in You (BELIEVE_IN_YOU) | 0 | Skill | Uncommon | colorless_creation, coop_only_value, energy, zero_cost | resource acceleration |
| Catastrophe (CATASTROPHE) | 2 | Skill | Uncommon | card_generation, colorless_creation, deck_manipulation, draw, expensive | draw/cycle; card generation/deck manipulation |
| Coordinate (COORDINATE) | 1 | Skill | Uncommon | colorless_creation, coop_only_value, strength | utility card; inspect exact text before drafting |
| Dark Shackles (DARK_SHACKLES) | 0 | Skill | Uncommon | colorless_creation, debuff, exhaust, strength, zero_cost | enemy debuff setup |
| Discovery (DISCOVERY) | 1 | Skill | Uncommon | colorless_creation, energy, exhaust | resource acceleration |
| Equilibrium (EQUILIBRIUM) | 2 | Skill | Uncommon | block, block_retention, colorless_creation, deck_manipulation, expensive, retain | block/mitigation |
| Finesse (FINESSE) | 0 | Skill | Uncommon | block, colorless_creation, draw, zero_cost | block/mitigation; draw/cycle |
| Huddle Up (HUDDLE_UP) | 1 | Skill | Uncommon | colorless_creation, coop_only_value, draw, exhaust | draw/cycle |
| Impatience (IMPATIENCE) | 0 | Skill | Uncommon | colorless_creation, draw, zero_cost | draw/cycle |
| Intercept (INTERCEPT) | 1 | Skill | Uncommon | block, colorless_creation, coop_only_value | block/mitigation |
| Jack of All Trades (JACK_OF_ALL_TRADES) | 0 | Skill | Uncommon | card_generation, colorless_creation, draw, exhaust, zero_cost | draw/cycle; card generation/deck manipulation |
| Lift (LIFT) | 1 | Skill | Uncommon | block, colorless_creation, coop_only_value | block/mitigation |
| Panic Button (PANIC_BUTTON) | 0 | Skill | Uncommon | block, colorless_creation, exhaust, zero_cost | block/mitigation |
| Production (PRODUCTION) | 0 | Skill | Uncommon | colorless_creation, energy, exhaust, zero_cost | resource acceleration |
| Prolong (PROLONG) | 0 | Skill | Uncommon | block, colorless_creation, energy, exhaust, zero_cost | block/mitigation; resource acceleration |
| Purity (PURITY) | 0 | Skill | Uncommon | colorless_creation, draw, exhaust, retain, zero_cost | draw/cycle |
| Restlessness (RESTLESSNESS) | 0 | Skill | Uncommon | colorless_creation, draw, energy, retain, zero_cost | draw/cycle; resource acceleration |
| Shockwave (SHOCKWAVE) | 2 | Skill | Uncommon | aoe, colorless_creation, debuff, exhaust, expensive, vulnerable, weak | enemy debuff setup |
| Splash (SPLASH) | 1 | Skill | Uncommon | card_generation, colorless_creation, energy, upgrade_forge | resource acceleration; card generation/deck manipulation |
| The Bomb (THE_BOMB) | 2 | Skill | Uncommon | aoe, attack, colorless_creation, expensive | damage/AoE |
| Thinking Ahead (THINKING_AHEAD) | 0 | Skill | Uncommon | colorless_creation, deck_manipulation, draw, exhaust, zero_cost | draw/cycle |
| Ultimate Defend (ULTIMATE_DEFEND) | 1 | Skill | Uncommon | block, colorless_creation | block/mitigation |
| 弃用卡牌 (DEPRECATED_CARD) | 0 | Status | Status | colorless_creation, exhaust, not_for_drafting, token_or_generated, zero_cost | generated/curse/status: avoid as a draft target |

## event (27)

| Card | Cost | Type | Rarity | Roles | Use |
| --- | ---: | --- | --- | --- | --- |
| Maul (MAUL) | 1 | Attack | Ancient | attack, multi_hit, token_or_generated | single-target damage |
| Neow's Fury (NEOWS_FURY) | 1 | Attack | Ancient | attack, card_generation, deck_manipulation, discard, draw, exhaust, token_or_generated | single-target damage; draw/cycle; card generation/deck manipulation |
| Whistle (WHISTLE) | 3 | Attack | Ancient | attack, exhaust, expensive, token_or_generated | single-target damage |
| Byrd Swoop (BYRD_SWOOP) | 0 | Attack | Event | attack, token_or_generated, zero_cost | single-target damage |
| Clash (CLASH) | 0 | Attack | Event | attack, token_or_generated, zero_cost | single-target damage |
| Exterminate (EXTERMINATE) | 1 | Attack | Event | aoe, attack, multi_hit, token_or_generated | damage/AoE |
| Mad Science (MAD_SCIENCE) | 1 | Attack | Event | attack, block, token_or_generated | single-target damage; block/mitigation |
| Peck (PECK) | 1 | Attack | Event | attack, multi_hit, token_or_generated | single-target damage |
| Rebound (REBOUND) | 1 | Attack | Event | attack, deck_manipulation, token_or_generated | single-target damage |
| Rip and Tear (RIP_AND_TEAR) | 1 | Attack | Event | aoe, attack, multi_hit, random_target, token_or_generated | damage/AoE |
| Squash (SQUASH) | 1 | Attack | Event | attack, debuff, token_or_generated, vulnerable | single-target damage; enemy debuff setup |
| Caltrops (CALTROPS) | 1 | Power | Event | attack, power_scaling, token_or_generated | single-target damage; persistent scaling engine |
| Hello World (HELLO_WORLD) | 1 | Power | Event | card_generation, power_scaling, token_or_generated | persistent scaling engine; card generation/deck manipulation |
| Apotheosis (APOTHEOSIS) | 2 | Skill | Ancient | exhaust, expensive, innate, token_or_generated, upgrade_forge | utility card; inspect exact text before drafting |
| Apparition (APPARITION) | 1 | Skill | Ancient | ethereal, exhaust, intangible, token_or_generated | utility card; inspect exact text before drafting |
| Brightest Flame (BRIGHTEST_FLAME) | 0 | Skill | Ancient | draw, energy, max_hp, token_or_generated, zero_cost | draw/cycle; resource acceleration |
| Relax (RELAX) | 3 | Skill | Ancient | block, draw, energy, exhaust, expensive, token_or_generated | block/mitigation; draw/cycle; resource acceleration |
| Wish (WISH) | 0 | Skill | Ancient | deck_manipulation, draw, exhaust, token_or_generated, zero_cost | draw/cycle |
| Distraction (DISTRACTION) | 1 | Skill | Event | card_generation, energy, exhaust, token_or_generated | resource acceleration; card generation/deck manipulation |
| Dual Wield (DUAL_WIELD) | 1 | Skill | Event | card_generation, draw, token_or_generated | draw/cycle; card generation/deck manipulation |
| Enlightenment (ENLIGHTENMENT) | 0 | Skill | Event | exhaust, token_or_generated, zero_cost | utility card; inspect exact text before drafting |
| Entrench (ENTRENCH) | 2 | Skill | Event | block, expensive, token_or_generated | block/mitigation |
| Feeding Frenzy (FEEDING_FRENZY) | 0 | Skill | Event | strength, token_or_generated, zero_cost | utility card; inspect exact text before drafting |
| Metamorphosis (METAMORPHOSIS) | 2 | Skill | Event | card_generation, deck_manipulation, draw, energy, exhaust, expensive, token_or_generated | draw/cycle; resource acceleration; card generation/deck manipulation |
| Outmaneuver (OUTMANEUVER) | 1 | Skill | Event | energy, token_or_generated | resource acceleration |
| Stack (STACK) | 1 | Skill | Event | attack, block, deck_manipulation, discard, token_or_generated | single-target damage; block/mitigation |
| Toric Toughness (TORIC_TOUGHNESS) | 2 | Skill | Event | block, expensive, token_or_generated | block/mitigation |

## token (14)

| Card | Cost | Type | Rarity | Roles | Use |
| --- | ---: | --- | --- | --- | --- |
| Giant Rock (GIANT_ROCK) | 1 | Attack | Token | attack, token_or_generated | single-target damage |
| Minion Dive Bomb (MINION_DIVE_BOMB) | 0 | Attack | Token | attack, exhaust, token_or_generated, zero_cost | single-target damage |
| Minion Strike (MINION_STRIKE) | 0 | Attack | Token | attack, draw, exhaust, token_or_generated, zero_cost | single-target damage; draw/cycle |
| Shiv (SHIV) | 0 | Attack | Token | aoe, attack, exhaust, shiv, token_or_generated, zero_cost | damage/AoE |
| Sovereign Blade (SOVEREIGN_BLADE) | 2 | Attack | Token | attack, expensive, multi_hit, retain, sovereign_blade, token_or_generated | single-target damage |
| Sweeping Gaze (SWEEPING_GAZE) | 0 | Attack | Token | aoe, attack, ethereal, exhaust, random_target, summon_osty, token_or_generated, zero_cost | damage/AoE |
| Fuel (FUEL) | 0 | Skill | Token | draw, energy, exhaust, token_or_generated, zero_cost | draw/cycle; resource acceleration |
| Luminesce (LUMINESCE) | 0 | Skill | Token | energy, exhaust, retain, token_or_generated, zero_cost | resource acceleration |
| Minion Sacrifice (MINION_SACRIFICE) | 0 | Skill | Token | block, exhaust, token_or_generated, zero_cost | block/mitigation |
| Soul (SOUL) | 0 | Skill | Token | draw, exhaust, summon_osty, token_or_generated, zero_cost | draw/cycle |
| Disintegration (DISINTEGRATION) | -1 | Status | Status | attack, not_for_drafting, token_or_generated | generated/curse/status: avoid as a draft target; single-target damage |
| Mind Rot (MIND_ROT) | -1 | Status | Status | draw, not_for_drafting, token_or_generated | generated/curse/status: avoid as a draft target; draw/cycle |
| Sloth (SLOTH) | -1 | Status | Status | not_for_drafting, token_or_generated | generated/curse/status: avoid as a draft target |
| Waste Away (WASTE_AWAY) | -1 | Status | Status | not_for_drafting, token_or_generated | generated/curse/status: avoid as a draft target |

## status (11)

| Card | Cost | Type | Rarity | Roles | Use |
| --- | ---: | --- | --- | --- | --- |
| Beckon (BECKON) | 1 | Status | Status | not_for_drafting, self_damage, token_or_generated | generated/curse/status: avoid as a draft target; self-damage payoff/enabler; needs HP discipline |
| Burn (BURN) | -1 | Status | Status | attack, not_for_drafting, status_pollution, token_or_generated | generated/curse/status: avoid as a draft target; single-target damage; adds junk/status; draft only with payoff or cleanup |
| Dazed (DAZED) | -1 | Status | Status | ethereal, not_for_drafting, status_pollution, token_or_generated | generated/curse/status: avoid as a draft target; adds junk/status; draft only with payoff or cleanup |
| Debris (DEBRIS) | 1 | Status | Status | exhaust, not_for_drafting, status_pollution, token_or_generated | generated/curse/status: avoid as a draft target; adds junk/status; draft only with payoff or cleanup |
| Frantic Escape (FRANTIC_ESCAPE) | 1 | Status | Status | not_for_drafting, token_or_generated | generated/curse/status: avoid as a draft target |
| Infection (INFECTION) | -1 | Status | Status | attack, not_for_drafting, token_or_generated | generated/curse/status: avoid as a draft target; single-target damage |
| Slimed (SLIMED) | 1 | Status | Status | draw, exhaust, not_for_drafting, status_pollution, token_or_generated | generated/curse/status: avoid as a draft target; draw/cycle; adds junk/status; draft only with payoff or cleanup |
| Soot (SOOT) | -1 | Status | Status | not_for_drafting, token_or_generated | generated/curse/status: avoid as a draft target |
| Toxic (TOXIC) | 1 | Status | Status | attack, exhaust, not_for_drafting, token_or_generated | generated/curse/status: avoid as a draft target; single-target damage |
| Void (VOID) | -1 | Status | Status | energy, ethereal, not_for_drafting, token_or_generated | generated/curse/status: avoid as a draft target; resource acceleration |
| Wound (WOUND) | -1 | Status | Status | not_for_drafting, status_pollution, token_or_generated | generated/curse/status: avoid as a draft target; adds junk/status; draft only with payoff or cleanup |

## curse (18)

| Card | Cost | Type | Rarity | Roles | Use |
| --- | ---: | --- | --- | --- | --- |
| Ascender's Bane (ASCENDERS_BANE) | -1 | Curse | Curse | ethereal, not_for_drafting, token_or_generated | generated/curse/status: avoid as a draft target |
| Bad Luck (BAD_LUCK) | -1 | Curse | Curse | not_for_drafting, self_damage, token_or_generated | generated/curse/status: avoid as a draft target; self-damage payoff/enabler; needs HP discipline |
| Clumsy (CLUMSY) | -1 | Curse | Curse | ethereal, not_for_drafting, token_or_generated | generated/curse/status: avoid as a draft target |
| Curse of the Bell (CURSE_OF_THE_BELL) | -1 | Curse | Curse | not_for_drafting, token_or_generated | generated/curse/status: avoid as a draft target |
| Debt (DEBT) | -1 | Curse | Curse | gold, not_for_drafting, token_or_generated | generated/curse/status: avoid as a draft target |
| Decay (DECAY) | -1 | Curse | Curse | attack, not_for_drafting, token_or_generated | generated/curse/status: avoid as a draft target; single-target damage |
| Doubt (DOUBT) | -1 | Curse | Curse | debuff, not_for_drafting, token_or_generated, weak | generated/curse/status: avoid as a draft target; enemy debuff setup |
| Enthralled (ENTHRALLED) | 2 | Curse | Curse | expensive, not_for_drafting, token_or_generated | generated/curse/status: avoid as a draft target |
| Folly (FOLLY) | -1 | Curse | Curse | ethereal, innate, not_for_drafting, token_or_generated | generated/curse/status: avoid as a draft target |
| Greed (GREED) | -1 | Curse | Curse | not_for_drafting, token_or_generated | generated/curse/status: avoid as a draft target |
| Guilty (GUILTY) | -1 | Curse | Curse | not_for_drafting, token_or_generated | generated/curse/status: avoid as a draft target |
| Injury (INJURY) | -1 | Curse | Curse | not_for_drafting, token_or_generated | generated/curse/status: avoid as a draft target |
| Normality (NORMALITY) | -1 | Curse | Curse | attack, not_for_drafting, token_or_generated | generated/curse/status: avoid as a draft target; single-target damage |
| Poor Sleep (POOR_SLEEP) | -1 | Curse | Curse | not_for_drafting, retain, token_or_generated | generated/curse/status: avoid as a draft target |
| Regret (REGRET) | -1 | Curse | Curse | not_for_drafting, self_damage, token_or_generated | generated/curse/status: avoid as a draft target; self-damage payoff/enabler; needs HP discipline |
| Shame (SHAME) | -1 | Curse | Curse | not_for_drafting, token_or_generated | generated/curse/status: avoid as a draft target |
| Spore Mind (SPORE_MIND) | 1 | Curse | Curse | exhaust, not_for_drafting, token_or_generated | generated/curse/status: avoid as a draft target |
| Writhe (WRITHE) | -1 | Curse | Curse | innate, not_for_drafting, token_or_generated | generated/curse/status: avoid as a draft target |

## quest (3)

| Card | Cost | Type | Rarity | Roles | Use |
| --- | ---: | --- | --- | --- | --- |
| Byrdonis Egg (BYRDONIS_EGG) | -1 | Quest | Quest | not_for_drafting, token_or_generated | generated/curse/status: avoid as a draft target |
| Lantern Key (LANTERN_KEY) | -1 | Quest | Quest | not_for_drafting, token_or_generated | generated/curse/status: avoid as a draft target |
| Spoils Map (SPOILS_MAP) | -1 | Quest | Quest | gold, not_for_drafting, token_or_generated | generated/curse/status: avoid as a draft target |

