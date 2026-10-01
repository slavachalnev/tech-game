"""The drawing kit: the game's drawings in the house style, written as short scripts in a save's drawings/ folder.

A part is drawn by a function, in millimetres with y up and the origin wherever suits it (the middle of its base,
say). The same function draws the part on its own sheet and inside every machine or site it belongs to, so it has
the same shape and faces the same way everywhere: that is what lets the drawing board open a part in place. The kit
supplies the house style (ink, washes, section hatching, line weights) and the marks the view reads (data-thing,
data-object, data-state, data-step, data-sky, data-sound). It fits the object to the sheet, lays labels out in the
margins with leader lines, and adds dimensions, the cartouche and a scale bar. Everything you give is in millimetres.

    # drawings/parts.py
    def cylinder(p, cut=False):                       # origin: the middle of its base
        p.rect(-57, 0, 114, 250, "brass", cut=cut)
        if cut:
            p.rect(-50, 12, 100, 238, "paper")        # the bore
        p.anchor("boss", -57, 30)

    # drawings/cylinder-10cm.py
    from engine.draw import Sheet
    from parts import cylinder

    s = Sheet("cylinder-10cm", "10 cm cylinder", "Half section")
    c = s.place(cylinder, cut=True)
    s.label("boss for the steam inlet, drilled", c["boss"])
    s.dim(c.at(-57, 0), c.at(-57, 250))
    s.save()

Run it with `uv run tg draw cylinder-10cm` (or `uv run tg draw` for all, after changing parts.py).
"""
import math
from contextlib import contextmanager
from pathlib import Path

INK, FADED, RED, PAPER = "#2b2118", "#7a6a55", "#9c3b25", "#f8f1e1"
# Washes, from the style guide's palette: (colour, opacity), and the hatching for a cut surface of that material.
WASH = {
    "brass": ("#b08d3c", 0.4), "copper": ("#b07a3c", 0.4), "iron": ("#56514b", 0.3), "lead": ("#7d8288", 0.35),
    "timber": ("#9a7446", 0.35), "leather": ("#7a5230", 0.4), "masonry": ("#8a7a62", 0.2), "earth": ("#8a7a62", 0.3),
    "water": ("#4f7390", 0.35), "steam": ("#9aa5a8", 0.3), "fire": ("#c0662b", 0.5), "paper": (PAPER, 1.0),
    "brick": ("#a8664a", 0.3),
}  # a material can also be given as a (colour, opacity) pair
SEE_THROUGH = {"water", "steam", "fire"}  # washes that show what's drawn behind them; the others hide it
CUT = {"brass": "metal", "copper": "metal", "iron": "metal", "lead": "metal", "timber": "grain", "masonry": "stipple", "earth": "stipple", "brick": "stipple"}
LINES = {  # (colour, width in px, dashes in px)
    "outline": (INK, 2.0, None), "detail": (INK, 1.2, None), "faint": (FADED, 0.9, None), "hidden": (FADED, 1.0, "6 4"),
    "centre": (FADED, 0.8, "14 4 2 4"), "red": (RED, 1.3, None), "none": (None, 0, None),
}


def num(v):
    if not isinstance(v, float):
        return str(v)
    v = f"{v:.3f}".rstrip("0").rstrip(".")
    return "0" if v == "-0" else v


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def wrap(text, width):
    """Words into lines of at most about `width` characters."""
    lines, line = [], ""
    for word in str(text).split():
        if line and len(line) + 1 + len(word) > width:
            lines.append(line)
            line = word
        else:
            line = f"{line} {word}".strip()
    return lines + [line] if line else lines


class Fine:
    """Detail shown only if `mm` comes to at least 4 px on the finished sheet (`coarse`: only if it doesn't). The
    scale is known only when the sheet is written, so this decides then."""

    def __init__(self, sheet, mm, out, coarse):
        self.sheet, self.mm, self.out, self.coarse = sheet, mm, out, coarse

    def __str__(self):
        return "".join(map(str, self.out)) if (self.mm * self.sheet.k >= 4) != self.coarse else ""


class Placed:
    """A part where it was put: its named points, in the sheet's millimetres."""

    def __init__(self, pen):
        self.pen = pen

    def __getitem__(self, name):
        return self.pen.anchors[name]

    def at(self, x, y):
        """A point given in the part's own millimetres, in the sheet's."""
        return self.pen.mm(x, y)


class Pen:
    """Draws in millimetres, y up, in the house style, into the current group. A part function gets one."""

    def __init__(self, sheet, T, out):
        self.sheet, self.T, self.out, self.anchors = sheet, T, out, {}  # T: this pen's mm -> the sheet's mm

    def mm(self, x, y):
        a, b, c, d, e, f = self.T
        return a * x + c * y + e, b * x + d * y + f

    def _reach(self, *pts):
        for p in pts:
            self.sheet.reach(*self.mm(*p))

    # ---- shapes
    def _shape(self, tag, attrs, material, cut, line, fill):
        colour, width, dash = LINES[line]
        wash, opacity = WASH[material] if isinstance(material, str) else material or (None, None)
        paint = f'fill="{wash}" fill-opacity="{num(opacity)}"' if material else f'fill="{fill or "none"}"'
        stroke = f' stroke="{colour}" stroke-width="{num(width)}" vector-effect="non-scaling-stroke" stroke-linejoin="round" stroke-linecap="round"' if colour else ' stroke="none"'
        dashes = f' stroke-dasharray="{dash}"' if dash else ""
        if material and material not in SEE_THROUGH and opacity < 1:  # paper under the wash: what's in front hides what's behind
            self.out.append(f'<{tag} {attrs} fill="{PAPER}" stroke="none"/>')
        self.out.append(f"<{tag} {attrs} {paint}{stroke}{dashes}/>")
        if cut and material in CUT:
            self.out.append(f'<{tag} {attrs} fill="url(#{CUT[material]})" stroke="none"/>')

    def rect(self, x, y, w, h, material=None, *, cut=False, line="outline", fill=None):
        """A rectangle from its lower-left corner (x, y), w wide and h tall. `material` washes it; `cut` hatches
        it as a cut surface (metal, timber or masonry)."""
        x, y, w, h = min(x, x + w), min(y, y + h), abs(w), abs(h)
        self._reach((x, y), (x + w, y + h))
        self._shape("rect", f'x="{num(x)}" y="{num(y)}" width="{num(w)}" height="{num(h)}"', material, cut, line, fill)

    def circle(self, cx, cy, r, material=None, *, cut=False, line="outline", fill=None):
        self._reach((cx - r, cy - r), (cx + r, cy + r))
        self._shape("circle", f'cx="{num(cx)}" cy="{num(cy)}" r="{num(r)}"', material, cut, line, fill)

    def ellipse(self, cx, cy, rx, ry, material=None, *, cut=False, line="outline", fill=None):
        self._reach((cx - rx, cy - ry), (cx + rx, cy + ry))
        self._shape("ellipse", f'cx="{num(cx)}" cy="{num(cy)}" rx="{num(rx)}" ry="{num(ry)}"', material, cut, line, fill)

    def poly(self, points, material=None, *, closed=True, cut=False, line="outline", fill=None):
        self._reach(*points)
        pts = " ".join(f"{num(x)},{num(y)}" for x, y in points)
        self._shape("polygon" if closed else "polyline", f'points="{pts}"', material, cut, line, fill)

    def line(self, x1, y1, x2, y2, line="detail"):
        self.poly([(x1, y1), (x2, y2)], closed=False, line=line)

    def path(self, d, material=None, *, reach=(), cut=False, line="outline", fill=None):
        """Raw SVG path data in millimetres, y up. Give `reach` (a few points it spans) if it's at an edge."""
        self._reach(*reach)
        self._shape("path", f'd="{d}"', material, cut, line, fill)

    def text(self, s, x, y, size=13, anchor="start", italic=True, colour=INK):
        """Words at a point of the part, set upright on the sheet."""
        self.sheet.texts.append((s, self.mm(x, y), size, anchor, italic, colour, list(self.sheet.conditions)))

    def anchor(self, name, x, y):
        """Name a point of the part, for labels and dimensions: placed["name"]."""
        self.anchors[name] = self.mm(x, y)

    def uid(self, stem):
        """An id no other on the sheet has, for a gradient or a mask drawn with raw()."""
        self.sheet.ids += 1
        return f"{self.sheet.id}-{stem}-{self.sheet.ids}"

    def raw(self, svg, reach=()):
        """Raw SVG in millimetres, y up, for what the kit doesn't draw (a gradient, a mask); `reach`: points it spans."""
        self._reach(*reach)
        self.out.append(svg)

    # ---- parts inside parts
    def part(self, draw, at=(0, 0), *, thing=None, flip=False, rotate=0, **kwargs):
        """Draw another part inside this one with its origin at `at`, mirrored left to right if `flip`, turned
        `rotate` degrees anticlockwise about its origin; `thing` marks it, for the board. (A part with its own
        drawing should be drawn the same way round in both, for the board to open it in place.)"""
        a, b, c, d, e, f = self.T
        co, si, sx = math.cos(math.radians(rotate)), math.sin(math.radians(rotate)), -1 if flip else 1
        la, lb, lc, ld = co * sx, si * sx, -si, co  # translate(at) rotate(rotate) scale(sx, 1)
        inner = Pen(self.sheet, (a * la + c * lb, b * la + d * lb, a * lc + c * ld, b * lc + d * ld, a * at[0] + c * at[1] + e, b * at[0] + d * at[1] + f), [])
        draw(inner, **kwargs)
        mark = f' data-thing="{thing}"' if thing else ""
        turn = f" rotate({num(float(rotate))})" if rotate else ""
        self.out += [f'<g{mark} transform="translate({num(at[0])} {num(at[1])}){turn}{" scale(-1 1)" if flip else ""}">', *inner.out, "</g>"]
        return Placed(inner)

    # ---- what shows when, and how it moves
    @contextmanager
    def _group(self, attrs, tail=""):
        outer, self.out = self.out, []
        self.sheet.conditions.append(attrs)
        try:
            yield
        finally:
            self.sheet.conditions.pop()
            inner, self.out = self.out, outer
            self.out += [f"<g {attrs}>", *inner, f"{tail}</g>"]

    @contextmanager
    def _fine(self, mm, coarse):
        outer, self.out = self.out, []
        try:
            yield
        finally:
            inner, self.out = self.out, outer
            self.out.append(Fine(self.sheet, mm, inner, coarse))

    def fine(self, mm):
        """Fine detail (staves, rope lay, brick courses), drawn only if `mm`, its spacing, comes to at least 4 px on
        the sheet, so a small part doesn't turn to mush. Words written with text() inside still show."""
        return self._fine(mm, False)

    def coarse(self, mm):
        """What to draw instead where fine(mm) detail is left out: a gear's pitch circle for its teeth, say."""
        return self._fine(mm, True)

    def state(self, *names):
        """Only in these states (of the nearest marked thing around it that has states, else the drawing's own)."""
        return self._group(f'data-state="{" ".join(names)}"')

    def step(self, n, caption):
        """Step n of a working cycle, shown one at a time with its caption."""
        return self._group(f'data-step="{n}" data-caption="{esc(caption)}"')

    def sky(self, *times):
        """Only at these times of day: dawn, day, dusk, night."""
        return self._group(f'data-sky="{" ".join(times)}"')

    def sound(self, kind):
        """Heard while this shows: fire, engine, water, hammer or wind."""
        return self._group(f'data-sound="{kind}"')

    def spin(self, cx, cy, seconds):
        """Turns steadily about (cx, cy)."""
        return self._group("", f'<animateTransform attributeName="transform" type="rotate" from="0 {num(cx)} {num(cy)}" to="-360 {num(cx)} {num(cy)}" dur="{seconds}s" repeatCount="indefinite"/>')

    def rock(self, cx, cy, degrees, seconds):
        """Rocks by ±degrees about (cx, cy), like a beam."""
        v = ";".join(f"{num(float(a))} {num(cx)} {num(cy)}" for a in (degrees, -degrees, degrees))
        return self._group("", f'<animateTransform attributeName="transform" type="rotate" values="{v}" keyTimes="0;0.5;1" calcMode="spline" keySplines="0.45 0 0.55 1;0.45 0 0.55 1" dur="{seconds}s" repeatCount="indefinite"/>')

    def slide(self, dx, dy, seconds):
        """Slides by (dx, dy) and back, like a piston."""
        return self._group("", f'<animateTransform attributeName="transform" type="translate" values="0 0;{num(dx)} {num(dy)};0 0" keyTimes="0;0.5;1" calcMode="spline" keySplines="0.45 0 0.55 1;0.45 0 0.55 1" dur="{seconds}s" repeatCount="indefinite"/>')

    def drift(self, dx, dy, seconds, delay=0, grow=1):
        """Drifts by (dx, dy), growing `grow` times about this pen's origin and fading in and out, over and over,
        like a puff of steam; `delay` (seconds) staggers several."""
        begin = f' begin="-{num(float(delay))}s"' if delay else ""
        times = f'dur="{seconds}s"{begin} repeatCount="indefinite"'
        scale = f'<animateTransform attributeName="transform" type="scale" values="1;{num(float(grow))}" additive="sum" {times}/>' if grow != 1 else ""
        return self._group("", f'<animateTransform attributeName="transform" type="translate" values="0 0;{num(dx)} {num(dy)}" {times}/>{scale}'
                               f'<animate attributeName="opacity" values="0;1;0.8;0" keyTimes="0;0.2;0.6;1" {times}/>')

    def flicker(self, seconds=1.3):
        """Flickers, like fire."""
        return self._group("", f'<animate attributeName="opacity" values="1;0.6;0.95;0.7;1" keyTimes="0;0.25;0.5;0.75;1" dur="{seconds}s" repeatCount="indefinite"/>')


class Sheet:
    """One drawing, visuals/<id>.svg. Draw on it with place() (parts) and draw (its own pen), then label it. The
    object is fitted to the sheet with room for the labels, unless you fix `px_per_mm` yourself (to keep the scale
    of a set of drawings the same, say)."""

    def __init__(self, id, title, subtitle="", *, size=(1600, 1200), px_per_mm=None):
        self.id, self.title, self.subtitle, (self.W, self.H), self.fixed = id, title, subtitle, size, px_per_mm
        self.texts, self.labels, self.flaws, self.dims, self.notes, self.conditions, self.box = [], [], [], [], [], [], None
        self.ids, self.k = 0, None
        self.draw = Pen(self, (1, 0, 0, 1, 0, 0), [])  # the sheet's own pen; everything drawn is the object

    def reach(self, x, y):
        b = self.box or [x, y, x, y]
        self.box = [min(b[0], x), min(b[1], y), max(b[2], x), max(b[3], y)]

    def place(self, draw, at=(0, 0), *, thing=None, flip=False, rotate=0, **kwargs):
        """Draw a part (a function taking a Pen) with its origin at `at`; `thing` marks it, for the board."""
        return self.draw.part(draw, at, thing=thing, flip=flip, rotate=rotate, **kwargs)

    # What shows when, around parts placed on the sheet: with s.state("running"): s.place(...).
    def state(self, *names):
        return self.draw.state(*names)

    def step(self, n, caption):
        return self.draw.step(n, caption)

    def sky(self, *times):
        return self.draw.sky(*times)

    def sound(self, kind):
        return self.draw.sound(kind)

    # ---- round the object, in millimetres
    def label(self, text, at, *, colour=INK, side=None, width=28):
        """A label in the margin, with a leader to `at` (e.g. placed["boss"] or placed.at(x, y))."""
        self.labels.append((text, at, colour, side, width, list(self.conditions)))

    def flaw(self, text, at, **kw):
        """A flaw: a red ring where it is, and a red label."""
        self.flaws.append((at, list(self.conditions)))
        self.label(text, at, colour=RED, **kw)

    def dim(self, a, b, text=None, *, offset=22):
        """A dimension line between two points, `offset` px off to the side away from the object's middle; the
        text is the length in mm unless given."""
        self.dims.append((a, b, text or f"{math.hypot(b[0] - a[0], b[1] - a[1]):.0f} mm", offset, list(self.conditions)))

    def note(self, title, text):
        """A block of notes (How it works, say), set at the bottom left."""
        self.notes.append((title, text))

    # ---- fitting and writing
    def _fit(self):
        """px per mm and where the sheet's mm (0, 0) falls, so the object fills the space the labels leave."""
        x0, y0, x1, y1 = self.box or (0, 0, 100, 100)
        mid = (x0 + x1) / 2
        left = any((s or ("left" if at[0] < mid else "right")) == "left" for _, at, _, s, *_ in self.labels)
        right = any((s or ("left" if at[0] < mid else "right")) == "right" for _, at, _, s, *_ in self.labels)
        note_h = sum(36 + 16 * len(wrap(t, 60)) for _, t in self.notes)
        L, R, T, B = (300 if left else 70), (300 if right else 70), 60, 120 + note_h
        w, h = max(x1 - x0, 1), max(y1 - y0, 1)
        k = self.fixed or min((self.W - L - R) / w, (self.H - T - B) / h)
        ox = L + (self.W - L - R - w * k) / 2 - x0 * k
        oy = T + (self.H - T - B - h * k) / 2 + y1 * k
        return k, ox, oy

    def svg(self):
        k, ox, oy = self._fit()
        self.k = k
        px = lambda p: (ox + p[0] * k, oy - p[1] * k)  # noqa: E731
        within = lambda el, conds: "".join(f"<g {c}>" for c in conds if c) + el + "</g>" * sum(1 for c in conds if c)  # noqa: E731
        s = 1 / k  # one px, in millimetres
        defs = (f'<filter id="ink" filterUnits="userSpaceOnUse" x="0" y="0" width="{self.W}" height="{self.H}"><feTurbulence type="fractalNoise" baseFrequency="0.035" numOctaves="2" seed="7"/><feDisplacementMap in="SourceGraphic" scale="2"/></filter>'
                f'<marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,1 L10,5 L0,9" fill="none" stroke="{FADED}" stroke-width="1.2"/></marker>'
                f'<pattern id="metal" width="{num(6 * s)}" height="{num(6 * s)}" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="{num(6 * s)}" stroke="{FADED}" stroke-width="{num(0.7 * s)}"/></pattern>'
                f'<pattern id="grain" width="{num(8 * s)}" height="{num(5 * s)}" patternUnits="userSpaceOnUse"><path d="M0,{num(4 * s)} Q{num(2 * s)},0 {num(4 * s)},{num(2.5 * s)} T{num(8 * s)},{num(s)}" fill="none" stroke="{FADED}" stroke-width="{num(0.6 * s)}"/></pattern>'
                f'<pattern id="stipple" width="{num(9 * s)}" height="{num(9 * s)}" patternUnits="userSpaceOnUse"><circle cx="{num(2 * s)}" cy="{num(3 * s)}" r="{num(0.7 * s)}" fill="{FADED}"/><circle cx="{num(6.5 * s)}" cy="{num(7 * s)}" r="{num(0.6 * s)}" fill="{FADED}"/></pattern>')
        texts = "".join(within(f'<text x="{num(px(at)[0])}" y="{num(px(at)[1])}" font-size="{size}" text-anchor="{anchor}"{" font-style=\"italic\"" if italic else ""} fill="{colour}">{esc(t)}</text>', conds)
                        for t, at, size, anchor, italic, colour, conds in self.texts)
        rings = "".join(within(f'<circle cx="{num(px(at)[0])}" cy="{num(px(at)[1])}" r="11" fill="none" stroke="{RED}" stroke-width="1.2" stroke-dasharray="3 2"/>', conds) for at, conds in self.flaws)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.W} {self.H}" font-family="Georgia, \'Times New Roman\', serif">\n<title>{esc(self.title)}</title>\n'
                f'<!-- Made with the drawing kit from drawings/{self.id}.py: edit that and run uv run tg draw {self.id}. -->\n<defs>{defs}</defs>\n'
                f'<g data-object="" filter="url(#ink)"><g transform="matrix({num(k)} 0 0 {num(-k)} {num(ox)} {num(oy)})">{"".join(map(str, self.draw.out))}</g></g>\n'
                f'<g>{texts}{rings}</g>\n<g>{self._dims(px, within)}</g>\n<g>{self._labels(px, within)}</g>\n<g>{self._notes()}{self._furniture(k)}</g>\n</svg>\n')

    def _dims(self, px, within):
        out = []
        mx, my = px(((self.box[0] + self.box[2]) / 2, (self.box[1] + self.box[3]) / 2)) if self.box else (self.W / 2, self.H / 2)
        for a, b, text, offset, conds in self.dims:
            (x1, y1), (x2, y2) = px(a), px(b)
            L = math.hypot(x2 - x1, y2 - y1) or 1
            nx, ny = -(y2 - y1) / L, (x2 - x1) / L
            if nx * ((x1 + x2) / 2 - mx) + ny * ((y1 + y2) / 2 - my) < 0:  # away from the middle of the object
                nx, ny = -nx, -ny
            ox, oy = nx * offset, ny * offset
            angle = math.degrees(math.atan2(y2 - y1, x2 - x1))
            angle += 180 if angle > 90 or angle <= -90 else 0
            tx, ty = (x1 + x2) / 2 + nx * (offset + 9), (y1 + y2) / 2 + ny * (offset + 9)
            out.append(within(
                f'<g stroke="{FADED}" stroke-width="0.8" fill="none"><line x1="{num(x1 + nx * 4)}" y1="{num(y1 + ny * 4)}" x2="{num(x1 + ox * 1.2)}" y2="{num(y1 + oy * 1.2)}"/>'
                f'<line x1="{num(x2 + nx * 4)}" y1="{num(y2 + ny * 4)}" x2="{num(x2 + ox * 1.2)}" y2="{num(y2 + oy * 1.2)}"/>'
                f'<line x1="{num(x1 + ox)}" y1="{num(y1 + oy)}" x2="{num(x2 + ox)}" y2="{num(y2 + oy)}" marker-start="url(#arrow)" marker-end="url(#arrow)"/></g>'
                f'<text x="{num(tx)}" y="{num(ty)}" dy="4" font-size="12" font-style="italic" text-anchor="middle" fill="{FADED}" transform="rotate({num(angle)} {num(tx)} {num(ty)})">{esc(text)}</text>', conds))
        return "".join(out)

    def _labels(self, px, within):
        """Labels go in columns either side of the object, level with what they point at, nudged apart."""
        if not self.labels:
            return ""
        (x0, y0), (x1, y1) = px((self.box[0], self.box[3])), px((self.box[2], self.box[1]))
        mid, sides, out = (x0 + x1) / 2, {"left": [], "right": []}, []
        for text, at, colour, side, width, conds in self.labels:
            X, Y = px(at)
            sides[side or ("left" if X < mid else "right")].append((text, X, Y, colour, width, conds))
        for side, labs in sides.items():
            col = max(16, x0 - 28) if side == "left" else min(self.W - 16, x1 + 28)
            placed = []
            for text, X, Y, colour, width, conds in sorted(labs, key=lambda l: l[2]):
                lines = wrap(text, width)
                h = 15 * len(lines)
                y = max(Y + 4 - 7.5 * (len(lines) - 1), placed[-1][1] + placed[-1][2] + 7 if placed else 34)
                placed.append([lines, y, h, X, Y, colour, conds])
            over = placed[-1][1] + placed[-1][2] - (self.H - 100) if placed else 0
            for p in placed if over > 0 else []:  # off the bottom: slide the column up
                p[1] -= over
            anchor, toward = ("end", 1) if side == "left" else ("start", -1)
            for lines, y, h, X, Y, colour, conds in placed:
                body = "".join(f'<tspan x="{num(col)}" dy="{0 if i == 0 else 15}">{esc(s)}</tspan>' for i, s in enumerate(lines))
                ly = y - 4 + 7.5 * (len(lines) - 1)
                out.append(within(
                    f'<text x="{num(col)}" y="{num(y)}" font-size="13" font-style="italic" text-anchor="{anchor}" fill="{colour}">{body}</text>'
                    f'<polyline points="{num(col + 6 * toward)},{num(ly)} {num(col + 18 * toward)},{num(ly)} {num(X)},{num(Y)}" fill="none" stroke="{colour}" stroke-width="0.7" opacity="0.85"/>'
                    f'<circle cx="{num(X)}" cy="{num(Y)}" r="1.8" fill="{colour}"/>', conds))
        return "".join(out)

    def _notes(self):
        out, y = [], self.H - 110
        for title, text in reversed(self.notes):
            lines = wrap(text, 60)
            y -= 16 * len(lines) + 36
            body = "".join(f'<tspan x="60" dy="{0 if i == 0 else 16}">{esc(s)}</tspan>' for i, s in enumerate(lines))
            out.append(f'<text x="60" y="{y}" font-size="16" font-variant="small-caps" fill="{FADED}">{esc(title)}</text>'
                       f'<text x="60" y="{y + 20}" font-size="13" font-style="italic" fill="{INK}">{body}</text>')
        return "".join(out)

    def _furniture(self, k):
        """The cartouche and a scale bar of round lengths."""
        W, H = self.W, self.H
        length = next((L for L in (10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000, 100000) if L * k >= 110), 100000)
        unit, show = ("m", length / 1000) if length >= 1000 else ("cm", length / 10)
        x0, y0, w = 60, H - 52, length * k
        bar = "".join(f'<rect x="{num(x0 + w * i / 4)}" y="{y0}" width="{num(w / 4)}" height="6" fill="{INK if i % 2 == 0 else PAPER}" stroke="{INK}" stroke-width="0.8"/>' for i in range(4))
        ticks = "".join(f'<text x="{num(x0 + w * i / 2)}" y="{y0 + 22}" font-size="12" text-anchor="middle" fill="{FADED}">{num(show * i / 2)}{" " + unit if i == 2 else ""}</text>' for i in range(3))
        return (bar + ticks + f'<text x="{W - 50}" y="{H - 64}" font-size="22" font-variant="small-caps" text-anchor="end" fill="{INK}">{esc(self.title)}</text>'
                f'<text x="{W - 50}" y="{H - 42}" font-size="13" font-style="italic" text-anchor="end" fill="{FADED}">{esc(self.subtitle)}</text>')

    def save(self, folder="visuals"):
        path = Path(folder) / f"{self.id}.svg"
        path.write_text(self.svg())
        print(path)
        return path
