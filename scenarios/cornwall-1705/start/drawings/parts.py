"""The parts of the starting things, each drawn once, in millimetres with y up. Each faces the way it stands in the
smithy, seen from the south (looking north at the back wall), so its own drawing and the smithy's line up."""
import math

from engine.draw import RED
from engine.stock import bench, fire, shelf

COAL = ("#56514b", 0.55)  # coal and coke: darker than iron
STEEL = ("#7d8288", 0.45)


def lump(p, x, y, r, seed):
    """A lump of coal: a rough polygon about r across."""
    n = 5 + seed % 3
    pts = [(x + r * (0.7 + 0.3 * ((seed * 7 + i * 13) % 5) / 4) * math.cos(2 * math.pi * (i + 0.2 * (seed % 3)) / n),
            y + r * 0.8 * (0.7 + 0.3 * ((seed * 11 + i * 5) % 5) / 4) * math.sin(2 * math.pi * (i + 0.2 * (seed % 3)) / n)) for i in range(n)]
    p.poly(pts, COAL, line="detail")


# ---------- the anvil

def anvil(p):
    """The 76 kg wrought-iron anvil with its steel face, on its elm stump, side on with the horn to the left (west).
    Origin: the floor under the middle of the stump. The face is 760 mm up."""
    p.poly([(-240, 0), (240, 0), (222, 480), (-222, 480)], "timber")  # the elm stump
    with p.fine(40):
        for gx, bend in ((-160, 14), (-70, -10), (30, 12), (130, -12)):
            p.path(f"M{gx},8 Q{gx + bend},240 {gx * 0.93:.0f},472", line="faint")
        for r in (40, 75):  # the sawn top's rings, seen edge on
            p.line(-222 + r, 468, 222 - r, 468, "faint")
    body = ("M-150,480 L210,480 L210,515 Q122,528 105,600 L105,640 Q112,702 250,712 L250,745 L-110,745 L-110,736 "
            "L-150,736 Q-292,736 -372,712 L-372,706 Q-250,682 -130,662 Q-68,652 -65,600 L-65,560 Q-70,522 -150,515 Z")
    p.path(body, "iron", reach=[(-372, 480), (250, 745)])
    p.rect(-110, 745, 360, 15, STEEL)  # the steel face, forge-welded on
    p.line(-110, 752, 250, 752, "faint")
    p.poly([(205, 760), (205, 696), (230, 696), (230, 760)], closed=False, line="hidden")  # hardy hole, square
    p.poly([(160, 760), (160, 712), (171, 712), (171, 760)], closed=False, line="hidden")  # pritchel hole, round
    p.path("M-100,760 Q70,740 240,760", line="red")  # the dish in the face, exaggerated
    p.poly([(-110, 760), (-90, 760), (-110, 748)], "paper", line="red")  # chips at its edges
    p.poly([(250, 760), (232, 760), (250, 750)], "paper", line="red")
    p.anchor("face", 20, 760)
    p.anchor("dish", 70, 751)
    p.anchor("chip", -104, 756)
    p.anchor("horn", -300, 722)
    p.anchor("hardy", 217, 735)
    p.anchor("body", 20, 620)
    p.anchor("stump", 100, 240)
    p.anchor("foot", -240, 0)


# ---------- the hearth and bellows

def forge(p):
    """The hearth and its bellows, seen from the front. The bellows, on the left, blow through the cast-iron nozzle
    (tuyere) into the side of the fire pit, which is drawn cut open; a boy works them with the rocking lever. Origin:
    the floor at the hearth's left face, under the nozzle. The fire burns only when the smithy's fire is lit."""
    # behind: the bellows' frame and the lever's post
    for x in (-1350, -650):
        p.rect(x, 0, 60, 640, "timber", line="detail")
    p.rect(-1350, 150, 760, 50, "timber", line="detail")
    p.rect(-1200, 0, 90, 1612, "timber", line="detail")
    # the bellows: leather between three ash boards, hinged at the nose
    p.path("M-380,690 L-1450,930 Q-1590,880 -1565,650 Q-1590,420 -1450,380 L-380,610 Z", "leather", reach=[(-1585, 380), (-380, 930)])
    with p.fine(60):
        for t in (0.25, 0.5, 0.72):
            x = -380 - 1070 * t
            p.path(f"M{x:.0f},{690 + 240 * t:.0f} Q{x - 70:.0f},{670 + 120 * t:.0f} {x:.0f},650 Q{x - 70:.0f},{630 - 115 * t:.0f} {x:.0f},{610 - 230 * t:.0f}", line="faint")
    p.poly([(-380, 690), (-1460, 932), (-1466, 964), (-380, 720)], "timber", line="detail")  # top board
    p.poly([(-380, 610), (-1460, 378), (-1466, 346), (-380, 580)], "timber", line="detail")  # bottom board
    p.rect(-1565, 636, 1185, 28, "timber", line="detail")  # the middle board, fixed to the frame
    p.poly([(-1180, 858), (-1030, 826), (-1010, 894), (-1160, 920)], "masonry", line="detail")  # a stone on the top board
    p.rect(-480, 575, 100, 150, "timber")  # the nose block
    p.poly([(-380, 668), (-60, 662), (-60, 638), (-380, 632)], "iron", line="detail")  # the bellows' pipe
    # the hearth: brick on a stone base, cut open round the fire pit
    p.rect(0, 0, 1200, 300, "masonry")
    p.rect(0, 300, 1200, 460, "brick")
    with p.fine(40):
        for x in (240, 560, 880):
            p.line(x, 0, x, 300, "faint")
        for i, y in enumerate(range(375, 760, 75)):
            p.line(0, y, 1200, y, "faint")
            for x in range(110 if i % 2 else 220, 1200, 230):
                p.line(x, y - 75, x, y, "faint")
    p.rect(0, 560, 820, 200, "brick", cut=True, line="detail")  # cut open
    p.rect(-20, 760, 1240, 30, "masonry")  # the top
    p.rect(300, 640, 460, 150, "paper")  # the fire pit, 150 mm deep
    p.poly([(300, 790), (300, 640), (760, 640), (760, 790)], closed=False)
    p.path("M420,0 L420,250 Q660,440 900,250 L900,0", "paper", reach=[(420, 0), (900, 345)])  # the ash hole
    p.path("M300,640 L760,640 L760,735 Q640,775 530,760 Q410,775 300,735 Z", COAL, line="detail", reach=[(300, 640), (760, 770)])  # coke in the pit
    p.path("M830,790 Q880,880 990,885 Q1110,880 1170,790 Z", COAL, line="detail", reach=[(830, 790), (1170, 885)])  # damp coal heaped by it
    p.poly([(-60, 702), (300, 676), (300, 624), (-60, 598)], "iron")  # the tuyere
    p.line(-60, 650, 300, 650, "hidden")
    with p.state("fire-lit"), p.sound("fire"):
        p.ellipse(360, 660, 120, 70, "fire", line="none")
        p.part(fire, at=(530, 750), width=420, height=260)
    # the rocking lever: pull the handle down and the rod lifts the bottom board
    lever = [(-1480, 1675), (150, 1445)]
    dx, dy = lever[1][0] - lever[0][0], lever[1][1] - lever[0][1]
    nx, ny = -dy / math.hypot(dx, dy) * 32, dx / math.hypot(dx, dy) * 32
    p.poly([(lever[0][0] + nx, lever[0][1] + ny), (lever[1][0] + nx, lever[1][1] + ny), (lever[1][0] - nx, lever[1][1] - ny), (lever[0][0] - nx, lever[0][1] - ny)], "timber")
    p.circle(-1155, 1629, 22, "iron", line="detail")  # its pivot
    p.line(-1450, 1665, -1430, 395, "detail")  # the rod down to the bottom board
    p.line(140, 1420, 140, 1290, "detail")  # the handle
    p.rect(110, 1250, 60, 45, "iron", line="detail")
    p.anchor("handle", 140, 1290)
    p.anchor("lever", -600, 1540)
    p.anchor("bellows", -1000, 760)
    p.anchor("rear", -1565, 650)
    p.anchor("tuyere", -30, 650)
    p.anchor("heat", 330, 660)
    p.anchor("pit", 600, 700)
    p.anchor("hearth", 1100, 450)
    p.anchor("brick", 1100, 650)
    p.anchor("fire", 600, 745)


# ---------- the smith's tools

def hammer(p, x, top, head, handle, peen=None):
    """A hammer resting on a rail by its head, handle hanging down. head: (width, height)."""
    w, h = head
    p.rect(x - 14, top - handle, 28, handle, "timber", line="detail")
    if peen == "cross":
        p.poly([(x - w / 2, top), (x + w / 2 - 25, top), (x + w / 2, top + h * 0.35), (x + w / 2, top + h * 0.65), (x + w / 2 - 25, top + h), (x - w / 2, top + h)], "iron")
    elif peen == "round":
        p.path(f"M{x - w / 2},{top} L{x + w / 2 - h / 2},{top} Q{x + w / 2 + 4},{top + h / 2} {x + w / 2 - h / 2},{top + h} L{x - w / 2},{top + h} Z", "iron", reach=[(x - w / 2, top), (x + w / 2, top + h)])
    else:
        p.rect(x - w / 2, top, w, h, "iron")


def tongs(p, x, top, length=560, jaws="flat"):
    """A pair of tongs hung on a peg by their jaws."""
    rivet = top - 110
    for s in (-1, 1):
        p.poly([(x + s * 6, rivet + 10), (x + s * 26, top - length), (x + s * 16, top - length), (x - s * 2, rivet - 10)], "iron", line="detail")
        if jaws == "flat":
            p.poly([(x - s * 4, rivet), (x + s * 14, rivet + 40), (x + s * 6, top), (x - s * 4, top)], "iron", line="detail")
        else:  # hollow-bit tongs, for round bar
            p.path(f"M{x},{rivet} Q{x + s * 34},{rivet + 55} {x + s * 6},{top}", line="detail")
    p.circle(x, rivet, 9, "iron", line="detail")
    p.circle(x, top + 15, 10, "timber", line="detail")  # the peg


def smith_tools(p):
    """The smith's tools: hammers and tools on a rack board on the wall, tongs and files on pegs, the sledge on the
    floor, and the leg vice on its post. Origin: the floor under the rack's left end."""
    p.rect(0, 1000, 700, 950, "timber")  # the rack board
    with p.fine(40):
        for x in (175, 350, 525):
            p.line(x, 1000, x, 1950, "faint")
    p.rect(0, 1760, 700, 50, "timber", line="detail")  # the hammer rail
    hammer(p, 70, 1810, (125, 44), 330, "cross")  # hand hammers
    hammer(p, 190, 1810, (110, 40), 310, "round")
    hammer(p, 310, 1810, (60, 70), 360, "round")  # fuller
    hammer(p, 410, 1810, (78, 78), 360)  # flatter
    for i, (x, w, l) in enumerate(((500, 16, 210), (540, 20, 190), (590, 22, 200), (640, 26, 180))):  # punches, chisels
        p.poly([(x - w / 2, 1830), (x + w / 2, 1830), (x + w / 2, 1830 - l + 40), (x + (0 if i < 2 else w / 2), 1830 - l), (x - (w / 2 if i < 2 else w / 2), 1830 - l + (0 if i < 2 else 20))], "iron", line="detail")
    for x, jaws in ((90, "flat"), (230, "hollow"), (370, "flat")):
        tongs(p, x, 1400, jaws=jaws)
    for x, l in ((490, 330), (560, 300), (630, 280)):  # files, with wooden handles
        p.circle(x, 1430, 9, "timber", line="detail")
        p.poly([(x - 14, 1420), (x + 14, 1420), (x + 12, 1320), (x - 12, 1320)], "timber", line="detail")
        p.poly([(x - 13, 1320), (x + 13, 1320), (x + 6, 1320 - l), (x - 6, 1320 - l)], "iron", line="detail")
        with p.fine(8):
            for y in range(1310, 1330 - l, -14):
                p.line(x - 11, y, x + 11, y - 6, "faint")
    # the sledge, its head on the floor and its handle against the post
    p.rect(560, 0, 170, 70, "iron")
    p.poly([(630, 70), (660, 70), (698, 830), (670, 830)], "timber", line="detail")
    # the leg vice, side on, on its post
    p.rect(700, 0, 120, 1950, "timber")
    p.rect(690, 850, 150, 30, "iron", line="detail")  # its strap round the post
    p.poly([(822, 0), (858, 0), (858, 960), (822, 960)], "iron")  # fixed leg
    p.rect(822, 960, 48, 90, "iron")  # fixed jaw
    p.poly([(862, 110), (892, 110), (914, 960), (878, 960)], "iron")  # moving leg, hinged at the foot
    p.rect(878, 960, 48, 90, "iron")  # moving jaw
    p.circle(876, 150, 12, "iron", line="detail")
    p.rect(780, 893, 200, 16, "iron", line="detail")  # the screw
    p.rect(940, 880, 40, 42, "iron", line="detail")
    p.rect(952, 760, 16, 280, "iron", line="detail")  # the tommy bar
    p.anchor("hammers", 70, 1650)
    p.anchor("fuller", 330, 1860)
    p.anchor("punches", 570, 1700)
    p.anchor("tongs", 230, 1100)
    p.anchor("files", 630, 1200)
    p.anchor("worn", 560, 1150)
    p.anchor("sledge", 645, 35)
    p.anchor("vice", 875, 1050)
    p.anchor("screw", 960, 1000)


# ---------- the carpenter's tools

def carpentry_tools(p):
    """The carpenter's bench with the tools: planes, chisels and a bow saw on it, a hand saw hung at its end, the axe,
    adze and augers leaning on its front, the drawknife on its shelf. Origin: the floor under the bench's middle."""
    p.part(bench, length=1400, height=850)
    top = 850
    # bow saw, standing on the bench against the wall
    for x in (-660, -270):
        p.rect(x, top + 10, 24, 330, "timber", line="detail")
    p.rect(-640, top + 160, 380, 18, "timber", line="detail")  # stretcher
    p.rect(-660, top + 20, 414, 10, "iron", line="detail")  # blade
    p.line(-650, top + 335, -258, top + 335, "detail")  # the twisted cord, and its toggle
    p.line(-470, top + 335, -440, top + 190, "detail")
    # jack plane and smoothing plane
    p.path(f"M-220,{top} L180,{top} L180,{top + 60} Q170,{top + 72} 150,{top + 72} L-200,{top + 72} Q-220,{top + 70} -220,{top + 40} Z", "timber", reach=[(-220, top), (180, top + 72)])
    p.path(f"M40,{top + 72} Q30,{top + 150} 60,{top + 165} L95,{top + 165} Q110,{top + 120} 115,{top + 72} Z", "timber", line="detail", reach=[(30, top + 72), (115, top + 165)])
    p.poly([(-95, top + 40), (-70, top + 135), (-50, top + 135), (-70, top + 40)], "iron", line="detail")  # iron and wedge
    p.poly([(-62, top + 72), (-40, top + 150), (-25, top + 145), (-45, top + 72)], "timber", line="detail")
    p.rect(220, top, 200, 64, "timber")
    p.poly([(300, top + 40), (320, top + 120), (338, top + 120), (318, top + 40)], "iron", line="detail")
    p.poly([(326, top + 64), (345, top + 135), (358, top + 130), (340, top + 64)], "timber", line="detail")
    # chisels in a block at the back of the bench, their handles up
    p.rect(450, top, 230, 45, "timber", line="detail")
    for x, w in ((475, 22), (530, 24), (585, 26), (640, 28)):
        p.rect(x - 5, top + 45, 10, 20, "iron", line="detail")
        p.poly([(x - w / 2, top + 65), (x + w / 2, top + 65), (x + w / 2 - 3, top + 185), (x - w / 2 + 3, top + 185)], "timber", line="detail")
    # the hand saw, hung from a nail in the bench's end
    p.poly([(712, 770), (830, 770), (790, 130), (742, 130)], "iron", line="detail")
    with p.fine(12):  # its teeth
        p.poly([(742 - 30 * i / 32 - 9 * (i % 2), 130 + 640 * i / 32) for i in range(33)], closed=False, line="faint")
    p.path("M712,760 L712,880 Q760,900 835,875 L835,760 Z", "timber", line="detail", reach=[(712, 760), (835, 900)])
    p.ellipse(772, 830, 30, 22, "paper", line="detail")
    p.circle(700, 860, 7, "iron", line="detail")  # the nail
    # the axe, the augers and the adze, leaning on the bench's front
    p.poly([(-420, 0), (-390, 0), (-330, 760), (-358, 762)], "timber", line="detail")
    p.path("M-372,700 L-322,708 Q-280,690 -238,650 Q-218,735 -232,818 Q-280,785 -324,778 L-374,772 Z", "iron", reach=[(-374, 650), (-218, 818)])
    for x0, x1, top_y, bar, bit in ((-200, -170, 640, 200, 16), (-100, -60, 720, 240, 30), (10, 60, 800, 280, 50)):
        p.poly([(x0 - bit / 2, 0), (x0 + bit / 2, 0), (x0 + bit / 2 + 2, 110), (x1 + 6, top_y), (x1 - 6, top_y), (x0 - bit / 2 + 2, 110)], "iron", line="detail")
        p.rect(x1 - bar / 2, top_y, bar, 30, "timber", line="detail")
    p.poly([(160, 0), (188, 0), (240, 700), (212, 702)], "timber", line="detail")
    p.path("M200,690 L240,710 Q330,700 360,600 L345,595 Q318,665 248,680 L205,672 Z", "iron", line="detail", reach=[(200, 595), (360, 710)])
    # the drawknife on the shelf
    p.rect(-330, 220, 330, 16, "iron", line="detail")
    for x in (-345, 5):
        p.rect(x, 220, 22, 120, "timber", line="detail")
    p.anchor("bow-saw", -470, top + 260)
    p.anchor("planes", -20, top + 60)
    p.anchor("chisels", 560, top + 160)
    p.anchor("hand-saw", 790, 400)
    p.anchor("axe", -270, 735)
    p.anchor("augers", -80, 500)
    p.anchor("bit", 35, 60)
    p.anchor("bit-left", 10, 50)
    p.anchor("bit-right", 60, 50)
    p.anchor("adze", 330, 640)
    p.anchor("drawknife", -170, 236)


# ---------- coal

def coal(p):
    """The coal: 500 kg heaped in a bay of boards against the wall, with its shovel stuck in. Origin: the floor under
    the bay's middle."""
    p.rect(-400, 0, 800, 620, "timber")  # the back boards
    with p.fine(40):
        for y in (207, 413):
            p.line(-400, y, 400, y, "faint")
    # the shovel, stuck into the far side of the heap
    p.poly([(130, 640), (290, 690), (270, 900), (115, 860)], "iron", line="detail")
    p.poly([(190, 860), (215, 866), (175, 1150), (151, 1146)], "timber", line="detail")
    p.rect(113, 1140, 100, 26, "timber", line="detail")
    heap = "M-380,0 L-380,560 Q-300,690 -170,760 Q-110,800 -40,790 Q20,815 90,792 Q200,770 280,700 Q350,640 380,580 L380,0 Z"
    p.path(heap, COAL, line="detail", reach=[(-380, 0), (380, 815)])
    p.path("M-470,0 Q-440,60 -380,95 L380,95 Q440,60 480,0 Z", COAL, line="detail", reach=[(-470, 0), (480, 95)])  # spilled forward
    with p.fine(20):
        seed = 0
        for row, y in enumerate(range(30, 790, 52)):
            half = 380 if y > 95 else 440 - y * 0.6
            for x in range(int(-half + 25 + 28 * (row % 2)), int(half - 20), 62):
                ceiling = 790 - 230 * (abs(x) / 380) ** 1.6
                if y < ceiling - 25:
                    seed += 1
                    lump(p, x + (seed * 17) % 23 - 11, y + (seed * 7) % 15 - 7, 18 + (seed * 5) % 4 * 5, seed)
    for x in (-420, 380):  # the bay's sides, end on
        p.rect(x, 0, 40, 660, "timber")
    p.anchor("heap", -100, 500)
    p.anchor("lump", -200, 250)
    p.anchor("shovel", 165, 1060)
    p.anchor("bay", 390, 600)


# ---------- bar iron

def bar_iron(p):
    """The bar iron: seven wrought-iron flat bars, 38 x 13 mm and 3.7 m long, laid flat on each other and bound with
    wire. Origin: the middle of the bundle's underside."""
    for i, shift in enumerate((0, 18, -12, 25, -20, 8, -5)):
        p.rect(-1850 + shift, 13 * i, 3700, 13, "iron", line="detail")
    for x, y, w in ((-900, 32, 260), (-200, 33, 180), (600, 19, 320), (1200, 58, 200), (-1400, 71, 150)):  # slag streaks
        p.ellipse(x, y, w / 2, 2.2, (RED, 0.55), line="none")
    for x in (-1350, -450, 450, 1350):  # the binding wire
        p.rect(x - 4, -3, 8, 97, "iron", line="detail")
        p.path(f"M{x},94 q14,22 -6,30", line="detail", reach=[(x - 6, 94), (x + 10, 124)])
    p.anchor("left", -1850, 45)
    p.anchor("right", 1850, 45)
    p.anchor("bar", 300, 78)
    p.anchor("slag", 600, 19)
    p.anchor("wire", 450, 94)


# ---------- drawing instruments

def drawing_kit(p):
    """The drawing instruments, kept on the wall: paper pinned up, the 60 cm brass ruler on two nails below it, the
    ink and quills on a little shelf, the dividers on a nail. Origin: the lower left corner of the paper."""
    p.rect(0, 0, 420, 330, ("#fbf6e8", 1.0))  # paper, with a sketch begun on it
    for x, y in ((12, 318), (408, 318), (12, 12), (408, 12)):
        p.circle(x, y, 5, "iron", line="detail")
    with p.fine(6):
        for y in (285, 268, 251):
            p.line(30, y, 250 - (y % 7) * 12, y, "faint")
        p.rect(70, 50, 150, 160, line="faint")
        p.circle(145, 230, 22, line="faint")
        p.line(245, 50, 245, 210, "faint")
        p.line(70, 30, 220, 30, "faint")
    # the brass ruler, hung on two nails
    p.rect(-60, -110, 600, 34, "brass")
    with p.fine(5):
        for mm in range(5, 600, 5):
            p.line(-60 + mm, -76, -60 + mm, -76 - (12 if mm % 50 == 0 else 7), "faint")
    with p.coarse(5):
        for mm in range(100, 600, 100):
            p.line(-60 + mm, -76, -60 + mm, -90, "faint")
    for x in (40, 440):
        p.circle(x, -93, 5, "iron", line="detail")
    # the little shelf, with the ink and quills
    p.part(shelf, at=(600, 0), length=300)
    p.path("M545,0 L545,60 Q545,85 560,90 L610,90 Q625,85 625,60 L625,0 Z", ("#56514b", 0.35), reach=[(545, 0), (625, 90)])
    p.rect(565, 90, 40, 18, "paper", line="detail")
    p.rect(568, 108, 34, 22, "timber", line="detail")  # cork
    for (x0, y0), (x1, y1) in (((575, 100), (530, 340)), ((595, 100), (680, 320))):
        p.line(x0, y0, x1, y1, "detail")
        mx, my = x0 + (x1 - x0) * 0.45, y0 + (y1 - y0) * 0.45
        nx, ny = -(y1 - y0) * 0.06, (x1 - x0) * 0.06
        p.path(f"M{mx:.0f},{my:.0f} Q{(mx + x1) / 2 + nx:.0f},{(my + y1) / 2 + ny:.0f} {x1},{y1} Q{(mx + x1) / 2 - nx * 0.5:.0f},{(my + y1) / 2 - ny * 0.5:.0f} {mx:.0f},{my:.0f} Z",
               ("#fbf6e8", 1.0), line="detail", reach=[(mx, my), (x1, y1)])
    # the dividers, on a nail
    p.circle(770, 330, 5, "iron", line="detail")
    p.circle(770, 305, 11, "brass", line="detail")
    for s in (-1, 1):
        p.poly([(770 + s * 3, 300), (770 + s * 9, 300), (770 + s * 42, 120), (770 + s * 36, 120)], "brass", line="detail")
        p.poly([(770 + s * 36, 120), (770 + s * 42, 120), (770 + s * 46, 80)], "iron", line="detail")
    p.anchor("paper", 300, 300)
    p.anchor("ruler", 400, -93)
    p.anchor("marks", 140, -82)
    p.anchor("ink", 585, 50)
    p.anchor("quills", 660, 290)
    p.anchor("dividers", 800, 200)


# ---------- the letter

def letter(p, side="address"):
    """The letter of introduction, folded into a packet 160 x 105 mm and sealed, from the address side or the seal
    side. Origin: its lower left corner."""
    p.rect(0, 0, 160, 105, ("#f3e7c6", 0.9))
    with p.fine(3):
        for x in range(12, 160, 24):  # the laid paper's chain lines
            p.line(x, 2, x, 103, "faint")
    if side == "address":
        p.text("To Mr Nicholas Penrose,", 12, 74, size=19)
        p.text("Treasurer of Wheal Fortune,", 24, 54, size=19)
        p.text("at Redruth", 50, 34, size=19)
        p.path("M44,26 Q80,20 118,28", line="detail")
        p.anchor("address", 12, 14)
    else:
        p.poly([(0, 78), (96, 70), (160, 74)], closed=False, line="detail")  # the folds and the tucked flap
        p.poly([(0, 26), (88, 32), (160, 28)], closed=False, line="faint")
        p.poly([(70, 105), (88, 32), (104, 0)], closed=False, line="detail")
        p.circle(92, 52, 15, (RED, 0.55))  # the wax seal, unbroken
        p.circle(92, 52, 9, (RED, 0.35), line="detail")
        p.path("M88,57 L96,57 L96,50 Q92,44 88,50 Z", line="detail")
        p.anchor("seal", 100, 58)
        p.anchor("fold", 30, 77)
