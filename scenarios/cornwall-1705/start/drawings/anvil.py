from engine.draw import Sheet
from parts import anvil

s = Sheet("anvil", "Anvil", "Side view, horn to the west, as it stands in the smithy · to scale")
a = s.place(anvil)
s.label("steel face, forge-welded onto the body", a["face"])
s.flaw("face slightly dished (exaggerated here)", a["dish"])
s.flaw("chipped at the edges", a["chip"])
s.label("horn, for bending", a["horn"])
s.label("hardy hole, for cutting and shaping tools", a["hardy"])
s.label("wrought-iron body, 76 kg in all", a["body"], side="left")
s.label("elm stump", a["stump"])
s.dim(a.at(-110, 760), a.at(250, 760), "36 cm", offset=40)
s.dim(a.at(-372, 0), a.at(-372, 760), "76 cm to the face")
s.save()
