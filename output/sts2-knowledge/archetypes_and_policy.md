# STS2 Archetypes And Agent Policy

Generated for the installed STS2 v0.103.3 environment on 2026-05-31.

This file is the human-facing strategy layer. The machine-facing layer is `card_model.json`.

## Data Source Rule

- Primary truth for current availability: live mod API at `http://127.0.0.1:8080/data/*`.
- Primary English text source: Spire Codex API snapshots in this folder.
- Current live card count is 577. Spire Codex English card count is 576.
- The only live-only card is `DEPRECATED_CARD`; treat it as cleanup/status baggage, not a draft target.
- The local bundled English file has stale edges: it still contains `GRAPPLE`, while the current live/API corpus does not.

## Global Draft Policy

The agent should draft in two layers:

1. Solve the next 3 floors: take efficient frontloaded damage, enough block, and at least one draw/cycle tool before chasing beautiful engines.
2. Commit only after signals: a payoff card, a relic, or 2+ enablers should be present before taking narrow synergy cards.
3. Penalize isolated payoffs: cards like `BODY_SLAM`, `ACCURACY`, `TIMES_UP`, or `SEEKING_EDGE` need the matching support already present or clearly available.
4. Penalize unbounded junk: cards that add Wounds, Dazed, Burn, Slimed, or Debris need status payoff/cleanup or overwhelming immediate value.
5. Reward density: card draw, energy/star gain, deck manipulation, and exhaust/discard cleanup get better as the deck gains a real engine.
6. Skip more often after the deck is functional; extra average cards are worse than drawing the good cards.

## Combat Policy

- Lethal check comes first. If lethal is possible without unacceptable risk, take it.
- Then prevent death and large HP loss. Low HP should sharply reduce self-damage and delayed setup.
- Play long-term powers early only when incoming damage is covered or the power prevents more future loss than it costs now.
- Treat X-cost and star-cost cards as resource sinks. They should be played after free draw/setup unless their immediate damage/block is required.
- Use generated-card and random-play effects only after verifying they cannot waste required resources or trigger self-harm.
- When a card has `coop_only_value`, down-rank it in singleplayer unless it still has direct self value.

## The Ironclad

Identity: high HP, frontloaded attacks, Vulnerable, exhaust engines, self-damage payoffs, and block-to-damage conversion.

Main archetypes:

- `ic_vulnerable_burst`: `BASH`, `THUNDERCLAP`, `TREMBLE`, `UPPERCUT`, `MOLTEN_FIST`, `BULLY`, `CRUELTY`, `VICIOUS`.
- `ic_exhaust_engine`: `TRUE_GRIT`, `BURNING_PACT`, `SECOND_WIND`, `FEEL_NO_PAIN`, `DARK_EMBRACE`, `CORRUPTION`, `FIEND_FIRE`, `ASHEN_STRIKE`, `PACTS_END`.
- `ic_self_damage_strength`: `BLOODLETTING`, `OFFERING`, `HEMOKINESIS`, `RUPTURE`, `INFERNO`, `TEAR_ASUNDER`, `SPITE`.
- `ic_block_body_slam`: `SHRUG_IT_OFF`, `FLAME_BARRIER`, `IMPERVIOUS`, `BARRICADE`, `JUGGERNAUT`, `BODY_SLAM`, `UNMOVABLE`.
- `ic_attack_chain`: `ANGER`, `TWIN_STRIKE`, `SWORD_BOOMERANG`, `WHIRLWIND`, `CONFLAGRATION`, `STOMP`, `JUGGLING`, `STAMPEDE`.

Draft notes:

- Early floors want 1-2 efficient attacks plus a real block card. `POMMEL_STRIKE`, `THUNDERCLAP`, `HEMOKINESIS`, `SHRUG_IT_OFF`, `FLAME_BARRIER`, and `TRUE_GRIT` are broadly useful.
- `BLOODLETTING` and `OFFERING` are strong tempo but become bad if the combat policy ignores HP thresholds.
- `BODY_SLAM` is not generic damage. It is a payoff for heavy block/Barricade/Juggernaut decks.
- `CORRUPTION` becomes excellent with `DARK_EMBRACE` or `FEEL_NO_PAIN`; alone it can exhaust too much defense.

## The Silent

Identity: draw/discard, Sly, poison, shivs, dexterity, Weak, and skill chains.

Main archetypes:

- `si_poison`: `DEADLY_POISON`, `BOUNCING_FLASK`, `SNAKEBITE`, `NOXIOUS_FUMES`, `ACCELERANT`, `OUTBREAK`, `ENVENOM`, `MIRAGE`.
- `si_shiv`: `BLADE_DANCE`, `CLOAK_AND_DAGGER`, `ACCURACY`, `INFINITE_BLADES`, `FAN_OF_KNIVES`, `PHANTOM_BLADES`, `STORM_OF_STEEL`, `KNIFE_TRAP`.
- `si_discard_sly`: `ACROBATICS`, `PREPARED`, `DAGGER_THROW`, `SURVIVOR`, `CALCULATED_GAMBLE`, `TACTICIAN`, `REFLEX`, `TOOLS_OF_THE_TRADE`, `MASTER_PLANNER`.
- `si_draw_skill_chain`: `ADRENALINE`, `BACKFLIP`, `BURST`, `BULLET_TIME`, `AFTERIMAGE`, `FLECHETTES`, `FINISHER`, `PINPOINT`, `SPEEDSTER`.
- `si_defense_control`: `NEUTRALIZE`, `SUCKER_PUNCH`, `LEG_SWEEP`, `PIERCING_WAIL`, `FOOTWORK`, `AFTERIMAGE`, `WRAITH_FORM`, `BLUR`.

Draft notes:

- Do not mix poison and shiv payoffs too early unless the card is independently strong.
- `ACCURACY` needs real shiv density. One `BLADE_DANCE` is a start, not a complete reason.
- Discard cards are good when they cycle or produce value. `TACTICIAN` and `REFLEX` need discard outlets.
- Poison is slow against hallway fights unless paired with frontloaded defense or AoE poison.
- `WRAITH_FORM` and `MALAISE` are high-impact survival tools, but the agent must time them around enemy intent.

## The Defect

Identity: orb economy, Focus, Frost defense, zero-cost recursion, power scaling, and selective status exploitation.

Main archetypes:

- `de_orb_focus`: `ZAP`, `DUALCAST`, `BALL_LIGHTNING`, `COLD_SNAP`, `COOLHEADED`, `GLACIER`, `DEFRAGMENT`, `CAPACITOR`, `LOOP`, `BIASED_COGNITION`, `MULTI_CAST`, `RAINBOW`.
- `de_frost_defense`: `CHILL`, `COLD_SNAP`, `COOLHEADED`, `GLACIER`, `COOLANT`, `HAILSTORM`, `ICE_LANCE`.
- `de_zero_claw`: `CLAW`, `BEAM_CELL`, `GO_FOR_THE_EYES`, `FTL`, `ALL_FOR_ONE`, `FERAL`, `TURBO`, `MOMENTUM_STRIKE`.
- `de_status_engine`: `BOOST_AWAY`, `FIGHT_THROUGH`, `GUNK_UP`, `OVERCLOCK`, `COMPACT`, `FLAK_CANNON`, `ITERATION`.
- `de_power_engine`: `ECHO_FORM`, `CREATIVE_AI`, `MACHINE_LEARNING`, `BUFFER`, `STORM`, `LOOP`, `DEFRAGMENT`.

Draft notes:

- Focus and Frost make the safest default engine. Draft `DEFRAGMENT`, `COOLHEADED`, `GLACIER`, and `CAPACITOR` highly when orb density exists.
- `CLAW` needs repeated copies/recursion; an isolated `CLAW` is usually just weak damage.
- Status-pollution cards need cleanup/payoff. `OVERCLOCK` is good with draw payoff but can bury the deck.
- `BIASED_COGNITION` is strong when the fight ends soon or Focus loss is offset by artifact/tempo.
- Orb evoke cards must respect orb order; do not blindly `DUALCAST` away the wrong rightmost orb.

## The Necrobinder

Identity: Osty/minion actions, Summon, Souls/Ethereal, Doom, debuff spreading, and delayed execution.

Main archetypes:

- `nb_osty_summon`: `BODYGUARD`, `UNLEASH`, `POKE`, `FETCH`, `SIC_EM`, `SPUR`, `REANIMATE`, `NECRO_MASTERY`, `SACRIFICE`, `SQUEEZE`.
- `nb_doom`: `SCOURGE`, `NEGATIVE_PULSE`, `NO_ESCAPE`, `OBLIVION`, `TIMES_UP`, `END_OF_DAYS`, `REAPER_FORM`, `SHROUD`, `DEATHBRINGER`.
- `nb_ethereal_soul`: `GRAVE_WARDEN`, `REAVE`, `SEVERANCE`, `SEANCE`, `GLIMPSE_BEYOND`, `PAGESTORM`, `SPIRIT_OF_ASH`, `PULL_FROM_BELOW`, `SOUL_STORM`.
- `nb_debuff_control`: `DEFY`, `FEAR`, `PUTREFY`, `DEBILITATE`, `MISERY`, `SLEIGHT_OF_FLESH`, `ENFEEBLING_TOUCH`, `SHARED_FATE`.

Draft notes:

- Osty decks need Summon density and clear payoff. Do not draft too many Osty attacks if Osty cannot stay alive or be resummoned.
- Doom is delayed damage. It needs stall, AoE application, or execution payoffs like `TIMES_UP` and `END_OF_DAYS`.
- Soul/Ethereal packages need draw and payoff; otherwise they dilute future turns.
- `SACRIFICE` is a defensive payoff, not a default click. It should be reserved for lethal prevention or when resummon is available.

## The Regent

Identity: star resource, star-cost burst, Forge/Sovereign Blade scaling, created cards, debuff control, and skill-chain turns.

Main archetypes:

- `rg_star_resource`: `VENERATE`, `FALLING_STAR`, `GATHER_LIGHT`, `ALIGNMENT`, `HIDDEN_CACHE`, `GENESIS`, `THE_SEALED_THRONE`, `ORBIT`, `BIG_BANG`, plus star-cost attacks like `COMET`, `DEVASTATE`, and `SEVEN_STARS`.
- `rg_forge_blade`: `REFINE_BLADE`, `SPOILS_OF_BATTLE`, `BULWARK`, `FURNACE`, `THE_SMITH`, `SUMMON_FORTH`, `SEEKING_EDGE`, `SWORD_SAGE`, `PARRY`, `CONQUEROR`.
- `rg_created_cards`: `MANIFEST_AUTHORITY`, `QUASAR`, `BUNDLE_OF_JOY`, `SPECTRUM_SHIFT`, `ARSENAL`, `PILLAR_OF_CREATION`, `SUPERMASSIVE`.
- `rg_skill_chain`: `GLIMMER`, `PHOTON_CUT`, `PROPHESIZE`, `MAKE_IT_SO`, `LUNAR_BLAST`, `PALE_BLUE_DOT`, `DECISIONS_DECISIONS`.
- `rg_strength_control`: `FALLING_STAR`, `GAMMA_BLAST`, `COMET`, `METEOR_SHOWER`, `CRUSH_UNDER`, `DYING_STAR`, `MONARCHS_GAZE`, `RESONANCE`.

Draft notes:

- Star spenders need star generation. Do not take multiple big star-cost cards without `VENERATE`, `GATHER_LIGHT`, `GENESIS`, or similar.
- Forge/Sovereign Blade is a real scaling plan only after the deck can find and replay the blade or has persistent Forge.
- Created-card decks can solve awkward turns but risk randomness. Reward `ARSENAL`/`PILLAR_OF_CREATION` only when generation density is already present.
- Regent can frontload debuffs well; `FALLING_STAR`, `KNOW_THY_PLACE`, `GAMMA_BLAST`, and `METEOR_SHOWER` are strong setup for burst turns.

## Integration Contract

Future code should consume `card_model.json` and keep these fields in draft/combat scoring:

- `roles`: immediate card functions.
- `archetype_tags`: deck-level synergy hooks.
- `live_present`: false means do not draft/use except for legacy deck cleanup.
- `not_for_drafting`: hard negative for rewards and shops.
- `coop_only_value`: down-rank in singleplayer.
- `self_damage`: apply HP-sensitive penalty.
- `status_pollution`: require payoff or cleanup.
- `x_cost`, `star_resource`, `expensive`: evaluate after current resource availability.

Deck scoring should maintain counts per archetype and role. Reward a card when it either fixes a missing role or strengthens the deck's top 1-2 archetypes. Penalize cards that introduce a third narrow archetype without solving immediate fights.
