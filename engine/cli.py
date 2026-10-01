"""`tg`: the game's command line, for the player and the DM."""
import argparse
import json
import math
import random
import sys
from pathlib import Path

from . import history, state
from .server import make_server, shot


def cmd_new(args):
    save = state.new_save(args.scenario, args.name or args.scenario)
    history.snapshot(save)
    rel = save.relative_to(Path.cwd()) if save.is_relative_to(Path.cwd()) else save
    print(f"Created {rel}\n\nTo play:\n  uv run tg serve {save.name}    # live view, in one terminal\n  cd {rel} && claude    # the referee, in another")


def cmd_serve(args):
    save = state.find_save(args.name or args.save)
    server = make_server(save, args.port)
    print(f"Serving {save.name} at http://127.0.0.1:{args.port}  (Ctrl-C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


def cmd_status(args):
    save, world = open_world(args)
    problems = state.check_save(save)
    print(f"Save:    {save.name} ({world['title']})")
    print(f"Player:  {world['player']['name'] or '(no name yet)'}")
    print(f"Clock:   {state.fmt_clock(world['clock'])}")
    print(f"Purse:   {state.fmt_money(world['purse_p'])}")
    print("Coming up:" + ("".join(f"\n  {c['label']} ({c['in']}): {c['what']}" for c in state.upcoming(world)) or " nothing noted"))
    print(f"Next turn: {state.next_turn(save)}")
    print("Things:" + "".join(f"\n  {t['id']}: {t['name']} ({t['status']}{', ' + t['owner'] if 'owner' in t else ''})" for t in state.records(save, "things")))
    print("People:" + "".join(f"\n  {p['id']}: {p['name']}, {p['role']}" for p in state.records(save, "people")))
    print("Recipes:" + ("".join(f"\n  {r['id']}: {r['name']}, {r['time']}" for r in state.records(save, "recipes")) or " none"))
    print(f"Maps: {', '.join(m['id'] for m in state.maps(save)) or 'none'}")
    print(f"Unseen sketches: {', '.join(state.unseen_sketches(save)) or 'none'}")
    print("Problems:" + "".join(f"\n  - {p}" for p in problems) if problems else "Problems: none")


def cmd_validate(args):
    problems = state.check_save(state.find_save(args.save))
    print("\n".join(problems) or "All state files valid.")
    sys.exit(1 if problems else 0)


def open_world(args):
    """The save and its world.json, which must be valid for commands that read or change it."""
    save = state.find_save(args.save)
    world = state.valid(save, save / "world.json")
    if world is None:
        raise SystemExit("world.json fails validation:\n" + "\n".join(f"  - {p}" for p in state.check_file(save, save / "world.json")))
    return save, world


def cmd_advance(args):
    save, world = open_world(args)
    before, world["clock"] = world["clock"], state.advance_clock(world["clock"], args.span)
    state.write_json(save / "world.json", world)
    print(f"{state.fmt_clock(before)}  ->  {state.fmt_clock(world['clock'])}")
    passed = sorted((c for c in world.get("coming_up", []) if before <= c["when"] <= world["clock"]), key=lambda c: c["when"])
    if passed:
        print("Passed (from coming_up):" + "".join(f"\n  {state.fmt_clock(c['when'])}: {c['what']}" for c in passed))
    due = state.paydays(before, world["clock"])
    staff = [p for p in state.records(save, "people") if p.get("employed") and p.get("wage_p_week")]
    if due and staff:
        weekly = sum(p["wage_p_week"] for p in staff)
        print(f"Payday passed: {', '.join(f'Saturday {d.day} {d:%B}' for d in due)}. Wages due each time: "
              + ", ".join(f"{p['name']} {state.fmt_money(p['wage_p_week'])}" for p in staff)
              + f". Total {state.fmt_money(weekly * len(due))}. Nothing has been paid yet.")


def cmd_money(sign):
    def run(args):
        amount = state.parse_money(args.amount)
        save, world = open_world(args)
        world["purse_p"] += sign * amount
        state.write_json(save / "world.json", world)
        print(f"{'Paid' if sign < 0 else 'Received'} {state.fmt_money(amount)}. Purse: {state.fmt_money(world['purse_p'])}")
    return run


def cmd_show(args):
    """Several records in one go, compactly: things, people, recipes or places by id, or paths like log/0003."""
    save = state.find_save(args.save)
    gazetteer = state.valid(save, save / "places.json") or {"places": [], "routes": []}
    places = {p["id"]: p for p in gazetteer["places"]}
    missing = []
    for name in args.ids:
        paths = [save / f"{name}.json"] if "/" in name else [save / f"{d}/{name}.json" for d in ("things", "people", "recipes")]
        found = [p for p in paths if p.is_file()]
        for p in found:
            print(f"== {p.relative_to(save).with_suffix('')}")
            data = state.read_json(p)
            for key, value in (data if isinstance(data, dict) else {"error": "not a valid record; see tg validate"}).items():
                print(f"{key}: {value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)}")
        if name in places:
            print(f"== place {name}\n{json.dumps(places[name], ensure_ascii=False)}")
            for r in gazetteer["routes"]:
                if name in (r["from"], r["to"]):
                    print(f"route: {json.dumps(r, ensure_ascii=False)}")
        if not found and name not in places:
            missing.append(name)
    if missing:
        raise SystemExit(f"Not found: {', '.join(missing)}")


def cmd_places(args):
    save = state.find_save(args.save)
    gazetteer = state.valid(save, save / "places.json")
    if not gazetteer:
        raise SystemExit("places.json is missing or fails validation (see tg validate).")
    places = {p["id"]: p for p in gazetteer["places"]}
    if (args.origin or gazetteer["origin"]) not in places:
        raise SystemExit(f"No place {args.origin!r}. Known: {', '.join(places)}")
    here = places[args.origin or gazetteer["origin"]]
    compass = "N NNE NE ENE E ESE SE SSE S SSW SW WSW W WNW NW NNW".split()
    print(f"Places, straight-line from {here['name']} ({args.origin or gazetteer['origin']}):")
    for p in sorted(places.values(), key=lambda p: math.dist((p["x_km"], p["y_km"]), (here["x_km"], here["y_km"]))):
        dx, dy = p["x_km"] - here["x_km"], p["y_km"] - here["y_km"]
        where = f"{math.hypot(dx, dy):6.1f} km {compass[round(math.degrees(math.atan2(dx, dy)) / 22.5) % 16]:3}" if p is not here else "  here"
        print(f"  {p['id']:16} {where}  {p['kind']:8} maps: {', '.join(p['maps'])}{'  (visited)' if p.get('visited') else ''}")
    print("Routes:")
    for r in gazetteer["routes"]:
        print(f"  {r['from']} – {r['to']}: {r['km']} km by {r['by']}, {r['time']}{'. ' + r['notes'] if r.get('notes') else ''}")


def cmd_room(args):
    save = state.find_save(args.save)
    places = {p["id"]: p for p in (state.valid(save, save / "places.json") or {"places": []})["places"]}
    if args.place not in places:
        raise SystemExit(f"No place {args.place!r}. Known: {', '.join(places)}")
    path, name = save / "visuals" / f"room-{args.place}.svg", state.plain(places[args.place]["name"])
    drawn = {mid for kind, mid in state.marks(path) if kind == "thing"} if path.is_file() else set()
    things = state.records(save, "things")
    fitted = {c for t in things for c in t.get("components", [])}
    here = [t for t in things if name in state.plain(t.get("location", "")) and t["status"] != "consumed"]
    print(f"{path.relative_to(save)}: {'drawn' if path.is_file() else 'not drawn yet'}")
    print("Here and drawn: " + (", ".join(sorted(t["id"] for t in here if t["id"] in drawn)) or "nothing"))
    missing = [t for t in here if t["id"] not in drawn and t["id"] not in fitted]
    print("Here but not drawn yet:" + ("".join(f"\n  {t['id']}: {t['location']}" for t in missing) or " nothing"))
    gone = sorted(drawn - {t["id"] for t in here} - fitted - {places[args.place].get("thing")})  # the place's own thing is the room
    print("Drawn but not here by their location (moved? used up?):" + ("".join(f"\n  {i}: {next((t.get('location', '?') for t in things if t['id'] == i), 'no such thing')}" for i in gone) or " nothing"))


def cmd_roll(args):
    draw = random.random()
    print(f"{args.what}: p={args.p}, drew {draw:.3f} -> {'YES' if draw < args.p else 'NO'}")


def cmd_shot(args):
    out = shot(state.find_save(args.save), args.target, args.state, args.sheet, args.step, args.hotspots, args.set, args.half)
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


def cmd_snapshot(args):
    """Claude Code Stop hook (after every referee reply): commit the save's changes to its history."""
    cwd = None if sys.stdin.isatty() else json.load(sys.stdin).get("cwd")
    save = state.save_of(cwd) if cwd else state.find_save(args.save)
    if save:
        history.snapshot(save)


def cmd_history(args):
    for commit, message in history.log(state.find_save(args.save)):
        print(f"  {commit}  {message}")


def cmd_undo(args):
    turn, tag = history.undo(state.find_save(args.save))
    print(f"Undid turn {turn}. The save is back to just before it.\nChanged your mind? uv run tg restore {tag}")


def cmd_restore(args):
    save = state.find_save(args.save)
    tag = history.restore(save, args.ref)
    print(f"Restored {args.ref}: {history.log(save)[0][1]}\nThe replaced state is kept as {tag}.")


def main():
    parser = argparse.ArgumentParser(prog="tg", description="Time Travel Game tools.")
    parser.add_argument("--save", help="save name or path (default: the save you're in, or the only one)")
    # --save also works after the subcommand; SUPPRESS keeps it from overwriting a --save given before it.
    save_after = argparse.ArgumentParser(add_help=False)
    save_after.add_argument("--save", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    sub = parser.add_subparsers(required=True)

    def command(name, **kwargs):
        return sub.add_parser(name, parents=[save_after], **kwargs)

    p = command("new", help="start a new game from a scenario")
    p.add_argument("scenario", help="a folder name under scenarios/")
    p.add_argument("--name", help="save name (default: the scenario name)")
    p.set_defaults(run=cmd_new)

    p = command("serve", help="serve the live view of a save")
    p.add_argument("name", nargs="?", help="save name (default: the save you're in, or the only one)")
    p.add_argument("--port", type=int, default=8765)
    p.set_defaults(run=cmd_serve)

    command("status", help="clock, purse, next turn, things, people, recipes, maps, unseen sketches, problems").set_defaults(run=cmd_status)
    command("validate", help="check every state file and cross-reference").set_defaults(run=cmd_validate)

    p = command("advance", help="move the clock forward: 3d, 4h, 1w2d, 90m")
    p.add_argument("span")
    p.set_defaults(run=cmd_advance)

    for name, sign in (("pay", -1), ("receive", 1)):
        p = command(name, help=f"{name} money, e.g. \"£2.35\" or \"45p\"")
        p.add_argument("amount")
        p.set_defaults(run=cmd_money(sign))

    p = command("show", help="print several things, people, recipes or places (by id), or paths like log/0003")
    p.add_argument("ids", nargs="+")
    p.set_defaults(run=cmd_show)

    p = command("places", help="the gazetteer: places by distance, and known routes")
    p.add_argument("origin", nargs="?", help="measure from this place id (default: the gazetteer's origin)")
    p.set_defaults(run=cmd_places)
    p = command("room", help="what's at a place against what its room drawing shows: missing, and moved")
    p.add_argument("place", help="a place id, e.g. smithy")
    p.set_defaults(run=cmd_room)

    p = command("roll", help='draw against a probability: roll 0.25 "Penrose is at the mine"')
    p.add_argument("p", type=float)
    p.add_argument("what", nargs="?", default="roll")
    p.set_defaults(run=cmd_roll)

    p = command("shot", help="screenshot the view with headless Chromium; prints the PNG path")
    p.add_argument("target", nargs="?", default="workshop", help="a tab (workshop, capabilities, people, map, map/<id>, journal, sketch), board/<id> (the drawing board opened at a thing), or a drawing: a thing id or visuals/<name>.svg's name")
    p.add_argument("--state", help="visual state to show, e.g. running")
    p.add_argument("--sheet", action="store_true", help="the thing's whole spec-sheet page, not just its drawing")
    p.add_argument("--step", help="only this step of a drawing's steps (data-step)")
    p.add_argument("--hotspots", action="store_true", help="outline what can be clicked in the drawing, with its id")
    p.add_argument("--half", action="store_true", help="with board/<id>: stop with its drawing half open over its machine's, to check they line up")
    p.add_argument("--set", action="append", default=[], metavar="ID=STATE", help="show a thing in another state, e.g. in a room: --set engine-10cm=cold")
    p.set_defaults(run=cmd_shot)

    command("history", help="list the save's snapshots, newest first").set_defaults(run=cmd_history)
    command("undo", help="put the save back to just before the last turn").set_defaults(run=cmd_undo)
    p = command("restore", help="put the save back to a snapshot from tg history (or a tag)")
    p.add_argument("ref")
    p.set_defaults(run=cmd_restore)

    command("hook", help="(Claude Code hook) validate a state file just written").set_defaults(run=cmd_hook)
    command("snapshot", help="(Claude Code hook) snapshot the save's changes into its history").set_defaults(run=cmd_snapshot)

    args = parser.parse_args()
    args.run(args)
