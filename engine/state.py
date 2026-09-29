"""Save folders: find, create, load and validate them. Money and clock helpers."""
import json
import os
import re
import shutil
from datetime import datetime, time, timedelta
from pathlib import Path
from xml.etree import ElementTree

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent
SAVES = ROOT / "saves"
SCENARIOS = ROOT / "scenarios"
SCHEMA = json.loads((Path(__file__).parent / "schema.json").read_text())
DIR_KINDS = {"things": "thing", "people": "person", "recipes": "recipe", "log": "turn"}
CLOCK_FMT = "%Y-%m-%dT%H:%M"


# --- Finding and creating saves ---

def save_of(path):
    """The save folder (one holding world.json) that contains `path`, or None."""
    path = Path(path).resolve()
    return next((d for d in [path, *path.parents] if (d / "world.json").is_file()), None)


def find_save(name=None):
    """A save by name or path; else the one we're standing in; else the only one there is."""
    if name:
        path = Path(name) if Path(name).exists() else SAVES / name
        if not (path / "world.json").is_file():
            raise SystemExit(f"No save at {path}")
        return path.resolve()
    here = save_of(Path.cwd())
    if here:
        return here
    saves = sorted(d.name for d in SAVES.glob("*") if (d / "world.json").is_file())
    if len(saves) == 1:
        return SAVES / saves[0]
    if not saves:
        raise SystemExit("No saves yet. Start one with: uv run tg new cornwall-1705 --name mygame")
    raise SystemExit(f"Which save? There are several: {', '.join(saves)}. Name one with --save (e.g. uv run tg --save {saves[0]} status), or run tg from inside the save's folder.")


def new_save(scenario, name):
    """Copy a scenario's start state into saves/<name> and make it a DM workspace."""
    start, dst = SCENARIOS / scenario / "start", SAVES / name
    if not start.is_dir():
        raise SystemExit(f"No scenario {scenario!r}. There are: {', '.join(sorted(d.name for d in SCENARIOS.iterdir() if d.is_dir()))}")
    if dst.exists():
        raise SystemExit(f"{dst} already exists. Pick another --name.")
    shutil.copytree(start, dst, ignore=shutil.ignore_patterns(".*"))
    for sub in ("things", "people", "recipes", "log", "fermi", "visuals", "maps", "sketches"):
        (dst / sub).mkdir(exist_ok=True)
    template = ROOT / "dm" / "save_template"
    (dst / "CLAUDE.md").write_text((template / "CLAUDE.md").read_text().replace("{scenario}", scenario))
    shutil.copy(template / "hidden.md", dst / "hidden.md")
    shutil.copytree(template / ".claude", dst / ".claude")
    return dst


# --- Reading ---

def read_json(path):
    """Parsed JSON, or None if the file doesn't exist or is mid-edit or broken (validation reports the latter)."""
    try:
        return json.loads(Path(path).read_text())
    except (FileNotFoundError, UnicodeDecodeError, json.JSONDecodeError):
        return None


def write_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def valid(save, path):
    """A state file's data if it passes check_file, else None (check_save reports why)."""
    return None if check_file(save, path) else read_json(path)


def records(save, folder):
    """The valid records in one of the save's folders: things/, people/, recipes/ or log/."""
    return [r for r in (valid(save, p) for p in sorted((save / folder).glob("*.json"))) if r is not None]


def load_state(save):
    """Everything the view needs, in one JSON-able dict. Invalid files are left out and listed in `problems`."""
    world = valid(save, save / "world.json") or {}
    things = records(save, "things")
    for t in things:  # cache-buster for drawings
        svg = save / t.get("visual", "-")
        t["_v"] = svg.stat().st_mtime_ns if svg.is_file() else None
    briefing = SCENARIOS / world.get("scenario", "-") / "scenario.md"
    return {
        "save": save.name,
        "world": world,
        "clock_label": fmt_clock(world["clock"]) if world else "",
        "things": things,
        "people": records(save, "people"),
        "recipes": records(save, "recipes"),
        "log": records(save, "log"),
        "maps": maps(save),
        "places": valid(save, save / "places.json") or {"origin": None, "places": [], "routes": []},
        "stores": (valid(save, save / "stores.json") or {"items": []})["items"],
        "visuals": {f"visuals/{p.name}": p.stat().st_mtime_ns for p in (save / "visuals").glob("*.svg")},
        "sketches": [f"sketches/{p.name}" for p in sorted((save / "sketches").glob("*.png"))],
        "briefing": briefing.read_text() if briefing.is_file() else "",
        "problems": check_save(save),
    }


def maps(save):
    """The save's maps, each titled by its SVG <title> (else its file name)."""
    def title(p):
        m = re.search(r"<title>(.*?)</title>", p.read_text(), re.S)
        return m[1].strip() if m else p.stem.replace("-", " ").capitalize()
    return [{"id": p.stem, "visual": f"maps/{p.name}", "_v": p.stat().st_mtime_ns, "title": title(p)} for p in sorted((save / "maps").glob("*.svg"))]


def visible_files(save):
    """Every file in the save outside dot-folders (.history, .claude, .shots), which aren't walked at all."""
    for folder, dirs, files in os.walk(save):
        dirs[:] = sorted(d for d in dirs if not d.startswith("."))
        yield from (Path(folder) / f for f in sorted(files) if not f.startswith("."))


def signature(save):
    """Changes whenever any visible file in the save changes."""
    return hash(tuple((str(p), p.stat().st_mtime_ns) for p in visible_files(save)))


def next_turn(save):
    return len(list((save / "log").glob("*.json"))) + 1


def unseen_sketches(save):
    """Sketches the player saved that no turn has used yet."""
    seen = {s for turn in records(save, "log") for s in turn.get("sketches", [])}
    sketches = (f"sketches/{p.name}" for p in sorted((save / "sketches").glob("*.png")))
    return [s for s in sketches if s not in seen]


# --- Validation ---

def validator(kind):
    return Draft202012Validator({**SCHEMA, "$ref": f"#/$defs/{kind}"})


def kind_of(rel):
    if rel in (Path("world.json"), Path("places.json"), Path("stores.json")):
        return rel.stem
    if len(rel.parts) == 2 and rel.suffix == ".json":
        return DIR_KINDS.get(rel.parts[0])


def check_file(save, path):
    """Problems with one file in a save: schema, id matching the file name, well-formed SVG. Bad content is
    reported, never raised, because the Claude Code hook relies on this to block bad writes."""
    path, save = Path(path).resolve(), Path(save).resolve()
    rel = path.relative_to(save)
    if rel.parts[0] in ("visuals", "maps") and rel.suffix == ".svg":
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
    if problems:
        return problems  # the checks below assume the right shape
    if kind in ("thing", "person", "recipe") and data["id"] != path.stem:
        problems.append(f"{rel}: id must match the file name ({path.stem!r})")
    if kind == "turn" and path.stem != f"{data['turn']:04d}":
        problems.append(f"{rel}: turn {data['turn']} must live in log/{data['turn']:04d}.json")
    return problems


def check_save(save):
    """check_file for every file, plus cross-references between the valid ones."""
    save = Path(save).resolve()
    problems = [p for f in visible_files(save) for p in check_file(save, f)]
    things = {t["id"]: t for t in records(save, "things")}
    people = {p["id"] for p in records(save, "people")}
    recipes = {r["id"]: r for r in records(save, "recipes")}
    world = valid(save, save / "world.json")

    def exists(owner, paths):
        return [f"{owner}: missing file {p}" for p in paths if not (save / p).is_file()]

    for tid, t in things.items():
        problems += [f"things/{tid}: unknown component {c!r}" for c in t.get("components", []) if c not in things]
        problems += exists(f"things/{tid}", t.get("fermi", []) + ([t["visual"]] if "visual" in t else []))
        if "state" in t and "states" in t and t["state"] not in t["states"]:
            problems.append(f"things/{tid}: state {t['state']!r} is not one of its states {t['states']}")
        recipe = t.get("made", {}).get("recipe")
        if recipe and recipe not in recipes:
            problems.append(f"things/{tid}: unknown recipe {recipe!r}")
    for rid, r in recipes.items():
        problems += [f"recipes/{rid}: unknown tool {x!r}" for x in r.get("tools", []) if x not in things]
        problems += [f"recipes/{rid}: unknown person {x!r}" for x in r.get("people", []) if x not in people]
        if "first_made" in r and r["first_made"] not in things:
            problems.append(f"recipes/{rid}: unknown first_made thing {r['first_made']!r}")
    names = [p.stem for p in sorted((save / "log").glob("*.json"))]
    if names != [f"{i:04d}" for i in range(1, len(names) + 1)]:
        problems.append("log: turn files must be numbered 0001, 0002, 0003… without gaps")
    turns = records(save, "log")
    for turn in turns:
        name = f"log/{turn['turn']:04d}"
        problems += exists(name, turn.get("fermi", []) + turn.get("sketches", []) + turn.get("visuals", []))
        problems += [f"{name}: measurements name unknown thing {m['thing']!r}"
                     for m in turn.get("measurements", []) if "thing" in m and m["thing"] not in things]
        if turn["clock_end"] < turn["clock_start"]:
            problems.append(f"{name}: clock_end is before clock_start")
    if turns and world and world["clock"] < turns[-1]["clock_end"]:
        problems.append("world.json: clock is behind the last turn's clock_end")
    return problems + check_places(save, things)


def plain(text):
    """Lower-case, single-spaced, without a leading "the" or "your". Place names match map labels this way
    (web/app.js does the same)."""
    return re.sub(r"^(the|your) ", "", " ".join(text.lower().split()))


def map_labels(svg_path):
    """The text of each <text> element on a map, made plain."""
    root = ElementTree.parse(svg_path).getroot()
    return [plain("".join(t.itertext())) for t in root.iter("{http://www.w3.org/2000/svg}text")]


def check_places(save, things):
    gazetteer = valid(save, save / "places.json")
    if not gazetteer:
        return []
    places = {p["id"]: p for p in gazetteer["places"]}
    labels = {p.stem: map_labels(p) for p in (save / "maps").glob("*.svg") if not check_file(save, p)}
    problems = [] if gazetteer["origin"] in places else [f"places.json: origin {gazetteer['origin']!r} is not a place"]
    for p in places.values():
        for m in p["maps"]:
            if m not in labels:
                problems.append(f"places.json: {p['id']} is on map {m!r}, but maps/{m}.svg doesn't exist")
            elif not any(plain(p["name"]) in label for label in labels[m]):
                problems.append(f"places.json: {p['name']!r} isn't labelled on maps/{m}.svg")
        if "thing" in p and p["thing"] not in things:
            problems.append(f"places.json: {p['id']} links to unknown thing {p['thing']!r}")
    for r in gazetteer["routes"]:
        problems += [f"places.json: route {r['from']}–{r['to']} uses unknown place {end!r}" for end in (r["from"], r["to"]) if end not in places]
    return problems


# --- Money (pence, 100p = £1) and clock ---

def fmt_money(p):
    """Pence -> '£47.18', '£50', '45p'."""
    sign, a = ("-" if p < 0 else ""), abs(p)
    if a < 100:
        return f"{sign}{a}p"
    return f"{sign}£{a // 100}" + (f".{a % 100:02d}" if a % 100 else "")


def parse_money(text):
    """'£3.25', '3.25', '£3', '45p' -> pence."""
    m = re.fullmatch(r"\s*£?\s*(\d+)(?:\.(\d{1,2}))?\s*", text)
    if m:
        return int(m[1]) * 100 + int((m[2] or "0").ljust(2, "0"))
    m = re.fullmatch(r"\s*(\d+)\s*p\s*", text)
    if m:
        return int(m[1])
    raise SystemExit(f"Can't read {text!r} as money. Write it like '£3.25', '£3' or '45p'.")


def advance_clock(clock, span):
    """'1705-04-02T08:00' + '1w2d3h30m' -> the later clock string."""
    m = re.fullmatch(r"(?:(\d+)w)?(?:(\d+)d)?(?:(\d+)h)?(?:(\d+)m)?", span)
    if not span or not m:
        raise SystemExit(f"Can't read {span!r} as a time span. Write it like '3d', '4h', '1w2d', '90m'.")
    weeks, days, hours, minutes = (int(g or 0) for g in m.groups())
    later = datetime.strptime(clock, CLOCK_FMT) + timedelta(weeks=weeks, days=days, hours=hours, minutes=minutes)
    return later.strftime(CLOCK_FMT)


def weekday(t):
    """The real weekday of a clock time. Before Britain's 1752 switch, dates are Old Style (Julian)."""
    julian_shift = t.year // 100 - t.year // 400 - 2 if t < datetime(1752, 9, 14) else 0
    return f"{t + timedelta(days=julian_shift):%A}"


def fmt_clock(clock):
    """'1705-04-02T08:00' -> 'Monday 2 April 1705, 08:00'."""
    t = datetime.strptime(clock, CLOCK_FMT)
    return f"{weekday(t)} {t.day} {t:%B} {t.year}, {t:%H:%M}"


def paydays(start, end):
    """Saturday evenings (18:00) passed between two clock times: when weekly wages fall due."""
    t0, t1 = (datetime.strptime(c, CLOCK_FMT) for c in (start, end))
    evenings = (datetime.combine(t0.date() + timedelta(days=i), time(18)) for i in range((t1 - t0).days + 2))
    return [e for e in evenings if t0 < e <= t1 and weekday(e) == "Saturday"]
