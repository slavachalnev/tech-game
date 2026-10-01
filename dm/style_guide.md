# Drawing style guide: the engineer's notebook

Every drawing looks like a page from a careful 18th-century engineer's notebook: iron-gall ink on warm paper, precise but hand-made. The view supplies the paper, so drawings have **transparent backgrounds**.

## How a drawing is made: the drawing kit

Every drawing of a thing, a project or a site is a short Python script in the save, `drawings/<id>.py`, written with the drawing kit (`engine/draw.py`; its docstrings are the reference). `uv run tg draw <id>` runs it and writes `visuals/<id>.svg`; `uv run tg draw` runs them all.

- **Parts are drawn once.** Each part is a function in `drawings/parts.py`, in millimetres with y up and its origin stated in its docstring. Its own sheet and every machine or site it's in call the same function, so it has the same shape and faces the same way everywhere: the drawing board opens it in place, lined up. When a part changes (re-bored, patched, enlarged), edit its function and run `uv run tg draw`, and every drawing showing it follows.
- **Stock parts** for everything that isn't the player's invention: `from engine.stock import person, barrel, pipe, cock, wheel, fire, ...`, true size in millimetres. The catalogue is `../../dm/stock.png`: read it before drawing.
- **The kit does the house style**: it fits the object to the sheet, washes and hatches by material, lays labels out in the margins with leader lines, and adds dimensions, flaw rings, the cartouche and a scale bar. It also writes the marks the view reads, so you never write them by hand.

```python
# drawings/parts.py
def cylinder(p, cut=False):
    """The 10 cm cylinder. Origin: the middle of its base."""
    p.rect(-57, 0, 114, 250, "brass", cut=cut)
    if cut:
        p.rect(-50, 12, 100, 238, "paper")  # the bore
    p.anchor("boss", -57, 30)

# drawings/cylinder-10cm.py
from engine.draw import Sheet
from parts import cylinder

s = Sheet("cylinder-10cm", "10 cm cylinder", "Half section")
c = s.place(cylinder, cut=True)
s.label("boss for the steam inlet, drilled", c["boss"])
s.flaw("bore tapers 0.4 mm", c.at(50, 200))
s.dim(c.at(-57, 0), c.at(-57, 250))
s.save()
```

A Pen draws `rect`, `circle`, `ellipse`, `poly`, `line`, `path` and `text`, places other parts with `part(fn, at, thing=...)`, and names points with `anchor`. Materials are `brass`, `copper`, `iron`, `lead`, `timber`, `leather`, `masonry`, `earth`, `water`, `steam`, `fire` and `paper` (to blank out); `cut=True` hatches a cut surface. Lines are `outline`, `detail`, `faint`, `hidden`, `centre` and `red`. Draw back to front: a washed shape hides what's drawn before it, except `water`, `steam` and `fire`, which you see through. A Sheet places parts with `place(fn, at, thing=...)`, draws loose geometry with `s.draw`, and takes `label`, `flaw`, `dim` and `note`. A second view (from above, a cross-section, an enlarged detail) goes in `s.inset(fn, at, scale=2, title="...")`: it sits beside the object and the board ignores it when lining parts up. On a wide drawing such as a site, labels read better in rows: `side="above"` or `"below"`; `dim` takes a `side` too. A part's named points reach out through the parts it's placed in: `mill["cutter-head.edge"]`.

## What to draw

- **A machine:** an elevation, or a section when the inside matters. Place each component as its own part with `thing="<id>"`, so the player can click through to it, and draw it open in place. Label what matters in plain modern words, put each flaw from the spec sheet where it is (`s.flaw`), and give the main dimensions.
- **A component:** its own sheet places the same part function as the machine does, often `cut=True`, with its labels and dimensions.
- **More sheets of one thing.** One drawing shouldn't carry everything. A machine can have other sheets beside its main drawing: how it works (the steps of its cycle), its valve gear, the layout of a site, written with `Sheet("<id>", "...", sheet="how-it-works")` to `visuals/<id>--how-it-works.svg`. The player sees them as tabs on the thing's sheet. Parts placed with `thing=` open from any of them.
- **A project** (a machine being gathered and built): a general arrangement placing every part with `thing=`, including the parts not yet made, drawn as planned. The board draws parts not in hand as pale blueprint ghosts, so the drawing shows how the project stands; nothing needs redrawing as parts arrive. Mark what isn't settled yet in a `note`.
- **A site** (the workshop, a mine yard): a cutaway or side view at true scale, placing every thing there with `thing=`, using the same part functions as the things' own drawings. People who work there are stock `person` figures, as illustration. Lay things side by side rather than one in front of another: on the board, a thing whose outline sits mostly inside another's looks like a part of it. A site grows with play: add or remove a placement as things come and go.
- **Tools, materials and documents:** a simple still life with a label or two.
- **Scenes** (`scene-<slug>`): the journal's illustrations of moments, with people. The kit and stock work for these too.

## States, steps, time of day, sound

- **States:** `with p.state("running"):` around what differs by state. It follows the nearest marked thing around it that has states (the engine drawn in the smithy runs when the engine runs), else the drawing's own thing. The view shows the thing's current state, and the player can switch to its other `states`.
- **Animation**, inside the states that move: `p.spin` (either way), `p.rock` (a beam), `p.slide` (a piston), `p.feed` (a steady one-way creep, or stripes running along a turning shaft), `p.drift` (a puff), `p.flicker` (fire), and `p.during(0.2, 0.6, seconds)` for what shows only for part of a cycle (a valve open, a puff at the top of the stroke). `delay=` shifts one within the cycle; `p.clip(x, y, w, h)` shows only what's inside a rectangle (a bore growing behind a cutter). Give everything in one machine the same `seconds`. Keep it slow and legible: a stroke takes 2–5 s.
- **A thing without states** shares the state of what it's part of: the forge is lit when the smithy is.
- **Steps** of a working cycle: `with s.step(n, "caption"):`, three to six of them, on a sheet of their own (`sheet="how-it-works"`), not as a state: a state is how the thing really is. Draw what doesn't move once, and in each step only what changes: valves open or shut, flows as washes, the moving parts where they are.
- **Time of day** (sites and scenes): `with p.sky("night"):` (or `"day"`, `"dawn dusk"`). Stock has `sky`, `night` (a dark wash with pools of light) and `rain`.
- **Sound:** `with p.sound("engine"):` (or `fire`, `water`, `hammer`, `wind`) around something that shows; the board plays it while that drawing is in view.

## Checking

- `uv run tg shot <id>` and Read the PNG (another sheet: `<id>--how-it-works`); add `--state running`, `--time night`, `--step 2`, `--at 1.5` (seconds into its animation) or `--set <thing>=<state>` for the others, and `--hotspots` to outline what's marked.
- `uv run tg shot board/<id> --half`: the part's drawing half open over its machine's. If both come from the same part function, they line up.
- Fix what reads badly: crowded labels (shorter words, or `side="left"`), a tiny object (draw less around it), clashing washes. Two or three rounds.

## Palette

| Use | Colour |
|---|---|
| Ink: outlines, text | `#2b2118` |
| Faded ink: hatching, dimension lines, hidden lines | `#7a6a55` |
| Red ochre: flaws, leaks, cracks, warnings, annotations | `#9c3b25` |
| Water (wash) | `#4f7390`, fill-opacity 0.25–0.45 |
| Fire, heat (wash) | `#c0662b`, fill-opacity 0.3–0.6 |
| Steam (wash) | `#9aa5a8`, fill-opacity 0.3 |
| Brass or copper (wash) | `#b08d3c` |
| Iron (wash) | `#56514b` |
| Timber (wash) | `#9a7446` |
| Earth or rock (wash) | `#8a7a62` |

Washes are pale fills under ink outlines. Never fill a shape with solid ink.

## Line and type

The kit draws these; they matter when drawing by hand.

- Outlines are 2 px. Details are 1.2 px. Hatching is 0.6 px at 45°, about 5 px apart, in faded ink. Dimension lines are 0.8 px with small arrowheads.
- Cut surfaces in sections are hatched: diagonal for metal, grain-like strokes for timber, stipple for masonry or earth.
- Text: Georgia, italic, 13–16 px, in ink. Titles in small caps at 18–22 px. Labels in plain modern words; dimensions in metric (mm for small parts, m for large).

## Maps

- Same ink-on-paper style. North is up. Every map has a compass mark, a scale bar in km and a `<title>` element (the name shown in the view's Map tab).
- **Coast:** an ink line with a pale water wash on the sea side, plus a few short parallel ripple strokes. **Hills:** small hachured bumps. **Rivers and streams:** thin water-coloured lines. **Roads:** fine ink lines; **tracks:** dashed.
- **Towns:** small filled squares, sized by importance, labelled in italic. **Mines:** a tiny headframe (or ⚒). **The player's base:** a red-ochre star.
- Places the player hasn't visited but has heard of can be drawn with a dotted outline or a "?".
- Places off the map's edge get an arrow at the edge: "London, 430 km, 7–9 days".

## Drawing by hand

Maps, and anything the kit can't do, are written as SVG by hand. The view reads these marks; keep them right:

- `<g data-thing="<id>">` around a thing or part (or an invisible outline over it), `<g data-object="">` around the object itself without its labels (the empty value keeps it valid XML), `data-state="running"`, `data-step="1" data-caption="..."`, `data-sky="night"`, `data-sound="engine"`, and `data-person="<id>"` for people.
- Drawings are shown as images: no scripts, external files or web fonts.
- **Straight lines can vanish under the ink filter** unless `#ink` is defined with `filterUnits="userSpaceOnUse" x="0" y="0" width="100%" height="100%"` and put on an outer group in the drawing's own coordinates.
- **SMIL `keyTimes` must start at 0 and end at 1**, with as many entries as `values`, or the browser silently ignores the animation.
