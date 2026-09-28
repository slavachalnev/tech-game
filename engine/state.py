"""Save folders: find, create, load and validate them. Money and clock helpers."""
import json
import re
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from xml.etree import ElementTree

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent
SAVES = ROOT / "saves"
SCENARIOS = ROOT / "scenarios"
SCHEMA = json.loads((Path(__file__).parent / "schema.json").read_text())
DIR_KINDS = {"things": "thing", "people": "person", "log": "turn"}
CLOCK_FMT = "%Y-%m-%dT%H:%M"


# --- Finding and creating saves ---

def save_of(path):
    """The save folder (one holding world.json) that contains `path`, or None."""
    path = Path(path).resolve()
    return next((d for d in [path, *path.parents] if (d / "world.json").is_file()), None)


def find_save(name=None):
    """A save by name or path; else the one we're standing in; else the most recently played."""
    if name:
        path = Path(name) if Path(name).exists() else SAVES / name
        if not (path / "world.json").is_file():
            raise SystemExit(f"No save at {path}")
        return path.resolve()
    here = save_of(Path.cwd())
    if here:
        return here
    saves = [d for d in SAVES.glob("*") if (d / "world.json").is_file()]
    if not saves:
        raise SystemExit("No saves yet. Start one with: uv run tg new cornwall-1705")
    return max(saves, key=lambda d: (d / "world.json").stat().st_mtime)


def new_save(scenario, name):
    """Copy a scenario's start state into saves/<name> and make it a DM workspace."""
    dst = SAVES / name
    shutil.copytree(SCENARIOS / scenario / "start", dst)
    for sub in ("things", "people", "log", "fermi", "visuals", "sketches"):
        (dst / sub).mkdir(exist_ok=True)
    template = ROOT / "dm" / "save_template"
    (dst / "CLAUDE.md").write_text((template / "CLAUDE.md").read_text().replace("{scenario}", scenario))
    shutil.copytree(template / ".claude", dst / ".claude")
    return dst


# --- Reading ---

def read_json(path):
    """Parsed JSON, or None if the file is mid-edit or broken (validation reports it)."""
    try:
        return json.loads(Path(path).read_text())
    except json.JSONDecodeError:
        return None


def write_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def load_state(save):
    """Everything the view needs, in one JSON-able dict."""
    def folder(name):
        items = [read_json(p) for p in sorted((save / name).glob("*.json"))]
        return [i for i in items if i is not None]

    world = read_json(save / "world.json") or {}
    things = folder("things")
    for t in things:  # cache-buster for drawings
        svg = save / t.get("visual", "-")
        t["_v"] = svg.stat().st_mtime_ns if svg.is_file() else None
    briefing = SCENARIOS / world.get("scenario", "-") / "scenario.md"
    return {
        "save": save.name,
        "world": world,
        "clock_label": fmt_clock(world["clock"]) if world else "",
        "things": things,
        "people": folder("people"),
        "log": folder("log"),
        "sketches": [f"sketches/{p.name}" for p in sorted((save / "sketches").glob("*.png"))],
        "briefing": briefing.read_text() if briefing.is_file() else "",
        "problems": check_save(save),
    }


def signature(save):
    """Changes whenever any visible file in the save changes (dot-folders ignored)."""
    return hash(tuple(
        (str(p), p.stat().st_mtime_ns)
        for p in sorted(save.rglob("*"))
        if p.is_file() and not any(part.startswith(".") for part in p.relative_to(save).parts)
    ))


def next_turn(save):
    return len(list((save / "log").glob("*.json"))) + 1


def unseen_sketches(save):
    """Sketches the player saved that no turn has used yet."""
    seen = {s for p in (save / "log").glob("*.json") for s in (read_json(p) or {}).get("sketches", [])}
    sketches = (f"sketches/{p.name}" for p in sorted((save / "sketches").glob("*.png")))
    return [s for s in sketches if s not in seen]


# --- Validation ---

def validator(kind):
    return Draft202012Validator({**SCHEMA, "$ref": f"#/$defs/{kind}"})


def kind_of(rel):
    if rel == Path("world.json"):
        return "world"
    if len(rel.parts) == 2 and rel.suffix == ".json":
        return DIR_KINDS.get(rel.parts[0])


def check_file(save, path):
    """Problems with one file in a save (schema, id/file-name match, SVG well-formedness)."""
    path = Path(path).resolve()
    rel = path.relative_to(save)
    if rel.parts[0] == "visuals" and rel.suffix == ".svg":
        try:
            ElementTree.parse(path)
        except ElementTree.ParseError as e:
            return [f"{rel}: not well-formed SVG: {e}"]
        return []
    kind = kind_of(rel)
    if not kind:
        return []
    data = read_json(path)
    if data is None:
        return [f"{rel}: not valid JSON"]
    problems = [
        f"{rel}: {'/'.join(map(str, e.absolute_path)) or '(top level)'}: {e.message}"
        for e in validator(kind).iter_errors(data)
    ]
    if kind in ("thing", "person") and data.get("id") != path.stem:
        problems.append(f"{rel}: id must match the file name ({path.stem!r})")
    if kind == "turn" and path.stem != f"{data.get('turn', 0):04d}":
        problems.append(f"{rel}: turn {data.get('turn')} must live in log/{data.get('turn', 0):04d}.json")
    return problems


def check_save(save):
    """check_file for every file, plus cross-references between files."""
    problems = [p for f in sorted(save.rglob("*")) if f.is_file() for p in check_file(save, f)]
    things = {p.stem: read_json(p) for p in (save / "things").glob("*.json")}
    turns = [read_json(p) for p in sorted((save / "log").glob("*.json"))]
    world = read_json(save / "world.json") or {}

    def exists(owner, paths):
        return [f"{owner}: missing file {p}" for p in paths if not (save / p).is_file()]

    for tid, t in things.items():
        if not t:
            continue
        problems += [f"things/{tid}: unknown component {c!r}" for c in t.get("components", []) if c not in things]
        problems += exists(f"things/{tid}", t.get("fermi", []) + ([t["visual"]] if "visual" in t else []))
        if "state" in t and "states" in t and t["state"] not in t["states"]:
            problems.append(f"things/{tid}: state {t['state']!r} is not one of its states {t['states']}")
    for i, turn in enumerate(turns, 1):
        if not turn:
            continue
        if turn.get("turn") != i:
            problems.append(f"log: turns must be numbered 1, 2, 3… without gaps (found {turn.get('turn')} at position {i})")
        problems += exists(f"log/{i:04d}", turn.get("fermi", []) + turn.get("sketches", []))
        if turn.get("clock_end", "") < turn.get("clock_start", ""):
            problems.append(f"log/{i:04d}: clock_end is before clock_start")
    if turns and turns[-1] and world.get("clock", "") < turns[-1].get("clock_end", ""):
        problems.append("world.json: clock is behind the last turn's clock_end")
    return problems


# --- Money (pence) and clock ---

def fmt_money(d):
    """Pence -> '£2 3s 6d' (zero parts left out)."""
    a = abs(d)
    parts = [a >= 240 and f"£{a // 240}", a % 240 >= 12 and f"{a % 240 // 12}s", a % 12 and f"{a % 12}d"]
    return ("-" if d < 0 else "") + (" ".join(p for p in parts if p) or "0d")


def parse_money(text):
    """'£2 3s 6d', '10s', '4d', '£5' -> pence."""
    m = re.fullmatch(r"\s*(?:£\s*(\d+))?\s*(?:(\d+)\s*s)?\s*(?:(\d+)\s*d)?\s*", text)
    if not m or not any(m.groups()):
        raise SystemExit(f"Can't read {text!r} as money. Write it like '£2 3s 6d', '10s' or '4d'.")
    pounds, shillings, pence = (int(g or 0) for g in m.groups())
    return pounds * 240 + shillings * 12 + pence


def advance_clock(clock, span):
    """'1705-04-02T08:00' + '1w2d3h30m' -> the later clock string."""
    m = re.fullmatch(r"(?:(\d+)w)?(?:(\d+)d)?(?:(\d+)h)?(?:(\d+)m)?", span)
    if not span or not m:
        raise SystemExit(f"Can't read {span!r} as a time span. Write it like '3d', '4h', '1w2d', '90m'.")
    weeks, days, hours, minutes = (int(g or 0) for g in m.groups())
    later = datetime.strptime(clock, CLOCK_FMT) + timedelta(weeks=weeks, days=days, hours=hours, minutes=minutes)
    return later.strftime(CLOCK_FMT)


def fmt_clock(clock):
    """'1705-04-02T08:00' -> 'Monday 2 April 1705, 08:00'. Before Britain's 1752 switch, dates are Old Style (Julian)."""
    t = datetime.strptime(clock, CLOCK_FMT)
    julian_shift = t.year // 100 - t.year // 400 - 2 if clock < "1752-09-14" else 0
    return f"{t + timedelta(days=julian_shift):%A} {t.day} {t:%B} {t.year}, {t:%H:%M}"
