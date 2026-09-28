# Time Travel Game: developer notes

A time-travel invention game. Claude Code is the referee (DM); a local web page shows the world state. The design is in `docs/design_doc.md`.

**If your working directory is inside `saves/`, you are the referee.** Follow that folder's CLAUDE.md and ignore this file, which is for work on the engine, the view, the rules and the scenarios.

## Layout

- `engine/`: Python package behind the `tg` CLI.
  - `state.py`: saves (find, create, load), validation, money and clock helpers.
  - `server.py`: the live-view server (stdlib) and Playwright screenshots.
  - `cli.py`: the commands.
  - `schema.json`: JSON Schema for every state file.
- `web/`: the live view. Vanilla JS modules, no build step. `app.js` renders the state; `sketch.js` is the sketch canvas.
- `dm/`: what the referee gets.
  - `rules.md`: the referee rulebook, the heart of the game.
  - `style_guide.md` and `visual_template.svg`: how drawings look.
  - `save_template/`: the CLAUDE.md and `.claude/settings.json` (schema hook, permissions) copied into each new save.
- `scenarios/<id>/`:
  - `scenario.md`: player briefing.
  - `period_notes.md`: DM-facing, not secret.
  - `referee.md`: **secret**.
  - `start/`: initial state, including starting drawings (`visuals/`) and maps (`maps/`).
- `saves/<name>/`: games in progress (gitignored). Each one is a world folder and a DM workspace.
- `tests/`: pytest.

## Commands

```sh
uv sync && uv run playwright install chromium   # one-time setup
uv run tg new cornwall-1705 --name mygame        # new save
uv run tg serve mygame                           # live view at http://127.0.0.1:8765
uv run tg --save mygame shot [target]            # screenshot the view (workshop, journal, a thing id…)
uv run tg --save scenarios/cornwall-1705/start validate   # check a scenario's start state
uv run pytest
```

## Conventions

- The world is data. State is JSON under `engine/schema.json`; the only code in a save is SVG drawings and Fermi scripts. When adding a field, change the schema, the view and `dm/rules.md` together.
- The browser never decides anything. Only the DM writes state; the one exception is the player's saved sketches.
- Everything the player sees is in modern plain English, metric units and decimal pounds (a deliberate anachronism; see the rules' "Language and units"). Money is integer pence, 100p = £1 (`purse_p`, `cost_p`, `wage_p_week`). The clock is `YYYY-MM-DDTHH:MM`, Old Style before 1752.
- **Don't read `scenarios/*/referee.md` out to the user.** They are also the player, and it's a spoiler.
- Keep dependencies minimal: stdlib server, vanilla JS, no bundler. To check a UI change, run `tg shot` and look at the PNG.
