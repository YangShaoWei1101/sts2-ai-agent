# STS2 Knowledge Snapshot

Generated on 2026-05-31 for the local game API reporting STS2 `v0.103.3`.

## Main Files

- `source_audit.json`: source counts, game/mod version, and data mismatches.
- `card_model.json`: machine-readable per-card role and archetype tags for 577 current card IDs.
- `card_model.md`: human-readable full card table grouped by color/character.
- `card_model_stats.json`: counts by role and archetype tag.
- `archetypes_and_policy.md`: human-readable strategy model and draft/combat policy.
- `characters_summary_english.json`: character starting decks, relics, HP, and unlock chain from Spire Codex.
- `local_keywords.json`: keyword definitions from bundled English data.

## Raw Snapshots

- `live_*.json`: current local game API data from `http://127.0.0.1:8080/data/*`.
- `spire_codex_*.json`: English data snapshots from `https://spire-codex.com/api/*`.

## Important Differences

- Live cards: 577.
- Spire Codex English cards: 576.
- Live-only card: `DEPRECATED_CARD`, which should not be drafted.
- Bundled local English data has a stale `GRAPPLE` entry that is not present in the current live/Spire Codex card list.

Future autoplay changes should load `card_model.json` first, then apply deck-state scoring on top of these tags.

## First Integration

`sts2-ai-agent-v0.7.2-windows-2/mcp_server/autoplay_strategy.py` now loads this card model and exposes scoring helpers for rewards, combat plays, upgrades, and character-aware deck profiles. `autoplay_ironclad.py` calls that layer before making reward, shop, combat, upgrade, and character-selection decisions.
