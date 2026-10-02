# Time Travel Game: developer notes

A time-travel invention game. A Claude Code session is the referee (DM), a local web page shows the world, and the world itself is a folder of plain files. `docs/design_doc.md` is the original vision. Parts of it were never built (MCP server, Three.js, plugin API, in-browser chat, a metrics dashboard), and the referee turned out relaxed rather than strict. The real interfaces are the `tg` CLI, two Claude Code hooks and the static view.

**If your working directory is inside `saves/`, you are the referee.** Follow that folder's CLAUDE.md and ignore this file, which is for work on the engine, the view, the rules and the scenarios.

## How it fits together

- **A save** (`saves/<name>/`, gitignored) is the world, and the referee's workspace. `dm/rules.md` ("The world is this folder") is the canonical description of its files:
  - `world.json`, `places.json` and `stores.json`;
  - folders `things/`, `people/`, `recipes/`, `log/`, `fermi/`, `visuals/`, `maps/` and `sketches/`;
  - `hidden.md`, the referee's notebook;
  - `.history/` (snapshots) and `.claude/settings.json` (hooks and permissions).
- **Creation.** `tg new` copies `scenarios/<id>/start/` and `dm/save_template/` into the save.
- **What reaches existing saves.** The save's CLAUDE.md @-imports `dm/rules.md`, `dm/style_guide.md` and the scenario's notes. Edits to those reach existing saves at the next referee session. **Edits to `dm/save_template/`, a scenario's `start/` or the schema don't update existing saves:** upgrade them by hand, e.g. copy in new template files and add missing fields.
- **Hooks**, in the save's `.claude/settings.json`, active once the folder is trusted in Claude Code:
  - `tg hook` (PostToolUse on Write/Edit) validates each file the referee writes. Exit 2 feeds the errors back to it, so `state.check_file` must report bad content and never raise.
  - `tg snapshot` (Stop) commits the save into `.history/` after every reply. That's what `tg undo`, `tg history` and `tg restore` use.
- **The `draw` subagent** (`.claude/agents/draw.md` in each save) makes every drawing in the background while the referee narrates. Running in the save, it loads the secret notes like the referee does; its instructions only keep them out of what the player sees. When it's done it adds the drawing to the turn's `visuals` and sets the thing's `visual`, so nothing points at a missing file meanwhile.
- **Validation** (`engine/state.py`) works in two layers:
  - `check_file`: one file's schema, `id` matching the file name, well-formed SVG.
  - `check_save`: adds cross-references between files (missing drawings, unknown components, tools or recipes, places not labelled on their maps, drawings marking unknown things or people). It feeds `tg validate`, `tg status` and the view's "State problems" banner.

  `load_state` passes only valid records to the view.
- **The view** (`web/`): `tg serve` streams a change event whenever a visible file in the save changes. The page refetches `/api/state` (`state.load_state`) and re-renders.
  - Routes: `#/workshop` (the drawing board), `#/thing/<id>[?half]` (the board at that thing; `#/board/<id>` is the same), `#/capabilities`, `#/people`, `#/map[/<id>]`, `#/journal`, `#/sketch`, and `#/visual/<name>[?state=…&time=…&step=…&at=…&hotspots&set=id=state,…]` (one drawing alone, for `tg shot`).
  - **One home per thing.** A thing lives on the drawing board: on its own sheet, or inside the sheet of what it's part of (a part without a drawing is shown there, its sheet in the panel), or on a blank sheet if it has no drawing at all. The board's panel is its sheet (`details()` in `app.js`: states, steps, parts list, flaws, trials, sizes, history); zoomed out, the panel is the register of every sheet. There is no separate thing page; the address follows what the board shows (`located`). A thing can have more sheets, `visuals/<id>--<name>.svg`, shown as tabs. The papers under the board are the desk: last turn, coming up, threads, house rules, stores.
  - **The drawing board** (`web/board.js`, the Workshop): every top-level drawing laid out in sections on one sheet, zoomed like a map (the root SVG's viewBox is the camera). Drawings are `<image>`s of prepared SVGs, measured once in a hidden sandbox for their `[data-object]` and `[data-thing]` outlines. A part with its own drawing opens in place: its drawing is fitted object-outline-to-part-outline and grows out of a clipping circle as it fills the screen (`walk()` decides the path: zooming opens the smallest part at the pointer, but a part with other parts drawn over much of it opens only on a click; an open detail stays open while you're inside it; after a flight nothing opens by itself until you zoom; zoom stops three times past the deepest drawing). Balloons and the panel's parts list are drawn by the view; parts not in hand are restyled as blueprint ghosts. Only the drawing in focus animates; the rest, and the whole board while a page lies over it, show a still (`data.still`: every SMIL animation ended at 0.001 s and frozen), because an animated drawing repaints all of itself, ink filter included, every frame. Other pages lie over the board like paper (`body.staged`); a link to a thing puts the page down and flies the board to it (`lineage`).
  - **Preparing a drawing** (`prepare()`): only the groups for the states and time of day being shown are kept. A `data-state` group follows the nearest enclosing `data-thing` that has states (the engine drawn in the smithy), else the drawing's own thing; a thing without states shares the state of what it's part of (`stateOf`); `data-sky` follows the clock; one `data-step` at a time.
  - **Sound** (`web/sound.js`): Web Audio makes ambience on the fly for the `data-sound` groups in the drawing the board is on; off until the player turns it on.
  - A turn's `measurements` are plotted as inline SVG line charts (`chart()` in `app.js`), in the journal and on the tested thing's sheet.
  - Journal illustrations show each drawing as it was when that turn ended. `/api/state` includes `snapshots` (`history.turn_ends`: the last snapshot before the next turn was logged), and `/api/rev/<sha>/<path>` serves a drawing or spec sheet from it. The latest turn uses the current files.
  - `world.json`'s `coming_up` is shown as a note at the top of the Workshop and the Journal (`state.upcoming` labels it); the Workshop also shows the four most recently changed drawings.
  - Thumbnails and journal illustrations are `<img>` blob URLs of prepared drawings. That keeps each drawing's ids and styles separate.
  - Maps are drawn inline in a shadow root so their labels can be clicked.
  - `render()` sets `document.body.dataset.ready = "1"` when a page is complete, and `tg shot` and the tests wait for it. New async view code must finish before that.
- **The sketch tab** (`web/sketch.js`) is the only place the browser writes: it POSTs PNGs to `/api/sketch`.

## Layout

- `engine/`: Python package behind the `tg` CLI. Run `uv run tg --help` for all commands; `dm/rules.md` documents the referee-facing ones.
  - `state.py`: saves (find, create, load), validation, money and clock helpers.
  - `history.py`: each save's snapshot history, a git repo in `<save>/.history`. It isn't `.git`, so Claude Code doesn't treat the save as its own project.
  - `server.py`: the live-view server (stdlib) and Playwright screenshots.
  - `cli.py`: the commands.
  - `draw.py`: the drawing kit. Drawings are scripts in a save's `drawings/` folder (`tg draw` runs them): parts are functions in millimetres, drawn once in `drawings/parts.py` and used by every drawing they're in, so the board's alignment holds by construction. The kit fits the object to the sheet, lays out labels, and writes the marks the view reads.
  - `stock.py`: true-size stock parts for the kit (people, barrels, pipes, taps, wheels, fire, sky and night…); `dm/stock.png` is their catalogue, made by `dm/stock_catalogue.py`.
  - `schema.json`: JSON Schema for every state file.
- `web/`: the live view. Vanilla JS modules, no build step. `app.js` renders the state; `sketch.js` is the sketch canvas; `sound.js` the ambience; `board.js` the drawing board.
- `dm/`: what the referee gets.
  - `rules.md`: the referee rulebook, the heart of the game.
  - `style_guide.md`: how drawings look.
  - `stock.png`: the catalogue of stock parts the drawers read.
  - `save_template/`: what each new save gets: `CLAUDE.md`, `hidden.md`, `.claude/settings.json` and `.claude/agents/draw.md`.
- `scenarios/<id>/`:
  - `scenario.md`: player briefing.
  - `period_notes.md`: DM-facing, not secret.
  - `referee.md`: **secret**.
  - `start/`: initial state: `world.json`, `places.json`, `things/`, `people/`, drawings in `visuals/`, and `maps/`.
- `.claude/skills/new-scenario/`: the skill for drafting a new scenario.
- `tests/`: pytest.
  - `test_state.py`: engine and schema.
  - `test_cli.py`: the commands and both hooks.
  - `test_view.py`: a Playwright smoke test of every page.

## Commands

```sh
uv sync && uv run playwright install chromium   # one-time setup (git is needed too)
uv run tg new cornwall-1705 --name mygame        # new save
uv run tg serve mygame                           # live view at http://127.0.0.1:8765
uv run tg --save mygame status                   # --save before or after the command; not needed inside a save
uv run tg --save scenarios/cornwall-1705/start validate   # check a scenario's start state
uv run tg --save scenarios/cornwall-1705/start shot map   # screenshot without making a save (writes a gitignored .shots/)
uv run pytest                                    # about 10 s, including the browser tests
```

## Conventions

- **Playable over rigorous.** The player is the user. They can override anything out of character, and lasting overrides become house rules. Don't add strictness machinery, or automation that changes state behind the referee's back. Prefer tools that do one lookup or calculation and print it (see `dm/rules.md`, "The player is in charge of the game").
- **Spoilers.** Don't show the user `scenarios/*/referee.md` or a save's `hidden.md`. That includes commands, heredocs and test fixtures they can see. Delegate edits to those files to a subagent that reports back without content. The server's refusal to serve `hidden.md` is spoiler courtesy, not security; don't harden it.
- **The world is data.** State is JSON under `engine/schema.json`; the only code in a save is drawings (SVG, and the kit scripts in `drawings/` that make them) and Fermi scripts. A new field or state file usually touches:
  - the schema;
  - `state.py` (`kind_of`, `load_state`, `new_save`, `check_save`);
  - the view (`web/app.js`);
  - `dm/rules.md`;
  - sometimes `cli.py` (`status`, `show`), the scenario's `start/` and the `new-scenario` skill;
  - the tests.
- **Edit `schema.json` one definition at a time.** A replace-all once pasted definitions inside other definitions. A test now catches that.
- **Everything the player sees** is in modern plain English, metric units and decimal pounds (a deliberate anachronism; see the rules' "Language and units"). Money is integer pence, 100p = £1 (`purse_p`, `cost_p`, `wage_p_week`). The clock is `YYYY-MM-DDTHH:MM`, Old Style before 1752. Spec-sheet property keys carry a unit suffix that the view knows (`UNIT` in `web/app.js`): `_mm`, `_m`, `_kg`, `_l_per_min`, `_c`, `_p` and so on.
- **The browser never decides anything.** Only the referee writes state; the one exception is the player's saved sketches.
- **No "secret" in referee-edited file names.** Common Claude Code deny rules (like `Edit(**/*secret*)`) block them. That's why the notebook is `hidden.md`.
- **Keep dependencies minimal:** stdlib server, vanilla JS, no bundler. To check a UI change, run `uv run pytest tests/test_view.py` and look at a `tg shot` PNG.
