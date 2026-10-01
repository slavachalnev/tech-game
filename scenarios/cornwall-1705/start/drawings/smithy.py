# The smithy: a section along its length through the doorway, looking north at the back wall. Millimetres, x east
# from the inside of the west wall, y up from the floor. Inside it is 9 m long, 5.5 m deep and 2.7 m to the eaves.
#
# FREE SPACE for the player's machines:
#   - floor from x = 5950 to 7350 (1.4 m, the room's whole depth), and the back wall above it up to the eaves;
#   - the back wall above the anvil and the coal, x = 3100 to 4700, from 1.2 m up to the eaves;
#   - overhead, the two tie beams (x = 3000 and 6000, underside at 2.65 m) will carry a hoist, a shaft or stock.
# Put a new machine on the free floor with s.place(<part>, at=(6650, 0), thing="<id>"), and move things along if
# it needs more room. Things are laid out side by side so that each one's outline on the drawing board is its own.
from engine.draw import Sheet
from engine.stock import ground, lantern, masonry, night, steam, window
from parts import anvil, bar_iron, carpentry_tools, coal, drawing_kit, forge, smith_tools

L, WALL, EAVES, RIDGE = 9000, 600, 2700, 5000  # inside length, wall thickness, eaves and ridge (underside) heights
TRUSSES = (3000, 6000)
FIRE = (1700 + 530, 900)  # the fire in the hearth, for its glow at night

s = Sheet("smithy", "The smithy", "Section along the smithy through the doorway, looking north · to scale")
p = s.draw

# the back wall, the window in it, and the underside of the roof's north slope
masonry(p, 0, 0, L, EAVES, "granite")
p.rect(0, EAVES - 110, L, 110, "timber", line="detail")  # wall plate
p.part(window, at=(8620, 1380), width=560, height=520)
p.rect(0, EAVES, L, RIDGE - EAVES, ("#6f7377", 0.18))  # slates' underside
with p.fine(40):
    for x in range(225, L, 450):  # common rafters, end on
        p.line(x, EAVES, x, RIDGE, "faint")
p.rect(0, 3750, L, 160, "timber", line="detail")  # purlin
# the hood and chimney over the hearth: hidden behind the roof, out through it above the ridge
p.poly([(1600, 1650), (3020, 1650), (2620, 2250), (2000, 2250)], "brick")
p.rect(2000, 2250, 620, EAVES - 2250, "brick")
p.line(2000, EAVES, 2000, RIDGE + 120, "hidden")
p.line(2620, EAVES, 2620, RIDGE + 120, "hidden")
p.rect(2000, RIDGE + 120, 620, 600, "brick")
p.rect(1960, RIDGE + 720, 700, 70, "masonry")
# the trusses, cut through their tie beams and king posts, the ridge, and the slates over it
for x in TRUSSES:
    p.rect(x - 70, EAVES + 250, 140, RIDGE - EAVES - 250, "timber", cut=True)
    p.rect(x - 110, EAVES - 50, 220, 250, "timber", cut=True)
p.rect(0, RIDGE - 120, L, 120, "timber", cut=True)  # ridge beam
p.rect(-WALL - 150, RIDGE, L + 2 * WALL + 300, 120, ("#6f7377", 0.45), cut=True)
# the floor, and the end walls cut through: the doorway in the east one
ground(p, 0, L, "floor")
ground(p, L + WALL, L + WALL + 1300, "grass")
p.rect(-WALL, -400, WALL, RIDGE + 400, "masonry", cut=True)
p.rect(L, -400, WALL, 400, "masonry", cut=True)
p.rect(L, 2100, WALL, 200, "timber", cut=True)  # lintel
p.rect(L, 2300, WALL, RIDGE - 2300, "masonry", cut=True)
p.rect(L - 30, 0, 30, 2100, "timber", line="detail")  # door frame
p.rect(L + WALL, 0, 30, 2100, "timber", line="detail")
# the door, its leaf swung out: 1.8 m wide, two leaves; the other is in the half cut away
p.rect(L + WALL + 30, 0, 900, 2080, "timber")
with p.fine(40):
    for x in range(L + WALL + 30 + 180, L + WALL + 930, 180):
        p.line(x, 0, x, 2080, "faint")
for y in (300, 1700):
    p.rect(L + WALL + 30, y, 600, 40, "iron", line="detail")  # strap hinges

# what's in it
s.place(forge, at=(1700, 0), thing="forge")
s.place(anvil, at=(3450, 0), thing="anvil")
s.place(coal, at=(4250, 0), thing="coal")
s.place(smith_tools, at=(4850, 0), thing="smith-tools")
s.place(carpentry_tools, at=(8150, 0), thing="carpentry-tools")
s.place(drawing_kit, at=(7520, 1450), thing="drawing-kit")
s.place(bar_iron, at=(4650, EAVES + 200), thing="bar-iron")
s.place(lantern, at=(6000, EAVES - 50))
with s.state("fire-lit"):
    s.place(steam, at=(2310, RIDGE + 790), width=260, height=700)

# at night: the lantern's pool of light, and the hearth's glow when the fire's lit
box = (-WALL - 150, -400, L + WALL + 1300, RIDGE + 1500)
with s.state("idle"):
    night(p, *box, lights=[(6000, 2400, 2300)])
with s.state("fire-lit"):
    night(p, *box, lights=[(6000, 2400, 2300), (*FIRE, 2200)])

# names, under the floor
for x, name in ((1300, "hearth and bellows"), (3400, "anvil"), (4250, "coal"), (5350, "smith's tools and vice"),
                (6650, "free floor"), (8150, "carpenter's bench and tools"), (L + WALL + 480, "door")):
    p.text(name, x, -560, size=14, anchor="middle")
p.text("drawing instruments", 7900, 2150, size=13, anchor="middle")
p.text("bar iron, on the tie beams", 4650, EAVES + 380, size=13, anchor="middle")
p.text("slate roof on oak trusses", 4500, 4300, size=13, anchor="middle")
p.text("granite rubble walls", -WALL, RIDGE + 260, size=13)
p.text("packed earth floor", 6650, -760, size=12, anchor="middle", colour="#7a6a55")
for i, line in enumerate(("no water power: a machine", "here must be driven by hand,", "by a horse, or by something", "you build")):
    p.text(line, 6650, 1500 - 140 * i, size=13, anchor="middle", colour="#9c3b25")
for i, line in enumerate(("dark inside: fine work", "needs the light from", "the doorway")):
    p.text(line, L + WALL + 480, -760 - 140 * i, size=13, anchor="middle", colour="#9c3b25")
s.dim((0, -1000), (L, -1000), "9 m inside")
s.dim((-WALL, 0), (-WALL, EAVES), "2.7 m to the eaves")
s.save()
