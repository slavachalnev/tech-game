# Wheal Fortune: the engine shaft in section, with the headframe and the two horse whims above it. Millimetres, x
# east from the middle of the shaft, y up from the surface. The depth is broken: only the stretches in SEGMENTS are
# drawn, one under the other with a gap between, so depth(m) turns a true depth into a height on the drawing.
from engine.draw import Sheet
from engine.stock import break_line, chain, ground, lantern, night, rope, sky, water, wheel, whim

SEGMENTS = [(0, 1.6), (19.8, 23), (42, 48.5), (64, 67)]  # true depths drawn, in m
GAP = 600
SHAFT = 900  # half its width: 1.8 m across
X0, X1 = -4500, 10000  # the underground strips' extent
WHIMS = 6000  # each whim's distance from the shaft
LODE = lambda m: 1500 + 90 * m  # noqa: E731  (the middle of the lode at a depth, dipping east)


def depth(m):
    top = 0
    for a, b in SEGMENTS:
        if m <= b:
            return top - (m - a) * 1000
        top -= (b - a) * 1000 + GAP
    raise ValueError(m)


s = Sheet("wheal-fortune", "Wheal Fortune", "Section through the engine shaft, its depth broken · to scale")
p = s.draw

# ---- above ground
sky(p, -10000, 10000, 0, 5200)
ground(p, -10000, 10000, "grass")
# the headframe over the shaft, carrying the two pumps' wheels
for sx in (-1, 1):
    p.rect(sx * 1300 - 90, 0, 180, 4100, "timber")
    p.poly([(sx * 2700, 0), (sx * 2550, 0), (sx * 1300, 2900), (sx * 1350, 3100)], "timber", line="detail")
p.rect(-1600, 4100, 3200, 220, "timber")
p.rect(-1390, 2600, 2780, 160, "timber", line="detail")  # the beam the wheels' bearings sit on, behind them
p.rect(-1100, -300, 200, 420, "timber", line="detail")  # the shaft's collar
p.rect(900, -300, 200, 420, "timber", line="detail")
p.part(lantern, at=(1450, 4100))


def wheels(q):
    """A pump's wheels, turning: the rope wheel the whim drives, and the rag wheel that draws up the chain."""
    q.part(wheel, radius=400, spokes=4)
    q.part(wheel, radius=320, spokes=6, material="iron")


def wheels_turning(q):
    with q.spin(0, 0, 9):
        wheels(q)


for sx in (-1, 1):
    with s.state("flooded"):
        p.part(wheels_turning, at=(sx * 450, 3000), flip=sx > 0)
        p.part(whim, at=(sx * WHIMS, 0), flip=sx < 0, radius=2700, seconds=26 if sx < 0 else 23)
    with s.state("drained"):
        p.part(wheels, at=(sx * 450, 3000))
        p.part(whim, at=(sx * WHIMS, 0), flip=sx < 0, radius=2700, walking=False)
    for y in (3400, 2600):  # the endless rope from the whim's drum round the rope wheel
        rope(p, [(sx * (WHIMS - 1100), y), (sx * 450, y)])

# ---- underground: a strip for each stretch of depth, broken between them
for i, (a, b) in enumerate(SEGMENTS):
    top, bottom = depth(a), depth(b)
    x0, x1 = (-10000, 10000) if i == 0 else (X0, X1)
    p.rect(x0, bottom, x1 - x0, (top if i else -250) - bottom, "earth", cut=True, line="none")
    for y in (top, bottom)[0 if i else 1:]:  # broken off: the strip's edge, with the break mark across the shaft
        p.line(x0, y, x1, y, "faint")
    if i:
        p.text(f"{a:g} m", X0 - 150, top - 120, size=12, anchor="end", colour="#7a6a55")
    p.text(f"{b:g} m", X0 - 150, bottom + 40, size=12, anchor="end", colour="#7a6a55")
    # the lode, richer below about 48 m
    for m0, m1, rich in ((a, min(b, 48), False), (max(a, 48), b, True)):
        if m0 < m1:
            p.poly([(LODE(m0) - 350, depth(m0)), (LODE(m0) + 350, depth(m0)), (LODE(m1) + 350, depth(m1)), (LODE(m1) - 350, depth(m1))],
                   ("#b08d3c", 0.5 if rich else 0.22), line="faint")
    p.rect(-SHAFT, bottom, 2 * SHAFT, (0 if i == 0 else top) - bottom, "paper", line="none")  # the shaft
    for sx in (-1, 1):
        p.line(sx * SHAFT, bottom, sx * SHAFT, 0 if i == 0 else top, "outline")

for i, (a, b) in enumerate(SEGMENTS):
    for m in ((a, b) if i else (b,)):
        break_line(p, -SHAFT - 500, SHAFT + 500, depth(m))

# the adit at 22 m, out to the valley, with the water the pumps lift running out along it
p.rect(SHAFT, depth(22), X1 - SHAFT, 1800, "paper", line="none")
p.line(SHAFT, depth(22) + 1800, X1, depth(22) + 1800, "outline")
p.line(SHAFT, depth(22), X1, depth(22), "outline")
p.rect(SHAFT, depth(22), X1 - SHAFT, 140, "water", line="none")
for x in range(2500, X1, 2200):
    p.poly([(x, depth(22) + 70), (x + 500, depth(22) + 70)], closed=False, line="faint")
    p.poly([(x + 400, depth(22) + 110), (x + 500, depth(22) + 70), (x + 400, depth(22) + 30)], closed=False, line="faint")
# the levels: crosscuts out to the lode at 44 m and at the bottom, 66 m
for m in (44, 66):
    p.rect(X0, depth(m), -SHAFT - X0, 1800, "paper", line="none")
    p.rect(SHAFT, depth(m), LODE(m) + 350 - SHAFT, 1800, "paper", line="none")
    for x0, x1 in ((X0, -SHAFT), (SHAFT, LODE(m) + 350)):
        p.line(x0, depth(m), x1, depth(m), "outline")
        p.line(x0, depth(m) + 1800, x1, depth(m) + 1800, "outline")
    p.line(LODE(m) + 350, depth(m), LODE(m) + 350, depth(m) + 1800, "outline")
# the sump below the bottom level
p.line(-SHAFT, depth(67), SHAFT, depth(67), "outline")

# the water: up to 44 m when flooded; when drained, only a puddle in the sump
with s.state("flooded"):
    water(p, -SHAFT, SHAFT, depth(44), depth(44) - depth(48.5))
    p.rect(-SHAFT, depth(67), 2 * SHAFT, depth(64) - depth(67), "water", line="none")
    for m in (66,):
        p.rect(X0, depth(m), -SHAFT - X0, 1800, "water", line="none")
        p.rect(SHAFT, depth(m), LODE(m) + 350 - SHAFT, 1800, "water", line="none")
with s.state("drained"):
    water(p, -SHAFT, SHAFT, depth(66.7), 300)

# the two rag-and-chain pumps: a wooden pipe each from the sump up to the adit, the chain up through it and down
# beside it, with its leather rag-balls
for sx in (-1, 1):
    for i, (a, b) in enumerate(SEGMENTS):
        lo = min(b, 46.6)
        if a >= 46.6:
            continue
        top = depth(a) if i else 3000
        chain(p, [(sx * 770, top), (sx * 770, depth(lo))])
        chain(p, [(sx * 130, top), (sx * 130, depth(lo))])
        pipe_top = max(a, 21.7)
        if lo > pipe_top:
            for wall in (695, 845):
                p.rect(sx * wall - 30, depth(lo), 60, depth(pipe_top) - depth(lo), "timber", line="detail")
            for m in range(int(pipe_top) + 1, int(lo) + 1):
                p.circle(sx * 770, depth(m), 45, "leather", line="detail")
    chain(p, [(sx * 770, depth(46.6)), (sx * 700, depth(47.2)), (sx * 450, depth(47.4)), (sx * 200, depth(47.2)), (sx * 130, depth(46.6))])
    p.rect(sx * 770 - 110, depth(21.7) - 10, 220 * 1, 70, "timber", line="detail")  # the pipe's head, spilling into the launder
p.rect(-880, depth(22) + 10, 1780, 60, "timber", line="detail")  # the launder across to the adit

# at night: the lantern on the headframe
night(p, -10000, -250, 10000, 5200, lights=[(1450, 3800, 3200)])

# ---- names and labels
for x, y, name in ((0, 4450, "headframe"), (-WHIMS, 4950, "horse whim"), (WHIMS, 4950, "horse whim"), (0, 3550, "rag wheels"),
                   (-3000, 3480, "rope drive"), (3000, 3480, "rope drive")):
    p.text(name, x, y, size=13, anchor="middle")
s.label("horse whims: horses walk round in shifts, day and night; fodder and stable boys cost about £12 a month", (WHIMS + 2700, 1500))
s.label("engine shaft, 1.8 by 1.2 m, 66 m deep", (SHAFT, -1000))
s.label("rag-and-chain pumps: leather balls on an endless chain, drawn up a wooden pipe, lift the water up to the adit", (845, depth(22.6)))
s.label("adit: a drainage tunnel at 22 m, out to the valley by gravity", (8500, depth(22) + 1000))
s.label("lode (the ore vein)", (LODE(22.7), depth(22.7)))
s.label("44 m level", (4300, depth(44) + 900))
s.label("inflow about 140 liters a minute in summer, 230 to 270 in winter", (SHAFT - 300, depth(46)))
s.label("66 m level, the bottom", (5500, depth(66) + 900))
with s.state("flooded"):
    s.flaw("water stands at 44 m: the whims only just hold it, and in a wet spell it rises", (500, depth(44)))
    s.flaw("the richest tin and copper ore lies below about 48 m, under water", (LODE(48.2), depth(48.2)))
with s.state("drained"):
    s.label("pumped dry to the bottom", (300, depth(66.6)))
    s.label("the richest ore, below about 48 m", (LODE(48.2), depth(48.2)))
s.save()
