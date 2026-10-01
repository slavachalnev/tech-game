"""Stock parts for the drawing kit: true-size period pieces for drawings, in millimetres with y up.

Each is a function of a Pen, like the game's own parts in drawings/parts.py, so it's placed the same way:
s.place(barrel, at=(2400, 0), height=900) or, inside a part, p.part(cock, at=(0, 120), open=True). Each docstring
says where its origin is. The catalogue, dm/stock.png, shows them all (made by dm/stock_catalogue.py).
"""
import math

from .draw import FADED, INK, PAPER, num

# ---------- people and animals

HATS = {
    "tricorn": [(-120, 0), (120, 0), (80, 55), (0, 70), (-80, 55)],
    "cap": [(-95, 0), (95, 0), (85, 60), (0, 85), (-85, 60)],
}


def person(p, height=1700, pose="stand", hat="tricorn", facing="right"):
    """A working figure in coat, breeches and stockings, seen side on. Origin: between the feet, on the ground.
    pose: stand, work (arms reaching forward), carry (a load at the chest) or sit (on something 450 mm high)."""
    s, f = height / 1700, 1 if facing == "right" else -1
    x = lambda v: v * s * f  # noqa: E731
    y = lambda v: v * s  # noqa: E731
    seat = pose == "sit"
    hip = 450 if seat else 900
    # legs, stockings and shoes
    if seat:
        p.poly([(x(-60), y(450)), (x(260), y(450)), (x(260), y(70)), (x(170), y(70)), (x(170), y(380)), (x(-60), y(380))], "earth", line="detail")
        p.poly([(x(170), 0), (x(300), 0), (x(300), y(40)), (x(170), y(70))], "iron", line="detail")
    else:
        for dx in (-45, 45):
            p.poly([(x(dx - 55), y(hip)), (x(dx + 55), y(hip)), (x(dx + 45), y(420)), (x(dx + 35), y(70)), (x(dx - 35), y(70)), (x(dx - 45), y(420))], "earth" if dx < 0 else "timber", line="detail")
            p.poly([(x(dx - 40), 0), (x(dx + 95), 0), (x(dx + 95), y(35)), (x(dx - 40), y(70))], "iron", line="detail")
    # coat, skirts to the knee
    p.poly([(x(-150), y(hip - 330 if not seat else 420)), (x(150), y(hip - 330 if not seat else 420)), (x(120), y(1380)), (x(-110), y(1380))], "earth")
    p.line(x(0), y(1360), x(0), y(hip - 200 if not seat else 430), "faint")
    # arms
    shoulder = (x(20), y(1340))
    hand = {"stand": (x(40), y(860)), "work": (x(430), y(1080)), "carry": (x(250), y(1050)), "sit": (x(300), y(800))}[pose]
    p.poly([shoulder, ((shoulder[0] + hand[0]) / 2 + x(30), (shoulder[1] + hand[1]) / 2), hand], closed=False, line="outline")
    p.circle(hand[0], hand[1], 40 * s, "leather", line="detail")
    p.anchor("hand", *hand)
    if pose == "carry":
        p.rect(hand[0] - x(160), hand[1] - y(60), x(300), y(260), "timber", line="detail")
    # neck, head and hat
    p.rect(x(-35), y(1380), x(70), y(70), "leather", line="detail")
    p.circle(x(10), y(1550), 115 * s, "paper")
    p.poly([(x(115), y(1560)), (x(150), y(1530)), (x(112), y(1515))], closed=False, line="detail")  # the nose
    if hat in HATS:
        p.poly([(x(10) + x(hx), y(1640) + y(hy)) for hx, hy in HATS[hat]], "iron")
    p.anchor("head", x(10), y(1550))


def horse(p, facing="right"):
    """A working horse in its collar, about 1.5 m at the withers and 2.4 m nose to tail. Origin: on the ground under
    its middle. Anchors: back (the top of its back), collar (where traces or a sweep are hitched), head."""
    f = 1 if facing == "right" else -1
    P = lambda pts: [(x * f, y) for x, y in pts]  # noqa: E731

    def leg(x, hind, material, line):
        if hind:  # thigh, hock and cannon, the hoof at x
            pts = [(-100, 980), (95, 930), (60, 560), (25, 140), (45, 60), (70, 0), (-60, 0), (-45, 90), (-50, 470), (-110, 560), (-150, 820)]
        else:  # forearm, knee and cannon
            pts = [(-60, 960), (80, 930), (70, 540), (55, 140), (75, 60), (100, 0), (-30, 0), (-15, 80), (-20, 500), (-45, 560), (-70, 800)]
        p.poly(P([(x + a, b) for a, b in pts]), material, line=line)

    for x, hind in ((-520, True), (330, False)):  # the far legs, a stride apart from the near ones
        leg(x, hind, "leather", "detail")
    p.poly(P([(-850, 1400), (-990, 1150), (-940, 760), (-880, 800), (-860, 1150), (-780, 1430)]), "leather", line="detail")  # tail
    body = [(600, 1050), (700, 1330), (850, 1610), (990, 1530), (1230, 1250), (1290, 1240), (1310, 1320), (1250, 1460),
            (1130, 1690), (1020, 1820), (1005, 1940), (955, 1840), (820, 1790), (560, 1650), (330, 1550), (100, 1470),
            (-200, 1460), (-560, 1530), (-780, 1470), (-840, 1250), (-790, 1000), (-640, 850), (-450, 820), (-50, 770),
            (380, 830), (520, 900)]
    p.poly(P(body), "timber")
    p.poly(P([(955, 1840), (820, 1790), (560, 1650), (330, 1550), (400, 1620), (600, 1730), (880, 1860)]), "leather", line="detail")  # mane
    for x, hind in ((-660, True), (450, False)):  # the near legs
        leg(x, hind, "timber", "outline")
    p.poly(P([(610, 1010), (720, 1060), (480, 1660), (380, 1610)]), "leather", line="detail")  # collar
    p.circle(1090 * f, 1660, 18, "iron", line="detail")  # eye
    p.anchor("back", -100 * f, 1455)
    p.anchor("collar", 560 * f, 1330)
    p.anchor("head", 1120 * f, 1550)


def whim(p, radius=3000, drum=1100, walking=True, seconds=24):
    """A horse whim (a horse gin), seen side on: a horse walking round a tall timber spindle under a big drum, which
    winds a rope or drives an endless one. Origin: the foot of the spindle. radius: the horse's circle. walking: the
    horse goes round once every `seconds` (seen side on, it walks to and fro), else it stands on the near side.
    Anchors: left and right, the drum's edges at its middle height; top and bottom, the middle of its top and foot."""
    top = 4700
    for sx in (-1, 1):  # the frame's two legs, splayed fore and aft of the spindle
        p.poly([(sx * 650, 0), (sx * 800, 0), (sx * 230, top - 170), (sx * 110, top - 170)], "timber", line="detail")
    p.rect(-130, 0, 260, top, "timber")  # the spindle
    p.rect(-520, top - 190, 1040, 210, "timber")  # the cap beam, with the top bearing
    p.rect(-drum, 2560, 2 * drum, 880, "timber")  # the drum, with its flanges
    for fy in (2480, 3440):
        p.rect(-drum - 70, fy, 2 * drum + 140, 80, "timber", line="detail")
    with p.fine(drum / 6):
        for i in range(1, 8):
            p.line(-drum + 2 * drum * i / 8, 2560, -drum + 2 * drum * i / 8, 3440, "faint")

    def sweep(q):  # the sweep arm, hitched to the horse's collar, with its brace
        q.poly([(0, 2380), (radius, 1300)], closed=False, line="outline")
        q.poly([(0, 1500), (radius * 0.55, 1300 + 1080 * 0.45)], closed=False, line="detail")

    ease = 'keyTimes="0;0.5;1" calcMode="spline" keySplines="0.45 0 0.55 1;0.45 0 0.55 1"'
    times = f'dur="{seconds}s" repeatCount="indefinite"'
    if walking:  # seen side on, going round is going to and fro, facing the way it walks
        p._reach((-radius - 1300, 0), (radius + 1300, 1900))
        with p._group("", f'<animateTransform attributeName="transform" type="scale" values="1 1;-1 1;1 1" {ease} {times}/>'):
            sweep(p)
        with p.slide(-2 * radius, 0, seconds):
            with p._group("", f'<animate attributeName="opacity" values="1;0;1" keyTimes="0;0.5;1" calcMode="discrete" {times}/>'):
                p.part(horse, at=(radius, 0), facing="left")
            with p._group("", f'<animate attributeName="opacity" values="0;1;0" keyTimes="0;0.5;1" calcMode="discrete" {times}/>'):
                p.part(horse, at=(radius, 0))
    else:
        sweep(p)
        p.part(horse, at=(radius, 0))
    p.anchor("left", -drum, 3000)
    p.anchor("right", drum, 3000)
    p.anchor("top", 0, top)
    p.anchor("bottom", 0, 0)


# ---------- the workshop

def barrel(p, height=700, diameter=500, hoops=4, water=None):
    """A coopered barrel, seen side on. Origin: the middle of its base. water=0.6: full to 60 %, cut open."""
    r, bulge = diameter / 2, diameter * 0.08
    p.path(f"M{num(-r)},0 Q{num(-r - bulge * 2)},{num(height / 2)} {num(-r)},{num(height)} L{num(r)},{num(height)} Q{num(r + bulge * 2)},{num(height / 2)} {num(r)},0 Z",
           "timber", reach=[(-r - bulge, 0), (r + bulge, height)])
    if water:
        p.rect(-r * 0.85, height * 0.06, r * 1.7, height * water * 0.9, "water", line="faint")
    with p.fine(diameter / 6):
        for sx in (-0.5, 0, 0.5):
            p.line(r * sx, 0, r * sx * 1.08, height, "faint")
    for i in range(hoops):
        hy = height * (0.1 + 0.8 * i / max(1, hoops - 1))
        p.line(-r - bulge * (1 - abs(1 - 2 * hy / height)), hy, r + bulge * (1 - abs(1 - 2 * hy / height)), hy, "detail")
    p.anchor("top", 0, height)


def bucket(p, height=280):
    """A wooden bucket with a rope handle. Origin: the middle of its base."""
    w = height * 0.95
    p.poly([(-w * 0.4, 0), (w * 0.4, 0), (w / 2, height), (-w / 2, height)], "timber")
    p.line(-w * 0.45, height * 0.25, w * 0.45, height * 0.25, "detail")
    p.line(-w * 0.48, height * 0.8, w * 0.48, height * 0.8, "detail")
    p.path(f"M{num(-w / 2)},{num(height)} Q0,{num(height * 1.6)} {num(w / 2)},{num(height)}", line="detail", reach=[(0, height * 1.3)])
    p.anchor("top", 0, height)


def bench(p, length=1800, height=850):
    """A joiner's bench: a thick top on four legs, with a shelf below. Origin: the floor under its middle."""
    p.rect(-length / 2, height - 90, length, 90, "timber")
    for lx in (-length / 2 + 60, length / 2 - 140):
        p.rect(lx, 0, 80, height - 90, "timber", line="detail")
    p.rect(-length / 2 + 60, 180, length - 120, 40, "timber", line="detail")
    p.anchor("top", 0, height)


def shelf(p, length=1200):
    """A plank shelf on two iron brackets, against a wall, seen from the front. Origin: the middle of its top surface."""
    for bx in (-length / 2 + min(120, length / 5), length / 2 - min(120, length / 5) - 20):
        p.rect(bx, -230, 20, 195, "iron", line="detail")
        p.circle(bx + 10, -200, 4, "iron", line="detail")  # its screw
    p.rect(-length / 2, -35, length, 35, "timber")
    p.anchor("top", 0, 0)


def ladder(p, height=3000, width=450):
    """A wooden ladder, standing upright. Origin: the middle of its foot."""
    for sx in (-1, 1):
        p.rect(sx * width / 2 - 30, 0, 60, height, "timber", line="detail")
    for i in range(1, int(height / 300)):
        p.line(-width / 2, i * 300, width / 2, i * 300, "detail")
    p.anchor("top", 0, height)


def door(p, width=1100, height=2000, open=False):
    """A plank door in its frame. Origin: the floor under the middle of the doorway."""
    p.rect(-width / 2 - 60, 0, width + 120, height + 60, "timber", line="detail")
    p.rect(-width / 2, 0, width, height, "paper", line="detail")
    if open:
        p.poly([(width / 2, 0), (width / 2 + width * 0.35, -120), (width / 2 + width * 0.35, height - 120), (width / 2, height)], "timber")
    else:
        p.rect(-width / 2, 0, width, height, "timber", line="detail")
        with p.fine(150):
            for i in range(1, 5):
                p.line(-width / 2 + width * i / 5, 0, -width / 2 + width * i / 5, height, "faint")
    p.anchor("handle", width / 2 - 120, height * 0.48)


def window(p, width=800, height=700):
    """A small leaded window in a deep wall. Origin: the middle of its sill."""
    p.rect(-width / 2 - 60, -60, width + 120, height + 120, "timber", line="detail")
    p.rect(-width / 2, 0, width, height, (("#dfe6e3", 0.6)), line="detail")
    with p.fine(60):
        for i in range(1, 4):
            p.line(-width / 2, height * i / 4, width / 2, height * i / 4, "faint")
            p.line(-width / 2 + width * i / 4, 0, -width / 2 + width * i / 4, height, "faint")
    p.anchor("middle", 0, height / 2)


def masonry(p, x, y, w, h, kind="granite"):
    """A wall or block of granite or brick in elevation, with its courses. Its lower-left corner at (x, y)."""
    p.rect(x, y, w, h, "masonry")
    course = 300 if kind == "granite" else 75
    with p.fine(course / 3):
        for i, cy in enumerate(range(int(y + course), int(y + h), course)):
            p.line(x, cy, x + w, cy, "faint")
            step = course * (1.6 if kind == "granite" else 3)
            for cx in range(int(x + (step / 2 if i % 2 else step)), int(x + w), int(step)):
                p.line(cx, cy - course, cx, cy, "faint")


def ground(p, x0, x1, kind="earth"):
    """The ground line from x0 to x1 at y = 0, with earth (or a floor, or grass) below it."""
    depth = 250
    if kind == "floor":
        p.rect(x0, -depth, x1 - x0, depth, "earth", cut=True, line="none")
    else:
        p.rect(x0, -depth, x1 - x0, depth, "earth", cut=True, line="none")
        if kind == "grass":
            with p.fine(60):
                for gx in range(int(x0) + 40, int(x1), 180):
                    p.poly([(gx, 0), (gx + 25, 70), (gx + 40, 0), (gx + 70, 55), (gx + 85, 0)], closed=False, line="faint")
    p.line(x0, 0, x1, 0, "outline")


def water(p, x0, x1, level, depth):
    """A body of water from x0 to x1, its surface at `level`, `depth` deep, with a wavy surface."""
    p.rect(x0, level - depth, x1 - x0, depth, "water", line="none")
    n = max(2, int((x1 - x0) / 120))
    d = f"M{num(x0)},{num(level)}" + "".join(f" q{num((x1 - x0) / n / 2)},{num(12 * (1 if i % 2 else -1))} {num((x1 - x0) / n)},0" for i in range(n))
    p.path(d, line="detail", reach=[(x0, level), (x1, level)])


# ---------- pipework and machinery

def pipe(p, points, diameter=25, material="copper"):
    """A pipe of outside `diameter` along a polyline of points, with rounded bends."""
    d = "M" + " L".join(f"{num(x)},{num(y)}" for x, y in points)
    p._reach(*points)
    p.out.append(f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="{num(diameter + 0.0)}" stroke-linejoin="round" stroke-linecap="butt"/>')
    p.out.append(f'<path d="{d}" fill="none" stroke="{PAPER}" stroke-width="{num(diameter * 0.82)}" stroke-linejoin="round" stroke-linecap="butt"/>')
    colour = {"copper": "#b07a3c", "lead": "#7d8288", "iron": "#56514b", "brass": "#b08d3c"}[material]
    p.out.append(f'<path d="{d}" fill="none" stroke="{colour}" stroke-opacity="0.45" stroke-width="{num(diameter * 0.82)}" stroke-linejoin="round" stroke-linecap="butt"/>')


def flange(p, diameter=120, thickness=20):
    """A pipe flange, seen edge on, with its bolts. Origin: the middle of the joint."""
    p.rect(-thickness, -diameter / 2, thickness * 2, diameter, "iron", line="detail")
    for by in (-diameter * 0.35, diameter * 0.35):
        p.rect(-thickness * 1.6, by - diameter * 0.05, thickness * 3.2, diameter * 0.1, "iron", line="detail")


def cock(p, bore=20, open=False):
    """A brass plug tap on a horizontal pipe, its handle along the flow when open and across it when shut.
    Origin: the middle of its body."""
    b = bore
    p.poly([(-b * 1.6, -b * 0.7), (b * 1.6, -b * 0.7), (b * 1.1, b * 0.9), (-b * 1.1, b * 0.9)], "brass")
    p.rect(-b * 0.35, b * 0.9, b * 0.7, b * 0.6, "brass", line="detail")
    if open:
        p.rect(-b * 1.5, b * 1.5, b * 3, b * 0.35, "brass", line="detail")
    else:
        p.rect(-b * 0.2, b * 1.5, b * 0.4, b * 2.2, "brass", line="detail")
    p.anchor("handle", 0, b * 1.8)


def wheel(p, radius, spokes=6, rim=None, material="timber"):
    """A spoked wheel, face on. Origin: its axle."""
    rim = rim or radius * 0.12
    p.circle(0, 0, radius, material)
    p.circle(0, 0, radius - rim, "paper", line="detail")
    for i in range(spokes):
        a = 2 * math.pi * i / spokes
        p.poly([(math.cos(a) * radius * 0.12, math.sin(a) * radius * 0.12), (math.cos(a) * (radius - rim), math.sin(a) * (radius - rim))], closed=False, line="outline")
    p.circle(0, 0, radius * 0.14, material, line="detail")
    p.circle(0, 0, radius * 0.05, "iron", line="detail")
    p.anchor("axle", 0, 0)


def gear(p, radius, teeth=24, material="iron"):
    """A spur gear, face on, its teeth on the pitch circle `radius`. Origin: its axle."""
    pts, depth = [], radius * 0.08
    for i in range(teeth * 4):
        a = 2 * math.pi * i / (teeth * 4)
        r = radius + (depth if i % 4 in (1, 2) else -depth)
        pts.append((math.cos(a) * r, math.sin(a) * r))
    with p.fine(2 * math.pi * radius / teeth / 3):
        p.poly(pts, material)
    with p.coarse(2 * math.pi * radius / teeth / 3):
        p.circle(0, 0, radius, material)
    p.circle(0, 0, radius * 0.6, "paper", line="detail")
    p.circle(0, 0, radius * 0.15, material, line="detail")
    p.anchor("axle", 0, 0)


def beam(p, length, depth, material="timber", pivot=None):
    """A beam lying level, its middle at the origin; `pivot` (mm from the middle) draws a gudgeon there."""
    p.rect(-length / 2, -depth / 2, length, depth, material)
    with p.fine(depth / 3):
        p.line(-length / 2, depth * 0.15, length / 2, depth * 0.1, "faint")
    if pivot is not None:
        p.circle(pivot, 0, depth * 0.18, "iron", line="detail")
        p.anchor("pivot", pivot, 0)
    p.anchor("left", -length / 2, 0)
    p.anchor("right", length / 2, 0)


def chain(p, points, link=40):
    """A chain along a polyline of points."""
    p._reach(*points)
    d = "M" + " L".join(f"{num(x)},{num(y)}" for x, y in points)
    p.out.append(f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="2.2" vector-effect="non-scaling-stroke" stroke-dasharray="7 3"/>')


def rope(p, points):
    """A rope along a polyline of points."""
    p.poly(points, closed=False, line="detail")
    with p.fine(30):
        p.out.append(f'<polyline points="{" ".join(f"{num(x)},{num(y)}" for x, y in points)}" fill="none" stroke="{FADED}" stroke-width="1" vector-effect="non-scaling-stroke" stroke-dasharray="2 3"/>')


def cylinder(p, bore, length, wall, cut=False, material="brass"):
    """A plain cylinder standing upright, open at the top. Origin: the middle of its base. cut: half section."""
    r = bore / 2 + wall
    p.rect(-r, 0, 2 * r, length, material, cut=cut)
    p.rect(-bore / 2, wall if cut else 0, bore, length - (wall if cut else 0), "paper" if cut else None, line="detail" if cut else "hidden")
    p.anchor("top", 0, length)
    p.anchor("wall", -r, length / 2)


def piston(p, diameter, thickness, rod=0, material="brass"):
    """A piston with its rod going up. Origin: the middle of its underside."""
    p.rect(-diameter / 2, 0, diameter, thickness, material)
    if rod:
        p.rect(-diameter * 0.07, thickness, diameter * 0.14, rod, "iron", line="detail")
        p.anchor("rod", 0, thickness + rod)


def break_line(p, x0, x1, y, size=None):
    """The standard break symbol across from x0 to x1 at height y: something drawn shortened. `size` is the
    zigzag's height (by default a twentieth of the width, at most 150 mm)."""
    w, z = x1 - x0, size or min((x1 - x0) * 0.05, 150)
    m = (x0 + x1) / 2
    p.poly([(x0, y), (m - z, y), (m - z / 2, y + z), (m + z / 2, y - z), (m + z, y), (x1, y)], closed=False, line="detail")


# ---------- fire, steam, weather and light

def fire(p, width=400, height=300):
    """Flames that flicker. Origin: the middle of their base."""
    with p.flicker():
        pts = [(-width / 2, 0)]
        for i in range(7):
            pts += [(-width / 2 + width * (i + 0.5) / 7, height * (0.6 + 0.4 * ((i * 37) % 5) / 4)), (-width / 2 + width * (i + 1) / 7, height * 0.15)]
        pts[-1] = (width / 2, 0)
        p.poly(pts, "fire", line="red")
    p.anchor("top", 0, height)


def steam(p, width=200, height=300):
    """Puffs of steam that rise and fade. Origin: where they come from."""
    p._reach((-width, 0), (width, height + width))  # as far as they drift
    for i, (dx, delay) in enumerate(((0, 0), (width * 0.3, 1.1), (-width * 0.25, 2.2))):
        with p.drift(dx * 0.5, height, 3.3, delay=delay, grow=1.8):
            p.ellipse(dx * 0.3, width * 0.2, width * 0.35, width * 0.25, "steam", line="faint")


def sky(p, x0, x1, horizon, top):
    """A sky from x0 to x1 between the horizon and `top`: grey by day, a warm band at dawn and dusk, dark with a few
    stars at night."""
    h = top - horizon
    with p.sky("day"):
        p.rect(x0, horizon, x1 - x0, h, ("#dde3e2", 0.22), line="none")
        p.rect(x0, horizon, x1 - x0, h * 0.3, ("#f3ead2", 0.35), line="none")  # lighter toward the horizon
    with p.sky("dawn", "dusk"):
        p.rect(x0, horizon, x1 - x0, h, ("#a9a4a8", 0.35), line="none")
        p.rect(x0, horizon, x1 - x0, h * 0.25, ("#c0662b", 0.25), line="none")
    with p.sky("night"):
        p.rect(x0, horizon, x1 - x0, h, ("#1f2433", 0.75), line="none")
        for i in range(12):
            sx, sy = x0 + (x1 - x0) * ((i * 0.618) % 1), horizon + h * (0.35 + 0.6 * ((i * 0.377) % 1))
            p.circle(sx, sy, h * 0.004, ("#f3ead2", 0.9), line="none")


def night(p, x0, y0, x1, y1, lights=()):
    """At night only: a dark wash over the area from (x0, y0) to (x1, y1), leaving warm pools of light around each
    (x, y, radius) in `lights` (a lantern, a fire)."""
    mid = p.uid("night")
    holes = "".join(f'<circle cx="{num(x)}" cy="{num(y)}" r="{num(r)}" fill="url(#{mid}-fade)"/>' for x, y, r in lights)
    glows = "".join(f'<circle cx="{num(x)}" cy="{num(y)}" r="{num(r)}" fill="url(#{mid}-warm)"/>' for x, y, r in lights)
    with p.sky("night"):
        p.raw(f'<defs><radialGradient id="{mid}-fade"><stop offset="0" stop-color="#000"/><stop offset="1" stop-color="#000" stop-opacity="0"/></radialGradient>'
              f'<radialGradient id="{mid}-warm"><stop offset="0" stop-color="#e8a24a" stop-opacity="0.45"/><stop offset="1" stop-color="#e8a24a" stop-opacity="0"/></radialGradient>'
              f'<mask id="{mid}" maskUnits="userSpaceOnUse" x="{num(x0)}" y="{num(y0)}" width="{num(x1 - x0)}" height="{num(y1 - y0)}">'
              f'<rect x="{num(x0)}" y="{num(y0)}" width="{num(x1 - x0)}" height="{num(y1 - y0)}" fill="#fff"/>{holes}</mask>'
              f'<clipPath id="{mid}-area"><rect x="{num(x0)}" y="{num(y0)}" width="{num(x1 - x0)}" height="{num(y1 - y0)}"/></clipPath></defs>'
              f'<rect x="{num(x0)}" y="{num(y0)}" width="{num(x1 - x0)}" height="{num(y1 - y0)}" fill="#1c1610" fill-opacity="0.55" mask="url(#{mid})"/>'
              f'<g clip-path="url(#{mid}-area)">{glows}</g>')


def rain(p, x0, x1, y0, y1):
    """Light slanted rain over the area, by day."""
    with p.sky("day"), p.fine(80):
        for i in range(int((x1 - x0) / 140)):
            x, y = x0 + (i * 140 + (i * 53) % 90), y0 + (y1 - y0) * ((i * 0.618) % 1)
            p.line(x, y, x - 40, y - 160, "faint")


def lantern(p, lit=True):
    """A hanging horn lantern on a short chain, its flame lit at night. Origin: where it hangs from."""
    p.line(0, 0, 0, -120, "detail")
    p.poly([(-70, -120), (70, -120), (90, -170), (-90, -170)], "iron", line="detail")
    p.rect(-75, -400, 150, 230, ("#e8d9a8", 0.5), line="detail")
    p.rect(-85, -430, 170, 30, "iron", line="detail")
    if lit:
        with p.sky("night", "dusk"), p.flicker(0.9):
            p.ellipse(0, -300, 22, 45, "fire", line="none")
    p.anchor("flame", 0, -300)
