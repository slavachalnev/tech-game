# Time Travel Game

Go back in time with only what's in your head, and see how much progress you can actually bring. Claude Code is the referee: it judges your plans with back-of-envelope physics, keeps a persistent world in JSON files, and draws what you build. A local web page shows the world live.

The first scenario: **Cornwall, 1705.** A tin mine is drowning, the owners will pay for anything that drains it, and Newcomen's engine is seven years away.

## Setup

Requires [uv](https://docs.astral.sh/uv/) and [Claude Code](https://claude.com/claude-code).

```sh
uv sync
uv run playwright install chromium
```

## Play

```sh
uv run tg new cornwall-1705 --name mygame   # start a game
uv run tg serve mygame                      # terminal 1: open http://127.0.0.1:8765
cd saves/mygame && claude                   # terminal 2: the referee
```

Say "let's begin" to the referee, then describe what you do in as much detail as you actually know. The referee credits only what you state or sketch. To show a design, draw it in the view's **Sketch** tab, save it, and paste the path it copies into the terminal with your message. Start a message with `ooc:` to ask the referee something out of character.

Made a mistake, or want to try something else? Ask the referee (`ooc: undo that`), or run `uv run tg undo` (last turn), `uv run tg history` and `uv run tg restore <id>` yourself, then tell the referee. Every referee reply is snapshotted.

Don't open `scenarios/*/referee.md` or a save's `secret.md`: they hold the referee's hidden notes.

## How it works

See `docs/design_doc.md` for the design and `CLAUDE.md` for the code layout.
