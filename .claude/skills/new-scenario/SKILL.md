---
name: new-scenario
description: Draft a new game scenario (e.g. "build a computer in 1850") from a one-line brief, using scenarios/cornwall-1705 as the template.
---

# New scenario

1. Ask for anything the brief leaves open: place, date, who the player is, starting wealth, and the starting pressure (an opportunity, not a win condition).
2. Research the period: prices and wages, materials, crafts and their precision, institutions, and what was known at the time. Also research the real history of the key technologies: what mattered, how they failed, and benchmark numbers.
3. Create `scenarios/<id>/` following `scenarios/cornwall-1705/`:
   - `scenario.md`: the player briefing (arrival, who you are, what you have, the situation, settings).
   - `period_notes.md`: DM-facing but not secret. Prices, materials, crafts, institutions, places. No engineering insights.
   - `referee.md`: secret. What really matters per technology, failure symptoms, benchmarks, traps, world events, historical years.
   - `start/`: `world.json`, `things/*.json`, `people/*.json`, and drawings in `visuals/` for the main site or structure (see `dm/style_guide.md`).
4. Check it: `uv run tg --save scenarios/<id>/start validate`, `uv run pytest`, and a `tg shot` of a test save.
5. Don't show `referee.md`'s content to the user: they'll play it. Delegate writing it to a subagent that reports back without content.
