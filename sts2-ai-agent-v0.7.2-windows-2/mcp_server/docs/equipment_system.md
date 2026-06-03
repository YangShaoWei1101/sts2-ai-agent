# Equipment / Relic System Notes

## Data Sources

- Static relic catalog: `data/eng/relics.json`
  - Fields used: `id`, `name`, `rarity`, `description`, `description_raw`, `pool`.
- Live owned relics: `state["run"]["relics"]` or `state["run"]["player_relics"]`
  - Preferred shape: dictionaries with `relic_id` or `id`.
  - Some agent-facing snapshots expose string-only relic names; strategy now normalizes English names when possible and keeps string entries for logging.
- Reward/shop/chest/event/rest live payloads:
  - `state["reward"]["rewards"]`
  - `state["reward"]["cards"]` / `card_options`
  - `state["shop"]["cards"]`, `relics`, `potions`, `items`, `inventory`
  - `state["treasure"]`, `state["chest"]`, `state["selection"]`, `state["event"]`, `state["rest"]`

## Acquisition Entrances

- Combat rewards: `claim_reward`, `choose_reward_card`, `resolve_rewards`.
- Shop purchase: `open_shop_inventory`, `buy_relic`, `buy_card`, `buy_potion`, `remove_card_at_shop`.
- Event rewards: `choose_event_option`, followed by reward or selection screens when the event grants items.
- Chest rewards: `open_chest`, then `choose_treasure_relic`.
- Boss rewards: exposed through reward/treasure/selection payloads and scored by `choose_relic_reward_index` when relic choices appear.
- Initial configuration: starter relics are present in `run.relics` after a run begins.
- Save/state sync: all current equipment is read from fresh MCP state snapshots each step; `journal_decision` records compact relic snapshots into `autoplay_decision_journal.jsonl`.

## Strategy Files

- `autoplay_relic_strategy.py`
  - Loads the static relic catalog.
  - Builds `RelicProfile` from the current run.
  - Scores relic synergy for combat, rewards, shops, route choices, event options, rest options, and card removal.
- `autoplay_ironclad.py`
  - Calls relic strategy from combat scoring, reward selection, shop logic, map routing, rest choice, event choice, and journal logging.
- `autoplay_strategy.py`
  - Builds deck/card plans used by relic synergy scoring.
- `test_relic_strategy_smoke.py`
  - Smoke tests for relic recognition, reward priority, shop removal protection, X-cost/star-cost handling, rest/event behavior, and card-reward selectivity.

## Current Strategy Coverage

- Combat:
  - Attack-chain relics, discard payoff, Chemical X, start-of-combat tempo, summon/scaling support, and Vajra attack damage are considered.
- Card rewards:
  - Existing relics adjust card score and take threshold.
  - Thick decks and high removal debt now raise the bar for non-essential cards.
- Shop:
  - Relic/card/potion purchases are scored with relic synergy.
  - If removal is important, buying first must preserve enough gold for removal unless the buy is clearly high impact.
- Route:
  - Relics can make elites, shops, rests, chests, and combats more or less attractive.
- Events/rest:
  - Relic-granting events, HP-for-relic trades, removal/transform options, shovel/rest/smith synergies are considered.

## Known Gaps

- String-only localized relic names cannot always be converted to English IDs if the top-level state omits `relic_id`.
- Some relics have complex counters or delayed effects that are approximated rather than fully simulated.
- Boss relic choices share the same generic relic scoring model; special hard-coded boss relic rules should be added as more live examples appear.
