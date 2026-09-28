"""`tg`: the game's command line, for the player and the DM."""
import argparse
import json
import random
import sys
from pathlib import Path

from . import state
from .server import make_server, shot


def cmd_new(args):
    save = state.new_save(args.scenario, args.name or args.scenario)
    rel = save.relative_to(Path.cwd()) if save.is_relative_to(Path.cwd()) else save
    print(f"Created {rel}\n\nTo play:\n  uv run tg serve             # live view, in one terminal\n  cd {rel} && claude    # the referee, in another")


def cmd_serve(args):
    save = state.find_save(args.save)
    server = make_server(save, args.port)
    print(f"Serving {save.name} at http://127.0.0.1:{args.port}  (Ctrl-C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


def cmd_status(args):
    save = state.find_save(args.save)
    world = state.read_json(save / "world.json")
    problems = state.check_save(save)
    unseen = state.unseen_sketches(save)
    print(f"Save:    {save.name} ({world['title']})")
    print(f"Clock:   {state.fmt_clock(world['clock'])}")
    print(f"Purse:   {state.fmt_money(world['purse_d'])}")
    print(f"Next turn: {state.next_turn(save)}")
    things = [state.read_json(p) or {"id": p.stem} for p in sorted((save / "things").glob("*.json"))]
    people = [state.read_json(p) or {"id": p.stem} for p in sorted((save / "people").glob("*.json"))]
    print("Things:\n" + "\n".join(f"  {t['id']}: {t.get('name')} ({t.get('status')}{', ' + t['owner'] if 'owner' in t else ''})" for t in things))
    print("People:\n" + "\n".join(f"  {p['id']}: {p.get('name')}, {p.get('role')}" for p in people))
    print(f"Unseen sketches: {', '.join(unseen) or 'none'}")
    print("Problems:" + "".join(f"\n  - {p}" for p in problems) if problems else "Problems: none")


def cmd_validate(args):
    problems = state.check_save(state.find_save(args.save))
    print("\n".join(problems) or "All state files valid.")
    sys.exit(1 if problems else 0)


def open_world(args):
    save = state.find_save(args.save)
    return save / "world.json", state.read_json(save / "world.json")


def cmd_advance(args):
    path, world = open_world(args)
    before, world["clock"] = world["clock"], state.advance_clock(world["clock"], args.span)
    state.write_json(path, world)
    print(f"{state.fmt_clock(before)}  ->  {state.fmt_clock(world['clock'])}")


def cmd_money(sign):
    def run(args):
        amount = state.parse_money(args.amount)
        path, world = open_world(args)
        world["purse_d"] += sign * amount
        state.write_json(path, world)
        print(f"{'Paid' if sign < 0 else 'Received'} {state.fmt_money(amount)}. Purse: {state.fmt_money(world['purse_d'])}")
    return run


def cmd_roll(args):
    draw = random.random()
    print(f"{args.what}: p={args.p}, drew {draw:.3f} -> {'YES' if draw < args.p else 'NO'}")


def cmd_shot(args):
    out = shot(state.find_save(args.save), args.target, args.state, args.sheet)
    print(out.relative_to(Path.cwd()) if out.is_relative_to(Path.cwd()) else out)


def cmd_hook(args):
    """Claude Code PostToolUse hook: reject state files that break the schema (exit 2 feeds stderr to Claude)."""
    event = json.load(sys.stdin)
    tool_input = event.get("tool_input", {})
    path = Path(event.get("cwd", ".")) / (tool_input.get("file_path") or tool_input.get("path") or "")
    save = state.save_of(path.parent)
    problems = state.check_file(save, path) if save and path.is_file() else []
    if problems:
        print("This state file breaks the schema (engine/schema.json). Fix it before continuing:", file=sys.stderr)
        print("\n".join(f"  - {p}" for p in problems), file=sys.stderr)
        sys.exit(2)


def main():
    parser = argparse.ArgumentParser(prog="tg", description="Time Travel Game tools.")
    parser.add_argument("--save", help="save name or path (default: the save you're in, else the latest)")
    sub = parser.add_subparsers(required=True)

    p = sub.add_parser("new", help="start a new game from a scenario")
    p.add_argument("scenario", help="a folder name under scenarios/")
    p.add_argument("--name", help="save name (default: the scenario name)")
    p.set_defaults(run=cmd_new)

    p = sub.add_parser("serve", help="serve the live view")
    p.add_argument("--port", type=int, default=8765)
    p.set_defaults(run=cmd_serve)

    sub.add_parser("status", help="clock, purse, next turn, unseen sketches, problems").set_defaults(run=cmd_status)
    sub.add_parser("validate", help="check every state file and cross-reference").set_defaults(run=cmd_validate)

    p = sub.add_parser("advance", help="move the clock forward: 3d, 4h, 1w2d, 90m")
    p.add_argument("span")
    p.set_defaults(run=cmd_advance)

    for name, sign in (("pay", -1), ("receive", 1)):
        p = sub.add_parser(name, help=f"{name} money, e.g. \"£2 3s 6d\"")
        p.add_argument("amount")
        p.set_defaults(run=cmd_money(sign))

    p = sub.add_parser("roll", help='draw against a probability: roll 0.25 "Penrose is at the mine"')
    p.add_argument("p", type=float)
    p.add_argument("what", nargs="?", default="roll")
    p.set_defaults(run=cmd_roll)

    p = sub.add_parser("shot", help="screenshot the view with headless Chromium; prints the PNG path")
    p.add_argument("target", nargs="?", default="workshop", help="workshop | people | journal | sketch | <thing-id>")
    p.add_argument("--state", help="visual state to show, e.g. running")
    p.add_argument("--sheet", action="store_true", help="the thing's whole spec-sheet page, not just its drawing")
    p.set_defaults(run=cmd_shot)

    sub.add_parser("hook", help="(Claude Code hook) validate a state file just written").set_defaults(run=cmd_hook)

    args = parser.parse_args()
    args.run(args)
